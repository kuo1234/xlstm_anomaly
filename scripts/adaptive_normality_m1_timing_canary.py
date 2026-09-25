"""Result-blind GB10 engineering canary for M1 learned arms.

Selection depends only on committed train-row counts in the M1 data manifest.
The canary never requests test observations or labels and writes only an
engineering timing record, not scientific score artifacts.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np

try:
    from scripts import adaptive_normality_m1_data as data
    from scripts import adaptive_normality_m1_execute as execute
    from scripts import adaptive_normality_m1_models as models
except ImportError:  # direct script execution
    import adaptive_normality_m1_data as data
    import adaptive_normality_m1_execute as execute
    import adaptive_normality_m1_models as models


BOUNDED_BATCHES = 4
VALIDATION_BATCHES = 4
MAX_FULL_EPOCH_SECONDS_PER_CASE = 600.0
MAX_TOTAL_FULL_EPOCH_SECONDS = 1800.0


def training_scope_record() -> dict[str, bool]:
    """Flags written only by a completed canary invocation."""
    return {"canary_training_started": True, "full_stage1_training_started": False}


def select_canary_machines(manifest: dict | None = None) -> dict[str, Any]:
    """Choose shortest, lower-median-rank, and longest by train length only."""
    source = data.MANIFEST if manifest is None else manifest
    ordered = sorted((int(values["train_rows"]), str(name))
                     for name, values in source["machines"].items())
    if len(ordered) != 28:
        raise RuntimeError(f"canary selection requires 28 manifest machines, found {len(ordered)}")
    selected = [ordered[0], ordered[(len(ordered) - 1) // 2], ordered[-1]]
    labels = ("shortest", "median_lower_rank", "longest")
    return {
        "selection_rule": "sort by (train_rows, machine_name); choose rank 0, lower median rank floor((28-1)/2)=13, and rank 27",
        "train_rows_only": True,
        "selected": [{"role": role, "machine": machine, "train_rows": rows,
                      "sorted_rank_zero_based": rank}
                     for role, (rows, machine), rank in zip(labels, selected,
                         (0, (len(ordered) - 1) // 2, len(ordered) - 1))],
    }


def _forward_throughput(model, z: np.ndarray, arm: str, endpoints: np.ndarray,
                        *, device: str, max_batches: int = VALIDATION_BATCHES) -> dict[str, Any]:
    torch = models.configure_runtime()["torch"]
    model.eval()
    selected = endpoints[:max_batches * execute.BATCH_SIZE]
    start = time.perf_counter()
    count = 0
    with torch.inference_mode():
        for offset in range(0, len(selected), execute.BATCH_SIZE):
            ts = selected[offset:offset + execute.BATCH_SIZE]
            if arm == "xlstmad_r":
                windows = np.stack([data.reconstruction_window(z, int(t), 0, len(z)) for t in ts])
            else:
                windows = np.stack([np.array(z[int(t)-data.W:int(t)], copy=True) for t in ts])
            x = torch.as_tensor(windows, dtype=torch.float32, device=device)
            out = model(x)
            if not bool(torch.isfinite(out).all()):
                raise RuntimeError(f"{arm} canary inference returned non-finite values")
            count += len(ts)
    if str(device).startswith("cuda"):
        torch.cuda.synchronize(device)
    duration = time.perf_counter() - start
    return {"windows": count, "seconds": duration,
            "windows_per_second": count / duration if duration else float("inf"),
            "batches": int(np.ceil(count / execute.BATCH_SIZE))}


def _environment() -> dict[str, Any]:
    record = execute.environment_record()
    torch = models.configure_runtime()["torch"]
    if not torch.cuda.is_available():
        raise RuntimeError("the authorized timing canary requires a visible GB10 CUDA device")
    free_bytes, total_bytes = torch.cuda.mem_get_info(0)
    record["gpu_total_memory_bytes"] = int(total_bytes)
    record["gpu_free_memory_before_canary_bytes"] = int(free_bytes)
    record["device_index"] = 0
    return record


def run_timing_canary(*, data_root: Path | None = None,
                      output: Path | None = None,
                      device: str = "cuda:0") -> dict[str, Any]:
    """Measure bounded fit batches, validation forwards, and affordable epochs."""
    data.install_test_label_access_guard()
    selection = select_canary_machines()
    environment = _environment()
    results = []
    for selected in selection["selected"]:
        machine = selected["machine"]
        train = data.load_train(machine, data_root)
        blocks = data.split_boundaries(len(train))
        transform = data.RobustScaler().fit(train, blocks.fit[1]).statistics
        if transform is None:
            raise RuntimeError("scaler did not produce frozen fit statistics")
        z = data.apply_robust_transform(train, transform)
        bounds = {"fit": blocks.fit, "validation": blocks.validation,
                  "calibration": blocks.calibration}
        fit_counts = {}
        arm_results = []
        for arm in execute.ARMS:
            expected_fit_windows = len(execute._fit_endpoints(arm, blocks.fit))
            fit_counts[arm] = expected_fit_windows
            with tempfile.TemporaryDirectory(prefix="m1-canary-checkpoint-") as checkpoint_dir:
                model, bounded = execute.fit_arm(
                    z, bounds, arm, device=device, seed=execute.SEED,
                    max_epochs=1, max_batches_per_epoch=BOUNDED_BATCHES,
                    validation_max_batches=VALIDATION_BATCHES,
                    checkpoint_path=Path(checkpoint_dir) / "best.pt")
                train_measure = bounded["history"][0]["train"]
                validation_measure = bounded["history"][0]["validation"]
                inference = _forward_throughput(
                    model, z, arm, execute._validation_endpoints(blocks.validation),
                    device=device, max_batches=VALIDATION_BATCHES)
                projected_full_epoch = (
                    expected_fit_windows / train_measure["windows_per_second"] +
                    len(execute._validation_endpoints(blocks.validation)) / inference["windows_per_second"]
                )
                arm_results.append({
                    "arm": execute.ARM_NAMES[arm], "arm_key": arm,
                    "parameter_count": bounded["parameter_count"],
                    "fit_windows_per_epoch": expected_fit_windows,
                    "bounded_batches": BOUNDED_BATCHES,
                    "bounded_train": train_measure,
                    "bounded_validation": validation_measure,
                    "forward_inference": inference,
                    "projected_one_epoch_seconds_from_bounded_throughput": projected_full_epoch,
                    "bounded_peak_allocated_bytes": bounded["peak_allocated_bytes"],
                    "bounded_peak_reserved_bytes": bounded["peak_reserved_bytes"],
                    "checkpoint_io_seconds": bounded["checkpoint_io_seconds"],
                    "checkpoint_bytes": (bounded["best_checkpoint"] or {}).get("bytes"),
                    "complete_epoch": False,
                })
        results.append({
            **selected,
            "fit_bounds": list(blocks.fit), "validation_bounds": list(blocks.validation),
            "calibration_bounds_not_used": list(blocks.calibration),
            "fit_transform_sha256": {
                "center": __import__("hashlib").sha256(transform.center.tobytes()).hexdigest(),
                "scale": __import__("hashlib").sha256(transform.scale.tobytes()).hexdigest(),
            },
            "arms": arm_results,
            "test_observations_read": False,
            "test_labels_read": False,
        })

    all_estimates = [arm["projected_one_epoch_seconds_from_bounded_throughput"]
                     for machine in results for arm in machine["arms"]]
    full_epoch_affordable = (
        max(all_estimates, default=float("inf")) <= MAX_FULL_EPOCH_SECONDS_PER_CASE and
        sum(all_estimates) <= MAX_TOTAL_FULL_EPOCH_SECONDS
    )
    epoch_rule = {
        "rule": "run one complete epoch for all nine arm/machine cases only if each projected epoch is <=600 s and their sum is <=1800 s",
        "threshold_seconds_per_case": MAX_FULL_EPOCH_SECONDS_PER_CASE,
        "threshold_total_seconds": MAX_TOTAL_FULL_EPOCH_SECONDS,
        "projected_total_seconds": float(sum(all_estimates)),
        "complete_epoch_authorized_by_canary_rule": bool(full_epoch_affordable),
    }
    if full_epoch_affordable:
        # Reinitialize each case from the frozen seed and run a whole first epoch.
        # This remains a timing-only sample and produces no anomaly score.
        for machine_row in results:
            machine = machine_row["machine"]
            train = data.load_train(machine, data_root)
            blocks = data.split_boundaries(len(train))
            transform = data.RobustScaler().fit(train, blocks.fit[1]).statistics
            assert transform is not None
            z = data.apply_robust_transform(train, transform)
            bounds = {"fit": blocks.fit, "validation": blocks.validation,
                      "calibration": blocks.calibration}
            for arm_result in machine_row["arms"]:
                arm = arm_result["arm_key"]
                with tempfile.TemporaryDirectory(prefix="m1-canary-epoch-") as checkpoint_dir:
                    _, complete = execute.fit_arm(
                        z, bounds, arm, device=device, seed=execute.SEED,
                        max_epochs=1, checkpoint_path=Path(checkpoint_dir) / "best.pt")
                epoch = complete["history"][0]
                arm_result["complete_epoch"] = True
                arm_result["complete_epoch_measurement"] = {
                    "train": epoch["train"], "validation": epoch["validation"],
                    "epoch_duration_seconds": epoch["train"]["seconds"] + epoch["validation"]["seconds"],
                    "fit_windows_per_second": epoch["train"]["windows_per_second"],
                    "optimizer_steps_per_second": epoch["train"]["steps_per_second"],
                    "peak_allocated_bytes": complete["peak_allocated_bytes"],
                    "peak_reserved_bytes": complete["peak_reserved_bytes"],
                    "checkpoint_io_seconds": complete["checkpoint_io_seconds"],
                    "checkpoint_bytes": (complete["best_checkpoint"] or {}).get("bytes"),
                }

    report = {
        "schema": "adaptive-normality-m1-engineering-canary-v1",
        "purpose": "engineering feasibility only; no anomaly result",
        "selection": selection,
        "canary_hyperparameters": {"W": data.W, "D": data.D,
            "batch_size": execute.BATCH_SIZE, "seed": execute.SEED,
            "max_epochs": execute.MAX_EPOCHS,
            "learning_rate": execute.LEARNING_RATE,
            "bounded_batches_per_case": BOUNDED_BATCHES,
            "validation_batches": VALIDATION_BATCHES},
        "environment": environment,
        "complete_epoch_decision": epoch_rule,
        "machines": results,
        "test_observations_read": False,
        "test_labels_read": False,
        "test_label_open_attempts": data.test_label_open_attempt_count(),
        "anomaly_metrics_computed": False,
        **training_scope_record(),
    }
    report["timing_completed_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    target = output or (Path(__file__).resolve().parents[1] /
                        "reports/adaptive_normality_m1_smd/timing_canary.json")
    if target.exists():
        raise FileExistsError(f"immutable timing-canary output exists: {target}")
    execute.immutable_json_write(target, report)
    return report


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    print(json.dumps(run_timing_canary(data_root=args.data_root,
                                      output=args.output, device=args.device),
                     sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
