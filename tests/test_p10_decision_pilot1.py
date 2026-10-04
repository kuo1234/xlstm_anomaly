import unittest,sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import p10_decision_pilot1_data as D
import p10_decision_pilot1_run as R
from p10_step2f_run import scaling,summaries
class TestPilot(unittest.TestCase):
 def test_runner_isolation(self):
  s=Path(R.__file__).read_text();self.assertNotIn('states(',s);self.assertNotIn('timestamps.npy',s);self.assertNotIn('evaluator_metadata.json',s.split('def main():')[0]);self.assertNotIn('optimizer',s)
 def test_fixed_cases_features(self):
  self.assertEqual(D.CONFIG['cases'],[f'pilot0{i}' for i in range(1,7)]);self.assertEqual(D.CONFIG['features'],['log_score','cv','top5_energy']);self.assertEqual(D.CONFIG['seeds'],[11,22,33]);self.assertFalse(D.CONFIG['neural_training'])
 def test_config_m0_matches_baseline(self):
  from p10_step2f_data import CONFIG
  for k in ('seeds','ops','w','dk','k','fit_frac','sd_floor','clip','window','stride','start_end'):self.assertEqual(D.CONFIG[k],CONFIG[k])
 def test_fit_scaler_cal_invariance(self):
  fit=np.arange(53*320,dtype=float).reshape(320,53);cal=np.zeros((80,53));test=np.ones((400,53))
  for v in D.CONFIG['views']:
   a=scaling(fit,cal,test,v);b=scaling(fit,cal+1000,test*100,v);np.testing.assert_array_equal(a[2],b[2]);np.testing.assert_array_equal(a[3],b[3])
 def test_missing_seal_blocks(self):
  with tempfile.TemporaryDirectory() as t,patch.object(D,'OUT',Path(t)):
   with self.assertRaises(FileNotFoundError):D.verify()
 def test_metadata_hash_protected(self):
  self.assertIn('evaluator_metadata.json',Path(R.__file__).read_text());self.assertIn("s['protocol_files']",Path(D.__file__).read_text())
 def test_no_test_write(self):
  s=Path(R.__file__).read_text();self.assertNotIn('mem.write(Kt',s);self.assertIn("'test_writes':0",s)
 def test_top5_is_energy_not_magnitude(self):
  x=np.ones((256,53));normal={'mean':np.zeros(53),'cov':np.eye(53),'inv':np.eye(53),'rsd':np.ones(53)}
  self.assertAlmostEqual(summaries(x,normal,np.ones(53))['top5_energy'],5/53)
  x[:,:5]=10;self.assertAlmostEqual(summaries(x,normal,np.ones(53))['top5_energy'],500/548)
 def test_source_profile_nominal_prefix(self):
  profiles={'idv_init':np.zeros((3,28)).tolist(),'setpoint_init':np.array([np.ones(12),np.r_[1.05,np.ones(11)],np.ones(12)*30]).tolist(),'time_info':[[0,100,.05,0,70]]}
  item={'arm':'setpoint','path':'/SP1/tRamp_0/SpMagnitude105'};self.assertTrue(D.check_profiles(item,profiles,0))
  profiles['idv_init'][0][0]=1
  with self.assertRaises(AssertionError):D.check_profiles(item,profiles,0)
if __name__=='__main__':unittest.main()
