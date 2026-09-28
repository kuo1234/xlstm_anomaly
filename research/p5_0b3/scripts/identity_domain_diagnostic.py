"""Pinned identity-only diagnostic for the SOURCE label boundary.

This module intentionally has no dependency on the normal firewall or method
execution path. It reads identity cells only and emits one fixed enum.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile
from typing import Mapping

from research.p5_0b3.scripts.firewall_runner import ALLOWED_MEMBERS


IDENTITY_ALL_RESOLVE_AFTER_DECIMAL_CANONICALIZATION = "IDENTITY_ALL_RESOLVE_AFTER_DECIMAL_CANONICALIZATION"
IDENTITY_EMPTY_OR_NONDECIMAL = "IDENTITY_EMPTY_OR_NONDECIMAL"
IDENTITY_OUTSIDE_SEALED_UNIVERSE = "IDENTITY_OUTSIDE_SEALED_UNIVERSE"
IDENTITY_INVALID_ROLE_VALUE = "IDENTITY_INVALID_ROLE_VALUE"
IDENTITY_MIXED_FAILURE = "IDENTITY_MIXED_FAILURE"
IDENTITY_UNCLASSIFIED = "IDENTITY_UNCLASSIFIED"
RESULTS = frozenset({
    IDENTITY_ALL_RESOLVE_AFTER_DECIMAL_CANONICALIZATION,
    IDENTITY_EMPTY_OR_NONDECIMAL,
    IDENTITY_OUTSIDE_SEALED_UNIVERSE,
    IDENTITY_INVALID_ROLE_VALUE,
    IDENTITY_MIXED_FAILURE,
    IDENTITY_UNCLASSIFIED,
})
MANUFACTURERS = ("manufacturer 1", "manufacturer 2")
ALLOWED_ROLES = frozenset({"SOURCE", "TARGET", "UNSUPPORTED_FOR_ENTITY_SPLIT"})
PROTOCOL_STATUS = "P5_0B2R2_PROTOCOL_RESEALED"
ROLE_SEAL_SHA256 = "00e0cec62d238c78f2d0b3c79910c0ffaf1122d1582c28c8848022fb3e10e33f"
ARCHIVE_PATH = Path("/tmp/predist_dataset-v2-19496480.zip")
ARCHIVE_SIZE = 266_814_500


def canonical_decimal_id(value: object) -> str | None:
    """Return a positive ASCII decimal ID in canonical integer form."""
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped or any(character < "0" or character > "9" for character in stripped):
        return None
    try:
        integer = int(stripped, 10)
    except Exception:
        return None
    return str(integer) if integer > 0 else None


def _read_identity_cell_values(csv_bytes: bytes) -> list[str]:
    text = csv_bytes.decode("utf-8-sig", errors="strict")
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=";", strict=True)
    try:
        header = next(reader)
    except StopIteration:
        raise ValueError from None
    return _identity_values_from_records(header, reader)


def _identity_values_from_records(header, records) -> list[str]:
    id_columns = [index for index, name in enumerate(header) if name == "substation ID"]
    if len(id_columns) != 1 or not header:
        raise ValueError from None
    column = id_columns[0]
    values: list[str] = []
    for row in records:
        if len(row) != len(header):
            raise ValueError from None
        values.append(row[column])
    return values


def identity_result(role_seal_bytes: bytes, members: Mapping[str, bytes]) -> str:
    """Classify synthetic or pinned bytes without retaining/emitting identities."""
    try:
        if (not isinstance(role_seal_bytes, bytes)
                or hashlib.sha256(role_seal_bytes).hexdigest() != ROLE_SEAL_SHA256):
            return IDENTITY_UNCLASSIFIED
        if (not isinstance(members, Mapping) or set(members) != ALLOWED_MEMBERS
                or any(not isinstance(value, bytes) for value in members.values())):
            return IDENTITY_UNCLASSIFIED

        role_document = json.loads(role_seal_bytes)
        entities = role_document.get("entities") if isinstance(role_document, dict) else None
        if not isinstance(entities, list):
            return IDENTITY_UNCLASSIFIED

        universe: dict[tuple[str, str], object] = {}
        invalid_id_seen = False
        for entity in entities:
            if not isinstance(entity, dict):
                return IDENTITY_UNCLASSIFIED
            # Deliberately access exactly these role-seal fields.
            manufacturer = entity.get("manufacturer")
            entity_id = entity.get("entity_id")
            role = entity.get("role")
            if manufacturer not in MANUFACTURERS:
                return IDENTITY_UNCLASSIFIED
            canonical = canonical_decimal_id(entity_id)
            if canonical is None:
                invalid_id_seen = True
                continue
            key = (manufacturer, canonical)
            if key in universe:
                return IDENTITY_UNCLASSIFIED
            universe[key] = role

        classifiable = invalid_id_seen
        failures: set[str] = set()
        if invalid_id_seen:
            failures.add(IDENTITY_EMPTY_OR_NONDECIMAL)

        for member in sorted(ALLOWED_MEMBERS):
            manufacturer = member.split("/", 1)[0]
            ids = _read_identity_cell_values(members[member])
            if ids:
                classifiable = True
            for value in ids:
                canonical = canonical_decimal_id(value)
                if canonical is None:
                    failures.add(IDENTITY_EMPTY_OR_NONDECIMAL)
                    continue
                key = (manufacturer, canonical)
                if key not in universe:
                    failures.add(IDENTITY_OUTSIDE_SEALED_UNIVERSE)
                elif not isinstance(universe[key], str) or universe[key] not in ALLOWED_ROLES:
                    failures.add(IDENTITY_INVALID_ROLE_VALUE)

        if not classifiable:
            return IDENTITY_UNCLASSIFIED
        if len(failures) > 1:
            return IDENTITY_MIXED_FAILURE
        if failures:
            return next(iter(failures))
        return IDENTITY_ALL_RESOLVE_AFTER_DECIMAL_CANONICALIZATION
    except Exception:
        return IDENTITY_UNCLASSIFIED


def _read_identity_members_from_zip(archive: str | Path) -> dict[str, bytes]:
    """Read each allowlisted member exactly once; never open unrelated entries."""
    with zipfile.ZipFile(archive, "r") as zipped:
        counts = {member: 0 for member in ALLOWED_MEMBERS}
        for info in zipped.infolist():
            if info.filename in counts:
                counts[info.filename] += 1
        if any(count != 1 for count in counts.values()):
            raise ValueError from None
        return {member: zipped.read(member) for member in sorted(ALLOWED_MEMBERS)}


def _pinned_preflight(root: Path, sealed_commit: str, archive_path: Path) -> tuple[bytes, dict[str, bytes]]:
    """Check committed-code and structural pins before reading the archive."""
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
                          capture_output=True, text=True).stdout.strip()
    status = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
                            check=True, capture_output=True, text=True).stdout
    if not sealed_commit or head != sealed_commit or status.strip():
        raise ValueError from None

    protocol = json.loads((root / "research/p5_0b2/protocol_seal.json").read_bytes())
    if (protocol.get("status") != PROTOCOL_STATUS
            or protocol.get("role_seal_sha256") != ROLE_SEAL_SHA256
            or protocol.get("target_access", {}).get("target_label_access") != "NOT_AUTHORIZED"):
        raise ValueError from None

    implementation = json.loads((root / "research/p5_0b3/implementation_seal.json").read_bytes())
    if implementation.get("status") != "P5_0B3_PREACCESS_CODE_SEALED":
        raise ValueError from None
    entries = implementation.get("sealed_files")
    if not isinstance(entries, list):
        raise ValueError from None
    code_bases = (root / "research/p5_0b3/scripts", root / "research/p5_0b3/tests")
    expected = {
        path.relative_to(root).as_posix()
        for base in code_bases
        for path in base.rglob("*.py") if path.is_file()
    }
    resolved_bases = tuple(base.resolve(strict=True) for base in code_bases)
    actual: dict[str, str] = {}
    for item in entries:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise ValueError from None
        relative, digest = item["path"], item["sha256"]
        if relative in actual or relative not in expected or not isinstance(digest, str):
            raise ValueError from None
        code_path = root / relative
        resolved = code_path.resolve(strict=True)
        if (code_path.is_symlink()
                or not any(resolved.is_relative_to(base) for base in resolved_bases)
                or hashlib.sha256(code_path.read_bytes()).hexdigest() != digest):
            raise ValueError from None
        actual[relative] = digest
    if set(actual) != expected:
        raise ValueError from None

    protocol_path = root / "research/p5_0b2/protocol_seal.json"
    protocol_bytes = protocol_path.read_bytes()
    protocol_record = implementation.get("protocol")
    if (not isinstance(protocol_record, dict)
            or hashlib.sha256(protocol_bytes).hexdigest() != protocol_record.get("protocol_seal_sha256")):
        raise ValueError from None
    firewall_path = root / "research/p5_0b2/scripts/source_label_firewall.py"
    expected_firewall_sha = protocol.get("source_development", {}).get("source_label_firewall_sha256")
    if (not isinstance(expected_firewall_sha, str)
            or hashlib.sha256(firewall_path.read_bytes()).hexdigest() != expected_firewall_sha):
        raise ValueError from None

    role_path = root / "research/p5_0b1r/role_split_seal.json"
    role_bytes = role_path.read_bytes()
    if hashlib.sha256(role_bytes).hexdigest() != ROLE_SEAL_SHA256:
        raise ValueError from None
    if archive_path.resolve() != ARCHIVE_PATH.resolve() or archive_path.stat().st_size != ARCHIVE_SIZE:
        raise ValueError from None
    members = _read_identity_members_from_zip(archive_path)
    return role_bytes, members


def main(argv: list[str] | None = None) -> int:
    try:
        values = list(sys.argv[1:] if argv is None else argv)
        allowed = {"--root", "--sealed-commit", "--archive"}
        if len(values) != 6 or len(values) % 2:
            raise ValueError from None
        args = dict(zip(values[::2], values[1::2]))
        if set(args) != allowed or any(not value for value in args.values()):
            raise ValueError from None
        role_bytes, members = _pinned_preflight(
            Path(args["--root"]), args["--sealed-commit"], Path(args["--archive"])
        )
        result = identity_result(role_bytes, members)
        print(result if result in RESULTS else IDENTITY_UNCLASSIFIED)
    except Exception:
        print(IDENTITY_UNCLASSIFIED)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
