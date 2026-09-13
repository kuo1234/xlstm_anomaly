"""F3-R: deterministic seed-33 epoch-29 canary failure localization.

This is an implementation diagnostic only.  It replays the sealed matched-LSTM
training prefix without labels/test data, freezes the model immediately after
epoch 29, and evaluates the fixed random canary without raising on failure.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch

from phase_f_v3_common import (
    REPORT,
    CONFIG,
    build,
    canary_input,
    configure,
    load_windows,
    model_hash,
    optimizer,
    reconstruction_loss,
    seed_all,
    verify_sealed_inputs,
    write_json,
)
from phase_f_lstm_observer import Observer as LSTMObserver

ROOT = Path(__file__).resolve().parents[1]
RUN_REPORT = REPORT / "replay_seed33"
RUN_DATA = ROOT / "data" / "phase_f_v3" / "runs" / "lstm_33"
ATOL = 1e-5
RTOL = 1e-4
STAGE_NAMES = (
    "input_projection",
    "encoder0",
    "encoder1",
    "encoder2",
    "decoder0",
    "decoder1",
    "decoder2",
    "GELU",
    "output_projection",
)


def cpu_state(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}


def rng_state() -> dict[str, object]:
    return {
        "torch": torch.get_rng_state().cpu(),
        "cuda": [state.cpu() for state in torch.cuda.get_rng_state_all()],
        "numpy": np.random.get_state(),
        "python": random.getstate(),
    }


def compare(a: torch.Tensor, b: torch.Tensor, exact: bool = False) -> dict[str, object]:
    close = torch.isclose(a, b, atol=ATOL, rtol=RTOL, equal_nan=False)
    diff = (a - b).abs()
    return {
        "pass_": bool(torch.equal(a, b) if exact else torch.allclose(a, b, atol=ATOL, rtol=RTOL, equal_nan=False)),
        "bitwise": bool(torch.equal(a, b)),
        "max_abs": float(diff.max().item()) if diff.numel() else 0.0,
        "mean_abs": float(diff.mean().item()) if diff.numel() else 0.0,
        "failed_element_count": int((~close).sum().item()),
        "element_count": int(diff.numel()),
        "shape": list(a.shape),
    }


def finite_shape(a: torch.Tensor, shape: list[int]) -> dict[str, object]:
    return {
        "pass_": list(a.shape) == shape and bool(torch.isfinite(a).all()),
        "shape": list(a.shape),
        "expected_shape": shape,
        "finite": bool(torch.isfinite(a).all()),
    }


def stage_modules(model: torch.nn.Module) -> dict[str, torch.nn.Module]:
    return {
        "input_projection": model.input_projection,
        "encoder0": model.encoder[0],
        "encoder1": model.encoder[1],
        "encoder2": model.encoder[2],
        "decoder0": model.decoder[0],
        "decoder1": model.decoder[1],
        "decoder2": model.decoder[2],
        "GELU": model.gelu,
        "output_projection": model.output_projection,
    }


def forward_with_stages(model: torch.nn.Module, x: torch.Tensor, partition: bool = False):
    """Return output and every requested stage, concatenating B1 partitions."""
    modules = stage_modules(model)
    captured: dict[str, list[torch.Tensor]] = {name: [] for name in STAGE_NAMES}
    handles = []

    def make_hook(name):
        def hook(_module, _args, output):
            value = output[0] if isinstance(output, tuple) else output
            captured[name].append(value.detach().clone())

        return hook

    for name, module in modules.items():
        handles.append(module.register_forward_hook(make_hook(name)))
    try:
        with torch.no_grad():
            if partition:
                outputs = [model(part) for part in x.split(1)]
                output = torch.cat(outputs, dim=0)
            else:
                output = model(x)
    finally:
        for handle in handles:
            handle.remove()
    stages = {}
    for name in STAGE_NAMES:
        values = captured[name]
        if len(values) == 1:
            stages[name] = values[0]
        else:
            stages[name] = torch.cat(values, dim=0)
    return output.detach(), stages


def reference_summary(checks: list[dict]) -> dict[str, object]:
    """Compact six-layer manual/native h/c/i/f summary."""
    by_layer = {}
    for row in checks:
        layer = row["layer"]
        by_layer[layer] = row["checks"]
    return {
        "layers": by_layer,
        "all_pass": all(
            all(value if isinstance(value, bool) else value["pass_"] for value in row["checks"].values())
            for row in checks
        ),
        "layer_count": len(by_layer),
    }


def aggregate_reference(rows: list[dict]) -> dict[str, object]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["layer"], []).append(row["checks"])
    result = {}
    for layer, checks in grouped.items():
        layer_out = {}
        for key in ("sequence_h", "final_h", "final_c"):
            values = [item[key] for item in checks]
            layer_out[key] = {
                "pass_": all(item["pass_"] for item in values),
                "failed_call_count": sum(not item["pass_"] for item in values),
                "max_abs": max(item["max_abs"] for item in values),
            }
        layer_out["finite"] = all(item["finite"] for item in checks)
        layer_out["gate_range"] = all(item["gate_range"] for item in checks)
        layer_out["call_count"] = len(checks)
        result[layer] = layer_out
    return {
        "layers": result,
        "all_pass": all(
            value["pass_"]
            for layer in result.values()
            for key, value in layer.items()
            if key in ("sequence_h", "final_h", "final_c")
        )
        and all(layer["finite"] and layer["gate_range"] for layer in result.values()),
        "layer_count": len(result),
        "call_count": len(rows),
    }


def observer_forward(model: torch.nn.Module, x: torch.Tensor):
    with torch.no_grad(), LSTMObserver(model) as observer:
        output = model(x)
        features = observer.summary()
        checks = copy.deepcopy(observer.checks)
    return output.detach(), features.detach(), checks


def canary_no_raise(model: torch.nn.Module, x: torch.Tensor, include_stages: bool = False) -> dict[str, object]:
    model.eval()
    with torch.no_grad():
        full_output, full_stages = forward_with_stages(model, x, partition=False)
        partition_output, partition_stages = forward_with_stages(model, x, partition=True)
        full_output_obs, full_features, full_checks = observer_forward(model, x)
        partition_features_parts = []
        partition_checks = []
        for part in x.split(1):
            _output, features, checks = observer_forward(model, part)
            partition_features_parts.append(features)
            partition_checks.extend(checks)
        partition_features = torch.cat(partition_features_parts, dim=0)

    full_score = (full_output - x).square().mean((1, 2))
    partition_score = (partition_output - x).square().mean((1, 2))
    # The observer must not alter detector output; keep this explicit even
    # though observer_forward has already run the same model call.
    observer_output = compare(full_output, full_output_obs, exact=True)
    checks = {
        "raw_output": compare(full_output, partition_output),
        "reconstruction_score": compare(full_score, partition_score),
        "common18": compare(full_features, partition_features),
        "full_shape_finite": finite_shape(full_output, [len(x), 64, 8]),
        "partition_shape_finite": {
            "pass_": bool(torch.isfinite(partition_output).all()) and bool(torch.isfinite(partition_features).all()),
            "output_finite": bool(torch.isfinite(partition_output).all()),
            "features_finite": bool(torch.isfinite(partition_features).all()),
        },
        "observer_reference": {
            "pass_": bool(reference_summary(full_checks)["all_pass"] and aggregate_reference(partition_checks)["all_pass"]),
            "full": reference_summary(full_checks),
            "partition": aggregate_reference(partition_checks),
        },
    }
    result = {
        "pass_": all(
            value["pass_"] for key, value in checks.items() if key != "observer_reference"
        )
        and checks["observer_reference"]["pass_"],
        "checks": checks,
        "observer_output_bitwise": observer_output,
        "batch_size": len(x),
        "partition_batch_size": 1,
        "seed": 710,
        "labels_used": False,
        "test_sources_used": False,
        "probe_fitting": False,
        "affects_optimization": False,
    }
    if include_stages:
        result["stage_localization"] = {
            name: compare(full_stages[name], partition_stages[name]) for name in STAGE_NAMES
        }
    return result


def observer_extra_checks(model: torch.nn.Module, x: torch.Tensor) -> dict[str, object]:
    model.eval()
    small = x[:4]
    with torch.no_grad():
        off = model(small)
        rng_before = torch.cuda.get_rng_state().clone()
        with LSTMObserver(model) as observer:
            on = model(small)
            features = observer.summary()
            checks = copy.deepcopy(observer.checks)
        rng_after = torch.cuda.get_rng_state().clone()
        with LSTMObserver(model) as first:
            first_output = model(small)
            first_features = first.summary()
        with LSTMObserver(model) as changed:
            changed_input = small.clone()
            changed_input[:, 32:] = torch.randn(4, 32, 8, device="cuda")
            changed_output = model(changed_input)
            changed_states = copy.deepcopy(changed.latest)
        with LSTMObserver(model) as shorter:
            shorter_output = model(small[:, :32])
            shorter_features = shorter.summary()
    return {
        "observer_on_off": {
            "output_bitwise": compare(on, off, exact=True),
            "score_bitwise": compare((on - small).square().mean((1, 2)), (off - small).square().mean((1, 2)), exact=True),
            "rng_unchanged": bool(torch.equal(rng_before, rng_after)),
            "reference": reference_summary(checks),
        },
        "reset": {
            "output_bitwise": compare(first_output, off, exact=True),
            "features_bitwise": compare(first_features, features, exact=True),
        },
        "prefix_causality": {
            "output": compare(changed_output[:, :32], first_output[:, :32]),
            "states": {
                name: {
                    key: bool(torch.equal(first.latest[name][key][:, :32], changed_states[name][key][:, :32]))
                    for key in first.latest[name]
                }
                for name in first.latest
            },
            "pass_": all(
                torch.equal(first.latest[name][key][:, :32], changed_states[name][key][:, :32])
                for name in first.latest
                for key in first.latest[name]
            )
            and compare(changed_output[:, :32], first_output[:, :32])["pass_"],
        },
        "short_prefix": {
            "output": compare(shorter_output, off[:, :32]),
            "feature_shape": list(shorter_features.shape),
            "features_finite": bool(torch.isfinite(shorter_features).all()),
        },
    }


def compare_replay_row(row: dict, sealed: dict) -> dict[str, object]:
    scalar = {
        "train_mse": {
            "replay": row["train_mse"],
            "sealed": sealed["train_mse"],
            "abs_diff": abs(row["train_mse"] - sealed["train_mse"]),
            "match": math.isclose(row["train_mse"], sealed["train_mse"], rel_tol=0.0, abs_tol=1e-12),
        },
        "validation_mse": {
            "replay": row["validation_mse"],
            "sealed": sealed["validation_mse"],
            "abs_diff": abs(row["validation_mse"] - sealed["validation_mse"]),
            "match": math.isclose(row["validation_mse"], sealed["validation_mse"], rel_tol=0.0, abs_tol=1e-12),
        },
        "training_order_sha256": {
            "replay": row["training_order_sha256"],
            "sealed": sealed["training_order_sha256"],
            "match": row["training_order_sha256"] == sealed["training_order_sha256"],
        },
    }
    replay_canary = row["canary"]
    sealed_canary = sealed["canary"]
    canary = {
        "pass_flag_match": replay_canary["pass_"] == sealed_canary["pass_"],
        "labels_used_match": replay_canary["labels_used"] == sealed_canary["labels_used"],
        "affects_optimization_match": replay_canary["affects_optimization"] == sealed_canary["affects_optimization"],
        "checks": {},
    }
    for key in sealed_canary["checks"]:
        left = replay_canary["checks"].get(key, {})
        right = sealed_canary["checks"][key]
        entry = {"pass_flag_match": left.get("pass_") == right.get("pass_")}
        if "max_abs" in right:
            entry.update(
                replay=left.get("max_abs"),
                sealed=right.get("max_abs"),
                abs_diff=abs(left.get("max_abs", float("nan")) - right["max_abs"]),
                max_abs_match=math.isclose(left.get("max_abs", float("nan")), right["max_abs"], rel_tol=0.0, abs_tol=1e-12),
            )
        if "shape" in right:
            entry["shape_match"] = left.get("shape") == right["shape"]
        canary["checks"][key] = entry
    return {
        "epoch": row["epoch"],
        "scalar": scalar,
        "canary": canary,
        "match": all(
            value.get("match", value.get("pass_flag_match", False))
            for value in scalar.values()
        )
        and canary["pass_flag_match"]
        and canary["labels_used_match"]
        and canary["affects_optimization_match"]
        and all(
            item["pass_flag_match"]
            and item.get("max_abs_match", True)
            and item.get("shape_match", True)
            for item in canary["checks"].values()
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=33)
    args = parser.parse_args()
    if args.seed != 33:
        raise SystemExit("F3-R is frozen to detector seed 33")
    started = time.perf_counter()
    environment = configure()
    sealed_inputs = verify_sealed_inputs()
    if CONFIG["detector_seeds"] != [11, 22, 33, 44, 55]:
        raise RuntimeError("Unexpected detector seed set")
    sealed_curves = json.loads((REPORT / "runs" / "lstm_33" / "curves.json").read_text())
    if len(sealed_curves) != 28:
        raise RuntimeError(f"Expected sealed epochs 1..28, found {len(sealed_curves)}")
    orders_info = sealed_inputs["orders"]["33"]
    orders = np.load(ROOT / orders_info["path"], allow_pickle=False)
    if orders.shape != (50, 40330):
        raise RuntimeError(f"Unexpected order shape {orders.shape}")
    for epoch, order in enumerate(orders):
        digest = hashlib.sha256(order.tobytes()).hexdigest()
        if digest != orders_info["epoch_sha256"][epoch] or not np.array_equal(np.sort(order), np.arange(40330)):
            raise RuntimeError(f"Order seal failed at epoch {epoch + 1}")

    seed_all(33)
    model = build("lstm", 33)
    opt = optimizer(model)
    train = load_windows("train")
    validation = load_windows("validation")
    fixed_canary = canary_input()
    order_hasher = hashlib.sha256()
    replay_rows = []
    diag = None
    for epoch in range(29):
        model.train()
        total = torch.zeros((), device="cuda", dtype=torch.float64)
        order = orders[epoch]
        order_hasher.update(order.tobytes())
        ids = torch.from_numpy(order.copy()).cuda()
        steps = 0
        for batch_ids in ids.split(128):
            observations = train[batch_ids]
            opt.zero_grad(set_to_none=True)
            loss = reconstruction_loss(model, observations)
            if not bool(torch.isfinite(loss)):
                raise RuntimeError(f"Nonfinite loss at epoch {epoch + 1}")
            loss.backward()
            if not all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in model.parameters()):
                raise RuntimeError(f"Nonfinite gradient at epoch {epoch + 1}")
            opt.step()
            total += loss.detach().double() * len(batch_ids)
            steps += 1
        model.eval()
        val_total = torch.zeros((), device="cuda", dtype=torch.float64)
        with torch.no_grad():
            for observations in validation.split(128):
                value = reconstruction_loss(model, observations)
                if not bool(torch.isfinite(value)):
                    raise RuntimeError(f"Nonfinite validation loss at epoch {epoch + 1}")
                val_total += value.double() * len(observations)
        row = {
            "epoch": epoch + 1,
            "train_mse": float(total / len(train)),
            "validation_mse": float(val_total / len(validation)),
            "training_order_sha256": hashlib.sha256(order.tobytes()).hexdigest(),
            "optimizer_steps_this_epoch": steps,
        }
        if epoch < 28:
            row["canary"] = canary_no_raise(model, fixed_canary)
            row["sealed_fidelity"] = compare_replay_row(row, sealed_curves[epoch])
        else:
            diagnostic_path = RUN_DATA / "epoch29_replay_diagnostic.pt"
            payload = {
                "epoch": 29,
                "model": cpu_state(model),
                "model_hash": model_hash(model),
                "backend": environment,
                "config_sha256": environment["config_sha256"],
                "training_order_sha256_through_epoch29": order_hasher.hexdigest(),
                "labels_used": False,
                "test_sources_used": False,
            }
            diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(payload, diagnostic_path)
            diag = {
                "path": str(diagnostic_path.relative_to(ROOT)),
                "sha256": hashlib.sha256(diagnostic_path.read_bytes()).hexdigest(),
                "model_hash": payload["model_hash"],
                "epoch": 29,
                "state_frozen_before_canary": True,
            }
            # Freeze the post-update state before invoking the epoch-29
            # canary, matching the requested diagnostic ordering.
            row["canary"] = canary_no_raise(model, fixed_canary, include_stages=True)
            row["observer_extras"] = observer_extra_checks(model, fixed_canary)
        replay_rows.append(row)

    result = {
        "status": "PASS_DIAGNOSTIC_CAPTURE" if diag else "STOP_NO_CAPTURE",
        "diagnostic_only": True,
        "seed": 33,
        "epoch29_state": diag,
        "environment": environment,
        "sealed_inputs": sealed_inputs,
        "replay_fidelity": {
            "epochs_checked": 28,
            "all_match": all(row["sealed_fidelity"]["match"] for row in replay_rows[:28]),
            "rows": [row["sealed_fidelity"] for row in replay_rows[:28]],
        },
        "epoch29": replay_rows[28],
        "run_seconds": time.perf_counter() - started,
        "labels_used": False,
        "test_sources_used": False,
        "probe_fitting": False,
        "phase_g_started": False,
        "quarantined_scientific_evidence": True,
    }
    RUN_REPORT.mkdir(parents=True, exist_ok=True)
    write_json(RUN_REPORT / "replay_result.json", result)
    write_json(
        RUN_REPORT / "replay_code.json",
        {
            "script": str(Path(__file__).relative_to(ROOT)),
            "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "frozen_atol": ATOL,
            "frozen_rtol": RTOL,
            "upstream_commit": CONFIG["upstream_commit"],
            "backend": CONFIG["backend"],
            "architecture": "MatchedLSTM H38; scoped cuDNN disabled",
        },
    )
    print(json.dumps({"status": result["status"], "replay_all_match": result["replay_fidelity"]["all_match"], "run_seconds": result["run_seconds"]}))


if __name__ == "__main__":
    main()
