"""CPU-only contract checks for the audit; no model or dataset mutation."""
import json
from pathlib import Path
import unittest

from real_data_acquire import SEALED_SMD_2_1, sha256
from real_data_inspect import intervals, smd, sensor


ROOT = Path(__file__).resolve().parents[1]


class AuditTests(unittest.TestCase):
    def test_interval_half_open(self):
        self.assertEqual(intervals([False, True, True, False, True]), [[1, 3], [4, 5]])

    def test_manifest_contract(self):
        rows = json.loads((ROOT / "research/real_data_feasibility/datasets.json").read_text())["datasets"]
        required = {"dataset_id", "dataset_name", "subset", "source_url", "paper", "license",
                    "access_mode", "download_status", "raw_path", "sha256", "multivariate",
                    "n_channels", "sampling_interval", "train_split", "test_split", "anomaly_labels",
                    "drift_labels", "drift_label_source", "label_granularity", "native_anomaly",
                    "native_drift", "injected_anomaly", "injected_drift", "normal_training_available",
                    "usable_for_standard_tsad", "usable_for_distribution_shift", "usable_for_drift_vs_anomaly"}
        self.assertEqual(len({row["dataset_id"] for row in rows}), len(rows))
        for row in rows:
            self.assertFalse(required - row.keys(), row["dataset_id"])

    def test_acquired_manifest_hashes(self):
        rows = json.loads((ROOT / "research/real_data_feasibility/datasets.json").read_text())["datasets"]
        for row in rows:
            if not row["download_status"].startswith("acquired"):
                continue
            hashes = row["sha256"]
            if isinstance(hashes, str):
                hashes = {Path(row["raw_path"]).name: hashes}
            for name, expected in hashes.items():
                path = ROOT / row["raw_path"]
                if path.is_dir():
                    path = path / name
                self.assertTrue(path.is_file(), str(path))
                self.assertEqual(sha256(path), expected, str(path))

    def test_existing_seal_if_acquired(self):
        for rel, expected in SEALED_SMD_2_1.items():
            path = ROOT / "data/external_real" / rel
            if path.exists():
                self.assertEqual(sha256(path), expected)

    def test_smd_shape_and_test_labels_if_acquired(self):
        result = smd("machine-2-1")
        if result["train"]["status"] == "available":
            self.assertEqual(result["train"]["shape"], [23693, 38])
            self.assertEqual(result["test"]["shape"], [23694, 38])
            self.assertEqual(result["test_labels"]["label_distribution"], {"0": 22524, "1": 1170})

    def test_sensor_change_markers_if_acquired(self):
        rows = sensor()
        if all(row["status"] == "available" for row in rows):
            self.assertEqual([row["drift_point_indices"] for row in rows], [[350, 1172], [581]])
            self.assertEqual([row["timestamp_parse_failures"] for row in rows], [0, 0])
            self.assertEqual([row["anomaly_pattern_or_point_distribution"]["1"] for row in rows], [10, 21])


if __name__ == "__main__":
    unittest.main()
