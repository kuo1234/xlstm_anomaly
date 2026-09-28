"""Synthetic boundary checks for the auditor and SOURCE method processes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch

import numpy as np

from research.p5_0b3.scripts import source_method_process as method
from research.p5_0b3.scripts import source_stage_runner as runner
from research.p5_0b3.tests.test_source_projection import STRATA, fixtures


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


class SourceProcessBoundaryTests(unittest.TestCase):
    def test_method_labels_require_source_membership_and_valid_kind_source(self):
        digest = "a" * 64
        row = {
            "role_digest": digest, "annotation_source": "faults",
            "annotation_kind": "KNOWN_FAULT", "interval_start": "2020-01-01T00:00:00",
            "interval_end": "2020-01-01T00:01:00",
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "labels.jsonl"
            payload = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
            path.write_bytes(payload)
            result = method._load_labels(path, hashlib.sha256(payload).hexdigest(), {digest})
            self.assertEqual(len(result[digest]), 1)
            with self.assertRaises(method.MethodFailure):
                method._load_labels(path, hashlib.sha256(payload).hexdigest(), {"b" * 64})
            row["annotation_source"] = "normal_events"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaises(method.MethodFailure):
                method._load_labels(path, hashlib.sha256(path.read_bytes()).hexdigest(), {digest})

    def test_runtime_record_requires_nested_pinned_lock_and_deterministic_cpu(self):
        record = {
            "status": "PASS",
            "code": {"efd_commit": method.EFD_COMMIT,
                     "runtime_lock_sha256": method.RUNTIME_LOCK_SHA256, "python": "3.12.3"},
            "runtime": {"tensorflow": "2.18.1", "keras": "3.15.1", "numpy": "1.26.4",
                        "device": "CPU", "deterministic_ops": True,
                        "intra_threads": 1, "inter_threads": 1},
        }
        self.assertTrue(method.runtime_preflight_is_pinned(record))
        self.assertTrue(runner.runtime_preflight_is_pinned(record))
        top_level_only = {**record, "code": {key: value for key, value in record["code"].items()
                                               if key != "runtime_lock_sha256"},
                          "runtime_lock_sha256": method.RUNTIME_LOCK_SHA256}
        self.assertFalse(method.runtime_preflight_is_pinned(top_level_only))
        self.assertFalse(runner.runtime_preflight_is_pinned(top_level_only))

    def test_synthetic_runtime_preflight_uses_pinned_child_and_private_stderr(self):
        record = {"status": "PASS", "code": {"pinned": "code"},
                  "runtime": {"device": "CPU"}, "result": {"runs": 2}}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stderr_path = root / "private" / "runtime.stderr"
            completed = __import__("subprocess").CompletedProcess(
                [], 0, json.dumps(record, separators=(",", ":")) + "\n", "TF warning\n"
            )
            with patch.object(runner.subprocess, "run", return_value=completed) as run:
                runner._run_synthetic_runtime_preflight(root, Path("/synthetic/efd"), record, stderr_path)
            command = run.call_args.args[0]
            env = run.call_args.kwargs["env"]
            self.assertEqual(command[0], runner.sys.executable)
            self.assertIn("research.p5_0b3.scripts.runtime_preflight", command)
            self.assertEqual(env["P5_EFD_SOURCE"], "/synthetic/efd")
            self.assertEqual(env["CUDA_VISIBLE_DEVICES"], "-1")
            self.assertEqual(stderr_path.read_text(encoding="utf-8"), "TF warning\n")

    def test_method_projection_schema_rejects_non_source_or_extra_metadata(self):
        roles, manifest, feature_projection = fixtures()
        from research.p5_0b3.scripts.source_projection import (
            EXPECTED_ROLE_SEAL_SHA256, build_method_projection,
        )
        value, _ = build_method_projection(
            roles, manifest, feature_projection, role_seal_sha256=EXPECTED_ROLE_SEAL_SHA256,
            entity_manifest_sha256="a" * 64, feature_projection_sha256=method.FEATURE_PROJECTION_SHA256,
        )
        value["pinned_inputs"]["role_seal_sha256"] = method.ROLE_SEAL_SHA256
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "projection.json"
            payload = canonical(value); path.write_bytes(payload)
            self.assertEqual(len(method._load_projection(path, hashlib.sha256(payload).hexdigest())["source_entities"]), 74)
            value["source_entities"][0]["role"] = "TARGET"
            payload = canonical(value); path.write_bytes(payload)
            with self.assertRaises(method.MethodFailure):
                method._load_projection(path, hashlib.sha256(payload).hexdigest())

    def test_method_projection_requires_exact_unique_strata_before_archive_stage(self):
        roles, manifest, feature_projection = fixtures()
        from research.p5_0b3.scripts.source_projection import (
            EXPECTED_ROLE_SEAL_SHA256, build_method_projection,
        )
        value, _ = build_method_projection(
            roles, manifest, feature_projection, role_seal_sha256=EXPECTED_ROLE_SEAL_SHA256,
            entity_manifest_sha256="a" * 64, feature_projection_sha256=method.FEATURE_PROJECTION_SHA256,
        )
        value["pinned_inputs"]["role_seal_sha256"] = method.ROLE_SEAL_SHA256
        value["strata"][1] = dict(value["strata"][0])
        payload = canonical(value)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "projection.json"
            path.write_bytes(payload)
            with self.assertRaises(method.MethodFailure):
                method._load_projection(path, hashlib.sha256(payload).hexdigest())

    def test_save_load_replay_tolerance_and_phase_wide_failure(self):
        class Model:
            def __init__(self, delta=0.0):
                self.delta = delta

            def predict(self, values, verbose=0):
                return np.asarray(values) + self.delta

        values = np.ones((3, 2), dtype=np.float32)
        expected_scores = np.zeros(3, dtype=np.float64)
        replay = method._check_replay(Model(), Model(), values, expected_scores)
        self.assertEqual(replay["model_max_absolute_delta"], 0.0)
        self.assertEqual(replay["score_max_absolute_delta"], 0.0)
        replay = method._check_replay(Model(), Model(1e-8), values, expected_scores)
        self.assertLessEqual(replay["model_max_absolute_delta"], 1e-7)
        self.assertLessEqual(replay["score_max_absolute_delta"], 1e-7)
        with self.assertRaises(method.PhaseWideFailure):
            method._check_replay(Model(), Model(1e-3), values, expected_scores)

    def test_execute_method_opens_only_projected_members_while_zip_is_open(self):
        roles, manifest, feature_projection = fixtures()
        features_by_key = {
            (item["manufacturer"], item["configuration_type"]): item["ordered_features"]
            for item in feature_projection["strata"]
        }
        role_by_id = {(row["manufacturer"], row["entity_id"]): row for row in roles}
        raw_payloads = {}
        for row in roles:
            if row["role"] != "SOURCE":
                continue
            feature_names = features_by_key[(row["manufacturer"], row["configuration_type"])]
            payload = ("time," + ",".join(feature_names) + "\n2020-01-01T00:00:00," +
                       ",".join("1" for _ in feature_names) + "\n").encode()
            raw_payloads[row["role_digest"]] = payload
        source_path_to_bytes = {}
        for item in manifest:
            role = role_by_id[(item["manufacturer"], item["entity_id"])]
            if role["role"] == "SOURCE":
                payload = raw_payloads[role["role_digest"]]
                item["raw_sha256"] = hashlib.sha256(payload).hexdigest()
                source_path_to_bytes[item["raw_path"]] = payload
        from research.p5_0b3.scripts.source_projection import (
            EXPECTED_ROLE_SEAL_SHA256, build_method_projection,
        )
        projection, _ = build_method_projection(
            roles, manifest, feature_projection, role_seal_sha256=EXPECTED_ROLE_SEAL_SHA256,
            entity_manifest_sha256="a" * 64, feature_projection_sha256=method.FEATURE_PROJECTION_SHA256,
        )
        projection["pinned_inputs"]["role_seal_sha256"] = method.ROLE_SEAL_SHA256
        labels_payload = b""
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            archive = base / "synthetic-source-only.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                for path, payload in source_path_to_bytes.items():
                    zipped.writestr(path, payload)
            labels = base / "source_labels.jsonl"
            labels.write_bytes(labels_payload)
            output = base / "method-output"
            with patch.object(method, "_runtime", return_value=(object, lambda seed: None)):
                result = method.execute_method(
                    projection, archive, labels, hashlib.sha256(labels_payload).hexdigest(),
                    output, base / "synthetic-efd",
                )
            self.assertEqual(result["opened_source_files"], 74)
            self.assertEqual(result["stratum_count"], 5)
            summary = json.loads((output / "source_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["access_audit"]["opened_source_files"], 74)
            self.assertTrue(all(row["status"] == "SOURCE_MODEL_NOT_EVALUABLE" for row in summary["strata"]))
            self.assertEqual(len(summary["strata"]), 5)
            self.assertEqual(len({(row["manufacturer"], row["configuration_type"])
                                  for row in summary["strata"]}), 5)
            audits = sorted((output / "source_artifacts").glob("stratum_*_audit.json"))
            self.assertEqual(len(audits), 5)
            audit_values = [json.loads(path.read_text(encoding="utf-8")) for path in audits]
            self.assertTrue(all("pipeline_diagnostics" in item for item in audit_values))
            self.assertTrue(all(item["pipeline_diagnostics"]["status"] == "SOURCE_MODEL_NOT_EVALUABLE"
                                for item in audit_values))
            self.assertTrue(all("fold_support" in item["pipeline_diagnostics"]
                                for item in audit_values))
            self.assertTrue(all(item["pipeline_diagnostics"]["failure_stage"] == "fold_support_gate"
                                for item in audit_values))

    def test_source_parse_failure_is_scoped_to_its_stratum(self):
        rows = []
        by_digest = {}
        staged = {}
        features = {}
        intervals = {}
        for index, (manufacturer, config, dimension) in enumerate(STRATA):
            digest = f"{index + 1:064x}"
            key = (manufacturer, config)
            row = {"manufacturer": manufacturer, "configuration_type": config,
                   "role_digest": digest, "role": "SOURCE"}
            rows.append(row); by_digest[digest] = row; intervals[digest] = []
            names = [f"feature_{j:02d}" for j in range(dimension)]
            features[key] = names
            if index == 0:
                staged[digest] = b"not,a,valid,projection\n1,2,3,4\n"
            else:
                staged[digest] = ("time," + ",".join(names) + "\n2020-01-01T00:00:00," +
                                  ",".join("1" for _ in names) + "\n").encode()
        parsed, failures = method._parse_projected_entities(rows, by_digest, staged, features, intervals)
        self.assertEqual(failures, {STRATA[0][:2]})
        self.assertEqual(parsed[STRATA[0][:2]], [])
        self.assertTrue(all(parsed[key] for key in (item[:2] for item in STRATA[1:])))

    def test_launcher_keeps_restricted_audit_out_of_method_arguments(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            output, private = base / "out", base / "private"
            commands = []
            root = base / "repo"
            root.mkdir()

            def fake_run(command, env, prefix, *, cwd, private_stderr_path):
                commands.append((prefix.strip(), command))
                private_stderr_path.parent.mkdir(parents=True, exist_ok=True)
                private_stderr_path.write_text("synthetic TF warning", encoding="utf-8")
                if prefix.startswith("P5_0B3_SOURCE_PROJECTION"):
                    (output / "source_projection.json").write_text("{}", encoding="utf-8")
                    return prefix + hashlib.sha256((output / "source_projection.json").read_bytes()).hexdigest()
                if prefix.startswith("P5_0B3_FIREWALL"):
                    method_dir = Path(command[command.index("--method-output") + 1])
                    method_dir.mkdir()
                    payload = b"{}\n"
                    (method_dir / "source_labels.jsonl").write_bytes(payload)
                    (method_dir / "source_labels.sha256").write_text(hashlib.sha256(payload).hexdigest() + "\n")
                    return prefix + hashlib.sha256(payload).hexdigest()
                return prefix + "74 5"

            def fake_sha(path):
                if Path(path).name == "role_split_seal.json":
                    return runner.PINNED_ROLE_SEAL_SHA256
                return hashlib.sha256(Path(path).read_bytes()).hexdigest()
            def fake_preflight(*args, **kwargs):
                commands.append("RUNTIME_PREFLIGHT")
                stderr_path = kwargs["runtime_stderr_path"]
                stderr_path.parent.mkdir(parents=True, mode=0o700)
                stderr_path.write_text("synthetic preflight warning", encoding="utf-8")
            with patch.object(runner, "preflight", side_effect=fake_preflight), patch.object(runner, "_sha", side_effect=fake_sha), patch.object(runner, "_run", side_effect=fake_run):
                runner.run_stage(root, sealed_commit="c" * 40,
                                 archive=Path("/synthetic/archive.zip"),
                                 efd_source=Path("/synthetic/efd"), output_root=output,
                                 private_audit_root=private)
            self.assertEqual(commands[0], "RUNTIME_PREFLIGHT")
            self.assertTrue(commands[2][0].startswith("P5_0B3_FIREWALL_OK"))
            firewall_args = commands[2][1]
            method_args = commands[3][1]
            self.assertIn("--restricted-output", firewall_args)
            self.assertNotIn("--restricted-output", method_args)
            self.assertNotIn(str(private), " ".join(method_args))
            self.assertIn("--projection", method_args)
            self.assertIn("--labels", method_args)
            self.assertNotIn("--role-seal", method_args)
            self.assertTrue((private / "method.stderr").is_file())
            self.assertEqual((private / "runtime_preflight.stderr").read_text(encoding="utf-8"),
                             "synthetic preflight warning")
            self.assertEqual(private.stat().st_mode & 0o777, 0o700)

    def test_implementation_seal_requires_complete_exact_file_set(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scripts, tests = root / "research/p5_0b3/scripts", root / "research/p5_0b3/tests"
            scripts.mkdir(parents=True); tests.mkdir(parents=True)
            files = {scripts / "a.py": b"a=1\n", tests / "test_a.py": b"assert True\n"}
            entries = []
            for path, payload in files.items():
                path.write_bytes(payload)
                entries.append({"path": path.relative_to(root).as_posix(),
                                "sha256": hashlib.sha256(payload).hexdigest()})
            seal = {"status": "P5_0B3_PREACCESS_CODE_SEALED", "sealed_files": entries,
                    "runtime_preflight_result_sha256": "e5ea82ab60d69e1578d4cef835e815c83e1d0fdb63eaa17a645557cbac9cb939",
                    "runtime_lock_sha256": runner.RUNTIME_LOCK_SHA256}
            seal_path = root / "research/p5_0b3/implementation_seal.json"
            seal_path.write_text(json.dumps(seal), encoding="utf-8")
            runner.verify_implementation_seal(root)
            files[scripts / "b.py"] = b"b=2\n"
            (scripts / "b.py").write_bytes(files[scripts / "b.py"])
            with self.assertRaises(runner.StageFailure):
                runner.verify_implementation_seal(root)

    def test_runner_preserves_fixed_terminal_firewall_and_backbone_tokens(self):
        categories = sorted(runner.FIREWALL_FAILURE_CATEGORIES)
        for token in ([f"P5_0B3_FIREWALL_BLOCKED {item}" for item in categories]
                      + ["P5_0B3_BACKBONE_NOT_ADMISSIBLE"]):
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                result = __import__("subprocess").CompletedProcess([], 2, token + "\n", "warning\n")
                with patch.object(runner.subprocess, "run", return_value=result):
                    with self.assertRaises(runner.StageFailure) as raised:
                        runner._run(["python"], {}, "P5_0B3_METHOD_OK ", cwd=root,
                                    private_stderr_path=root / "private.stderr")
                self.assertEqual(str(raised.exception), token)
                self.assertEqual((root / "private.stderr").read_text(encoding="utf-8"), "warning\n")

    def test_runner_rejects_non_enum_firewall_stdout(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = __import__("subprocess").CompletedProcess([], 2,
                "P5_0B3_FIREWALL_BLOCKED /SECRET/path\n", "sensitive exception text\n")
            with patch.object(runner.subprocess, "run", return_value=result):
                with self.assertRaises(runner.StageFailure) as raised:
                    runner._run(["python"], {}, "P5_0B3_METHOD_OK ", cwd=root,
                                private_stderr_path=root / "private.stderr")
            self.assertEqual(str(raised.exception), "P5_0B3_STAGE_BLOCKED")

    def test_projection_builder_exposes_only_source_role_rows(self):
        roles, manifest, projection = fixtures()
        from research.p5_0b3.scripts.source_projection import (
            EXPECTED_ROLE_SEAL_SHA256, build_method_projection,
        )
        result, payload = build_method_projection(
            roles, manifest, projection, role_seal_sha256=EXPECTED_ROLE_SEAL_SHA256,
            entity_manifest_sha256="a" * 64, feature_projection_sha256="b" * 64,
        )
        self.assertEqual(result["source_entity_count"], 74)
        self.assertTrue(all(row["role"] == "SOURCE" for row in result["source_entities"]))
        self.assertNotIn(b"target_private_id", payload)
        self.assertNotIn(b"unsupported_private_id", payload)
        self.assertEqual({(s["manufacturer"], s["configuration_type"]) for s in result["strata"]},
                         {(m, c) for m, c, _ in STRATA})


if __name__ == "__main__":
    unittest.main()
