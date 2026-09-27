"""In-memory SOURCE-only P5-0B3 development pipeline.

This module is deliberately a scientific core rather than a data loader.  A
restricted SOURCE process constructs :class:`SourceEntityRows` values from
the already gated operational rows and canonical firewall intervals, then
calls :func:`run_source_stratum`.  No filesystem, archive, manifest, label
table, TensorFlow, or EFD import is performed here.

The implementation keeps row-level arrays in memory for the duration of the
run because they are needed for fold-local fitting and OOF evaluation.  The
returned :class:`PipelineResult.safe_summary` contains only stratum-level
values.  Sensitive row arrays remain available through ``artifacts`` for the
parent writer, but are intentionally omitted by ``safe_summary`` and
``to_safe_dict``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import math
from typing import Callable, Mapping, Sequence

import numpy as np

try:  # Package import from the project root.
    from .preprocessing import MedianImputeStandardScaler
    from .readiness import Candidate as ReadinessCandidate
    from .readiness import Trajectory, enumerate_candidates, evaluate_grid
    from .source_detector import (
        Candidate as DetectorCandidate,
        SourceStratumError,
        annotation_clean_mask,
        candidate_grid,
        fold_assignments,
        midpoint_indices,
        ordered_capped_rows,
        select_candidate as select_detector_candidate,
        semantic_labels,
        support_row_mask,
        train_candidate,
    )
    from .source_evaluator import (
        CandidateSummary as ReadinessCandidateSummary,
        CandidateSelection,
        SuffixMetrics,
        TaskOutcome,
        SourceNotEvaluable,
        effective_recall_floor,
        evaluate_suffix,
        fixed_n_threshold,
        select_candidate as select_readiness_candidate,
        source_fixed_n_baselines,
        type7_quantile,
    )
except ImportError:  # ``scripts`` directory placed directly on sys.path.
    from preprocessing import MedianImputeStandardScaler
    from readiness import Candidate as ReadinessCandidate
    from readiness import Trajectory, enumerate_candidates, evaluate_grid
    from source_detector import (
        Candidate as DetectorCandidate,
        SourceStratumError,
        annotation_clean_mask,
        candidate_grid,
        fold_assignments,
        midpoint_indices,
        ordered_capped_rows,
        select_candidate as select_detector_candidate,
        semantic_labels,
        support_row_mask,
        train_candidate,
    )
    from source_evaluator import (
        CandidateSummary as ReadinessCandidateSummary,
        CandidateSelection,
        SuffixMetrics,
        TaskOutcome,
        SourceNotEvaluable,
        effective_recall_floor,
        evaluate_suffix,
        fixed_n_threshold,
        select_candidate as select_readiness_candidate,
        source_fixed_n_baselines,
        type7_quantile,
    )


# These are protocol constants.  They are intentionally not configurable by
# the production entry point, so a source result cannot silently drift to a
# different support, look, or fit budget.
SOURCE_ENTITY_MINIMUM = 6
FIT_ENTITY_MINIMUM = 4
FIT_ROW_MINIMUM = 1024
ENTITY_ROW_MINIMUM = 256
SOURCE_ROW_CAP = 8192
OUTER_FOLD_COUNT = 5
PREFIX_ROWS = 2304
MAX_ELAPSED_DAYS = 64.0
SCORE_REPEAT_ATOL = 1e-7
SCORE_REPEAT_RTOL = 1e-7
IQR_MINIMUM = 1e-12
PSEUDO_TARGET_MINIMUM = 4

_INTERVAL_KINDS = frozenset({
    "KNOWN_FAULT",
    "REFERENCE_NORMAL_EVENT",
    "DISTURBANCE_FAULT",
    "DISTURBANCE_OTHER",
})
_INTERVAL_SOURCES = frozenset({"faults", "normal_events", "disturbances"})
_KIND_SOURCE = {
    "KNOWN_FAULT": "faults",
    "REFERENCE_NORMAL_EVENT": "normal_events",
    "DISTURBANCE_FAULT": "disturbances",
    "DISTURBANCE_OTHER": "disturbances",
}


class SourcePipelineError(ValueError):
    """Generic stratum-scoped error with no row, entity, or value detail."""

    def __init__(self, code: str = "SOURCE_MODEL_NOT_EVALUABLE") -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class CanonicalSourceInterval:
    """One row from the canonical SOURCE firewall artifact.

    ``role_digest`` is optional for callers that attach intervals to the
    corresponding entity object.  When present it is checked against that
    entity before use.  The canonical artifact's source/kind pairing is
    validated and timestamps remain naive local datetimes.
    """

    annotation_source: str
    annotation_kind: str
    interval_start: datetime
    interval_end: datetime
    role_digest: str | None = None

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, object],
        *,
        expected_role_digest: str | None = None,
    ) -> "CanonicalSourceInterval":
        try:
            item = cls(
                annotation_source=str(value["annotation_source"]),
                annotation_kind=str(value["annotation_kind"]),
                interval_start=value["interval_start"],  # type: ignore[arg-type]
                interval_end=value["interval_end"],  # type: ignore[arg-type]
                role_digest=(str(value["role_digest"])
                             if "role_digest" in value and value["role_digest"] is not None
                             else None),
            )
        except Exception as exc:
            raise SourcePipelineError() from exc
        item._validate(expected_role_digest=expected_role_digest)
        return item

    def _validate(self, *, expected_role_digest: str | None = None) -> None:
        try:
            if self.annotation_source not in _INTERVAL_SOURCES:
                raise ValueError
            if self.annotation_kind not in _INTERVAL_KINDS:
                raise ValueError
            if _KIND_SOURCE[self.annotation_kind] != self.annotation_source:
                raise ValueError
            if not isinstance(self.interval_start, datetime) or not isinstance(self.interval_end, datetime):
                raise ValueError
            if (self.interval_start.tzinfo is not None and self.interval_start.utcoffset() is not None) or (
                self.interval_end.tzinfo is not None and self.interval_end.utcoffset() is not None
            ) or self.interval_end < self.interval_start:
                raise ValueError
            if self.role_digest is not None and expected_role_digest is not None:
                if self.role_digest != expected_role_digest:
                    raise ValueError
        except Exception as exc:
            raise SourcePipelineError() from exc


@dataclass(frozen=True)
class SourceEntityRows:
    """Projected rows and canonical annotations for one SOURCE role digest.

    ``features`` is a two-dimensional float64 matrix in the frozen projected
    feature order.  ``timestamps`` and all validity/index arrays retain raw
    row alignment.  Invalid measurement rows may be represented by NaNs; an
    all-NaN row is never a support row.  Arrays are copied on construction so
    a caller cannot mutate data while a fold is being fitted.
    """

    role_digest: str
    features: np.ndarray = field(repr=False)
    timestamps: tuple[datetime | None, ...] = field(repr=False)
    timestamp_valid: np.ndarray | None = field(default=None, repr=False)
    measurement_valid: np.ndarray | None = field(default=None, repr=False)
    raw_row_indices: np.ndarray | None = field(default=None, repr=False)
    intervals: tuple[CanonicalSourceInterval | Mapping[str, object], ...] = field(
        default_factory=tuple, repr=False
    )

    def __post_init__(self) -> None:
        try:
            if not isinstance(self.role_digest, str) or not self.role_digest:
                raise ValueError
            matrix = np.array(self.features, dtype=np.float64, copy=True)
            if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
                raise ValueError
            if np.isinf(matrix).any():
                raise ValueError
            stamps = tuple(self.timestamps)
            n = matrix.shape[0]
            if len(stamps) != n:
                raise ValueError
            derived_timestamp_valid = np.asarray(
                [_valid_naive_timestamp(stamp) for stamp in stamps], dtype=bool
            )
            if self.timestamp_valid is None:
                timestamp_valid = derived_timestamp_valid
            else:
                timestamp_valid = np.asarray(self.timestamp_valid, dtype=bool).reshape(-1)
                if timestamp_valid.size != n:
                    raise ValueError
                timestamp_valid = timestamp_valid & derived_timestamp_valid
            support = support_row_mask(matrix)
            if self.measurement_valid is None:
                measurement_valid = support
            else:
                measurement_valid = np.asarray(self.measurement_valid, dtype=bool).reshape(-1)
                if measurement_valid.size != n:
                    raise ValueError
                measurement_valid = measurement_valid & support
            if self.raw_row_indices is None:
                raw_indices = np.arange(n, dtype=np.int64)
            else:
                raw_indices = np.asarray(self.raw_row_indices, dtype=np.int64).reshape(-1)
                if raw_indices.size != n:
                    raise ValueError
            if np.any(raw_indices < 0) or len(set(raw_indices.tolist())) != n:
                raise ValueError
            normalized = tuple(
                item if isinstance(item, CanonicalSourceInterval)
                else CanonicalSourceInterval.from_mapping(
                    item, expected_role_digest=self.role_digest
                )
                for item in self.intervals
            )
            for item in normalized:
                item._validate(expected_role_digest=self.role_digest)
        except SourcePipelineError:
            raise
        except Exception as exc:
            raise SourcePipelineError() from exc
        object.__setattr__(self, "features", matrix)
        object.__setattr__(self, "timestamps", stamps)
        object.__setattr__(self, "timestamp_valid", timestamp_valid)
        object.__setattr__(self, "measurement_valid", measurement_valid)
        object.__setattr__(self, "raw_row_indices", raw_indices)
        object.__setattr__(self, "intervals", normalized)


@dataclass(frozen=True)
class FoldPlan:
    """Deterministic source entity fold assignment and support counts."""

    assignments: Mapping[str, int]
    support_counts: Mapping[str, int]
    fit_entity_counts: tuple[int, ...]
    fit_row_counts: tuple[int, ...]


@dataclass(frozen=True)
class SafeDetectorMetric:
    candidate_id: str
    macro_ap: float
    macro_auroc: float


@dataclass(frozen=True)
class SafeReadinessMetric:
    candidate_id: str
    joint_success_fraction: float
    mean_acquisition_cost: float
    macro_fault_report_recall: float
    macro_normal_pointwise_fpr: float
    conjunct_count: int
    joint_success_count: int
    task_count: int


@dataclass(frozen=True)
class SourcePipelineSummary:
    """Value-safe seal values for one exact source stratum."""

    status: str
    source_entity_count: int
    selected_detector_id: str
    selected_readiness_id: str
    common_heldout_entity_count: int
    iqr_source: float
    recall_min_source_q10: float
    recall_min_effective: float
    fpr_q90_source_fixed_n_diagnostic: float
    fold_fit_entity_counts: tuple[int, ...]
    fold_fit_row_counts: tuple[int, ...]
    detector_metrics: tuple[SafeDetectorMetric, ...]
    readiness_metrics: tuple[SafeReadinessMetric, ...]
    oof_score_hash: str
    final_score_hash: str
    final_preprocessor_hash: str
    invalid_score_row_count: int

    def to_safe_dict(self) -> dict[str, object]:
        """Return a JSON-safe summary without row/entity artifacts."""
        return {
            "status": self.status,
            "source_entity_count": self.source_entity_count,
            "selected_detector_id": self.selected_detector_id,
            "selected_readiness_id": self.selected_readiness_id,
            "common_heldout_entity_count": self.common_heldout_entity_count,
            "iqr_source": self.iqr_source,
            "recall_min_source_q10": self.recall_min_source_q10,
            "recall_min_effective": self.recall_min_effective,
            "fpr_q90_source_fixed_n_diagnostic": self.fpr_q90_source_fixed_n_diagnostic,
            "fold_fit_entity_counts": list(self.fold_fit_entity_counts),
            "fold_fit_row_counts": list(self.fold_fit_row_counts),
            "detector_metrics": [
                {
                    "candidate_id": metric.candidate_id,
                    "macro_ap": metric.macro_ap,
                    "macro_auroc": metric.macro_auroc,
                }
                for metric in self.detector_metrics
            ],
            "readiness_metrics": [
                {
                    "candidate_id": metric.candidate_id,
                    "joint_success_fraction": metric.joint_success_fraction,
                    "mean_acquisition_cost": metric.mean_acquisition_cost,
                    "macro_fault_report_recall": metric.macro_fault_report_recall,
                    "macro_normal_pointwise_fpr": metric.macro_normal_pointwise_fpr,
                    "conjunct_count": metric.conjunct_count,
                    "joint_success_count": metric.joint_success_count,
                    "task_count": metric.task_count,
                }
                for metric in self.readiness_metrics
            ],
            "oof_score_hash": self.oof_score_hash,
            "final_score_hash": self.final_score_hash,
            "final_preprocessor_hash": self.final_preprocessor_hash,
            "invalid_score_row_count": self.invalid_score_row_count,
            "invalid_score_reason": "INVALID_SCORE_ROW",
        }


@dataclass(frozen=True)
class SourceScoreArtifacts:
    """In-memory score/model artifacts for the parent writer.

    These mappings intentionally have no serializer.  ``SourcePipelineSummary``
    carries only hashes and aggregate counts; callers that need row-level
    values must use this object inside the restricted SOURCE process.
    """

    oof_scores_by_candidate: Mapping[str, Mapping[str, np.ndarray]]
    selected_oof_scores: Mapping[str, np.ndarray]
    final_scores: Mapping[str, np.ndarray]
    trajectories: Mapping[str, Mapping[str, Trajectory]]


@dataclass(frozen=True)
class PipelineResult:
    summary: SourcePipelineSummary
    final_model: object
    final_preprocessor: MedianImputeStandardScaler
    selected_detector: DetectorCandidate
    selected_readiness: ReadinessCandidate
    artifacts: SourceScoreArtifacts

    @property
    def safe_summary(self) -> dict[str, object]:
        return self.summary.to_safe_dict()


def _valid_naive_timestamp(value: object) -> bool:
    return isinstance(value, datetime) and not (
        value.tzinfo is not None and value.utcoffset() is not None
    )


def _normalise_intervals(entity: SourceEntityRows) -> tuple[CanonicalSourceInterval, ...]:
    try:
        result = []
        for interval in entity.intervals:
            item = (interval if isinstance(interval, CanonicalSourceInterval)
                    else CanonicalSourceInterval.from_mapping(
                        interval, expected_role_digest=entity.role_digest
                    ))
            item._validate(expected_role_digest=entity.role_digest)
            result.append(item)
        return tuple(result)
    except SourcePipelineError:
        raise
    except Exception as exc:
        raise SourcePipelineError() from exc


def _annotation_masks(entity: SourceEntityRows) -> tuple[np.ndarray, ...]:
    """Return known, reference-normal, disturbance-fault, disturbance-other."""
    n = len(entity.timestamps)
    masks = {kind: np.zeros(n, dtype=bool) for kind in _INTERVAL_KINDS}
    intervals = _normalise_intervals(entity)
    for interval in intervals:
        for index, stamp in enumerate(entity.timestamps):
            if (entity.timestamp_valid[index] and _valid_naive_timestamp(stamp)
                    and interval.interval_start <= stamp <= interval.interval_end):
                masks[interval.annotation_kind][index] = True
    return (
        masks["KNOWN_FAULT"],
        masks["REFERENCE_NORMAL_EVENT"],
        masks["DISTURBANCE_FAULT"],
        masks["DISTURBANCE_OTHER"],
    )


def _effective_support_mask(entity: SourceEntityRows) -> np.ndarray:
    return (
        np.asarray(entity.timestamp_valid, dtype=bool)
        & np.asarray(entity.measurement_valid, dtype=bool)
        & support_row_mask(entity.features)
    )


def _clean_fit_mask(entity: SourceEntityRows) -> np.ndarray:
    known, _, disturbance_fault, disturbance_other = _annotation_masks(entity)
    return _effective_support_mask(entity) & annotation_clean_mask(
        known, disturbance_fault, disturbance_other
    )


def _validate_entities(entities: Sequence[SourceEntityRows]) -> int:
    try:
        if not entities or len({entity.role_digest for entity in entities}) != len(entities):
            raise ValueError
        dimensions = {entity.features.shape[1] for entity in entities}
        if len(dimensions) != 1:
            raise ValueError
        return next(iter(dimensions))
    except Exception as exc:
        raise SourcePipelineError() from exc


def capped_clean_indices(entity: SourceEntityRows, cap: int = SOURCE_ROW_CAP) -> np.ndarray:
    """Return chronological clean SOURCE rows after the per-entity midpoint cap."""
    if cap != SOURCE_ROW_CAP or cap < 1:
        raise SourcePipelineError()
    try:
        mask = _clean_fit_mask(entity)
        selected = np.flatnonzero(mask).tolist()
        selected.sort(key=lambda index: (entity.timestamps[index], entity.raw_row_indices[index]))
        selected = [selected[index] for index in midpoint_indices(len(selected), cap)]
        return np.asarray(selected, dtype=np.int64)
    except SourcePipelineError:
        raise
    except Exception as exc:
        raise SourcePipelineError() from exc


def _fold_plan_details(entities: Sequence[SourceEntityRows]) -> FoldPlan:
    """Build value-free fold support details without applying the gates."""
    dimension = _validate_entities(entities)
    del dimension  # validation is intentionally retained for the caller contract.
    try:
        assignments = fold_assignments(
            [entity.role_digest for entity in entities],
            lambda payload: hashlib.sha256(payload).hexdigest(),
        )
        support_counts = {
            entity.role_digest: int(np.count_nonzero(_clean_fit_mask(entity)))
            for entity in entities
        }
        fit_entity_counts = []
        fit_row_counts = []
        for fold in range(OUTER_FOLD_COUNT):
            fit_entities = [
                entity for entity in entities if assignments[entity.role_digest] != fold
            ]
            usable = [
                entity for entity in fit_entities
                if support_counts[entity.role_digest] >= ENTITY_ROW_MINIMUM
            ]
            rows = sum(support_counts[entity.role_digest] for entity in usable)
            fit_entity_counts.append(len(usable))
            fit_row_counts.append(rows)
        return FoldPlan(assignments, support_counts,
                        tuple(fit_entity_counts), tuple(fit_row_counts))
    except SourcePipelineError:
        raise
    except Exception as exc:
        raise SourcePipelineError() from exc


def _fold_plan_audit(plan: FoldPlan, entities: Sequence[SourceEntityRows]) -> dict[str, object]:
    return {
        "source_entity_count": len(entities),
        "source_entity_minimum": SOURCE_ENTITY_MINIMUM,
        "fold_assignments": dict(sorted(plan.assignments.items())),
        "entity_clean_fit_rows": dict(sorted(plan.support_counts.items())),
        "entity_clean_fit_row_minimum": ENTITY_ROW_MINIMUM,
        "fold_fit_entity_minimum": FIT_ENTITY_MINIMUM,
        "fold_fit_row_minimum": FIT_ROW_MINIMUM,
        "folds": [
            {
                "fold": index,
                "heldout_entity_count": sum(value == index for value in plan.assignments.values()),
                "fit_usable_entity_count": plan.fit_entity_counts[index],
                "fit_clean_row_count": plan.fit_row_counts[index],
                "status": "PASS" if (plan.fit_entity_counts[index] >= FIT_ENTITY_MINIMUM
                                      and plan.fit_row_counts[index] >= FIT_ROW_MINIMUM)
                else "FAIL",
            }
            for index in range(OUTER_FOLD_COUNT)
        ],
    }


def build_fold_plan(entities: Sequence[SourceEntityRows]) -> FoldPlan:
    """Assign exact-stratum entities and enforce every protocol support gate."""
    if len(entities) < SOURCE_ENTITY_MINIMUM:
        raise SourcePipelineError()
    plan = _fold_plan_details(entities)
    if any(fit_entities < FIT_ENTITY_MINIMUM or fit_rows < FIT_ROW_MINIMUM
           for fit_entities, fit_rows in zip(plan.fit_entity_counts, plan.fit_row_counts)):
        raise SourcePipelineError()
    return plan


def _labels_for_entity(entity: SourceEntityRows) -> np.ndarray:
    known, normal, disturbance_fault, disturbance_other = _annotation_masks(entity)
    labels = semantic_labels(known, normal, disturbance_fault, disturbance_other)
    valid = _effective_support_mask(entity)
    labels[~valid] = -1
    return labels


def _stack_fit_rows(
    entities: Sequence[SourceEntityRows],
    assignments: Mapping[str, int],
    heldout_fold: int,
) -> tuple[np.ndarray, tuple[SourceEntityRows, ...], tuple[np.ndarray, ...]]:
    """Build deterministic capped fit rows and heldout score row segments."""
    fit_entities = [
        entity for entity in entities
        if assignments[entity.role_digest] != heldout_fold
        and int(np.count_nonzero(_clean_fit_mask(entity))) >= ENTITY_ROW_MINIMUM
    ]
    role_values: list[str] = []
    timestamps: list[datetime] = []
    raw_indices: list[int] = []
    rows: list[np.ndarray] = []
    for entity in fit_entities:
        indices = capped_clean_indices(entity)
        for index in indices.tolist():
            role_values.append(entity.role_digest)
            timestamps.append(entity.timestamps[index])  # type: ignore[arg-type]
            raw_indices.append(int(entity.raw_row_indices[index]))
            rows.append(entity.features[index])
    if not rows:
        raise SourcePipelineError()
    pooled = np.asarray(rows, dtype=np.float64)
    # ``ordered_capped_rows`` is the single ordering implementation used by
    # the protocol.  It receives rows already reduced to capped clean rows.
    ordered = ordered_capped_rows(
        pooled, role_values, timestamps, raw_indices,
        np.ones(len(rows), dtype=bool), cap=SOURCE_ROW_CAP,
    )
    fit_rows = pooled[ordered]

    heldout = tuple(sorted(
        (entity for entity in entities if assignments[entity.role_digest] == heldout_fold),
        key=lambda entity: entity.role_digest,
    ))
    heldout_indices = tuple(
        np.flatnonzero(_effective_support_mask(entity)).astype(np.int64)
        for entity in heldout
    )
    return fit_rows, heldout, heldout_indices


def _prediction_scores(model: object, model_input: np.ndarray) -> np.ndarray:
    try:
        reconstruction = np.asarray(model.predict(model_input, verbose=0), dtype=np.float64)
        values = np.asarray(model_input, dtype=np.float32)
    except Exception as exc:
        raise SourcePipelineError() from exc
    if reconstruction.shape != values.shape:
        raise SourcePipelineError("BACKBONE_NOT_ADMISSIBLE")
    try:
        scores = np.sqrt(np.mean((values.astype(np.float64) - reconstruction) ** 2, axis=1))
        scores[~np.isfinite(scores)] = np.nan
        return scores
    except Exception as exc:
        raise SourcePipelineError() from exc


def _transform_scoring_rows(
    preprocessor: MedianImputeStandardScaler, rows: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Transform score rows independently; invalid rows remain NaN, value-free."""
    values = np.asarray(rows, dtype=np.float64)
    transformed = np.full(values.shape, np.nan, dtype=np.float32)
    if (preprocessor.medians_ is None or preprocessor.means_ is None
            or preprocessor.scales_ is None or values.ndim != 2
            or values.shape[1] != preprocessor.medians_.size):
        raise SourcePipelineError()
    valid = (~np.isinf(values).any(axis=1) & ~np.isnan(values).all(axis=1))
    candidates = np.flatnonzero(valid)
    if candidates.size:
        imputed = values[candidates].copy()
        missing_rows, missing_cols = np.where(np.isnan(imputed))
        imputed[missing_rows, missing_cols] = preprocessor.medians_[missing_cols]
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            scaled = (imputed - preprocessor.means_) / preprocessor.scales_
            cast = scaled.astype(np.float32)
        row_finite = np.isfinite(scaled).all(axis=1) & np.isfinite(cast).all(axis=1)
        valid[candidates[~row_finite]] = False
        transformed[candidates[row_finite]] = cast[row_finite]
    # Invalid rows are represented only by NaN and a Boolean mask; no raw
    # values or exception text are retained.
    return transformed, valid


