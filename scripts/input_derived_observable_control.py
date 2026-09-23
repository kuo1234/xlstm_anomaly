"""Temporally matched bounded input-derived observable control (P1r).

P1r is the last bounded input-derived control of the synthetic ladder.  It is
the scaled raw input window ``[64, 8]`` summarised by the frozen 128-column O1
statistic family, followed by the identical causal current + mean/std/slope
expansion at decision widths 4/8/16/32.  It is an input-derived observable
summary, not the complete observation.  ``internal234`` is a deterministic
function of the causal input window, so information-theoretic superiority over
the full observation is out of scope in principle; the only admissible result
is additional predictive/decodable utility under the fixed decoder.

Commands
--------
``preflight``       label-blind repository preflight (stage 1; no cache, no fit).
``host-preflight``  label-blind cache-host preflight (stage 2; reads cache
                    timestamps only, recomputes P1r fingerprints; no fit).
``fit-one``         the sealed experiment for one backbone/seed.  Refuses to run
                    unless both preflights passed under the same protocol seal.
``aggregate``       source×seed aggregation with crossed/source-only bootstrap.

No command trains or runs a detector, writes the A+ cache, or touches
``reports/``.
"""
from __future__ import annotations

import argparse
import ast
import gc
import hashlib
import inspect
import json
import os
import platform
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import nonlinear_observable_control as _nl  # noqa: E402
import strong_observable_control as _soc  # noqa: E402
import temporally_matched_observable_control as _ap  # noqa: E402
from nonlinear_observable_control import (  # noqa: E402
    BOOTSTRAP_DRAWS,
    BOOTSTRAP_SEED,
    MAX_ITER_GRID,
    _fit_candidate,
    _fit_selected,
    _scenario_ap,
    _source_ap,
    atomic_json_write,
    crossed_bootstrap,
    estimator_parameters,
    source_only_bootstrap,
)
from strong_observable_control import (  # noqa: E402
    ARCHITECTURES,
    CONDITIONS,
    FOLDS,
    SCENARIOS,
    SEEDS,
    WINDOW,
    _scaler,
    _stream_name,
    _truth_rows,
    array_sha,
    dense_windows,
    residual_o1,
    scale_input,
)
from temporally_matched_observable_control import (  # noqa: E402
    DECISION_START,
    INTERNAL_DIM,
    O1_BASE_DIM,
    O1R_DIM,
    ROLLING_WIDTHS,
    _key_sha,
    expand_o1r,
)

# ---------------------------------------------------------------------------
# Frozen definitions
# ---------------------------------------------------------------------------
H_DIM = 14
P1_BASE_DIM = 128
P1R_DIM = P1_BASE_DIM * (1 + 3 * len(ROLLING_WIDTHS))  # 1664
ARMS = ("H+P1r", "H+P1r+I")
ARM_DIMS = {"H+P1r": H_DIM + P1R_DIM, "H+P1r+I": H_DIM + P1R_DIM + INTERNAL_DIM}  # 1678 / 1912
FIRST_FINITE_INDEX = max(ROLLING_WIDTHS) - 1  # 31
FIRST_FINITE_TIMESTAMP = DECISION_START + FIRST_FINITE_INDEX  # 94
RAW_SUPPORT_LAG = (WINDOW - 1) + (max(ROLLING_WIDTHS) - 1)  # 94 -> raw union [t-94, t]
FEATURE_CHUNK = 2048
SCALER_SCENARIO, SCALER_CONDITION = "stationary", "none"
PRIMARY_STRATA = ("anomaly", "drift")
HOST_FEATURE_RTOL = 1e-9  # stage-1 vs cache-host P1r sums; inputs must match bit-exactly

OUT_ROOT = ROOT / "research" / "input_derived_observable_control"
PROTOCOL = OUT_ROOT / "protocol.md"
PREFLIGHT = OUT_ROOT / "preflight.json"
HOST_PREFLIGHT = OUT_ROOT / "host_preflight.json"
APLUS_RESULTS = ROOT / "research" / "temporally_matched_observable_control" / "results"
NL_RESULTS = ROOT / "research" / "nonlinear_observable_control" / "results.json"
GENERATOR_CASES = ROOT / "reports" / "generator_validation_v4" / "cases.json"
GENERATOR_SUMMARY = ROOT / "reports" / "generator_validation_v4" / "summary.json"
SEALED_FILES = (
    "scripts/input_derived_observable_control.py",
    "research/input_derived_observable_control/protocol.md",
    "tests/test_input_derived_observable_control.py",
    "scripts/strong_observable_control.py",
    "scripts/temporally_matched_observable_control.py",
    "scripts/nonlinear_observable_control.py",
    "scripts/phase_g1_core.py",
    "m0/synthetic.py",
    "m0/correlation.py",
    "configs/synthetic_v1.json",
)
TRUTH_NAMES = frozenset({
    "labels", "drift_active", "regime", "event_ids", "events", "semantic", "truth",
    "stratum", "label", "y", "_truth_rows", "build_evaluator_rows",
})
OUTCOMES = ("ADDITIONAL_UTILITY_BEYOND_P1R", "NO_RESOLVED_ADDITIONAL_UTILITY", "NEGATIVE_INCREMENT")


