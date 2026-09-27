import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

from research.p5_0b2.scripts.validate_protocol import (
    MIN_FINITE_NORMAL_SUFFIX_OBSERVATIONS,
    MIN_NORMAL_SCORE_COVERAGE,
    PRIMARY_ABSOLUTE_FPR_CAP,
    PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR,
    effective_recall_minimum,
    has_banned_positive_claim,
    primary_success,
    project_features,
    source_candidates_have_any_joint_success,
)
from research.p5_0b2.scripts.seal_protocol import build_seal


ROOT = Path(__file__).resolve().parents[3]


class ProtocolInvariantTests(unittest.TestCase):
    def test_protocol_validator_accepts_the_resealed_protocol(self):
        result = subprocess.run(
            [sys.executable, "-m", "research.p5_0b2.scripts.validate_protocol"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "PROTOCOL_VALIDATION_PASS\n")
        self.assertEqual(result.stderr, "")

    def test_absolute_primary_fpr_cap_is_exactly_three_percent(self):
        self.assertEqual(PRIMARY_ABSOLUTE_FPR_CAP, 0.03)
        self.assertTrue(primary_success(True, 0.03, 0.6, 0.5))
        self.assertFalse(primary_success(True, 0.030001, 0.6, 0.5))

    def test_primary_absolute_fault_report_recall_floor_is_exactly_half(self):
        self.assertEqual(PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR, 0.50)
        seal = json.loads((ROOT / "research/p5_0b2/protocol_seal.json").read_text(encoding="utf-8"))
        self.assertEqual(
            seal["readiness_selection"]["primary_success"]["absolute_fault_report_recall_floor"],
            0.50,
        )

    def test_normal_suffix_count_and_coverage_gates_are_frozen(self):
        self.assertEqual(MIN_FINITE_NORMAL_SUFFIX_OBSERVATIONS, 100)
        self.assertEqual(MIN_NORMAL_SCORE_COVERAGE, 0.95)
        seal = build_seal()
        for section in ("source_development", "evaluation"):
            gate = seal[section]["normal_suffix_evaluation"]
            self.assertEqual(gate["MIN_FINITE_NORMAL_SUFFIX_OBSERVATIONS"], 100)
            self.assertEqual(gate["MIN_NORMAL_SCORE_COVERAGE"], 0.95)
            self.assertEqual(gate["normal_score_coverage"],
                             "N_normal_finite / N_normal_raw; zero raw support is not evaluable")
            self.assertEqual(gate["fpr_denominator"], "N_normal_finite")

        source = (ROOT / "research/p5_0b2/source_development_protocol.md").read_text(encoding="utf-8")
        evaluation = (ROOT / "research/p5_0b2/evaluation_contract.md").read_text(encoding="utf-8")
        for text in (source, evaluation):
            self.assertIn("N_normal_raw", text)
            self.assertIn("N_normal_finite", text)
            self.assertIn("MIN_FINITE_NORMAL_SUFFIX_OBSERVATIONS = 100", text)
            self.assertIn("MIN_NORMAL_SCORE_COVERAGE = 0.95", text)
            self.assertIn("invalid", text.lower())
        self.assertIn("remains in the denominator and is a miss", " ".join(source.split()))
        self.assertIn("remains in the denominator and is a miss", " ".join(evaluation.split()))

        self.assertEqual(seal["result_blind_clarification"], {
            "issue": 9,
            "issue_comment_id": 5857603327,
            "scientific_design_reopened": False,
        })

    def test_effective_recall_floor_for_zero_source_q10_is_half(self):
        self.assertEqual(effective_recall_minimum(0.0), 0.50)

    def test_effective_recall_floor_uses_source_q10_above_half(self):
        self.assertEqual(effective_recall_minimum(0.75), 0.75)

    def test_primary_success_rejects_recall_below_effective_floor(self):
        floor = effective_recall_minimum(0.0)
        self.assertFalse(primary_success(True, 0.03, 0.49, floor))
        self.assertTrue(primary_success(True, 0.03, 0.50, floor))

    def test_source_q90_cannot_relax_primary_fpr_cap(self):
        # The diagnostic is deliberately not an input to the primary gate.
        diagnostic_q90 = 0.99
        self.assertGreater(diagnostic_q90, PRIMARY_ABSOLUTE_FPR_CAP)
        self.assertFalse(primary_success(True, 0.04, 0.8, 0.5))

    def test_zero_success_readiness_grid_uses_negative_path(self):
        self.assertFalse(source_candidates_have_any_joint_success([0, 0, 0]))
        self.assertTrue(source_candidates_have_any_joint_success([0, 1, 0]))

    def test_projection_removes_energy_and_volume_and_is_deterministic(self):
        names = [
            "p_net_meter_volume",
            "s_hc1_supply_temperature",
            "p_net_meter_energy",
            "p_net_meter_flow",
            "p_net_meter_heat_power",
            "x__duplicate_2_temperature",
        ]
        expected = [
            "p_net_meter_flow",
            "p_net_meter_heat_power",
            "s_hc1_supply_temperature",
        ]
        self.assertEqual(project_features(names), expected)
        self.assertEqual(project_features(names), project_features(names))
        self.assertFalse(any(name.endswith(("_meter_energy", "_meter_volume")) for name in expected))

    def test_every_stratum_projection_is_nonempty_and_has_frozen_count(self):
        with (ROOT / "research/p5_0b1r/schema_audit.csv").open(encoding="utf-8", newline="") as stream:
            import csv

            rows = list(csv.DictReader(stream))
        by_key = {
            (row["manufacturer"], row["configuration_type"]): json.loads(row["automated_common_feature_intersection"])
            for row in rows
        }
        projection = json.loads((ROOT / "research/p5_0b2/feature_projection.json").read_text(encoding="utf-8"))
        eligible_keys = sorted(
            (row["manufacturer"], row["configuration_type"])
            for row in projection["strata"]
        )
        observed = [len(project_features(by_key[key])) for key in eligible_keys]
        self.assertEqual(observed, [8, 11, 8, 12, 8])
        self.assertTrue(all(project_features(by_key[key]) for key in eligible_keys))

    def test_source_and_target_share_fault_report_recall_definition(self):
        source = (ROOT / "research/p5_0b2/source_development_protocol.md").read_text(encoding="utf-8")
        evaluation = (ROOT / "research/p5_0b2/evaluation_contract.md").read_text(encoding="utf-8")
        self.assertIn("eligible fault-report recall", source)
        self.assertIn("eligible fault-report recall", evaluation)
        for text in (source, evaluation):
            self.assertIn("faults.csv", text)
            self.assertIn("efd_possible=true", text)
            self.assertIn("duplicates", text.lower())
            self.assertIn("not unique", text.lower())

    def test_claim_checker_rejects_positive_claims_and_allows_explicit_caveats(self):
        self.assertTrue(has_banned_positive_claim("This is verified-normal evidence."))
        self.assertTrue(has_banned_positive_claim("This is a safe READY guarantee."))
        self.assertFalse(has_banned_positive_claim("This is not verified-normal; no safe READY claim is made."))

    def test_regenerated_seal_artifact_hashes_match_files(self):
        seal = json.loads((ROOT / "research/p5_0b2/protocol_seal.json").read_text(encoding="utf-8"))
        for artifact in seal["sealed_artifacts"]:
            path = ROOT / artifact["path"]
            self.assertTrue(path.is_file(), artifact["path"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), artifact["sha256"], artifact["path"])

    def test_reviewer_clearance_marks_path_read_as_structural_only(self):
        seal = json.loads((ROOT / "research/p5_0b2/protocol_seal.json").read_text(encoding="utf-8"))
        self.assertEqual(seal["reviewer_adjudication"], {
            "raw_path_metadata_read": "STRUCTURAL_METADATA_DEVIATION",
            "semantic_boundary_breach": "NO",
            "outcome_leakage": "NO",
            "review_status": "ISSUE_9_REVIEWER_CLEARED",
        })

    def test_target_access_remains_unauthorized_after_path_clearance(self):
        seal = json.loads((ROOT / "research/p5_0b2/protocol_seal.json").read_text(encoding="utf-8"))
        access = seal["target_access"]
        self.assertEqual(access["target_label_access"], "NOT_AUTHORIZED")
        self.assertFalse(access["target_raw_values_or_scores_accessed"])
        self.assertFalse(access["target_prefix_adjudication_performed"])
        self.assertFalse(access["suffix_evaluation_performed"])
        authorized_stage = "P5-0B3 SOURCE-only development and source model/readiness-parameter seal"
        self.assertEqual(access["next_stage"], authorized_stage)
        self.assertEqual(seal["information_boundary"]["next_authorized_stage"], authorized_stage)

    def test_seal_builder_is_canonical_and_repeatable(self):
        first = build_seal()
        second = build_seal()
        self.assertEqual(first, second)
        written = json.loads((ROOT / "research/p5_0b2/protocol_seal.json").read_text(encoding="utf-8"))
        self.assertEqual(first, written)


if __name__ == "__main__":
    unittest.main()
