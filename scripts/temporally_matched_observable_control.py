"""A+ temporally matched observable-control analysis.

The strong-observable experiment stores one dense, observation-only O1 row for
every W=64 decision.  A+ applies the *same* causal feature-wise rolling
operator used by ``internal234`` to that O1 sequence.  No model inference is
performed here: the existing cache is read-only and evaluator rows are joined
only after the observation arrays have been loaded.

The two new arms are fitted one at a time to keep the high-dimensional O1r
working set bounded:

    H+O1r
    H+O1r+I

H/H+I and the historical raw O1/O2 arms are copied from their committed
strong-observable summaries as read-only references.  This module never writes
to ``reports/phase_g1`` and never modifies a checkpoint or cache.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from strong_observable_control import (  # noqa: E402
    ARCHITECTURES,
    C_GRID,
    CONDITIONS,
    FOLDS,
    SCENARIOS,
    SEEDS,
    _fit_arm,
    _rolling,
    _stream_name,
    _truth_rows,
    array_sha,
    expand_internal,
    history14,
)

WINDOW = 64
DECISION_START = WINDOW - 1
ROLLING_WIDTHS = (4, 8, 16, 32)
O1_BASE_DIM = 128
O1R_DIM = O1_BASE_DIM * (1 + 3 * len(ROLLING_WIDTHS))
INTERNAL_DIM = 234
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 901
ATOL, RTOL = 1e-5, 1e-4

REFERENCE_ROOT = ROOT / "research" / "strong_observable_control"


def _key_sha(source: np.ndarray, scenario: np.ndarray, condition: np.ndarray, timestamp: np.ndarray) -> str:
    """Hash ordered row keys without serializing a potentially huge JSON list."""
    n = len(timestamp)
    dtype = np.dtype([
        ("source", "<i4"),
        ("scenario", "S16"),
        ("condition", "S16"),
        ("timestamp", "<i8"),
    ])
    keys = np.empty(n, dtype=dtype)
    keys["source"] = np.asarray(source, dtype=np.int32)
    keys["scenario"] = np.asarray([str(x).encode("utf-8") for x in scenario], dtype="S16")
    keys["condition"] = np.asarray([str(x).encode("utf-8") for x in condition], dtype="S16")
    keys["timestamp"] = np.asarray(timestamp, dtype=np.int64)
    return array_sha(keys)


def expand_o1r(base_o1: np.ndarray) -> np.ndarray:
    """Apply the internal234 feature-major causal expansion to every O1 column.

    For a base column ``j`` the output order is:
    ``current, mean/std/slope(width=4), ..., mean/std/slope(width=32)``.
    This is intentionally feature-major, matching ``expand_internal`` rather
    than the grouped-column layout returned by ``_rolling``.
    """
    base = np.asarray(base_o1, dtype=np.float64)
    if base.ndim != 2 or base.shape[1] != O1_BASE_DIM:
        raise ValueError(f"expected [N,{O1_BASE_DIM}] O1 rows, got {base.shape}")
    if not np.isfinite(base).all():
        raise ValueError("O1 rows must be finite before temporal expansion")
    # Compute each width once for all 128 columns, then transpose the grouped
    # rolling layout into the feature-major layout required by internal234.
    # This is mathematically identical to applying ``expand_internal`` to one
    # scalar column at a time, but avoids 512 Python/Numpy kernel dispatches
    # per stream.
    grouped = np.concatenate((base, *(_rolling(base, width) for width in ROLLING_WIDTHS)), axis=1)
    expanded = grouped.reshape(len(base), 1 + 3 * len(ROLLING_WIDTHS), O1_BASE_DIM)
    expanded = np.transpose(expanded, (0, 2, 1)).reshape(len(base), O1R_DIM)
    if expanded.shape != (len(base), O1R_DIM):
        raise RuntimeError(f"O1r schema drift: {expanded.shape}")
    return expanded


def _make_records(cache_dir: Path, fold: str, source: int, scenario: str, condition: str) -> dict[str, np.ndarray] | None:
    """Load one observation cache stream, then join evaluator rows.

    The cache contains no labels.  This function keeps the boundary explicit:
    feature construction happens from arrays first; ``generate`` is called
    only for the post-extraction primary cohort mask.
    """
    from m0.synthetic import generate

    target = cache_dir / _stream_name(fold, source, scenario, condition)
    with np.load(target, allow_pickle=False) as loaded:
        timestamp = np.asarray(loaded["timestamp"], dtype=np.int64)
        score = np.asarray(loaded["score"], dtype=np.float64)
        internal_base = np.asarray(loaded["internal_base18"], dtype=np.float64)
        o1 = np.asarray(loaded["o1"], dtype=np.float64)
    if not np.array_equal(timestamp, np.arange(DECISION_START, DECISION_START + len(timestamp), dtype=np.int64)):
        raise ValueError(f"non-contiguous/right-edge timestamp stream: {target}")
    if internal_base.shape != (len(timestamp), 18) or o1.shape != (len(timestamp), O1_BASE_DIM):
        raise ValueError(f"cache schema mismatch in {target}")

    # Observation-only feature construction.  The temporal transform is done
    # before any evaluator mask, so filtering cannot compress the time axis.
    h = history14(score)
    internal = expand_internal(internal_base)
    o1r = expand_o1r(o1)
    finite = np.isfinite(h).all(1) & np.isfinite(internal).all(1) & np.isfinite(o1r).all(1)

    stream = generate(source, scenario, condition)
    truth = _truth_rows(stream, timestamp)
    primary = np.isin(truth["stratum"], ("anomaly", "drift"))
    keep = finite & primary
    if not np.any(keep):
        return None
    count = int(keep.sum())
    return {
        "H": h[keep].astype(np.float32),
        "I": internal[keep].astype(np.float32),
        "O1r": o1r[keep].astype(np.float32),
        "y": np.asarray(truth["label"], dtype=np.int8)[keep],
        "source": np.full(count, source, dtype=np.int32),
        "scenario": np.asarray([scenario] * count, dtype=object),
        "condition": np.asarray([condition] * count, dtype=object),
        "timestamp": timestamp[keep],
    }


def collect(cache_dir: Path, fold: str) -> list[dict[str, np.ndarray]]:
    records: list[dict[str, np.ndarray]] = []
    for source in FOLDS[fold]:
        for scenario in SCENARIOS:
            for condition in CONDITIONS:
                record = _make_records(cache_dir, fold, source, scenario, condition)
                if record is not None:
                    records.append(record)
    if not records:
        raise RuntimeError(f"no valid records for fold {fold}")
    return records


def arm_matrix(records: list[dict[str, np.ndarray]], arm: str) -> dict[str, np.ndarray]:
    if arm not in {"H+O1r", "H+O1r+I"}:
        raise ValueError(f"A+ fitting arm not supported: {arm}")
    matrices: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    sources: list[np.ndarray] = []
    scenarios: list[np.ndarray] = []
    conditions: list[np.ndarray] = []
    timestamps: list[np.ndarray] = []
    for record in records:
        x = np.concatenate(
            (record["H"], record["O1r"], record["I"])
            if arm == "H+O1r+I" else (record["H"], record["O1r"]),
            axis=1,
        )
        matrices.append(x)
        ys.append(record["y"])
        sources.append(record["source"])
        scenarios.append(record["scenario"])
        conditions.append(record["condition"])
        timestamps.append(record["timestamp"])
    return {
        "X": np.concatenate(matrices),
        "y": np.concatenate(ys),
        "source": np.concatenate(sources),
        "scenario": np.concatenate(scenarios),
        "condition": np.concatenate(conditions),
        "timestamp": np.concatenate(timestamps),
    }


def _scenario_ap(test: dict[str, np.ndarray], prediction: np.ndarray) -> dict[str, float]:
    from sklearn.metrics import average_precision_score

    result: dict[str, float] = {}
    for scenario in SCENARIOS:
        mask = test["scenario"] == scenario
        if np.unique(test["y"][mask]).size == 2:
            result[scenario] = float(average_precision_score(test["y"][mask], prediction[mask]))
    return result


def _source_ap(test: dict[str, np.ndarray], prediction: np.ndarray) -> dict[str, float | None]:
    from sklearn.metrics import average_precision_score

    result: dict[str, float | None] = {}
    for source in FOLDS["test"]:
        mask = test["source"] == source
        result[str(source)] = (
            float(average_precision_score(test["y"][mask], prediction[mask]))
            if np.unique(test["y"][mask]).size == 2 else None
        )
    return result


def _fit_new_arm(stacked: dict[str, dict[str, np.ndarray]], arm: str, seed: int) -> tuple[dict[str, Any], dict[str, Any]]:
    info, prediction = _fit_arm(stacked["train"], stacked["validation"], stacked["test"], arm, seed)
    info["scenario_AP"] = _scenario_ap(stacked["test"], prediction)
    info["source_AP"] = _source_ap(stacked["test"], prediction)
    return info, prediction


def _reference(seed: int, architecture: str) -> dict[str, Any]:
    path = REFERENCE_ROOT / f"results_{architecture}_{seed}.json"
    payload = json.loads(path.read_text())
    return {
        "path": str(path.relative_to(ROOT)),
        "arms": {name: payload["arms"][name]["test_AP"] for name in payload["arms"]},
        "increments": payload["increments"],
        "rows": payload["rows"],
        "feature_dimensions": payload["feature_dimensions"],
        "source_AP": payload.get("source_AP"),
        "scenario_effects": payload.get("scenario_effects"),
    }


def _row_meta(records: dict[str, list[dict[str, np.ndarray]]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for fold, fold_records in records.items():
        source = np.concatenate([record["source"] for record in fold_records])
        scenario = np.concatenate([record["scenario"] for record in fold_records])
        condition = np.concatenate([record["condition"] for record in fold_records])
        timestamp = np.concatenate([record["timestamp"] for record in fold_records])
        result[fold] = {
            "rows": int(len(timestamp)),
            "key_sha256": _key_sha(source, scenario, condition, timestamp),
            "timestamp_min": int(timestamp.min()),
            "timestamp_max": int(timestamp.max()),
        }
    return result


def analyze(cache_dir: Path, seed: int, architecture: str, output: Path) -> dict[str, Any]:
    if seed not in SEEDS or architecture not in ARCHITECTURES:
        raise ValueError("unregistered seed or architecture")
    cache_dir = cache_dir.resolve()
    records = {fold: collect(cache_dir, fold) for fold in FOLDS}
    row_meta = _row_meta(records)
    reference = _reference(seed, architecture)
    for fold in FOLDS:
        if row_meta[fold]["rows"] != int(reference["rows"][fold]):
            raise RuntimeError(f"row count mismatch versus historical arm for {fold}")

    result: dict[str, Any] = {
        "status": "exploratory_temporally_matched_observable_control",
        "architecture": architecture,
        "detector_seed": seed,
        "protocol": "configs/temporally_matched_observable_control.json",
        "cache_read_only": True,
        "row_meta": row_meta,
        "reference_historical": reference,
        "new_arms": {},
        "primary": {},
    }
    fitted: dict[str, dict[str, Any]] = {}
    for arm in ("H+O1r", "H+O1r+I"):
        stacked = {fold: arm_matrix(records[fold], arm) for fold in FOLDS}
        # The two fitted arms must share the exact ordered rows.  The metadata
        # is recomputed from the actual matrices rather than assumed from the
        # record list.
        keys = {
            fold: _key_sha(stacked[fold]["source"], stacked[fold]["scenario"], stacked[fold]["condition"], stacked[fold]["timestamp"])
            for fold in FOLDS
        }
        if any(keys[fold] != row_meta[fold]["key_sha256"] for fold in FOLDS):
            raise RuntimeError(f"arm row-key mismatch for {arm}")
        info, prediction = _fit_new_arm(stacked, arm, seed)
        info["fold_key_sha256"] = keys
        result["new_arms"][arm] = info
        fitted[arm] = info
        print(f"fit {architecture} seed={seed} arm={arm} dim={info['dimension']} C={info['selected_C']} AP={info['test_AP']:.6f}", flush=True)
        del stacked, prediction
        gc.collect()

    left = float(fitted["H+O1r"]["test_AP"])
    right = float(fitted["H+O1r+I"]["test_AP"])
    source_effect = {
        source: (
            None if fitted["H+O1r"]["source_AP"][source] is None or fitted["H+O1r+I"]["source_AP"][source] is None
            else float(fitted["H+O1r+I"]["source_AP"][source] - fitted["H+O1r"]["source_AP"][source])
        )
        for source in fitted["H+O1r"]["source_AP"]
    }
    result["primary"] = {
        "contrast": "AP(H+O1r+I) - AP(H+O1r)",
        "test_AP_H+O1r": left,
        "test_AP_H+O1r+I": right,
        "delta": right - left,
        "source_effects": source_effect,
        "scenario_effects": {
            scenario: (
                fitted["H+O1r+I"]["scenario_AP"].get(scenario, float("nan"))
                - fitted["H+O1r"]["scenario_AP"].get(scenario, float("nan"))
            ) for scenario in SCENARIOS
        },
        "positive_source_count": int(sum(value is not None and value > 0 for value in source_effect.values())),
        "source_at_or_above_reference_count": int(sum(value is not None and value >= 0.02 for value in source_effect.values())),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


def _bootstrap(source_seed: np.ndarray, draws: int = BOOTSTRAP_DRAWS, seed: int = BOOTSTRAP_SEED) -> dict[str, Any]:
    values = np.asarray(source_seed, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] != 10 or values.shape[1] != 3 or not np.isfinite(values).all():
        raise ValueError("expected finite [10,3] source-by-seed effects")
    rng = np.random.default_rng(seed)
    source_indices = rng.integers(0, 10, size=(draws, 10))
    seed_indices = rng.integers(0, 3, size=(draws, 10, 3))
    sampled = values[source_indices[:, :, None], seed_indices]
    means = sampled.mean(axis=(1, 2))
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {"draws": draws, "seed": seed, "mean": float(values.mean()), "ci95": [float(lo), float(hi)]}


def aggregate(output_dir: Path, output: Path) -> dict[str, Any]:
    results: dict[str, dict[str, Any]] = {}
    for architecture in ARCHITECTURES:
        for seed in SEEDS:
            path = output_dir / f"results_{architecture}_{seed}.json"
            if not path.exists():
                raise FileNotFoundError(path)
            results[f"{architecture}_{seed}"] = json.loads(path.read_text())
    aggregate_result: dict[str, Any] = {
        "status": "exploratory_A_plus_complete",
        "protocol": "configs/temporally_matched_observable_control.json",
        "historical_reports_phase_g1_modified": False,
        "architectures": {},
        "bootstrap": {},
    }
    for architecture in ARCHITECTURES:
        matrix = np.asarray([
            [results[f"{architecture}_{seed}"]["primary"]["source_effects"][str(source)] for seed in SEEDS]
            for source in FOLDS["test"]
        ], dtype=np.float64)
        per_seed = {
            str(seed): float(results[f"{architecture}_{seed}"]["primary"]["delta"])
            for seed in SEEDS
        }
        source_means = matrix.mean(axis=1)
        seed_means = matrix.mean(axis=0)
        aggregate_result["architectures"][architecture] = {
            "per_seed": per_seed,
            "source_seed_matrix": matrix.tolist(),
            "mean": float(matrix.mean()),
            "median": float(np.median(matrix)),
            "min": float(matrix.min()),
            "max": float(matrix.max()),
            "detector_seed_means": {str(seed): float(value) for seed, value in zip(SEEDS, seed_means)},
            "source_means": {str(source): float(value) for source, value in zip(FOLDS["test"], source_means)},
            "positive_source_seed_units": int(np.sum(matrix > 0)),
            "source_seed_units": int(matrix.size),
            "at_or_above_reference_source_seed_units": int(np.sum(matrix >= 0.02)),
            "scenario_effects_by_seed": {
                str(seed): results[f"{architecture}_{seed}"]["primary"]["scenario_effects"] for seed in SEEDS
            },
            "dimensions": {
                "H+O1r": int(results[f"{architecture}_11"]["new_arms"]["H+O1r"]["dimension"]),
                "H+O1r+I": int(results[f"{architecture}_11"]["new_arms"]["H+O1r+I"]["dimension"]),
            },
            "historical_reference_by_seed": {
                str(seed): results[f"{architecture}_{seed}"]["reference_historical"] for seed in SEEDS
            },
        }
        aggregate_result["bootstrap"][architecture] = _bootstrap(matrix)
    means = {name: aggregate_result["architectures"][name]["mean"] for name in ARCHITECTURES}
    aggregate_result["interpretation"] = {
        "descriptive_rule": "internal234 > O1r if mean AP(H+O1r+I)-AP(H+O1r) >= 0.02 and at least 2/3 seed effects >= 0.02",
        "classification": {
            name: (
                "INTERNAL234_GT_O1R"
                if means[name] >= 0.02 and sum(value >= 0.02 for value in aggregate_result["architectures"][name]["per_seed"].values()) >= 2
                else "TEMPORAL_SPAN_EXPLANATION_NOT_DISPROVED"
            ) for name in ARCHITECTURES
        },
        "confirmatory": False,
        "no_holm_or_p_values": True,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(aggregate_result, indent=2, allow_nan=False) + "\n")
    return aggregate_result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("analyze")
    p.add_argument("--cache-dir", type=Path, required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--architecture", choices=ARCHITECTURES, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("aggregate")
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "analyze":
        analyze(args.cache_dir, args.seed, args.architecture, args.output)
    else:
        aggregate(args.output_dir, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
