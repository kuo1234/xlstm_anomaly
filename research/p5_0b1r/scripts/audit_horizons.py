#!/usr/bin/env python3
"""Aggregate fixed-grid structural availability from the label-blind entity manifest."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path
from typing import Any, Sequence


def _load_json(value: str) -> Any:
    return json.loads(value) if value else []


def audit_horizons(entity_manifest: Path, output_path: Path) -> list[dict[str, Any]]:
    with entity_manifest.open("r", encoding="utf-8", newline="") as stream:
        entities = list(csv.DictReader(stream))
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in entities:
        key = (row["manufacturer"], row["configuration_type"], row["role"])
        groups.setdefault(key, []).append(row)

    output: list[dict[str, Any]] = []
    for (manufacturer, configuration_type, role), members in sorted(groups.items()):
        raw_members = [row for row in members if row["raw_status"] == "PARSED"]
        chronology_valid = [
            row for row in raw_members if row.get("chronology_status") == "CHRONOLOGY_VALID"
        ]
        windows_by_entity = {
            (row["manufacturer"], row["entity_id"]): {
                int(item["horizon_days"]): item for item in _load_json(row.get("horizon_windows", "[]"))
            }
            for row in chronology_valid
        }
        for horizon_days in (1, 2, 4, 8, 16, 32, 64):
            windows = [
                windows_by_entity[(row["manufacturer"], row["entity_id"])][horizon_days]
                for row in chronology_valid
                if horizon_days in windows_by_entity[(row["manufacturer"], row["entity_id"])]
            ]
            reaching = [row for row in windows if row["reaches_elapsed_horizon"]]
            row_counts = [int(row["actual_rows"]) for row in windows]
            gap_counts = [int(row["gap_count_over_1_5x_median"]) for row in windows]
            largest_gaps = [float(row["largest_gap_seconds"]) for row in windows]
            missing_fractions = [
                float(row["missing_cell_fraction"])
                for row in windows
                if row.get("missing_cell_fraction") is not None
            ]
            nominal_fraction = [float(row["nominal_row_fraction_10min"]) for row in windows]
            output.append(
                {
                    "manufacturer": manufacturer,
                    "configuration_type": configuration_type,
                    "role": role,
                    "horizon_days": horizon_days,
                    "nominal_rows_10min": horizon_days * 144,
                    "assigned_entities": len(members),
                    "raw_available_entities": len(raw_members),
                    "chronology_valid_entities": len(chronology_valid),
                    "entities_with_horizon_window": len(windows),
                    "entities_reaching_elapsed_horizon": len(reaching),
                    "coverage_fraction_all_assigned": round(len(reaching) / len(members), 8) if members else None,
                    "coverage_fraction_raw_available": round(len(reaching) / len(raw_members), 8)
                    if raw_members
                    else None,
                    "coverage_fraction_chronology_valid": round(
                        len(reaching) / len(chronology_valid), 8
                    )
                    if chronology_valid
                    else None,
                    "actual_rows_min": min(row_counts) if row_counts else None,
                    "actual_rows_median": statistics.median(row_counts) if row_counts else None,
                    "actual_rows_max": max(row_counts) if row_counts else None,
                    "nominal_row_fraction_median": statistics.median(nominal_fraction) if nominal_fraction else None,
                    "gap_count_median": statistics.median(gap_counts) if gap_counts else None,
                    "largest_gap_seconds_max": max(largest_gaps) if largest_gaps else None,
                    "missing_cell_fraction_median": statistics.median(missing_fractions)
                    if missing_fractions
                    else None,
                    "interpretation": "structural time/data availability only; not normal-label or evaluator coverage",
                }
            )

    fieldnames = [
        "manufacturer",
        "configuration_type",
        "role",
        "horizon_days",
        "nominal_rows_10min",
        "assigned_entities",
        "raw_available_entities",
        "chronology_valid_entities",
        "entities_with_horizon_window",
        "entities_reaching_elapsed_horizon",
        "coverage_fraction_all_assigned",
        "coverage_fraction_raw_available",
        "coverage_fraction_chronology_valid",
        "actual_rows_min",
        "actual_rows_median",
        "actual_rows_max",
        "nominal_row_fraction_median",
        "gap_count_median",
        "largest_gap_seconds_max",
        "missing_cell_fraction_median",
        "interpretation",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    return output


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entity-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    rows = audit_horizons(args.entity_manifest, args.output)
    print(f"wrote {len(rows)} structural-availability rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
