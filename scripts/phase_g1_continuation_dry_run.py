"""Metric-free real-inventory continuation cardinality dry-run.

This entrypoint verifies the sealed cache inventory and reconstructs all
primary cache references, then stops before loading feature arrays or entering
any probe/statistics path.  It is intentionally separate from the production
continuation command, which requires the report-only continuation seal.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import phase_g1_cache_audit as audit  # noqa: E402
import phase_g1_continue_from_cache as continuation  # noqa: E402


REPORT_PATH = ROOT / "reports" / "phase_g1" / "g1_continuation_dry_run_v1.json"


def run() -> dict[str, Any]:
    records = continuation._load_verified_inventory()
    refs = continuation.reconstruct_primary_cache_refs(records)
    cardinality = continuation.validate_primary_cache_ref_cardinality(refs)

    old_formula: dict[str, Any] = {}
    old_formula_rejected = True
    for fold, sources in audit.FOLDS:
        old_expected = len(audit.ARMS) * len(audit.ARCHITECTURES) * len(sources)
        actual = cardinality["per_seed"][str(audit.DETECTOR_SEEDS[0])][str(fold)]["actual_total"]
        rejected = actual != old_expected
        old_formula[str(fold)] = {
            "old_buggy_expected_total": int(old_expected),
            "correct_actual_total": int(actual),
            "rejected": bool(rejected),
        }
        old_formula_rejected = old_formula_rejected and rejected

    expected_total = 40_000
    expected_per_seed = {"train": 3_200, "validation": 1_600, "test": 3_200}
    expected_per_arm = {"train": 200, "validation": 100, "test": 200}
    per_seed_checks: dict[str, Any] = {}
    counts_pass = True
    for seed in audit.DETECTOR_SEEDS:
        seed_summary = cardinality["per_seed"][str(seed)]
        fold_checks: dict[str, Any] = {}
        for fold in expected_per_seed:
            details = seed_summary[fold]
            arm_counts = details["per_arm_architecture_actual"]
            fold_pass = (
                details["actual_total"] == expected_per_seed[fold]
                and set(arm_counts) == {f"{arm}_{arch}" for arm in audit.ARMS for arch in audit.ARCHITECTURES}
                and all(value == expected_per_arm[fold] for value in arm_counts.values())
            )
            counts_pass = counts_pass and fold_pass
            fold_checks[fold] = {
                "pass": bool(fold_pass),
                "actual_total": int(details["actual_total"]),
                "expected_total": int(expected_per_seed[fold]),
                "per_arm_architecture": arm_counts,
                "expected_per_arm_architecture": int(expected_per_arm[fold]),
            }
        per_seed_checks[str(seed)] = {
            "folds": fold_checks,
            "actual_total": int(seed_summary["total"]),
            "expected_total": 8_000,
            "pass": bool(seed_summary["total"] == 8_000 and all(item["pass"] for item in fold_checks.values())),
        }
        counts_pass = counts_pass and per_seed_checks[str(seed)]["pass"]

    status = (
        "PASS"
        if len(records) == 120_000
        and cardinality["total_primary_cache_chunk_refs"] == expected_total
        and counts_pass
        and old_formula_rejected
        else "STOP"
    )
    return {
        "status": status,
        "cache_audit_status": "PASS_CACHE_REUSABLE",
        "inventory_path": str(continuation.INVENTORY_PATH.relative_to(ROOT)),
        "inventory_record_count": int(len(records)),
        "expected_inventory_record_count": 120_000,
        "total_primary_cache_chunk_refs": int(cardinality["total_primary_cache_chunk_refs"]),
        "expected_total_primary_cache_chunk_refs": expected_total,
        "per_seed": per_seed_checks,
        "old_buggy_cardinality_formula": old_formula,
        "old_buggy_cardinality_rejected": bool(old_formula_rejected),
        "cache_arrays_decoded": False,
        "labels_read": False,
        "probe_fitted": False,
        "predictions_computed": False,
        "ap_or_auroc_computed": False,
        "bootstrap_or_sign_flip": False,
        "holm_or_hypothesis_decision": False,
        "stopped_before_scientific_metrics": True,
    }


def main() -> None:
    if REPORT_PATH.exists():
        raise SystemExit(f"refusing to overwrite existing dry-run report: {REPORT_PATH}")
    result = run()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "refs": result["total_primary_cache_chunk_refs"]}, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
