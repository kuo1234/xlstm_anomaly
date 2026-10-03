"""Step 2a evaluator -- the ONLY label-consuming stage.  Metrics are fixed here before any label is read:

    AP (sklearn average_precision_score), VUS-PR and VUS-ROC (official `vus` 0.0.6, slidingWindow = 100), AUROC;
    at the sealed per-unit threshold tau: normal FPR, point recall, event recall (episode has >= 1 point > tau).
    No point-adjust.
Per-episode diagnostics (episode = maximal run of label-1 points):
    mean / max score per policy, fraction of the episode's points written to memory, and for E the rollback events
    that overlap the episode (+/- 16 steps).  Absorption under always-update = mean score(B) / mean score(A).
Labels are loaded only through p10_step2a_data.load_test_labels, which verifies the seal (SHA-256 of seal.json, and of
every sealed trace) and logs each access.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p10_step2a_data as D  # noqa: E402


def episodes(y):
    d = np.diff(np.concatenate([[0], y, [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def main(run_dir, seal_sha, label_root, out_dir):
    from vus.metrics import get_metrics
    run_dir, out_dir = Path(run_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    runs = json.loads((run_dir / "runs.json").read_text())
    cfg = json.loads((run_dir / "policy_config.json").read_text())
    labels = {m: D.load_test_labels(m, purpose="step2a_final_evaluation", seal_path=run_dir / "seal.json",
                                    label_root=label_root, expected_seal_sha=seal_sha) for m in cfg["machines"]}
    rows, eprows = [], []
    traces = {}
    for r in runs:
        z = np.load(run_dir / r["file"])
        traces[(r["machine"], r["phi_seed"], r["op"], r["policy"])] = (z["score"].astype(float), z["written"], r)
    for (m, s, op, pol), (sc, wr, r) in traces.items():
        y = labels[m]
        assert len(y) == len(sc)
        v = get_metrics(sc, y, metric="vus", slidingWindow=cfg["vus_window"])
        tau = r["tau"]
        eps = episodes(y)
        hit = [bool((sc[a:b] > tau).any()) for a, b in eps]
        rows.append(dict(machine=m, phi_seed=s, op=op, policy=pol, AP=average_precision_score(y, sc),
                         VUS_PR=float(v["VUS_PR"]), VUS_ROC=float(v["VUS_ROC"]), AUROC=roc_auc_score(y, sc),
                         normal_FPR=float((sc[y == 0] > tau).mean()), point_recall=float((sc[y == 1] > tau).mean()),
                         event_recall=float(np.mean(hit)), n_episodes=len(eps), anomaly_frac=float(y.mean()),
                         **{k: r[k] for k in ("written_frac", "mem_size_end", "promotions", "discards",
                                              "quarantined_points", "n_rollbacks", "n_removed", "mean_rollback_span",
                                              "replayed_writes", "runtime_s", "tau")}))
        for e, (a, b) in enumerate(eps):
            ov = [ev for ev in r["rollback_events"] if ev["t"] >= a - 16 and ev["start"] <= b + 16]
            eprows.append(dict(machine=m, phi_seed=s, op=op, policy=pol, episode=e, start=int(a), end=int(b),
                               length=int(b - a), mean_score=float(sc[a:b].mean()), max_score=float(sc[a:b].max()),
                               detected=hit[e], written_frac=float(wr[a:b].mean()), rollbacks_overlapping=len(ov)))
    pd.DataFrame(rows).to_csv(out_dir / "step2a_metrics_units.csv", index=False)
    pd.DataFrame(eprows).to_csv(out_dir / "step2a_episode_trace.csv.gz", index=False)
    (out_dir / "label_access_log.json").write_text(json.dumps(dict(seal_sha256=seal_sha,
                                                                  accesses=D.label_access_log()), indent=1))
    print("labels read:", len(D.label_access_log()))


if __name__ == "__main__":
    main(*sys.argv[1:5])
