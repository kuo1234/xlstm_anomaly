import sys,json,inspect,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/"scripts"))
from core import LinearAE,Runtime,run_array,probe
import run,base
from eval import evaluate,recover,gate
C=json.loads((P/"configs/pilot.json").read_text())
def fixture():
 rng=np.random.default_rng(814);x=rng.normal(size=(180,4));m=LinearAE.fit(x[:100],x[100:150],C)
 # Force long candidate with a large vector orthogonal to fixed encoder.
 v=np.linalg.svd(m.encoder.T,full_matrices=True)[2][-1]*15
 high=m.mu+m.sd*v
 return x,m,high
class Pilot(unittest.TestCase):
 def test_runtime_no_label_or_identity_inputs(self):
  self.assertEqual(list(inspect.signature(Runtime.step).parameters),["self","x","t"])
  _,m,_=fixture()
  self.assertFalse(set(m.cfg)&{"arms","physical_groups","events","seeds","gates"})
  with self.assertRaises(TypeError):Runtime(m,"FROZEN").step([0]*4,1,labels=1)
  text=inspect.getsource(sys.modules["core"])
  self.assertNotIn("np.load",text);self.assertNotIn("open(",text)
 def test_score_before_write_full_state_hash(self):
  _,m,h=fixture();before=m.state_hash();score,z=m.score(h)
  row,_=Runtime(m,"IMMEDIATE_UPDATE").step(h,10)
  self.assertEqual(row["score"],score);self.assertEqual(row["full_state_pre_hash"],before)
  self.assertNotEqual(row["full_state_post_hash"],before)
  self.assertLess(row["score_time"],row["decision_time"]);self.assertLess(row["decision_time"],row["mutation_time"])
 def test_future_modification_all_policies(self):
  x,m,h=fixture();s=np.vstack([np.tile(h,(20,1)),x[:20]])
  changed=s.copy();changed[25:]+=900
  for p in C["policies"]:
   a,da,_=run_array(s,m,p,0);b,db,_=run_array(changed,m,p,0)
   self.assertEqual(a[:25],b[:25]);np.testing.assert_array_equal(da[:25],db[:25])
 def test_Q_wait_current_only_and_exact_delay(self):
  _,m,h=fixture();rt=Runtime(m,"QUARANTINE_64");before=m.state_hash()
  for t in range(63):
   r,_=rt.step(h,t);self.assertEqual(r["decision"],"WAIT");self.assertEqual(m.state_hash(),before)
  r,_=rt.step(h,63);self.assertEqual(r["decision"],"PROMOTE");self.assertEqual(r["loss_ids"],[63])
  self.assertEqual(r["loss_weights"],[1.])
 def test_Q_clean_point_resets(self):
  _,m,h=fixture();rt=Runtime(m,"QUARANTINE_64")
  for t in range(20):rt.step(h,t)
  r,_=rt.step(m.mu,20);self.assertEqual(r["candidate_reset"],1);self.assertEqual(rt.count,0)
  r,_=rt.step(h,21);self.assertEqual(r["candidate_start"],21);self.assertEqual(r["decision"],"WAIT")
 def test_CANDI_pending_not_written_exact_flush(self):
  _,m,h=fixture();m.similar=lambda z,kind:True;rt=Runtime(m,"CANDI_STYLE_CAUSAL");before=m.state_hash()
  for t in range(15):
   r,_=rt.step(h,t);self.assertEqual(r["selected_ids"],[t]);self.assertEqual(r["loss_ids"],[])
   self.assertEqual(m.state_hash(),before)
  r,_=rt.step(h,15);self.assertEqual(r["loss_ids"],list(range(16)));self.assertEqual(r["buffer_exit_ids"],list(range(16)))
  self.assertEqual(r["loss_weights"],[1/16]*16);self.assertEqual(r["pending_post"]["hard"],0)
 def test_Q1_immediate_parameter_parity(self):
  x,m,h=fixture();v=np.vstack([np.tile(h,(30,1)),x[:30]])
  a,d,_=run_array(v,m,"IMMEDIATE_UPDATE",0);b,e,_=run_array(v,m,"QUARANTINE_1",0)
  np.testing.assert_array_equal(d,e);self.assertEqual([r["score"] for r in a],[r["score"] for r in b])
 def test_identical_X_mirrored_actions_no_truth(self):
  x,m,h=fixture();v=np.vstack([np.tile(h,(20,1)),x[:20]])
  for pol in C["policies"]:
   a,d,pa=run_array(v,m,pol,0);b,e,pb=run_array(v.copy(),m,pol,0)
   self.assertEqual(a,b);np.testing.assert_array_equal(d,e);self.assertEqual(pa,pb)
 def test_SGD_same_mean_loss_operator(self):
  x,m,_=fixture();V=np.array([(v-m.mu)/m.sd for v in x[:3]]);old=m.decoder.copy()
  L=np.column_stack([V@m.encoder,np.ones(3)])
  expected=old-.01*(2/(3*4)*L.T@(L@old-V))
  m.write(V);np.testing.assert_allclose(m.decoder,expected,atol=1e-15)
 def test_train_only_scaler_constant(self):
  x,m,h=fixture();np.testing.assert_allclose(m.mu,x[:100].mean(0));np.testing.assert_allclose(m.sd,x[:100].std(0))
  x[:,3]=2;z=LinearAE.fit(x[:100],x[100:150],C);self.assertEqual(z.sd[3],1)
 def test_probe_no_state_mutation(self):
  x,m,_=fixture();pre=m.state_hash();v=probe(m,m.decoder,x[:10])
  self.assertEqual(pre,m.state_hash());self.assertTrue(v["read_only"])
 def test_never_write_is_not_acceptance(self):
  x,m,h=fixture();v=np.tile(h,(400,1));rows,d,_=run_array(v,m,"FROZEN",0)
  states=np.full(400,"NORMAL_B_SETTLED",dtype="U32");states[:10]="NORMAL_A";y=np.zeros(400,dtype=np.uint8);states[350:355]="TRUE_ANOMALY_UNDER_B";y[350:355]=1
  c={**C,"eval_start":0};r={"t_settled_B":10,"t_transition_start":5,"acceptance_censor_time":350,"events":[{"id":"fault","start":350,"end":355}]}
  z=evaluate(rows,d,m,states,y,r,"benign_B_with_anomalies",x[:10],c)
  self.assertEqual(z["FAR_admit"],0);self.assertIsNone(z["contaminated_purity"]);self.assertFalse(z["valid_before_censor"])
 def test_no_execution_before_freeze_or_data_access(self):
  with patch("run.freeze",side_effect=ValueError("missing freeze")),patch("run.np.load",side_effect=AssertionError("data accessed")):
   with self.assertRaises(ValueError):run.main()
 def test_runner_refuses_truth_paths_before_load(self):
  with patch("run.np.load",side_effect=AssertionError("must not load truth")):
   with self.assertRaises(ValueError):run.load_observations({"path":"/tmp/truth_state.npy","sha256":"unused"})
 def test_Q_family_and_native_semantics_frozen(self):
  self.assertEqual(C["Q"],[1,64,128,256,512]);self.assertEqual(C["technical_replicates"],1);self.assertEqual(C["rollback"],"NOT_IMPLEMENTED")
 def test_recovery_keeps_original_timeline(self):
  a=np.zeros(300,dtype=bool);s=np.full(300,"NORMAL_B_SETTLED");r=recover(a,s,10,300,C)
  self.assertEqual(r["confirmation_time"],10+64*3-1)
if __name__=="__main__":unittest.main(verbosity=2)
