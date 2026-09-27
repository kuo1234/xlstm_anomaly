"""Auditor-side pinned SOURCE projection builder; performs no data opens."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Mapping, Sequence

from research.p5_0b3.scripts.source_access_gate import build_source_projection


EXPECTED_SOURCE_COUNT = 74
EXPECTED_FEATURE_COUNTS = (8, 11, 8, 12, 8)
EXPECTED_ROLE_SEAL_SHA256 = "00e0cec62d238c78f2d0b3c79910c0ffaf1122d1582c28c8848022fb3e10e33f"


class ProjectionSealError(RuntimeError):
    """Generic structural projection failure with no input details."""

    def __init__(self) -> None:
        super().__init__("SOURCE_PROJECTION_SEAL_FAILED")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _fail() -> None:
    raise ProjectionSealError() from None


def _canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                        ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def build_method_projection(
    role_entities: Sequence[Mapping[str, object]],
    manifest_rows: Sequence[Mapping[str, object]],
    feature_projection: Mapping[str, object],
    *,
    role_seal_sha256: str,
    entity_manifest_sha256: str,
    feature_projection_sha256: str,
    expected_source_entities: int = EXPECTED_SOURCE_COUNT,
) -> tuple[dict[str, object], bytes]:
    """Validate the complete role/path relation and emit SOURCE-only JSON."""
    try:
        if (role_seal_sha256 != EXPECTED_ROLE_SEAL_SHA256 or
                expected_source_entities != EXPECTED_SOURCE_COUNT or
                feature_projection.get("schema_version") != "p5-0b2-feature-projection-v2"):
            _fail()
        rows = [dict(row) for row in role_entities]
        manifest = [dict(row) for row in manifest_rows]
        source_rows = build_source_projection(
            rows, manifest, expected_source_entities=expected_source_entities
        )

        raw_strata = feature_projection.get("strata")
        if not isinstance(raw_strata, list):
            _fail()
        strata: list[dict[str, object]] = []
        seen_strata: set[tuple[str, str]] = set()
        for item in raw_strata:
            if not isinstance(item, dict):
                _fail()
            manufacturer = item.get("manufacturer")
            configuration_type = item.get("configuration_type")
            ordered = item.get("ordered_features")
            key = (manufacturer, configuration_type)
            if (not all(isinstance(x, str) and x for x in key) or
                    key in seen_strata or not isinstance(ordered, list) or
                    not ordered or any(not isinstance(x, str) or not x for x in ordered) or
                    len(ordered) != len(set(ordered)) or ordered != sorted(ordered)):
                _fail()
            seen_strata.add(key)
            strata.append({
                "manufacturer": manufacturer,
                "configuration_type": configuration_type,
                "ordered_features": list(ordered),
                "feature_count": len(ordered),
                "feature_schema_sha256": _sha256(_canonical_json(ordered)),
            })
        strata.sort(key=lambda item: (item["manufacturer"], item["configuration_type"]))
        if len(strata) != 5 or tuple(item["feature_count"] for item in strata) != EXPECTED_FEATURE_COUNTS:
            _fail()
        source_strata = {(row["manufacturer"], row["configuration_type"])
                         for row in source_rows}
        if source_strata != seen_strata:
            _fail()

        membership = sorted(row["role_digest"] for row in source_rows)
        membership_bytes = ("P5-0B3-SOURCE-MEMBERSHIP-v1\n" +
                            "\n".join(membership) + "\n").encode("ascii")
        method_projection: dict[str, object] = {
            "schema_version": "p5-0b3-source-method-input-v1",
            "source_entities": source_rows,
            "source_entity_count": EXPECTED_SOURCE_COUNT,
            "source_membership_sha256": _sha256(membership_bytes),
            "strata": strata,
            "pinned_inputs": {
                "role_seal_sha256": role_seal_sha256,
                "entity_manifest_sha256": entity_manifest_sha256,
                "feature_projection_sha256": feature_projection_sha256,
            },
        }
        payload = _canonical_json(method_projection)
        return method_projection, payload
    except ProjectionSealError:
        raise
    except Exception:
        _fail()


def build_pinned_method_projection(repository_root: str | Path) -> tuple[dict[str, object], bytes]:
    """Read and hash only pinned structural inputs, then return SOURCE-only JSON."""
    try:
        root = Path(repository_root)
        protocol_path = root / "research/p5_0b2/protocol_seal.json"
        protocol_bytes = protocol_path.read_bytes()
        protocol = json.loads(protocol_bytes)
        if (protocol.get("status") != "P5_0B2R2_PROTOCOL_RESEALED" or
                protocol.get("information_boundary", {}).get("target_label_access") != "NOT_AUTHORIZED" or
                protocol.get("target_access", {}).get("target_label_access") != "NOT_AUTHORIZED"):
            _fail()
        sealed = {item["path"]: item["sha256"] for item in protocol["sealed_artifacts"]}

        structural_path = root / "research/p5_0b2/structural_inputs_seal.json"
        structural_bytes = structural_path.read_bytes()
        if _sha256(structural_bytes) != sealed.get("research/p5_0b2/structural_inputs_seal.json"):
            _fail()
        structural = json.loads(structural_bytes)

        role_path = root / "research/p5_0b1r/role_split_seal.json"
        role_bytes = role_path.read_bytes()
        role_hash = _sha256(role_bytes)
        if role_hash != structural.get("role_seal", {}).get("sha256"):
            _fail()
        if role_hash != EXPECTED_ROLE_SEAL_SHA256:
            _fail()
        role_doc = json.loads(role_bytes)
        role_entities = [
            {key: item.get(key) for key in
             ("manufacturer", "configuration_type", "entity_id", "role", "role_digest")}
            for item in role_doc.get("entities", [])
        ]

        manifest_path = root / "research/p5_0b1r/entity_manifest.csv"
        manifest_bytes = manifest_path.read_bytes()
        manifest_hash = _sha256(manifest_bytes)
        pinned_manifest_hash = structural.get("referenced_structural_artifacts", {}).get(
            "research/p5_0b1r/entity_manifest.csv"
        )
        if manifest_hash != pinned_manifest_hash:
            _fail()
        manifest_text = manifest_bytes.decode("utf-8")
        with __import__("io").StringIO(manifest_text, newline="") as stream:
            reader = csv.DictReader(stream)
            required = {"manufacturer", "entity_id", "configuration_type", "role",
                        "role_digest", "raw_path", "raw_sha256"}
            if reader.fieldnames is None or not required.issubset(reader.fieldnames):
                _fail()
            manifest_rows = [
                {key: row.get(key) for key in required}
                for row in reader
            ]

        feature_path = root / "research/p5_0b2/feature_projection.json"
        feature_bytes = feature_path.read_bytes()
        feature_hash = _sha256(feature_bytes)
        if feature_hash != sealed.get("research/p5_0b2/feature_projection.json"):
            _fail()
        projection = json.loads(feature_bytes)
        return build_method_projection(
            role_entities, manifest_rows, projection,
            role_seal_sha256=role_hash,
            entity_manifest_sha256=manifest_hash,
            feature_projection_sha256=feature_hash,
        )
    except ProjectionSealError:
        raise
    except Exception:
        _fail()


def write_projection_atomic(destination: str | Path, payload: bytes) -> str:
    """Write a SOURCE-only method input with restrictive permissions."""
    path = Path(destination)
    parent = path.parent
    try:
        if path.exists():
            _fail()
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(parent, 0o700)
        fd, temporary = tempfile.mkstemp(prefix=".source-projection-", dir=parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            directory_fd = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except Exception:
            Path(temporary).unlink(missing_ok=True)
            raise
        return _sha256(payload)
    except ProjectionSealError:
        raise
    except Exception:
        _fail()


def main(argv: list[str] | None = None) -> int:
    """Prepare the value-free SOURCE projection without opening raw members."""
    try:
        args = sys.argv[1:] if argv is None else argv
        if len(args) != 2 or args[0] != "--output" or not args[1]:
            raise ProjectionSealError()
        _, payload = build_pinned_method_projection(Path.cwd())
        digest = write_projection_atomic(args[1], payload)
        print(f"P5_0B3_SOURCE_PROJECTION_OK {digest}")
        return 0
    except Exception:
        print("P5_0B3_SOURCE_PROJECTION_FAILED")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
