"""Evaluator for the Step 2b POST-HOC headroom run (DEph_cv).  Same metrics as p10_step2b_eval; the persistent-
deviation regions (PF / PN) and the no-update reference traces come from the main Step 2b run, so the two runs are
scored on identical point sets.  Labels only via p10_step2b_data.load_test_labels (post-hoc seal, access log).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p10_step2b_data as D  # noqa: E402
from p10_step2b_eval import episodes  # noqa: E402


def main(ph_dir, seal_sha, label_root, main_run, main_eval, out_dir):
    from vus.metrics import get_metrics
    ph_dir, main_run, main_eval, out_dir = map(Path, (ph_dir, main_run, main_eval, out_dir))
    out_dir.mkdir(parents=True, exist_ok=True)
    runs = json.loads((ph_dir / "runs.json").read_text())
    cfg = json.loads((ph_dir / "policy_config.json").read_text())
    labels = {m: D.load_test_labels(m, purpose="step2b_dev_evaluation", seal_path=ph_dir / "seal.json",
                                    label_root=label_root, expected_seal_sha=seal_sha) for m in cfg["machines"]}
    ckm = pd.read_csv(main_eval / "step2b_checkpoints_labelled.csv.gz")
    regions = {}
    for (m, s, op), g in ckm[ckm.policy == "H_hold"].groupby(["machine", "phi_seed", "op"]):
        r = np.zeros(len(labels[m]), bool)
        for st, gg in g.groupby("start"):
            r[int(st):int(gg.t.max())] = True
        regions[(m, s, op)] = r
    rows, eprows = [], []
    for r in runs:
        m, s, op, pol = r["machine"], r["phi_seed"], r["op"], r["policy"]
        z = np.load(ph_dir / r["file"])
        sc, wr, y, tau = z["score"].astype(float), z["written"], labels[m], r["tau"]
        a0 = np.load(main_run / f"traces/{m}__s{s}__{op}__A_no_update.npz")["score"].astype(float)
        v = get_metrics(sc, y, metric="vus", slidingWindow=cfg["vus_window"])
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
        for e, (a, b) in enumerate(eps):
            eprows.append(dict(machine=m, phi_seed=s, op=op, policy=pol, episode=e, start=int(a), end=int(b),
                               length=int(b - a), mean_score=float(sc[a:b].mean()),
                               ratio_vs_A=float(sc[a:b].mean() / a0[a:b].mean()), detected=hit[e],
                               written_frac=float(wr[a:b].mean()), point_recall=float((sc[a:b] > tau).mean())))
    pd.DataFrame(rows).to_csv(out_dir / "step2b_posthoc_metrics_units.csv", index=False)
    pd.DataFrame(eprows).to_csv(out_dir / "step2b_posthoc_episode_trace.csv.gz", index=False)
    ck = pd.read_csv(ph_dir / "checkpoints.csv.gz")
    af = np.array([labels[m][int(t) - cfg["trail"]:int(t)].mean() for m, t in zip(ck.machine, ck.t)])
    ck["anom_frac_T"] = af
    ck["cls"] = np.where(af >= 0.5, "fault", np.where(af == 0, "normal", "mixed"))
    ck.to_csv(out_dir / "step2b_posthoc_checkpoints_labelled.csv.gz", index=False)
    (out_dir / "label_access_log_posthoc.json").write_text(json.dumps(dict(seal_sha256=seal_sha,
                                                                          accesses=D.label_access_log()), indent=1))
    print("labels read:", len(D.label_access_log()))


if __name__ == "__main__":
    main(*sys.argv[1:7])