def _fit_and_score_valid_rows(
    model_factory: Callable[..., object], candidate: DetectorCandidate,
    fit_rows: np.ndarray, transformed: np.ndarray, valid: np.ndarray,
    seed_fn: Callable[[int], None],
) -> tuple[object, np.ndarray]:
    scores = np.full(len(transformed), np.nan, dtype=np.float64)
    if not np.any(valid):
        raise SourcePipelineError()
    model, finite_scores = train_candidate(
        model_factory, candidate, fit_rows.copy(), transformed[valid].copy(), seed_fn
    )
    scores[valid] = finite_scores
    return model, scores


def _repeat_fit_candidate(
    model_factory: Callable[..., object],
    candidate: DetectorCandidate,
    fit_rows: np.ndarray,
    score_rows: np.ndarray,
    seed_fn: Callable[[int], None],
) -> tuple[object, np.ndarray, MedianImputeStandardScaler]:
    """Fit a fold/config twice and enforce the frozen repeatability gate."""
    try:
        first_preprocessor = MedianImputeStandardScaler().fit(fit_rows)
        first_fit = first_preprocessor.transform(fit_rows)
        first_score, first_valid = _transform_scoring_rows(first_preprocessor, score_rows)
        second_preprocessor = MedianImputeStandardScaler().fit(fit_rows)
        second_fit = second_preprocessor.transform(fit_rows)
        second_score, second_valid = _transform_scoring_rows(second_preprocessor, score_rows)
        exact_arrays = (
            first_fit.dtype == second_fit.dtype
            and first_score.dtype == second_score.dtype
            and first_fit.shape == second_fit.shape
            and first_score.shape == second_score.shape
            and first_fit.tobytes() == second_fit.tobytes()
            and first_valid.tobytes() == second_valid.tobytes()
            and first_score.tobytes() == second_score.tobytes()
            and first_preprocessor.medians_.tobytes() == second_preprocessor.medians_.tobytes()
            and first_preprocessor.means_.tobytes() == second_preprocessor.means_.tobytes()
            and first_preprocessor.scales_.tobytes() == second_preprocessor.scales_.tobytes()
        )
        if not exact_arrays:
            raise SourcePipelineError("BACKBONE_NOT_ADMISSIBLE")
        first_model, first_scores = _fit_and_score_valid_rows(
            model_factory, candidate, first_fit, first_score, first_valid, seed_fn
        )
        _, second_scores = _fit_and_score_valid_rows(
            model_factory, candidate, second_fit, second_score, second_valid, seed_fn
        )
        if (first_scores.shape != second_scores.shape
                or not np.array_equal(np.isnan(first_scores), np.isnan(second_scores))
                or not np.isfinite(first_scores[np.isfinite(first_scores)]).all()
                or not np.isfinite(second_scores[np.isfinite(second_scores)]).all()
                or not np.allclose(
                    first_scores, second_scores,
                    atol=SCORE_REPEAT_ATOL, rtol=SCORE_REPEAT_RTOL,
                    equal_nan=True,
                )):
            raise SourcePipelineError("BACKBONE_NOT_ADMISSIBLE")
        return first_model, first_scores, first_preprocessor
    except SourcePipelineError:
        raise
    except SourceStratumError as exc:
        if exc.code == "BACKBONE_NOT_ADMISSIBLE":
            raise SourcePipelineError("BACKBONE_NOT_ADMISSIBLE") from exc
        raise SourcePipelineError() from exc
    except Exception as exc:
        raise SourcePipelineError() from exc


