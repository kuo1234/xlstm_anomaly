"""Protocol and causal tests on synthetic fixtures only; never opens evaluation labels."""
import json, sys, ast
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import p10_step2c_data as D
import p10_step2c_transfer as T
from p10_step2b_posthoc import run_cv_policy
from p10_step2a_stream import W1S,scale,run_policy,CFG2A
from p10_step2c_eval import episodes,promotions_and_segments


def test_runner_has_no_label_path():
    source=Path(T.__file__).read_text()
    assert 'load_test_labels' not in source and 'test_label' not in source
    assert all('label' not in x.arg for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) for x in n.args.args)


def test_preseal_labels_blocked(tmp_path,monkeypatch):
    monkeypatch.setattr(D.np,'loadtxt',lambda *a,**k:pytest.fail('label parsing before seal'))
    with pytest.raises(D.ProtocolViolation): D.load_test_labels(D.MACHINES[0],run=tmp_path,expected_sha='0'*64,root=tmp_path,log_path=tmp_path/'log')


def test_no_retuning():
    assert T.CONFIG['cv_max']==0.10 and T.CONFIG['self_max']==1 and T.CONFIG['stat_max']==.5
    assert [T.CONFIG[k] for k in ('block','check_start','check_every','trail')]==[16,256,128,256]
    for key,val in [('cv_max',.11),('trail',512),('check_start',512),('self_max',2)]:
        with pytest.raises(D.ProtocolViolation): T.validate_config(dict(T.CONFIG,**{key:val}))


def test_policy_and_machine_list_sealed():
    source=Path(T.__file__).read_text()
    assert '"policy_config.json"' in source and '"machines.json"' in source
    assert 'files=files' in source and 'frozen_policy_config=CONFIG' in source
    assert list(D.MACHINES)==T.CONFIG['machines'] and len(D.MACHINES)==9
    assert not set(D.MACHINES)&{'machine-1-6','machine-2-7','machine-3-7'}


def test_split_and_order_observation_only(tmp_path):
    x=np.arange(380.).reshape(10,38)
    np.savetxt(tmp_path/(D.MACHINES[0]+'_test.txt'),x,delimiter=',')
    assert np.array_equal(D.load_observations(D.MACHINES[0],'test',tmp_path),x)
    with pytest.raises(D.ProtocolViolation): D.load_observations(D.MACHINES[0],'test_label',tmp_path)
    x[0,0]=np.nan;np.savetxt(tmp_path/(D.MACHINES[0]+'_train.txt'),x,delimiter=',')
    with pytest.raises(D.ProtocolViolation): D.load_observations(D.MACHINES[0],'train',tmp_path)


def test_scaler_train_only_constant_deterministic():
    tr=np.c_[np.arange(20.),np.ones(20)]; te=np.array([[100.,1.],[200.,2.]])
    a,b=scale(tr,te,T.CONFIG); c,d=scale(tr,te*10,T.CONFIG)
    assert np.array_equal(a,c) and np.isfinite(b).all()
    assert np.array_equal(b,scale(tr,te,T.CONFIG)[1])
    assert np.array_equal(a[:,1],np.zeros(20))


def fixture(V):
    rng=np.random.default_rng(7);K0=np.abs(rng.normal(size=(300,16)));K0/=np.linalg.norm(K0,axis=1,keepdims=True)
    K=np.abs(rng.normal(size=(len(V),16)));K/=np.linalg.norm(K,axis=1,keepdims=True);V0=np.zeros((300,3))
    def builder():
        m=W1S(2000,16,3,5);m.write(K0,V0,-np.ones(300,dtype=int));return m
    ctx=dict(cfg=T.CONFIG,tau=1.,Kt=K,Vt=V,K0=K0,taus={op:1. for op in T.CONFIG['ops']},
             frozen={op:np.linalg.norm(V,axis=1) for op in T.CONFIG['ops']},
             zbase=lambda st:np.r_[np.zeros((256,3)),V][st:st+256])
    return builder,ctx


def test_future_invariance():
    V=np.ones((900,3))*2;V2=V.copy();V2[800:]=100
    b,c=fixture(V);b2,c2=fixture(V2)
    a=run_cv_policy(b,c);z=run_cv_policy(b2,c2)
    assert np.array_equal(a['score'][:800],z['score'][:800])
    assert [x for x in a['checks'] if x['t']<=800]==[x for x in z['checks'] if x['t']<=800]


