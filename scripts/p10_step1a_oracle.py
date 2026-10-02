"""Step 1a (P7+P10, issue #15 comment 5954497867): role-matched oracle memory pilot.  Exploratory, no seal.

All memories play the SAME role (normal reference, retrieval prediction); only the write operator differs.
    key   k_t = phi(z[t-w : t])            (w steps ending at t-1; fixed random ReLU features, L2-normalised)
    value v_t = z_t
    score s_t = || v_t - M(k_t) ||_2
Operators (identical k, v, stream, oracle segment):
    W1        append / kNN: bank of (k, v); M(q) = mean v of top-K cosine neighbours (K=5)
    W2_f1     Hebbian + normalizer (mLSTM-style):  C <- f C + v k^T, n <- f n + k;  M(q) = C q / max(|n.q|, 1),  f = 1
    W2_f0995  same, f = 0.995 per write
    W3_b01    delta rule: C <- C + beta (v - C k) k^T, beta = 0.1;  M(q) = C q
    W3_b05    delta rule, beta = 0.5
Every memory starts from M0 = sequential write of the fit-train region [0, tr_end).
Oracle admission a_S in {0,1} gates a whole segment; inside a segment W2/W3 apply their per-step increments in order.

M1a benign-write utility: drift onset t0 (G-L1 plan, families level/ramp/gain/none).  Threshold = q0.99 of M0 scores on
    [t0-1024, t0).  Segment [t0, t0+256) of the drifted stream is written (a=1) or not (a=0); then the memory is frozen and
    the same drifted path is scored on [t0+256+16, t0+256+16+512) (16-step unwritten guard for all operators).
M1b contamination causality: clean stream.  A1 = 30-step fault at ta; admission segment = [ta, ta+30+w) (every step whose
    key or value touches the fault).  B = write that segment from the faulty stream, D = write it from the clean stream,
    C = do not write it.  Diagnostic B30/D30: write only [ta, ta+30) (fault-value steps; the w trailing
    'recovery' steps whose keys contain the fault but whose values are clean are skipped).  Then the clean stream [ta+30+w, ta2-16) is written in all arms (identical), 16-step guard,
    A2 at ta2 = ta+30+Delta scored on frozen memory.  lift = mean_{30 steps} [s(stream + A2) - s(stream)].
    Faults (existing G-L1 injection machinery): spike (sentinel 'spike', 5 ch, 2u) and burst (level 2 sigma, 8 ch, 30 steps).
    A2 identical = same additive deviation as A1;  variant: spike -> same channels, fresh signs; burst -> amplitude x0.6.
Contextual no-memory baselines (M1a only, no write): persistence ||z_t - z_{t-1}||, and RevIN-W1 (window-mean-centred
    keys/values, kNN on the train bank).
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p10_gl1_core import apply_drift, apply_sentinel, grid_positions, load_train_split, make_plan, prepare  # noqa: E402

CFG1A = dict(
    machines=["machine-3-7", "machine-1-6", "machine-2-7"],
    phi_seeds=[11, 22, 33], w=8, dk=128, knn_k=5,
    operators=["W1", "W2_f1", "W2_f0995", "W3_b01", "W3_b05"],
    m1a=dict(families=["level", "ramp", "gain", "none"], seg_len=256, guard=16, eval_len=512, calib_len=1024, q=0.99),
    m1b=dict(faults=["spike", "burst"], a_len=30, deltas=[64, 256, 1024], guard=16, episodes=16, seed=904,
             burst_sigma=2.0, burst_channels=8, variant_burst_scale=0.6),
)


# ============================================================================ keys
class Phi:
    def __init__(self, C, w, dk, seed):
        rng = np.random.default_rng(seed)
        self.w, self.C = w, C
        self.R = rng.standard_normal((w * C, dk)) / np.sqrt(w * C)
        self.b = rng.standard_normal(dk)

    def raw(self, z, ts, center=False):
        ts = np.asarray(ts)
        idx = ts[:, None] - self.w + np.arange(self.w)[None]          # z[t-w .. t-1]
        X = z[idx]                                                      # n, w, C
        m = X.mean(1) if center else None
        if center:
            X = X - m[:, None]
        return X.reshape(len(ts), -1), m

    def __call__(self, z, ts, center=False):
        X, m = self.raw(z, ts, center)
        F = np.maximum(X @ self.R + self.b, 0.0)
        F /= np.linalg.norm(F, axis=1, keepdims=True) + 1e-6
        return (F, m) if center else F


# ============================================================================ memories
class W1:
    def __init__(self, k=5):
        self.k, self.K, self.V = k, None, None

    def write(self, K, V):
        self.K = K.copy() if self.K is None else np.concatenate([self.K, K])
        self.V = V.copy() if self.V is None else np.concatenate([self.V, V])

    def read(self, Q):
        S = Q @ self.K.T
        idx = np.argpartition(-S, self.k, axis=1)[:, :self.k]
        return self.V[idx].mean(1)

    def copy(self):
        m = W1(self.k)
        m.K, m.V = self.K, self.V          # arrays are never mutated in place (write concatenates)
        return m


class W2:
    def __init__(self, dk, dv, f):
        self.f, self.C, self.n = f, np.zeros((dv, dk)), np.zeros(dk)

    def write(self, K, V):
        L = len(K)
        wts = self.f ** np.arange(L - 1, -1, -1.0)                      # closed form of the sequential recurrence
        self.C = self.f ** L * self.C + (V * wts[:, None]).T @ K
        self.n = self.f ** L * self.n + wts @ K

    def read(self, Q):
        return (Q @ self.C.T) / np.maximum(np.abs(Q @ self.n), 1.0)[:, None]

    def copy(self):
        return copy.deepcopy(self)


class W3:
    def __init__(self, dk, dv, beta):
        self.beta, self.C = beta, np.zeros((dv, dk))

    def write(self, K, V):
        C, b = self.C, self.beta
        for k, v in zip(K, V):
            C += b * np.outer(v - C @ k, k)
        self.C = C

    def read(self, Q):
        return Q @ self.C.T

    def copy(self):
        return copy.deepcopy(self)


def make_memory(name, dk, dv, knn_k):
    return {"W1": lambda: W1(knn_k), "W2_f1": lambda: W2(dk, dv, 1.0), "W2_f0995": lambda: W2(dk, dv, 0.995),
            "W3_b01": lambda: W3(dk, dv, 0.1), "W3_b05": lambda: W3(dk, dv, 0.5)}[name]()


def scores(mem, Q, V):
    return np.linalg.norm(V - mem.read(Q), axis=1)


# ============================================================================ M1a
def run_m1a(P, plan, phi, mems0, cfg, gcfg, bases):
    c = cfg["m1a"]
    w, Ls, G, E, Lc = phi.w, c["seg_len"], c["guard"], c["eval_len"], c["calib_len"]
    rows = []
    for fam in c["families"]:
        for i, t0 in enumerate(plan.onsets[fam]):
            t0 = int(t0)
            lo, hi = t0 - Lc - w - 1, t0 + Ls + G + E + 1
            ch, sg = plan.chans[(fam, i)]
            seg = apply_drift(P.z[lo:hi], t0 - lo, fam, ch, sg, gcfg)
            t_cal = np.arange(t0 - Lc, t0) - lo
            t_seg = np.arange(t0, t0 + Ls) - lo
            t_ev = np.arange(t0 + Ls + G, t0 + Ls + G + E) - lo
            Kc, Ks, Ke = phi(seg, t_cal), phi(seg, t_seg), phi(seg, t_ev)
            for name, m0 in mems0.items():
                s_cal = scores(m0, Kc, seg[t_cal])
                thr = float(np.quantile(s_cal, c["q"]))
                s_seg0 = scores(m0, Ks, seg[t_seg])
                s_no = scores(m0, Ke, seg[t_ev])
                m1 = m0.copy()
                m1.write(Ks, seg[t_seg])
                s_wr = scores(m1, Ke, seg[t_ev])
                rows.append(dict(family=fam, ep=i, t0=t0, op=name, thr=thr, cal_mean=float(s_cal.mean()),
                                 fpr_seg_nowrite=float((s_seg0 > thr).mean()),
                                 fpr_nowrite=float((s_no > thr).mean()), fpr_write=float((s_wr > thr).mean()),
                                 mean_nowrite=float(s_no.mean()), mean_write=float(s_wr.mean())))
            # contextual no-memory baselines
            for bname in ("persistence", "revin_W1"):
                if bname == "persistence":
                    f = lambda tt: np.linalg.norm(seg[tt] - seg[tt - 1], axis=1)
                else:
                    def f(tt):
                        Q, m = phi(seg, tt, center=True)
                        return np.linalg.norm((seg[tt] - m) - bases["revin"].read(Q), axis=1)
                s_cal, s_ev = f(t_cal), f(t_ev)
                thr = float(np.quantile(s_cal, c["q"]))
                rows.append(dict(family=fam, ep=i, t0=t0, op=bname, thr=thr, cal_mean=float(s_cal.mean()),
                                 fpr_seg_nowrite=float((f(t_seg) > thr).mean()),
                                 fpr_nowrite=float((s_ev > thr).mean()), fpr_write=np.nan,
                                 mean_nowrite=float(s_ev.mean()), mean_write=np.nan))
    return rows


# ============================================================================ M1b
def m1b_plan(P, cfg, machine):
    c = cfg["m1b"]
    base = int(hashlib.sha256(machine.encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng([c["seed"], base])
    C = P.z.shape[1]
    span = c["a_len"] + max(c["deltas"]) + c["a_len"] + 64
    eps = {}
    for fault in c["faults"]:
        tas = grid_positions(rng, P.fit_end + 64, P.z.shape[0] - span, c["episodes"])
        for i, ta in enumerate(tas):
            if fault == "spike":
                ch = rng.choice(C, size=min(5, C), replace=False)
                xi = rng.choice([-1.0, 1.0], size=(c["a_len"], len(ch)))
                xi2 = rng.choice([-1.0, 1.0], size=(c["a_len"], len(ch)))
                eps[(fault, i)] = dict(ta=int(ta), ch=ch, sg=None, xi=xi, xi2=xi2)
            else:
                ch = rng.choice(C, size=min(c["burst_channels"], C), replace=False)
                eps[(fault, i)] = dict(ta=int(ta), ch=ch, sg=rng.choice([-1.0, 1.0], size=len(ch)), xi=None, xi2=None)
    return eps


def fault_dev(P, e, fault, L, cfg, variant=False):
    """Additive deviation (L, C) of the fault (uses G-L1 sentinel / level machinery semantics)."""
    D = np.zeros((L, P.z.shape[1]))
    if fault == "spike":
        amp = 2.0 * P.u[e["ch"]][None]                  # sentinel 'spike' amp_u = 2
        D[:, e["ch"]] = amp * (e["xi2"] if variant else e["xi"])
    else:
        s = cfg["m1b"]["burst_sigma"] * (cfg["m1b"]["variant_burst_scale"] if variant else 1.0)
        D[:, e["ch"]] = s * e["sg"][None]
    return D


def run_m1b(P, eps, phi, mems0, cfg):
    c = cfg["m1b"]
    w, La, G = phi.w, c["a_len"], c["guard"]
    rows = []
    for (fault, i), e in eps.items():
        ta = e["ta"]
        lo, hi = ta - w - 1, ta + La + max(c["deltas"]) + La + w + 2
        clean = P.z[lo:hi].astype(np.float64)
        faulty = clean.copy()
        faulty[ta - lo:ta - lo + La] += fault_dev(P, e, fault, La, cfg)
        t_a1 = np.arange(ta, ta + La + w) - lo               # admission segment (key or value touches A1)
        K_B, V_B = phi(faulty, t_a1), faulty[t_a1]
        K_D, V_D = phi(clean, t_a1), clean[t_a1]
        n30 = La                                          # diagnostic: fault-value steps only (no recovery keys)
        for dl in c["deltas"]:
            ta2 = ta + La + dl
            t_gap = np.arange(ta + La + w, ta2 - G) - lo     # identical clean writes in all arms
            K_g, V_g = phi(clean, t_gap), clean[t_gap]
            t2 = np.arange(ta2, ta2 + La) - lo
            K0, V0 = phi(clean, t2), clean[t2]
            A2 = {}
            for var in ("identical", "variant"):
                s2 = clean.copy()
                s2[ta2 - lo:ta2 - lo + La] += fault_dev(P, e, fault, La, cfg, variant=(var == "variant"))
                A2[var] = (phi(s2, t2), s2[t2])
            for name, m0 in mems0.items():
                for arm in ("B", "C", "D", "B30", "D30"):
                    m = m0.copy()
                    if arm == "B":
                        m.write(K_B, V_B)
                    elif arm == "D":
                        m.write(K_D, V_D)
                    elif arm == "B30":
                        m.write(K_B[:n30], V_B[:n30])
                    elif arm == "D30":
                        m.write(K_D[:n30], V_D[:n30])
                    if len(t_gap):
                        m.write(K_g, V_g)
                    s_base = scores(m, K0, V0)
                    for var, (Kq, Vq) in A2.items():
                        lift = scores(m, Kq, Vq) - s_base
                        rows.append(dict(fault=fault, ep=i, ta=ta, delta=dl, op=name, arm=arm, a2=var,
                                         lift=float(lift.mean()), lift_max=float(lift.max()),
                                         base_mean=float(s_base.mean())))
    return rows


# ============================================================================ driver
def run_one(machine, seed, data_dir, gcfg, cfg=CFG1A, log=print):
    x = load_train_split(str(Path(data_dir) / f"{machine}_train.txt"))
    P = prepare(x, gcfg)
    C = P.z.shape[1]
    phi = Phi(C, cfg["w"], cfg["dk"], seed)
    t_tr = np.arange(cfg["w"], P.tr_end)
    K0, V0 = phi(P.z, t_tr), P.z[t_tr].astype(np.float64)
    t0 = time.time()
    mems0 = {}
    for name in cfg["operators"]:
        m = make_memory(name, cfg["dk"], C, cfg["knn_k"])
        m.write(K0, V0)
        mems0[name] = m
    Kr, mr = phi(P.z, t_tr, center=True)
    rev = W1(cfg["knn_k"])
    rev.write(Kr, V0 - mr)
    plan = make_plan(P, gcfg, machine)
    r1a = run_m1a(P, plan, phi, mems0, cfg, gcfg, {"revin": rev})
    eps = m1b_plan(P, cfg, machine)
    r1b = run_m1b(P, eps, phi, mems0, cfg)
    for r in r1a + r1b:
        r.update(machine=machine, phi_seed=seed)
    log(f"{machine} seed={seed} C={C} tr_end={P.tr_end} fit_end={P.fit_end} N={P.z.shape[0]} "
        f"rows1a={len(r1a)} rows1b={len(r1b)} {time.time() - t0:.0f}s")
    return r1a, r1b


def _job(args):
    machine, seed, data_dir, gcfg_path = args
    gcfg = yaml.safe_load(open(gcfg_path))
    return run_one(machine, seed, data_dir, gcfg)


if __name__ == "__main__":
    import argparse
    from multiprocessing import Pool

    import pandas as pd
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--gl1-config", default=str(Path(__file__).resolve().parents[1] / "configs/p10_gl1_config.yaml"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--procs", type=int, default=9)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(m, s, a.data_dir, a.gl1_config) for m in CFG1A["machines"] for s in CFG1A["phi_seeds"]]
    with Pool(a.procs) as pool:
        res = pool.map(_job, jobs)
    pd.DataFrame([r for r1a, _ in res for r in r1a]).to_csv(out / "m1a_raw.csv.gz", index=False)
    pd.DataFrame([r for _, r1b in res for r in r1b]).to_csv(out / "m1b_raw.csv.gz", index=False)
    json.dump({"cfg": CFG1A, "gl1_config": a.gl1_config}, open(out / "run_config.json", "w"), indent=1, default=str)
