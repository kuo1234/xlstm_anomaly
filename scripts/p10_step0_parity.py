"""Step 0 parity checks for p10_canonical_mlstm (issue #15).  Run: python scripts/p10_step0_parity.py [out.json]

Every check returns a dict of max-abs errors; tests/test_p10_canonical_mlstm.py asserts thresholds.
Stabilized states are compared in their *effective* (un-stabilized) form C*exp(m), n*exp(m),
because the max-state m is path dependent (chunkwise vs recurrent) while C*exp(m) is not.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p10_canonical_mlstm import (KERNELS, VERSIONS, CanonicalMLSTMForecaster, CanonicalMLSTMLayer,  # noqa: E402
                                 siging_step)
from mlstm_kernels.torch.chunkwise.native import mlstm_chunkwise__native_autograd  # noqa: E402
from mlstm_kernels.torch.recurrent.native_step import mlstm_recurrent_step__native  # noqa: E402
from mlstm_kernels.torch.parallel.native_siging import mlstm_siging_parallel__native_autograd  # noqa: E402
from xlstm.blocks.mlstm.backends import recurrent_step_stabilized_simple  # noqa: E402

DT = torch.float64


def _mx(a, b):
    return float((a - b).abs().max())


def _eff(st):
    e = torch.exp(st["m"])
    return st["C"] * e[..., None], st["n"] * e


def _state_err(a, b):
    Ca, na = _eff(a)
    Cb, nb = _eff(b)
    scale = max(float(Ca.abs().max()), 1.0)
    return {"C_eff_rel": _mx(Ca, Cb) / scale, "n_eff_rel": _mx(na, nb) / max(float(na.abs().max()), 1.0),
            "conv": _mx(a["conv"], b["conv"]) if "conv" in a and "conv" in b else 0.0}


def _layer(variant="exp", seed=0, **kw):
    torch.manual_seed(seed)
    lay = CanonicalMLSTMLayer(d_model=32, num_heads=4, context_length=512, variant=variant, **kw).to(DT)
    with torch.no_grad():   # non-trivial gates/skip so every path is exercised
        for p in lay.parameters():
            p.add_(0.05 * torch.randn_like(p))
    return lay.eval()


# ------------------------------------------------------------------------- 1 kernel level
def check_kernel_chunk_vs_step(S=150, L=64, seed=1):
    """mlstm_chunkwise native WITH c/n/m_initial + return_last_states vs native_step loop
    and vs xlstm backend recurrent_step_stabilized_simple loop; S not a multiple of L handled
    by chunking the multiple-of-L prefix and stepping the remainder (as in the wrapper)."""
    g = torch.Generator().manual_seed(seed)
    B, NH, DH = 2, 3, 16
    r = lambda *s: torch.randn(*s, generator=g, dtype=DT)
    q, k, v = r(B, NH, S, DH), r(B, NH, S, DH), r(B, NH, S, DH)
    i, f = r(B, NH, S), 3.0 + r(B, NH, S)
    C0, n0, m0 = 0.3 * r(B, NH, DH, DH), 0.3 * r(B, NH, DH), r(B, NH, 1)   # nonzero initial state
    Sf = (S // L) * L
    C, n, m, hs = C0, n0, m0, []
    if Sf > 0:
        Hc, (C, n, m) = mlstm_chunkwise__native_autograd(q[:, :, :Sf], k[:, :, :Sf], v[:, :, :Sf], i[:, :, :Sf],
                                                         f[:, :, :Sf], c_initial=C0, n_initial=n0, m_initial=m0,
                                                         return_last_states=True, chunk_size=L)
        hs = [Hc]
    for t in range(Sf, S):
        h, (C, n, m) = mlstm_recurrent_step__native(q[:, :, t], k[:, :, t], v[:, :, t], i[:, :, t, None],
                                                    f[:, :, t, None], C, n, m, dtype_state=DT)
        hs.append(h[:, :, None])
    H_chunk, st_chunk = torch.cat(hs, 2), {"C": C, "n": n, "m": m}
    # reference 1: mlstm_kernels native step loop
    C, n, m, hs = C0, n0, m0, []
    for t in range(S):
        h, (C, n, m) = mlstm_recurrent_step__native(q[:, :, t], k[:, :, t], v[:, :, t], i[:, :, t, None],
                                                    f[:, :, t, None], C, n, m, dtype_state=DT)
        hs.append(h)
    H_step, st_step = torch.stack(hs, 2), {"C": C, "n": n, "m": m}
    # reference 2: xlstm backend (official xlstm repo) recurrent step loop
    # xlstm backend scales k (not q) by 1/sqrt(DH): same trajectory has C_x = C_kernels/sqrt(DH)
    c, nn_, mm, hs = C0.clone() * DH ** -0.5, n0[..., None].clone() * DH ** -0.5, m0[..., None].clone(), []
    for t in range(S):
        h, (c, nn_, mm) = recurrent_step_stabilized_simple(c, nn_, mm, q[:, :, t:t + 1].clone(), k[:, :, t:t + 1].clone(),
                                                           v[:, :, t:t + 1].clone(), i[:, :, t, None, None],
                                                           f[:, :, t, None, None])
        hs.append(h.reshape(B, NH, DH))
    H_x = torch.stack(hs, 2)
    st_x = {"C": c * DH ** 0.5, "n": nn_[..., 0] * DH ** 0.5, "m": mm[..., 0]}
    return {"S": S, "chunk": L, "H_chunk_vs_native_step": _mx(H_chunk, H_step),
            "H_chunk_vs_xlstm_backend_step": _mx(H_chunk, H_x),
            "state_chunk_vs_native_step": _state_err(st_chunk, st_step),
            "state_chunk_vs_xlstm_backend_step": _state_err(st_chunk, st_x)}


# ------------------------------------------------------------------------- 2 full layer vs official step
def check_layer_vs_official_step(S=150, split=None, seed=2):
    """Wrapper forward (chunkwise, optionally in two calls at `split`) vs official mLSTMLayer.step loop."""
    lay = _layer("exp", seed)
    x = torch.randn(2, S, 32, generator=torch.Generator().manual_seed(seed), dtype=DT)
    with torch.no_grad():
        if split is None:
            y, st = lay(x)
        else:
            y1, s1 = lay(x[:, :split])
            y2, st = lay(x[:, split:], s1)
            y = torch.cat([y1, y2], 1)
        sref, ys = lay.init_state(2, dtype=DT), []
        for t in range(S):
            yt, sref = lay.official_step(x[:, t:t + 1], sref)
            ys.append(yt)
        yref = torch.cat(ys, 1)
    return {"S": S, "split": split, "y_max_abs": _mx(y, yref), "y_scale": float(yref.abs().max()),
            "state": _state_err(st, sref)}


def check_mixed_chunk_then_official_step(S=150, split=70, seed=8):
    """Wrapper chunkwise for x[:split], then hand the state to the OFFICIAL layer.step for the rest
    (and the reverse), vs a single wrapper call.  Proves the state bridge (incl. conv state) is exact."""
    lay = _layer("exp", seed)
    x = torch.randn(2, S, 32, generator=torch.Generator().manual_seed(seed), dtype=DT)
    with torch.no_grad():
        yf, sf = lay(x)
        y1, st = lay(x[:, :split])
        ys = [y1]
        for t in range(split, S):
            yt, st = lay.official_step(x[:, t:t + 1], st)
            ys.append(yt)
        y_a, st_a = torch.cat(ys, 1), st
        st, ys = lay.init_state(2, dtype=DT), []
        for t in range(split):
            yt, st = lay.official_step(x[:, t:t + 1], st)
            ys.append(yt)
        y2, st_b = lay(x[:, split:], st)
        y_b = torch.cat(ys + [y2], 1)
    return {"chunk_then_official_step": _mx(y_a, yf), "official_step_then_chunk": _mx(y_b, yf),
            "state_chunk_then_step": _state_err(st_a, sf), "state_step_then_chunk": _state_err(st_b, sf),
            "y_scale": float(yf.abs().max())}


def check_layer_vs_official_parallel_forward(S=150, seed=3):
    """Informational: wrapper (zero state) vs official mLSTMLayer.forward (parallel_stabilized_simple)."""
    lay = _layer("exp", seed)
    x = torch.randn(2, S, 32, generator=torch.Generator().manual_seed(seed), dtype=DT)
    with torch.no_grad():
        y, _ = lay(x)
        yref = lay.layer(x)
    return {"S": S, "y_max_abs": _mx(y, yref), "y_scale": float(yref.abs().max())}


def check_conv_state_carried(S=150, split=37, seed=4):
    """Split-call continuation equals single call; dropping the conv state at the split changes it."""
    out = {}
    for variant in ("exp", "sig"):
        lay = _layer(variant, seed)
        x = torch.randn(2, S, 32, generator=torch.Generator().manual_seed(seed), dtype=DT)
        with torch.no_grad():
            yf, sf = lay(x)
            y1, s1 = lay(x[:, :split])
            y2, s2 = lay(x[:, split:], s1)
            s1z = dict(s1, conv=torch.zeros_like(s1["conv"]))
            y2z, _ = lay(x[:, split:], s1z)
        out[variant] = {"split_vs_full": _mx(torch.cat([y1, y2], 1), yf),
                        "conv_state_full_vs_split": _mx(sf["conv"], s2["conv"]),
                        "conv_state_equals_last_inputs": _mx(
                            s2["conv"], lay.layer.proj_up(x[:, -(lay.KS - 1):]).split(lay.D, -1)[0]),
                        "effect_of_zeroing_conv_state_first3": _mx(y2z[:, :3], y2[:, :3]),
                        }
    return out


# ------------------------------------------------------------------------- 3 mLSTMsig
def check_siging(S=150, seed=5):
    g = torch.Generator().manual_seed(seed)
    B, NH, DH = 2, 3, 16
    r = lambda *s: torch.randn(*s, generator=g, dtype=DT)
    q, k, v, i, f = r(B, NH, S, DH), r(B, NH, S, DH), r(B, NH, S, DH), r(B, NH, S), 3.0 + r(B, NH, S)
    out = {}
    for normalize in (False, True):
        Hp = mlstm_siging_parallel__native_autograd(q, k, v, i, f, normalize=normalize)
        Hp = Hp[0] if isinstance(Hp, tuple) else Hp
        C, n, hs = torch.zeros(B, NH, DH, DH, dtype=DT), torch.zeros(B, NH, DH, dtype=DT), []
        for t in range(S):
            h, C, n = siging_step(C, n, q[:, :, t], k[:, :, t], v[:, :, t], i[:, :, t, None], f[:, :, t, None],
                                  normalize=normalize)
            hs.append(h)
        out[f"normalize={normalize}"] = {"step_vs_official_parallel": _mx(torch.stack(hs, 2), Hp),
                                         "scale": float(Hp.abs().max())}
    lay = _layer("sig", seed)
    x = torch.randn(2, S, 32, generator=g, dtype=DT)
    with torch.no_grad():
        yf, _ = lay(x)
        # zero-state wrapper cell vs official parallel kernel inside the full layer
        qq, kk, vv, ii, ff, x_act, z, _ = lay._qkv_gates(x, lay.init_state(2, dtype=DT)["conv"])
        Hp = mlstm_siging_parallel__native_autograd(qq, kk, vv, ii, ff, normalize=lay.sig_normalize)
        Hp = Hp[0] if isinstance(Hp, tuple) else Hp
        yp = lay._readout(Hp, x_act, z)
    out["layer_wrapper_vs_official_parallel_core"] = _mx(yf, yp)
    return out


def check_siging_triton(S=150, L=64, seed=6):
    """GPU only: official triton siging chunkwise with c/n_initial + return_last_states vs siging_step."""
    if not torch.cuda.is_available():
        return {"skipped": "no cuda"}
    from mlstm_kernels.torch.chunkwise.triton_xl_chunk_siging import mlstm_siging_chunkwise__xl_chunk
    g = torch.Generator().manual_seed(seed)
    B, NH, DH = 2, 4, 64
    dev = "cuda"
    r = lambda *s: torch.randn(*s, generator=g, dtype=torch.float32).to(dev)
    q, k, v, i, f = r(B, NH, S, DH), r(B, NH, S, DH), r(B, NH, S, DH), r(B, NH, S), 3.0 + r(B, NH, S)
    C0, n0 = 0.3 * r(B, NH, DH, DH), 0.3 * r(B, NH, DH)
    out = {}
    Sf = (S // L) * L
    for normalize in (False, True):
        Hc, (Cc, nc) = mlstm_siging_chunkwise__xl_chunk(q[:, :, :Sf].contiguous(), k[:, :, :Sf].contiguous(),
                                                        v[:, :, :Sf].contiguous(), i[:, :, :Sf].contiguous(),
                                                        f[:, :, :Sf].contiguous(), c_initial=C0, n_initial=n0,
                                                        return_last_states=True, normalize=normalize, chunk_size=L,
                                                        autocast_kernel_dtype=torch.float32)
        C, n, hs = C0.double(), n0.double(), []
        for t in range(Sf):
            h, C, n = siging_step(C, n, q[:, :, t].double(), k[:, :, t].double(), v[:, :, t].double(),
                                  i[:, :, t, None].double(), f[:, :, t, None].double(), normalize=normalize)
            hs.append(h)
        Hs = torch.stack(hs, 2)
        out[f"normalize={normalize}"] = {"H": _mx(Hc.double(), Hs), "H_scale": float(Hs.abs().max()),
                                         "C_rel": _mx(Cc.double(), C) / float(C.abs().max()),
                                         "n_rel": (_mx(nc.double(), n) / float(n.abs().max())) if normalize else None}
    # full layer on GPU: triton chunk path split-continuation vs CPU recurrent path
    lay = _layer("sig", seed).float()
    x = torch.randn(2, S, 32, generator=torch.Generator().manual_seed(seed))
    with torch.no_grad():
        y_cpu, _ = lay(x)
        lay_g = lay.to(dev)
        y1, s1 = lay_g(x[:, :70].to(dev))
        y2, _ = lay_g(x[:, 70:].to(dev), s1)
    out["layer_gpu_triton_split_vs_cpu_step"] = _mx(torch.cat([y1, y2], 1).cpu(), y_cpu)
    out["layer_scale"] = float(y_cpu.abs().max())
    # mLSTMexp on GPU (fp32, native chunkwise): split continuation vs OFFICIAL layer.step on GPU
    lay = _layer("exp", seed).float().to(dev)
    xg = x.to(dev)
    with torch.no_grad():
        y1, s1 = lay(xg[:, :70])
        y2, se = lay(xg[:, 70:], s1)
        sr, ys = lay.init_state(2, dev), []
        for t in range(S):
            yt, sr = lay.official_step(xg[:, t:t + 1], sr)
            ys.append(yt)
    out["exp_gpu_fp32_split_vs_official_step"] = _mx(torch.cat([y1, y2], 1), torch.cat(ys, 1))
    out["exp_gpu_fp32_state"] = _state_err(se, sr)
    out["device"] = torch.cuda.get_device_name(0)
    return out


# ------------------------------------------------------------------------- 4 forecaster smoke
def check_forecaster_smoke(T=150, C=7, seed=7, train_steps=60):
    out = {}
    for variant in ("exp", "sig"):
        torch.manual_seed(seed)
        m = CanonicalMLSTMForecaster(C, d_model=32, variant=variant, context_length=512).to(DT)
        z = torch.randn(2, T, C, dtype=DT)
        with torch.no_grad():
            pf, sf = m(z)
            p1, s1 = m(z[:, :71])
            p2, s2 = m(z[:, 71:], s1)
            st, ps = m.init_state(2), []
            st = {k_: v_.to(DT) for k_, v_ in st.items()}
            for t in range(T):
                pt, st = m.step(z[:, t], st)
                ps.append(pt)
            z2 = z.clone()
            z2[:, 100] += 5.0
            pc, _ = m(z2)
        # tiny training run on a sine: loss must drop
        tt = torch.arange(256, dtype=torch.float32)
        y = torch.stack([torch.sin(tt * (0.05 + 0.03 * c)) for c in range(C)], -1)[None].repeat(4, 1, 1)
        mf = CanonicalMLSTMForecaster(C, d_model=32, variant=variant, context_length=512)
        opt = torch.optim.Adam(mf.parameters(), 3e-3)
        losses = []
        for _ in range(train_steps):
            pred, _ = mf(y[:, :-1])
            loss = ((pred - y[:, 1:]) ** 2).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
            losses.append(float(loss))
        out[variant] = {"arm": m.name, "pred_shape": list(pf.shape), "state_keys": sorted(sf),
                        "state_shapes": {k_: list(v_.shape) for k_, v_ in sf.items()},
                        "split_vs_full": _mx(torch.cat([p1, p2], 1), pf),
                        "step_loop_vs_forward": _mx(torch.stack(ps, 1), pf),
                        "causality_leak_before_t100": _mx(pc[:, :100], pf[:, :100]),
                        "perturbation_effect_at_t100": _mx(pc[:, 100], pf[:, 100]),
                        "loss_first": losses[0], "loss_last": losses[-1],
                        "n_params": sum(p.numel() for p in mf.parameters())}
    return out


def run_all():
    return {"versions": VERSIONS, "kernels": KERNELS, "dtype": str(DT),
            "kernel_chunk_vs_step_S150": check_kernel_chunk_vs_step(150),
            "kernel_chunk_vs_step_S128": check_kernel_chunk_vs_step(128),
            "kernel_chunk_vs_step_S50": check_kernel_chunk_vs_step(50),
            "layer_vs_official_step_S150": check_layer_vs_official_step(150),
            "layer_vs_official_step_S150_split70": check_layer_vs_official_step(150, split=70),
            "layer_vs_official_step_S129_split1": check_layer_vs_official_step(129, split=1),
            "mixed_chunk_and_official_step_S150_split70": check_mixed_chunk_then_official_step(),
            "layer_vs_official_parallel_forward_S150": check_layer_vs_official_parallel_forward(150),
            "conv_state": check_conv_state_carried(),
            "siging": check_siging(),
            "siging_triton_gpu": check_siging_triton(),
            "forecaster_smoke": check_forecaster_smoke()}


if __name__ == "__main__":
    res = run_all()
    s = json.dumps(res, indent=1)
    print(s)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(s)
