"""Bounded Phase-G1 Stage-A preflight.

This command is intentionally label-blind.  It exercises the executable
feature/row-key contract on deterministic observation-only fixtures and
validates hashes of the already sealed G0/F4 inputs.  It does not instantiate
scientific checkpoints, join evaluator truth, fit a scaler/classifier, or
compute AP/AUROC/statistics.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import numpy as np

from phase_g1_core import (
    C_GRID,
    EXPECTED_DIMENSIONS,
    FIRST_COMMON_TIMESTAMP,
    G1_CONFIG,
    PURGE,
    ProtocolViolation,
    assert_candi_alignment,
    assert_confirmatory_direction,
    assert_difference_formula,
    assert_duration_severity_protocol,
    assert_fixed_robustness_strata,
    assert_semantic_nonidentifiability,
    assert_family_names,
    assert_observation_only_api,
    assert_pooled_shifted_rows,
    assert_same_row_order,
    assert_shared_control,
    assert_source_fold_separation,
    build_feature_groups,
    expand_internal234,
    fit_scaler_train_only,
    history14,
    make_row_keys,
    paired_intersection,
    duration_severity_match_status,
    reject_per_scenario_selection,
    reject_stratum_refit,
    reject_stratum_scaler_fit,
    require_supportive_analysis_kind,
    row_key_hash,
)
from phase_g1_pipeline import SCIENTIFIC_PRELABEL_FILES, require_duration_matching_resolution


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "phase_g1"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expect_failure(name: str, function) -> dict:
    try:
        function()
    except ProtocolViolation:
        return {"name": name, "status": "PASS", "rejected": True}
    except (TypeError, ValueError):
        return {"name": name, "status": "PASS", "rejected": True}
    return {"name": name, "status": "FAIL", "rejected": False}


def _source_no_metric_execution() -> dict:
    """AST guard for Stage-A: no metric/statistic call is executed here."""
    source = (ROOT / "scripts" / "phase_g1_stage_a.py").read_text()
    tree = ast.parse(source)
    forbidden_calls = {
        "average_precision_score",
        "roc_auc_score",
        "metrics",
        "hierarchical_bootstrap",
        "source_cluster_sign_flip",
        "fit_probe_pooled",
    }
    seen = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ""
            if callee in forbidden_calls:
                seen.append(callee)
    return {"status": "PASS" if not seen else "FAIL", "forbidden_calls": seen}


def run() -> dict:
    checks: list[dict] = []
    checks.append({"name": "source_fold_separation", "status": "PASS" if not assert_source_fold_separation() else "FAIL"})
    checks.append({"name": "extractor_observation_only_signature", "status": "PASS", **assert_observation_only_api(__import__("phase_g1_core").extract_backbone_rows)})

    # Deterministic observation-only feature fixture.  No generator truth is
    # constructed and no scientific metric is evaluated.
    rng = np.random.default_rng(1701)
    scores = np.linspace(0.1, 1.0, 96, dtype=np.float64)
    base = rng.normal(size=(96, 18)).astype(np.float64)
    groups = build_feature_groups(scores, base)
    dimension_values = {
        "history14": groups["history14"].shape[1],
        "hidden52": groups["hidden52"].shape[1],
        "gate130": groups["gate130"].shape[1],
        "memory52": groups["memory52"].shape[1],
        "combined234": groups["combined234"].shape[1],
        "history_plus_combined248": groups["history_plus_combined248"].shape[1],
    }
    dimensions_ok = dimension_values == EXPECTED_DIMENSIONS and np.isnan(groups["history14"][0]).any() and np.isnan(groups["combined234"][:31]).any()
    checks.append({
        "name": "sealed_feature_dimensions",
        "status": "PASS" if dimensions_ok else "FAIL",
        "dimensions": {key: list(value.shape) for key, value in groups.items()},
    })

    # Prefix causality: changes after the first 48 decisions cannot alter the
    # earlier history/internal expansions.
    future_scores = scores.copy(); future_scores[48:] = rng.normal(size=len(scores) - 48)
    future_base = base.copy(); future_base[48:] = rng.normal(size=(len(scores) - 48, 18))
    causal_history = np.array_equal(history14(scores)[:48], history14(future_scores)[:48], equal_nan=True)
    causal_internal = np.array_equal(expand_internal234(base)[:48], expand_internal234(future_base)[:48], equal_nan=True)
    checks.append({"name": "prefix_causality", "status": "PASS" if causal_history and causal_internal else "FAIL", "history": causal_history, "internal": causal_internal})

    timestamps = np.arange(FIRST_COMMON_TIMESTAMP, FIRST_COMMON_TIMESTAMP + len(scores), dtype=np.int64)
    keys = make_row_keys(11, 3000, "abrupt", "spike", timestamps)
    assert_same_row_order(keys, list(keys))
    mask, mask2, digest = paired_intersection(keys, list(keys), np.ones(len(keys), bool), np.ones(len(keys), bool))
    checks.append({"name": "paired_row_key_intersection", "status": "PASS" if np.array_equal(mask, mask2) and digest == row_key_hash(keys) else "FAIL", "row_key_sha256": digest})

    # CANDI is checked as a shared, aligned control but no CANDI model is
    # loaded in Stage A.
    assert_candi_alignment(timestamps, timestamps)
    assert_shared_control(groups["history14"], groups["history14"], keys, keys)
    checks.append({"name": "candi_alignment_shared_control", "status": "PASS", "first_timestamp": int(timestamps[0]), "window": 10})

    assert_pooled_shifted_rows(np.repeat(1000, 4), ("abrupt", "gradual", "recurring", "correlation"), "train")
    checks.append({"name": "pooled_four_scenario_contract", "status": "PASS"})
    assert_family_names(("H2", "H3a-A", "H3a-B", "H3a-C"))
    checks.append({"name": "holm_family_size_four", "status": "PASS"})
    checks.append({"name": "c_grid_and_purge", "status": "PASS" if C_GRID == (0.01, 0.1, 1.0, 10.0) and PURGE == 96 else "FAIL"})
    checks.append({"name": "resolved_duration_protocol", "status": "PASS" if assert_duration_severity_protocol()["status"] == "PASS" else "FAIL"})
    amendment_path = ROOT / "reports" / "phase_g1" / "g1_1_duration_severity_amendment.md"
    checks.append({"name": "g11_amendment_documented", "status": "PASS" if amendment_path.exists() else "FAIL", "path": str(amendment_path.relative_to(ROOT))})
    review_path = ROOT / str(G1_CONFIG.get("prelabel_review_path", ""))
    checks.append({"name": "prelabel_review_path_frozen", "status": "PASS" if str(review_path.relative_to(ROOT)) == "reports/phase_g1/g1_self_review_prelabel_v2.json" else "FAIL", "path": str(review_path.relative_to(ROOT))})
    try:
        require_duration_matching_resolution()
    except ProtocolViolation:
        checks.append({"name": "duration_matching_resolution", "status": "FAIL"})
    else:
        checks.append({"name": "duration_matching_resolution", "status": "PASS"})

    runner_source = (ROOT / "scripts" / "phase_g1_run.py").read_text()
    g1_1_contract = all(token in runner_source for token in (
        "duration_severity_stratified_robustness",
        "semantic_nonidentifiability_control",
        "robustness_artifacts",
        "g1_execution_ledger",
    ))
    checks.append({"name": "g11_runner_contract_bound", "status": "PASS" if g1_1_contract else "FAIL"})
    backend_contract = all(token in runner_source for token in (
        "f4.configure()",
        '"cudnn_deterministic": True',
        '"cudnn_benchmark": False',
        '"deterministic_algorithms": False',
        '"matmul_allow_tf32": False',
        '"cudnn_allow_tf32": False',
    ))
    checks.append({"name": "f_v4_backend_configured_before_inference", "status": "PASS" if backend_contract else "FAIL"})
    closure_ok = all((ROOT / relative).exists() for relative in SCIENTIFIC_PRELABEL_FILES)
    checks.append({"name": "scientific_dependency_closure_present", "status": "PASS" if closure_ok else "FAIL", "file_count": len(SCIENTIFIC_PRELABEL_FILES)})
    try:
        import phase_g1_postrun_audit as postrun
        import phase_g1_run as runner
        entrypoints_ok = all(hasattr(runner, name) for name in ("run", "_sha", "_difference_table")) and hasattr(postrun, "audit") and hasattr(postrun, "row_key_hash")
    except Exception as exc:
        entrypoints_ok = False
        checks.append({"name": "entrypoint_import_smoke_error", "status": "FAIL", "error": repr(exc)})
    checks.append({"name": "entrypoint_import_and_symbol_smoke", "status": "PASS" if entrypoints_ok else "FAIL"})

    # Required negative fixtures.  They are bounded protocol checks only.
    negatives = [
        _expect_failure("permuted_test_row_order", lambda: assert_same_row_order(keys, list(reversed(keys)))),
        _expect_failure("removed_warmup_valid_row", lambda: assert_same_row_order(keys, keys[:-1])),
        _expect_failure("validation_row_in_train_scaler", lambda: fit_scaler_train_only(np.ones((2, 3)), np.asarray([1000, 2000])),),
        _expect_failure("shifted_candi_timestamp", lambda: assert_candi_alignment(timestamps, timestamps + np.r_[0, np.ones(len(timestamps) - 1, dtype=np.int64)])),
        _expect_failure("different_shared_candi_tensor", lambda: assert_shared_control(groups["history14"], groups["history14"] + 1.0, keys, keys)),
        _expect_failure("reversed_subtraction", lambda: assert_difference_formula("fixture", 0.7, 0.4, 0.4 - 0.7)),
        _expect_failure("fifth_holm_member", lambda: assert_family_names(("H2", "H3a-A", "H3a-B", "H3a-C", "extra"))),
        _expect_failure("per_scenario_c_selection", lambda: reject_per_scenario_selection("scenario")),
        _expect_failure("extractor_label_argument", lambda: __import__("phase_g1_core").extract_backbone_rows(None, "lstm", np.zeros((64, 8)), {}, np.arange(63), labels=np.zeros(1))),
        _expect_failure("reordered_source_pair", lambda: assert_same_row_order(make_row_keys(11, 3000, "abrupt", "spike", timestamps), make_row_keys(11, 3001, "abrupt", "spike", timestamps))),
        _expect_failure("g11_unresolved_matching_config", lambda: assert_duration_severity_protocol({"duration_severity_matching": {"status": "UNRESOLVED", "label_access_blocked": True}})),
        _expect_failure("g11_duration_strata_drift", lambda: duration_severity_match_status({"duration": np.asarray([17, 17], dtype=object), "severity": np.asarray([1, 1], dtype=object), "label": np.asarray([1, 0], dtype=np.int8)})),
        _expect_failure("g11_severity_strata_drift", lambda: duration_severity_match_status({"duration": np.asarray([16, 16], dtype=object), "severity": np.asarray([4, 4], dtype=object), "label": np.asarray([1, 0], dtype=np.int8)})),
        _expect_failure("g11_nonbinary_matching_label", lambda: duration_severity_match_status({"duration": np.asarray([16], dtype=object), "severity": np.asarray([1], dtype=object), "label": np.asarray([2], dtype=np.int8)})),
        _expect_failure("g11_missing_exclusion", lambda: assert_duration_severity_protocol(dict(G1_CONFIG, duration_severity_matching=dict(G1_CONFIG["duration_severity_matching"], exclude_mixed_windows=False)))),
        _expect_failure("g11_semantic_control_as_support", lambda: require_supportive_analysis_kind("semantic_nonidentifiability_control")),
        _expect_failure("g11_duration_stratum_probe_refit", lambda: reject_stratum_refit("duration=16")),
        _expect_failure("g11_severity_stratum_scaler_refit", lambda: reject_stratum_scaler_fit("severity=2")),
        _expect_failure("g11_unsupported_duration_merge", lambda: assert_fixed_robustness_strata("duration", (1, 16, 256))),
        _expect_failure("g11_metadata_into_observation_api", lambda: assert_observation_only_api(lambda observations, duration: observations)),
        _expect_failure("g11_semantic_observation_mismatch", lambda: assert_semantic_nonidentifiability(np.zeros((2, 8)), np.ones((2, 8)), np.zeros((2, 3)), np.zeros((2, 3)))),
        _expect_failure("g11_duration_row_cohort_mismatch", lambda: assert_same_row_order(keys, keys[:-1])),
    ]
    checks.extend(negatives)
    support = duration_severity_match_status({"duration": np.asarray([16, 16], dtype=object), "severity": np.asarray([1, 1], dtype=object), "label": np.asarray([1, 0], dtype=np.int8)})
    checks.append({"name": "g11_fixed_matching_bin", "status": "PASS" if support["status"] == "PASS" else "FAIL"})
    insufficient = duration_severity_match_status({"duration": np.asarray([16], dtype=object), "severity": np.asarray([1], dtype=object), "label": np.asarray([1], dtype=np.int8)})
    checks.append({"name": "g11_insufficient_support_no_merge", "status": "PASS" if insufficient["status"] == "N/A" and insufficient["usable_bins"] == {} else "FAIL"})
    checks.append({"name": "stage_a_no_metric_execution", **_source_no_metric_execution()})

    # Verify sealed input files by hash only.  Reading these manifests does not
    # read evaluator labels or model outcomes.
    sealed = G1_CONFIG["sealed_input_sha256"]
    hash_checks = []
    for relative, expected in sealed.items():
        path = ROOT / relative
        actual = _sha(path)
        hash_checks.append({"path": relative, "expected": expected, "actual": actual, "pass_": actual == expected})
    checks.append({"name": "sealed_g0_f4_input_hashes", "status": "PASS" if all(row["pass_"] for row in hash_checks) else "FAIL", "files": hash_checks})
    base_path = ROOT / G1_CONFIG["base_g0_config"]
    base_actual = _sha(base_path)
    checks.append({"name": "base_g0_config_hash", "status": "PASS" if base_actual == G1_CONFIG["base_g0_config_sha256"] else "FAIL", "expected": G1_CONFIG["base_g0_config_sha256"], "actual": base_actual})

    failed = [row["name"] for row in checks if row.get("status") != "PASS"]
    return {
        "status": "PASS" if not failed else "STOP",
        "checks": checks,
        "failed_checks": failed,
        "real_phase_g_labels_read": False,
        "test_source_labels_read": False,
        "scaler_fitted": False,
        "logistic_fitted": False,
        "ap_or_auroc_computed": False,
        "bootstrap_or_sign_flip": False,
        "optimizer_created_or_stepped": False,
        "checkpoint_mutated": False,
        "phase": "G1 Stage A",
    }


def main() -> None:
    REPORT.mkdir(parents=True, exist_ok=True)
    result = run()
    (REPORT / "stage_a_preflight.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "failed_checks": result["failed_checks"], "labels_read": result["real_phase_g_labels_read"]}, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
