"""Feature-level V0/FastObserver canary on the sealed Phase-F xLSTM checkpoint.

This is an engineering canary only.  It never computes labels or anomaly
metrics.  The fixture is selected deterministically from observation arrays;
the observer APIs receive only ``[B,W,D]`` tensors.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[2]
CUDA_ROOT = Path(
    os.environ.get("CUDA_WORKTREE", str(ROOT.parent / "cuda-spark"))
).resolve()
DATA_ROOT = Path(
    os.environ.get("XLSTM_DATA_ROOT", str(ROOT.parent.parent / "xlstm_anomaly"))
).resolve()
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(CUDA_ROOT / "research" / "cuda_spark"))

from phase_e2_fast_observer import FastStateObserver  # noqa: E402
from phase_e2_observer import Observer  # noqa: E402
from phase_f_common import build as build_vanilla  # noqa: E402
from phase_e2_common import model_hash, sha  # noqa: E402
from xlstmad_cuda_bench import (  # noqa: E402
    _load_vanilla_weights_into_cuda,
    build_model,
)


ATOL = 1e-5
RTOL = 1e-4
WINDOW = 64
DIMENSION = 8
CHECKPOINT = ROOT / "data" / "phase_f_v4" / "runs" / "xlstm_11" / "best.pt"
EXTENSION_DIR = Path(
    os.environ.get("TORCH_EXTENSIONS_DIR", "/tmp/xlstm_cuda_full121_false")
)


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _diff(left: torch.Tensor, right: torch.Tensor) -> dict:
    if tuple(left.shape) != tuple(right.shape):
        return {
            "shape_left": list(left.shape),
            "shape_right": list(right.shape),
            "shape_equal": False,
            "finite_left": bool(torch.isfinite(left).all()),
            "finite_right": bool(torch.isfinite(right).all()),
            "allclose": False,
            "max_abs": None,
            "mean_abs": None,
            "failed_elements": None,
            "elements": int(left.numel()),
        }
    delta = (left.detach().float() - right.detach().float()).abs()
    close = torch.isclose(left, right, atol=ATOL, rtol=RTOL)
    return {
        "shape_left": list(left.shape),
        "shape_right": list(right.shape),
        "shape_equal": True,
        "finite_left": bool(torch.isfinite(left).all()),
        "finite_right": bool(torch.isfinite(right).all()),
        "allclose": bool(close.all()),
        "max_abs": float(delta.max()) if delta.numel() else 0.0,
        "mean_abs": float(delta.mean()) if delta.numel() else 0.0,
        "failed_elements": int((~close).sum()),
        "elements": int(delta.numel()),
    }


def _capture_v0(model: torch.nn.Module, x: torch.Tensor):
    with torch.no_grad(), Observer(model) as observer:
        output = model(x)
        score = (output - x).square().mean((1, 2))
        traces = {
            cell: {name: value.detach().clone() for name, value in layer.items()}
            for cell, layer in observer.latest.items()
        }
        common18 = observer.summary().detach().clone()
    if not all(
        check["hidden_close"]
        and check["state_close"]
        and check["finite"]
        and check["all_float32"]
        for check in observer.checks
    ):
        raise RuntimeError("V0 observer's native/reference parity failed")
    return output.detach().clone(), score.detach().clone(), traces, common18


def _capture_fast(model: torch.nn.Module, x: torch.Tensor):
    with torch.no_grad(), FastStateObserver(model) as observer:
        output = model(x)
        score = (output - x).square().mean((1, 2))
        traces = {
            cell: {name: value.detach().clone() for name, value in layer.items()}
            for cell, layer in observer.latest.items()
        }
        common18 = observer.summary().detach().clone()
    return output.detach().clone(), score.detach().clone(), traces, common18


def _fit_prefix_scaled(stream_observations: np.ndarray) -> np.ndarray:
    """Apply the sealed Phase-F fit-prefix transform without truth access."""
    if stream_observations.shape[1] != DIMENSION or len(stream_observations) < 4096:
        raise ValueError("unexpected synthetic observation shape")
    fit = stream_observations[:4096].astype(np.float64, copy=False)
    mean = fit.mean(axis=0)
    std = fit.std(axis=0, ddof=0)
    scale = np.where(std == 0.0, 1.0, std)
    return ((stream_observations.astype(np.float64) - mean) / scale).astype(np.float32)


def _fixture_windows() -> tuple[torch.Tensor, list[dict]]:
    """Build a fixed observation-only fixture; labels never leave the generator."""
    from m0.synthetic import generate

    # These source/scenario/condition/end tuples are fixed before execution.
    # Conditions named ``mixture`` are only used to include representative
    # anomaly-containing observations; no labels are read or passed onward.
    selections = [
        (3000, "stationary", "none", 4000),
        (3000, "abrupt", "none", 5500),
        (3001, "gradual", "none", 6500),
        (3001, "recurring", "none", 9500),
        (3002, "correlation", "none", 5500),
        (3002, "abrupt", "mixture", 5640),
    ]
    windows: list[np.ndarray] = []
    metadata: list[dict] = []
    for source, scenario, condition, endpoint in selections:
        stream = generate(source, scenario, condition)
        observations = _fit_prefix_scaled(np.asarray(stream.observations))
        if endpoint < WINDOW - 1 or endpoint >= len(observations):
            raise ValueError("fixture endpoint outside stream")
        # Twenty fixed endpoints per stream gives 120 rows; the first eight
        # are repeated only as the deterministic B=128 completion below.
        endpoints = [endpoint + 3 * i for i in range(20)]
        if max(endpoints) >= len(observations):
            raise ValueError("fixture endpoint range outside stream")
        for t in endpoints:
            windows.append(observations[t - WINDOW + 1 : t + 1])
            metadata.append(
                {
                    "source": source,
                    "scenario": scenario,
                    "condition": condition,
                    "endpoint": t,
                }
            )
        # Drop the stream object before the extractor is called; only arrays
        # selected above are retained and no evaluator field is consulted.
        del stream
    while len(windows) < 128:
        windows.append(windows[len(windows) % 120].copy())
        metadata.append(dict(metadata[len(metadata) % 120], repeated_for_batch_128=True))
    array = np.stack(windows[:128]).astype(np.float32, copy=False)
    if array.shape != (128, WINDOW, DIMENSION) or not np.isfinite(array).all():
        raise AssertionError("invalid observation-only fixture")
    return torch.from_numpy(array).cuda(), metadata[:128]


def run(output: Path) -> dict:
    torch.set_float32_matmul_precision("highest")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the FastObserver canary")
    if not CHECKPOINT.exists():
        raise FileNotFoundError(CHECKPOINT)
    payload = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
    state = payload["model"]
    vanilla = build_vanilla("xlstm", 11).eval()
    vanilla.load_state_dict(state, strict=True)
    if model_hash(vanilla) != "49cf7982872c53280d315fb529133aaca3ac34609d9a34c7382bccbed0773f15":
        raise RuntimeError("sealed seed-11 model hash mismatch")
    cuda = build_model("cuda", seed=711, extension_dir=EXTENSION_DIR).eval()
    _load_vanilla_weights_into_cuda(vanilla, cuda)
    observations, fixture = _fixture_windows()

    rows = []
    for batch in (1, 8, 128):
        x = observations[:batch]
        v_output, v_score, v_trace, v_features = _capture_v0(cuda, x)
        f_output, f_score, f_trace, f_features = _capture_fast(cuda, x)
        row = {
            "batch": batch,
            "output": _diff(v_output, f_output),
            "score": _diff(v_score, f_score),
            "common18": _diff(v_features, f_features),
            "traces": {},
        }
        for cell in sorted(v_trace):
            row["traces"][cell] = {
                family: _diff(v_trace[cell][family], f_trace[cell][family])
                for family in ("hidden", "input", "retention", "memory")
            }
        row["pass"] = all(
            item["allclose"]
            for item in [row["output"], row["score"], row["common18"]]
            + [v for cell in row["traces"].values() for v in cell.values()]
        )
        rows.append(row)

    result = {
        "status": "PASS" if all(row["pass"] for row in rows) else "FAIL",
        "checkpoint": {
            "path": str(CHECKPOINT),
            "sha256": sha(CHECKPOINT),
            "expected_sha256": "4729a3ba385b285078aa987fce176e61fd382715c5357fc92f2635a929a0ae41",
            "model_hash": model_hash(vanilla),
            "selected_epoch": int(payload["epoch"]),
        },
        "backend": {
            "device": torch.cuda.get_device_name(),
            "capability": list(torch.cuda.get_device_capability()),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "extension_dir": str(EXTENSION_DIR),
            "observer": "CUDA V0 Observer vs FastStateObserver",
        },
        "fixture": {
            "shape": [128, WINDOW, DIMENSION],
            "selection_sha256": _digest(json.dumps(fixture, sort_keys=True).encode()),
            "selection": fixture,
            "labels_passed_to_extractor": False,
            "scaler": "per-stream observations[:4096], Phase-F population mean/std semantics",
        },
        "tolerance": {"atol": ATOL, "rtol": RTOL},
        "batches": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps({"status": result["status"], "output": str(args.output)}, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
