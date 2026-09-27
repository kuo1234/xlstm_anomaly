"""Synthetic tests for value-minimizing SOURCE CSV projection."""

from datetime import datetime
import unittest

import numpy as np


from research.p5_0b3.scripts import source_ingestion as ingestion


class SourceIngestionTests(unittest.TestCase):
    def test_projects_ordered_features_and_preserves_row_identity(self):
        data = (
            "time,ignored,a,b\n"
            "2024-01-01 00:00:00,not-a-number,1,2\n"
            "2024-01-01 00:01:00,also-ignored,NaN,4\n"
        )
        result = ingestion.project_source_csv(
            data, timestamp_column="time", feature_columns=["b", "a"]
        )
        self.assertEqual(result.feature_names, ("b", "a"))
        np.testing.assert_array_equal(result.features, [[2.0, 1.0], [4.0, np.nan]])
        np.testing.assert_array_equal(result.raw_row_indices, [0, 1])
        self.assertEqual(result.raw_row_count, 2)
        np.testing.assert_array_equal(result.measurement_valid, [True, True])
        np.testing.assert_array_equal(result.timestamp_valid, [True, True])

    def test_invalid_measurements_are_generic_and_values_discarded(self):
        data = "t,x,y\n2024-01-01,12,bad\n2024-01-02,inf,3\n2024-01-03,NaN,\n"
        result = ingestion.project_source_csv(
            data, timestamp_column="t", feature_columns=["x", "y"]
        )
        np.testing.assert_array_equal(result.measurement_valid, [False, False, False])
        self.assertTrue(np.isnan(result.features).all())

    def test_invalid_and_aware_timestamps_are_flagged_without_reordering(self):
        data = "t,x\n2024-01-01T00:00:00+08:00,1\nnot-a-time,2\n2024-01-01 00:02:00,3\n"
        result = ingestion.project_source_csv(
            data, timestamp_column="t", feature_columns=["x"]
        )
        np.testing.assert_array_equal(result.timestamp_valid, [False, False, True])
        self.assertEqual(result.timestamps, (None, None, datetime(2024, 1, 1, 0, 2)))
        np.testing.assert_array_equal(result.raw_row_indices, [0, 1, 2])

    def test_b1_timestamp_formats_and_delimiter_are_supported(self):
        data = "timestamp;x;ignored\n01.02.2024 03:04;2;bad\n2024/02/01 03:05:00;3;bad\n"
        timestamp, delimiter = ingestion.detect_timestamp_column(data)
        self.assertEqual((timestamp, delimiter), ("timestamp", ";"))
        result = ingestion.project_source_csv(
            data, timestamp_column=timestamp, feature_columns=["x"], delimiter=delimiter
        )
        self.assertEqual(result.timestamps, (datetime(2024, 2, 1, 3, 4), datetime(2024, 2, 1, 3, 5)))
        np.testing.assert_array_equal(result.features, [[2.0], [3.0]])

    def test_unselected_duplicate_header_is_discarded_before_schema_check(self):
        result = ingestion.project_source_csv(
            "time,ignored,ignored,x\n2024-01-01,bad,also-bad,2\n",
            timestamp_column="time", feature_columns=["x"]
        )
        np.testing.assert_array_equal(result.features, [[2.0]])

    def test_duplicate_header_missing_selected_field_and_bad_row_width_fail(self):
        for data, features in (
            ("t,x,x\n2024-01-01,1,2\n", ["x"]),
            ("t,x\n2024-01-01,1\n", ["missing"]),
            ("t,x\n2024-01-01,1,extra\n", ["x"]),
        ):
            with self.subTest(data=data):
                with self.assertRaises(ingestion.SourceCsvError):
                    ingestion.project_source_csv(
                        data, timestamp_column="t", feature_columns=features
                    )

    def test_inclusive_union_masks_endpoints_and_ignores_invalid_timestamps(self):
        timestamps = [
            datetime(2024, 1, 1),
            datetime(2024, 1, 2),
            datetime(2024, 1, 3),
            None,
        ]
        mask = ingestion.inclusive_interval_mask(
            timestamps,
            [{"start": datetime(2024, 1, 1), "end": datetime(2024, 1, 2)}],
        )
        np.testing.assert_array_equal(mask, [True, True, False, False])


if __name__ == "__main__":
    unittest.main()
