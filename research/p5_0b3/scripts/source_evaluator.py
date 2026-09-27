"""Pure SOURCE pseudo-target suffix evaluator and readiness selector.

Inputs are already-projected score/mask arrays. This module has no manifest,
label, archive, or project-data access; callers retain responsibility for
constructing the permitted SOURCE-only masks.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence

import numpy as np

try:  # Support both ``scripts``-on-path execution and package imports.
    from .readiness import Candidate, enumerate_candidates
except ImportError:  # pragma: no cover - exercised by production script launcher
    from readiness import Candidate, enumerate_candidates

PRIMARY_ABSOLUTE_FPR_CAP = 0.03
PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR = 0.50
MIN_FINITE_NORMAL_SUFFIX_OBSERVATIONS = 100
MIN_NORMAL_SCORE_COVERAGE = 0.95


class SourceNotEvaluable(ValueError):
    """Generic source stratum has no candidate with any joint successes."""

    def __init__(self, message: str = "SOURCE_MODEL_NOT_EVALUABLE", *, summaries=()):
        self.summaries = tuple(summaries)
        super().__init__(message)


@dataclass(frozen=True)
class SuffixMetrics:
    normal_pointwise_fpr: float
    eligible_fault_report_recall: float
    normal_score_count: int
    eligible_fault_report_count: int
    hit_fault_report_count: int
    normal_raw_count: int = -1
    normal_finite_count: int = -1
    normal_score_coverage: float = math.nan

    def __post_init__(self) -> None:
        # Preserve compatibility with synthetic/manual metrics constructed
        # before raw and finite support were reported separately.
        if self.normal_raw_count < 0:
            object.__setattr__(self, "normal_raw_count", self.normal_score_count)
        if self.normal_finite_count < 0:
            object.__setattr__(self, "normal_finite_count", self.normal_score_count)
        if math.isnan(self.normal_score_coverage):
            coverage = (self.normal_finite_count / self.normal_raw_count
                        if self.normal_raw_count else math.nan)
            object.__setattr__(self, "normal_score_coverage", coverage)

    @property
    def normal_scores_evaluable(self) -> bool:
        """Whether normal suffix support meets the frozen count/coverage gate."""
        return (self.normal_raw_count >= MIN_FINITE_NORMAL_SUFFIX_OBSERVATIONS and
                self.normal_finite_count >= MIN_FINITE_NORMAL_SUFFIX_OBSERVATIONS and
                math.isfinite(self.normal_score_coverage) and
                self.normal_score_coverage >= MIN_NORMAL_SCORE_COVERAGE)


@dataclass(frozen=True)
class TaskOutcome:
    """One pseudo-target task for a candidate; no entity identity is retained."""
    ready: bool
    metrics: SuffixMetrics
    raw_count: int = 2304
    elapsed_days: float = 64.0


@dataclass(frozen=True)
class CandidateSummary:
    candidate_id: str
    joint_success_fraction: float
    mean_acquisition_cost: float
    macro_fault_report_recall: float
    macro_normal_pointwise_fpr: float
    conjunct_count: int
    joint_success_count: int
    task_count: int


@dataclass(frozen=True)
class CandidateSelection:
    selected: Candidate
    summaries: tuple[CandidateSummary, ...]


def type7_quantile(values: Iterable[float], q: float) -> float:
    """Float64 Hyndman-Fan type-7 quantile; empty input yields NaN."""
    if not 0.0 <= q <= 1.0:
        raise ValueError("quantile probability out of range")
    data = np.asarray(tuple(values), dtype=np.float64).reshape(-1)
    data = data[np.isfinite(data)]
    if not data.size:
        return math.nan
    return float(np.quantile(data, q, method="linear"))


def fixed_n_threshold(prefix_scores: Iterable[float]) -> float:
    """Return fixed-N q99 when at least 200 finite scores are supported."""
    data = np.asarray(tuple(prefix_scores), dtype=np.float64).reshape(-1)
    data = data[np.isfinite(data)]
    return type7_quantile(data, 0.99) if data.size >= 200 else math.nan


def source_fixed_n_baselines(
    task_metrics: Sequence[SuffixMetrics],
) -> tuple[float, float]:
    """Return fixed-N eligible-report recall q10 and normal-FPR diagnostic q90."""
    if not task_metrics:
        return math.nan, math.nan
    return (
        type7_quantile((m.eligible_fault_report_recall for m in task_metrics), 0.10),
        type7_quantile((m.normal_pointwise_fpr for m in task_metrics), 0.90),
    )


def effective_recall_floor(recall_q10: float) -> float:
    """Apply the protocol's fixed 0.50 minimum to the source type-7 q10."""
    if not math.isfinite(recall_q10):
        return math.nan
    return max(PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR, recall_q10)


def inclusive_interval_mask(raw_indices: Iterable[int], start: int, end: int) -> np.ndarray:
    """Build an inclusive interval mask on suffix raw-row indices."""
    if end < start:
        raise ValueError("interval end precedes start")
    indices = np.asarray(tuple(raw_indices), dtype=np.int64).reshape(-1)
    return (indices >= start) & (indices <= end)


