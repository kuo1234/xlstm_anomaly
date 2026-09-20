"""Frozen-checkpoint strong observable residual-control diagnostic.

The ``extract`` command is observation-only and writes a per-stream cache
containing scores, residuals, O1, and the existing common18 base.  The
``analyze`` command is the only label boundary: it regenerates evaluator rows
after extraction, constructs the fixed arms, and fits the frozen linear probe.
No optimizer or checkpoint write exists in this module.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

WINDOW = 64
BATCH_SIZE = 256
SCENARIOS = ("abrupt", "gradual", "recurring", "correlation")
CONDITIONS = ("none", "spike", "collective", "dependency", "mixture")
FOLDS = {
    "train": tuple(range(1000, 1010)),
    "validation": tuple(range(2000, 2005)),
    "test": tuple(range(3000, 3010)),
}
SEEDS = (11, 22, 33)
ARCHITECTURES = ("xlstm", "lstm")
C_GRID = (0.01, 0.1, 1.0, 10.0)
ATOL, RTOL = 1e-5, 1e-4


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def array_sha(value: np.ndarray) -> str:
    value = np.ascontiguousarray(value)
    return _sha_bytes(str(value.dtype).encode() + str(value.shape).encode() + value.tobytes())


def _stream_name(fold: str, source: int, scenario: str, condition: str) -> str:
    return f"{fold}_s{source}_{scenario}_{condition}.npz"


def _scaler(source: int) -> dict[str, np.ndarray]:
    from m0.synthetic import generate

    prefix = np.asarray(generate(source, "stationary", "none").observations[:4096], dtype=np.float64)
    mean = prefix.mean(axis=0)
    scale = prefix.std(axis=0, ddof=0)
    scale[scale == 0] = 1.0
    return {"mean": mean, "scale": scale}


def scale_input(observations: np.ndarray, scaler: dict[str, np.ndarray]) -> np.ndarray:
    x = np.asarray(observations, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != 8 or not np.isfinite(x).all():
        raise ValueError("expected finite [N,8] observations")
    return ((x - scaler["mean"]) / scaler["scale"]).astype(np.float32)


def dense_windows(observations: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    timestamps = np.arange(WINDOW - 1, len(observations), dtype=np.int64)
    # The explicit stack is intentional: it prevents a strided host view from
    # being retained while the CUDA batch executes.
    windows = np.stack([observations[t - WINDOW + 1 : t + 1] for t in timestamps]).astype(np.float32, copy=False)
    return windows, timestamps


def residual_o1(residual: np.ndarray) -> np.ndarray:
    """Compute the frozen 128-column O1 summary for [B,64,8] residuals."""
    r = np.asarray(residual, dtype=np.float64)
    if r.ndim != 3 or r.shape[1:] != (WINDOW, 8) or not np.isfinite(r).all():
        raise ValueError("expected finite [B,64,8] residual")
    b = r.shape[0]
    t = np.arange(WINDOW, dtype=np.float64)
    tc = t - t.mean()
    denom = float(np.square(tc).sum())
    mean = r.mean(axis=1)
    std = r.std(axis=1, ddof=0)
    rms = np.sqrt(np.mean(r * r, axis=1))
    mean_abs = np.mean(np.abs(r), axis=1)
    final = r[:, -1]
    slope = np.einsum("btc,t->bc", r, tc) / denom
    x0 = r[:, :-1] - r[:, :-1].mean(axis=1, keepdims=True)
    x1 = r[:, 1:] - r[:, 1:].mean(axis=1, keepdims=True)
    den = np.sqrt(np.sum(x0 * x0, axis=1) * np.sum(x1 * x1, axis=1))
    ac = np.divide(np.sum(x0 * x1, axis=1), den, out=np.zeros_like(mean), where=den > 0)
    channel = np.stack((mean, std, rms, mean_abs, final, np.abs(final), slope, ac), axis=2)
    channel = channel.reshape(b, 64)
    centered = r - mean[:, None, :]
    cov = np.einsum("bti,btj->bij", centered, centered) / WINDOW
    diagonal = np.sqrt(np.maximum(np.diagonal(cov, axis1=1, axis2=2), 0.0))
    corr_den = diagonal[:, :, None] * diagonal[:, None, :]
    corr = np.divide(cov, corr_den, out=np.zeros_like(cov), where=corr_den > 0)
    # Nonzero-variance diagonal entries are exactly one; zero-variance entries
    # remain the deterministic zero specified by the protocol.
    diag = np.arange(8)
    corr[:, diag, diag] = np.where(diagonal > 0, 1.0, 0.0)
    cov_cols = np.stack([cov[:, i, j] for i in range(8) for j in range(i, 8)], axis=1)
    corr_cols = np.stack([corr[:, i, j] for i in range(8) for j in range(i + 1, 8)], axis=1)
    result = np.concatenate((channel, cov_cols, corr_cols), axis=1)
    if result.shape != (b, 128) or not np.isfinite(result).all():
        raise RuntimeError("O1 schema drift or non-finite statistic")
    return result.astype(np.float32)


def residual_o2(residual: np.ndarray) -> np.ndarray:
    r = np.asarray(residual, dtype=np.float32)
    if r.ndim != 3 or r.shape[1:] != (WINDOW, 8):
        raise ValueError("expected [B,64,8] residual")
    result = np.concatenate((r.reshape(len(r), -1), (r * r).reshape(len(r), -1)), axis=1)
    if result.shape[1] != 1024 or not np.isfinite(result).all():
        raise RuntimeError("O2 schema drift or non-finite value")
    return result


def _load_lstm(seed: int):
    import torch
    import phase_f_v4_common as f4

    f4.configure()
    model = f4.build("lstm", seed)
    path = ROOT / ("data/phase_f_v3/runs/lstm_%d/best.pt" % seed if seed in (11, 22) else "data/phase_f_v4/runs/lstm_%d/best.pt" % seed)
    if not path.exists():
        raise FileNotFoundError(path)
    payload = torch.load(path, map_location="cpu", weights_only=True)
    model.load_state_dict(payload["model"], strict=True)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    return model, path


def _load_xlstm(seed: int):
    # This is the already validated native-SM121 CUDA overlay path.  It is
    # intentionally isolated here; no training or vanilla checkpoint rewrite
    # occurs.
    import mlstm_inference_canary as canary

    canary.configure()
    checkpoint = ROOT / f"data/phase_f_v4/runs/xlstm_{seed}/best.pt"
    if not checkpoint.exists():
        raise FileNotFoundError(checkpoint)
    vanilla = canary.load_checkpoint(canary.build_vanilla(), checkpoint)
    model = canary.build_cuda()
    canary.map_vanilla_weights(vanilla, model)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    return model, checkpoint


def _extract_batch(model: Any, architecture: str, batch: "Any") -> tuple[Any, Any, Any]:
    import torch

    if architecture == "xlstm":
        from phase_e2_fast_observer import FastStateObserver

        with torch.no_grad(), FastStateObserver(model) as observer:
            output = model(batch)
            internal = observer.summary()
    else:
        from phase_f_lstm_observer import Observer

        # F-v4's matched-LSTM execution contract scopes cuDNN off to each
        # native LSTM call.  The observer replay is the accepted common18 path.
        with torch.backends.cudnn.flags(enabled=False, benchmark=False, deterministic=True, allow_tf32=False):
            with torch.no_grad(), Observer(model) as observer:
                output = model(batch)
                internal = observer.summary()
    score = (output - batch).square().mean((1, 2))
    return output, score, internal


def extract_stream(model: Any, architecture: str, observations: np.ndarray, scaler: dict[str, np.ndarray], batch_size: int = BATCH_SIZE) -> dict[str, np.ndarray]:
    """Observation-only extraction; no SyntheticStream/truth object crosses this boundary."""
    import torch

    scaled = scale_input(observations, scaler)
    windows, timestamps = dense_windows(scaled)
    scores, internals, residuals, summaries, bases = [], [], [], [], []
    for left in range(0, len(windows), batch_size):
        batch = torch.from_numpy(windows[left : left + batch_size]).cuda()
        output, score, internal = _extract_batch(model, architecture, batch)
        residual = batch - output
        # Score equivalence is checked before any host transfer or reduction.
        expected = residual.square().mean((1, 2))
        if not torch.allclose(score, expected, atol=ATOL, rtol=RTOL):
            raise RuntimeError("residual MSE does not reproduce scalar score")
        scores.append(score.detach().cpu().numpy().astype(np.float32))
        internals.append(internal.detach().cpu().numpy().astype(np.float32))
        residual_host = residual.detach().cpu().numpy().astype(np.float32)
        residuals.append(residual_host)
        summaries.append(residual_o1(residual_host))
        bases.append(expected.detach().cpu().numpy().astype(np.float32))
    arrays = {
        "timestamp": timestamps,
        "score": np.concatenate(scores),
        "internal_base18": np.concatenate(internals),
        "residual": np.concatenate(residuals),
        "o1": np.concatenate(summaries),
    }
    if arrays["score"].shape != (len(timestamps),) or arrays["internal_base18"].shape != (len(timestamps), 18):
        raise RuntimeError("extraction shape mismatch")
    if arrays["residual"].shape != (len(timestamps), WINDOW, 8) or arrays["o1"].shape != (len(timestamps), 128):
        raise RuntimeError("residual schema shape mismatch")
    if not np.allclose(arrays["score"], np.mean(arrays["residual"] ** 2, axis=(1, 2)), atol=ATOL, rtol=RTOL):
        raise RuntimeError("host residual MSE mismatch")
    del windows
    return arrays


def extract_cache(cache_dir: Path, seed: int, architecture: str, batch_size: int = BATCH_SIZE, resume: bool = False) -> dict:
    from m0.synthetic import generate

    if seed not in SEEDS or architecture not in ARCHITECTURES:
        raise ValueError("unregistered seed/architecture")
    cache_dir = cache_dir.resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = cache_dir / f"manifest_{architecture}_{seed}.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        "status": "in_progress", "seed": seed, "architecture": architecture,
        "batch_size": batch_size, "window": WINDOW, "stride": 1,
        "labels_in_cache": False, "streams": [],
    }
    model, checkpoint = _load_xlstm(seed) if architecture == "xlstm" else _load_lstm(seed)
    completed = {row["file"] for row in manifest["streams"]}
    manifest["checkpoint"] = str(checkpoint)
    manifest["arrays"] = ["timestamp", "score", "internal_base18", "residual", "o1"]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    for fold, sources in FOLDS.items():
        for source in sources:
            scaler = _scaler(source)
            for scenario in SCENARIOS:
                for condition in CONDITIONS:
                    filename = _stream_name(fold, source, scenario, condition)
                    target = cache_dir / filename
                    if filename in completed and target.exists() and resume:
                        continue
                    if target.exists():
                        raise FileExistsError(target)
                    stream = generate(source, scenario, condition)
                    # Copy observations only; truth is deliberately not passed.
                    observations = np.asarray(stream.observations, dtype=np.float32).copy()
                    started = time.perf_counter()
                    arrays = extract_stream(model, architecture, observations, scaler, batch_size)
                    np.savez(target, **arrays)
                    row = {
                        "fold": fold, "source": int(source), "scenario": scenario,
                        "condition": condition, "file": filename,
                        "rows": int(len(arrays["timestamp"])),
                        "seconds": time.perf_counter() - started,
                        "sha256": _sha_bytes(target.read_bytes()),
                    }
                    manifest["streams"].append(row)
                    completed.add(filename)
                    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
                    print(f"cached {architecture} seed={seed} {filename} rows={row['rows']} wall={row['seconds']:.2f}s", flush=True)
                    del stream, observations, arrays
                    gc.collect()
    manifest["status"] = "complete"
    manifest["stream_count"] = len(manifest["streams"])
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    del model
    gc.collect()
    return manifest


def _rolling(values: np.ndarray, width: int) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    result = np.full((len(values), values.shape[1] * 3), np.nan, dtype=np.float64)
    if len(values) < width:
        return result
    windows = np.lib.stride_tricks.sliding_window_view(values, width, axis=0)
    windows = np.moveaxis(windows, -1, 1)
    t = np.arange(width, dtype=np.float64) - (width - 1) / 2
    den = np.square(t).sum()
    mean = windows.mean(axis=1)
    std = windows.std(axis=1)
    slope = np.einsum("nwd,w->nd", windows, t) / den
    result[width - 1 :] = np.concatenate((mean, std, slope), axis=1)
    return result


def history14(scores: np.ndarray) -> np.ndarray:
    scores = np.asarray(scores, dtype=np.float64)
    previous = np.concatenate(([np.nan], scores[:-1]))
    return np.concatenate((scores[:, None], (scores - previous)[:, None], *(_rolling(scores[:, None], w) for w in (4, 8, 16, 32))), axis=1)


def expand_internal(base: np.ndarray) -> np.ndarray:
    base = np.asarray(base, dtype=np.float64)
    return np.concatenate([np.concatenate((base[:, i : i + 1], *(_rolling(base[:, i : i + 1], w) for w in (4, 8, 16, 32))), axis=1) for i in range(18)], axis=1)


def _truth_rows(stream: Any, timestamps: np.ndarray) -> dict[str, np.ndarray]:
    from phase_g1_core import build_evaluator_rows

    return build_evaluator_rows(stream, timestamps, WINDOW)


def _make_records(cache_dir: Path, fold: str, source: int, scenario: str, condition: str) -> dict[str, np.ndarray] | None:
    from m0.synthetic import generate

    target = cache_dir / _stream_name(fold, source, scenario, condition)
    with np.load(target, allow_pickle=False) as loaded:
        arrays = {key: loaded[key] for key in loaded.files}
    stream = generate(source, scenario, condition)
    truth = _truth_rows(stream, arrays["timestamp"])
    h = history14(arrays["score"])
    internal = expand_internal(arrays["internal_base18"])
    finite = np.isfinite(h).all(1) & np.isfinite(internal).all(1) & np.isfinite(arrays["o1"]).all(1)
    finite &= np.isfinite(arrays["residual"]).all((1, 2))
    primary = np.isin(truth["stratum"], ("anomaly", "drift"))
    keep = finite & primary
    if not np.any(keep):
        return None
    return {
        "H": h[keep], "I": internal[keep], "O1": arrays["o1"][keep].astype(np.float64),
        "O2": np.concatenate((arrays["residual"][keep].reshape(int(keep.sum()), -1), (arrays["residual"][keep] ** 2).reshape(int(keep.sum()), -1)), axis=1).astype(np.float64),
        "y": np.asarray(truth["label"], dtype=np.int8)[keep],
        "source": np.full(int(keep.sum()), source, dtype=np.int32),
        "scenario": np.asarray([scenario] * int(keep.sum()), dtype=object),
        "condition": np.asarray([condition] * int(keep.sum()), dtype=object),
        "timestamp": arrays["timestamp"][keep],
    }


def _collect(cache_dir: Path, fold: str) -> list[dict[str, np.ndarray]]:
    records = []
    for source in FOLDS[fold]:
        for scenario in SCENARIOS:
            for condition in CONDITIONS:
                record = _make_records(cache_dir, fold, source, scenario, condition)
                if record is not None:
                    records.append(record)
    return records


def _arm_matrix(records: list[dict[str, np.ndarray]], arm: str) -> dict[str, np.ndarray]:
    matrices = []
    ys, sources, scenarios, conditions, timestamps = [], [], [], [], []
    for record in records:
        pieces = {"H": record["H"], "I": record["I"], "O1": record["O1"], "O2": record["O2"]}
        if arm == "H": x = pieces["H"]
        elif arm == "H+I": x = np.concatenate((pieces["H"], pieces["I"]), 1)
        elif arm == "H+O1": x = np.concatenate((pieces["H"], pieces["O1"]), 1)
        elif arm == "H+O1+I": x = np.concatenate((pieces["H"], pieces["O1"], pieces["I"]), 1)
        elif arm == "H+O2": x = np.concatenate((pieces["H"], pieces["O2"]), 1)
        elif arm == "H+O2+I": x = np.concatenate((pieces["H"], pieces["O2"], pieces["I"]), 1)
        else: raise ValueError(arm)
        matrices.append(x.astype(np.float64, copy=False)); ys.append(record["y"])
        sources.append(record["source"]); scenarios.append(record["scenario"]); conditions.append(record["condition"]); timestamps.append(record["timestamp"])
    return {"X": np.concatenate(matrices), "y": np.concatenate(ys), "source": np.concatenate(sources), "scenario": np.concatenate(scenarios), "condition": np.concatenate(conditions), "timestamp": np.concatenate(timestamps)}


def _fit_arm(train: dict[str, np.ndarray], validation: dict[str, np.ndarray], test: dict[str, np.ndarray], arm: str, seed: int) -> tuple[dict, np.ndarray]:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler().fit(train["X"])
    x_train = scaler.transform(train["X"]); x_val = scaler.transform(validation["X"]); x_test = scaler.transform(test["X"])
    candidates = []
    for c in C_GRID:
        model = LogisticRegression(C=c, penalty="l2", solver="lbfgs", max_iter=1000, random_state=0)
        model.fit(x_train, train["y"])
        candidates.append((float(average_precision_score(validation["y"], model.predict_proba(x_val)[:, 1])), c))
    best = max(v for v, _ in candidates)
    selected = min(c for v, c in candidates if v == best)
    model = LogisticRegression(C=selected, penalty="l2", solver="lbfgs", max_iter=1000, random_state=0)
    model.fit(x_train, train["y"])
    prediction = model.predict_proba(x_test)[:, 1]
    info = {
        "arm": arm, "detector_seed": seed, "dimension": int(train["X"].shape[1]),
        "selected_C": float(selected), "validation_candidates": [{"AP": v, "C": c} for v, c in candidates],
        "test_AP": float(average_precision_score(test["y"], prediction)),
        "train_rows": int(len(train["y"])), "validation_rows": int(len(validation["y"])), "test_rows": int(len(test["y"])),
        "test_class_counts": np.bincount(test["y"], minlength=2).tolist(),
        "scaler_mean_sha256": array_sha(np.asarray(scaler.mean_, dtype=np.float64)),
        "scaler_scale_sha256": array_sha(np.asarray(scaler.scale_, dtype=np.float64)),
        "coef_sha256": array_sha(np.asarray(model.coef_, dtype=np.float64)),
        "intercept_sha256": array_sha(np.asarray(model.intercept_, dtype=np.float64)),
    }
    return info, prediction


def _scenario_ap(test: dict[str, np.ndarray], prediction: np.ndarray) -> dict[str, float]:
    from sklearn.metrics import average_precision_score

    return {scenario: float(average_precision_score(test["y"][test["scenario"] == scenario], prediction[test["scenario"] == scenario])) for scenario in SCENARIOS if np.unique(test["y"][test["scenario"] == scenario]).size == 2}


def analyze(cache_dir: Path, seed: int, architecture: str, output: Path) -> dict:
    from sklearn.metrics import average_precision_score

    records = {fold: _collect(cache_dir, fold) for fold in FOLDS}
    arms = ("H", "H+I", "H+O1", "H+O1+I", "H+O2", "H+O2+I")
    result = {"status": "exploratory_strong_observable_control", "architecture": architecture, "detector_seed": seed, "arms": {}, "increments": {}, "scenario_effects": {}}
    source_aps: dict[str, dict[str, float | None]] = {}
    # These are invariant cache metadata.  Capture them before releasing each
    # arm's high-dimensional matrices below; keeping ``stacked`` alive until
    # result serialization would unnecessarily retain the O2 working set.
    rows = {
        fold: int(sum(len(record["y"]) for record in records[fold]))
        for fold in FOLDS
    }
    feature_dimensions: dict[str, int] = {}
    for arm in arms:
        # Build and release one arm at a time.  O2 is intentionally high
        # dimensional; retaining six duplicated matrices can exhaust host RAM.
        stacked = {fold: _arm_matrix(records[fold], arm) for fold in FOLDS}
        info, prediction = _fit_arm(stacked["train"], stacked["validation"], stacked["test"], arm, seed)
        feature_dimensions[arm] = int(info["dimension"])
        info["scenario_AP"] = _scenario_ap(stacked["test"], prediction)
        result["arms"][arm] = info
        result["scenario_effects"][arm] = dict(info["scenario_AP"])
        source_aps[arm] = {}
        for source in FOLDS["test"]:
            mask = stacked["test"]["source"] == source
            source_aps[arm][str(source)] = float(average_precision_score(stacked["test"]["y"][mask], prediction[mask])) if np.unique(stacked["test"]["y"][mask]).size == 2 else None
        print(f"fit {architecture} seed={seed} arm={arm} dim={info['dimension']} C={info['selected_C']} AP={info['test_AP']:.6f}", flush=True)
        del stacked, prediction
        gc.collect()
    ap = {arm: result["arms"][arm]["test_AP"] for arm in arms}
    result["increments"] = {
        "I_given_H": ap["H+I"] - ap["H"],
        "I_given_H+O1": ap["H+O1+I"] - ap["H+O1"],
        "I_given_H+O2": ap["H+O2+I"] - ap["H+O2"],
        "O1_given_H": ap["H+O1"] - ap["H"],
        "O2_given_H": ap["H+O2"] - ap["H"],
    }
    result["rows"] = rows
    result["feature_dimensions"] = feature_dimensions
    result["source_AP"] = source_aps
    result["source_effects"] = {}
    for name, left, right in (
        ("I_given_H", "H+I", "H"),
        ("I_given_H+O1", "H+O1+I", "H+O1"),
        ("I_given_H+O2", "H+O2+I", "H+O2"),
        ("O1_given_H", "H+O1", "H"),
        ("O2_given_H", "H+O2", "H"),
    ):
        result["source_effects"][name] = {
            source: None if source_aps[left][source] is None or source_aps[right][source] is None else source_aps[left][source] - source_aps[right][source]
            for source in source_aps[left]
        }
    # Predictions are intentionally not retained in the compact result file;
    # this runner never inserts a ``_predictions`` field.
    result.pop("_predictions", None)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("extract")
    p.add_argument("--cache-dir", type=Path, required=True); p.add_argument("--seed", type=int, required=True); p.add_argument("--architecture", choices=ARCHITECTURES, required=True); p.add_argument("--batch-size", type=int, default=BATCH_SIZE); p.add_argument("--resume", action="store_true")
    p = sub.add_parser("analyze")
    p.add_argument("--cache-dir", type=Path, required=True); p.add_argument("--seed", type=int, required=True); p.add_argument("--architecture", choices=ARCHITECTURES, required=True); p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "extract": extract_cache(args.cache_dir, args.seed, args.architecture, args.batch_size, args.resume)
    else: analyze(args.cache_dir, args.seed, args.architecture, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