def _score_oof_candidates(
    entities: Sequence[SourceEntityRows],
    plan: FoldPlan,
    candidates: Sequence[DetectorCandidate],
    model_factory: Callable[..., object],
    seed_fn: Callable[[int], None],
) -> dict[str, dict[str, np.ndarray]]:
    result = {
        candidate.candidate_id: {
            entity.role_digest: np.full(len(entity.timestamps), np.nan, dtype=np.float64)
            for entity in entities
        }
        for candidate in candidates
    }
    for fold in range(OUTER_FOLD_COUNT):
        fit_rows, heldout, heldout_indices = _stack_fit_rows(
            entities, plan.assignments, fold
        )
        if not heldout:
            continue
        score_blocks = [
            entity.features[indices]
            for entity, indices in zip(heldout, heldout_indices)
        ]
        if any(block.ndim != 2 or len(block) == 0 for block in score_blocks):
            raise SourcePipelineError()
        score_rows = np.vstack(score_blocks)
        offsets: list[tuple[str, np.ndarray, int, int]] = []
        start = 0
        for entity, indices in zip(heldout, heldout_indices):
            end = start + len(indices)
            offsets.append((entity.role_digest, indices, start, end))
            start = end
        for candidate in candidates:
            model, scores, _ = _repeat_fit_candidate(
                model_factory, candidate, fit_rows, score_rows, seed_fn
            )
            del model  # The final selected fit is the only retained model.
            if len(scores) != len(score_rows):
                raise SourcePipelineError()
            for role_digest, indices, begin, end in offsets:
                result[candidate.candidate_id][role_digest][indices] = scores[begin:end]
    return result


