"""Synthetic-only tests for the in-memory P5-0B3 SOURCE pipeline."""

from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import unittest
from unittest.mock import patch

import numpy as np

from research.p5_0b3.scripts.source_pipeline import (
    CanonicalSourceInterval,
    SourceEntityRows,
    SourcePipelineError,
    _pseudo_target_info,
    _repeat_fit_candidate,
    _fit_final_model,
    _readiness_selection,
    build_fold_plan,
    capped_clean_indices,
    _transform_scoring_rows,
    run_source_stratum,
)
from research.p5_0b3.scripts.source_detector import candidate_grid


BASE = datetime(2024, 1, 1)


def _entity(
    digest: str,
    *,
    rows: int = 300,
    pseudo_target: bool = False,
    prefix_fault: bool = False,
    normal_suffix_rows: int = 100,
) -> SourceEntityRows:
    if pseudo_target and rows == 2424 and normal_suffix_rows != 100:
        rows = 2304 + normal_suffix_rows + 20
    stamps = tuple(BASE + timedelta(minutes=index) for index in range(rows))
    x = np.column_stack((
        np.linspace(0.0, 1.0, rows, dtype=np.float64),
        np.linspace(1.0, 0.0, rows, dtype=np.float64),
    ))
    intervals = []
    if pseudo_target:
        # The first 2,304 raw observations are clean; the suffix contains
        # 100 normal observations followed by a known fault report.
        normal_start = BASE + timedelta(minutes=2304)
        normal_end = BASE + timedelta(minutes=2303 + normal_suffix_rows)
        fault_start = BASE + timedelta(minutes=2304 + normal_suffix_rows)
        fault_end = stamps[-1]
        intervals = [
            CanonicalSourceInterval(
                "normal_events", "REFERENCE_NORMAL_EVENT", normal_start, normal_end,
                digest,
            ),
            CanonicalSourceInterval(
                "faults", "KNOWN_FAULT", fault_start, fault_end, digest,
            ),
        ]
        # Keep the fault observations well outside the source-fit range so
        # every ready candidate has a deterministic synthetic hit.
        fault_index = 2304 + normal_suffix_rows
        x[fault_index:, 0] = 10.0
        x[fault_index:, 1] = -10.0
    if prefix_fault:
        intervals.append(CanonicalSourceInterval(
            "faults", "KNOWN_FAULT", stamps[10], stamps[10], digest
        ))
    return SourceEntityRows(digest, x, stamps, intervals=tuple(intervals))


class _ZeroReconstructionModel:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.fit_calls = 0

    def fit(self, x, **kwargs):
        self.fit_calls += 1
        self.fit_kwargs = kwargs
        return self

    def predict(self, x, **kwargs):
        return np.zeros_like(x)


class _ChangingReconstructionModel(_ZeroReconstructionModel):
    counter = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        type(self).counter += 1
        self.instance_number = type(self).counter

    def predict(self, x, **kwargs):
        return np.full_like(x, float(self.instance_number))


