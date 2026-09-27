"""Validate P5-0B2 protocol invariants and pinned structural artifact hashes."""

from __future__ import annotations

import hashlib
import json
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BASE_COMMIT = "96e7afa9696303d31e5b7f0163349a97d53ce029"
ROLE_SHA256 = "00e0cec62d238c78f2d0b3c79910c0ffaf1122d1582c28c8848022fb3e10e33f"
ROLE_COUNTS = {"SOURCE": 74, "TARGET": 16, "UNSUPPORTED_FOR_ENTITY_SPLIT": 3}
CONTINUOUS_FEATURE_SUFFIXES = (
    "_temperature",
    "_temperature_setpoint",
    "_room_temperature_setpoint",
    "_meter_energy",
    "_meter_flow",
    "_meter_heat_power",
    "_meter_volume",
    "_control_valve_position",
    "_control_valve_position_setpoint",
)
TARGET_COUNTS_BY_STRATUM = [5, 1, 4, 4, 2]
EXPECTED_STRUCTURAL_HASHES = {
    "research/p5_0b1r/entity_manifest.csv": "ecd59569a17e4699b964724aaf4bf8180b7f703f07bfdab3f5ebb0471e349556",
    "research/p5_0b1r/access_policy.json": "45447b922ede5b0367883816331b7154b83723dc883f654cc65d3c95b9969b46",
    "research/p5_0b1r/schema_audit.csv": "3b06f57c7dc500b01f230adb5d2db8911c320f957584912018c1606faef4ab3a",
    "research/p5_0b1r/horizon_coverage.csv": "66a823c7e3682ebc11b5522436de10665c88ccd2332e29ddd27ad0f4f26fb25b",
    "research/p5_0b1r/download_manifest.json": "8062b306deaf4a887b294f82c3810c167ff682414bf4735171261a9109904f67",
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
        manifest_path = ROOT / "research/p5_0b1r/entity_manifest.csv"
        with manifest_path.open(encoding="utf-8", newline="") as stream:
            manifest_rows = list(csv.DictReader(stream))
        manifest_counts: dict[str, int] = {}
        manifest_keys: set[tuple[str, str]] = set()
        raw_paths: list[str] = []
        for row in manifest_rows:
            manifest_counts[row.get("role", "")] = manifest_counts.get(row.get("role", ""), 0) + 1
            key = (row.get("manufacturer", ""), row.get("entity_id", ""))
            manifest_keys.add(key)
            raw_paths.append(row.get("raw_path", ""))
        role_keys = {
            (entity.get("manufacturer", ""), entity.get("entity_id", ""))
            for entity in role.get("entities", [])
        }
        fail_if(len(manifest_rows) != 93 or manifest_counts != ROLE_COUNTS, "entity_manifest_counts", failures)
        fail_if(manifest_keys != role_keys or len(raw_paths) != 93 or not all(raw_paths) or len(set(raw_paths)) != 93, "raw_path_isolation", failures)
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
        fail_if(projection.get("schema_version") != "p5-0b2-feature-projection-v1", "feature_projection_schema", failures)
        fail_if(projection.get("role_seal_sha256") != ROLE_SHA256, "feature_projection_role_hash", failures)
        fail_if(projection.get("schema_audit_sha256") != sha256(schema_path), "feature_projection_schema_hash", failures)
        fail_if(set(projection_by_stratum) != source_strata, "feature_projection_strata", failures)
        fail_if(rule.get("source") != "automated_common_feature_intersection, preserving its committed order", "feature_projection_source", failures)
        fail_if(rule.get("keep_name_suffixes") != list(CONTINUOUS_FEATURE_SUFFIXES), "feature_projection_allowlist", failures)
        fail_if(rule.get("keep_exact_names") != [] or rule.get("exclude_if_contains") != ["__duplicate_"], "feature_projection_exclusions", failures)
        for key in source_strata:
            schema_row = schema_by_stratum.get(key, {})
            projection_row = projection_by_stratum.get(key, {})
            common = json.loads(schema_row.get("automated_common_feature_intersection", "[]"))
            expected_features = [
                name for name in common
                if name.endswith(CONTINUOUS_FEATURE_SUFFIXES) and "__duplicate_" not in name
            ]
            fail_if(projection_row.get("common_feature_count") != len(common), "feature_projection_common_count", failures)
            fail_if(projection_row.get("ordered_features") != expected_features, "feature_projection_order", failures)
            fail_if(projection_row.get("excluded_common_features") != [name for name in common if name not in expected_features], "feature_projection_excluded", failures)
            fail_if(not expected_features, "feature_projection_empty", failures)
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
        if not file_path.is_file() or actual != expected or sha256(file_path) != expected:
            failures.append("structural_artifact_hash")
            break

    fail_if(seal.get("schema_version") != "p5-0b2-protocol-seal-v1", "seal_schema", failures)
    fail_if(seal.get("status") != "P5_0B2_PROTOCOL_SEALED", "terminal_status", failures)
    fail_if(seal.get("base_commit") != BASE_COMMIT, "seal_base_commit", failures)
    fail_if(seal.get("branch") != "research/p5-0b2-prelabel-protocol-seal", "branch", failures)
    fail_if(seal.get("role_seal_sha256") != ROLE_SHA256, "seal_role_hash", failures)
    fail_if(seal.get("target_access", {}).get("target_label_access") != "NOT_AUTHORIZED", "target_access", failures)
    boundary = seal.get("information_boundary", {})
    fail_if(boundary.get("target_label_access") != "NOT_AUTHORIZED", "information_boundary_target_labels", failures)
    fail_if(boundary.get("target_raw_paths_opened") is not False, "information_boundary_raw_paths", failures)
    fail_if(boundary.get("target_values_scores_missingness_or_eligibility_released") is not False, "information_boundary_target_data", failures)
    fail_if("SOURCE-only manifest projection" not in boundary.get("source_raw_file_gate", ""), "information_boundary_source_projection", failures)
    fail_if(seal.get("energy_fault_detector", {}).get("selected_version") != "v0.7.1", "efd_version", failures)
    fail_if(seal.get("energy_fault_detector", {}).get("selected_commit") != "ced470e1386066931bad32f3cb6e24bac9c5bb89", "efd_commit", failures)
    fail_if(seal.get("energy_fault_detector", {}).get("paper_cited_version") != "v0.3.0", "efd_version_correction", failures)
    fail_if(seal.get("readiness_selection", {}).get("primary_fixed_n_reference") != 2304, "primary_fixed_n", failures)
    evaluation_seal = seal.get("evaluation", {})
    fail_if(evaluation_seal.get("fixed_target_counts_ascii_stratum_order") != TARGET_COUNTS_BY_STRATUM, "seal_evaluation_target_counts", failures)
    fail_if(evaluation_seal.get("pooled_success_denominator") != 16, "seal_evaluation_denominator", failures)
    fail_if(evaluation_seal.get("minimum_suffix_evaluable_per_stratum") != 0, "seal_evaluation_support", failures)
    fail_if(evaluation_seal.get("unavailable_outcomes_count_as_failure") is not True, "seal_evaluation_missing_outcomes", failures)
    fail_if(evaluation_seal.get("unavailable_source_model_or_margins_prohibit_pooled_claim") is not True, "seal_evaluation_model_gate", failures)
    fail_if(seal.get("verification", {}).get("astra_review") != "PASS", "astra_review", failures)

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
    fail_if("P5-0B2-SOURCE-FOLD-v1" not in source_doc or "selected candidate's OOF score" not in source_doc, "source_selection_boundary", failures)
    fail_if("quantile(method=\"linear\")" not in threshold_doc or "q99" not in threshold_doc, "threshold_contract", failures)
    fail_if("FPR_max" not in readiness_doc or "Recall_min" not in readiness_doc or "Never-ready" not in readiness_doc, "readiness_contract", failures)
    fail_if("event recall" not in evaluation_doc or "pointwise future-normal FPR" not in evaluation_doc, "evaluation_contract", failures)
    fail_if("fixed TARGET counts in ASCII lexical stratum order are `5, 1, 4, 4, 2`" not in evaluation_doc, "evaluation_target_counts", failures)
    fail_if("no minimum per-stratum suffix-evaluable count" not in evaluation_doc, "evaluation_support_gate", failures)
    fail_if("fewer than four prefix-eligible targets" in evaluation_doc, "evaluation_impossible_gate", failures)
    fail_if("feature_projection.json" not in preprocessing_doc or "Raw columns outside that list" not in preprocessing_doc, "preprocessing_projection", failures)
    fail_if("feature_projection.json" not in detector_doc or "Raw union-only and excluded status/mode columns" not in detector_doc, "detector_projection", failures)
    fail_if("P5_0B2_PROTOCOL_SEALED" not in final_gate or "TARGET_LABEL_ACCESS=NOT_AUTHORIZED" not in final_gate, "final_gate", failures)
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
