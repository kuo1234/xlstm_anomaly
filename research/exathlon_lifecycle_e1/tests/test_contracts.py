import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
import pandas as pd
from prepare import INPUTS,FEATURES,EXEC,features
from metrics import summarize
from models import target_ids
class Contracts(unittest.TestCase):
    def test_prefix_causal_features_with_gap_sentinel_and_duplicate(self):
        r=pd.DataFrame({s:np.arange(70,dtype=float)+2 for s in INPUTS});r['t']=np.arange(70)+1000
        r.loc[20,INPUTS[0]]=-1;r=r.drop(30);r=pd.concat([r.iloc[:10],r.iloc[[9]],r.iloc[10:]],ignore_index=True)
        t,x,o=features(r);tt,xx,oo=features(r[r.t<=1040])
        np.testing.assert_allclose(x[t<=1040],xx,equal_nan=True);np.testing.assert_array_equal(o[t<=1040],oo)
        self.assertFalse(o[t==1030][0]);self.assertEqual(len(tt),41)
    def test_no_initial_future_fill(self):
        r=pd.DataFrame({s:[-1,3,4] for s in INPUTS});r['t']=[0,1,2]
        _,x,_=features(r);self.assertFalse(np.isfinite(x[0]).any())
    def test_inactive_executor_does_not_reenter_average_via_fill(self):
        r=pd.DataFrame({s:[1,2,3] for s in INPUTS});r['t']=[0,1,2]
        r['1_'+EXEC[0]]=[100,-1,-1]
        _,x,_=features(r)
        col=FEATURES.index('diff_avg_'+EXEC[0])
        self.assertAlmostEqual(float(x[1,col]),2-(100+4)/5,places=5)
    def test_history_excludes_target_and_cannot_cross_missing_features(self):
        x=np.ones((8,2));ids=target_ids(x,np.ones(8,bool),3);self.assertEqual(ids.tolist(),[3,4,5,6,7])
        x[3]=np.nan;self.assertEqual(target_ids(x,np.ones(8,bool),3).tolist(),[7])
    def test_raw_contrast_and_effect_only(self):
        t=np.arange(0,450);s=np.zeros(len(t));s[401:431]=3
        r=summarize(t,s,350,400,430,2,1)
        self.assertEqual(r['Delta_effect'],3);self.assertTrue(r['effect_only_alarm']);self.assertTrue(r['raw_eligible']);self.assertEqual(r['detection_delay'],51)
    def test_missing_root_score_cannot_be_effect_only(self):
        t=np.arange(450);s=np.zeros(450);s[380]=np.nan;s[401:431]=3
        r=summarize(t,s,350,400,430,2,1)
        self.assertIsNone(r['effect_only_alarm']);self.assertIsNone(r['detection_delay'])
    def test_unobserved_overlap_censors_delay(self):
        t=np.arange(450);s=np.zeros(450);s[380]=np.nan;s[401:431]=3
        r=summarize(t,s,350,400,430,2,1,others=[(380,380)])
        self.assertEqual(r['rci_overlap_excluded'],1);self.assertIsNone(r['detection_delay'])
    def test_out_of_trace_coverage_not_complete(self):
        r=summarize(np.arange(20),np.zeros(20),5,30,35,2,1)
        self.assertLess(r['rci_coverage'],1);self.assertIsNone(r['effect_only_alarm']);self.assertTrue(r['recovery_right_censored'])
    def test_degenerate_scale_unavailable(self):
        r=summarize(np.arange(450),np.zeros(450),350,400,430,2,0)
        self.assertIsNone(r['Delta_effect']);self.assertFalse(r['raw_eligible'])
if __name__=='__main__':unittest.main()
