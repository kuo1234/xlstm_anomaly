"""F-v4 epoch canary.

Raw reconstruction tensors are finite/shape hard requirements but their
batch-partition allclose is diagnostic only.  Scores, common18 features,
recurrent/reference checks and same-batch observer parity remain fail-closed.
"""
from __future__ import annotations

import torch

from phase_e2_observer import Observer as XObserver
from phase_f_lstm_observer import Observer as LObserver

ATOL = 1e-5
RTOL = 1e-4


def _diagnostic(a: torch.Tensor, b: torch.Tensor) -> dict:
    shape_valid = tuple(a.shape) == tuple(b.shape)
    finite = bool(torch.isfinite(a).all() and torch.isfinite(b).all())
    if shape_valid:
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


def _compare(a: torch.Tensor, b: torch.Tensor, *, exact: bool = False) -> dict:
    result = _diagnostic(a, b)
    result["pass_"] = bool(
        result["shape_valid"]
        and result["finite"]
        and (result["bitwise"] if exact else result["allclose"])
    )
    return result


def _reference_pass(records: list[dict], architecture: str) -> bool:
    if architecture == "xlstm":
        return all(
            bool(row.get("hidden_close"))
            and bool(row.get("state_close"))
            and bool(row.get("finite"))
            and bool(row.get("all_float32"))
            for row in records
        )
    return all(
        all(bool(v) if isinstance(v, bool) else bool(v.get("pass_")) for v in row["checks"].values())
        for row in records
    )


def _shape_finite(tensor: torch.Tensor, expected: tuple[int, ...] | None = None) -> bool:
    return bool(
        torch.isfinite(tensor).all()
        and (expected is None or tuple(tensor.shape) == expected)
    )


def canary(model, architecture: str, x: torch.Tensor) -> dict:
    """Run the fixed random-unlabeled B128/B3/B1 canary.

    The caller places this inside ``forbid_native_predict``.  No labels,
    test-source data, threshold, or optimizer operation is reachable here.
    """
    model.eval()
    observer_type = XObserver if architecture == "xlstm" else LObserver
    expected_output_shape = tuple(x.shape)
    expected_feature_shape = (len(x), 18)

    with torch.no_grad():
        # Same-batch observer OFF/ON is a hard, bitwise contract.
        bare = model(x)
        with observer_type(model) as off_observer:
            observed = model(x)
            observed_features = off_observer.summary()

        # Full B128 call and its internal reference traces.
        with observer_type(model) as full_observer:
            full = model(x)
            full_features = full_observer.summary()
            full_reference = list(full_observer.checks)

        outputs_b1, features_b1, refs_b1 = [], [], []
        for part in x.split(1):
            with observer_type(model) as observer:
                outputs_b1.append(model(part))
                features_b1.append(observer.summary())
                refs_b1.extend(observer.checks)
        b1 = torch.cat(outputs_b1, dim=0)
        f1 = torch.cat(features_b1, dim=0)

        outputs_b3, features_b3, refs_b3 = [], [], []
        for part in x.split(3):
            with observer_type(model) as observer:
                outputs_b3.append(model(part))
                features_b3.append(observer.summary())
                refs_b3.extend(observer.checks)
        b3 = torch.cat(outputs_b3, dim=0)
        f3 = torch.cat(features_b3, dim=0)

    full_score = (full - x).square().mean((1, 2))
    b1_score = (b1 - x).square().mean((1, 2))
    b3_score = (b3 - x).square().mean((1, 2))
    bare_score = (bare - x).square().mean((1, 2))
    observed_score = (observed - x).square().mean((1, 2))

    finite_shape = all(
        (
            _shape_finite(value, shape)
            if shape is not None
            else _shape_finite(value)
        )
        for value, shape in (
            (bare, expected_output_shape),
            (observed, expected_output_shape),
            (full, expected_output_shape),
            (b1, expected_output_shape),
            (b3, expected_output_shape),
            (observed_features, expected_feature_shape),
            (full_features, expected_feature_shape),
            (f1, expected_feature_shape),
            (f3, expected_feature_shape),
        )
    )
    reference = _reference_pass(full_reference + refs_b1 + refs_b3, architecture)
    observer_same = bool(
        torch.equal(bare, observed)
        and torch.equal(bare_score, observed_score)
    )

    checks = {
        # Diagnostic only for raw output allclose; finite/shape is included in
        # the hard finite_shape check above.
        "raw_output_B128_vs_B1": {**_diagnostic(full, b1), "hard": False},
        "raw_output_B128_vs_B3": {**_diagnostic(full, b3), "hard": False},
        "reconstruction_score_B128_vs_B1": {**_compare(full_score, b1_score), "hard": True},
        "reconstruction_score_B128_vs_B3": {**_compare(full_score, b3_score), "hard": True},
        "common18_B128_vs_B1": {**_compare(full_features, f1), "hard": True},
        "common18_B128_vs_B3": {**_compare(full_features, f3), "hard": True},
        "finite_shape": {"pass_": finite_shape, "hard": True,
                         "output_shapes": [list(v.shape) for v in (bare, observed, full, b1, b3)],
                         "feature_shapes": [list(v.shape) for v in (observed_features, full_features, f1, f3)]},
        "observer_reference": {"pass_": reference, "hard": True},
        "observer_on_off": {"pass_": observer_same, "hard": True, "output_bitwise": torch.equal(bare, observed), "score_bitwise": torch.equal(bare_score, observed_score)},
    }
    hard_pass = all(bool(row["pass_"]) if "pass_" in row else bool(row["shape_valid"] and row["finite"]) for row in checks.values() if row.get("hard"))
    result = {
        "pass_": hard_pass,
        "checks": checks,
        "batch_size": int(len(x)),
        "partition_batch_sizes": [1, 3],
        "seed": 710,
        "labels_used": False,
        "test_sources_used": False,
        "probe_fitting": False,
        "affects_optimization": False,
        "raw_output_contract": "diagnostic_only_allclose; finite_and_shape_hard",
    }
    if not hard_pass:
        failures = [name for name, row in checks.items() if row.get("hard") and not row.get("pass_")]
        raise RuntimeError("F-v4 hard canary failed: " + ",".join(failures))
    return result


__all__ = ["canary"]
