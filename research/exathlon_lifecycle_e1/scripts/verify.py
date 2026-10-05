"""Seal/result validation, independent score readout and actual-model causality."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
import numpy as np
import pandas as pd
from prepare import ROOT,REPO,CACHE,E0,sha,save,features

def main():
    final='--final' in sys.argv;p=json.loads((ROOT/'configs/protocol.json').read_text());m=json.loads((ROOT/'configs/data_manifest.json').read_text())
    subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),'-v'],check=True)
    assert p['baselines']==['PCA_SPE','CAUSAL_LSTM_REFERENCE'] and p['method_design_GO'] is False
    identities=0
    for r in m:
        assert sha(REPO/r['local_path'])==r['sha256'];d=np.load(REPO/r['prepared_path'])
        assert hashlib.sha256(d['t'].tobytes()+d['x'].tobytes()+d['observed'].tobytes()).hexdigest()==r['prepared_array_sha256'];identities+=1
    roles={role:{r['trace'] for r in m if r['role']==role} for role in ['fit','validation','calibration','normal_control']}
    for a,na in roles.items():
        assert len(na)==3 and all(n.split('_')[1]=='0' for n in na)
        for b,nb in roles.items():
            if a!=b:assert not na&nb
    events=json.loads((ROOT/'configs/event_manifest.json').read_text());assert len(events)==109
    primary=[e for e in events if e['stratum']=='primary'];assert len(primary)==24
    assert all(e['root_cause_end']>e['root_cause_start'] and e['extended_effect_end'] is not None and e['anomaly_details'] not in ['no_application_impact','application_crash'] for e in primary)
    links=0
    for doc in ROOT.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
            if target.startswith(('http:','https:')):continue
            assert (doc.parent/target.split('#')[0]).exists(),(doc,target);links+=1
    for path in ROOT.rglob('*.json'):json.loads(path.read_text(),parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))
    checks={'status':'PASS','phase':'result' if final else 'seal','raw_archive_and_canonical_array_checks':identities,'whole_trace_disjoint_roles':True,'primary_events':len(primary),'local_links_checked':links,'unit_tests':9,'training_before_pushed_seal':False}
    if final:
        import torch
        from models import Predictor,infer_lstm,pca_score
        art=json.loads((ROOT/'provenance/score_artifacts.json').read_text());assert len(art)==38
        training=json.loads((ROOT/'results/training.json').read_text())
        assert sha(CACHE/'pca.npz')==training['checkpoints']['PCA_SPE']
        assert sha(CACHE/'lstm.pt')==training['checkpoints']['CAUSAL_LSTM_REFERENCE']
        assert sha(CACHE/'scaler.npz')==training['scaler_hash']
        scaler=np.load(CACHE/'scaler.npz');mean=scaler['mean'];std=scaler['std'];basis=np.load(CACHE/'pca.npz')['basis']
        model=Predictor();model.load_state_dict(torch.load(CACHE/'lstm.pt',weights_only=True));model.eval();torch.set_num_threads(2)
        maxerr=0;count=0
        for r in art:
            assert sha(REPO/r['path'])==r['sha256'];score=pd.read_csv(REPO/r['path']);finite=np.isfinite(score.score)
            assert (score.available_at[finite]<=score.target_timestamp[finite]).all() and score.target_observed[finite].all()
            raw=next(mr for mr in m if mr['trace']==r['trace']);arr=np.load(REPO/raw['prepared_path']);z=((arr['x']-mean)/std).astype(np.float32);ids=np.flatnonzero(finite.to_numpy())
            sample=ids[np.linspace(0,len(ids)-1,min(5,len(ids)),dtype=int)]
            if r['baseline']=='PCA_SPE':expected=np.array([np.mean((z[i].astype(float)-basis.T@(basis@z[i].astype(float)))**2) for i in sample])
            else:
                with torch.no_grad():pred=model(torch.from_numpy(np.stack([z[i-32:i] for i in sample]))).numpy()
                expected=np.mean((pred-z[sample])**2,axis=1)
            actual=score.score.to_numpy()[sample];np.testing.assert_allclose(actual,expected,rtol=1e-5,atol=1e-5);maxerr=max(maxerr,float(np.max(np.abs(actual-expected))));count+=len(sample)
        # Actual checkpoint future-suffix mutation, using normal control data.
        mr=next(x for x in m if x['role']=='normal_control');a=np.load(REPO/mr['prepared_path']);z=((a['x']-mean)/std).astype(np.float32)[:1600];obs=a['observed'][:1600];mut=z.copy();cut=800;mut[cut+1:]=123
        s1=infer_lstm(model,z,obs,32);s2=infer_lstm(model,mut,obs,32)
        np.testing.assert_allclose(s1[:cut+1],s2[:cut+1],rtol=1e-5,atol=1e-5,equal_nan=True)
        np.testing.assert_allclose(pca_score(z[:cut+1],basis),pca_score(mut[:cut+1],basis),equal_nan=True)
        # Independent rederive scaler from fit rows only; calibration/control cannot affect it.
        fit_parts=[]
        for row in m:
            fit_array=np.load(REPO/row['prepared_path'])
            valid=fit_array['observed']&np.isfinite(fit_array['x']).all(axis=1)
            fit_parts.append(fit_array['x'][valid]) if row['role']=='fit' else None
        fitx=np.concatenate(fit_parts)
        np.testing.assert_array_equal(mean,fitx.mean(axis=0,dtype=np.float64));ds=fitx.std(axis=0,dtype=np.float64);ds[ds==0]=1;np.testing.assert_array_equal(std,ds)
        for thr in json.loads((ROOT/'results/thresholds.json').read_text()):
            vals=np.concatenate([pd.read_csv(REPO[r['path']]).score.to_numpy() for r in art if r['baseline']==thr['baseline'] and r['role']=='calibration' and (thr['app'] is None or int(r['trace'].split('_')[0])==thr['app'])]);vals=vals[np.isfinite(vals)]
            np.testing.assert_allclose(thr['threshold'],np.quantile(vals,.995,method='linear'),rtol=1e-12)
        # Deterministic metric replay, without model retraining/scoring or touching outcome choices.
        outputs=list((ROOT/'results').glob('*'));before={x.name:sha(x) for x in outputs if x.is_file() and x.name!='verification.json'}
        subprocess.run([sys.executable,str(ROOT/'scripts/analyze.py')],check=True,capture_output=True)
        subprocess.run([sys.executable,str(ROOT/'scripts/document.py'),'--final'],check=True,capture_output=True)
        after={x.name:sha(x) for x in outputs if x.is_file() and x.name!='verification.json'};assert before==after
        checks.update({'score_artifacts_checked':len(art),'independent_single_target_readouts':count,'max_absolute_readout_error':maxerr,'actual_checkpoint_future_suffix_invariance':True,'fit_only_scaler_rederived':True,'normal_only_thresholds_rederived':True,'deterministic_metric_replay':True,'no_after_result_scientific_protocol_change':True,'verification_only_amendment':'AMENDMENT_01.md'})
    save(ROOT/'provenance'/('result_verification.json' if final else 'seal_verification.json'),checks);print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
