"""Metric-free tests for the sealed-cache continuation boundary."""
from __future__ import annotations

import ast
import sys
from contextlib import contextmanager
from pathlib import Path

try:
    import pytest
except ImportError:  # pragma: no cover - fallback for the minimal audit venv
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

import phase_g1_continue_from_cache as continuation  # noqa: E402


def _valid_review():
    implementation = "a" * 40
    seal = "b" * 40
    hashes = {path: "1" * 64 for path in continuation.CONTINUATION_REVIEWED_EXECUTABLES}
    return implementation, seal, hashes, {
        "verdict": continuation.CONTINUATION_REVIEW_VERDICT,
        "reviewed_commit": implementation,
        "reviewed_executable_sha256": hashes,
    }


def test_correct_cardinality_includes_scenarios_and_conditions():
    assert continuation.expected_primary_ref_cardinality("train")["per_arm_architecture"] == 200
    assert continuation.expected_primary_ref_cardinality("validation")["per_arm_architecture"] == 100
    assert continuation.expected_primary_ref_cardinality("test")["per_arm_architecture"] == 200
    assert continuation.expected_primary_ref_cardinality("train")["total"] == 3200
    assert continuation.expected_primary_ref_cardinality("validation")["total"] == 1600
    assert continuation.expected_primary_ref_cardinality("test")["total"] == 3200


def test_old_buggy_cardinality_formula_is_rejected_by_frozen_counts():
    for fold, sources in (("train", 10), ("validation", 5), ("test", 10)):
        old = len(continuation.audit.ARMS) * len(continuation.audit.ARCHITECTURES) * sources
        corrected = continuation.expected_primary_ref_cardinality(fold)["total"]
        assert corrected != old
        assert corrected > old


def test_exact_review_seal_values_pass():
    implementation, seal, hashes, review = _valid_review()
    continuation._validate_continuation_review_values(
        seal,
        seal,
        review,
        hashes,
        hashes,
        implementation_is_ancestor=True,
        committed_review_matches=True,
    )


def test_modified_continuation_file_is_rejected():
    _implementation, seal, hashes, review = _valid_review()
    changed = dict(hashes, **{"scripts/phase_g1_continue_from_cache.py": "2" * 64})
    with pytest.raises(continuation.ContinuationFailure):
        continuation._validate_continuation_review_values(
            seal, seal, review, changed, hashes,
            implementation_is_ancestor=True, committed_review_matches=True,
        )


def test_modified_cache_audit_file_is_rejected():
    _implementation, seal, hashes, review = _valid_review()
    changed = dict(hashes, **{"scripts/phase_g1_cache_audit.py": "2" * 64})
    with pytest.raises(continuation.ContinuationFailure):
        continuation._validate_continuation_review_values(
            seal, seal, review, changed, hashes,
            implementation_is_ancestor=True, committed_review_matches=True,
        )


def test_unreviewed_descendant_is_rejected():
    _implementation, seal, hashes, review = _valid_review()
    with pytest.raises(continuation.ContinuationFailure):
        continuation._validate_continuation_review_values(
            seal, seal, review, hashes, hashes,
            implementation_is_ancestor=False, committed_review_matches=True,
        )


def test_wrong_or_missing_continuation_seal_is_rejected():
    implementation, seal, hashes, review = _valid_review()
    for supplied in (None, "0" * 40, "not-a-sha"):
        with pytest.raises(continuation.ContinuationFailure):
            continuation._validate_continuation_review_values(
                supplied, seal, review, hashes, hashes,
                implementation_is_ancestor=True, committed_review_matches=True,
            )


def test_review_report_byte_mutation_is_rejected():
    _implementation, seal, hashes, review = _valid_review()
    with pytest.raises(continuation.ContinuationFailure):
        continuation._validate_continuation_review_values(
            seal, seal, review, hashes, hashes,
            implementation_is_ancestor=True, committed_review_matches=False,
        )


def test_review_hash_set_cannot_be_widened_or_shrunk():
    _implementation, seal, hashes, review = _valid_review()
    for altered in (
        dict(hashes, extra_file="1" * 64),
        {key: value for key, value in hashes.items() if key != "scripts/phase_g1_run.py"},
    ):
        bad_review = dict(review, reviewed_executable_sha256=altered)
        with pytest.raises(continuation.ContinuationFailure):
            continuation._validate_continuation_review_values(
                seal, seal, bad_review, hashes, hashes,
                implementation_is_ancestor=True, committed_review_matches=True,
            )


def test_output_outside_root_is_rejected_before_metric_path():
    with pytest.raises(continuation.ContinuationFailure):
        continuation._canonical_continuation_output_dir(Path("/tmp/g1-outside-root"))
    with pytest.raises(continuation.ContinuationFailure):
        continuation._canonical_continuation_output_dir(continuation.ROOT)
    with pytest.raises(continuation.ContinuationFailure):
        continuation._canonical_continuation_output_dir(continuation.audit.CACHE_DIR / "nested")


def test_cli_requires_explicit_continuation_seal():
    old_argv = sys.argv
    try:
        sys.argv = ["phase_g1_continue_from_cache.py", "--allow-cache-continuation"]
        with pytest.raises(SystemExit):
            continuation.main()
    finally:
        sys.argv = old_argv


def test_dry_run_source_has_no_scientific_metric_calls():
    source = (ROOT / "scripts" / "phase_g1_continuation_dry_run.py").read_text()
    tree = ast.parse(source)
    forbidden = {
        "fit_probe_pooled", "compute_arm_ap", "build_confirmatory_statistics",
        "average_precision_score", "roc_auc_score", "hierarchical_bootstrap",
        "source_cluster_sign_flip", "holm_adjust",
    }
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ""
            if name in forbidden:
                calls.append(name)
    assert calls == []
    assert "stopped_before_scientific_metrics" in source


def test_continuation_source_keeps_probe_path_after_guard_only():
    source = (ROOT / "scripts" / "phase_g1_continue_from_cache.py").read_text()
    guard_pos = source.index("require_continuation_review_seal(continuation_seal)")
    inventory_pos = source.index("_load_verified_inventory()", guard_pos)
    assert guard_pos < inventory_pos
    assert "--continuation-seal" in source
