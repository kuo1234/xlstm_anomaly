"""One fresh Phase F-v4 training run.

This is the frozen F-v3 scientific training loop with only the versioned
artifact namespace and F-v4 canary/parity validity contract changed.  It is
never used for H2/H3 labels or test-source evaluation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import resource
import subprocess
import time

import numpy as np
import torch

from phase_f_v4_common import *
from phase_f_v4_canary import canary
from phase_f_v4_parity import parity


def cpu_state(model):
    return {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}


def _checkpoint_hashes(directory):
    return {str(path.name): sha(path) for path in sorted(directory.glob("*.pt"))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("architecture", choices=("xlstm", "lstm"))
    parser.add_argument("seed", type=int)
    args = parser.parse_args()
    if args.seed not in CONFIG["detector_seeds"]:
        raise ValueError("Unregistered detector seed")

    start = time.perf_counter()
    environment = configure()
    sealed = verify_sealed_inputs()
    gates_path = REPORT / "mechanical_gates.json"
    if not gates_path.exists():
        raise SystemExit("F-v4 mechanical gates are not sealed; training forbidden")
    gates = json.loads(gates_path.read_text())
    if gates.get("status") != "PASS":
        raise SystemExit("F-v4 mechanical gates are not PASS; training forbidden")

    # Reuse only sealed clean prefixes/scalers/orders.  No test source is
    # reachable through load_windows or verify_sealed_inputs.
    orderinfo = sealed["orders"][str(args.seed)]
    orders = np.load(ROOT / orderinfo["path"], allow_pickle=False)
    expected_epochs = int(CONFIG["epochs"])
    expected_windows = int(sealed.get("train_windows", 40330))
    if orders.shape != (expected_epochs, expected_windows):
        raise RuntimeError(f"Unexpected sealed order shape: {orders.shape}")
    for epoch, row in enumerate(orders):
        if hashlib.sha256(row.tobytes()).hexdigest() != orderinfo["epoch_sha256"][epoch]:
            raise RuntimeError("Sealed epoch order hash mismatch")
        if not np.array_equal(np.sort(row), np.arange(expected_windows)):
            raise RuntimeError("Sealed epoch order is not a permutation")

    run_name = f"{args.architecture}_{args.seed}"
    data_dir = ROOT / "data" / "phase_f_v4" / "runs" / run_name
    report_dir = REPORT / "runs" / run_name
    # A fresh run must never overwrite/reuse a partial or quarantined state.
    if data_dir.exists() or report_dir.exists():
        raise SystemExit(f"F-v4 run path already exists; refusing reuse: {run_name}")
    data_dir.mkdir(parents=True, exist_ok=False)
    report_dir.mkdir(parents=True, exist_ok=False)

    train = load_windows("train")
    validation = load_windows("validation")
    fixed_canary = canary_input()
    canary_hash = hashlib.sha256(fixed_canary.detach().cpu().numpy().tobytes()).hexdigest()

    model = build(args.architecture, args.seed)
    model.train()
    opt = optimizer(model)
    expected_optimizer = dict(CONFIG["optimizer"])
    expected_optimizer["betas"] = tuple(expected_optimizer["betas"])
    if any(opt.defaults[key] != value for key, value in expected_optimizer.items()):
        raise RuntimeError("Optimizer semantics do not match sealed config")

    initial = cpu_state(model)
    initial_hash = model_hash(model)
    torch.save(initial, data_dir / "initial.pt")
    order_hasher = hashlib.sha256()
    curves = []
    best_validation = float("inf")
    best_epoch = None
    optimizer_steps = 0
    exposures = 0
    batch_size = int(CONFIG["batch_size"])
    train_steps_per_epoch = (len(train) + batch_size - 1) // batch_size

    torch.cuda.reset_peak_memory_stats()
    training_start = time.perf_counter()
    with forbid_native_predict() as native_predict_trap:
        for epoch in range(expected_epochs):
            epoch_start = time.perf_counter()
            model.train()
            total = torch.zeros((), device="cuda", dtype=torch.float64)
            order = orders[epoch]
            order_hasher.update(order.tobytes())
            ids = torch.from_numpy(order.copy()).cuda()
            for batch_ids in ids.split(batch_size):
                observations = train[batch_ids]
                opt.zero_grad(set_to_none=True)
                loss = reconstruction_loss(model, observations)
                if not bool(torch.isfinite(loss)):
                    raise RuntimeError("Nonfinite training loss")
                loss.backward()
                if not all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in model.parameters()):
                    raise RuntimeError("Nonfinite training gradient")
                opt.step()
                optimizer_steps += 1
                exposures += len(batch_ids)
                total += loss.detach().double() * len(batch_ids)

            model.eval()
            validation_total = torch.zeros((), device="cuda", dtype=torch.float64)
            with torch.no_grad():
                for observations in validation.split(batch_size):
                    validation_loss = reconstruction_loss(model, observations)
                    if not bool(torch.isfinite(validation_loss)):
                        raise RuntimeError("Nonfinite validation loss")
                    validation_total += validation_loss.double() * len(observations)
            train_mse = float((total / len(train)).cpu())
            validation_mse = float((validation_total / len(validation)).cpu())

            # Raw output partition allclose is diagnostic-only.  The canary
            # raises only on hard checks and cannot affect optimization or
            # checkpoint selection.
            canary_result = canary(model, args.architecture, fixed_canary)
            if validation_mse < best_validation:
                best_validation = validation_mse
                best_epoch = epoch + 1
                torch.save({"model": cpu_state(model), "epoch": best_epoch, "validation_mse": best_validation}, data_dir / "best.pt")

            row = {
                "epoch": epoch + 1,
                "train_mse": train_mse,
                "validation_mse": validation_mse,
                "training_order_sha256": hashlib.sha256(order.tobytes()).hexdigest(),
                "optimizer_steps_this_epoch": train_steps_per_epoch,
                "train_windows": len(train),
                "validation_windows": len(validation),
                "seconds": time.perf_counter() - epoch_start,
                "canary": canary_result,
            }
            curves.append(row)
            write_json(report_dir / "curves.json", curves)
            print(json.dumps({"run": run_name, **row}), flush=True)

        if native_predict_trap.call_count:
            raise RuntimeError("Native predict_step called by scientific path")

    torch.cuda.synchronize()
    training_seconds = time.perf_counter() - training_start
    if optimizer_steps != expected_epochs * train_steps_per_epoch:
        raise RuntimeError("Unexpected optimizer step count")
    if exposures != expected_epochs * len(train):
        raise RuntimeError("Unexpected training exposure count")

    final_state = cpu_state(model)
    final_hash = model_hash(model)
    torch.save({
        "model": final_state,
        "optimizer": opt.state_dict(),
        "epoch": expected_epochs,
        "rng": {"torch": torch.get_rng_state(), "cuda": torch.cuda.get_rng_state_all(), "numpy": np.random.get_state(), "python": random.getstate()},
    }, data_dir / "final.pt")
    best_payload = torch.load(data_dir / "best.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(best_payload["model"])
    model.eval()
    best_hash = model_hash(model)
    post = parity(model, args.architecture)
    write_json(report_dir / "post_training_parity.json", post)

    recurrent_changes = {}
    for name, state in initial.items():
        if recurrent_name(name):
            best_state = best_payload["model"][name]
            recurrent_changes[name] = {
                "initial_norm": float(state.norm()),
                "best_delta_norm": float((best_state - state).norm()),
                "final_delta_norm": float((final_state[name] - state).norm()),
                "best_changed": not torch.equal(best_state, state),
            }
    artifacts = {str(path.relative_to(ROOT)): sha(path) for path in sorted(data_dir.iterdir())}
    result = {
        "status": "PASS" if post["status"] == "PASS" else "STOP_POST_TRAIN_PARITY",
        "phase_f_version": "v4",
        "architecture": args.architecture,
        "seed": args.seed,
        "implementation_commit": subprocess.check_output(["rtk", "git", "rev-parse", "HEAD"], text=True).strip(),
        "environment": environment,
        "sealed_inputs": sealed,
        "initial_model_hash": initial_hash,
        "final_model_hash": final_hash,
        "best_model_hash": best_hash,
        "artifacts": artifacts,
        "checkpoint_sha256": _checkpoint_hashes(data_dir),
        "training_order_file_sha256": orderinfo["sha256"],
        "consumed_order_sha256": order_hasher.hexdigest(),
        "optimizer_config": CONFIG["optimizer"],
        "epochs": expected_epochs,
        "optimizer_steps": optimizer_steps,
        "window_exposures": exposures,
        "parameter_count": CONFIG["parameters"][args.architecture],
        "selected_epoch": best_epoch,
        "best_validation_mse": best_validation,
        "recurrent_changes": recurrent_changes,
        "canary": {"seed": CONFIG["canary"]["seed"], "shape": CONFIG["canary"]["shape"], "input_sha256": canary_hash, "after_every_epoch": True, "fail_fast_hard_checks_only": True, "raw_output_diagnostic_only": True, "affects_optimization": False},
        "training_seconds": training_seconds,
        "total_seconds": time.perf_counter() - start,
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
        "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
        "cpu_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "native_predict_calls": native_predict_trap.call_count,
        "labels_used": False,
        "test_sources_used": False,
        "probe_fitting": False,
        "post_training_parity": post,
    }
    write_json(report_dir / "manifest.json", result)
    print(json.dumps({"run": run_name, "status": result["status"], "selected_epoch": best_epoch, "total_seconds": result["total_seconds"]}), flush=True)
    if result["status"] != "PASS":
        raise SystemExit(3)


if __name__ == "__main__":
    main()
