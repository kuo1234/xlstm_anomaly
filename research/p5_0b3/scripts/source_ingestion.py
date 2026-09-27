"""Value-minimizing CSV projection and timestamp/interval helpers for SOURCE rows."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from collections.abc import Iterable, Mapping, Sequence

import numpy as np


class SourceCsvError(ValueError):
    """A value-free malformed SOURCE CSV error."""

    def __init__(self) -> None:
        super().__init__("SOURCE_CSV_INVALID")


TIMESTAMP_HEADERS = frozenset({
    "time", "timestamp", "time_stamp", "datetime", "date_time", "date/time",
    "date", "zeitstempel",
})
DELIMITERS = (",", ";", "\t")


def _detect_delimiter(header_line: str) -> str:
    try:
        counts = [(len(next(csv.reader([header_line], delimiter=delimiter))), delimiter)
                  for delimiter in DELIMITERS]
        width, delimiter = max(counts, key=lambda item: (item[0], -DELIMITERS.index(item[1])))
        if width < 2:
            raise SourceCsvError()
        return delimiter
    except SourceCsvError:
        raise
    except Exception:
        raise SourceCsvError() from None


def detect_timestamp_column(text: str, *, delimiter: str | None = None) -> tuple[str, str]:
    """Return the unique B1R-recognized timestamp header and raw delimiter.

    Only the header is inspected. The accepted names mirror the pinned B1R
    structural parser; no operational values are parsed by this helper.
    """
    try:
        if not isinstance(text, str) or not text:
            raise SourceCsvError()
        first_line = text.splitlines()[0]
        selected_delimiter = delimiter or _detect_delimiter(first_line)
        if selected_delimiter not in DELIMITERS:
            raise SourceCsvError()
        headers = next(csv.reader([first_line], delimiter=selected_delimiter, strict=True))
        cleaned = [header.strip() for header in headers]
        matches = [header for header in cleaned if header.casefold() in TIMESTAMP_HEADERS]
        if len(matches) != 1:
            raise SourceCsvError()
        return matches[0], selected_delimiter
    except SourceCsvError:
        raise
    except Exception:
        raise SourceCsvError() from None


@dataclass(frozen=True)
class SourceRows:
    """Projected rows, retaining raw CSV order and zero-based data-row indices.

    Invalid measurement rows are represented by an all-NaN feature row and a
    false ``measurement_valid`` flag. ``timestamps`` contains naive datetimes
    or None; invalid/aware timestamps are separately flagged.
    """

    timestamps: tuple[datetime | None, ...]
    timestamp_valid: np.ndarray
    features: np.ndarray
    measurement_valid: np.ndarray
    raw_row_indices: np.ndarray
    raw_row_count: int
    feature_names: tuple[str, ...]


def _parse_timestamp(value: str) -> datetime | None:
    try:
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%Y/%m/%d %H:%M:%S"):
                try:
                    parsed = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    continue
            else:
                return None
        if parsed.tzinfo is not None and parsed.utcoffset() is not None:
            return None
        return parsed
    except (TypeError, ValueError, OverflowError):
        return None


def project_source_csv(
    text: str,
    *,
    timestamp_column: str | None,
    feature_columns: Sequence[str],
    delimiter: str | None = None,
) -> SourceRows:
    """Parse CSV structure, then inspect only timestamp and selected feature cells.

    Empty feature fields and numeric NaN are the only imputed-missing values.
    Other nonnumeric tokens, infinities, and rows with no finite measurements
    invalidate that row. The invalid row's values are discarded wholesale.
    """
    try:
        if not isinstance(text, str) or not text:
            raise SourceCsvError()
        first_line = text.splitlines()[0]
        selected_delimiter = delimiter or _detect_delimiter(first_line)
        if selected_delimiter not in DELIMITERS:
            raise SourceCsvError()
        if timestamp_column is None:
            timestamp_column, detected_delimiter = detect_timestamp_column(
                text, delimiter=selected_delimiter
            )
            if detected_delimiter != selected_delimiter:
                raise SourceCsvError()
        ordered_features = tuple(feature_columns)
        if not ordered_features or len(set(ordered_features)) != len(ordered_features):
            raise SourceCsvError()
        reader = csv.reader(StringIO(text, newline=""), delimiter=selected_delimiter, strict=True)
        headers = next(reader)
        headers = [header.strip() for header in headers]
        if any(not header for header in headers):
            raise SourceCsvError()
        required = (timestamp_column,) + ordered_features
        if len(set(required)) != len(required):
            raise SourceCsvError()
        positions: dict[str, int] = {}
        for name in required:
            matches = [index for index, header in enumerate(headers) if header == name]
            if len(matches) != 1:
                raise SourceCsvError()
            positions[name] = matches[0]
        selected = tuple(positions[name] for name in required)

        times: list[datetime | None] = []
        time_valid: list[bool] = []
        feature_rows: list[list[float]] = []
        measurement_valid: list[bool] = []
        indices: list[int] = []
        for row_index, row in enumerate(reader):
            if len(row) != len(headers):
                raise SourceCsvError()
            # Project first; unselected values are not converted or examined.
            projected = [row[position] for position in selected]
            timestamp = _parse_timestamp(projected[0])
            times.append(timestamp)
            time_valid.append(timestamp is not None)
            parsed_values: list[float] = []
            valid = True
            for raw in projected[1:]:
                if raw == "":
                    parsed_values.append(float("nan"))
                    continue
                try:
                    value = float(raw)
                except (TypeError, ValueError, OverflowError):
                    valid = False
                    break
                if np.isinf(value):
                    valid = False
                    break
                parsed_values.append(value)
            if valid and parsed_values and not np.isfinite(parsed_values).any():
                valid = False
            if not valid:
                parsed_values = [float("nan")] * len(ordered_features)
            feature_rows.append(parsed_values)
            measurement_valid.append(valid)
            indices.append(row_index)
        if not indices:
            raise SourceCsvError()
        return SourceRows(
            timestamps=tuple(times),
            timestamp_valid=np.asarray(time_valid, dtype=bool),
            features=np.asarray(feature_rows, dtype=np.float64),
            measurement_valid=np.asarray(measurement_valid, dtype=bool),
            raw_row_indices=np.asarray(indices, dtype=np.int64),
            raw_row_count=len(indices),
            feature_names=ordered_features,
        )
    except SourceCsvError:
        raise
    except Exception:
        raise SourceCsvError() from None


def inclusive_interval_mask(
    timestamps: Sequence[datetime | None],
    intervals: Iterable[Mapping[str, object]],
    *,
    start_key: str = "start",
    end_key: str = "end",
) -> np.ndarray:
    """Return membership in the inclusive union of naive canonical intervals."""
    try:
        parsed_intervals: list[tuple[datetime, datetime]] = []
        for interval in intervals:
            start = interval[start_key]
            end = interval[end_key]
            if not isinstance(start, datetime) or not isinstance(end, datetime):
                raise ValueError
            if (start.tzinfo is not None and start.utcoffset() is not None) or (
                end.tzinfo is not None and end.utcoffset() is not None
            ) or end < start:
                raise ValueError
            parsed_intervals.append((start, end))
        mask = np.zeros(len(timestamps), dtype=bool)
        for index, stamp in enumerate(timestamps):
            if stamp is None:
                continue
            if not isinstance(stamp, datetime) or (
                stamp.tzinfo is not None and stamp.utcoffset() is not None
            ):
                continue
            mask[index] = any(start <= stamp <= end for start, end in parsed_intervals)
        return mask
    except Exception:
        raise ValueError("SOURCE_INTERVAL_INVALID") from None
