"""Phase G1 executable contract (Stage A/B label-blind implementation).

This module contains the complete frozen H2/H3a data flow, together with
fail-closed guards used by the pre-label adversarial fixtures.  The observation
path is deliberately separate from evaluator truth: model/scaler feature
functions accept observations only, while ``build_evaluator_rows`` is the only
truth-joining boundary and is intended for the post-seal Stage-C runner.

No function in this module changes a frozen checkpoint or creates an optimizer.
The module is usable on small deterministic fixtures for Stage A without
loading real Phase-G labels or computing a scientific metric.
"""
from __future__ import annotations

import hashlib
import inspect
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "phase_g.json"
G0_CONFIG = json.loads(CONFIG_PATH.read_text())
G1_CONFIG_PATH = ROOT / "configs" / "phase_g1.json"
G1_CONFIG = json.loads(G1_CONFIG_PATH.read_text())

TRAIN_SOURCES = tuple(range(1000, 1010))
VALIDATION_SOURCES = tuple(range(2000, 2005))
TEST_SOURCES = tuple(range(3000, 3010))
DETECTOR_SEEDS = (11, 22, 33, 44, 55)
SHIFTED_SCENARIOS = ("abrupt", "gradual", "recurring", "correlation")
STATIONARY_SCENARIO = "stationary"
ROLLING_WIDTHS = (4, 8, 16, 32)
WINDOW = 64
CANDI_WINDOW = 10
FIRST_COMMON_TIMESTAMP = 63
ATOL = 1e-5
RTOL = 1e-4
C_GRID = (0.01, 0.1, 1.0, 10.0)
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 901
SIGN_FLIP_SEED = 902
HOLM_ALPHA = 0.05
HOLM_FAMILY_SIZE = 4
PURGE = 96

EXPECTED_DIMENSIONS = {
    "history14": 14,
    "hidden52": 52,
    "gate130": 130,
    "memory52": 52,
    "combined234": 234,
    "history_plus_combined248": 248,
}

FORBIDDEN_EXTRACTOR_NAMES = frozenset(
    {
        "labels",
        "label",
        "evaluator_labels",
        "regime",
        "regime_id",
        "event_id",
        "event_age",
        "event_end",
        "severity",
        "anomaly_type",
        "generator_parameters",
        "metadata",
    }
)


class ProtocolViolation(RuntimeError):
    """Raised whenever a frozen scientific contract is violated."""


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def array_sha(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    return sha_bytes(
        str(array.dtype).encode()
        + str(array.shape).encode()
        + array.tobytes(order="C")
    )


def object_sha(value: Any) -> str:
    return sha_bytes(_canonical(value).encode())


def _ensure_float_observations(observations: np.ndarray) -> np.ndarray:
    """Validate and return observations without accepting evaluator metadata."""
    if not isinstance(observations, np.ndarray):
        raise ProtocolViolation("extractor accepts an observations ndarray only")
    if observations.ndim != 2 or observations.shape[1] != 8:
        raise ProtocolViolation("expected finite D=8 observation matrix")
    if not np.issubdtype(observations.dtype, np.number):
        raise ProtocolViolation("observations must be numeric")
    if not np.isfinite(observations).all():
        raise ProtocolViolation("observations contain non-finite values")
    return np.asarray(observations)


def assert_observation_only_api(function: Any) -> dict:
    """Static guard: extractor signatures cannot expose truth-like arguments."""
    signature = inspect.signature(function)
    names = {name.lower() for name in signature.parameters}
    forbidden = sorted(names & FORBIDDEN_EXTRACTOR_NAMES)
    has_var_kw = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )
    if forbidden or has_var_kw:
        raise ProtocolViolation(
            f"extractor API exposes forbidden arguments: {forbidden or 'kwargs'}"
        )
    return {"parameters": list(signature.parameters), "forbidden": forbidden, "var_kwargs": has_var_kw}


def window_matrix(observations: np.ndarray, timestamps: Sequence[int], width: int = WINDOW) -> np.ndarray:
    """Create right-edge windows; no padding, tail repetition, or future data."""
    x = _ensure_float_observations(observations)
    ts = np.asarray(timestamps, dtype=np.int64)
    if ts.ndim != 1 or np.any(ts < width - 1) or np.any(ts >= len(x)):
        raise ProtocolViolation("window timestamp outside causal observation range")
    if len(ts) and np.any(np.diff(ts) < 0):
        raise ProtocolViolation("timestamps must remain chronological")
    windows = np.ascontiguousarray(np.stack([x[t - width + 1 : t + 1] for t in ts]))
    expected = (len(ts), width, 8)
    if windows.shape != expected:
        raise ProtocolViolation(f"window shape {windows.shape} != {expected}")
    return windows


