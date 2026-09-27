"""SOURCE-only operational path projection and access gate for P5-0B3.

Callers may parse the committed structural CSV, then pass its rows here. This
module validates the complete role/manifest relationship before an injected
opener can access any operational file. Errors are deliberately value-free.
"""

from __future__ import annotations

import hashlib
import posixpath
import re
from collections.abc import Callable, Iterable, Mapping
from pathlib import PurePosixPath


EXPECTED_SOURCE_ENTITIES = 74
EXPECTED_ROLES = {"SOURCE", "TARGET", "UNSUPPORTED_FOR_ENTITY_SPLIT"}


class SourceAccessGateError(RuntimeError):
    """Fail-closed, value-free access-gate error."""

    def __init__(self) -> None:
        super().__init__("SOURCE_ACCESS_GATE_FAILED")


def _fail() -> None:
    raise SourceAccessGateError() from None


def _required_text(row: Mapping[str, object], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        _fail()
    return value.strip()


def _canonical_relative_path(value: str) -> str:
    """Normalize a relative POSIX path and reject traversal or ambiguity."""
    if "\\" in value or PurePosixPath(value).is_absolute():
        _fail()
    normalized = posixpath.normpath(value)
    if normalized in {"", ".", ".."} or normalized.startswith("../") or normalized != value:
        _fail()
    return normalized


def build_source_projection(
    role_entities: Iterable[Mapping[str, object]],
    manifest_rows: Iterable[Mapping[str, object]],
    *,
    expected_source_entities: int = EXPECTED_SOURCE_ENTITIES,
) -> list[dict[str, str]]:
    """Validate every role row against the manifest and return SOURCE only.

    The full manifest's ``raw_path`` uniqueness check happens before this
    function returns any paths to the caller, and the returned dictionaries
    contain no TARGET/unsupported identities or paths.
    """
    try:
        roles: dict[tuple[str, str], dict[str, str]] = {}
        role_digests: set[str] = set()
        for raw in role_entities:
            manufacturer = _required_text(raw, "manufacturer")
            entity_id = _required_text(raw, "entity_id")
            role = _required_text(raw, "role")
            configuration_type = _required_text(raw, "configuration_type")
            if role not in EXPECTED_ROLES:
                _fail()
            key = (manufacturer, entity_id)
            if key in roles:
                _fail()
            role_digest = str(raw.get("role_digest", "")).strip()
            if (re.fullmatch(r"[0-9a-f]{64}", role_digest) is None or
                    role_digest in role_digests):
                _fail()
            role_digests.add(role_digest)
            roles[key] = {
                "manufacturer": manufacturer,
                "entity_id": entity_id,
                "configuration_type": configuration_type,
                "role": role,
                "role_digest": role_digest,
            }

        manifest: dict[tuple[str, str], dict[str, str]] = {}
        raw_paths: set[str] = set()
        for raw in manifest_rows:
            manufacturer = _required_text(raw, "manufacturer")
            entity_id = _required_text(raw, "entity_id")
            key = (manufacturer, entity_id)
            if key in manifest:
                _fail()
            raw_path = _canonical_relative_path(_required_text(raw, "raw_path"))
            if raw_path in raw_paths:
                _fail()
            raw_paths.add(raw_path)
            manifest[key] = {
                "manufacturer": manufacturer,
                "entity_id": entity_id,
                "configuration_type": _required_text(raw, "configuration_type"),
                "role": _required_text(raw, "role"),
                "role_digest": str(raw.get("role_digest", "")).strip(),
                "raw_path": raw_path,
                "raw_sha256": _required_text(raw, "raw_sha256"),
            }
            if re.fullmatch(r"[0-9a-f]{64}", manifest[key]["raw_sha256"]) is None:
                _fail()

        if set(roles) != set(manifest):
            _fail()
        projection: list[dict[str, str]] = []
        source_digests: set[str] = set()
        for key, role_row in roles.items():
            manifest_row = manifest[key]
            for field in ("configuration_type", "role", "role_digest"):
                if role_row[field] != manifest_row[field]:
                    _fail()
            if role_row["role"] != "SOURCE":
                continue
            digest = role_row["role_digest"]
            if digest in source_digests:
                _fail()
            source_digests.add(digest)
            projection.append(
                {
                    "manufacturer": role_row["manufacturer"],
                    "configuration_type": role_row["configuration_type"],
                    "role": "SOURCE",
                    "role_digest": digest,
                    "raw_path": manifest_row["raw_path"],
                    "raw_sha256": manifest_row["raw_sha256"],
                }
            )
        if len(projection) != expected_source_entities:
            _fail()
        projection.sort(key=lambda row: (row["role_digest"], row["manufacturer"]))
        return projection
    except SourceAccessGateError:
        raise
    except Exception:
        _fail()


def execute_source_access_gate(
    role_entities: Iterable[Mapping[str, object]],
    manifest_rows: Iterable[Mapping[str, object]],
    *,
    opener: Callable[[str], bytes],
    stager: Callable[[Mapping[str, str], bytes], object],
    expected_source_entities: int = EXPECTED_SOURCE_ENTITIES,
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Open/hash/stage exactly the SOURCE projection; expose generic audit."""
    projection = build_source_projection(
        role_entities,
        manifest_rows,
        expected_source_entities=expected_source_entities,
    )
    opened = 0
    try:
        for entry in projection:
            payload = opener(entry["raw_path"])
            if not isinstance(payload, bytes):
                _fail()
            if hashlib.sha256(payload).hexdigest() != entry["raw_sha256"]:
                _fail()
            stager(entry, payload)
            opened += 1
    except SourceAccessGateError:
        raise
    except Exception:
        _fail()
    audit = {
        "expected_source_entities": expected_source_entities,
        "opened_source_files": opened,
        "target_operational_files_opened": 0,
        "target_semantic_rows_released": 0,
    }
    return projection, audit


def execute_projected_source_access_gate(
    source_projection: Iterable[Mapping[str, object]],
    *,
    opener: Callable[[str], bytes],
    stager: Callable[[Mapping[str, str], bytes], object],
    expected_source_entities: int = EXPECTED_SOURCE_ENTITIES,
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Open only a previously audited SOURCE projection in the method process.

    The auditor-side builder must first validate all role rows and path
    uniqueness. This method-side gate accepts no TARGET/unsupported metadata,
    validates the SOURCE projection in full before opening any member, then
    opens and hashes only those exact paths.
    """
    try:
        projection: list[dict[str, str]] = []
        paths: set[str] = set()
        digests: set[str] = set()
        for raw in source_projection:
            if set(raw) != {"manufacturer", "configuration_type", "role", "role_digest",
                            "raw_path", "raw_sha256"}:
                _fail()
            manufacturer = _required_text(raw, "manufacturer")
            configuration_type = _required_text(raw, "configuration_type")
            role = _required_text(raw, "role")
            role_digest = _required_text(raw, "role_digest")
            raw_path = _canonical_relative_path(_required_text(raw, "raw_path"))
            raw_sha256 = _required_text(raw, "raw_sha256")
            if (role != "SOURCE" or re.fullmatch(r"[0-9a-f]{64}", role_digest) is None or
                    role_digest in digests or raw_path in paths or
                    re.fullmatch(r"[0-9a-f]{64}", raw_sha256) is None):
                _fail()
            digests.add(role_digest)
            paths.add(raw_path)
            projection.append({
                "manufacturer": manufacturer,
                "configuration_type": configuration_type,
                "role": role,
                "role_digest": role_digest,
                "raw_path": raw_path,
                "raw_sha256": raw_sha256,
            })
        if len(projection) != expected_source_entities:
            _fail()
        projection.sort(key=lambda row: (row["role_digest"], row["manufacturer"]))

        opened = 0
        for entry in projection:
            payload = opener(entry["raw_path"])
            if not isinstance(payload, bytes) or hashlib.sha256(payload).hexdigest() != entry["raw_sha256"]:
                _fail()
            stager(entry, payload)
            opened += 1
        return projection, {
            "expected_source_entities": expected_source_entities,
            "opened_source_files": opened,
            "target_operational_files_opened": 0,
            "target_semantic_rows_released": 0,
        }
    except SourceAccessGateError:
        raise
    except Exception:
        _fail()
