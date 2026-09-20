#!/usr/bin/env python3
"""Aggregate fixed strong-observable-control probe outputs.

This is a reporting-only companion to ``strong_observable_control.py``.  It
does not read labels or model artifacts and never refits a probe; it consumes
the six compact per-seed JSON summaries produced by the fixed analysis.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


SEEDS = (11, 22, 33)
ARCHITECTURES = ("xlstm", "lstm")
SCENARIOS = ("abrupt", "gradual", "recurring", "correlation")
PRIMARY_INCREMENT = "I_given_H+O2"
PRACTICAL_REFERENCE = 0.02


def _load(directory: Path, architecture: str, seed: int) -> dict:
    path = directory / f"results_{architecture}_{seed}.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text())
    if value.get("architecture") != architecture or value.get("detector_seed") != seed:
        raise ValueError(f"metadata mismatch in {path}")
    return value


def _bootstrap(matrix: np.ndarray, draws: int = 10_000, seed: int = 901) -> dict:
    """Source-first, detector-seed-second exploratory bootstrap.

    ``matrix`` has shape [test source, detector seed].  The resampling order is
    explicit so the summary is reproducible and remains a descriptive
    uncertainty interval rather than a confirmatory test.
    """

    if matrix.ndim != 2:
        raise ValueError("bootstrap matrix must be two-dimensional")
    rng = np.random.default_rng(seed)
    source_indices = rng.integers(0, matrix.shape[0], size=(draws, matrix.shape[0]))
    seed_indices = rng.integers(0, matrix.shape[1], size=(draws, matrix.shape[1]))
    sampled = matrix[source_indices[:, :, None], seed_indices[:, None, :]]
    means = sampled.mean(axis=(1, 2))
    return {
        "draws": draws,
        "seed": seed,
        "resampling": "source first, detector seeds second; whole source units retained",
        "mean": float(means.mean()),
        "ci95": [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))],
    }


def _summary(values: np.ndarray) -> dict:
    flat = values[np.isfinite(values)]
    if flat.size == 0:
        raise ValueError("no finite effects")
    return {
        "mean": float(flat.mean()),
        "median": float(np.median(flat)),
        "min": float(flat.min()),
        "max": float(flat.max()),
        "positive_units": int(np.sum(flat > 0)),
        "units": int(flat.size),
        "above_practical_reference": int(np.sum(flat >= PRACTICAL_REFERENCE)),
        "practical_reference": PRACTICAL_REFERENCE,
    }


def aggregate(directory: Path) -> dict:
    loaded = {
        arch: {seed: _load(directory, arch, seed) for seed in SEEDS}
        for arch in ARCHITECTURES
    }
    result: dict = {
        "status": "exploratory_post_g1_strong_observable_control",
        "input_directory": str(directory),
        "seeds": list(SEEDS),
        "architectures": list(ARCHITECTURES),
        "primary_arm_contrast": "AP(H+O2+I) - AP(H+O2)",
        "no_confirmatory_p_values": True,
        "architectures_summary": {},
    }
    for arch in ARCHITECTURES:
        per_seed = loaded[arch]
        arms = {
            str(seed): {
                arm: float(per_seed[seed]["arms"][arm]["test_AP"])
                for arm in ("H", "H+I", "H+O1", "H+O1+I", "H+O2", "H+O2+I")
            }
            for seed in SEEDS
        }
        increments = {
            str(seed): {name: float(value) for name, value in per_seed[seed]["increments"].items()}
            for seed in SEEDS
        }
        sources = sorted(next(iter(per_seed.values()))["source_effects"][PRIMARY_INCREMENT], key=int)
        source_matrix = np.asarray(
            [[per_seed[seed]["source_effects"][PRIMARY_INCREMENT][source] for seed in SEEDS] for source in sources],
            dtype=float,
        )
        scenario = {
            name: {
                "by_seed": {str(seed): float(per_seed[seed]["scenario_effects"]["H+O2+I"].get(name, np.nan) - per_seed[seed]["scenario_effects"]["H+O2"].get(name, np.nan)) for seed in SEEDS},
                "mean": float(np.nanmean([per_seed[seed]["scenario_effects"]["H+O2+I"].get(name, np.nan) - per_seed[seed]["scenario_effects"]["H+O2"].get(name, np.nan) for seed in SEEDS])),
            }
            for name in SCENARIOS
        }
        source_means = source_matrix.mean(axis=1)
        seed_means = source_matrix.mean(axis=0)
        flat_summary = _summary(source_matrix)
        result["architectures_summary"][arch] = {
            "arm_AP_by_seed": arms,
            "increment_by_seed": increments,
            "primary_by_seed": {str(seed): float(per_seed[seed]["increments"][PRIMARY_INCREMENT]) for seed in SEEDS},
            "primary_seed_mean": float(np.mean([per_seed[seed]["increments"][PRIMARY_INCREMENT] for seed in SEEDS])),
            "primary_seed_median": float(np.median([per_seed[seed]["increments"][PRIMARY_INCREMENT] for seed in SEEDS])),
            "primary_source_seed_matrix": {str(source): {str(seed): float(source_matrix[i, j]) for j, seed in enumerate(SEEDS)} for i, source in enumerate(sources)},
            "primary_source_means": {str(source): float(source_means[i]) for i, source in enumerate(sources)},
            "primary_detector_seed_means": {str(seed): float(seed_means[j]) for j, seed in enumerate(SEEDS)},
            "primary_summary_over_source_seed_units": flat_summary,
            "primary_bootstrap": _bootstrap(source_matrix),
            "scenario_primary_effect": scenario,
            "feature_dimensions": next(iter(per_seed.values()))["feature_dimensions"],
            "rows": next(iter(per_seed.values()))["rows"],
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = aggregate(args.results_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
