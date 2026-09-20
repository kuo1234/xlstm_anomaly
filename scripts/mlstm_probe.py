"""Fixed low-capacity mLSTM mechanism screen.

The extractor receives only a float observation matrix.  Evaluator truth is
joined after extraction by :func:`evaluator_rows`; it never enters the model,
observer, rolling summaries, scaler, or logistic fit.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from mlstm_inference_canary import (  # noqa: E402
    build_cuda,
    build_vanilla,
    load_checkpoint,
    map_vanilla_weights,
    configure as cuda_configure,
    combined_observer,
)


SOURCES = {
    "train": tuple(range(1000, 1010)),
    "validation": tuple(range(2000, 2005)),
    "test": tuple(range(3000, 3010)),
}
SCENARIOS = ("abrupt", "gradual", "recurring", "correlation")
CONDITIONS = ("none", "spike", "collective", "dependency", "mixture")
C_GRID = (0.01, 0.1, 1.0, 10.0)
WINDOW = 64
TIMESTAMP_STRIDE = 32
ATOL = 1e-5
RTOL = 1e-4


def array_sha(a: np.ndarray) -> str:
    x = np.ascontiguousarray(a)
    return hashlib.sha256(str(x.dtype).encode() + str(x.shape).encode() + x.tobytes()).hexdigest()


def _rolling(values: np.ndarray, width: int) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    result = np.full((len(values), values.shape[1] * 3), np.nan, dtype=np.float64)
    if len(values) < width:
        return result
    t = np.arange(width, dtype=np.float64)
    t -= t.mean()
    denominator = float(np.square(t).sum())
    for end in range(width - 1, len(values)):
        window = values[end - width + 1 : end + 1]
        result[end] = np.concatenate(
            [window.mean(0), window.std(0), (window * t[:, None]).sum(0) / denominator]
        )
    return result


def history14(scores: np.ndarray) -> np.ndarray:
    score = np.asarray(scores, dtype=np.float64)
    previous = np.concatenate(([np.nan], score[:-1]))
    columns = [score[:, None], (score - previous)[:, None]]
    columns.extend(_rolling(score[:, None], width) for width in (4, 8, 16, 32))
    result = np.concatenate(columns, axis=1)
    if result.shape[1] != 14:
        raise RuntimeError("history14 schema drift")
    return result


def expand234(base: np.ndarray) -> np.ndarray:
    base = np.asarray(base, dtype=np.float64)
    if base.ndim != 2 or base.shape[1] != 18:
        raise RuntimeError("mLSTM base schema drift")
    columns = []
    for index in range(18):
        one = base[:, index : index + 1]
        columns.append(one)
        for width in (4, 8, 16, 32):
            columns.append(_rolling(one, width))
    result = np.concatenate(columns, axis=1)
    if result.shape[1] != 234:
        raise RuntimeError("expanded 234 schema drift")
    return result


def source_scaler(seed: int) -> tuple[np.ndarray, np.ndarray]:
    from m0.synthetic import generate

    prefix = np.asarray(generate(seed, "stationary", "none").observations[:4096], dtype=np.float64)
    mean, scale = prefix.mean(0), prefix.std(0)
    scale[scale == 0] = 1.0
    return mean, scale


def observation_windows(observations: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Fixed timestamp cohort, chosen without evaluator metadata."""
    ts = np.arange(WINDOW - 1, len(observations), TIMESTAMP_STRIDE, dtype=np.int64)
    windows = np.stack([observations[t - WINDOW + 1 : t + 1] for t in ts]).astype(np.float32)
    return windows, ts


