"""Bounded observation-only extraction workload with cache-style writes.

The stream observations come from two fixed preregistered synthetic source
realizations, but evaluator labels/metadata are never read.  This is an
engineering workload, not a Phase-G rerun.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve()
WORKTREE = HERE.parents[2]
PROJECT_ROOT = WORKTREE.parents[1]
sys.path.insert(0, str(WORKTREE / "scripts"))
sys.path.insert(0, str(WORKTREE))
sys.path.insert(0, str(PROJECT_ROOT / ".worktrees" / "cuda-spark" / "research" / "cuda_spark"))

from m0.synthetic import generate  # noqa: E402
from phase_e2_fast_observer import extract_fast  # noqa: E402
from phase_e2_observer import extract as extract_v0  # noqa: E402
from xlstmad_cuda_bench import build_model  # noqa: E402


def make_batches(batch: int) -> list[np.ndarray]:
    batches = []
    for seed, scenario in ((3000, "abrupt"), (3001, "correlation")):
        stream = generate(seed, scenario, "mixture")
        observations = np.asarray(stream.observations, dtype=np.float64)
        fit = observations[:4096]
        scaled = ((observations - fit.mean(0)) / fit.std(0)).astype(np.float32)
        timestamps = np.arange(63, 63 + 1024, dtype=np.int64)
        windows = np.stack([scaled[t - 63 : t + 1] for t in timestamps])
        batches.extend(windows[i : i + batch] for i in range(0, len(windows), batch))
    return batches


def run_pipeline(model, batches, extractor, output_dir: Path) -> tuple[float, list[np.ndarray]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    start = time.perf_counter()
    with torch.no_grad():
        for index, array in enumerate(batches):
            x = torch.from_numpy(array).cuda(non_blocking=False)
            score, feature = extractor(model, x)
            packed = np.concatenate(
                [score.detach().cpu().numpy()[:, None], feature.detach().cpu().numpy()], axis=1
            )
            np.save(output_dir / f"chunk_{index:03d}.npy", packed, allow_pickle=False)
            outputs.append(packed)
    torch.cuda.synchronize()
    return time.perf_counter() - start, outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extension-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch", type=int, default=128)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    batches = make_batches(args.batch)
    model = build_model("cuda", seed=810, extension_dir=args.extension_dir).eval()
    # Warmup is outside the measured fixed workload.
    with torch.no_grad():
        extract_v0(model, torch.from_numpy(batches[0]).cuda())
        extract_fast(model, torch.from_numpy(batches[0]).cuda())
    torch.cuda.synchronize()
    rows = {}
    outputs = {}
    for name, extractor in (("v0_current_observer", extract_v0), ("optimized_state_capture", extract_fast)):
        out_dir = args.output.parent / f"pipeline_{name}"
        elapsed, values = run_pipeline(model, batches, extractor, out_dir)
        rows[name] = {
            "elapsed_s": elapsed,
            "batches": len(batches),
            "decisions": sum(len(value) for value in values),
            "decisions_per_s": sum(len(value) for value in values) / elapsed,
            "cache_files": len(list(out_dir.glob("chunk_*.npy"))),
        }
        outputs[name] = values
    a = np.concatenate(outputs["v0_current_observer"])
    b = np.concatenate(outputs["optimized_state_capture"])
    delta = np.abs(a.astype(np.float64) - b.astype(np.float64))
    result = {
        "workload": {
            "sources": [3000, 3001],
            "scenarios": ["abrupt", "correlation"],
            "condition": "mixture",
            "decisions_per_stream": 1024,
            "batch": args.batch,
            "labels_read": False,
            "metadata_read": False,
        },
        "timing": rows,
        "equivalence": {
            "packed_shape": list(a.shape),
            "max_abs": float(delta.max()),
            "mean_abs": float(delta.mean()),
            "failed_elements": int((delta > (1e-5 + 1e-4 * np.abs(b))).sum()),
            "allclose": bool(np.allclose(a, b, atol=1e-5, rtol=1e-4)),
        },
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
