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
    assert_family_names,
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


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


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
    timestamps = np.arange(FIRST_COMMON_TIMESTAMP, len(observations), dtype=np.int64)
    if len(timestamps) == 0:
        raise ProtocolViolation("source stream has no common t>=63 decisions")
    scaler = _phase_f_scaler(int(stream.source_seed))
    extracted_backbone = extract_backbone_rows(
        backbone, architecture, observations, scaler, timestamps
    )
    groups = build_feature_groups(extracted_backbone["scores"], extracted_backbone["internal_base"])
    if candi_history.shape != groups["history14"].shape:
        raise ProtocolViolation("shared CANDI history shape mismatch")
    groups["candi_history14"] = np.asarray(candi_history, dtype=np.float64).copy()
    groups["candi_history_plus_combined248"] = np.concatenate(
        (groups["candi_history14"], groups["combined234"]), axis=1
    )
    extracted = {"timestamps": timestamps, "groups": groups, "scores": extracted_backbone["scores"]}
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


def _duration_matched_rows(
    joined: Mapping[str, Any],
    legitimate_truth: Mapping[str, Any],
    feature_arm: str,
    valid_mask: Sequence[bool] | None = None,
) -> dict[str, Any]:
    """Build the preregistered semantic duration/severity stress cohort.

    The frozen generator supplies an observation-identical ``semantic=legitimate``
    counterpart for every injected event.  We pair each pure anomaly window
    with its same timestamp/event/duration/severity legitimate counterpart.
    This diagnostic is evaluator-side only, never enters probe fitting, and is
    deliberately allowed to be non-identifiable (AP ties are a valid result).
    Persistent-fault stress events and mixed windows are excluded.
    """
    anomaly_stratum = np.asarray(joined["stratum"], dtype=object)
    event = np.asarray(joined["event"], dtype=np.int32)
    event_type = np.asarray(joined["event_type"], dtype=object)
    duration = np.asarray(joined["duration"], dtype=object)
    severity = np.asarray(joined["severity"], dtype=object)
    legit_label = np.asarray(legitimate_truth["label"], dtype=np.int8)
    legit_event = np.asarray(legitimate_truth["event"], dtype=np.int32)
    legit_duration = np.asarray(legitimate_truth["duration"], dtype=object)
    legit_severity = np.asarray(legitimate_truth["severity"], dtype=object)
    if len(legit_label) != len(event):
        raise ProtocolViolation("legitimate counterpart truth length differs")
    keep = (anomaly_stratum == "anomaly") & (event >= 0) & (event_type != "persistent_fault")
    keep &= np.asarray([value is not None for value in duration], dtype=bool)
    keep &= np.asarray([value is not None for value in severity], dtype=bool)
    keep &= legit_label == 0
    keep &= legit_event == event
    keep &= np.asarray([a == b for a, b in zip(duration, legit_duration)], dtype=bool)
    keep &= np.asarray([a == b for a, b in zip(severity, legit_severity)], dtype=bool)
    if valid_mask is not None:
        supplied = np.asarray(valid_mask, dtype=bool)
        if supplied.shape != keep.shape:
            raise ProtocolViolation("matched cohort mask shape mismatch")
        keep &= supplied
    features = np.asarray(joined["groups"][feature_arm], dtype=np.float64)
    keep &= np.isfinite(features).all(axis=1)
    indices = np.flatnonzero(keep)
    # Place all positive rows first and their exact legitimate counterparts
    # second; semantic is a diagnostic-only key extension so keys remain unique.
    X_one = features[indices]
    X = np.concatenate((X_one, X_one), axis=0)
    y = np.concatenate((np.ones(len(indices), dtype=np.int8), np.zeros(len(indices), dtype=np.int8)))
    base_keys = [dict(joined["keys"][int(index)]) for index in indices]
    keys = [dict(key, semantic="anomaly") for key in base_keys] + [dict(key, semantic="legitimate") for key in base_keys]
    source = np.asarray(joined["source_seed"], dtype=np.int64)[indices]
    scenarios = tuple(np.asarray(joined["scenario"], dtype=object)[indices].tolist())
    events = tuple(event[indices].tolist())
    event_types = tuple(event_type[indices].tolist())
    return {
        "X": X,
        "y": y,
        "keys": keys,
        "source_seeds": np.concatenate((source, source)),
        "scenarios": scenarios + scenarios,
        "events": events + events,
        "event_types": event_types + event_types,
        "duration": np.concatenate((duration[indices], duration[indices])),
        "severity": np.concatenate((severity[indices], severity[indices])),
    }