def extract_observation_only(model, observations: np.ndarray, batch_size: int = 128) -> dict:
    """Extract scores/S/M from observations only; no stream/truth object accepted."""
    if observations.ndim != 2 or observations.shape[1] != 8 or not np.isfinite(observations).all():
        raise ValueError("expected finite D=8 observations")
    windows, timestamps = observation_windows(observations)
    scores, s_bases, m_bases = [], [], []
    with torch.no_grad():
        for left in range(0, len(windows), batch_size):
            batch = torch.from_numpy(windows[left : left + batch_size]).cuda()
            _, score, s_base, m_base, _ = combined_observer(model, batch)
            scores.append(score.detach().cpu().numpy().astype(np.float64))
            s_bases.append(s_base.detach().cpu().numpy().astype(np.float64))
            m_bases.append(m_base.detach().cpu().numpy().astype(np.float64))
    result = {
        "timestamps": timestamps,
        "scores": np.concatenate(scores),
        "s_base": np.concatenate(s_bases),
        "m_base": np.concatenate(m_bases),
    }
    if result["s_base"].shape[1] != 18 or result["m_base"].shape[1] != 18:
        raise RuntimeError("observer base dimensions are not 18")
    return result


def evaluator_rows(stream, timestamps: np.ndarray) -> dict:
    """Truth boundary, called only after observation-only extraction returns."""
    labels, drift, regime, event_ids = stream.labels, stream.drift_active, stream.regime, stream.event_ids
    labels_out, strata, events, durations, severities = [], [], [], [], []
    by_id = {int(e["id"]): e for e in stream.events}
    for t in timestamps:
        left, right = int(t) - WINDOW + 1, int(t) + 1
        anomaly = bool(labels[left:right].any())
        active = bool(drift[left:right].any())
        if anomaly and active:
            category = "mixed"
        elif anomaly:
            category = "anomaly"
        elif active:
            category = "drift"
        elif int(regime[int(t)]) != 0:
            category = "stable_new_normal"
        else:
            category = "stationary_normal"
        ids = sorted(set(int(v) for v in event_ids[left:right] if int(v) >= 0))
        event = by_id.get(ids[0]) if len(ids) == 1 else None
        labels_out.append(int(anomaly))
        strata.append(category)
        events.append(ids[0] if len(ids) == 1 else -1)
        durations.append(None if event is None else int(event["duration"]))
        severities.append(None if event is None else int(event["severity"]))
    return {
        "label": np.asarray(labels_out, dtype=np.int8),
        "stratum": np.asarray(strata, dtype=object),
        "event": np.asarray(events, dtype=np.int32),
        "duration": np.asarray(durations, dtype=object),
        "severity": np.asarray(severities, dtype=object),
        "timestamps": timestamps.copy(),
    }


def make_record(model, source: int, scenario: str, condition: str) -> dict:
    from m0.synthetic import generate

    stream = generate(source, scenario, condition)
    mean, scale = source_scaler(source)
    observations = ((stream.observations.astype(np.float64) - mean) / scale).astype(np.float32)
    extracted = extract_observation_only(model, observations)
    # Labels are joined only after the model/observer call has completely
    # returned.  They are never passed into extract_observation_only.
    truth = evaluator_rows(stream, extracted["timestamps"])
    h = history14(extracted["scores"])
    s = expand234(extracted["s_base"])
    m = expand234(extracted["m_base"])
    valid = np.isfinite(h).all(1) & np.isfinite(s).all(1) & np.isfinite(m).all(1)
    primary = np.isin(truth["stratum"], ("anomaly", "drift"))
    keep = valid & primary
    return {
        "source": int(source), "scenario": scenario, "condition": condition,
        "timestamps": extracted["timestamps"][keep],
        "H": h[keep].astype(np.float32),
        "S": s[keep].astype(np.float32),
        "M": m[keep].astype(np.float32),
        "y": truth["label"][keep],
        "stratum": truth["stratum"][keep],
        "event": truth["event"][keep],
        "duration": truth["duration"][keep],
        "severity": truth["severity"][keep],
    }


def _fold_records(model, fold: str) -> list[dict]:
    records = []
    for source in SOURCES[fold]:
        for scenario in SCENARIOS:
            for condition in CONDITIONS:
                start = time.perf_counter()
                record = make_record(model, source, scenario, condition)
                record["extract_wall_s"] = time.perf_counter() - start
                records.append(record)
                print(f"{fold} source={source} {scenario}/{condition} rows={len(record['y'])} wall={record['extract_wall_s']:.2f}s", flush=True)
    return records


