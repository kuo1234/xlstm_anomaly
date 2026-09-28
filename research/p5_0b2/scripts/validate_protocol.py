"""Validate P5-0B2R2 protocol invariants and pinned structural artifact hashes."""

from __future__ import annotations

import hashlib
import json
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BASE_COMMIT = "758c48b23e54bd775a71bc0542fb008cd7e2e426"
ROLE_SHA256 = "00e0cec62d238c78f2d0b3c79910c0ffaf1122d1582c28c8848022fb3e10e33f"
ROLE_COUNTS = {"SOURCE": 74, "TARGET": 16, "UNSUPPORTED_FOR_ENTITY_SPLIT": 3}
PRIMARY_ABSOLUTE_FPR_CAP = 0.03
PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR = 0.50
MIN_FINITE_NORMAL_SUFFIX_OBSERVATIONS = 100
MIN_NORMAL_SCORE_COVERAGE = 0.95
REMOVED_FEATURE_SUFFIXES = ("_meter_energy", "_meter_volume")
CONTINUOUS_FEATURE_SUFFIXES = (
    "_temperature",
    "_temperature_setpoint",
    "_room_temperature_setpoint",
    "_meter_flow",
    "_meter_heat_power",
    "_control_valve_position",
    "_control_valve_position_setpoint",
)
TARGET_COUNTS_BY_STRATUM = [5, 1, 4, 4, 2]
EXPECTED_FEATURE_COUNTS_BY_STRATUM = [8, 11, 8, 12, 8]
EXPECTED_STRUCTURAL_HASHES = {
    "research/p5_0b1r/entity_manifest.csv": "ecd59569a17e4699b964724aaf4bf8180b7f703f07bfdab3f5ebb0471e349556",
    "research/p5_0b1r/access_policy.json": "45447b922ede5b0367883816331b7154b83723dc883f654cc65d3c95b9969b46",
    "research/p5_0b1r/schema_audit.csv": "3b06f57c7dc500b01f230adb5d2db8911c320f957584912018c1606faef4ab3a",
    "research/p5_0b1r/horizon_coverage.csv": "66a823c7e3682ebc11b5522436de10665c88ccd2332e29ddd27ad0f4f26fb25b",
    "research/p5_0b1r/download_manifest.json": "8062b306deaf4a887b294f82c3810c167ff682414bf4735171261a9109904f67",
}
PATH_BEARING_STRUCTURAL_ARTIFACTS = {
    "research/p5_0b1r/entity_manifest.csv",
    "research/p5_0b1r/download_manifest.json",
}
REQUIRED_ORDER = (
    "Full method-development procedure seal",
    "Source-label firewall seal",
    "SOURCE-only development and model/readiness seal",
    "TARGET prefix-only adjudication",
    "TARGET score/READY trajectory and seal",
    "Suffix evaluator unlock",
    "Outcome scoring",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail_if(condition: bool, rule: str, failures: list[str]) -> None:
    if condition:
        failures.append(rule)


def project_features(common_names: list[str]) -> list[str]:
    """Return the deterministic name-only projection for one SOURCE stratum."""
    return sorted(
        name for name in common_names
        if name.endswith(CONTINUOUS_FEATURE_SUFFIXES)
        and not name.endswith(REMOVED_FEATURE_SUFFIXES)
        and "__duplicate_" not in name
    )


def primary_success(ready_within_budget: bool, future_normal_fpr: float,
                    eligible_fault_report_recall: float, recall_min_effective: float) -> bool:
    """Frozen primary joint-success rule; source FPR q90 is intentionally absent."""
    return (
        ready_within_budget
        and future_normal_fpr <= PRIMARY_ABSOLUTE_FPR_CAP
        and eligible_fault_report_recall >= recall_min_effective
    )


def effective_recall_minimum(recall_min_source_q10: float) -> float:
    """Apply the frozen project floor to the source-derived q10 margin."""
    return max(PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR, recall_min_source_q10)


def source_candidates_have_any_joint_success(joint_success_counts: list[int]) -> bool:
    """A source stratum without any joint-success task is not sealable."""
    return bool(joint_success_counts) and any(count > 0 for count in joint_success_counts)


def has_banned_positive_claim(text: str) -> bool:
    """Reject positive normality/safety claims while allowing explicit caveats."""
    patterns = (
        r"\bverified[- ]normal\b",
        r"\bknown[- ]normal\b",
        r"\bnormal[- ]only (?:commissioning )?(?:prefix|evidence)\b",
        r"\b(?:safe|certified|guaranteed) READY\b",
    )
    normalized = re.sub(r"\s+", " ", text)
    sentences = re.split(r"(?<=[.!?])\s+", normalized)
    for sentence in sentences:
        if any(re.search(pattern, sentence, flags=re.IGNORECASE) for pattern in patterns):
            if not re.search(r"\b(?:not|no|never|does not|cannot|without|rejects?)\b", sentence, flags=re.IGNORECASE):
                return True
    return False


def validate() -> list[str]:
    failures: list[str] = []
    try:
        structural = json.loads((ROOT / "research/p5_0b2/structural_inputs_seal.json").read_text(encoding="utf-8"))
        role_path = ROOT / structural["role_seal"]["path"]
        role_bytes = role_path.read_bytes()
        role = json.loads(role_bytes)
        seal = json.loads((ROOT / "research/p5_0b2/protocol_seal.json").read_text(encoding="utf-8"))
    except Exception:
        return ["required_seal_input"]

    fail_if(structural.get("schema_version") != "p5-0b2r2-structural-inputs-v1", "structural_schema", failures)
    fail_if(structural.get("base_commit") != BASE_COMMIT, "base_commit", failures)
    fail_if(structural.get("role_seal", {}).get("sha256") != ROLE_SHA256, "structural_role_hash", failures)
    fail_if(hashlib.sha256(role_bytes).hexdigest() != ROLE_SHA256, "role_file_hash", failures)
    role_counts: dict[str, int] = {}
    for entity in role.get("entities", []):
        role_counts[entity.get("role", "")] = role_counts.get(entity.get("role", ""), 0) + 1
    fail_if(role_counts != ROLE_COUNTS, "role_counts", failures)
    fail_if(structural.get("role_seal", {}).get("entity_counts") != ROLE_COUNTS, "structural_role_counts", failures)
    source_strata = {
        (entity.get("manufacturer"), entity.get("configuration_type"))
        for entity in role.get("entities", [])
        if entity.get("role") == "SOURCE"
    }
    fail_if(len(source_strata) != 5, "source_strata_count", failures)
    target_counts = {
        key: sum(
            1 for entity in role.get("entities", [])
            if entity.get("role") == "TARGET"
            and (entity.get("manufacturer"), entity.get("configuration_type")) == key
        )
        for key in source_strata
    }
    ordered_target_counts = [target_counts[key] for key in sorted(source_strata)]
    fail_if(ordered_target_counts != TARGET_COUNTS_BY_STRATUM, "target_stratum_counts", failures)
    fail_if(
        structural.get("role_seal", {}).get("target_counts_by_exact_stratum_in_ascii_order")
        != TARGET_COUNTS_BY_STRATUM,
        "structural_target_stratum_counts",
        failures,
    )

    try:
        # The manifests can contain operational raw paths. Their immutable
        # digest tokens remain pinned below, but B2R deliberately does not open
        # either file; path resolution belongs to the later SOURCE-only gate.
        schema_path = ROOT / "research/p5_0b1r/schema_audit.csv"
        with schema_path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            schema_rows = list(reader)
        fail_if(not schema_rows or "automated_common_feature_intersection" not in (reader.fieldnames or []), "structural_feature_column", failures)
        schema_by_stratum = {
            (row.get("manufacturer", ""), row.get("configuration_type", "")): row
            for row in schema_rows
        }
        fail_if(
            any(
                key not in schema_by_stratum
                or not schema_by_stratum[key].get("automated_common_feature_intersection", "")
                or not schema_by_stratum[key].get("schema_status", "").startswith("SCHEMA_COMPATIBLE")
                for key in source_strata
            ),
            "structural_feature_strata",
            failures,
        )
        projection_path = ROOT / "research/p5_0b2/feature_projection.json"
        projection = json.loads(projection_path.read_text(encoding="utf-8"))
        projection_rows = projection.get("strata", [])
        projection_by_stratum = {
            (row.get("manufacturer"), row.get("configuration_type")): row
            for row in projection_rows
        }
        rule = projection.get("projection_rule", {})
        fail_if(projection.get("schema_version") != "p5-0b2-feature-projection-v2", "feature_projection_schema", failures)
        fail_if(projection.get("role_seal_sha256") != ROLE_SHA256, "feature_projection_role_hash", failures)
        fail_if(projection.get("schema_audit_sha256") != sha256(schema_path), "feature_projection_schema_hash", failures)
        fail_if(set(projection_by_stratum) != source_strata, "feature_projection_strata", failures)
        fail_if(rule.get("source") != "automated_common_feature_intersection, retained names sorted in ASCII lexical order", "feature_projection_source", failures)
        fail_if(rule.get("keep_name_suffixes") != list(CONTINUOUS_FEATURE_SUFFIXES), "feature_projection_allowlist", failures)
        fail_if(rule.get("keep_exact_names") != [] or rule.get("exclude_if_contains") != ["__duplicate_"], "feature_projection_exclusions", failures)
        observed_feature_counts = []
        for key in sorted(source_strata):
            schema_row = schema_by_stratum.get(key, {})
            projection_row = projection_by_stratum.get(key, {})
            common = json.loads(schema_row.get("automated_common_feature_intersection", "[]"))
            expected_features = project_features(common)
            observed_feature_counts.append(len(expected_features))
            fail_if(projection_row.get("common_feature_count") != len(common), "feature_projection_common_count", failures)
            fail_if(projection_row.get("ordered_features") != expected_features, "feature_projection_order", failures)
            fail_if(projection_row.get("excluded_common_features") != [name for name in common if name not in expected_features], "feature_projection_excluded", failures)
            fail_if(not expected_features, "feature_projection_empty", failures)
            fail_if(project_features(common) != expected_features, "feature_projection_nondeterministic", failures)
            fail_if(any(name.endswith(REMOVED_FEATURE_SUFFIXES) for name in expected_features), "feature_projection_counter_like", failures)
        fail_if(observed_feature_counts != EXPECTED_FEATURE_COUNTS_BY_STRATUM, "feature_projection_counts", failures)
    except Exception:
        failures.append("structural_projection_inventory")

    acquisition = structural.get("acquisition", {})
    fail_if(acquisition.get("looks") != [144, 288, 576, 1152, 2304], "raw_looks", failures)
    fail_if(acquisition.get("n_max") != 2304, "n_max", failures)
    fail_if(acquisition.get("max_elapsed_days") != 64, "elapsed_cap", failures)
    fail_if(acquisition.get("primary_purge_raw_observations") != 0, "purge", failures)
    fail_if(acquisition.get("common_suffix_starts_after_raw_observation") != 2304, "suffix_boundary", failures)
    for path, expected in EXPECTED_STRUCTURAL_HASHES.items():
        actual = structural.get("referenced_structural_artifacts", {}).get(path)
        file_path = ROOT / path
        if actual != expected:
            failures.append("structural_artifact_hash")
            break
        if path in PATH_BEARING_STRUCTURAL_ARTIFACTS:
            continue
        if not file_path.is_file() or sha256(file_path) != expected:
            failures.append("structural_artifact_hash")
            break

    status = seal.get("status")
    fail_if(seal.get("schema_version") != "p5-0b2r2-protocol-seal-v1", "seal_schema", failures)
    fail_if(status not in {"P5_0B2R2_CANDIDATE", "P5_0B2R2_PROTOCOL_RESEALED", "P5_0B2R2_BLOCKED_BY_PROTOCOL_INVARIANT"}, "terminal_status", failures)
    fail_if(seal.get("base_commit") != BASE_COMMIT, "seal_base_commit", failures)
    fail_if(seal.get("branch") != "research/p5-0b2r2-nondegeneracy-reseal", "branch", failures)
    fail_if(seal.get("role_seal_sha256") != ROLE_SHA256, "seal_role_hash", failures)
    fail_if(seal.get("source_development", {}).get("source_label_firewall_version")
            != "p5-0b2-source-label-firewall-v2", "firewall_version", failures)
    clarification = seal.get("result_blind_clarification", {})
    fail_if(clarification.get("issue") != 9, "clarification_issue", failures)
    fail_if(clarification.get("issue_comment_id") != 5857603327, "clarification_comment", failures)
    fail_if(clarification.get("scientific_design_reopened") is not False, "clarification_scope", failures)
    universe = seal.get("data_universe_clarification", {})
    fail_if(universe.get("issue") != 9, "universe_clarification_issue", failures)
    fail_if(universe.get("adjudication_comment_id") != 5865521121, "universe_adjudication_comment", failures)
    fail_if(universe.get("handoff_comment_id") != 5865526941, "universe_handoff_comment", failures)
    fail_if(universe.get("SCIENTIFIC_ESTIMAND_CHANGED") is not False, "universe_estimand_changed", failures)
    fail_if(universe.get("DATA_UNIVERSE_CLARIFICATION") is not True, "universe_clarification_missing", failures)
    fail_if(universe.get("outside_rows_semantic_fields_accessed") is not False, "universe_semantic_access", failures)
    fail_if(universe.get("target_access") != "NOT_AUTHORIZED", "universe_target_access", failures)
    fail_if(seal.get("target_access", {}).get("target_label_access") != "NOT_AUTHORIZED", "target_access", failures)
    fail_if(seal.get("target_access", {}).get("target_raw_values_or_scores_accessed") is not False, "target_raw_scores_access", failures)
    fail_if(seal.get("target_access", {}).get("target_prefix_adjudication_performed") is not False, "target_prefix_access", failures)
    fail_if(seal.get("target_access", {}).get("suffix_evaluation_performed") is not False, "target_suffix_access", failures)
    boundary = seal.get("information_boundary", {})
    fail_if(boundary.get("target_label_access") != "NOT_AUTHORIZED", "information_boundary_target_labels", failures)
    fail_if(boundary.get("target_raw_paths_opened") is not False, "information_boundary_raw_paths", failures)
    fail_if(boundary.get("target_values_scores_missingness_or_eligibility_released") is not False, "information_boundary_target_data", failures)
    fail_if(boundary.get("target_path_metadata_read_during_initial_validation") is not True, "path_metadata_disclosure_status", failures)
    fail_if(boundary.get("raw_path_metadata_read_status") != "STRUCTURAL_METADATA_DEVIATION", "path_metadata_status", failures)
    fail_if(boundary.get("semantic_boundary_breach") != "NO", "semantic_boundary_breach", failures)
    fail_if(boundary.get("outcome_leakage") != "NO", "outcome_leakage", failures)
    fail_if("SOURCE-only manifest projection" not in boundary.get("source_raw_file_gate", ""), "information_boundary_source_projection", failures)
    fail_if(seal.get("energy_fault_detector", {}).get("selected_version") != "v0.7.1", "efd_version", failures)
    fail_if(seal.get("energy_fault_detector", {}).get("selected_commit") != "ced470e1386066931bad32f3cb6e24bac9c5bb89", "efd_commit", failures)
    fail_if(seal.get("energy_fault_detector", {}).get("paper_cited_version") != "v0.3.0", "efd_version_correction", failures)
    fail_if(seal.get("readiness_selection", {}).get("primary_fixed_n_reference") != 2304, "primary_fixed_n", failures)
    primary_success_contract = seal.get("readiness_selection", {}).get("primary_success", {})
    fail_if(primary_success_contract.get("future_normal_pointwise_fpr_lte") != PRIMARY_ABSOLUTE_FPR_CAP, "primary_fpr_cap", failures)
    fail_if(primary_success_contract.get("eligible_fault_report_recall_gte") != "Recall_min_effective", "primary_recall_minimum", failures)
    fail_if(primary_success_contract.get("absolute_fault_report_recall_floor") != PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR, "primary_recall_floor", failures)
    fail_if(primary_success_contract.get("recall_min_source_q10") != "Recall_min_source_q10", "primary_recall_q10", failures)
    fail_if(primary_success_contract.get("recall_min_effective_formula") != "max(0.50, Recall_min_source_q10)", "primary_effective_recall_formula", failures)
    fail_if(seal.get("readiness_selection", {}).get("zero_success_path") != "If every candidate has zero pseudo-target tasks satisfying all primary joint-success conditions, mark that exact stratum SOURCE_MODEL_NOT_EVALUABLE; do not seal the tie-break winner.", "zero_success_path", failures)
    fail_if(seal.get("feature_projection", {}).get("features_per_stratum_ascii_order_before") != [10, 13, 10, 14, 10], "seal_feature_counts_before", failures)
    fail_if(seal.get("feature_projection", {}).get("features_per_stratum_ascii_order_after") != EXPECTED_FEATURE_COUNTS_BY_STRATUM, "seal_feature_counts_after", failures)
    fail_if(seal.get("feature_projection", {}).get("forbidden_suffixes") != list(REMOVED_FEATURE_SUFFIXES), "seal_feature_exclusions", failures)
    fail_if(seal.get("feature_projection", {}).get("counter_transform_added") is not False, "seal_counter_transform", failures)
    fail_if(seal.get("source_development", {}).get("primary_absolute_fpr_cap") != PRIMARY_ABSOLUTE_FPR_CAP, "source_absolute_fpr_cap", failures)
    fail_if(seal.get("source_development", {}).get("primary_absolute_fault_report_recall_floor") != PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR, "source_recall_floor", failures)
    fail_if(seal.get("source_development", {}).get("recall_min_effective_formula") != "max(0.50, Recall_min_source_q10)", "source_effective_recall_formula", failures)
    source_normal_gate = seal.get("source_development", {}).get("normal_suffix_evaluation", {})
    fail_if(source_normal_gate.get("MIN_FINITE_NORMAL_SUFFIX_OBSERVATIONS") != MIN_FINITE_NORMAL_SUFFIX_OBSERVATIONS, "source_normal_suffix_min_finite", failures)
    fail_if(source_normal_gate.get("MIN_NORMAL_SCORE_COVERAGE") != MIN_NORMAL_SCORE_COVERAGE, "source_normal_suffix_min_coverage", failures)
    fail_if(source_normal_gate.get("normal_score_coverage") != "N_normal_finite / N_normal_raw; zero raw support is not evaluable", "source_normal_suffix_coverage_formula", failures)
    fail_if(source_normal_gate.get("fpr_denominator") != "N_normal_finite", "source_normal_suffix_fpr_denominator", failures)
    fail_if(source_normal_gate.get("invalid_normal_score_semantics") != "neither false positive nor true negative; lowers normal_score_coverage", "source_normal_suffix_invalid_score_semantics", failures)
    fail_if(source_normal_gate.get("raw_acquisition_semantics") != "invalid-score observations remain raw acquisitions and do not shift or fill scheduled looks", "source_normal_suffix_raw_acquisition", failures)
    fail_if(seal.get("source_development", {}).get("fixed_n_fpr_q90_role") != "FPR_q90_source_fixedN_diagnostic; diagnostic only, never primary and never relaxes the absolute cap", "source_fpr_q90_role", failures)
    evaluation_seal = seal.get("evaluation", {})
    fail_if(evaluation_seal.get("fixed_target_counts_ascii_stratum_order") != TARGET_COUNTS_BY_STRATUM, "seal_evaluation_target_counts", failures)
    fail_if(evaluation_seal.get("pooled_success_denominator") != 16, "seal_evaluation_denominator", failures)
    fail_if(evaluation_seal.get("minimum_suffix_evaluable_per_stratum") != 0, "seal_evaluation_support", failures)
    fail_if(evaluation_seal.get("unavailable_outcomes_count_as_failure") is not True, "seal_evaluation_missing_outcomes", failures)
    fail_if(evaluation_seal.get("unavailable_source_model_or_margins_prohibit_pooled_claim") is not True, "seal_evaluation_model_gate", failures)
    fail_if(evaluation_seal.get("primary_absolute_fpr_cap") != PRIMARY_ABSOLUTE_FPR_CAP, "evaluation_absolute_fpr_cap", failures)
    fail_if(evaluation_seal.get("primary_absolute_fault_report_recall_floor") != PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR, "evaluation_recall_floor", failures)
    fail_if(evaluation_seal.get("recall_min_effective_formula") != "max(0.50, Recall_min_source_q10)", "evaluation_effective_recall_formula", failures)
    fail_if(evaluation_seal.get("primary_fault_metric") != "eligible fault-report recall", "evaluation_fault_metric", failures)
    evaluation_normal_gate = evaluation_seal.get("normal_suffix_evaluation", {})
    fail_if(evaluation_normal_gate.get("MIN_FINITE_NORMAL_SUFFIX_OBSERVATIONS") != MIN_FINITE_NORMAL_SUFFIX_OBSERVATIONS, "evaluation_normal_suffix_min_finite", failures)
    fail_if(evaluation_normal_gate.get("MIN_NORMAL_SCORE_COVERAGE") != MIN_NORMAL_SCORE_COVERAGE, "evaluation_normal_suffix_min_coverage", failures)
    fail_if(evaluation_normal_gate.get("normal_score_coverage") != "N_normal_finite / N_normal_raw; zero raw support is not evaluable", "evaluation_normal_suffix_coverage_formula", failures)
    fail_if(evaluation_normal_gate.get("fpr_denominator") != "N_normal_finite", "evaluation_normal_suffix_fpr_denominator", failures)
    fail_if(evaluation_normal_gate.get("invalid_normal_score_semantics") != "neither false positive nor true negative; lowers normal_score_coverage", "evaluation_normal_suffix_invalid_score_semantics", failures)
    fail_if(evaluation_normal_gate.get("raw_acquisition_semantics") != "invalid-score observations remain raw acquisitions and do not shift or fill scheduled looks", "evaluation_normal_suffix_raw_acquisition", failures)
    fail_if(evaluation_normal_gate.get("fault_report_eligibility") != "parsed efd_possible=true report interval overlaps a timestamp-valid suffix raw observation", "evaluation_fault_report_raw_overlap", failures)
    fail_if(evaluation_normal_gate.get("fault_report_hit") != "at least one finite overlapping suffix score is strictly greater than the frozen threshold; invalid-only scores are a miss", "evaluation_fault_report_invalid_score_miss", failures)
    fail_if(evaluation_seal.get("fault_metric_is_unique_physical_fault_recall") is not False, "evaluation_unique_physical_fault_claim", failures)
    fail_if(evaluation_seal.get("fault_metric_matches_paper_repeat_filtered_event_set") is not False, "evaluation_paper_event_claim", failures)
    expected_review = "PENDING" if status == "P5_0B2R2_CANDIDATE" else "PASS"
    fail_if(seal.get("verification", {}).get("astra_review") != expected_review, "astra_review", failures)
    fail_if(seal.get("verification", {}).get("protocol_invariant_tests") != 18, "protocol_invariant_test_count", failures)
    fail_if(seal.get("verification", {}).get("synthetic_firewall_tests") != 27, "synthetic_firewall_test_count", failures)
    fail_if(seal.get("verification", {}).get("combined_test_count") != 45, "protocol_combined_test_count", failures)
    clearance = seal.get("reviewer_adjudication", {})
    fail_if(clearance.get("raw_path_metadata_read") != "STRUCTURAL_METADATA_DEVIATION", "path_metadata_classification", failures)
    fail_if(clearance.get("semantic_boundary_breach") != "NO", "path_metadata_semantic_clearance", failures)
    fail_if(clearance.get("outcome_leakage") != "NO", "path_metadata_outcome_clearance", failures)
    fail_if(clearance.get("review_status") != "ISSUE_9_REVIEWER_CLEARED", "path_metadata_review_status", failures)
    if status == "P5_0B2R2_PROTOCOL_RESEALED":
        authorized_stage = "P5-0B3 SOURCE-only development and source model/readiness-parameter seal"
        fail_if(seal.get("target_access", {}).get("next_stage") != authorized_stage, "resealed_next_stage", failures)
        fail_if(boundary.get("next_authorized_stage") != authorized_stage, "resealed_boundary_next_stage", failures)
    elif status == "P5_0B2R2_CANDIDATE":
        fail_if("conditional on P5_0B2R2_PROTOCOL_RESEALED" not in seal.get("target_access", {}).get("next_stage", ""), "candidate_next_stage", failures)
    else:
        fail_if("No next stage authorized" not in seal.get("target_access", {}).get("next_stage", ""), "blocked_next_stage", failures)

    entries = seal.get("sealed_artifacts", [])
    manifest: dict[str, str] = {}
    for entry in entries:
        path = entry.get("path")
        digest = entry.get("sha256")
        if not isinstance(path, str) or path.startswith("/") or ".." in Path(path).parts or path in manifest:
            failures.append("artifact_manifest_path")
            continue
        manifest[path] = digest
        file_path = ROOT / path
        if not file_path.is_file() or not isinstance(digest, str) or sha256(file_path) != digest:
            failures.append("artifact_manifest_hash")
    expected_paths = {
        "research/p5_0b2/README.md",
        "research/p5_0b2/structural_inputs_seal.json",
        "research/p5_0b2/feature_projection.json",
        "research/p5_0b2/detector_backbone_audit.md",
        "research/p5_0b2/detector_contract.md",
        "research/p5_0b2/preprocessing_contract.md",
        "research/p5_0b2/source_development_protocol.md",
        "research/p5_0b2/source_label_firewall.md",
        "research/p5_0b2/target_prefix_adjudication_contract.md",
        "research/p5_0b2/readiness_rule_contract.md",
        "research/p5_0b2/threshold_contract.md",
        "research/p5_0b2/evaluation_contract.md",
        "research/p5_0b2/canonical_sequence.md",
        "research/p5_0b2/final_gate.md",
        "research/p5_0b2/scripts/source_label_firewall.py",
        "research/p5_0b2/scripts/validate_protocol.py",
        "research/p5_0b2/scripts/seal_protocol.py",
        "research/p5_0b2/tests/test_source_label_firewall.py",
        "research/p5_0b2/tests/test_protocol_invariants.py",
        "research/p5_0b2/reviewer_amendment_b2r.md",
        "research/p5_0b2/reviewer_amendment_b2r2.md",
    }
    fail_if(set(manifest) != expected_paths, "artifact_manifest_coverage", failures)

    sequence = (ROOT / "research/p5_0b2/canonical_sequence.md").read_text(encoding="utf-8")
    positions = [sequence.find(label) for label in REQUIRED_ORDER]
    fail_if(any(position < 0 for position in positions) or positions != sorted(positions), "phase_order", failures)
    prefix = (ROOT / "research/p5_0b2/target_prefix_adjudication_contract.md").read_text(encoding="utf-8")
    preprocessing_doc = (ROOT / "research/p5_0b2/preprocessing_contract.md").read_text(encoding="utf-8")
    detector_doc = (ROOT / "research/p5_0b2/detector_contract.md").read_text(encoding="utf-8")
    firewall_doc = (ROOT / "research/p5_0b2/source_label_firewall.md").read_text(encoding="utf-8")
    source_doc = (ROOT / "research/p5_0b2/source_development_protocol.md").read_text(encoding="utf-8")
    threshold_doc = (ROOT / "research/p5_0b2/threshold_contract.md").read_text(encoding="utf-8")
    readiness_doc = (ROOT / "research/p5_0b2/readiness_rule_contract.md").read_text(encoding="utf-8")
    evaluation_doc = (ROOT / "research/p5_0b2/evaluation_contract.md").read_text(encoding="utf-8")
    final_gate = (ROOT / "research/p5_0b2/final_gate.md").read_text(encoding="utf-8")
    fail_if("restricted prefix projection" not in prefix or "NOT_EVALUABLE" not in prefix, "prefix_boundary", failures)
    fail_if("efd_possible" not in firewall_doc or "target_semantics_logged=false" not in firewall_doc, "firewall_contract", failures)
    fail_if("outside this experiment's operational universe" not in firewall_doc
            or "outside_operational_universe_rows_discarded" not in firewall_doc
            or "before role lookup" not in firewall_doc,
            "operational_universe_projection_contract", failures)
    fail_if("P5-0B2-SOURCE-FOLD-v1" not in source_doc or "selected candidate's OOF score" not in source_doc, "source_selection_boundary", failures)
    fail_if("quantile(method=\"linear\")" not in threshold_doc or "q99" not in threshold_doc, "threshold_contract", failures)
    fail_if("PRIMARY_ABSOLUTE_FPR_CAP = 0.03" not in readiness_doc or "PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR = 0.50" not in readiness_doc or "FPR_q90_source_fixedN_diagnostic" not in readiness_doc or "diagnostic only" not in readiness_doc or "Recall_min_source_q10" not in readiness_doc or "Recall_min_effective" not in readiness_doc or "Never-ready" not in readiness_doc, "readiness_contract", failures)
    fail_if("eligible fault-report recall" not in evaluation_doc or "pointwise future-normal FPR" not in evaluation_doc, "evaluation_contract", failures)
    for normal_doc, failure_prefix in ((source_doc, "source"), (evaluation_doc, "evaluation")):
        normalized_doc = re.sub(r"\s+", " ", normal_doc)
        fail_if("N_normal_raw" not in normalized_doc or "N_normal_finite" not in normalized_doc, f"{failure_prefix}_normal_suffix_counts", failures)
        fail_if("MIN_FINITE_NORMAL_SUFFIX_OBSERVATIONS = 100" not in normalized_doc, f"{failure_prefix}_normal_suffix_min_finite", failures)
        fail_if("MIN_NORMAL_SCORE_COVERAGE = 0.95" not in normalized_doc, f"{failure_prefix}_normal_suffix_min_coverage", failures)
        fail_if("normal_score_coverage = N_normal_finite / N_normal_raw" not in normalized_doc, f"{failure_prefix}_normal_suffix_coverage_formula", failures)
        fail_if("FPR denominator" not in normalized_doc or "N_normal_finite" not in normalized_doc, f"{failure_prefix}_normal_suffix_fpr_denominator", failures)
        fail_if("invalid-score observation still advances the raw index" not in normalized_doc, f"{failure_prefix}_normal_suffix_raw_acquisition", failures)
    fail_if("PRIMARY_ABSOLUTE_FPR_CAP = 0.03" not in evaluation_doc or "PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR = 0.50" not in evaluation_doc or "eligible_fault_report_recall >= Recall_min_effective" not in evaluation_doc, "evaluation_primary_success", failures)
    fail_if("faults.csv" not in source_doc or "duplicates are retained" not in source_doc or "not unique physical-fault recall" not in source_doc, "source_fault_report_definition", failures)
    fail_if("faults.csv" not in evaluation_doc or "Duplicate records are retained" not in evaluation_doc or "not unique" not in evaluation_doc, "evaluation_fault_report_definition", failures)
    fail_if("every candidate has zero such" not in readiness_doc or "SOURCE_MODEL_NOT_EVALUABLE" not in readiness_doc, "readiness_zero_success_path", failures)
    fail_if("fixed TARGET counts in ASCII lexical stratum order are `5, 1, 4, 4, 2`" not in evaluation_doc, "evaluation_target_counts", failures)
    fail_if("no minimum per-stratum suffix-evaluable count" not in evaluation_doc, "evaluation_support_gate", failures)
    fail_if("fewer than four prefix-eligible targets" in evaluation_doc, "evaluation_impossible_gate", failures)
    fail_if("feature_projection.json" not in preprocessing_doc or "Raw columns outside that list" not in preprocessing_doc, "preprocessing_projection", failures)
    fail_if("feature_projection.json" not in detector_doc or "Raw union-only and excluded status/mode columns" not in detector_doc, "detector_projection", failures)
    fail_if(not any(status_label in final_gate for status_label in ("P5_0B2R2_CANDIDATE", "P5_0B2R2_PROTOCOL_RESEALED", "P5_0B2R2_BLOCKED_BY_PROTOCOL_INVARIANT")), "final_gate_status", failures)
    fail_if("TARGET_LABEL_ACCESS=NOT_AUTHORIZED" not in final_gate, "final_gate_target_access", failures)
    claim_docs = (
        "research/p5_0b2/README.md",
        "research/p5_0b2/target_prefix_adjudication_contract.md",
        "research/p5_0b2/readiness_rule_contract.md",
        "research/p5_0b2/evaluation_contract.md",
        "research/p5_0b2/final_gate.md",
        "research/p5_0b2/reviewer_amendment_b2r.md",
        "research/p5_0b2/reviewer_amendment_b2r2.md",
    )
    for path in claim_docs:
        if has_banned_positive_claim((ROOT / path).read_text(encoding="utf-8")):
            failures.append("positive_normality_or_safety_claim")
    prefix_vocabulary = (ROOT / "research/p5_0b2/target_prefix_adjudication_contract.md").read_text(encoding="utf-8")
    fail_if("REFERENCE_CLEAN_PRIMARY" not in prefix_vocabulary or "reference-clean commissioning prefix" not in prefix_vocabulary or "record-clean under available annotations" not in prefix_vocabulary, "prefix_claim_vocabulary", failures)
    fail_if("does not prove physical normality" not in prefix_vocabulary or "unlabelled faults may remain" not in prefix_vocabulary, "prefix_physical_normality_caveat", failures)
    return sorted(set(failures))


def main() -> None:
    failures = validate()
    if failures:
        for failure in failures:
            print(f"PROTOCOL_VALIDATION_FAILED:{failure}")
        raise SystemExit(1)
    print("PROTOCOL_VALIDATION_PASS")


if __name__ == "__main__":
    main()
