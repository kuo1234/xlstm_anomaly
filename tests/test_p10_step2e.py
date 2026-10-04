import json,sys,unittest,tempfile,subprocess
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import p10_step2e_data as D
import p10_step2e_transfer as T
from p10_step2a_stream import scale,run_policy,CFG2A,W1S
from p10_step2b_posthoc import run_cv_policy
from p10_step2e_eval import max_unwritten_hours


def fixture(V):
    rng=np.random.default_rng(7);K0=np.abs(rng.normal(size=(300,16)));K0/=np.linalg.norm(K0,axis=1,keepdims=True)
    K=np.abs(rng.normal(size=(len(V),16)));K/=np.linalg.norm(K,axis=1,keepdims=True)
    def builder():
        m=W1S(2000,16,3,5);m.write(K0,np.zeros((300,3)),-np.ones(300,dtype=int));return m
    ctx=dict(cfg=T.CONFIG,tau=1.,Kt=K,Vt=V,K0=K0,taus={op:1. for op in T.CONFIG['ops']},frozen={op:np.linalg.norm(V,axis=1) for op in T.CONFIG['ops']},zbase=lambda st:np.r_[np.zeros((256,3)),V][st:st+256])
    return builder,ctx

class TestStep2e(unittest.TestCase):
    def test_source_boundaries_and_fault_never_safe(self):
        t=np.array([0,29.95,30,69.95,70,100])
        self.assertEqual(D.states(t,'setpoint').tolist(),['NORMAL_A','NORMAL_A','TRANSITION','TRANSITION','NORMAL_B','NORMAL_B'])
        self.assertEqual(D.states(t,'fault').tolist(),['NORMAL_A','NORMAL_A','FAULT','FAULT','FAULT','FAULT'])

    def test_frozen_config(self):
        T.validate_config()
        for key,v in [('cv_max',.11),('trail',64),('check_start',64)]:
            with patch.dict(T.CONFIG,{key:v}):
                with self.assertRaises(AssertionError):T.validate_config()

    def test_train_only_scaling_and_constants(self):
        tr=np.c_[np.arange(30),np.ones(30)];te=np.ones((400,2))*100
        a,b=scale(tr,te,T.CONFIG);c,d=scale(tr,te*10,T.CONFIG)
        np.testing.assert_array_equal(a,c);self.assertTrue(np.isfinite(b).all());self.assertTrue((a[:,1]==0).all())

    def test_runner_does_not_load_truth_or_timestamps(self):
        s=Path(T.__file__).read_text();self.assertNotIn('states(',s);self.assertNotIn('timestamps.npy',s)
        self.assertNotIn("OUT/'evaluator_metadata.json'",s);self.assertNotIn("OUT/'selection.json'",s)
        self.assertIn("'evaluator_metadata_git_blob':git('rev-parse'",s)

    def test_missing_seal_blocks_before_truth_access(self):
        with tempfile.TemporaryDirectory() as p,patch.object(D,'OUT',Path(p)):
            with self.assertRaises(FileNotFoundError):D.verify(Path(p)/'run')

    def test_unpushed_seal_blocks(self):
        with tempfile.TemporaryDirectory() as p:
            root=Path(p);run=root/'run';run.mkdir();raw=root/'raw';raw.mkdir()
            (run/'seal.json').write_text(json.dumps({'labels_read_by_runner':0,'cv_max':.1,'posthoc':False,'frozen_config':{'cv_max':.1},'evaluator_metadata_git_blob':'blob','files':{},'code':{},'raw':{}}))
            def fake(*a):
                return 'blob' if a[0] in ['hash-object','rev-parse'] else 'abc' if a[0]=='log' else 'def refs/heads/research/p7-p10-segment-memory'
            with patch.object(D,'ROOT',root),patch.object(D,'OUT',root),patch.object(D,'RAW',raw),patch.object(D,'git',side_effect=fake),patch.object(D.subprocess,'run',side_effect=subprocess.CalledProcessError(1,['merge-base'])):
                with self.assertRaises(subprocess.CalledProcessError):D.verify(run)

    def test_future_change_does_not_change_past_decisions(self):
        v=np.ones((900,3))*2;w=v.copy();w[800:]=100
        b,c=fixture(v);b2,c2=fixture(w);a=run_cv_policy(b,c);z=run_cv_policy(b2,c2)
        np.testing.assert_array_equal(a['score'][:800],z['score'][:800]);self.assertEqual([x for x in a['checks'] if x['t']<=800],[x for x in z['checks'] if x['t']<=800])

    def test_score_before_write(self):
        b,c=fixture(np.ones((32,3))*2);r=run_policy('B_always','W1',b,c['Kt'],c['Vt'],1.,CFG2A)
        np.testing.assert_allclose(r['score'][:16],np.sqrt(12));self.assertTrue(r['written'].all())

    def test_conjunction_and_trailing_only(self):
        import p10_step2b_posthoc as P
        b,c=fixture(np.ones((400,3))*2)
        with patch.object(P.S,'evidence',side_effect=lambda m,ctx,s,st,t:dict(self=0.,stat=0.,cv=.11 if t==256 else .10)):
            r=run_cv_policy(b,c);self.assertFalse(r['written'][:128].any());self.assertTrue(r['written'][128:384].all())
        for selfv,stat in [(1.01,0),(.5,.51)]:
            with patch.object(P.S,'evidence',return_value=dict(self=selfv,stat=stat,cv=0.)):
                b,c=fixture(np.ones((256,3))*2);self.assertEqual(run_cv_policy(b,c)['events']['promotions'],0)

    def test_unwritten_cost_is_distinct_from_no_promotion(self):
        self.assertEqual(max_unwritten_hours(np.ones(10,bool),np.ones(10,bool)),0)
        self.assertEqual(max_unwritten_hours(np.zeros(10,bool),np.ones(10,bool)),.5)

    def test_sealed_subset_has_five_literal_cases(self):
        sel=json.loads((D.OUT/'selection.json').read_text());m=json.loads((D.OUT/'dataset_manifest.json').read_text())
        self.assertEqual([x['id'] for x in sel['cases']],T.CONFIG['machines']);self.assertEqual(len(m['datasets']),5)
        self.assertEqual(m['selection_sha256'],D.sha(D.OUT/'selection.json'))
        for d in m['datasets']:self.assertEqual(d['dimension'],53);self.assertGreaterEqual(d['train_count'],320)

if __name__=='__main__':unittest.main()