def stack_arm(records: list[dict], arm: str) -> dict:
    xs, ys, sources, scenarios, conditions, timestamps, strata, events, durations, severities = ([] for _ in range(10))
    for rec in records:
        if arm == "H":
            x = rec["H"]
        elif arm == "H+S":
            x = np.concatenate((rec["H"], rec["S"]), axis=1)
        elif arm == "H+M":
            x = np.concatenate((rec["H"], rec["M"]), axis=1)
        elif arm == "H+S+M":
            x = np.concatenate((rec["H"], rec["S"], rec["M"]), axis=1)
        else:
            raise ValueError(arm)
        xs.append(x); ys.append(rec["y"]); sources.append(np.full(len(x), rec["source"], dtype=np.int32))
        scenarios.append(np.full(len(x), rec["scenario"], dtype=object)); conditions.append(np.full(len(x), rec["condition"], dtype=object))
        timestamps.append(rec["timestamps"]); strata.append(rec["stratum"]); events.append(rec["event"])
        durations.append(rec["duration"]); severities.append(rec["severity"])
    return {
        "X": np.concatenate(xs), "y": np.concatenate(ys), "source": np.concatenate(sources),
        "scenario": np.concatenate(scenarios), "condition": np.concatenate(conditions),
        "timestamp": np.concatenate(timestamps), "stratum": np.concatenate(strata),
        "event": np.concatenate(events), "duration": np.concatenate(durations),
        "severity": np.concatenate(severities),
    }


def scaler_train_only(x: np.ndarray, source: np.ndarray) -> dict:
    if not np.all(np.isin(source, SOURCES["train"])):
        raise RuntimeError("non-train row entered scaler")
    mean = x.astype(np.float64).mean(0)
    scale = x.astype(np.float64).std(0)
    scale[scale == 0] = 1.0
    return {"mean": mean, "scale": scale}


def fit_arm(train: dict, validation: dict, test: dict, arm: str, seed: int) -> tuple[dict, np.ndarray]:
    scaler = scaler_train_only(train["X"], train["source"])
    x_train = (train["X"].astype(np.float64) - scaler["mean"]) / scaler["scale"]
    x_val = (validation["X"].astype(np.float64) - scaler["mean"]) / scaler["scale"]
    x_test = (test["X"].astype(np.float64) - scaler["mean"]) / scaler["scale"]
    candidates = []
    for C in C_GRID:
        clf = LogisticRegression(C=C, penalty="l2", solver="lbfgs", max_iter=300, random_state=0)
        clf.fit(x_train, train["y"])
        candidates.append((float(average_precision_score(validation["y"], clf.predict_proba(x_val)[:, 1])), C))
    best_ap = max(value for value, _ in candidates)
    selected = min(C for value, C in candidates if value == best_ap)
    clf = LogisticRegression(C=selected, penalty="l2", solver="lbfgs", max_iter=300, random_state=0)
    clf.fit(x_train, train["y"])
    prediction = clf.predict_proba(x_test)[:, 1]
    return {
        "arm": arm, "detector_seed": seed, "dimension": int(train["X"].shape[1]),
        "selected_C": float(selected),
        "validation_candidates": [{"ap": float(value), "C": float(C)} for value, C in candidates],
        "scaler_sha256": array_sha(np.concatenate((scaler["mean"], scaler["scale"]))),
        "coef_sha256": array_sha(np.asarray(clf.coef_, dtype=np.float64)),
        "intercept_sha256": array_sha(np.asarray(clf.intercept_, dtype=np.float64)),
        "train_count": int(len(train["y"])), "validation_count": int(len(validation["y"])),
        "test_count": int(len(test["y"])),
        "test_class_counts": np.bincount(test["y"], minlength=2).tolist(),
        "prediction": prediction,
    }, prediction


