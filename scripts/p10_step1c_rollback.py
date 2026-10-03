"""Step 1c (issue #15 comment 5965829950): oracle rollback-granularity pilot.  Exploratory, no seal.

Stream as Step 1b: benign regime from t0 (ramp primary, level cross-check), A1 burst at ta = t0+128.
History written after M0 (in order):
    1. admitted segment [ta, ta+L), L in {30, 38, 46}, from the actual stream (regime + fault)
    2. delay: the next `delay` steps of the actual stream (delay in {0, 64}), written as normal
    3. rollback (oracle), then the memory is frozen and evaluated.
Step categories (relative to ta): fault-value [0, 30), recovery-key [30, 38) (value clean, key contains A1), benign.
Rollback targets:
    R0          nothing removed
    R_fault     remove fault-value steps
    R_fault_rec remove fault-value + recovery-key steps (wherever written: segment or delay)
    R_all       remove the whole admitted segment (delay writes stay)
Clean counterfactual target T ("D"): the same segment + delay steps written from the matched stream without the fault.
Rollback semantics per operator:
    W1 append      delete the target entries by provenance tag (== replay omitting them; verified in tests)
    W2 Hebbian     analytical subtraction from a write ledger: C -= f^age v k^T, n -= f^age k (age = number of
                   later writes).  This equals replay with the removed writes turned into decay-only steps
                   (verified); its functional distance to replay-omitting ('never written') is also reported.
    W3 delta rule  exact oracle rollback = checkpoint at M0 + replay of the kept writes (cost = #replayed writes)
Per-rollback clean reference T_R = the same rollback applied to the clean history (clean versions of the kept
steps).  lift_R/lift_T = (lift_R/lift_TR) x (lift_TR/lift_T): contamination left behind x information removed.
Endpoints (frozen memory after rollback):
    residual_func  sum mean_q ||M_R(q) - M_TR(q)|| / sum mean_q ||M_R0(q) - M_T(q)||  (sums over episodes; probe keys =
                   eval window + A2 windows); 1 = contamination untouched, 0 = none left in the kept writes
    residual_param ||C_R - C_TR|| / ||C_R0 - C_T||  (W2, W3)
    utility        FPR / mean score on [ta+126, ta+638) of the A2-free stream (threshold q0.99 of M0 on [t0-1024, t0))
    A2             paired lift at Delta in {128, 256} (A2 at ta+30+Delta, after the latest write + 16-step guard),
                   identical burst and x0.6 variant; ratio = lift_R / lift_T
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p10_gl1_core import apply_drift, load_train_split, make_plan, prepare  # noqa: E402
from p10_step1a_oracle import W1, W3, Phi, scores  # noqa: E402
from p10_step1a1_diag import W2D, FeatW2, PhiPCA  # noqa: E402
from p10_step1b_boundary import CFG1B, make_ops  # noqa: E402

CFG1C = dict(CFG1B, seg_L=[30, 38, 46], delays=[0, 64], deltas=[128, 256], eval_start=126, eval_len=512,
             rollbacks=["R0", "R_fault", "R_fault_rec", "R_all"])


def category(rel, La, w):
    rel = np.asarray(rel)
    return np.where((rel >= 0) & (rel < La), "fault", np.where((rel >= La) & (rel < La + w), "recovery", "benign"))


def keep_mask(rb, cat, in_seg):
    if rb == "R0":
        return np.ones(len(cat), bool)
    if rb == "R_fault":
        return cat != "fault"
    if rb == "R_fault_rec":
        return (cat != "fault") & (cat != "recovery")
    if rb == "R_all":
        return ~in_seg
    raise ValueError(rb)


def w2_subtract(m_full, K, V, keep):
    """Analytical removal of the writes with keep == False from a W2 state that wrote K, V in order."""
    m = m_full.copy()
    F = m._phi(K) if isinstance(m, FeatW2) else K
    age = np.arange(len(K) - 1, -1, -1.0)                 # number of later writes
    wts = np.where(keep, 0.0, m.f ** age)
    m.C = m.C - (V * wts[:, None]).T @ F
    m.n = m.n - wts @ F
    return m


def w2_decay_replay(m0, K, V, keep):
    """Replay where removed writes become decay-only steps (reference for w2_subtract)."""
    m = m0.copy()
    for j in range(len(K)):
        if keep[j]:
            m.write(K[j:j + 1], V[j:j + 1])
        else:
            m.decay(1)
    return m


def replay(m0, K, V, keep):
    m = m0.copy()
    if keep.any():
        m.write(K[keep], V[keep])
    return m


def rollback(name, m0, m_full, K, V, keep):
    if name.startswith("W2"):
        return w2_subtract(m_full, K, V, keep)
    return replay(m0, K, V, keep)                         # W1: tag deletion == replay; W3: checkpoint + replay


def run_unit(machine, kind, seed, data_dir, gcfg, cfg=CFG1C):
    x = load_train_split(str(Path(data_dir) / f"{machine}_train.txt"))
    P = prepare(x, gcfg)
    C = P.z.shape[1]
    w, La = cfg["w"], cfg["a_len"]
    t_tr = np.arange(w, P.tr_end)
    if kind == "relu":
        phi, dk = Phi(C, w, cfg["dk_relu"], seed), cfg["dk_relu"]
    else:
        phi, dk = PhiPCA(P.z, t_tr, w, cfg["dk_pca"]), cfg["dk_pca"]
    K0, V0 = phi(P.z, t_tr), P.z[t_tr].astype(np.float64)
    mems0 = make_ops(kind, dk, C, cfg["knn_k"])
    for m in mems0.values():
        m.write(K0, V0)
    plan = make_plan(P, gcfg, machine)
    base = int(hashlib.sha256(machine.encode()).hexdigest()[:8], 16)
    rows, t_start = [], time.time()
    for fam in cfg["families"]:
        for i, t0 in enumerate(plan.onsets[fam]):
            t0 = int(t0)
            rng = np.random.default_rng([cfg["seed"], base, i, 0 if fam == "ramp" else 1])   # same draws as Step 1b
            ch = rng.choice(C, size=min(cfg["burst_channels"], C), replace=False)
            sg = rng.choice([-1.0, 1.0], size=len(ch))
            ta = t0 + cfg["fault_offset"]
            lo = t0 - cfg["calib_len"] - w - 1
            hi = ta + cfg["eval_start"] + cfg["eval_len"] + 2
            dch, dsg = plan.chans[(fam, i)]
            clean = apply_drift(P.z[lo:hi].astype(np.float64), t0 - lo, fam, dch, dsg, gcfg)
            dev = np.zeros((La, C))
            dev[:, ch] = cfg["burst_sigma"] * sg[None]
            stream = clean.copy()
            stream[ta - lo:ta - lo + La] += dev
            t_cal = np.arange(t0 - cfg["calib_len"], t0) - lo
            t_ev = np.arange(ta + cfg["eval_start"], ta + cfg["eval_start"] + cfg["eval_len"]) - lo
            Kc, Ke, Ve = phi(clean, t_cal), phi(stream, t_ev), stream[t_ev]
            A2q, probes = {}, [Ke]
            for dl in cfg["deltas"]:
                ta2 = ta + La + dl
                t2 = np.arange(ta2, ta2 + La) - lo
                Kb, Vb = phi(stream, t2), stream[t2]
                probes.append(Kb)
                for var, sc in (("identical", 1.0), ("variant", cfg["variant_scale"])):
                    s2 = stream.copy()
                    s2[ta2 - lo:ta2 - lo + La] += sc * dev
                    Kq = phi(s2, t2)
                    A2q[(dl, var)] = ((Kb, Vb), (Kq, s2[t2]))
                    probes.append(Kq)
            Q = np.concatenate(probes)
            for name, m0 in mems0.items():
                thr = float(np.quantile(scores(m0, Kc, clean[t_cal]), cfg["q"]))

                def readout(m):
                    s = scores(m, Ke, Ve)
                    out = dict(fpr=float((s > thr).mean()), mean=float(s.mean()))
                    for (dl, var), ((Kb, Vb), (Kq, Vq)) in A2q.items():
                        out[f"lift_{dl}_{var}"] = float((scores(m, Kq, Vq) - scores(m, Kb, Vb)).mean())
                    return out
                for L in cfg["seg_L"]:
                    for delay in cfg["delays"]:
                        tw = np.arange(ta, ta + L + delay)                       # absolute write times, in order
                        in_seg = tw < ta + L
                        cat = category(tw - ta, La, w)
                        KB, VB = phi(stream, tw - lo), stream[tw - lo]
                        KT, VT = phi(clean, tw - lo), clean[tw - lo]
                        mT = replay(m0, KT, VT, np.ones(len(tw), bool))
                        mB = replay(m0, KB, VB, np.ones(len(tw), bool))
                        PT = mT.read(Q)
                        d0 = np.linalg.norm(mB.read(Q) - PT, axis=1).mean()
                        rT = readout(mT)
                        rows.append(dict(family=fam, ep=i, op=name, L=L, delay=delay, rollback="T_clean", thr=thr,
                                         n_removed=0, n_replayed=len(tw), res_den=float(d0), **rT))
                        for rb in cfg["rollbacks"]:
                            keep = keep_mask(rb, cat, in_seg)
                            mR = rollback(name, m0, mB, KB, VB, keep)
                            mTR = rollback(name, m0, mT, KT, VT, keep)     # same rollback on the clean history
                            PR, PTR = mR.read(Q), mTR.read(Q)
                            row = dict(family=fam, ep=i, op=name, L=L, delay=delay, rollback=rb, thr=thr,
                                       n_removed=int((~keep).sum()),
                                       n_replayed=int(keep.sum()) if name.startswith("W3") else 0,
                                       res_num=float(np.linalg.norm(PR - PTR, axis=1).mean()),   # contamination left
                                       res_den=float(d0),                                         # before rollback
                                       info_num=float(np.linalg.norm(PTR - PT, axis=1).mean()),  # info removed
                                       w2_never_num=np.nan)
                            if not isinstance(mR, W1):
                                row["par_num"] = float(np.linalg.norm(mR.C - mTR.C))
                                row["par_den"] = float(np.linalg.norm(mB.C - mT.C))
                            if name.startswith("W2") and rb != "R0":
                                mN = replay(m0, KB, VB, keep)                    # never written
                                row["w2_never_num"] = float(np.linalg.norm(PR - mN.read(Q), axis=1).mean())
                            row.update(readout(mR))
                            row.update({f"TR_{k}": v for k, v in readout(mTR).items()})
                            rows.append(row)
    for r in rows:
        r.update(machine=machine, phi=kind, phi_seed=seed)
    print(f"{machine} {kind} seed={seed} rows={len(rows)} {time.time() - t_start:.0f}s", flush=True)
    return rows


def _job(a):
    machine, kind, seed, data_dir, gpath = a
    return run_unit(machine, kind, seed, data_dir, yaml.safe_load(open(gpath)))


if __name__ == "__main__":
    import argparse
    from multiprocessing import Pool

    import pandas as pd
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--gl1-config", default=str(Path(__file__).resolve().parents[1] / "configs/p10_gl1_config.yaml"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--procs", type=int, default=12)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(m, "relu", s, a.data_dir, a.gl1_config) for m in CFG1C["machines"] for s in CFG1C["phi_seeds"]]
    jobs += [(m, "pca", 0, a.data_dir, a.gl1_config) for m in CFG1C["machines"]]
    with Pool(a.procs) as pool:
        res = pool.map(_job, jobs)
    pd.DataFrame([r for x in res for r in x]).to_csv(out / "step1c_raw.csv.gz", index=False)
    json.dump({"cfg": CFG1C}, open(out / "run_config.json", "w"), indent=1)
