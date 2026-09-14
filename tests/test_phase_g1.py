"""Bounded, label-blind adversarial tests for the Phase-G1 contract.

These tests intentionally exercise only deterministic fixtures and protocol
guards.  They do not load Phase-G truth, fit probes, compute AP/AUROC, or run
model training.
"""
from __future__ import annotations

import ast
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
try:
    import pytest
except ImportError:  # the sealed research venv is intentionally minimal
    class _PytestFallback:
        @staticmethod
        @contextmanager
        def raises(expected):
            try:
                yield
            except expected:
                return
            raise AssertionError(f"expected {expected.__name__}")
    pytest = _PytestFallback()


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import phase_g1_core as core  # noqa: E402


def _keys(source: int = 3000, n: int = 12):
    return core.make_row_keys(11, source, "abrupt", "spike", np.arange(63, 63 + n))


def _groups(n: int = 64):
    scores = np.linspace(0.1, 1.0, n, dtype=np.float64)
    base = np.arange(n * 18, dtype=np.float64).reshape(n, 18) / 100.0
    return core.build_feature_groups(scores, base)


def test_frozen_dimensions_and_causal_expansion():
    groups = _groups()
    assert {name: value.shape[1] for name, value in groups.items()} == core.EXPECTED_DIMENSIONS
    assert np.isnan(groups["history14"][:1]).any()
    assert np.isnan(groups["combined234"][:31]).any()

    scores = np.linspace(0.1, 1.0, 64)
    base = np.arange(64 * 18, dtype=np.float64).reshape(64, 18)
    future_scores = scores.copy()
    future_base = base.copy()
    future_scores[40:] = -future_scores[40:]
    future_base[40:] = 999.0
    assert np.array_equal(core.history14(scores)[:40], core.history14(future_scores)[:40], equal_nan=True)
    assert np.array_equal(core.expand_internal234(base)[:40], core.expand_internal234(future_base)[:40], equal_nan=True)


def test_source_folds_are_disjoint_and_shifted_rows_are_pooled():
    core.assert_source_fold_separation()
    for fold, sources in (("train", core.TRAIN_SOURCES), ("validation", core.VALIDATION_SOURCES), ("test", core.TEST_SOURCES)):
        core.assert_pooled_shifted_rows(np.repeat(sources[0], 4), core.SHIFTED_SCENARIOS, fold)


def test_stage_a_source_contains_no_metric_or_label_execution():
    source = (ROOT / "scripts" / "phase_g1_stage_a.py").read_text()
    tree = ast.parse(source)
    forbidden = {
        "average_precision_score", "roc_auc_score", "fit_probe_pooled",
        "hierarchical_bootstrap", "source_cluster_sign_flip",
    }
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ""
            if name in forbidden:
                calls.append(name)
    assert calls == []
    assert "real_phase_g_labels_read" in source
    assert "ap_or_auroc_computed" in source


def test_permuted_test_row_order_is_rejected():
    with pytest.raises(core.ProtocolViolation):
        core.assert_same_row_order(_keys(), list(reversed(_keys())))


def test_removed_warmup_valid_row_is_rejected():
    left = _keys()
    with pytest.raises(core.ProtocolViolation):
        core.assert_same_row_order(left, left[:-1])


def test_scaler_validation_inclusion_is_rejected():
    x = np.ones((2, 3), dtype=np.float64)
    with pytest.raises(core.ProtocolViolation):
        core.fit_scaler_train_only(x, np.array([1000, 2000]))


def test_shifted_candi_timestamp_is_rejected():
    ts = np.arange(63, 75)
    shifted = ts.copy()
    shifted[4] += 1
    with pytest.raises(core.ProtocolViolation):
        core.assert_candi_alignment(ts, shifted)


def test_different_shared_candi_tensor_is_rejected():
    groups = _groups()
    keys = _keys(n=64)
    with pytest.raises(core.ProtocolViolation):
        core.assert_shared_control(groups["history14"], groups["history14"] + 1.0, keys, keys)


