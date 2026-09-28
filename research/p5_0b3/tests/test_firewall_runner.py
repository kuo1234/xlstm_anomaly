from __future__ import annotations

import hashlib
import contextlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from research.p5_0b2.scripts import source_label_firewall
from research.p5_0b3.scripts.firewall_runner import (
    ALLOWED_MEMBERS,
    read_allowed_zip_members,
    run_firewall_from_members,
    run_firewall_from_zip,
)
from research.p5_0b3.scripts import firewall_process


class FirewallRunnerTests(unittest.TestCase):
    def _synthetic_inputs(self) -> tuple[dict[str, bytes], bytes]:
        role_payload = json.dumps(
            {"entities": [{
                "manufacturer": "manufacturer 1",
                "entity_id": "source-1",
                "role": "SOURCE",
                "role_digest": "d" * 64,
            }]},
            separators=(",", ":"),
        ).encode("utf-8")
        headers = {
            "faults": "substation ID;efd_possible;Possible anomaly start;Possible anomaly end;Report date\n",
            "normal_events": "substation ID;Event start;Event end\n",
            "disturbances": "substation ID;Event start;type\n",
        }
        members: dict[str, bytes] = {}
        for manufacturer in ("manufacturer 1", "manufacturer 2"):
            for table, header in headers.items():
                body = ""
                if manufacturer == "manufacturer 1" and table == "faults":
                    body = "source-1;true;2020-01-01;2020-01-02;\n"
                members[f"{manufacturer}/{table}.csv"] = (header + body).encode("utf-8")
        return members, role_payload

    def test_zip_runner_reads_allowlist_and_keeps_audit_out_of_method_output(self) -> None:
        members, role_bytes = self._synthetic_inputs()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "synthetic.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                for name, content in members.items():
                    zipped.writestr(name, content)
                # A traversal-like unrelated entry is ignored and never extracted.
                zipped.writestr("../../outside.txt", b"must-not-be-written")

            selected = read_allowed_zip_members(archive)
            self.assertEqual(set(selected), ALLOWED_MEMBERS)
            self.assertEqual(selected, members)
            self.assertFalse((root.parent / "outside.txt").exists())

            restricted = root / "restricted-audit"
            method = root / "method-input"
            with patch.object(
                source_label_firewall,
                "ROLE_SEAL_SHA256",
                hashlib.sha256(role_bytes).hexdigest(),
            ):
                result = run_firewall_from_zip(archive, role_bytes, restricted, method)

            self.assertEqual(set(result), {"source_artifact_sha256"})
            self.assertEqual(
                {path.name for path in restricted.iterdir()},
                {"source_labels.jsonl", "source_labels.sha256", "access_audit.json"},
            )
            self.assertEqual(
                {path.name for path in method.iterdir()},
                {"source_labels.jsonl", "source_labels.sha256"},
            )
            source = (method / "source_labels.jsonl").read_text(encoding="utf-8")
            self.assertIn('"role_digest":"' + "d" * 64 + '"', source)
            self.assertNotIn("source-1", source)
            self.assertNotIn("access_audit", json.dumps(result))
            audit = json.loads((restricted / "access_audit.json").read_text(encoding="utf-8"))
            self.assertNotIn("entity_id", audit)

    def test_missing_or_duplicate_allowlisted_zip_member_fails_closed(self) -> None:
        members, _ = self._synthetic_inputs()
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "bad.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                for name, content in members.items():
                    if name != sorted(ALLOWED_MEMBERS)[0]:
                        zipped.writestr(name, content)
                zipped.writestr(sorted(ALLOWED_MEMBERS)[1], members[sorted(ALLOWED_MEMBERS)[1]])
                zipped.writestr(sorted(ALLOWED_MEMBERS)[1], members[sorted(ALLOWED_MEMBERS)[1]])
            with self.assertRaises(source_label_firewall.FirewallError):
                read_allowed_zip_members(archive)

    def test_sealed_firewall_protocol_hash_pins_match(self) -> None:
        root = Path(__file__).resolve().parents[2]
        seal = json.loads((root / "p5_0b2" / "protocol_seal.json").read_text(encoding="utf-8"))
        expected = seal["source_development"]["source_label_firewall_sha256"]
        path = root / "p5_0b2" / "scripts" / "source_label_firewall.py"
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)

    def test_cli_emits_only_fixed_category_for_sensitive_failure(self):
        for category in sorted(source_label_firewall.FAILURE_CATEGORIES):
            output = io.StringIO()
            args = {"--archive": str(firewall_process.PINNED_ARCHIVE_PATH), "--role-seal": "/SECRET/role.json",
                    "--restricted-output": "/SECRET/restricted", "--method-output": "/SECRET/method"}
            with patch.object(firewall_process, "_arguments", return_value=args), \
                    patch.object(firewall_process, "_verify_firewall_pin"), \
                    patch.object(firewall_process, "PINNED_ARCHIVE_PATH", Path(args["--archive"])), \
                    patch.object(Path, "stat", return_value=type("Stat", (), {"st_size": firewall_process.PINNED_ARCHIVE_BYTES})()), \
                    patch.object(Path, "read_bytes", return_value=b"synthetic-role-seal"), \
                    patch.object(firewall_process, "PINNED_ROLE_SEAL_SHA256", hashlib.sha256(b"synthetic-role-seal").hexdigest()), \
                    patch.object(firewall_process, "run_firewall_from_zip",
                                 side_effect=source_label_firewall.FirewallError(category)), \
                    contextlib.redirect_stdout(output):
                code = firewall_process.main([])
            self.assertEqual(code, 2)
            self.assertEqual(output.getvalue(), f"P5_0B3_FIREWALL_BLOCKED {category}\n")
            self.assertNotIn("SECRET", output.getvalue())

    def test_cli_redacts_unexpected_exception_message_and_path(self):
        output = io.StringIO()
        archive = str(firewall_process.PINNED_ARCHIVE_PATH)
        args = {"--archive": archive, "--role-seal": "/SECRET/role.json",
                "--restricted-output": "/SECRET/restricted", "--method-output": "/SECRET/method"}
        sensitive = "SYNTHETIC_EXCEPTION /SECRET/private/label.csv"
        with patch.object(firewall_process, "_arguments", return_value=args), \
                patch.object(firewall_process, "_verify_firewall_pin"), \
                patch.object(firewall_process, "PINNED_ARCHIVE_PATH", Path(archive)), \
                patch.object(Path, "stat", return_value=type("Stat", (), {"st_size": firewall_process.PINNED_ARCHIVE_BYTES})()), \
                patch.object(Path, "read_bytes", return_value=b"synthetic-role-seal"), \
                patch.object(firewall_process, "PINNED_ROLE_SEAL_SHA256", hashlib.sha256(b"synthetic-role-seal").hexdigest()), \
                patch.object(firewall_process, "run_firewall_from_zip", side_effect=RuntimeError(sensitive)), \
                contextlib.redirect_stdout(output):
            code = firewall_process.main([])
        self.assertEqual(code, 2)
        self.assertEqual(output.getvalue(), "P5_0B3_FIREWALL_BLOCKED UNCLASSIFIED\n")
        self.assertNotIn(sensitive, output.getvalue())

    def test_input_member_staging_io_and_method_copy_io_have_distinct_categories(self):
        members, role_bytes = self._synthetic_inputs()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            restricted, method = root / "restricted", root / "method"
            real_write_bytes = Path.write_bytes
            write_count = 0

            def fail_second_write(path, payload):
                nonlocal write_count
                write_count += 1
                if write_count == 2:
                    raise OSError("SYNTHETIC_STAGE_SECRET /SECRET/member.csv")
                return real_write_bytes(path, payload)

            with patch.object(Path, "write_bytes", fail_second_write):
                with self.assertRaises(source_label_firewall.FirewallError) as raised:
                    run_firewall_from_members(members, role_bytes, restricted, method)
            self.assertEqual(raised.exception.category, "ARCHIVE_MEMBER_IO")
            self.assertEqual(str(raised.exception), "FIREWALL_FAILED")

        members, role_bytes = self._synthetic_inputs()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            restricted, method = root / "restricted", root / "method"
            payload = b""
            digest = hashlib.sha256(payload).hexdigest()

            def publish_empty_source(_paths, _role, destination):
                destination.mkdir(parents=True)
                (destination / "source_labels.jsonl").write_bytes(payload)
                (destination / "source_labels.sha256").write_text(digest + "\n", encoding="ascii")
                (destination / "access_audit.json").write_text("{}\n", encoding="utf-8")
                return {"source_artifact_sha256": digest}

            real_open = Path.open

            def fail_method_open(path, *args, **kwargs):
                if path.parent == method and path.name == "source_labels.jsonl":
                    raise OSError("SYNTHETIC_COPY_SECRET /SECRET/output.jsonl")
                return real_open(path, *args, **kwargs)

            with patch.object(source_label_firewall, "execute_firewall", side_effect=publish_empty_source), \
                    patch.object(Path, "open", fail_method_open):
                with self.assertRaises(source_label_firewall.FirewallError) as raised:
                    run_firewall_from_members(members, role_bytes, restricted, method)
            self.assertEqual(raised.exception.category, "METHOD_ARTIFACT_COPY_OR_DIGEST")
            self.assertEqual(str(raised.exception), "FIREWALL_FAILED")


if __name__ == "__main__":
    unittest.main()
