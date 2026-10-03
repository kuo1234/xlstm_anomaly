"""Step 1b (issue #15 comment 5965080510): mixed-segment / boundary pilot.  Exploratory, oracle segments, no seal.

Stream per episode (G-L1 plan onsets, families ramp [primary] and level [cross-check]):
    t0            onset of the benign new-normal regime (drift 2 sigma on 8 channels; ramp over 512 steps)
    ta = t0+128   A1 burst (level 2 sigma on 8 other-random channels, 30 steps) inside that regime
Memory = M0 (fit-train, as Step 1a) + ONE oracle admission segment [s, s+L); nothing else is written.
    Sweep A: L = 38, s = ta + o,  o in {-16, -8, 0, +8, +16, +30}
    Sweep B: s = ta,  L in {16, 30, 38, 46, 62}
Arms per segment:  B = write the segment from the actual stream (regime + fault);
                   D = write the same steps from the matched stream without the fault (regime only);
                   C = no write (shared by all segments).
Segment composition: benign steps (key and value untouched by A1), fault-value steps (value inside A1),
    recovery-key steps (value clean, key window contains A1).
Read-outs (memory frozen after the segment):
    adaptation  FPR / mean score on [ta+84, ta+596) of the A2-free stream (latest segment end is ta+68; 16-step guard);
                threshold = q0.99 of M0 scores on [t0-1024, t0) (as Step 1a M1a).
    contamination  paired A2 lift (identical burst, and x0.6 variant) at Delta in {64, 256}: A2 at ta+30+Delta.
    write norm     ||M_after - M0|| (Frobenius of C for W2/W3; number of entries for W1), diagnostic only.
Operators (role-matched as Step 1a/1a.1):
    phi1 (random ReLU, seeds 11/22/33): W1, W2_f0995 (normalizer read), W3_b01, W3_b05
    phi2 (PCA-whitened, signed):        W1, W2p_split_f0995 (positive split map inside W2), W3_b01, W3_b05
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
from p10_step1a_oracle import CFG1A, W1, W3, Phi, scores  # noqa: E402
from p10_step1a1_diag import W2D, FeatW2, PhiPCA  # noqa: E402

CFG1B = dict(machines=CFG1A["machines"], phi_seeds=CFG1A["phi_seeds"], w=8, dk_relu=128, dk_pca=64, knn_k=5,
             families=["ramp", "level"], fault_offset=128, a_len=30, burst_sigma=2.0, burst_channels=8,
             variant_scale=0.6, sweepA_L=38, sweepA_offsets=[-16, -8, 0, 8, 16, 30], sweepB_L=[16, 30, 38, 46, 62],
             deltas=[64, 256], eval_start=84, eval_len=512, calib_len=1024, q=0.99, seed=905)


def segments(cfg):
    segs = [("A", o, cfg["sweepA_L"]) for o in cfg["sweepA_offsets"]]
    segs += [("B", 0, L) for L in cfg["sweepB_L"]]
    return segs                                            # (sweep, offset, length); A/o=0 == B/L=38 by design


def composition(o, L, La, w):
    t = np.arange(o, o + L)                                # relative to ta
    fault = (t >= 0) & (t < La)
    rec = (t >= La) & (t < La + w)
    return dict(n_benign=int((~fault & ~rec).sum()), n_fault=int(fault.sum()), n_recovery=int(rec.sum()))


def make_ops(kind, dk, dv, k):
    if kind == "relu":
        return {"W1": W1(k), "W2_f0995": W2D(dk, dv, 0.995), "W3_b01": W3(dk, dv, 0.1), "W3_b05": W3(dk, dv, 0.5)}
    return {"W1": W1(k), "W2p_split_f0995": FeatW2(dk, dv, 0.995, "split"), "W3_b01": W3(dk, dv, 0.1),
            "W3_b05": W3(dk, dv, 0.5)}


def wnorm(m, m0):
    if isinstance(m, W1):
        return float(len(m.K) - len(m0.K))
    return float(np.linalg.norm(m.C - m0.C))


def run_unit(machine, kind, seed, data_dir, gcfg, cfg=CFG1B):
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
    segs = segments(cfg)
    rows = []
    t_start = time.time()
    for fam in cfg["families"]:
        for i, t0 in enumerate(plan.onsets[fam]):
            t0 = int(t0)
            rng = np.random.default_rng([cfg["seed"], base, i, 0 if fam == "ramp" else 1])
            ch = rng.choice(C, size=min(cfg["burst_channels"], C), replace=False)
            sg = rng.choice([-1.0, 1.0], size=len(ch))
            ta = t0 + cfg["fault_offset"]
            lo = t0 - cfg["calib_len"] - w - 1
            hi = ta + cfg["eval_start"] + cfg["eval_len"] + 2
            dch, dsg = plan.chans[(fam, i)]
            regime = apply_drift(P.z[lo:hi].astype(np.float64), t0 - lo, fam, dch, dsg, gcfg)   # matched (no fault)
            dev = np.zeros((La, C))
            dev[:, ch] = cfg["burst_sigma"] * sg[None]
            stream = regime.copy()
            stream[ta - lo:ta - lo + La] += dev                                               # actual (regime + A1)
            t_cal = np.arange(t0 - cfg["calib_len"], t0) - lo
            t_ev = np.arange(ta + cfg["eval_start"], ta + cfg["eval_start"] + cfg["eval_len"]) - lo
            Kc, Ke, Ve = phi(regime, t_cal), phi(stream, t_ev), stream[t_ev]
            A2q = {}
            for dl in cfg["deltas"]:
                ta2 = ta + La + dl
                t2 = np.arange(ta2, ta2 + La) - lo
                base_q = (phi(stream, t2), stream[t2])
                for var, sc in (("identical", 1.0), ("variant", cfg["variant_scale"])):
                    s2 = stream.copy()
                    s2[ta2 - lo:ta2 - lo + La] += sc * dev
                    A2q[(dl, var)] = (base_q, (phi(s2, t2), s2[t2]))
            for name, m0 in mems0.items():
                s_cal = scores(m0, Kc, regime[t_cal])
                thr = float(np.quantile(s_cal, cfg["q"]))

                def readout(m):
                    s = scores(m, Ke, Ve)
                    out = dict(fpr=float((s > thr).mean()), mean=float(s.mean()))
                    for (dl, var), ((Kb, Vb), (Kq, Vq)) in A2q.items():
                        sb = scores(m, Kb, Vb)
                        out[f"lift_{dl}_{var}"] = float((scores(m, Kq, Vq) - sb).mean())
                        out[f"base_{dl}"] = float(sb.mean())          # A2-free stream at the A2 positions
                    return out
                rC = readout(m0)
                rows.append(dict(family=fam, ep=i, op=name, sweep="none", offset=0, L=0, arm="C", thr=thr,
                                 n_benign=0, n_fault=0, n_recovery=0, write_norm=0.0, **rC))
                for sweep, o, L in segs:
                    ts = np.arange(ta + o, ta + o + L) - lo
                    comp = composition(o, L, La, w)
                    for arm, src in (("B", stream), ("D", regime)):
                        m = m0.copy()
                        m.write(phi(src, ts), src[ts])
                        rows.append(dict(family=fam, ep=i, op=name, sweep=sweep, offset=o, L=L, arm=arm, thr=thr,
                                         write_norm=wnorm(m, m0), **comp, **readout(m)))
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
    jobs = [(m, "relu", s, a.data_dir, a.gl1_config) for m in CFG1B["machines"] for s in CFG1B["phi_seeds"]]
    jobs += [(m, "pca", 0, a.data_dir, a.gl1_config) for m in CFG1B["machines"]]
    with Pool(a.procs) as pool:
        res = pool.map(_job, jobs)
    pd.DataFrame([r for x in res for r in x]).to_csv(out / "step1b_raw.csv.gz", index=False)
    json.dump({"cfg": CFG1B, "segments": segments(CFG1B)}, open(out / "run_config.json", "w"), indent=1)
