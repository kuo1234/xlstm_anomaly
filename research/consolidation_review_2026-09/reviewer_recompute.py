"""Reviewer re-aggregation for the post-G1 control-line consolidation review.

Pure re-aggregation of committed artifacts.  No fitting, no cache access, no
detector inference.  Run from the repository root:

    python research/consolidation_review_2026-09/reviewer_recompute.py

Inputs (all committed, read-only):
  research/temporally_matched_observable_control/results/results_{arch}_{seed}.json   (A+, linear)
  research/aplus_solver_convergence_audit/s2/s2_{arch}_{seed}.json                     (A+S S2, linear)
  research/nonlinear_observable_control/runs/results_{arch}_{seed}.json                (HGB)
  research/nonlinear_observable_control/results.json                                   (HGB aggregate)

Output: research/consolidation_review_2026-09/reviewer_numbers.csv
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ARCH = ("xlstm", "lstm")
SEEDS = (11, 22, 33)
SOURCES = tuple(str(s) for s in range(3000, 3010))
DRAWS, SEED = 10_000, 901
APLUS = ROOT / "research/temporally_matched_observable_control/results"
S2 = ROOT / "research/aplus_solver_convergence_audit/s2"
NL = ROOT / "research/nonlinear_observable_control"
OUT = ROOT / "research/consolidation_review_2026-09/reviewer_numbers.csv"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def crossed(matrix: np.ndarray) -> tuple[float, float]:
    """Identical to crossed_bootstrap() in the A+S and nonlinear scripts."""
    rng = np.random.default_rng(SEED)
    si = rng.integers(0, matrix.shape[0], size=(DRAWS, matrix.shape[0]))
    sj = rng.integers(0, matrix.shape[1], size=(DRAWS, matrix.shape[1]))
    means = matrix[si[:, :, None], sj[:, None, :]].mean(axis=(1, 2))
    lo, hi = np.quantile(means, [0.025, 0.975])
    return float(lo), float(hi)


def crossed_difference(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    """xLSTM minus LSTM: test sources shared, detector-seed columns resampled
    independently per backbone (seed labels are not a natural pairing)."""
    rng = np.random.default_rng(SEED)
    si = rng.integers(0, 10, size=(DRAWS, 10))
    sa = rng.integers(0, 3, size=(DRAWS, 3))
    sb = rng.integers(0, 3, size=(DRAWS, 3))
    da = a[si[:, :, None], sa[:, None, :]].mean(axis=(1, 2))
    db = b[si[:, :, None], sb[:, None, :]].mean(axis=(1, 2))
    lo, hi = np.quantile(da - db, [0.025, 0.975])
    return float(lo), float(hi)


def main() -> int:
    nl_runs = {(a, s): load(NL / "runs" / f"results_{a}_{s}.json") for a in ARCH for s in SEEDS}
    nl_agg = load(NL / "results.json")
    rows: list[dict[str, object]] = []

    def put(name: str, arch: str, value: float, note: str = "") -> None:
        rows.append({"quantity": name, "architecture": arch, "value": f"{value:.8f}", "note": note})

    matrices_nl, matrices_lin = {}, {}
    for a in ARCH:
        nl = np.array([[nl_runs[(a, s)]["primary"]["source_effects"][src] for s in SEEDS] for src in SOURCES])
        lin = np.array([[load(APLUS / f"results_{a}_{s}.json")["primary"]["source_effects"][src] for s in SEEDS] for src in SOURCES])
        assert np.array_equal(nl, np.array(nl_agg["architectures"][a]["source_seed_matrix"]))
        matrices_nl[a], matrices_lin[a] = nl, lin

        # 1. Reproduce the committed nonlinear crossed interval exactly.
        lo, hi = crossed(nl)
        committed = nl_agg["architectures"][a]["bootstrap_crossed"]["ci95"]
        assert abs(lo - committed[0]) < 1e-12 and abs(hi - committed[1]) < 1e-12
        put("nl_source_level_mean", a, nl.mean())
        put("nl_crossed_lo", a, lo, "reproduces committed results.json exactly")
        put("nl_crossed_hi", a, hi, "reproduces committed results.json exactly")
        put("nl_seed_main_effect_sd", a, nl.mean(axis=0).std(ddof=1))
        put("aplus_linear_seed_main_effect_sd", a, lin.mean(axis=0).std(ddof=1))

        # 2. Like-for-like pooled comparison with A+S S2 (S2 has no source-level matrix).
        lin_base, lin_full, nl_base, nl_full = [], [], [], []
        val100, val300 = [], []
        for s in SEEDS:
            s2 = load(S2 / f"s2_{a}_{s}.json")["arms"]
            lin_base.append(s2["H+O1r"]["selected_final"]["test_AP"])
            lin_full.append(s2["H+O1r+I"]["selected_final"]["test_AP"])
            arms = nl_runs[(a, s)]["arms"]
            nl_base.append(arms["H+O1r"]["selected"]["test_AP"])
            nl_full.append(arms["H+O1r+I"]["selected"]["test_AP"])
            cand = {arm: {c["max_iter"]: c["validation_AP"] for c in arms[arm]["candidates"]} for arm in arms}
            val100.append(cand["H+O1r+I"][100] - cand["H+O1r"][100])
            val300.append(cand["H+O1r+I"][300] - cand["H+O1r"][300])
        lin_base, lin_full, nl_base, nl_full = map(np.array, (lin_base, lin_full, nl_base, nl_full))
        lin_d, nl_d = (lin_full - lin_base).mean(), (nl_full - nl_base).mean()
        put("s2_linear_mean_pooled_delta", a, lin_d, "the +0.02596099 / +0.01076562 reference is this estimand")
        put("nl_mean_pooled_delta", a, nl_d)
        put("pooled_like_for_like_change", a, nl_d - lin_d)
        put("pooled_like_for_like_relative_change", a, nl_d / lin_d - 1)
        put("mixed_estimand_change_as_documented", a, nl.mean() - lin_d, "source-level NL minus pooled S2")
        put("s2_linear_mean_AP_H+O1r", a, lin_base.mean())
        put("s2_linear_mean_AP_H+O1r+I", a, lin_full.mean())
        put("nl_mean_AP_H+O1r", a, nl_base.mean())
        put("nl_mean_AP_H+O1r+I", a, nl_full.mean())
        put("decoder_gain_observable_arm", a, (nl_base - lin_base).mean(), "HGB minus S2 linear, H+O1r")
        put("decoder_gain_full_arm", a, (nl_full - lin_full).mean(), "HGB minus S2 linear, H+O1r+I")
        put("nl_headroom_normalised_increment", a, ((nl_full - nl_base) / (1 - nl_base)).mean(), "delta / (1 - AP(H+O1r))")
        put("s2_headroom_normalised_increment", a, ((lin_full - lin_base) / (1 - lin_base)).mean())
        put("nl_validation_delta_fixed_max_iter_100", a, float(np.mean(val100)), "validation fold, descriptive")
        put("nl_validation_delta_fixed_max_iter_300", a, float(np.mean(val300)), "validation fold, descriptive")

        # 3. Source-level paired attenuation versus the A+ linear matrix (same cells).
        diff = nl - lin
        lo, hi = crossed(diff)
        put("source_level_change_vs_aplus_linear", a, diff.mean(), "HGB minus A+ (C grid 4, max_iter 1000)")
        put("source_level_change_crossed_lo", a, lo)
        put("source_level_change_crossed_hi", a, hi)
        put("cells_attenuated_vs_aplus_linear", a, float((diff < 0).sum()), "of 30")
        put("nl_cells_at_or_above_0p02", a, float((nl >= 0.02).sum()), "of 30; descriptive reference only")

    # 4. Backbone difference (not a superiority test; baselines differ by backbone).
    for label, mats in (("nl", matrices_nl), ("aplus_linear", matrices_lin)):
        lo, hi = crossed_difference(mats["xlstm"], mats["lstm"])
        put(f"{label}_xlstm_minus_lstm_increment", "both", mats["xlstm"].mean() - mats["lstm"].mean())
        put(f"{label}_xlstm_minus_lstm_crossed_lo", "both", lo)
        put(f"{label}_xlstm_minus_lstm_crossed_hi", "both", hi)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["quantity", "architecture", "value", "note"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
