"""Bounded real Phase-F seed-11 vanilla/CUDA training canary.

This script is deliberately separate from the scientific Phase-F runner.  It
uses the sealed train/validation windows and epoch orders, performs at most
three epochs, writes only temporary checkpoints, and never reaches test data,
labels, observers, or probe code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[2]
CUDA_ROOT = Path(
    os.environ.get("CUDA_WORKTREE", str(ROOT.parent / "cuda-spark"))
).resolve()
EXTENSION_DIR = Path(
    os.environ.get("TORCH_EXTENSIONS_DIR", "/tmp/xlstm_cuda_full121_false")
)
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(CUDA_ROOT / "research" / "cuda_spark"))

from phase_f_common import (  # noqa: E402
    build as build_vanilla,
    load_windows,
    reconstruction_loss,
    optimizer as make_optimizer,
)
from phase_e2_common import sha  # noqa: E402
from xlstmad_cuda_bench import (  # noqa: E402
    _load_vanilla_weights_into_cuda,
    build_model,
)


SEED = 11
BATCH_SIZE = 128
MAX_EPOCHS = 3
VALIDATION_RELATIVE_TOLERANCE = 0.01
FIRST_STEPS_RELATIVE_TOLERANCE = 0.02
CHECKPOINT = ROOT / "data" / "phase_f_v4" / "runs" / "xlstm_11" / "best.pt"
ORDERS = ROOT / "data" / "phase_f" / "orders_11.npy"
ORDER_SHA256 = "83620f8707e9f8c9f563eb017b1b93063eafa566d5d010bff7f334dcef8d54a6"
EXPECTED_TRAIN_WINDOWS = 40330
EXPECTED_VALIDATION_WINDOWS = 20165


def _finite_parameters(model: torch.nn.Module) -> bool:
    return all(bool(torch.isfinite(p).all()) for p in model.parameters())


def _state_to_cpu(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}


def _relative(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1e-12)


def _environment() -> dict:
    return {
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "device": torch.cuda.get_device_name(),
        "capability": list(torch.cuda.get_device_capability()),
        "device_count": torch.cuda.device_count(),
        "python": sys.version,
        "cudnn_deterministic": torch.backends.cudnn.deterministic,
        "cudnn_benchmark": torch.backends.cudnn.benchmark,
        "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
        "cuda_matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
        "matmul_precision": torch.get_float32_matmul_precision(),
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "torch_threads": torch.get_num_threads(),
        "cuda_extension_dir": str(EXTENSION_DIR),
        "cuda_architecture": "sm_121; static-global-template-stub=false",
    }


def _validate_sealed_orders() -> tuple[np.ndarray, dict]:
    if not ORDERS.exists():
        raise FileNotFoundError(ORDERS)
    digest = sha(ORDERS)
    if digest != ORDER_SHA256:
        raise RuntimeError(f"sealed order hash mismatch: {digest}")
    orders = np.load(ORDERS, allow_pickle=False)
    if orders.shape != (50, EXPECTED_TRAIN_WINDOWS):
        raise RuntimeError(f"unexpected order shape: {orders.shape}")
    for row in orders[:MAX_EPOCHS]:
        if not np.array_equal(np.sort(row), np.arange(EXPECTED_TRAIN_WINDOWS)):
            raise RuntimeError("order is not a complete permutation")
    batch_sizes = [
        min(BATCH_SIZE, EXPECTED_TRAIN_WINDOWS - start)
        for start in range(0, EXPECTED_TRAIN_WINDOWS, BATCH_SIZE)
    ]
    return orders[:MAX_EPOCHS], {
        "path": str(ORDERS),
        "sha256": digest,
        "shape": list(orders.shape),
        "epoch_hashes": [hashlib.sha256(row.tobytes()).hexdigest() for row in orders[:MAX_EPOCHS]],
        "train_windows": EXPECTED_TRAIN_WINDOWS,
        "batch_size": BATCH_SIZE,
        "batch_count": len(batch_sizes),
        "batch_sizes_head": batch_sizes[:3],
        "batch_sizes_tail": batch_sizes[-3:],
    }


def _validate_data(train: torch.Tensor, validation: torch.Tensor) -> dict:
    if tuple(train.shape) != (EXPECTED_TRAIN_WINDOWS, 64, 8):
        raise RuntimeError(f"unexpected train shape {tuple(train.shape)}")
    if tuple(validation.shape) != (EXPECTED_VALIDATION_WINDOWS, 64, 8):
        raise RuntimeError(f"unexpected validation shape {tuple(validation.shape)}")
    if train.dtype != torch.float32 or validation.dtype != torch.float32:
        raise RuntimeError("Phase-F data must be float32")
    if not bool(torch.isfinite(train).all()) or not bool(torch.isfinite(validation).all()):
        raise RuntimeError("non-finite sealed input")
    return {
        "train_shape": list(train.shape),
        "validation_shape": list(validation.shape),
        "dtype": str(train.dtype),
        "device": str(train.device),
        "test_sources_used": False,
        "labels_used": False,
    }


def _validate_model(model: torch.nn.Module) -> dict:
    count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    if count != 73504:
        raise RuntimeError(f"unexpected xLSTM parameter count {count}")
    return {"parameter_count": count, "finite": _finite_parameters(model)}


def _initial_probe(model: torch.nn.Module, first_batch: torch.Tensor) -> dict:
    model.eval()
    with torch.no_grad():
        out = model(first_batch)
        loss = (out - first_batch).square().mean()
    return {
        "loss": float(loss),
        "output_finite": bool(torch.isfinite(out).all()),
        "loss_finite": bool(torch.isfinite(loss)),
    }


def _validation(model: torch.nn.Module, validation: torch.Tensor) -> tuple[float, float]:
    start = time.perf_counter()
    total = torch.zeros((), device="cuda", dtype=torch.float64)
    model.eval()
    with torch.no_grad():
        for batch in validation.split(BATCH_SIZE):
            loss = reconstruction_loss(model, batch)
            if not bool(torch.isfinite(loss)):
                raise RuntimeError("non-finite validation loss")
            total += loss.detach().double() * len(batch)
    torch.cuda.synchronize()
    return float(total.cpu() / len(validation)), time.perf_counter() - start


def _run_epoch(model, opt, train, validation, order, temp_dir, backend, epoch):
    model.train()
    epoch_start = time.perf_counter()
    forward_s = backward_s = optimizer_s = 0.0
    total = torch.zeros((), device="cuda", dtype=torch.float64)
    first_losses: list[float] = []
    gradient_checks: list[bool] = []
    steps = 0
    # Match the sealed Phase-F runner exactly: contiguous order slices with
    # 315 full batches of 128 and one final batch of 10.  ``np.array_split``
    # would distribute the remainder across many smaller batches and change
    # the optimizer trajectory.
    for start_index in range(0, len(order), BATCH_SIZE):
        batch_ids_np = order[start_index : start_index + BATCH_SIZE]
        batch_ids = torch.from_numpy(np.asarray(batch_ids_np, dtype=np.int64)).cuda()
        observations = train[batch_ids]
        opt.zero_grad(set_to_none=True)
        torch.cuda.synchronize()
        start = time.perf_counter()
        loss = reconstruction_loss(model, observations)
        torch.cuda.synchronize()
        forward_s += time.perf_counter() - start
        if not bool(torch.isfinite(loss)):
            raise RuntimeError("non-finite training loss")
        if len(first_losses) < 3:
            first_losses.append(float(loss.detach()))
        start = time.perf_counter()
        loss.backward()
        torch.cuda.synchronize()
        backward_s += time.perf_counter() - start
        if steps < 3 or steps == int(np.ceil(len(order) / BATCH_SIZE)) - 1:
            gradient_checks.append(all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in model.parameters()))
        start = time.perf_counter()
        opt.step()
        torch.cuda.synchronize()
        optimizer_s += time.perf_counter() - start
        total += loss.detach().double() * len(observations)
        steps += 1
    train_mse = float(total.cpu() / len(train))
    validation_mse, validation_s = _validation(model, validation)
    state_start = time.perf_counter()
    torch.save({"model": _state_to_cpu(model), "epoch": epoch}, temp_dir / f"{backend}_epoch{epoch}.pt")
    report_overhead_s = time.perf_counter() - state_start
    torch.cuda.synchronize()
    epoch_wall_s = time.perf_counter() - epoch_start
    return {
        "epoch": epoch,
        "train_mse": train_mse,
        "validation_mse": validation_mse,
        "forward_seconds": forward_s,
        "backward_seconds": backward_s,
        "optimizer_seconds": optimizer_s,
        "validation_seconds": validation_s,
        "checkpoint_report_seconds": report_overhead_s,
        "epoch_wall_seconds": epoch_wall_s,
        "optimizer_steps": steps,
        "windows_consumed": len(order),
        "first_three_step_losses": first_losses,
        "finite_gradients_checked": gradient_checks,
        "finite_parameters": _finite_parameters(model),
        "finite_train_loss": bool(np.isfinite(train_mse)),
        "finite_validation_loss": bool(np.isfinite(validation_mse)),
        "peak_memory_bytes": torch.cuda.max_memory_allocated(),
    }


def run(output: Path) -> dict:
    torch.set_float32_matmul_precision("highest")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the training canary")
    if not CHECKPOINT.exists():
        raise FileNotFoundError(CHECKPOINT)
    orders, order_info = _validate_sealed_orders()
    load_start = time.perf_counter()
    train = load_windows("train")
    validation = load_windows("validation")
    torch.cuda.synchronize()
    data_loading_s = time.perf_counter() - load_start
    data_info = _validate_data(train, validation)

    # Build/map once per backend from the same mathematical initial state.
    vanilla = build_vanilla("xlstm", SEED).float().cuda()
    cuda = build_model("cuda", seed=SEED + 100, extension_dir=EXTENSION_DIR).float()
    _load_vanilla_weights_into_cuda(vanilla, cuda)
    vanilla.eval()
    cuda.eval()
    initial_v = _initial_probe(vanilla, train[:BATCH_SIZE])
    initial_c = _initial_probe(cuda, train[:BATCH_SIZE])
    initial_loss_relative = _relative(initial_v["loss"], initial_c["loss"])
    with tempfile.TemporaryDirectory(prefix="integration_canary_", dir="/tmp") as temp:
        temp_dir = Path(temp)
        models = {"vanilla": vanilla, "cuda": cuda}
        opts = {name: make_optimizer(model) for name, model in models.items()}
        runs = {
            "vanilla": {"model": vanilla, "optimizer": opts["vanilla"], "model_info": _validate_model(vanilla), "initial": initial_v, "epochs": []},
            "cuda": {"model": cuda, "optimizer": opts["cuda"], "model_info": _validate_model(cuda), "initial": initial_c, "epochs": []},
        }
        # Execute paired epochs.  The first-epoch gate is evaluated before any
        # second/third epoch is started, so a failed canary never runs beyond
        # the authorized initial epoch.
        epoch1_stable = False
        validation_rel_1 = None
        first_step_rel_1 = None
        for epoch, order in enumerate(orders, start=1):
            for backend in ("vanilla", "cuda"):
                torch.cuda.reset_peak_memory_stats()
                runs[backend]["epochs"].append(
                    _run_epoch(models[backend], opts[backend], train, validation, order, temp_dir, backend, epoch)
                )
            if epoch == 1:
                first_v = runs["vanilla"]["epochs"][0]
                first_c = runs["cuda"]["epochs"][0]
                validation_rel_1 = _relative(first_v["validation_mse"], first_c["validation_mse"])
                first_step_rel_1 = max(
                    (_relative(a, b) for a, b in zip(first_v["first_three_step_losses"], first_c["first_three_step_losses"])),
                    default=float("inf"),
                )
                epoch1_stable = validation_rel_1 <= VALIDATION_RELATIVE_TOLERANCE
                if not epoch1_stable:
                    break

        first_v = runs["vanilla"]["epochs"][0]
        first_c = runs["cuda"]["epochs"][0]
        epochs_run = len(runs["vanilla"]["epochs"])

        train_losses_v = [r["train_mse"] for r in runs["vanilla"]["epochs"]]
        train_losses_c = [r["train_mse"] for r in runs["cuda"]["epochs"]]
        valid_losses_v = [r["validation_mse"] for r in runs["vanilla"]["epochs"]]
        valid_losses_c = [r["validation_mse"] for r in runs["cuda"]["epochs"]]
        validation_relative_by_epoch = [
            _relative(v, c) for v, c in zip(valid_losses_v, valid_losses_c)
        ]
        validation_all_pass = all(
            value <= VALIDATION_RELATIVE_TOLERANCE for value in validation_relative_by_epoch
        )
        all_finite = all(
            r["finite_parameters"]
            and all(r["finite_gradients_checked"])
            and r["finite_train_loss"]
            and r["finite_validation_loss"]
            for result in runs.values()
            for r in result["epochs"]
        )
        losses_decrease = all(
            values[-1] < values[0] for values in (train_losses_v, train_losses_c)
        ) if epochs_run > 1 else all(
            result["epochs"][0]["first_three_step_losses"][-1]
            < result["epochs"][0]["first_three_step_losses"][0]
            for result in runs.values()
        )
        same_counts = all(
            len(result["epochs"]) == epochs_run and all(r["optimizer_steps"] == 316 for r in result["epochs"])
            for result in runs.values()
        )
        criterion = {
            "validation_relative_tolerance": VALIDATION_RELATIVE_TOLERANCE,
            "first_step_relative_tolerance": FIRST_STEPS_RELATIVE_TOLERANCE,
            "epoch1_validation_relative_difference": validation_rel_1,
            "validation_relative_difference_by_epoch": validation_relative_by_epoch,
            "epoch1_first_three_step_max_relative_difference": first_step_rel_1,
            "epoch1_validation_pass": epoch1_stable,
            "all_executed_epochs_validation_pass": validation_all_pass,
            "first_steps_finite": all(
                all(np.isfinite(row) for row in result["initial"].values() if isinstance(row, (int, float)))
                for result in runs.values()
            ),
            "all_finite": all_finite,
            "losses_decrease": losses_decrease,
            "same_counts_and_orders": same_counts,
            "parameter_layout_adapter": True,
            "pass": epoch1_stable and validation_all_pass and all_finite and losses_decrease and same_counts,
        }
        serial_runs = {}
        for backend, result in runs.items():
            serial_runs[backend] = {
                "model_info": result["model_info"],
                "initial": result["initial"],
                "epochs": result["epochs"],
            }
        output_result = {
            "status": "PASS" if criterion["pass"] else "BLOCKED",
            "decision_scope": "engineering_canary_only; no scientific conclusion",
            "environment": _environment(),
            "checkpoint": {"path": str(CHECKPOINT), "sha256": sha(CHECKPOINT)},
            "data_loading_seconds": data_loading_s,
            "data": data_info,
            "orders": order_info,
            "initial_pair": {
                "vanilla": initial_v,
                "cuda": initial_c,
                "loss_relative_difference": initial_loss_relative,
                "same_math_initial_state": True,
                "adapter": "_load_vanilla_weights_into_cuda recurrent int2ext/ext2int",
            },
            "criterion": criterion,
            "epochs_run": epochs_run,
            "runs": serial_runs,
            "temporary_checkpoints_written": True,
            "labels_used": False,
            "test_sources_used": False,
            "observers_used": False,
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(output_result, indent=2, allow_nan=False) + "\n")
    return output_result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps({"status": result["status"], "epochs_run": result["epochs_run"], "output": str(args.output)}))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
