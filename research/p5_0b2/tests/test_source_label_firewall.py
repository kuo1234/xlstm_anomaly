import hashlib
import json
import contextlib
import csv
import io
import tempfile
import traceback
import unittest
from pathlib import Path
from unittest.mock import patch

from research.p5_0b2.scripts import source_label_firewall as firewall
from research.p5_0b2.scripts.source_label_firewall import (
    FirewallError,
    build_role_index,
    canonical_source_bytes,
    extract_source_bytes,
    load_role_index,
    normalize_table_rows,
    publish_artifacts,
    read_source_csv,
    sha256_file,
)


def role_index():
    return build_role_index(
        [
            {"manufacturer": "manufacturer 1", "entity_id": "S1", "role": "SOURCE", "role_digest": "source-digest"},
            {"manufacturer": "manufacturer 1", "entity_id": "T1", "role": "TARGET", "role_digest": "target-secret-digest"},
            {"manufacturer": "manufacturer 1", "entity_id": "U1", "role": "UNSUPPORTED_FOR_ENTITY_SPLIT", "role_digest": ""},
        ]
    )


class GuardedTargetRow(dict):
    """A synthetic row that fails if code reads target semantic fields."""

    forbidden = {
        "efd_possible",
        "Possible anomaly start",
        "Possible anomaly end",
        "Report date",
        "Event start",
        "Event end",
        "type",
        "description",
    }

    def get(self, key, default=None):
        if key in self.forbidden:
            raise AssertionError("target semantic field was inspected")
        return super().get(key, default)


def tables(source_row, target_row):
    result = {
        ("manufacturer 1", "faults"): [source_row, target_row],
        ("manufacturer 1", "normal_events"): [
            {"substation ID": "S1", "Event start": "2020-01-01 00:00:00", "Event end": "2020-01-01 01:00:00"},
            {"substation ID": "T1", "Event start": "SECRET TARGET DATE", "Event end": "SECRET TARGET DATE"},
        ],
        ("manufacturer 1", "disturbances"): [
            {"substation ID": "S1", "Event start": "2020-01-02 12:39:01", "type": "task"},
        ],
    }
    for table in ("faults", "normal_events", "disturbances"):
        result[("manufacturer 2", table)] = []
    return result