def _score_hash(score_map: Mapping[str, np.ndarray]) -> str:
    digest = hashlib.sha256()
    for role_digest in sorted(score_map):
        values = np.ascontiguousarray(np.asarray(score_map[role_digest], dtype=np.float64))
        digest.update(role_digest.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(values.shape).encode("ascii"))
        digest.update(b"\0")
        digest.update(values.tobytes())
    return digest.hexdigest()


def _preprocessor_hash(preprocessor: MedianImputeStandardScaler) -> str:
    try:
        digest = hashlib.sha256()
        for values in (preprocessor.medians_, preprocessor.means_, preprocessor.scales_):
            array = np.ascontiguousarray(np.asarray(values, dtype=np.float64))
            digest.update(array.tobytes())
        return digest.hexdigest()
    except Exception as exc:
        raise SourcePipelineError() from exc


def _source_iqr(
    entities: Sequence[SourceEntityRows],
    selected_scores: Mapping[str, np.ndarray],
) -> float:
    values: list[float] = []
    for entity in entities:
        clean = _clean_fit_mask(entity)
        scores = np.asarray(selected_scores[entity.role_digest], dtype=np.float64)
        values.extend(scores[clean & np.isfinite(scores)].tolist())
    if not values:
        raise SourcePipelineError()
    q25 = type7_quantile(values, 0.25)
    q75 = type7_quantile(values, 0.75)
    iqr = q75 - q25
    if not math.isfinite(iqr) or iqr <= IQR_MINIMUM:
        raise SourcePipelineError()
    return float(iqr)


