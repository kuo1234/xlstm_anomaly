"""Metric-free V0/optimized observer benchmark on the Spark CUDA overlay.

The benchmark uses fresh random weights and observations only.  It never
loads scientific checkpoints, labels, or Phase-G artifacts.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import torch


HERE = Path(__file__).resolve()
WORKTREE = HERE.parents[2]
PROJECT_ROOT = WORKTREE.parents[1]
SCRIPTS = WORKTREE / "scripts"
CUDA_UTIL = PROJECT_ROOT / ".worktrees" / "cuda-spark" / "research" / "cuda_spark"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(CUDA_UTIL))

from phase_e2_fast_observer import extract_fast  # noqa: E402
from phase_e2_observer import extract as extract_v0  # noqa: E402
from xlstmad_cuda_bench import build_model  # noqa: E402


def _timed(fn, repeats: int) -> list[float]:
    values = []
    for _ in range(repeats):
        torch.cuda.synchronize()
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        fn()
        end.record()
        end.synchronize()
        values.append(start.elapsed_time(end) / 1000.0)
    return values


def _summary(values: list[float], batch: int) -> dict:
    values = sorted(values)
    mean = sum(values) / len(values)
    return {
        "n": len(values),
        "mean_s": mean,
        "median_s": values[len(values) // 2],
        "min_s": values[0],
        "max_s": values[-1],
        "decisions_per_s": batch / mean,
    }


def _diff(a: torch.Tensor, b: torch.Tensor, atol: float = 1e-5, rtol: float = 1e-4) -> dict:
    d = (a.detach().float() - b.detach().float()).abs()
    return {
        "shape": list(a.shape),
        "max_abs": float(d.max()),
        "mean_abs": float(d.mean()),
        "failed_elements": int((d > (atol + rtol * b.detach().float().abs())).sum()),
        "allclose": bool(torch.allclose(a, b, atol=atol, rtol=rtol)),
        "finite_a": bool(torch.isfinite(a).all()),
        "finite_b": bool(torch.isfinite(b).all()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extension-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--batches", type=int, nargs="+", default=[128, 256, 512])
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    torch.set_float32_matmul_precision("highest")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    rows = []
    correctness = {}

    for batch in args.batches:
        torch.manual_seed(710 + batch)
        torch.cuda.manual_seed_all(710 + batch)
        model = build_model("cuda", seed=710 + batch, extension_dir=args.extension_dir).eval()
        x = torch.randn(batch, 64, 8, device="cuda", dtype=torch.float32)
        with torch.no_grad():
            for _ in range(args.warmup):
                extract_v0(model, x)
                extract_fast(model, x)
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        with torch.no_grad():
            v0_score, v0_features = extract_v0(model, x)
            fast_score, fast_features = extract_fast(model, x)
        correctness[str(batch)] = {
            "score": _diff(v0_score, fast_score),
            "common18": _diff(v0_features, fast_features),
        }
        for name, fn in (("v0_current_observer", lambda: extract_v0(model, x)), ("optimized_state_capture", lambda: extract_fast(model, x))):
            with torch.no_grad():
                times = _timed(fn, args.repeats)
            row = _summary(times, batch)
            row.update({
                "batch": batch,
                "observer": name,
                "warmup": args.warmup,
                "peak_memory_bytes": torch.cuda.max_memory_allocated(),
            })
            rows.append(row)
        del model, x
        torch.cuda.empty_cache()

    result = {
        "environment": {
            "torch": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "device": torch.cuda.get_device_name(0),
            "capability": torch.cuda.get_device_capability(0),
            "float32_matmul_precision": torch.get_float32_matmul_precision(),
            "cuda_matmul_tf32": torch.backends.cuda.matmul.allow_tf32,
            "cudnn_tf32": torch.backends.cudnn.allow_tf32,
        },
        "config": {"window": 64, "feature_dim": 8, "embedding": 40, "repeats": args.repeats},
        "timing": rows,
        "correctness": correctness,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
