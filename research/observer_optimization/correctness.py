"""Feature-level equivalence checks for the optimized observer.

Only fresh random CUDA fixtures are used.  The unmodified observer and its
scalar replay are the reference; no labels or scientific artifacts are read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve()
WORKTREE = HERE.parents[2]
PROJECT_ROOT = WORKTREE.parents[1]
sys.path.insert(0, str(WORKTREE / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / ".worktrees" / "cuda-spark" / "research" / "cuda_spark"))

from phase_e2_fast_observer import FastStateObserver  # noqa: E402
from phase_e2_observer import SCALAR_CELLS, scalar_reference  # noqa: E402
from phase_e2_schema import summarize  # noqa: E402
from xlstmad_cuda_bench import build_model  # noqa: E402


ATOL = 1e-5
RTOL = 1e-4


def diff(a: torch.Tensor, b: torch.Tensor) -> dict:
    delta = (a.detach().float() - b.detach().float()).abs()
    return {
        "shape": list(a.shape),
        "max_abs": float(delta.max()),
        "mean_abs": float(delta.mean()),
        "failed_elements": int((delta > ATOL + RTOL * b.detach().float().abs()).sum()),
        "allclose": bool(torch.allclose(a, b, atol=ATOL, rtol=RTOL)),
        "finite_a": bool(torch.isfinite(a).all()),
        "finite_b": bool(torch.isfinite(b).all()),
    }


def state_hash(model) -> str:
    digest = hashlib.sha256()
    for name, value in model.state_dict().items():
        digest.update(name.encode())
        digest.update(str(value.dtype).encode())
        digest.update(str(tuple(value.shape)).encode())
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def capture_inputs(model, x):
    captured = {}
    handles = []
    for name, module in model.named_modules():
        if name.endswith("slstm_cell"):
            handles.append(
                module.register_forward_pre_hook(
                    lambda _module, args, name=name: captured.__setitem__(name, args[0].detach())
                )
            )
    with torch.no_grad():
        output = model(x)
    for handle in handles:
        handle.remove()
    return output, captured


def check_fixture(model, x):
    before_hash = state_hash(model)
    output, captured = capture_inputs(model, x)
    reference = {}
    for name in SCALAR_CELLS:
        cell = dict(model.named_modules())[name]
        reference[name], _states = scalar_reference(cell, captured[name])
    with torch.no_grad(), FastStateObserver(model) as observer:
        optimized_output = model(x)
    optimized = observer.latest
    rows = {"score_output": diff(output, optimized_output), "traces": {}, "common18": None}
    for name in SCALAR_CELLS:
        rows["traces"][name] = {
            key: diff(reference[name][key], optimized[name][key])
            for key in ("hidden", "input", "retention", "memory")
        }
    rows["common18"] = diff(summarize(reference), observer.summary())
    rows["pass"] = rows["score_output"]["allclose"] and rows["common18"]["allclose"] and all(
        item["allclose"] for cell in rows["traces"].values() for item in cell.values()
    )
    rows["parameter_unchanged"] = before_hash == state_hash(model)
    rows["pass"] = rows["pass"] and rows["parameter_unchanged"]
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extension-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checks = []
    for seed, batch in ((710, 1), (711, 8), (712, 128)):
        model = build_model("cuda", seed=seed, extension_dir=args.extension_dir).eval()
        torch.manual_seed(seed + 10000)
        x = torch.randn(batch, 64, 8, device="cuda", dtype=torch.float32)
        check = check_fixture(model, x)
        check.update({"seed": seed, "batch": batch})
        checks.append(check)
        del model, x
        torch.cuda.empty_cache()
    result = {
        "tolerance": {"atol": ATOL, "rtol": RTOL},
        "fixtures": checks,
        "pass": all(row["pass"] for row in checks),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