class SourcePipelineTests(unittest.TestCase):
    def test_entity_input_normalizes_masks_and_rejects_bad_interval_source(self):
        entity = _entity("role-a", rows=300)
        self.assertEqual(entity.features.dtype, np.float64)
        self.assertEqual(entity.timestamp_valid.dtype, np.bool_)
        self.assertEqual(entity.measurement_valid.dtype, np.bool_)
        with self.assertRaisesRegex(SourcePipelineError, "^SOURCE_MODEL_NOT_EVALUABLE$"):
            SourceEntityRows(
                "role-b",
                np.ones((2, 2)),
                (BASE, BASE + timedelta(minutes=1)),
                intervals=(
                    {
                        "annotation_source": "faults",
                        "annotation_kind": "REFERENCE_NORMAL_EVENT",
                        "interval_start": BASE,
                        "interval_end": BASE,
                    },
                ),
            )

    def test_fold_support_gate_and_midpoint_cap_are_stratum_local(self):
        entities = tuple(_entity(f"role-{index}", rows=300) for index in range(6))
        plan = build_fold_plan(entities)
        self.assertEqual(len(plan.assignments), 6)
        self.assertEqual(len(plan.fit_entity_counts), 5)
        self.assertTrue(all(count >= 4 for count in plan.fit_entity_counts))
        self.assertTrue(all(count >= 1024 for count in plan.fit_row_counts))

        long_entity = _entity("long", rows=9000)
        selected = capped_clean_indices(long_entity)
        self.assertEqual(len(selected), 8192)
        expected = np.floor((np.arange(8192) + 0.5) * 9000 / 8192).astype(np.int64)
        np.testing.assert_array_equal(selected, expected)

    def test_subminimum_entity_is_never_fit_or_counted_as_usable(self):
        entities = tuple(_entity(f"role-{index}", rows=(255 if index == 0 else 300))
                         for index in range(7))
        plan = build_fold_plan(entities)
        self.assertEqual(plan.support_counts["role-0"], 255)
        self.assertTrue(all(count <= 6 for count in plan.fit_entity_counts))
        self.assertTrue(all(count >= 4 for count in plan.fit_entity_counts))

    def test_scoring_transform_marks_only_overflow_row_invalid(self):
        fit = np.column_stack((np.linspace(-1.0, 1.0, 300),
                               np.linspace(1.0, -1.0, 300)))
        from research.p5_0b3.scripts.preprocessing import MedianImputeStandardScaler
        preprocessor = MedianImputeStandardScaler().fit(fit)
        rows = np.array([[0.0, 0.0], [1e300, 0.0], [0.5, -0.5],
                         [np.nan, 0.25]])
        transformed, valid = _transform_scoring_rows(preprocessor, rows)
        self.assertEqual(valid.tolist(), [True, False, True, True])
        self.assertTrue(np.isnan(transformed[1]).all())
        self.assertTrue(np.isfinite(transformed[valid]).all())
        expected = preprocessor.transform(rows[valid])
        np.testing.assert_array_equal(transformed[valid], expected)

    def test_pseudo_target_gates_reject_prefix_annotations_and_accept_clean_suffix(self):
        eligible = _entity("eligible", rows=2424, pseudo_target=True)
        scores = np.linspace(0.0, 1.0, 2424)
        self.assertIsNotNone(_pseudo_target_info(eligible, scores))
        ineligible = _entity("bad", rows=2424, pseudo_target=True, prefix_fault=True)
        self.assertIsNone(_pseudo_target_info(ineligible, scores))

    def test_pseudo_target_requires_finite_normal_count_and_coverage(self):
        def eligible_with(normal_rows, finite_rows):
            entity = _entity("coverage", rows=2424, pseudo_target=True,
                             normal_suffix_rows=normal_rows)
            scores = np.linspace(0.0, 1.0, len(entity.timestamps))
            scores[2304 + finite_rows:2304 + normal_rows] = np.nan
            return _pseudo_target_info(entity, scores)

        self.assertIsNotNone(eligible_with(100, 100))
        self.assertIsNotNone(eligible_with(104, 100))
        self.assertIsNone(eligible_with(106, 100))
        self.assertIsNone(eligible_with(99, 99))

    def test_readiness_task_audit_reports_raw_finite_coverage_and_fpr_denominator(self):
        entities = tuple(_entity(f"audit-{index}", rows=2428, pseudo_target=True,
                                 normal_suffix_rows=104)
                         for index in range(4))
        score_values = np.linspace(0.0, 1.0, 2428)
        score_values[2404:2408] = np.nan
        score_map = {entity.role_digest: score_values.copy() for entity in entities}
        diagnostics = {}
        try:
            _readiness_selection(entities, score_map, 1.0, diagnostics)
        except SourcePipelineError:
            pass
        row = next(item for item in diagnostics["readiness_task_outcomes"]
                   if item["ready"])
        self.assertEqual(row["N_normal_raw"], 104)
        self.assertEqual(row["N_normal_finite"], 100)
        self.assertEqual(row["normal_score_coverage"], 100 / 104)
        self.assertEqual(row["normal_fpr_denominator"], 100)

    def test_repeat_fit_is_terminal_when_scores_are_not_repeatable(self):
        candidate = candidate_grid(2)[0]
        rows = np.column_stack((
            np.linspace(0.0, 1.0, 12),
            np.linspace(1.0, 0.0, 12),
        ))
        with self.assertRaisesRegex(SourcePipelineError, "^BACKBONE_NOT_ADMISSIBLE$"):
            _repeat_fit_candidate(
                _ChangingReconstructionModel,
                candidate,
                rows,
                rows,
                lambda seed: None,
            )

    def test_wrong_fitted_model_contract_is_terminal_and_stops_fold_loop(self):
        class WrongModel(_ZeroReconstructionModel):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.model = type("Inner", (), {"layers": []})()
                self.layers = [999]
                self.code_size = kwargs["code_size"]
                self.epochs = kwargs["epochs"]
                self.batch_size = kwargs["batch_size"]
                self.loss_name = kwargs["loss_name"]
                self.noise = kwargs["noise"]
                self.callbacks = []
                self.epochs_completed = kwargs["epochs"]

        entities = tuple(_entity(f"role-{index}", rows=2424, pseudo_target=True)
                         for index in range(6))
        seeds = []
        with self.assertRaisesRegex(SourcePipelineError, "^BACKBONE_NOT_ADMISSIBLE$"):
            run_source_stratum(entities, model_factory=WrongModel, seed_fn=seeds.append)
        self.assertEqual(seeds, [17])

    def test_wrong_fitted_model_contract_is_terminal_during_final_fit(self):
        class WrongModel(_ZeroReconstructionModel):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.model = type("Inner", (), {"layers": []})()
                self.layers = [999]
                self.code_size = kwargs["code_size"]
                self.epochs = kwargs["epochs"]
                self.batch_size = kwargs["batch_size"]
                self.loss_name = kwargs["loss_name"]
                self.noise = kwargs["noise"]
                self.callbacks = []
                self.epochs_completed = kwargs["epochs"]

        entities = tuple(_entity(f"role-{index}", rows=300) for index in range(6))
        with self.assertRaisesRegex(SourcePipelineError, "^BACKBONE_NOT_ADMISSIBLE$"):
            _fit_final_model(entities, candidate_grid(2)[0], WrongModel,
                             lambda seed: None)

    def test_final_scoring_shape_violation_is_phase_wide(self):
        class WrongFinalScoreShape(_ZeroReconstructionModel):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.predict_count = 0

            def predict(self, values, **kwargs):
                self.predict_count += 1
                if self.predict_count == 1:
                    return np.zeros_like(values)
                return np.zeros((len(values), values.shape[1] + 1), dtype=np.float32)

        entities = tuple(_entity(f"role-{index}", rows=300) for index in range(6))
        with self.assertRaisesRegex(SourcePipelineError, "^BACKBONE_NOT_ADMISSIBLE$"):
            _fit_final_model(entities, candidate_grid(2)[0], WrongFinalScoreShape,
                             lambda seed: None)

    def test_full_source_run_uses_injected_factory_and_safe_summary(self):
        entities = tuple(
            _entity(f"role-{index}", rows=2424, pseudo_target=True)
            for index in range(6)
        )
        seeds = []
        result = run_source_stratum(
            entities,
            model_factory=_ZeroReconstructionModel,
            seed_fn=seeds.append,
        )
        self.assertEqual(result.summary.status, "SOURCE_MODEL_READY")
        self.assertEqual(result.summary.source_entity_count, 6)
        self.assertEqual(result.summary.common_heldout_entity_count, 6)
        self.assertEqual(result.summary.recall_min_effective, 1.0)
        self.assertEqual(len(result.summary.detector_metrics), 4)
        self.assertEqual(len(result.summary.readiness_metrics), 228)
        self.assertEqual(len(result.artifacts.final_scores), 6)
        self.assertEqual(len(seeds), 5 * 4 * 2 + 1)
        safe = result.safe_summary
        self.assertNotIn("role-0", repr(safe))
        self.assertNotIn("features", safe)
        self.assertEqual(safe["oof_score_hash"], result.summary.oof_score_hash)
        diagnostics = {}
        run_source_stratum(
            entities, model_factory=_ZeroReconstructionModel, seed_fn=lambda seed: None,
            diagnostic_sink=diagnostics,
        )
        self.assertEqual(diagnostics["status"], "SOURCE_MODEL_READY")
        self.assertEqual(len(diagnostics["outer_fold_outcomes"]), 5)
        self.assertEqual(len(diagnostics["readiness_candidate_summaries"]), 228)
        self.assertTrue(diagnostics["readiness_trajectories"])

    def test_zero_readiness_success_retains_candidate_and_trajectory_audit(self):
        entities = tuple(_entity(f"pseudo-{index}", rows=2424, pseudo_target=True)
                         for index in range(4))
        score_values = np.linspace(0.0, 1.0, 2424)
        score_map = {entity.role_digest: score_values.copy() for entity in entities}
        diagnostics = {}
        from research.p5_0b3.scripts.source_evaluator import SuffixMetrics
        with patch("research.p5_0b3.scripts.source_pipeline._suffix_metrics",
                   return_value=SuffixMetrics(1.0, 0.0, 100, 1, 0)):
            with self.assertRaisesRegex(SourcePipelineError, "^SOURCE_MODEL_NOT_EVALUABLE$"):
                _readiness_selection(entities, score_map, 1.0, diagnostics)
        self.assertEqual(diagnostics["readiness_selection"], "ZERO_JOINT_SUCCESS")
        self.assertEqual(len(diagnostics["readiness_candidate_summaries"]), 228)
        self.assertTrue(all(item["joint_success_count"] == 0
                            for item in diagnostics["readiness_candidate_summaries"]))
        self.assertEqual(len(diagnostics["readiness_task_outcomes"]), 4 * 228)
        self.assertEqual(len(diagnostics["readiness_trajectories"]), 4 * 228)

    def test_overflowing_heldout_and_final_rows_are_nan_with_safe_count(self):
        entities = [_entity(f"role-{index}", rows=2424, pseudo_target=True)
                    for index in range(6)]
        entities[0].features[2410, 0] = 1e300
        result = run_source_stratum(
            entities, model_factory=_ZeroReconstructionModel, seed_fn=lambda seed: None
        )
        digest = entities[0].role_digest
        self.assertTrue(np.isnan(result.artifacts.selected_oof_scores[digest][2410]))
        self.assertTrue(np.isnan(result.artifacts.final_scores[digest][2410]))
        self.assertGreaterEqual(result.safe_summary["invalid_score_row_count"], 2)
        self.assertEqual(result.safe_summary["invalid_score_reason"], "INVALID_SCORE_ROW")

    def test_fold_assignment_matches_protocol_salt(self):
        entities = tuple(_entity(f"role-{index}", rows=300) for index in range(6))
        plan = build_fold_plan(entities)
        ranked = sorted(
            (
                hashlib.sha256(
                    ("P5-0B2-SOURCE-FOLD-v1|" + entity.role_digest).encode("utf-8")
                ).hexdigest(),
                entity.role_digest,
            )
            for entity in entities
        )
        expected = {digest: rank % 5 for rank, (_, digest) in enumerate(ranked)}
        self.assertEqual(dict(plan.assignments), expected)


if __name__ == "__main__":
    unittest.main()