@dataclass(frozen=True)
class _PseudoTargetInfo:
    entity: SourceEntityRows = field(repr=False)
    scores: np.ndarray = field(repr=False)
    suffix_scores: np.ndarray = field(repr=False)
    suffix_normal_mask: np.ndarray = field(repr=False)
    suffix_report_masks: tuple[np.ndarray, ...] = field(repr=False)


def _report_masks_for_suffix(
    entity: SourceEntityRows,
    suffix_timestamps: Sequence[datetime | None],
) -> tuple[np.ndarray, ...]:
    masks: list[np.ndarray] = []
    for interval in _normalise_intervals(entity):
        if interval.annotation_kind != "KNOWN_FAULT":
            continue
        mask = np.asarray([
            _valid_naive_timestamp(stamp)
            and interval.interval_start <= stamp <= interval.interval_end
            for stamp in suffix_timestamps
        ], dtype=bool)
        if np.any(mask):
            masks.append(mask)
    return tuple(masks)


def _pseudo_target_info(
    entity: SourceEntityRows,
    scores: np.ndarray,
    reason_sink: list[str] | None = None,
) -> _PseudoTargetInfo | None:
    """Apply every fixed SOURCE pseudo-target eligibility gate."""
    def reject(reason: str):
        if reason_sink is not None:
            reason_sink.append(reason)
        return None

    try:
        n = len(entity.timestamps)
        if n <= PREFIX_ROWS or len(scores) != n:
            return reject("row_count_or_score_alignment")
        prefix_stamps = entity.timestamps[:PREFIX_ROWS]
        if (not entity.timestamp_valid[0]
                or any(not entity.timestamp_valid[index] for index in range(PREFIX_ROWS))):
            return reject("invalid_prefix_timestamp")
        if any(prefix_stamps[index] > prefix_stamps[index + 1]
               for index in range(PREFIX_ROWS - 1)):
            return reject("decreasing_prefix_timestamp")
        elapsed = (prefix_stamps[-1] - prefix_stamps[0]).total_seconds() / 86400.0
        if not math.isfinite(elapsed) or elapsed > MAX_ELAPSED_DAYS or elapsed < 0:
            return reject("prefix_elapsed_out_of_range")
        known, _, disturbance_fault, disturbance_other = _annotation_masks(entity)
        if np.any(known[:PREFIX_ROWS] | disturbance_fault[:PREFIX_ROWS]
                  | disturbance_other[:PREFIX_ROWS]):
            return reject("prefix_not_annotation_clean")
        prefix_scores = np.asarray(scores[:PREFIX_ROWS], dtype=np.float64)
        if np.count_nonzero(np.isfinite(prefix_scores)) < 200:
            return reject("insufficient_finite_prefix_scores")
        suffix_stamps = entity.timestamps[PREFIX_ROWS:]
        if not suffix_stamps or any(not entity.timestamp_valid[index]
                                    for index in range(PREFIX_ROWS, n)):
            return reject("invalid_suffix_timestamp")
        if any(suffix_stamps[index] > suffix_stamps[index + 1]
               for index in range(len(suffix_stamps) - 1)):
            return reject("decreasing_suffix_timestamp")
        if suffix_stamps and prefix_stamps[-1] > suffix_stamps[0]:
            return reject("decreasing_prefix_suffix_boundary")
        suffix_scores = np.asarray(scores[PREFIX_ROWS:], dtype=np.float64)
        normal = _annotation_masks(entity)[1][PREFIX_ROWS:]
        dirty = (known | disturbance_fault | disturbance_other)[PREFIX_ROWS:]
        suffix_normal = normal & ~dirty & np.isfinite(suffix_scores)
        if np.count_nonzero(suffix_normal) < 100:
            return reject("insufficient_finite_normal_suffix_scores")
        report_masks = _report_masks_for_suffix(entity, suffix_stamps)
        if len(report_masks) < 1:
            return reject("no_eligible_fault_report")
        if reason_sink is not None:
            reason_sink.append("eligible")
        return _PseudoTargetInfo(
            entity=entity,
            scores=np.asarray(scores, dtype=np.float64),
            suffix_scores=suffix_scores,
            suffix_normal_mask=suffix_normal,
            suffix_report_masks=report_masks,
        )
    except Exception as exc:
        if reason_sink is not None:
            reason_sink.append("internal_eligibility_error")
        raise SourcePipelineError() from exc


