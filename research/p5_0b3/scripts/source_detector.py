"""Frozen SOURCE-only AE training and detector selection helpers for P5-0B3.

The module has no data loading or EFD import side effects. Callers inject the
v0.7.1 ``MultilayerAutoencoder`` class and a seed-reset function after the
runtime gate has passed.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import numbers
from typing import Callable, Mapping, Sequence

import numpy as np


LEARNING_RATES = (0.0003, 0.001)
EPOCHS = 100
BATCH_SIZE = 128
SEED = 17
MIN_COMMON_ENTITIES = 4
FOLD_SALT = "P5-0B2-SOURCE-FOLD-v1|"


class SourceStratumError(ValueError):
    """Generic stratum-scoped failure; intentionally carries no row details."""

    def __init__(self, code: str = "SOURCE_MODEL_NOT_EVALUABLE") -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    dimension: int
    bottleneck: int
    learning_rate: float
    encoder_widths: tuple[int, int]
    decoder_widths: tuple[int, int]


def candidate_grid(dimension: int) -> tuple[Candidate, ...]:
    """Return the fixed four-candidate Cartesian product for projected D."""
    if not isinstance(dimension, int) or dimension < 1:
        raise SourceStratumError()
    widths = (4 * dimension, 2 * dimension)
    bottlenecks = (max(2, math.ceil(dimension / 4)),
                   max(2, math.ceil(dimension / 2)))
    result = []
    for bottleneck in bottlenecks:
        for rate in LEARNING_RATES:
            rate_text = f"{rate:.4f}"
            result.append(Candidate(
                f"ae-bottleneck-{bottleneck}-adam-lr-{rate_text}",
                dimension, bottleneck, rate, widths, tuple(reversed(widths))))
    return tuple(sorted(result, key=lambda candidate: candidate.candidate_id))


def fold_assignments(role_digests: Sequence[str], sha256_hex: Callable[[bytes], str]) -> dict[str, int]:
    """Hash/rank role digests into five deterministic, round-robin folds."""
    if len(set(role_digests)) != len(role_digests) or any(not x for x in role_digests):
        raise SourceStratumError()
    ranked = []
    for digest in role_digests:
        try:
            fold_digest = sha256_hex((FOLD_SALT + digest).encode("utf-8"))
        except Exception as exc:
            raise SourceStratumError() from exc
        ranked.append((fold_digest, digest))
    ranked.sort()
    return {role_digest: rank % 5 for rank, (_, role_digest) in enumerate(ranked)}


def midpoint_indices(count: int, cap: int = 8192) -> np.ndarray:
    """Indices for deterministic midpoint sampling of an already ordered entity."""
    if count < 0 or cap < 1:
        raise SourceStratumError()
    if count <= cap:
        return np.arange(count, dtype=np.int64)
    return np.floor((np.arange(cap, dtype=np.float64) + 0.5) * count / cap).astype(np.int64)


def ordered_capped_rows(rows: np.ndarray, role_digests: Sequence[str],
                        timestamps: Sequence[object], raw_row_indices: Sequence[int],
                        clean_mask: Sequence[bool], cap: int = 8192) -> np.ndarray:
    """Return pooled fit rows ordered by digest/time/raw index, capped per entity."""
    values = np.asarray(rows)
    n = len(values)
    if values.ndim != 2 or not (len(role_digests) == len(timestamps) ==
                                len(raw_row_indices) == len(clean_mask) == n):
        raise SourceStratumError()
    clean = np.asarray(clean_mask, dtype=bool)
    chosen: list[int] = []
    by_entity: dict[str, list[int]] = {}
    for i, digest in enumerate(role_digests):
        if clean[i]:
            by_entity.setdefault(digest, []).append(i)
    try:
        for digest in sorted(by_entity):
            entity_rows = sorted(by_entity[digest], key=lambda i: (timestamps[i], raw_row_indices[i]))
            chosen.extend(entity_rows[j] for j in midpoint_indices(len(entity_rows), cap))
    except Exception as exc:
        raise SourceStratumError() from exc
    chosen.sort(key=lambda i: (role_digests[i], timestamps[i], raw_row_indices[i]))
    return np.asarray(chosen, dtype=np.int64)


def annotation_clean_mask(known_fault: Sequence[bool], disturbance_fault: Sequence[bool],
                          disturbance_other: Sequence[bool]) -> np.ndarray:
    """AE support mask: exclude the inclusive union of all fault/disturbance intervals."""
    arrays = [np.asarray(x, dtype=bool) for x in
              (known_fault, disturbance_fault, disturbance_other)]
    if any(a.ndim != 1 for a in arrays) or len({a.size for a in arrays}) != 1:
        raise SourceStratumError()
    return ~(arrays[0] | arrays[1] | arrays[2])


def support_row_mask(values: np.ndarray) -> np.ndarray:
    """Rows with all-numeric/finite-or-NaN support and at least one finite value."""
    raw = np.asarray(values)
    if raw.ndim != 2:
        raise SourceStratumError()
    valid = np.zeros(raw.shape[0], dtype=bool)
    for index, row in enumerate(raw):
        if any(not isinstance(value, numbers.Real) or isinstance(value, bool)
               for value in row):
            continue
        try:
            numeric = np.asarray(row, dtype=np.float64)
        except (TypeError, ValueError, OverflowError):
            continue
        valid[index] = (not np.isinf(numeric).any() and np.isfinite(numeric).any())
    return valid


def semantic_labels(known_fault: Sequence[bool], reference_normal: Sequence[bool],
                    disturbance_fault: Sequence[bool],
                    disturbance_other: Sequence[bool]) -> np.ndarray:
    """Return 1/0/-1 for positive/negative/unlabeled source observations."""
    arrays = [np.asarray(x, dtype=bool) for x in
              (known_fault, reference_normal, disturbance_fault, disturbance_other)]
    if any(a.ndim != 1 for a in arrays) or len({a.size for a in arrays}) != 1:
        raise SourceStratumError()
    fault, normal, dist_fault, dist_other = arrays
    excluded_overlap = fault | dist_fault | dist_other
    labels = np.full(fault.size, -1, dtype=np.int8)
    # A normal overlap is explicitly ambiguous; disturbances are never a
    # positive class even when they overlap a known-fault interval.
    labels[fault & ~normal & ~dist_fault & ~dist_other] = 1
    labels[normal & ~excluded_overlap] = 0
    return labels


def reset_seed(seed_fn: Callable[[int], None]) -> None:
    """Delegate seeding to runtime-gated caller; always reset to protocol seed."""
    try:
        seed_fn(SEED)
    except Exception as exc:
        raise SourceStratumError() from exc


def _assert_fitted_model_contract(autoencoder: object, candidate: Candidate) -> None:
    """Fail closed if the runtime-built EFD model differs from the frozen grid."""
    try:
        dense_widths = [4 * candidate.dimension, 2 * candidate.dimension,
                        candidate.bottleneck, 2 * candidate.dimension,
                        4 * candidate.dimension, candidate.dimension]
        if (list(autoencoder.layers) != list(candidate.encoder_widths) or
                int(autoencoder.code_size) != candidate.bottleneck or
                int(autoencoder.epochs) != EPOCHS or
                int(autoencoder.batch_size) != BATCH_SIZE or
                autoencoder.loss_name != "mean_squared_error" or
                float(autoencoder.noise) != 0.0 or autoencoder.callbacks or
                int(autoencoder.epochs_completed) != EPOCHS):
            raise SourceStratumError("BACKBONE_NOT_ADMISSIBLE")
        model = autoencoder.model
        dense = [layer for layer in model.layers if layer.__class__.__name__ == "Dense"]
        if [int(layer.units) for layer in dense] != dense_widths:
            raise SourceStratumError("BACKBONE_NOT_ADMISSIBLE")
        if any(layer.kernel_initializer.__class__.__name__ != "HeNormal" or
               layer.bias_initializer.__class__.__name__ != "Zeros" or
               layer.dtype_policy.name != "float32" for layer in dense):
            raise SourceStratumError("BACKBONE_NOT_ADMISSIBLE")
        prelus = [layer for layer in model.layers if layer.__class__.__name__ == "PReLU"]
        if (len(prelus) != 5 or
                any(layer.shared_axes is not None or
                    layer.alpha_initializer.__class__.__name__ != "Zeros" or
                    layer.dtype_policy.name != "float32" for layer in prelus)):
            raise SourceStratumError("BACKBONE_NOT_ADMISSIBLE")
        if model.layers[-1].activation.__name__ != "linear":
            raise SourceStratumError("BACKBONE_NOT_ADMISSIBLE")
        optimizer = model.optimizer
        learning_rate = np.asarray(optimizer.learning_rate.numpy())
        if (optimizer.__class__.__name__ != "Adam" or learning_rate.shape != () or
                np.float32(learning_rate) != np.float32(candidate.learning_rate) or
                float(optimizer.beta_1) != 0.9 or float(optimizer.beta_2) != 0.999 or
                float(optimizer.epsilon) != 1e-7 or bool(optimizer.amsgrad) or
                getattr(optimizer, "weight_decay", None) is not None):
            raise SourceStratumError("BACKBONE_NOT_ADMISSIBLE")
    except SourceStratumError:
        raise
    except Exception as exc:
        raise SourceStratumError() from exc


def train_candidate(model_factory: Callable[..., object], candidate: Candidate,
                    training_rows: np.ndarray, score_rows: np.ndarray,
                    seed_fn: Callable[[int], None]) -> tuple[object, np.ndarray]:
    """Fit direct EFD MultilayerAutoencoder and return per-row RMSE scores."""
    try:
        x = np.asarray(training_rows, dtype=np.float32)
        scored = np.asarray(score_rows, dtype=np.float32)
        if (x.ndim != 2 or scored.ndim != 2 or x.shape[1] != candidate.dimension or
                scored.shape[1] != candidate.dimension or len(x) == 0 or
                not np.isfinite(x).all() or not np.isfinite(scored).all()):
            raise SourceStratumError()
        reset_seed(seed_fn)
        model = model_factory(
            layers=list(candidate.encoder_widths), code_size=candidate.bottleneck,
            kernel_initializer="he_normal", act="prelu", last_act="linear",
            learning_rate=candidate.learning_rate, batch_size=BATCH_SIZE,
            epochs=EPOCHS, loss_name="mean_squared_error", early_stopping=False,
            noise=0.0, decay_rate=None, verbose=0)
        model.fit(x, x_val=None, shuffle=False)
        if getattr(model, "model", None) is not None:
            _assert_fitted_model_contract(model, candidate)
        reconstruction = np.asarray(model.predict(scored, verbose=0), dtype=np.float64)
        if reconstruction.shape != scored.shape:
            raise SourceStratumError("BACKBONE_NOT_ADMISSIBLE")
        scores = np.sqrt(np.mean((scored.astype(np.float64) - reconstruction) ** 2, axis=1))
        # Keep row alignment when an otherwise well-formed inference returns
        # non-finite reconstruction values. The common-entity selector drops
        # an entity globally if any required labeled row is then unscorable.
        scores[~np.isfinite(scores)] = np.nan
        return model, scores
    except SourceStratumError:
        raise
    except Exception as exc:
        raise SourceStratumError() from exc


def average_precision(labels: np.ndarray, scores: np.ndarray) -> float:
    """Non-interpolated average precision, grouping tied descending thresholds."""
    y, s = np.asarray(labels), np.asarray(scores, dtype=np.float64)
    if y.ndim != 1 or s.ndim != 1 or len(y) != len(s) or not np.isfinite(s).all():
        raise SourceStratumError()
    if not np.isin(y, (0, 1)).all() or not np.any(y == 1):
        raise SourceStratumError()
    order = np.argsort(-s, kind="mergesort")
    sorted_y = y[order].astype(np.int64)
    sorted_s = s[order]
    ends = np.r_[np.flatnonzero(np.diff(sorted_s) != 0), len(s) - 1]
    true_positives = np.cumsum(sorted_y)[ends]
    retrieved = ends + 1
    return float(np.sum((np.diff(np.r_[0, true_positives]) / np.sum(y)) *
                        (true_positives / retrieved)))


def average_rank_auroc(labels: np.ndarray, scores: np.ndarray) -> float:
    """AUROC computed from average ranks for tied finite scores."""
    y, s = np.asarray(labels), np.asarray(scores, dtype=np.float64)
    if y.ndim != 1 or s.ndim != 1 or len(y) != len(s) or not np.isfinite(s).all():
        raise SourceStratumError()
    positives, negatives = int(np.sum(y == 1)), int(np.sum(y == 0))
    if not np.isin(y, (0, 1)).all() or not positives or not negatives:
        raise SourceStratumError()
    order = np.argsort(s, kind="mergesort")
    sorted_scores = s[order]
    ranks = np.empty(len(s), dtype=np.float64)
    start = 0
    while start < len(s):
        end = start + 1
        while end < len(s) and sorted_scores[end] == sorted_scores[start]:
            end += 1
        ranks[order[start:end]] = (start + 1 + end) / 2.0
        start = end
    rank_sum = float(np.sum(ranks[y == 1]))
    return (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)


@dataclass(frozen=True)
class CandidateMetrics:
    candidate_id: str
    macro_ap: float
    macro_auroc: float
    bottleneck: int
    learning_rate: float


def select_candidate(candidates: Sequence[Candidate],
                     scores_by_candidate: Mapping[str, Mapping[str, np.ndarray]],
                     labels_by_entity: Mapping[str, np.ndarray],
                     minimum_common_entities: int = MIN_COMMON_ENTITIES
                     ) -> tuple[Candidate, tuple[str, ...], tuple[CandidateMetrics, ...]]:
    """Select on common held-out entities; tie-break by protocol's ordered rules."""
    if not candidates or minimum_common_entities < 1:
        raise SourceStratumError()
    common = set(labels_by_entity)
    for candidate in candidates:
        candidate_scores = scores_by_candidate.get(candidate.candidate_id, {})
        common &= set(candidate_scores)
    evaluable = []
    for entity in sorted(common):
        labels = np.asarray(labels_by_entity[entity])
        if (labels.ndim != 1 or not np.isin(labels, (0, 1, -1)).all()):
            raise SourceStratumError()
        valid = labels != -1
        y = labels[valid]
        entity_complete = True
        for candidate in candidates:
            try:
                values = np.asarray(scores_by_candidate[candidate.candidate_id][entity],
                                    dtype=np.float64)
            except (TypeError, ValueError, OverflowError) as exc:
                raise SourceStratumError() from exc
            if values.shape != labels.shape or not np.isfinite(values[valid]).all():
                entity_complete = False
        if not entity_complete:
            continue
        if len(y) and np.any(y == 0) and np.any(y == 1):
            evaluable.append(entity)
    if len(evaluable) < minimum_common_entities:
        raise SourceStratumError()
    metrics = []
    for candidate in candidates:
        aps, aucs = [], []
        for entity in evaluable:
            labels = np.asarray(labels_by_entity[entity])
            mask = labels != -1
            scores = np.asarray(scores_by_candidate[candidate.candidate_id][entity])[mask]
            y = labels[mask]
            aps.append(average_precision(y, scores))
            aucs.append(average_rank_auroc(y, scores))
        metrics.append(CandidateMetrics(candidate.candidate_id, float(np.mean(aps)),
                                        float(np.mean(aucs)), candidate.bottleneck,
                                        candidate.learning_rate))
    # Treat macro AP values within 1e-12 as tied, then apply subsequent keys.
    best_ap = max(item.macro_ap for item in metrics)
    tied = [item for item in metrics if best_ap - item.macro_ap <= 1e-12]
    winner = sorted(tied, key=lambda item: (-item.macro_auroc, item.bottleneck,
                                             item.learning_rate, item.candidate_id))[0]
    by_id = {candidate.candidate_id: candidate for candidate in candidates}
    return by_id[winner.candidate_id], tuple(evaluable), tuple(metrics)