def evaluate_suffix(
    scores: Iterable[float],
    normal_mask: Iterable[bool],
    eligible_fault_report_masks: Sequence[Iterable[bool]],
    frozen_threshold: float,
) -> SuffixMetrics:
    """Evaluate pointwise normal FPR and duplicate-preserving report recall.

    Every mask is aligned to suffix raw observations. Bounds/interval inclusion
    are represented by caller-provided masks; reports are counted separately,
    including repeated/equal masks. Invalid normal scores are omitted from the
    pointwise FPR denominator. Every report whose interval overlaps at least
    one suffix raw observation remains in the recall denominator even if that
    row has no finite score. Alarms use strict ``score > threshold``.
    """
    if not math.isfinite(float(frozen_threshold)):
        raise ValueError("frozen threshold must be finite")
    values = np.asarray(tuple(scores), dtype=np.float64).reshape(-1)
    normal = np.asarray(tuple(normal_mask), dtype=bool).reshape(-1)
    if values.shape != normal.shape:
        raise ValueError("suffix score and normal mask lengths differ")
    finite = np.isfinite(values)
    normal_rows = normal & finite
    normal_raw_n = int(np.count_nonzero(normal))
    normal_finite_n = int(np.count_nonzero(normal_rows))
    coverage = normal_finite_n / normal_raw_n if normal_raw_n else math.nan
    fpr = (float(np.count_nonzero((values[normal_rows] > frozen_threshold))) / normal_finite_n
           if normal_finite_n else math.nan)
    hits = 0
    reports_n = 0
    for raw_mask in eligible_fault_report_masks:
        mask = np.asarray(tuple(raw_mask), dtype=bool).reshape(-1)
        if mask.shape != values.shape:
            raise ValueError("fault report mask length differs from suffix")
        # An eligible report must overlap at least one suffix observation.
        if not np.any(mask):
            continue
        reports_n += 1
        hits += int(np.any(mask & finite & (values > frozen_threshold)))
    recall = hits / reports_n if reports_n else math.nan
    return SuffixMetrics(fpr, recall, normal_finite_n, reports_n, hits,
                         normal_raw_n, normal_finite_n, coverage)


def acquisition_cost(raw_count: int, elapsed_days: float) -> float:
    """Protocol acquisition cost for a READY task."""
    if raw_count < 0 or not math.isfinite(float(elapsed_days)):
        raise ValueError("invalid acquisition measurements")
    return 0.5 * (raw_count / 2304.0 + elapsed_days / 64.0)


def summarize_candidate(
    candidate: Candidate,
    tasks: Sequence[TaskOutcome],
    *,
    recall_floor: float,
) -> CandidateSummary:
    """Summarize primary joint success and macro tie-break metrics."""
    if not tasks:
        raise ValueError("candidate requires at least one pseudo-target task")
    if (not math.isfinite(recall_floor) or
            recall_floor < PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR):
        raise ValueError("selection thresholds must be finite")
    successes = 0
    costs: list[float] = []
    recalls: list[float] = []
    fprs: list[float] = []
    for task in tasks:
        if task.ready:
            if (task.raw_count not in (288, 576, 1152, 2304) or
                    not 0.0 <= task.elapsed_days <= 64.0):
                raise ValueError("READY task is outside the frozen acquisition budget")
            costs.append(acquisition_cost(task.raw_count, task.elapsed_days))
            recall = task.metrics.eligible_fault_report_recall
            fpr = task.metrics.normal_pointwise_fpr
            if not math.isfinite(recall) or not math.isfinite(fpr):
                raise ValueError("READY task lacks evaluable suffix metrics")
            recalls.append(recall)
            fprs.append(fpr)
            if (task.metrics.normal_scores_evaluable and
                    fpr <= PRIMARY_ABSOLUTE_FPR_CAP and recall >= recall_floor):
                successes += 1
        else:
            costs.append(1.0)
            recalls.append(0.0)
            fprs.append(0.0)
    n = len(tasks)
    return CandidateSummary(
        candidate.candidate_id, successes / n, float(np.mean(costs)),
        float(np.mean(recalls)), float(np.mean(fprs)),
        len(candidate.components), successes, n,
    )


def select_candidate(
    candidates: Sequence[Candidate],
    outcomes: dict[str, Sequence[TaskOutcome]],
    *,
    recall_floor: float,
) -> CandidateSelection:
    """Select the exact protocol lexicographic winner, or fail generically."""
    expected = {candidate.candidate_id: candidate for candidate in enumerate_candidates()}
    ids = [candidate.candidate_id for candidate in candidates]
    if (len(ids) != len(expected) or len(ids) != len(set(ids)) or
            set(ids) != set(expected) or set(outcomes) != set(expected)):
        raise SourceNotEvaluable("SOURCE_MODEL_NOT_EVALUABLE")
    for candidate in candidates:
        frozen = expected[candidate.candidate_id]
        if (candidate.family != frozen.family or dict(candidate.parameters) != dict(frozen.parameters) or
                candidate.components != frozen.components):
            raise SourceNotEvaluable("SOURCE_MODEL_NOT_EVALUABLE")
    counts = {len(outcomes[candidate_id]) for candidate_id in ids}
    if len(counts) != 1 or not counts or next(iter(counts)) < 4:
        raise SourceNotEvaluable("SOURCE_MODEL_NOT_EVALUABLE")
    summaries = tuple(summarize_candidate(c, outcomes[c.candidate_id],
                                          recall_floor=recall_floor)
                      for c in candidates)
    if not summaries or max(s.joint_success_count for s in summaries) == 0:
        raise SourceNotEvaluable("SOURCE_MODEL_NOT_EVALUABLE", summaries=summaries)
    by_id = {s.candidate_id: s for s in summaries}
    winner = min(candidates, key=lambda c: (
        -by_id[c.candidate_id].joint_success_fraction,
        by_id[c.candidate_id].mean_acquisition_cost,
        -by_id[c.candidate_id].macro_fault_report_recall,
        by_id[c.candidate_id].macro_normal_pointwise_fpr,
        len(c.components),
        c.candidate_id,
    ))
    return CandidateSelection(winner, summaries)
