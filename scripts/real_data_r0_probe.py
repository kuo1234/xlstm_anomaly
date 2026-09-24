"""R0 probe (Design B), estimand, exploratory resampling and predeclared wording.

Pure functions.  Nothing here runs during the protocol/preflight stage: the
preflight imports only the torch/sklearn-free constants and the unit tests
exercise the functions on synthetic arrays.  ``sklearn`` is imported lazily,
only inside functions that fit or score.

Isolation contract of :func:`select_and_evaluate`
-------------------------------------------------
1. Both HGB candidates are fitted on the probe-train block only.
2. Selection uses probe-validation AP only; an exact tie selects 100.
3. The selected candidate's probe-test predictions are computed and the
   selection record is frozen *before* the probe-test labels are requested.
4. Probe-test labels are requested exactly once, through a callable.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import real_data_r0_data as r0data  # noqa: E402

CONFIG = r0data.CONFIG
PROBE = CONFIG["probe"]
ESTIMAND = CONFIG["estimand"]
HGB_PARAMETERS: dict[str, Any] = dict(PROBE["hgb_parameters"])
MAX_ITER_GRID: tuple[int, ...] = tuple(int(v) for v in PROBE["max_iter_grid"])
TIE_MAX_ITER = 100
ARMS = ("H", "H+I")
H_DIM, I_DIM = 14, 234

WORDING = {
    "R0_POSITIVE_INCREMENT": (
        "Recurrent internal-state features retain additional anomaly predictive/decodable utility over causal "
        "score/history in the tested source-native SMD within-machine diagnostic (Design B; exploratory "
        "uncertainty; not unseen-machine transfer)."
    ),
    "R0_NO_RESOLVED_INCREMENT": (
        "R0 does not resolve additional real-data predictive utility of internal state beyond score/history "
        "under the frozen diagnostic."
    ),
    "R0_NEGATIVE_INCREMENT": (
        "Under the frozen diagnostic, adding internal234 to score/history reduced probe-test AP on source-native "
        "SMD; this negative increment is reported directly."
    ),
}
NEVER_CLAIM = (
    "internal information unavailable in raw input",
    "contradiction of P1r",
    "xLSTM superiority over LSTM",
    "benign-drift discrimination",
    "cross-domain generality",
    "unseen-machine transfer (Design B)",
    "deployment validity",
    "online adaptation value",
)


def estimator_parameters(max_iter: int) -> dict[str, Any]:
    if int(max_iter) not in MAX_ITER_GRID:
        raise r0data.ProtocolViolation(f"max_iter must be one of {MAX_ITER_GRID}")
    return {**HGB_PARAMETERS, "max_iter": int(max_iter)}


def make_estimator(max_iter: int):
    from sklearn.ensemble import HistGradientBoostingClassifier

    return HistGradientBoostingClassifier(**estimator_parameters(max_iter))


def average_precision(y: np.ndarray, score: np.ndarray) -> float:
    from sklearn.metrics import average_precision_score

    y = np.asarray(y)
    if np.unique(y).size != 2:
        raise r0data.ProtocolViolation("AP undefined: block lacks one class")
    return float(average_precision_score(y, score))


def arm_matrix(history: np.ndarray, internal: np.ndarray | None, arm: str) -> np.ndarray:
    h = np.asarray(history, dtype=np.float64)
    if h.ndim != 2 or h.shape[1] != H_DIM:
        raise r0data.ProtocolViolation("H must be [n, 14]")
    if arm == "H":
        x = h
    elif arm == "H+I":
        i = np.asarray(internal, dtype=np.float64)
        if i.shape != (len(h), I_DIM):
            raise r0data.ProtocolViolation("internal234 must be [n, 234]")
        x = np.concatenate((h, i), axis=1)
    else:
        raise r0data.ProtocolViolation("unregistered arm")
    if not np.isfinite(x).all():
        raise r0data.ProtocolViolation("probe features must be finite (warmup rows excluded)")
    return x


def select_and_evaluate(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_validation: np.ndarray,
    y_validation: np.ndarray,
    x_test: np.ndarray,
    load_test_labels: Callable[[], np.ndarray],
    *,
    estimator_factory: Callable[[int], Any] = make_estimator,
    ap: Callable[[np.ndarray, np.ndarray], float] = average_precision,
) -> dict[str, Any]:
    fitted: dict[int, Any] = {}
    validation_ap: dict[int, float] = {}
    for max_iter in MAX_ITER_GRID:
        estimator = estimator_factory(max_iter)
        estimator.fit(x_train, y_train)
        fitted[max_iter] = estimator
        validation_ap[max_iter] = float(ap(y_validation, estimator.predict_proba(x_validation)[:, 1]))
    best = max(validation_ap.values())
    tied = [m for m in MAX_ITER_GRID if validation_ap[m] == best]
    selected = TIE_MAX_ITER if TIE_MAX_ITER in tied else min(tied)
    selection = {"validation_ap": {str(k): v for k, v in validation_ap.items()}, "selected_max_iter": int(selected),
                 "tie": len(tied) > 1}
    prediction = np.asarray(fitted[selected].predict_proba(x_test)[:, 1], dtype=np.float64)
    y_test = np.asarray(load_test_labels())
    if y_test.shape != (len(x_test),):
        raise r0data.ProtocolViolation("probe-test labels misaligned with probe-test rows")
    return {**selection, "test_ap": float(ap(y_test, prediction)), "test_rows": int(len(x_test)),
            "test_positives": int(y_test.sum())}


# --------------------------------------------------------------------------- estimand and resampling


def summarize_matrix(matrix: np.ndarray, machines: tuple[str, ...], seeds: tuple[int, ...]) -> dict[str, Any]:
    m = np.asarray(matrix, dtype=np.float64)
    if m.shape != (len(machines), len(seeds)) or not np.isfinite(m).all():
        raise r0data.ProtocolViolation("delta-AP matrix must be finite machines x seeds")
    return {
        "cells": {machine: {str(seed): float(m[i, j]) for j, seed in enumerate(seeds)} for i, machine in enumerate(machines)},
        "mean": float(m.mean()),
        "machine_means": {machine: float(m[i].mean()) for i, machine in enumerate(machines)},
        "seed_means": {str(seed): float(m[:, j].mean()) for j, seed in enumerate(seeds)},
        "positive_cells": int((m > 0).sum()),
        "n_cells": int(m.size),
    }


def two_way_bootstrap(matrix: np.ndarray, draws: int = 10_000, seed: int = 901) -> dict[str, float]:
    """Per replicate: resample machine rows, then seed columns, with replacement."""
    m = np.asarray(matrix, dtype=np.float64)
    rng = np.random.default_rng(seed)
    stats = np.empty(draws, dtype=np.float64)
    for b in range(draws):
        rows = rng.integers(0, m.shape[0], size=m.shape[0])
        cols = rng.integers(0, m.shape[1], size=m.shape[1])
        stats[b] = m[np.ix_(rows, cols)].mean()
    return {"lower": float(np.quantile(stats, 0.025)), "upper": float(np.quantile(stats, 0.975)), "draws": int(draws),
            "seed": int(seed), "label": ESTIMAND["uncertainty_label"]}


def machine_only_bootstrap(matrix: np.ndarray, draws: int = 10_000, seed: int = 901) -> dict[str, float]:
    """Resample machine rows only, conditional on the observed seeds."""
    m = np.asarray(matrix, dtype=np.float64)
    rng = np.random.default_rng(seed)
    stats = np.empty(draws, dtype=np.float64)
    for b in range(draws):
        rows = rng.integers(0, m.shape[0], size=m.shape[0])
        stats[b] = m[rows].mean()
    return {"lower": float(np.quantile(stats, 0.025)), "upper": float(np.quantile(stats, 0.975)), "draws": int(draws),
            "seed": int(seed), "label": ESTIMAND["uncertainty_label"]}


def classify(summary: dict[str, Any], two_way: dict[str, float], machine_only: dict[str, float]) -> dict[str, str]:
    positive = summary["positive_cells"]
    if two_way["lower"] > 0 and machine_only["lower"] > 0 and positive >= 7:
        label = "R0_POSITIVE_INCREMENT"
    elif two_way["upper"] < 0 and machine_only["upper"] < 0 and positive <= 2:
        label = "R0_NEGATIVE_INCREMENT"
    else:
        label = "R0_NO_RESOLVED_INCREMENT"
    return {"class": label, "wording": WORDING[label]}


# --------------------------------------------------------------------------- detector sanity (diagnostic only)


def calibration_threshold(validation_scores: np.ndarray) -> float:
    s = np.asarray(validation_scores, dtype=np.float64)
    if s.ndim != 1 or not np.isfinite(s).all() or len(s) == 0:
        raise r0data.ProtocolViolation("calibration scores must be finite 1-D")
    return float(np.quantile(s, 0.95))


def detector_sanity(test_scores: np.ndarray, window_labels: np.ndarray, threshold: float) -> dict[str, float]:
    from sklearn.metrics import roc_auc_score

    s = np.asarray(test_scores, dtype=np.float64)
    y = np.asarray(window_labels).astype(bool)
    alarm = s > threshold
    auroc = float(roc_auc_score(y, s))
    return {"ap": average_precision(y.astype(np.uint8), s), "auroc": auroc,
            "recall_at_threshold": float(alarm[y].mean()), "fpr_at_threshold": float(alarm[~y].mean()),
            "window_prevalence": float(y.mean()), "threshold": float(threshold),
            "detector_weak_flag": bool(auroc <= 0.55)}
