"""CPU-only C3 authorization/reporting regression tests; never launches a model."""
import json
import unittest
from contextlib import ExitStack
import numpy as np
from unittest.mock import patch
import phase_c3 as c3
from phase_c3_finalize import stats


class C3Tests(unittest.TestCase):
    def fixture_pilot(self,adaptation_changes):
        rows = []
        for seed in (0,1):
            init = dict(loaded_backbone_sha256='same-backbone',
                adaptation_combined_sha256=f'adaptation-{seed if adaptation_changes else 0}',
                global_rng_before_adapter_sha256=f'before-{seed}',global_rng_after_adapter_sha256=f'after-{seed}')
            audit = dict(seed_initialization=init,candidate={},committed={},gradient_exposure={},queues={},update_count=0,pending_total=0)
            rows.append(dict(seed=seed,error=None,audit=audit,resolved_config=f'SEED: {seed}\n',
                checkpoint_sha256='same',final_model_sha256='same-model',observed={'AUROC':.5}))
        events = dict(selection_and_commit_events=[],optimizer_steps=[])
        with ExitStack() as stack:
            stack.enter_context(patch.object(c3,'record',side_effect=lambda m,a,s:rows[s]))
            stack.enter_context(patch.object(c3,'trace',return_value=events))
            stack.enter_context(patch.object(c3.v2,'record',return_value=rows[0]))
            stack.enter_context(patch.object(c3.v2,'events',return_value=events))
            stack.enter_context(patch.object(c3.v2,'score_path',return_value='fixture-only'))
            stack.enter_context(patch.object(c3.np,'load',return_value=np.array([1.,2.])))
            stack.enter_context(patch.object(c3,'digest',return_value='same-score-hash'))
            return c3.pilot()

    def test_rng_metadata_only_is_seed_inert(self):
        result = self.fixture_pilot(False)
        self.assertFalse(result['checks']['rng_before_equal'])
        self.assertEqual(result['status'],'SEED-INERT')

    def test_adaptation_initialization_change_is_seed_active(self):
        result = self.fixture_pilot(True)
        self.assertTrue(result['checks']['scores_equal'])
        self.assertEqual(result['status'],'SEED-ACTIVE')

    def test_inert_pilot_locks_expansion(self):
        with patch.object(c3,'pilot',return_value={'status':'SEED-INERT'}):
            for seed in (2,3,4):
                with self.assertRaises(AssertionError):
                    c3.authorize('SMD_1-8','5.0',seed)

    def test_active_pilot_allows_only_fixed_expansion(self):
        with patch.object(c3,'pilot',return_value={'status':'SEED-ACTIVE'}):
            for machine in ('SMD_1-8','SMD_2-1'):
                for alpha in ('0.5','1.0','5.0'):
                    c3.authorize(machine,alpha,4)
            with self.assertRaises(AssertionError):
                c3.authorize('SMD_2-1','0.5',0)  # sealed row must be reused
            c3.authorize('SMD_1-8','1.0',0)  # missing-audit integrity exception

    def test_invalid_seed_and_config_rejected(self):
        for machine,alpha,seed in [('SMD_1-8','5.0',5),('SMD_1-8','5.0',-1),
                                  ('SMD_1-8','2.0',1),('SMD_9-9','5.0',1)]:
            with self.assertRaises(AssertionError):
                c3.authorize(machine,alpha,seed)

    def test_empty_contamination_stays_na(self):
        r = stats([None]*5)
        self.assertEqual(r['n'],0)
        self.assertIsNone(r['mean'])
        self.assertIsNone(r['sample_sd'])
        self.assertEqual(stats([0.0])['mean'],0.0)
        self.assertIsNone(stats([0.0])['sample_sd'])

    def test_within_condition_sample_sd(self):
        r = stats([0,1,2,3,4])
        self.assertEqual(r['n'],5)
        self.assertEqual(r['mean'],2)
        self.assertAlmostEqual(r['sample_sd'],2.5**0.5)


if __name__=='__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(C3Tests))
    (c3.REPORT/'cpu_test_results.json').write_text(json.dumps(dict(tests_run=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),successful=result.wasSuccessful(),
        scope='CPU-only authorization/reporting tests; patched gate statuses are test fixtures, not experimental evidence'),indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
