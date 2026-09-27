"""Synthetic checks for the P5-0B3 SOURCE-only raw access boundary."""

from __future__ import annotations

import hashlib
import unittest

from research.p5_0b3.scripts.source_access_gate import (
    SourceAccessGateError,
    build_source_projection,
    execute_source_access_gate,
    execute_projected_source_access_gate,
)


def fixtures():
    role_digests = {key: hashlib.sha256(key.encode()).hexdigest()
                    for key in ("s1", "s2", "t1", "u1")}
    entities = [
        {"manufacturer": "m", "configuration_type": "c", "entity_id": "s1", "role": "SOURCE", "role_digest": role_digests["s1"]},
        {"manufacturer": "m", "configuration_type": "c", "entity_id": "s2", "role": "SOURCE", "role_digest": role_digests["s2"]},
        {"manufacturer": "m", "configuration_type": "c", "entity_id": "t1", "role": "TARGET", "role_digest": role_digests["t1"]},
        {"manufacturer": "m", "configuration_type": "c", "entity_id": "u1", "role": "UNSUPPORTED_FOR_ENTITY_SPLIT", "role_digest": role_digests["u1"]},
    ]
    payloads = {"source/1.csv": b"s1", "source/2.csv": b"s2", "target/private.csv": b"target", "unsupported.csv": b"unsupported"}
    manifest = [
        {**row, "raw_path": path, "raw_sha256": hashlib.sha256(payloads[path]).hexdigest()}
        for row, path in zip(entities, payloads)
    ]
    return entities, manifest, payloads


class SourceAccessGateTests(unittest.TestCase):
    def test_projection_is_source_only(self):
        entities, manifest, _ = fixtures()
        projection = build_source_projection(entities, manifest, expected_source_entities=2)
        self.assertEqual({row["role_digest"] for row in projection}, {
            hashlib.sha256(b"s1").hexdigest(), hashlib.sha256(b"s2").hexdigest()
        })
        self.assertTrue(all(row["role"] == "SOURCE" for row in projection))
        self.assertTrue(all("entity_id" not in row for row in projection))
        serialized = repr(projection)
        self.assertNotIn("t1", serialized)
        self.assertNotIn("target/private.csv", serialized)
        self.assertNotIn("u1", serialized)

    def test_unsupported_structural_row_may_have_no_split_digest(self):
        entities, manifest, _ = fixtures()
        entities[-1]["role_digest"] = ""
        manifest[-1]["role_digest"] = ""
        entities[-1]["configuration_type"] = ""
        manifest[-1]["configuration_type"] = ""
        projection = build_source_projection(entities, manifest, expected_source_entities=2)
        self.assertEqual(len(projection), 2)
        self.assertTrue(all(item["role"] == "SOURCE" for item in projection))

    def test_source_and_target_rows_still_require_valid_unique_split_digests(self):
        for index in (0, 2):
            entities, manifest, _ = fixtures()
            entities[index]["role_digest"] = ""
            manifest[index]["role_digest"] = ""
            with self.assertRaises(SourceAccessGateError):
                build_source_projection(entities, manifest, expected_source_entities=2)

    def test_opens_hashes_and_stages_only_source_paths(self):
        entities, manifest, payloads = fixtures()
        opened = []
        staged = []

        def opener(path):
            opened.append(path)
            return payloads[path]

        projection, audit = execute_source_access_gate(
            entities,
            manifest,
            opener=opener,
            stager=lambda entry, payload: staged.append((entry["raw_path"], payload)),
            expected_source_entities=2,
        )
        self.assertEqual(set(opened), {"source/1.csv", "source/2.csv"})
        self.assertEqual(len(opened), 2)
        self.assertEqual({path for path, _ in staged}, {"source/1.csv", "source/2.csv"})
        self.assertEqual(
            audit,
            {
                "expected_source_entities": 2,
                "opened_source_files": 2,
                "target_operational_files_opened": 0,
                "target_semantic_rows_released": 0,
            },
        )
        self.assertTrue(all(item["role"] == "SOURCE" for item in projection))

    def test_duplicate_path_across_roles_fails_before_any_open(self):
        entities, manifest, payloads = fixtures()
        manifest[2]["raw_path"] = "./" + manifest[0]["raw_path"]
        opened = []
        with self.assertRaises(SourceAccessGateError):
            execute_source_access_gate(
                entities,
                manifest,
                opener=lambda path: opened.append(path) or payloads[path],
                stager=lambda *_: self.fail("must not stage"),
                expected_source_entities=2,
            )
        self.assertEqual(opened, [])

    def test_role_manifest_mismatch_fails_before_open(self):
        entities, manifest, _ = fixtures()
        manifest[0]["role"] = "TARGET"
        opened = []
        with self.assertRaises(SourceAccessGateError):
            execute_source_access_gate(
                entities,
                manifest,
                opener=lambda path: opened.append(path) or b"unexpected",
                stager=lambda *_: None,
                expected_source_entities=2,
            )
        self.assertEqual(opened, [])

    def test_source_count_mismatch_fails_before_open(self):
        entities, manifest, _ = fixtures()
        opened = []
        with self.assertRaises(SourceAccessGateError):
            execute_source_access_gate(
                entities,
                manifest,
                opener=lambda path: opened.append(path) or b"unexpected",
                stager=lambda *_: None,
                expected_source_entities=74,
            )
        self.assertEqual(opened, [])

    def test_invalid_hash_syntax_fails_before_open(self):
        entities, manifest, _ = fixtures()
        manifest[0]["raw_sha256"] = "not-a-sha256"
        opened = []
        with self.assertRaises(SourceAccessGateError):
            execute_source_access_gate(
                entities,
                manifest,
                opener=lambda path: opened.append(path) or b"unexpected",
                stager=lambda *_: None,
                expected_source_entities=2,
            )
        self.assertEqual(opened, [])

    def test_hash_mismatch_fails_closed(self):
        entities, manifest, _ = fixtures()
        with self.assertRaises(SourceAccessGateError):
            execute_source_access_gate(
                entities,
                manifest,
                opener=lambda _: b"wrong payload",
                stager=lambda *_: self.fail("bad bytes must not be staged"),
                expected_source_entities=2,
            )

    def test_method_gate_rejects_non_source_fields_before_open(self):
        entities, manifest, payloads = fixtures()
        projection = build_source_projection(entities, manifest, expected_source_entities=2)
        projection[0]["entity_id"] = "must-not-pass"
        opened = []
        with self.assertRaises(SourceAccessGateError):
            execute_projected_source_access_gate(
                projection,
                opener=lambda path: opened.append(path) or payloads[path],
                stager=lambda *_: self.fail("must not stage"),
                expected_source_entities=2,
            )
        self.assertEqual(opened, [])

    def test_method_gate_opens_only_exact_projected_sources(self):
        entities, manifest, payloads = fixtures()
        projection = build_source_projection(entities, manifest, expected_source_entities=2)
        opened = []
        seen = []
        result, audit = execute_projected_source_access_gate(
            projection,
            opener=lambda path: opened.append(path) or payloads[path],
            stager=lambda entry, content: seen.append((entry["role_digest"], content)),
            expected_source_entities=2,
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(len(seen), 2)
        self.assertEqual(set(opened), {"source/1.csv", "source/2.csv"})
        self.assertEqual(audit["target_operational_files_opened"], 0)


if __name__ == "__main__":
    unittest.main()