def ap_strata(test: dict, prediction: np.ndarray) -> dict:
    from sklearn.metrics import average_precision_score

    result = {}
    for scenario in SCENARIOS:
        mask = test["scenario"] == scenario
        result[scenario] = float(average_precision_score(test["y"][mask], prediction[mask])) if mask.any() and test["y"][mask].sum() else None
    result["duration"] = {}
    for duration in (1, 16, 64, 256):
        mask = ((test["y"] == 1) & (test["duration"] == duration)) | ((test["y"] == 0) & (test["stratum"] == "drift"))
        result["duration"][str(duration)] = float(average_precision_score(test["y"][mask], prediction[mask])) if mask.any() and len(np.unique(test["y"][mask])) == 2 else None
    result["severity"] = {}
    for severity in (1, 2, 3):
        mask = ((test["y"] == 1) & (test["severity"] == severity)) | ((test["y"] == 0) & (test["stratum"] == "drift"))
        result["severity"][str(severity)] = float(average_precision_score(test["y"][mask], prediction[mask])) if mask.any() and len(np.unique(test["y"][mask])) == 2 else None
    return result


def run(seed: int, output: Path) -> dict:
    cuda_configure()
    checkpoint = ROOT / "data" / "phase_f_v4" / "runs" / f"xlstm_{seed}" / "best.pt"
    if not checkpoint.exists():
        raise FileNotFoundError(checkpoint)
    vanilla = load_checkpoint(build_vanilla(), checkpoint)
    model = build_cuda()
    map_vanilla_weights(vanilla, model)
    model.eval()
    records = {}
    total = 0
    for fold in ("train", "validation", "test"):
        records[fold] = _fold_records(model, fold)
        total += sum(len(record["y"]) for record in records[fold])
    arms = ("H", "H+S", "H+M", "H+S+M")
    fitted = {}
    stacked = {fold: {arm: stack_arm(records[fold], arm) for arm in arms} for fold in records}
    for arm in arms:
        fit, prediction = fit_arm(stacked["train"][arm], stacked["validation"][arm], stacked["test"][arm], arm, seed)
        fit["strata"] = ap_strata(stacked["test"][arm], prediction)
        fitted[arm] = fit
        print(f"fit {arm} C={fit['selected_C']} test_AP={average_precision_score(stacked['test'][arm]['y'], prediction):.6f}", flush=True)
    base = {arm: float(average_precision_score(stacked["test"][arm]["y"], fitted[arm]["prediction"])) for arm in arms}
    result = {
        "status": "exploratory_seed_screen",
        "detector_seed": seed,
        "checkpoint": str(checkpoint),
        "timestamp_stride": TIMESTAMP_STRIDE,
        "window": WINDOW,
        "source_folds": {k: list(v) for k, v in SOURCES.items()},
        "scenarios": list(SCENARIOS), "conditions": list(CONDITIONS),
        "labels_joined_after_observation_extraction": True,
        "rows_extracted": int(total),
        "rows_by_fold": {fold: int(sum(len(r["y"]) for r in records[fold])) for fold in records},
        "arms": {arm: {k: v for k, v in info.items() if k != "prediction"} for arm, info in fitted.items()},
        "test_AP": base,
        "increments": {
            "M_given_history": base["H+M"] - base["H"],
            "M_given_sLSTM": base["H+S+M"] - base["H+S"],
            "sLSTM_given_history": base["H+S"] - base["H"],
            "H+M_vs_H+S_descriptive": base["H+M"] - base["H+S"],
        },
    }
    # Keep only predictions/truth metadata required for the exploratory audit;
    # no raw feature cache is written.
    np.savez_compressed(
        output.with_suffix(".predictions.npz"),
        y=stacked["test"]["H"]["y"],
        source=stacked["test"]["H"]["source"],
        scenario=stacked["test"]["H"]["scenario"],
        condition=stacked["test"]["H"]["condition"],
        timestamp=stacked["test"]["H"]["timestamp"],
        duration=stacked["test"]["H"]["duration"],
        severity=stacked["test"]["H"]["severity"],
        **{f"prediction_{arm.replace('+', '_')}": fitted[arm]["prediction"] for arm in arms},
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.seed, args.output)
