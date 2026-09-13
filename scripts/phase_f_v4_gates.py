"""F-v4 pre-training mechanical gates.

No optimizer step is executed here.  The gate uses only sealed clean training
prefix windows and a fixed random unlabeled canary; labels and test sources are
unreachable.
"""
from __future__ import annotations

import json
import resource
import time

import numpy as np
import torch

from phase_e2_schema import SCALAR_CELLS, summarize as x_summary
from phase_f_lstm_observer import BASE_COLUMNS, EXPANDED_COLUMNS, LAYERS, expand_history as l_expand_history, summarize as l_summary
from phase_f_v4_common import *
from phase_f_v4_parity import parity
from phase_f_v4_canary import canary


def _json_copy(value):
    """Convert optimizer tuples/tensors into JSON-safe structures."""
    if isinstance(value, dict):
        return {str(k): _json_copy(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_copy(v) for v in value]
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def main() -> None:
    start = time.perf_counter()
    environment = configure()
    sealed = verify_sealed_inputs()
    diagnostic_path = ROOT / "reports/phase_f_v2/spark_cudnn_diagnostic.json"
    diagnostic = json.loads(diagnostic_path.read_text())
    if diagnostic.get("status") != "PASS" or diagnostic.get("conditions", {}).get("B", {}).get("all_required_original_gate_checks") is not True:
        raise SystemExit("Accepted Spark cuDNN-disabled diagnostic is missing; training forbidden")

    batch = load_windows("train")[:128]
    fixed_canary = canary_input()
    rows = {}
    optimizer_defaults = []

    for architecture in ("xlstm", "lstm"):
        model = build(architecture, 11).train()
        initial_hash = model_hash(model)
        opt = optimizer(model)
        optimizer_defaults.append(_json_copy(opt.defaults))
        torch.cuda.reset_peak_memory_stats()
        tick = time.perf_counter()
        with forbid_native_predict() as trap:
            loss = reconstruction_loss(model, batch)
            if not bool(torch.isfinite(loss)):
                raise RuntimeError(f"{architecture}: nonfinite forward loss")
            loss.backward()
            finite_gradients = all(
                p.grad is not None and bool(torch.isfinite(p.grad).all())
                for p in model.parameters()
            )
        torch.cuda.synchronize()
        recurrent_gradients = {
            name: float(parameter.grad.norm().item())
            for name, parameter in model.named_parameters()
            if recurrent_name(name) and parameter.grad is not None
        }
        gates = {
            "finite_loss": bool(torch.isfinite(loss)),
            "finite_gradients": finite_gradients,
            "nonzero_recurrent_gradient": any(value > 0 for value in recurrent_gradients.values()),
            "no_native_predict": trap.call_count == 0,
            "no_parameter_mutation": model_hash(model) == initial_hash,
        }
        if architecture == "lstm":
            gates["scoped_cudnn_disabled"] = model.last_cudnn_enabled is False
        else:
            gates["xLSTM_global_cudnn_enabled"] = torch.backends.cudnn.enabled is True

        rows[architecture] = {
            "gates": gates,
            "initial_model_hash": initial_hash,
            "recurrent_gradient_norms": recurrent_gradients,
            "loss": float(loss.detach().cpu()),
            "seconds_forward_backward": time.perf_counter() - tick,
            "optimizer_steps": 0,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
            "optimizer_defaults": _json_copy(opt.defaults),
            "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        }
        model.zero_grad(set_to_none=True)
        rows[architecture]["parity"] = parity(model, architecture)
        rows[architecture]["pretraining_canary"] = canary(model, architecture, fixed_canary)
        if architecture == "xlstm":
            expected = json.loads((ROOT / "reports/phase_e2/architecture.json").read_text())
            rows[architecture]["E2_seed11_initial_hash"] = initial_hash == expected["initial_model_hash"]
        del model, opt

    schema_checks = {
        "lstm_common18": l_summary({name: {key: torch.ones(2, 2, 38) for key in ("hidden", "input", "retention", "memory")} for name in LAYERS}).shape == (2, 18),
        "lstm_expanded234": l_expand_history(torch.ones(40, 18)).shape == (40, 234),
        "xLSTM_common18": x_summary({name: {key: torch.ones(2, 2, 1, 1) for key in ("hidden", "input", "retention", "memory")} for name in SCALAR_CELLS}).shape == (2, 18),
        "all_six_lstm_layers": len(LAYERS) == 6,
    }
    write_json(REPORT / "schema_binding.json", {
        "base_columns": BASE_COLUMNS,
        "expanded_columns": EXPANDED_COLUMNS,
        "layers": LAYERS,
        "mapping": {"hidden": "h_t", "input": "sigmoid(input gate)", "retention": "sigmoid(forget gate)", "memory": "c_t"},
        "width": 38,
        "pooling": "equal all six real LSTM layers; full H38 statistics",
        "rolling": "4/8/16/32",
        "labels_extracted": False,
        "unit_checks": schema_checks,
        "source_schema_sha256": sha(ROOT / "reports/phase_f/lstm_common18_schema.json"),
        "canary": {"seed": CONFIG["canary"]["seed"], "shape": CONFIG["canary"]["shape"], "after_every_epoch": True, "raw_output": "diagnostic_only"},
    })

    parity_ok = all(row["parity"]["status"] == "PASS" for row in rows.values())
    canary_ok = all(row["pretraining_canary"]["pass_"] for row in rows.values())
    gates_ok = all(all(bool(value) for value in row["gates"].values()) for row in rows.values())
    optimizer_equal = optimizer_defaults[0] == optimizer_defaults[1]
    result = {
        "status": "PASS" if gates_ok and parity_ok and canary_ok and all(schema_checks.values()) and optimizer_equal else "STOP",
        "phase_f_version": "v4",
        "backend": "F-v3 global F2 flags; scoped matched-LSTM cuDNN disabled",
        "environment": environment,
        "sealed_inputs": sealed,
        "diagnostic_reference": {"path": str(diagnostic_path.relative_to(ROOT)), "sha256": sha(diagnostic_path), "B_pass": True},
        "architectures": rows,
        "optimizer_semantics_equal": optimizer_equal,
        "schema_checks": schema_checks,
        "total_seconds": time.perf_counter() - start,
        "cpu_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "scientific_optimizer_steps": 0,
        "labels_read": False,
        "test_sources_used": False,
        "probe_fit": False,
        "raw_output_partition_contract": "diagnostic_only_allclose; finite_and_shape_hard",
    }
    write_json(REPORT / "mechanical_gates.json", result)
    print(json.dumps({"status": result["status"], "total_seconds": result["total_seconds"], "failures": {
        arch: {"gates": [key for key, value in row["gates"].items() if not value], "parity": row["parity"].get("hard_failures", []), "canary": [key for key, value in row["pretraining_canary"]["checks"].items() if value.get("hard") and not value.get("pass_")]}
        for arch, row in rows.items()
    }}, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
