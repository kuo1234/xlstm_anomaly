import dataclasses
import inspect
import tempfile
from pathlib import Path
import unittest
import numpy as np
from m0.causal import (Decision, FixedScaler, Trace, admission_audit, aligned_labels,
                       calibration_threshold, run_stream)
from m0.metrics import metrics, post_shift
from m0.synthetic import CONFIG, generate, opposite_label_control, window_strata, save_stream


class ArithmeticFixture:
    """Test spy, not a detector: score exposes mutation ordering directly."""
    def __init__(self):
        self.state = 0
        self.normalizer = 0

    def score(self,x,t):
        assert not x.flags.writeable
        return x[-1,0]+self.state+self.normalizer

    def select(self,x,t,score):
        return t%2==0

    def update(self,x,t,selected):
        self.state += 10
        return (t,) if selected else ()

    def observe_normalizer(self,x,t):
        self.normalizer += 100


class CausalTests(unittest.TestCase):
    def test_score_emit_before_all_updates(self):
        trace = run_stream(np.zeros((5,2)),ArithmeticFixture,2,window=3)
        self.assertEqual([d.score for d in trace.decisions],[0,110,220])
        self.assertEqual([e[0] for e in trace.timeline[:5]],['score','emit','select','update','normalizer'])
        with self.assertRaises(dataclasses.FrozenInstanceError):
            trace.decisions[0].score = 42

    def test_future_prefix_invariance_and_reset(self):
        x = np.zeros((100,2))
        first = run_stream(x,ArithmeticFixture,63)
        x[80:] = 123
        second = run_stream(x,ArithmeticFixture,63)
        self.assertEqual(first.decisions[:17],second.decisions[:17])
        self.assertEqual(second,run_stream(x,ArithmeticFixture,63))

    def test_label_isolation_permutation(self):
        x = np.arange(200).reshape(100,2)
        y = np.arange(100)%2
        first = run_stream(x,ArithmeticFixture,63)
        aligned_labels(first,y)
        admission_audit(first,y)
        second = run_stream(x,ArithmeticFixture,63)
        aligned_labels(second,y[::-1])
        admission_audit(second,y[::-1])
        self.assertEqual(first,second)
        self.assertNotIn('labels',inspect.signature(run_stream).parameters)

    def test_window_endpoint_and_warmup(self):
        trace = run_stream(np.zeros((5,2)),ArithmeticFixture,0,window=3)
        y = np.array([1,0,0,0,1])
        self.assertEqual([d.time for d in trace.decisions],[2,3,4])
        np.testing.assert_array_equal(aligned_labels(trace,y,3),[1,0,1])
        np.testing.assert_array_equal(aligned_labels(trace,y,3,'endpoint'),[0,0,1])

    def test_fixed_fit_scaler_and_calibration(self):
        x = np.array([[0.,2.],[2.,2.]])
        scaler = FixedScaler.fit(x)
        np.testing.assert_array_equal(scaler.scale,[1,1])
        original = scaler.mean.copy()
        scaler.transform(np.full((100,2),1e6))
        np.testing.assert_array_equal(scaler.mean,original)
        self.assertEqual(calibration_threshold(np.arange(101)),95.)
        with self.assertRaises(ValueError):
            scaler.mean.flags.writeable = True

    def test_candidate_committed_pending_denominators(self):
        trace = Trace((),(2,3),((2,3),(2,4)),())
        result = admission_audit(trace,[1,0,0,0,0],3)
        self.assertEqual(result['candidate']['rate'],.5)
        self.assertEqual(result['committed']['rate'],1.)
        self.assertEqual(result['committed']['unique_windows'],1)
        self.assertEqual(result['pending']['exposures'],1)
        self.assertEqual(result['candidate_to_commit'],[1,2])
        self.assertIsNone(admission_audit(Trace((),(),(),()),[0,0,0],3)['committed']['rate'])

    def test_bad_inputs(self):
        with self.assertRaises(ValueError):
            run_stream(np.full((100,2),np.nan),ArithmeticFixture,63)
        with self.assertRaises(ValueError):
            calibration_threshold([])


