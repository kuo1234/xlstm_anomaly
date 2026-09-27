#!/usr/bin/env python3
"""Build PreDist P5-0B1R structural manifests under an exact path allowlist.

This program never opens the archive root README or any label/event payload.
Only the two explicitly named metadata files and raw paths derived from
configuration_types.csv plus ZIP central-directory paths can be read.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import statistics
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Sequence


RECORD_URL = "https://zenodo.org/records/19496480"
DOWNLOAD_URL = "https://zenodo.org/api/records/19496480/files/predist_dataset.zip/content"
RECORD_ID = "19496480"
VERSION = "v2"
PUBLICATION_DATE = "2026-04-10"
LICENSE = "CC BY 4.0"
EXPECTED_SIZE = 266_814_500
EXPECTED_MD5 = "298b6425df12ee0d93c05bd67efa3b75"
EXPECTED_SHA256 = "bbd95677835110a953146441f2215ad4ebd207bf3aca70496ce799605cfc218e"
ROLE_SALT = "P5-PREDIST-V2|209e1f55ee19bbaf71ee6e658938e4e14788ad46"
HORIZON_DAYS = (1, 2, 4, 8, 16, 32, 64)
NOMINAL_ROWS_10MIN = {day: day * 144 for day in HORIZON_DAYS}

METADATA_BASENAMES = {"configuration_types.csv", "feature_descriptions.csv"}
FORBIDDEN_PATH_TERMS = (
    "readme",
    "normal_event",
    "fault",
    "disturbance",
    "maintenance",
    "report",
    "event",
    "anomal",
    "label",
)
FORBIDDEN_COLUMN_TERMS = (
    "normal",
    "fault",
    "disturbance",
    "maintenance",
    "report",
    "event",
    "anomal",
    "label",
)
RAW_MEMBER_RE = re.compile(r"^manufacturer [0-9]+/operational_data/substation_[0-9]+\.csv$")
MANUFACTURER_METADATA_RE = re.compile(
    r"^(manufacturer [0-9]+)/(configuration_types|feature_descriptions)\.csv$"
)
TIMESTAMP_HEADERS = {
    "time",
    "timestamp",
    "time_stamp",
    "datetime",
    "date_time",
    "date/time",
    "date",
    "zeitstempel",
}
MISSING_MARKERS = {"", "na", "n/a", "null", "none"}
NEAR_CONSTANT_REL_TOL = 1e-6
GAP_FACTOR = 1.5


class AccessPolicyError(RuntimeError):
    """Raised before opening any non-allowlisted archive member."""


class StructuralLayoutError(RuntimeError):
    """Raised when archive structure or raw schema cannot be safely interpreted."""


def _unsafe_path(path: str) -> bool:
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or "\\" in path:
        return True
    lower = path.casefold()
    return any(term in lower for term in FORBIDDEN_PATH_TERMS)


def _forbidden_column(name: str) -> bool:
    lower = re.sub(r"[^a-z0-9]+", "_", name.casefold()).strip("_")
    return any(term in lower for term in FORBIDDEN_COLUMN_TERMS)


def canonical_json_bytes(obj: Any) -> bytes:
    """Stable UTF-8 JSON serialization for committed manifests and tests."""
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


class ArchiveAccess:
    """ZIP reader that refuses all payload paths outside explicit allowlists."""

    def __init__(self, zip_path: str | Path, metadata_allowlist: set[str] | frozenset[str]):
        self.zip_path = Path(zip_path)
        self.archive = zipfile.ZipFile(self.zip_path, "r")
        self.member_names = [info.filename for info in self.archive.infolist()]
        if len(self.member_names) != len(set(self.member_names)):
            self.archive.close()
            raise StructuralLayoutError("duplicate ZIP member paths")
        self.member_set = set(self.member_names)
        self.metadata_allowlist = set(metadata_allowlist)
        self.raw_allowlist: set[str] = set()
        self.open_log: list[str] = []

        for path in self.metadata_allowlist:
            if not MANUFACTURER_METADATA_RE.fullmatch(path):
                self.archive.close()
                raise AccessPolicyError(f"metadata path is outside the approved exact pattern: {path}")
            if path not in self.member_set:
                self.archive.close()
                raise StructuralLayoutError(f"allowlisted metadata member missing: {path}")
            if _unsafe_path(path):
                self.archive.close()
                raise AccessPolicyError(f"unsafe archive path cannot be allowlisted: {path}")

    def install_raw_allowlist(self, paths: set[str] | frozenset[str]) -> None:
        checked: set[str] = set()
        for path in paths:
            if path not in self.member_set:
                raise StructuralLayoutError(f"allowlisted raw member missing: {path}")
            if _unsafe_path(path) or not RAW_MEMBER_RE.fullmatch(path):
                raise AccessPolicyError(f"raw path is not an exact operational-data member: {path}")
            checked.add(path)
        self.raw_allowlist = checked

    def open_member_stream(self, path: str):
        """Authorize by exact path before delegating to ZipFile.open."""
        if _unsafe_path(path):
            raise AccessPolicyError(f"denied path: {path}")
        if path not in self.metadata_allowlist and path not in self.raw_allowlist:
            raise AccessPolicyError(f"member is not in the active path allowlist: {path}")
        if path not in self.member_set:
            raise AccessPolicyError(f"allowlisted member missing: {path}")
        self.open_log.append(path)
        return self.archive.open(path, "r")

    def read_member_bytes(self, path: str) -> bytes:
        with self.open_member_stream(path) as stream:
            return stream.read()

    def close(self) -> None:
        self.archive.close()

    def __enter__(self) -> "ArchiveAccess":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def _detect_delimiter(first_line: str) -> str:
    candidates = [",", ";", "\t"]
    parsed = [(len(next(csv.reader([first_line], delimiter=delimiter))), delimiter) for delimiter in candidates]
    width, delimiter = max(parsed, key=lambda item: (item[0], -candidates.index(item[1])))
    if width < 2:
        raise StructuralLayoutError("could not identify a delimited metadata/raw header")
    return delimiter


def _decode_first_line(data: bytes) -> str:
    try:
        line = data.decode("utf-8-sig").splitlines()[0]
    except (UnicodeDecodeError, IndexError) as exc:
        raise StructuralLayoutError("invalid or empty UTF-8 header") from exc
    return line


def _header_fields(first_line: str, *, allow_duplicate_names: bool = False) -> tuple[list[str], str]:
    delimiter = _detect_delimiter(first_line)
    fields = [field.strip() for field in next(csv.reader([first_line], delimiter=delimiter))]
    if any(_forbidden_column(field) for field in fields):
        raise AccessPolicyError("forbidden semantic outcome column found in an allowlisted file header")
    if not fields or any(not field for field in fields):
        raise StructuralLayoutError("empty header field")
    if not allow_duplicate_names and len(fields) != len(set(fields)):
        raise StructuralLayoutError("duplicate header fields")
    return fields, delimiter


def _disambiguate_duplicate_headers(fields: Sequence[str]) -> tuple[list[str], list[str]]:
    """Preserve repeated measurement columns using deterministic occurrence suffixes."""
    totals = Counter(fields)
    seen: Counter[str] = Counter()
    unique_fields: list[str] = []
    duplicate_names = sorted(name for name, count in totals.items() if count > 1)
    for field in fields:
        seen[field] += 1
        unique_fields.append(f"{field}__duplicate_{seen[field]}" if seen[field] > 1 else field)
    if len(unique_fields) != len(set(unique_fields)):
        raise StructuralLayoutError("could not deterministically disambiguate duplicate header fields")
    return unique_fields, duplicate_names


def discover_metadata_allowlist(member_names: Iterable[str]) -> tuple[list[str], dict[str, list[str]]]:
    """Find only the exact approved metadata paths from ZIP directory names."""
    paths: dict[str, list[str]] = defaultdict(list)
    for name in member_names:
        match = MANUFACTURER_METADATA_RE.fullmatch(name)
        if match:
            paths[match.group(1)].append(name)
    roots = sorted(paths)
    if not roots:
        raise StructuralLayoutError("no manufacturer metadata roots found in central directory")
    allowlist: list[str] = []
    for root in roots:
        expected = {f"{root}/{basename}" for basename in METADATA_BASENAMES}
        found = set(paths[root])
        if not expected.issubset(found):
            raise StructuralLayoutError(f"required allowlisted metadata missing for {root}")
        allowlist.extend(sorted(expected))
    return sorted(allowlist), {root: sorted(names) for root, names in paths.items()}


def parse_configuration_bytes(data: bytes, manufacturer: str | None = None) -> list[dict[str, str]]:
    first_line = _decode_first_line(data)
    fields, delimiter = _header_fields(first_line)
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter)
    normalized = {field.casefold().strip(): field for field in fields}
    if {"manufacturer", "entity_id", "configuration_type"}.issubset(normalized):
        manufacturer_field = normalized["manufacturer"]
        entity_field = normalized["entity_id"]
        config_field = normalized["configuration_type"]
        source_has_manufacturer = True
    elif {"substation id", "configuration_type"}.issubset(normalized) and manufacturer:
        manufacturer_field = None
        entity_field = normalized["substation id"]
        config_field = normalized["configuration_type"]
        source_has_manufacturer = False
    else:
        raise StructuralLayoutError(f"unexpected configuration metadata schema: {fields}")

    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for source_row in reader:
        entity_id = (source_row.get(entity_field) or "").strip()
        configuration_type = (source_row.get(config_field) or "").strip()
        row_manufacturer = (
            (source_row.get(manufacturer_field) or "").strip() if source_has_manufacturer else str(manufacturer)
        )
        if not entity_id or not row_manufacturer:
            raise StructuralLayoutError("configuration row contains an empty identity")
        key = row_manufacturer, entity_id
        if key in seen:
            raise StructuralLayoutError(f"duplicate configuration entity: {key}")
        seen.add(key)
        rows.append(
            {
                "manufacturer": row_manufacturer,
                "entity_id": entity_id,
                "configuration_type": configuration_type,
            }
        )
    return sorted(rows, key=lambda row: (row["manufacturer"], row["configuration_type"], row["entity_id"]))


def parse_feature_description_bytes(data: bytes) -> list[str]:
    first_line = _decode_first_line(data)
    fields, delimiter = _header_fields(first_line)
    normalized = [field.casefold().strip() for field in fields]
    first_field = normalized[0]
    if first_field not in {"column", "feature"} or any(
        field not in {first_field, "description", "unit"} for field in normalized
    ):
        raise StructuralLayoutError(f"unexpected feature-description metadata schema: {fields}")
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter)
    feature_field = fields[0]
    features: list[str] = []
    for row in reader:
        feature = (row.get(feature_field) or "").strip()
        if not feature or _forbidden_column(feature):
            raise AccessPolicyError("forbidden or empty feature name in metadata allowlist")
        features.append(feature)
    if len(features) != len(set(features)):
        raise StructuralLayoutError("duplicate feature names in feature-description metadata")
    return sorted(features)


def derive_raw_allowlist(member_names: Iterable[str], configurations: Sequence[dict[str, str]]) -> set[str]:
    """Build exact raw paths from static entity IDs and central-directory paths."""
    names = set(member_names)
    allowed: set[str] = set()
    for row in configurations:
        expected = (
            f"{row['manufacturer']}/operational_data/substation_{row['entity_id']}.csv"
        )
        if expected in names and RAW_MEMBER_RE.fullmatch(expected) and not _unsafe_path(expected):
            allowed.add(expected)
    return allowed


def validate_csv_layout(
    member_names: Iterable[str], configurations: Sequence[dict[str, str]]
) -> None:
    """Fail closed on CSVs that are neither approved metadata, raw, nor known denied payloads."""
    configured_raw_paths = {
        f"{row['manufacturer']}/operational_data/substation_{row['entity_id']}.csv"
        for row in configurations
    }
    for name in member_names:
        if name.endswith("/"):
            continue
        if "/operational_data/" in name:
            if not RAW_MEMBER_RE.fullmatch(name):
                raise StructuralLayoutError(f"unknown operational-data member in central directory: {name}")
            if name not in configured_raw_paths:
                raise StructuralLayoutError(f"raw member has no exact configuration metadata identity: {name}")
            continue
        if MANUFACTURER_METADATA_RE.fullmatch(name):
            continue
        if _unsafe_path(name):
            continue
        if name.casefold().endswith(".csv"):
            raise StructuralLayoutError(f"unknown CSV member in central directory: {name}")


def build_role_split(
    config_rows: Sequence[dict[str, str]], salt: str = ROLE_SALT
) -> list[dict[str, Any]]:
    """Apply the reviewer-frozen hash split independently inside each stratum."""
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    output: list[dict[str, Any]] = []
    for row in config_rows:
        if not row["configuration_type"]:
            # Missing static metadata is never silently merged into a synthetic stratum.
            output.append(
                {
                    **row,
                    "role": "UNSUPPORTED_FOR_ENTITY_SPLIT",
                    "stratum_size": 1,
                    "role_hash_input": "",
                    "role_digest": "",
                }
            )
            continue
        grouped[(row["manufacturer"], row["configuration_type"])].append(dict(row))
    for (manufacturer, configuration_type), rows in sorted(grouped.items()):
        stratum_size = len(rows)
        if stratum_size < 5:
            for row in rows:
                output.append(
                    {
                        **row,
                        "role": "UNSUPPORTED_FOR_ENTITY_SPLIT",
                        "stratum_size": stratum_size,
                        "role_hash_input": "",
                        "role_digest": "",
                    }
                )
            continue
        candidates = []
        for row in rows:
            hash_input = f"{salt}{manufacturer}{configuration_type}{row['entity_id']}"
            digest = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
            candidates.append((digest, row["entity_id"], hash_input, row))
        candidates.sort(key=lambda item: (item[0], item[1]))
        target_count = max(1, stratum_size // 5)
        for index, (digest, _entity_id, hash_input, row) in enumerate(candidates):
            output.append(
                {
                    **row,
                    "role": "TARGET" if index < target_count else "SOURCE",
                    "stratum_size": stratum_size,
                    "role_hash_input": hash_input,
                    "role_digest": digest,
                }
            )
    return sorted(output, key=lambda row: (row["manufacturer"], row["configuration_type"], row["entity_id"]))


def _parse_timestamp(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        result = datetime.fromisoformat(text)
    except ValueError:
        for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%Y/%m/%d %H:%M:%S"):
            try:
                result = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
        else:
            raise
    if result.tzinfo is not None:
        return result.astimezone(timezone.utc)
    return result


def _read_raw_header(
    access: ArchiveAccess, path: str
) -> tuple[list[str], str, str, list[str], list[str]]:
    with access.open_member_stream(path) as stream:
        first_line_bytes = stream.readline(128 * 1024)
    first_line = _decode_first_line(first_line_bytes)
    original_fields, delimiter = _header_fields(first_line, allow_duplicate_names=True)
    time_fields = [field for field in original_fields if field.casefold().strip() in TIMESTAMP_HEADERS]
    if len(time_fields) != 1:
        raise StructuralLayoutError(f"raw allowlisted file has no unique recognized timestamp column: {path}")
    fields, duplicate_names = _disambiguate_duplicate_headers(original_fields)
    timestamp_field = fields[original_fields.index(time_fields[0])]
    return fields, delimiter, timestamp_field, duplicate_names, original_fields


def _welford_add(state: dict[str, float | int], value: float) -> None:
    count = int(state["finite_count"]) + 1
    delta = value - float(state["mean"])
    mean = float(state["mean"]) + delta / count
    delta2 = value - mean
    state["m2"] = float(state["m2"]) + delta * delta2
    state["mean"] = mean
    state["finite_count"] = count
    state["min"] = value if state["min"] is None else min(float(state["min"]), value)
    state["max"] = value if state["max"] is None else max(float(state["max"]), value)


def _parse_raw_payload(
    payload: bytes,
    fields: Sequence[str],
    delimiter: str,
    timestamp_field: str,
    documented_features: set[str],
    original_header_fields: Sequence[str] | None = None,
) -> dict[str, Any]:
    if any(_forbidden_column(field) for field in fields):
        raise AccessPolicyError("forbidden semantic outcome column in raw time-series header")
    feature_fields = [field for field in fields if field != timestamp_field]
    if not feature_fields:
        raise StructuralLayoutError("raw operational file has no measurement features")
    text = payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter)
    source_header = list(reader.fieldnames or [])
    expected_source_header = (
        list(original_header_fields) if original_header_fields is not None else list(fields)
    )
    if source_header != expected_source_header or len(source_header) != len(fields):
        raise StructuralLayoutError("raw header changed between header gate and parser pass")
    reader.fieldnames = list(fields)
    feature_states: dict[str, dict[str, float | int | None]] = {
        field: {
            "finite_count": 0,
            "missing_count": 0,
            "nonnumeric_count": 0,
            "nonfinite_count": 0,
            "mean": 0.0,
            "m2": 0.0,
            "min": None,
            "max": None,
        }
        for field in feature_fields
    }
    timed_rows: list[tuple[datetime, int, int]] = []
    row_count = 0
    malformed_rows = 0
    invalid_timestamp_rows = 0
    out_of_order_rows = 0
    timestamp_timezone_mismatch_rows = 0
    previous_row_time: datetime | None = None
    timestamp_awareness: bool | None = None
    first_raw_timestamp: datetime | None = None
    last_raw_timestamp: datetime | None = None
    total_feature_cells = 0
    missing_cells = 0
    nonnumeric_cells = 0
    nonfinite_cells = 0
    undocumented = sorted(set(feature_fields) - documented_features)

    for row in reader:
        row_count += 1
        if None in row or any(row.get(field) is None for field in fields):
            malformed_rows += 1
        try:
            timestamp = _parse_timestamp(row.get(timestamp_field) or "")
        except (ValueError, TypeError):
            invalid_timestamp_rows += 1
            timestamp = None
        if timestamp is not None:
            if row_count == 1:
                first_raw_timestamp = timestamp
            last_raw_timestamp = timestamp
            aware = timestamp.tzinfo is not None
            if timestamp_awareness is not None and timestamp_awareness != aware:
                timestamp_timezone_mismatch_rows += 1
                timestamp = None
            else:
                timestamp_awareness = aware
                if previous_row_time is not None and timestamp < previous_row_time:
                    out_of_order_rows += 1
                previous_row_time = timestamp

        row_missing = 0
        row_cells = len(feature_fields)
        for field in feature_fields:
            value_text = (row.get(field) or "").strip()
            state = feature_states[field]
            total_feature_cells += 1
            if value_text.casefold() in MISSING_MARKERS:
                state["missing_count"] = int(state["missing_count"]) + 1
                missing_cells += 1
                row_missing += 1
                continue
            try:
                value = float(value_text)
            except ValueError:
                state["nonnumeric_count"] = int(state["nonnumeric_count"]) + 1
                nonnumeric_cells += 1
                continue
            if not math.isfinite(value):
                state["nonfinite_count"] = int(state["nonfinite_count"]) + 1
                nonfinite_cells += 1
                continue
            _welford_add(state, value)
        if timestamp is not None:
            timed_rows.append((timestamp, row_missing, row_cells))

    if row_count == 0:
        raise StructuralLayoutError("raw operational series contains no data rows")
    timed_rows.sort(key=lambda item: item[0])
    timestamps = [row[0] for row in timed_rows]
    counts = Counter(timestamps)
    unique_timestamps = sorted(counts)
    minimum_valid_timestamp = unique_timestamps[0] if unique_timestamps else None
    maximum_valid_timestamp = unique_timestamps[-1] if unique_timestamps else None
    chronology_status = (
        "CHRONOLOGY_VALID"
        if invalid_timestamp_rows == 0
        and timestamp_timezone_mismatch_rows == 0
        and out_of_order_rows == 0
        and first_raw_timestamp is not None
        else "CHRONOLOGY_INVALID"
    )
    positive_deltas = [
        (right - left).total_seconds()
        for left, right in zip(unique_timestamps, unique_timestamps[1:])
        if right > left
    ]
    median_cadence = statistics.median(positive_deltas) if positive_deltas else None
    rounded_delta_counts = Counter(round(value) for value in positive_deltas)
    modal_cadence = (
        min(rounded_delta_counts, key=lambda value: (-rounded_delta_counts[value], value))
        if rounded_delta_counts
        else None
    )
    duplicate_count = len(timestamps) - len(unique_timestamps)
    gap_threshold = GAP_FACTOR * median_cadence if median_cadence is not None else None
    all_gaps = [
        (right - left).total_seconds()
        for left, right in zip(unique_timestamps, unique_timestamps[1:])
    ]
    large_gaps = [gap for gap in all_gaps if gap_threshold is not None and gap > gap_threshold]

    spans: list[dict[str, Any]] = []
    if unique_timestamps:
        span_start = unique_timestamps[0]
        previous = unique_timestamps[0]
        span_unique_count = 1
        span_rows = counts[previous]
        for timestamp in unique_timestamps[1:]:
            gap = (timestamp - previous).total_seconds()
            if gap_threshold is not None and gap > gap_threshold:
                spans.append(
                    {
                        "start": span_start.isoformat(),
                        "end": previous.isoformat(),
                        "unique_timestamps": span_unique_count,
                        "rows": span_rows,
                        "duration_seconds": (previous - span_start).total_seconds(),
                    }
                )
                span_start = timestamp
                span_unique_count = 0
                span_rows = 0
            span_unique_count += 1
            span_rows += counts[timestamp]
            previous = timestamp
        spans.append(
            {
                "start": span_start.isoformat(),
                "end": previous.isoformat(),
                "unique_timestamps": span_unique_count,
                "rows": span_rows,
                "duration_seconds": (previous - span_start).total_seconds(),
            }
        )

    horizon_windows = []
    if timestamps and first_raw_timestamp is not None:
        for horizon_day in HORIZON_DAYS:
            boundary = first_raw_timestamp + timedelta(days=horizon_day)
            window_rows = [
                item for item in timed_rows if first_raw_timestamp <= item[0] < boundary
            ]
            window_unique = sorted({item[0] for item in window_rows})
            window_gaps = [
                (right - left).total_seconds()
                for left, right in zip(window_unique, window_unique[1:])
            ]
            horizon_missing = sum(item[1] for item in window_rows)
            horizon_cells = sum(item[2] for item in window_rows)
            horizon_windows.append(
                {
                    "horizon_days": horizon_day,
                    "reaches_elapsed_horizon": bool(
                        maximum_valid_timestamp is not None and maximum_valid_timestamp >= boundary
                    ),
                    "actual_rows": len(window_rows),
                    "nominal_rows_10min": NOMINAL_ROWS_10MIN[horizon_day],
                    "nominal_row_fraction_10min": round(
                        len(window_rows) / NOMINAL_ROWS_10MIN[horizon_day], 8
                    ),
                    "gap_count_over_1_5x_median": sum(
                        1 for gap in window_gaps if gap_threshold is not None and gap > gap_threshold
                    ),
                    "largest_gap_seconds": max(window_gaps, default=0.0),
                    "missing_cell_fraction": round(horizon_missing / horizon_cells, 8)
                    if horizon_cells
                    else None,
                }
            )

    feature_stats: dict[str, dict[str, Any]] = {}
    for field in feature_fields:
        state = feature_states[field]
        count = int(state["finite_count"])
        minimum = state["min"]
        maximum = state["max"]
        variance = float(state["m2"]) / max(1, count - 1) if count > 1 else 0.0
        std = math.sqrt(max(0.0, variance))
        mean = float(state["mean"])
        constant = count > 0 and minimum == maximum
        near_constant = count > 0 and not constant and std <= NEAR_CONSTANT_REL_TOL * max(1.0, abs(mean))
        feature_stats[field] = {
            "finite_count": count,
            "missing_count": int(state["missing_count"]),
            "nonnumeric_count": int(state["nonnumeric_count"]),
            "nonfinite_count": int(state["nonfinite_count"]),
            "constant": constant,
            "near_constant_tolerance": NEAR_CONSTANT_REL_TOL,
            "near_constant": near_constant,
            "finite_range": (float(maximum) - float(minimum)) if count else None,
            "mean_abs": abs(mean) if count else None,
            "std": std if count else None,
            "missing_fraction": round(int(state["missing_count"]) / row_count, 8) if row_count else None,
        }

    schema_hash = hashlib.sha256(canonical_json_bytes(sorted(feature_fields))).hexdigest()
    valid_count = len(timestamps)
    missing_fraction = missing_cells / total_feature_cells if total_feature_cells else None
    return {
        "row_count": row_count,
        "timestamp_valid_rows": valid_count,
        "timestamp_parse_failures": invalid_timestamp_rows,
        "timestamp_timezone_mismatch_rows": timestamp_timezone_mismatch_rows,
        "malformed_rows": malformed_rows,
        "out_of_order_rows": out_of_order_rows,
        "chronology_status": chronology_status,
        "first_timestamp": first_raw_timestamp.isoformat() if first_raw_timestamp else "",
        "last_timestamp": last_raw_timestamp.isoformat() if last_raw_timestamp else "",
        "minimum_valid_timestamp": minimum_valid_timestamp.isoformat()
        if minimum_valid_timestamp
        else "",
        "maximum_valid_timestamp": maximum_valid_timestamp.isoformat()
        if maximum_valid_timestamp
        else "",
        "cadence_median_seconds": median_cadence,
        "cadence_mode_seconds": modal_cadence,
        "cadence_min_seconds": min(positive_deltas) if positive_deltas else None,
        "cadence_max_seconds": max(positive_deltas) if positive_deltas else None,
        "duplicate_timestamp_rows": duplicate_count,
        "gap_threshold_seconds": gap_threshold,
        "gap_count": len(large_gaps),
        "largest_gap_seconds": max(large_gaps, default=0.0),
        "missing_cells": missing_cells,
        "missing_cell_fraction": round(missing_fraction, 8) if missing_fraction is not None else None,
        "nonnumeric_cells": nonnumeric_cells,
        "nonfinite_cells": nonfinite_cells,
        "numeric_cell_count": sum(int(s["finite_count"]) for s in feature_states.values()),
        "numeric_finite_fraction": round(
            sum(int(s["finite_count"]) for s in feature_states.values()) / total_feature_cells, 8
        )
        if total_feature_cells
        else None,
        "feature_fields": sorted(feature_fields),
        "schema_hash": schema_hash,
        "documented_feature_names": sorted(documented_features),
        "undocumented_feature_names": undocumented,
        "feature_stats": feature_stats,
        "usable_contiguous_spans": spans,
        "horizon_windows": horizon_windows,
    }


def _sha(data: bytes, algorithm: str = "sha256") -> str:
    return hashlib.new(algorithm, data).hexdigest()


def _hash_file(path: Path) -> tuple[int, str, str]:
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(chunk)
            md5.update(chunk)
            sha256.update(chunk)
    return size, md5.hexdigest(), sha256.hexdigest()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(data))


def _write_csv(path: Path, fieldnames: Sequence[str], rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    field: json.dumps(row.get(field), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                    if isinstance(row.get(field), (dict, list))
                    else row.get(field, "")
                    for field in fieldnames
                }
            )


def _group_schema_audit(
    config_rows: Sequence[dict[str, str]], entity_rows: Sequence[dict[str, Any]]
) -> list[dict[str, Any]]:
    manifest_lookup = {(row["manufacturer"], row["entity_id"]): row for row in entity_rows}
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in config_rows:
        groups[(row["manufacturer"], row["configuration_type"])].append(row)
    output = []
    for (manufacturer, configuration_type), members in sorted(groups.items()):
        present = [manifest_lookup[(r["manufacturer"], r["entity_id"])] for r in members]
        available = [r for r in present if r.get("raw_status") == "PARSED"]
        feature_sets = [set(r["feature_fields"]) for r in available]
        if not feature_sets:
            common_features: set[str] = set()
            schema_status = "SCHEMA_INCOMPATIBLE"
        else:
            common_features = set.intersection(*feature_sets)
            has_duplicate_headers = any(r.get("duplicate_header_names") for r in available)
            if has_duplicate_headers:
                schema_status = "SCHEMA_INCOMPATIBLE"
            elif all(features == feature_sets[0] for features in feature_sets):
                schema_status = "SCHEMA_COMPATIBLE"
            elif common_features:
                schema_status = "SCHEMA_COMPATIBLE_WITH_PREDECLARED_COMMON_SUBSET"
            else:
                schema_status = "SCHEMA_INCOMPATIBLE"

        all_features = sorted(set().union(*feature_sets)) if feature_sets else []
        feature_diagnostics = []
        for feature in all_features:
            stats = [r["feature_stats"].get(feature) for r in available if feature in r["feature_stats"]]
            ranges = [float(s["finite_range"]) for s in stats if s and s["finite_range"] is not None]
            positive_ranges = [value for value in ranges if value > 0]
            spread = max(positive_ranges) / min(positive_ranges) if len(positive_ranges) > 1 else None
            feature_diagnostics.append(
                {
                    "feature": feature,
                    "present_entities": sum(feature in fields for fields in feature_sets),
                    "constant_entities": sum(bool(s and s["constant"]) for s in stats),
                    "near_constant_entities": sum(bool(s and s["near_constant"]) for s in stats),
                    "nonnumeric_cells": sum(int(s["nonnumeric_count"]) for s in stats),
                    "nonfinite_cells": sum(int(s["nonfinite_count"]) for s in stats),
                    "median_finite_range": statistics.median(ranges) if ranges else None,
                    "finite_range_spread_ratio": spread,
                    "range_spread_over_1000x_diagnostic": spread is not None and spread > 1000,
                }
            )
        output.append(
            {
                "manufacturer": manufacturer,
                "configuration_type": configuration_type,
                "metadata_entity_count": len(members),
                "raw_available_count": len(available),
                "raw_missing_count": len(members) - len(available),
                "duplicate_header_entity_count": sum(
                    bool(r.get("duplicate_header_names")) for r in available
                ),
                "schema_status": schema_status,
                "feature_union": all_features,
                "automated_common_feature_intersection": sorted(common_features),
                "constant_diagnostic_tolerance": NEAR_CONSTANT_REL_TOL,
                "near_constant_definition": "sample_std <= 1e-6 * max(1, abs(mean)); diagnostic only",
                "range_spread_diagnostic": "max(entity feature range)/min(positive entity feature range); >1000x flagged only",
                "feature_diagnostics": feature_diagnostics,
            }
        )
    return output


def build_manifests(archive_path: Path, output_dir: Path) -> dict[str, Any]:
    archive_size, actual_md5, actual_sha256 = _hash_file(archive_path)
    if archive_size != EXPECTED_SIZE or actual_md5 != EXPECTED_MD5 or actual_sha256 != EXPECTED_SHA256:
        raise StructuralLayoutError("downloaded archive size/hash does not match pinned official record")

    with zipfile.ZipFile(archive_path, "r") as archive:
        infos = archive.infolist()
        member_names = [info.filename for info in infos]
        if len(member_names) != len(set(member_names)):
            raise StructuralLayoutError("duplicate ZIP member paths")
        unsafe_names = [name for name in member_names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name]
        if unsafe_names:
            raise StructuralLayoutError("unsafe ZIP member path detected")
        size_by_name = {info.filename: info.file_size for info in infos}

    metadata_allowlist, metadata_paths_by_root = discover_metadata_allowlist(member_names)
    config_rows: list[dict[str, str]] = []
    features_by_root: dict[str, list[str]] = {}
    with ArchiveAccess(archive_path, set(metadata_allowlist)) as access:
        for root in sorted(metadata_paths_by_root):
            config_path = f"{root}/configuration_types.csv"
            features_path = f"{root}/feature_descriptions.csv"
            config_rows.extend(parse_configuration_bytes(access.read_member_bytes(config_path), manufacturer=root))
            features_by_root[root] = parse_feature_description_bytes(access.read_member_bytes(features_path))

        validate_csv_layout(member_names, config_rows)
        raw_allowlist = derive_raw_allowlist(member_names, config_rows)
        access.install_raw_allowlist(raw_allowlist)
        role_rows = build_role_split(config_rows)
        role_lookup = {(r["manufacturer"], r["entity_id"]): r for r in role_rows}
        feature_description_lookup = features_by_root
        entity_rows: list[dict[str, Any]] = []
        for config in config_rows:
            key = (config["manufacturer"], config["entity_id"])
            raw_path = f"{config['manufacturer']}/operational_data/substation_{config['entity_id']}.csv"
            role = role_lookup[key]
            row: dict[str, Any] = {
                **config,
                "role": role["role"],
                "stratum_size": role["stratum_size"],
                "role_digest": role["role_digest"],
                "raw_path": raw_path,
                "raw_status": "RAW_MEMBER_MISSING" if raw_path not in raw_allowlist else "PENDING",
                "raw_sha256": "",
                "schema_hash": "",
                "feature_fields": [],
                "duplicate_header_names": [],
                "feature_stats": {},
                "row_count": 0,
                "timestamp_valid_rows": 0,
                "timestamp_parse_failures": 0,
                "timestamp_timezone_mismatch_rows": 0,
                "malformed_rows": 0,
                "out_of_order_rows": 0,
                "chronology_status": "NOT_AVAILABLE",
                "first_timestamp": "",
                "last_timestamp": "",
                "minimum_valid_timestamp": "",
                "maximum_valid_timestamp": "",
                "cadence_median_seconds": None,
                "cadence_mode_seconds": None,
                "cadence_min_seconds": None,
                "cadence_max_seconds": None,
                "duplicate_timestamp_rows": 0,
                "gap_threshold_seconds": None,
                "gap_count": 0,
                "largest_gap_seconds": 0.0,
                "missing_cells": 0,
                "missing_cell_fraction": None,
                "nonnumeric_cells": 0,
                "nonfinite_cells": 0,
                "numeric_cell_count": 0,
                "numeric_finite_fraction": None,
                "documented_feature_names": features_by_root[config["manufacturer"]],
                "undocumented_feature_names": [],
                "usable_contiguous_spans": [],
                "horizon_windows": [],
            }
            if raw_path in raw_allowlist:
                (
                    header_fields,
                    delimiter,
                    timestamp_field,
                    duplicate_header_names,
                    original_header_fields,
                ) = _read_raw_header(access, raw_path)
                payload = access.read_member_bytes(raw_path)
                summary = _parse_raw_payload(
                    payload,
                    header_fields,
                    delimiter,
                    timestamp_field,
                    set(feature_description_lookup[config["manufacturer"]]),
                    original_header_fields,
                )
                row.update(summary)
                row["duplicate_header_names"] = duplicate_header_names
                row["raw_sha256"] = _sha(payload, "sha256")
                row["raw_status"] = "PARSED"
            entity_rows.append(row)

        # The open log contains only explicitly allowlisted paths, never label paths.
        open_log = list(access.open_log)

    schema_rows = _group_schema_audit(config_rows, entity_rows)
    entity_by_key = {(r["manufacturer"], r["entity_id"]): r for r in entity_rows}
    sealed_entities = []
    for role in role_rows:
        entity = entity_by_key[(role["manufacturer"], role["entity_id"])]
        sealed_entities.append(
            {
                "manufacturer": role["manufacturer"],
                "configuration_type": role["configuration_type"],
                "entity_id": role["entity_id"],
                "stratum_size": role["stratum_size"],
                "role": role["role"],
                "role_hash_input": role["role_hash_input"],
                "role_digest": role["role_digest"],
                "raw_path": entity["raw_path"],
                "raw_member_available": entity["raw_status"] == "PARSED",
                "first_raw_timestamp": entity["first_timestamp"],
                "chronology_status": entity["chronology_status"],
            }
        )
    role_seal = {
        "salt": ROLE_SALT,
        "hash_rule": "SHA256(UTF8(salt || manufacturer || configuration_type || entity_id)); lexical digest order",
        "stratum_rule": "group by exact (manufacturer, configuration_type); n<5 => unsupported and never merge; else target_count=max(1,floor(n/5)); first digests TARGET; remainder SOURCE",
        "target_start_rule": "timestamp in the first raw data row; if it is invalid, the target has no evaluable start; no moving cuts",
        "entities": sealed_entities,
    }
    denied_paths = sorted(
        ({"path": name, "uncompressed_size_bytes": size_by_name[name], "content_access": "DENIED"} for name in member_names if _unsafe_path(name)),
        key=lambda row: row["path"],
    )
    access_policy = {
        "policy_version": "p5-0b1r-v1",
        "archive_sha256": EXPECTED_SHA256,
        "archive_member_count": len(member_names),
        "permanently_denied_paths": denied_paths,
        "metadata_allowlist": metadata_allowlist,
        "raw_allowlist": sorted(raw_allowlist),
        "validated_raw_member_paths": sorted(
            name for name in member_names if RAW_MEMBER_RE.fullmatch(name)
        ),
        "opened_member_path_log": open_log,
        "only_allowlist_paths_were_opened": all(
            path in set(metadata_allowlist) | raw_allowlist for path in open_log
        ),
        "content_sniffing_for_path_classification": False,
    }
    archive_manifest = {
        "record": RECORD_URL,
        "record_id": RECORD_ID,
        "version": VERSION,
        "publication_date": PUBLICATION_DATE,
        "license": LICENSE,
        "archive_filename": "predist_dataset.zip",
        "download_url": DOWNLOAD_URL,
        "archive_bytes": EXPECTED_SIZE,
        "md5": EXPECTED_MD5,
        "sha256": EXPECTED_SHA256,
        "md5_matches_official_record": True,
        "sha256_pinned_from_preflight": True,
        "archive_tracked_by_git": False,
        "semantic_label_payload_access": False,
        "root_readme_access": False,
        "archive_member_count": len(member_names),
    }

    role_by_key = {(r["manufacturer"], r["entity_id"]): r for r in role_rows}
    for entity in entity_rows:
        entity["role_hash_input"] = role_by_key[(entity["manufacturer"], entity["entity_id"])]["role_hash_input"]
        entity["horizon_grid_days"] = list(HORIZON_DAYS)
    entity_columns = [
        "manufacturer",
        "configuration_type",
        "entity_id",
        "role",
        "stratum_size",
        "role_digest",
        "role_hash_input",
        "raw_path",
        "raw_status",
        "raw_sha256",
        "schema_hash",
        "feature_fields",
        "duplicate_header_names",
        "documented_feature_names",
        "undocumented_feature_names",
        "first_timestamp",
        "last_timestamp",
        "minimum_valid_timestamp",
        "maximum_valid_timestamp",
        "row_count",
        "timestamp_valid_rows",
        "timestamp_parse_failures",
        "timestamp_timezone_mismatch_rows",
        "malformed_rows",
        "out_of_order_rows",
        "chronology_status",
        "cadence_median_seconds",
        "cadence_mode_seconds",
        "cadence_min_seconds",
        "cadence_max_seconds",
        "duplicate_timestamp_rows",
        "gap_threshold_seconds",
        "gap_count",
        "largest_gap_seconds",
        "missing_cells",
        "missing_cell_fraction",
        "nonnumeric_cells",
        "nonfinite_cells",
        "numeric_cell_count",
        "numeric_finite_fraction",
        "feature_stats",
        "usable_contiguous_spans",
        "horizon_windows",
        "horizon_grid_days",
    ]
    schema_columns = [
        "manufacturer",
        "configuration_type",
        "metadata_entity_count",
        "raw_available_count",
        "raw_missing_count",
        "duplicate_header_entity_count",
        "schema_status",
        "feature_union",
        "automated_common_feature_intersection",
        "constant_diagnostic_tolerance",
        "near_constant_definition",
        "range_spread_diagnostic",
        "feature_diagnostics",
    ]
    _write_json(output_dir / "download_manifest.json", archive_manifest)
    _write_json(output_dir / "access_policy.json", access_policy)
    _write_json(output_dir / "role_split_seal.json", role_seal)
    _write_csv(output_dir / "entity_manifest.csv", entity_columns, entity_rows)
    _write_csv(output_dir / "schema_audit.csv", schema_columns, schema_rows)
    return {
        "archive_manifest": archive_manifest,
        "access_policy": access_policy,
        "role_seal": role_seal,
        "entity_rows": entity_rows,
        "schema_rows": schema_rows,
        "output_dir": str(output_dir),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    result = build_manifests(args.archive, args.output_dir)
    print(
        json.dumps(
            {
                "archive_sha256": result["archive_manifest"]["sha256"],
                "entities": len(result["entity_rows"]),
                "strata": len(result["schema_rows"]),
                "metadata_allowlist_count": len(result["access_policy"]["metadata_allowlist"]),
                "raw_allowlist_count": len(result["access_policy"]["raw_allowlist"]),
                "output_dir": result["output_dir"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
