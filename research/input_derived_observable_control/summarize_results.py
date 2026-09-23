"""Descriptive tables for the sealed P1r experiment (post-aggregation formatting only).

Written before any P1r result was inspected.  Reads the six committed run files,
their execution sidecars, the sealed aggregate and (for a descriptive baseline
comparison allowed by protocol.md) the committed nonlinear H+O1r runs.  Fits
nothing and adds no inferential analysis: the primary estimand, intervals and
outcome come unchanged from results.json.

    PYTHONPATH=.:scripts python research/input_derived_observable_control/summarize_results.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "input_derived_observable_control"
RUNS = OUT / "runs"
NL_RUNS = ROOT / "research" / "nonlinear_observable_control" / "runs"
APLUS = ROOT / "research" / "temporally_matched_observable_control" / "results"
ARCH = ("xlstm", "lstm")
SEEDS = (11, 22, 33)
SOURCES = tuple(str(s) for s in range(3000, 3010))
SCENARIOS = ("abrupt", "gradual", "recurring", "correlation")
ARMS = ("H+P1r", "H+P1r+I")
SEAL = "90b2470b45b1f8e52aa95ee8677b855b2e3c4e4d"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> int:
    agg = load(OUT / "results.json")
    reference_keys = {fold: meta["key_sha256"] for fold, meta in load(APLUS / "results_xlstm_11.json")["row_meta"].items()}
    summary: dict = {"protocol_seal": agg["protocol_seal"], "architectures": {}}
    rows = []
    for a in ARCH:
        runs = {s: load(RUNS / f"results_{a}_{s}.json") for s in SEEDS}
        sides = {s: load(RUNS / f"execution_{a}_{s}.json") for s in SEEDS}
        nl = {s: load(NL_RUNS / f"results_{a}_{s}.json") for s in SEEDS}
        matrix = np.array([[runs[s]["primary"]["source_effects"][src] for s in SEEDS] for src in SOURCES], dtype=float)
        assert np.array_equal(matrix, np.array(agg["architectures"][a]["source_seed_matrix"]))
        for s in SEEDS:
            rows.append({"architecture": a, "detector_seed": s, **{f"source_{src}": runs[s]["primary"]["source_effects"][src] for src in SOURCES}})
        arm = lambda s, k: runs[s]["arms"][k]  # noqa: E731
        integrity = {
            "protocol_seal_all_runs": sorted({r["protocol_seal"] for r in runs.values()}) == [SEAL],
            "row_keys_equal_aplus_all_arms": all(arm(s, k)["row_key_sha256"] == reference_keys for s in SEEDS for k in ARMS),
            "dimensions": {k: sorted({arm(s, k)["dimension"] for s in SEEDS}) for k in ARMS},
            "n_iter_equals_max_iter_all_fits": all(
                c["n_iter_equals_max_iter"] for s in SEEDS for k in ARMS for c in (*arm(s, k)["candidates"], arm(s, k)["selected"])
            ),
            "early_stopping_false_all_fits": all(
                not c["early_stopping"] and not c["do_early_stopping"] for s in SEEDS for k in ARMS for c in (*arm(s, k)["candidates"], arm(s, k)["selected"])
            ),
            "selected_is_validation_argmax_tie_100": all(
                arm(s, k)["selected"]["max_iter"] == min(c["max_iter"] for c in arm(s, k)["candidates"] if c["validation_AP"] == max(x["validation_AP"] for x in arm(s, k)["candidates"]))
                for s in SEEDS for k in ARMS
            ),
            "no_test_metric_in_candidates": all("test_AP" not in c for s in SEEDS for k in ARMS for c in arm(s, k)["candidates"]),
            "execution_hosts": sorted({x["execution_host"] for x in sides.values()}),
            "cache_unchanged_all_runs": all(x["cache_unchanged"] for x in sides.values()),
            "sklearn": sorted({x["sklearn"] for x in sides.values()}),
            "numpy": sorted({x["numpy"] for x in sides.values()}),
            "wall_seconds": {str(s): sides[s]["wall_seconds"] for s in SEEDS},
        }
        summary["architectures"][a] = {
            "source_level_mean": float(matrix.mean()),
            "bootstrap_crossed_ci95": agg["architectures"][a]["bootstrap_crossed"]["ci95"],
            "bootstrap_source_only_ci95": agg["architectures"][a]["bootstrap_source_only"]["ci95"],
            "outcome": agg["architectures"][a]["outcome"],
            "positive_cells": int((matrix > 0).sum()),
            "cells_at_or_above_0p02_descriptive": int((matrix >= 0.02).sum()),
            "min_cell": float(matrix.min()), "max_cell": float(matrix.max()),
            "per_source_mean": {src: float(matrix[i].mean()) for i, src in enumerate(SOURCES)},
            "per_seed_mean": {str(s): float(matrix[:, j].mean()) for j, s in enumerate(SEEDS)},
            "pooled_delta_by_seed_descriptive": {str(s): runs[s]["primary"]["pooled_test_delta_descriptive"] for s in SEEDS},
            "test_AP_by_seed": {str(s): {k: arm(s, k)["selected"]["test_AP"] for k in ARMS} for s in SEEDS},
            "validation_AP_candidates": {str(s): {k: {str(c["max_iter"]): c["validation_AP"] for c in arm(s, k)["candidates"]} for k in ARMS} for s in SEEDS},
            "selected_max_iter": {str(s): {k: arm(s, k)["selected"]["max_iter"] for k in ARMS} for s in SEEDS},
            "scenario_mean_effects_descriptive": {
                sc: float(np.mean([runs[s]["primary"]["scenario_effects"][sc] for s in SEEDS])) for sc in SCENARIOS
            },
            "descriptive_baseline_comparison": {
                str(s): {
                    "AP_H+P1r": arm(s, "H+P1r")["selected"]["test_AP"],
                    "AP_H+O1r_nonlinear": nl[s]["arms"]["H+O1r"]["selected"]["test_AP"],
                    "AP_H+P1r+I": arm(s, "H+P1r+I")["selected"]["test_AP"],
                    "AP_H+O1r+I_nonlinear": nl[s]["arms"]["H+O1r+I"]["selected"]["test_AP"],
                }
                for s in SEEDS
            },
            "integrity": integrity,
        }
    with (OUT / "source_seed_effects.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["architecture", "detector_seed", *[f"source_{s}" for s in SOURCES]], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "descriptive_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
