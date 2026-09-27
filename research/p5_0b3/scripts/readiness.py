"""Frozen, source-only readiness candidate grid and trajectory evaluator.

The module is deliberately pure: callers provide finite score prefixes at the
scheduled raw looks. It has no data/manifest/label access.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Iterable, Mapping, Sequence

import numpy as np

SCHEDULED_LOOKS = (144, 288, 576, 1152, 2304)
MAX_DAYS = 64
MIN_PREFIX_SCORES = 200
RECENT_WINDOW = 64
THRESHOLD_EPSILONS = (0.01, 0.025, 0.05, 0.10)
KS_LIMITS = (0.05, 0.10, 0.15, 0.20)
EXCEEDANCE_LIMITS = (0.01, 0.025, 0.05, 0.10)
PLATEAU_LIMITS = (0.05, 0.10, 0.20, 0.40)


@dataclass(frozen=True)
class Candidate:
    family: str
    parameters: Mapping[str, object]
    candidate_id: str
    components: tuple[str, ...] = ()


def _canonical_id(family: str, parameters: Mapping[str, object]) -> str:
    # Preserve the protocol's written decimal tokens (notably 0.10/0.20/0.40)
    # while keeping the in-memory parameters numeric for comparisons.
    def encode(value: object) -> str:
        if isinstance(value, float):
            tokens = {0.01: "0.01", 0.025: "0.025", 0.05: "0.05",
                      0.10: "0.10", 0.20: "0.20", 0.40: "0.40"}
            return tokens.get(value, json.dumps(value, allow_nan=False))
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False)

    payload = "{" + ",".join(
        f"{json.dumps(key, ensure_ascii=True)}:{encode(parameters[key])}"
        for key in sorted(parameters)
    ) + "}"
    return f"{family}|{payload}"


def enumerate_candidates() -> tuple[Candidate, ...]:
    """Return the fixed 228 candidates in stable protocol order."""
    result: list[Candidate] = []

    def add(family: str, params: Mapping[str, object]) -> Candidate:
        item = Candidate(family, dict(params), _canonical_id(family, params))
        result.append(item)
        return item

    fixed = [add("fixed_n", {"look": n}) for n in SCHEDULED_LOOKS]
    add("always_ready", {})
    add("maximum_horizon", {})
    threshold = []
    for eps in THRESHOLD_EPSILONS:
        for consecutive in (2, 3):
            threshold.append(add("threshold_stability", {"consecutive": consecutive, "eps": eps}))
    distribution = []
    for limit in KS_LIMITS:
        for consecutive in (1, 2):
            distribution.append(add("score_distribution_stability", {"consecutive": consecutive, "ks_max": limit}))
    hold = []
    for limit in EXCEEDANCE_LIMITS:
        for consecutive in (1, 2):
            hold.append(add("hold_forward_exceedance", {"consecutive": consecutive, "exceedance_max": limit}))
    for limit in PLATEAU_LIMITS:
        add("marginal_gain_plateau", {"consecutive": 2, "median_change_max": limit})
    # AND candidate IDs are based on sorted component IDs, independent of enumeration order.
    for left_family, right_family in (
        ("threshold_stability", "score_distribution_stability"),
        ("threshold_stability", "hold_forward_exceedance"),
        ("score_distribution_stability", "hold_forward_exceedance"),
    ):
        left_set = threshold if left_family == "threshold_stability" else distribution if left_family == "score_distribution_stability" else hold
        right_set = threshold if right_family == "threshold_stability" else distribution if right_family == "score_distribution_stability" else hold
        for left in left_set:
            for right in right_set:
                components = tuple(sorted((left.candidate_id, right.candidate_id)))
                params = {"left": components[0], "right": components[1]}
                item = Candidate("and", params, _canonical_id("and", params), components)
                result.append(item)
    add("never_ready", {})
    assert len(result) == 228
    return tuple(result)


def finite_scores(scores: Iterable[float]) -> np.ndarray:
    """Canonical float64 finite-score sequence; invalid scores are omitted."""
    values = np.asarray(tuple(scores), dtype=np.float64).reshape(-1)
    return values[np.isfinite(values)]


def score_supported(scores: Iterable[float]) -> bool:
    values = finite_scores(scores)
    return len(values) >= MIN_PREFIX_SCORES and len(values[-RECENT_WINDOW:]) == RECENT_WINDOW


def empirical_q99(scores: Iterable[float]) -> float:
    values = finite_scores(scores)
    if not len(values):
        return math.nan
    return float(np.quantile(values, 0.99, method="linear"))


def two_sample_ks(left: Iterable[float], right: Iterable[float]) -> float:
    """Two-sample empirical KS statistic over pooled distinct values."""
    a, b = finite_scores(left), finite_scores(right)
    if not len(a) or not len(b):
        return math.nan
    pooled = np.unique(np.concatenate((a, b)))
    ca = np.searchsorted(np.sort(a), pooled, side="right") / len(a)
    cb = np.searchsorted(np.sort(b), pooled, side="right") / len(b)
    return float(np.max(np.abs(ca - cb)))


@dataclass(frozen=True)
class LookResult:
    raw_look: int
    supported: bool
    ready: bool
    threshold: float | None
    statistic: float | None
    run_length: int


@dataclass(frozen=True)
class Trajectory:
    candidate_id: str
    results: tuple[LookResult, ...]
    ready_look: int | None
    frozen_threshold: float | None


def evaluate_candidate(
    candidate: Candidate,
    prefixes: Mapping[int, Iterable[float]],
    *,
    iqr_source: float,
) -> Trajectory:
    """Evaluate one candidate on cumulative finite score prefixes by raw look.

    Missing scheduled prefix entries are unsupported and break consecutive runs.
    A READY transition freezes the current full-prefix q99 permanently.
    """
    by_look = {look: finite_scores(prefixes[look]) if look in prefixes else np.array([], dtype=np.float64)
               for look in SCHEDULED_LOOKS}
    rule_families = {"threshold_stability", "score_distribution_stability", "hold_forward_exceedance", "marginal_gain_plateau"}
    if candidate.family == "and":
        # The evaluator is stateless across calls; resolve components from the frozen grid.
        grid = {c.candidate_id: c for c in enumerate_candidates()}
        components = [grid[x] for x in candidate.components]
        trajectories = [evaluate_candidate(c, prefixes, iqr_source=iqr_source) for c in components]
        ready_looks = [t.ready_look for t in trajectories]
        results = []
        for i, look in enumerate(SCHEDULED_LOOKS):
            supported = score_supported(by_look[look])
            ready = supported and all(r is not None and r <= look for r in ready_looks)
            threshold = empirical_q99(by_look[look]) if ready else None
            results.append(LookResult(look, supported, ready, threshold, None, 0))
            if ready:
                # It is a single first-ready event; later READY values are suppressed below.
                break
        return _trajectory(candidate, tuple(results))

    results: list[LookResult] = []
    run = 0
    for i, look in enumerate(SCHEDULED_LOOKS):
        scores = by_look[look]
        supported = score_supported(scores)
        stat: float | None = None
        ready = False
        threshold = empirical_q99(scores) if supported else None
        family = candidate.family

        if family == "fixed_n":
            ready = supported and look == candidate.parameters["look"]
        elif family == "always_ready":
            ready = supported
        elif family == "maximum_horizon":
            ready = supported and look == 2304
        elif family == "never_ready":
            pass
        elif family in rule_families:
            passed = False
            if family == "threshold_stability":
                # Transition requires the immediately preceding scheduled look to be supported.
                if supported and i > 0 and score_supported(by_look[SCHEDULED_LOOKS[i - 1]]):
                    previous = empirical_q99(by_look[SCHEDULED_LOOKS[i - 1]])
                    if threshold is not None and previous > 0 and threshold > 0:
                        stat = abs(math.log(threshold / previous))
                        passed = stat <= float(candidate.parameters["eps"])
            elif family == "score_distribution_stability":
                if supported and len(scores) >= 128:
                    stat = two_sample_ks(scores[-64:], scores[-128:-64])
                    passed = stat <= float(candidate.parameters["ks_max"])
            elif family == "hold_forward_exceedance":
                if supported and len(scores) >= 192:
                    base, recent = scores[:-64], scores[-64:]
                    base_threshold = empirical_q99(base)
                    stat = float(np.count_nonzero(recent > base_threshold) / 64)
                    passed = stat <= float(candidate.parameters["exceedance_max"])
            elif family == "marginal_gain_plateau":
                if supported and len(scores) >= 128 and math.isfinite(iqr_source):
                    previous_recent = scores[-128:-64]
                    current_recent = scores[-64:]
                    stat = abs(float(np.median(current_recent) - np.median(previous_recent))) / max(iqr_source, 1e-12)
                    passed = stat <= float(candidate.parameters["median_change_max"])
            run = run + 1 if passed else 0
            ready = passed and run >= int(candidate.parameters["consecutive"])
        else:
            raise ValueError(f"unknown readiness family: {family}")

        results.append(LookResult(look, supported, ready, threshold if ready else None, stat, run))
        if ready:
            # Commissioning ends at READY; no later scheduled look is consumed.
            break
    return _trajectory(candidate, tuple(results))


def _trajectory(candidate: Candidate, results: tuple[LookResult, ...]) -> Trajectory:
    first = next((r for r in results if r.ready), None)
    return Trajectory(candidate.candidate_id, results, first.raw_look if first else None,
                      first.threshold if first else None)


def evaluate_grid(prefixes: Mapping[int, Iterable[float]], *, iqr_source: float) -> tuple[Trajectory, ...]:
    """Evaluate all candidates in canonical grid order."""
    return tuple(evaluate_candidate(c, prefixes, iqr_source=iqr_source) for c in enumerate_candidates())
