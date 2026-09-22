"""Bounded nonlinear observable-control audit on the frozen A+ cache.

This module reuses the A+ observation-only feature construction and fits only
the two preregistered arms with HistGradientBoostingClassifier.  It never
performs detector inference, writes the A+ cache, or touches reports/phase_g1.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from temporally_matched_observable_control import (  # noqa: E402
    ARCHITECTURES,
    CONDITIONS,
    FOLDS,
    SCENARIOS,
    SEEDS,
    _key_sha,
    arm_matrix,
    collect,
)

ARMS = ("H+O1r", "H+O1r+I")
MAX_ITER_GRID = (100, 300)
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 901
REFERENCE_ROOT = ROOT / "research" / "temporally_matched_observable_control"
LINEAR_REFERENCE = {
    "xlstm": {11: 0.02812832021330436, 22: 0.01629509034617682, 33: 0.03345956975022035},
    "lstm": {11: 0.011324541421041445, 22: 0.011944438377673006, 33: 0.009027893074030735},
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def estimator_parameters(max_iter: int) -> dict[str, Any]:
    if int(max_iter) not in MAX_ITER_GRID:
        raise ValueError(f"max_iter must be one of {MAX_ITER_GRID}")
    return {
        "loss": "log_loss",
        "learning_rate": 0.1,
        "max_leaf_nodes": 31,
        "max_depth": 6,
        "min_samples_leaf": 100,
        "l2_regularization": 1.0,
        "max_bins": 255,
        "categorical_features": None,
        "early_stopping": False,
        "random_state": 901,
        "class_weight": None,
        "max_iter": int(max_iter),
    }


def make_estimator(max_iter: int):
    from sklearn.ensemble import HistGradientBoostingClassifier

    return HistGradientBoostingClassifier(**estimator_parameters(max_iter))


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


def _historical_row_meta(architecture: str, seed: int) -> dict[str, Any]:
    path = REFERENCE_ROOT / "results" / f"results_{architecture}_{seed}.json"
    payload = json.loads(path.read_text())
    return payload["row_meta"]


def _verify_row_contract(records: dict[str, list[dict[str, np.ndarray]]], architecture: str, seed: int) -> dict[str, Any]:
    meta = _row_meta(records)
    historical = _historical_row_meta(architecture, seed)
    if meta != historical:
        raise RuntimeError(f"A+ row contract mismatch for {architecture}_{seed}")
    return meta


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


def _fit_candidate(train: dict[str, np.ndarray], validation: dict[str, np.ndarray], max_iter: int) -> dict[str, Any]:
    from sklearn.metrics import average_precision_score

    model = make_estimator(max_iter)
    if not np.isfinite(train["X"]).all() or not np.isfinite(validation["X"]).all():
        raise ValueError("non-finite features reached nonlinear probe")
    model.fit(train["X"], train["y"])
    validation_prediction = model.predict_proba(validation["X"])[:, 1]
    validation_ap = float(average_precision_score(validation["y"], validation_prediction))
    n_iter = int(getattr(model, "n_iter_", max_iter))
    metadata = {
        "max_iter": int(max_iter),
        "validation_AP": validation_ap,
        "n_iter": n_iter,
        "n_iter_equals_max_iter": bool(n_iter == max_iter),
        "early_stopping": False,
        "do_early_stopping": bool(getattr(model, "do_early_stopping_", False)),
        "parameters": estimator_parameters(max_iter),
    }
    del validation_prediction, model
    gc.collect()
    return metadata


def _fit_selected(test: dict[str, np.ndarray], train: dict[str, np.ndarray], max_iter: int) -> tuple[dict[str, Any], np.ndarray]:
    from sklearn.metrics import average_precision_score

    model = make_estimator(max_iter)
    model.fit(train["X"], train["y"])
    prediction = model.predict_proba(test["X"])[:, 1]
    selected = {
        "max_iter": int(max_iter),
        "validation_AP": None,
        "test_AP": float(average_precision_score(test["y"], prediction)),
        "n_iter": int(getattr(model, "n_iter_", max_iter)),
        "n_iter_equals_max_iter": bool(int(getattr(model, "n_iter_", max_iter)) == max_iter),
        "early_stopping": False,
        "do_early_stopping": bool(getattr(model, "do_early_stopping_", False)),
        "parameters": estimator_parameters(max_iter),
    }
    return selected, prediction


def _fit_arm(records: dict[str, list[dict[str, np.ndarray]]], arm: str, seed: int) -> dict[str, Any]:
    from sklearn import __version__ as sklearn_version

    stacked = {fold: arm_matrix(records[fold], arm) for fold in FOLDS}
    keys = {
        fold: _key_sha(
            stacked[fold]["source"],
            stacked[fold]["scenario"],
            stacked[fold]["condition"],
            stacked[fold]["timestamp"],
        )
        for fold in FOLDS
    }
    if any(keys[fold] != _row_meta(records)[fold]["key_sha256"] for fold in FOLDS):
        raise RuntimeError(f"row order changed while constructing {arm}")
    train, validation, test = (stacked[fold] for fold in ("train", "validation", "test"))
    candidates: list[dict[str, Any]] = []
    for max_iter in MAX_ITER_GRID:
        metadata = _fit_candidate(train, validation, max_iter)
        candidates.append(metadata)
    best_ap = max(candidate["validation_AP"] for candidate in candidates)
    selected_max_iter = min(candidate["max_iter"] for candidate in candidates if candidate["validation_AP"] == best_ap)
    gc.collect()
    selected, prediction = _fit_selected(test, train, selected_max_iter)
    selected["validation_AP"] = float(best_ap)
    result = {
        "arm": arm,
        "architecture": records.get("architecture", "unknown"),
        "detector_seed": int(seed),
        "sklearn_version": sklearn_version,
        "dimension": int(train["X"].shape[1]),
        "candidates": candidates,
        "selected": selected,
        "source_AP": _source_ap(test, prediction),
        "scenario_AP": _scenario_ap(test, prediction),
        "train_rows": int(len(train["y"])),
        "validation_rows": int(len(validation["y"])),
        "test_rows": int(len(test["y"])),
        "class_counts": {
            "train": np.bincount(train["y"], minlength=2).tolist(),
            "validation": np.bincount(validation["y"], minlength=2).tolist(),
            "test": np.bincount(test["y"], minlength=2).tolist(),
        },
        "row_key_sha256": keys,
    }
    del stacked, prediction
    gc.collect()
    return result


def run_one(cache_root: Path, architecture: str, seed: int, output: Path, protocol_seal: str) -> dict[str, Any]:
    if architecture not in ARCHITECTURES or seed not in SEEDS:
        raise ValueError("unregistered architecture or detector seed")
    cache_dir = (cache_root / f"{architecture}_{seed}").resolve()
    if not cache_dir.is_dir():
        raise FileNotFoundError(cache_dir)
    records = {fold: collect(cache_dir, fold) for fold in FOLDS}
    row_meta = _verify_row_contract(records, architecture, seed)
    for record_list in records.values():
        for record in record_list:
            if not np.isfinite(record["H"]).all() or not np.isfinite(record["O1r"]).all() or not np.isfinite(record["I"]).all():
                raise ValueError("non-finite A+ features")
    arms: dict[str, Any] = {}
    for arm in ARMS:
        arms[arm] = _fit_arm(records, arm, seed)
        arms[arm]["architecture"] = architecture
    delta = arms["H+O1r+I"]["selected"]["test_AP"] - arms["H+O1r"]["selected"]["test_AP"]
    source_effects = {
        source: None if arms["H+O1r"]["source_AP"][source] is None or arms["H+O1r+I"]["source_AP"][source] is None else arms["H+O1r+I"]["source_AP"][source] - arms["H+O1r"]["source_AP"][source]
        for source in arms["H+O1r"]["source_AP"]
    }
    scenario_effects = {
        scenario: arms["H+O1r+I"]["scenario_AP"].get(scenario, float("nan")) - arms["H+O1r"]["scenario_AP"].get(scenario, float("nan"))
        for scenario in SCENARIOS
    }
    result = {
        "status": "exploratory_nonlinear_observable_control_run",
        "protocol_seal": protocol_seal,
        "architecture": architecture,
        "detector_seed": int(seed),
        "cache_read_only": True,
        "no_detector_inference": True,
        "row_meta": row_meta,
        "arms": arms,
        "primary": {
            "contrast": "AP(H+O1r+I) - AP(H+O1r)",
            "pooled_test_delta": float(delta),
            "source_effects": source_effects,
            "scenario_effects": scenario_effects,
            "positive_source_count": int(sum(value is not None and value > 0 for value in source_effects.values())),
            "source_at_or_above_reference_count": int(sum(value is not None and value >= 0.02 for value in source_effects.values())),
        },
        "linear_A_plus_S2_reference": LINEAR_REFERENCE[architecture][seed],
    }
    atomic_json_write(output, result)
    return result


def crossed_bootstrap(matrix: np.ndarray, draws: int = BOOTSTRAP_DRAWS, seed: int = BOOTSTRAP_SEED) -> dict[str, Any]:
    values = np.asarray(matrix, dtype=np.float64)
    if values.ndim != 2 or values.shape != (10, 3) or not np.isfinite(values).all():
        raise ValueError("expected finite [10,3] source-by-seed matrix")
    rng = np.random.default_rng(seed)
    source_indices = rng.integers(0, values.shape[0], size=(draws, values.shape[0]))
    seed_indices = rng.integers(0, values.shape[1], size=(draws, values.shape[1]))
    sampled = values[source_indices[:, :, None], seed_indices[:, None, :]]
    means = sampled.mean(axis=(1, 2))
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {"method": "crossed_source_rows_seed_columns", "draws": draws, "seed": seed, "mean": float(values.mean()), "ci95": [float(lo), float(hi)]}


def source_only_bootstrap(matrix: np.ndarray, draws: int = BOOTSTRAP_DRAWS, seed: int = BOOTSTRAP_SEED) -> dict[str, Any]:
    values = np.asarray(matrix, dtype=np.float64)
    if values.ndim != 2 or values.shape != (10, 3) or not np.isfinite(values).all():
        raise ValueError("expected finite [10,3] source-by-seed matrix")
    rng = np.random.default_rng(seed)
    source_indices = rng.integers(0, values.shape[0], size=(draws, values.shape[0]))
    means = values[source_indices].mean(axis=(1, 2))
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {"method": "source_only_condition_on_three_observed_seeds", "draws": draws, "seed": seed, "mean": float(values.mean()), "ci95": [float(lo), float(hi)]}


def aggregate(output_dir: Path, output: Path, protocol_seal: str) -> dict[str, Any]:
    from sklearn import __version__ as sklearn_version

    loaded: dict[tuple[str, int], dict[str, Any]] = {}
    for architecture in ARCHITECTURES:
        for seed in SEEDS:
            path = output_dir / f"results_{architecture}_{seed}.json"
            if not path.exists():
                raise FileNotFoundError(path)
            payload = json.loads(path.read_text())
            if payload.get("protocol_seal") != protocol_seal:
                raise ValueError(f"protocol seal mismatch in {path}")
            loaded[(architecture, seed)] = payload
    aggregate_result: dict[str, Any] = {
        "status": "exploratory_nonlinear_observable_control_complete",
        "protocol_seal": protocol_seal,
        "sklearn_version": sklearn_version,
        "historical_reports_phase_g1_modified": False,
        "architectures": {},
        "linear_A_plus_S2_reference": LINEAR_REFERENCE,
        "uncertainty_note": "Only three detector-seed levels are observed; crossed intervals are exploratory and not precisely calibrated population confidence intervals.",
    }
    for architecture in ARCHITECTURES:
        matrix = np.asarray([
            [loaded[(architecture, seed)]["primary"]["source_effects"][str(source)] for seed in SEEDS]
            for source in FOLDS["test"]
        ], dtype=np.float64)
        pooled = {str(seed): loaded[(architecture, seed)]["primary"]["pooled_test_delta"] for seed in SEEDS}
        scenario_matrix = {
            scenario: {str(seed): loaded[(architecture, seed)]["primary"]["scenario_effects"][scenario] for seed in SEEDS}
            for scenario in SCENARIOS
        }
        aggregate_result["architectures"][architecture] = {
            "source_seed_matrix": matrix.tolist(),
            "source_level_mean_effect": float(matrix.mean()),
            "median": float(np.median(matrix)),
            "min": float(matrix.min()),
            "max": float(matrix.max()),
            "pooled_test_delta_by_seed": pooled,
            "detector_seed_means": {str(seed): float(matrix[:, i].mean()) for i, seed in enumerate(SEEDS)},
            "source_means": {str(source): float(matrix[i].mean()) for i, source in enumerate(FOLDS["test"])},
            "positive_source_seed_units": int(np.sum(matrix > 0)),
            "at_or_above_reference_source_seed_units": int(np.sum(matrix >= 0.02)),
            "scenario_effects_by_seed": scenario_matrix,
            "scenario_mean_effects": {scenario: float(np.mean(list(values.values()))) for scenario, values in scenario_matrix.items()},
            "selected_max_iter": {
                str(seed): {arm: loaded[(architecture, seed)]["arms"][arm]["selected"]["max_iter"] for arm in ARMS}
                for seed in SEEDS
            },
            "bootstrap_crossed": crossed_bootstrap(matrix),
            "bootstrap_source_only": source_only_bootstrap(matrix),
            "linear_reference_effect_by_seed": LINEAR_REFERENCE[architecture],
        }
    aggregate_result["interpretation"] = {
        "confirmatory": False,
        "no_information_theoretic_claim": True,
        "no_xlstm_superiority_claim": True,
        "comparison": "nonlinear incremental AP versus historical linear A+S S2 incremental AP",
    }
    atomic_json_write(output, aggregate_result)
    return aggregate_result


def preflight(cache_root: Path, output: Path, protocol_seal: str) -> dict[str, Any]:
    import sklearn

    manifests: dict[str, Any] = {}
    for architecture in ARCHITECTURES:
        for seed in SEEDS:
            cache_dir = (cache_root / f"{architecture}_{seed}").resolve()
            manifest_path = cache_dir / f"manifest_{architecture}_{seed}.json"
            if not cache_dir.is_dir() or not manifest_path.exists():
                raise FileNotFoundError(cache_dir)
            payload = json.loads(manifest_path.read_text())
            manifests[f"{architecture}_{seed}"] = {
                "cache_dir": str(cache_dir),
                "manifest": str(manifest_path),
                "manifest_sha256": sha256_file(manifest_path),
                "status": payload.get("status"),
                "stream_count": payload.get("stream_count", len(payload.get("streams", []))),
            }
    row_counts = {"train": 697430, "validation": 348715, "test": 697430}
    dimensions = {"H+O1r": 1678, "H+O1r+I": 1912}
    memory = {
        arm: {fold: int(row_counts[fold] * dimension * 4) for fold in FOLDS}
        for arm, dimension in dimensions.items()
    }
    result = {
        "status": "label_blind_nonlinear_preflight",
        "protocol_seal": protocol_seal,
        "python": sys.version,
        "platform": platform.platform(),
        "sklearn_version": sklearn.__version__,
        "estimator_parameters": {str(max_iter): estimator_parameters(max_iter) for max_iter in MAX_ITER_GRID},
        "folds": {fold: list(sources) for fold, sources in FOLDS.items()},
        "scenarios": list(SCENARIOS),
        "conditions": list(CONDITIONS),
        "architectures": list(ARCHITECTURES),
        "detector_seeds": list(SEEDS),
        "rows": row_counts,
        "feature_dimensions": dimensions,
        "approximate_feature_matrix_bytes": memory,
        "cache_manifests": manifests,
        "early_stopping": False,
        "label_blind": True,
        "no_nonlinear_fit": True,
    }
    atomic_json_write(output, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("preflight")
    p.add_argument("--cache-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--protocol-seal", required=True)
    p = sub.add_parser("fit-one")
    p.add_argument("--cache-root", type=Path, required=True)
    p.add_argument("--architecture", choices=ARCHITECTURES, required=True)
    p.add_argument("--seed", type=int, choices=SEEDS, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--protocol-seal", required=True)
    p = sub.add_parser("aggregate")
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--protocol-seal", required=True)
    args = parser.parse_args()
    if args.command == "preflight":
        preflight(args.cache_root.resolve(), args.output, args.protocol_seal)
    elif args.command == "fit-one":
        run_one(args.cache_root.resolve(), args.architecture, args.seed, args.output, args.protocol_seal)
    else:
        aggregate(args.output_dir, args.output, args.protocol_seal)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
