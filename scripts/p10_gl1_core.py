"""P10 G-L1 core: label-blind data handling, injections, training, episode evaluation.

Time conventions (fixed):
  * state "at t" = state after consuming inputs z[:t] (ready to consume z[t]).
  * the forecast produced while consuming input z[t] is the prediction of z[t+1];
    the observation z[tau] is therefore scored with the prediction made at input tau-1
    (score-before-write).
  * every fork time (G0 positions, drift onsets, sentinel starts) lies on a 16-step grid
    measured from index 0 of the series, so Titans chunk position is 0 at every fork.
"""
from __future__ import annotations

import hashlib
import math
import os
import zlib
from dataclasses import dataclass, field

import numpy as np
import torch

import p10_gl1_models as M

GRID = 16


class TechnicalInvalid(Exception):
    """A-class failure (data/manifest/implementation/hardware); reserve substitution allowed."""


# ============================================================================ data
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_train_split(path, expected_sha=None):
    base = os.path.basename(path)
    if "test" in base or not base.endswith("_train.txt"):
        raise TechnicalInvalid(f"label-blind guard: refusing non-train file {base}")
    if not os.path.exists(path):
        raise TechnicalInvalid(f"missing data file {path}")
    if expected_sha is not None and sha256_file(path) != expected_sha:
        raise TechnicalInvalid(f"SHA256 mismatch for {base}")
    x = np.loadtxt(path, delimiter=",", dtype=np.float64)
    if x.ndim != 2 or not np.isfinite(x).all():
        raise TechnicalInvalid(f"corrupt data in {base}")
    return x


@dataclass
class Prepared:
    z: np.ndarray            # N,C float32 z-scored
    fit_end: int
    tr_end: int
    kept: np.ndarray
    u: np.ndarray            # per-channel impulse/sentinel unit (z units)
    meta: dict = field(default_factory=dict)


def prepare(x, cfg):
    d = cfg["data"]
    N = x.shape[0]
    fit_end = int(N * d["fit_fraction"]) // GRID * GRID
    tr_end = int(fit_end * d["train_fraction_of_fit"]) // GRID * GRID
    fit = x[:fit_end]
    kept = np.where(fit.std(0) >= d["near_constant_sd"])[0]
    mu = fit[:, kept].mean(0)
    sd = np.maximum(fit[:, kept].std(0), d["zscore_sd_floor"])
    z = ((x[:, kept] - mu) / sd).astype(np.float32)
    u = np.maximum(np.diff(z[:fit_end], axis=0).std(0), d["unit_floor"]).astype(np.float32)
    return Prepared(z=z, fit_end=fit_end, tr_end=tr_end, kept=kept, u=u,
                    meta=dict(N=N, C=len(kept), fit_end=fit_end, tr_end=tr_end))


def synthetic_series(N=6000, C=6, seed=0):
    """Synthetic AR(1)+seasonal series used ONLY for dry-runs and unit tests."""
    rng = np.random.default_rng(seed)
    t = np.arange(N)
    base = np.stack([np.sin(2 * np.pi * t / (50 + 7 * c)) for c in range(C)], 1)
    e = np.zeros((N, C))
    for i in range(1, N):
        e[i] = 0.8 * e[i - 1] + 0.3 * rng.standard_normal(C)
    return base + e + 0.05 * rng.standard_normal((N, C))


# ============================================================================ injections (z units)
def grid_positions(rng, lo, hi, n):
    lo_g, hi_g = math.ceil(lo / GRID), math.floor(hi / GRID)
    if hi_g - lo_g + 1 < n:
        raise TechnicalInvalid(f"stream too short for {n} grid positions in [{lo},{hi}]")
    return np.sort(rng.choice(np.arange(lo_g, hi_g + 1), size=n, replace=False) * GRID)


