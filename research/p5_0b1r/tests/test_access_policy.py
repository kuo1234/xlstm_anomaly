"""Synthetic tests for the P5-0B1R archive access boundary.

These tests use only tiny temporary ZIPs. They never locate or open the source
dataset archive.
"""

from __future__ import annotations

import csv
import hashlib
import io
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from build_manifest import (  # noqa: E402
    ROLE_SALT,
    AccessPolicyError,
    ArchiveAccess,
    StructuralLayoutError,
    _parse_raw_payload,
    _disambiguate_duplicate_headers,
    _header_fields,
    build_role_split,
    canonical_json_bytes,
    derive_raw_allowlist,
    parse_configuration_bytes,
    parse_feature_description_bytes,
    validate_csv_layout,
)


def csv_bytes(header, rows, delimiter=","):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=delimiter)
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


class AccessPolicyTests(unittest.TestCase):
    def test_preDist_archive_is_not_git_tracked(self):
        repository_root = Path(__file__).resolve().parents[3]
        result = subprocess.run(
            ["git", "ls-files", "*predist_dataset*.zip"],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stdout.strip(), "")

    def make_zip(self, path, members):
        with zipfile.ZipFile(path, "w") as archive:
            for name, payload in members.items():
                archive.writestr(name, payload)

    def test_forbidden_and_unknown_member_attempts_fail_before_payload_open(self):
        members = {
            "README.md": b"synthetic only",
            "manufacturer 1/normal_events.csv": b"synthetic only",
            "manufacturer 1/faults.csv": b"synthetic only",
            "manufacturer 1/disturbances.csv": b"synthetic only",
            "manufacturer 1/maintenance_report.csv": b"synthetic only",
            "manufacturer 1/event_labels.csv": b"synthetic only",
            "mystery.csv": b"synthetic only",
            "manufacturer 1/configuration_types.csv": b"substation ID;configuration_type\n1;SH\n",
            "manufacturer 1/feature_descriptions.csv": b"column;unit\nvalue;u\n",
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "fixture.zip"
            self.make_zip(path, members)
            original_open = zipfile.ZipFile.open
            opened = []

            def observed_open(archive, name, *args, **kwargs):
                opened.append(name.filename if isinstance(name, zipfile.ZipInfo) else name)
                return original_open(archive, name, *args, **kwargs)

            metadata = {
                "manufacturer 1/configuration_types.csv",
                "manufacturer 1/feature_descriptions.csv",
            }
            with patch.object(zipfile.ZipFile, "open", observed_open):
                with ArchiveAccess(path, metadata_allowlist=metadata) as access:
                    for member in members:
                        if member in metadata:
                            continue
                        with self.subTest(member=member), self.assertRaises(AccessPolicyError):
                            access.read_member_bytes(member)
            self.assertEqual(opened, [])

    def test_only_exact_metadata_and_installed_raw_paths_are_opened(self):
        members = {
            "manufacturer 1/configuration_types.csv": b"substation ID;configuration_type\n1;SH\n",
            "manufacturer 1/feature_descriptions.csv": b"column;unit\nvalue;u\n",
            "manufacturer 1/operational_data/substation_1.csv": b"timestamp,value\n2020-01-01,1\n",
            "manufacturer 1/operational_data/substation_2.csv": b"timestamp,value\n2020-01-01,2\n",
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthetic.zip"
            self.make_zip(path, members)
            metadata = {
                "manufacturer 1/configuration_types.csv",
                "manufacturer 1/feature_descriptions.csv",
            }
            with ArchiveAccess(path, metadata_allowlist=metadata) as access:
                self.assertEqual(
                    access.read_member_bytes("manufacturer 1/configuration_types.csv"),
                    members["manufacturer 1/configuration_types.csv"],
                )
                with self.assertRaises(AccessPolicyError):
                    access.read_member_bytes("manufacturer 1/operational_data/substation_2.csv")
                access.install_raw_allowlist({"manufacturer 1/operational_data/substation_1.csv"})
                self.assertEqual(
                    access.read_member_bytes("manufacturer 1/operational_data/substation_1.csv"),
                    members["manufacturer 1/operational_data/substation_1.csv"],
                )
                with self.assertRaises(AccessPolicyError):
                    access.read_member_bytes("manufacturer 1/operational_data/substation_2.csv")
                self.assertEqual(
                    access.open_log,
                    [
                        "manufacturer 1/configuration_types.csv",
                        "manufacturer 1/operational_data/substation_1.csv",
                    ],
                )

    def test_unknown_metadata_allowlist_path_is_rejected_before_payload_open(self):
        members = {
            "mystery.csv": b"unknown",
            "manufacturer 1/configuration_types.csv": b"substation ID;configuration_type\n1;SH\n",
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthetic.zip"
            self.make_zip(path, members)
            original_open = zipfile.ZipFile.open
            opened = []

            def observed_open(archive, name, *args, **kwargs):
                opened.append(name.filename if isinstance(name, zipfile.ZipInfo) else name)
                return original_open(archive, name, *args, **kwargs)

            with patch.object(zipfile.ZipFile, "open", observed_open):
                with self.assertRaises(AccessPolicyError):
                    ArchiveAccess(path, metadata_allowlist={"mystery.csv"})
            self.assertEqual(opened, [])

    def test_raw_allowlist_uses_exact_manufacturer_entity_paths(self):
        configurations = [
            {"manufacturer": "manufacturer 1", "entity_id": "1", "configuration_type": "SH + DHW"},
            {"manufacturer": "manufacturer 1", "entity_id": "2", "configuration_type": "SH + DHW"},
        ]
        names = {
            "manufacturer 1/operational_data/substation_1.csv",
            "manufacturer 1/operational_data/substation_10.csv",
            "manufacturer 2/operational_data/substation_1.csv",
            "README.md",
        }
        self.assertEqual(
            derive_raw_allowlist(names, configurations),
            {"manufacturer 1/operational_data/substation_1.csv"},
        )

    def test_unknown_csv_layout_fails_closed(self):
        members = {
            "manufacturer 1/configuration_types.csv",
            "manufacturer 1/feature_descriptions.csv",
            "manufacturer 1/operational_data/substation_1.csv",
            "manufacturer 1/extra.csv",
        }
        configurations = [
            {"manufacturer": "manufacturer 1", "entity_id": "1", "configuration_type": "SH"}
        ]
        with self.assertRaises(StructuralLayoutError):
            validate_csv_layout(members, configurations)

    def test_feature_and_raw_parsers_reject_forbidden_semantic_columns(self):
        with self.assertRaises(AccessPolicyError):
            parse_feature_description_bytes(
                csv_bytes(["feature", "event_label"], [["temperature", "fault"]])
            )
        with self.assertRaises(AccessPolicyError):
            _parse_raw_payload(
                b"timestamp,temperature,event_label\n2020-01-01,1,0\n",
                ["timestamp", "temperature", "event_label"],
                ",",
                "timestamp",
                {"temperature"},
            )

    def test_raw_parser_output_contains_only_structural_measurements(self):
        summary = _parse_raw_payload(
            b"timestamp,temperature\n2020-01-01,1\n2020-01-02,\n",
            ["timestamp", "temperature"],
            ",",
            "timestamp",
            {"temperature"},
        )
        self.assertEqual(summary["row_count"], 2)
        self.assertEqual(summary["feature_fields"], ["temperature"])
        self.assertEqual(summary["feature_stats"]["temperature"]["missing_count"], 1)
        self.assertEqual(summary["feature_stats"]["temperature"]["missing_fraction"], 0.5)
        self.assertFalse(any("label" in field.casefold() or "event" in field.casefold() for field in summary))

    def test_horizon_window_uses_half_open_elapsed_interval(self):
        from datetime import datetime, timedelta

        start = datetime(2020, 1, 1)
        rows = [
            [(start + timedelta(minutes=10 * index)).isoformat(sep=" "), str(index)]
            for index in range(145)
        ]
        payload = csv_bytes(["timestamp", "temperature"], rows)
        summary = _parse_raw_payload(
            payload,
            ["timestamp", "temperature"],
            ",",
            "timestamp",
            {"temperature"},
        )
        first_day = summary["horizon_windows"][0]
        self.assertEqual(first_day["actual_rows"], 144)
        self.assertEqual(first_day["nominal_row_fraction_10min"], 1.0)
        self.assertTrue(first_day["reaches_elapsed_horizon"])

    def test_invalid_first_timestamp_does_not_substitute_a_later_start(self):
        summary = _parse_raw_payload(
            b"timestamp,temperature\ninvalid,1\n2020-01-01 00:00:00,2\n2020-01-01 00:10:00,3\n",
            ["timestamp", "temperature"],
            ",",
            "timestamp",
            {"temperature"},
        )
        self.assertEqual(summary["first_timestamp"], "")
        self.assertEqual(summary["timestamp_parse_failures"], 1)
        self.assertEqual(summary["chronology_status"], "CHRONOLOGY_INVALID")
        self.assertEqual(summary["horizon_windows"], [])

    def test_out_of_order_rows_keep_first_raw_timestamp_and_fail_chronology(self):
        summary = _parse_raw_payload(
            b"timestamp,temperature\n2020-01-01 00:10:00,1\n2020-01-01 00:00:00,2\n",
            ["timestamp", "temperature"],
            ",",
            "timestamp",
            {"temperature"},
        )
        self.assertEqual(summary["first_timestamp"], "2020-01-01T00:10:00")
        self.assertEqual(summary["minimum_valid_timestamp"], "2020-01-01T00:00:00")
        self.assertEqual(summary["out_of_order_rows"], 1)
        self.assertEqual(summary["chronology_status"], "CHRONOLOGY_INVALID")

    def test_mixed_timezone_rows_fail_chronology_without_guessing_timezone(self):
        summary = _parse_raw_payload(
            b"timestamp,temperature\n2020-01-01 00:00:00,1\n2020-01-01T01:10:00+01:00,2\n",
            ["timestamp", "temperature"],
            ",",
            "timestamp",
            {"temperature"},
        )
        self.assertEqual(summary["timestamp_timezone_mismatch_rows"], 1)
        self.assertEqual(summary["timestamp_parse_failures"], 0)
        self.assertEqual(summary["chronology_status"], "CHRONOLOGY_INVALID")

    def test_duplicate_measurement_headers_are_preserved_and_flagged(self):
        original_fields, delimiter = _header_fields(
            "timestamp,temperature,temperature", allow_duplicate_names=True
        )
        fields, duplicates = _disambiguate_duplicate_headers(original_fields)
        self.assertEqual(duplicates, ["temperature"])
        self.assertEqual(fields, ["timestamp", "temperature", "temperature__duplicate_2"])
        summary = _parse_raw_payload(
            b"timestamp,temperature,temperature\n2020-01-01,1,2\n",
            fields,
            delimiter,
            "timestamp",
            {"temperature"},
            original_fields,
        )
        self.assertEqual(summary["feature_fields"], ["temperature", "temperature__duplicate_2"])
        self.assertEqual(summary["feature_stats"]["temperature__duplicate_2"]["finite_count"], 1)

    def test_canonical_json_bytes_are_deterministic(self):
        left = {"z": [2, 1], "a": {"y": True, "x": "value"}}
        right = {"a": {"x": "value", "y": True}, "z": [2, 1]}
        self.assertEqual(canonical_json_bytes(left), canonical_json_bytes(right))

    def test_role_split_is_stable_disjoint_and_does_not_merge_small_strata(self):
        rows = []
        for configuration_type, count in (("SH", 8), ("DHW", 8), ("small", 4)):
            rows.extend(
                {
                    "manufacturer": "manufacturer 1",
                    "entity_id": f"{configuration_type}-{index}",
                    "configuration_type": configuration_type,
                }
                for index in range(count)
            )
        first = build_role_split(rows)
        second = build_role_split(list(reversed(rows)))
        self.assertEqual(canonical_json_bytes(first), canonical_json_bytes(second))
        self.assertEqual(
            [(row["manufacturer"], row["configuration_type"], row["entity_id"]) for row in first],
            sorted((row["manufacturer"], row["configuration_type"], row["entity_id"]) for row in first),
        )

        small_rows = [row for row in first if row["configuration_type"] == "small"]
        self.assertEqual(len(small_rows), 4)
        self.assertEqual({row["stratum_size"] for row in small_rows}, {4})
        self.assertEqual({row["role"] for row in small_rows}, {"UNSUPPORTED_FOR_ENTITY_SPLIT"})

        for configuration_type in ("SH", "DHW"):
            stratum = [row for row in first if row["configuration_type"] == configuration_type]
            sources = {row["entity_id"] for row in stratum if row["role"] == "SOURCE"}
            targets = {row["entity_id"] for row in stratum if row["role"] == "TARGET"}
            self.assertEqual(sources | targets, {row["entity_id"] for row in stratum})
            self.assertTrue(sources.isdisjoint(targets))
            expected_targets = {
                entity_id
                for _, entity_id in sorted(
                    (
                        hashlib.sha256(
                            f"{ROLE_SALT}manufacturer 1{configuration_type}{entity_id}".encode("utf-8")
                        ).hexdigest(),
                        entity_id,
                    )
                    for entity_id in (row["entity_id"] for row in stratum)
                )[: max(1, len(stratum) // 5)]
            }
            self.assertEqual(targets, expected_targets)

    def test_missing_configuration_type_is_unsupported_without_merging(self):
        rows = [
            {"manufacturer": "manufacturer 1", "entity_id": "1", "configuration_type": ""},
            {"manufacturer": "manufacturer 1", "entity_id": "2", "configuration_type": ""},
        ]
        split = build_role_split(rows)
        self.assertTrue(all(row["role"] == "UNSUPPORTED_FOR_ENTITY_SPLIT" for row in split))
        self.assertEqual({row["stratum_size"] for row in split}, {1})
        self.assertTrue(all(row["role_digest"] == "" for row in split))

    def test_parsers_accept_synthetic_metadata(self):
        configs = parse_configuration_bytes(
            csv_bytes(
                ["substation ID", "configuration_type"],
                [["1", "SH + DHW"]],
                delimiter=";",
            ),
            manufacturer="manufacturer 1",
        )
        features = parse_feature_description_bytes(
            csv_bytes(["column", "description"], [["temperature", "synthetic"]])
        )
        self.assertEqual(configs[0]["configuration_type"], "SH + DHW")
        self.assertEqual(features, ["temperature"])


if __name__ == "__main__":
    unittest.main()
