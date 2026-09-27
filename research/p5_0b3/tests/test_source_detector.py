"""Synthetic contract tests for SOURCE detector helpers; no EFD/runtime needed."""

import hashlib
import unittest

import numpy as np

from research.p5_0b3.scripts.source_detector import (
    SourceStratumError,
    annotation_clean_mask,
    average_precision,
    average_rank_auroc,
    candidate_grid,
    fold_assignments,
    midpoint_indices,
    ordered_capped_rows,
    select_candidate,
    semantic_labels,
    support_row_mask,
    train_candidate,
)


class SourceDetectorTests(unittest.TestCase):
  def test_fixed_grid_and_dimensions(self):
    grid = candidate_grid(8)
    self.assertEqual(len(grid), 4)
    self.assertEqual({x.encoder_widths for x in grid}, {(32, 16)})
    self.assertEqual({x.decoder_widths for x in grid}, {(16, 32)})
    self.assertEqual({x.bottleneck for x in grid}, {2, 4})
    self.assertEqual({x.learning_rate for x in grid}, {0.0003, 0.001})
    self.assertEqual({x.candidate_id.rsplit("-", 1)[-1] for x in grid}, {"0.0003", "0.0010"})
    self.assertEqual({x.bottleneck for x in candidate_grid(14)}, {4, 7})


  def test_fold_assignments_match_salted_sha_and_round_robin(self):
    role_digests = ["r3", "r1", "r4", "r2", "r0", "r5"]
    actual = fold_assignments(role_digests, lambda value: hashlib.sha256(value).hexdigest())
    ranked = sorted((hashlib.sha256(("P5-0B2-SOURCE-FOLD-v1|" + value).encode()).hexdigest(), value)
                    for value in role_digests)
    self.assertEqual(actual, {digest: rank % 5 for rank, (_, digest) in enumerate(ranked)})


  def test_midpoint_cap_and_ordered_entity_pooled_rows(self):
    self.assertTrue(np.array_equal(midpoint_indices(5, 2), [1, 3]))
    values = np.arange(8).reshape(8, 1)
    role = ["b", "a", "b", "a", "a", "b", "a", "b"]
    times = [2, 3, 1, 2, 1, 4, 4, 3]
    raw = list(range(8))
    ids = ordered_capped_rows(values, role, times, raw, [True] * 8, cap=2)
    # Within each entity chronological midpoint ranks are selected then globally ordered.
    self.assertEqual(ids.tolist(), [3, 6, 0, 5])


  def test_annotation_masks_and_support_rows(self):
    clean = annotation_clean_mask([False, True, False], [False, False, True], [False] * 3)
    self.assertEqual(clean.tolist(), [True, False, False])
    self.assertEqual(support_row_mask(np.array([[np.nan, 2.0], [np.nan, np.nan],
                                                [np.inf, 1.0]])).tolist(), [True, False, False])
    mixed = np.array([[1.0, 2.0], ["bad", 3.0], [np.nan, 4.0]], dtype=object)
    self.assertEqual(support_row_mask(mixed).tolist(), [True, False, True])


  def test_semantic_labels_exclude_unlabeled_and_normal_fault_overlap(self):
    labels = semantic_labels(
        known_fault=[False, True, False, False],
        reference_normal=[True, True, True, True],
        disturbance_fault=[False, False, True, False],
        disturbance_other=[False] * 4,
    )
    self.assertEqual(labels.tolist(), [0, -1, -1, 0])


  def test_metrics_group_threshold_ties_and_average_ranks(self):
    y = np.array([0, 1, 0, 1])
    scores = np.array([0.5, 0.5, 0.1, 0.1])
    self.assertAlmostEqual(average_precision(y, scores), 0.5)
    self.assertAlmostEqual(average_rank_auroc(y, scores), 0.5)


  def test_selection_uses_common_entity_set_and_protocol_tie_break(self):
    candidates = candidate_grid(8)
    ids = [x.candidate_id for x in candidates]
    labels = {f"e{i}": np.array([0, 1, 0, 1]) for i in range(4)}
    scores = {candidate_id: {entity: np.array([0.1, 0.9, 0.2, 0.8])
                            for entity in labels} for candidate_id in ids}
    # A fifth entity is omitted from one candidate and therefore excluded globally.
    labels["extra"] = np.array([0, 1])
    for candidate_id in ids:
        scores[candidate_id]["extra"] = np.array([0.1, 0.9])
    del scores[ids[0]]["extra"]
    winner, entities, metrics = select_candidate(candidates, scores, labels)
    self.assertEqual(entities, ("e0", "e1", "e2", "e3"))
    self.assertEqual(winner.bottleneck, min(x.bottleneck for x in candidates))
    self.assertEqual(len(metrics), 4)


  def test_selection_rejects_malformed_and_nonfinite_required_scores(self):
    candidates = candidate_grid(8)
    entities = {f"e{i}": np.array([0, 1]) for i in range(4)}
    scores = {candidate.candidate_id: {entity: np.array([0.0, 1.0]) for entity in entities}
              for candidate in candidates}
    scores[candidates[0].candidate_id]["e0"] = np.array([0.0])
    with self.assertRaisesRegex(SourceStratumError, "^SOURCE_MODEL_NOT_EVALUABLE$"):
      select_candidate(candidates, scores, entities)

  def test_selection_drops_entity_incomplete_for_any_candidate(self):
    candidates = candidate_grid(8)
    entities = {f"e{i}": np.array([0, 1]) for i in range(5)}
    scores = {candidate.candidate_id: {entity: np.array([0.0, 1.0])
                                      for entity in entities}
              for candidate in candidates}
    scores[candidates[0].candidate_id]["e4"] = np.array([0.0, np.nan])
    _, common, _ = select_candidate(candidates, scores, entities)
    self.assertEqual(common, ("e0", "e1", "e2", "e3"))
    scores[candidates[0].candidate_id]["e0"] = np.array([0.0, np.nan])
    with self.assertRaisesRegex(SourceStratumError, "^SOURCE_MODEL_NOT_EVALUABLE$"):
      select_candidate(candidates, scores, entities)


  def test_training_contract_uses_factory_no_efd_import(self):
    class Model:
        def __init__(self, kwargs):
            self.kwargs = kwargs
            self.fit_args = None

        def fit(self, x, **kwargs):
            self.fit_args = kwargs
            return self

        def predict(self, x, **kwargs):
            return np.zeros_like(x)

    created = []

    def factory(**kwargs):
        model = Model(kwargs)
        created.append(model)
        return model

    seeds = []
    x = np.arange(12, dtype=np.float32).reshape(6, 2)
    candidate = candidate_grid(2)[0]
    model, scores = train_candidate(factory, candidate, x, x, seeds.append)
    self.assertEqual(seeds, [17])
    self.assertEqual(model.kwargs["epochs"], 100)
    self.assertEqual(model.kwargs["batch_size"], 128)
    self.assertIs(model.kwargs["early_stopping"], False)
    self.assertEqual(model.fit_args, {"x_val": None, "shuffle": False})
    self.assertTrue(np.allclose(scores, np.sqrt(np.mean(x.astype(np.float64) ** 2, axis=1))))
    self.assertEqual(len(created), 1)


  def test_bad_training_is_generic_stratum_failure(self):
    with self.assertRaisesRegex(SourceStratumError, "^SOURCE_MODEL_NOT_EVALUABLE$"):
      train_candidate(lambda **kwargs: None, candidate_grid(2)[0],
                      np.array([[np.nan, 1]], dtype=np.float32),
                      np.ones((1, 2)), lambda seed: None)

  def test_nonfinite_reconstruction_is_row_aligned_nan_score(self):
    class PartiallyNonfiniteModel:
        def fit(self, x, **kwargs):
            return self

        def predict(self, x, **kwargs):
            result = np.zeros_like(x)
            result[1, 0] = np.nan
            return result

    candidate = candidate_grid(2)[0]
    x = np.arange(8, dtype=np.float32).reshape(4, 2)
    _, scores = train_candidate(
        lambda **kwargs: PartiallyNonfiniteModel(), candidate, x, x,
        lambda seed: None,
    )
    self.assertTrue(np.isfinite(scores[[0, 2, 3]]).all())
    self.assertTrue(np.isnan(scores[1]))

  def test_reconstruction_shape_violation_is_backbone_terminal(self):
    class WrongShape:
        def fit(self, x, **kwargs):
            return self

        def predict(self, x, **kwargs):
            return np.zeros((len(x), x.shape[1] + 1), dtype=np.float32)

    candidate = candidate_grid(2)[0]
    rows = np.ones((8, 2), dtype=np.float32)
    with self.assertRaisesRegex(SourceStratumError, "^BACKBONE_NOT_ADMISSIBLE$"):
        train_candidate(lambda **kwargs: WrongShape(), candidate, rows, rows,
                        lambda seed: None)


if __name__ == "__main__":
    unittest.main()
