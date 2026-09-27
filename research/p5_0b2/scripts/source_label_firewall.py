"""Fail-closed SOURCE-only extractor for PreDist interval labels.

This module is sealed for a later gated phase. It has not been run against
project label tables. Synthetic tests exercise the filter and interval rules.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Mapping


ROLE_SEAL_SHA256 = "00e0cec62d238c78f2d0b3c79910c0ffaf1122d1582c28c8848022fb3e10e33f"
FIREWALL_VERSION = "p5-0b2-source-label-firewall-v1"
TABLES = ("faults", "normal_events", "disturbances")
MANUFACTURERS = ("manufacturer 1", "manufacturer 2")
ALLOWED_ROLES = {"SOURCE", "TARGET", "UNSUPPORTED_FOR_ENTITY_SPLIT"}
REQUIRED_COLUMNS = {
    "faults": {"substation ID", "efd_possible", "Possible anomaly start", "Possible anomaly end", "Report date"},
    "normal_events": {"substation ID", "Event start", "Event end"},
    "disturbances": {"substation ID", "Event start", "type"},
}


class FirewallError(RuntimeError):
    """An intentionally value-free firewall failure."""

    def __init__(self) -> None:
        super().__init__("FIREWALL_FAILED")


def _fail() -> None:
    # Suppress the active exception context: tracebacks must not repeat a
    # malformed annotation value, source path, or decoder/filesystem detail.
    raise FirewallError() from None


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def build_role_index(entities: Iterable[Mapping[str, object]]) -> dict[tuple[str, str], dict[str, str]]:
    """Build an exact manufacturer/entity lookup; never expose TARGET rows."""
    index: dict[tuple[str, str], dict[str, str]] = {}
    source_digests: set[str] = set()
    for row in entities:
        manufacturer = _text(row.get("manufacturer"))
        entity_id = _text(row.get("entity_id"))
        role = _text(row.get("role"))
        if manufacturer not in MANUFACTURERS or not entity_id or role not in ALLOWED_ROLES:
            _fail()
        key = (manufacturer, entity_id)
        if key in index:
            _fail()
        entry = {"role": role}
        if role == "SOURCE":
            role_digest = _text(row.get("role_digest"))
            if not role_digest or role_digest in source_digests:
                _fail()
            source_digests.add(role_digest)
            entry["role_digest"] = role_digest
        index[key] = entry
    return index


def load_role_index(path: str | Path) -> dict[tuple[str, str], dict[str, str]]:
    """Load only the sealed structural role file, verifying its exact bytes."""
    try:
        raw = Path(path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != ROLE_SEAL_SHA256:
            _fail()
        payload = json.loads(raw)
        return build_role_index(payload["entities"])
    except FirewallError:
        raise
    except Exception:
        _fail()


def _parse_time(value: object) -> datetime:
    text = _text(value)
    if not text:
        _fail()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        _fail()
    if parsed.tzinfo is not None:
        _fail()
    return parsed


def _iso_timestamp(value: datetime) -> str:
    return value.isoformat(timespec="microseconds" if value.microsecond else "seconds")


def _fault_possible(value: object) -> bool:
    normalized = _text(value).casefold()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    _fail()


def _row_interval(
    table: str,
    row: Mapping[str, object],
) -> tuple[str, str, str]:
    if table == "faults":
        if "efd_possible" not in row:
            _fail()
        if not _fault_possible(row.get("efd_possible")):
            return "", "", ""
        start_text = _text(row.get("Possible anomaly start"))
        end_text = _text(row.get("Possible anomaly end"))
        report: datetime | None = None
        if not start_text or not end_text:
            report_text = _text(row.get("Report date"))
            if report_text:
                report = _parse_time(report_text)
        if start_text:
            start = _parse_time(start_text)
        elif report is not None:
            start = report - timedelta(hours=48)
        else:
            _fail()
        if end_text:
            end = _parse_time(end_text)
        elif report is not None:
            end = report + timedelta(hours=24)
        else:
            _fail()
        if end < start:
            _fail()
        return "KNOWN_FAULT", _iso_timestamp(start), _iso_timestamp(end)

    if table == "normal_events":
        start = _parse_time(row.get("Event start"))
        end = _parse_time(row.get("Event end"))
        if end < start:
            _fail()
        return "REFERENCE_NORMAL_EVENT", _iso_timestamp(start), _iso_timestamp(end)

    if table == "disturbances":
        start = _parse_time(row.get("Event start"))
        start = start.replace(minute=(start.minute // 10) * 10, second=0, microsecond=0)
        if _text(row.get("type")).casefold() == "fault":
            left = start - timedelta(hours=48)
            right = start + timedelta(hours=24)
            kind = "DISTURBANCE_FAULT"
        else:
            left = start
            right = datetime.combine(start.date() + timedelta(days=1), datetime.min.time())
            kind = "DISTURBANCE_OTHER"
        return kind, _iso_timestamp(left), _iso_timestamp(right)

    _fail()


def normalize_table_rows(
    table: str,
    manufacturer: str,
    rows: Iterable[Mapping[str, object]],
    role_index: Mapping[tuple[str, str], Mapping[str, str]],
) -> list[dict[str, str]]:
    """Drop TARGET/unsupported rows before reading any semantic field."""
    if table not in TABLES or manufacturer not in MANUFACTURERS:
        _fail()
    output: list[dict[str, str]] = []
    for row in rows:
        # Identity is the only field read before role classification.
        entity_id = _text(row.get("substation ID"))
        if not entity_id:
            _fail()
        role_entry = role_index.get((_text(manufacturer), entity_id))
        if role_entry is None:
            _fail()
        role = role_entry.get("role")
        if role in {"TARGET", "UNSUPPORTED_FOR_ENTITY_SPLIT"}:
            continue
        if role != "SOURCE":
            _fail()
        # Validate SOURCE row structure only after role classification and
        # before interpreting any interval field. DictReader uses missing
        # values for short records and the None key for excess cells.
        if None in row or not REQUIRED_COLUMNS[table].issubset(row.keys()):
            _fail()
        if any(value is None for value in row.values()):
            _fail()
        role_digest = _text(role_entry.get("role_digest"))
        if not role_digest:
            _fail()
        kind, interval_start, interval_end = _row_interval(table, row)
        if not kind:
            # EFD's published `efd_possible=false` rows are excluded.
            continue
        output.append(
            {
                "role_digest": role_digest,
                "annotation_source": table,
                "annotation_kind": kind,
                "interval_start": interval_start,
                "interval_end": interval_end,
            }
        )
    return output


def canonical_source_bytes(rows: Iterable[Mapping[str, str]]) -> bytes:
    canonical_rows = [dict(row) for row in rows]
    allowed = {
        "role_digest",
        "annotation_source",
        "annotation_kind",
        "interval_start",
        "interval_end",
    }
    if any(set(row) != allowed for row in canonical_rows):
        _fail()
    canonical_rows.sort(
        key=lambda row: (
            row["role_digest"],
            row["interval_start"],
            row["interval_end"],
            row["annotation_source"],
            row["annotation_kind"],
        )
    )
    payload = "".join(
        json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"
        for row in canonical_rows
    )
    return payload.encode("utf-8")


def extract_source_bytes(
    tables: Mapping[tuple[str, str], Iterable[Mapping[str, object]]],
    role_index: Mapping[tuple[str, str], Mapping[str, str]],
) -> tuple[bytes, int]:
    """Return only canonical SOURCE bytes and distinct SOURCE entity count."""
    expected_keys = {(manufacturer, table) for manufacturer in MANUFACTURERS for table in TABLES}
    if set(tables) != expected_keys:
        _fail()
    normalized: list[dict[str, str]] = []
    for manufacturer, table in sorted(tables):
        normalized.extend(normalize_table_rows(table, manufacturer, tables[(manufacturer, table)], role_index))
    payload = canonical_source_bytes(normalized)
    entity_count = sum(1 for entry in role_index.values() if entry.get("role") == "SOURCE")
    return payload, entity_count


def read_source_csv(
    table: str,
    manufacturer: str,
    path: str | Path,
    role_index: Mapping[tuple[str, str], Mapping[str, str]],
) -> list[dict[str, str]]:
    """Stream raw CSV rows through the role filter without returning raw rows."""
    if table not in TABLES or manufacturer not in MANUFACTURERS:
        _fail()
    try:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream, delimiter=";", strict=True)
            if (
                not reader.fieldnames
                or reader.line_num != 1
                or len(reader.fieldnames) != len(set(reader.fieldnames))
                or not REQUIRED_COLUMNS[table].issubset(set(reader.fieldnames))
            ):
                _fail()
            def single_physical_line_records():
                previous_line = reader.line_num
                for row in reader:
                    current_line = reader.line_num
                    if current_line != previous_line + 1:
                        _fail()
                    previous_line = current_line
                    yield row

            return normalize_table_rows(table, manufacturer, single_physical_line_records(), role_index)
    except FirewallError:
        raise
    except Exception:
        _fail()


def _write_sync(path: Path, content: bytes) -> None:
    with path.open("wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def publish_artifacts(
    output_dir: str | Path,
    source_payload: bytes,
    source_entity_count: int,
    input_sha256: Mapping[str, str],
) -> dict[str, str]:
    """Atomically publish the three restricted firewall artifacts."""
    destination = Path(output_dir)
    if destination.exists() or source_entity_count < 0:
        _fail()
    for name, digest in input_sha256.items():
        if name not in {f"{manufacturer}/{table}.csv" for manufacturer in MANUFACTURERS for table in TABLES}:
            _fail()
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            _fail()
    source_hash = hashlib.sha256(source_payload).hexdigest()
    source_rows = [line for line in source_payload.splitlines() if line]
    audit = {
        "firewall_version": FIREWALL_VERSION,
        "role_seal_sha256": ROLE_SEAL_SHA256,
        "input_tables_sha256": dict(sorted(input_sha256.items())),
        "source_artifact_sha256": source_hash,
        "source_entity_count": source_entity_count,
        "source_record_count": len(source_rows),
        "target_rows_emitted": False,
        "target_identifiers_logged": False,
        "target_semantics_logged": False,
    }
    audit_bytes = (json.dumps(audit, sort_keys=True, indent=2) + "\n").encode("utf-8")
    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="p5-0b2-firewall-", dir=parent) as temp_name:
            temp_path = Path(temp_name)
            _write_sync(temp_path / "source_labels.jsonl", source_payload)
            _write_sync(temp_path / "source_labels.sha256", (source_hash + "\n").encode("ascii"))
            _write_sync(temp_path / "access_audit.json", audit_bytes)
            os.replace(temp_path, destination)
            temp_path = None
        parent_fd = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    except Exception:
        if temp_path is not None and temp_path.exists():
            shutil.rmtree(temp_path, ignore_errors=True)
        _fail()
    return {"source_artifact_sha256": source_hash, "audit_sha256": hashlib.sha256(audit_bytes).hexdigest()}


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except Exception:
        _fail()
    return digest.hexdigest()


def execute_firewall(
    label_paths: Mapping[tuple[str, str], str | Path],
    role_seal_path: str | Path,
    output_dir: str | Path,
) -> dict[str, str]:
    """Read only the three known label tables per manufacturer and publish SOURCE rows."""
    expected_keys = {(manufacturer, table) for manufacturer in MANUFACTURERS for table in TABLES}
    if set(label_paths) != expected_keys:
        _fail()
    role_index = load_role_index(role_seal_path)
    normalized: list[dict[str, str]] = []
    input_hashes: dict[str, str] = {}
    try:
        for manufacturer, table in sorted(expected_keys):
            path = label_paths[(manufacturer, table)]
            before_hash = sha256_file(path)
            rows = read_source_csv(table, manufacturer, path, role_index)
            after_hash = sha256_file(path)
            if before_hash != after_hash:
                _fail()
            normalized.extend(rows)
            input_hashes[f"{manufacturer}/{table}.csv"] = before_hash
        payload = canonical_source_bytes(normalized)
        source_entity_count = sum(1 for entry in role_index.values() if entry.get("role") == "SOURCE")
        return publish_artifacts(output_dir, payload, source_entity_count, input_hashes)
    except FirewallError:
        raise
    except Exception:
        _fail()