def test_reversed_confirmatory_subtraction_is_rejected():
    with pytest.raises(core.ProtocolViolation):
        core.assert_difference_formula("H2", 0.7, 0.4, 0.4 - 0.7)
    # A genuinely negative effect is a valid scientific result and must not be
    # rejected merely because it is negative.
    core.assert_difference_formula("negative_effect", 0.4, 0.7, -0.3)


def test_fifth_holm_member_is_rejected():
    with pytest.raises(core.ProtocolViolation):
        core.assert_family_names(("H2", "H3a-A", "H3a-B", "H3a-C", "extra"))
    with pytest.raises(core.ProtocolViolation):
        core.holm_adjust([0.01, 0.02, 0.03, 0.04, 0.05])


def test_per_scenario_c_selection_is_rejected():
    with pytest.raises(core.ProtocolViolation):
        core.reject_per_scenario_selection("abrupt")


def test_labels_cannot_be_passed_to_observation_extractor():
    with pytest.raises((core.ProtocolViolation, TypeError)):
        core.extract_backbone_rows(
            None, "lstm", np.zeros((64, 8), dtype=np.float32), {}, np.arange(63),
            labels=np.zeros(1, dtype=np.int8),
        )
    core.assert_observation_only_api(core.extract_backbone_rows)


def test_reordered_source_realization_is_rejected():
    with pytest.raises(core.ProtocolViolation):
        core.assert_same_row_order(_keys(3000), _keys(3001))


def test_candi_history_and_feature_extraction_do_not_accept_truth_arguments():
    core.assert_observation_only_api(core.extract_backbone_rows)
    assert "labels" not in core.inspect.signature(core.extract_backbone_rows).parameters
    assert "metadata" not in core.inspect.signature(core.extract_backbone_rows).parameters


def test_no_native_predict_step_in_common_path():
    core.ensure_no_native_predict_path()


def test_all_g1_entrypoints_import_without_label_execution():
    for module_name in (
        "phase_g1_pipeline",
        "phase_g1_run",
        "phase_g1_stage_a",
        "phase_g1_adversarial",
        "phase_g1_postrun_audit",
    ):
        __import__(module_name)


def test_review_provenance_derives_enclosing_seal_without_self_reference():
    pipeline = __import__("phase_g1_pipeline")
    implementation = "a" * 40
    review_seal = "b" * 40
    review = {
        "verdict": "PASS_FOR_LABEL_ACCESS",
        "reviewed_commit": implementation,
        "implementation_commit": implementation,
    }
    assert pipeline._validate_review_provenance(review, review_seal) == implementation
    with pytest.raises(core.ProtocolViolation):
        pipeline._validate_review_provenance(dict(review, review_commit=review_seal), review_seal)
    with pytest.raises(core.ProtocolViolation):
        pipeline._validate_review_provenance({"implementation_commit": implementation}, review_seal)


def test_primary_statistics_require_source_pooled_shape():
    with pytest.raises(core.ProtocolViolation):
        __import__("phase_g1_pipeline").build_confirmatory_statistics(
            {name: np.zeros((10, 5, 4), dtype=np.float64) for name in ("h2", "h3a_a", "h3a_b", "h3a_c")}
        )


def test_resolved_duration_protocol_allows_label_access():
    assert core.assert_duration_severity_protocol()["status"] == "PASS"


def test_g11_semantic_control_cannot_support_h2():
    with pytest.raises(core.ProtocolViolation):
        core.require_supportive_analysis_kind("semantic_nonidentifiability_control")


def test_g11_duration_stratum_c_refit_is_rejected():
    with pytest.raises(core.ProtocolViolation):
        core.reject_stratum_refit("duration=16")


def test_g11_severity_stratum_scaler_refit_is_rejected():
    with pytest.raises(core.ProtocolViolation):
        core.reject_stratum_scaler_fit("severity=2")


