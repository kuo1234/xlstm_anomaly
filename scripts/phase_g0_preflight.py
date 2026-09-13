"""Phase G0 label-blind, inference-only preflight.

This script intentionally uses random observations rather than generator
streams.  It verifies the sealed detector checkpoints and the executable
common18/rolling feature contract without loading labels, event metadata,
test-result arrays, or fitting anything.  The G0 CANDI control is still
unresolved by design, so a successful backbone audit remains a fail-closed
pre-label STOP.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import phase_f_v4_common as f4
from phase_e2_observer import Observer as XObserver
from phase_f_lstm_observer import Observer as LObserver

ATOL, RTOL = 1e-5, 1e-4
ROLLING = (4, 8, 16, 32)
EXPECTED = {"history": 14, "internal_base": 18, "hidden": 52,
            "gate": 130, "memory": 52, "combined": 234,
            "history_plus_combined": 248}


def _json(path: Path):
    return json.loads(path.read_text())


def _cmp(a: torch.Tensor, b: torch.Tensor, exact: bool = False) -> dict:
    close = torch.equal(a, b) if exact else torch.allclose(a, b, atol=ATOL, rtol=RTOL)
    return {"pass_": bool(close), "bitwise": bool(torch.equal(a, b)),
            "max_abs": float((a - b).abs().max().item()),
            "shape": list(a.shape), "other_shape": list(b.shape)}


def _causal_cmp(a: torch.Tensor, b: torch.Tensor) -> dict:
    """Exact comparison that treats matching NaN warmups as equal."""
    if a.shape != b.shape:
        return {"pass_": False, "bitwise": False, "shape": list(a.shape),
                "other_shape": list(b.shape)}
    nan_a, nan_b = torch.isnan(a), torch.isnan(b)
    finite_equal = torch.equal(torch.nan_to_num(a), torch.nan_to_num(b))
    return {"pass_": bool(torch.equal(nan_a, nan_b) and finite_equal),
            "bitwise": bool(torch.equal(a, b)),
            "nan_count": int(nan_a.sum().item()), "shape": list(a.shape)}


def _rolling(rows: torch.Tensor, width: int) -> torch.Tensor:
    """Causal mean/std/slope for a T x F matrix; no future values."""
    if rows.ndim != 2 or rows.shape[0] < width:
        raise ValueError("rolling input is too short or not a matrix")
    x = rows.unfold(0, width, 1)  # (T-width+1, F, width)
    mean = x.mean(-1)
    std = x.std(-1, correction=0)
    t = torch.arange(width, device=rows.device, dtype=rows.dtype)
    t = t - t.mean()
    slope = (x * t).sum(-1) / t.square().sum()
    pad = rows.new_full((width - 1, rows.shape[1] * 3), float("nan"))
    return torch.cat((pad, torch.cat((mean, std, slope), dim=1)), dim=0)


def _expand(base: torch.Tensor) -> torch.Tensor:
    """Expand T x 18 to T x 234, preserving current-row causal semantics."""
    if base.ndim != 2 or base.shape[1] != 18:
        raise ValueError("expected T x 18 common base")
    # _rolling is arranged by feature blocks; the sealed schema is feature
    # major (base column, then mean/std/slope at each width).
    result = []
    for j in range(18):
        result.append(base[:, j:j + 1])
        for width in ROLLING:
            stats = _rolling(base[:, j:j + 1], width)
            result.append(stats)
    return torch.cat(result, dim=1)


def _history(scores: torch.Tensor) -> torch.Tensor:
    if scores.ndim != 1:
        raise ValueError("expected score vector")
    previous = torch.cat((scores.new_full((1,), float("nan")), scores[:-1]))
    first = (scores - previous).unsqueeze(1)
    result = [scores.unsqueeze(1), first]
    for width in ROLLING:
        result.append(_rolling(scores[:, None], width))
    return torch.cat(result, dim=1)


def _extract(model, architecture: str, x: torch.Tensor):
    observer = XObserver if architecture == "xlstm" else LObserver
    with f4.forbid_native_predict() as trap, torch.no_grad(), observer(model) as obs:
        output = model(x)
        features = obs.summary()
    score = (output - x).square().mean((1, 2))
    if trap.call_count:
        raise RuntimeError("scientific common path invoked native predict_step")
    return output, score, features, obs


def _outer_label_blind_extract(model, architecture: str, x: torch.Tensor,
                               evaluator_metadata: dict):
    """Model-facing extraction deliberately drops evaluator-only metadata.

    The outer harness may carry labels for a later evaluator, but this helper
    makes the boundary explicit: the actual extractor receives observations
    only.  G0 uses dummy metadata solely to test that changing it cannot alter
    the feature tensors.
    """
    del evaluator_metadata
    return _extract(model, architecture, x)


def _load_entry(entry: dict):
    path = ROOT / entry["path"]
    if not path.name == "best.pt" or not path.exists():
        raise RuntimeError(f"sealed best checkpoint unavailable: {path}")
    if f4.sha(path) != entry["sha256"]:
        raise RuntimeError(f"checkpoint file hash mismatch: {path}")
    model = f4.build(entry["architecture"], int(entry["detector_seed"]))
    payload = torch.load(path, map_location="cpu", weights_only=True)
    if set(payload) != {"model", "epoch", "validation_mse"}:
        raise RuntimeError(f"unexpected checkpoint payload: {path}")
    model.load_state_dict(payload["model"], strict=True)
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    model.eval()
    if f4.model_hash(model) != entry["model_hash"]:
        raise RuntimeError(f"model hash mismatch: {path}")
    if any(p.requires_grad for p in model.parameters()):
        raise RuntimeError("G0 model parameters must be frozen")
    return model


def _run_model(entry: dict) -> dict:
    model = _load_entry(entry)
    initial_hash = f4.model_hash(model)
    gen = torch.Generator(device="cuda").manual_seed(9011 + entry["detector_seed"])
    x = torch.randn(131, 64, 8, device="cuda", generator=gen, dtype=torch.float32)
    out, scores, base, obs = _extract(model, entry["architecture"], x)
    expected_base = (131, 18)
    checks = {
        "finite_shape": {"pass_": list(out.shape) == list(x.shape)
                         and list(base.shape) == list(expected_base)
                         and bool(torch.isfinite(out).all())
                         and bool(torch.isfinite(scores).all())
                         and bool(torch.isfinite(base).all())},
        "observer_off_on_output_score": {"pass_": True},
        "no_native_predict": {"pass_": True},
    }
    # Explicit same-batch OFF/ON check, separate from the observer extraction.
    with torch.no_grad(), f4.forbid_native_predict() as trap:
        off = model(x[:4])
        with (XObserver if entry["architecture"] == "xlstm" else LObserver)(model) as onobs:
            on = model(x[:4])
            onbase = onobs.summary()
    checks["observer_off_on_output_score"] = {
        "output": _cmp(off, on, exact=True),
        "score": _cmp((off - x[:4]).square().mean((1, 2)),
                       (on - x[:4]).square().mean((1, 2)), exact=True),
        "pass_": bool(torch.equal(off, on) and torch.equal(
            (off - x[:4]).square().mean((1, 2)), (on - x[:4]).square().mean((1, 2))))
                  and trap.call_count == 0,
    }
    # Re-run the complete stream in permuted and B3/B1 partitions.  Score and
    # common18 are hard; raw reconstruction output itself is not a G0 gate.
    permutation = torch.randperm(len(x), device="cuda", generator=gen)
    _, ps, pf, _ = _extract(model, entry["architecture"], x[permutation])
    checks["score_permutation"] = _cmp(ps, scores[permutation])
    checks["common18_permutation"] = _cmp(pf, base[permutation])
    for width in (3, 1):
        parts = [_extract(model, entry["architecture"], chunk) for chunk in x.split(width)]
        joined_score = torch.cat([p[1] for p in parts])
        joined_base = torch.cat([p[2] for p in parts])
        checks[f"score_partition_B{width}"] = _cmp(joined_score, scores)
        checks[f"common18_partition_B{width}"] = _cmp(joined_base, base)
    # Independent window reset: repeat the same call after an unrelated call.
    _, reset_score, reset_base, _ = _extract(model, entry["architecture"], x[:4])
    model(x[4:7])
    _, reset2_score, reset2_base, _ = _extract(model, entry["architecture"], x[:4])
    checks["independent_window_reset"] = {
        "score": _cmp(reset_score, reset2_score, exact=True),
        "common18": _cmp(reset_base, reset2_base, exact=True),
        "pass_": bool(torch.equal(reset_score, reset2_score) and torch.equal(reset_base, reset2_base)),
    }
    # Prefix causality is checked over the causal rolling transforms: changing
    # rows after t must not change features through t.
    base2 = base.clone()
    base2[80:] = torch.randn(base2[80:].shape, device=base2.device,
                             dtype=base2.dtype, generator=gen)
    history = _history(scores)
    # Change only observations/scores after the prefix.  The first 80 rows of
    # the history features must remain identical if the transform is causal.
    scores2 = scores.clone()
    scores2[80:] = torch.randn(scores2[80:].shape, device=scores2.device,
                               dtype=scores2.dtype, generator=gen)
    history2 = _history(scores2)
    internal = _expand(base)
    internal2 = _expand(base2)
    checks["prefix_causality"] = {
        "internal": _causal_cmp(internal[:80], internal2[:80]),
        "history": _causal_cmp(history[:80], history2[:80]),
        "pass_": bool(_causal_cmp(internal[:80], internal2[:80])["pass_"]
                      and _causal_cmp(history[:80], history2[:80])["pass_"]),
    }
    combined = torch.cat((history, internal), dim=1)
    checks["feature_schema"] = {
        "pass_": list(history.shape) == [131, 14] and list(base.shape) == [131, 18]
                  and list(internal.shape) == [131, 234] and list(combined.shape) == [131, 248]
                  and bool(torch.isfinite(combined[32:]).all()),
        "history": list(history.shape), "internal_base": list(base.shape),
        "internal_combined": list(internal.shape), "history_plus_combined": list(combined.shape),
    }
    # The extractor has observations-only input.  Running the exact same x
    # under two dummy outer-label permutations must produce identical tensors;
    # no label object is passed below or read by this script.
    dummy_a = {"semantic_label": torch.zeros(8, dtype=torch.int64)}
    dummy_b = {"semantic_label": torch.ones(8, dtype=torch.int64)}
    _, s_a, b_a, _ = _outer_label_blind_extract(
        model, entry["architecture"], x[:8], dummy_a)
    _, s_b, b_b, _ = _outer_label_blind_extract(
        model, entry["architecture"], x[:8], dummy_b)
    checks["dummy_opposite_label_invariance"] = {
        "score": _cmp(s_a, s_b, exact=True), "features": _cmp(b_a, b_b, exact=True),
        "pass_": bool(torch.equal(s_a, s_b) and torch.equal(b_a, b_b)),
        "labels_passed_to_extractor": False,
    }
    checks["common18_finite"] = {"pass_": bool(torch.isfinite(base).all())}
    checks["checkpoint_unchanged"] = {"pass_": f4.model_hash(model) == initial_hash}
    hard = [name for name, value in checks.items() if not value.get("pass_")]
    return {"run": entry["run"], "architecture": entry["architecture"],
            "detector_seed": entry["detector_seed"], "checkpoint": entry["path"],
            "status": "PASS" if not hard else "STOP", "hard_failures": hard,
            "checks": checks, "native_observer_calls": len(obs.checks),
            "output_shape": list(out.shape), "score_shape": list(scores.shape),
            "features_shape": list(base.shape), "labels_read": False,
            "test_sources_used": False, "test_metrics_computed": False,
            "optimizer_created_or_stepped": False, "parameter_mutated": False,
            "exploratory_or_labeled_features": False}


def main() -> None:
    environment = f4.configure()
    manifest = _json(ROOT / "reports/phase_g/checkpoint_manifest.json")
    schema = _json(ROOT / "reports/phase_g/schema_binding.json")
    config = _json(ROOT / "configs/phase_g.json")
    entries = manifest["entries"]
    if len(entries) != 10:
        raise RuntimeError("invalid checkpoint manifest cardinality")
    # Validate both sealed bindings; neither is allowed to drift at preflight.
    dims = config["feature_schema"]
    sealed_dims = schema["dimensions"]
    if any(k not in dims or dims[k] != v for k, v in EXPECTED.items()):
        raise RuntimeError("phase_g config feature dimensions disagree")
    sealed_required = ("hidden", "gate", "memory", "combined",
                       "history_plus_combined")
    if any(k not in sealed_dims or sealed_dims[k] != EXPECTED[k]
           for k in sealed_required):
        raise RuntimeError("sealed G0 feature dimensions disagree")
    if len(schema.get("internal_base_columns", [])) != 18 or not {
            "hidden", "gate", "memory", "combined", "history_plus_combined_order"
        }.issubset(schema.get("groups", {})):
        raise RuntimeError("sealed common18/group schema is incomplete")
    results = [_run_model(entry) for entry in entries]
    candi = config["candi_history_control"]
    status = "PASS" if all(r["status"] == "PASS" for r in results) else "STOP"
    if candi["resolution_status"] != "UNRESOLVED_PRELABEL":
        raise RuntimeError("G0 CANDI resolution status changed unexpectedly")
    report = {
        "status": "STOP_CANDI_CONTROL_UNRESOLVED" if status == "PASS" else "STOP_BACKBONE_PREFLIGHT",
        "backbone_preflight_status": status,
        "candi_control_status": candi["resolution_status"],
        "runs": results,
        "feature_schema_expected": EXPECTED,
        "atol": ATOL, "rtol": RTOL,
        "random_unlabeled_only": True,
        "labels_read": False, "test_sources_used": False,
        "test_metrics_computed": False, "scaler_fit": False,
        "classifier_fit": False, "optimizer_created_or_stepped": False,
        "native_predict_invoked": False,
        "phase_g_label_join_started": False,
        "phase_g_statistics_started": False,
        "preflight_script_sha256": f4.sha(Path(__file__).resolve()),
        "environment": environment,
        "note": "CANDI history control remains unresolved; no labels or model results were used to choose a control.",
    }
    out = ROOT / "reports/phase_g/preflight.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"], "runs": len(results),
                      "backbone_preflight": status, "output": str(out)}))
    # STOP_CANDI_CONTROL_UNRESOLVED is the expected, successful fail-closed
    # outcome; only implementation failures return non-zero.
    if status != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