class MetricTests(unittest.TestCase):
    def test_perfect_and_reversed(self):
        self.assertEqual(metrics([0,0,1,1],[0,1,2,3],1.5)['ap'],1.)
        result = metrics([1,0],[0,1],.5)
        self.assertEqual(result['ap'],.5)
        self.assertEqual(result['auroc'],0.)
        self.assertEqual(result['pr_auc_trapezoidal'],.25)
        self.assertEqual(result['fpr'],1.)

    def test_ties_not_arbitrary_ranks(self):
        result = metrics([1,0,1,0],[1,1,1,1],1.)
        self.assertEqual(result['ap'],.5)
        self.assertEqual(result['auroc'],.5)
        self.assertEqual(result['fpr'],0.)

    def test_undefined_metrics(self):
        self.assertIsNone(metrics([0,0],[0,1],.5)['ap'])
        self.assertIsNone(metrics([1,1],[0,1],.5)['auroc'])
        self.assertIsNone(metrics([1,1],[0,1],.5)['fpr'])
        self.assertIsNone(metrics([],[],.5)['prevalence'])
        with self.assertRaises(ValueError):
            metrics([2],[0],.5)

    def test_post_shift_recovery_and_censoring(self):
        decisions = [Decision(t,0.) for t in range(256)]
        result = post_shift(decisions,np.zeros(256),1.,0)
        self.assertEqual(result['normal_n'],256)
        self.assertEqual(result['recovery_latency'],191)
        self.assertEqual(result['recovery_start_latency'],0)
        self.assertTrue(post_shift(decisions[:100],np.zeros(256),1.,0)['censored'])
        self.assertTrue(post_shift(decisions,np.ones(256),1.,0)['censored'])
        self.assertIsNone(post_shift(decisions,np.zeros(256),1.,None)['fpr'])


class GeneratorTests(unittest.TestCase):
    def test_saved_truth_separate_and_no_overwrite(self):
        stream = generate(1000,'correlation')
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'stream'
            save_stream(stream,target)
            np.testing.assert_array_equal(np.load(target/'observations.npy',allow_pickle=False),stream.observations)
            with np.load(target/'evaluator_truth.npz',allow_pickle=False) as truth:
                np.testing.assert_array_equal(truth['labels'],stream.labels)
                np.testing.assert_array_equal(truth['overlap'],stream.drift_active & stream.labels.astype(bool))
            with self.assertRaises(FileExistsError):
                save_stream(stream,target)

    def test_all_scenarios_reproducible_finite_clean_prefix(self):
        for scenario in CONFIG['scenarios']:
            with self.subTest(scenario=scenario):
                a = generate(1000,scenario)
                b = generate(1000,scenario)
                self.assertEqual(a.observations.shape,(21504,8))
                self.assertTrue(np.isfinite(a.observations).all())
                self.assertFalse(a.labels[:a.test_start].any())
                np.testing.assert_array_equal(a.observations,b.observations)
                self.assertTrue(np.isin(a.labels,[0,1]).all())

    def test_identical_observation_opposite_label(self):
        a,b = opposite_label_control()
        np.testing.assert_array_equal(a.observations,b.observations)
        np.testing.assert_array_equal(a.event_ids,b.event_ids)
        self.assertTrue(np.all(a.labels[a.event_ids>=0]==1))
        self.assertTrue(np.all(b.labels[b.event_ids>=0]==0))
        # Every paired row has contradictory labels: no observation-only rule can separate the pair.
        paired_truth = np.r_[a.labels[a.event_ids>=0],b.labels[b.event_ids>=0]]
        paired_score = np.tile(a.observations[a.event_ids>=0,0],2)
        self.assertAlmostEqual(metrics(paired_truth,paired_score,0)['ap'],.5)
        self.assertAlmostEqual(metrics(paired_truth,paired_score,0)['auroc'],.5)

    def test_schedule_types_and_no_latent_contamination(self):
        mixture = generate(1000,'stationary')
        clean = generate(1000,'stationary','none')
        mask = mixture.event_ids<0
        np.testing.assert_array_equal(mixture.observations[mask],clean.observations[mask])
        self.assertFalse(clean.labels.any())
        for kind in ('spike','collective','dependency'):
            events = [e for e in mixture.events if e['type']==kind]
            self.assertEqual(len(events),9)
            self.assertEqual({e['severity'] for e in events},{1,2,3})
            if kind!='spike':
                self.assertEqual({e['duration'] for e in events},{16,64,256})
            single = generate(1000,'stationary',kind)
            self.assertEqual(len(single.events),10)  # 9 events + separately flagged persistent stress
            for e in events:
                np.testing.assert_array_equal(single.observations[e['start']:e['end']],mixture.observations[e['start']:e['end']])

    def test_source_disjoint_folds_and_boundaries(self):
        folds = [set(CONFIG[f+'_seeds']) for f in ('train','validation','test')]
        self.assertFalse(folds[0]&folds[1] or folds[0]&folds[2] or folds[1]&folds[2])
        with self.assertRaises(ValueError):
            generate(42,'stationary')
        a = generate(1000,'recurring')
        onset = a.test_start+4096
        self.assertEqual(a.regime[onset-1],0)
        self.assertEqual(a.regime[onset],1)
        self.assertEqual(a.regime[a.test_start+8192],0)
        self.assertIn('mixed',window_strata(a))
        self.assertIn('drift',window_strata(a))