def apply_drift(seg, rel_onset, family, chans, signs, cfg):
    """seg: T,C array (copy is returned); drift active for rows >= rel_onset."""
    out = seg.copy()
    if family == "none":
        return out
    f = cfg["utility"]["families"][family]
    T = seg.shape[0]
    k = np.arange(T) - rel_onset
    act = k >= 0
    if family == "level":
        for c, s in zip(chans, signs):
            out[act, c] += s * f["magnitude_sigma"]
    elif family == "ramp":
        frac = np.clip((k + 1) / f["ramp_steps"], 0, 1)
        for c, s in zip(chans, signs):
            out[act, c] += s * f["magnitude_sigma"] * frac[act]
    elif family == "gain":
        for c in chans:
            out[act, c] = f["factor"] * seg[act, c]  # fit-region mean is 0 in z units
    else:
        raise ValueError(family)
    return out


def apply_sentinel(seg, rel_start, kind, chans, u, cfg, rng, donor=None):
    out = seg.copy()
    S = cfg["sentinel"]["types"][kind]
    L = S["length"]
    sl = slice(rel_start, rel_start + L)
    if kind == "spike":
        xi = rng.choice([-1.0, 1.0], size=(L, len(chans)))
        out[sl, chans] += S["amp_u"] * u[chans][None] * xi
    elif kind == "stuck":
        out[sl, chans] = seg[rel_start - 1, chans][None]
    elif kind == "corr_break":
        out[sl, chans] = donor[:, chans]
    return out


# ============================================================================ inference helpers
def to_t(a, dev):
    return torch.as_tensor(a, dtype=torch.float32, device=dev)


@torch.no_grad()
def run(model, z, state, seg=2048):
    """Consume z (B,T,C) from state; return preds (B,T,C), final state, max state norm."""
    preds, mx = [], torch.zeros(z.shape[0], device=z.device)
    for s in range(0, z.shape[1], seg):
        p, state = model.forward(z[:, s:s + seg], state)
        preds.append(p)
        mx = torch.maximum(mx, model.state_norm(state))
    return torch.cat(preds, 1), state, mx


@torch.no_grad()
def run_capture(model, z1, state, t_begin, t_end, capture):
    """Single stream z1 (T_all,C) tensor. Consume inputs z1[t_begin:t_end] from `state` (state at
    t_begin). Returns preds for observations t_begin+1..t_end (array index tau -> pred of z[tau]),
    dict of states at the capture times, and max state norm."""
    caps = sorted(set(int(c) for c in capture if t_begin <= c <= t_end))
    out = {}
    preds = []
    cur, st, mx = t_begin, state, torch.zeros(1, device=z1.device)
    for c in caps + [t_end]:
        if c > cur:
            p, st, m = run(model, z1[None, cur:c], st)
            preds.append(p[0]); mx = torch.maximum(mx, m); cur = c
        if c in caps:
            out[c] = st
    P = torch.cat(preds, 0) if preds else torch.zeros(0, z1.shape[1], device=z1.device)
    return P, out, float(mx.max())


@torch.no_grad()
def windowed_preds(model, z_seg, ends, R, batch):
    """Reset arm: for each input index e in `ends` (indices into z_seg), predict z_seg[e+1] from
    a zero state using only z_seg[e-R+1 : e+1]."""
    ends = np.asarray(ends)
    assert (ends - R + 1 >= 0).all()
    out = []
    for s in range(0, len(ends), batch):
        e = ends[s:s + batch]
        idx = (e[:, None] - R + 1) + np.arange(R)[None]
        W = z_seg[torch.as_tensor(idx, device=z_seg.device)]  # n,R,C
        if isinstance(model, M.WindowOnly):
            out.append(model.forward_windows(W))
        else:
            p, _ = model.forward(W, model.init_state(W.shape[0], z_seg.device))
            out.append(p[:, -1])
    return torch.cat(out, 0)


def scores_from(pred, obs, sigma):
    return (((obs - pred) / sigma) ** 2).mean(-1)


# ============================================================================ training
def _rewind(model, zt, t, dev):
    _, st, _ = run(model, zt[None, :t - 1], model.init_state(1, dev))
    return st