def _elapsed_at_look(entity: SourceEntityRows, look: int) -> float:
    try:
        elapsed = (entity.timestamps[look - 1] - entity.timestamps[0]).total_seconds() / 86400.0
        if not math.isfinite(elapsed) or elapsed < 0 or elapsed > MAX_ELAPSED_DAYS:
            raise ValueError
        return float(elapsed)
    except Exception as exc:
        raise SourcePipelineError() from exc


def _suffix_metrics(info: _PseudoTargetInfo, threshold: float) -> SuffixMetrics:
    try:
        return evaluate_suffix(
            info.suffix_scores,
            info.suffix_normal_mask,
            info.suffix_report_masks,
            threshold,
        )
    except Exception as exc:
        raise SourcePipelineError() from exc


def _readiness_selection(
    entities: Sequence[SourceEntityRows],
    selected_oof_scores: Mapping[str, np.ndarray],
    iqr_source: float,
    diagnostics: dict[str, object] | None = None,
) -> tuple[CandidateSelection, Mapping[str, Mapping[str, Trajectory]], float, float, float]:
    """Seal trajectories first, then evaluate suffixes and select readiness."""
    infos: list[_PseudoTargetInfo] = []
    eligibility_counts: dict[str, int] = {}
    eligible_digests: list[str] = []
    for entity in sorted(entities, key=lambda item: item.role_digest):
        reason: list[str] = []
        info = _pseudo_target_info(
            entity, np.asarray(selected_oof_scores[entity.role_digest], dtype=np.float64), reason
        )
        if info is not None:
            infos.append(info)
            eligible_digests.append(entity.role_digest)
        for item in reason:
            eligibility_counts[item] = eligibility_counts.get(item, 0) + 1
    if diagnostics is not None:
        diagnostics["pseudo_target_eligibility"] = {
            "minimum_required": PSEUDO_TARGET_MINIMUM,
            "eligible_count": len(infos),
            "eligible_role_digests": eligible_digests,
            "exclusion_reason_counts": eligibility_counts,
        }
    if len(infos) < PSEUDO_TARGET_MINIMUM:
        raise SourcePipelineError()

    prefixes = {
        info.entity.role_digest: {
            look: info.scores[:look]
            for look in (144, 288, 576, 1152, 2304)
        }
        for info in infos
    }
    trajectories: dict[str, dict[str, Trajectory]] = {}
    for info in infos:
        trajectories[info.entity.role_digest] = {
            trajectory.candidate_id: trajectory
            for trajectory in evaluate_grid(
                prefixes[info.entity.role_digest], iqr_source=iqr_source
            )
        }
    if diagnostics is not None:
        diagnostics["readiness_trajectories"] = [
            {
                "role_digest": role_digest,
                "candidate_id": candidate_id,
                "ready_look": trajectory.ready_look,
                "frozen_threshold": trajectory.frozen_threshold,
                "looks": [
                    {
                        "raw_look": look.raw_look,
                        "supported": look.supported,
                        "ready": look.ready,
                        "threshold": look.threshold,
                        "statistic": look.statistic,
                        "run_length": look.run_length,
                    }
                    for look in trajectory.results
                ],
            }
            for role_digest, by_candidate in sorted(trajectories.items())
            for candidate_id, trajectory in sorted(by_candidate.items())
        ]
    # No suffix evaluator is called before the complete trajectory store above
    # has been constructed for every eligible pseudo-target entity.
    fixed_metrics: list[SuffixMetrics] = []
    outcomes: dict[str, list[TaskOutcome]] = {
        candidate.candidate_id: []
        for candidate in enumerate_candidates()
    }
    for info in infos:
        fixed_threshold = fixed_n_threshold(info.scores[:PREFIX_ROWS])
        if not math.isfinite(fixed_threshold):
            raise SourcePipelineError()
        fixed_metrics.append(_suffix_metrics(info, fixed_threshold))
    recall_q10, fpr_q90 = source_fixed_n_baselines(fixed_metrics)
    recall_floor = effective_recall_floor(recall_q10)
    if not math.isfinite(recall_floor):
        raise SourcePipelineError()
    readiness_grid = enumerate_candidates()
    task_audit: list[dict[str, object]] = []
    for info in infos:
        for candidate in readiness_grid:
            trajectory = trajectories[info.entity.role_digest][candidate.candidate_id]
            if trajectory.ready_look is None or trajectory.frozen_threshold is None:
                outcome = TaskOutcome(False, SuffixMetrics(math.nan, math.nan, 0, 0, 0))
            else:
                metrics = _suffix_metrics(info, trajectory.frozen_threshold)
                outcome = TaskOutcome(
                    True,
                    metrics,
                    trajectory.ready_look,
                    _elapsed_at_look(info.entity, trajectory.ready_look),
                )
            outcomes[candidate.candidate_id].append(outcome)
            metric = outcome.metrics
            task_audit.append({
                "role_digest": info.entity.role_digest,
                "candidate_id": candidate.candidate_id,
                "ready": outcome.ready,
                "raw_count": outcome.raw_count if outcome.ready else None,
                "elapsed_days": outcome.elapsed_days if outcome.ready else None,
                "frozen_threshold": trajectory.frozen_threshold,
                "normal_pointwise_fpr": metric.normal_pointwise_fpr if math.isfinite(metric.normal_pointwise_fpr) else None,
                "normal_score_count": metric.normal_score_count,
                "eligible_fault_report_recall": metric.eligible_fault_report_recall if math.isfinite(metric.eligible_fault_report_recall) else None,
                "eligible_fault_report_count": metric.eligible_fault_report_count,
                "hit_fault_report_count": metric.hit_fault_report_count,
            })
    if diagnostics is not None:
        diagnostics["fixed_n_baselines"] = {
            "recall_min_source_q10": recall_q10,
            "recall_min_effective": recall_floor,
            "fpr_q90_source_fixed_n_diagnostic": fpr_q90,
        }
        diagnostics["readiness_task_outcomes"] = task_audit
    try:
        selection = select_readiness_candidate(
            readiness_grid, outcomes, recall_floor=recall_floor
        )
    except SourceNotEvaluable as exc:
        if diagnostics is not None:
            diagnostics["readiness_candidate_summaries"] = [
                _readiness_candidate_summary(item) for item in exc.summaries
            ]
            diagnostics["readiness_selection"] = "ZERO_JOINT_SUCCESS" if exc.summaries else "NO_SELECTION"
        raise SourcePipelineError("SOURCE_MODEL_NOT_EVALUABLE") from exc
    if diagnostics is not None:
        diagnostics["readiness_candidate_summaries"] = [
            _readiness_candidate_summary(item) for item in selection.summaries
        ]
        diagnostics["readiness_selection"] = selection.selected.candidate_id
    return selection, trajectories, float(recall_q10), float(recall_floor), float(fpr_q90)


