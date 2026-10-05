"""Random-input CPU API audit, not a detector or scientific performance test.

Run with --upstream-dir pointing at unmodified pinned Nyderx/xlstmad source.
Only calls upstream stack.step (sLSTMLayer.step uses cell.forward).
"""
import argparse
import copy
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import platform
import sys
import time

import torch

ATOL, RTOL = 1e-5, 1e-4


def leaves(obj, prefix=""):
    if isinstance(obj, torch.Tensor):
        return {prefix: obj}
    if isinstance(obj, dict):
        return {p: t for k, v in obj.items() for p, t in leaves(v, prefix + "/" + str(k)).items()}
    if isinstance(obj, (tuple, list)):
        return {p: t for k, v in enumerate(obj) for p, t in leaves(v, prefix + "/" + str(k)).items()}
    return {}


def digest(obj):
    h = hashlib.sha256()
    for k, v in sorted(leaves(obj).items()):
        h.update(k.encode())
        h.update(str((tuple(v.shape), v.dtype)).encode())
        h.update(v.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--upstream-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.upstream_dir / 'xlstmad.py'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == '6e0d615e0237413e7d565c181276a455b7c663559b880916ff18b58cc467e49a'
    assert importlib.metadata.version('xlstm') == '2.0.5'
    sys.path.insert(0, str(args.upstream_dir.resolve()))
    import xlstmad as native
    torch.set_num_threads(1)
    torch.manual_seed(22)
    torch.use_deterministic_algorithms(True)
    original = native.create_config

    def config(*a, **kw):
        c = original(*a, **kw)
        for n in ('dtype', 'dtype_b', 'dtype_r', 'dtype_w', 'dtype_g', 'dtype_s', 'dtype_a'):
            setattr(c.slstm_block.slstm, n, 'float32')
        return c

    native.create_config = config
    try:
        model = native.xLSTMAD(embedding_dim=40, features_no=8, window_size=64, slstm_backend='vanilla').float().eval()
    finally:
        native.create_config = original
    # Nonzero recurrent weights avoid a trivial untrained-zero recurrence test.
    # Random fixture only: never loads or changes a scientific checkpoint.
    with torch.no_grad():
        for name, p in model.named_parameters():
            if '_recurrent_kernel_' in name:
                p.normal_(0, 0.05)
    model.requires_grad_(False)
    x = torch.randn(2, 23, 8)
    def immutable_model_state():
        return {'parameters': dict(model.named_parameters()), 'buffers': dict(model.named_buffers())}

    before = digest(immutable_model_state())
    rng_before = torch.get_rng_state().clone()
    checks = {}
    start = time.monotonic()

    def compare(name, a, b, exact=False):
        aa, bb = leaves(a), leaves(b)
        assert aa.keys() == bb.keys(), name
        errors = [float((aa[k] - bb[k]).abs().max()) for k in aa]
        ok = all(torch.equal(aa[k], bb[k]) if exact else torch.allclose(aa[k], bb[k], atol=ATOL, rtol=RTOL) for k in aa)
        checks[name] = dict(pass_=ok, max_abs=max(errors, default=0), exact=all(torch.equal(aa[k], bb[k]) for k in aa))

    def step(z, state=None):
        if state is None:
            state = {'encoder': None, 'decoder': None}
        enc, state['encoder'] = model.encoder.step(model.input_projection(z), state['encoder'])
        dec, state['decoder'] = model.decoder.step(enc, state['decoder'])
        return model.output_projection(model.gelu(dec)), state

    def run(z, state=None, chunks=None):
        chunks = chunks or [z.shape[1]]
        assert sum(chunks) == z.shape[1]
        ys, offset = [], 0
        for size in chunks:
            for t in range(offset, offset + size):
                y, state = step(z[:, t:t+1], state)
                ys.append(y)
            # Actual capture/restore at each delivery boundary, not reinitialization.
            state = copy.deepcopy(state)
            offset += size
        return torch.cat(ys, dim=1), state

    with torch.inference_mode():
        full = model(x)
        recurrent, end = run(x)
        chunked, chunk_end = run(x, chunks=[3, 1, 7, 12])
        compare('native_forward_vs_recurrent_output', full, recurrent)
        compare('recurrent_vs_chunked_output', recurrent, chunked, exact=True)
        compare('recurrent_vs_chunked_final_state', end, chunk_end, exact=True)
        _, prefix = run(x[:, :9])
        snapshot = copy.deepcopy(prefix)
        snapshot_hash = digest(snapshot)
        expected, expected_state = run(x[:, 9:], copy.deepcopy(prefix))
        buf = io.BytesIO()
        torch.save(snapshot, buf)
        buf.seek(0)
        restored = torch.load(buf, weights_only=True)
        actual, actual_state = run(x[:, 9:], restored)
        compare('serialized_restore_output', expected, actual, exact=True)
        compare('serialized_restore_final_state', expected_state, actual_state, exact=True)
        step(x[:, 9:10], prefix)
        checks['deep_snapshot_immutable'] = dict(pass_=digest(snapshot) == snapshot_hash)
        checks['live_state_mutates_negative_control'] = dict(pass_=digest(prefix) != snapshot_hash)
        # Reset means discard every stack/layer recurrent and convolution state.
        reset_out, reset_state = run(x[:, 9:], None)
        fresh_out = model(x[:, 9:])
        compare('whole_reset_equals_native_fresh_output', reset_out, fresh_out)
        partial = copy.deepcopy(snapshot)
        for stack in partial.values():
            for block in stack.values():
                block.pop('slstm_state', None)
                block.pop('mlstm_state', None)
        partial_out, _ = run(x[:, 9:], partial)
        checks['conv_only_history_negative_control'] = dict(pass_=not torch.allclose(partial_out, fresh_out, atol=ATOL, rtol=RTOL), max_abs=float((partial_out-fresh_out).abs().max()))
        changed = x.clone()
        changed[:, 9:] = changed[:, 9:] + 100
        compare('native_future_prefix_invariance', full[:, :9], model(changed)[:, :9], exact=True)
        changed_out, _ = run(changed)
        compare('recurrent_future_prefix_invariance', recurrent[:, :9], changed_out[:, :9], exact=True)
        compare('batch_permutation', recurrent.flip(0), run(x.flip(0))[0])
        compare('batch_partition', recurrent, torch.cat([run(x[i:i+1])[0] for i in range(2)]))
        compare('new_stream_no_prior_history', run(x[:1], None)[0], model(x[:1]))
        # Score first, then discard candidate state for RESET; no rescore of x_t.
        decisions = {}
        for action in ('KEEP', 'RESET'):
            now, candidate = step(x[:, 9:10], copy.deepcopy(snapshot))
            score = ((now - x[:, 9:10])**2).mean(-1).clone()
            next_state = candidate if action == 'KEEP' else None
            nxt, _ = step(x[:, 10:11], next_state)
            decisions[action] = (score, nxt)
        compare('score_before_action_equal', decisions['KEEP'][0], decisions['RESET'][0], exact=True)
        checks['action_changes_only_later_output'] = dict(pass_=not torch.allclose(decisions['KEEP'][1], decisions['RESET'][1], atol=ATOL, rtol=RTOL))
        checks['all_state_finite'] = dict(pass_=all(torch.isfinite(v).all().item() for v in leaves(end).values()))
        checks['parameters_and_registered_buffers_unchanged'] = dict(pass_=digest(immutable_model_state()) == before)
        checks['rng_unchanged_during_eval'] = dict(pass_=torch.equal(torch.get_rng_state(), rng_before))
    result = dict(date='2026-10-05', scope='random_input_API_probe_not_performance', seed=22,
                  shape=list(x.shape), embedding=40, context_length=64, nonzero_recurrent_fixture=True,
                  backend='vanilla_cpu_float32', atol=ATOL, rtol=RTOL, python=sys.version,
                  platform=platform.platform(), versions={p: importlib.metadata.version(p) for p in ('torch','xlstm','lightning','numpy')},
                  elapsed_seconds=time.monotonic()-start, checks=checks,
                  state_shapes={k:list(v.shape) for k,v in leaves(end).items()},
                  parameter_buffer_sha256=before,
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  upstream_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  not_tested=['forecast-trained checkpoint','long-horizon numerical stability','CUDA','optimized chunk kernel','heterogeneous per-row resets','performance','drift observer'])
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k in ('elapsed_seconds','checks','versions')},indent=2))
    assert all(v['pass_'] for v in checks.values()), 'API probe failed; preserve output for review'


if __name__ == '__main__':
    main()
