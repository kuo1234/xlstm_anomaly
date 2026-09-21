"""A+S convergence and uncertainty audit.

This module deliberately reuses the committed A+ observation/cache and feature
construction code. It never runs model inference and never writes historical
G1 or A+ result files. S0 is metric-only reaggregation; S1/S2 refit only the
two A+ logistic arms with a larger iteration budget.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import warnings
from pathlib import Path
from typing import Any, Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "research" / "temporally_matched_observable_control"
AP_RESULT_ROOT = RESULT_ROOT / "results"
ARCHITECTURES = ("xlstm", "lstm")
SEEDS = (11, 22, 33)
S1_GRID = (0.01, 0.1, 1.0, 10.0)
S2_GRID = (0.001, 0.01, 0.1, 1.0, 10.0, 100.0)
MAX_ITER = 10_000
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 901


def load_ap_aggregate(path: Path = RESULT_ROOT / "results.json") -> dict[str, Any]:
    """Load the immutable A+ aggregate and validate its source×seed matrices."""
    data = json.loads(path.read_text())
    if data.get("historical_reports_phase_g1_modified") is not False:
        raise ValueError("A+ aggregate does not certify G1 immutability")
    for architecture in ARCHITECTURES:
        matrix = np.asarray(data["architectures"][architecture]["source_seed_matrix"], dtype=np.float64)
        if matrix.shape != (10, 3) or not np.isfinite(matrix).all():
            raise ValueError(f"invalid A+ {architecture} source×seed matrix: {matrix.shape}")
    return data


def source_level_matrix(data: dict[str, Any], architecture: str) -> np.ndarray:
    return np.asarray(data["architectures"][architecture]["source_seed_matrix"], dtype=np.float64)


def crossed_bootstrap(
    matrix: np.ndarray,
    draws: int = BOOTSTRAP_DRAWS,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Resample source rows and seed columns once per replicate."""
    values = np.asarray(matrix, dtype=np.float64)
    if values.ndim != 2 or values.shape != (10, 3) or not np.isfinite(values).all():
        raise ValueError("expected a finite [10,3] source×seed matrix")
    rng = np.random.default_rng(seed)
    source_indices = rng.integers(0, values.shape[0], size=(draws, values.shape[0]))
    seed_indices = rng.integers(0, values.shape[1], size=(draws, values.shape[1]))
    sampled = values[source_indices[:, :, None], seed_indices[:, None, :]]
    means = sampled.mean(axis=(1, 2))
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {
        "method": "two_way_crossed_source_rows_seed_columns",
        "draws": int(draws),
        "seed": int(seed),
        "estimand": "source_level_mean_AP_difference",
        "mean": float(values.mean()),
        "ci95": [float(lo), float(hi)],
        "replicate_sd": float(means.std(ddof=1)),
    }