def _readiness_candidate_summary(item: ReadinessCandidateSummary) -> dict[str, object]:
    return {
        "candidate_id": item.candidate_id,
        "joint_success_fraction": item.joint_success_fraction,
        "mean_acquisition_cost": item.mean_acquisition_cost,
        "macro_fault_report_recall": item.macro_fault_report_recall,
        "macro_normal_pointwise_fpr": item.macro_normal_pointwise_fpr,
        "conjunct_count": item.conjunct_count,
        "joint_success_count": item.joint_success_count,
        "task_count": item.task_count,
    }


def _fit_final_model(
    entities: Sequence[SourceEntityRows],
    candidate: DetectorCandidate,
    model_factory: Callable[..., object],
    seed_fn: Callable[[int], None],
) -> tuple[object, MedianImputeStandardScaler, dict[str, np.ndarray]]:
    """Fit exactly one selected final AE/preprocessor pair for the stratum."""
    try:
        rows: list[np.ndarray] = []
        for entity in entities:
            if int(np.count_nonzero(_clean_fit_mask(entity))) < ENTITY_ROW_MINIMUM:
                continue
            indices = capped_clean_indices(entity)
            rows.extend(entity.features[indices])
        if not rows:
            raise SourcePipelineError()
        fit_rows = np.asarray(rows, dtype=np.float64)
        # Reapply the required global order after concatenating per-entity caps.
        role_values: list[str] = []
        timestamps: list[datetime] = []
        raw_indices: list[int] = []
        for entity in entities:
            if int(np.count_nonzero(_clean_fit_mask(entity))) < ENTITY_ROW_MINIMUM:
                continue
            for index in capped_clean_indices(entity).tolist():
                role_values.append(entity.role_digest)
                timestamps.append(entity.timestamps[index])  # type: ignore[arg-type]
                raw_indices.append(int(entity.raw_row_indices[index]))
        order = ordered_capped_rows(
            fit_rows, role_values, timestamps, raw_indices,
            np.ones(len(fit_rows), dtype=bool), cap=SOURCE_ROW_CAP,
        )
        fit_rows = fit_rows[order]
        preprocessor = MedianImputeStandardScaler().fit(fit_rows)
        model_input = preprocessor.transform(fit_rows)
        model, _ = train_candidate(
            model_factory, candidate, model_input.copy(), model_input.copy(), seed_fn
        )
        final_scores: dict[str, np.ndarray] = {}
        for entity in sorted(entities, key=lambda item: item.role_digest):
            indices = np.flatnonzero(_effective_support_mask(entity)).astype(np.int64)
            values = np.full(len(entity.timestamps), np.nan, dtype=np.float64)
            if len(indices):
                transformed, valid = _transform_scoring_rows(preprocessor, entity.features[indices])
                if np.any(valid):
                    values[indices[valid]] = _prediction_scores(model, transformed[valid])
            final_scores[entity.role_digest] = values
        return model, preprocessor, final_scores
    except SourcePipelineError:
        raise
    except SourceStratumError as exc:
        if exc.code == "BACKBONE_NOT_ADMISSIBLE":
            raise SourcePipelineError("BACKBONE_NOT_ADMISSIBLE") from exc
        raise SourcePipelineError() from exc
    except Exception as exc:
        raise SourcePipelineError() from exc


