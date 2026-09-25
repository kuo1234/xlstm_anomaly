"""Re-estimate frozen Stage-1 GB10 cost from the measured M1 canary only."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from scripts.adaptive_normality_m1_execute import ARMS, ARM_NAMES, BATCH_SIZE, MAX_EPOCHS
from scripts.adaptive_normality_m1_models import EXPECTED_PARAMETERS
from scripts.adaptive_normality_m1_scores import STAGE1_SCORE_NAMES
from scripts.adaptive_normality_m1_data import D, W


def _manifest_rows(manifest: dict) -> dict[str, int]:
    return {machine: int(values["train_rows"]) for machine, values in manifest["machines"].items()}


def estimate_stage1_compute(canary: dict, manifest: dict,
                            *, available_memory_after_canary_bytes: int | None = None) -> dict[str, Any]:
    """Estimate all frozen fits, val passes, calibration and test forwards.

    Per-machine throughput is assigned from the nearest train-length canary;
    ties prefer the canary with smaller selected rank. The report distinguishes
    directly measured epochs from extrapolated 50-epoch Stage-1 work.
    """
    rows = _manifest_rows(manifest)
    selected = canary["selection"]["selected"]
    canary_rows = {entry["machine"]: int(entry["train_rows"]) for entry in selected}
    measured = {}
    memory_peaks = []
    checkpoint_peaks = []
    for machine_record in canary["machines"]:
        for arm_record in machine_record["arms"]:
            arm = arm_record["arm_key"]
            epoch = arm_record.get("complete_epoch_measurement")
            if arm_record.get("complete_epoch") and epoch:
                train_wps = float(epoch["fit_windows_per_second"])
                train_sps = float(epoch["optimizer_steps_per_second"])
                epoch_seconds = float(epoch["epoch_duration_seconds"])
                allocated = int(epoch["peak_allocated_bytes"])
                reserved = int(epoch["peak_reserved_bytes"])
                checkpoint_io = float(epoch["checkpoint_io_seconds"][0]) if epoch["checkpoint_io_seconds"] else 0.0
            else:
                train = arm_record["bounded_train"]
                train_wps = float(train["windows_per_second"])
                train_sps = float(train["steps_per_second"])
                epoch_seconds = None
                allocated = int(arm_record["bounded_peak_allocated_bytes"])
                reserved = int(arm_record["bounded_peak_reserved_bytes"])
                checkpoint_io = float(arm_record["checkpoint_io_seconds"][0]) if arm_record["checkpoint_io_seconds"] else 0.0
            infer_wps = float(arm_record["forward_inference"]["windows_per_second"])
            measured[(machine_record["machine"], arm)] = {
                "train_windows_per_second": train_wps,
                "optimizer_steps_per_second": train_sps,
                "epoch_seconds": epoch_seconds,
                "inference_windows_per_second": infer_wps,
                "checkpoint_io_seconds": checkpoint_io,
                "checkpoint_bytes": int(arm_record.get("checkpoint_bytes") or 0),
                "peak_allocated_bytes": allocated,
                "peak_reserved_bytes": reserved,
            }
            memory_peaks.append((arm, allocated, reserved))
            checkpoint_peaks.append((arm, int(arm_record.get("checkpoint_bytes") or 0)))

    def nearest_canary(machine: str) -> str:
        n = rows[machine]
        return min(canary_rows, key=lambda selected_machine: (
            abs(canary_rows[selected_machine] - n),
            next(i for i, entry in enumerate(selected) if entry["machine"] == selected_machine)))

    detailed = {arm: [] for arm in ARMS}
    summaries = {}
    for arm in ARMS:
        total_fit = total_val = total_cal = total_test = total_steps = 0
        total_fit_seconds = total_val_seconds = total_infer_seconds = total_checkpoint_seconds = 0.0
        for machine, n in rows.items():
            fit_end, val_end = (7 * n) // 10, (85 * n) // 100
            fit_windows = max(0, fit_end - W + (1 if arm == "xlstmad_r" else 0))
            validation_windows = max(0, val_end - fit_end)
            cal_windows = max(0, n - val_end)
            test_rows = int(manifest["machines"][machine]["test_rows"])
            test_windows = max(0, test_rows - W)
            bucket = nearest_canary(machine)
            perf = measured[(bucket, arm)]
            steps_per_epoch = math.ceil(fit_windows / BATCH_SIZE)
            fit_seconds = fit_windows / perf["train_windows_per_second"]
            validation_seconds = validation_windows / perf["inference_windows_per_second"]
            inference_seconds = (cal_windows + test_windows) / perf["inference_windows_per_second"]
            checkpoint_seconds = perf["checkpoint_io_seconds"]
            machine_fit_seconds = MAX_EPOCHS * (fit_seconds + validation_seconds + checkpoint_seconds)
            total_fit += fit_windows
            total_val += validation_windows
            total_cal += cal_windows
            total_test += test_windows
            total_steps += MAX_EPOCHS * steps_per_epoch
            total_fit_seconds += MAX_EPOCHS * fit_seconds
            total_val_seconds += MAX_EPOCHS * validation_seconds
            total_checkpoint_seconds += MAX_EPOCHS * checkpoint_seconds
            total_infer_seconds += inference_seconds
            detailed[arm].append({
                "machine": machine,
                "train_rows": n,
                "throughput_reference_canary": bucket,
                "fit_windows_per_epoch": fit_windows,
                "validation_windows_per_epoch": validation_windows,
                "calibration_score_windows": cal_windows,
                "test_score_windows_after_t256": test_windows,
                "optimizer_steps_per_epoch": steps_per_epoch,
                "estimated_fit_and_validation_50_epochs_seconds": machine_fit_seconds,
                "estimated_calibration_and_test_forward_seconds": inference_seconds,
            })
        total_seconds = total_fit_seconds + total_val_seconds + total_checkpoint_seconds + total_infer_seconds
        summaries[arm] = {
            "arm": ARM_NAMES[arm],
            "parameter_count": EXPECTED_PARAMETERS[arm],
            "epochs_per_machine": MAX_EPOCHS,
            "machines": len(rows),
            "total_fit_windows_per_epoch": total_fit,
            "total_validation_windows_per_epoch": total_val,
            "total_calibration_windows": total_cal,
            "total_test_windows_from_t256": total_test,
            "total_optimizer_steps_50_epochs": total_steps,
            "measured_canary_train_windows_per_second": {
                "min": min(perf["train_windows_per_second"] for (machine, arm_key), perf in measured.items() if arm_key == arm),
                "median": sorted(perf["train_windows_per_second"] for (machine, arm_key), perf in measured.items() if arm_key == arm)[1],
                "max": max(perf["train_windows_per_second"] for (machine, arm_key), perf in measured.items() if arm_key == arm),
            },
            "measured_canary_forward_windows_per_second": {
                "min": min(perf["inference_windows_per_second"] for (machine, arm_key), perf in measured.items() if arm_key == arm),
                "median": sorted(perf["inference_windows_per_second"] for (machine, arm_key), perf in measured.items() if arm_key == arm)[1],
                "max": max(perf["inference_windows_per_second"] for (machine, arm_key), perf in measured.items() if arm_key == arm),
            },
            "estimated_fit_training_hours": total_fit_seconds / 3600.0,
            "estimated_validation_hours": total_val_seconds / 3600.0,
            "estimated_checkpoint_io_hours": total_checkpoint_seconds / 3600.0,
            "estimated_calibration_and_test_inference_hours": total_infer_seconds / 3600.0,
            "estimated_serial_GB10_hours": total_seconds / 3600.0,
        }

    total_serial_seconds = sum(row["estimated_serial_GB10_hours"] for row in summaries.values()) * 3600.0
    by_memory = sorted((reserved for _, _, reserved in memory_peaks), reverse=True)
    max_one_reserved = by_memory[0] if by_memory else 0
    max_two_reserved = sum(by_memory[:2]) if len(by_memory) >= 2 else max_one_reserved
    if available_memory_after_canary_bytes is None:
        available_memory_after_canary_bytes = int(
            canary.get("environment", {}).get("gpu_free_memory_after_canary_bytes", 0))
    gpu_total = int(canary["environment"]["gpu_total_memory_bytes"])
    available = int(available_memory_after_canary_bytes)
    two_fit_memory_permitted = available > 0 and max_two_reserved * 1.15 <= available
    # Timed overlap is not measured. If memory permits, report the idealized
    # lower bound for two workers; otherwise use serial measured-rate runtime.
    expected_wall_seconds = total_serial_seconds / 2.0 if two_fit_memory_permitted else total_serial_seconds
    feature_bytes = sum(int(v[s]["bytes"]) for v in manifest["machines"].values() for s in ("train", "test"))
    score_values = sum(max(0, int(v["test_rows"]) - W) for v in manifest["machines"].values())
    uncompressed_score_bytes = score_values * 8 * (len(STAGE1_SCORE_NAMES) + 1)
    calibration_artifact_bytes = sum(
        ((cal_windows + 1) // 2) * (len(STAGE1_SCORE_NAMES) * 8 + 8) +
        (cal_windows // 2) * 7 * 8
        for cal_windows in (int(v["train_rows"]) - (85 * int(v["train_rows"]) // 100)
                            for v in manifest["machines"].values())
    )
    scaler_artifact_bytes = len(rows) * (D * 3 * 8 + 8 + 2 * 8)
    best_checkpoint_bytes = sum(
        28 * size for arm, size in {name: max((n for key, n in checkpoint_peaks if key == name), default=0)
                                    for name in ARMS}.items())
    run_record_bytes = 28 * len(ARMS) * 12_000  # 50-epoch JSON curve allowance
    artifact_bytes = (feature_bytes + uncompressed_score_bytes + calibration_artifact_bytes +
                      scaler_artifact_bytes + best_checkpoint_bytes + run_record_bytes)
    disk_requirement = math.ceil(artifact_bytes * 1.25)
    return {
        "schema": "adaptive-normality-m1-stage1-compute-estimate-v1",
        "status": "ENGINEERING_ESTIMATE_ONLY",
        "source_timing_canary": "reports/adaptive_normality_m1_smd/timing_canary.json",
        "frozen_configuration": {"machines": 28, "W": W, "D": D,
            "seed": 11, "epochs": MAX_EPOCHS, "batch_size": BATCH_SIZE,
            "no_parameter_or_hyperparameter_changes": True},
        "throughput_assignment": "nearest canary by absolute train-row length; ties follow shortest, median, longest selection order",
        "learned_arms": summaries,
        "serial_GB10_hours": total_serial_seconds / 3600.0,
        "planning_contingency": {
            "percentage": 25,
            "serial_GB10_hours_with_contingency": total_serial_seconds * 1.25 / 3600.0,
            "expected_wall_hours_with_contingency": expected_wall_seconds * 1.25 / 3600.0,
            "purpose": "engineering schedule margin for run-to-run and per-machine throughput variation; does not change scientific configuration",
        },
        "serial_components": {"xLSTMAD-R": summaries["xlstmad_r"]["estimated_serial_GB10_hours"],
                              "xLSTMAD-F": summaries["xlstmad_f"]["estimated_serial_GB10_hours"],
                              "LSTM-F": summaries["lstm_f"]["estimated_serial_GB10_hours"]},
        "concurrency": {
            "fit_peak_reserved_bytes": int(max_one_reserved),
            "two_fit_peak_reserved_bytes": int(max_two_reserved),
            "available_device_memory_after_canary_bytes": available,
            "device_total_memory_bytes": gpu_total,
            "one_fit_margin_against_available_bytes": max(0, available - max_one_reserved),
            "two_concurrent_fits_permitted_with_15pct_margin": bool(two_fit_memory_permitted),
            "expected_wall_hours_at_at_most_two_concurrent_fits": expected_wall_seconds / 3600.0,
            "wall_time_basis": "two-worker idealized estimate only if measured free memory permits; otherwise serial",
            "concurrent_throughput_contention_measured": False,
        },
        "disk": {"pinned_train_test_feature_bytes": feature_bytes,
                 "uncompressed_nine_score_plus_timestamp_bytes": uncompressed_score_bytes,
                 "uncompressed_calibration_score_and_tail_reference_bytes": calibration_artifact_bytes,
                 "uncompressed_scaler_artifact_bytes": scaler_artifact_bytes,
                 "best_checkpoint_bytes_all_machine_arms": best_checkpoint_bytes,
                 "run_record_allowance_bytes": run_record_bytes,
                 "total_with_25pct_staging_margin_bytes": disk_requirement,
                 "total_with_25pct_staging_margin_GiB": disk_requirement / (1024 ** 3)},
        "per_machine_fit_estimates": detailed,
        "exclusions": ["No Stage-1 training run was performed; timings are measured only on nine one-epoch canary fits.",
                       "Two-fit concurrent throughput was not measured.",
                       "CPU cheap-control scoring is excluded from GB10 hours.",
                       "No scientific gate, cohort, hyperparameter, or model arm was changed."],
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canary", type=Path,
                        default=Path("reports/adaptive_normality_m1_smd/timing_canary.json"))
    parser.add_argument("--manifest", type=Path,
                        default=Path("research/adaptive_normality_m1_smd/smd_28_manifest.json"))
    parser.add_argument("--output", type=Path,
                        default=Path("reports/adaptive_normality_m1_smd/compute_estimate.json"))
    parser.add_argument("--available-memory-after-canary-bytes", type=int, default=None)
    args = parser.parse_args()
    estimate = estimate_stage1_compute(json.loads(args.canary.read_text()),
        json.loads(args.manifest.read_text()),
        available_memory_after_canary_bytes=args.available_memory_after_canary_bytes)
    if args.output.exists():
        raise FileExistsError(f"immutable compute estimate exists: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(estimate, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"serial_GB10_hours": estimate["serial_GB10_hours"],
                      "serial_components": estimate["serial_components"],
                      "expected_wall_hours_at_at_most_two_concurrent_fits": estimate["concurrency"]["expected_wall_hours_at_at_most_two_concurrent_fits"],
                      "serial_GB10_hours_with_contingency": estimate["planning_contingency"]["serial_GB10_hours_with_contingency"],
                      "two_concurrent_fits_permitted": estimate["concurrency"]["two_concurrent_fits_permitted_with_15pct_margin"],
                      "disk_GiB": estimate["disk"]["total_with_25pct_staging_margin_GiB"]},
                     sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