def test_promote_only_trailing256(monkeypatch):
    import p10_step2b_posthoc as P
    # First checkpoint KEEP, second PROMOTE: never write the older 128 points.
    monkeypatch.setattr(P.S,'evidence',lambda mem,ctx,sc,st,t:dict(self=0.,stat=0.,cv=.11 if t==256 else .10))
    b,c=fixture(np.ones((400,3))*2);r=run_cv_policy(b,c)
    assert r['checks'][0]['decision']=='KEEP' and r['checks'][1]['decision']=='PROMOTE'
    assert not r['written'][:128].any() and r['written'][128:384].all()


def test_conjunction_not_cv_alone(monkeypatch):
    import p10_step2b_posthoc as P
    for selfv,stat in [(1.01,0),(.5,.51)]:
        monkeypatch.setattr(P.S,'evidence',lambda *a:dict(self=selfv,stat=stat,cv=0.))
        b,c=fixture(np.ones((256,3))*2);assert run_cv_policy(b,c)['events']['promotions']==0


def test_score_before_write():
    b,c=fixture(np.ones((32,3))*2)
    r=run_policy('B_always','W1',b,c['Kt'],c['Vt'],1.,CFG2A)
    assert np.allclose(r['score'][:16],np.sqrt(12))
    assert r['written'].all()


def test_episode_uint_safe_and_promotion_reconstruction():
    assert episodes(np.array([0,1,1,0],dtype=np.uint8))==[(1,3)]
    import pandas as pd
    r=dict(policy='D_quarantine',tau=1.,promotions=1)
    seg,p=promotions_and_segments(r,np.ones(512)*2,pd.DataFrame(),T.CONFIG)
    assert p[0]['t']==512 and p[0]['write_start']==0 and p[0]['delay']==512


def seal_fixture(tmp_path,monkeypatch):
    root=tmp_path/'repo';run=root/'run';run.mkdir(parents=True)
    monkeypatch.setattr(D,'ROOT',root)
    (run/'policy_config.json').write_text(json.dumps(T.CONFIG))
    (run/'machines.json').write_text(json.dumps(list(D.MACHINES)))
    s=dict(stage='step2c_label_blind',labels_read=0,posthoc=False,cv_max=.1,machines=list(D.MACHINES),
           files={p:D.sha256(run/p) for p in ('policy_config.json','machines.json')},code={})
    (run/'seal.json').write_text(json.dumps(s)); h=D.sha256(run/'seal.json')
    import subprocess
    def fakegit(*args):
        if args[0]=='log': return 'a'*40
        if args[0]=='ls-remote': return 'b'*40+' refs/heads/'+D.BRANCH
        return ''
    monkeypatch.setattr(D,'git',fakegit)
    monkeypatch.setattr(subprocess,'check_output',lambda *a,**k:(run/'seal.json').read_bytes())
    return run,h,fakegit


def test_config_machine_tamper_gate(tmp_path,monkeypatch):
    run,h,g=seal_fixture(tmp_path,monkeypatch)
    assert D.verify_seal(run,h)['seal_commit']=='a'*40
    (run/'policy_config.json').write_text(json.dumps(dict(T.CONFIG,cv_max=.11)))
    with pytest.raises(D.ProtocolViolation): D.verify_seal(run,h)
    (run/'policy_config.json').write_text(json.dumps(T.CONFIG))
    (run/'machines.json').write_text('[]')
    with pytest.raises(D.ProtocolViolation): D.verify_seal(run,h)


def test_local_seal_without_push_rejected(tmp_path,monkeypatch):
    run,h,g=seal_fixture(tmp_path,monkeypatch)
    import subprocess
    def unpushed(*args):
        if args[0]=='merge-base': raise subprocess.CalledProcessError(1,args)
        return g(*args)
    monkeypatch.setattr(D,'git',unpushed)
    with pytest.raises(D.ProtocolViolation,match='not pushed'): D.verify_seal(run,h)


def test_retrieval_batching_parity():
    b,c=fixture(np.ones((600,3))*2)
    m=b();np.testing.assert_allclose(T.batched_scores(m,c['Kt'],c['Vt']),T.scores(m,c['Kt'],c['Vt']),rtol=1e-12,atol=1e-12)
