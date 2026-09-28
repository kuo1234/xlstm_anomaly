from __future__ import annotations

import contextlib
import hashlib
import io
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from research.p5_0b3.scripts import identity_domain_diagnostic as diagnostic
from research.p5_0b3.scripts.firewall_runner import ALLOWED_MEMBERS


def fixture(role_entities=None, per_member=None):
    if role_entities is None:
        role_entities = [
            {"manufacturer": "manufacturer 1", "entity_id": "1", "role": "SOURCE",
             "role_digest": "PRIVATE_ROLE_DIGEST_A"},
            {"manufacturer": "manufacturer 2", "entity_id": "2", "role": "TARGET",
             "role_digest": "PRIVATE_ROLE_DIGEST_B"},
        ]
    role_bytes = json.dumps({"entities": role_entities}, separators=(",", ":")).encode()
    if per_member is None:
        per_member = {}
        for member in ALLOWED_MEMBERS:
            manufacturer = member.split("/", 1)[0]
            value = "1" if manufacturer == "manufacturer 1" else "2"
            per_member[member] = value
    members = {
        member: (
            "substation ID;semantic-secret-column\n"
            + value + ";SEMANTIC_SECRET_DATE_OR_BOOLEAN\n"
        ).encode()
        for member, value in per_member.items()
    }
    return role_bytes, members


class GuardedCells(list):
    def __init__(self, values, identity_column):
        super().__init__(values)
        self.identity_column = identity_column

    def __getitem__(self, index):
        if index != self.identity_column:
            raise AssertionError("non-identity CSV cell accessed")
        return super().__getitem__(index)


class GuardedRole(dict):
    allowed = {"manufacturer", "entity_id", "role"}

    def get(self, key, default=None):
        if key not in self.allowed:
            raise AssertionError("non-identity role field accessed")
        return super().get(key, default)