# ---------------------------------------------------------------------------
# Truth-free feature path.  Nothing below receives a stream object, a label,
# an event, a regime, a backbone, a detector seed, or a cache path.
# ---------------------------------------------------------------------------
def p1_statistic_family(windows: np.ndarray) -> np.ndarray:
    """Frozen 128-column O1 statistic family applied to scaled input windows."""
    return residual_o1(windows)


def p1_base_from_scaled(scaled: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """[N,8] scaled input -> ([N-63,128] float32 P1 base, right-edge timestamps)."""
    windows, timestamps = dense_windows(scaled)
    parts = [p1_statistic_family(windows[left:left + FEATURE_CHUNK]) for left in range(0, len(windows), FEATURE_CHUNK)]
    base = np.concatenate(parts, axis=0)
    if base.shape != (len(timestamps), P1_BASE_DIM):
        raise RuntimeError(f"P1 base schema drift: {base.shape}")
    return base, timestamps


def p1r_from_scaled(scaled: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Temporally matched P1r (float64, NaN before decision index 31)."""
    base, timestamps = p1_base_from_scaled(scaled)
    p1r = expand_o1r(base.astype(np.float64))
    if p1r.shape != (len(timestamps), P1R_DIM):
        raise RuntimeError(f"P1r schema drift: {p1r.shape}")
    return p1r, timestamps


def p1r_from_observations(observations: np.ndarray, scaler: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """P1r from raw detector-input observations and the source-specific scaler."""
    return p1r_from_scaled(scale_input(observations, scaler))


FEATURE_FUNCTIONS = (p1_statistic_family, p1_base_from_scaled, p1r_from_scaled, p1r_from_observations)
INHERITED_FEATURE_FUNCTIONS = (residual_o1, dense_windows, scale_input, expand_o1r, _ap._rolling)


def detector_observations(source: int, scenario: str, condition: str) -> np.ndarray:
    """Observations exactly as passed to the detector by the cache extractor."""
    from m0.synthetic import generate

    stream = generate(source, scenario, condition)
    return np.asarray(stream.observations, dtype=np.float32).copy()


def source_scaler(source: int) -> dict[str, np.ndarray]:
    """The existing source-specific detector input scaler (unchanged)."""
    return _scaler(source)


# ---------------------------------------------------------------------------
# Evaluator-side cohort (inherited from A+; used only to define rows)
# ---------------------------------------------------------------------------
def cohort_keep(source: int, scenario: str, condition: str, timestamps: np.ndarray) -> np.ndarray:
    """A+ primary cohort membership for right-edge rows.

    The A+ finite mask (H, internal234, O1r all finite) is positional: every
    rolling component is finite exactly from decision index 31.  The only
    truth-derived quantity is membership of the primary anomaly/drift stratum;
    no label value is joined to any feature here.
    """
    from m0.synthetic import generate

    truth = _truth_rows(generate(source, scenario, condition), timestamps)
    positional = np.arange(len(timestamps)) >= FIRST_FINITE_INDEX
    return positional & np.isin(truth["stratum"], PRIMARY_STRATA)


def cohort_rows(key: tuple[str, int, str, str]) -> tuple[tuple[str, int, str, str], np.ndarray]:
    """Worker: kept right-edge timestamps of one stream under the A+ cohort."""
    from m0.synthetic import generate

    _, source, scenario, condition = key
    n = len(generate(source, scenario, condition).observations)
    timestamps = np.arange(DECISION_START, n, dtype=np.int64)
    return key, timestamps[cohort_keep(source, scenario, condition, timestamps)]


def aplus_row_meta() -> dict[str, dict[str, Any]]:
    metas = [json.loads((APLUS_RESULTS / f"results_{a}_{s}.json").read_text())["row_meta"] for a in ARCHITECTURES for s in SEEDS]
    if any(meta != metas[0] for meta in metas):
        raise RuntimeError("A+ row_meta differs across runs")
    return metas[0]


# ---------------------------------------------------------------------------
# Hashing helpers
# ---------------------------------------------------------------------------
def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generator_arrayhash(array: np.ndarray) -> str:
    """Identical encoding to scripts/validate_generator_full.py::arrayhash."""
    a = np.ascontiguousarray(array)
    header = json.dumps(dict(shape=a.shape, dtype=a.dtype.str), sort_keys=True).encode()
    return hashlib.sha256(header + b"\n" + a.tobytes()).hexdigest()


def sealed_file_hashes() -> dict[str, str]:
    return {path: sha256_file(ROOT / path) for path in SEALED_FILES}


def environment() -> dict[str, Any]:
    import scipy

    return {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
    }


EXECUTION: dict[str, Any] = {"mode": "unset"}


def _map(function: Any, items: list[Any], workers: int) -> list[Any]:
    """Process-parallel map; sequential fallback where the host forbids semaphores."""
    if workers > 1:
        try:
            with ProcessPoolExecutor(max_workers=workers) as pool:
                out = list(pool.map(function, items, chunksize=1))
            EXECUTION["mode"] = f"process_pool_{workers}_workers"
            return out
        except (PermissionError, NotImplementedError, OSError) as error:
            EXECUTION["fallback_reason"] = f"{type(error).__name__}: {error}"
    EXECUTION["mode"] = "sequential_single_process"
    return [function(item) for item in items]


def stream_grid() -> list[tuple[str, int, str, str]]:
    return [(fold, source, scenario, condition) for fold, sources in FOLDS.items() for source in sources for scenario in SCENARIOS for condition in CONDITIONS]


# ---------------------------------------------------------------------------
# Per-stream fingerprint (worker; truth-free)
# ---------------------------------------------------------------------------
def stream_fingerprint(key: tuple[str, int, str, str]) -> dict[str, Any]:
    fold, source, scenario, condition = key
    scaler = source_scaler(source)
    observations = detector_observations(source, scenario, condition)
    scaled = scale_input(observations, scaler)
    base, timestamps = p1_base_from_scaled(scaled)
    p1r = expand_o1r(base.astype(np.float64))
    finite_rows = np.isfinite(p1r).all(axis=1)
    p1r32 = p1r.astype(np.float32)
    kept = p1r[FIRST_FINITE_INDEX:]
    result = {
        "fold": fold, "source": int(source), "scenario": scenario, "condition": condition,
        "observations_generator_sha256": generator_arrayhash(np.asarray(_raw_observations(source, scenario, condition))),
        "detector_input_sha256": array_sha(observations),
        "scaled_input_sha256": array_sha(scaled),
        "p1_base_sha256": array_sha(base),
        "p1r_float32_sha256": array_sha(p1r32),
        "decision_rows": int(len(timestamps)),
        "timestamp_first": int(timestamps[0]),
        "timestamp_last": int(timestamps[-1]),
        "timestamps_contiguous": bool(np.array_equal(timestamps, np.arange(DECISION_START, DECISION_START + len(timestamps)))),
        "first_all_finite_index": int(np.argmax(finite_rows)),
        "all_finite_from_index_31": bool(finite_rows[FIRST_FINITE_INDEX:].all() and not finite_rows[:FIRST_FINITE_INDEX].any()),
        "p1r_sum": float(kept.sum()),
        "p1r_sumsq": float(np.square(kept).sum()),
    }
    del observations, scaled, base, p1r, p1r32, kept
    gc.collect()
    return result


def _raw_observations(source: int, scenario: str, condition: str) -> np.ndarray:
    from m0.synthetic import generate

    return generate(source, scenario, condition).observations


def _semantic_observation_identity(key: tuple[str, int, str, str]) -> bool:
    """Anomaly/legitimate semantic variants must yield byte-identical observations."""
    from m0.synthetic import generate

    _, source, scenario, condition = key
    a = generate(source, scenario, condition, semantic="anomaly").observations
    b = generate(source, scenario, condition, semantic="legitimate").observations
    return generator_arrayhash(a) == generator_arrayhash(b)


# ---------------------------------------------------------------------------
# Static checks
# ---------------------------------------------------------------------------
def _names_in(function: Any) -> set[str]:
    tree = ast.parse(inspect.getsource(function).lstrip())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    return names


def truth_free_feature_path() -> dict[str, Any]:
    offenders = {}
    for function in (*FEATURE_FUNCTIONS, *INHERITED_FEATURE_FUNCTIONS):
        hits = sorted(_names_in(function) & TRUTH_NAMES)
        if hits:
            offenders[f"{function.__module__}.{function.__name__}"] = hits
    signature = tuple(inspect.signature(p1r_from_observations).parameters)
    obs_names = _names_in(detector_observations) & TRUTH_NAMES
    return {
        "feature_function_signature": list(signature),
        "signature_is_observations_and_scaler_only": signature == ("observations", "scaler"),
        "truth_names_in_feature_path": offenders,
        "detector_observations_reads_only_observations": not obs_names,
        "pass": signature == ("observations", "scaler") and not offenders and not obs_names,
    }


def backbone_invariance() -> dict[str, Any]:
    forbidden = {"architecture", "seed", "detector_seed", "cache_dir", "cache_root", "model", "checkpoint"}
    hits = {}
    for function in (*FEATURE_FUNCTIONS, source_scaler, detector_observations, stream_fingerprint):
        params = set(inspect.signature(function).parameters) & forbidden
        if params:
            hits[function.__name__] = sorted(params)
    return {
        "feature_functions_take_no_backbone_seed_or_cache": not hits,
        "offending_parameters": hits,
        "fingerprint_key": "fold/source/scenario/condition only",
        "pass": not hits,
    }


def selection_path_check() -> dict[str, Any]:
    """AST check of the sealed fitting path: candidates see train/validation only."""
    calls: dict[str, list[tuple[str, ...]]] = {}
    for node in ast.walk(ast.parse(inspect.getsource(_fit_arm))):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"_fit_candidate", "_fit_selected"}:
            calls.setdefault(node.func.id, []).append(tuple(a.id if isinstance(a, ast.Name) else "?" for a in node.args))
    module_names = set()
    for node in ast.walk(ast.parse(Path(__file__).read_text())):
        if isinstance(node, ast.Name):
            module_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            module_names.add(node.attr)
    checks = {
        "candidates_fit_on_train_scored_on_validation": calls.get("_fit_candidate") == [("train", "validation", "max_iter")],
        "test_predicted_once_after_selection": calls.get("_fit_selected") == [("test", "train", "selected_max_iter")],
        "candidate_function_has_no_test_argument": "test" not in inspect.signature(_fit_candidate).parameters,
        "estimator_is_nonlinear_audit_family": estimator_parameters is _nl.estimator_parameters and _fit_candidate is _nl._fit_candidate and _fit_selected is _nl._fit_selected,
        "max_iter_grid": list(MAX_ITER_GRID) == [100, 300],
        "no_scaler_in_fit_path": "StandardScaler" not in module_names,
        "early_stopping_false": all(estimator_parameters(m)["early_stopping"] is False for m in MAX_ITER_GRID),
    }
    checks["pass"] = all(checks.values())
    return checks


def temporal_support_check(scaled: np.ndarray, offset: int) -> dict[str, Any]:
    """Perturb one scaled input sample and locate every changed P1r decision row.

    Causality: no decision before ``offset`` and none after ``offset + 94`` may
    change.  Support: on fully finite rows (t >= 94) the changed set must be
    exactly ``[offset, offset + 94]``.  Warmup rows (t < 94) are NaN in the
    wider rolling components and are only checked for leakage.
    """
    reference, timestamps = p1r_from_scaled(scaled)
    perturbed = scaled.copy()
    perturbed[offset] += np.float32(1.0)
    changed_values, _ = p1r_from_scaled(perturbed)
    same = (reference == changed_values) | (np.isnan(reference) & np.isnan(changed_values))
    changed = ~same.all(axis=1)
    changed_t = timestamps[changed]
    finite = np.isfinite(reference).all(axis=1)
    lo, hi = offset, offset + RAW_SUPPORT_LAG
    in_support = (timestamps >= lo) & (timestamps <= hi)
    leakage_free = bool(not np.any(changed & ~in_support))
    complete = bool(np.array_equal(changed & finite, in_support & finite))
    return {
        "perturbed_input_index": int(offset),
        "changed_decision_min": int(changed_t.min()) if changed_t.size else None,
        "changed_decision_max": int(changed_t.max()) if changed_t.size else None,
        "changed_decision_count": int(changed_t.size),
        "support": [int(lo), int(hi)],
        "no_backward_or_out_of_support_change": leakage_free,
        "no_backward_leakage": bool(not np.any(changed & (timestamps < lo))),
        "raw_union_is_t_minus_94_to_t_on_finite_rows": complete,
        "pass": leakage_free and complete and bool(changed.any()),
    }


# ---------------------------------------------------------------------------
# Stage 1: label-blind repository preflight
# ---------------------------------------------------------------------------
def preflight(output: Path, protocol_seal: str, workers: int) -> dict[str, Any]:
    from m0.synthetic import generate

    gates: dict[str, Any] = {}
    grid = stream_grid()

    # G1 sealed code identity and generator code identity.
    code = sealed_file_hashes()
    generator_code = json.loads(GENERATOR_SUMMARY.read_text())["code_config_sha256"]
    gates["G1_code_identity"] = {
        "sealed_file_sha256": code,
        "generator_code_matches_generator_validation_v4": {
            path: code.get(path) == digest for path, digest in generator_code.items() if path in code
        },
    }
    gates["G1_code_identity"]["pass"] = all(gates["G1_code_identity"]["generator_code_matches_generator_validation_v4"].values())

    # Per-stream fingerprints, computed twice in independent worker processes.
    first = _map(stream_fingerprint, grid, workers)
    second = _map(stream_fingerprint, list(reversed(grid)), workers)[::-1]
    semantic = _map(_semantic_observation_identity, grid, workers)
    cohort = dict(_map(cohort_rows, grid, workers))

    # G2 cross-host generator identity: observations and scaler streams equal the
    # sealed generator_validation_v4 hashes produced on the cache host.
    sealed = {}
    for case in json.loads(GENERATOR_CASES.read_text()):
        for cond in case["conditions"]:
            sealed[(int(case["seed"]), case["scenario"], cond["condition"])] = cond["hashes"]["anomaly"]["array_sha256"]["observations"]
    stream_matches = [sealed.get((f["source"], f["scenario"], f["condition"])) == f["observations_generator_sha256"] for f in first]
    scaler_sources = sorted({source for _, source, _, _ in grid})
    scaler_matches = [
        sealed.get((s, SCALER_SCENARIO, SCALER_CONDITION)) == generator_arrayhash(generate(s, SCALER_SCENARIO, SCALER_CONDITION).observations)
        for s in scaler_sources
    ]
    gates["G2_generator_matches_sealed_cache_host_hashes"] = {
        "streams_checked": len(stream_matches), "streams_matching": int(sum(stream_matches)),
        "scaler_streams_checked": len(scaler_matches), "scaler_streams_matching": int(sum(scaler_matches)),
        "pass": all(stream_matches) and all(scaler_matches),
    }

    # G3 determinism: two independent computations agree bit-for-bit.
    fields = ("detector_input_sha256", "scaled_input_sha256", "p1_base_sha256", "p1r_float32_sha256")
    mismatch = [f"{a['fold']}_{a['source']}_{a['scenario']}_{a['condition']}" for a, b in zip(first, second) if any(a[k] != b[k] for k in fields)]
    scalers = {s: array_sha(np.concatenate([source_scaler(s)["mean"], source_scaler(s)["scale"]])) for s in scaler_sources}
    scalers_again = {s: array_sha(np.concatenate([source_scaler(s)["mean"], source_scaler(s)["scale"]])) for s in scaler_sources}
    gates["G3_deterministic_scaled_input_and_p1r"] = {
        "streams": len(first), "mismatching_streams": mismatch,
        "scalers_deterministic": scalers == scalers_again,
        "pass": not mismatch and scalers == scalers_again,
    }

    # G4 row-key contract: regenerated rows reproduce the A+ cohort exactly.
    reference = aplus_row_meta()
    regenerated: dict[str, Any] = {}
    for fold in FOLDS:
        sources, scenarios, conditions, stamps = [], [], [], []
        for key in (k for k in grid if k[0] == fold):
            kept = cohort[key]
            count = int(len(kept))
            if count == 0:
                continue
            sources.append(np.full(count, key[1], dtype=np.int32))
            scenarios.append(np.asarray([key[2]] * count, dtype=object))
            conditions.append(np.asarray([key[3]] * count, dtype=object))
            stamps.append(kept)
        ts = np.concatenate(stamps)
        regenerated[fold] = {
            "rows": int(len(ts)),
            "key_sha256": _key_sha(np.concatenate(sources), np.concatenate(scenarios), np.concatenate(conditions), ts),
            "timestamp_min": int(ts.min()),
            "timestamp_max": int(ts.max()),
        }
    gates["G4_row_key_contract"] = {
        "regenerated": regenerated, "aplus_reference": reference,
        "timestamps_contiguous_right_edge": all(f["timestamps_contiguous"] and f["timestamp_first"] == DECISION_START for f in first),
        "pass": regenerated == reference and all(f["timestamps_contiguous"] for f in first),
    }

    # G5 truth independence of the feature path.
    gates["G5_no_label_event_regime_dependency"] = truth_free_feature_path()
    gates["G5_no_label_event_regime_dependency"]["semantic_variant_observations_identical"] = f"{sum(semantic)}/{len(semantic)}"
    gates["G5_no_label_event_regime_dependency"]["pass"] = gates["G5_no_label_event_regime_dependency"]["pass"] and all(semantic)

    # G6 backbone invariance.
    gates["G6_identical_across_backbones"] = backbone_invariance()

    # G7 temporal support and future leakage on a real stream.
    probe = ("test", 3000, "gradual", "none")
    scaled = scale_input(detector_observations(*probe[1:]), source_scaler(probe[1]))
    support = [temporal_support_check(scaled, offset) for offset in (0, 5000, 12345, len(scaled) - 1)]
    gates["G7_temporal_support_and_no_future_leakage"] = {
        "probe_stream": list(probe), "perturbations": support,
        "first_all_finite_decision_index": sorted({f["first_all_finite_index"] for f in first}),
        "first_all_finite_timestamp": FIRST_FINITE_TIMESTAMP,
        "finite_pattern_all_streams": all(f["all_finite_from_index_31"] for f in first),
        "pass": all(s["pass"] for s in support) and all(f["all_finite_from_index_31"] for f in first),
    }

    # G8 frozen feature dimensions.
    dims = {"H": H_DIM, "P1_base": P1_BASE_DIM, "P1r": P1R_DIM, "internal234": INTERNAL_DIM, **ARM_DIMS}
    gates["G8_frozen_dimensions"] = {
        **dims,
        "O1_base_equals_P1_base": O1_BASE_DIM == P1_BASE_DIM, "O1r_equals_P1r": O1R_DIM == P1R_DIM,
        "pass": P1R_DIM == 1664 and ARM_DIMS == {"H+P1r": 1678, "H+P1r+I": 1912} and O1R_DIM == P1R_DIM,
    }

    # G9 no test metric in model/hyperparameter selection; no fit here.
    gates["G9_selection_validation_only"] = selection_path_check()
    gates["G9_selection_validation_only"]["sklearn_imported_during_preflight"] = "sklearn" in sys.modules
    gates["G9_selection_validation_only"]["pass"] = gates["G9_selection_validation_only"]["pass"] and "sklearn" not in sys.modules

    status = "PASS" if all(g["pass"] for g in gates.values()) else "FAIL"
    result = {
        "status": status,
        "stage": "repository_preflight_label_blind",
        "protocol_seal": protocol_seal,
        "environment": environment(),
        "execution": dict(EXECUTION),
        "label_use": "cohort membership only (A+ primary anomaly/drift stratum) to reproduce row keys; no label value joined to any feature; no metric computed",
        "fit_performed": False,
        "results_produced": False,
        "cache_read": False,
        "gates": gates,
        "streams": first,
    }
    atomic_json_write(output, result)
    return result


# ---------------------------------------------------------------------------
# Stage 2: label-blind cache-host preflight
# ---------------------------------------------------------------------------
def host_preflight(cache_root: Path, output: Path, protocol_seal: str, workers: int) -> dict[str, Any]:
    stage1 = json.loads(PREFLIGHT.read_text())
    gates: dict[str, Any] = {}
    gates["H1_stage1_pass_same_seal"] = {"pass": stage1.get("status") == "PASS" and stage1.get("protocol_seal") == protocol_seal}
    gates["H2_sealed_code_unchanged"] = {"pass": sealed_file_hashes() == stage1["gates"]["G1_code_identity"]["sealed_file_sha256"]}
    grid = stream_grid()
    fresh = _map(stream_fingerprint, grid, workers)
    exact_fields = ("observations_generator_sha256", "detector_input_sha256", "scaled_input_sha256")
    input_mismatch = [f"{a['fold']}_{a['source']}_{a['scenario']}_{a['condition']}" for a, b in zip(fresh, stage1["streams"]) if any(a[k] != b[k] for k in exact_fields)]
    feature_exact = sum(a["p1r_float32_sha256"] == b["p1r_float32_sha256"] for a, b in zip(fresh, stage1["streams"]))
    rel = max(
        max(abs(a[k] - b[k]) / max(abs(a[k]), abs(b[k]), 1e-300) for k in ("p1r_sum", "p1r_sumsq"))
        for a, b in zip(fresh, stage1["streams"])
    )
    gates["H3_inputs_bit_identical_to_stage1"] = {"mismatching_streams": input_mismatch, "pass": not input_mismatch}
    gates["H4_p1r_matches_stage1"] = {
        "bit_identical_streams": f"{feature_exact}/{len(fresh)}",
        "max_relative_sum_deviation": rel,
        "tolerance": HOST_FEATURE_RTOL,
        "pass": feature_exact == len(fresh) or rel <= HOST_FEATURE_RTOL,
    }
    cache_issues = []
    for architecture in ARCHITECTURES:
        for seed in SEEDS:
            cache_dir = (cache_root / f"{architecture}_{seed}").resolve()
            manifest = json.loads((cache_dir / f"manifest_{architecture}_{seed}.json").read_text())
            if manifest.get("status") != "complete":
                cache_issues.append(f"{architecture}_{seed}: manifest not complete")
            for f in fresh:
                with np.load(cache_dir / _stream_name(f["fold"], f["source"], f["scenario"], f["condition"]), allow_pickle=False) as loaded:
                    cached = np.asarray(loaded["timestamp"], dtype=np.int64)
                expected = np.arange(DECISION_START, DECISION_START + f["decision_rows"], dtype=np.int64)
                if not np.array_equal(cached, expected):
                    cache_issues.append(f"{architecture}_{seed}:{f['fold']}_{f['source']}_{f['scenario']}_{f['condition']}")
    gates["H5_cache_timestamps_equal_regenerated"] = {"issues": cache_issues, "pass": not cache_issues}
    gates["H6_no_fit"] = {"sklearn_imported": "sklearn" in sys.modules, "pass": "sklearn" not in sys.modules}
    status = "PASS" if all(g["pass"] for g in gates.values()) else "FAIL"
    result = {
        "status": status, "stage": "cache_host_preflight_label_blind", "protocol_seal": protocol_seal,
        "environment": environment(), "execution": dict(EXECUTION), "cache_root": str(cache_root), "fit_performed": False,
        "results_produced": False, "gates": gates, "streams": fresh,
    }
    atomic_json_write(output, result)
    return result


# ---------------------------------------------------------------------------
# Sealed experiment (not executed during preparation)
# ---------------------------------------------------------------------------
def require_preflights(protocol_seal: str) -> dict[str, Any]:
    for path in (PREFLIGHT, HOST_PREFLIGHT):
        if not path.exists():
            raise PermissionError(f"refusing to fit: {path.name} missing")
        payload = json.loads(path.read_text())
        if payload.get("status") != "PASS" or payload.get("protocol_seal") != protocol_seal:
            raise PermissionError(f"refusing to fit: {path.name} is not PASS for seal {protocol_seal}")
    stage1 = json.loads(PREFLIGHT.read_text())
    if sealed_file_hashes() != stage1["gates"]["G1_code_identity"]["sealed_file_sha256"]:
        raise PermissionError("refusing to fit: sealed files changed since preflight")
    # Fit-time fingerprints are checked bit-exactly against the same host's stage-2 record.
    return json.loads(HOST_PREFLIGHT.read_text())


def _records_with_p1r(cache_dir: Path, fold: str, manifest: dict[tuple, dict[str, Any]]) -> list[dict[str, np.ndarray]]:
    records: list[dict[str, np.ndarray]] = []
    scalers: dict[int, dict[str, np.ndarray]] = {}
    for source in FOLDS[fold]:
        scalers[source] = source_scaler(source)
        for scenario in SCENARIOS:
            for condition in CONDITIONS:
                record = _ap._make_records(cache_dir, fold, source, scenario, condition)
                with np.load(cache_dir / _stream_name(fold, source, scenario, condition), allow_pickle=False) as loaded:
                    cached_ts = np.asarray(loaded["timestamp"], dtype=np.int64)
                p1r, timestamps = p1r_from_observations(detector_observations(source, scenario, condition), scalers[source])
                if not np.array_equal(timestamps, cached_ts):
                    raise RuntimeError(f"regenerated timestamps differ from cache: {fold} {source} {scenario} {condition}")
                if array_sha(p1r.astype(np.float32)) != manifest[(fold, source, scenario, condition)]["p1r_float32_sha256"]:
                    raise RuntimeError(f"P1r fingerprint differs from preflight: {fold} {source} {scenario} {condition}")
                if record is None:
                    continue
                index = record["timestamp"] - DECISION_START
                values = p1r[index].astype(np.float32)
                if not np.isfinite(values).all():
                    raise RuntimeError("non-finite P1r on a cohort row")
                record["P1r"] = values
                del record["O1r"]
                records.append(record)
                del p1r
    return records


def p1r_arm_matrix(records: list[dict[str, np.ndarray]], arm: str) -> dict[str, np.ndarray]:
    if arm not in ARMS:
        raise ValueError(f"unregistered P1r arm: {arm}")
    blocks = [np.concatenate((r["H"], r["P1r"], r["I"]) if arm == "H+P1r+I" else (r["H"], r["P1r"]), axis=1) for r in records]
    out = {"X": np.concatenate(blocks)}
    for field in ("y", "source", "scenario", "condition", "timestamp"):
        out[field] = np.concatenate([r[field] for r in records])
    if out["X"].shape[1] != ARM_DIMS[arm]:
        raise RuntimeError(f"arm dimension drift: {arm} {out['X'].shape}")
    return out


def _fit_arm(records: dict[str, list[dict[str, np.ndarray]]], arm: str) -> tuple[dict[str, Any], np.ndarray, dict[str, np.ndarray]]:
    stacked = {fold: p1r_arm_matrix(records[fold], arm) for fold in FOLDS}
    train, validation, test = stacked["train"], stacked["validation"], stacked["test"]
    candidates = [_fit_candidate(train, validation, max_iter) for max_iter in MAX_ITER_GRID]
    best_ap = max(c["validation_AP"] for c in candidates)
    selected_max_iter = min(c["max_iter"] for c in candidates if c["validation_AP"] == best_ap)
    selected, prediction = _fit_selected(test, train, selected_max_iter)
    selected["validation_AP"] = float(best_ap)
    keys = {fold: _key_sha(stacked[fold]["source"], stacked[fold]["scenario"], stacked[fold]["condition"], stacked[fold]["timestamp"]) for fold in FOLDS}
    result = {
        "arm": arm, "dimension": int(train["X"].shape[1]), "candidates": candidates, "selected": selected,
        "source_AP": _source_ap(test, prediction), "scenario_AP": _scenario_ap(test, prediction), "row_key_sha256": keys,
    }
    return result, prediction, test


def fit_one(cache_root: Path, architecture: str, seed: int, output: Path, protocol_seal: str) -> dict[str, Any]:
    host = require_preflights(protocol_seal)
    manifest = {(s["fold"], s["source"], s["scenario"], s["condition"]): s for s in host["streams"]}
    cache_dir = (cache_root / f"{architecture}_{seed}").resolve()
    records = {fold: _records_with_p1r(cache_dir, fold, manifest) for fold in FOLDS}
    reference = aplus_row_meta()
    arms = {}
    for arm in ARMS:
        arms[arm], _, _ = _fit_arm(records, arm)
        if {fold: arms[arm]["row_key_sha256"][fold] for fold in FOLDS} != {fold: reference[fold]["key_sha256"] for fold in FOLDS}:
            raise RuntimeError("row-key contract violated")
    delta = arms["H+P1r+I"]["selected"]["test_AP"] - arms["H+P1r"]["selected"]["test_AP"]
    source_effects = {
        s: None if arms["H+P1r"]["source_AP"][s] is None or arms["H+P1r+I"]["source_AP"][s] is None
        else arms["H+P1r+I"]["source_AP"][s] - arms["H+P1r"]["source_AP"][s]
        for s in arms["H+P1r"]["source_AP"]
    }
    result = {
        "status": "exploratory_input_derived_observable_control_run", "protocol_seal": protocol_seal,
        "architecture": architecture, "detector_seed": int(seed), "environment": environment(),
        "arms": arms,
        "primary": {"contrast": "AP(H+P1r+I) - AP(H+P1r)", "pooled_test_delta_descriptive": float(delta), "source_effects": source_effects,
                    "scenario_effects": {sc: arms["H+P1r+I"]["scenario_AP"].get(sc, float("nan")) - arms["H+P1r"]["scenario_AP"].get(sc, float("nan")) for sc in SCENARIOS}},
    }
    atomic_json_write(output, result)
    return result


def classify(ci95: list[float]) -> str:
    lo, hi = ci95
    if lo > 0:
        return OUTCOMES[0]
    if hi < 0:
        return OUTCOMES[2]
    return OUTCOMES[1]


def aggregate(output_dir: Path, output: Path, protocol_seal: str) -> dict[str, Any]:
    loaded = {}
    for architecture in ARCHITECTURES:
        for seed in SEEDS:
            payload = json.loads((output_dir / f"results_{architecture}_{seed}.json").read_text())
            if payload.get("protocol_seal") != protocol_seal:
                raise ValueError("protocol seal mismatch")
            loaded[(architecture, seed)] = payload
    result: dict[str, Any] = {"status": "exploratory_input_derived_observable_control_complete", "protocol_seal": protocol_seal, "architectures": {}}
    for architecture in ARCHITECTURES:
        matrix = np.asarray([[loaded[(architecture, seed)]["primary"]["source_effects"][str(src)] for seed in SEEDS] for src in FOLDS["test"]], dtype=np.float64)
        crossed = crossed_bootstrap(matrix)
        result["architectures"][architecture] = {
            "source_seed_matrix": matrix.tolist(), "source_level_mean_effect": float(matrix.mean()),
            "bootstrap_crossed": crossed, "bootstrap_source_only": source_only_bootstrap(matrix),
            "pooled_test_delta_by_seed_descriptive": {str(s): loaded[(architecture, s)]["primary"]["pooled_test_delta_descriptive"] for s in SEEDS},
            "positive_source_seed_units": int(np.sum(matrix > 0)),
            "outcome": classify(crossed["ci95"]),
        }
    result["interpretation"] = {
        "admissible": "additional predictive/decodable utility beyond the frozen input-derived P1r summary under the frozen decoder",
        "information_theoretic_claim": False, "backbone_superiority_claim": False, "last_bounded_input_derived_control": True,
    }
    atomic_json_write(output, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("preflight")
    p.add_argument("--output", type=Path, default=PREFLIGHT)
    p.add_argument("--protocol-seal", required=True)
    p.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    p = sub.add_parser("host-preflight")
    p.add_argument("--cache-root", type=Path, required=True)
    p.add_argument("--output", type=Path, default=HOST_PREFLIGHT)
    p.add_argument("--protocol-seal", required=True)
    p.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
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
        return 0 if preflight(args.output, args.protocol_seal, args.workers)["status"] == "PASS" else 1
    if args.command == "host-preflight":
        return 0 if host_preflight(args.cache_root.resolve(), args.output, args.protocol_seal, args.workers)["status"] == "PASS" else 1
    if args.command == "fit-one":
        fit_one(args.cache_root.resolve(), args.architecture, args.seed, args.output, args.protocol_seal)
        return 0
    aggregate(args.output_dir, args.output, args.protocol_seal)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
