import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import readiness


class ReadinessTests(unittest.TestCase):
    def test_grid_count_order_and_canonical_ids(self):
        grid = readiness.enumerate_candidates()
        self.assertEqual(len(grid), 228)
        self.assertEqual([c.family for c in grid[:8]], [
            "fixed_n", "fixed_n", "fixed_n", "fixed_n", "fixed_n",
            "always_ready", "maximum_horizon", "threshold_stability",
        ])
        self.assertEqual(grid[0].candidate_id, 'fixed_n|{"look":144}')
        self.assertEqual(grid[5].candidate_id, "always_ready|{}")
        self.assertIn('"eps":0.10', next(c.candidate_id for c in grid
                                           if c.family == "threshold_stability" and
                                           c.parameters["eps"] == 0.10))
        self.assertIn('"median_change_max":0.20', next(c.candidate_id for c in grid
                                                           if c.family == "marginal_gain_plateau" and
                                                           c.parameters["median_change_max"] == 0.20))
        self.assertEqual(grid[-1].family, "never_ready")
        ands = [c for c in grid if c.family == "and"]
        self.assertEqual(len(ands), 192)
        self.assertTrue(all(tuple(sorted(c.components)) == c.components for c in ands))
        self.assertTrue(all(c.candidate_id == readiness._canonical_id("and", c.parameters) for c in ands))
        self.assertEqual(len({c.candidate_id for c in grid}), 228)

    def test_shared_support_and_fixed_baselines(self):
        grid = readiness.enumerate_candidates()
        prefixes = {144: np.arange(144), 288: np.arange(288), 576: np.arange(576),
                    1152: np.arange(1152), 2304: np.arange(2304)}
        fixed144 = readiness.evaluate_candidate(grid[0], prefixes, iqr_source=1.0)
        self.assertIsNone(fixed144.ready_look)
        always = readiness.evaluate_candidate(grid[5], prefixes, iqr_source=1.0)
        self.assertEqual(always.ready_look, 288)
        self.assertEqual([x.supported for x in always.results], [False, True])
        maximum = readiness.evaluate_candidate(grid[6], prefixes, iqr_source=1.0)
        self.assertEqual(maximum.ready_look, 2304)
        never = readiness.evaluate_candidate(grid[-1], prefixes, iqr_source=1.0)
        self.assertIsNone(never.ready_look)

    def test_ks_and_hold_forward_calculations(self):
        self.assertEqual(readiness.two_sample_ks([0, 0, 1, 1], [0, 1, 1, 1]), 0.25)
        values = np.ones(264)
        prefixes = {288: values}
        candidate = next(c for c in readiness.enumerate_candidates()
                         if c.family == "hold_forward_exceedance" and c.parameters == {
                             "consecutive": 1, "exceedance_max": 0.01
                         })
        result = readiness.evaluate_candidate(candidate, prefixes, iqr_source=1.0)
        self.assertTrue(result.results[1].supported)
        self.assertEqual(result.results[1].statistic, 0.0)
        self.assertEqual(result.ready_look, 288)

    def test_consecutive_reset_and_ready_freeze(self):
        high = lambda n: np.concatenate((np.full(int(n * 0.02), 100.0),
                                         np.ones(n - int(n * 0.02))))
        prefixes = {288: np.ones(288), 576: high(576),
                    1152: np.ones(1152), 2304: high(2304)}
        candidate = next(c for c in readiness.enumerate_candidates()
                         if c.family == "threshold_stability" and
                         c.parameters == {"consecutive": 2, "eps": 0.01})
        trajectory = readiness.evaluate_candidate(candidate, prefixes, iqr_source=1.0)
        self.assertIsNone(trajectory.ready_look)

        stable = {look: np.linspace(1.0, 2.0, look) for look in readiness.SCHEDULED_LOOKS}
        always = readiness.enumerate_candidates()[5]
        trajectory = readiness.evaluate_candidate(always, stable, iqr_source=1.0)
        self.assertEqual(trajectory.ready_look, 288)
        self.assertEqual(trajectory.frozen_threshold, readiness.empirical_q99(stable[288]))
        self.assertEqual(len(trajectory.results), 2)
        self.assertEqual(trajectory.results[-1].threshold, trajectory.frozen_threshold)

    def test_threshold_nonpositive_transition_is_reset(self):
        prefixes = {288: -np.ones(288), 576: -np.ones(576),
                    1152: -np.ones(1152), 2304: -np.ones(2304)}
        candidate = next(c for c in readiness.enumerate_candidates()
                         if c.family == "threshold_stability" and
                         c.parameters == {"consecutive": 2, "eps": 0.01})
        result = readiness.evaluate_candidate(candidate, prefixes, iqr_source=1.0)
        self.assertIsNone(result.ready_look)
        self.assertEqual([r.run_length for r in result.results], [0, 0, 0, 0, 0])

    def test_staggered_conjunction_latches_first_ready_components(self):
        # Threshold stability first becomes READY at 1152; the permissive KS
        # rule is READY at 288. Their conjunction fires at 1152.
        prefixes = {look: np.full(look, 2.0) for look in readiness.SCHEDULED_LOOKS}
        grid = readiness.enumerate_candidates()
        threshold = next(c for c in grid if c.family == "threshold_stability" and
                         c.parameters == {"consecutive": 2, "eps": 0.10})
        ks = next(c for c in grid if c.family == "score_distribution_stability" and
                  c.parameters == {"consecutive": 1, "ks_max": 0.20})
        components = tuple(sorted((threshold.candidate_id, ks.candidate_id)))
        params = {"left": components[0], "right": components[1]}
        conjunction = readiness.Candidate("and", params, readiness._canonical_id("and", params), components)
        self.assertEqual(readiness.evaluate_candidate(threshold, prefixes, iqr_source=1).ready_look, 1152)
        self.assertEqual(readiness.evaluate_candidate(ks, prefixes, iqr_source=1).ready_look, 288)
        result = readiness.evaluate_candidate(conjunction, prefixes, iqr_source=1)
        self.assertEqual(result.ready_look, 1152)
        self.assertEqual(result.frozen_threshold, readiness.empirical_q99(prefixes[1152]))


if __name__ == "__main__":
    unittest.main()
