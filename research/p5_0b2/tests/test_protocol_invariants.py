import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

from research.p5_0b2.scripts.validate_protocol import (
    PRIMARY_ABSOLUTE_FPR_CAP,
    has_banned_positive_claim,
    primary_success,
    project_features,
    source_candidates_have_any_joint_success,
)


ROOT = Path(__file__).resolve().parents[3]


class ProtocolInvariantTests(unittest.TestCase):
    def test_protocol_validator_accepts_the_review_candidate(self):
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


if __name__ == "__main__":
    unittest.main()