def _matched_effect_table(
    fits: Mapping[int, Mapping[str, Mapping[str, Any]]],
    matched_rows: Mapping[int, Mapping[str, Mapping[str, Mapping[str, list[Mapping[str, Any]]]]]],
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, Any]]:
    """Compute matched AP effects and evaluator support before decision logic."""
    from sklearn.metrics import average_precision_score

    primary: dict[str, np.ndarray] = {}
    scenario: dict[str, np.ndarray] = {}
    support_bins: dict[str, Any] = {}
    arm_names = ("history14", "history_plus_combined248", "combined234", "candi_history14", "candi_history_plus_combined248")
    ap_primary: dict[str, np.ndarray] = {}
    ap_scenario: dict[str, np.ndarray] = {}
    for architecture in ARCHITECTURES:
        for base_arm in arm_names:
            name = f"{base_arm}_{architecture}"
            matrix = np.full((len(TEST_SOURCES), len(DETECTOR_SEEDS)), np.nan)
            smatrix = np.full((len(TEST_SOURCES), len(DETECTOR_SEEDS), len(SHIFTED_SCENARIOS)), np.nan)
            for seed_index, seed in enumerate(DETECTOR_SEEDS):
                parts = [part for part in matched_rows[seed][architecture][base_arm] if len(part["keys"]) > 0]
                if not parts:
                    continue
                rows = _concat(parts)
                fit = fits[seed][name]
                prediction = fit["model"].predict_proba(apply_scaler(rows["X"], fit["scaler"]))[:, 1]
                source = np.asarray(rows["source_seeds"], dtype=np.int64)
                labels = np.asarray(rows["y"], dtype=np.int8)
                scenarios = np.asarray(rows["scenarios"], dtype=object)
                for source_index, source_seed in enumerate(TEST_SOURCES):
                    mask = source == source_seed
                    if mask.sum() and len(np.unique(labels[mask])) == 2:
                        matrix[source_index, seed_index] = average_precision_score(labels[mask], prediction[mask])
                    for scenario_index, scenario_name in enumerate(SHIFTED_SCENARIOS):
                        smask = mask & (scenarios == scenario_name)
                        if smask.sum() and len(np.unique(labels[smask])) == 2:
                            smatrix[source_index, seed_index, scenario_index] = average_precision_score(labels[smask], prediction[smask])
            ap_primary[name] = matrix
            ap_scenario[name] = smatrix
    def g(name: str) -> np.ndarray:
        value = ap_primary[name]
        if not np.isfinite(value).all():
            raise ProtocolViolation(f"duration/severity matched cohort lacks source/class support for {name}")
        return value
    def gs(name: str) -> np.ndarray:
        value = ap_scenario[name]
        # Scenario support can be sparse for a fixed event type; retain NaN in
        # the diagnostic and evaluate only supported cells below.
        return value
    primary = {
        "h2": g("history_plus_combined248_xlstm") - g("history14_xlstm"),
        "h3a_a": g("combined234_xlstm") - g("combined234_lstm"),
        "h3a_b": (g("history_plus_combined248_xlstm") - g("history14_xlstm")) - (g("history_plus_combined248_lstm") - g("history14_lstm")),
        "h3a_c": (g("candi_history_plus_combined248_xlstm") - g("candi_history14_xlstm")) - (g("candi_history_plus_combined248_lstm") - g("candi_history14_lstm")),
    }
    scenario = {
        "h2": gs("history_plus_combined248_xlstm") - gs("history14_xlstm"),
        "h3a_a": gs("combined234_xlstm") - gs("combined234_lstm"),
        "h3a_b": (gs("history_plus_combined248_xlstm") - gs("history14_xlstm")) - (gs("history_plus_combined248_lstm") - gs("history14_lstm")),
        "h3a_c": (gs("candi_history_plus_combined248_xlstm") - gs("candi_history14_xlstm")) - (gs("candi_history_plus_combined248_lstm") - gs("candi_history14_lstm")),
    }
    matched_summaries: dict[str, Any] = {}
    for name, value in primary.items():
        finite = bool(np.isfinite(value).all())
        summary = hierarchical_bootstrap(value, draws=10_000, seed=901) if finite else None
        p_value = source_cluster_sign_flip(value) if finite else None
        seed_count = int((value.mean(axis=0) > 0).sum()) if finite else 0
        scenario_value = scenario[name]
        scenario_count = int((np.nanmean(scenario_value, axis=(0, 1)) > 0).sum()) if np.isfinite(scenario_value).any() else 0
        matched_summaries[name] = {
            "effect": summary,
            "raw_p": p_value,
            "positive_detector_seeds": seed_count,
            "positive_shifted_scenarios": scenario_count,
            "support_available": finite and bool(np.isfinite(scenario_value).any()),
            "supportive_if_resolved": bool(
                summary is not None
                and summary["mean"] >= 0.02
                and summary["ci95"][0] > 0
                and seed_count >= 4
                and scenario_count >= 3
            ),
        }
    h2_matched_bootstrap = matched_summaries["h2"]["effect"]
    h2_matched_scenario = scenario["h2"]
    matched_seed_count = matched_summaries["h2"]["positive_detector_seeds"]
    matched_scenario_count = matched_summaries["h2"]["positive_shifted_scenarios"]
    # This is the frozen identical-observation/opposite-semantic control, not
    # the duration/severity-matched supportive analysis required by the H2
    # gate.  Its protocol role is explicitly non-identifiability diagnostics;
    # it must never be promoted to a supportive PASS merely because rows are
    # available.  A future protocol amendment must define the separate
    # legitimate-excursion matching estimand before H2 label access.
    control_gate_pass = bool(
        h2_matched_bootstrap is not None
        and h2_matched_bootstrap["mean"] >= 0.02
        and h2_matched_bootstrap["ci95"][0] > 0
        and matched_seed_count >= 4
        and matched_scenario_count >= 3
    )
    support_bins["status"] = "UNRESOLVED_PROTOCOL"
    support_bins["protocol_status"] = "UNRESOLVED_PROTOCOL"
    support_bins["control_gate_pass_if_misused"] = control_gate_pass
    support_bins["summaries"] = matched_summaries
    support_bins["supportive_h2_if_resolved"] = matched_summaries["h2"]["supportive_if_resolved"]
    support_bins["supportive_h3a_if_resolved"] = all(
        matched_summaries[name]["supportive_if_resolved"] for name in ("h3a_a", "h3a_b", "h3a_c")
    )
    support_bins["analysis_kind"] = "identical_observation_opposite_semantic_non_identifiability_control"
    support_bins["definition"] = "same source/scenario/condition/event/timestamp, pure anomaly versus observation-identical legitimate counterpart; persistent_fault and mixed excluded"
    support_bins["reason"] = "frozen generator's opposite-semantic control is not a supportive duration/severity-matched estimand; external protocol resolution required"
    support_bins["rows"] = int(sum(len(part["keys"]) for seed in DETECTOR_SEEDS for architecture in ARCHITECTURES for part in matched_rows[seed][architecture]["history14"]))
    support_bins["h2_effect"] = h2_matched_bootstrap
    support_bins["h2_positive_detector_seeds"] = matched_seed_count
    support_bins["h2_positive_scenarios"] = matched_scenario_count
    support_bins["primary_effects"] = {name: {"mean": float(np.nanmean(value)), "positive_detector_seeds": int((np.nanmean(value, axis=0) > 0).sum())} for name, value in primary.items()}
    return primary, scenario, support_bins


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


