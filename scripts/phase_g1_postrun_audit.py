"""Independent post-label audit for a sealed Phase-G1 run.

The auditor deliberately does not call the Stage-C statistics implementation.
It reconstructs AP, source-pooled effects, validation-C selection, bootstrap,
sign-flip, Holm adjustment and Boolean decisions from the primitive arrays
written by the runner. A discrepancy quarantines the run; this module never
repairs or overwrites scientific outputs.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from phase_g1_core import (  # noqa: E402
    BOOTSTRAP_DRAWS,
    BOOTSTRAP_SEED,
    C_GRID,
    DETECTOR_SEEDS,
    DURATION_STRATA,
    SEVERITY_STRATA,
    HOLM_FAMILY_SIZE,
    SHIFTED_SCENARIOS,
    TEST_SOURCES,
    ProtocolViolation,
    assert_same_row_order,
    assert_unique_keys,
    row_key_hash,
)
from phase_g1_pipeline import SCIENTIFIC_PRELABEL_FILES  # noqa: E402


ARMS = (
    "history14",
    "hidden52",
    "gate130",
    "memory52",
    "combined234",
    "history_plus_combined248",
    "candi_history14",
    "candi_history_plus_combined248",
)
ARCHITECTURES = ("xlstm", "lstm")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _close(a: float, b: float) -> bool:
    return bool(np.isclose(float(a), float(b), atol=1e-12, rtol=1e-10))


def _ap(y: np.ndarray, prediction: np.ndarray) -> float:
    from sklearn.metrics import average_precision_score

    return float(average_precision_score(np.asarray(y, dtype=np.int8), np.asarray(prediction, dtype=np.float64)))


def _source_pooled_ap(labels: np.ndarray, prediction: np.ndarray, keys: list[dict[str, Any]]) -> np.ndarray:
    result = np.full((len(TEST_SOURCES),), np.nan, dtype=np.float64)
    source = np.asarray([int(key["source_seed"]) for key in keys], dtype=np.int64)
    for index, source_seed in enumerate(TEST_SOURCES):
        mask = source == source_seed
        if int(mask.sum()) == 0 or len(np.unique(labels[mask])) < 2:
            raise ProtocolViolation(f"source-pooled artifact lacks both classes: {source_seed}")
        result[index] = _ap(labels[mask], prediction[mask])
    return result


def _source_scenario_ap(labels: np.ndarray, prediction: np.ndarray, keys: list[dict[str, Any]]) -> np.ndarray:
    result = np.full((len(TEST_SOURCES), len(SHIFTED_SCENARIOS)), np.nan, dtype=np.float64)
    source = np.asarray([int(key["source_seed"]) for key in keys], dtype=np.int64)
    scenario = np.asarray([str(key["scenario"]) for key in keys], dtype=object)
    for i, source_seed in enumerate(TEST_SOURCES):
        for j, scenario_name in enumerate(SHIFTED_SCENARIOS):
            mask = (source == source_seed) & (scenario == scenario_name)
            if int(mask.sum()) == 0 or len(np.unique(labels[mask])) < 2:
                raise ProtocolViolation(f"source/scenario artifact lacks both classes: {source_seed}/{scenario_name}")
            result[i, j] = _ap(labels[mask], prediction[mask])
    return result


def _bootstrap_primary(values: np.ndarray) -> dict[str, Any]:
    """Independent implementation of the frozen source-first bootstrap."""
    values = np.asarray(values, dtype=np.float64)
    if values.shape != (10, 5) or not np.isfinite(values).all():
        raise ProtocolViolation("primary bootstrap tensor must be finite [10,5]")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    source_indices = rng.integers(0, 10, size=(BOOTSTRAP_DRAWS, 10))
    seed_indices = rng.integers(0, 5, size=(BOOTSTRAP_DRAWS, 10, 5))
    sampled = values[source_indices[:, :, None], seed_indices]
    means = sampled.mean(axis=(1, 2))
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {"draws": BOOTSTRAP_DRAWS, "seed": BOOTSTRAP_SEED, "mean": float(values.mean()), "ci95": [float(lo), float(hi)]}


def _sign_flip_primary(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=np.float64)
    if values.shape != (10, 5) or not np.isfinite(values).all():
        raise ProtocolViolation("primary sign-flip tensor must be finite [10,5]")
    source_means = values.mean(axis=1)
    signs = np.asarray(list(itertools.product((-1.0, 1.0), repeat=10)), dtype=np.float64)
    observed = abs(float(source_means.mean()))
    null = np.abs((signs * source_means[None, :]).mean(axis=1))
    return float(np.mean(null >= observed - 1e-15))


def _holm(values: list[float]) -> list[float]:
    if len(values) != HOLM_FAMILY_SIZE:
        raise ProtocolViolation("independent Holm family is not exactly four members")
    p = np.asarray(values, dtype=np.float64)
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ProtocolViolation("invalid p-value family")
    order = np.argsort(p, kind="stable")
    adjusted = np.minimum(1.0, np.maximum.accumulate(p[order] * (len(p) - np.arange(len(p)))))
    result = np.empty_like(p)
    result[order] = adjusted
    return result.tolist()


def _independent_h2(effect: float, ci_lower: float, p: float, seed_count: int, scenario_count: int, robustness_support: bool) -> bool:
    return bool(effect >= 0.02 and ci_lower > 0 and p < 0.05 and seed_count >= 4 and scenario_count >= 3 and robustness_support)


def _independent_h3(h2: bool, a: Mapping[str, float], b: Mapping[str, float], c: Mapping[str, float], reproducibility: bool, robustness_support: bool) -> bool:
    if not h2:
        return False
    return bool(
        a["mean"] >= 0.02 and a["ci_lower"] > 0 and a["p"] < 0.05
        and b["mean"] > 0 and b["ci_lower"] > 0 and b["p"] < 0.05
        and c["mean"] > 0 and c["ci_lower"] > 0 and c["p"] < 0.05
        and reproducibility and robustness_support
    )


def _load_array(relative: str, expected_sha: str) -> np.ndarray:
    path = ROOT / relative
    if _sha(path) != expected_sha:
        raise ProtocolViolation(f"artifact hash mismatch: {relative}")
    return np.load(path, allow_pickle=False)


def _probe_prediction(fit: Mapping[str, Any], features: np.ndarray) -> np.ndarray:
    """Reconstruct a frozen logistic prediction from manifest primitives."""
    x = np.asarray(features, dtype=np.float64)
    scaler = fit["scaler"]
    mean = np.asarray(scaler["mean"], dtype=np.float64)
    scale = np.asarray(scaler["scale"], dtype=np.float64)
    coef = np.asarray(fit["coef"], dtype=np.float64)
    intercept = np.asarray(fit["intercept"], dtype=np.float64)
    if (
        x.ndim != 2
        or mean.shape != (x.shape[1],)
        or scale.shape != mean.shape
        or not np.isfinite(mean).all()
        or not np.isfinite(scale).all()
        or np.any(scale <= 0)
        or coef.ndim != 2
        or coef.shape != (1, x.shape[1])
        or intercept.shape != (1,)
        or not np.isfinite(coef).all()
        or not np.isfinite(intercept).all()
    ):
        raise ProtocolViolation("semantic/robustness feature dimension mismatch")
    logits = ((x - mean) / scale) @ coef.T + intercept
    return (1.0 / (1.0 + np.exp(-logits[:, 0]))).astype(np.float64)


def _frozen_probe_prediction(
    probes: Mapping[str, Any],
    stem: str,
    features: np.ndarray,
    expected_prediction: np.ndarray | None = None,
) -> np.ndarray:
    """Recompute a prediction from the numeric probe artifact, not summaries.

    ``probes['fits']`` is a metadata-only serialization whose coefficient
    arrays are intentionally reduced to shape/dtype/hash records.  The
    report's per-arm artifact contains the numeric scaler/coef/intercept needed
    for an independent replay.  When a saved prediction is supplied, it is
    checked against that replay so a hash-consistent but numerically altered
    subgroup cannot pass the post-run audit.
    """
    artifact = probes.get("artifacts", {}).get(stem)
    if not isinstance(artifact, Mapping):
        raise ProtocolViolation(f"missing numeric probe artifact {stem}")
    prediction = _probe_prediction(artifact, features)
    if expected_prediction is not None:
        expected = np.asarray(expected_prediction, dtype=np.float64)
        if expected.shape != prediction.shape or not np.allclose(
            prediction, expected, atol=1e-12, rtol=1e-10
        ):
            raise ProtocolViolation(f"saved prediction differs from frozen probe replay: {stem}")
    return prediction


def _audit_semantic_control(
    probes: Mapping[str, Any],
    discrepancies: list[str],
) -> dict[str, Any]:
    """Audit semantic-identical artifacts without treating them as evidence."""
    report = probes.get("semantic_control", {})
    if report.get("analysis_kind") != "semantic_nonidentifiability_control":
        discrepancies.append("semantic control has an unexpected analysis kind")
    if report.get("status") != "PASS":
        discrepancies.append("semantic non-identifiability control did not pass")
    artifacts = probes.get("semantic_control_artifacts", {})
    checked = 0
    for seed in DETECTOR_SEEDS:
        for architecture in ("xlstm", "lstm"):
            for arm in ARMS:
                stem = f"seed{seed}_{arm}_{architecture}"
                artifact = artifacts.get(stem)
                if not artifact:
                    discrepancies.append(f"missing semantic-control artifact {stem}")
                    continue
                if artifact.get("status") != "PASS":
                    # A no-support stream is valid only as an explicit N/A;
                    # the fixed synthetic test cohort should normally provide
                    # the non-stress counterpart rows.
                    if artifact.get("status") != "N/A":
                        discrepancies.append(f"unexpected semantic artifact status {stem}")
                    continue
                try:
                    feature_path = ROOT / artifact["features"]
                    keys_path = ROOT / artifact["keys"]
                    if _sha(feature_path) != artifact["features_sha256"] or _sha(keys_path) != artifact["keys_sha256"]:
                        raise ProtocolViolation("semantic artifact hash mismatch")
                    with np.load(feature_path, allow_pickle=False) as cached:
                        anomaly_x = np.asarray(cached["anomaly_X"], dtype=np.float64)
                        legitimate_x = np.asarray(cached["legitimate_X"], dtype=np.float64)
                    keys = json.loads(keys_path.read_text())
                    assert_unique_keys(keys)
                    if row_key_hash(keys) != artifact.get("row_key_sha256"):
                        raise ProtocolViolation("semantic control row-key hash mismatch")
                    if len(keys) != len(anomaly_x) or anomaly_x.shape != legitimate_x.shape:
                        raise ProtocolViolation("semantic artifact lengths/shapes differ")
                    if not np.allclose(anomaly_x, legitimate_x, atol=1e-5, rtol=1e-4, equal_nan=True):
                        raise ProtocolViolation("semantic counterpart features differ")
                    stem = f"seed{seed}_{arm}_{architecture}"
                    anomaly_pred = _frozen_probe_prediction(probes, stem, anomaly_x)
                    legitimate_pred = _frozen_probe_prediction(probes, stem, legitimate_x)
                    if not np.allclose(anomaly_pred, legitimate_pred, atol=1e-5, rtol=1e-4):
                        raise ProtocolViolation("semantic counterpart predictions differ")
                    checked += 1
                except (OSError, KeyError, ValueError, ProtocolViolation) as exc:
                    discrepancies.append(f"semantic artifact {stem}: {exc}")
    # A synthetic AP from artificial opposite labels is intentionally absent;
    # reject any accidental attempt to make it part of the confirmatory family.
    if any("semantic" in str(name).lower() for name in probes.get("delta_artifacts", {})):
        discrepancies.append("semantic control was included in confirmatory deltas")
    for check in report.get("checks", []):
        if check.get("ap_used_as_evidence") is not False:
            discrepancies.append("semantic control AP/evidence flag is not false")
    return {"status": "PASS" if not any("semantic" in item for item in discrepancies) else "STOP", "checked_artifacts": checked}


def _audit_robustness(
    probes: Mapping[str, Any],
    results: Mapping[str, Any],
    discrepancies: list[str],
) -> dict[str, Any]:
    """Recompute duration/severity robustness from primitive subgroup artifacts."""
    robustness = results.get("duration_severity_robustness", {})
    if robustness.get("analysis_name") != "duration_severity_stratified_robustness":
        discrepancies.append("duration/severity robustness analysis name drifted")
    artifacts = probes.get("robustness_artifacts", {})
    types = ("spike", "collective", "dependency")
    ap_by_axis: dict[str, dict[str, dict[str, np.ndarray]]] = {"duration": {}, "severity": {}}
    derived: dict[str, dict[str, list[dict[str, Any]]]] = {
        "duration": {name: [] for name in ("h2", "h3a_a", "h3a_b", "h3a_c")},
        "severity": {name: [] for name in ("h2", "h3a_a", "h3a_b", "h3a_c")},
    }
    checked = 0
    for axis, values in (("duration", DURATION_STRATA), ("severity", SEVERITY_STRATA)):
        for value in values:
            key = str(value)
            ap_by_axis[axis][key] = {}
            for seed_index, seed in enumerate(DETECTOR_SEEDS):
                for arm in ARMS:
                    for architecture in ARCHITECTURES:
                        name = f"{arm}_{architecture}"
                        stem = f"seed{seed}_{axis}{key}_{name}"
                        artifact = artifacts.get(stem)
                        if not artifact:
                            discrepancies.append(f"missing robustness artifact {stem}")
                            continue
                        if artifact.get("status") != "PASS":
                            if artifact.get("status") != "INSUFFICIENT_SUPPORT":
                                discrepancies.append(f"unexpected robustness status {stem}")
                            continue
                        try:
                            labels = _load_array(artifact["labels"], artifact["labels_sha256"]).astype(np.int8)
                            prediction = _load_array(artifact["prediction"], artifact["prediction_sha256"]).astype(np.float64)
                            feature_path = ROOT / artifact["features"]
                            keys_path = ROOT / artifact["keys"]
                            metadata_path = ROOT / artifact["metadata"]
                            if _sha(feature_path) != artifact["features_sha256"] or _sha(keys_path) != artifact["keys_sha256"] or _sha(metadata_path) != artifact["metadata_sha256"]:
                                raise ProtocolViolation("robustness artifact hash mismatch")
                            with np.load(feature_path, allow_pickle=False) as cached:
                                features = np.asarray(cached["X"], dtype=np.float64)
                            keys = json.loads(keys_path.read_text())
                            metadata = _json(metadata_path)
                            assert_unique_keys(keys)
                            if row_key_hash(keys) != artifact.get("row_key_sha256"):
                                raise ProtocolViolation("robustness row-key hash mismatch")
                            n = len(keys)
                            if labels.shape != (n,) or prediction.shape != (n,) or features.shape[0] != n:
                                raise ProtocolViolation("robustness artifact lengths differ")
                            if not np.isfinite(prediction).all() or not np.isfinite(features).all() or not np.isin(labels, [0, 1]).all():
                                raise ProtocolViolation("robustness artifact contains non-finite/nonbinary values")
                            # Reconstruct from the numeric frozen probe
                            # artifact and compare to the saved subgroup
                            # predictions before computing AP.
                            _frozen_probe_prediction(probes, stem, features, prediction)
                            for field in ("event_types", "duration", "severity", "stratum"):
                                if len(metadata.get(field, [])) != n:
                                    raise ProtocolViolation(f"robustness metadata length mismatch: {field}")
                            for index, (label, row_key) in enumerate(zip(labels, keys)):
                                event_type = metadata["event_types"][index]
                                duration = metadata["duration"][index]
                                severity = metadata["severity"][index]
                                stratum = metadata["stratum"][index]
                                if stratum not in {"anomaly", "drift"}:
                                    raise ProtocolViolation("mixed/stationary row entered robustness artifact")
                                if int(label) == 1:
                                    if event_type not in types or int(row_key["event"]) < 0:
                                        raise ProtocolViolation("non-stress event attribution missing from positive robustness row")
                                    if axis == "duration" and int(duration) != int(value):
                                        raise ProtocolViolation("duration stratum metadata mismatch")
                                    if axis == "severity" and int(severity) != int(value):
                                        raise ProtocolViolation("severity stratum metadata mismatch")
                                else:
                                    if int(row_key["event"]) != -1 or event_type is not None or duration is not None or severity is not None:
                                        raise ProtocolViolation("drift negative received event duration/severity metadata")
                            source = np.asarray([int(row["source_seed"]) for row in keys], dtype=np.int64)
                            matrix = ap_by_axis[axis][key].setdefault(name, np.full((len(TEST_SOURCES), len(DETECTOR_SEEDS),), np.nan))
                            for source_index, source_seed in enumerate(TEST_SOURCES):
                                mask = source == source_seed
                                if mask.sum() and len(np.unique(labels[mask])) == 2:
                                    matrix[source_index, seed_index] = _ap(labels[mask], prediction[mask])
                            checked += 1
                        except (OSError, KeyError, ValueError, ProtocolViolation) as exc:
                            discrepancies.append(f"robustness artifact {stem}: {exc}")
            # Exact paired row cohorts are checked across all arms and both
            # backbones for each detector seed/stratum.
            for seed in DETECTOR_SEEDS:
                reference_keys: list[dict[str, Any]] | None = None
                reference_labels: np.ndarray | None = None
                for arm in ARMS:
                    for architecture in ARCHITECTURES:
                        stem = f"seed{seed}_{axis}{key}_{arm}_{architecture}"
                        artifact = artifacts.get(stem, {})
                        if artifact.get("status") != "PASS":
                            continue
                        try:
                            keys = json.loads((ROOT / artifact["keys"]).read_text())
                            labels = _load_array(artifact["labels"], artifact["labels_sha256"]).astype(np.int8)
                            if reference_keys is None:
                                reference_keys, reference_labels = keys, labels
                            else:
                                assert_same_row_order(reference_keys, keys)
                                if not np.array_equal(reference_labels, labels):
                                    raise ProtocolViolation("robustness paired labels differ")
                        except (OSError, ValueError, ProtocolViolation) as exc:
                            discrepancies.append(f"robustness paired cohort {stem}: {exc}")
            # Compare independently reconstructed effects and statuses against
            # the runner's report; no cached GO flag is trusted.
            def m(name: str) -> np.ndarray:
                return ap_by_axis[axis][key].get(name, np.full((len(TEST_SOURCES), len(DETECTOR_SEEDS)), np.nan))
            effects = {
                "h2": m("history_plus_combined248_xlstm") - m("history14_xlstm"),
                "h3a_a": m("combined234_xlstm") - m("combined234_lstm"),
                "h3a_b": (m("history_plus_combined248_xlstm") - m("history14_xlstm")) - (m("history_plus_combined248_lstm") - m("history14_lstm")),
                "h3a_c": (m("candi_history_plus_combined248_xlstm") - m("candi_history14_xlstm")) - (m("candi_history_plus_combined248_lstm") - m("candi_history14_lstm")),
            }
            for name, effect in effects.items():
                report_strata = robustness.get(axis, {}).get("comparisons", {}).get(name, {}).get("strata", [])
                reported = next((row for row in report_strata if int(row.get("stratum", -1)) == int(value)), None)
                supported = bool(np.isfinite(effect).all())
                if reported is None:
                    discrepancies.append(f"missing reported robustness stratum {axis}={value}/{name}")
                    continue
                if bool(reported.get("support")) != supported:
                    discrepancies.append(f"robustness support mismatch {axis}={value}/{name}")
                if supported:
                    reported_effect = np.asarray(reported.get("effect", []), dtype=np.float64)
                    if reported_effect.shape != effect.shape or not np.array_equal(reported_effect, effect):
                        discrepancies.append(f"robustness effect mismatch {axis}={value}/{name}")
                    if not _close(float(reported.get("mean")), float(effect.mean())):
                        discrepancies.append(f"robustness mean mismatch {axis}={value}/{name}")
            for name, effect in effects.items():
                supported = bool(np.isfinite(effect).all())
                derived[axis][name].append({
                    "support": supported,
                    "mean": float(effect.mean()) if supported else None,
                    "positive_strata": None,
                })
    statuses: dict[str, dict[str, Any]] = {"duration": {}, "severity": {}}
    for axis, values in (("duration", DURATION_STRATA), ("severity", SEVERITY_STRATA)):
        for name, strata in derived[axis].items():
            if len(strata) != len(values) or not all(item["support"] for item in strata):
                statuses[axis][name] = "INSUFFICIENT_SUPPORT"
                reported_comparison = robustness.get(axis, {}).get("comparisons", {}).get(name, {})
                if reported_comparison.get("status") != "INSUFFICIENT_SUPPORT":
                    discrepancies.append(f"robustness insufficient-support status mismatch {axis}/{name}")
                continue
            means = np.asarray([float(item["mean"]) for item in strata], dtype=np.float64)
            threshold = 0.02 if name in {"h2", "h3a_a"} else 0.0
            margin_ok = float(means.mean()) >= threshold if threshold > 0 else float(means.mean()) > threshold
            positive = int((means > 0).sum())
            minimum = 3 if len(values) == 4 else 2
            statuses[axis][name] = "PASS" if margin_ok and positive >= minimum else "STOP"
            reported_comparison = robustness.get(axis, {}).get("comparisons", {}).get(name, {})
            if not _close(float(reported_comparison.get("macro")), float(means.mean())):
                discrepancies.append(f"robustness macro mismatch {axis}/{name}")
            if int(reported_comparison.get("positive_strata", -1)) != positive:
                discrepancies.append(f"robustness positive-strata count mismatch {axis}/{name}")
            if reported_comparison.get("status") != statuses[axis][name]:
                discrepancies.append(f"robustness status mismatch {axis}/{name}")
    h2_statuses = [statuses[axis]["h2"] for axis in ("duration", "severity")]
    h2_status = "PASS" if all(status == "PASS" for status in h2_statuses) else "INSUFFICIENT_SUPPORT" if any(status == "INSUFFICIENT_SUPPORT" for status in h2_statuses) else "STOP"
    h3_statuses = [statuses[axis][name] for axis in ("duration", "severity") for name in ("h3a_a", "h3a_b", "h3a_c")]
    h3_status = "PASS" if all(status == "PASS" for status in h3_statuses) else "INSUFFICIENT_SUPPORT" if any(status == "INSUFFICIENT_SUPPORT" for status in h3_statuses) else "STOP"
    if robustness.get("h2_status") != h2_status:
        discrepancies.append("robustness top-level H2 status mismatch")
    if robustness.get("h3a_status_if_primary_h2_go") != h3_status:
        discrepancies.append("robustness top-level H3a status mismatch")
    return {
        "status": "PASS" if not any("robustness" in item for item in discrepancies) else "STOP",
        "checked_artifacts": checked,
        "derived_statuses": statuses,
        "h2_status": h2_status,
        "h3a_status_if_primary_h2_go": h3_status,
    }


def audit(output_dir: Path, prelabel_commit: str) -> dict[str, Any]:
    required = (
        "g1_execution_manifest.json", "g1_probe_manifest.json", "g1_results.json",
        "g1_statistics.json", "g1_decision.json", "g1_decision.md",
    )
    missing = [name for name in required if not (output_dir / name).exists()]
    if missing:
        raise ProtocolViolation(f"missing G1 output artifacts: {missing}")
    execution = _json(output_dir / "g1_execution_manifest.json")
    probes = _json(output_dir / "g1_probe_manifest.json")
    results = _json(output_dir / "g1_results.json")
    statistics = _json(output_dir / "g1_statistics.json")
    decision = _json(output_dir / "g1_decision.json")
    discrepancies: list[str] = []

    if execution.get("prelabel_seal_commit") != prelabel_commit or execution.get("execution_commit") != prelabel_commit:
        discrepancies.append("execution commit differs from G1_PRELABEL_SEAL_COMMIT")
    try:
        current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        if current != prelabel_commit:
            discrepancies.append("current Git HEAD differs from G1_PRELABEL_SEAL_COMMIT")
    except Exception as exc:
        discrepancies.append(f"cannot resolve current Git HEAD: {exc!r}")
    expected_code_sha = hashlib.sha256((ROOT / "scripts" / "phase_g1_run.py").read_bytes()).hexdigest()
    if execution.get("code_sha256") != expected_code_sha:
        discrepancies.append("labelled runner code hash differs from execution manifest")
    sealed_files = execution.get("scientific_file_sha256", {})
    for relative in SCIENTIFIC_PRELABEL_FILES:
        if relative not in sealed_files or not (ROOT / relative).exists() or _sha(ROOT / relative) != sealed_files.get(relative):
            discrepancies.append(f"scientific file seal mismatch: {relative}")
    if execution.get("test_result_metrics_computed") is not True:
        discrepancies.append("execution manifest does not declare test metrics")
    if execution.get("duration_severity_protocol_status") != "RESOLVED":
        discrepancies.append("duration/severity supportive estimand was unresolved during labeled execution")
    expected_backend = {
        "cudnn_deterministic": True,
        "cudnn_benchmark": False,
        "deterministic_algorithms": False,
        "matmul_precision": "highest",
        "matmul_allow_tf32": False,
        "cudnn_allow_tf32": False,
    }
    backend = execution.get("backend_environment", {})
    if any(backend.get(key) != value for key, value in expected_backend.items()):
        discrepancies.append("execution backend fingerprint differs from F-v4 contract")
    ledger_rel = execution.get("execution_ledger")
    ledger_records: list[dict[str, Any]] = []
    if not isinstance(ledger_rel, str):
        discrepancies.append("execution-forensics ledger path is missing")
    else:
        ledger_path = ROOT / ledger_rel
        try:
            if not ledger_path.exists():
                raise ProtocolViolation("execution-forensics ledger is missing")
            expected_ledger_sha = execution.get("execution_ledger_sha256")
            if not isinstance(expected_ledger_sha, str) or _sha(ledger_path) != expected_ledger_sha:
                raise ProtocolViolation("execution-forensics ledger hash mismatch")
            for line in ledger_path.read_text().splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                if not isinstance(record, dict) or "event" not in record:
                    raise ProtocolViolation("malformed execution-forensics record")
                ledger_records.append(record)
            events = [str(record["event"]) for record in ledger_records]
            if not events or events[0] != "process_start" or events[-1] != "process_complete":
                raise ProtocolViolation("execution-forensics ledger lacks clean start/terminal records")
            if "process_exception" in events:
                raise ProtocolViolation("execution-forensics ledger records an exception")
            expected_stream_count = len(DETECTOR_SEEDS) * (10 + 5 + 10) * (1 + 4 * 5)
            completed_streams = [record for record in ledger_records if record.get("event") == "labelled_stream_complete"]
            if len(completed_streams) != expected_stream_count:
                raise ProtocolViolation(f"execution-forensics stream count {len(completed_streams)} != {expected_stream_count}")
            if any(record.get("event") in {"retry", "resume", "overwrite"} for record in ledger_records):
                raise ProtocolViolation("execution-forensics records retry/resume/overwrite")
        except (OSError, ValueError, ProtocolViolation) as exc:
            discrepancies.append(f"execution-forensics ledger: {exc}")
    expected_inventory = {(seed, source, fold, scenario, condition) for seed in DETECTOR_SEEDS for fold, sources in (("train", range(1000, 1010)), ("validation", range(2000, 2005)), ("test", range(3000, 3010))) for source in sources for scenario in (*SHIFTED_SCENARIOS, "stationary") for condition in (("none",) if scenario == "stationary" else ("none", "spike", "collective", "dependency", "mixture"))}
    observed_inventory = {(int(row["seed"]), int(row["source"]), row["fold"], row["scenario"], row["condition"]) for row in execution.get("rows", [])}
    if len(execution.get("rows", [])) != len(observed_inventory):
        discrepancies.append("execution inventory contains duplicate run rows")
    if observed_inventory != expected_inventory:
        discrepancies.append(f"execution inventory mismatch: expected {len(expected_inventory)}, observed {len(observed_inventory)}")

    all_artifacts = probes.get("artifacts", {})
    test_ap_by_seed: dict[int, dict[str, float]] = {seed: {} for seed in DETECTOR_SEEDS}
    pooled_ap_by_arm = {f"{arm}_{architecture}": np.full((10, 5), np.nan) for arm in ARMS for architecture in ARCHITECTURES}
    scenario_ap_by_arm = {f"{arm}_{architecture}": np.full((10, 5, 4), np.nan) for arm in ARMS for architecture in ARCHITECTURES}

    for seed_index, seed in enumerate(DETECTOR_SEEDS):
        for arm in ARMS:
            for architecture in ARCHITECTURES:
                name = f"{arm}_{architecture}"
                stem = f"seed{seed}_{name}"
                artifact = all_artifacts.get(stem)
                if artifact is None:
                    discrepancies.append(f"missing probe artifact {stem}")
                    continue
                try:
                    labels = _load_array(artifact["labels"], artifact["labels_sha256"]).astype(np.int8)
                    prediction = _load_array(artifact["prediction"], artifact["prediction_sha256"]).astype(np.float64)
                    test_feature_path = ROOT / artifact["test_features"]
                    if _sha(test_feature_path) != artifact["test_features_sha256"]:
                        raise ProtocolViolation(f"test feature cache hash mismatch: {stem}")
                    with np.load(test_feature_path, allow_pickle=False) as feature_cache:
                        test_x = np.asarray(feature_cache["test_X"], dtype=np.float64)
                    keys_path = ROOT / artifact["keys"]
                    if _sha(keys_path) != artifact["keys_sha256"]:
                        raise ProtocolViolation(f"key hash mismatch: {stem}")
                    keys = json.loads(keys_path.read_text())
                    if len(labels) != len(prediction) or len(keys) != len(labels):
                        raise ProtocolViolation(f"artifact lengths differ: {stem}")
                    scaler = artifact["scaler"]
                    coef = np.asarray(artifact["coef"], dtype=np.float64)
                    intercept = np.asarray(artifact["intercept"], dtype=np.float64)
                    if test_x.shape[0] != len(labels) or test_x.shape[1] != coef.shape[1]:
                        raise ProtocolViolation(f"test feature cache shape mismatch: {stem}")
                    logits = ((test_x - np.asarray(scaler["mean"], dtype=np.float64)) / np.asarray(scaler["scale"], dtype=np.float64)) @ coef.T + intercept
                    reconstructed_prediction = 1.0 / (1.0 + np.exp(-logits[:, 0]))
                    if not np.allclose(reconstructed_prediction, prediction, atol=1e-12, rtol=1e-10):
                        raise ProtocolViolation(f"saved test predictions do not follow saved features/coef/scaler: {stem}")
                    assert_unique_keys(keys)
                    if row_key_hash(keys) != artifact.get("test_row_key_sha256"):
                        raise ProtocolViolation(f"test row-key hash mismatch: {stem}")
                    if any(int(key["source_seed"]) not in TEST_SOURCES or key["scenario"] not in SHIFTED_SCENARIOS for key in keys):
                        raise ProtocolViolation(f"test artifact has wrong source/scenario: {stem}")
                    tv_path = ROOT / artifact["train_validation_arrays"]
                    if _sha(tv_path) != artifact["train_validation_arrays_sha256"]:
                        raise ProtocolViolation(f"train/validation array hash mismatch: {stem}")
                    with np.load(tv_path, allow_pickle=False) as tv:
                        train_x = np.asarray(tv["train_X"], dtype=np.float64)
                        val_x = np.asarray(tv["validation_X"], dtype=np.float64)
                        val_y = np.asarray(tv["validation_y"], dtype=np.int8)
                    train_keys_path = ROOT / artifact["train_keys"]
                    val_keys_path = ROOT / artifact["validation_keys"]
                    if _sha(train_keys_path) != artifact["train_keys_sha256"] or _sha(val_keys_path) != artifact["validation_keys_sha256"]:
                        raise ProtocolViolation(f"train/validation key hash mismatch: {stem}")
                    train_keys = json.loads(train_keys_path.read_text())
                    val_keys = json.loads(val_keys_path.read_text())
                    if any(int(key["source_seed"]) not in range(1000, 1010) for key in train_keys) or any(int(key["source_seed"]) not in range(2000, 2005) for key in val_keys):
                        raise ProtocolViolation(f"fold leakage in train/validation keys: {stem}")
                    scaler = artifact["scaler"]
                    mean = train_x.mean(axis=0)
                    scale = train_x.std(axis=0, ddof=0)
                    scale[scale == 0] = 1.0
                    if not np.allclose(mean, np.asarray(scaler["mean"]), atol=1e-12, rtol=1e-10) or not np.allclose(scale, np.asarray(scaler["scale"]), atol=1e-12, rtol=1e-10) or scaler.get("fit_fold") != "train":
                        raise ProtocolViolation(f"scaler is not train-only fit: {stem}")
                    val_labels = _load_array(artifact["validation_labels"], artifact["validation_labels_sha256"]).astype(np.int8)
                    if not np.array_equal(val_labels, val_y):
                        raise ProtocolViolation(f"validation labels differ: {stem}")
                    candidates = artifact.get("validation_candidates", [])
                    if tuple(float(row["C"]) for row in candidates) != tuple(float(value) for value in C_GRID):
                        raise ProtocolViolation(f"C grid drifted: {stem}")
                    validation_aps = []
                    for row in candidates:
                        c_value = str(float(row["C"]))
                        pred_meta = artifact.get("validation_prediction_paths", {}).get(c_value)
                        if pred_meta is None:
                            raise ProtocolViolation(f"missing validation prediction: {stem}/C={c_value}")
                        val_prediction = _load_array(pred_meta["path"], pred_meta["sha256"]).astype(np.float64)
                        if len(val_prediction) != len(val_labels):
                            raise ProtocolViolation(f"validation prediction length mismatch: {stem}")
                        ap_value = _ap(val_labels, val_prediction)
                        if not _close(ap_value, float(row["ap"])):
                            raise ProtocolViolation(f"validation AP mismatch: {stem}/C={c_value}")
                        validation_aps.append((ap_value, float(row["C"])))
                    best_ap = max(value for value, _ in validation_aps)
                    expected_c = min(c for value, c in validation_aps if value == best_ap)
                    if float(artifact["selected_C"]) != expected_c:
                        raise ProtocolViolation(f"selected C is not pooled-validation winner: {stem}")
                    def canonical_array_sha(value: np.ndarray) -> str:
                        return hashlib.sha256(str(value.dtype).encode() + str(value.shape).encode() + np.ascontiguousarray(value).tobytes()).hexdigest()
                    if canonical_array_sha(coef) != artifact["coef_sha256"] or canonical_array_sha(intercept) != artifact["intercept_sha256"]:
                        raise ProtocolViolation(f"coefficient/intercept hash mismatch: {stem}")
                    observed_ap = _ap(labels, prediction)
                    test_ap_by_seed[seed][name] = observed_ap
                    reported_ap = results.get("test_ap", {}).get(str(seed), {}).get(name, {}).get("ap", float("nan"))
                    if not _close(observed_ap, reported_ap):
                        raise ProtocolViolation(f"reported test AP differs from primitive AP: {stem}")
                    pooled_ap_by_arm[name][:, seed_index] = _source_pooled_ap(labels, prediction, keys)
                    scenario_ap_by_arm[name][:, seed_index, :] = _source_scenario_ap(labels, prediction, keys)
                except (KeyError, OSError, ValueError, ProtocolViolation) as exc:
                    discrepancies.append(f"{stem}: {exc}")

    cohort_checks = []
    for seed in DETECTOR_SEEDS:
        for arm in ARMS:
            x_art = all_artifacts.get(f"seed{seed}_{arm}_xlstm")
            l_art = all_artifacts.get(f"seed{seed}_{arm}_lstm")
            if not x_art or not l_art:
                discrepancies.append(f"missing paired artifacts {seed}/{arm}")
                continue
            try:
                x_keys = json.loads((ROOT / x_art["keys"]).read_text())
                l_keys = json.loads((ROOT / l_art["keys"]).read_text())
                digest = assert_same_row_order(x_keys, l_keys)
                x_labels = np.load(ROOT / x_art["labels"], allow_pickle=False)
                l_labels = np.load(ROOT / l_art["labels"], allow_pickle=False)
                if not np.array_equal(x_labels, l_labels):
                    raise ProtocolViolation("paired label arrays differ")
                cohort_checks.append({"seed": seed, "arm": arm, "status": "PASS", "row_key_sha256": digest})
            except (OSError, ValueError, ProtocolViolation) as exc:
                discrepancies.append(f"paired cohort mismatch {seed}/{arm}: {exc}")
        # H2/B/C compare different feature arms within each backbone.  Their
        # ordered test cohorts must be identical, not merely x/L paired within
        # one arm.
        for architecture in ARCHITECTURES:
            reference_art = all_artifacts.get(f"seed{seed}_history14_{architecture}")
            if reference_art is None:
                continue
            reference_keys = json.loads((ROOT / reference_art["keys"]).read_text())
            reference_labels = np.load(ROOT / reference_art["labels"], allow_pickle=False)
            for arm in ARMS[1:]:
                other_art = all_artifacts.get(f"seed{seed}_{arm}_{architecture}")
                if other_art is None:
                    discrepancies.append(f"missing within-backbone cohort {seed}/{arm}/{architecture}")
                    continue
                other_keys = json.loads((ROOT / other_art["keys"]).read_text())
                other_labels = np.load(ROOT / other_art["labels"], allow_pickle=False)
                try:
                    assert_same_row_order(reference_keys, other_keys)
                    if not np.array_equal(reference_labels, other_labels):
                        raise ProtocolViolation("within-backbone arm labels differ")
                except ProtocolViolation as exc:
                    discrepancies.append(f"within-backbone cohort mismatch {seed}/{architecture}/{arm}: {exc}")

    for seed in DETECTOR_SEEDS:
        control = probes.get("shared_control_artifacts", {}).get(str(seed))
        if not control:
            discrepancies.append(f"missing shared CANDI control artifact {seed}")
            continue
        try:
            x_control = _load_array(control["x_path"], control["x_sha256"])
            l_control = _load_array(control["l_path"], control["l_sha256"])
            if x_control.shape != tuple(control["shape"]) or x_control.ndim != 2 or x_control.shape[1] != 14 or not np.array_equal(x_control, l_control, equal_nan=True):
                raise ProtocolViolation("xLSTM/LSTM shared CANDI history values differ")
        except (OSError, ValueError, ProtocolViolation) as exc:
            discrepancies.append(f"shared CANDI control {seed}: {exc}")

    def get(name: str) -> np.ndarray:
        value = pooled_ap_by_arm.get(name)
        if value is None or not np.isfinite(value).all():
            raise ProtocolViolation(f"missing pooled AP arm {name}")
        return value
    reconstructed = {
        "h2": get("history_plus_combined248_xlstm") - get("history14_xlstm"),
        "h3a_a": get("combined234_xlstm") - get("combined234_lstm"),
        "h3a_b": (get("history_plus_combined248_xlstm") - get("history14_xlstm")) - (get("history_plus_combined248_lstm") - get("history14_lstm")),
        "h3a_c": (get("candi_history_plus_combined248_xlstm") - get("candi_history14_xlstm")) - (get("candi_history_plus_combined248_lstm") - get("candi_history14_lstm")),
    }
    reconstructed_scenario = {
        "h2": scenario_ap_by_arm["history_plus_combined248_xlstm"] - scenario_ap_by_arm["history14_xlstm"],
        "h3a_a": scenario_ap_by_arm["combined234_xlstm"] - scenario_ap_by_arm["combined234_lstm"],
        "h3a_b": (scenario_ap_by_arm["history_plus_combined248_xlstm"] - scenario_ap_by_arm["history14_xlstm"]) - (scenario_ap_by_arm["history_plus_combined248_lstm"] - scenario_ap_by_arm["history14_lstm"]),
        "h3a_c": (scenario_ap_by_arm["candi_history_plus_combined248_xlstm"] - scenario_ap_by_arm["candi_history14_xlstm"]) - (scenario_ap_by_arm["candi_history_plus_combined248_lstm"] - scenario_ap_by_arm["candi_history14_lstm"]),
    }
    semantic_audit = _audit_semantic_control(probes, discrepancies)
    robustness_audit = _audit_robustness(probes, results, discrepancies)
    delta_arrays = {}
    for name in ("h2", "h3a_a", "h3a_b", "h3a_c"):
        artifact = probes.get("delta_artifacts", {}).get(name)
        if not artifact:
            discrepancies.append(f"missing delta artifact {name}")
            continue
        try:
            path = ROOT / artifact["path"]
            if _sha(path) != artifact["sha256"]:
                raise ProtocolViolation("delta hash mismatch")
            saved = np.load(path, allow_pickle=False)
            if saved.shape != (10, 5) or not np.array_equal(saved, reconstructed[name]):
                raise ProtocolViolation("saved delta differs from independently reconstructed AP effects")
            delta_arrays[name] = reconstructed[name]
            saved_scenario = np.asarray(results.get("scenario_deltas", {}).get(name, {}).get("values", []), dtype=np.float64)
            if saved_scenario.shape != (10, 5, 4) or not np.array_equal(saved_scenario, reconstructed_scenario[name]):
                raise ProtocolViolation(f"scenario delta mismatch {name}")
        except (OSError, ValueError, ProtocolViolation) as exc:
            discrepancies.append(f"delta {name}: {exc}")

    independent_stats: dict[str, Any] = {}
    if len(delta_arrays) == 4:
        pvalues = []
        for name in ("h2", "h3a_a", "h3a_b", "h3a_c"):
            summary = _bootstrap_primary(delta_arrays[name])
            summary["raw_p"] = _sign_flip_primary(delta_arrays[name])
            independent_stats[name] = summary
            pvalues.append(summary["raw_p"])
        for name, value in zip(("h2", "h3a_a", "h3a_b", "h3a_c"), _holm(pvalues)):
            independent_stats[name]["holm_adjusted_p"] = value
        saved_stats = statistics.get("comparisons", {})
        for name, summary in independent_stats.items():
            saved = saved_stats.get(name, {})
            for field in ("mean", "raw_p", "holm_adjusted_p"):
                if not _close(summary[field], saved.get(field, float("nan"))):
                    discrepancies.append(f"statistic mismatch {name}/{field}")
            if not all(_close(summary["ci95"][idx], saved.get("ci95", [float("nan"), float("nan")])[idx]) for idx in (0, 1)):
                discrepancies.append(f"bootstrap CI mismatch {name}")
        counts = {name: {"positive_detector_seeds": int((delta_arrays[name].mean(axis=0) > 0).sum()), "positive_scenarios": int((reconstructed_scenario[name].mean(axis=(0, 1)) > 0).sum())} for name in delta_arrays}
        robustness_support = robustness_audit.get("h2_status") == "PASS"
        h3_robustness_support = robustness_audit.get("h3a_status_if_primary_h2_go") == "PASS"
        if bool(decision.get("h2_robustness_support_used", False)) != robustness_support:
            discrepancies.append("H2 decision did not use independently reconstructed robustness support flag")
        if bool(decision.get("h3a_robustness_support_used", False)) != h3_robustness_support:
            discrepancies.append("H3a decision did not use independently reconstructed robustness support flag")
        h2_raw = independent_stats["h2"]
        h2_expected = "GO" if _independent_h2(h2_raw["mean"], h2_raw["ci95"][0], h2_raw["holm_adjusted_p"], counts["h2"]["positive_detector_seeds"], counts["h2"]["positive_scenarios"], robustness_support) else "STOP"
        if decision.get("H2") != h2_expected:
            discrepancies.append("H2 Boolean decision mismatch")
        if h2_expected == "GO":
            h3_repro = all(counts[name]["positive_detector_seeds"] >= 4 and counts[name]["positive_scenarios"] >= 3 for name in ("h3a_a", "h3a_b", "h3a_c"))
            h3_args = []
            for name in ("h3a_a", "h3a_b", "h3a_c"):
                h3_args.append({"mean": independent_stats[name]["mean"], "ci_lower": independent_stats[name]["ci95"][0], "p": independent_stats[name]["holm_adjusted_p"]})
            h3_expected = "GO" if _independent_h3(True, h3_args[0], h3_args[1], h3_args[2], h3_repro, h3_robustness_support) else "STOP"
        else:
            h3_expected = "NOT_ELIGIBLE"
        if decision.get("H3a") != h3_expected:
            discrepancies.append("H3a Boolean decision mismatch")
    verdict = "PASS_SCIENTIFIC_AUDIT" if not discrepancies else "STOP_RESULT_INVALID"
    return {
        "verdict": verdict,
        "G1_PRELABEL_SEAL_COMMIT": prelabel_commit,
        "execution_commit": execution.get("execution_commit"),
        "files_audited": required,
        "recomputed_ap": {str(seed): values for seed, values in test_ap_by_seed.items()},
        "recomputed_primary_effects": {name: value.tolist() for name, value in reconstructed.items()},
        "independent_statistics": independent_stats,
        "semantic_nonidentifiability_audit": semantic_audit,
        "duration_severity_robustness_audit": robustness_audit,
        "cohort_checks": cohort_checks,
        "execution_forensics": {
            "ledger_path": ledger_rel,
            "record_count": len(ledger_records),
            "events": {event: sum(1 for record in ledger_records if record.get("event") == event) for event in sorted(set(str(record.get("event")) for record in ledger_records))},
            "terminal_complete": bool(ledger_records and ledger_records[-1].get("event") == "process_complete"),
        },
        "discrepancies": discrepancies,
        "outcome_exposure": "real labels/test AP were observed for this post-run audit",
        "bootstrap_seed": BOOTSTRAP_SEED,
        "sign_flip_seed": 902,
        "holm_family_size": HOLM_FAMILY_SIZE,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prelabel-seal", required=True)
    args = parser.parse_args()
    try:
        result = audit(args.output_dir, args.prelabel_seal)
    except (ProtocolViolation, FileNotFoundError, KeyError, ValueError) as exc:
        result = {"verdict": "STOP_RESULT_UNRESOLVED", "discrepancies": [repr(exc)], "G1_PRELABEL_SEAL_COMMIT": args.prelabel_seal}
    report_dir = ROOT / "reports" / "phase_g1"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "g1_self_review_postrun.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    lines = ["# G1 post-run scientific self-review", "", f"Verdict: {result['verdict']}", "", f"G1_PRELABEL_SEAL_COMMIT: {result.get('G1_PRELABEL_SEAL_COMMIT')}", "", "Discrepancies:"]
    lines.extend(f"- {item}" for item in result.get("discrepancies", []))
    (report_dir / "g1_self_review_postrun.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"verdict": result["verdict"], "discrepancies": result.get("discrepancies", [])}, indent=2))
    if result["verdict"] != "PASS_SCIENTIFIC_AUDIT":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
