"""Fail-closed Stage-C launcher for the sealed Phase-G1 experiment.

This file is deliberately an executable launcher rather than an import-time
experiment.  It requires both an exact pre-label commit and an explicit
``--label-access`` acknowledgement.  Feature extraction receives observations
only; evaluator truth is joined in a separate step after each stream has been
processed.  No default invocation is provided, and an existing output
directory is never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from phase_g1_core import (  # noqa: E402
    DETECTOR_SEEDS,
    FIRST_COMMON_TIMESTAMP,
    G1_CONFIG,
    SHIFTED_SCENARIOS,
    TEST_SOURCES,
    TRAIN_SOURCES,
    VALIDATION_SOURCES,
    ProtocolViolation,
    array_sha,
    apply_scaler,
    assert_fixed_robustness_strata,
    assert_semantic_nonidentifiability,
    assert_family_names,
    assert_same_row_order,
    build_feature_groups,
    build_evaluator_rows,
    extract_backbone_rows,
    assert_shared_control,
    assert_source_fold_separation,
    hierarchical_bootstrap,
    make_row_keys,
    primary_binary_mask,
    row_key_hash,
    source_cluster_sign_flip,
    reject_stratum_refit,
    reject_stratum_scaler_fit,
    require_supportive_analysis_kind,
)
from phase_g1_pipeline import (  # noqa: E402
    FeatureRecord,
    assert_common_cohort,
    assert_sealed_inputs,
    build_confirmatory_statistics,
    compute_arm_ap,
    expected_feature_arms,
    extract_candi_history,
    fit_probe_pooled,
    join_evaluator_labels,
    load_backbone_entries,
    load_candi_controls,
    probe_split_from_rows,
    require_duration_matching_resolution,
    require_prelabel_seal,
    select_primary_rows,
    _phase_f_scaler,
    _model_state_hash,
    _sha,
    current_commit,
    scientific_file_sha256,
)
import phase_g1_pipeline as _g1_pipeline  # noqa: E402


CONDITIONS = ("none", "spike", "collective", "dependency", "mixture")
SHIFTED_CONDITIONS = CONDITIONS
ARCHITECTURES = ("xlstm", "lstm")
DURATION_STRATA = (1, 16, 64, 256)
SEVERITY_STRATA = (1, 2, 3)
NONSTRESS_EVENT_TYPES = ("spike", "collective", "dependency")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def _canonical_output_dir(output_dir: Path) -> Path:
    """Return an absolute output path for repository-relative artifact links.

    Scientific execution accepts a relative output directory, but artifact
    manifests store paths relative to ROOT.  Canonicalizing once at the
    boundary keeps that serialization operation reporting-only and avoids
    calling Path.relative_to() between relative and absolute paths.
    """
    return Path(output_dir).expanduser().resolve()


def _ledger_append(path: Path, event: str, **fields: Any) -> None:
    """Append an execution-forensics record without exposing evaluator data.

    The ledger is deliberately metadata-only.  It records process progress and
    fail-closed state, never labels, scores, features, or predictions.  A
    missing terminal ``complete`` record lets the post-run auditor distinguish
    a partial/killed execution from a clean run.
    """
    record = {
        "event": str(event),
        "pid": int(__import__("os").getpid()),
        "commit": current_commit() if (ROOT / ".git").exists() else None,
        "fields": {str(key): value for key, value in fields.items()},
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")


def _clean(value: Any) -> Any:
    """Convert numpy values and fitted-model fields into JSON-safe metadata."""
    if isinstance(value, Mapping):
        return {str(k): _clean(v) for k, v in value.items() if k not in {"model", "test_prediction", "validation_prediction"}}
    if isinstance(value, np.ndarray):
        return {"shape": list(value.shape), "dtype": str(value.dtype), "sha256": array_sha(value)}
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    return value


def _source_fold(seed: int) -> str:
    if seed in TRAIN_SOURCES:
        return "train"
    if seed in VALIDATION_SOURCES:
        return "validation"
    if seed in TEST_SOURCES:
        return "test"
    raise ProtocolViolation(f"unregistered source seed: {seed}")


def _generate(seed: int, scenario: str, condition: str, semantic: str = "anomaly") -> Any:
    # This is the sole source-data boundary.  Truth is not passed to the
    # extractor: the generated object's observations are copied first, and
    # join_evaluator_labels is called only after extraction returns.
    from m0.synthetic import generate

    return generate(seed, scenario, condition, semantic)


def _observation_then_label(
    stream: Any,
    detector_seed: int,
    architecture: str,
    backbone: Any,
    candi_history: np.ndarray,
) -> dict[str, Any]:
    """Extract first, then cross the evaluator truth boundary exactly once."""
    # Copy only the observation field.  The extractor has no handle to the
    # SyntheticStream object or any evaluator metadata.
    observations = np.asarray(stream.observations, dtype=np.float32).copy()
    extracted = _observation_only_features(
        backbone,
        architecture,
        observations,
        int(stream.source_seed),
        candi_history,
    )
    record = FeatureRecord(
        detector_seed=detector_seed,
        architecture=architecture,
        source_seed=int(stream.source_seed),
        scenario=str(stream.scenario),
        condition=str(stream.condition),
        timestamps=np.asarray(extracted["timestamps"], dtype=np.int64),
        groups=extracted["groups"],
        scores=np.asarray(extracted["scores"]),
        source_fold=_source_fold(int(stream.source_seed)),
    )
    # Truth is joined only after all observation-only feature extraction for
    # this stream has completed.
    return join_evaluator_labels(record, stream)


def _observation_only_features(
    backbone: Any,
    architecture: str,
    observations: np.ndarray,
    source_seed: int,
    candi_history: np.ndarray,
) -> dict[str, Any]:
    """Extract all feature groups from observations with no evaluator truth."""
    observations = np.asarray(observations, dtype=np.float32).copy()
    timestamps = np.arange(FIRST_COMMON_TIMESTAMP, len(observations), dtype=np.int64)
    if len(timestamps) == 0:
        raise ProtocolViolation("source stream has no common t>=63 decisions")
    scaler = _phase_f_scaler(int(source_seed))
    extracted_backbone = extract_backbone_rows(backbone, architecture, observations, scaler, timestamps)
    groups = build_feature_groups(extracted_backbone["scores"], extracted_backbone["internal_base"])
    if candi_history.shape != groups["history14"].shape:
        raise ProtocolViolation("shared CANDI history shape mismatch")
    groups["candi_history14"] = np.asarray(candi_history, dtype=np.float64).copy()
    groups["candi_history_plus_combined248"] = np.concatenate((groups["candi_history14"], groups["combined234"]), axis=1)
    return {"timestamps": timestamps, "groups": groups, "scores": extracted_backbone["scores"]}


def _append_rows(target: dict[str, list], rows: Mapping[str, Any], arms: tuple[str, ...]) -> None:
    for arm in arms:
        target.setdefault(arm, []).append(select_primary_rows(rows, arm))


def _concat(parts: list[Mapping[str, Any]]) -> dict[str, Any]:
    parts = [part for part in parts if len(part["keys"]) > 0]
    if not parts:
        raise ProtocolViolation("empty pooled probe cohort")
    keys = [key for part in parts for key in part["keys"]]
    X = np.concatenate([part["X"] for part in parts], axis=0)
    y = np.concatenate([part["y"] for part in parts], axis=0)
    sources = np.concatenate([part["source_seeds"] for part in parts], axis=0)
    scenarios = tuple(x for part in parts for x in part["scenarios"])
    events = tuple(x for part in parts for x in part["events"])
    event_types = tuple(x for part in parts for x in part.get("event_types", ()))
    result = {"X": X, "y": y, "keys": keys, "source_seeds": sources,
              "scenarios": scenarios, "events": events, "event_types": event_types,
              "duration": np.concatenate([part["duration"] for part in parts]),
              "severity": np.concatenate([part["severity"] for part in parts])}
    if all("stratum" in part for part in parts):
        result["stratum"] = np.concatenate([np.asarray(part["stratum"], dtype=object) for part in parts])
    if len(event_types) != len(keys):
        raise ProtocolViolation("event-type metadata cardinality mismatch")
    from phase_g1_core import assert_unique_keys
    assert_unique_keys(keys)
    return result


def _select_category_rows(joined: Mapping[str, Any], feature_arm: str, categories: Sequence[str]) -> dict[str, Any]:
    strata = np.asarray(joined["stratum"], dtype=object)
    features = np.asarray(joined["groups"][feature_arm], dtype=np.float64)
    keep = np.isin(strata, list(categories)) & np.isfinite(features).all(axis=1)
    return {
        "X": features[keep],
        "y": np.asarray(joined["label"], dtype=np.int8)[keep],
        "keys": [dict(key) for key, include in zip(joined["keys"], keep) if include],
        "source_seeds": np.asarray(joined["source_seed"], dtype=np.int64)[keep],
        "scenarios": tuple(np.asarray(joined["scenario"], dtype=object)[keep].tolist()),
        "events": tuple(np.asarray(joined["event"], dtype=np.int32)[keep].tolist()),
        "event_types": tuple(np.asarray(joined["event_type"], dtype=object)[keep].tolist()),
        "duration": np.asarray(joined["duration"], dtype=object)[keep],
        "severity": np.asarray(joined["severity"], dtype=object)[keep],
    }


def _select_event_type_rows(joined: Mapping[str, Any], feature_arm: str, event_type: str) -> dict[str, Any]:
    """Select anomaly-only windows for one evaluator event type.

    Event type is evaluator metadata and is consulted only after the
    observation-only extractor has returned.  Mixed windows are intentionally
    excluded here and are retained in the separate mixed stress stratum.
    """
    strata = np.asarray(joined["stratum"], dtype=object)
    types = np.asarray(joined["event_type"], dtype=object)
    features = np.asarray(joined["groups"][feature_arm], dtype=np.float64)
    keep = (strata == "anomaly") & (types == event_type) & np.isfinite(features).all(axis=1)
    return {
        "X": features[keep],
        "y": np.asarray(joined["label"], dtype=np.int8)[keep],
        "keys": [dict(key) for key, include in zip(joined["keys"], keep) if include],
        "source_seeds": np.asarray(joined["source_seed"], dtype=np.int64)[keep],
        "scenarios": tuple(np.asarray(joined["scenario"], dtype=object)[keep].tolist()),
        "events": tuple(np.asarray(joined["event"], dtype=np.int32)[keep].tolist()),
        "event_types": tuple(np.asarray(joined["event_type"], dtype=object)[keep].tolist()),
        "duration": np.asarray(joined["duration"], dtype=object)[keep],
        "severity": np.asarray(joined["severity"], dtype=object)[keep],
    }


def _select_all_rows(joined: Mapping[str, Any], feature_arm: str) -> dict[str, Any]:
    """Select every finite test decision for natural-prevalence reporting.

    This evaluator-side view is never used to fit a probe or choose a
    hyperparameter.  It retains anomaly, drift, mixed, stable-new-normal and
    stationary-normal windows so the reported prevalence is the stream's
    native window prevalence rather than the prevalence of the filtered
    primary binary cohort.
    """
    features = np.asarray(joined["groups"][feature_arm], dtype=np.float64)
    keep = np.isfinite(features).all(axis=1)
    return {
        "X": features[keep],
        "y": np.asarray(joined["label"], dtype=np.int8)[keep],
        "keys": [dict(key) for key, include in zip(joined["keys"], keep) if include],
        "source_seeds": np.asarray(joined["source_seed"], dtype=np.int64)[keep],
        "scenarios": tuple(np.asarray(joined["scenario"], dtype=object)[keep].tolist()),
        "events": tuple(np.asarray(joined["event"], dtype=np.int32)[keep].tolist()),
        "event_types": tuple(np.asarray(joined["event_type"], dtype=object)[keep].tolist()),
        "duration": np.asarray(joined["duration"], dtype=object)[keep],
        "severity": np.asarray(joined["severity"], dtype=object)[keep],
        "stratum": np.asarray(joined["stratum"], dtype=object)[keep],
    }


def _select_duration_or_severity_rows(
    joined: Mapping[str, Any],
    feature_arm: str,
    common_mask: Sequence[bool],
    axis: str,
    value: int,
) -> dict[str, Any]:
    """Build one fixed robustness stratum from the ordinary anomaly stream.

    Positive rows are pure anomaly windows uniquely attributable to one
    non-stress event with the requested duration or severity.  Negative rows
    are the same eligible anomaly-free drift/transition rows used by the
    primary binary task for this source/scenario.  Drift rows deliberately do
    not receive a synthetic duration/severity value.
    """
    if axis not in {"duration", "severity"}:
        raise ProtocolViolation("robustness axis must be duration or severity")
    base = select_primary_rows(joined, feature_arm, common_mask)
    strata = np.asarray(base["stratum"], dtype=object)
    events = np.asarray(base["events"], dtype=np.int32)
    types = np.asarray(base["event_types"], dtype=object)
    metadata = np.asarray(base[axis], dtype=object)
    positive = (strata == "anomaly") & (events >= 0) & np.isin(types, NONSTRESS_EVENT_TYPES)
    positive &= np.asarray([item is not None and int(item) == int(value) for item in metadata], dtype=bool)
    negative = strata == "drift"
    # Keep every eligible drift row even when this individual
    # source/scenario/condition has no positive event in the requested bin.
    # Two-class support is assessed only after the prescribed pooling across
    # streams, so a sparse event-duration bin cannot silently change the
    # negative cohort.
    selected = positive | negative
    if not np.any(selected):
        return {
            "X": np.empty((0, base["X"].shape[1]), dtype=np.float64),
            "y": np.empty((0,), dtype=np.int8),
            "keys": [],
            "source_seeds": np.empty((0,), dtype=np.int64),
            "scenarios": tuple(),
            "events": tuple(),
            "event_types": tuple(),
            "duration": np.empty((0,), dtype=object),
            "severity": np.empty((0,), dtype=object),
            "stratum": np.empty((0,), dtype=object),
            "support": False,
            "positive_rows": int(np.sum(positive)),
            "negative_rows": int(np.sum(negative)),
            "excluded_multi_event": int(np.sum((strata == "anomaly") & (events < 0))),
            "excluded_persistent_fault": int(np.sum((strata == "anomaly") & (types == "persistent_fault"))),
            "excluded_mixed": int(np.sum(strata == "mixed")),
            "excluded_nonstress_other": int(np.sum((strata == "anomaly") & (events >= 0) & ~np.isin(types, NONSTRESS_EVENT_TYPES))),
        }
    return {
        "X": np.asarray(base["X"])[selected],
        "y": np.asarray(base["y"])[selected],
        "keys": [dict(key) for key, keep in zip(base["keys"], selected) if keep],
        "source_seeds": np.asarray(base["source_seeds"])[selected],
        "scenarios": tuple(np.asarray(base["scenarios"], dtype=object)[selected].tolist()),
        "events": tuple(np.asarray(base["events"], dtype=np.int32)[selected].tolist()),
        "event_types": tuple(np.asarray(base["event_types"], dtype=object)[selected].tolist()),
        "duration": np.asarray(base["duration"], dtype=object)[selected],
        "severity": np.asarray(base["severity"], dtype=object)[selected],
        "stratum": np.asarray(base["stratum"], dtype=object)[selected],
        "support": bool(np.any(positive) and np.any(negative)),
        "positive_rows": int(np.sum(positive)),
        "negative_rows": int(np.sum(negative)),
        "excluded_multi_event": int(np.sum((strata == "anomaly") & (events < 0))),
        "excluded_persistent_fault": int(np.sum((strata == "anomaly") & (types == "persistent_fault"))),
        "excluded_mixed": int(np.sum(strata == "mixed")),
        "excluded_nonstress_other": int(np.sum((strata == "anomaly") & (events >= 0) & ~np.isin(types, NONSTRESS_EVENT_TYPES))),
    }


def _semantic_pair_rows(
    joined: Mapping[str, Any],
    legitimate_features: Mapping[str, np.ndarray],
    feature_arm: str,
    common_mask: Sequence[bool],
) -> dict[str, Any]:
    """Retain an exact semantic-control feature pair for post-fit checks."""
    base = select_primary_rows(joined, feature_arm, common_mask)
    events = np.asarray(base["events"], dtype=np.int32)
    types = np.asarray(base["event_types"], dtype=object)
    keep = (np.asarray(base["stratum"], dtype=object) == "anomaly") & (events >= 0) & np.isin(types, NONSTRESS_EVENT_TYPES)
    keys = [dict(key) for key, include in zip(base["keys"], keep) if include]
    if not keys:
        width = int(np.asarray(base["X"]).shape[1])
        return {"anomaly_X": np.empty((0, width)), "legitimate_X": np.empty((0, width)), "keys": []}
    positions = np.flatnonzero(keep)
    anomaly_x = np.asarray(base["X"], dtype=np.float64)[positions]
    # ``legitimate_features`` has the full common decision stream; positions
    # index the same row order as ``base`` after primary/common filtering.
    legitimate_base = np.asarray(legitimate_features[feature_arm], dtype=np.float64)
    common_indices = np.flatnonzero(np.asarray(common_mask, dtype=bool))
    if legitimate_base.shape[0] != len(joined["keys"]):
        raise ProtocolViolation("semantic counterpart feature rows differ from joined observations")
    legitimate_selected = legitimate_base[common_indices]
    # The primary mask is additionally applied by select_primary_rows; recover
    # the corresponding positions by matching canonical row keys rather than
    # relying on a hidden metadata order.
    common_keys = [dict(key) for key, include in zip(joined["keys"], np.asarray(common_mask, dtype=bool)) if include]
    legitimate_by_key = {(int(key["timestamp"]), int(key["event"])): legitimate_selected[index] for index, key in enumerate(common_keys)}
    legitimate_x = np.asarray([legitimate_by_key[(int(key["timestamp"]), int(key["event"]))] for key in keys], dtype=np.float64)
    return {"anomaly_X": anomaly_x, "legitimate_X": legitimate_x, "keys": keys}


def _semantic_control_report(
    fits: Mapping[int, Mapping[str, Mapping[str, Any]]],
    semantic_pairs: Mapping[int, Mapping[str, Mapping[str, list[Mapping[str, Any]]]]],
) -> dict[str, Any]:
    """Audit the observation-identical/opposite-semantic negative control.

    This report checks feature and frozen-probe prediction invariance only. It
    is deliberately excluded from every H2/H3a robustness gate.
    """
    output: dict[str, Any] = {"status": "PASS", "analysis_kind": "semantic_nonidentifiability_control", "checks": []}
    for seed in DETECTOR_SEEDS:
        for architecture in ARCHITECTURES:
            for arm in expected_feature_arms():
                parts = [part for part in semantic_pairs[seed][architecture][arm] if len(part["keys"]) > 0]
                if not parts:
                    continue
                anomaly_x = np.concatenate([np.asarray(part["anomaly_X"], dtype=np.float64) for part in parts], axis=0)
                legitimate_x = np.concatenate([np.asarray(part["legitimate_X"], dtype=np.float64) for part in parts], axis=0)
                if anomaly_x.shape != legitimate_x.shape or not np.allclose(
                    anomaly_x, legitimate_x, atol=1e-5, rtol=1e-4, equal_nan=True
                ):
                    raise ProtocolViolation(f"semantic control feature invariance failed: {seed}/{architecture}/{arm}")
                fit = fits[seed][f"{arm}_{architecture}"]
                anomaly_pred = fit["model"].predict_proba(apply_scaler(anomaly_x, fit["scaler"]))[:, 1]
                legitimate_pred = fit["model"].predict_proba(apply_scaler(legitimate_x, fit["scaler"]))[:, 1]
                if not np.allclose(anomaly_pred, legitimate_pred, atol=1e-5, rtol=1e-4):
                    raise ProtocolViolation(f"semantic control prediction invariance failed: {seed}/{architecture}/{arm}")
                output["checks"].append({
                    "detector_seed": int(seed), "architecture": architecture, "feature_arm": arm,
                    "rows": int(len(anomaly_x)), "feature_max_abs": float(np.max(np.abs(anomaly_x - legitimate_x))) if anomaly_x.size else 0.0,
                    "prediction_max_abs": float(np.max(np.abs(anomaly_pred - legitimate_pred))) if anomaly_pred.size else 0.0,
                    "feature_invariant": True, "prediction_invariant": True,
                    "anomaly_prediction_sha256": array_sha(np.asarray(anomaly_pred)),
                    "legitimate_prediction_sha256": array_sha(np.asarray(legitimate_pred)),
                    "ap_used_as_evidence": False,
                })
    output["check_count"] = len(output["checks"])
    return output


def _robustness_effect_table(
    fits: Mapping[int, Mapping[str, Mapping[str, Any]]],
    rows: Mapping[int, Mapping[str, Mapping[str, Mapping[str, Mapping[str, list[Mapping[str, Any]]]]]]],
) -> dict[str, Any]:
    """Compute the frozen test-only duration/severity robustness gates."""
    from sklearn.metrics import average_precision_score

    require_supportive_analysis_kind("duration_severity_stratified_robustness")
    reject_stratum_refit("frozen_probe")
    reject_stratum_scaler_fit("train_only")
    assert_fixed_robustness_strata("duration", DURATION_STRATA)
    assert_fixed_robustness_strata("severity", SEVERITY_STRATA)
    matching_config = G1_CONFIG["duration_severity_matching"]
    arm_names = ("history14", "history_plus_combined248", "combined234", "candi_history14", "candi_history_plus_combined248")
    contrasts = ("h2", "h3a_a", "h3a_b", "h3a_c")
    output: dict[str, Any] = {"analysis_name": "duration_severity_stratified_robustness", "duration": {}, "severity": {}}
    for axis, values in (("duration", DURATION_STRATA), ("severity", SEVERITY_STRATA)):
        per_contrast: dict[str, list[dict[str, Any]]] = {name: [] for name in contrasts}
        ap_by_stratum: dict[str, dict[str, np.ndarray]] = {}
        exclusions: dict[str, dict[str, int]] = {}
        for value in values:
            key = str(value)
            ap_by_stratum[key] = {}
            exclusions[key] = {
                "multi_event": 0,
                "persistent_fault": 0,
                "mixed": 0,
                "nonstress_other": 0,
                "unsupported_streams": 0,
            }
            for seed_index, seed in enumerate(DETECTOR_SEEDS):
                stratum_rows: dict[str, dict[str, Any]] = {}
                for arm in arm_names:
                    for architecture in ARCHITECTURES:
                        name = f"{arm}_{architecture}"
                        matrix = ap_by_stratum[key].setdefault(name, np.full((len(TEST_SOURCES), len(DETECTOR_SEEDS)), np.nan))
                        parts = [part for part in rows[seed][architecture][arm][axis][key] if len(part["keys"]) > 0]
                        if not parts:
                            continue
                        pooled = _concat(parts)
                        stratum_rows[name] = pooled
                if len(stratum_rows) == len(arm_names) * len(ARCHITECTURES):
                    # All feature arms use the intersection mask fixed before
                    # extraction.  Recheck the exact ordered cohort at every
                    # stratum so differential NaNs cannot alter AP support.
                    reference = stratum_rows[f"history14_xlstm"]
                    for name, pooled in stratum_rows.items():
                        if name == "history14_xlstm":
                            continue
                        assert_same_row_order(reference["keys"], pooled["keys"])
                        if not np.array_equal(reference["y"], pooled["y"]):
                            raise ProtocolViolation(f"robustness labels differ for {axis}={value}/{name}")
                for arm in arm_names:
                    for architecture in ARCHITECTURES:
                        name = f"{arm}_{architecture}"
                        matrix = ap_by_stratum[key].setdefault(name, np.full((len(TEST_SOURCES), len(DETECTOR_SEEDS)), np.nan))
                        parts = [part for part in rows[seed][architecture][arm][axis][key] if len(part["keys"]) > 0]
                        if not parts:
                            continue
                        pooled = stratum_rows[name]
                        fit = fits[seed][name]
                        prediction = fit["model"].predict_proba(apply_scaler(pooled["X"], fit["scaler"]))[:, 1]
                        source_values = np.asarray(pooled["source_seeds"], dtype=np.int64)
                        labels = np.asarray(pooled["y"], dtype=np.int8)
                        for source_index, source_seed in enumerate(TEST_SOURCES):
                            mask = source_values == source_seed
                            if mask.sum() and len(np.unique(labels[mask])) == 2:
                                matrix[source_index, seed_index] = average_precision_score(labels[mask], prediction[mask])
                        if arm == "history14" and architecture == "xlstm":
                            exclusions[key]["multi_event"] += int(sum(part.get("excluded_multi_event", 0) for part in parts))
                            exclusions[key]["persistent_fault"] += int(sum(part.get("excluded_persistent_fault", 0) for part in parts))
                            exclusions[key]["mixed"] += int(sum(part.get("excluded_mixed", 0) for part in parts))
                            exclusions[key]["nonstress_other"] += int(sum(part.get("excluded_nonstress_other", 0) for part in parts))
            def matrix(name: str) -> np.ndarray:
                value_array = ap_by_stratum[key].get(name)
                if value_array is None:
                    return np.full((len(TEST_SOURCES), len(DETECTOR_SEEDS)), np.nan)
                return value_array
            x_hist = matrix("history14_xlstm")
            x_combined = matrix("history_plus_combined248_xlstm")
            l_hist = matrix("history14_lstm")
            l_combined = matrix("history_plus_combined248_lstm")
            x_internal = matrix("combined234_xlstm")
            l_internal = matrix("combined234_lstm")
            x_candi = matrix("candi_history14_xlstm")
            l_candi = matrix("candi_history14_lstm")
            x_candi_internal = matrix("candi_history_plus_combined248_xlstm")
            l_candi_internal = matrix("candi_history_plus_combined248_lstm")
            effects = {
                "h2": x_combined - x_hist,
                "h3a_a": x_internal - l_internal,
                "h3a_b": (x_combined - x_hist) - (l_combined - l_hist),
                "h3a_c": (x_candi_internal - x_candi) - (l_candi_internal - l_candi),
            }
            for name, effect in effects.items():
                support = bool(np.isfinite(effect).all())
                per_contrast[name].append({"stratum": int(value), "support": support, "effect": effect.tolist() if support else None, "mean": float(np.mean(effect)) if support else None, "positive_detector_seeds": int((np.mean(effect, axis=0) > 0).sum()) if support else None, "row_count": int(sum(len(part["keys"]) for part in rows[DETECTOR_SEEDS[0]]["xlstm"]["history14"][axis][key])) if support else 0})
        comparisons: dict[str, Any] = {}
        for name in contrasts:
            strata = per_contrast[name]
            valid = [item for item in strata if item["support"]]
            required_count = len(values)
            if len(valid) != required_count:
                comparisons[name] = {"status": "INSUFFICIENT_SUPPORT", "macro": None, "positive_strata": None, "required_strata": [int(value) for value in values], "strata": strata}
                continue
            means = np.asarray([item["mean"] for item in valid], dtype=np.float64)
            if name == "h2":
                threshold = float(matching_config[f"h2_{axis}_macro_min"])
            elif name == "h3a_a":
                threshold = float(matching_config[f"h3a_a_{axis}_macro_min"])
            else:
                threshold = float(matching_config[f"h3a_increment_{axis}_macro_min"])
            positive_count = int((means > 0).sum())
            minimum_positive = 3 if len(values) == 4 else 2
            margin_ok = float(means.mean()) >= threshold if threshold > 0 else float(means.mean()) > threshold
            comparisons[name] = {"status": "PASS" if margin_ok and positive_count >= minimum_positive else "STOP", "macro": float(means.mean()), "positive_strata": positive_count, "required_strata": [int(value) for value in values], "strata": strata, "threshold": threshold, "strict_margin": bool(threshold == 0)}
        output[axis] = {"strata": per_contrast, "comparisons": comparisons, "exclusions": exclusions}
    h2_statuses = [output[axis]["comparisons"]["h2"]["status"] for axis in ("duration", "severity")]
    if all(status == "PASS" for status in h2_statuses):
        output["h2_status"] = "PASS"
    elif any(status == "INSUFFICIENT_SUPPORT" for status in h2_statuses):
        output["h2_status"] = "INSUFFICIENT_SUPPORT"
    else:
        output["h2_status"] = "STOP"
    h3_statuses = [
        output[axis]["comparisons"][name]["status"]
        for axis in ("duration", "severity")
        for name in ("h3a_a", "h3a_b", "h3a_c")
    ]
    output["h3a_status_if_primary_h2_go"] = (
        "PASS" if all(status == "PASS" for status in h3_statuses)
        else "INSUFFICIENT_SUPPORT" if any(status == "INSUFFICIENT_SUPPORT" for status in h3_statuses)
        else "STOP"
    )
    return output


def _descriptive_strata_summary(
    fits: Mapping[int, Mapping[str, Mapping[str, Any]]],
    strata_rows: Mapping[int, Mapping[str, Mapping[str, Mapping[str, list[Mapping[str, Any]]]]]],
) -> dict[str, Any]:
    """Report mixed/anomaly-type strata without turning them confirmatory."""
    from sklearn.metrics import average_precision_score

    output: dict[str, Any] = {}
    for seed in DETECTOR_SEEDS:
        output[str(seed)] = {}
        for architecture in ARCHITECTURES:
            output[str(seed)][architecture] = {}
            for stratum, by_arm in strata_rows[seed][architecture].items():
                output[str(seed)][architecture][stratum] = {}
                for arm, parts in by_arm.items():
                    parts = [part for part in parts if len(part["keys"]) > 0]
                    if not parts:
                        output[str(seed)][architecture][stratum][arm] = {"status": "N/A", "n": 0}
                        continue
                    rows = _concat(parts)
                    fit = fits[seed][f"{arm}_{architecture}"]
                    prediction = fit["model"].predict_proba(apply_scaler(rows["X"], fit["scaler"]))[:, 1]
                    labels = np.asarray(rows["y"], dtype=np.int8)
                    ap = float(average_precision_score(labels, prediction)) if len(np.unique(labels)) == 2 else None
                    output[str(seed)][architecture][stratum][arm] = {
                        "status": "PASS" if ap is not None else "DESCRIPTIVE_ONLY",
                        "n": int(len(labels)),
                        "positives": int(labels.sum()),
                        "natural_prevalence": float(labels.mean()) if len(labels) else None,
                        "ap": ap,
                        "fixed_probability_threshold": 0.5,
                        "threshold_positive_rate": float(np.mean(prediction >= 0.5)) if len(prediction) else None,
                        "mean_predicted_anomaly_probability": float(np.mean(prediction)) if len(prediction) else None,
                        "prediction_sha256": array_sha(np.asarray(prediction)),
                        "row_key_sha256": row_key_hash(rows["keys"]),
                    }
    return output


def _natural_prevalence_summary(
    fits: Mapping[int, Mapping[str, Mapping[str, Any]]],
    natural_rows: Mapping[int, Mapping[str, Mapping[str, list[Mapping[str, Any]]]]],
) -> dict[str, Any]:
    """Evaluate frozen probes once on the native, unfiltered test prevalence."""
    from sklearn.metrics import average_precision_score

    output: dict[str, Any] = {}
    for seed in DETECTOR_SEEDS:
        output[str(seed)] = {}
        for architecture in ARCHITECTURES:
            output[str(seed)][architecture] = {}
            for arm, parts in natural_rows[seed][architecture].items():
                parts = [part for part in parts if len(part["keys"]) > 0]
                if not parts:
                    output[str(seed)][architecture][arm] = {"status": "N/A", "n": 0}
                    continue
                rows = _concat(parts)
                fit = fits[seed][f"{arm}_{architecture}"]
                prediction = fit["model"].predict_proba(apply_scaler(rows["X"], fit["scaler"]))[:, 1]
                labels = np.asarray(rows["y"], dtype=np.int8)
                ap = float(average_precision_score(labels, prediction)) if len(np.unique(labels)) == 2 else None
                output[str(seed)][architecture][arm] = {
                    "status": "PASS" if ap is not None else "DESCRIPTIVE_ONLY",
                    "n": int(len(labels)),
                    "positives": int(labels.sum()),
                    "natural_prevalence": float(labels.mean()) if len(labels) else None,
                    "ap": ap,
                    "fixed_probability_threshold": 0.5,
                    "threshold_positive_rate": float(np.mean(prediction >= 0.5)) if len(prediction) else None,
                    "mean_predicted_anomaly_probability": float(np.mean(prediction)) if len(prediction) else None,
                    "prediction_sha256": array_sha(np.asarray(prediction)),
                    "row_key_sha256": row_key_hash(rows["keys"]),
                }
    return output


def _assert_paired_arms(rows: Mapping[str, Mapping[str, Any]]) -> str:
    required = ("history14", "history_plus_combined248", "combined234",
                "candi_history14", "candi_history_plus_combined248")
    selected = {name: rows[name] for name in required if name in rows}
    if len(selected) != len(required):
        raise ProtocolViolation("required paired feature arms are missing")
    digest = assert_common_cohort(selected)
    candi = rows["candi_history14"]["X"]
    combined = rows["candi_history_plus_combined248"]["X"]
    if not np.array_equal(candi, combined[:, :14], equal_nan=True):
        raise ProtocolViolation("CANDI history does not equal combined arm prefix")
    return digest


def _source_scenario_ap(fit: Mapping[str, Any], rows: Mapping[str, Any]) -> np.ndarray:
    from sklearn.metrics import average_precision_score

    prediction = np.asarray(fit["test_prediction"], dtype=np.float64)
    y = np.asarray(rows["y"], dtype=np.int8)
    source = np.asarray(rows["source_seeds"], dtype=np.int64)
    scenario = np.asarray(rows["scenarios"], dtype=object)
    result = np.full((len(TEST_SOURCES), len(SHIFTED_SCENARIOS)), np.nan)
    for i, src in enumerate(TEST_SOURCES):
        for j, name in enumerate(SHIFTED_SCENARIOS):
            mask = (source == src) & (scenario == name)
            if mask.sum() == 0 or len(np.unique(y[mask])) < 2:
                raise ProtocolViolation(f"test source/scenario cohort lacks both classes: {src}/{name}")
            result[i, j] = average_precision_score(y[mask], prediction[mask])
    return result


def _pooled_source_ap(fits: Mapping[int, Mapping[str, Any]], rows: Mapping[int, Mapping[str, Any]]) -> dict[str, np.ndarray]:
    """Primary estimand: pooled four-scenario AP per source, then macro."""
    from sklearn.metrics import average_precision_score

    result: dict[str, np.ndarray] = {}
    for arm in fits[DETECTOR_SEEDS[0]]:
        matrix = np.full((len(TEST_SOURCES), len(DETECTOR_SEEDS)), np.nan)
        for seed_index, seed in enumerate(DETECTOR_SEEDS):
            row = rows[seed][arm]
            prediction = np.asarray(fits[seed][arm]["test_prediction"], dtype=np.float64)
            source_values = np.asarray(row["source_seeds"], dtype=np.int64)
            labels = np.asarray(row["y"], dtype=np.int8)
            for source_index, source in enumerate(TEST_SOURCES):
                mask = source_values == source
                if mask.sum() == 0 or len(np.unique(labels[mask])) < 2:
                    raise ProtocolViolation(f"pooled source cohort lacks both classes: {source}")
                matrix[source_index, seed_index] = average_precision_score(labels[mask], prediction[mask])
        result[arm] = matrix
    return result


def _specificity_summary(
    fits: Mapping[int, Mapping[str, Mapping[str, Any]]],
    specificity_rows: Mapping[int, Mapping[str, Mapping[str, Mapping[str, list[Mapping[str, Any]]]]]],
) -> dict[str, Any]:
    """Descriptive fixed-threshold specificity for stable/stationary normals."""
    result: dict[str, Any] = {}
    for seed in DETECTOR_SEEDS:
        result[str(seed)] = {}
        for architecture in ARCHITECTURES:
            result[str(seed)][architecture] = {}
            for category, by_arm in specificity_rows[seed][architecture].items():
                result[str(seed)][architecture][category] = {}
                for arm, parts in by_arm.items():
                    fit = fits[seed][f"{arm}_{architecture}"]
                    by_fold: dict[str, Any] = {}
                    for fold in ("train", "validation", "test"):
                        fold_parts = [part for part in parts if len(part["keys"]) > 0 and all(_source_fold(int(source)) == fold for source in part["source_seeds"])]
                        if not fold_parts:
                            by_fold[fold] = {"status": "N/A", "n": 0}
                            continue
                        rows = _concat(fold_parts)
                        scaled = apply_scaler(rows["X"], fit["scaler"])
                        prediction = fit["model"].predict_proba(scaled)[:, 1]
                        by_fold[fold] = {
                            "status": "PASS",
                            "n": int(len(prediction)),
                            "fixed_probability_threshold": 0.5,
                            "fpr": float(np.mean(prediction >= 0.5)),
                            "mean_predicted_anomaly_probability": float(np.mean(prediction)),
                            "prediction_sha256": array_sha(np.asarray(prediction)),
                            "row_key_sha256": row_key_hash(rows["keys"]),
                        }
                    result[str(seed)][architecture][category][arm] = {"by_fold": by_fold}
    return result


def _scenario_difference_table(
    fits: Mapping[int, Mapping[str, Mapping[str, Any]]],
    rows: Mapping[int, Mapping[str, Mapping[str, Any]]],
) -> dict[str, np.ndarray]:
    """Return descriptive [source, detector seed, scenario] effects."""
    arm_ap: dict[str, list[np.ndarray]] = {}
    for seed in DETECTOR_SEEDS:
        for arm, fit in fits[seed].items():
            arm_ap.setdefault(arm, []).append(_source_scenario_ap(fit, rows[seed][arm]))
    matrices = {arm: np.stack(values, axis=1) for arm, values in arm_ap.items()}
    def get(arm: str) -> np.ndarray:
        if arm not in matrices:
            raise ProtocolViolation(f"missing AP arm {arm}")
        return matrices[arm]
    x_hist = get("history14_xlstm")
    x_combined = get("history_plus_combined248_xlstm")
    l_hist = get("history14_lstm")
    l_combined = get("history_plus_combined248_lstm")
    x_internal = get("combined234_xlstm")
    l_internal = get("combined234_lstm")
    x_candi = get("candi_history14_xlstm")
    l_candi = get("candi_history14_lstm")
    x_candi_internal = get("candi_history_plus_combined248_xlstm")
    l_candi_internal = get("candi_history_plus_combined248_lstm")
    return {
        "h2": x_combined - x_hist,
        "h3a_a": x_internal - l_internal,
        "h3a_b": (x_combined - x_hist) - (l_combined - l_hist),
        "h3a_c": (x_candi_internal - x_candi) - (l_candi_internal - l_candi),
    }


def _difference_table(
    fits: Mapping[int, Mapping[str, Mapping[str, Any]]],
    rows: Mapping[int, Mapping[str, Mapping[str, Any]]],
) -> dict[str, np.ndarray]:
    """Return the confirmatory [source, detector seed] pooled effects.

    AP is first computed after pooling all four shifted scenarios (and their
    fixed conditions) within each source realization.  Only then are source
    and detector-seed macro units formed.  This is intentionally distinct from
    ``_scenario_difference_table``; averaging scenario APs would change the
    nonlinear AP estimand.
    """
    matrices = _pooled_source_ap(fits, rows)
    def get(arm: str) -> np.ndarray:
        if arm not in matrices:
            raise ProtocolViolation(f"missing AP arm {arm}")
        value = np.asarray(matrices[arm], dtype=np.float64)
        if value.shape != (len(TEST_SOURCES), len(DETECTOR_SEEDS)):
            raise ProtocolViolation(f"pooled AP shape mismatch for {arm}")
        return value
    x_hist = get("history14_xlstm")
    x_combined = get("history_plus_combined248_xlstm")
    l_hist = get("history14_lstm")
    l_combined = get("history_plus_combined248_lstm")
    x_internal = get("combined234_xlstm")
    l_internal = get("combined234_lstm")
    x_candi = get("candi_history14_xlstm")
    l_candi = get("candi_history14_lstm")
    x_candi_internal = get("candi_history_plus_combined248_xlstm")
    l_candi_internal = get("candi_history_plus_combined248_lstm")
    return {
        "h2": x_combined - x_hist,
        "h3a_a": x_internal - l_internal,
        "h3a_b": (x_combined - x_hist) - (l_combined - l_hist),
        "h3a_c": (x_candi_internal - x_candi) - (l_candi_internal - l_candi),
    }


class _OrderedKeyHash:
    """Incremental equivalent of ``row_key_hash`` for bounded summaries."""

    def __init__(self) -> None:
        self._digest = hashlib.sha256(b"[")
        self._count = 0

    def add(self, keys: Sequence[Mapping[str, Any]]) -> None:
        for key in keys:
            if self._count:
                self._digest.update(b",")
            self._digest.update(
                json.dumps(dict(key), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
            )
            self._count += 1

    @property
    def count(self) -> int:
        return self._count

    def hexdigest(self) -> str:
        digest = self._digest.copy()
        digest.update(b"]")
        return digest.hexdigest()


def _new_vector_acc() -> dict[str, Any]:
    return {"labels": [], "predictions": [], "keys": _OrderedKeyHash()}


def _append_vector_acc(acc: dict[str, Any], rows: Mapping[str, Any], prediction: np.ndarray) -> None:
    if len(rows["keys"]) == 0:
        return
    acc["labels"].append(np.asarray(rows["y"], dtype=np.int8).copy())
    acc["predictions"].append(np.asarray(prediction, dtype=np.float64).copy())
    acc["keys"].add(rows["keys"])


def _new_specificity_acc() -> dict[str, Any]:
    return {"n": 0, "false_positive": 0, "prediction_sum": 0.0, "keys": _OrderedKeyHash()}


def _append_specificity_acc(acc: dict[str, Any], rows: Mapping[str, Any], prediction: np.ndarray) -> None:
    if len(rows["keys"]) == 0:
        return
    values = np.asarray(prediction, dtype=np.float64)
    acc["n"] += int(len(values))
    acc["false_positive"] += int(np.sum(values >= 0.5))
    acc["prediction_sum"] += float(values.sum())
    acc["keys"].add(rows["keys"])


def _predict_frozen_rows(fit: Mapping[str, Any], rows: Mapping[str, Any]) -> np.ndarray:
    """Predict one secondary row chunk with an already-fitted frozen probe."""
    if len(rows["keys"]) == 0:
        return np.empty((0,), dtype=np.float64)
    return np.asarray(
        fit["model"].predict_proba(apply_scaler(np.asarray(rows["X"], dtype=np.float64), fit["scaler"]))[:, 1],
        dtype=np.float64,
    )


def _secondary_stream_spec() -> tuple[tuple[str, tuple[int, ...]], ...]:
    """Return the deterministic all-fold stream inventory used for replay."""
    return (
        ("train", TRAIN_SOURCES),
        ("validation", VALIDATION_SOURCES),
        ("test", TEST_SOURCES),
    )


def _write_secondary_chunk(
    cache_dir: Path,
    prefix: str,
    rows: Mapping[str, Any],
    prediction: np.ndarray,
    *,
    semantic: bool = False,
) -> dict[str, str]:
    """Persist one feature chunk so no secondary grid remains resident."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    npz_path = cache_dir / f"{prefix}.npz"
    keys_path = cache_dir / f"{prefix}.keys.json"
    metadata_path = cache_dir / f"{prefix}.metadata.json"
    if semantic:
        np.savez_compressed(
            npz_path,
            anomaly_X=np.asarray(rows["anomaly_X"], dtype=np.float64),
            legitimate_X=np.asarray(rows["legitimate_X"], dtype=np.float64),
        )
        keys = rows["keys"]
        metadata = {}
    else:
        np.savez_compressed(
            npz_path,
            X=np.asarray(rows["X"], dtype=np.float64),
            y=np.asarray(rows["y"], dtype=np.int8),
            prediction=np.asarray(prediction, dtype=np.float64),
        )
        keys = rows["keys"]
        metadata = {
            "event_types": [None if value is None else str(value) for value in rows.get("event_types", ())],
            "duration": [None if value is None else int(value) for value in rows.get("duration", ())],
            "severity": [None if value is None else int(value) for value in rows.get("severity", ())],
            "stratum": [str(value) for value in rows.get("stratum", ())],
        }
    keys_path.write_text(json.dumps(keys, sort_keys=True, separators=(",", ":")) + "\n")
    metadata_path.write_text(json.dumps(metadata, sort_keys=True, separators=(",", ":")) + "\n")
    return {
        "npz": str(npz_path),
        "keys": str(keys_path),
        "metadata": str(metadata_path),
        "npz_sha256": _sha(npz_path),
        "keys_sha256": _sha(keys_path),
        "metadata_sha256": _sha(metadata_path),
        "n": int(len(keys)),
    }