def scale_observations(observations: np.ndarray, scaler: Mapping[str, Sequence[float]]) -> np.ndarray:
    """Apply a sealed scaler; fitting is intentionally a separate guarded API."""
    x = _ensure_float_observations(observations).astype(np.float64, copy=False)
    mean = np.asarray(scaler["mean"], dtype=np.float64)
    scale = np.asarray(scaler.get("scale", scaler.get("population_std")), dtype=np.float64)
    if mean.shape != (8,) or scale.shape != (8,) or not np.isfinite(mean).all() or not np.isfinite(scale).all():
        raise ProtocolViolation("invalid D=8 scaler")
    if np.any(scale <= 0):
        raise ProtocolViolation("scaler contains a non-positive scale")
    result = ((x - mean) / scale).astype(np.float32)
    if not np.isfinite(result).all():
        raise ProtocolViolation("scaled observations are non-finite")
    return result


def extract_backbone_rows(
    model: Any,
    architecture: str,
    observations: np.ndarray,
    scaler: Mapping[str, Sequence[float]],
    timestamps: Sequence[int],
    batch_size: int = 128,
) -> dict:
    """Observation-only xLSTM/LSTM score and common18 extraction.

    The imported G0 observers are the already sealed implementation.  This
    function never accepts labels/metadata, never creates an optimizer, and
    processes each independent W64 window with fresh recurrent state.
    """
    assert_observation_only_api(extract_backbone_rows)
    if architecture not in {"xlstm", "lstm"}:
        raise ProtocolViolation("unregistered backbone")
    if not isinstance(batch_size, int) or batch_size < 1:
        raise ProtocolViolation("invalid extraction batch size")
    scaled = scale_observations(observations, scaler)
    ts = np.asarray(timestamps, dtype=np.int64)
    windows = window_matrix(scaled, ts, WINDOW)
    import torch

    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    import phase_g0_preflight as g0  # local import avoids CUDA setup at import time

    before = None
    try:
        import phase_f_v4_common as f4

        before = f4.model_hash(model)
    except Exception:
        # Test doubles need not expose state_dict; real sealed models do.
        before = None
    device = next(model.parameters()).device if hasattr(model, "parameters") else torch.device("cpu")
    scores: list[np.ndarray] = []
    bases: list[np.ndarray] = []
    for left in range(0, len(windows), batch_size):
        batch = torch.from_numpy(windows[left : left + batch_size]).to(device)
        _output, score, base, observer = g0._extract(model, architecture, batch)
        if score.ndim != 1 or base.ndim != 2 or base.shape[1] != 18:
            raise ProtocolViolation("backbone observer returned an invalid shape")
        if not bool(torch.isfinite(score).all()) or not bool(torch.isfinite(base).all()):
            raise ProtocolViolation("backbone score/internal summary is non-finite")
        for check in getattr(observer, "checks", []):
            if "hidden_close" in check or "state_close" in check:
                if not bool(check.get("hidden_close", False) and check.get("state_close", False)):
                    raise ProtocolViolation("xLSTM scalar observer parity failed during extraction")
            elif "checks" in check:
                nested = check["checks"]
                if not all(bool(value.get("pass_", False)) for value in nested.values() if isinstance(value, Mapping)):
                    raise ProtocolViolation("LSTM manual recurrence parity failed during extraction")
        scores.append(score.detach().cpu().numpy().astype(np.float64, copy=False))
        bases.append(base.detach().cpu().numpy().astype(np.float64, copy=False))
    result_score = np.concatenate(scores) if scores else np.empty(0, dtype=np.float64)
    result_base = np.concatenate(bases) if bases else np.empty((0, 18), dtype=np.float64)
    if len(result_score) != len(ts) or result_base.shape != (len(ts), 18):
        raise ProtocolViolation("backbone row cardinality mismatch")
    try:
        import phase_f_v4_common as f4

        if before is not None and f4.model_hash(model) != before:
            raise ProtocolViolation("model mutated during feature extraction")
    except ImportError:
        pass
    return {
        "timestamps": ts.copy(),
        "scores": result_score,
        "internal_base": result_base,
        "score_sha256": array_sha(result_score),
        "internal_base_sha256": array_sha(result_base),
        "architecture": architecture,
        "window": WINDOW,
        "stride": 1,
        "decision_timestamp": "right_edge",
    }


def _rolling(values: np.ndarray, width: int) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 2 or width < 1 or len(values) < width:
        if values.ndim != 2:
            raise ProtocolViolation("rolling input must be T x F")
    result = np.full((len(values), values.shape[1] * 3), np.nan, dtype=np.float64)
    if len(values) < width:
        return result
    t = np.arange(width, dtype=np.float64)
    t -= t.mean()
    denominator = float(np.square(t).sum())
    for end in range(width - 1, len(values)):
        window = values[end - width + 1 : end + 1]
        result[end] = np.concatenate(
            [window.mean(axis=0), window.std(axis=0), (window * t[:, None]).sum(axis=0) / denominator]
        )
    return result