def val_residuals(model, name, zt, P, R, dev, batch):
    """Validation residuals in each deployment arm (used for sigma and the fit-adequacy check)."""
    out = {}
    obs = zt[P.tr_end:P.fit_end]
    ends = np.arange(P.tr_end - 1, P.fit_end - 1)
    if name == "window_only":
        out["single"] = obs - windowed_preds(model, zt, ends, R, batch)
        return out
    if name != "mlstm_std":
        st = _rewind(model, zt, P.tr_end, dev)
        p, _, _ = run(model, zt[None, P.tr_end - 1:P.fit_end - 1], st)
        out["persistent"] = obs - p[0]
    out["reset"] = obs - windowed_preds(model, zt, ends, R, batch)
    return out


def train_model(name, P, cfg, seed, dev, log=print):
    """Returns dict(model, info). Scientific failures are recorded in info, never raised."""
    tc = cfg["training"]
    torch.manual_seed(seed); np.random.seed(seed)
    rng = np.random.default_rng(seed)
    C = P.z.shape[1]
    model = M.build(name, C).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=tc["lr"])
    zt = to_t(P.z, dev)
    R = cfg["models"]["reset_period_R"]
    info = dict(model=name, seed=seed, n_params=M.n_params(model), nan_train=False, iters=0,
                best_val=float("inf"), train_state_norm_max=0.0)
    best, bad, it = None, 0, 0
    L, Bt = tc["seq_len"], tc["batch"]
    stateful = name in ("mlstm", "gdeltanet", "titans", "lstm")

    def val_loss():
        model.eval()
        with torch.no_grad():
            r = val_residuals(model, name, zt, P, R, dev, cfg["eval"]["window_batch"])
            key = "persistent" if stateful else ("single" if name == "window_only" else "reset")
            v = float((r[key] ** 2).mean())
        model.train()
        return v

    while it < tc["max_iters"]:
        if stateful:  # one epoch of stateful TBPTT over the training region
            offs = rng.integers(0, L, size=Bt)
            n_ch = int(min((P.tr_end - 1 - o) // L for o in offs))
            st = model.init_state(Bt, dev)
            for j in range(n_ch):
                idx = offs[:, None] + j * L + np.arange(L)[None]
                x = zt[torch.as_tensor(idx, device=dev)]
                y = zt[torch.as_tensor(idx + 1, device=dev)]
                p, st = model.forward(x, st)
                loss = ((p - y) ** 2).mean()
                opt.zero_grad(); loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), tc["grad_clip"])
                opt.step()
                st = M.state_detach(st)
                info["train_state_norm_max"] = max(info["train_state_norm_max"], float(model.state_norm(st).max()))
                it += 1
                if not torch.isfinite(loss):
                    info["nan_train"] = True
                    break
                if it % tc["eval_every"] == 0 or it >= tc["max_iters"]:
                    break
            if info["nan_train"]:
                break
        else:  # window models: random windows of length R (window_only: K=R) from zero state
            nb = tc["window_batch"]
            e = rng.integers(R - 1, P.tr_end - 1, size=nb)
            idx = (e[:, None] - R + 1) + np.arange(R)[None]
            W = zt[torch.as_tensor(idx, device=dev)]
            y = zt[torch.as_tensor(e + 1, device=dev)]
            if name == "window_only":
                p = model.forward_windows(W)
            else:
                p = model.forward(W, model.init_state(nb, dev))[0][:, -1]
            loss = ((p - y) ** 2).mean()
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), tc["grad_clip"])
            opt.step(); it += 1
            if not torch.isfinite(loss):
                info["nan_train"] = True
                break
        if it % tc["eval_every"] == 0 or it >= tc["max_iters"]:
            v = val_loss()
            if not math.isfinite(v):
                info["nan_train"] = True
                break
            if v < info["best_val"]:
                info["best_val"], best, bad = v, {k: t.detach().clone() for k, t in model.state_dict().items()}, 0
            else:
                bad += 1
                if bad >= tc["patience"]:
                    break
    info["iters"] = it
    if best is not None:
        model.load_state_dict(best)
    model.eval()
    return model, info


