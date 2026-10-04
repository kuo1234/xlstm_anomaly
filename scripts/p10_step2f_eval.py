"""Source-state attachment and fixed upper-bound probes; never an admission controller."""
import json
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,average_precision_score
from p10_step2f_data import ROOT,OUT,RAW,CONFIG,sha,save,utc,verify
from p10_step2e_data import states


def probe(train,test,cols):
    y=(train.state=='FAULT').astype(int);yt=(test.state=='FAULT').astype(int)
    model=make_pipeline(StandardScaler(),LogisticRegression(C=CONFIG['probe_C'],random_state=CONFIG['probe_seed'],max_iter=CONFIG['probe_max_iter']))
    counts=train.groupby('case').case.transform('size');weight=1/counts
    model.fit(train[cols],y,logisticregression__sample_weight=weight)
    prediction=model.predict_proba(test[cols])[:,1]
    case=pd.DataFrame({'case':test.case,'truth':yt,'pred':prediction}).groupby('case').agg(truth=('truth','first'),pred=('pred','mean'))
    return float(roc_auc_score(yt,prediction)),float(average_precision_score(yt,prediction)),prediction,float(roc_auc_score(case.truth,case.pred)),float(average_precision_score(case.truth,case.pred))


def main():
    proof=verify();run=OUT/'run';out=OUT/'results';out.mkdir(exist_ok=True);save(out/'evaluation_start.json',proof)
    meta={x['id']:x for x in json.loads((ROOT/'research/writable_neural_memory_p10/step2e/evaluator_metadata.json').read_text())['cases']}
    time={};truth={};access=[]
    for c,m in meta.items():
        time[c]=np.load(RAW/f'{c}_timestamps.npy');truth[c]=states(time[c],m['arm']);access.append({'case':c,'utc':utc(),'purpose':'Step2f_A sealed residual evidence evaluation','seal_sha256':proof['seal_sha256'],'time_sha256':sha(RAW/f'{c}_timestamps.npy')})
    save(out/'label_access_log.json',access)
    f=pd.read_csv(run/'window_evidence.csv.gz');f['state']=[truth[c][int(a):int(b)][0] if len(set(truth[c][int(a):int(b)]))==1 else 'MIXED' for c,a,b in zip(f.case,f.start,f.end)]
    f['end_hours']=[float(time[c][int(b)-1]) for c,b in zip(f.case,f.end)]
    f.to_csv(out/'windows_labelled.csv.gz',index=False)
    entries=json.loads((run/'runs.json').read_text());point=[];channels=[];covars={}
    for r in entries:
        z=np.load(run/r['file']);R=z['residual'];clip=z['clip_mask'];identity={k:r[k] for k in ['case','seed','op','view']};near=z['raw_train_sd']<.02
        for state in sorted(set(truth[r['case']])):
            mask=truth[r['case']]==state;rr=R[mask];e=(rr**2).mean(0);total=max(e.sum(),1e-12);mu=rr.mean(0);direction=mu/max(np.linalg.norm(mu),1e-12)
            point.append({**identity,'state':state,'n_points':int(mask.sum()),'cell_clip_fraction':float(clip[mask].mean()),'any_channel_clip_fraction':float(clip[mask].any(1).mean()),'mean_score':float(np.linalg.norm(rr,axis=1).mean()),'fixed_prediction_no_clip_score_mean':float(z['value_no_clip_score'][mask].mean()),'fixed_prediction_no_clip_score_CV':float(z['value_no_clip_score'][mask].std()/max(z['value_no_clip_score'][mask].mean(),1e-12)),'state_pooled_score_CV':float(np.linalg.norm(rr,axis=1).std()/max(np.linalg.norm(rr,axis=1).mean(),1e-12)),
                'near_constant_channels':int(near.sum()),'near_constant_energy_share':float(e[near].sum()/total),'manipulated_energy_share':float(e[41:].sum()/total),'top5_channels':','.join(map(str,np.argsort(e)[-5:][::-1])),'top5_energy_share':float(np.sort(e)[-5:].sum()/total)})
            for j in range(53):channels.append({**identity,'state':state,'channel':j,'raw_fit_std':float(z['raw_train_sd'][j]),'near_constant':bool(near[j]),'clip_fraction':float(clip[mask,j].mean()),'residual_mean':float(mu[j]),'residual_sd':float(rr[:,j].std()),'signed_direction':float(direction[j]),'energy_share':float(e[j]/total),'group':'manipulated' if j>=41 else 'measurement'})
            covars['_'.join(map(str,identity.values()))+'_'+state]=np.cov(rr,rowvar=False)
    pd.DataFrame(point).to_csv(out/'clipping_state_summary.csv',index=False);pd.DataFrame(channels).to_csv(out/'channel_residual_summary.csv.gz',index=False);np.savez_compressed(out/'state_covariances.npz',**covars)
    # Match exactly the same source ages; require entire256-point windows in respective truth state.
    ff=f[f.state.isin(['FAULT','NORMAL_B'])];ends=set(ff[ff.state=='NORMAL_B'].end)&set(ff[ff.state=='FAULT'].end)
    ff=ff[ff.end.isin(ends)];ff.to_csv(out/'age_matched_evidence.csv',index=False)
    probes=[];predrows=[];directions=[]
    for (view,seed,op),g in ff.groupby(['view','seed','op']):
        for fold,split in enumerate(CONFIG['folds']):
            tr=g[g.case.isin(split['train'])];te=g[g.case.isin(split['test'])]
            assert not set(tr.case)&set(te.case) and len(set(tr.state))==len(set(te.state))==2
            for arm,cols in [('A0',CONFIG['A0']),('A1',CONFIG['A0']+CONFIG['A1_extra']),('A2',CONFIG['A0']+CONFIG['A2_extra'])]:
                auc,ap,pred,case_auc,case_ap=probe(tr,te,cols)
                probes.append({'view':view,'seed':seed,'op':op,'fold':fold,'arm':arm,'AUROC':auc,'AP':ap,'case_AUROC':case_auc,'case_AP':case_ap,'train_cases':','.join(split['train']),'test_cases':','.join(split['test']),'claim':'diagnostic supervised upper bound; same benign seed across interventions, not independent heldout benign seed'})
                for idx,(_,row) in enumerate(te.iterrows()):predrows.append({'view':view,'seed':seed,'op':op,'fold':fold,'arm':arm,'case':row.case,'end':row.end,'state':row.state,'pred':float(pred[idx])})
        for feature in CONFIG['A0']+CONFIG['A2_extra']:
            for fc in ['case04','case05']:
                for bc in ['case01','case02','case03']:
                    a=g[g.case==fc].set_index('end')[feature];b=g[g.case==bc].set_index('end')[feature]
                    directions.append({'view':view,'seed':seed,'op':op,'feature':feature,'fault_case':fc,'benign_case':bc,'fault_median':float(a.median()),'benign_median':float(b.median()),'fault_greater_at_matched_ages':float((a>b).mean()),'direction':'fault_high' if a.median()>b.median() else 'fault_low' if a.median()<b.median() else 'equal'})
    pd.DataFrame(probes).to_csv(out/'probe_upper_bound.csv',index=False);pd.DataFrame(predrows).to_csv(out/'probe_predictions.csv',index=False);pd.DataFrame(directions).to_csv(out/'case_pair_direction.csv',index=False)
    med=ff.groupby(['view','seed','op','case','state'])[CONFIG['A0']+CONFIG['A2_extra']].median().reset_index();med.to_csv(out/'physical_case_feature_medians.csv',index=False)
    # Compare fixed .10 CV observations; no tuned cutoff, no admission rerun.
    pivot=ff.pivot(index=['case','seed','op','end','state'],columns='view',values='cv').reset_index()
    pivot['clip_pass_cv']=pivot.fit_only_clip<=.10;pivot['no_clip_pass_cv']=pivot.fit_only_no_clip<=.10
    pivot.to_csv(out/'clip_no_clip_cv.csv',index=False)
    save(out/'evaluation_complete.json',{'utc':utc(),'matched_end_indices':sorted(map(int,ends)),'diagnostic_only':True,'neural_arm':'NOT_RUN until A gate','controller_run':False,'new_threshold_fitted':False})
    print('evaluated',len(probes),'probes;',len(ff),'age-matched windows',flush=True)

if __name__=='__main__':main()
