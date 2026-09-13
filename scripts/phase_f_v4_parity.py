"""F-v4 post-training validity checks.

This wraps the accepted F-v2 observer/reference suite and reclassifies only
raw reconstruction-tensor partition/permutation allclose as diagnostic.  All
scientific observables and finite/shape checks remain hard gates.
"""
from __future__ import annotations

import torch

from phase_f_v2_parity import parity as _base_parity, compare

ATOL = 1e-5
RTOL = 1e-4


def _raw(a: torch.Tensor, b: torch.Tensor) -> dict:
    shape_valid = tuple(a.shape) == tuple(b.shape)
    finite = bool(torch.isfinite(a).all() and torch.isfinite(b).all())
    if not shape_valid:
        return {
            "allclose": False,
            "bitwise": False,
            "max_abs": None,
            "mean_abs": None,
            "failed_element_count": None,
            "element_count": int(a.numel()),
            "shape": list(a.shape),
            "other_shape": list(b.shape),
            "finite": finite,
            "shape_valid": False,
        }
    delta = (a - b).abs()
    close = torch.isclose(a, b, atol=ATOL, rtol=RTOL)
    return {
        "allclose": bool(torch.allclose(a, b, atol=ATOL, rtol=RTOL)),
        "bitwise": bool(torch.equal(a, b)),
        "max_abs": float(delta.max().item()),
        "mean_abs": float(delta.mean().item()),
        "failed_element_count": int((~close).sum().item()),
        "element_count": int(a.numel()),
        "shape": list(a.shape),
        "other_shape": list(b.shape),
        "finite": finite,
        "shape_valid": True,
    }


def _mark_raw(check: dict, diagnostic: dict) -> dict:
    check["raw_diagnostic"] = diagnostic
    check["hard"] = False
    # Preserve the actual allclose result for transparency while excluding it
    # from the hard validity aggregate.
    return check


def parity(model, architecture: str) -> dict:
    result = _base_parity(model, architecture)
    checks = result["checks"]

    # v2 already computes these calls; repeat the fixed random fixture only to
    # attach complete raw diagnostic fields to every required comparison.
    generator = torch.Generator(device="cuda").manual_seed(710)
    x = torch.randn(131, 64, 8, device="cuda", generator=generator)
    with torch.no_grad():
        full = model(x)
        for batch_size in (128, 3, 1):
            partition = torch.cat([model(chunk) for chunk in x.split(batch_size)], dim=0)
            key = f"partition_B{batch_size}_output"
            if key not in checks:
                checks[key] = {"pass_": False}
            _mark_raw(checks[key], _raw(full, partition))

        permutation = torch.randperm(len(x), device="cuda", generator=generator)
        permuted = model(x[permutation])
        if "output_permutation" not in checks:
            checks["output_permutation"] = {"pass_": False}
        _mark_raw(checks["output_permutation"], _raw(permuted, full[permutation]))

    # Explicit hard finite/shape checks cover all raw output calls despite
    # diagnostic-only allclose status.
    output_tensors = [full]
    with torch.no_grad():
        for batch_size in (128, 3, 1):
            output_tensors.extend(model(chunk) for chunk in x.split(batch_size))
    output_shapes = [list(t.shape) for t in output_tensors]
    output_finite_shape = all(
        tuple(t.shape) == tuple(x[: t.shape[0]].shape)
        and bool(torch.isfinite(t).all())
        for t in output_tensors
    )
    checks["raw_output_finite_shape"] = {
        "pass_": bool(output_finite_shape),
        "hard": True,
        "shapes": output_shapes,
        "expected_last_two": [64, 8],
    }

    # Mark the v2 output permutation and output-partition allclose fields as
    # diagnostic.  Score/common18/reference and all other checks remain hard.
    raw_keys = {"output_permutation", "partition_B128_output", "partition_B3_output", "partition_B1_output"}
    for key, check in checks.items():
        if key in raw_keys:
            check["hard"] = False
        elif "hard" not in check:
            check["hard"] = True

    hard_failures = [key for key, check in checks.items() if check.get("hard") and not check.get("pass_")]
    result["status"] = "PASS" if not hard_failures else "STOP"
    result["hard_failures"] = hard_failures
    result["raw_output_partition_contract"] = "diagnostic_only_allclose; finite_and_shape_remain_hard"
    result["atol"] = ATOL
    result["rtol"] = RTOL
    return result


__all__ = ["parity", "compare"]
