"""Dense-cache extraction and offline attribution for the frozen mLSTM audit.

This module deliberately separates the observation-only CUDA path from every
evaluator operation.  ``extract`` writes only timestamps, scores, and compact
named state summaries.  Labels are regenerated and joined by ``analyze``
after extraction has returned, and all stride/family variants are built from
the same cache.
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

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from mlstm_inference_canary import (  # noqa: E402
    build_cuda,
    build_vanilla,
    combined_observer,
    configure,
    load_checkpoint,
    map_vanilla_weights,
)


SOURCES = {
    "train": tuple(range(1000, 1010)),
    "validation": tuple(range(2000, 2005)),
    "test": tuple(range(3000, 3010)),
}
SCENARIOS = ("abrupt", "gradual", "recurring", "correlation")
CONDITIONS = ("none", "spike", "collective", "dependency", "mixture")
WINDOW = 64
ROLLING_WIDTHS = (4, 8, 16, 32)
C_GRID = (0.01, 0.1, 1.0, 10.0)
ATOL = 1e-5
RTOL = 1e-4
BASE_COLUMNS = {
    "mh": ("hidden_mean", "hidden_std", "hidden_rms", "hidden_delta_rms"),
    "mc": (
        "memory_c_mean", "memory_c_std", "memory_c_frobenius",
        "memory_c_relative_delta", "memory_c_top_singular_ratio",
        "memory_c_spectral_entropy",
    ),
    "mn": ("normalizer_n_mean", "normalizer_n_std", "normalizer_n_rms", "normalizer_n_delta_rms"),
    "mm": ("stabilizer_m_mean", "stabilizer_m_std", "stabilizer_m_rms", "stabilizer_m_delta_mean"),
}


def array_sha(array: np.ndarray) -> str:
    value = np.ascontiguousarray(array)
    return hashlib.sha256(
        str(value.dtype).encode() + str(value.shape).encode() + value.tobytes()
    ).hexdigest()


def _cache_name(fold: str, source: int, scenario: str, condition: str) -> str:
    return f"{fold}_s{source}_{scenario}_{condition}.npz"


def _import_generator():
    from m0.synthetic import generate

    return generate


def source_scaler(seed: int) -> tuple[np.ndarray, np.ndarray]:
    generate = _import_generator()
    prefix = np.asarray(generate(seed, "stationary", "none").observations[:4096], dtype=np.float64)
    mean = prefix.mean(0)
    scale = prefix.std(0)
    scale[scale == 0] = 1.0
    return mean, scale


def dense_windows(observations: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    timestamps = np.arange(WINDOW - 1, len(observations), dtype=np.int64)
    windows = np.stack(
        [observations[t - WINDOW + 1 : t + 1] for t in timestamps]
    ).astype(np.float32, copy=False)
    return windows, timestamps


def extract_observation_only(model, observations: np.ndarray, batch_size: int) -> dict[str, np.ndarray]:
    """Extract a complete dense stream without accepting evaluator metadata."""
    if observations.ndim != 2 or observations.shape[1] != 8 or not np.isfinite(observations).all():
        raise ValueError("expected finite D=8 observations")
    windows, timestamps = dense_windows(observations)
    scores: list[np.ndarray] = []
    s_bases: list[np.ndarray] = []
    m_bases: list[np.ndarray] = []
    import torch

    with torch.no_grad():
        for left in range(0, len(windows), batch_size):
            batch = torch.from_numpy(windows[left : left + batch_size]).cuda()
            _, score, s_base, m_base, _ = combined_observer(model, batch)
            scores.append(score.detach().cpu().numpy().astype(np.float32, copy=False))
            s_bases.append(s_base.detach().cpu().numpy().astype(np.float32, copy=False))
            m_bases.append(m_base.detach().cpu().numpy().astype(np.float32, copy=False))
    s = np.concatenate(s_bases, axis=0)
    m = np.concatenate(m_bases, axis=0)
    if s.shape != (len(timestamps), 18) or m.shape != (len(timestamps), 18):
        raise RuntimeError("observer base dimensions are not 18")
    return {
        "timestamp": timestamps,
        "score": np.concatenate(scores, axis=0),
        "s_base18": s,
        "mh_base4": m[:, :4],
        "mc_base6": m[:, 4:10],
        "mn_base4": m[:, 10:14],
        "mm_base4": m[:, 14:18],
    }


def _load_model(seed: int = 11):
    configure()
    checkpoint = ROOT / "data" / "phase_f_v4" / "runs" / f"xlstm_{seed}" / "best.pt"
    if not checkpoint.exists():
        raise FileNotFoundError(checkpoint)
    vanilla = load_checkpoint(build_vanilla(), checkpoint)
    model = build_cuda()
    map_vanilla_weights(vanilla, model)
    model.eval()
    return model, checkpoint


def extract_cache(cache_dir: Path, batch_size: int = 256, resume: bool = False) -> dict:
    """Create the one dense observation-only cache for all registered streams."""
    cache_dir = cache_dir.resolve()
    if cache_dir.exists() and not resume:
        if any(cache_dir.iterdir()):
            raise FileExistsError(f"refusing non-empty cache directory: {cache_dir}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = cache_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("status") == "complete":
            return manifest
    model, checkpoint = _load_model(11)
    generate = _import_generator()
    manifest = {
        "status": "in_progress",
        "checkpoint": str(checkpoint),
        "batch_size": int(batch_size),
        "window": WINDOW,
        "decision_stride": 1,
        "rolling_widths": list(ROLLING_WIDTHS),
        "folds": {key: list(value) for key, value in SOURCES.items()},
        "scenarios": list(SCENARIOS),
        "conditions": list(CONDITIONS),
        "labels_in_cache": False,
        "arrays": ["timestamp", "score", "s_base18", "mh_base4", "mc_base6", "mn_base4", "mm_base4"],
        "streams": [],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    for fold, sources in SOURCES.items():
        for source in sources:
            mean, scale = source_scaler(source)
            for scenario in SCENARIOS:
                for condition in CONDITIONS:
                    name = _cache_name(fold, source, scenario, condition)
                    target = cache_dir / name
                    if target.exists():
                        if not resume:
                            raise FileExistsError(target)
                        continue
                    stream = generate(source, scenario, condition)
                    observations = ((stream.observations.astype(np.float64) - mean) / scale).astype(np.float32)
                    started = time.perf_counter()
                    arrays = extract_observation_only(model, observations, batch_size)
                    np.savez(target, **arrays)
                    elapsed = time.perf_counter() - started
                    entry = {
                        "fold": fold, "source": int(source), "scenario": scenario,
                        "condition": condition, "file": name,
                        "rows": int(len(arrays["timestamp"])),
                        "seconds": float(elapsed),
                        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                    }
                    manifest["streams"].append(entry)
                    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
                    print(
                        f"cached {fold} source={source} {scenario}/{condition} "
                        f"rows={entry['rows']} wall={elapsed:.2f}s",
                        flush=True,
                    )
                    del stream, observations, arrays
                    gc.collect()
    manifest["status"] = "complete"
    manifest["stream_count"] = len(manifest["streams"])
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def _rolling(values: np.ndarray, width: int) -> np.ndarray:
    """Causal mean/std/slope, matching the previous probe implementation."""
    values = np.asarray(values, dtype=np.float64)
    if values.ndim == 1:
        values = values[:, None]
    n, dim = values.shape
    result = np.full((n, dim * 3), np.nan, dtype=np.float64)
    if n < width:
        return result
    windows = np.lib.stride_tricks.sliding_window_view(values, width, axis=0)
    windows = np.moveaxis(windows, -1, 1)  # [n-width+1,width,dim]
    t = np.arange(width, dtype=np.float64)
    t -= t.mean()
    mean = windows.mean(axis=1)
    std = windows.std(axis=1)
    slope = np.einsum("nwd,w->nd", windows, t) / float(np.square(t).sum())
    result[width - 1 :] = np.concatenate((mean, std, slope), axis=1)
    return result


def history14(scores: np.ndarray) -> np.ndarray:
    values = np.asarray(scores, dtype=np.float64)
    previous = np.concatenate(([np.nan], values[:-1]))
    # Current score precedes delta in the frozen schema.
    result = np.concatenate(
        (values[:, None], (values - previous)[:, None]), axis=1
    )
    result = np.concatenate((result, *(_rolling(values, width) for width in ROLLING_WIDTHS)), axis=1)
    if result.shape[1] != 14:
        raise RuntimeError("history14 schema drift")
    return result


def expand_base(base: np.ndarray, widths: tuple[int, ...] = ROLLING_WIDTHS) -> np.ndarray:
    base = np.asarray(base, dtype=np.float64)
    if base.ndim != 2:
        raise ValueError("base must be [T,F]")
    columns: list[np.ndarray] = []
    for index in range(base.shape[1]):
        one = base[:, index]
        columns.append(one[:, None])
        for width in widths:
            columns.append(_rolling(one, width))
    return np.concatenate(columns, axis=1)


def select_stride(arrays: dict[str, np.ndarray], stride: int) -> dict[str, np.ndarray]:
    timestamp = arrays["timestamp"]
    if stride == 1:
        index = np.arange(len(timestamp), dtype=np.int64)
    else:
        index = np.flatnonzero((timestamp - (WINDOW - 1)) % stride == 0)
    return {key: value[index] for key, value in arrays.items()}


def evaluator_rows(stream, timestamps: np.ndarray) -> dict[str, np.ndarray]:
    labels, drift, regime, event_ids = stream.labels, stream.drift_active, stream.regime, stream.event_ids
    by_id = {int(event["id"]): event for event in stream.events}
    label, stratum, event, duration, severity = [], [], [], [], []
    for timestamp in timestamps:
        left, right = int(timestamp) - WINDOW + 1, int(timestamp) + 1
        anomaly = bool(labels[left:right].any())
        active = bool(drift[left:right].any())
        if anomaly and active:
            category = "mixed"
        elif anomaly:
            category = "anomaly"
        elif active:
            category = "drift"
        elif int(regime[int(timestamp)]) != 0:
            category = "stable_new_normal"
        else:
            category = "stationary_normal"
        ids = sorted(set(int(item) for item in event_ids[left:right] if int(item) >= 0))
        one = by_id.get(ids[0]) if len(ids) == 1 else None
        label.append(int(anomaly))
        stratum.append(category)
        event.append(ids[0] if len(ids) == 1 else -1)
        duration.append(None if one is None else int(one["duration"]))
        severity.append(None if one is None else int(one["severity"]))
    return {
        "y": np.asarray(label, dtype=np.int8),
        "stratum": np.asarray(stratum, dtype=object),
        "event": np.asarray(event, dtype=np.int32),
        "duration": np.asarray(duration, dtype=object),
        "severity": np.asarray(severity, dtype=object),
    }


def _records(cache_dir: Path, fold: str, stride: int) -> list[dict]:
    generate = _import_generator()
    records = []
    for source in SOURCES[fold]:
        for scenario in SCENARIOS:
            for condition in CONDITIONS:
                path = cache_dir / _cache_name(fold, source, scenario, condition)
                if not path.exists():
                    raise FileNotFoundError(path)
                with np.load(path, allow_pickle=False) as loaded:
                    arrays = {key: loaded[key] for key in loaded.files}
                arrays = select_stride(arrays, stride)
                truth = evaluator_rows(generate(source, scenario, condition), arrays["timestamp"])
                h = history14(arrays["score"])
                s = expand_base(arrays["s_base18"])
                mh = expand_base(arrays["mh_base4"])
                mc = expand_base(arrays["mc_base6"])
                mn = expand_base(arrays["mn_base4"])
                mm = expand_base(arrays["mm_base4"])
                finite = np.isfinite(h).all(1) & np.isfinite(s).all(1)
                finite &= np.isfinite(mh).all(1) & np.isfinite(mc).all(1)
                finite &= np.isfinite(mn).all(1) & np.isfinite(mm).all(1)
                primary = np.isin(truth["stratum"], ("anomaly", "drift"))
                keep = finite & primary
                records.append({
                    "source": int(source), "scenario": scenario, "condition": condition,
                    "timestamp": arrays["timestamp"][keep], "H": h[keep], "S": s[keep],
                    "Mh": mh[keep], "MC": mc[keep], "Mn": mn[keep], "Mm": mm[keep],
                    "y": truth["y"][keep], "stratum": truth["stratum"][keep],
                    "event": truth["event"][keep], "duration": truth["duration"][keep],
                    "severity": truth["severity"][keep],
                })
    return records


def _arm_features(record: dict, arm: str) -> np.ndarray:
    if arm == "H":
        return record["H"]
    if arm == "H+Mh":
        return np.concatenate((record["H"], record["Mh"]), axis=1)
    if arm == "H+MC":
        return np.concatenate((record["H"], record["MC"]), axis=1)
    if arm == "H+Mn+Mm":
        return np.concatenate((record["H"], record["Mn"], record["Mm"]), axis=1)
    if arm == "H+M_noC":
        return np.concatenate((record["H"], record["Mh"], record["Mn"], record["Mm"]), axis=1)
    if arm == "H+M_full":
        return np.concatenate((record["H"], record["Mh"], record["MC"], record["Mn"], record["Mm"]), axis=1)
    if arm == "H+S":
        return np.concatenate((record["H"], record["S"]), axis=1)
    if arm == "H+S+M_noC":
        return np.concatenate((record["H"], record["S"], record["Mh"], record["Mn"], record["Mm"]), axis=1)
    if arm == "H+S+M_full":
        return np.concatenate((record["H"], record["S"], record["Mh"], record["MC"], record["Mn"], record["Mm"]), axis=1)
    raise ValueError(arm)


def _stack(records: list[dict], arm: str) -> dict[str, np.ndarray]:
    fields = {key: [] for key in ("X", "y", "source", "scenario", "condition", "timestamp", "stratum", "event", "duration", "severity")}
    for record in records:
        x = _arm_features(record, arm)
        fields["X"].append(x.astype(np.float64, copy=False))
        fields["y"].append(record["y"])
        fields["source"].append(np.full(len(x), record["source"], dtype=np.int32))
        for key in ("scenario", "condition", "stratum"):
            fields[key].append(np.full(len(x), record[key], dtype=object))
        for key in ("timestamp", "event", "duration", "severity"):
            fields[key].append(record[key])
    return {key: np.concatenate(value, axis=0) for key, value in fields.items()}


def _scale_train_only(train: dict, validation: dict, test: dict) -> tuple[dict, np.ndarray, np.ndarray, np.ndarray]:
    if not np.all(np.isin(train["source"], SOURCES["train"])):
        raise RuntimeError("non-train source entered scaler")
    mean = train["X"].mean(0)
    scale = train["X"].std(0)
    scale[scale == 0] = 1.0
    transform = lambda x: (x - mean) / scale
    return {"mean": mean, "scale": scale}, transform(train["X"]), transform(validation["X"]), transform(test["X"])


def fit_arm(train: dict, validation: dict, test: dict, arm: str, seed: int) -> tuple[dict, np.ndarray]:
    scaler, x_train, x_val, x_test = _scale_train_only(train, validation, test)
    candidates = []
    for c in C_GRID:
        classifier = LogisticRegression(C=c, penalty="l2", solver="lbfgs", max_iter=300, random_state=0)
        classifier.fit(x_train, train["y"])
        candidates.append((float(average_precision_score(validation["y"], classifier.predict_proba(x_val)[:, 1])), c))
    best = max(value for value, _ in candidates)
    selected = min(c for value, c in candidates if value == best)
    classifier = LogisticRegression(C=selected, penalty="l2", solver="lbfgs", max_iter=300, random_state=0)
    classifier.fit(x_train, train["y"])
    prediction = classifier.predict_proba(x_test)[:, 1]
    return {
        "arm": arm, "detector_seed": seed, "dimension": int(train["X"].shape[1]),
        "selected_C": float(selected),
        "validation_candidates": [{"ap": float(value), "C": float(c)} for value, c in candidates],
        "scaler_sha256": array_sha(np.concatenate((scaler["mean"], scaler["scale"]))),
        "coef_sha256": array_sha(np.asarray(classifier.coef_, dtype=np.float64)),
        "intercept_sha256": array_sha(np.asarray(classifier.intercept_, dtype=np.float64)),
        "train_count": int(len(train["y"])), "validation_count": int(len(validation["y"])),
        "test_count": int(len(test["y"])),
        "test_class_counts": np.bincount(test["y"], minlength=2).tolist(),
    }, prediction


def _ap(test: dict, prediction: np.ndarray) -> float:
    if len(np.unique(test["y"])) < 2:
        return float("nan")
    return float(average_precision_score(test["y"], prediction))


def _scenario_ap(test: dict, prediction: np.ndarray) -> dict[str, float | None]:
    result = {}
    for scenario in SCENARIOS:
        mask = test["scenario"] == scenario
        result[scenario] = _ap({"y": test["y"][mask]}, prediction[mask]) if mask.any() else None
    return result


def _fit_mode(cache_dir: Path, stride: int, seed: int, arms: tuple[str, ...], output: Path) -> dict:
    records = {fold: _records(cache_dir, fold, stride) for fold in ("train", "validation", "test")}
    stacked = {fold: {arm: _stack(records[fold], arm) for arm in arms} for fold in records}
    results = {}
    predictions = {}
    for arm in arms:
        info, prediction = fit_arm(stacked["train"][arm], stacked["validation"][arm], stacked["test"][arm], arm, seed)
        info["test_AP"] = _ap(stacked["test"][arm], prediction)
        info["scenario_AP"] = _scenario_ap(stacked["test"][arm], prediction)
        results[arm] = info
        predictions[arm] = prediction
        print(f"fit stride={stride} arm={arm} dim={info['dimension']} C={info['selected_C']} AP={info['test_AP']:.6f}", flush=True)
    ap = {arm: results[arm]["test_AP"] for arm in arms}
    increments = {}
    if "H+M_full" in ap:
        increments["M_full_given_H"] = ap["H+M_full"] - ap["H"]
    if "H+S+M_full" in ap:
        increments["M_full_given_H_plus_S"] = ap["H+S+M_full"] - ap["H+S"]
    if "H+S" in ap:
        increments["S_given_H"] = ap["H+S"] - ap["H"]
    if "H+M_noC" in ap and "H+M_full" in ap:
        increments["C_history"] = ap["H+M_full"] - ap["H+M_noC"]
    if "H+S+M_noC" in ap and "H+S+M_full" in ap:
        increments["C_given_sLSTM"] = ap["H+S+M_full"] - ap["H+S+M_noC"]
    key = next(iter(stacked["test"].values()))
    np.savez_compressed(
        output.with_suffix(".predictions.npz"),
        y=key["y"], source=key["source"], scenario=key["scenario"],
        condition=key["condition"], timestamp=key["timestamp"],
        **{f"prediction_{arm.replace('+', '_')}": predictions[arm] for arm in arms},
    )
    result = {
        "status": "exploratory_dense_attribution",
        "detector_seed": seed, "decision_stride": stride,
        "rolling_widths": list(ROLLING_WIDTHS), "window": WINDOW,
        "arms": results, "test_AP": ap, "increments": increments,
        "rows_by_fold": {
            fold: {arm: int(len(stacked[fold][arm]["y"])) for arm in arms}
            for fold in stacked
        },
        "feature_dimensions": {arm: int(stacked["train"][arm]["X"].shape[1]) for arm in arms},
        "labels_joined_after_observation_cache": True,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


def analyze(cache_dir: Path, mode: str, output: Path, seed: int = 11) -> dict:
    if mode == "stride32":
        arms = ("H", "H+S", "H+M_full", "H+S+M_full")
        return _fit_mode(cache_dir, 32, seed, arms, output)
    if mode == "stride1":
        arms = (
            "H", "H+S", "H+M_full", "H+S+M_full", "H+Mh", "H+MC",
            "H+Mn+Mm", "H+M_noC", "H+S+M_noC",
        )
        return _fit_mode(cache_dir, 1, seed, arms, output)
    if mode == "span":
        # The dense cache is reused; these widths are a clearly labelled
        # temporal-span diagnostic, not a replacement for stride-1 semantics.
        original = ROLLING_WIDTHS
        globals()["ROLLING_WIDTHS"] = (97, 225, 481, 993)
        try:
            return _fit_mode(cache_dir, 1, seed, ("H", "H+S", "H+M_full", "H+S+M_full", "H+M_noC", "H+S+M_noC"), output)
        finally:
            globals()["ROLLING_WIDTHS"] = original
    raise ValueError(mode)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    extract = sub.add_parser("extract")
    extract.add_argument("--cache-dir", type=Path, required=True)
    extract.add_argument("--batch-size", type=int, default=256)
    extract.add_argument("--resume", action="store_true")
    analysis = sub.add_parser("analyze")
    analysis.add_argument("--cache-dir", type=Path, required=True)
    analysis.add_argument("--mode", choices=("stride32", "stride1", "span"), required=True)
    analysis.add_argument("--output", type=Path, required=True)
    analysis.add_argument("--seed", type=int, default=11)
    args = parser.parse_args()
    if args.command == "extract":
        result = extract_cache(args.cache_dir, args.batch_size, args.resume)
    else:
        result = analyze(args.cache_dir, args.mode, args.output, args.seed)
    print(json.dumps({key: value for key, value in result.items() if key not in ("arms",)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