def _load_secondary_chunk(ref: Mapping[str, str], *, semantic: bool = False) -> tuple[dict[str, np.ndarray], list[dict[str, Any]], dict[str, Any]]:
    npz_path = Path(ref["npz"])
    keys_path = Path(ref["keys"])
    metadata_path = Path(ref["metadata"])
    if _sha(npz_path) != ref["npz_sha256"] or _sha(keys_path) != ref["keys_sha256"] or _sha(metadata_path) != ref["metadata_sha256"]:
        raise ProtocolViolation("secondary feature chunk hash mismatch")
    with np.load(npz_path, allow_pickle=False) as cached:
        arrays = {name: np.asarray(cached[name], dtype=np.float64 if name.endswith("X") or name == "prediction" else np.int8) for name in cached.files}
    keys = json.loads(keys_path.read_text())
    metadata = json.loads(metadata_path.read_text())
    if semantic:
        if arrays["anomaly_X"].shape != arrays["legitimate_X"].shape or len(keys) != arrays["anomaly_X"].shape[0]:
            raise ProtocolViolation("semantic secondary chunk shape mismatch")
    else:
        if arrays["X"].shape[0] != len(keys) or arrays["y"].shape != (len(keys),) or arrays["prediction"].shape != (len(keys),):
            raise ProtocolViolation("secondary chunk shape mismatch")
    return arrays, keys, metadata


