"""Step 2b (issue #15 comment 5970197497): delayed-evidence drift-vs-fault admission pilot.

LABEL-BLIND STAGE.  Reads SMD train / test observations only.  Every rule and threshold below is fixed in CFG2B
before any Step 2b label access; the script writes score traces, per-checkpoint evidence logs and a seal.

Detector, scaling, M0, tau, operators and the 16-step block-delayed causal protocol are identical to Step 2a
(p10_step2a_stream): blocks are scored with the block-start memory, then the policy decides what is written.

Segment machinery (shared by all new policies)
    A block with an exceedance (any score > tau) opens / extends a QUARANTINE SEGMENT; held blocks are not written.
    Clean blocks inside a segment are held too; the segment ENDS after G = 2 consecutive clean blocks (DISCARD:
    the held exceedance blocks are dropped, the trailing clean blocks are written).  While a segment is open, a
    CHECKPOINT fires at age 256 and every 128 steps after; delayed evidence is computed on the trailing window
    T = last 256 steps (T1 = first 128, T2 = last 128), and the policy chooses KEEP-QUARANTINED or PROMOTE.
    PROMOTE writes only T (the stabilised suffix) and drops the earlier part of the segment.

Delayed evidence logged at every checkpoint (all causal: data <= checkpoint time)
    level     median score(T) / tau                      cv     std / mean of score(T)
    slope     OLS slope of log score(T) per 100 steps
    self0     q0.9 score(T2) under the current memory / tau
    self      q0.9 score(T2) after a TRIAL WRITE of T1 into a copy of the memory (operator-specific) / tau
    learn     self / self0
    stat      ||mean z(T2) - mean z(T1)|| / ||mean z(T) - mean z(base)||,  base = 256 steps before segment start
    shift     RMS over channels of mean z(T) - mean z(base)
    nch       channels with |mean z(T) - mean z(base)| > 1 (train-sd units)
    conc      share of the squared shift carried by the top-3 channels
    novel     1 - mean_t max_j cos(k_t, K0_j)   (key novelty vs. the initial normal memory)
    dis       std over W1/W2/W3 of log(median frozen-M0 score(T) / tau_op)   (operator disagreement)
    frozen    mean over operators of log(median frozen-M0 score(T) / tau_op)
    age       steps since segment start

Policies (A-D reproduce Step 2a exactly through p10_step2a_stream.run_policy)
    A_no_update, B_always, C_threshold, D_quarantine (Step 2a fixed-512, promotes the whole buffer)
    H_hold         segment machinery, always KEEP (reference policy for the identifiability analysis)
    D_trail512     PROMOTE T at the first checkpoint with age >= 512 (age-only; isolates "what is promoted")
    DE_stab        PROMOTE T when self <= 1.0 AND stat <= 0.5 (trial-written memory explains T2 at the normal
                   noise level, and the deviation has settled on a plateau)
    DE_stab512     DE_stab evidence AND age >= 512 (age-matched to D_trail512: isolates what the evidence adds)
    C_lb           threshold + delayed commit: clean blocks wait 128 steps before being written; an exceedance
                   block purges pending blocks whose max score > tau_low = q0.95 of the calibration scores
    DE_stab_lb     DE_stab + the same delayed commit / purge
    rand_DE        random block-level writes at DE_stab's written fraction
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p10_step1a_oracle import Phi  # noqa: E402
from p10_step2a_data import MACHINES, load_observations, sha256  # noqa: E402
from p10_step2a_stream import CFG2A, W1S, W2S, W3S, make_mem, run_policy, scale, scores  # noqa: E402

CFG2B = dict({k: CFG2A[k] for k in ("machines", "phi_seeds", "w", "dk", "knn_k", "sd_floor", "z_clip", "fit_frac",
                                    "calib_q", "block", "ops", "quarantine_promote_blocks", "vus_window")},
             seg_gap_blocks=2, check_start=256, check_every=128, trail=256, self_q=0.9, self_max=1.0,
             stat_max=0.5, promote_age_trail=512, lb_steps=128, lb_q=0.95, base_win=256, chan_shift=1.0, top_c=3,
             random_seed=917,
             policies=["A_no_update", "B_always", "C_threshold", "D_quarantine", "H_hold", "D_trail512", "DE_stab",
                       "DE_stab512", "C_lb", "DE_stab_lb", "rand_DE"])
FEATURES = ["level", "cv", "slope", "self0", "self", "learn", "stat", "shift", "nch", "conc", "novel", "dis",
            "frozen", "age"]


# ============================================================================ trial write (copy semantics)
def trial_scores(mem, Kw, Vw, Kq, Vq):
    """Score (Kq, Vq) after writing (Kw, Vw) into a COPY of the memory; the live memory is unchanged."""
    if isinstance(mem, W1S):
        n0 = mem.n
        mem.write(Kw, Vw, -2 * np.ones(len(Kw), np.int64))
        s = scores(mem, Kq, Vq)
        mem.alive[n0:mem.n] = False
        mem.n = n0
        return s
    if isinstance(mem, W2S):
        C, nv, nw = mem.C.copy(), mem.nv.copy(), mem.nw
        mem.write(Kw, Vw)
        s = scores(mem, Kq, Vq)
        mem.C, mem.nv, mem.nw = C, nv, nw
        return s
    C = mem.C.copy()
    mem._apply(Kw, Vw)
    s = scores(mem, Kq, Vq)
    mem.C = C
    return s


# ============================================================================ delayed evidence
def evidence(mem, ctx, s_all, start, j1):
    cfg, tau = ctx["cfg"], ctx["tau"]
    T = np.arange(j1 - cfg["trail"], j1)
    h = cfg["trail"] // 2
    T1, T2 = T[:h], T[h:]
    K, Z = ctx["Kt"], ctx["Vt"]
    s = np.maximum(s_all[T].astype(float), 1e-9)
    f = dict(level=float(np.median(s) / tau), cv=float(s.std() / s.mean()),
             slope=float(np.polyfit(np.arange(len(T)) / 100.0, np.log(s), 1)[0]))
    s0 = scores(mem, K[T2], Z[T2])
    s1 = trial_scores(mem, K[T1], Z[T1], K[T2], Z[T2])
    f["self0"] = float(np.quantile(s0, cfg["self_q"]) / tau)
    f["self"] = float(np.quantile(s1, cfg["self_q"]) / tau)
    f["learn"] = f["self"] / max(f["self0"], 1e-9)
    zb = ctx["zbase"](start)
    d = Z[T].mean(0) - zb.mean(0)
    f["stat"] = float(np.linalg.norm(Z[T2].mean(0) - Z[T1].mean(0)) / (np.linalg.norm(d) + 1e-6))
    f["shift"] = float(np.sqrt(np.mean(d ** 2)))
    f["nch"] = int((np.abs(d) > cfg["chan_shift"]).sum())
    d2 = np.sort(d ** 2)[::-1]
    f["conc"] = float(d2[:cfg["top_c"]].sum() / (d2.sum() + 1e-12))
    f["novel"] = float(1.0 - (K[T] @ ctx["K0"].T).max(1).mean())
    r = np.array([np.log(max(np.median(ctx["frozen"][op][T]), 1e-9) / ctx["taus"][op]) for op in cfg["ops"]])
    f["dis"], f["frozen"] = float(r.std()), float(r.mean())
    f["age"] = int(j1 - start)
    return f


# ============================================================================ segment / delayed-commit policies
def run_seg_policy(policy, builder, ctx):
    cfg, tau, tau_low = ctx["cfg"], ctx["tau"], ctx["tau_low"]
    Kt, Vt, B, N = ctx["Kt"], ctx["Vt"], cfg["block"], len(ctx["Kt"])
    use_seg = policy in ("H_hold", "D_trail512", "DE_stab", "DE_stab512", "DE_stab_lb")
    use_lb = policy in ("C_lb", "DE_stab_lb")
    mem = builder()
    s_all = np.zeros(N, np.float32)
    written = np.zeros(N, bool)
    ev = dict(promotions=0, discards=0, purged_blocks=0, quarantined_points=0)
    checks = []
    pending = []                     # (j0, j1, max score) clean blocks awaiting delayed commit
    seg = None                       # dict(start, gap)

    def commit(a, b):
        mem.write(Kt[a:b], Vt[a:b], np.arange(a, b))
        written[a:b] = True

    def clean_write(a, b, smax):
        if use_lb:
            pending.append((a, b, smax))
        else:
            commit(a, b)

    t0 = time.time()
    for j0 in range(0, N, B):
        j1 = min(j0 + B, N)
        s = scores(mem, Kt[j0:j1], Vt[j0:j1])
        s_all[j0:j1] = s
        exc = bool((s > tau).any())
        if use_lb:
            if exc:
                keep = [p for p in pending if p[2] <= tau_low]
                ev["purged_blocks"] += len(pending) - len(keep)
                pending[:] = keep
            while pending and pending[0][0] + cfg["lb_steps"] <= j0:
                a, b, _ = pending.pop(0)
                commit(a, b)
        if not use_seg:                                   # C_lb
            if not exc:
                clean_write(j0, j1, float(s.max()))
            continue
        if seg is None:
            if not exc:
                clean_write(j0, j1, float(s.max()))
                continue
            seg = dict(start=j0, gap=0)
        else:
            seg["gap"] = 0 if exc else seg["gap"] + 1
            if seg["gap"] > cfg["seg_gap_blocks"]:        # return to baseline -> DISCARD, write the clean tail
                for a in range(j1 - B * seg["gap"], j1, B):
                    b = min(a + B, N)
                    clean_write(a, b, float(s_all[a:b].max()))
                ev["discards"] += 1
                seg = None
                continue
        ev["quarantined_points"] += j1 - j0
        age = j1 - seg["start"]
        if age >= cfg["check_start"] and (age - cfg["check_start"]) % cfg["check_every"] == 0:
            f = evidence(mem, ctx, s_all, seg["start"], j1)
            if policy == "D_trail512":
                promote = age >= cfg["promote_age_trail"]
            elif policy in ("DE_stab", "DE_stab_lb", "DE_stab512"):
                promote = f["self"] <= cfg["self_max"] and f["stat"] <= cfg["stat_max"]
                if policy == "DE_stab512":
                    promote = promote and age >= cfg["promote_age_trail"]
            else:
                promote = False
            checks.append(dict(t=int(j1), start=int(seg["start"]), decision="PROMOTE" if promote else "KEEP", **f))
            if promote:
                commit(j1 - cfg["trail"], j1)
                ev["promotions"] += 1
                seg = None
    return dict(score=s_all, written=written, events=ev, checks=checks, mem_size=mem.size(),
                runtime_s=time.time() - t0)


# ============================================================================ one (machine, seed) unit
def run_unit(machine, seed, train_root, test_root, out, cfg=CFG2B):
    tr = load_observations(machine, "train", train_root)
    te = load_observations(machine, "test", test_root)
    ztr, zte = scale(tr, te, cfg)
    C, w = ztr.shape[1], cfg["w"]
    phi = Phi(C, w, cfg["dk"], seed)
    fit_end = int(len(ztr) * cfg["fit_frac"])
    t_fit = np.arange(w, fit_end)
    K0, V0 = phi(ztr, t_fit), ztr[t_fit]
    t_cal = np.arange(fit_end, len(ztr))
    Kc, Vc = phi(ztr, t_cal), ztr[t_cal]
    zext = np.concatenate([ztr[-w:], zte])
    Kt, Vt = phi(zext, np.arange(w, len(zext))), zte
    cap = len(K0) + len(Kt) + 16
    zb_ext = np.concatenate([ztr[-cfg["base_win"]:], zte])

    def zbase(start):                                # 256 observations strictly before the segment start
        return zb_ext[start:start + cfg["base_win"]]

    def builder_for(op):
        def builder():
            m = make_mem(op, cap, cfg["dk"], C, cfg["knn_k"])
            if isinstance(m, W1S):
                m.write(K0, V0, -np.ones(len(K0), np.int64))
            else:
                m.write(K0, V0)
            return m
        return builder

    taus, taus_low, frozen = {}, {}, {}
    for op in cfg["ops"]:
        m0 = builder_for(op)()
        sc = scores(m0, Kc, Vc)
        taus[op], taus_low[op] = float(np.quantile(sc, cfg["calib_q"])), float(np.quantile(sc, cfg["lb_q"]))
        frozen[op] = scores(m0, Kt, Vt)               # == A_no_update trace; causal (memory never changes)
    out = Path(out)
    (out / "traces").mkdir(parents=True, exist_ok=True)
    metas, checks = [], []
    cfg2a = dict(CFG2A)
    for op in cfg["ops"]:
        builder = builder_for(op)
        ctx = dict(cfg=cfg, tau=taus[op], tau_low=taus_low[op], Kt=Kt, Vt=Vt, K0=K0, zbase=zbase, frozen=frozen,
                   taus=taus)
        res = {}
        for pol in ("A_no_update", "B_always", "C_threshold", "D_quarantine"):
            r = run_policy(pol, op, builder, Kt, Vt, taus[op], cfg2a)
            r["checks"] = []
            res[pol] = r
        for pol in ("H_hold", "D_trail512", "DE_stab", "DE_stab512", "C_lb", "DE_stab_lb"):
            res[pol] = run_seg_policy(pol, builder, ctx)
        p = float(res["DE_stab"]["written"].mean())
        rng = np.random.default_rng([cfg["random_seed"], seed, MACHINES.index(machine), cfg["ops"].index(op)])
        r = run_policy("rand_DE", op, builder, Kt, Vt, taus[op], cfg2a, p_write=p, rng=rng)
        r["checks"] = []
        res["rand_DE"] = r
        for pol, r in res.items():
            name = f"traces/{machine}__s{seed}__{op}__{pol}.npz"
            np.savez_compressed(out / name, score=r["score"], written=r["written"])
            e = r["events"]
            metas.append(dict(machine=machine, phi_seed=seed, op=op, policy=pol, tau=taus[op], tau_low=taus_low[op],
                              file=name, n_test=len(Kt), written_frac=float(r["written"].mean()),
                              mem_size_end=r["mem_size"], promotions=e.get("promotions", 0),
                              discards=e.get("discards", 0), purged_blocks=e.get("purged_blocks", 0),
                              quarantined_points=e.get("quarantined_points", 0), n_checks=len(r["checks"]),
                              runtime_s=r["runtime_s"]))
            for c in r["checks"]:
                checks.append(dict(machine=machine, phi_seed=seed, op=op, policy=pol, **c))
        print(f"{machine} s{seed} {op} tau={taus[op]:.3f} done", flush=True)
    return metas, checks


def _job(a):
    return run_unit(*a)


if __name__ == "__main__":
    import argparse
    from multiprocessing import Pool

    import pandas as pd
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-root", required=True)
    ap.add_argument("--test-root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--procs", type=int, default=9)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(m, s, a.train_root, a.test_root, str(out)) for m in CFG2B["machines"] for s in CFG2B["phi_seeds"]]
    with Pool(a.procs) as pool:
        res = pool.map(_job, jobs)
    metas = [x for r in res for x in r[0]]
    checks = [x for r in res for x in r[1]]
    (out / "runs.json").write_text(json.dumps(metas, indent=1))
    pd.DataFrame(checks).to_csv(out / "checkpoints.csv.gz", index=False)
    (out / "policy_config.json").write_text(json.dumps(dict(CFG2B, features=FEATURES), indent=1))
    here = Path(__file__).resolve().parent
    files = {m["file"]: sha256(out / m["file"]) for m in metas}
    for f in ("runs.json", "checkpoints.csv.gz", "policy_config.json"):
        files[f] = sha256(out / f)
    seal = dict(stage="step2b_label_blind_scores", machines=CFG2B["machines"], files=files,
                code={p: sha256(here / p) for p in ("p10_step2b_stream.py", "p10_step2b_data.py",
                                                    "p10_step2a_stream.py", "p10_step2a_data.py",
                                                    "p10_step1a_oracle.py")},
                observations={f"{m}_{s}": sha256(Path(a.train_root if s == "train" else a.test_root) / f"{m}_{s}.txt")
                              for m in CFG2B["machines"] for s in ("train", "test")},
                labels_read=0, utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    (out / "seal.json").write_text(json.dumps(seal, indent=1, sort_keys=True))
    print("seal.json", sha256(out / "seal.json"))
