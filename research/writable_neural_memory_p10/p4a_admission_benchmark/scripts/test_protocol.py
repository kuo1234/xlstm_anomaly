"""Small deterministic data-contract fixtures only; no detector or dataset audit."""
import json,unittest,importlib.util
from unittest.mock import patch
import numpy as np
import common,controlled as g,tsb_audit as a
C=json.loads((common.OUT/"controlled_config.json").read_text())
T=json.loads((common.OUT/"tsb_audit_config.json").read_text())
M=json.loads((common.OUT/"metrics_contract.json").read_text())
spec=importlib.util.spec_from_file_location("js_fixture",common.ROOT/"data/p4a_admission_benchmark/sources/StrAD/TSB-drift/jsd_drift.py")
up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up)
class Protocol(unittest.TestCase):
    def test_settled_is_generator_endpoint(self):
        r=C["physical_runs"][0];t=np.array([r["t_settled_B"]-1,r["t_settled_B"],r["t_settled_B"]+1])
        amp,mu=g.law_parameters(t,r,C)
        np.testing.assert_array_equal(amp[1:],np.tile(C["amplitude_B"],(2,1)))
        np.testing.assert_array_equal(mu[1:],np.tile(C["offset_B"],(2,1)))
        self.assertFalse(np.array_equal(mu[0],mu[1]))
    def test_future_event_does_not_modify_prefix(self):
        import copy
        r=C["physical_runs"][0];alt=copy.deepcopy(r);alt["events"][0]["severity_sd_A"]=900
        x,_,_=g.series(C,r,C["arms"][0]);z,_,_=g.series(C,alt,C["arms"][0])
        np.testing.assert_array_equal(x[:r["events"][0]["start"]],z[:r["events"][0]["start"]])
    def test_scaler_train_only_and_constant(self):
        x=np.ones((20,2));x[:10,0]=np.arange(10);z=x.copy();z[10:]=99999
        for v,w in zip(g.fit_scale(x,[0,10]),g.fit_scale(z,[0,10])):np.testing.assert_array_equal(v,w)
        self.assertEqual(g.fit_scale(x,[0,10])[1][1],1)
    def test_identical_observations_opposite_semantics(self):
        r=C["physical_runs"][0];x,s,y=g.series(C,r,C["arms"][0]);z,u,v=g.series(C,r,"semantic_fault_twin")
        np.testing.assert_array_equal(x,z);t=r["t_settled_B"]
        self.assertTrue(g.admissible_payload(s,[t]));self.assertFalse(g.admissible_payload(u,[t]))
    def test_transition_or_fault_payload_invalid(self):
        r=C["physical_runs"][0];_,s,_=g.series(C,r,C["arms"][0]);t=r["t_settled_B"]
        self.assertFalse(g.admissible_payload(s,[t-1,t]))
        self.assertFalse(g.admissible_payload(s,[t,r["events"][0]["start"]]))
        self.assertFalse(g.admissible_payload(s,[]))
    def test_mask_preserves_original_batches_and_empty_support(self):
        x=np.repeat([0.,1.,2.],40);y=np.zeros(120);y[40:80]=1
        mat,n,v,req=a.mask_batches(x,y,40,np.array([-.5,.5,1.5,2.5]),up,T)
        self.assertEqual(n.tolist(),[40,0,40]);self.assertEqual(v.tolist(),[True,False,True])
        self.assertTrue(np.isnan(mat[1]).all());self.assertEqual(mat.shape,(3,3))
        self.assertFalse(a.persistent([0,.5,.5],v))
    def test_mask_same_edges_no_labels_equals_raw(self):
        x=np.repeat([0.,1.,2.],40);edges=np.array([-.5,.5,1.5,2.5])
        masked,_,v,_=a.mask_batches(x,np.zeros(120),40,edges,up,T)
        raw=up.jsd_matrix_from_probs(np.array([up._hist_probs(x[i:i+40],edges,T["alpha"]) for i in range(0,120,40)]))
        np.testing.assert_allclose(masked,raw);self.assertTrue(v.all())
    def test_classification_support_precedes_strength(self):
        self.assertEqual(a.classify([0,.6,.6],[0,.6,.6],[False,True,True],1,T),"INSUFFICIENT_SERIES_LENGTH / SUPPORT")
    def test_four_qualifications_fixed_cutoffs(self):
        v=[True]*3
        self.assertEqual(a.classify([0,.6,.6],[0,.5,.5],v,.8,T),"REAL_DRIFT_SUPPORTED")
        self.assertEqual(a.classify([0,.6,.6],[0,.01,.01],v,.02,T),"DRIFT_ANOMALY_CONFOUNDED")
        self.assertEqual(a.classify([0,.01,.01],[0,.01,.01],v,1,T),"DRIFT_CAUSE_UNRESOLVED")
        self.assertEqual(T["persistence_JS_nats_min"],.10);self.assertEqual(T["mask_retention_ratio_min"],.5)
    def test_inventory_is_all_non_simulated_not_outcome_selected(self):
        inv=json.loads((common.OUT/"tsb_candidate_inventory.json").read_text())
        self.assertEqual(sorted(T["assessed_files"]),sorted(r["file"] for r in inv if r["real_arm_selected"]))
        self.assertEqual(len(inv),75);self.assertEqual(len(T["assessed_files"]),47)
        self.assertTrue(all(not r["selection_used_numeric_outcomes"] for r in inv))
    def test_metric_native_censoring_and_physical_unit(self):
        self.assertIn("N/A_NATIVE",M["formal_TTAccept"]);self.assertIn("censored",M["never_admit"])
        self.assertIn("physical",M["N"]);self.assertIn("NOT_EVALUABLE",M["unsafe"])
        self.assertNotIn("labels",C["runtime_interface"])
        self.assertEqual(len(C["physical_runs"]),5)
    def test_no_execution_without_freeze(self):
        with patch("common.Path.read_text",side_effect=FileNotFoundError("missing freeze")):
            with self.assertRaises(FileNotFoundError):common.freeze_check()
if __name__=="__main__":unittest.main(verbosity=2)