def _empty_secondary_rows() -> dict[str, Any]:
    return {
        "X": np.empty((0, 0), dtype=np.float64),
        "y": np.empty((0,), dtype=np.int8),
        "keys": [],
        "source_seeds": np.empty((0,), dtype=np.int64),
        "scenarios": tuple(),
        "events": tuple(),
        "event_types": tuple(),
        "duration": np.empty((0,), dtype=object),
        "severity": np.empty((0,), dtype=object),
        "stratum": np.empty((0,), dtype=object),
    }


def _finalize_vector_acc(acc: Mapping[str, Any]) -> dict[str, Any]:
    """Finalize a scalar label/prediction accumulator without feature retention."""
    from sklearn.metrics import average_precision_score

    if not acc["labels"]:
        return {"status": "N/A", "n": 0}
    labels = np.concatenate(acc["labels"]).astype(np.int8, copy=False)
    prediction = np.concatenate(acc["predictions"]).astype(np.float64, copy=False)
    ap = float(average_precision_score(labels, prediction)) if len(np.unique(labels)) == 2 else None
    result = {
        "status": "PASS" if ap is not None else "DESCRIPTIVE_ONLY",
        "n": int(len(labels)),
        "positives": int(labels.sum()),
        "natural_prevalence": float(labels.mean()) if len(labels) else None,
        "ap": ap,
        "fixed_probability_threshold": 0.5,
        "threshold_positive_rate": float(np.mean(prediction >= 0.5)) if len(prediction) else None,
        "mean_predicted_anomaly_probability": float(np.mean(prediction)) if len(prediction) else None,
        "prediction_sha256": array_sha(np.asarray(prediction)),
        "row_key_sha256": acc["keys"].hexdigest(),
        "row_key_hash_algorithm": "canonical-json-list-stream",
    }
    return result


