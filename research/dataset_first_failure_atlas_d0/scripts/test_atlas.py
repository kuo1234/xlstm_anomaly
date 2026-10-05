import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd
from atlas import keyed,summaries,pareto,RULES,ROOT,RESULT
from select_sentinels import eligible,choose
from semantics_trace import trace_swknn,trace_leap


class AtlasTests(unittest.TestCase):
    def test_duplicate_keys_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.csv';p.write_text('file,score\nx,0.1\nx,0.2\n')
            with self.assertRaises(AssertionError):keyed(p)

    def test_family_weight_is_not_series_weight(self):
        d=pd.DataFrame({'family':['large']*10+['small'],'portfolio_gap':[.8]*10+[-.2]})
        s=summaries(d)
        self.assertAlmostEqual(s['equal_family_mean_gap'],.3)
        self.assertAlmostEqual(s['series_mean_gap'],7.8/11)
        self.assertEqual(s['families'],2)

    def test_pareto_strict_dominance_and_ties(self):
        d=pd.DataFrame({'method':['A','B','C','D','E'],'auc_pr':[.9,.8,.9,.9,.5],'throughput':[1,3,1,.5,2]})
        self.assertEqual(pareto(d),['A','B','C'])

    def test_sentinel_thresholds_and_no_oracle_column(self):
        d=pd.DataFrame({'portfolio_gap':[.05,.049,.10],'cross_pair_stream_win_share':[.75,1,.5],'streaming_lomo_min_gap':[.02,.2,.2]})
        self.assertEqual(eligible(d,'robust_streaming_win').tolist(),[True,False,False])
        d['oracle_gap']=[-100,1000,1000]
        self.assertEqual(eligible(d,'robust_streaming_win').tolist(),[True,False,False])

    def test_spearman_average_ties_without_scipy(self):
        a=pd.Series([1,1,2,3]);b=pd.Series([1,2,3,4])
        self.assertAlmostEqual(a.rank().corr(b.rank()),.9486832980505138)

    def test_no_model_wrapper_trace_replay_and_lag(self):
        sw=trace_swknn();leap=trace_leap()
        self.assertEqual(sw['backend_rows_consumed'],449*64)
        self.assertEqual(sw['maximum_ingestions_per_observation'],64)
        self.assertEqual(leap['backend_rows_consumed'],256)
        self.assertEqual(leap['batch_availability_lag_max'],31)
        self.assertEqual(leap['unemitted_tail_points'],1)

    def test_real_sentinel_quotas_known_duplicates_and_no_D1(self):
        d=pd.read_csv(RESULT/'series_atlas.csv');selected,status=choose(d)
        self.assertEqual(status['selected_count'],12);self.assertTrue(status['family_target_met']);self.assertFalse(status['rules_relaxed']);self.assertFalse(status['D1_executed'])
        self.assertEqual(len(set(r['duplicate_group'] for r in selected)),12)
        self.assertEqual(len(set(r['file'] for r in selected)),12)
        for r in selected:self.assertEqual(r['status'],'CONDITIONAL_D1_CANDIDATE_NOT_AUTHORIZED')

    def test_oracle_reproduction_and_composition(self):
        d=json.loads((RESULT/'oracle_envelope.json').read_text())
        self.assertEqual((d['ALL_RELEASED']['positive_series'],d['ALL_RELEASED']['negative_series']),(22,158))
        self.assertEqual((d['TSB_DRIFT']['positive_series'],d['TSB_DRIFT']['negative_series']),(18,57))
        self.assertEqual((d['NON_DRIFT']['positive_series'],d['NON_DRIFT']['negative_series']),(4,101))
        frame=pd.read_csv(RESULT/'series_atlas.csv')
        self.assertEqual(set(frame[frame.features>80].family),{'OPPORTUNITY'})
        self.assertEqual(int(frame.seq_anomaly.sum()),180)
        self.assertTrue(frame[frame.point_anomaly.eq(1)].seq_anomaly.eq(1).all())


if __name__=='__main__':unittest.main()