class SourceLabelFirewallTests(unittest.TestCase):
    def test_pinned_role_manufacturer_keys_match_synthetic_source_labels(self):
        root = Path(__file__).resolve().parents[3]
        index = load_role_index(root / "research/p5_0b1r/role_split_seal.json")
        source_key = next(
            key for key, value in index.items()
            if key[0] == "manufacturer 1" and value["role"] == "SOURCE"
        )
        target_key = next(
            key for key, value in index.items()
            if key[0] == "manufacturer 1" and value["role"] == "TARGET"
        )
        rows = normalize_table_rows(
            "faults",
            source_key[0],
            [
                {
                    "substation ID": source_key[1],
                    "efd_possible": "true",
                    "Possible anomaly start": "2020-01-01 00:00:00",
                    "Possible anomaly end": "2020-01-01 01:00:00",
                    "Report date": "",
                },
                GuardedTargetRow({"substation ID": target_key[1], "description": "synthetic target"}),
            ],
            index,
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["annotation_kind"], "KNOWN_FAULT")
        self.assertNotIn(target_key[1], json.dumps(rows))

    def test_formatted_tracebacks_redact_parse_decode_and_filesystem_details(self):
        secret_value = "SYNTHETIC_SECRET_DATE_8f2d"
        secret_path = "SYNTHETIC_SECRET_SOURCE_PATH_8f2d.csv"
        with tempfile.TemporaryDirectory() as temp:
            malformed_csv = Path(temp) / secret_path
            malformed_csv.write_bytes(
                b"substation ID;efd_possible;Possible anomaly start;Possible anomaly end;Report date\n"
                b"S1;true;\xff;2020-01-01 01:00:00;2020-01-01 02:00:00\n"
            )
            missing_path = Path(temp) / f"missing-{secret_path}"
            cases = (
                ("parse", lambda: firewall._parse_time(secret_value)),
                ("decode", lambda: read_source_csv("faults", "manufacturer 1", malformed_csv, role_index())),
                ("filesystem", lambda: sha256_file(missing_path)),
            )
            for name, operation in cases:
                with self.subTest(name=name):
                    stderr = io.StringIO()
                    with contextlib.redirect_stderr(stderr):
                        with self.assertRaises(FirewallError) as caught:
                            operation()
                    rendered = "".join(
                        traceback.format_exception(
                            type(caught.exception), caught.exception, caught.exception.__traceback__
                        )
                    )
                    self.assertEqual(str(caught.exception), "FIREWALL_FAILED")
                    self.assertTrue(caught.exception.__suppress_context__)
                    self.assertNotIn(secret_value, rendered)
                    self.assertNotIn(secret_path, rendered)
                    self.assertEqual(stderr.getvalue(), "")

    def test_target_row_is_discarded_before_semantic_fields_are_read(self):
        source = {
            "substation ID": "S1",
            "efd_possible": "True",
            "Possible anomaly start": "2020-02-01 00:00:00",
            "Possible anomaly end": "2020-02-01 01:00:00",
            "Report date": "2020-02-01 02:00:00",
        }
        target = GuardedTargetRow({"substation ID": "T1", "description": "TARGET SECRET"})
        payload, count = extract_source_bytes(tables(source, target), role_index())
        self.assertEqual(count, 1)
        self.assertIn(b"source-digest", payload)
        self.assertNotIn(b"target-secret-digest", payload)
        self.assertNotIn(b"TARGET SECRET", payload)
        self.assertNotIn(b"SECRET TARGET DATE", payload)

    def test_fault_fallback_and_disturbance_intervals_are_frozen(self):
        index = role_index()
        fault = normalize_table_rows(
            "faults",
            "manufacturer 1",
            [{
                "substation ID": "S1",
                "efd_possible": "yes",
                "Possible anomaly start": "",
                "Possible anomaly end": "",
                "Report date": "2020-02-01 12:00:00",
            }],
            index,
        )
        self.assertEqual(fault[0]["interval_start"], "2020-01-30T12:00:00")
        self.assertEqual(fault[0]["interval_end"], "2020-02-02T12:00:00")
        other = normalize_table_rows(
            "disturbances",
            "manufacturer 1",
            [{"substation ID": "S1", "Event start": "2020-02-03 12:39:01", "type": "task"}],
            index,
        )
        self.assertEqual(other[0]["interval_start"], "2020-02-03T12:30:00")
        self.assertEqual(other[0]["interval_end"], "2020-02-04T00:00:00")

        partial_fallback = normalize_table_rows(
            "faults",
            "manufacturer 1",
            [
                {
                    "substation ID": "S1",
                    "efd_possible": "yes",
                    "Possible anomaly start": "2020-02-01 00:00:00",
                    "Possible anomaly end": "",
                    "Report date": "2020-02-01 12:00:00",
                }
            ],
            index,
        )
        self.assertEqual(partial_fallback[0]["interval_start"], "2020-02-01T00:00:00")
        self.assertEqual(partial_fallback[0]["interval_end"], "2020-02-02T12:00:00")

    def test_explicit_fault_bounds_do_not_depend_on_unused_fallback_date(self):
        rows = normalize_table_rows(
            "faults",
            "manufacturer 1",
            [
                {
                    "substation ID": "S1",
                    "efd_possible": "true",
                    "Possible anomaly start": "2020-02-01 00:00:00",
                    "Possible anomaly end": "2020-02-01 01:00:00",
                    "Report date": "unused and malformed",
                }
            ],
            role_index(),
        )
        self.assertEqual(rows[0]["interval_start"], "2020-02-01T00:00:00")
        self.assertEqual(rows[0]["interval_end"], "2020-02-01T01:00:00")

    def test_disturbance_floor_clears_subsecond_precision(self):
        rows = normalize_table_rows(
            "disturbances",
            "manufacturer 1",
            [{"substation ID": "S1", "Event start": "2020-02-03 12:39:01.123456", "type": "fault"}],
            role_index(),
        )
        self.assertEqual(rows[0]["interval_start"], "2020-02-01T12:30:00")
        self.assertEqual(rows[0]["interval_end"], "2020-02-04T12:30:00")

    def test_non_possible_fault_and_non_source_roles_do_not_emit_rows(self):
        rows = normalize_table_rows(
            "faults",
            "manufacturer 1",
            [
                {
                    "substation ID": "S1",
                    "efd_possible": "false",
                    "Possible anomaly start": "",
                    "Possible anomaly end": "",
                    "Report date": "",
                },
                {"substation ID": "T1", "not semantic": "must not be read"},
                {"substation ID": "U1", "not semantic": "must not be read"},
            ],
            role_index(),
        )
        self.assertEqual(rows, [])

    def test_unknown_or_duplicate_role_keys_fail_with_redacted_error(self):
        with self.assertRaisesRegex(FirewallError, "^FIREWALL_FAILED$"):
            build_role_index(
                [
                    {"manufacturer": "manufacturer 1", "entity_id": "S1", "role": "SOURCE", "role_digest": "a"},
                    {"manufacturer": "manufacturer 1", "entity_id": "S1", "role": "TARGET", "role_digest": "b"},
                ]
            )
        with self.assertRaisesRegex(FirewallError, "^FIREWALL_FAILED$"):
            normalize_table_rows("faults", "manufacturer 1", [{"substation ID": "UNKNOWN"}], role_index())

    def test_manufacturer_key_must_match_pinned_case_exactly(self):
        with self.assertRaisesRegex(FirewallError, "^FIREWALL_FAILED$"):
            normalize_table_rows("faults", "Manufacturer 1", [{"substation ID": "S1"}], role_index())

    def test_explicit_timezone_offset_fails_closed(self):
        with self.assertRaisesRegex(FirewallError, "^FIREWALL_FAILED$"):
            normalize_table_rows(
                "normal_events",
                "manufacturer 1",
                [{"substation ID": "S1", "Event start": "2020-01-01T00:00:00+02:00", "Event end": "2020-01-01T01:00:00+02:00"}],
                role_index(),
            )

    def test_csv_reader_discards_target_before_parsing_dates(self):
        with tempfile.TemporaryDirectory() as temp:
            csv_path = Path(temp) / "synthetic.csv"
            csv_path.write_text(
                "substation ID;Possible anomaly start;Possible anomaly end;Report date;efd_possible\n"
                "T1;not-a-date;not-a-date;not-a-date;not-a-boolean\n",
                encoding="utf-8",
            )
            self.assertEqual(read_source_csv("faults", "manufacturer 1", csv_path, role_index()), [])

    def test_csv_reader_rejects_duplicate_headers(self):
        with tempfile.TemporaryDirectory() as temp:
            csv_path = Path(temp) / "duplicate-header.csv"
            csv_path.write_text(
                "substation ID;substation ID;Possible anomaly start;Possible anomaly end;Report date;efd_possible\n"
                "S1;T1;2020-01-01 00:00:00;2020-01-01 01:00:00;2020-01-01 02:00:00;true\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(FirewallError, "^FIREWALL_FAILED$"):
                read_source_csv("faults", "manufacturer 1", csv_path, role_index())

    def test_short_source_record_fails_before_interval_normalization(self):
        with tempfile.TemporaryDirectory() as temp:
            csv_path = Path(temp) / "truncated-source.csv"
            csv_path.write_text(
                "substation ID;Event start;type\nS1;2020-01-01 00:00:00\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(FirewallError, "^FIREWALL_FAILED$"):
                read_source_csv("disturbances", "manufacturer 1", csv_path, role_index())

    def test_malformed_quote_fails_without_partial_publish_or_traceback_leak(self):
        entities = [
            {"manufacturer": "manufacturer 1", "entity_id": "S1", "role": "SOURCE", "role_digest": "source-digest"},
            {"manufacturer": "manufacturer 1", "entity_id": "T1_PRIVATE", "role": "TARGET", "role_digest": "target-secret-digest"},
        ]
        role_bytes = (json.dumps({"entities": entities}, sort_keys=True) + "\n").encode("utf-8")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            role_path = root / "synthetic-role-seal.json"
            role_path.write_bytes(role_bytes)
            table_paths = {}
            for manufacturer in firewall.MANUFACTURERS:
                for table in firewall.TABLES:
                    path = root / f"{manufacturer.replace(' ', '_')}-{table}.csv"
                    columns = sorted(firewall.REQUIRED_COLUMNS[table] | {"description"})
                    if manufacturer == "manufacturer 1" and table == "faults":
                        source = {
                            "substation ID": "S1",
                            "efd_possible": "true",
                            "Possible anomaly start": "2020-01-01 00:00:00",
                            "Possible anomaly end": "2020-01-01 01:00:00",
                            "Report date": "",
                            "description": "synthetic source row",
                        }
                        with path.open("w", encoding="utf-8", newline="") as stream:
                            writer = csv.DictWriter(stream, fieldnames=columns, delimiter=";", lineterminator="\n")
                            writer.writeheader()
                            writer.writerow(source)
                        target_cells = [
                            '"TARGET_SECRET_UNCLOSED' if column == "description" else
                            "T1_PRIVATE" if column == "substation ID" else
                            "true" if column == "efd_possible" else
                            "2020-01-01 00:00:00" if column == "Possible anomaly start" else
                            "2020-01-01 01:00:00" if column == "Possible anomaly end" else ""
                            for column in columns
                        ]
                        with path.open("a", encoding="utf-8", newline="") as stream:
                            stream.write(";".join(target_cells) + "\n")
                            stream.write('";true;2020-01-02 00:00:00;2020-01-02 01:00:00;2020-01-02 02:00:00;S1\n')
                    else:
                        with path.open("w", encoding="utf-8", newline="") as stream:
                            writer = csv.DictWriter(stream, fieldnames=columns, delimiter=";", lineterminator="\n")
                            writer.writeheader()
                    table_paths[(manufacturer, table)] = path

            output = root / "must-not-publish"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                with patch.object(firewall, "ROLE_SEAL_SHA256", hashlib.sha256(role_bytes).hexdigest()):
                    with self.assertRaises(FirewallError) as caught:
                        firewall.execute_firewall(table_paths, role_path, output)
            rendered = "".join(
                traceback.format_exception(type(caught.exception), caught.exception, caught.exception.__traceback__)
            )
            self.assertEqual(str(caught.exception), "FIREWALL_FAILED")
            self.assertTrue(caught.exception.__suppress_context__)
            self.assertNotIn("TARGET_SECRET_UNCLOSED", rendered)
            self.assertNotIn("T1_PRIVATE", rendered)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(stderr.getvalue(), "")
            self.assertFalse(output.exists())

    def test_canonical_output_is_byte_deterministic_and_whitelisted(self):
        row = {
            "role_digest": "source-digest",
            "annotation_source": "faults",
            "annotation_kind": "KNOWN_FAULT",
            "interval_start": "2020-01-01T00:00:00",
            "interval_end": "2020-01-01T01:00:00",
        }
        reversed_row = dict(reversed(list(row.items())))
        self.assertEqual(canonical_source_bytes([row]), canonical_source_bytes([reversed_row]))
        with self.assertRaises(FirewallError):
            canonical_source_bytes([dict(row, description="must-not-emit")])

    def test_artifact_publication_contains_only_sanitized_audit_fields(self):
        row = {
            "role_digest": "source-digest",
            "annotation_source": "faults",
            "annotation_kind": "KNOWN_FAULT",
            "interval_start": "2020-01-01T00:00:00",
            "interval_end": "2020-01-01T01:00:00",
        }
        payload = canonical_source_bytes([row])
        input_hash = hashlib.sha256(b"synthetic raw table").hexdigest()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "restricted"
            result = publish_artifacts(output, payload, 1, {"manufacturer 1/faults.csv": input_hash})
            self.assertEqual((output / "source_labels.jsonl").read_bytes(), payload)
            self.assertEqual((output / "source_labels.sha256").read_text().strip(), result["source_artifact_sha256"])
            audit = json.loads((output / "access_audit.json").read_text())
            self.assertFalse(audit["target_rows_emitted"])
            self.assertFalse(audit["target_identifiers_logged"])
            self.assertFalse(audit["target_semantics_logged"])
            self.assertEqual(audit["source_record_count"], 1)
            self.assertNotIn("target_count", audit)
            self.assertNotIn("target_ids", audit)

    def test_publication_refuses_existing_directory_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "existing"
            output.mkdir()
            marker = output / "preserve.txt"
            marker.write_text("synthetic", encoding="utf-8")
            with self.assertRaises(FirewallError):
                publish_artifacts(output, b"", 0, {})
            self.assertEqual(marker.read_text(encoding="utf-8"), "synthetic")

    def test_end_to_end_synthetic_publication_is_redacted_and_deterministic(self):
        entities = [
            {"manufacturer": "manufacturer 1", "entity_id": "S1", "role": "SOURCE", "role_digest": "source-digest"},
            {"manufacturer": "manufacturer 1", "entity_id": "T1_PRIVATE", "role": "TARGET", "role_digest": "target-secret-digest"},
            {"manufacturer": "manufacturer 1", "entity_id": "U1", "role": "UNSUPPORTED_FOR_ENTITY_SPLIT", "role_digest": ""},
        ]
        role_bytes = (json.dumps({"entities": entities}, sort_keys=True) + "\n").encode("utf-8")
        table_paths = {}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            role_path = root / "synthetic-role-seal.json"
            role_path.write_bytes(role_bytes)
            for manufacturer in ("manufacturer 1", "manufacturer 2"):
                for table in firewall.TABLES:
                    path = root / f"{manufacturer.replace(' ', '_')}-{table}.csv"
                    columns = sorted(firewall.REQUIRED_COLUMNS[table] | {"description"})
                    rows = []
                    if manufacturer == "manufacturer 1" and table == "faults":
                        rows = [
                            {
                                "substation ID": "S1",
                                "efd_possible": "true",
                                "Possible anomaly start": "2020-02-01 00:00:00",
                                "Possible anomaly end": "2020-02-01 01:00:00",
                                "Report date": "2020-02-01 02:00:00",
                                "description": "source synthetic event",
                            },
                            {
                                "substation ID": "T1_PRIVATE",
                                "efd_possible": "not-a-flag",
                                "Possible anomaly start": "target-secret-date",
                                "Possible anomaly end": "target-secret-date",
                                "Report date": "target-secret-date",
                                "description": "target-secret-description",
                            },
                        ]
                    with path.open("w", encoding="utf-8", newline="") as stream:
                        writer = csv.DictWriter(stream, fieldnames=columns, delimiter=";", lineterminator="\n")
                        writer.writeheader()
                        writer.writerows(rows)
                    table_paths[(manufacturer, table)] = path

            role_hash = hashlib.sha256(role_bytes).hexdigest()
            outputs = [root / "out-one", root / "out-two"]
            results = []
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                for output in outputs:
                    with patch.object(firewall, "ROLE_SEAL_SHA256", role_hash):
                        results.append(firewall.execute_firewall(table_paths, role_path, output))
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(stderr.getvalue(), "")
            for name in ("source_labels.jsonl", "source_labels.sha256", "access_audit.json"):
                self.assertEqual((outputs[0] / name).read_bytes(), (outputs[1] / name).read_bytes())
                artifact = (outputs[0] / name).read_bytes()
                for forbidden in (b"T1_PRIVATE", b"target-secret-digest", b"target-secret-date", b"target-secret-description"):
                    self.assertNotIn(forbidden, artifact)
            self.assertEqual(results[0], results[1])
            audit = json.loads((outputs[0] / "access_audit.json").read_text(encoding="utf-8"))
            self.assertEqual(audit["source_entity_count"], 1)
            self.assertEqual(audit["source_record_count"], 1)

    def test_unknown_csv_entity_fails_without_partial_publish_or_leak(self):
        entities = [
            {"manufacturer": "manufacturer 1", "entity_id": "S1", "role": "SOURCE", "role_digest": "source-digest"},
        ]
        role_bytes = (json.dumps({"entities": entities}, sort_keys=True) + "\n").encode("utf-8")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            role_path = root / "synthetic-role-seal.json"
            role_path.write_bytes(role_bytes)
            table_paths = {}
            for manufacturer in ("manufacturer 1", "manufacturer 2"):
                for table in firewall.TABLES:
                    path = root / f"{manufacturer.replace(' ', '_')}-{table}.csv"
                    columns = sorted(firewall.REQUIRED_COLUMNS[table])
                    with path.open("w", encoding="utf-8", newline="") as stream:
                        writer = csv.DictWriter(stream, fieldnames=columns, delimiter=";", lineterminator="\n")
                        writer.writeheader()
                        if manufacturer == "manufacturer 1" and table == "faults":
                            writer.writerow({"substation ID": "unknown-secret-id"})
                    table_paths[(manufacturer, table)] = path

            output = root / "must-not-publish"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                with patch.object(firewall, "ROLE_SEAL_SHA256", hashlib.sha256(role_bytes).hexdigest()):
                    with self.assertRaisesRegex(FirewallError, "^FIREWALL_FAILED$") as error:
                        firewall.execute_firewall(table_paths, role_path, output)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(stderr.getvalue(), "")
            self.assertNotIn("unknown-secret-id", str(error.exception))
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
