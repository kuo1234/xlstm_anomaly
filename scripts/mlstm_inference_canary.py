"""Inference/parity/throughput canaries for the frozen mLSTM audit.

This script is engineering-only.  It receives observation windows, never
evaluator labels, and never creates an optimizer or writes a checkpoint.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT / "data" / "phase_e2" / "official_xlstmad"
CUDA_OVERLAY = Path(os.environ.get("XLSTM_CUDA_WORKTREE", ROOT.parent / "cuda-spark"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(OFFICIAL))
sys.path.insert(0, str(CUDA_OVERLAY / "research" / "cuda_spark"))

from phase_e2_common import build as build_vanilla  # noqa: E402
from phase_e2_observer import extract as extract_s_observer  # noqa: E402
from phase_e2_fast_observer import FastStateObserver  # noqa: E402
from mlstm_observer import Capture, MLSTM_CELLS, extract as extract_m_observer  # noqa: E402


CHECKPOINT = ROOT / "data" / "phase_f_v4" / "runs" / "xlstm_11" / "best.pt"
EXTENSION_DIR = Path(os.environ.get("TORCH_EXTENSIONS_DIR", "/tmp/xlstm_cuda_full121_false"))
ATOL = 1e-5
RTOL = 1e-4


def configure() -> None:
    torch.set_num_threads(4)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.set_float32_matmul_precision("highest")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def metric(a: torch.Tensor, b: torch.Tensor) -> dict:
    aa = a.detach().float()
    bb = b.detach().float()
    diff = (aa - bb).abs()
    return {
        "shape_a": list(aa.shape),
        "shape_b": list(bb.shape),
        "max_abs": float(diff.max().item()) if diff.numel() else 0.0,
        "mean_abs": float(diff.mean().item()) if diff.numel() else 0.0,
        "failed_elements": int((~torch.isclose(aa, bb, atol=ATOL, rtol=RTOL)).sum().item()),
        "finite_a": bool(torch.isfinite(aa).all()),
        "finite_b": bool(torch.isfinite(bb).all()),
        "allclose": bool(torch.allclose(aa, bb, atol=ATOL, rtol=RTOL)),
    }


def _float32_factory(original):
    def factory(*args, **kwargs):
        cfg = original(*args, **kwargs)
        for name in ("dtype", "dtype_b", "dtype_r", "dtype_w", "dtype_g", "dtype_s", "dtype_a"):
            setattr(cfg.slstm_block.slstm, name, "float32")
        return cfg

    return factory


def build_cuda():
    from slstm_cuda_fixture import install_loader
    import xlstmad as native

    install_loader(
        arch="121", code="sm_121", static_stub="false", rdc=False,
        extension_dir=EXTENSION_DIR,
    )
    import xlstm.blocks.slstm.cell as cell_mod
    cell_mod.sLSTMCellCUDA.mod.clear()
    original = native.create_config
    native.create_config = _float32_factory(original)
    try:
        model = native.xLSTMAD(
            embedding_dim=40, features_no=8, window_size=64,
            lr=0.001, slstm_backend="cuda",
        ).float().cuda()
    finally:
        native.create_config = original
    return model


def load_checkpoint(model, checkpoint: Path = CHECKPOINT):
    payload = torch.load(checkpoint, map_location="cpu")
    model.load_state_dict(payload["model"], strict=True)
    model.eval()
    return model


def map_vanilla_weights(vanilla, cuda) -> None:
    """Convert the public vanilla sLSTM layout to CUDA's internal layout."""
    state = {name: value.detach().clone() for name, value in vanilla.state_dict().items()}
    vmods, cmods = dict(vanilla.named_modules()), dict(cuda.named_modules())
    for name in list(state):
        if name.endswith(".slstm_cell._recurrent_kernel_"):
            module = name[: -len("._recurrent_kernel_")]
            state[name] = cmods[module]._recurrent_kernel_ext2int(
                vmods[module]._recurrent_kernel_int2ext(state[name])
            )
        elif name.endswith(".slstm_cell._bias_"):
            module = name[: -len("._bias_")]
            state[name] = cmods[module]._bias_ext2int(
                vmods[module]._bias_int2ext(state[name])
            )
    cuda.load_state_dict(state, strict=True)


