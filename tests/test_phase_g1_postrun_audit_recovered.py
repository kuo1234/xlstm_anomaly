"""Metric-free adversarial tests for the recovered Phase-G1 auditor.

The fixtures below are deliberately synthetic metadata/arrays.  They exercise
the fail-closed lineage and primitive-recomputation guards without opening the
118 GB cache or any recovered scientific result.
"""
from __future__ import annotations

import ast
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np

try:
    import pytest
except ImportError:  # pragma: no cover - minimal audit environment fallback
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

import phase_g1_postrun_audit_recovered as recovered  # noqa: E402
from phase_g1_core import ProtocolViolation, object_sha  # noqa: E402


def _scientific_hashes(value: str = "a" * 64) -> dict[str, str]:
    return {relative: value for relative in recovered.SCIENTIFIC_PRELABEL_FILES}


def _lineage_fixture():
    seal = "b" * 40
    implementation = recovered.REVIEWED_CONTINUATION_IMPLEMENTATION
    hashes = {relative: "1" * 64 for relative in recovered.CONTINUATION_REVIEWED_EXECUTABLES}
    review = {
        "verdict": recovered.CONTINUATION_REVIEW_VERDICT,
        "reviewed_commit": implementation,
        "reviewed_executable_sha256": hashes,
    }
    execution = {
        "status": "LABELLED_EXECUTION_RECOVERED_FROM_VERIFIED_CACHE",
        "prelabel_seal_commit": recovered.ORIGINAL_PRELABEL_SEAL,
        "execution_commit": seal,
    }
    scientific = _scientific_hashes()
    return {
        "execution": execution,
        "seal": seal,
        "review": review,
        "hashes": hashes,
        "scientific": scientific,
        "implementation_hashes": dict(hashes),
    }


def _validate(fixture, **changes):
    values = {
        "execution": fixture["execution"],
        "continuation_seal": fixture["seal"],
        "current_head": fixture["seal"],
        "review": fixture["review"],
        "current_executable_sha256": fixture["hashes"],
        "implementation_executable_sha256": fixture["implementation_hashes"],
        "implementation_is_ancestor": True,
        "code_sha256": fixture["hashes"]["scripts/phase_g1_continue_from_cache.py"],
        "expected_code_sha256": fixture["hashes"]["scripts/phase_g1_continue_from_cache.py"],
        "runner_sha256": fixture["hashes"]["scripts/phase_g1_run.py"],
        "expected_runner_sha256": fixture["hashes"]["scripts/phase_g1_run.py"],
        "scientific_file_sha256": fixture["scientific"],
        "expected_scientific_file_sha256": fixture["scientific"],
        "duration_status": "RESOLVED",
    }
    values.update(changes)
    recovered._validate_recovered_lineage_values(**values)


def _cache_fixture():
    paths = {
        str(recovered.CACHE_AUDIT_PATH.relative_to(ROOT)): recovered.CACHE_AUDIT_SHA256,
        str(recovered.INVENTORY_PATH.relative_to(ROOT)): recovered.INVENTORY_SHA256,
        str(recovered.INCIDENT_PATH.relative_to(ROOT)): recovered.INCIDENT_SHA256,
        str(recovered.AUTH_PATH.relative_to(ROOT)): recovered.AUTH_SHA256,
        str(recovered.PATCH_AUDIT_PATH.relative_to(ROOT)): recovered.PATCH_AUDIT_SHA256,
    }
    cache_audit = {
        "status": "PASS_CACHE_REUSABLE",
        "labels_or_metrics_accessed": False,
        "probe_fit": False,
        "ap_or_auroc": False,
        "cache_integrity": {"status": "PASS", "labels_or_outcome_summary_emitted": False},
        "replay": {"status": "PASS"},
    }
    authorization = {
        "authorization_type": "G1-R1_POST_LABEL_REPORTING_PATCH",
        "cache_use_authorized": False,
        "probe_or_metric_execution_authorized": False,
        "original_prelabel_review_seal": recovered.ORIGINAL_PRELABEL_SEAL,
        "reporting_patch_commit": recovered.REPORTING_PATCH,
        "quarantined_execution_ledger_sha256": recovered.LEDGER_SHA256,
    }
    patch_audit = {"status": "PASS"}
    return paths, cache_audit, authorization, patch_audit


def test_normal_stage_c_lineage_is_not_accepted_as_recovered():
    fixture = _lineage_fixture()
    normal = dict(fixture["execution"], status="LABELLED_EXECUTION_COMPLETE")
    with pytest.raises(ProtocolViolation):
        _validate(fixture, execution=normal)


def test_wrong_original_prelabel_seal_is_rejected():
    fixture = _lineage_fixture()
    bad = dict(fixture["execution"], prelabel_seal_commit="c" * 40)
    with pytest.raises(ProtocolViolation):
        _validate(fixture, execution=bad)