def source_only_bootstrap(
    matrix: np.ndarray,
    draws: int = BOOTSTRAP_DRAWS,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Resample source rows while conditioning on the three observed seeds."""
    values = np.asarray(matrix, dtype=np.float64)
    if values.ndim != 2 or values.shape != (10, 3) or not np.isfinite(values).all():
        raise ValueError("expected a finite [10,3] source×seed matrix")
    rng = np.random.default_rng(seed)
    source_indices = rng.integers(0, values.shape[0], size=(draws, values.shape[0]))
    means = values[source_indices].mean(axis=(1, 2))
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {
        "method": "source_only_condition_on_observed_seeds",
        "draws": int(draws),
        "seed": int(seed),
        "estimand": "source_level_mean_AP_difference",
        "mean": float(values.mean()),
        "ci95": [float(lo), float(hi)],
        "replicate_sd": float(means.std(ddof=1)),
    }


def run_s0(output: Path) -> dict[str, Any]:
    """Write the no-fitting statistical reassessment."""
    data = load_ap_aggregate()
    result: dict[str, Any] = {
        "status": "S0_COMPLETE_NO_FITTING",
        "input": "research/temporally_matched_observable_control/results.json",
        "input_sha256": hashlib.sha256((RESULT_ROOT / "results.json").read_bytes()).hexdigest(),
        "primary_estimand": "mean of the 10 source-level means, with detector seeds retained as a crossed factor",
        "pooled_test_AP_difference": "descriptive historical value only",
        "seed_levels": list(SEEDS),
        "seed_level_caveat": "Only three detector-seed levels are available; neither interval is precisely calibrated as a 95% population interval.",
        "architectures": {},
        "historical_nested_bootstrap": {},
    }
    for architecture in ARCHITECTURES:
        matrix = source_level_matrix(data, architecture)
        old_boot = data["bootstrap"][architecture]
        result["architectures"][architecture] = {
            "source_seed_matrix": matrix.tolist(),
            "source_level_mean": float(matrix.mean()),
            "pooled_test_descriptive_mean": float(np.mean([
                data["architectures"][architecture]["per_seed"][str(seed)] for seed in SEEDS
            ])),
            "crossed_bootstrap": crossed_bootstrap(matrix),
            "source_only_bootstrap": source_only_bootstrap(matrix),
        }
        result["historical_nested_bootstrap"][architecture] = {
            "draws": old_boot["draws"],
            "seed": old_boot["seed"],
            "ci95": old_boot["ci95"],
            "label": "historical published nested source-then-independent-seed resampling",
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


def _load_reference(architecture: str, seed: int) -> dict[str, Any]:
    path = AP_RESULT_ROOT / f"results_{architecture}_{seed}.json"
    return json.loads(path.read_text())


def _reference_row_meta(architecture: str, seed: int) -> dict[str, Any]:
    return _load_reference(architecture, seed)["row_meta"]


def _fit_with_metadata(
    train: dict[str, np.ndarray],
    validation: dict[str, np.ndarray],
    test: dict[str, np.ndarray],
    arm: str,
    seed: int,
    c_grid: Iterable[float],
    max_iter: int = MAX_ITER,
) -> tuple[dict[str, Any], np.ndarray]:
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler().fit(train["X"])
    x_train = scaler.transform(train["X"])
    x_validation = scaler.transform(validation["X"])
    x_test = scaler.transform(test["X"])
    candidates: list[dict[str, Any]] = []
    for c_value in c_grid:
        model = LogisticRegression(C=float(c_value), penalty="l2", solver="lbfgs", tol=1e-4, max_iter=max_iter, random_state=0)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            model.fit(x_train, train["y"])
        n_iter = int(np.max(np.asarray(model.n_iter_, dtype=np.int64)))
        convergence_warning = any(issubclass(w.category, ConvergenceWarning) for w in caught)
        hit_max = n_iter == max_iter
        validation_ap = float(average_precision_score(validation["y"], model.predict_proba(x_validation)[:, 1]))
        candidates.append({
            "C": float(c_value),
            "validation_AP": validation_ap,
            "n_iter": n_iter,
            "convergence_warning": bool(convergence_warning),
            "hit_max_iter": bool(hit_max),
            "converged": bool(not convergence_warning and not hit_max),
            "coef_sha256": hashlib.sha256(np.asarray(model.coef_, dtype=np.float64).tobytes()).hexdigest(),
            "intercept_sha256": hashlib.sha256(np.asarray(model.intercept_, dtype=np.float64).tobytes()).hexdigest(),
        })
        del model
    best_ap = max(item["validation_AP"] for item in candidates)
    selected_c = min(item["C"] for item in candidates if item["validation_AP"] == best_ap)
    selected_candidate = next(item for item in candidates if item["C"] == selected_c)
    selected_model = LogisticRegression(C=selected_c, penalty="l2", solver="lbfgs", tol=1e-4, max_iter=max_iter, random_state=0)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        selected_model.fit(x_train, train["y"])
    selected_n_iter = int(np.max(np.asarray(selected_model.n_iter_, dtype=np.int64)))
    selected_warning = any(issubclass(w.category, ConvergenceWarning) for w in caught)
    selected_hit_max = selected_n_iter == max_iter
    prediction = selected_model.predict_proba(x_test)[:, 1]
    final = {
        "C": float(selected_c),
        "validation_AP": float(selected_candidate["validation_AP"]),
        "test_AP": float(average_precision_score(test["y"], prediction)),
        "n_iter": selected_n_iter,
        "convergence_warning": bool(selected_warning),
        "hit_max_iter": bool(selected_hit_max),
        "converged": bool(not selected_warning and not selected_hit_max),
        "coef_sha256": hashlib.sha256(np.asarray(selected_model.coef_, dtype=np.float64).tobytes()).hexdigest(),
        "intercept_sha256": hashlib.sha256(np.asarray(selected_model.intercept_, dtype=np.float64).tobytes()).hexdigest(),
    }
    info = {
        "arm": arm,
        "detector_seed": int(seed),
        "dimension": int(train["X"].shape[1]),
        "solver": "lbfgs",
        "tol": 1e-4,
        "max_iter": int(max_iter),
        "C_grid": [float(c) for c in c_grid],
        "selected_C": float(selected_c),
        "validation_candidates": candidates,
        "selected_final": final,
        "all_candidates_converged": bool(all(item["converged"] for item in candidates)),
        "selected_final_converged": bool(final["converged"]),
        "all_fits_converged": bool(all(item["converged"] for item in candidates) and final["converged"]),
        "train_rows": int(len(train["y"])),
        "validation_rows": int(len(validation["y"])),
        "test_rows": int(len(test["y"])),
        "test_class_counts": np.bincount(test["y"], minlength=2).tolist(),
        "scaler_mean_sha256": hashlib.sha256(np.asarray(scaler.mean_, dtype=np.float64).tobytes()).hexdigest(),
        "scaler_scale_sha256": hashlib.sha256(np.asarray(scaler.scale_, dtype=np.float64).tobytes()).hexdigest(),
    }
    return info, prediction


def _fit_stage_run(cache_root: Path, architecture: str, seed: int, stage: str, output: Path) -> dict[str, Any]:
    from scripts.temporally_matched_observable_control import arm_matrix, collect, _key_sha

    cache_dir = (cache_root / f"{architecture}_{seed}").resolve()
    records = {fold: collect(cache_dir, fold) for fold in ("train", "validation", "test")}
    _ensure_rows(records, architecture, seed)
    row_keys = {
        fold: _key_sha(
            np.concatenate([r["source"] for r in records[fold]]),
            np.concatenate([r["scenario"] for r in records[fold]]),
            np.concatenate([r["condition"] for r in records[fold]]),
            np.concatenate([r["timestamp"] for r in records[fold]]),
        )
        for fold in records
    }
    c_grid = S1_GRID if stage == "s1" else S2_GRID
    result: dict[str, Any] = {
        "status": f"A_PLUS_{stage.upper()}_RUN",
        "architecture": architecture,
        "detector_seed": int(seed),
        "stage": stage,
        "cache_read_only": True,
        "cache_dir": str(cache_dir),
        "row_key_sha256": row_keys,
        "arms": {},
        "historical_A_plus": _load_reference(architecture, seed),
    }
    for arm in ("H+O1r", "H+O1r+I"):
        stacked = {fold: arm_matrix(records[fold], arm) for fold in records}
        for fold in stacked:
            key = _key_sha(stacked[fold]["source"], stacked[fold]["scenario"], stacked[fold]["condition"], stacked[fold]["timestamp"])
            if key != row_keys[fold]:
                raise RuntimeError(f"arm row-key mismatch in {architecture} seed {seed} {arm} {fold}")
        info, prediction = _fit_with_metadata(stacked["train"], stacked["validation"], stacked["test"], arm, seed, c_grid)
        info["row_key_sha256"] = row_keys
        old = result["historical_A_plus"]["new_arms"][arm]
        info["historical_comparison"] = {
            "selected_C": old["selected_C"],
            "test_AP": old["test_AP"],
            "validation_candidates": old["validation_candidates"],
        }
        result["arms"][arm] = info
        print(f"{stage} {architecture} seed={seed} {arm} C={info['selected_C']} AP={info['selected_final']['test_AP']:.9f} converged={info['all_fits_converged']}", flush=True)
        del stacked, prediction
        gc.collect()
    baseline = result["arms"]["H+O1r"]["selected_final"]["test_AP"]
    internal = result["arms"]["H+O1r+I"]["selected_final"]["test_AP"]
    result["primary"] = {
        "contrast": "AP(H+O1r+I) - AP(H+O1r)",
        "test_AP_H+O1r": float(baseline),
        "test_AP_H+O1r+I": float(internal),
        "delta": float(internal - baseline),
        "all_fits_converged": bool(all(arm["all_fits_converged"] for arm in result["arms"].values())),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


def _ensure_rows(records: dict[str, list[dict[str, np.ndarray]]], architecture: str, seed: int) -> None:
    from scripts.temporally_matched_observable_control import _row_meta

    actual = _row_meta(records)
    expected = _reference_row_meta(architecture, seed)
    for fold in ("train", "validation", "test"):
        if actual[fold] != expected[fold]:
            raise RuntimeError(f"A+ row metadata changed for {architecture} seed {seed} fold {fold}")


def run_stage(cache_root: Path, output_dir: Path, stage: str) -> dict[str, Any]:
    if stage not in {"s1", "s2"}:
        raise ValueError(stage)
    output_dir.mkdir(parents=True, exist_ok=True)
    stage_results = {}
    for architecture in ARCHITECTURES:
        for seed in SEEDS:
            path = output_dir / f"{stage}_{architecture}_{seed}.json"
            stage_results[f"{architecture}_{seed}"] = _fit_stage_run(cache_root, architecture, seed, stage, path)
    all_converged = all(result["primary"]["all_fits_converged"] for result in stage_results.values())
    summary = {
        "status": "CONVERGENCE_PASS" if all_converged else "CONVERGENCE_UNRESOLVED",
        "stage": stage,
        "max_iter": MAX_ITER,
        "C_grid": list(S1_GRID if stage == "s1" else S2_GRID),
        "all_fits_converged": bool(all_converged),
        "runs": {key: str((output_dir / f"{stage}_{key}.json").relative_to(ROOT)) for key in stage_results},
    }
    (output_dir / f"{stage}_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def _comparison_for_stage(stage_results: dict[str, Any], architecture: str) -> dict[str, Any]:
    values = []
    for seed in SEEDS:
        result = stage_results[f"{architecture}_{seed}"]
        values.append({
            "seed": seed,
            "original_selected_C": result["historical_A_plus"]["new_arms"]["H+O1r"]["selected_C"],
            "stage_selected_C_H+O1r": result["arms"]["H+O1r"]["selected_C"],
            "original_selected_C_internal": result["historical_A_plus"]["new_arms"]["H+O1r+I"]["selected_C"],
            "stage_selected_C_internal": result["arms"]["H+O1r+I"]["selected_C"],
            "original_delta": result["historical_A_plus"]["primary"]["delta"],
            "stage_delta": result["primary"]["delta"],
            "stage_delta_minus_original": result["primary"]["delta"] - result["historical_A_plus"]["primary"]["delta"],
            "all_fits_converged": result["primary"]["all_fits_converged"],
        })
    return {"architecture": architecture, "runs": values}


def summarize_stage(output_dir: Path, stage: str, output: Path) -> dict[str, Any]:
    stage_results = {
        f"{architecture}_{seed}": json.loads((output_dir / f"{stage}_{architecture}_{seed}.json").read_text())
        for architecture in ARCHITECTURES for seed in SEEDS
    }
    summary = json.loads((output_dir / f"{stage}_summary.json").read_text())
    result = {
        "status": summary["status"],
        "stage": stage,
        "all_fits_converged": summary["all_fits_converged"],
        "comparison": {architecture: _comparison_for_stage(stage_results, architecture) for architecture in ARCHITECTURES},
        "source_seed_effects": {
            architecture: [stage_results[f"{architecture}_{seed}"]["primary"]["delta"] for seed in SEEDS]
            for architecture in ARCHITECTURES
        },
    }
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("s0")
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("fit")
    p.add_argument("--cache-root", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--stage", choices=("s1", "s2"), required=True)
    p = sub.add_parser("fit-one")
    p.add_argument("--cache-root", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--stage", choices=("s1", "s2"), required=True)
    p.add_argument("--architecture", choices=ARCHITECTURES, required=True)
    p.add_argument("--seed", type=int, choices=SEEDS, required=True)
    p = sub.add_parser("summarize")
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--stage", choices=("s1", "s2"), required=True)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "s0":
        run_s0(args.output)
    elif args.command == "fit":
        run_stage(args.cache_root.resolve(), args.output_dir, args.stage)
    elif args.command == "fit-one":
        args.output_dir.mkdir(parents=True, exist_ok=True)
        _fit_stage_run(
            args.cache_root.resolve(),
            args.architecture,
            args.seed,
            args.stage,
            args.output_dir / f"{args.stage}_{args.architecture}_{args.seed}.json",
        )
    else:
        summarize_stage(args.output_dir, args.stage, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