def _scaler(seed: int) -> tuple[np.ndarray, np.ndarray]:
    from m0.synthetic import generate

    prefix = np.asarray(generate(seed, "stationary", "none").observations[:4096], dtype=np.float64)
    mean = prefix.mean(0)
    std = prefix.std(0)
    std[std == 0] = 1.0
    return mean, std


def fixture_windows() -> torch.Tensor:
    """Fixed observation-only windows; endpoint choices are pre-outcome constants."""
    from m0.synthetic import generate

    choices = [
        (3000, "stationary", "none", (5000, 5200)),
        (3000, "abrupt", "none", (9000, 9200)),
        (3001, "gradual", "none", (12000, 12200)),
        (3001, "recurring", "none", (10000, 10200)),
        (3002, "correlation", "none", (9000, 9200)),
        (3002, "abrupt", "mixture", (5632, 5700)),
    ]
    rows = []
    for seed, scenario, condition, interval in choices:
        stream = generate(seed, scenario, condition)
        mean, std = _scaler(seed)
        observations = ((stream.observations.astype(np.float64) - mean) / std).astype(np.float32)
        endpoints = np.arange(interval[0], interval[1], 8, dtype=np.int64)
        rows.append(np.stack([observations[t - 63 : t + 1] for t in endpoints]))
    x = np.concatenate(rows, axis=0)
    if len(x) < 128:
        raise RuntimeError("fixed fixture unexpectedly small")
    return torch.from_numpy(x).cuda()


def plain_score(model, x):
    with torch.no_grad():
        output = model(x)
    return output, (output - x).square().mean((1, 2))


def combined_observer(model, x):
    with torch.no_grad(), FastStateObserver(model) as s_obs, Capture(model) as m_obs:
        output = model(x)
        s_base = s_obs.summary()
        m_base = m_obs.summary()
        m_traces = {cell: {key: value.clone() for key, value in trace.items()} for cell, trace in m_obs.latest.items()}
    return output, (output - x).square().mean((1, 2)), s_base, m_base, m_traces