def test_wrong_continuation_seal_and_manifest_commit_are_rejected():
    fixture = _lineage_fixture()
    with pytest.raises(ProtocolViolation):
        _validate(fixture, continuation_seal="c" * 40, current_head="c" * 40)
    bad = dict(fixture["execution"], execution_commit="c" * 40)
    with pytest.raises(ProtocolViolation):
        _validate(fixture, execution=bad)


def test_current_head_and_reviewed_implementation_lineage_are_rejected():
    fixture = _lineage_fixture()
    with pytest.raises(ProtocolViolation):
        _validate(fixture, current_head="c" * 40)
    with pytest.raises(ProtocolViolation):
        _validate(fixture, implementation_is_ancestor=False)


def test_continuation_code_and_runner_hash_drift_are_rejected():
    fixture = _lineage_fixture()
    with pytest.raises(ProtocolViolation):
        _validate(fixture, code_sha256="2" * 64)
    with pytest.raises(ProtocolViolation):
        _validate(fixture, runner_sha256="2" * 64)


def test_scientific_file_hash_and_duration_drift_are_rejected():
    fixture = _lineage_fixture()
    bad_scientific = dict(fixture["scientific"], **{"configs/phase_g1.json": "2" * 64})
    with pytest.raises(ProtocolViolation):
        _validate(fixture, scientific_file_sha256=bad_scientific)
    with pytest.raises(ProtocolViolation):
        _validate(fixture, duration_status="UNRESOLVED")


def test_cache_audit_and_inventory_hash_mismatch_are_rejected():
    fixture = _lineage_fixture()
    paths, cache_audit, authorization, patch_audit = _cache_fixture()
    recovered._validate_cache_provenance_values(paths, cache_audit, authorization, patch_audit, primary_cache_read_only=True)
    for relative in (str(recovered.CACHE_AUDIT_PATH.relative_to(ROOT)), str(recovered.INVENTORY_PATH.relative_to(ROOT))):
        bad = dict(paths, **{relative: "2" * 64})
        with pytest.raises(ProtocolViolation):
            recovered._validate_cache_provenance_values(bad, cache_audit, authorization, patch_audit, primary_cache_read_only=True)


def test_cache_read_only_and_authorization_scope_are_hard_guards():
    paths, cache_audit, authorization, patch_audit = _cache_fixture()
    with pytest.raises(ProtocolViolation):
        recovered._validate_cache_provenance_values(paths, cache_audit, authorization, patch_audit, primary_cache_read_only=False)
    with pytest.raises(ProtocolViolation):
        recovered._validate_cache_provenance_values(paths, cache_audit, dict(authorization, reporting_patch_commit="c" * 40), patch_audit, primary_cache_read_only=True)


def test_tampered_prediction_primitive_is_detected():
    fit = {
        "scaler": {"mean": [0.0], "scale": [1.0]},
        "coef": [[1.0]],
        "intercept": [0.0],
    }
    features = np.asarray([[1.0], [2.0]], dtype=np.float64)
    expected = np.asarray([0.0, 0.0], dtype=np.float64)
    with pytest.raises(ProtocolViolation):
        recovered.ordinary._frozen_probe_prediction({"artifacts": {"stem": fit}}, "stem", features, expected)


def test_altered_decision_summary_is_detected():
    with pytest.raises(ProtocolViolation):
        recovered._assert_close_reported("AP summary", 0.8, 0.7)
    with pytest.raises(ProtocolViolation):
        recovered._assert_close_reported("bootstrap statistic", 0.1, 0.2)
    with pytest.raises(ProtocolViolation):
        recovered._assert_decision_matches("H2", "GO", "STOP")
    recovered._assert_decision_matches("H2", "GO", "GO")


def test_old_auditor_top_level_is_not_called_and_cache_is_not_mutated():
    source = (ROOT / "scripts" / "phase_g1_postrun_audit_recovered.py").read_text()
    tree = ast.parse(source)
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "ordinary" and node.func.attr == "audit":
                calls.append(node.lineno)
    assert calls == []
    assert "continue_from_cache(" not in source
    assert "CACHE_DIR" in source


def test_hash_and_fixture_helpers_are_metric_free():
    fixture = _lineage_fixture()
    assert fixture["execution"]["status"].startswith("LABELLED_EXECUTION_RECOVERED")
    assert object_sha({"fit_fold": "train", "mean": [0.0], "scale": [1.0]})
    source = (ROOT / "scripts" / "phase_g1_postrun_audit_recovered.py").read_text()
    # These tests never call the production recovered-audit entrypoint or the
    # continuation; they only exercise pure synthetic guards.
    tree = ast.parse(Path(__file__).read_text())
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    assert not any(isinstance(node.func, ast.Name) and node.func.id in {"audit_recovered", "fit_probe_pooled"} for node in calls)
    assert "CACHE_DIR" in source
