import unittest,sys,json,inspect,tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np,torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from p10_left_point_data import OUT,UP,check_upstream,verify
from p10_left_point_model import Left,create,endpoint,windows,MAPS
from p10_left_point_train import fit_scaler,HealthyWindows
class TestLEFT(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  torch.set_num_threads(2);torch.manual_seed(71);cls.models={}
  for name in ['primary','robustness']:
   c=json.loads((OUT/f'left_config_{name}.json').read_text());cls.models[name]=create(c,'cpu').eval()
 def test_pinned_config_enc_in_only(self):check_upstream()
 def test_instrumentation_exact_parity_both_anchors(self):
  from types import SimpleNamespace
  for name,m in self.models.items():
   orig=Left(SimpleNamespace(**json.loads((OUT/f'left_config_{name}.json').read_text()))).eval();orig.load_state_dict(m.state_dict());x=torch.randn(2,192,53)
   with torch.no_grad():a,_=orig.infer(x,None,None,None);b,_=m.infer(x,None,None,None)
   self.assertTrue(torch.equal(a,b));self.assertEqual(tuple(b.shape),(2,192,53));self.assertEqual(set(m.last_components),set(MAPS))
 def test_total_reconstructs_official_formula(self):
  from models.Left.Tools import moving_average_1d
  for m in self.models.values():
   with torch.no_grad():m.infer(torch.randn(2,192,53),None,None,None)
   c=m.last_components;cycle=moving_average_1d(m.alpha_freq*c['score_freq']+m.alpha_time*c['score_time']+m.alpha_gate*c['prototype_gate']+m.alpha_cons_s*c['cross_path_consistency'],m.smooth_k)
   torch.testing.assert_close(c['score_total'],m.alpha_cycle_s*cycle+m.alpha_ms_s*c['score_ms'],rtol=0,atol=0)
 def test_future_modification_does_not_change_past_point(self):
  x=np.random.default_rng(11).normal(size=(220,53));z=x.copy();z[201:]*=1000
  for m in self.models.values():
   a=endpoint(m,x,np.array([192,200]));b=endpoint(m,z,np.array([192,200]))
   for k in MAPS:np.testing.assert_array_equal(a[k],b[k])
 def test_eval_does_not_update_weights_or_prototypes(self):
  for m in self.models.values():
   before={k:v.clone() for k,v in m.state_dict().items()};endpoint(m,np.ones((200,53)),np.array([192,200]))
   for k,v in m.state_dict().items():self.assertTrue(torch.equal(v,before[k]))
 def test_endpoint_has_no_outside_window(self):
  x=np.arange(250*53).reshape(250,53);np.testing.assert_array_equal(windows(x,[200],192)[0],x[8:200])
 def test_train_scaler_only_train_arrays(self):
  a=[np.zeros((600,53)),np.ones((600,53))];mu,sd=fit_scaler(a);np.testing.assert_array_equal(mu,np.ones(53)*.5);self.assertTrue(np.isfinite(sd).all());self.assertTrue((sd>=.02).all())
 def test_no_window_bridges_physical_run(self):
  d=HealthyWindows([np.zeros((200,53)),np.ones((200,53))],192)
  for i in range(len(d)):self.assertTrue(torch.all(d[i]==0) or torch.all(d[i]==1))
 def test_training_cannot_access_event_or_truth(self):
  import p10_left_point_train as t
  s=Path(t.__file__).read_text();self.assertNotIn('event_numeric',s);self.assertNotIn('evaluator_metadata',s);self.assertNotIn('timestamps',s);self.assertNotIn('states(',s)
 def test_healthy_numeric_manifest_no_source_labels(self):
  import p10_left_point_data as d
  s=inspect.getsource(d.healthy_numeric);self.assertIn('healthy_numeric_manifest.json',s);self.assertNotIn('healthy_train_manifest.json',s)
 def test_missing_seal_blocks_truth(self):
  import p10_left_point_data as d
  with tempfile.TemporaryDirectory() as t,patch.object(d,'OUT',Path(t)),patch.object(d,'check_upstream'):
   with self.assertRaises(FileNotFoundError):verify()
 def test_primary_separate_from_event_metadata(self):
  import p10_left_point_run as r
  s=Path(r.__file__).read_text();self.assertNotIn('states(',s);self.assertNotIn("np.load(RAW/'arrays'/f",s)
if __name__=='__main__':unittest.main()