def test_g11_unsupported_duration_merge_is_rejected():
    with pytest.raises(core.ProtocolViolation):
        core.assert_fixed_robustness_strata("duration", (1, 16, 256))


def test_g11_duration_severity_metadata_is_rejected_by_extractor_api():
    def extractor(observations, duration):
        return observations

    with pytest.raises(core.ProtocolViolation):
        core.assert_observation_only_api(extractor)


def test_g11_semantic_truth_change_keeps_observation_features_identical():
    observations = np.arange(16, dtype=np.float32).reshape(2, 8)
    features = np.arange(6, dtype=np.float64).reshape(2, 3)
    predictions = np.asarray([0.2, 0.8], dtype=np.float64)
    anomaly_truth = np.ones(2, dtype=np.int8)
    legitimate_truth = np.zeros(2, dtype=np.int8)
    assert not np.array_equal(anomaly_truth, legitimate_truth)
    result = core.assert_semantic_nonidentifiability(observations, observations.copy(), features, features.copy(), predictions, predictions.copy())
    assert result["features_invariant"] and result["predictions_invariant"]


def test_g11_duration_stratum_row_cohort_mismatch_is_rejected():
    left = _keys(n=4)
    right = _keys(n=4)
    right[-1] = dict(right[-1], timestamp=right[-1]["timestamp"] + 1)
    with pytest.raises(core.ProtocolViolation):
        core.assert_same_row_order(left, right)


def _matching_rows(duration=(16, 16), severity=(1, 1), labels=(1, 0)):
    return {
        "duration": np.asarray(duration, dtype=object),
        "severity": np.asarray(severity, dtype=object),
        "label": np.asarray(labels, dtype=np.int8),
    }


def test_g11_rejects_unresolved_matching_config():
    config = dict(core.G1_CONFIG)
    config["duration_severity_matching"] = {"status": "UNRESOLVED", "label_access_blocked": True}
    with pytest.raises(core.ProtocolViolation):
        core.assert_duration_severity_protocol(config)


def test_g11_rejects_strata_drift():
    config = dict(core.G1_CONFIG)
    config["duration_severity_matching"] = dict(config["duration_severity_matching"])
    config["duration_severity_matching"]["duration_strata"] = [1, 32, 64, 256]
    with pytest.raises(core.ProtocolViolation):
        core.assert_duration_severity_protocol(config)


def test_g11_rejects_missing_required_exclusion():
    config = dict(core.G1_CONFIG)
    config["duration_severity_matching"] = dict(config["duration_severity_matching"])
    config["duration_severity_matching"]["exclude_mixed_windows"] = False
    with pytest.raises(core.ProtocolViolation):
        core.assert_duration_severity_protocol(config)


def test_g11_rejects_out_of_stratum_duration_or_severity():
    with pytest.raises(core.ProtocolViolation):
        core.duration_severity_match_status(_matching_rows(duration=(17, 17)))
    with pytest.raises(core.ProtocolViolation):
        core.duration_severity_match_status(_matching_rows(severity=(4, 4)))


def test_g11_rejects_nonbinary_matching_label():
    with pytest.raises(core.ProtocolViolation):
        core.duration_severity_match_status(_matching_rows(labels=(1, 2)))


def test_g11_reports_insufficient_support_without_merging_bins():
    result = core.duration_severity_match_status(_matching_rows(duration=(16,), severity=(1,), labels=(1,)))
    assert result["status"] == "N/A"
    assert result["usable_bins"] == {}


def test_g11_accepts_one_fixed_supported_bin():
    result = core.duration_severity_match_status(_matching_rows(duration=(16, 16), severity=(1, 1), labels=(1, 0)))
    assert result["status"] == "PASS"
    assert result["usable_bins"] == {"duration=16|severity=1": {"positive": 1, "negative": 1}}