def history14(scores: np.ndarray) -> np.ndarray:
    """Current score, first difference and causal 4/8/16/32 summaries."""
    score = np.asarray(scores, dtype=np.float64)
    if score.ndim != 1 or not np.isfinite(score).all():
        raise ProtocolViolation("history scores must be finite 1-D")
    previous = np.concatenate(([np.nan], score[:-1]))
    columns = [score[:, None], (score - previous)[:, None]]
    for width in ROLLING_WIDTHS:
        columns.append(_rolling(score[:, None], width))
    result = np.concatenate(columns, axis=1)
    if result.shape != (len(score), 14):
        raise ProtocolViolation("history14 dimension mismatch")
    return result


def expand_internal234(base: np.ndarray) -> np.ndarray:
    """Feature-major causal expansion of the 18 internal columns."""
    matrix = np.asarray(base, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[1] != 18 or not np.isfinite(matrix).all():
        raise ProtocolViolation("internal base must be finite T x 18")
    columns: list[np.ndarray] = []
    for index in range(18):
        one = matrix[:, index : index + 1]
        columns.append(one)
        for width in ROLLING_WIDTHS:
            columns.append(_rolling(one, width))
    result = np.concatenate(columns, axis=1)
    if result.shape != (len(matrix), 234):
        raise ProtocolViolation("combined234 dimension mismatch")
    return result


def internal_groups(base: np.ndarray) -> dict[str, np.ndarray]:
    internal = expand_internal234(base)
    groups = {
        "hidden52": internal[:, : 4 * 13],
        "gate130": internal[:, 4 * 13 : 14 * 13],
        "memory52": internal[:, 14 * 13 : 18 * 13],
        "combined234": internal,
    }
    if {key: value.shape[1] for key, value in groups.items()} != {
        "hidden52": 52,
        "gate130": 130,
        "memory52": 52,
        "combined234": 234,
    }:
        raise ProtocolViolation("internal feature group dimensions mismatch")
    return groups


def build_feature_groups(scores: np.ndarray, internal_base: np.ndarray, candi_history: np.ndarray | None = None) -> dict[str, np.ndarray]:
    history = history14(scores)
    groups = internal_groups(internal_base)
    result = {"history14": history, **groups}
    result["history_plus_combined248"] = np.concatenate((history, groups["combined234"]), axis=1)
    if result["history_plus_combined248"].shape[1] != 248:
        raise ProtocolViolation("history+combined dimension mismatch")
    if candi_history is not None:
        control = np.asarray(candi_history, dtype=np.float64)
        if control.shape != history.shape:
            raise ProtocolViolation("CANDI history must be exactly T x 14")
        if not np.array_equal(np.isnan(control), np.isnan(history)):
            raise ProtocolViolation("CANDI history warmup mask differs from common history")
        result["candi_history14"] = control.copy()
        result["candi_history_plus_combined248"] = np.concatenate((control, groups["combined234"]), axis=1)
    return result


def candi_history14(scores: np.ndarray, timestamps: Sequence[int]) -> np.ndarray:
    """Align native W10 CANDI scores to common t>=63 decisions."""
    ts = np.asarray(timestamps, dtype=np.int64)
    if ts.ndim != 1 or len(ts) == 0 or np.any(ts < FIRST_COMMON_TIMESTAMP) or np.any(np.diff(ts) < 0):
        raise ProtocolViolation("CANDI common stream must be chronological and start at t=63")
    score = np.asarray(scores, dtype=np.float64)
    if score.shape != ts.shape or not np.isfinite(score).all():
        raise ProtocolViolation("CANDI scores/timestamps mismatch")
    history = history14(score)
    return history


def assert_candi_alignment(x_timestamps: Sequence[int], candi_timestamps: Sequence[int], candi_window: int = CANDI_WINDOW) -> None:
    x = np.asarray(x_timestamps, dtype=np.int64)
    c = np.asarray(candi_timestamps, dtype=np.int64)
    if not np.array_equal(x, c):
        raise ProtocolViolation("CANDI and W64 timestamps are not byte-identical")
    if len(c) and (int(c[0]) != FIRST_COMMON_TIMESTAMP or np.any(c < candi_window - 1)):
        raise ProtocolViolation("CANDI timestamp alignment violates t>=63/native W10")


def make_row_keys(
    detector_seed: int,
    source_seed: int,
    scenario: str,
    condition: str,
    timestamps: Sequence[int],
    event_ids: Sequence[int] | None = None,
) -> list[dict[str, Any]]:
    ts = np.asarray(timestamps, dtype=np.int64)
    if event_ids is None:
        events = [-1] * len(ts)
    else:
        events = np.asarray(event_ids, dtype=np.int64)
        if events.shape != ts.shape:
            raise ProtocolViolation("event id/timestamp cardinality mismatch")
    return [
        {
            "detector_seed": int(detector_seed),
            "source_seed": int(source_seed),
            "scenario": str(scenario),
            "condition": str(condition),
            "event": int(event),
            "timestamp": int(timestamp),
        }
        for timestamp, event in zip(ts, events)
    ]


def row_key_hash(keys: Sequence[Mapping[str, Any]]) -> str:
    return object_sha(list(keys))


def assert_unique_keys(keys: Sequence[Mapping[str, Any]]) -> None:
    required = {"detector_seed", "source_seed", "scenario", "condition", "event", "timestamp"}
    canonical = [_canonical(dict(key)) for key in keys]
    if any(not required.issubset(dict(key)) for key in keys):
        raise ProtocolViolation("row key is missing a required canonical field")
    if len(canonical) != len(set(canonical)):
        raise ProtocolViolation("duplicate row keys")


def assert_same_row_order(left: Sequence[Mapping[str, Any]], right: Sequence[Mapping[str, Any]]) -> str:
    """Strict cohort gate; order changes/removals are not silently repaired."""
    assert_unique_keys(left)
    assert_unique_keys(right)
    if len(left) != len(right) or list(left) != list(right):
        raise ProtocolViolation("paired arms do not have byte-identical row-key order")
    digest_left = row_key_hash(left)
    digest_right = row_key_hash(right)
    if digest_left != digest_right:
        raise ProtocolViolation("paired row-key hashes differ")
    return digest_left


def paired_intersection(
    left_keys: Sequence[Mapping[str, Any]],
    right_keys: Sequence[Mapping[str, Any]],
    left_valid: Sequence[bool],
    right_valid: Sequence[bool],
) -> tuple[np.ndarray, np.ndarray, str]:
    """Apply a common validity mask only after strict raw-key equality."""
    assert_same_row_order(left_keys, right_keys)
    lm = np.asarray(left_valid, dtype=bool)
    rm = np.asarray(right_valid, dtype=bool)
    if lm.shape != rm.shape or lm.shape != (len(left_keys),):
        raise ProtocolViolation("paired validity mask shape mismatch")
    mask = lm & rm
    keys = [dict(key) for key, keep in zip(left_keys, mask) if keep]
    digest = row_key_hash(keys)
    return mask, mask.copy(), digest


def _source_fold(source_seed: int) -> str:
    source = int(source_seed)
    if source in TRAIN_SOURCES:
        return "train"
    if source in VALIDATION_SOURCES:
        return "validation"
    if source in TEST_SOURCES:
        return "test"
    raise ProtocolViolation(f"unregistered source seed: {source}")


def assert_source_fold_separation() -> None:
    all_sets = [set(TRAIN_SOURCES), set(VALIDATION_SOURCES), set(TEST_SOURCES)]
    if any(a & b for i, a in enumerate(all_sets) for b in all_sets[i + 1 :]):
        raise ProtocolViolation("probe source folds overlap")


def fit_scaler_train_only(features: np.ndarray, source_seeds: Sequence[int], declared_fold: str = "train") -> dict:
    """Fit StandardScaler statistics only when every row is a train source."""
    if declared_fold != "train":
        raise ProtocolViolation("StandardScaler may only be fit on probe-train")
    x = np.asarray(features, dtype=np.float64)
    sources = np.asarray(source_seeds, dtype=np.int64)
    if x.ndim != 2 or len(x) != len(sources) or not np.isfinite(x).all():
        raise ProtocolViolation("invalid scaler input")
    if any(_source_fold(int(seed)) != "train" for seed in sources):
        raise ProtocolViolation("validation/test row reached train scaler")
    mean = x.mean(axis=0)
    var = x.var(axis=0)
    scale = np.sqrt(var)
    scale[scale == 0] = 1.0
    return {"mean": mean.tolist(), "var": var.tolist(), "scale": scale.tolist(), "fit_fold": "train"}


def apply_scaler(features: np.ndarray, scaler: Mapping[str, Sequence[float]]) -> np.ndarray:
    x = np.asarray(features, dtype=np.float64)
    mean = np.asarray(scaler["mean"], dtype=np.float64)
    scale = np.asarray(scaler["scale"], dtype=np.float64)
    if x.ndim != 2 or mean.shape != (x.shape[1],) or scale.shape != mean.shape or np.any(scale <= 0):
        raise ProtocolViolation("invalid feature scaler")
    result = (x - mean) / scale
    if not np.isfinite(result).all():
        raise ProtocolViolation("scaled probe features are non-finite")
    return result


def assert_pooled_shifted_rows(source_seeds: Sequence[int], scenarios: Sequence[str], fold: str) -> None:
    sources = np.asarray(source_seeds, dtype=np.int64)
    values = tuple(str(s) for s in scenarios)
    if any(_source_fold(int(seed)) != fold for seed in sources):
        raise ProtocolViolation(f"{fold} probe rows contain another source fold")
    if set(values) != set(SHIFTED_SCENARIOS):
        raise ProtocolViolation("one pooled probe over exactly four shifted scenarios is required")


def reject_per_scenario_selection(scope: str) -> None:
    if scope != "pooled_shifted":
        raise ProtocolViolation("C selection must be pooled across all four shifted scenarios")


def _require_binary(y: Sequence[int], expected_length: int | None = None) -> np.ndarray:
    labels = np.asarray(y, dtype=np.int8)
    if labels.ndim != 1 or (expected_length is not None and len(labels) != expected_length):
        raise ProtocolViolation("invalid probe labels")
    if not np.isin(labels, [0, 1]).all():
        raise ProtocolViolation("probe labels are not binary")
    return labels


@dataclass(frozen=True)
class ProbeSplit:
    X: np.ndarray
    y: np.ndarray
    keys: tuple[dict[str, Any], ...]
    source_seeds: np.ndarray
    scenarios: tuple[str, ...]
    events: tuple[int, ...]

    def validate(self, fold: str, expected_dim: int | None = None) -> None:
        if self.X.ndim != 2 or not np.isfinite(self.X).all():
            raise ProtocolViolation("probe features must be finite 2-D")
        if expected_dim is not None and self.X.shape[1] != expected_dim:
            raise ProtocolViolation("probe feature dimension mismatch")
        if len(self.X) != len(self.y) or len(self.X) != len(self.keys) or len(self.X) != len(self.source_seeds):
            raise ProtocolViolation("probe split lengths differ")
        _require_binary(self.y, len(self.X))
        assert_unique_keys(self.keys)
        if any(_source_fold(int(seed)) != fold for seed in self.source_seeds):
            raise ProtocolViolation(f"rows from wrong source fold in {fold}")


def fit_probe_pooled(
    train: ProbeSplit,
    validation: ProbeSplit,
    test: ProbeSplit,
    feature_arm: str,
    detector_seed: int,
    expected_dim: int,
    scope: str = "pooled_shifted",
) -> dict:
    """Fit train-only-scaled L2 logistic and select C on pooled validation AP."""
    reject_per_scenario_selection(scope)
    train.validate("train", expected_dim)
    validation.validate("validation", expected_dim)
    test.validate("test", expected_dim)
    assert_pooled_shifted_rows(train.source_seeds, train.scenarios, "train")
    assert_pooled_shifted_rows(validation.source_seeds, validation.scenarios, "validation")
    assert_pooled_shifted_rows(test.source_seeds, test.scenarios, "test")
    if tuple(sorted(C_GRID)) != tuple(C_GRID):
        raise ProtocolViolation("C grid drifted")
    scaler = fit_scaler_train_only(train.X, train.source_seeds)
    x_train = apply_scaler(train.X, scaler)
    x_val = apply_scaler(validation.X, scaler)
    x_test = apply_scaler(test.X, scaler)
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score

    candidates = []
    validation_predictions: dict[str, np.ndarray] = {}
    for C in C_GRID:
        classifier = LogisticRegression(C=float(C), penalty="l2", solver="lbfgs", max_iter=1000, random_state=0)
        classifier.fit(x_train, train.y)
        val_score = classifier.predict_proba(x_val)[:, 1]
        candidates.append((float(average_precision_score(validation.y, val_score)), float(C)))
        validation_predictions[str(float(C))] = np.asarray(val_score, dtype=np.float64)
    best_ap = max(ap for ap, _ in candidates)
    selected = min(C for ap, C in candidates if ap == best_ap)
    model = LogisticRegression(C=selected, penalty="l2", solver="lbfgs", max_iter=1000, random_state=0)
    model.fit(x_train, train.y)
    prediction = model.predict_proba(x_test)[:, 1]
    return {
        "feature_arm": feature_arm,
        "detector_seed": int(detector_seed),
        "classifier": "L2 logistic regression",
        "scaler": scaler,
        "scaler_sha256": object_sha(scaler),
        "selected_C": selected,
        "validation_candidates": [{"C": C, "ap": ap} for ap, C in candidates],
        "validation_predictions": validation_predictions,
        "coef": np.asarray(model.coef_, dtype=np.float64).copy(),
        "intercept": np.asarray(model.intercept_, dtype=np.float64).copy(),
        "coef_sha256": array_sha(np.asarray(model.coef_)),
        "intercept_sha256": array_sha(np.asarray(model.intercept_)),
        "train_row_key_sha256": row_key_hash(train.keys),
        "validation_row_key_sha256": row_key_hash(validation.keys),
        "test_row_key_sha256": row_key_hash(test.keys),
        "train_class_counts": np.bincount(train.y, minlength=2).tolist(),
        "validation_class_counts": np.bincount(validation.y, minlength=2).tolist(),
        "test_class_counts": np.bincount(test.y, minlength=2).tolist(),
        "model": model,
        "test_prediction": prediction,
        "validation_prediction": candidates,
    }


def build_evaluator_rows(stream: Any, timestamps: Sequence[int], window: int = WINDOW) -> dict:
    """Evaluator-only truth boundary; never call this from an extractor."""
    if not hasattr(stream, "labels") or not hasattr(stream, "drift_active"):
        raise ProtocolViolation("evaluator truth object is incomplete")
    labels = np.asarray(stream.labels)
    drift = np.asarray(stream.drift_active, dtype=bool)
    regime = np.asarray(stream.regime)
    event_ids = np.asarray(stream.event_ids)
    ts = np.asarray(timestamps, dtype=np.int64)
    if labels.ndim != 1 or drift.shape != labels.shape or regime.shape != labels.shape or event_ids.shape != labels.shape:
        raise ProtocolViolation("evaluator truth arrays are inconsistent")
    if not np.isin(labels, [0, 1]).all():
        raise ProtocolViolation("evaluator anomaly labels are not binary")
    if np.any(ts < window - 1) or np.any(ts >= len(labels)):
        raise ProtocolViolation("evaluator timestamp outside truth range")
    row_labels: list[int] = []
    strata: list[str] = []
    events: list[int] = []
    event_types: list[str | None] = []
    durations: list[int | None] = []
    severities: list[int | None] = []
    for t in ts:
        left = int(t) - window + 1
        right = int(t) + 1
        anomaly = bool(labels[left:right].any())
        active_drift = bool(drift[left:right].any())
        if anomaly and active_drift:
            category = "mixed"
        elif anomaly:
            category = "anomaly"
        elif active_drift:
            category = "drift"
        elif int(regime[int(t)]) != 0:
            category = "stable_new_normal"
        else:
            category = "stationary_normal"
        strata.append(category)
        row_labels.append(int(anomaly))
        ids = sorted(set(int(value) for value in event_ids[left:right] if int(value) >= 0))
        events.append(ids[0] if len(ids) == 1 else -1)
        matching = [event for event in getattr(stream, "events", ()) if int(event.get("id", -1)) in ids]
        event_types.append(str(matching[0]["type"]) if len(matching) == 1 else None)
        durations.append(int(matching[0]["duration"]) if len(matching) == 1 else None)
        severities.append(int(matching[0]["severity"]) if len(matching) == 1 else None)
    return {
        "timestamps": ts.copy(),
        "label": np.asarray(row_labels, dtype=np.int8),
        "stratum": np.asarray(strata, dtype=object),
        "event": np.asarray(events, dtype=np.int32),
        "event_type": np.asarray(event_types, dtype=object),
        "duration": np.asarray(durations, dtype=object),
        "severity": np.asarray(severities, dtype=object),
        "truth_access_boundary": "evaluator-only",
    }


def primary_binary_mask(evaluator_rows: Mapping[str, Any], allow_empty: bool = False) -> np.ndarray:
    strata = np.asarray(evaluator_rows["stratum"], dtype=object)
    mask = np.isin(strata, ["anomaly", "drift"])
    if not np.any(mask) and not allow_empty:
        raise ProtocolViolation("primary binary cohort is empty")
    return mask


def duration_severity_match_status(
    evaluator_rows: Mapping[str, Any],
    min_rows_per_class: int = 1,
) -> dict[str, Any]:
    """Fixed evaluator-side support check for the mandatory matched analysis.

    A duration/severity bin is usable only when the *same* bin contains both a
    positive anomaly row and a negative drift row.  No bin merging or
    post-outcome redefinition is permitted.  Synthetic drift rows normally
    have no event duration/severity, so returning ``N/A`` is an explicit,
    conservative outcome rather than silently inventing a match.
    """
    durations = np.asarray(evaluator_rows.get("duration", ()), dtype=object)
    severities = np.asarray(evaluator_rows.get("severity", ()), dtype=object)
    labels = np.asarray(evaluator_rows.get("label", ()), dtype=np.int8)
    if len(durations) != len(severities) or len(labels) != len(durations):
        raise ProtocolViolation("duration/severity/label arrays differ")
    bins: dict[str, dict[str, int]] = {}
    for duration, severity, label in zip(durations, severities, labels):
        if duration is None or severity is None:
            continue
        key = f"duration={int(duration)}|severity={int(severity)}"
        row = bins.setdefault(key, {"positive": 0, "negative": 0})
        row["positive" if int(label) == 1 else "negative"] += 1
    usable = {key: value for key, value in bins.items() if value["positive"] >= min_rows_per_class and value["negative"] >= min_rows_per_class}
    return {
        "status": "PASS" if usable else "N/A",
        "bins": bins,
        "usable_bins": usable,
        "reason": None if usable else "no fixed duration/severity bin contains both classes",
    }


def assert_shared_control(left_history: np.ndarray, right_history: np.ndarray, left_keys: Sequence[Mapping[str, Any]], right_keys: Sequence[Mapping[str, Any]]) -> None:
    assert_same_row_order(left_keys, right_keys)
    left = np.asarray(left_history)
    right = np.asarray(right_history)
    if left.shape != right.shape or not np.array_equal(left, right, equal_nan=True):
        raise ProtocolViolation("H3a-C arms do not reuse one identical CANDI history tensor")


def assert_difference_formula(
    name: str,
    left: float,
    right: float,
    computed: float,
    *,
    atol: float = 1e-12,
    rtol: float = 1e-10,
) -> None:
    """Check an algebraic subtraction without rejecting a valid negative effect.

    A negative scientific effect is a legitimate outcome and must be reported,
    not treated as an implementation error.  The pre-label adversarial fixture
    therefore checks the *formula* against frozen component values instead of
    asserting that every observed effect is positive.
    """
    values = (float(left), float(right), float(computed))
    if not np.isfinite(values).all():
        raise ProtocolViolation(f"{name} subtraction contains a non-finite value")
    expected = float(left) - float(right)
    if not bool(np.isclose(float(computed), expected, atol=atol, rtol=rtol)):
        raise ProtocolViolation(f"{name} subtraction formula is reversed or incorrect")


def assert_confirmatory_direction(name: str, effect: float, expected: str = "positive") -> None:
    """Validate finite direction metadata; do not classify negative outcomes.

    Kept as a compatibility helper for older Stage-A callers.  Scientific
    decisions apply the frozen positive-margin rules in ``h2_go``/``h3a_go``;
    this function must not reject a negative observed effect.
    """
    if not np.isfinite(float(effect)):
        raise ProtocolViolation(f"{name} effect is non-finite")
    if expected != "positive":
        raise ProtocolViolation("confirmatory directions are frozen as positive")


def holm_adjust(pvalues: Sequence[float], family_size: int = HOLM_FAMILY_SIZE) -> list[float]:
    p = np.asarray(pvalues, dtype=np.float64)
    if len(p) != family_size or family_size != HOLM_FAMILY_SIZE:
        raise ProtocolViolation(f"confirmatory Holm family must contain exactly {HOLM_FAMILY_SIZE} members")
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ProtocolViolation("invalid p-value family")
    order = np.argsort(p, kind="stable")
    adjusted = np.minimum(1.0, np.maximum.accumulate(p[order] * (len(p) - np.arange(len(p)))))
    result = np.empty_like(p)
    result[order] = adjusted
    return result.tolist()


def assert_family_names(names: Sequence[str]) -> None:
    expected = ("H2", "H3a-A", "H3a-B", "H3a-C")
    if tuple(names) != expected:
        raise ProtocolViolation("confirmatory p-value family/order is not the sealed four-member family")


def hierarchical_bootstrap(delta: np.ndarray, draws: int = BOOTSTRAP_DRAWS, seed: int = BOOTSTRAP_SEED) -> dict:
    """Source-first then detector-seed bootstrap.

    The confirmatory estimand is ``[source, detector_seed]``: each source's
    AP is pooled over all four shifted scenarios before the source macro.  A
    third scenario axis is accepted only for descriptive strata and is averaged
    within each sampled source/seed draw.
    """
    values = np.asarray(delta, dtype=np.float64)
    if values.ndim not in (2, 3) or values.shape[0] != 10 or values.shape[1] != 5 or not np.isfinite(values).all():
        raise ProtocolViolation("expected finite [10,5] primary or [10,5,4] descriptive effects")
    source_count, seed_count = values.shape[:2]
    rng = np.random.default_rng(seed)
    source_indices = rng.integers(0, source_count, size=(draws, source_count))
    seed_indices = rng.integers(0, seed_count, size=(draws, source_count, seed_count))
    if values.ndim == 2:
        sampled = values[source_indices[:, :, None], seed_indices]
        means = sampled.mean(axis=(1, 2))
    else:
        sampled = values[source_indices[:, :, None], seed_indices, :]
        means = sampled.mean(axis=(1, 2, 3))
    observed = float(values.mean())
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {"draws": int(draws), "seed": int(seed), "mean": observed, "ci95": [float(lo), float(hi)]}


def source_cluster_sign_flip(delta: np.ndarray, seed: int = SIGN_FLIP_SEED, permutations: int = 10_000) -> float:
    values = np.asarray(delta, dtype=np.float64)
    if values.ndim not in (2, 3) or values.shape[0] != 10 or values.shape[1] != 5 or not np.isfinite(values).all():
        raise ProtocolViolation("expected finite [10,5] primary or [10,5,4] descriptive effects")
    source_means = values.mean(axis=tuple(range(1, values.ndim)))
    observed = abs(float(source_means.mean()))
    n = len(source_means)
    if n <= 20:
        signs = np.asarray(list(itertools.product((-1.0, 1.0), repeat=n)), dtype=np.float64)
        null = np.abs((signs * source_means[None, :]).mean(axis=1))
    else:
        rng = np.random.default_rng(seed)
        signs = rng.choice((-1.0, 1.0), size=(permutations, n))
        null = np.abs((signs * source_means[None, :]).mean(axis=1))
    return float(np.mean(null >= observed - 1e-15))


def positive_seed_scenario_counts(delta: np.ndarray) -> tuple[int, int]:
    values = np.asarray(delta, dtype=np.float64)
    if values.shape != (10, 5, 4):
        raise ProtocolViolation("positive-count input must be [10,5,4]")
    return int((values.mean(axis=(0, 2)) > 0).sum()), int((values.mean(axis=(0, 1)) > 0).sum())


def positive_seed_source_counts(delta: np.ndarray) -> int:
    """Count detector seeds with positive primary source-macro effects."""
    values = np.asarray(delta, dtype=np.float64)
    if values.shape != (10, 5) or not np.isfinite(values).all():
        raise ProtocolViolation("primary positive-count input must be [10,5]")
    return int((values.mean(axis=0) > 0).sum())


def primary_scenario_support(delta: np.ndarray) -> tuple[int, int]:
    """Return positive detector/scenario counts from a descriptive [10,5,4] tensor."""
    return positive_seed_scenario_counts(delta)


def h2_go(effect: float, ci_lower: float, holm_p: float, positive_seeds: int, positive_scenarios: int, matched_support: bool) -> bool:
    return bool(
        effect >= 0.02
        and ci_lower > 0
        and holm_p < 0.05
        and positive_seeds >= 4
        and positive_scenarios >= 3
        and matched_support
    )


def h3a_go(
    h2: bool,
    effect_a: float,
    ci_a: float,
    p_a: float,
    effect_b: float,
    ci_b: float,
    p_b: float,
    effect_c: float,
    ci_c: float,
    p_c: float,
    reproducibility: bool,
    matched_support: bool,
) -> bool:
    if not h2:
        return False
    return bool(
        effect_a >= 0.02
        and ci_a > 0
        and p_a < 0.05
        and effect_b > 0
        and ci_b > 0
        and p_b < 0.05
        and effect_c > 0
        and ci_c > 0
        and p_c < 0.05
        and reproducibility
        and matched_support
    )


def assert_decision_direction_fixture() -> None:
    """Used by Stage-A: deliberately reversed subtraction must be rejected."""
    assert_difference_formula("fixture", 0.7, 0.4, 0.4 - 0.7)


def ensure_no_native_predict_path() -> None:
    """Fail-closed source-level check for the scientific common extractor."""
    source = inspect.getsource(extract_backbone_rows)
    if "predict_step" in source:
        raise ProtocolViolation("native predict_step appears in common extractor")


__all__ = [
    "ATOL",
    "RTOL",
    "BOOTSTRAP_DRAWS",
    "BOOTSTRAP_SEED",
    "C_GRID",
    "CANDI_WINDOW",
    "CONFIG_PATH",
    "DETECTOR_SEEDS",
    "EXPECTED_DIMENSIONS",
    "FIRST_COMMON_TIMESTAMP",
    "G1_CONFIG",
    "HOLM_FAMILY_SIZE",
    "ProtocolViolation",
    "ProbeSplit",
    "PURGE",
    "SHIFTED_SCENARIOS",
    "TEST_SOURCES",
    "TRAIN_SOURCES",
    "VALIDATION_SOURCES",
    "apply_scaler",
    "assert_candi_alignment",
    "assert_confirmatory_direction",
    "assert_difference_formula",
    "assert_decision_direction_fixture",
    "assert_family_names",
    "assert_observation_only_api",
    "assert_pooled_shifted_rows",
    "assert_same_row_order",
    "assert_shared_control",
    "assert_source_fold_separation",
    "array_sha",
    "build_evaluator_rows",
    "build_feature_groups",
    "candi_history14",
    "ensure_no_native_predict_path",
    "expand_internal234",
    "fit_probe_pooled",
    "fit_scaler_train_only",
    "hierarchical_bootstrap",
    "history14",
    "holm_adjust",
    "h2_go",
    "h3a_go",
    "internal_groups",
    "make_row_keys",
    "object_sha",
    "paired_intersection",
    "positive_seed_scenario_counts",
    "positive_seed_source_counts",
    "primary_binary_mask",
    "duration_severity_match_status",
    "reject_per_scenario_selection",
    "row_key_hash",
    "scale_observations",
    "source_cluster_sign_flip",
    "window_matrix",
]