def _duration_severity_support(rows: Mapping[str, Any]) -> dict[str, Any]:
    """Report support without post-outcome bin merging or redefinition."""
    duration = np.asarray(rows["duration"], dtype=object)
    severity = np.asarray(rows["severity"], dtype=object)
    labels = np.asarray(rows["y"], dtype=np.int8)
    groups: dict[str, set[int]] = {}
    for d, s, y in zip(duration, severity, labels):
        if d is None or s is None:
            continue
        groups.setdefault(f"{d}:{s}", set()).add(int(y))
    supported = sorted(key for key, values in groups.items() if values == {0, 1})
    return {"status": "PASS" if supported else "N/A", "supported_strata": supported, "group_count": len(groups)}


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


def run(prelabel_commit: str, output_dir: Path) -> dict[str, Any]:
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
    raw_rows: dict[int, dict[str, dict[str, list[dict[str, Any]]]]] = {
        seed: {fold: {} for fold in ("train", "validation", "test")}
        for seed in DETECTOR_SEEDS
    }
    specificity_rows: dict[int, dict[str, dict[str, dict[str, list[dict[str, Any]]]]]] = {
        seed: {architecture: {category: {arm: [] for arm in feature_arms} for category in ("stable_new_normal", "stationary_normal")}
               for architecture in ARCHITECTURES}
        for seed in DETECTOR_SEEDS
    }
    descriptive_test_rows: dict[int, dict[str, dict[str, dict[str, list[dict[str, Any]]]]]] = {
        seed: {
            architecture: {
                stratum: {arm: [] for arm in feature_arms}
                for stratum in ("mixed", "spike", "collective", "dependency")
            }
            for architecture in ARCHITECTURES
        }
        for seed in DETECTOR_SEEDS
    }
    natural_test_rows: dict[int, dict[str, dict[str, list[dict[str, Any]]]]] = {
        seed: {architecture: {arm: [] for arm in feature_arms} for architecture in ARCHITECTURES}
        for seed in DETECTOR_SEEDS
    }
    matched_rows: dict[int, dict[str, dict[str, list[dict[str, Any]]]]] = {
        seed: {architecture: {arm: [] for arm in feature_arms} for architecture in ARCHITECTURES}
        for seed in DETECTOR_SEEDS
    }
    execution_rows: list[dict[str, Any]] = []
    descriptive_rows: list[dict[str, Any]] = []
    for detector_seed in DETECTOR_SEEDS:
        _ledger_append(ledger_path, "detector_seed_start", detector_seed=int(detector_seed))
        candi_model, candi_row = candi[detector_seed]
        backbones = {
            architecture: __import__("phase_g1_pipeline")._load_backbone(entries[(detector_seed, architecture)])
            for architecture in ARCHITECTURES
        }
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
                        if fold == "test":
                            for architecture in ARCHITECTURES:
                                for arm in feature_arms:
                                    natural_test_rows[detector_seed][architecture][arm].append(
                                        _select_all_rows(per_architecture[architecture], arm)
                                    )
                        if scenario in SHIFTED_SCENARIOS:
                            # The duration/severity-matched diagnostic uses
                            # the generator's fixed semantic counterpart.  It
                            # is generated before any probe fitting and is
                            # never part of the primary binary cohort.
                            legitimate_stream = _generate(source, scenario, condition, "legitimate") if fold == "test" else None
                            legitimate_truth = None
                            if legitimate_stream is not None:
                                if not np.array_equal(observations, np.asarray(legitimate_stream.observations, dtype=np.float32)):
                                    raise ProtocolViolation("semantic legitimate counterpart changed observations")
                                legitimate_truth = build_evaluator_rows(legitimate_stream, timestamps, 64)
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
                                raw_rows[detector_seed][fold].setdefault(f"{arm}_xlstm", []).append(x_rows)
                                raw_rows[detector_seed][fold].setdefault(f"{arm}_lstm", []).append(l_rows)
                            for architecture in ARCHITECTURES:
                                for arm in feature_arms:
                                    specificity_rows[detector_seed][architecture]["stable_new_normal"][arm].append(
                                        _select_category_rows(per_architecture[architecture], arm, ("stable_new_normal",))
                                    )
                                    if fold == "test":
                                        descriptive_test_rows[detector_seed][architecture]["mixed"][arm].append(
                                            _select_category_rows(per_architecture[architecture], arm, ("mixed",))
                                        )
                                        for event_type in ("spike", "collective", "dependency"):
                                            descriptive_test_rows[detector_seed][architecture][event_type][arm].append(
                                                _select_event_type_rows(per_architecture[architecture], arm, event_type)
                                            )
                                    if legitimate_truth is not None:
                                        matched_valid = np.asarray(per_architecture[architecture]["stratum"] == "anomaly", dtype=bool)
                                        for other_architecture in ARCHITECTURES:
                                            for other_arm in feature_arms:
                                                matched_values = np.asarray(per_architecture[other_architecture]["groups"][other_arm], dtype=np.float64)
                                                matched_valid &= np.isfinite(matched_values).all(axis=1)
                                        matched_rows[detector_seed][architecture][arm].append(
                                            _duration_matched_rows(per_architecture[architecture], legitimate_truth, arm, matched_valid)
                                        )
                        else:
                            for architecture in ARCHITECTURES:
                                for arm in feature_arms:
                                    specificity_rows[detector_seed][architecture]["stationary_normal"][arm].append(
                                        _select_category_rows(per_architecture[architecture], arm, ("stationary_normal",))
                                    )
                        execution_rows.append({"seed": detector_seed, "source": source, "fold": fold, "scenario": scenario, "condition": condition, "row_count": len(timestamps), "candi_history_sha256": array_sha(candi_history), "labels_joined_after_extraction": True})
                        _ledger_append(ledger_path, "labelled_stream_complete", detector_seed=int(detector_seed), fold=str(fold), source_seed=int(source), scenario=str(scenario), condition=str(condition), row_count=int(len(timestamps)))
        _ledger_append(ledger_path, "detector_seed_complete", detector_seed=int(detector_seed))
    pooled: dict[str, dict[int, dict[str, Any]]] = {"train": {}, "validation": {}, "test": {}}
    for seed in DETECTOR_SEEDS:
        pooled["train"][seed] = {arm: _concat(parts) for arm, parts in raw_rows[seed]["train"].items()}
        pooled["validation"][seed] = {arm: _concat(parts) for arm, parts in raw_rows[seed]["validation"].items()}
        pooled["test"][seed] = {arm: _concat(parts) for arm, parts in raw_rows[seed]["test"].items()}
        for architecture in ARCHITECTURES:
            _assert_paired_arms({arm.removesuffix(f"_{architecture}"): pooled["test"][seed][arm] for arm in pooled["test"][seed] if arm.endswith(f"_{architecture}")})
        for arm in feature_arms:
            assert_common_cohort({"xlstm": pooled["test"][seed][f"{arm}_xlstm"], "lstm": pooled["test"][seed][f"{arm}_lstm"]})
            if arm == "candi_history14":
                left = pooled["test"][seed][f"{arm}_xlstm"]
                right = pooled["test"][seed][f"{arm}_lstm"]
                assert_shared_control(left["X"], right["X"], left["keys"], right["keys"])
            elif arm == "candi_history_plus_combined248":
                # Only columns 0:14 are the shared CANDI control; trailing
                # internal summaries are intentionally backbone-specific.
                left = pooled["test"][seed][f"{arm}_xlstm"]
                right = pooled["test"][seed][f"{arm}_lstm"]
                assert_shared_control(left["X"][:, :14], right["X"][:, :14], left["keys"], right["keys"])
    fits: dict[int, dict[str, dict[str, Any]]] = {}
    expected_dims = {
        "history14": 14, "hidden52": 52, "gate130": 130,
        "memory52": 52, "combined234": 234,
        "history_plus_combined248": 248, "candi_history14": 14,
        "candi_history_plus_combined248": 248,
    }
    for seed in DETECTOR_SEEDS:
        fits[seed] = {}
        for arm in pooled["train"][seed]:
            suffix = "_xlstm" if arm.endswith("_xlstm") else "_lstm"
            base_arm = arm.removesuffix(suffix)
            fits[seed][arm] = fit_probe_pooled(
                probe_split_from_rows(pooled["train"][seed][arm]),
                probe_split_from_rows(pooled["validation"][seed][arm]),
                probe_split_from_rows(pooled["test"][seed][arm]),
                arm,
                seed,
                expected_dims[base_arm],
            )
    comparison_fits = fits
    comparison_rows = pooled["test"]
    # Confirmatory effects use pooled four-scenario AP per source.  The
    # scenario-wise tensor is retained only for reproducibility diagnostics.
    deltas = _difference_table(comparison_fits, comparison_rows)
    scenario_deltas = _scenario_difference_table(comparison_fits, comparison_rows)
    statistics = build_confirmatory_statistics(deltas)
    _ledger_append(ledger_path, "probe_statistics_complete", confirmatory_family_size=4)
    matched_deltas, matched_scenario_deltas, matched_report = _matched_effect_table(fits, matched_rows)
    pooled_ap = _pooled_source_ap(fits, comparison_rows)
    specificity = _specificity_summary(fits, specificity_rows)
    descriptive_test = _descriptive_strata_summary(fits, descriptive_test_rows)
    natural_prevalence = _natural_prevalence_summary(fits, natural_test_rows)
    artifact_dir = output_dir / "g1_artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=False)
    probe_manifest = {"fits": _clean(fits), "row_key_sha256": {str(seed): {arm: row_key_hash(value["keys"]) for arm, value in comparison_rows[seed].items()} for seed in DETECTOR_SEEDS}, "artifacts": {}}
    shared_control_artifacts: dict[str, Any] = {}
    for seed in DETECTOR_SEEDS:
        x_control = comparison_rows[seed]["candi_history14_xlstm"]
        l_control = comparison_rows[seed]["candi_history14_lstm"]
        x_path = artifact_dir / f"seed{seed}_candi_history_x.npy"
        l_path = artifact_dir / f"seed{seed}_candi_history_l.npy"
        np.save(x_path, np.asarray(x_control["X"], dtype=np.float64), allow_pickle=False)
        np.save(l_path, np.asarray(l_control["X"], dtype=np.float64), allow_pickle=False)
        shared_control_artifacts[str(seed)] = {
            "x_path": str(x_path.relative_to(ROOT)), "x_sha256": _sha(x_path),
            "l_path": str(l_path.relative_to(ROOT)), "l_sha256": _sha(l_path),
            "row_key_sha256": row_key_hash(x_control["keys"]),
            "shape": list(x_control["X"].shape),
        }
    probe_manifest["shared_control_artifacts"] = shared_control_artifacts
    for name, delta in deltas.items():
        delta_path = artifact_dir / f"delta_{name}.npy"
        np.save(delta_path, np.asarray(delta, dtype=np.float64), allow_pickle=False)
        probe_manifest.setdefault("delta_artifacts", {})[name] = {"path": str(delta_path.relative_to(ROOT)), "sha256": _sha(delta_path), "shape": list(delta.shape)}
    probe_manifest["matched_artifacts"] = {}
    for seed in DETECTOR_SEEDS:
        for architecture in ARCHITECTURES:
            for arm in feature_arms:
                parts = [part for part in matched_rows[seed][architecture][arm] if len(part["keys"]) > 0]
                if not parts:
                    probe_manifest["matched_artifacts"][f"seed{seed}_{arm}_{architecture}"] = {"status": "N/A"}
                    continue
                match = _concat(parts)
                fit = fits[seed][f"{arm}_{architecture}"]
                prediction = fit["model"].predict_proba(apply_scaler(match["X"], fit["scaler"]))[:, 1]
                stem = f"seed{seed}_{arm}_{architecture}"
                labels_path = artifact_dir / f"matched_{stem}_labels.npy"
                prediction_path = artifact_dir / f"matched_{stem}_prediction.npy"
                keys_path = artifact_dir / f"matched_{stem}_keys.json"
                np.save(labels_path, np.asarray(match["y"], dtype=np.int8), allow_pickle=False)
                np.save(prediction_path, np.asarray(prediction, dtype=np.float64), allow_pickle=False)
                keys_path.write_text(json.dumps(match["keys"], sort_keys=True, separators=(",", ":")) + "\n")
                probe_manifest["matched_artifacts"][stem] = {
                    "status": "PASS",
                    "labels": str(labels_path.relative_to(ROOT)), "labels_sha256": _sha(labels_path),
                    "prediction": str(prediction_path.relative_to(ROOT)), "prediction_sha256": _sha(prediction_path),
                    "keys": str(keys_path.relative_to(ROOT)), "keys_sha256": _sha(keys_path),
                    "row_key_sha256": row_key_hash(match["keys"]),
                }
    for name, delta in matched_deltas.items():
        matched_path = artifact_dir / f"matched_delta_{name}.npy"
        np.save(matched_path, np.asarray(delta, dtype=np.float64), allow_pickle=False)
        probe_manifest.setdefault("matched_delta_artifacts", {})[name] = {"path": str(matched_path.relative_to(ROOT)), "sha256": _sha(matched_path), "shape": list(delta.shape)}
    test_results: dict[str, Any] = {}
    for seed in DETECTOR_SEEDS:
        for arm, fit in comparison_fits[seed].items():
            rows = comparison_rows[seed][arm]
            stem = f"seed{seed}_{arm}"
            labels_path = artifact_dir / f"{stem}_labels.npy"
            prediction_path = artifact_dir / f"{stem}_prediction.npy"
            keys_path = artifact_dir / f"{stem}_keys.json"
            np.save(labels_path, np.asarray(rows["y"], dtype=np.int8), allow_pickle=False)
            np.save(prediction_path, np.asarray(fit["test_prediction"], dtype=np.float64), allow_pickle=False)
            keys_path.write_text(json.dumps(rows["keys"], sort_keys=True, separators=(",", ":")) + "\n")
            train_row = pooled["train"][seed][arm]
            val_row = pooled["validation"][seed][arm]
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
                validation_prediction_paths[c_value] = {"path": str(c_path.relative_to(ROOT)), "sha256": _sha(c_path), "n": int(len(validation_prediction))}
            probe_manifest["artifacts"][stem] = {
                "labels": str(labels_path.relative_to(ROOT)), "labels_sha256": _sha(labels_path),
                "prediction": str(prediction_path.relative_to(ROOT)), "prediction_sha256": _sha(prediction_path),
                "keys": str(keys_path.relative_to(ROOT)), "keys_sha256": _sha(keys_path),
                "train_validation_arrays": str(train_val_path.relative_to(ROOT)), "train_validation_arrays_sha256": _sha(train_val_path),
                "train_keys": str(train_keys_path.relative_to(ROOT)), "train_keys_sha256": _sha(train_keys_path),
                "validation_keys": str(val_keys_path.relative_to(ROOT)), "validation_keys_sha256": _sha(val_keys_path),
                "validation_labels": str(validation_labels_path.relative_to(ROOT)), "validation_labels_sha256": _sha(validation_labels_path),
                "test_features": str(test_features_path.relative_to(ROOT)), "test_features_sha256": _sha(test_features_path),
                "validation_prediction_paths": validation_prediction_paths,
                "coef": np.asarray(fit["model"].coef_, dtype=np.float64).tolist(), "intercept": np.asarray(fit["model"].intercept_, dtype=np.float64).tolist(),
                "coef_sha256": fit["coef_sha256"], "intercept_sha256": fit["intercept_sha256"],
                "scaler": fit["scaler"], "scaler_sha256": fit["scaler_sha256"], "selected_C": fit["selected_C"],
                "validation_candidates": fit["validation_candidates"],
                "train_row_key_sha256": fit["train_row_key_sha256"], "validation_row_key_sha256": fit["validation_row_key_sha256"], "test_row_key_sha256": fit["test_row_key_sha256"],
            }
            scenario_ap = _source_scenario_ap(fit, rows)
            test_results.setdefault(str(seed), {})[arm] = {"ap": compute_arm_ap(fit, rows), "scenario_ap": scenario_ap.tolist(), "n": int(len(rows["y"])), "positives": int(np.sum(rows["y"])), "natural_prevalence": float(np.mean(rows["y"])), "labels_sha256": _sha(labels_path), "prediction_sha256": _sha(prediction_path), "row_key_sha256": row_key_hash(rows["keys"])}
    _write_json(output_dir / "g1_execution_manifest.json", {"status": "LABELLED_EXECUTION_COMPLETE", "prelabel_seal_commit": prelabel_commit, "execution_commit": current_commit(), "code_sha256": _sha_bytes(Path(__file__).read_bytes()), "scientific_file_sha256": scientific_file_sha256(), "backend_environment": backend_environment, "rows": execution_rows, "feature_arms": feature_arms, "folds": G1_CONFIG["folds"], "shifted_scenarios": list(SHIFTED_SCENARIOS), "conditions": list(CONDITIONS), "labels_joined_after_observation_extraction": True, "optimizer_steps": False, "test_result_metrics_computed": True, "duration_severity_protocol_status": G1_CONFIG.get("duration_severity_matching", {}).get("status"), "execution_ledger": str(ledger_path.relative_to(ROOT)), "execution_ledger_sha256": _sha(ledger_path), "execution_ledger_contract": "metadata-only process/progress/exception ledger; no labels, predictions, features or metrics"})
    _write_json(output_dir / "g1_probe_manifest.json", probe_manifest)
    _write_json(output_dir / "g1_statistics.json", _clean(statistics))
    scenario_statistics = {name: {"shape": list(value.shape), "sha256": array_sha(value), "values": value.tolist()} for name, value in scenario_deltas.items()}
    matched_statistics = {name: {"shape": list(value.shape), "sha256": array_sha(value), "values": value.tolist()} for name, value in matched_deltas.items()}
    matched_scenario_statistics = {name: {"shape": list(value.shape), "sha256": array_sha(value), "values": value.tolist()} for name, value in matched_scenario_deltas.items()}
    _write_json(output_dir / "g1_results.json", {"test_ap": test_results, "specificity": specificity, "descriptive_strata": descriptive_rows, "descriptive_test_strata": descriptive_test, "natural_prevalence_evaluation": natural_prevalence, "pooled_source_ap": {arm: values.tolist() for arm, values in pooled_ap.items()}, "pooled_source_ap_mean": {arm: float(np.mean(values)) for arm, values in pooled_ap.items()}, "scenario_deltas": scenario_statistics, "duration_severity_support": matched_report, "duration_severity_primary_effects": matched_statistics, "duration_severity_scenario_effects": matched_scenario_statistics, "delta_sha256": {name: array_sha(value) for name, value in deltas.items()}, "delta_shape": {name: list(value.shape) for name, value in deltas.items()}, "test_sources": list(TEST_SOURCES), "scenarios": list(SHIFTED_SCENARIOS), "conditions": list(CONDITIONS), "primary_cohort_prevalence": {str(seed): {arm: float(test_results[str(seed)][arm]["positives"] / test_results[str(seed)][arm]["n"]) for arm in test_results[str(seed)]} for seed in DETECTOR_SEEDS}})
    from phase_g1_core import h2_go, h3a_go, positive_seed_scenario_counts, positive_seed_source_counts
    h2_raw = statistics["comparisons"]["h2"]
    h2_seed_count = positive_seed_source_counts(deltas["h2"])
    h2_scenario_count = positive_seed_scenario_counts(scenario_deltas["h2"])[1]
    # Duration/severity support is evaluator-side and fixed: require at least
    # one supported binary duration/severity stratum.  If unavailable, report
    # N/A and fail closed rather than merging bins after seeing outcomes.
    # The current frozen generator provides only the explicitly labelled
    # identical-observation control.  It is not eligible to satisfy the
    # protocol's supportive duration/severity gate until an external
    # pre-outcome amendment defines that estimand.
    matched_support = bool(
        matched_report.get("protocol_status") == "RESOLVED"
        and matched_report.get("supportive_h2_if_resolved", False)
    )
    h2_status = "GO" if h2_go(h2_raw["mean"], h2_raw["ci95"][0], h2_raw["holm_adjusted_p"], h2_seed_count, h2_scenario_count, matched_support) else "STOP"
    h3a_counts = {name: {"positive_detector_seeds": positive_seed_source_counts(deltas[name]), "positive_scenarios": positive_seed_scenario_counts(scenario_deltas[name])[1]} for name in ("h3a_a", "h3a_b", "h3a_c")}
    h3_repro = all(row["positive_detector_seeds"] >= 4 and row["positive_scenarios"] >= 3 for row in h3a_counts.values())
    h3a_matched_support = bool(
        matched_report.get("protocol_status") == "RESOLVED"
        and matched_report.get("supportive_h3a_if_resolved", False)
    )
    h3a_status = "NOT_ELIGIBLE"
    if h2_status == "GO":
        a, b, c = (statistics["comparisons"][name] for name in ("h3a_a", "h3a_b", "h3a_c"))
        h3a_status = "GO" if h3a_go(True, a["mean"], a["ci95"][0], a["holm_adjusted_p"], b["mean"], b["ci95"][0], b["holm_adjusted_p"], c["mean"], c["ci95"][0], c["holm_adjusted_p"], h3_repro, h3a_matched_support) else "STOP"
    decision = {"H2": h2_status, "H3a": h3a_status, "H3b": "UNLOCKED" if h3a_status == "GO" else "LOCKED", "h1_controlled_harm": "STOP", "h1_natural_harm": "NOT_RUN", "h1_harm_overall": "UNRESOLVED", "duration_severity_matched": matched_report, "h2_positive_detector_seeds": h2_seed_count, "h2_positive_scenarios": h2_scenario_count, "h3a_reproducibility": h3a_counts, "h3a_reproducibility_pass": h3_repro, "h2_matched_support_used": matched_support, "h3a_matched_support_used": h3a_matched_support}
    _write_json(output_dir / "g1_decision.json", decision)
    (output_dir / "g1_decision.md").write_text("# Phase G1 decision\n\n" + "\n".join(f"{key} = {value}" for key, value in (("H2", h2_status), ("H3a", h3a_status), ("H3b", decision["H3b"]))) + "\n\nH1_controlled_harm = STOP\nH1_natural_harm = NOT_RUN\nH1_harm_overall = UNRESOLVED\n\nDuration/severity-matched analysis: " + str(matched_report) + "\n")
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
