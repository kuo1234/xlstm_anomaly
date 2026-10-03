"""Step 1a.1 (issue #15 comment 5955307476): three cheap mechanism diagnostics on the Step 1a pilot.  Exploratory.

A. W2 decay-matched no-write.  W2 gains decay(L) = apply f^L without adding v k^T.
   M1a arms: write / decay_only / skip.   Primary utility = write - decay_only.
   M1b arms: C (skip, as Step 1a) and Cdec (block the input write, keep the decay).
B. W1 neighbour provenance (burst and spike, every Delta, B arm): share of A1 / M0 / gap entries in the top-5,
   max similarity to A1 entries, the 5th-best non-A1 similarity (the bar A1 entries must beat), top-1 source and
   its time distance.  Causal companion arms Bng/Dng: identical to B/D but the clean gap is NOT written
   (W2: decay only), so 'clean gap entries displace A1' can be tested directly.
C. Second phi (phi2): fixed PCA whitening of the 8-step window fitted on the M0 (fit-train) windows, top 64
   components, then L2 normalisation.  Signed, data-derived, untrained, not forced non-negative.
   Under phi2 the W2 normalizer read max(|n.q|,1) is not meaningful (n.q crosses 0), so W2 uses
   the count-normalised Hebbian read  M(q) = d_k * C q / c,  c <- f c + 1  (for whitened isotropic keys this is the
   cross-covariance / Hebbian linear-regression estimator).  W1 (cosine kNN) and W3 (delta rule) are unchanged.
   phi2 has no random component, so it gives 3 units (machines), not 9.
   W2s turned out not to be a valid normal reference under phi2 (calibration error 3-46, benign normal writes raise
   FPR), so phi kind 'pca_w2p' adds W2 read variants that apply a fixed positive feature map INSIDE W2 to the same
   signed phi2 key (linear-attention style) and keep the mLSTM normalizer read:
     W2p_split: [relu(k), relu(-k)];   W2p_elu: elu(sqrt(d_k) k) + 1  (Katharopoulos et al. 2020 feature map).
Everything else (stream, onsets, faults, admission segments, guards, scores) is identical to Step 1a.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p10_gl1_core import apply_drift, load_train_split, make_plan, prepare  # noqa: E402
from p10_step1a_oracle import CFG1A, W1, W2, W3, Phi, fault_dev, m1b_plan, scores  # noqa: E402


# ============================================================================ phi2
class PhiPCA:
    def __init__(self, z, ts_train, w, dk):
        self.w = w
        X = self.raw(z, ts_train)
        self.mu = X.mean(0)
        _, S, Vt = np.linalg.svd(X - self.mu, full_matrices=False)
        self.P = Vt[:dk].T / (S[:dk] / np.sqrt(len(X)))         # whitening
        self.explained = float((S[:dk] ** 2).sum() / (S ** 2).sum())

    def raw(self, z, ts):
        ts = np.asarray(ts)
        idx = ts[:, None] - self.w + np.arange(self.w)[None]
        return z[idx].reshape(len(ts), -1)

    def __call__(self, z, ts):
        F = (self.raw(z, ts) - self.mu) @ self.P
        return F / (np.linalg.norm(F, axis=1, keepdims=True) + 1e-9)


# ============================================================================ operators with decay / provenance
class W2D(W2):
    def decay(self, L):
        self.C = self.f ** L * self.C
        self.n = self.f ** L * self.n


class W2S:
    """Count-normalised Hebbian (signed keys): C <- f C + v k^T, c <- f c + 1, M(q) = d_k C q / c."""

    def __init__(self, dk, dv, f):
        self.f, self.dk, self.C, self.c = f, dk, np.zeros((dv, dk)), 0.0

    def write(self, K, V, **kw):
        L = len(K)
        wts = self.f ** np.arange(L - 1, -1, -1.0)
        self.C = self.f ** L * self.C + (V * wts[:, None]).T @ K
        self.c = self.f ** L * self.c + wts.sum()

    def decay(self, L):
        self.C = self.f ** L * self.C
        self.c = self.f ** L * self.c

    def read(self, Q):
        return self.dk * (Q @ self.C.T) / max(self.c, 1e-12)

    def copy(self):
        m = W2S(self.dk, self.C.shape[0], self.f)
        m.C, m.c = self.C.copy(), self.c
        return m


class W1P(W1):
    """Append/kNN with provenance tags: src 0 = M0, 1 = A1 admission segment, 2 = clean gap / benign segment."""

    def __init__(self, k=5):
        super().__init__(k)
        self.src, self.tt = np.zeros(0, int), np.zeros(0, int)

    def write(self, K, V, src=0, t=None):
        super().write(K, V)
        self.src = np.concatenate([self.src, np.full(len(K), src)])
        self.tt = np.concatenate([self.tt, np.asarray(t if t is not None else np.full(len(K), -1))])

    def copy(self):
        m = W1P(self.k)
        m.K, m.V, m.src, m.tt = self.K, self.V, self.src, self.tt
        return m

    def provenance(self, Q, tq):
        S = Q @ self.K.T
        idx = np.argpartition(-S, self.k, axis=1)[:, :self.k]
        src = self.src[idx]
        a1 = self.src == 1
        top1 = idx[np.arange(len(Q)), np.argmax(S[np.arange(len(Q))[:, None], idx], 1)]
        Snon = np.where(a1[None], -np.inf, S)
        kth_non = -np.partition(-Snon, self.k - 1, axis=1)[:, self.k - 1]
        out = dict(frac_A1=float((src == 1).mean()), frac_M0=float((src == 0).mean()),
                   frac_gap=float((src == 2).mean()),
                   sim_A1_max=float(S[:, a1].max(1).mean()) if a1.any() else np.nan,
                   sim_M0_max=float(S[:, self.src == 0].max(1).mean()),
                   sim_gap_max=float(S[:, self.src == 2].max(1).mean()) if (self.src == 2).any() else np.nan,
                   sim_nonA1_kth=float(kth_non.mean()),
                   top1_A1=float((self.src[top1] == 1).mean()), top1_gap=float((self.src[top1] == 2).mean()),
                   top1_dt_median=float(np.median(tq - self.tt[top1])))
        return out


class FeatW2(W2D):
    """W2 (Hebbian + mLSTM normalizer) with a fixed positive feature map applied INSIDE the operator to the shared
    signed key (linear-attention style).  'split': [relu(k), relu(-k)];  'elu': elu(sqrt(d) k) + 1."""

    def __init__(self, dk, dv, f, fmap):
        self.fmap, self.dk0 = fmap, dk
        super().__init__(2 * dk if fmap == "split" else dk, dv, f)

    def _phi(self, K):
        if self.fmap == "split":
            return np.concatenate([np.maximum(K, 0), np.maximum(-K, 0)], 1)
        x = np.sqrt(self.dk0) * K
        return np.where(x > 0, x + 1.0, np.exp(x))

    def write(self, K, V, **kw):
        super().write(self._phi(K), V)

    def read(self, Q):
        return super().read(self._phi(Q))


def decay(m, L):
    if hasattr(m, "decay") and L > 0:
        m.decay(L)


def make_ops(phi_kind, dk, dv, k):
    if phi_kind == "relu":
        return {"W1": W1P(k), "W2_f1": W2D(dk, dv, 1.0), "W2_f0995": W2D(dk, dv, 0.995),
                "W3_b01": W3(dk, dv, 0.1), "W3_b05": W3(dk, dv, 0.5)}
    if phi_kind == "pca_w2p":
        return {"W2p_split_f1": FeatW2(dk, dv, 1.0, "split"), "W2p_split_f0995": FeatW2(dk, dv, 0.995, "split"),
                "W2p_elu_f1": FeatW2(dk, dv, 1.0, "elu"), "W2p_elu_f0995": FeatW2(dk, dv, 0.995, "elu")}
    return {"W1": W1P(k), "W2s_f1": W2S(dk, dv, 1.0), "W2s_f0995": W2S(dk, dv, 0.995),
            "W3_b01": W3(dk, dv, 0.1), "W3_b05": W3(dk, dv, 0.5)}


def _w(m, K, V, src, t):
    if isinstance(m, W1P):
        m.write(K, V, src=src, t=t)
    else:
        m.write(K, V)


# ============================================================================ M1a (decay-matched)
def run_m1a(P, plan, phi, mems0, cfg, gcfg):
    c = cfg["m1a"]
    w, Ls, G, E, Lc = phi.w, c["seg_len"], c["guard"], c["eval_len"], c["calib_len"]
    rows = []
    for fam in c["families"]:
        for i, t0 in enumerate(plan.onsets[fam]):
            t0 = int(t0)
            lo, hi = t0 - Lc - w - 1, t0 + Ls + G + E + 1
            ch, sg = plan.chans[(fam, i)]
            seg = apply_drift(P.z[lo:hi], t0 - lo, fam, ch, sg, gcfg)
            t_cal, t_seg = np.arange(t0 - Lc, t0) - lo, np.arange(t0, t0 + Ls) - lo
            t_ev = np.arange(t0 + Ls + G, t0 + Ls + G + E) - lo
            Kc, Ks, Ke = phi(seg, t_cal), phi(seg, t_seg), phi(seg, t_ev)
            for name, m0 in mems0.items():
                s_cal = scores(m0, Kc, seg[t_cal])
                thr = float(np.quantile(s_cal, c["q"]))
                r = dict(family=fam, ep=i, t0=t0, op=name, thr=thr, cal_mean=float(s_cal.mean()))
                for arm in ("skip", "decay_only", "write"):
                    m = m0.copy()
                    if arm == "write":
                        _w(m, Ks, seg[t_seg], 2, t_seg + lo)
                    elif arm == "decay_only":
                        decay(m, Ls)
                    s = scores(m, Ke, seg[t_ev])
                    r[f"fpr_{arm}"], r[f"mean_{arm}"] = float((s > thr).mean()), float(s.mean())
                rows.append(r)
    return rows


# ============================================================================ M1b (+Cdec, no-gap, provenance)
def run_m1b(P, eps, phi, mems0, cfg):
    c = cfg["m1b"]
    w, La, G = phi.w, c["a_len"], c["guard"]
    rows, prov = [], []
    for (fault, i), e in eps.items():
        ta = e["ta"]
        lo, hi = ta - w - 1, ta + La + max(c["deltas"]) + La + w + 2
        clean = P.z[lo:hi].astype(np.float64)
        faulty = clean.copy()
        faulty[ta - lo:ta - lo + La] += fault_dev(P, e, fault, La, cfg)
        t_a1 = np.arange(ta, ta + La + w) - lo
        KB, VB, KD, VD = phi(faulty, t_a1), faulty[t_a1], phi(clean, t_a1), clean[t_a1]
        for dl in c["deltas"]:
            ta2 = ta + La + dl
            t_gap = np.arange(ta + La + w, ta2 - G) - lo
            Kg, Vg = phi(clean, t_gap), clean[t_gap]
            t2 = np.arange(ta2, ta2 + La) - lo
            K0, V0 = phi(clean, t2), clean[t2]
            A2 = {}
            for var in ("identical", "variant"):
                s2 = clean.copy()
                s2[ta2 - lo:ta2 - lo + La] += fault_dev(P, e, fault, La, cfg, variant=(var == "variant"))
                A2[var] = (phi(s2, t2), s2[t2])
            for name, m0 in mems0.items():
                for arm in ("B", "D", "C", "Cdec", "B30", "D30", "Bng", "Dng"):
                    if arm == "Cdec" and not hasattr(m0, "decay"):
                        continue                                   # identical to C for W1/W3
                    m = m0.copy()
                    if arm in ("B", "Bng"):
                        _w(m, KB, VB, 1, t_a1 + lo)
                    elif arm in ("D", "Dng"):
                        _w(m, KD, VD, 1, t_a1 + lo)
                    elif arm == "B30":
                        _w(m, KB[:La], VB[:La], 1, t_a1[:La] + lo)
                    elif arm == "D30":
                        _w(m, KD[:La], VD[:La], 1, t_a1[:La] + lo)
                    elif arm == "Cdec":
                        decay(m, len(t_a1))
                    if arm in ("Bng", "Dng"):
                        decay(m, len(t_gap))                       # gap writes blocked, decay kept
                    elif len(t_gap):
                        _w(m, Kg, Vg, 2, t_gap + lo)
                    s_base = scores(m, K0, V0)
                    for var, (Kq, Vq) in A2.items():
                        lift = scores(m, Kq, Vq) - s_base
                        rows.append(dict(fault=fault, ep=i, ta=ta, delta=dl, op=name, arm=arm, a2=var,
                                         lift=float(lift.mean()), base_mean=float(s_base.mean())))
                        if name == "W1" and arm in ("B", "Bng", "D"):
                            prov.append(dict(fault=fault, ep=i, delta=dl, arm=arm, a2=var,
                                             **m.provenance(Kq, t2 + lo)))
    return rows, prov


# ============================================================================ driver
def run_one(machine, phi_kind, seed, data_dir, gcfg, cfg=CFG1A):
    x = load_train_split(str(Path(data_dir) / f"{machine}_train.txt"))
    P = prepare(x, gcfg)
    C = P.z.shape[1]
    t_tr = np.arange(cfg["w"], P.tr_end)
    if phi_kind == "relu":
        phi, dk, extra = Phi(C, cfg["w"], cfg["dk"], seed), cfg["dk"], {}
    else:
        phi = PhiPCA(P.z, t_tr, cfg["w"], 64)
        dk, extra = 64, {"pca_explained": phi.explained}
    K0, V0 = phi(P.z, t_tr), P.z[t_tr].astype(np.float64)
    t0 = time.time()
    mems0 = make_ops(phi_kind, dk, C, cfg["knn_k"])
    for m in mems0.values():
        _w(m, K0, V0, 0, t_tr)
    plan = make_plan(P, gcfg, machine)
    r1a = run_m1a(P, plan, phi, mems0, cfg, gcfg)
    r1b, prov = run_m1b(P, m1b_plan(P, cfg, machine), phi, mems0, cfg)
    for r in r1a + r1b + prov:
        r.update(machine=machine, phi=phi_kind, phi_seed=seed, **extra)
    print(f"{machine} {phi_kind} seed={seed} {time.time() - t0:.0f}s", flush=True)
    return r1a, r1b, prov


def _job(args):
    machine, phi_kind, seed, data_dir, gcfg_path = args
    return run_one(machine, phi_kind, seed, data_dir, yaml.safe_load(open(gcfg_path)))


if __name__ == "__main__":
    import argparse
    from multiprocessing import Pool

    import pandas as pd
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--gl1-config", default=str(Path(__file__).resolve().parents[1] / "configs/p10_gl1_config.yaml"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--procs", type=int, default=12)
    ap.add_argument("--only", default=None, help="restrict to one phi kind (relu | pca | pca_w2p)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(m, "relu", s, a.data_dir, a.gl1_config) for m in CFG1A["machines"] for s in CFG1A["phi_seeds"]]
    jobs += [(m, "pca", 0, a.data_dir, a.gl1_config) for m in CFG1A["machines"]]
    jobs += [(m, "pca_w2p", 0, a.data_dir, a.gl1_config) for m in CFG1A["machines"]]
    if a.only:
        jobs = [j for j in jobs if j[1] == a.only]
    with Pool(a.procs) as pool:
        res = pool.map(_job, jobs)
    pd.DataFrame([r for x in res for r in x[0]]).to_csv(out / "m1a_diag_raw.csv.gz", index=False)
    pd.DataFrame([r for x in res for r in x[1]]).to_csv(out / "m1b_diag_raw.csv.gz", index=False)
    pd.DataFrame([r for x in res for r in x[2]]).to_csv(out / "w1_provenance_raw.csv.gz", index=False)
    json.dump({"cfg": CFG1A, "phi2": "PCA-whitened 8-step window, 64 comps, L2-normalised", "jobs": len(jobs)},
              open(out / "run_config.json", "w"), indent=1, default=str)
