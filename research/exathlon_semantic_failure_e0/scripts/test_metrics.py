import unittest
import numpy as np
from lifecycle_metrics import phase_masks, event_summary, normal_threshold


class LifecycleTests(unittest.TestCase):
    def test_closed_rci_and_disjoint_eei(self):
        r,e,p,a=phase_masks(np.arange(8),2,4,6)
        self.assertEqual(np.flatnonzero(r).tolist(),[2,3,4])
        self.assertEqual(np.flatnonzero(e).tolist(),[5,6])
        self.assertFalse(np.any(r&e))

    def test_point_rci_missing_is_not_effect_only_detection(self):
        v=event_summary([0,2,4,6],[0,0,10,10],[0,2,4,6],3,3,6,5,1)
        self.assertEqual(v['status'],'MISSING_RCI_SCORE')
        self.assertIsNone(v['effect_only_detection'])
        self.assertEqual(v['rci_score_count'],0)

    def test_effect_only_alarm_and_delay(self):
        v=event_summary(range(8),[0,0,0,0,0,10,10,0],range(8),2,4,6,5,2)
        self.assertEqual(v['status'],'MEASURED')
        self.assertFalse(v['root_cause_capture']);self.assertTrue(v['effect_only_detection'])
        self.assertEqual(v['detection_delay_seconds'],3)
        self.assertEqual(v['rci_vs_eei_scaled_median_gap'],-5)

    def test_future_available_scores_and_missing_eei(self):
        v=event_summary(range(6),[0,0,10,10,0,0],[0,1,5,5,4,5],2,3,None,5,1)
        self.assertEqual(v['status'],'MISSING_RCI_SCORE')
        self.assertIsNone(v['eei_median']);self.assertIsNone(v['effect_only_detection'])
        self.assertEqual(v['future_unavailable_score_count'],2)

    def test_overlap_exclusion_and_censored_recovery(self):
        v=event_summary(range(8),[0]*8,range(8),2,4,6,5,1,other_ranges=[(4,5)])
        self.assertEqual(v['rci_score_count'],2);self.assertEqual(v['eei_score_count'],1)
        self.assertEqual(v['overlap_excluded_rci_count'],1)
        self.assertTrue(v['recovery_right_censored'])

    def test_fragmentation_not_bridged_across_missing_scores(self):
        v=event_summary(range(9),[0,0,8,8,np.nan,8,8,0,0],range(9),2,6,None,5,1)
        self.assertEqual(v['rci_alarm_fragments'],2)
        self.assertEqual(v['rci_longest_alarm_run_seconds'],2)
        self.assertEqual(v['rci_valid_score_fraction'],.8)
        self.assertEqual(v['rci_alarm_dropout_rate'],0)

    def test_threshold_refuses_anomalous_calibration_labels(self):
        self.assertEqual(normal_threshold([0,1,2],[0,0,0],q=.5),1)
        with self.assertRaises(ValueError):normal_threshold([0,1,2],[0,0,1])

    def test_actual_native_ae_readout_latency_and_tail(self):
        from readout_trace import trace_native_ae
        result=trace_native_ae(n=6,w=3)
        self.assertEqual(result['max_future_window_availability_lag_seconds'],2)
        np.testing.assert_allclose(result['constant_window_score_readout'],[1,1,1,1,2/3,1/3])

    def test_missing_native_time_cannot_establish_no_root_capture(self):
        v=event_summary([0,1,2,4,5,6],[0,0,0,0,10,10],[0,1,2,4,5,6],2,4,6,5,1)
        self.assertAlmostEqual(v['rci_valid_score_fraction'],2/3)
        self.assertIsNone(v['root_cause_capture']);self.assertIsNone(v['effect_only_detection'])
        self.assertIsNone(v['detection_delay_seconds'])

    def test_missing_score_censors_first_alarm_delay(self):
        v=event_summary(range(8),[0,0,0,np.nan,0,10,10,0],range(8),2,4,6,5,1)
        self.assertIsNone(v['effect_only_detection']);self.assertIsNone(v['detection_delay_seconds'])
        self.assertEqual(v['first_observed_alarm_delay_seconds'],3)

    def test_absent_overlapping_native_instant_censors_delay(self):
        t=[0,1,2,4,5,6]
        v=event_summary(t,[0,0,0,0,10,10],t,2,4,6,5,1,other_ranges=[(3,3)])
        self.assertEqual(v['overlap_excluded_rci_count'],1)
        self.assertEqual(v['overlap_observed_rci_count'],0)
        self.assertEqual(v['first_observed_alarm_delay_seconds'],3)
        self.assertIsNone(v['detection_delay_seconds'])

    def test_off_grid_timestamp_cannot_replace_missing_native_instant(self):
        t=[0,1,2,2.5,4,5,6]
        with self.assertRaisesRegex(ValueError,'native cadence grid'):
            event_summary(t,[0,0,0,0,0,10,10],t,2,4,6,5,1)

    def test_epoch_off_grid_timestamp_is_rejected(self):
        t=np.array([0,1,2,2.5,4,5,6])+1528853422
        with self.assertRaisesRegex(ValueError,'native cadence grid'):
            event_summary(t,[0,0,0,0,0,10,10],t,t[2],t[4],t[6],5,1)


if __name__=='__main__':unittest.main()
