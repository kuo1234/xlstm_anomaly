"""Synthetic-only SOURCE evaluator contract tests."""
import math
import unittest

import numpy as np

from research.p5_0b3.scripts.readiness import Candidate, enumerate_candidates
from research.p5_0b3.scripts.source_evaluator import (
    SourceNotEvaluable, SuffixMetrics, TaskOutcome,
    effective_recall_floor, evaluate_suffix, fixed_n_threshold,
    inclusive_interval_mask, select_candidate,
    source_fixed_n_baselines, summarize_candidate, type7_quantile,
)


class SourceEvaluatorTests(unittest.TestCase):
    def test_suffix_strict_threshold_inclusive_masks_and_duplicate_reports(self):
        scores = [1.0, 2.0, 3.0, np.nan, 4.0]
        normal = [True, True, False, True, True]
        report = [False, False, True, False, True]
        result = evaluate_suffix(scores, normal, [report, report, [False] * 5], 2.0)
        self.assertEqual(result.normal_score_count, 3)
        self.assertEqual(result.normal_pointwise_fpr, 1 / 3)
        # score == threshold is not an alarm; each repeated report is retained.
        self.assertEqual(result.eligible_fault_report_count, 2)
        self.assertEqual(result.hit_fault_report_count, 2)
        self.assertEqual(result.eligible_fault_report_recall, 1.0)

    def test_interval_mask_includes_both_endpoints(self):
        np.testing.assert_array_equal(
            inclusive_interval_mask([2304, 2305, 2306, 2307], 2305, 2306),
            [False, True, True, False],
        )

    def test_empty_finite_denominators_are_nan(self):
        result = evaluate_suffix([np.nan], [True], [[True]], 0.0)
        self.assertTrue(math.isnan(result.normal_pointwise_fpr))
        # The report overlaps a suffix raw observation, so it remains in the
        # denominator and is a miss when that observation has no score.
        self.assertEqual(result.eligible_fault_report_recall, 0.0)

    def test_type7_quantiles_fixed_n_diagnostics_and_effective_floor(self):
        self.assertEqual(type7_quantile([0, 10], 0.1), 1.0)
        self.assertEqual(type7_quantile([0, 10], 0.9), 9.0)
        self.assertTrue(math.isnan(fixed_n_threshold([0, 10])))
        self.assertAlmostEqual(fixed_n_threshold(np.arange(200)), 197.01)
        self.assertTrue(math.isnan(type7_quantile([], 0.1)))
        metrics = [
            SuffixMetrics(.01, .2, 100, 5, 1),
            SuffixMetrics(.02, .6, 100, 5, 3),
            SuffixMetrics(.03, 1., 100, 5, 5),
            SuffixMetrics(.04, .8, 100, 5, 4),
        ]
        q10, q90 = source_fixed_n_baselines(metrics)
        self.assertAlmostEqual(q10, .32)
        self.assertAlmostEqual(q90, .037)
        self.assertEqual(effective_recall_floor(q10), .5)
        self.assertEqual(effective_recall_floor(.75), .75)
        self.assertTrue(math.isnan(effective_recall_floor(math.nan)))
        empty_q10, empty_q90 = source_fixed_n_baselines([])
        self.assertTrue(math.isnan(empty_q10))
        self.assertTrue(math.isnan(empty_q90))

    def test_primary_joint_boundaries_are_inclusive(self):
        c = Candidate("fixed_n", {"look": 2304}, "fixed")
        exactly_on_limits = TaskOutcome(
            True, SuffixMetrics(.03, .5, 100, 10, 5), 2304, 64.0)
        summary = summarize_candidate(c, [exactly_on_limits], recall_floor=.5)
        self.assertEqual(summary.joint_success_count, 1)
        self.assertEqual(summary.joint_success_fraction, 1.0)
        self.assertEqual(summary.mean_acquisition_cost, 1.0)

    def test_never_ready_cost_and_zero_tie_metrics(self):
        c = Candidate("never_ready", {}, "never")
        task = TaskOutcome(False, SuffixMetrics(.9, .9, 1, 1, 1))
        result = summarize_candidate(c, [task], recall_floor=.5)
        self.assertEqual(result.mean_acquisition_cost, 1.0)
        self.assertEqual(result.macro_fault_report_recall, 0.0)
        self.assertEqual(result.macro_normal_pointwise_fpr, 0.0)
        self.assertEqual(result.joint_success_count, 0)

    def test_candidate_lexicographic_tie_break_and_lexical_final_tie(self):
        candidates = enumerate_candidates()
        outcomes = {
            candidate.candidate_id: [
                TaskOutcome(True, SuffixMetrics(.02, .6, 100, 10, 6), 2304, 64)
                for _ in range(4)
            ]
            for candidate in candidates
        }
        # Equal success fraction: lower cost wins, then macro recall, then FPR.
        cheap_id = next(c.candidate_id for c in candidates
                        if c.family == "fixed_n" and c.parameters["look"] == 576)
        outcomes[cheap_id] = [
            TaskOutcome(True, SuffixMetrics(.02, .6, 100, 10, 6), 576, 0.0)
            for _ in range(4)
        ]
        selected = select_candidate(candidates, outcomes, recall_floor=.5)
        self.assertEqual(selected.selected.candidate_id, cheap_id)

        tied = {
            candidate.candidate_id: [
                TaskOutcome(True, SuffixMetrics(.02, .6, 100, 10, 6), 2304, 64)
                for _ in range(4)
            ]
            for candidate in candidates
        }
        winner_id = next(c.candidate_id for c in candidates
                         if c.family == "fixed_n" and c.parameters["look"] == 576)
        tied[winner_id] = [
            TaskOutcome(True, SuffixMetrics(.01, .8, 100, 10, 8), 2304, 64)
            for _ in range(4)
        ]
        picked = select_candidate(candidates, tied, recall_floor=.5)
        self.assertEqual(picked.selected.candidate_id, winner_id)

    def test_candidate_tie_break_recall_then_fpr_then_conjuncts(self):
        candidates = enumerate_candidates()
        baseline = TaskOutcome(True, SuffixMetrics(.02, .6, 100, 10, 6), 2304, 64)
        outcomes = {c.candidate_id: [baseline] * 4 for c in candidates}
        by_look = {c.parameters["look"]: c.candidate_id for c in candidates
                   if c.family == "fixed_n"}

        # Recall precedes FPR after joint fraction and cost tie.
        outcomes[by_look[576]] = [
            TaskOutcome(True, SuffixMetrics(.01, .6, 100, 10, 6), 2304, 64)
            for _ in range(4)
        ]
        outcomes[by_look[1152]] = [
            TaskOutcome(True, SuffixMetrics(.02, .8, 100, 10, 8), 2304, 64)
            for _ in range(4)
        ]
        self.assertEqual(select_candidate(candidates, outcomes, recall_floor=.5).selected.candidate_id,
                         by_look[1152])

        # With recall tied, lower macro FPR wins.
        outcomes[by_look[576]] = [
            TaskOutcome(True, SuffixMetrics(.02, .7, 100, 10, 7), 2304, 64)
            for _ in range(4)
        ]
        outcomes[by_look[1152]] = [
            TaskOutcome(True, SuffixMetrics(.01, .7, 100, 10, 7), 2304, 64)
            for _ in range(4)
        ]
        self.assertEqual(select_candidate(candidates, outcomes, recall_floor=.5).selected.candidate_id,
                         by_look[1152])

        # Identical metrics fall through to fewer conjuncts and then lexical ID.
        and_id = next(c.candidate_id for c in candidates if c.family == "and")
        plain_id = next(c.candidate_id for c in candidates if c.family == "fixed_n" and
                        c.parameters["look"] == 576)
        identical = [TaskOutcome(True, SuffixMetrics(.01, .7, 100, 10, 7), 2304, 64)] * 4
        outcomes = {c.candidate_id: [baseline] * 4 for c in candidates}
        outcomes[and_id] = identical
        outcomes[plain_id] = identical
        self.assertEqual(select_candidate(candidates, outcomes, recall_floor=.5).selected.candidate_id,
                         plain_id)

    def test_all_zero_joint_success_fails_without_entity_details(self):
        candidates = enumerate_candidates()
        outcomes = {
            c.candidate_id: [
                TaskOutcome(False, SuffixMetrics(math.nan, math.nan, 0, 0, 0))
                for _ in range(4)
            ]
            for c in candidates
        }
        with self.assertRaisesRegex(SourceNotEvaluable, "SOURCE_MODEL_NOT_EVALUABLE") as raised:
            select_candidate(candidates, outcomes, recall_floor=.5)
        self.assertEqual(len(raised.exception.summaries), 228)
        self.assertTrue(all(item.joint_success_count == 0
                            for item in raised.exception.summaries))


if __name__ == "__main__":
    unittest.main()
