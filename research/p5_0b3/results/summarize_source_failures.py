#!/usr/bin/env python3
"""Create a public, privacy-filtered summary from completed SOURCE method outputs.

This helper reads only method_output/source_summary.json and the fixed
source_artifacts/stratum_NN_audit.json files. It deliberately projects an
allowlist of aggregate fields; audit identifiers and unrelated diagnostics are
never copied to the result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "p5-0b3-source-failure-summary-v1"
STRATUM_FIELDS = (
    "manufacturer",
    "configuration_type",
    "status",
    "failure_stage",
    "source_entity_count",
    "fold_support_status",
    "failing_fold_count",
    "common_heldout_entity_count",
    "pseudo_target_eligibility_reason_counts",
    "eligible_pseudo_target_count",
    "readiness_selection",
    "max_joint_success_count",
    "candidate_count_evaluated",
)


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _max_joint_success_count(diagnostics: dict[str, Any]) -> int | None:
    summaries = diagnostics.get("readiness_candidate_summaries")
    if not isinstance(summaries, list) or not summaries:
        return None
    counts = [
        item.get("joint_success_count")
        for item in summaries
        if isinstance(item, dict)
    ]
    if len(counts) != len(summaries) or not all(
        isinstance(count, int) and not isinstance(count, bool) and count >= 0
        for count in counts
    ):
        return None
    return max(counts)


def _candidate_count_evaluated(diagnostics: dict[str, Any]) -> int | None:
    summaries = diagnostics.get("readiness_candidate_summaries")
    if not isinstance(summaries, list) or any(not isinstance(item, dict) for item in summaries):
        return None
    return len(summaries)


def summarize(method_output_dir: Path) -> dict[str, Any]:
    summary = _read_json(method_output_dir / "source_summary.json")
    strata = summary.get("strata")
    if not isinstance(strata, list) or len(strata) != 5:
        raise ValueError("source_summary.json must contain exactly five strata")

    result_strata: list[dict[str, Any]] = []
    for index, summary_stratum in enumerate(strata):
        if not isinstance(summary_stratum, dict):
            raise ValueError(f"Invalid source summary stratum at index {index}")
        # source_method_process enumerates sorted entities once and emits both
        # this audit filename and summary.strata[index] from the same loop.
        audit_path = method_output_dir / "source_artifacts" / f"stratum_{index:02d}_audit.json"
        audit = _read_json(audit_path)
        diagnostics = audit.get("pipeline_diagnostics")
        if not isinstance(diagnostics, dict):
            diagnostics = {}
        if diagnostics.get("status") != summary_stratum.get("status"):
            raise ValueError(f"Status mismatch between summary and audit at stratum {index}")

        folds_data = diagnostics.get("fold_support")
        folds = folds_data.get("folds") if isinstance(folds_data, dict) else None
        if isinstance(folds, list) and folds and all(isinstance(fold, dict) for fold in folds):
            failing_fold_count = sum(fold.get("status") != "PASS" for fold in folds)
            fold_support_status = "PASS" if failing_fold_count == 0 else "NOT_PASS"
        else:
            failing_fold_count = None
            fold_support_status = None

        detector_selection = diagnostics.get("detector_selection")
        if not isinstance(detector_selection, dict):
            detector_selection = {}
        common_heldout_entity_count = detector_selection.get("common_heldout_entity_count")
        pseudo = diagnostics.get("pseudo_target_eligibility")
        if not isinstance(pseudo, dict):
            pseudo = {}
        reason_counts = pseudo.get("exclusion_reason_counts")
        if not isinstance(reason_counts, dict):
            reason_counts = None
        else:
            # Copy only string reason labels and integer aggregate counts.
            reason_counts = {
                key: value
                for key, value in sorted(reason_counts.items())
                if isinstance(key, str) and isinstance(value, int)
            }
        readiness_selection = diagnostics.get("readiness_selection", "NOT_REACHED")
        if readiness_selection is None:
            readiness_selection = "NOT_REACHED"
        elif readiness_selection not in {"ZERO_JOINT_SUCCESS", "NO_SELECTION", "NOT_REACHED"}:
            raise ValueError(f"Unexpected readiness selection at stratum {index}")

        row = {
            "manufacturer": summary_stratum.get("manufacturer"),
            "configuration_type": summary_stratum.get("configuration_type"),
            "status": summary_stratum.get("status"),
            "failure_stage": diagnostics.get("failure_stage"),
            "source_entity_count": diagnostics.get("source_entity_count"),
            "fold_support_status": fold_support_status,
            "failing_fold_count": failing_fold_count,
            "common_heldout_entity_count": common_heldout_entity_count,
            "pseudo_target_eligibility_reason_counts": reason_counts,
            "eligible_pseudo_target_count": pseudo.get("eligible_count"),
            "readiness_selection": readiness_selection,
            "max_joint_success_count": _max_joint_success_count(diagnostics),
            # Count only readiness candidates with emitted summaries; the AE
            # detector candidate grid is a separate quantity.
            "candidate_count_evaluated": _candidate_count_evaluated(diagnostics),
        }
        result_strata.append({key: row[key] for key in STRATUM_FIELDS})

    return {"schema_version": SCHEMA_VERSION, "strata": result_strata}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--method-output-dir",
        type=Path,
        required=True,
        help="Completed run's method_output directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("source_failure_summary.json"),
        help="Destination JSON path (default: adjacent source_failure_summary.json)",
    )
    args = parser.parse_args()
    payload = summarize(args.method_output_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