def _finalize_specificity_acc(acc: Mapping[str, Any]) -> dict[str, Any]:
    if int(acc["n"]) == 0:
        return {"status": "N/A", "n": 0}
    return {
        "status": "PASS",
        "n": int(acc["n"]),
        "fixed_probability_threshold": 0.5,
        "fpr": float(acc["false_positive"] / acc["n"]),
        "mean_predicted_anomaly_probability": float(acc["prediction_sum"] / acc["n"]),
        "row_key_sha256": acc["keys"].hexdigest(),
        "row_key_hash_algorithm": "canonical-json-list-stream",
    }


def _write_primary_chunk(
    cache_dir: Path,
    prefix: str,
    rows: Mapping[str, Any],
) -> dict[str, str]:
    """Persist one primary probe row chunk before advancing the stream.

    Primary fitting is pooled over all chunks for one detector seed/fold/arm,
    but no cross-seed feature matrix is retained in memory.  Numeric arrays
    use pickle-free NPZ storage; evaluator metadata needed for row-key and
    source/event auditing is kept in a separately hashed JSON sidecar.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    npz_path = cache_dir / f"{prefix}.npz"
    keys_path = cache_dir / f"{prefix}.keys.json"
    metadata_path = cache_dir / f"{prefix}.metadata.json"
    np.savez_compressed(
        npz_path,
        X=np.asarray(rows["X"], dtype=np.float64),
        y=np.asarray(rows["y"], dtype=np.int8),
        source_seeds=np.asarray(rows["source_seeds"], dtype=np.int64),
    )
    keys = [dict(key) for key in rows["keys"]]
    keys_path.write_text(json.dumps(keys, sort_keys=True, separators=(",", ":")) + "\n")
    metadata = {
        "scenarios": [str(value) for value in rows.get("scenarios", ())],
        "events": [int(value) for value in rows.get("events", ())],
        "event_types": [None if value is None else str(value) for value in rows.get("event_types", ())],
        "stratum": [str(value) for value in rows.get("stratum", ())],
        "duration": [None if value is None else int(value) for value in rows.get("duration", ())],
        "severity": [None if value is None else int(value) for value in rows.get("severity", ())],
    }
    metadata_path.write_text(json.dumps(metadata, sort_keys=True, separators=(",", ":")) + "\n")
    return {
        "npz": str(npz_path),
        "keys": str(keys_path),
        "metadata": str(metadata_path),
        "npz_sha256": _sha(npz_path),
        "keys_sha256": _sha(keys_path),
        "metadata_sha256": _sha(metadata_path),
        "n": int(len(keys)),
    }


def _load_primary_chunk(ref: Mapping[str, str]) -> dict[str, Any]:
    """Load and validate one primary chunk from the immutable cache."""
    npz_path = Path(ref["npz"])
    keys_path = Path(ref["keys"])
    metadata_path = Path(ref["metadata"])
    if _sha(npz_path) != ref["npz_sha256"] or _sha(keys_path) != ref["keys_sha256"] or _sha(metadata_path) != ref["metadata_sha256"]:
        raise ProtocolViolation("primary feature chunk hash mismatch")
    with np.load(npz_path, allow_pickle=False) as cached:
        X = np.asarray(cached["X"], dtype=np.float64)
        y = np.asarray(cached["y"], dtype=np.int8)
        source_seeds = np.asarray(cached["source_seeds"], dtype=np.int64)
    keys = json.loads(keys_path.read_text())
    metadata = json.loads(metadata_path.read_text())
    n = len(keys)
    if X.ndim != 2 or X.shape[0] != n or y.shape != (n,) or source_seeds.shape != (n,):
        raise ProtocolViolation("primary feature chunk shape mismatch")
    fields = ("scenarios", "events", "event_types", "stratum", "duration", "severity")
    if any(len(metadata.get(field, [])) != n for field in fields):
        raise ProtocolViolation("primary feature chunk metadata cardinality mismatch")
    from phase_g1_core import assert_unique_keys

    assert_unique_keys(keys)
    return {
        "X": X,
        "y": y,
        "keys": keys,
        "source_seeds": source_seeds,
        "scenarios": tuple(metadata["scenarios"]),
        "events": tuple(int(value) for value in metadata["events"]),
        "event_types": tuple(metadata["event_types"]),
        "stratum": np.asarray(metadata["stratum"], dtype=object),
        "duration": np.asarray(metadata["duration"], dtype=object),
        "severity": np.asarray(metadata["severity"], dtype=object),
    }


def _materialize_semantic_artifact(
    refs: Sequence[Mapping[str, str]],
    artifact_dir: Path,
    stem: str,
) -> dict[str, Any]:
    """Merge semantic chunks one arm at a time into the sealed audit format."""
    if not refs:
        return {"status": "N/A"}
    anomaly_parts: list[np.ndarray] = []
    legitimate_parts: list[np.ndarray] = []
    keys: list[dict[str, Any]] = []
    for ref in refs:
        arrays, chunk_keys, _metadata = _load_secondary_chunk(ref, semantic=True)
        anomaly_parts.append(np.asarray(arrays["anomaly_X"], dtype=np.float64))
        legitimate_parts.append(np.asarray(arrays["legitimate_X"], dtype=np.float64))
        keys.extend(chunk_keys)
    anomaly_x = np.concatenate(anomaly_parts, axis=0)
    legitimate_x = np.concatenate(legitimate_parts, axis=0)
    if anomaly_x.shape != legitimate_x.shape or anomaly_x.shape[0] != len(keys):
        raise ProtocolViolation(f"semantic artifact materialization shape mismatch: {stem}")
    feature_path = artifact_dir / f"semantic_{stem}_features.npz"
    keys_path = artifact_dir / f"semantic_{stem}_keys.json"
    np.savez_compressed(feature_path, anomaly_X=anomaly_x, legitimate_X=legitimate_x)
    keys_path.write_text(json.dumps(keys, sort_keys=True, separators=(",", ":")) + "\n")
    return {
        "status": "PASS",
        "features": str(feature_path.relative_to(ROOT)),
        "features_sha256": _sha(feature_path),
        "keys": str(keys_path.relative_to(ROOT)),
        "keys_sha256": _sha(keys_path),
        "row_key_sha256": row_key_hash(keys),
        "n": int(len(keys)),
        "chunk_count": int(len(refs)),
        "chunks": [
            {
                "npz": str(ref["npz"]),
                "keys": str(ref["keys"]),
                "metadata": str(ref["metadata"]),
                "npz_sha256": ref["npz_sha256"],
                "keys_sha256": ref["keys_sha256"],
                "metadata_sha256": ref["metadata_sha256"],
            }
            for ref in refs
        ],
    }


def _materialize_robustness_artifact(
    refs: Sequence[Mapping[str, str]],
    artifact_dir: Path,
    stem: str,
    axis: str,
    value: int,
) -> dict[str, Any]:
    """Merge one bounded robustness arm into the post-run audit format."""
    if not refs:
        return {"status": "INSUFFICIENT_SUPPORT", "axis": axis, "stratum": int(value)}
    feature_parts: list[np.ndarray] = []
    label_parts: list[np.ndarray] = []
    prediction_parts: list[np.ndarray] = []
    keys: list[dict[str, Any]] = []
    metadata_parts: dict[str, list[Any]] = {"event_types": [], "duration": [], "severity": [], "stratum": []}
    for ref in refs:
        arrays, chunk_keys, metadata = _load_secondary_chunk(ref)
        feature_parts.append(np.asarray(arrays["X"], dtype=np.float64))
        label_parts.append(np.asarray(arrays["y"], dtype=np.int8))
        prediction_parts.append(np.asarray(arrays["prediction"], dtype=np.float64))
        keys.extend(chunk_keys)
        for field in metadata_parts:
            metadata_parts[field].extend(metadata.get(field, []))
    features = np.concatenate(feature_parts, axis=0)
    labels = np.concatenate(label_parts, axis=0)
    prediction = np.concatenate(prediction_parts, axis=0)
    n = len(keys)
    if features.shape[0] != n or labels.shape != (n,) or prediction.shape != (n,) or any(len(values) != n for values in metadata_parts.values()):
        raise ProtocolViolation(f"robustness artifact materialization shape mismatch: {stem}")
    labels_path = artifact_dir / f"robustness_{stem}_labels.npy"
    prediction_path = artifact_dir / f"robustness_{stem}_prediction.npy"
    features_path = artifact_dir / f"robustness_{stem}_features.npz"
    keys_path = artifact_dir / f"robustness_{stem}_keys.json"
    metadata_path = artifact_dir / f"robustness_{stem}_metadata.json"
    np.save(labels_path, labels, allow_pickle=False)
    np.save(prediction_path, prediction, allow_pickle=False)
    np.savez_compressed(features_path, X=features)
    keys_path.write_text(json.dumps(keys, sort_keys=True, separators=(",", ":")) + "\n")
    metadata_path.write_text(json.dumps(metadata_parts, sort_keys=True, separators=(",", ":")) + "\n")
    return {
        "status": "PASS",
        "axis": axis,
        "stratum": int(value),
        "labels": str(labels_path.relative_to(ROOT)),
        "labels_sha256": _sha(labels_path),
        "prediction": str(prediction_path.relative_to(ROOT)),
        "prediction_sha256": _sha(prediction_path),
        "features": str(features_path.relative_to(ROOT)),
        "features_sha256": _sha(features_path),
        "keys": str(keys_path.relative_to(ROOT)),
        "keys_sha256": _sha(keys_path),
        "metadata": str(metadata_path.relative_to(ROOT)),
        "metadata_sha256": _sha(metadata_path),
        "row_key_sha256": row_key_hash(keys),
        "n": int(n),
        "positives": int(labels.sum()),
        "chunk_count": int(len(refs)),
        "chunks": [
            {
                "npz": str(ref["npz"]),
                "keys": str(ref["keys"]),
                "metadata": str(ref["metadata"]),
                "npz_sha256": ref["npz_sha256"],
                "keys_sha256": ref["keys_sha256"],
                "metadata_sha256": ref["metadata_sha256"],
            }
            for ref in refs
        ],
    }


def _robustness_report_from_ap(
    ap_by_axis: Mapping[str, Mapping[str, Mapping[str, np.ndarray]]],
    row_counts: Mapping[str, Mapping[str, Sequence[int]]],
    exclusions: Mapping[str, Mapping[str, Mapping[str, int]]],
) -> dict[str, Any]:
    """Build the frozen duration/severity report from source-wise AP matrices."""
    require_supportive_analysis_kind("duration_severity_stratified_robustness")
    reject_stratum_refit("frozen_probe")
    reject_stratum_scaler_fit("train_only")
    assert_fixed_robustness_strata("duration", DURATION_STRATA)
    assert_fixed_robustness_strata("severity", SEVERITY_STRATA)
    matching_config = G1_CONFIG["duration_severity_matching"]
    contrasts = ("h2", "h3a_a", "h3a_b", "h3a_c")
    output: dict[str, Any] = {"analysis_name": "duration_severity_stratified_robustness", "duration": {}, "severity": {}}
    for axis, values in (("duration", DURATION_STRATA), ("severity", SEVERITY_STRATA)):
        per_contrast: dict[str, list[dict[str, Any]]] = {name: [] for name in contrasts}
        for value in values:
            key = str(value)
            matrices = ap_by_axis[axis].get(key, {})
            def m(name: str) -> np.ndarray:
                return np.asarray(matrices.get(name, np.full((len(TEST_SOURCES), len(DETECTOR_SEEDS)), np.nan)), dtype=np.float64)
            x_hist = m("history14_xlstm")
            x_combined = m("history_plus_combined248_xlstm")
            l_hist = m("history14_lstm")
            l_combined = m("history_plus_combined248_lstm")
            x_internal = m("combined234_xlstm")
            l_internal = m("combined234_lstm")
            x_candi = m("candi_history14_xlstm")
            l_candi = m("candi_history14_lstm")
            x_candi_internal = m("candi_history_plus_combined248_xlstm")
            l_candi_internal = m("candi_history_plus_combined248_lstm")
            effects = {
                "h2": x_combined - x_hist,
                "h3a_a": x_internal - l_internal,
                "h3a_b": (x_combined - x_hist) - (l_combined - l_hist),
                "h3a_c": (x_candi_internal - x_candi) - (l_candi_internal - l_candi),
            }
            for name, effect in effects.items():
                supported = bool(effect.shape == (len(TEST_SOURCES), len(DETECTOR_SEEDS)) and np.isfinite(effect).all())
                per_contrast[name].append({
                    "stratum": int(value),
                    "support": supported,
                    "effect": effect.tolist() if supported else None,
                    "mean": float(effect.mean()) if supported else None,
                    "positive_detector_seeds": int((effect.mean(axis=0) > 0).sum()) if supported else None,
                    "row_count": int(row_counts.get(axis, {}).get(key, (0,))[0]) if supported else 0,
                })
        comparisons: dict[str, Any] = {}
        for name in contrasts:
            strata = per_contrast[name]
            if not all(item["support"] for item in strata):
                comparisons[name] = {
                    "status": "INSUFFICIENT_SUPPORT",
                    "macro": None,
                    "positive_strata": None,
                    "required_strata": [int(value) for value in values],
                    "strata": strata,
                }
                continue
            means = np.asarray([item["mean"] for item in strata], dtype=np.float64)
            if name == "h2":
                threshold = float(matching_config[f"h2_{axis}_macro_min"])
            elif name == "h3a_a":
                threshold = float(matching_config[f"h3a_a_{axis}_macro_min"])
            else:
                threshold = float(matching_config[f"h3a_increment_{axis}_macro_min"])
            positive_count = int((means > 0).sum())
            minimum_positive = 3 if len(values) == 4 else 2
            margin_ok = float(means.mean()) >= threshold if threshold > 0 else float(means.mean()) > threshold
            comparisons[name] = {
                "status": "PASS" if margin_ok and positive_count >= minimum_positive else "STOP",
                "macro": float(means.mean()),
                "positive_strata": positive_count,
                "required_strata": [int(value) for value in values],
                "strata": strata,
                "threshold": threshold,
                "strict_margin": bool(threshold == 0),
            }
        output[axis] = {
            "strata": per_contrast,
            "comparisons": comparisons,
            "exclusions": {str(value): dict(exclusions.get(axis, {}).get(str(value), {})) for value in values},
        }
    h2_statuses = [output[axis]["comparisons"]["h2"]["status"] for axis in ("duration", "severity")]
    output["h2_status"] = "PASS" if all(status == "PASS" for status in h2_statuses) else "INSUFFICIENT_SUPPORT" if any(status == "INSUFFICIENT_SUPPORT" for status in h2_statuses) else "STOP"
    h3_statuses = [output[axis]["comparisons"][name]["status"] for axis in ("duration", "severity") for name in ("h3a_a", "h3a_b", "h3a_c")]
    output["h3a_status_if_primary_h2_go"] = "PASS" if all(status == "PASS" for status in h3_statuses) else "INSUFFICIENT_SUPPORT" if any(status == "INSUFFICIENT_SUPPORT" for status in h3_statuses) else "STOP"
    return output


def _secondary_streaming_pass(
    fits: Mapping[int, Mapping[str, Mapping[str, Any]]],
    frozen_backbones: Mapping[int, Mapping[str, Any]],
    frozen_candi: Mapping[int, tuple[Any, Mapping[str, Any]]],
    feature_arms: Sequence[str],
    output_dir: Path,
    artifact_dir: Path,
) -> dict[str, Any]:
    """Recompute secondary views one detector seed/stream at a time.

    The primary train/validation/test binary rows are needed for probe fitting
    and are handled by the caller.  Native-prevalence, specificity,
    semantic-control and duration/severity views are deliberately regenerated
    after fitting and reduced to scalar predictions or incrementally persisted
    chunks.  At no point does this function retain the full secondary feature
    grid, while the final per-arm artifacts remain available for the
    post-label audit.
    """
    from sklearn.metrics import average_precision_score

    cache_dir = output_dir / "g1_secondary_cache"
    if cache_dir.exists():
        raise ProtocolViolation(f"refusing to reuse secondary cache directory: {cache_dir}")
    cache_dir.mkdir(parents=True, exist_ok=False)

    specificity_result: dict[str, Any] = {}
    descriptive_result: dict[str, Any] = {}
    natural_result: dict[str, Any] = {}
    semantic_control_checks: list[dict[str, Any]] = []
    semantic_report_checks: list[dict[str, Any]] = []
    semantic_artifacts: dict[str, Any] = {}
    robustness_artifacts: dict[str, Any] = {}
    robustness_names = [f"{arm}_{architecture}" for arm in feature_arms for architecture in ARCHITECTURES]
    robustness_ap: dict[str, dict[str, dict[str, np.ndarray]]] = {
        axis: {
            str(value): {name: np.full((len(TEST_SOURCES), len(DETECTOR_SEEDS)), np.nan) for name in robustness_names}
            for value in (DURATION_STRATA if axis == "duration" else SEVERITY_STRATA)
        }
        for axis in ("duration", "severity")
    }
    robustness_row_counts: dict[str, dict[str, list[int]]] = {
        axis: {str(value): [0] * len(DETECTOR_SEEDS) for value in (DURATION_STRATA if axis == "duration" else SEVERITY_STRATA)}
        for axis in ("duration", "severity")
    }
    robustness_exclusions: dict[str, dict[str, dict[str, int]]] = {
        axis: {
            str(value): {field: 0 for field in ("multi_event", "persistent_fault", "mixed", "nonstress_other", "unsupported_streams")}
            for value in (DURATION_STRATA if axis == "duration" else SEVERITY_STRATA)
        }
        for axis in ("duration", "severity")
    }

    for seed_index, detector_seed in enumerate(DETECTOR_SEEDS):
        backbones = frozen_backbones[int(detector_seed)]
        candi_model, candi_row = frozen_candi[int(detector_seed)]
        seed_specificity = {
            architecture: {
                category: {arm: {fold: _new_specificity_acc() for fold in ("train", "validation", "test")} for arm in feature_arms}
                for category in ("stable_new_normal", "stationary_normal")
            }
            for architecture in ARCHITECTURES
        }
        seed_descriptive = {
            architecture: {stratum: {arm: _new_vector_acc() for arm in feature_arms} for stratum in ("mixed", "spike", "collective", "dependency")}
            for architecture in ARCHITECTURES
        }
        seed_natural = {architecture: {arm: _new_vector_acc() for arm in feature_arms} for architecture in ARCHITECTURES}
        semantic_refs: dict[str, list[dict[str, str]]] = {
            f"{arm}_{architecture}": [] for arm in feature_arms for architecture in ARCHITECTURES
        }
        robustness_refs: dict[str, list[dict[str, str]]] = {
            f"{axis}{value}_{arm}_{architecture}": []
            for axis, values in (("duration", DURATION_STRATA), ("severity", SEVERITY_STRATA))
            for value in values
            for arm in feature_arms
            for architecture in ARCHITECTURES
        }
        for fold, sources in _secondary_stream_spec():
            for source in sources:
                scenario_conditions = [(scenario, condition) for scenario in SHIFTED_SCENARIOS for condition in SHIFTED_CONDITIONS]
                scenario_conditions.append(("stationary", "none"))
                for scenario, condition in scenario_conditions:
                    stream = _generate(int(source), scenario, condition)
                    observations = np.asarray(stream.observations, dtype=np.float32).copy()
                    timestamps = np.arange(FIRST_COMMON_TIMESTAMP, len(observations), dtype=np.int64)
                    if len(timestamps) == 0:
                        raise ProtocolViolation("secondary stream has no common t>=63 decisions")
                    candi_history = extract_candi_history(candi_model, candi_row, observations, timestamps)
                    per_architecture = {
                        architecture: _observation_then_label(
                            stream, detector_seed, architecture, backbones[architecture], candi_history
                        )
                        for architecture in ARCHITECTURES
                    }

                    # Descriptive and native-prevalence summaries consume only
                    # scalar predictions; no feature matrix is retained.
                    for architecture in ARCHITECTURES:
                        for arm in feature_arms:
                            fit = fits[int(detector_seed)][f"{arm}_{architecture}"]
                            if fold == "test":
                                natural_rows = _select_all_rows(per_architecture[architecture], arm)
                                _append_vector_acc(seed_natural[architecture][arm], natural_rows, _predict_frozen_rows(fit, natural_rows))
                                if scenario in SHIFTED_SCENARIOS:
                                    mixed_rows = _select_category_rows(per_architecture[architecture], arm, ("mixed",))
                                    _append_vector_acc(seed_descriptive[architecture]["mixed"][arm], mixed_rows, _predict_frozen_rows(fit, mixed_rows))
                                    for event_type in ("spike", "collective", "dependency"):
                                        type_rows = _select_event_type_rows(per_architecture[architecture], arm, event_type)
                                        _append_vector_acc(seed_descriptive[architecture][event_type][arm], type_rows, _predict_frozen_rows(fit, type_rows))
                            category = "stationary_normal" if scenario == "stationary" else "stable_new_normal" if scenario in SHIFTED_SCENARIOS else None
                            if category is not None:
                                category_rows = _select_category_rows(per_architecture[architecture], arm, (category,))
                                _append_specificity_acc(
                                    seed_specificity[architecture][category][arm][fold],
                                    category_rows,
                                    _predict_frozen_rows(fit, category_rows),
                                )

                    if scenario not in SHIFTED_SCENARIOS or fold != "test":
                        continue

                    # The same common finite-row mask used for primary paired
                    # comparisons is reused for every robustness/semantic arm.
                    common_mask = primary_binary_mask(per_architecture["xlstm"], allow_empty=True)
                    for architecture in ARCHITECTURES:
                        for arm in feature_arms:
                            values = np.asarray(per_architecture[architecture]["groups"][arm], dtype=np.float64)
                            if values.shape[0] != len(common_mask):
                                raise ProtocolViolation("secondary feature rows differ across arms")
                            common_mask &= np.isfinite(values).all(axis=1)

                    for axis, values in (("duration", DURATION_STRATA), ("severity", SEVERITY_STRATA)):
                        for value in values:
                            key = str(value)
                            selected_rows: dict[str, dict[str, Any]] = {}
                            for architecture in ARCHITECTURES:
                                for arm in feature_arms:
                                    name = f"{arm}_{architecture}"
                                    selected_rows[name] = _select_duration_or_severity_rows(
                                        per_architecture[architecture], arm, common_mask, axis, int(value)
                                    )
                            nonempty = [row for row in selected_rows.values() if row["keys"]]
                            if nonempty and len(nonempty) != len(selected_rows):
                                raise ProtocolViolation(f"robustness arm support differs for {axis}={value}")
                            reference = nonempty[0] if nonempty else next(iter(selected_rows.values()))
                            for name, row in selected_rows.items():
                                if row["keys"]:
                                    assert_same_row_order(reference["keys"], row["keys"])
                                    if not np.array_equal(reference["y"], row["y"]):
                                        raise ProtocolViolation(f"robustness labels differ for {axis}={value}/{name}")
                            for field in ("excluded_multi_event", "excluded_persistent_fault", "excluded_mixed", "excluded_nonstress_other"):
                                robustness_exclusions[axis][key][field.removeprefix("excluded_")] += int(reference.get(field, 0))
                            if reference["keys"]:
                                robustness_row_counts[axis][key][seed_index] += int(len(reference["keys"]))
                            for name, row in selected_rows.items():
                                if not row["keys"]:
                                    continue
                                fit = fits[int(detector_seed)][name]
                                prediction = _predict_frozen_rows(fit, row)
                                prefix = f"robust_seed{detector_seed}_{source}_{scenario}_{condition}_{axis}{value}_{name}"
                                ref = _write_secondary_chunk(cache_dir, prefix, row, prediction)
                                robustness_refs[f"{axis}{value}_{name}"].append(ref)

                    # Generate the opposite-semantic stream only after all
                    # ordinary observation-only features for this stream are
                    # complete.  It is a negative control, never a probe arm.
                    legitimate_stream = _generate(int(source), scenario, condition, "legitimate")
                    if not np.array_equal(observations, np.asarray(legitimate_stream.observations, dtype=np.float32)):
                        raise ProtocolViolation("semantic legitimate counterpart changed observations")
                    legitimate_truth = build_evaluator_rows(legitimate_stream, timestamps, 64)
                    for architecture in ARCHITECTURES:
                        legitimate_features = _observation_only_features(
                            backbones[architecture], architecture,
                            np.asarray(legitimate_stream.observations, dtype=np.float32), int(source), candi_history,
                        )
                        if not np.array_equal(legitimate_features["timestamps"], per_architecture[architecture]["timestamps"]):
                            raise ProtocolViolation("semantic counterpart timestamps differ")
                        if not np.array_equal(
                            np.asarray(per_architecture[architecture]["event"], dtype=np.int32),
                            np.asarray(legitimate_truth["event"], dtype=np.int32),
                        ):
                            raise ProtocolViolation("semantic counterpart event IDs differ")
                        anomaly_event_labels = np.asarray(per_architecture[architecture]["label"], dtype=np.int8)
                        legitimate_event_labels = np.asarray(legitimate_truth["label"], dtype=np.int8)
                        event_rows = anomaly_event_labels == 1
                        if not np.all(legitimate_event_labels[event_rows] == 0):
                            raise ProtocolViolation("semantic counterpart truth is not opposite on event rows")
                        group_diffs: dict[str, float] = {}
                        for arm in feature_arms:
                            left_values = np.asarray(per_architecture[architecture]["groups"][arm], dtype=np.float64)
                            right_values = np.asarray(legitimate_features["groups"][arm], dtype=np.float64)
                            assert_semantic_nonidentifiability(
                                observations,
                                np.asarray(legitimate_stream.observations, dtype=np.float32),
                                left_values,
                                right_values,
                            )
                            group_diffs[arm] = float(np.nanmax(np.abs(left_values - right_values))) if left_values.size else 0.0
                            pair = _semantic_pair_rows(per_architecture[architecture], legitimate_features["groups"], arm, common_mask)
                            if pair["keys"]:
                                fit = fits[int(detector_seed)][f"{arm}_{architecture}"]
                                anomaly_prediction = _predict_frozen_rows(fit, {"X": pair["anomaly_X"], "keys": pair["keys"]})
                                legitimate_prediction = _predict_frozen_rows(fit, {"X": pair["legitimate_X"], "keys": pair["keys"]})
                                if not np.allclose(anomaly_prediction, legitimate_prediction, atol=1e-5, rtol=1e-4):
                                    raise ProtocolViolation(f"semantic counterpart prediction mismatch: {detector_seed}/{architecture}/{arm}")
                                semantic_report_checks.append({
                                    "detector_seed": int(detector_seed), "source_seed": int(source),
                                    "scenario": str(scenario), "condition": str(condition),
                                    "architecture": architecture, "feature_arm": arm, "rows": int(len(pair["keys"])),
                                    "feature_max_abs": float(np.nanmax(np.abs(pair["anomaly_X"] - pair["legitimate_X"]))) if pair["anomaly_X"].size else 0.0,
                                    "prediction_max_abs": float(np.max(np.abs(anomaly_prediction - legitimate_prediction))) if anomaly_prediction.size else 0.0,
                                    "feature_invariant": True, "prediction_invariant": True,
                                    "ap_used_as_evidence": False,
                                    "anomaly_prediction_sha256": array_sha(anomaly_prediction),
                                    "legitimate_prediction_sha256": array_sha(legitimate_prediction),
                                })
                                prefix = f"semantic_seed{detector_seed}_{source}_{scenario}_{condition}_{arm}_{architecture}"
                                semantic_refs[f"{arm}_{architecture}"].append(
                                    _write_secondary_chunk(cache_dir, prefix, pair, np.empty((0,), dtype=np.float64), semantic=True)
                                )
                        semantic_control_checks.append({
                            "detector_seed": int(detector_seed), "source_seed": int(source),
                            "scenario": str(scenario), "condition": str(condition),
                            "observations_identical": True, "timestamps_identical": True,
                            "event_ids_identical": True, "truth_opposite_on_event_rows": True,
                            "feature_max_abs_diffs": group_diffs,
                        })

        # Finalize scalar secondary summaries for this seed and release all
        # per-stream feature/prediction lists before advancing to seed+1.
        seed_specificity_result: dict[str, Any] = {}
        for architecture in ARCHITECTURES:
            seed_specificity_result[architecture] = {}
            for category in ("stable_new_normal", "stationary_normal"):
                seed_specificity_result[architecture][category] = {}
                for arm in feature_arms:
                    seed_specificity_result[architecture][category][arm] = {
                        "by_fold": {
                            fold: _finalize_specificity_acc(seed_specificity[architecture][category][arm][fold])
                            for fold in ("train", "validation", "test")
                        }
                    }
        specificity_result[str(detector_seed)] = seed_specificity_result
        descriptive_result[str(detector_seed)] = {
            architecture: {
                stratum: {arm: _finalize_vector_acc(seed_descriptive[architecture][stratum][arm]) for arm in feature_arms}
                for stratum in ("mixed", "spike", "collective", "dependency")
            }
            for architecture in ARCHITECTURES
        }
        natural_result[str(detector_seed)] = {
            architecture: {arm: _finalize_vector_acc(seed_natural[architecture][arm]) for arm in feature_arms}
            for architecture in ARCHITECTURES
        }

        # Materialize one final audit artifact at a time.  Chunk references are
        # retained only as immutable provenance metadata; feature arrays are
        # not kept in the Python object graph.
        for key, refs in semantic_refs.items():
            stem = f"seed{detector_seed}_{key}"
            semantic_artifacts[stem] = _materialize_semantic_artifact(refs, artifact_dir, stem)
        for axis, values in (("duration", DURATION_STRATA), ("severity", SEVERITY_STRATA)):
            for value in values:
                key = str(value)
                for name in robustness_names:
                    stem = f"seed{detector_seed}_{axis}{key}_{name}"
                    refs = robustness_refs[f"{axis}{value}_{name}"]
                    robustness_artifacts[stem] = _materialize_robustness_artifact(refs, artifact_dir, stem, axis, int(value))
                    if refs:
                        # Re-open the already materialized artifact one arm at
                        # a time to compute source-pooled AP. This avoids a
                        # second in-memory copy of every robustness label and
                        # prediction chunk while preserving the source-level
                        # AP estimand.
                        materialized = robustness_artifacts[stem]
                        labels = np.load(ROOT / materialized["labels"], allow_pickle=False).astype(np.int8, copy=False)
                        predictions = np.load(ROOT / materialized["prediction"], allow_pickle=False).astype(np.float64, copy=False)
                        materialized_keys = json.loads((ROOT / materialized["keys"]).read_text())
                        source_values = np.asarray([int(item["source_seed"]) for item in materialized_keys], dtype=np.int64)
                        for source_index, source_seed in enumerate(TEST_SOURCES):
                            mask = source_values == source_seed
                            if mask.any() and len(np.unique(labels[mask])) == 2:
                                robustness_ap[axis][key][name][source_index, seed_index] = average_precision_score(labels[mask], predictions[mask])
                        del labels, predictions, materialized_keys, source_values

    semantic_report = {
        "status": "PASS",
        "analysis_kind": "semantic_nonidentifiability_control",
        "checks": semantic_report_checks,
        "check_count": len(semantic_report_checks),
    }
    robustness_report = _robustness_report_from_ap(robustness_ap, robustness_row_counts, robustness_exclusions)
    return {
        "specificity": specificity_result,
        "descriptive_test": descriptive_result,
        "natural_prevalence": natural_result,
        "semantic_report": semantic_report,
        "semantic_control_checks": semantic_control_checks,
        "semantic_artifacts": semantic_artifacts,
        "robustness_report": robustness_report,
        "robustness_artifacts": robustness_artifacts,
        "secondary_cache_dir": str(cache_dir.relative_to(ROOT)),
        "secondary_cache_file_count": sum(1 for _ in cache_dir.iterdir()),
    }


def _light_primary_rows(rows: Mapping[str, Any]) -> dict[str, Any]:
    """Drop primary feature matrices after they have been persisted."""
    return {
        "y": np.asarray(rows["y"], dtype=np.int8),
        "keys": list(rows["keys"]),
        "source_seeds": np.asarray(rows["source_seeds"], dtype=np.int64),
        "scenarios": tuple(rows["scenarios"]),
        "events": tuple(rows["events"]),
    }


def _write_primary_probe_artifacts(
    seed: int,
    fits_for_seed: Mapping[str, Mapping[str, Any]],
    train_rows: Mapping[str, Mapping[str, Any]],
    validation_rows: Mapping[str, Mapping[str, Any]],
    test_rows: Mapping[str, Mapping[str, Any]],
    artifact_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Persist one detector seed's primary probes and return compact summaries."""
    test_results: dict[str, Any] = {}
    artifact_entries: dict[str, Any] = {}
    for arm, fit in fits_for_seed.items():
        rows = test_rows[arm]
        stem = f"seed{seed}_{arm}"
        labels_path = artifact_dir / f"{stem}_labels.npy"
        prediction_path = artifact_dir / f"{stem}_prediction.npy"
        keys_path = artifact_dir / f"{stem}_keys.json"
        np.save(labels_path, np.asarray(rows["y"], dtype=np.int8), allow_pickle=False)
        np.save(prediction_path, np.asarray(fit["test_prediction"], dtype=np.float64), allow_pickle=False)
        keys_path.write_text(json.dumps(rows["keys"], sort_keys=True, separators=(",", ":")) + "\n")
        train_row = train_rows[arm]
        val_row = validation_rows[arm]
        train_val_path = artifact_dir / f"{stem}_train_validation.npz"
        np.savez_compressed(
            train_val_path,
            train_X=np.asarray(train_row["X"], dtype=np.float64),
            train_y=np.asarray(train_row["y"], dtype=np.int8),
            validation_X=np.asarray(val_row["X"], dtype=np.float64),
            validation_y=np.asarray(val_row["y"], dtype=np.int8),
        )
        train_keys_path = artifact_dir / f"{stem}_train_keys.json"
        val_keys_path = artifact_dir / f"{stem}_validation_keys.json"
        train_keys_path.write_text(json.dumps(train_row["keys"], sort_keys=True, separators=(",", ":")) + "\n")
        val_keys_path.write_text(json.dumps(val_row["keys"], sort_keys=True, separators=(",", ":")) + "\n")
        validation_labels_path = artifact_dir / f"{stem}_validation_labels.npy"
        np.save(validation_labels_path, np.asarray(val_row["y"], dtype=np.int8), allow_pickle=False)
        test_features_path = artifact_dir / f"{stem}_test_features.npz"
        np.savez_compressed(test_features_path, test_X=np.asarray(rows["X"], dtype=np.float64))
        validation_prediction_paths: dict[str, dict[str, Any]] = {}
        for c_value, validation_prediction in fit.get("validation_predictions", {}).items():
            c_path = artifact_dir / f"{stem}_validation_prediction_C{c_value.replace('.', 'p')}.npy"
            np.save(c_path, np.asarray(validation_prediction, dtype=np.float64), allow_pickle=False)
            validation_prediction_paths[c_value] = {
                "path": str(c_path.relative_to(ROOT)),
                "sha256": _sha(c_path),
                "n": int(len(validation_prediction)),
            }
        artifact_entries[stem] = {
            "labels": str(labels_path.relative_to(ROOT)), "labels_sha256": _sha(labels_path),
            "prediction": str(prediction_path.relative_to(ROOT)), "prediction_sha256": _sha(prediction_path),
            "keys": str(keys_path.relative_to(ROOT)), "keys_sha256": _sha(keys_path),
            "train_validation_arrays": str(train_val_path.relative_to(ROOT)),
            "train_validation_arrays_sha256": _sha(train_val_path),
            "train_keys": str(train_keys_path.relative_to(ROOT)), "train_keys_sha256": _sha(train_keys_path),
            "validation_keys": str(val_keys_path.relative_to(ROOT)), "validation_keys_sha256": _sha(val_keys_path),
            "validation_labels": str(validation_labels_path.relative_to(ROOT)),
            "validation_labels_sha256": _sha(validation_labels_path),
            "test_features": str(test_features_path.relative_to(ROOT)), "test_features_sha256": _sha(test_features_path),
            "validation_prediction_paths": validation_prediction_paths,
            "coef": np.asarray(fit["model"].coef_, dtype=np.float64).tolist(),
            "intercept": np.asarray(fit["model"].intercept_, dtype=np.float64).tolist(),
            "coef_sha256": fit["coef_sha256"], "intercept_sha256": fit["intercept_sha256"],
            "scaler": fit["scaler"], "scaler_sha256": fit["scaler_sha256"],
            "selected_C": fit["selected_C"], "validation_candidates": fit["validation_candidates"],
            "train_row_key_sha256": fit["train_row_key_sha256"],
            "validation_row_key_sha256": fit["validation_row_key_sha256"],
            "test_row_key_sha256": fit["test_row_key_sha256"],
        }
        scenario_ap = _source_scenario_ap(fit, rows)
        test_results[arm] = {
            "ap": compute_arm_ap(fit, rows), "scenario_ap": scenario_ap.tolist(),
            "n": int(len(rows["y"])), "positives": int(np.sum(rows["y"])),
            "natural_prevalence": float(np.mean(rows["y"])),
            "labels_sha256": _sha(labels_path), "prediction_sha256": _sha(prediction_path),
            "row_key_sha256": row_key_hash(rows["keys"]),
        }
    return test_results, artifact_entries