def run_parity() -> dict:
    configure()
    fixture = fixture_windows()
    vanilla = load_checkpoint(build_vanilla())
    cuda = build_cuda()
    map_vanilla_weights(vanilla, cuda)
    cuda.eval()
    rows = {}
    for batch in (1, 8, 128):
        x = fixture[:batch].contiguous()
        with torch.no_grad():
            yv, sv = plain_score(vanilla, x)
            yc, sc = plain_score(cuda, x)
        row = {"output": metric(yv, yc), "score": metric(sv, sc)}

        # Vanilla reference observer and CUDA native-state observer are the
        # existing sLSTM semantics, not a new scientific feature.
        sv_score, sv_feat = extract_s_observer(vanilla, x)
        with torch.no_grad(), FastStateObserver(cuda) as fast:
            yc2 = cuda(x)
            sc2 = (yc2 - x).square().mean((1, 2))
            sc_feat = fast.summary()
        row["sLSTM_score"] = metric(sv_score, sc2)
        row["sLSTM_common18"] = metric(sv_feat, sc_feat)

        mv = extract_m_observer(vanilla, x, check_mutation=True)
        mc = extract_m_observer(cuda, x, check_mutation=True)
        row["mLSTM_score"] = metric(mv["score"], mc["score"])
        row["mLSTM_base18"] = metric(mv["base"], mc["base"])
        row["mLSTM_native_replay"] = {"vanilla": {}, "cuda": {}}
        for cell in MLSTM_CELLS:
            for backend_name, model, result in (("vanilla", vanilla, mv), ("cuda", cuda, mc)):
                cmod = dict(model.named_modules())[cell]
                replay = result["replay_outputs"][cell]["replay_h"].reshape(batch, 64, 4, 20).permute(0, 2, 1, 3)
                normalized = cmod.outnorm(replay).permute(0, 2, 1, 3).reshape(batch, 64, 80)
                row["mLSTM_native_replay"][backend_name][cell] = metric(normalized, result["native_outputs"][cell])
        rows[str(batch)] = row

    # Observer ON/OFF, reset, permutation, and prefix-causality contracts on
    # one fixed B=128 fixture.
    x = fixture[:128].contiguous()
    y_plain, score_plain = plain_score(cuda, x)
    y_combo, score_combo, s_base, m_base, _ = combined_observer(cuda, x)
    checks = {
        "observer_output_invariance": metric(y_plain, y_combo),
        "observer_score_invariance": metric(score_plain, score_combo),
        "reset_duplicate_output": metric(*[y_combo[:1], y_combo[1:2]]) if False else None,
    }
    duplicate = torch.cat((x[:1], x[:1]), dim=0)
    yd, sd, sdup, mdup, _ = combined_observer(cuda, duplicate)
    checks["reset_duplicate_output"] = metric(yd[:1], yd[1:2])
    checks["reset_duplicate_s"] = metric(sdup[:1], sdup[1:2])
    checks["reset_duplicate_m"] = metric(mdup[:1], mdup[1:2])
    perm = torch.tensor([3, 0, 2, 1] + list(range(4, 128)), device="cuda")
    yp, sp, spp, mpp, _ = combined_observer(cuda, x[perm])
    inv = torch.argsort(perm)
    checks["batch_permutation_output"] = metric(y_plain, yp[inv])
    checks["batch_permutation_s"] = metric(s_base, spp[inv])
    checks["batch_permutation_m"] = metric(m_base, mpp[inv])
    future = x.clone()
    future[:, 32:] += 7.0
    yf, sf = plain_score(cuda, future)
    checks["prefix_output_0_32"] = metric(y_plain[:, :32], yf[:, :32])
    # Fast and m observers are deliberately run with model hashing enabled in
    # the m observer; no optimizer or state is created by either path.
    return {
        "checkpoint": str(CHECKPOINT),
        "checkpoint_payload_epoch": int(torch.load(CHECKPOINT, map_location="cpu")["epoch"]),
        "atol": ATOL,
        "rtol": RTOL,
        "batches": rows,
        "invariance": checks,
        "status": "PASS" if all(
            value.get("allclose", True) for value in checks.values() if isinstance(value, dict)
        ) and all(
            value["output"]["allclose"] and value["score"]["allclose"] and value["mLSTM_base18"]["allclose"]
            for value in rows.values()
        ) else "FAIL",
    }


def _bench_one(fn, x, warmup=3, steps=10):
    for _ in range(warmup):
        fn()
    torch.cuda.synchronize()
    start = time.perf_counter()
    for _ in range(steps):
        fn()
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    return {
        "steps": steps,
        "elapsed_s": elapsed,
        "decisions_per_sec": float(x.shape[0] * steps / elapsed),
        "batches_per_sec": float(steps / elapsed),
        "peak_memory_bytes": int(torch.cuda.max_memory_allocated()),
    }


def run_benchmark() -> dict:
    configure()
    vanilla = load_checkpoint(build_vanilla())
    model = build_cuda()
    map_vanilla_weights(vanilla, model)
    model.eval()
    x = fixture_windows()[:128].contiguous()
    rows = {}
    for name, fn in (
        ("score_only", lambda: plain_score(model, x)),
        ("sLSTM_fast_observer", lambda: (lambda z: z)(None) if False else _fast_once(model, x)),
        ("mLSTM_observer", lambda: extract_m_observer(model, x, check_mutation=False)),
        ("sLSTM_plus_mLSTM", lambda: combined_observer(model, x)),
    ):
        torch.cuda.reset_peak_memory_stats()
        rows[name] = _bench_one(fn, x)
    return {"batch": 128, "window": 64, "rows": rows}


def _fast_once(model, x):
    with torch.no_grad(), FastStateObserver(model) as observer:
        output = model(x)
        summary = observer.summary()
    return output, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("parity", "benchmark"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_parity() if args.mode == "parity" else run_benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result.get("status", "PASS") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
