import copy
import sys
import unittest
from pathlib import Path
import numpy as np
import torch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import configure,load_config,array_hash,model_hash
from audit import preflight
from generator import histories,contaminated_suffix,process_seed
from models import build
from evaluate import predict_arms,losses,linear_ar_fit,baseline_losses
from metrics import average_precision,detection_metrics,group_decision


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):configure()

    def test_process_state_parity_and_parameter_invariants(self):
        report=preflight()
        self.assertEqual(report['parameter_counts'],{'xlstm':6832,'lstm':7016})

    def test_predict_before_ingest_and_exact_recent_history(self):
        rng=np.random.default_rng(888);prefix_a=rng.normal(size=(2,40,8)).astype(np.float32);prefix_b=prefix_a+3;suffix=rng.normal(size=(2,45,8)).astype(np.float32)
        scaler={'mean':np.zeros(8,np.float32),'std':np.ones(8,np.float32)}
        for backbone in ['xlstm','lstm']:
            model=build(backbone,22).eval().requires_grad_(False);before=model_hash(model)
            with torch.inference_mode():
                a=predict_arms(model,prefix_a,suffix,scaler);b=predict_arms(model,prefix_b,suffix,scaler)
                altered=suffix.copy();altered[:,17:]+=99;c=predict_arms(model,prefix_a,altered,scaler)
            for arm in a:self.assertTrue(np.array_equal(a[arm][:,:18],c[arm][:,:18]),arm)
            self.assertTrue(np.array_equal(a['KEEP'][:,0],a['ORACLE_BOUNDARY_RESET'][:,0]))
            self.assertTrue(np.array_equal(a['ORACLE_BOUNDARY_RESET'][:,1:],b['ORACLE_BOUNDARY_RESET'][:,1:]))
            for l in [8,32]:self.assertTrue(np.array_equal(a['FIXED_'+str(l)][:,l:],b['FIXED_'+str(l)][:,l:]))
            self.assertEqual(before,model_hash(model))

    def test_anomaly_design_labels_only_observed_stream(self):
        clean=np.zeros((8,256,8),np.float32);scales=np.arange(1,9,dtype=np.float32);before=array_hash(clean)
        for kind,duration in [('spike',1),('short_collective',8),('long_collective',32)]:
            x,y,events=contaminated_suffix(clean,'dynamics',2,kind,32,scales)
            self.assertEqual(int(y.sum()),8*duration)
            self.assertEqual(before,array_hash(clean))
            self.assertTrue(np.array_equal(x[:,:32],clean[:,:32]))
            self.assertTrue(np.array_equal(x[:,32+duration:],clean[:,32+duration:]))
            for e in events:
                self.assertEqual(len(e['channels']),2)
                for c,d in zip(e['channels'],e['delta']):
                    self.assertTrue(np.allclose(x[e['replicate'],32:32+duration,c],d))
                    self.assertAlmostEqual(abs(d),4*scales[c])

    def test_metric_alignment_and_average_precision_ties(self):
        self.assertAlmostEqual(average_precision([1,0,1],[.9,.8,.7]),5/6)
        self.assertAlmostEqual(average_precision([1,0],[.5,.5]),.5)
        self.assertIsNone(average_precision([0,0],[.2,.1]))
        y=np.array([[0,1,1,0]]);score=np.array([[.1,.9,.2,.8]])
        m=detection_metrics(y,score,.5,[{'replicate':0,'onset':1,'duration':2}])
        self.assertEqual(m['event_recall'],1);self.assertEqual(m['normal_false_alarm_rate'],.5);self.assertEqual(m['post_reset_missed_anomaly_point_rate'],.5)

    def test_joint_seed_gate_cannot_mix_different_witnesses(self):
        row={'b_support':{'pass':True},'mechanism':{'history_harm_normalized':.1,'reset_recovery_fraction':.8,'stationary_deterioration_normalized':{'A':0,'B':0},'long_context_benefit_normalized':{'8':.03,'32':.03},'replay_vs_reset_normalized':{'8':.03,'32':.03}}}
        rows=[copy.deepcopy(row) for _ in range(3)]
        rows[0]['b_support']['pass']=False;rows[1]['mechanism']['history_harm_normalized']=0
        self.assertFalse(group_decision(rows)['mechanism_pre_ad'])
        self.assertTrue(group_decision([row,row,rows[0]])['all_forecast_gates'])

    def test_cpu_optimizer_readiness_on_random_fixture(self):
        self.assertFalse(torch.cuda.is_available())
        x=torch.randn(2,12,8,generator=torch.Generator().manual_seed(98765))
        for backbone in ['xlstm','lstm']:
            model=build(backbone,11);optimizer=torch.optim.Adam(model.parameters(),lr=.002)
            before=model_hash(model);loss=model(x[:,:-1]).sub(x[:,1:]).square().mean()
            self.assertTrue(torch.isfinite(loss))
            loss.backward();optimizer.step()
            self.assertNotEqual(before,model_hash(model))

    def test_linear_baseline_is_past_only(self):
        rng=np.random.default_rng(45);x=rng.normal(size=(2,50,8));scaler={'mean':np.zeros(8),'std':np.ones(8)}
        fit=linear_ar_fit(x,.001);base=baseline_losses(x[:,:32],x[:,32:],scaler,fit)
        modified=x[:,32:].copy();modified[:,7:]+=100
        other=baseline_losses(x[:,:32],modified,scaler,fit)
        for key in base:self.assertTrue(np.array_equal(base[key][:,:7],other[key][:,:7]))


if __name__=='__main__':unittest.main()
