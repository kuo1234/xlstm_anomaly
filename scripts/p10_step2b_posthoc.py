"""Step 2b POST-HOC headroom run (development set only; NOT confirmatory).

After the Step 2b dev evaluation, the identifiability table showed that the pre-registered DE_stab rule
(self <= 1 AND stat <= 0.5) passes ~20-39% of fault checkpoints, while the score-trajectory coefficient of
variation `cv` separated fault from persistent-normal checkpoints on both machines that have both classes.
This script runs ONE rule chosen after seeing dev labels:

    DEph_cv   PROMOTE T when self <= 1.0 AND stat <= 0.5 AND cv <= 0.10

cv threshold 0.10 lies between the dev class medians (machine-1-6 fault 0.17 / normal 0.05; machine-3-7 fault 0.36 /
normal 0.02).  It is therefore tuned on the development labels; its numbers only estimate headroom and must be
re-tested with a sealed config on machines whose labels have not been seen.

Still label-blind as code: reads observations only; writes traces + checkpoints + a seal (posthoc=True).
Everything else (detector, segment machinery, evidence) is imported unchanged from p10_step2b_stream.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p10_step2b_stream as S  # noqa: E402
from p10_step2a_data import MACHINES, load_observations, sha256  # noqa: E402
from p10_step2a_stream import W1S, make_mem, scale, scores  # noqa: E402
from p10_step1a_oracle import Phi  # noqa: E402

PH = dict(rule="self <= 1.0 AND stat <= 0.5 AND cv <= 0.10", cv_max=0.10, policy="DEph_cv",
          chosen_after_dev_labels=True)


def run_cv_policy(builder, ctx):
    """Segment machinery identical to p10_step2b_stream.run_seg_policy('DE_stab', ...) plus the cv condition."""
    cfg, tau = ctx["cfg"], ctx["tau"]
    Kt, Vt, B, N = ctx["Kt"], ctx["Vt"], cfg["block"], len(ctx["Kt"])
    mem = builder()
    s_all = np.zeros(N, np.float32)
    written = np.zeros(N, bool)
    ev = dict(promotions=0, discards=0, purged_blocks=0, quarantined_points=0)
    checks, seg = [], None

    def commit(a, b):
        mem.write(Kt[a:b], Vt[a:b], np.arange(a, b))
        written[a:b] = True

    t0 = time.time()
    for j0 in range(0, N, B):
        j1 = min(j0 + B, N)
        s = scores(mem, Kt[j0:j1], Vt[j0:j1])
        s_all[j0:j1] = s
        exc = bool((s > tau).any())
        if seg is None:
            if not exc:
                commit(j0, j1)
                continue
            seg = dict(start=j0, gap=0)
        else:
            seg["gap"] = 0 if exc else seg["gap"] + 1
            if seg["gap"] > cfg["seg_gap_blocks"]:
                for a in range(j1 - B * seg["gap"], j1, B):
                    commit(a, min(a + B, N))
                ev["discards"] += 1
                seg = None
                continue
        ev["quarantined_points"] += j1 - j0
        age = j1 - seg["start"]
        if age >= cfg["check_start"] and (age - cfg["check_start"]) % cfg["check_every"] == 0:
            f = S.evidence(mem, ctx, s_all, seg["start"], j1)
            promote = f["self"] <= cfg["self_max"] and f["stat"] <= cfg["stat_max"] and f["cv"] <= PH["cv_max"]
            checks.append(dict(t=int(j1), start=int(seg["start"]), decision="PROMOTE" if promote else "KEEP", **f))
            if promote:
                commit(j1 - cfg["trail"], j1)
                ev["promotions"] += 1
                seg = None
    return dict(score=s_all, written=written, events=ev, checks=checks, mem_size=mem.size(),
                runtime_s=time.time() - t0)


def run_unit(machine, seed, train_root, test_root, out, cfg=S.CFG2B):
    tr, te = load_observations(machine, "train", train_root), load_observations(machine, "test", test_root)
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

    def builder_for(op):
        def builder():
            m = make_mem(op, cap, cfg["dk"], C, cfg["knn_k"])
            m.write(K0, V0, -np.ones(len(K0), np.int64)) if isinstance(m, W1S) else m.write(K0, V0)
            return m
        return builder

    taus, frozen = {}, {}
    for op in cfg["ops"]:
        m0 = builder_for(op)()
        taus[op] = float(np.quantile(scores(m0, Kc, Vc), cfg["calib_q"]))
        frozen[op] = scores(m0, Kt, Vt)
    out = Path(out)
    (out / "traces").mkdir(parents=True, exist_ok=True)
    metas, checks = [], []
    for op in cfg["ops"]:
        ctx = dict(cfg=cfg, tau=taus[op], Kt=Kt, Vt=Vt, K0=K0, frozen=frozen, taus=taus,
                   zbase=lambda st: zb_ext[st:st + cfg["base_win"]])
        r = run_cv_policy(builder_for(op), ctx)
        name = f"traces/{machine}__s{seed}__{op}__{PH['policy']}.npz"
        np.savez_compressed(out / name, score=r["score"], written=r["written"])
        e = r["events"]
        metas.append(dict(machine=machine, phi_seed=seed, op=op, policy=PH["policy"], tau=taus[op], file=name,
                          n_test=len(Kt), written_frac=float(r["written"].mean()), mem_size_end=r["mem_size"],
                          promotions=e["promotions"], discards=e["discards"], purged_blocks=0,
                          quarantined_points=e["quarantined_points"], n_checks=len(r["checks"]),
                          runtime_s=r["runtime_s"]))
        checks += [dict(machine=machine, phi_seed=seed, op=op, policy=PH["policy"], **c) for c in r["checks"]]
    print(f"{machine} s{seed} done", flush=True)
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
    jobs = [(m, s, a.train_root, a.test_root, str(out)) for m in S.CFG2B["machines"] for s in S.CFG2B["phi_seeds"]]
    with Pool(a.procs) as pool:
        res = pool.map(_job, jobs)
    metas = [x for r in res for x in r[0]]
    (out / "runs.json").write_text(json.dumps(metas, indent=1))
    pd.DataFrame([x for r in res for x in r[1]]).to_csv(out / "checkpoints.csv.gz", index=False)
    (out / "policy_config.json").write_text(json.dumps(dict(S.CFG2B, features=S.FEATURES, posthoc=PH), indent=1))
    here = Path(__file__).resolve().parent
    files = {m["file"]: sha256(out / m["file"]) for m in metas}
    for f in ("runs.json", "checkpoints.csv.gz", "policy_config.json"):
        files[f] = sha256(out / f)
    seal = dict(stage="step2b_label_blind_scores", posthoc=True, machines=S.CFG2B["machines"], files=files,
                code={p: sha256(here / p) for p in ("p10_step2b_posthoc.py", "p10_step2b_stream.py",
                                                    "p10_step2b_data.py", "p10_step2a_stream.py")},
                labels_read=0, utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    (out / "seal.json").write_text(json.dumps(seal, indent=1, sort_keys=True))
    print("seal.json", sha256(out / "seal.json"))
