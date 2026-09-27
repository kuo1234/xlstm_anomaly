"""Synthetic checks for the auditor-to-method SOURCE projection boundary."""

import hashlib
import unittest

from research.p5_0b3.scripts.source_projection import (
    EXPECTED_ROLE_SEAL_SHA256,
    ProjectionSealError,
    build_method_projection,
)


STRATA = [
    ("manufacturer 1", "SH + DHW", 8),
    ("manufacturer 1", "SH + DHW with sub-circuits", 11),
    ("manufacturer 2", "SH", 8),
    ("manufacturer 2", "SH + DHW", 12),
    ("manufacturer 2", "SH with buffer tank", 8),
]


def fixtures():
    roles = []
    manifest = []
    source_index = 0
    role_index = 0
    entities_per_stratum = [15, 15, 15, 15, 14]
    for (manufacturer, configuration_type, _), count in zip(STRATA, entities_per_stratum):
        for _ in range(count):
            role_index += 1
            entity_id = f"source-id-{role_index}"
            role_digest = hashlib.sha256(entity_id.encode()).hexdigest()
            path = f"{manufacturer}/operational_data/source_{role_index}.csv"
            row = {
                "manufacturer": manufacturer, "configuration_type": configuration_type,
                "entity_id": entity_id, "role": "SOURCE", "role_digest": role_digest,
            }
            roles.append(row)
            manifest.append({**row, "raw_path": path, "raw_sha256": hashlib.sha256(path.encode()).hexdigest()})
            source_index += 1
    for role in ("TARGET", "UNSUPPORTED_FOR_ENTITY_SPLIT"):
        extra_count = 16 if role == "TARGET" else 3
        for i in range(extra_count):
            role_index += 1
            manufacturer, configuration_type, _ = STRATA[i % len(STRATA)]
            entity_id = f"{role.lower()}-private-id-{i}"
            role_digest = hashlib.sha256(entity_id.encode()).hexdigest()
            path = f"{manufacturer}/operational_data/{role.lower()}_private_{i}.csv"
            row = {
                "manufacturer": manufacturer, "configuration_type": configuration_type,
                "entity_id": entity_id, "role": role, "role_digest": role_digest,
            }
            roles.append(row)
            manifest.append({**row, "raw_path": path, "raw_sha256": hashlib.sha256(path.encode()).hexdigest()})
    projection = {
        "schema_version": "p5-0b2-feature-projection-v2",
        "strata": [
            {"manufacturer": m, "configuration_type": c,
             "ordered_features": [f"feature_{i:02d}" for i in range(d)]}
            for m, c, d in STRATA
        ],
    }
    return roles, manifest, projection


class SourceProjectionTests(unittest.TestCase):
    def test_projection_contains_only_source_paths_and_no_entity_ids(self):
        roles, manifest, feature_projection = fixtures()
        projected, payload = build_method_projection(
            roles, manifest, feature_projection,
            role_seal_sha256=EXPECTED_ROLE_SEAL_SHA256,
            entity_manifest_sha256="a" * 64,
            feature_projection_sha256="b" * 64,
        )
        self.assertEqual(projected["source_entity_count"], 74)
        self.assertEqual(len(projected["source_entities"]), 74)
        self.assertTrue(all(item["role"] == "SOURCE" for item in projected["source_entities"]))
        self.assertTrue(all("entity_id" not in item for item in projected["source_entities"]))
        rendered = payload.decode("utf-8")
        self.assertNotIn("target_private_id", rendered)
        self.assertNotIn("unsupported_private_id", rendered)
        self.assertNotIn("target_private_", rendered)
        self.assertNotIn("unsupported_private_", rendered)
        self.assertEqual(len(projected["strata"]), 5)

    def test_cross_role_path_alias_fails_before_method_projection(self):
        roles, manifest, feature_projection = fixtures()
        manifest[-1]["raw_path"] = manifest[0]["raw_path"]
        with self.assertRaises(ProjectionSealError):
            build_method_projection(
                roles, manifest, feature_projection,
                role_seal_sha256=EXPECTED_ROLE_SEAL_SHA256,
                entity_manifest_sha256="a" * 64,
                feature_projection_sha256="b" * 64,
            )

    def test_wrong_role_seal_or_feature_schema_fails_closed(self):
        roles, manifest, feature_projection = fixtures()
        with self.assertRaises(ProjectionSealError):
            build_method_projection(
                roles, manifest, feature_projection,
                role_seal_sha256="0" * 64,
                entity_manifest_sha256="a" * 64,
                feature_projection_sha256="b" * 64,
            )
        feature_projection["strata"][0]["ordered_features"].append("other")
        with self.assertRaises(ProjectionSealError):
            build_method_projection(
                roles, manifest, feature_projection,
                role_seal_sha256=EXPECTED_ROLE_SEAL_SHA256,
                entity_manifest_sha256="a" * 64,
                feature_projection_sha256="b" * 64,
            )


if __name__ == "__main__":
    unittest.main()
