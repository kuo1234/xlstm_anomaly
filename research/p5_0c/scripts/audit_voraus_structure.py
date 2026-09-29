#!/usr/bin/env python3
"""Aggregate-only structural audit of the official VorausAD 100 Hz Parquet.

Reads the seven episode/metadata columns for counts and ordering checks. The
complete Parquet schema is read from file metadata only. No feature values are
read, transformed, modeled, or emitted. Sample identifiers are held in memory
only for grouping and are never serialized.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REQUIRED = ("sample", "time", "anomaly", "category", "setting", "action", "active")
OPTIONAL = ("variant",)


def scalar(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "as_py"):
        value = value.as_py()
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def key(value: Any) -> str:
    value = scalar(value)
    return "<NULL>" if value is None else str(value)


def quantiles(values: list[int]) -> dict[str, float | int | None]:
    if not values:
        return {"min": None, "p05": None, "p25": None, "median": None,
                "p75": None, "p95": None, "max": None}
    ordered = sorted(values)

    def q(p: float) -> float:
        pos = (len(ordered) - 1) * p
        lo, hi = math.floor(pos), math.ceil(pos)
        return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)

    return {"min": ordered[0], "p05": q(.05), "p25": q(.25),
            "median": q(.5), "p75": q(.75), "p95": q(.95), "max": ordered[-1]}


def support_rows(counter: Counter, dimensions: tuple[str, ...], name: str) -> list[dict[str, Any]]:
    rows = []
    for values, count in sorted(counter.items()):
        if not isinstance(values, tuple):
            values = (values,)
        rows.append({**dict(zip(dimensions, values)), name: count})
    return rows


def run(dataset_path: Path) -> dict[str, Any]:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("pyarrow is required to read the Parquet file") from exc

    parquet = pq.ParquetFile(dataset_path)
    schema = parquet.schema_arrow
    names = set(schema.names)
    missing = [name for name in REQUIRED if name not in names]
    if missing:
        raise ValueError(f"Missing required Parquet columns: {', '.join(missing)}")
    columns = [name for name in REQUIRED + OPTIONAL if name in names]
    consistency_fields = ("anomaly", "category", "setting")
    if "variant" in columns:
        consistency_fields += ("variant",)

    full_schema = [
        {"name": field.name, "type": str(field.type), "nullable": field.nullable}
        for field in schema
    ]
    schema_bytes = json.dumps(full_schema, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    # Values in `samples` are internal group keys only and never enter output.
    samples: dict[str, dict[str, Any]] = {}
    null_counts: Counter = Counter()
    row_count = 0
    anomaly_rows: Counter = Counter()
    rows_by_action_label: Counter = Counter()
    reappeared_samples: set[str] = set()
    closed_samples: set[str] = set()
    last_sample: str | None = None
    time_order = {"comparable_adjacent_pairs": 0, "nondecreasing_pairs": 0,
                  "strictly_increasing_pairs": 0, "decreasing_pairs": 0,
                  "equal_adjacent_pairs": 0, "uncomparable_adjacent_pairs": 0}

    for batch in parquet.iter_batches(batch_size=131072, columns=columns):
        data = {name: batch.column(batch.schema.get_field_index(name)).to_pylist()
                for name in columns}
        for i in range(batch.num_rows):
            row_count += 1
            sid = key(data["sample"][i])
            if sid != last_sample:
                if last_sample is not None:
                    closed_samples.add(last_sample)
                if sid in closed_samples:
                    reappeared_samples.add(sid)
                last_sample = sid

            rec = samples.get(sid)
            if rec is None:
                rec = {
                    "length": 0,
                    "constants": {field: set() for field in consistency_fields},
                    "labels": Counter(),
                    "actions": set(),
                    "strata": set(),
                    "setting_labels": set(),
                    "category_labels": set(),
                    "action_labels": set(),
                    "stratum_labels": set(),
                    "first_time": None,
                    "last_time": None,
                    "all_time_present": True,
                    "bad_order": False,
                }
                samples[sid] = rec

            for field in columns:
                if data[field][i] is None:
                    null_counts[field] += 1
            for field in consistency_fields:
                rec["constants"][field].add(key(data[field][i]))

            label = key(data["anomaly"][i])
            setting = key(data["setting"][i])
            action = key(data["action"][i])
            rec["labels"][label] += 1
            rec["actions"].add(action)
            rec["strata"].add((setting, action))
            rec["setting_labels"].add((setting, label))
            rec["category_labels"].add((key(data["category"][i]), label))
            rec["action_labels"].add((action, label))
            rec["stratum_labels"].add((setting, action, label))
            anomaly_rows[label] += 1
            rows_by_action_label[(action, label)] += 1

            current = data["time"][i]
            previous = rec["last_time"]
            if rec["length"] > 0:
                if current is not None and previous is not None:
                    try:
                        a, b = float(previous), float(current)
                        if math.isfinite(a) and math.isfinite(b):
                            time_order["comparable_adjacent_pairs"] += 1
                            if b >= a:
                                time_order["nondecreasing_pairs"] += 1
                            else:
                                time_order["decreasing_pairs"] += 1
                                rec["bad_order"] = True
                            if b > a:
                                time_order["strictly_increasing_pairs"] += 1
                            elif b == a:
                                time_order["equal_adjacent_pairs"] += 1
                        else:
                            time_order["uncomparable_adjacent_pairs"] += 1
                    except (TypeError, ValueError, OverflowError):
                        time_order["uncomparable_adjacent_pairs"] += 1
                else:
                    time_order["uncomparable_adjacent_pairs"] += 1
            elif current is not None:
                rec["first_time"] = scalar(current)
            else:
                rec["all_time_present"] = False
            rec["all_time_present"] = rec["all_time_present"] and current is not None
            rec["last_time"] = scalar(current)
            rec["length"] += 1

    lengths = [rec["length"] for rec in samples.values()]
    consistency = {
        field: {
            "single_value_samples": sum(len(rec["constants"][field]) == 1 for rec in samples.values()),
            "multiple_or_missing_value_samples": sum(len(rec["constants"][field]) != 1 for rec in samples.values()),
        }
        for field in consistency_fields
    }

    sample_label_counts: Counter = Counter()
    setting_sample_support: Counter = Counter()
    setting_sample_label_support: Counter = Counter()
    category_sample_support: Counter = Counter()
    category_label_support: Counter = Counter()
    action_sample_support: Counter = Counter()
    action_label_support: Counter = Counter()
    stratum_sample_support: Counter = Counter()
    stratum_label_support: Counter = Counter()
    mixed_label_samples = 0
    action_counts_per_sample = []
    stratum_counts_per_sample = []

    for rec in samples.values():
        labels = rec["labels"]
        for label in labels:
            sample_label_counts[label] += 1
        if len(labels) != 1:
            mixed_label_samples += 1
        for setting in {setting for setting, _label in rec["setting_labels"]}:
            setting_sample_support[setting] += 1
        for setting, label in rec["setting_labels"]:
            setting_sample_label_support[(setting, label)] += 1
        for category in {category for category, _label in rec["category_labels"]}:
            category_sample_support[category] += 1
        for category, label in rec["category_labels"]:
            category_label_support[(category, label)] += 1
        for action in rec["actions"]:
            action_sample_support[action] += 1
        for action, label in rec["action_labels"]:
            action_label_support[(action, label)] += 1
        for setting, action in rec["strata"]:
            stratum_sample_support[(setting, action)] += 1
        for setting, action, label in rec["stratum_labels"]:
            stratum_label_support[(setting, action, label)] += 1
        action_counts_per_sample.append(len(rec["actions"]))
        stratum_counts_per_sample.append(len(rec["strata"]))

    strata_by_class = Counter()
    for (setting, action), _n in stratum_sample_support.items():
        classes = {label for (s, a, label), n in stratum_label_support.items()
                   if s == setting and a == action and n > 0}
        strata_by_class["mixed" if len(classes) > 1 else next(iter(classes), "<NONE>")] += 1

    schema_signature = hashlib.sha256(schema_bytes).hexdigest()
    return {
        "audit": {
            "purpose": "aggregate-only structural metadata audit",
            "model_work": False,
            "data_values_read": columns,
            "full_feature_values_read": False,
            "time_interpretation": "within-sample file-order pairs only; no chronology compared across samples",
            "setting_interpretation": "official variant/split metadata, not physical identities",
            "action_interpretation": "within-sample phase/action metadata; not an independent target",
            "sample_identifiers_or_raw_rows_emitted": False,
        },
        "source": {"file_name": dataset_path.name, "file_size_bytes": dataset_path.stat().st_size},
        "schema": {
            "field_count": len(full_schema),
            "metadata_field_count": len(columns),
            "full_field_signature_sha256": schema_signature,
            "fields": full_schema,
        },
        "counts": {
            "parquet_row_groups": parquet.num_row_groups,
            "rows": row_count,
            "samples": len(samples),
            "samples_with_mixed_anomaly_labels": mixed_label_samples,
            "null_values_in_read_metadata_columns": dict(sorted(null_counts.items())),
            "rows_by_anomaly_label": support_rows(anomaly_rows, ("anomaly",), "rows"),
            "samples_by_anomaly_label": support_rows(sample_label_counts, ("anomaly",), "samples"),
            "samples_with_noncontiguous_file_blocks": len(reappeared_samples),
            "rows_by_action_and_anomaly_label": support_rows(
                rows_by_action_label, ("action", "anomaly"), "rows"),
        },
        "sample_length_rows": quantiles(lengths),
        "sample_field_consistency": consistency,
        "within_sample_time_order": {
            **time_order,
            "samples_with_any_decreasing_adjacent_time": sum(rec["bad_order"] for rec in samples.values()),
            "samples_with_all_time_present": sum(rec["all_time_present"] for rec in samples.values()),
        },
        "setting_sample_support": [
            {"setting": setting, "samples": n,
             "samples_by_anomaly_label": [
                 {"anomaly": label, "samples": support}
                 for (s, label), support in sorted(setting_sample_label_support.items()) if s == setting
             ]}
            for setting, n in sorted(setting_sample_support.items())
        ],
        "category_sample_support": [
            {"category": category, "samples": n,
             "samples_by_anomaly_label": [
                 {"anomaly": label, "samples": support}
                 for (c, label), support in sorted(category_label_support.items()) if c == category
             ]}
            for category, n in sorted(category_sample_support.items())
        ],
        "action_sample_support": [
            {"action": action, "samples": n,
             "samples_by_anomaly_label": [
                 {"anomaly": label, "samples": support}
                 for (a, label), support in sorted(action_label_support.items()) if a == action
             ]}
            for action, n in sorted(action_sample_support.items())
        ],
        "setting_action_candidate_support": {
            "distinct_strata": len(stratum_sample_support),
            "sample_support_per_stratum": quantiles(list(stratum_sample_support.values())),
            "strata_by_anomaly_support": dict(sorted(strata_by_class.items())),
            "actions_per_sample": quantiles(action_counts_per_sample),
            "setting_action_strata_per_sample": quantiles(stratum_counts_per_sample),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path, help="input official Parquet path")
    parser.add_argument("--output", required=True, type=Path, help="aggregate JSON output path")
    args = parser.parse_args()
    if not args.dataset.is_file():
        parser.error(f"dataset path is not a file: {args.dataset}")
    result = run(args.dataset)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                           encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
