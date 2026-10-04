import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import p10_step2f_data as D
import p10_step2f_run as R
from p10_step1a_oracle import Phi
from p10_step2a_stream import W1S

class TestStep2f(unittest.TestCase):
 def test_runner_no_truth_or_time_loader(self):
  s=Path(R.__file__).read_text();self.assertNotIn('states(',s);self.assertNotIn('timestamps.npy',s);self.assertNotIn('evaluator_metadata.json',s)

 def test_scaler_fit_only_and_cal_never_fits(self):
  rng=np.random.default_rng(31);fit=rng.normal(size=(30,53));cal=rng.normal(size=(10,53));test=rng.normal(size=(32,53))
  for view in ['fit_only_clip','fit_only_no_clip']:
   a=R.scaling(fit,cal,test,view);b=R.scaling(fit,cal*100,test*100,view)
   np.testing.assert_array_equal(a[0][0],b[0][0]);np.testing.assert_array_equal(a[2],b[2]);np.testing.assert_array_equal(a[3],b[3])

 def test_neural_loader_and_optimizer_disabled(self):
  self.assertFalse(D.CONFIG['neural_training']);self.assertEqual(D.CONFIG['phase'],'A')
  for module in (D,R):
   s=Path(module.__file__).read_text();self.assertNotIn('import torch',s);self.assertNotIn('optimizer.step',s);self.assertNotIn('backward(',s)

 def test_memory_fits_only_fit_normal(self):
  s=Path(R.__file__).read_text();self.assertIn('ids=np.arange(w,nfit)',s);self.assertIn('norm=manifold(rfit)',s)
  self.assertNotIn('mem.write(Kc',s);self.assertNotIn('mem.write(Kt',s)

 def test_future_observations_do_not_change_past_residual(self):
  rng=np.random.default_rng(33);train=rng.normal(size=(64,53));test=rng.normal(size=(64,53));changed=test.copy();changed[32:]+=100
  phi=Phi(53,8,128,11);ids=np.arange(8,64);m=W1S(256,128,53,5);m.write(phi(train,ids),train[ids],-np.ones(len(ids),int))
  def run(te):
   ex=np.r_[train[-8:],te];return R.residuals(m,phi(ex,np.arange(8,len(ex))),te)
  np.testing.assert_array_equal(run(test)[:32],run(changed)[:32])

 def test_score_before_write_and_no_test_mutation(self):
  rng=np.random.default_rng(42);K=np.abs(rng.normal(size=(40,8)));m=W1S(100,8,53,5);m.write(K,np.zeros((40,53)),-np.ones(40,int));n=m.n
  v=np.ones((16,53))*2;r=R.residuals(m,K[:16],v)
  np.testing.assert_array_equal(r,v);self.assertEqual(m.n,n)

 def test_clipping_exact_and_constants(self):
  fit=np.tile(np.r_[-1.,1.],(53,1)).T;cal=fit.copy();test=np.zeros((2,53));test[0,0]=21;test[1,1]=-20
  z,pre,mu,sd,rs=R.scaling(fit,cal,test,'fit_only_clip');mask=np.abs(pre[2])>20
  self.assertEqual(mask.sum(),1);self.assertEqual(mask.mean(),1/106);self.assertEqual(z[2][0,0],20);self.assertEqual(z[2][1,1],-20)
  fit[:,3]=1;z,*_=R.scaling(fit,cal,test,'fit_only_clip');self.assertTrue(np.isfinite(z[0]).all())

 def test_residual_norm_rebuilds_scalar(self):
  rng=np.random.default_rng(7);r=rng.normal(size=(30,53));n=R.manifold(r);s=R.summaries(r,n,np.ones(53))
  self.assertAlmostEqual(np.exp(s['log_score']),np.linalg.norm(r,axis=1).mean());self.assertAlmostEqual(s['cv'],np.linalg.norm(r,axis=1).std()/np.linalg.norm(r,axis=1).mean())

 def test_regression_control_scaler_matches_step2e(self):
  from p10_step2a_stream import scale,CFG2A
  rng=np.random.default_rng(13);a=rng.normal(size=(30,53));b=rng.normal(size=(10,53));t=rng.normal(size=(10,53))
  z,*_=R.scaling(a,b,t,'step2e_regression_clip');old,ot=scale(np.r_[a,b],t,CFG2A)
  np.testing.assert_array_equal(np.r_[z[0],z[1]],old);np.testing.assert_array_equal(z[2],ot)

 def test_config_windows_and_seeds_fixed(self):
  c=D.CONFIG;self.assertEqual([c['window'],c['stride'],c['start_end']],[256,128,256]);self.assertEqual(c['seeds'],[11,22,33]);self.assertEqual(c['cv_diagnostic_threshold'],.10)
  self.assertEqual(json.loads((D.OUT/'representation_config.json').read_text()),c)

 def test_missing_seal_blocks_evaluation(self):
  with tempfile.TemporaryDirectory() as p,patch.object(D,'OUT',Path(p)):
   with self.assertRaises(FileNotFoundError):D.verify()

 def test_probe_fold_intervention_families_disjoint(self):
  family={'case01':'SP1','case02':'SP1','case03':'SP2','case04':'IDV1','case05':'IDV2'}
  for f in D.CONFIG['folds']:
   self.assertFalse(set(f['train'])&set(f['test']));self.assertFalse({family[c] for c in f['train']}&{family[c] for c in f['test']})

 def test_third_clean_block_close(self):
  from p10_step2b_stream import CFG2B,run_seg_policy
  self.assertEqual(CFG2B['seg_gap_blocks'],2)
  K=np.ones((64,8));V=np.r_[np.ones((16,53))*2,np.zeros((48,53))]
  def builder():
   m=W1S(200,8,53,5);m.write(np.ones((40,8)),np.zeros((40,53)),-np.ones(40,int));return m
  cfg=dict(CFG2B);ctx={'cfg':cfg,'tau':1.,'tau_low':.5,'Kt':K,'Vt':V}
  out=run_seg_policy('H_hold',builder,ctx);self.assertEqual(out['events']['discards'],1);self.assertEqual(out['written'].sum(),48)

if __name__=='__main__':unittest.main()
