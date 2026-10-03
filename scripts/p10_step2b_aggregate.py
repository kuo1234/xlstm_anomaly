"""Step 2b tables from the evaluator outputs (no label access: reads only the labelled per-unit / per-checkpoint
CSVs written by p10_step2b_eval / p10_step2b_posthoc_eval).

Note: the identifiability table is recomputed here because the first evaluator pass let the feature `level`
overwrite the unit-level key of the row dict (fixed in p10_step2b_eval.py); the AUROC values themselves were unaffected.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p10_step2b_stream import FEATURES  # noqa: E402

POLS = ["A_no_update", "B_always", "C_threshold", "D_quarantine", "H_hold", "D_trail512", "DE_stab", "DE_stab512",
        "C_lb", "DE_stab_lb", "rand_DE", "DEph_cv"]
COLS = ["AP", "VUS_PR", "VUS_ROC", "AUROC", "normal_FPR", "point_recall", "event_recall", "PF_recall", "PN_FPR",
        "anomaly_written_frac", "written_frac", "promotions"]
PAIRS = [("DE_stab", "C_threshold"), ("DE_stab", "D_quarantine"), ("D_trail512", "D_quarantine"),
         ("DE_stab512", "D_trail512"), ("DE_stab", "D_trail512"), ("DE_stab_lb", "DE_stab"), ("C_lb", "C_threshold"),
         ("DE_stab", "rand_DE"), ("DE_stab", "A_no_update"), ("DEph_cv", "C_threshold"), ("DEph_cv", "DE_stab"),
         ("DEph_cv", "D_quarantine"), ("DEph_cv", "A_no_update")]


def _auc(y, x):
    return float(roc_auc_score(y, x)) if 0 < y.sum() < len(y) else np.nan


def physical_segments(H, tol=256):
    """Cluster H_hold segment starts across (seed, op) into physical segments (starts within `tol` steps)."""
    out = []
    for m, g in H.groupby("machine"):
        st, groups = np.sort(g.start.unique()), []
        for s in st:
            if groups and s - groups[-1][-1] <= tol:
                groups[-1].append(s)
            else:
                groups.append([s])
        for gr in groups:
            sub = g[(g.start >= gr[0]) & (g.start <= gr[-1])]
            vc = sub.cls.value_counts()
            out.append(dict(machine=m, start_min=int(gr[0]), start_max=int(gr[-1]), n_checkpoints=len(sub),
                            n_unit_segments=sub.groupby(["phi_seed", "op", "start"]).ngroups,
                            max_age=int(sub.age.max()), ck_fault=int(vc.get("fault", 0)),
                            ck_mixed=int(vc.get("mixed", 0)), ck_normal=int(vc.get("normal", 0)),
                            mean_seg_anom_frac=float(sub.seg_anom_frac.mean())))
    return pd.DataFrame(out)


def main(eval_dir, out_dir):
    E, O = Path(eval_dir), Path(out_dir)
    O.mkdir(parents=True, exist_ok=True)
    u = pd.concat([pd.read_csv(E / "step2b_metrics_units.csv"), pd.read_csv(E / "step2b_posthoc_metrics_units.csv")])
    u["posthoc"] = u.policy == "DEph_cv"
    s = u.groupby(["op", "policy"])[COLS].mean().reset_index()
    s["policy"] = pd.Categorical(s.policy, POLS, ordered=True)
    s.sort_values(["op", "policy"]).to_csv(O / "step2b_summary.csv", index=False, float_format="%.4f")
    sm = u.groupby(["machine", "op", "policy"])[COLS].mean().reset_index()
    sm["policy"] = pd.Categorical(sm.policy, POLS, ordered=True)
    sm.sort_values(["machine", "op", "policy"]).to_csv(O / "step2b_summary_by_machine.csv", index=False,
                                                        float_format="%.4f")
    P = u.pivot_table(index=["machine", "phi_seed", "op"], columns="policy", values="AP")
    rows = []
    for a, b in PAIRS:
        d = P[a] - P[b]
        mm = d.groupby("machine").mean()
        rows.append(dict(contrast=f"{a} - {b}", unit_wins=int((d > 0).sum()), unit_ties=int((d.abs() < 1e-4).sum()),
                         n_units=len(d), mean_dAP=d.mean(), machines_positive=int((mm > 1e-4).sum()),
                         **{f"dAP_{k}": v for k, v in mm.items()}))
    pd.DataFrame(rows).to_csv(O / "step2b_contrasts_AP.csv", index=False, float_format="%.4f")

    ck = pd.read_csv(E / "step2b_checkpoints_labelled.csv.gz")
    H = ck[ck.policy == "H_hold"]
    physical_segments(H).to_csv(O / "step2b_physical_segments.csv", index=False, float_format="%.3f")
    Hn = H[H.cls != "mixed"].assign(yf=lambda d: (d.cls == "fault").astype(int))
    first = Hn.sort_values("t").groupby(["machine", "phi_seed", "op", "start"]).head(1)
    first = first[first.age == 256]
    idrows = []
    for level, df in (("checkpoint", Hn), ("segment_first_check", first)):
        for scope, g in [("pooled", df)] + list(df.groupby("machine")):
            row = dict(unit_level=level, scope=scope, n_fault=int(g.yf.sum()), n_normal=int((1 - g.yf).sum()))
            row.update({f: _auc(g.yf.values, g[f].values) for f in FEATURES})
            idrows.append(row)
    pd.DataFrame(idrows).to_csv(O / "step2b_identifiability_auroc.csv", index=False, float_format="%.3f")
    rules = {"pre-registered: self<=1 & stat<=0.5": (Hn.self <= 1) & (Hn.stat <= 0.5),
             "post-hoc: + cv<=0.10": (Hn.self <= 1) & (Hn.stat <= 0.5) & (Hn.cv <= 0.10),
             "cv<=0.10 alone": Hn.cv <= 0.10}
    rr = []
    for k, r in rules.items():
        for m, g in Hn.assign(p=r.values).groupby("machine"):
            f, n = g[g.cls == "fault"], g[g.cls == "normal"]
            rr.append(dict(rule=k, machine=m, n_fault=len(f), pass_fault=f.p.mean() if len(f) else np.nan,
                           n_normal=len(n), pass_normal=n.p.mean() if len(n) else np.nan))
    pd.DataFrame(rr).to_csv(O / "step2b_rule_pass_rates.csv", index=False, float_format="%.3f")
    ckp = pd.read_csv(E / "step2b_posthoc_checkpoints_labelled.csv.gz")
    allck = pd.concat([ck, ckp])
    dec = (allck[allck.decision == "PROMOTE"].groupby(["policy", "op", "cls"]).size().unstack(fill_value=0)
           .reindex(columns=["fault", "mixed", "normal"], fill_value=0).reset_index())
    dec.to_csv(O / "step2b_promotion_quality.csv", index=False)
    ep = pd.concat([pd.read_csv(E / "step2b_episode_trace.csv.gz"),
                    pd.read_csv(E / "step2b_posthoc_episode_trace.csv.gz")])
    key = ep[((ep.machine == "machine-1-6") & ep.start.isin([4647, 18600])) |
             ((ep.machine == "machine-3-7") & (ep.length >= 256)) | ((ep.machine == "machine-2-7") & (ep.length >= 256))]
    (key.groupby(["machine", "start", "length", "op", "policy"])[["written_frac", "ratio_vs_A", "point_recall"]].mean()
     .reset_index().to_csv(O / "step2b_key_episodes.csv", index=False, float_format="%.3f"))
    print("tables written to", O)


if __name__ == "__main__":
    main(*sys.argv[1:3])