def run_source_stratum(
    entities: Sequence[SourceEntityRows],
    *,
    model_factory: Callable[..., object],
    seed_fn: Callable[[int], None],
    diagnostic_sink: dict[str, object] | None = None,
) -> PipelineResult:
    """Run the complete sealed SOURCE-only procedure for one exact stratum.

    The caller must provide only SOURCE role entities and canonical SOURCE
    intervals.  The function performs no external reads and raises a generic
    :class:`SourcePipelineError` on any unsupported or non-evaluable stratum.
    """
    diagnostics = diagnostic_sink if diagnostic_sink is not None else {}
    diagnostics.update({
        "schema_version": "p5-0b3-source-pipeline-diagnostics-v1",
        "status": "RUNNING",
        "stage": "entity_validation",
    })
    try:
        entities = tuple(entities)
        dimension = _validate_entities(entities)
        diagnostics["source_entity_count"] = len(entities)
        diagnostics["feature_count"] = dimension
        diagnostics["stage"] = "fold_support_gate"
        fold_details = _fold_plan_details(entities)
        diagnostics["fold_support"] = _fold_plan_audit(fold_details, entities)
        plan = build_fold_plan(entities)
        candidates = candidate_grid(dimension)
        diagnostics["stage"] = "outer_fold_candidate_training"
        oof_by_candidate = _score_oof_candidates(
            entities, plan, candidates, model_factory, seed_fn
        )
        diagnostics["oof_candidate_support"] = {
            candidate_id: {
                "score_row_count": int(sum(len(scores) for scores in values.values())),
                "finite_score_row_count": int(sum(np.count_nonzero(np.isfinite(scores))
                                                   for scores in values.values())),
                "entity_count": len(values),
            }
            for candidate_id, values in sorted(oof_by_candidate.items())
        }
        diagnostics["outer_fold_outcomes"] = [
            {
                "fold": fold,
                "status": "PASS",
                "fit_usable_entity_count": plan.fit_entity_counts[fold],
                "fit_clean_row_count": plan.fit_row_counts[fold],
                "candidate_count": len(candidates),
            }
            for fold in range(OUTER_FOLD_COUNT)
        ]
        labels = {
            entity.role_digest: _labels_for_entity(entity)
            for entity in entities
        }
        diagnostics["stage"] = "detector_candidate_selection"
        try:
            selected_detector, common_entities, detector_metrics = select_detector_candidate(
                candidates, oof_by_candidate, labels
            )
        except SourceStratumError as exc:
            raise SourcePipelineError() from exc
        diagnostics["detector_selection"] = {
            "selected_candidate_id": selected_detector.candidate_id,
            "common_heldout_role_digests": list(common_entities),
            "common_heldout_entity_count": len(common_entities),
            "candidate_metrics": [
                {"candidate_id": metric.candidate_id,
                 "macro_ap": metric.macro_ap,
                 "macro_auroc": metric.macro_auroc}
                for metric in detector_metrics
            ],
        }
        selected_oof = oof_by_candidate[selected_detector.candidate_id]
        diagnostics["stage"] = "source_iqr"
        iqr_source = _source_iqr(entities, selected_oof)
        diagnostics["iqr_source"] = iqr_source
        diagnostics["stage"] = "readiness_candidate_evaluation"
        readiness_selection, trajectories, recall_q10, recall_floor, fpr_q90 = (
            _readiness_selection(entities, selected_oof, iqr_source, diagnostics)
        )
        diagnostics["stage"] = "final_model_fit_and_score"
        final_model, final_preprocessor, final_scores = _fit_final_model(
            entities, selected_detector, model_factory, seed_fn
        )
        diagnostics["final_score_support"] = {
            "score_row_count": int(sum(len(scores) for scores in final_scores.values())),
            "finite_score_row_count": int(sum(np.count_nonzero(np.isfinite(scores))
                                               for scores in final_scores.values())),
            "entity_count": len(final_scores),
        }
        safe_detector_metrics = tuple(
            SafeDetectorMetric(metric.candidate_id, metric.macro_ap, metric.macro_auroc)
            for metric in detector_metrics
        )
        safe_readiness_metrics = tuple(
            SafeReadinessMetric(
                metric.candidate_id,
                metric.joint_success_fraction,
                metric.mean_acquisition_cost,
                metric.macro_fault_report_recall,
                metric.macro_normal_pointwise_fpr,
                metric.conjunct_count,
                metric.joint_success_count,
                metric.task_count,
            )
            for metric in readiness_selection.summaries
        )
        summary = SourcePipelineSummary(
            status="SOURCE_MODEL_READY",
            source_entity_count=len(entities),
            selected_detector_id=selected_detector.candidate_id,
            selected_readiness_id=readiness_selection.selected.candidate_id,
            common_heldout_entity_count=len(common_entities),
            iqr_source=iqr_source,
            recall_min_source_q10=recall_q10,
            recall_min_effective=recall_floor,
            fpr_q90_source_fixed_n_diagnostic=fpr_q90,
            fold_fit_entity_counts=plan.fit_entity_counts,
            fold_fit_row_counts=plan.fit_row_counts,
            detector_metrics=safe_detector_metrics,
            readiness_metrics=safe_readiness_metrics,
            oof_score_hash=_score_hash(selected_oof),
            final_score_hash=_score_hash(final_scores),
            final_preprocessor_hash=_preprocessor_hash(final_preprocessor),
            invalid_score_row_count=sum(
                int(np.count_nonzero(_effective_support_mask(entity)
                                     & ~np.isfinite(selected_oof[entity.role_digest])))
                + int(np.count_nonzero(_effective_support_mask(entity)
                                       & ~np.isfinite(final_scores[entity.role_digest])))
                for entity in entities
            ),
        )
        artifacts = SourceScoreArtifacts(
            oof_scores_by_candidate=oof_by_candidate,
            selected_oof_scores=selected_oof,
            final_scores=final_scores,
            trajectories=trajectories,
        )
        diagnostics["stage"] = "complete"
        diagnostics["status"] = "SOURCE_MODEL_READY"
        diagnostics["selected_detector_id"] = selected_detector.candidate_id
        diagnostics["selected_readiness_id"] = readiness_selection.selected.candidate_id
        return PipelineResult(
            summary=summary,
            final_model=final_model,
            final_preprocessor=final_preprocessor,
            selected_detector=selected_detector,
            selected_readiness=readiness_selection.selected,
            artifacts=artifacts,
        )
    except SourcePipelineError as exc:
        diagnostics["status"] = exc.code
        diagnostics.setdefault("failure_stage", diagnostics.get("stage", "unknown"))
        raise
    except Exception as exc:
        diagnostics["status"] = "SOURCE_MODEL_NOT_EVALUABLE"
        diagnostics.setdefault("failure_stage", diagnostics.get("stage", "unknown"))
        raise SourcePipelineError() from exc


# Short aliases make the parent process launcher easier to read while keeping
# the explicit SOURCE scope in the canonical function name.
run_pipeline = run_source_stratum
run_stratum = run_source_stratum
run_development = run_source_stratum
EntitySourceData = SourceEntityRows
SourceInterval = CanonicalSourceInterval


__all__ = [
    "CanonicalSourceInterval",
    "EntitySourceData",
    "FoldPlan",
    "PipelineResult",
    "SafeDetectorMetric",
    "SafeReadinessMetric",
    "SourceEntityRows",
    "SourceInterval",
    "SourcePipelineError",
    "SourcePipelineSummary",
    "SourceScoreArtifacts",
    "build_fold_plan",
    "capped_clean_indices",
    "run_development",
    "run_pipeline",
    "run_stratum",
    "run_source_stratum",
]