def run(prelabel_commit: str, output_dir: Path) -> dict[str, Any]:
    output_dir = _canonical_output_dir(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    protected = {
        "g1_execution_manifest.json", "g1_probe_manifest.json", "g1_results.json",
        "g1_statistics.json", "g1_decision.md",
    }
    if any((output_dir / name).exists() for name in protected):
        raise ProtocolViolation(f"refusing to overwrite existing G1 artifacts: {output_dir}")
    ledger_path = output_dir / "g1_execution_ledger.jsonl"
    if ledger_path.exists():
        raise ProtocolViolation(f"refusing to reuse an existing execution ledger: {ledger_path}")
    _ledger_append(ledger_path, "process_start", prelabel_seal_commit=prelabel_commit, label_access_ack=True)
    require_prelabel_seal(prelabel_commit)
    require_duration_matching_resolution()
    require_supportive_analysis_kind("duration_severity_stratified_robustness")
    assert_fixed_robustness_strata("duration", DURATION_STRATA)
    assert_fixed_robustness_strata("severity", SEVERITY_STRATA)
    reject_stratum_refit("frozen_probe")
    reject_stratum_scaler_fit("train_only")
    assert_sealed_inputs()
    assert_source_fold_separation()
    assert_family_names(("H2", "H3a-A", "H3a-B", "H3a-C"))
    # F-v4 accepted backend must be configured in every fresh G1 process
    # before loading or executing either frozen backbone.
    import phase_f_v4_common as f4
    backend_environment = f4.configure()
    expected_backend = {
        "cudnn_deterministic": True,
        "cudnn_benchmark": False,
        "deterministic_algorithms": False,
        "matmul_precision": "highest",
        "matmul_allow_tf32": False,
        "cudnn_allow_tf32": False,
    }
    if any(backend_environment.get(key) != value for key, value in expected_backend.items()):
        raise ProtocolViolation(f"F-v4 backend state mismatch: {backend_environment}")
    entries = load_backbone_entries()
    candi = load_candi_controls()
    _ledger_append(ledger_path, "sealed_inputs_verified", checkpoint_count=10, candi_control_count=5)
    feature_arms = expected_feature_arms()
    # Keep source/scenario/condition loops explicit and deterministic.  Each
    # detector seed has one frozen backbone per architecture and one CANDI
    # history computed once per stream and reused by both arms.
    # Primary rows are written per stream to an immutable, hash-sealed cache.
    # This preserves pooled four-scenario fitting while preventing all five
    # detector seeds (and their duplicated arm arrays) from coexisting in RAM.
    primary_cache_dir = output_dir / "g1_primary_cache"
    if primary_cache_dir.exists():
        raise ProtocolViolation(f"refusing to reuse primary cache directory: {primary_cache_dir}")
    primary_cache_dir.mkdir(parents=True, exist_ok=False)
    primary_cache_refs: dict[int, dict[str, dict[str, list[dict[str, str]]]]] = {
        seed: {fold: {} for fold in ("train", "validation", "test")}
        for seed in DETECTOR_SEEDS
    }
    # Secondary reporting views are computed in a post-fit streaming pass.
    # Keeping their feature matrices in the primary extraction loop would
    # retain hundreds of gigabytes of boolean-indexed arrays (especially the
    # native-prevalence and stable-normal views).
    frozen_backbones: dict[int, dict[str, Any]] = {}
    frozen_candi: dict[int, tuple[Any, dict[str, Any]]] = {}
    execution_rows: list[dict[str, Any]] = []
    descriptive_rows: list[dict[str, Any]] = []
    for detector_seed in DETECTOR_SEEDS:
        _ledger_append(ledger_path, "detector_seed_start", detector_seed=int(detector_seed))
        candi_model, candi_row = candi[detector_seed]
        backbones = {
            architecture: __import__("phase_g1_pipeline")._load_backbone(entries[(detector_seed, architecture)])
            for architecture in ARCHITECTURES
        }
        frozen_backbones[int(detector_seed)] = backbones
        frozen_candi[int(detector_seed)] = (candi_model, candi_row)
        seed_primary_refs = primary_cache_refs[int(detector_seed)]
        for fold, sources in (("train", TRAIN_SOURCES), ("validation", VALIDATION_SOURCES), ("test", TEST_SOURCES)):
            for source in sources:
                scenario_conditions = [(scenario, condition) for scenario in SHIFTED_SCENARIOS for condition in SHIFTED_CONDITIONS]
                scenario_conditions.append(("stationary", "none"))
                for scenario, condition in scenario_conditions:
                        _ledger_append(ledger_path, "labelled_stream_start", detector_seed=int(detector_seed), fold=str(fold), source_seed=int(source), scenario=str(scenario), condition=str(condition))
                        stream = _generate(source, scenario, condition)
                        observations = np.asarray(stream.observations, dtype=np.float32).copy()
                        timestamps = np.arange(FIRST_COMMON_TIMESTAMP, len(observations), dtype=np.int64)
                        if len(timestamps) == 0:
                            raise ProtocolViolation("source stream has no common t>=63 decisions")
                        # The CANDI history is a single immutable value per
                        # detector/source/scenario/condition/timestamp.
                        candi_history = extract_candi_history(candi_model, candi_row, observations, timestamps)
                        per_architecture = {}
                        for architecture in ARCHITECTURES:
                            per_architecture[architecture] = _observation_then_label(
                                stream, detector_seed, architecture, backbones[architecture], candi_history
                            )
                        # Evaluator-only descriptive accounting is retained
                        # separately from the primary binary cohort.
                        truth_strata = np.asarray(per_architecture["xlstm"]["stratum"], dtype=object)
                        truth_labels = np.asarray(per_architecture["xlstm"]["label"], dtype=np.int8)
                        descriptive_rows.append({
                            "detector_seed": detector_seed, "source_seed": source,
                            "fold": fold, "scenario": scenario, "condition": condition,
                            "strata_counts": {str(name): int(np.sum(truth_strata == name)) for name in ("anomaly", "drift", "mixed", "stable_new_normal", "stationary_normal")},
                            "anomaly_prevalence": float(np.mean(truth_labels)),
                            "mixed_count": int(np.sum(truth_strata == "mixed")),
                            "event_type_counts": {str(name): int(np.sum(np.asarray(per_architecture["xlstm"]["event_type"], dtype=object) == name)) for name in ("spike", "collective", "dependency", "persistent_fault")},
                        })
                        if scenario in SHIFTED_SCENARIOS:
                            # Pair rows before adding them to any pooled arm.
                            # This prevents a differential NaN/warmup mask from
                            # changing a later AP cohort.
                            common_mask = primary_binary_mask(per_architecture["xlstm"], allow_empty=True)
                            for architecture in ARCHITECTURES:
                                for arm in feature_arms:
                                    values = np.asarray(per_architecture[architecture]["groups"][arm], dtype=np.float64)
                                    if values.shape[0] != len(common_mask):
                                        raise ProtocolViolation("feature rows differ across arms")
                                    common_mask &= np.isfinite(values).all(axis=1)
                            for arm in feature_arms:
                                x_rows = select_primary_rows(per_architecture["xlstm"], arm, common_mask)
                                l_rows = select_primary_rows(per_architecture["lstm"], arm, common_mask)
                                if len(x_rows["keys"]) == 0 or len(l_rows["keys"]) == 0:
                                    continue
                                assert_common_cohort({"xlstm": x_rows, "lstm": l_rows})
                                seed_primary_refs[fold].setdefault(f"{arm}_xlstm", []).append(
                                    _write_primary_chunk(
                                        primary_cache_dir,
                                        f"seed{detector_seed}_{fold}_{source}_{scenario}_{condition}_{arm}_xlstm",
                                        x_rows,
                                    )
                                )
                                seed_primary_refs[fold].setdefault(f"{arm}_lstm", []).append(
                                    _write_primary_chunk(
                                        primary_cache_dir,
                                        f"seed{detector_seed}_{fold}_{source}_{scenario}_{condition}_{arm}_lstm",
                                        l_rows,
                                    )
                                )
                        execution_rows.append({"seed": detector_seed, "source": source, "fold": fold, "scenario": scenario, "condition": condition, "row_count": len(timestamps), "candi_history_sha256": array_sha(candi_history), "labels_joined_after_extraction": True})
                        _ledger_append(ledger_path, "labelled_stream_complete", detector_seed=int(detector_seed), fold=str(fold), source_seed=int(source), scenario=str(scenario), condition=str(condition), row_count=int(len(timestamps)))
        _ledger_append(ledger_path, "detector_seed_complete", detector_seed=int(detector_seed))
    expected_dims = {
        "history14": 14, "hidden52": 52, "gate130": 130,
        "memory52": 52, "combined234": 234,
        "history_plus_combined248": 248, "candi_history14": 14,
        "candi_history_plus_combined248": 248,
    }
    artifact_dir = output_dir / "g1_artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=False)
    fits: dict[int, dict[str, dict[str, Any]]] = {}
    comparison_rows: dict[int, dict[str, dict[str, Any]]] = {}
    test_results: dict[str, Any] = {}
    # Write all primary numeric artifacts while the train/validation/test
    # matrices are still available.  Secondary views are regenerated in a
    # bounded post-fit streaming pass below and never accumulate here.
    probe_manifest = {
        "fits": _clean(fits),
        "row_key_sha256": {},
        "artifacts": {},
        "primary_cache": {
            "directory": str(primary_cache_dir.relative_to(ROOT)),
            "resource_contract": "one stream chunk persisted; one detector seed pooled at a time",
            "chunk_count": int(sum(
                len(refs)
                for seed_refs in primary_cache_refs.values()
                for fold_refs in seed_refs.values()
                for refs in fold_refs.values()
            )),
        },
    }
    shared_control_artifacts: dict[str, Any] = {}
    for seed in DETECTOR_SEEDS:
        pooled_seed: dict[str, dict[str, Any]] = {"train": {}, "validation": {}, "test": {}}
        for fold in ("train", "validation", "test"):
            for arm, refs in primary_cache_refs[int(seed)][fold].items():
                if not refs:
                    raise ProtocolViolation(f"empty primary cache arm: {seed}/{fold}/{arm}")
                pooled_seed[fold][arm] = _concat([_load_primary_chunk(ref) for ref in refs])
        for architecture in ARCHITECTURES:
            _assert_paired_arms({
                arm.removesuffix(f"_{architecture}"): pooled_seed["test"][arm]
                for arm in pooled_seed["test"] if arm.endswith(f"_{architecture}")
            })
        for arm in feature_arms:
            assert_common_cohort({
                "xlstm": pooled_seed["test"][f"{arm}_xlstm"],
                "lstm": pooled_seed["test"][f"{arm}_lstm"],
            })
            if arm == "candi_history14":
                left = pooled_seed["test"][f"{arm}_xlstm"]
                right = pooled_seed["test"][f"{arm}_lstm"]
                assert_shared_control(left["X"], right["X"], left["keys"], right["keys"])
                x_path = artifact_dir / f"seed{seed}_candi_history_x.npy"
                l_path = artifact_dir / f"seed{seed}_candi_history_l.npy"
                np.save(x_path, np.asarray(left["X"], dtype=np.float64), allow_pickle=False)
                np.save(l_path, np.asarray(right["X"], dtype=np.float64), allow_pickle=False)
                shared_control_artifacts[str(seed)] = {
                    "x_path": str(x_path.relative_to(ROOT)), "x_sha256": _sha(x_path),
                    "l_path": str(l_path.relative_to(ROOT)), "l_sha256": _sha(l_path),
                    "row_key_sha256": row_key_hash(left["keys"]), "shape": list(left["X"].shape),
                }
            elif arm == "candi_history_plus_combined248":
                left = pooled_seed["test"][f"{arm}_xlstm"]
                right = pooled_seed["test"][f"{arm}_lstm"]
                assert_shared_control(left["X"][:, :14], right["X"][:, :14], left["keys"], right["keys"])
        seed_fits: dict[str, dict[str, Any]] = {}
        for arm in pooled_seed["train"]:
            suffix = "_xlstm" if arm.endswith("_xlstm") else "_lstm"
            base_arm = arm.removesuffix(suffix)
            seed_fits[arm] = fit_probe_pooled(
                probe_split_from_rows(pooled_seed["train"][arm]),
                probe_split_from_rows(pooled_seed["validation"][arm]),
                probe_split_from_rows(pooled_seed["test"][arm]),
                arm,
                seed,
                expected_dims[base_arm],
            )
        fits[int(seed)] = seed_fits
        comparison_rows[int(seed)] = {
            arm: _light_primary_rows(rows) for arm, rows in pooled_seed["test"].items()
        }
        probe_manifest["row_key_sha256"][str(seed)] = {
            arm: row_key_hash(value["keys"]) for arm, value in comparison_rows[int(seed)].items()
        }
        seed_results, seed_artifacts = _write_primary_probe_artifacts(
            int(seed), seed_fits, pooled_seed["train"], pooled_seed["validation"], pooled_seed["test"], artifact_dir
        )
        test_results[str(seed)] = seed_results
        probe_manifest["artifacts"].update(seed_artifacts)
        del pooled_seed, seed_fits
    probe_manifest["shared_control_artifacts"] = shared_control_artifacts
    probe_manifest["fits"] = _clean(fits)
    comparison_fits = fits
    del primary_cache_refs

    # Confirmatory effects use pooled four-scenario AP per source.  The
    # scenario-wise tensor is retained only for reproducibility diagnostics.
    pooled_ap = _pooled_source_ap(comparison_fits, comparison_rows)
    deltas = _difference_table(comparison_fits, comparison_rows)
    scenario_deltas = _scenario_difference_table(comparison_fits, comparison_rows)
    statistics = build_confirmatory_statistics(deltas)
    _ledger_append(ledger_path, "probe_statistics_complete", confirmatory_family_size=4)
    for name, delta in deltas.items():
        delta_path = artifact_dir / f"delta_{name}.npy"
        np.save(delta_path, np.asarray(delta, dtype=np.float64), allow_pickle=False)
        probe_manifest.setdefault("delta_artifacts", {})[name] = {
            "path": str(delta_path.relative_to(ROOT)), "sha256": _sha(delta_path), "shape": list(delta.shape)
        }

    secondary = _secondary_streaming_pass(
        fits,
        frozen_backbones,
        frozen_candi,
        feature_arms,
        output_dir,
        artifact_dir,
    )
    specificity = secondary["specificity"]
    descriptive_test = secondary["descriptive_test"]
    natural_prevalence = secondary["natural_prevalence"]
    semantic_report = secondary["semantic_report"]
    semantic_control_checks = secondary["semantic_control_checks"]
    robustness_report = secondary["robustness_report"]
    probe_manifest["semantic_control"] = semantic_report
    probe_manifest["semantic_control_checks"] = semantic_control_checks
    probe_manifest["semantic_control_artifacts"] = secondary["semantic_artifacts"]
    probe_manifest["robustness_artifacts"] = secondary["robustness_artifacts"]
    probe_manifest["secondary_cache"] = {
        "directory": secondary["secondary_cache_dir"],
        "file_count": secondary["secondary_cache_file_count"],
        "resource_contract": "one source/scenario/condition feature chunk at a time",
    }
    _write_json(output_dir / "g1_execution_manifest.json", {"status": "LABELLED_EXECUTION_COMPLETE", "prelabel_seal_commit": prelabel_commit, "execution_commit": current_commit(), "code_sha256": _sha_bytes(Path(__file__).read_bytes()), "scientific_file_sha256": scientific_file_sha256(), "backend_environment": backend_environment, "rows": execution_rows, "feature_arms": feature_arms, "folds": G1_CONFIG["folds"], "shifted_scenarios": list(SHIFTED_SCENARIOS), "conditions": list(CONDITIONS), "labels_joined_after_observation_extraction": True, "optimizer_steps": False, "test_result_metrics_computed": True, "duration_severity_protocol_status": G1_CONFIG.get("duration_severity_matching", {}).get("status"), "execution_ledger": str(ledger_path.relative_to(ROOT)), "execution_ledger_sha256": _sha(ledger_path), "execution_ledger_contract": "metadata-only process/progress/exception ledger; no labels, predictions, features or metrics"})
    _write_json(output_dir / "g1_probe_manifest.json", probe_manifest)
    _write_json(output_dir / "g1_statistics.json", _clean(statistics))
    scenario_statistics = {name: {"shape": list(value.shape), "sha256": array_sha(value), "values": value.tolist()} for name, value in scenario_deltas.items()}
    _write_json(output_dir / "g1_results.json", {"test_ap": test_results, "specificity": specificity, "descriptive_strata": descriptive_rows, "descriptive_test_strata": descriptive_test, "natural_prevalence_evaluation": natural_prevalence, "pooled_source_ap": {arm: values.tolist() for arm, values in pooled_ap.items()}, "pooled_source_ap_mean": {arm: float(np.mean(values)) for arm, values in pooled_ap.items()}, "scenario_deltas": scenario_statistics, "duration_severity_robustness": robustness_report, "semantic_nonidentifiability_control": semantic_report, "semantic_control_checks": semantic_control_checks, "delta_sha256": {name: array_sha(value) for name, value in deltas.items()}, "delta_shape": {name: list(value.shape) for name, value in deltas.items()}, "test_sources": list(TEST_SOURCES), "scenarios": list(SHIFTED_SCENARIOS), "conditions": list(CONDITIONS), "primary_cohort_prevalence": {str(seed): {arm: float(test_results[str(seed)][arm]["positives"] / test_results[str(seed)][arm]["n"]) for arm in test_results[str(seed)]} for seed in DETECTOR_SEEDS}})
    from phase_g1_core import h2_go, h3a_go, positive_seed_scenario_counts, positive_seed_source_counts
    h2_raw = statistics["comparisons"]["h2"]
    h2_seed_count = positive_seed_source_counts(deltas["h2"])
    h2_scenario_count = positive_seed_scenario_counts(scenario_deltas["h2"])[1]
    h2_robustness_support = robustness_report.get("h2_status") == "PASS"
    h3a_robustness_support = robustness_report.get("h3a_status_if_primary_h2_go") == "PASS"
    h2_status = "GO" if h2_go(h2_raw["mean"], h2_raw["ci95"][0], h2_raw["holm_adjusted_p"], h2_seed_count, h2_scenario_count, h2_robustness_support) else "STOP"
    h3a_counts = {name: {"positive_detector_seeds": positive_seed_source_counts(deltas[name]), "positive_scenarios": positive_seed_scenario_counts(scenario_deltas[name])[1]} for name in ("h3a_a", "h3a_b", "h3a_c")}
    h3_repro = all(row["positive_detector_seeds"] >= 4 and row["positive_scenarios"] >= 3 for row in h3a_counts.values())
    h3a_status = "NOT_ELIGIBLE"
    if h2_status == "GO":
        a, b, c = (statistics["comparisons"][name] for name in ("h3a_a", "h3a_b", "h3a_c"))
        h3a_status = "GO" if h3a_go(True, a["mean"], a["ci95"][0], a["holm_adjusted_p"], b["mean"], b["ci95"][0], b["holm_adjusted_p"], c["mean"], c["ci95"][0], c["holm_adjusted_p"], h3_repro, h3a_robustness_support) else "STOP"
    decision = {"H2": h2_status, "H3a": h3a_status, "H3b": "UNLOCKED" if h3a_status == "GO" else "LOCKED", "h1_controlled_harm": "STOP", "h1_natural_harm": "NOT_RUN", "h1_harm_overall": "UNRESOLVED", "duration_severity_robustness": robustness_report, "semantic_nonidentifiability_control": semantic_report, "h2_positive_detector_seeds": h2_seed_count, "h2_positive_scenarios": h2_scenario_count, "h3a_reproducibility": h3a_counts, "h3a_reproducibility_pass": h3_repro, "h2_robustness_support_used": h2_robustness_support, "h3a_robustness_support_used": h3a_robustness_support}
    _write_json(output_dir / "g1_decision.json", decision)
    (output_dir / "g1_decision.md").write_text("# Phase G1 decision\n\n" + "\n".join(f"{key} = {value}" for key, value in (("H2", h2_status), ("H3a", h3a_status), ("H3b", decision["H3b"]))) + "\n\nH1_controlled_harm = STOP\nH1_natural_harm = NOT_RUN\nH1_harm_overall = UNRESOLVED\n\nDuration/severity robustness: " + str(robustness_report) + "\n\nSemantic non-identifiability control: " + str(semantic_report) + "\n")
    _ledger_append(ledger_path, "process_complete", h2=str(h2_status), h3a=str(h3a_status), h3b=str(decision["H3b"]))
    # The terminal ledger record is part of the immutable execution manifest;
    # seal its final hash only after the complete decision and all artifacts
    # have been written.
    execution_manifest_path = output_dir / "g1_execution_manifest.json"
    execution_manifest = _json(execution_manifest_path)
    execution_manifest["execution_ledger_sha256"] = _sha(ledger_path)
    _write_json(execution_manifest_path, execution_manifest)
    return {"status": "PASS", "output_dir": str(output_dir), "statistics": statistics, "decision": decision}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prelabel-seal", required=True)
    parser.add_argument("--label-access", action="store_true", required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports" / "phase_g")
    args = parser.parse_args()
    if not args.label_access:
        raise SystemExit("FAIL_CLOSED: --label-access is required")
    try:
        result = run(args.prelabel_seal, args.output_dir)
    except Exception as exc:
        ledger_path = args.output_dir / "g1_execution_ledger.jsonl"
        if ledger_path.exists():
            _ledger_append(ledger_path, "process_exception", exception_type=type(exc).__name__, exception=str(exc))
        raise SystemExit(f"FAIL_CLOSED: {exc}") from exc
    print(json.dumps({"status": result["status"], "output_dir": result["output_dir"]}, indent=2))


if __name__ == "__main__":
    main()