class IdentityDomainDiagnosticTests(unittest.TestCase):
    def classify(self, role_entities=None, per_member=None):
        role_bytes, members = fixture(role_entities, per_member)
        with patch.object(diagnostic, "ROLE_SEAL_SHA256", hashlib.sha256(role_bytes).hexdigest()):
            return diagnostic.identity_result(role_bytes, members)

    def test_decimal_canonicalizer_accepts_leading_zeroes_and_whitespace(self):
        self.assertEqual(diagnostic.canonical_decimal_id(" 00017 \t"), "17")
        self.assertEqual(diagnostic.canonical_decimal_id("1"), "1")

    def test_decimal_canonicalizer_rejects_non_ascii_or_non_integer_forms(self):
        for value in (None, "", "   ", "0", "000", "+1", "-1", "1.0", "1e2", "abc", "١", "１２"):
            with self.subTest(value=value):
                self.assertIsNone(diagnostic.canonical_decimal_id(value))

    def test_all_six_members_resolve_after_decimal_canonicalization(self):
        self.assertEqual(self.classify(), diagnostic.IDENTITY_ALL_RESOLVE_AFTER_DECIMAL_CANONICALIZATION)

    def test_leading_zero_role_and_whitespace_label_ids_resolve_identically(self):
        per_member = {
            member: (" 001 \t" if member.startswith("manufacturer 1/") else "2")
            for member in ALLOWED_MEMBERS
        }
        roles = [
            {"manufacturer": "manufacturer 1", "entity_id": "0001", "role": "SOURCE"},
            {"manufacturer": "manufacturer 2", "entity_id": "2", "role": "TARGET"},
        ]
        self.assertEqual(self.classify(roles, per_member),
                         diagnostic.IDENTITY_ALL_RESOLVE_AFTER_DECIMAL_CANONICALIZATION)

    def test_same_numeric_id_in_wrong_manufacturer_is_outside_universe(self):
        per_member = {
            member: ("1" if member.startswith("manufacturer 2/") else "1")
            for member in ALLOWED_MEMBERS
        }
        result = self.classify(
            [{"manufacturer": "manufacturer 1", "entity_id": "1", "role": "SOURCE"}],
            per_member,
        )
        self.assertEqual(result, diagnostic.IDENTITY_OUTSIDE_SEALED_UNIVERSE)

    def test_invalid_role_value_is_reported_only_for_matched_identity(self):
        result = self.classify(
            [{"manufacturer": "manufacturer 1", "entity_id": "1", "role": "SECRET_ROLE"},
             {"manufacturer": "manufacturer 2", "entity_id": "2", "role": "TARGET"}],
            {member: ("1" if member.startswith("manufacturer 1/") else "2")
             for member in ALLOWED_MEMBERS},
        )
        self.assertEqual(result, diagnostic.IDENTITY_INVALID_ROLE_VALUE)

    def test_matched_non_string_role_is_an_invalid_role_value(self):
        result = self.classify(
            [{"manufacturer": "manufacturer 1", "entity_id": "1", "role": None},
             {"manufacturer": "manufacturer 2", "entity_id": "2", "role": "TARGET"}],
        )
        self.assertEqual(result, diagnostic.IDENTITY_INVALID_ROLE_VALUE)

    def test_empty_nondecimal_mixed_and_unclassified_are_deterministic(self):
        result = self.classify(
            [{"manufacturer": "manufacturer 1", "entity_id": "bad-id", "role": "SOURCE"},
             {"manufacturer": "manufacturer 2", "entity_id": "2", "role": "TARGET"}],
            {member: ("bad-id" if member.startswith("manufacturer 1/") else "2")
             for member in ALLOWED_MEMBERS},
        )
        self.assertEqual(result, diagnostic.IDENTITY_EMPTY_OR_NONDECIMAL)
        mixed_values = {member: ("bad-id" if member.startswith("manufacturer 1/") else "99")
                        for member in ALLOWED_MEMBERS}
        self.assertEqual(self.classify(per_member=mixed_values), diagnostic.IDENTITY_MIXED_FAILURE)
        duplicate_roles = [
            {"manufacturer": "manufacturer 1", "entity_id": "01", "role": "SOURCE"},
            {"manufacturer": "manufacturer 1", "entity_id": "1", "role": "TARGET"},
        ]
        self.assertEqual(self.classify(duplicate_roles), diagnostic.IDENTITY_UNCLASSIFIED)
        malformed = {member: b"semantic header only\n1;x\n" for member in ALLOWED_MEMBERS}
        role_bytes, _ = fixture()
        with patch.object(diagnostic, "ROLE_SEAL_SHA256", hashlib.sha256(role_bytes).hexdigest()):
            self.assertEqual(diagnostic.identity_result(role_bytes, malformed), diagnostic.IDENTITY_UNCLASSIFIED)

    def test_target_rows_use_only_identity_and_do_not_expose_semantics_or_digest(self):
        role_bytes, members = fixture()
        with patch.object(diagnostic, "ROLE_SEAL_SHA256", hashlib.sha256(role_bytes).hexdigest()):
            result = diagnostic.identity_result(role_bytes, members)
        self.assertEqual(result, diagnostic.IDENTITY_ALL_RESOLVE_AFTER_DECIMAL_CANONICALIZATION)
        self.assertNotIn("PRIVATE_ROLE_DIGEST", result)
        self.assertNotIn("SEMANTIC_SECRET", result)

    def test_guarded_csv_rows_and_role_mapping_block_non_identity_access(self):
        guarded = diagnostic._identity_values_from_records(
            ["semantic-secret", "substation ID", "other-secret"],
            [GuardedCells(["SECRET_DATE", " 01 ", "SECRET_BOOLEAN"], 1)],
        )
        self.assertEqual(guarded, [" 01 "])

        role_bytes, members = fixture()
        role_entities = [
            GuardedRole({"manufacturer": "manufacturer 1", "entity_id": "1", "role": "SOURCE",
                         "role_digest": "MUST_NOT_READ"}),
            GuardedRole({"manufacturer": "manufacturer 2", "entity_id": "2", "role": "TARGET",
                         "role_digest": "MUST_NOT_READ"}),
        ]
        with patch.object(diagnostic, "ROLE_SEAL_SHA256", hashlib.sha256(role_bytes).hexdigest()), \
                patch.object(diagnostic.json, "loads", return_value={"entities": role_entities}):
            self.assertEqual(
                diagnostic.identity_result(role_bytes, members),
                diagnostic.IDENTITY_ALL_RESOLVE_AFTER_DECIMAL_CANONICALIZATION,
            )

    def test_cli_emits_exactly_one_enum_line_and_no_stderr(self):
        role_bytes, members = fixture()
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(diagnostic, "_pinned_preflight", return_value=(role_bytes, members)), \
                patch.object(diagnostic, "ROLE_SEAL_SHA256", hashlib.sha256(role_bytes).hexdigest()), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = diagnostic.main(["--root", "/synthetic/root", "--sealed-commit", "a" * 40,
                                    "--archive", "/synthetic/archive.zip"])
        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), diagnostic.IDENTITY_ALL_RESOLVE_AFTER_DECIMAL_CANONICALIZATION + "\n")
        self.assertEqual(stderr.getvalue(), "")

    def test_cli_unexpected_error_redacts_fake_values_and_path(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        fake = "PRIVATE_ID_981 /SECRET/source-labels.csv"
        with patch.object(diagnostic, "_pinned_preflight", side_effect=RuntimeError(fake)), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = diagnostic.main(["--root", "/synthetic/root", "--sealed-commit", "a" * 40,
                                    "--archive", "/synthetic/archive.zip"])
        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), diagnostic.IDENTITY_UNCLASSIFIED + "\n")
        self.assertEqual(stderr.getvalue(), "")
        self.assertNotIn(fake, stdout.getvalue())

    def test_cli_malformed_arguments_still_have_enum_stdout_and_empty_stderr(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = diagnostic.main(["--unknown", "value"])
        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), diagnostic.IDENTITY_UNCLASSIFIED + "\n")
        self.assertEqual(stderr.getvalue(), "")

    def test_synthetic_six_member_zip_reads_only_exact_allowlist_once(self):
        _, members = fixture()
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "synthetic.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                for member, content in members.items():
                    zipped.writestr(member, content)
                zipped.writestr("unrelated/private.csv", b"must not be read")
            self.assertEqual(diagnostic._read_identity_members_from_zip(archive), members)

            duplicate = Path(temporary) / "duplicate.zip"
            with zipfile.ZipFile(duplicate, "w") as zipped:
                for member, content in members.items():
                    zipped.writestr(member, content)
                repeated = sorted(ALLOWED_MEMBERS)[0]
                zipped.writestr(repeated, members[repeated])
            with self.assertRaises(ValueError):
                diagnostic._read_identity_members_from_zip(duplicate)

    def test_empty_six_headers_are_unclassified(self):
        role_bytes, _ = fixture()
        members = {
            member: b"substation ID;semantic\n"
            for member in ALLOWED_MEMBERS
        }
        with patch.object(diagnostic, "ROLE_SEAL_SHA256", hashlib.sha256(role_bytes).hexdigest()):
            self.assertEqual(diagnostic.identity_result(role_bytes, members), diagnostic.IDENTITY_UNCLASSIFIED)

    def test_preflight_checks_b3_protocol_pin_and_b2_firewall_hash_synthetically(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scripts = root / "research/p5_0b3/scripts"
            tests = root / "research/p5_0b3/tests"
            scripts.mkdir(parents=True)
            tests.mkdir(parents=True)
            code_files = {scripts / "fixture.py": b"VALUE = 1\n", tests / "test_fixture.py": b"assert True\n"}
            for path, payload in code_files.items():
                path.write_bytes(payload)
            role_bytes = b'{"entities":[]}'
            role_path = root / "research/p5_0b1r/role_split_seal.json"
            role_path.parent.mkdir(parents=True)
            role_path.write_bytes(role_bytes)
            firewall_path = root / "research/p5_0b2/scripts/source_label_firewall.py"
            firewall_path.parent.mkdir(parents=True)
            firewall_path.write_bytes(b"PINNED_FIREWALL_SOURCE\n")
            protocol = {
                "status": diagnostic.PROTOCOL_STATUS,
                "role_seal_sha256": hashlib.sha256(role_bytes).hexdigest(),
                "target_access": {"target_label_access": "NOT_AUTHORIZED"},
                "source_development": {
                    "source_label_firewall_sha256": hashlib.sha256(firewall_path.read_bytes()).hexdigest()
                },
            }
            protocol_bytes = json.dumps(protocol, sort_keys=True).encode()
            protocol_path = root / "research/p5_0b2/protocol_seal.json"
            protocol_path.parent.mkdir(parents=True, exist_ok=True)
            protocol_path.write_bytes(protocol_bytes)
            entries = [
                {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(data).hexdigest()}
                for path, data in code_files.items()
            ]
            implementation = {
                "status": "P5_0B3_PREACCESS_CODE_SEALED",
                "sealed_files": entries,
                "protocol": {"protocol_seal_sha256": hashlib.sha256(protocol_bytes).hexdigest()},
            }
            seal_path = root / "research/p5_0b3/implementation_seal.json"
            seal_path.write_text(json.dumps(implementation), encoding="utf-8")
            archive = root / "synthetic.zip"
            members = {member: b"substation ID;semantic\n1;SECRET\n" for member in ALLOWED_MEMBERS}
            with zipfile.ZipFile(archive, "w") as zipped:
                for member, payload in members.items():
                    zipped.writestr(member, payload)
            with patch.object(diagnostic, "ROLE_SEAL_SHA256", hashlib.sha256(role_bytes).hexdigest()), \
                    patch.object(diagnostic, "ARCHIVE_PATH", archive), \
                    patch.object(diagnostic, "ARCHIVE_SIZE", archive.stat().st_size), \
                    patch.object(subprocess, "run", side_effect=[
                        subprocess.CompletedProcess([], 0, "sealed-head\n", ""),
                        subprocess.CompletedProcess([], 0, "", ""),
                    ]):
                loaded_role, loaded_members = diagnostic._pinned_preflight(root, "sealed-head", archive)
            self.assertEqual(loaded_role, role_bytes)
            self.assertEqual(loaded_members, members)

    def test_identity_audit_never_calls_normal_firewall_stage_or_method(self):
        role_bytes, members = fixture()
        with patch.object(diagnostic, "ROLE_SEAL_SHA256", hashlib.sha256(role_bytes).hexdigest()), \
                patch("research.p5_0b2.scripts.source_label_firewall.execute_firewall",
                      side_effect=AssertionError("normal firewall called")), \
                patch("research.p5_0b3.scripts.source_stage_runner.run_stage",
                      side_effect=AssertionError("stage called")), \
                patch("research.p5_0b3.scripts.source_method_process.execute_method",
                      side_effect=AssertionError("method called"), create=True):
            self.assertEqual(
                diagnostic.identity_result(role_bytes, members),
                diagnostic.IDENTITY_ALL_RESOLVE_AFTER_DECIMAL_CANONICALIZATION,
            )


if __name__ == "__main__":
    unittest.main()