# ============================================================================ evaluation of one fit
@dataclass
class EvalPlan:
    g0_pos: np.ndarray
    onsets: dict          # family -> array of t0
    chans: dict           # (family, i) -> (chans, signs)
    sent_chans: dict      # (family, i, kind) -> chans
    sent_donor: dict      # (family, i) -> donor offset for corr_break
    g0_chans: dict


def make_plan(P, cfg, machine_key):
    """All positions/channels are drawn label-blind from seeds; identical for all models/arms."""
    ucfg, g0 = cfg["utility"], cfg["g0"]
    N, C = P.z.shape
    E, Lc = ucfg["eval_len"], ucfg["calibration_len"]
    base = int(hashlib.sha256(machine_key.encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng([ucfg["onset_seed"], base])
    Lmax = g0["max_lag"]
    g0_pos = grid_positions(rng, P.fit_end + g0["warmup"], N - Lmax - 2, g0["positions_per_machine"])
    g0_chans = {p: rng.choice(C, size=min(g0["impulse_channels"], C), replace=False) for p in g0_pos}
    onsets, chans, sent_chans, donor = {}, {}, {}, {}
    fams = list(ucfg["families"]) + ["none"]
    for f in fams:
        t0s = grid_positions(rng, P.fit_end + Lc + cfg["utility"]["min_warmup"], N - E - 2,
                             ucfg["episodes_per_family"])
        onsets[f] = t0s
        for i, t0 in enumerate(t0s):
            nch = min(ucfg["drift_channels"], C)
            chans[(f, i)] = (rng.choice(C, size=nch, replace=False), rng.choice([-1.0, 1.0], size=nch))
            for kind, S in cfg["sentinel"]["types"].items():
                sent_chans[(f, i, kind)] = rng.choice(C, size=min(S["channels"], C), replace=False)
            # donor segment for corr_break: real data from >= 2048 steps away (fit or stream region)
            ts = t0 + cfg["sentinel"]["offsets"]["corr_break"]
            cands = np.array([o for o in range(0, N - 64, GRID) if abs(o - ts) >= 2048])
            donor[(f, i)] = int(rng.choice(cands))
    return EvalPlan(g0_pos, onsets, chans, sent_chans, donor, g0_chans)



def sentinel_detection(s_cal, s_bg, event_max, cfg):
    """P3 primary (frozen pre-onset event threshold) and secondary (local rank) detection.
    s_cal: arm's clean scores on [t0-Lc, t0); s_bg: arm's sentinel-free scores on the evaluation
    window; event_max: max score over the 30-step sentinel event. Returns dict."""
    sc = cfg["sentinel"]
    Ls = sc["event_window"]
    cal_max = np.lib.stride_tricks.sliding_window_view(np.asarray(s_cal), Ls).max(1)
    event_thr = float(np.quantile(cal_max, sc["event_threshold_quantile"]))
    bg_max = np.lib.stride_tricks.sliding_window_view(np.asarray(s_bg), Ls).max(1)
    q = float((bg_max < event_max).mean())
    return dict(event_thr=event_thr, event_max=float(event_max), detected=bool(event_max > event_thr),
                q_local=q, detected_local=bool(q > sc["local_q_quantile"]))


def plan_hash(plan):
    h = hashlib.sha256()
    h.update(np.asarray(plan.g0_pos, dtype=np.int64).tobytes())
    for f in sorted(plan.onsets):
        h.update(f.encode()); h.update(np.asarray(plan.onsets[f], dtype=np.int64).tobytes())
    for k in sorted(plan.chans, key=str):
        c, sg = plan.chans[k]
        h.update(str(k).encode()); h.update(np.asarray(c).tobytes()); h.update(np.asarray(sg).tobytes())
    for k in sorted(plan.sent_chans, key=str):
        h.update(str(k).encode()); h.update(np.asarray(plan.sent_chans[k]).tobytes())
    for k in sorted(plan.sent_donor, key=str):
        h.update(f"{k}:{plan.sent_donor[k]}".encode())
    return h.hexdigest()


def g0_response(model, P, plan, cfg, dev, clean_states):
    """Impulse responses R(lag), lag=1..Lmax, and the null-fork difference."""
    g0 = cfg["g0"]
    Lmax = g0["max_lag"]
    zt = to_t(P.z, dev)
    res = []
    for p in plan.g0_pos:
        st = clean_states[int(p)]
        seg = P.z[p:p + Lmax + 1].copy()
        segB = seg.copy()
        ch = plan.g0_chans[p]
        segB[0, ch] += g0["impulse_u"] * P.u[ch]
        sA = tuple(s.clone() if torch.is_tensor(s) else s for s in st)
        pa, _, _ = run(model, to_t(seg, dev)[None], st)
        pa2, _, _ = run(model, to_t(seg, dev)[None], sA)
        pb, _, _ = run(model, to_t(segB, dev)[None], st)
        # preds index l = forecast produced at input p+l; lag l>=1 has clean input, impulse only in state
        Rl = (pb[0, 1:] - pa[0, 1:]).abs().mean(-1).cpu().numpy()       # lags 1..Lmax
        nl = (pa2[0, 1:] - pa[0, 1:]).abs().mean(-1).cpu().numpy()
        res.append((int(p), Rl, nl))
    return res


def h05_from_response(Rl, floor, ref_lags, unstable_factor):
    """Returns (h05, status). status in {ok, censored, not_measurable, unstable}."""
    Rref = float(Rl[:ref_lags].max())
    if not (0.05 * Rref > floor):
        return 0, "not_measurable"
    if Rl[ref_lags:].size and float(Rl[ref_lags:].max()) > unstable_factor * Rref:
        return 0, "unstable"
    above = np.where(Rl >= 0.05 * Rref)[0]
    last = int(above.max()) + 1  # lag index (1-based) of last exceedance
    if last >= len(Rl):
        return len(Rl), "censored"
    return last + 1, "ok"


def evaluate_fit(model, name, P, plan, cfg, dev, sig, log=print):
    """Run G0 (persistent arm), drift episodes and sentinels for both arms of one fit.
    Returns dict with g0 rows, episode rows, sentinel rows, divergence flag."""
    R = cfg["models"]["reset_period_R"]
    ucfg, scfg = cfg["utility"], cfg["sentinel"]
    E, Lc = ucfg["eval_len"], ucfg["calibration_len"]
    wb = cfg["eval"]["window_batch_titans"] if name == "titans" else cfg["eval"]["window_batch"]
    zt = to_t(P.z, dev)
    N = P.z.shape[0]
    has_persist = name in ("mlstm", "gdeltanet", "titans", "lstm")
    arms = (["persistent"] if has_persist else []) + (["reset"] if name != "window_only" else ["single"])
    out = dict(g0=[], episodes=[], sentinel=[], diverged=False, stream_state_norm_max=None)

    # ---- persistent clean run through fit + stream, capturing states at every fork time
    clean_pred = None
    if has_persist:
        caps = set(plan.g0_pos.tolist())
        for f, t0s in plan.onsets.items():
            caps |= set(t0s.tolist())
        Pc, states, mx = run_capture(model, zt, model.init_state(1, dev), 0, N - 1, caps)
        clean_pred = torch.cat([torch.full((1, P.z.shape[1]), float("nan"), device=dev), Pc], 0)  # index tau
        out["stream_state_norm_max"] = mx
        if (not math.isfinite(mx)) or (mx > cfg["stability"]["state_norm_blowup_factor"] * max(sig["train_norm"], 1e-6)) \
                or (not torch.isfinite(Pc[P.fit_end:]).all()):
            out["diverged"] = True
        # ---- G0
        for p, Rl, nl in g0_response(model, P, plan, cfg, dev, states):
            out["g0"].append(dict(pos=p, R=Rl, null=nl))

    # ---- drift episodes
    for f, t0s in plan.onsets.items():
        for arm in arms:
            sigma = sig[arm]
            for i, t0 in enumerate(t0s):
                t0 = int(t0)
                lo = t0 - Lc - R                      # segment start (enough history for windows)
                seg = P.z[lo:t0 + E + 64].copy()
                ch, sg = plan.chans[(f, i)]
                segD = apply_drift(seg, t0 - lo, f, ch, sg, cfg)
                zD = to_t(segD, dev)
                taus_cal = np.arange(t0 - Lc, t0)
                taus_ev = np.arange(t0, t0 + E)
                if arm == "persistent":
                    st = states[t0]
                    pb, st_b, _ = run(model, zD[None, t0 - lo:t0 - lo + E - 1], st)
                    pred_ev = torch.cat([clean_pred[t0:t0 + 1], pb[0]], 0)
                    pred_cal = clean_pred[t0 - Lc:t0]
                else:
                    pr = windowed_preds(model, zD, np.concatenate([taus_cal, taus_ev]) - 1 - lo, R, wb)
                    pred_cal, pred_ev = pr[:Lc], pr[Lc:]
                obs_cal = zD[taus_cal - lo]; obs_ev = zD[taus_ev - lo]
                s_cal = scores_from(pred_cal, obs_cal, sigma).cpu().numpy()
                s_ev = scores_from(pred_ev, obs_ev, sigma).cpu().numpy()
                thr = float(np.quantile(s_cal, ucfg["threshold_quantile"]))
                fpr = float((s_ev > thr).mean())
                out["episodes"].append(dict(family=f, ep=i, arm=arm, t0=t0, thr=thr, fpr=fpr,
                                            fpr_late=float((s_ev[E // 2:] > thr).mean())))
                # ---- sentinels (forked, scored, discarded)
                Ls = scfg["event_window"]
                for kind, off in scfg["offsets"].items():
                    ts = t0 + off
                    rng = np.random.default_rng([scfg["seed"], i, off, zlib.crc32(f.encode())])
                    donor = None
                    if kind == "corr_break":
                        d0 = plan.sent_donor[(f, i)]
                        donor = P.z[d0:d0 + Ls]
                    sch = plan.sent_chans[(f, i, kind)]
                    segS = apply_sentinel(segD, ts - lo, kind, sch, P.u, cfg, rng, donor)
                    zS = to_t(segS, dev)
                    taus_s = np.arange(ts, ts + Ls)
                    if arm == "persistent":
                        st_ts = _state_after(model, st, zD[None, t0 - lo:ts - lo])
                        ps, _, _ = run(model, zS[None, ts - lo:ts - lo + Ls - 1], st_ts)
                        pred_s = torch.cat([pred_ev[ts - t0:ts - t0 + 1], ps[0]], 0)
                    else:
                        pred_s = windowed_preds(model, zS, taus_s - 1 - lo, R, wb)
                    ev = float(scores_from(pred_s, zS[taus_s - lo], sigma).max())
                    det = sentinel_detection(s_cal, s_ev, ev, cfg)
                    out["sentinel"].append(dict(family=f, ep=i, arm=arm, kind=kind, ts=ts, **det))
    return out


@torch.no_grad()
def _state_after(model, st, z):
    s = tuple(x.clone() if torch.is_tensor(x) else x for x in st)
    if z.shape[1] == 0:
        return s
    _, s, _ = run(model, z, s)
    return s


def sigmas(model, name, P, cfg, dev, train_norm):
    zt = to_t(P.z, dev)
    r = val_residuals(model, name, zt, P, cfg["models"]["reset_period_R"], dev, cfg["eval"]["window_batch"])
    sig = {k: torch.clamp(v.std(0), min=1e-3) for k, v in r.items()}
    mse = {k: float((v ** 2).mean()) for k, v in r.items()}
    sig["train_norm"] = train_norm
    return sig, mse


# ============================================================================ kNN-append reference
@torch.no_grad()
def knn_evaluate(P, plan, cfg, dev):
    """Explicit-memory reference (report only). Persistent: bank = fit-train windows (stride s)
    + every scored window, entries younger than `excl` steps are ignored. Reset: fit-train bank only."""
    kc = cfg["knn"]
    w, excl, stride = kc["window"], kc["exclusion"], kc["bank_stride"]
    zt = to_t(P.z, dev)
    def feats(z, ends):
        idx = (np.asarray(ends)[:, None] - w + 1) + np.arange(w)[None]
        return z[torch.as_tensor(idx, device=dev)].flatten(1)
    base_ends = np.arange(w - 1, P.tr_end, stride)
    Fb = feats(zt, base_ends)
    ucfg, scfg = cfg["utility"], cfg["sentinel"]
    E, Lc = ucfg["eval_len"], ucfg["calibration_len"]
    rows, srows = [], []

    def nn_dist(Q, q_end, extra, extra_end):
        d = torch.cdist(Q, Fb).min(1).values
        if extra is not None and extra.shape[0]:
            D = torch.cdist(Q, extra)
            ok = torch.as_tensor(extra_end[None, :] <= (q_end[:, None] - excl), device=dev)
            D = torch.where(ok, D, torch.full_like(D, float("inf")))
            d = torch.minimum(d, D.min(1).values)
        return d

    for f, t0s in plan.onsets.items():
        for i, t0 in enumerate(t0s):
            t0 = int(t0); lo = t0 - Lc - w - GRID
            seg = P.z[lo:t0 + E + 64]
            ch, sg = plan.chans[(f, i)]
            segD = apply_drift(seg, t0 - lo, f, ch, sg, cfg)
            zD = to_t(segD, dev)
            taus = np.arange(t0 - Lc, t0 + E)
            clean_hist_ends = np.arange(P.fit_end, t0)
            Fh = feats(zt, clean_hist_ends)                # clean stream windows ending before t0
            Fe = feats(zD, np.arange(t0, t0 + E) - lo)      # drifted windows (episode)
            Qf = feats(zD, taus - lo)
            for arm in ("persistent", "reset"):
                if arm == "persistent":
                    extra = torch.cat([Fh, Fe], 0)
                    extra_end = np.concatenate([clean_hist_ends, np.arange(t0, t0 + E)])
                    s = nn_dist(Qf, taus, extra, extra_end).cpu().numpy()
                else:
                    s = nn_dist(Qf, taus, None, None).cpu().numpy()
                s_cal, s_ev = s[:Lc], s[Lc:]
                thr = float(np.quantile(s_cal, ucfg["threshold_quantile"]))
                rows.append(dict(family=f, ep=i, arm=arm, t0=t0, thr=thr, fpr=float((s_ev > thr).mean()),
                                 fpr_late=float((s_ev[E // 2:] > thr).mean())))
                for kind, off in scfg["offsets"].items():
                    ts = t0 + off
                    rng = np.random.default_rng([scfg["seed"], i, off, zlib.crc32(f.encode())])
                    donor = P.z[plan.sent_donor[(f, i)]:plan.sent_donor[(f, i)] + scfg["event_window"]] if kind == "corr_break" else None
                    segS = apply_sentinel(segD, ts - lo, kind, plan.sent_chans[(f, i, kind)], P.u, cfg, rng, donor)
                    zS = to_t(segS, dev)
                    tq = np.arange(ts, ts + scfg["event_window"])
                    Qs = feats(zS, tq - lo)
                    if arm == "persistent":
                        ends_e = np.arange(t0, ts + scfg["event_window"])
                        Fse = feats(zS, ends_e - lo)  # drift windows then sentinel windows (fork)
                        extra = torch.cat([Fh, Fse], 0)
                        extra_end = np.concatenate([clean_hist_ends, ends_e])
                        ev = float(nn_dist(Qs, tq, extra, extra_end).max())
                    else:
                        ev = float(nn_dist(Qs, tq, None, None).max())
                    det = sentinel_detection(s_cal, s_ev, ev, cfg)
                    srows.append(dict(family=f, ep=i, arm=arm, kind=kind, ts=ts, **det))
    return rows, srows
