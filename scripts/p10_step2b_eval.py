"""Step 2b evaluator -- the ONLY label-consuming stage (development set; exploratory, not confirmatory).

Fixed before any Step 2b label access:
  1. Unit metrics per policy (as Step 2a): AP, VUS-PR / VUS-ROC (vus 0.0.6, slidingWindow = 100), AUROC, normal FPR,
     point recall, event recall at the sealed tau.  No point-adjust.
  2. Persistent-deviation regions, defined label-free from the H_hold reference run of the same unit: every
     quarantine segment that reached a checkpoint, from its start to its last checkpoint.  Labels then split them into
         PF  persistent-fault points  (y = 1 inside those segments)
         PN  persistent-normal points (y = 0 inside those segments; new regime / benign sustained drift)
     Per policy: PF recall (score > tau, want high = long fault not absorbed) and PN FPR (want low = adapted).
  3. Checkpoint classes from labels on the trailing window T (256 steps): fault if mean y(T) >= 0.5, normal if
     mean y(T) == 0, mixed otherwise.
     a. Identifiability (H_hold checkpoints): per-feature AUROC fault vs normal -- checkpoint-level, and
        segment-level using each segment's first checkpoint (age 256, the earliest decision point); per machine.
     b. Label-trained linear probe (diagnostic of information content, NOT a policy): standardised logistic
        regression on all features, leave-one-machine-out AUROC.
     c. Decision quality of the promoting policies: PROMOTE counts by class of the promoted window.
  4. Long-episode absorption (episodes >= 256 steps): written fraction and mean-score ratio vs. no-update.
Labels are loaded only through p10_step2b_data.load_test_labels (seal + per-file SHA check, access log).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p10_step2b_data as D  # noqa: E402
from p10_step2b_stream import FEATURES  # noqa: E402


def episodes(y):
    d = np.diff(np.concatenate([[0], y, [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def _auc(y, x):
    y, x = np.asarray(y), np.asarray(x, float)
    return float(roc_auc_score(y, x)) if 0 < y.sum() < len(y) else np.nan


def main(run_dir, seal_sha, label_root, out_dir):
    from vus.metrics import get_metrics
    run_dir, out_dir = Path(run_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    runs = json.loads((run_dir / "runs.json").read_text())
    cfg = json.loads((run_dir / "policy_config.json").read_text())
    ck = pd.read_csv(run_dir / "checkpoints.csv.gz")
    labels = {m: D.load_test_labels(m, purpose="step2b_dev_evaluation", seal_path=run_dir / "seal.json",
                                    label_root=label_root, expected_seal_sha=seal_sha) for m in cfg["machines"]}
    trail = cfg["trail"]

    # ---- persistent-deviation regions from the H_hold reference run (label-free definition)
    regions = {}
    for (m, s, op), g in ck[ck.policy == "H_hold"].groupby(["machine", "phi_seed", "op"]):
        r = np.zeros(len(labels[m]), bool)
        for st, gg in g.groupby("start"):
            r[int(st):int(gg.t.max())] = True
        regions[(m, s, op)] = r

    traces = {}
    for r in runs:
        z = np.load(run_dir / r["file"])
        traces[(r["machine"], r["phi_seed"], r["op"], r["policy"])] = (z["score"].astype(float), z["written"], r)

    rows, eprows = [], []
    for (m, s, op, pol), (sc, wr, r) in traces.items():
        y = labels[m]
        assert len(y) == len(sc)
        v = get_metrics(sc, y, metric="vus", slidingWindow=cfg["vus_window"])
        tau = r["tau"]
        eps = episodes(y)
        hit = [bool((sc[a:b] > tau).any()) for a, b in eps]
        reg = regions.get((m, s, op), np.zeros(len(y), bool))
        pf, pn = reg & (y == 1), reg & (y == 0)
        rows.append(dict(machine=m, phi_seed=s, op=op, policy=pol, AP=average_precision_score(y, sc),
                         VUS_PR=float(v["VUS_PR"]), VUS_ROC=float(v["VUS_ROC"]), AUROC=roc_auc_score(y, sc),
                         normal_FPR=float((sc[y == 0] > tau).mean()), point_recall=float((sc[y == 1] > tau).mean()),
                         event_recall=float(np.mean(hit)), anomaly_written_frac=float(wr[y == 1].mean()),
                         PF_points=int(pf.sum()), PN_points=int(pn.sum()),
                         PF_recall=float((sc[pf] > tau).mean()) if pf.any() else np.nan,
                         PN_FPR=float((sc[pn] > tau).mean()) if pn.any() else np.nan,
                         **{k: r[k] for k in ("written_frac", "mem_size_end", "promotions", "discards",
                                              "purged_blocks", "quarantined_points", "n_checks", "runtime_s", "tau")}))
        a0 = traces[(m, s, op, "A_no_update")][0]
        for e, (a, b) in enumerate(eps):
            eprows.append(dict(machine=m, phi_seed=s, op=op, policy=pol, episode=e, start=int(a), end=int(b),
                               length=int(b - a), mean_score=float(sc[a:b].mean()),
                               ratio_vs_A=float(sc[a:b].mean() / a0[a:b].mean()), detected=hit[e],
                               written_frac=float(wr[a:b].mean()), point_recall=float((sc[a:b] > tau).mean())))
    units = pd.DataFrame(rows)
    units.to_csv(out_dir / "step2b_metrics_units.csv", index=False)
    pd.DataFrame(eprows).to_csv(out_dir / "step2b_episode_trace.csv.gz", index=False)

    # ---- checkpoint classes
    af = np.array([labels[m][int(t) - trail:int(t)].mean() for m, t in zip(ck.machine, ck.t)])
    ck["anom_frac_T"] = af
    ck["cls"] = np.where(af >= 0.5, "fault", np.where(af == 0, "normal", "mixed"))
    ck["seg_anom_frac"] = [labels[m][int(st):int(t)].mean() for m, st, t in zip(ck.machine, ck.start, ck.t)]
    ck.to_csv(out_dir / "step2b_checkpoints_labelled.csv.gz", index=False)

    H = ck[(ck.policy == "H_hold") & (ck.cls != "mixed")].copy()
    H["yf"] = (H.cls == "fault").astype(int)
    first = H.sort_values("t").groupby(["machine", "phi_seed", "op", "start"]).head(1)
    first = first[first.age == cfg["check_start"]]
    idrows = []
    for level, df in (("checkpoint", H), ("segment_first_check", first)):
        for scope, gdf in [("pooled", df)] + [(m, g) for m, g in df.groupby("machine")]:
            row = dict(level=level, scope=scope, n_fault=int(gdf.yf.sum()), n_normal=int((1 - gdf.yf).sum()),
                       n_fault_segments=int(gdf[gdf.yf == 1].groupby(["phi_seed", "op", "start"]).ngroups),
                       n_normal_segments=int(gdf[gdf.yf == 0].groupby(["phi_seed", "op", "start"]).ngroups))
            for f in FEATURES:
                row[f] = _auc(gdf.yf, gdf[f])
            idrows.append(row)
    ident = pd.DataFrame(idrows)
    ident.to_csv(out_dir / "step2b_identifiability_auroc.csv", index=False)

    probe = []
    feats = [f for f in FEATURES if f != "age"]
    for level, df in (("checkpoint", H), ("segment_first_check", first)):
        for held in sorted(df.machine.unique()):
            tr, te = df[df.machine != held], df[df.machine == held]
            if tr.yf.nunique() < 2 or te.yf.nunique() < 2:
                probe.append(dict(level=level, held_out=held, AUROC=np.nan, n_test=len(te),
                                  note="single class in train or test"))
                continue
            sc = StandardScaler().fit(tr[feats])
            lr = LogisticRegression(C=1.0, max_iter=2000, class_weight="balanced").fit(sc.transform(tr[feats]), tr.yf)
            p = lr.predict_proba(sc.transform(te[feats]))[:, 1]
            probe.append(dict(level=level, held_out=held, AUROC=_auc(te.yf, p), n_test=len(te), note=""))
    pd.DataFrame(probe).to_csv(out_dir / "step2b_lomo_probe.csv", index=False)

    dec = (ck[ck.decision == "PROMOTE"].groupby(["policy", "op", "cls"]).size().unstack(fill_value=0)
           .reindex(columns=["fault", "mixed", "normal"], fill_value=0).reset_index())
    dec.to_csv(out_dir / "step2b_promotion_quality.csv", index=False)
    (out_dir / "label_access_log.json").write_text(json.dumps(dict(seal_sha256=seal_sha,
                                                                  accesses=D.label_access_log()), indent=1))
    print("labels read:", len(D.label_access_log()))


if __name__ == "__main__":
    main(*sys.argv[1:5])
