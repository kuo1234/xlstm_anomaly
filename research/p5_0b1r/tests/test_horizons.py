"""Synthetic fixed-grid availability tests; no dataset files are used."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from audit_horizons import audit_horizons  # noqa: E402


class HorizonAuditTests(unittest.TestCase):
    def test_fixed_grid_is_reported_as_structural_availability(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entity_path = root / "entity_manifest.csv"
            output_path = root / "horizon_coverage.csv"
            fields = [
                "manufacturer",
                "configuration_type",
                "entity_id",
                "role",
                "raw_status",
                "chronology_status",
                "horizon_windows",
            ]
            windows = [
                {
                    "horizon_days": day,
                    "reaches_elapsed_horizon": day <= 2,
                    "actual_rows": day * 140,
                    "gap_count_over_1_5x_median": 1,
                    "largest_gap_seconds": 900,
                    "missing_cell_fraction": 0.01,
                    "nominal_row_fraction_10min": round(day * 140 / (day * 144), 8),
                }
                for day in (1, 2, 4, 8, 16, 32, 64)
            ]
            with entity_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                writer.writerow(
                    {
                        "manufacturer": "manufacturer 1",
                        "configuration_type": "SH",
                        "entity_id": "1",
                        "role": "TARGET",
                        "raw_status": "PARSED",
                        "chronology_status": "CHRONOLOGY_VALID",
                        "horizon_windows": json.dumps(windows, separators=(",", ":")),
                    }
                )

            rows = audit_horizons(entity_path, output_path)
            self.assertEqual([row["horizon_days"] for row in rows], [1, 2, 4, 8, 16, 32, 64])
            self.assertEqual(rows[0]["nominal_rows_10min"], 144)
            self.assertEqual(rows[0]["entities_reaching_elapsed_horizon"], 1)
            self.assertEqual(rows[2]["entities_reaching_elapsed_horizon"], 0)
            self.assertIn("availability only", rows[0]["interpretation"])
            with output_path.open("r", encoding="utf-8", newline="") as stream:
                written = list(csv.DictReader(stream))
            self.assertEqual(len(written), 7)


if __name__ == "__main__":
    unittest.main()
