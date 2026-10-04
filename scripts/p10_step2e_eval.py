"""Source-state evaluator after pushed trace seal; no rule tuning or point-adjust."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score,roc_auc_score
from p10_step2e_data import ROOT,OUT,RAW,sha,save,utc,verify,states
from p10_step2c_eval import promotions_and_segments


def max_unwritten_hours(written,mask,dt=.05):
    v=(~np.asarray(written,dtype=bool))&mask
    d=np.diff(np.r_[0,v.astype(int),0]);a=np.flatnonzero(d==1);b=np.flatnonzero(d==-1)
    return float(max(b-a,default=0)*dt)


def evaluate():
    run=OUT/'run';out=OUT/'results';out.mkdir(exist_ok=True)
    proof=verify(run);save(out/'evaluation_start.json',proof)
    cfg=json.loads((run/'policy_config.json').read_text());runs=json.loads((run/'runs.json').read_text())
    meta={x['id']:x for x in json.loads((OUT/'evaluator_metadata.json').read_text())['cases']}
    ck=pd.read_csv(run/'checkpoints.csv.gz')
    times={};truth={}
    log=[]
    for c,m in meta.items():
        t=np.load(RAW/f'{c}_timestamps.npy');times[c]=t;truth[c]=states(t,m['arm'])
        log.append({'case':c,'utc':utc(),'purpose':'step2e_after_pushed_seal_evaluation','proof':proof,'time_sha256':sha(RAW/f'{c}_timestamps.npy'),'evaluator_source':m['arm']})
    save(out/'label_access_log.json',log)
    units=[];promotions=[];segments=[];longs=[];occupancy=[];labelled=[]
    from vus.metrics import get_metrics
    for ix,r in enumerate(runs):
        c=r['machine'];t=times[c];y=truth[c];z=np.load(run/r['file']);sc=z['score'];wr=z['written'];pred=sc>r['tau']
        assert len(sc)==len(t) and np.isfinite(sc).all()
        ch=ck[(ck.machine==c)&(ck.phi_seed==r['phi_seed'])&(ck.op==r['op'])&(ck.policy==r['policy'])]
        seg,pr=promotions_and_segments(r,sc,ch,cfg)
        identity={k:r[k] for k in ['machine','phi_seed','op','policy']}
        row={**r,'arm':meta[c]['arm'],'AP':None,'AUROC':None,'VUS_PR':None,'VUS_ROC':None,'normal_A_FPR':float(pred[y=='NORMAL_A'].mean()),'normal_B_FPR':None,'transition_FPR':None,'fault_recall':None,'event_recall':None,'fault_written_fraction':None,'normal_B_written_fraction':None,'transition_written_fraction':None}
        fault=y=='FAULT';benign=y=='NORMAL_B';trans=y=='TRANSITION'
        if fault.any():
            v=get_metrics(sc,fault.astype(int),metric='vus',slidingWindow=cfg['vus_window'])
            row.update(AP=float(average_precision_score(fault,sc)),AUROC=float(roc_auc_score(fault,sc)),VUS_PR=float(v['VUS_PR']),VUS_ROC=float(v['VUS_ROC']),fault_recall=float(pred[fault].mean()),event_recall=int(pred[fault].any()),fault_written_fraction=float(wr[fault].mean()))
        else:
            row.update(normal_B_FPR=float(pred[benign].mean()),transition_FPR=float(pred[trans].mean()),normal_B_written_fraction=float(wr[benign].mean()),transition_written_fraction=float(wr[trans].mean()))
        p_rows=[]
        for p in pr:
            a,b=p['write_start'],p['t'];tt=float(t[b-1]);yy=y[a:b]
            q={**identity,**p,'decision_hours':tt,'write_first_hours':float(t[a]),'write_last_hours':float(t[b-1]),'delay_hours':float(t[b-1]-t[p['start']]+.05),'fault_written':int((yy=='FAULT').sum()),'transition_written':int((yy=='TRANSITION').sum()),'normal_B_written':int((yy=='NORMAL_B').sum()),'safe_normal_B_promotion':bool(np.all(yy=='NORMAL_B')),'transition_period_promotion':bool(meta[c]['arm']=='setpoint' and 30<=tt<70),'fault_false_promotion':bool((yy=='FAULT').any())}
            p_rows.append(q);promotions.append(q)
        safe=[p['decision_hours'] for p in p_rows if p['safe_normal_B_promotion']]
        unsafe=[p['decision_hours'] for p in p_rows if p['fault_false_promotion']]
        row.update(fault_false_promotions=len(unsafe),first_fault_false_promotion_hours=min(unsafe) if unsafe else None,
            transition_period_promotions=sum(p['transition_period_promotion'] for p in p_rows),transition_touching_promotions=sum(p['transition_written']>0 for p in p_rows),
            normal_B_safe_promotions=len(safe),normal_B_decision_promotions=sum(p['decision_hours']>=70 for p in p_rows) if benign.any() else None,
            normal_B_promotion_rate=int(bool(safe)) if benign.any() else None,
            first_safe_promotion_hours=min(safe) if safe else None,time_to_safe_promotion_after_70h=min(safe)-70 if safe else None,
            promotion_starvation_hours=min(safe)-70 if safe else float(t[-1]+.05-70) if benign.any() else None,
            starvation_right_censored=bool(benign.any() and not safe),never_promote=not bool(pr),
            normal_B_max_unwritten_hours=max_unwritten_hours(wr,benign) if benign.any() else None,
            post_safe_promotion_FPR=float(pred[t>=min(safe)].mean()) if safe else None,
            mean_quarantine_hours=float(np.mean([s['duration']*.05 for s in seg])) if seg else None)
        units.append(row)
        for s in seg:segments.append({**identity,**s,'start_hours':float(t[s['start']]),'end_hours':float(t[s['end']-1]),'duration_hours':s['duration']*.05})
        for _,chrow in ch.iterrows():
            b=int(chrow.t);yy=y[b-cfg['trail']:b];cl='FAULT' if np.all(yy=='FAULT') else 'NORMAL_B' if np.all(yy=='NORMAL_B') else 'NORMAL_A' if np.all(yy=='NORMAL_A') else 'TRANSITION' if np.all(yy=='TRANSITION') else 'MIXED'
            labelled.append({**chrow.to_dict(),'decision_hours':float(t[b-1]),'state':cl,'fault_fraction':float((yy=='FAULT').mean()),'normal_B_fraction':float((yy=='NORMAL_B').mean()),'pass_cv':bool(chrow.cv<=.10),'pass_conjunction':bool(chrow.cv<=.10 and chrow['self']<=1 and chrow.stat<=.5)})
        if fault.any():
            fcheck=[x for x in labelled if all(x[k]==v for k,v in identity.items()) and x['state']=='FAULT']
            passcv=[x['decision_hours'] for x in fcheck if x['pass_cv']]
            longs.append({**identity,'fault_start_hours':30,'fault_end_hours':float(t[-1]+.05),'n_checkpoints':len(fcheck),'n_pass_cv':len(passcv),'n_pass_conjunction':sum(x['pass_conjunction'] for x in fcheck),'first_pass_time_hours':min(passcv) if passcv else None,'was_promoted':bool(unsafe),'first_false_promotion_hours':min(unsafe) if unsafe else None,'fraction_fault_written':row['fault_written_fraction']})
        # Provenance-ledger occupancy, not effective matrix rank. Initial W2/W3 ledger excludes M0.
        admitted=np.full(len(t),-1,dtype=int);admitted[wr]=np.minimum((np.flatnonzero(wr)//cfg['block']+1)*cfg['block'],len(t))
        for p in pr:admitted[p['write_start']:p['t']]=p['t']
        for s in seg:
            if s['action']=='DISCARD':
                ids=np.arange(s['start'],s['end']);ids=ids[wr[ids]];admitted[ids]=s['end']
        counts=np.bincount(admitted[admitted>=0],minlength=len(t)+1).cumsum()
        for end in range(cfg['block'],len(t)+cfg['block'],cfg['block']):
            b=min(end,len(t));occupancy.append({**identity,'decision_hours':float(t[b-1]),'admitted_test':int(counts[b]),'ledger_occupancy':int(counts[b]+(r['n_initial'] if r['op']=='W1' else 0)),'matrix_elements':cfg['dk']*53 if r['op']!='W1' else 0})
        if (ix+1)%24==0:print('evaluated',ix+1,'/',len(runs),flush=True)
    u=pd.DataFrame(units);u.to_csv(out/'units.csv',index=False)
    for name,rows in [('promotions',promotions),('segments',segments),('long_faults',longs),('occupancy',occupancy),('checkpoints_labelled',labelled)]:pd.DataFrame(rows).to_csv(out/(name+'.csv.gz' if name in ['occupancy','checkpoints_labelled'] else name+'.csv'),index=False)
    primary=u[(u.phi_seed==11)&(u.op=='W1')];primary.to_csv(out/'primary_case_results.csv',index=False)
    cols=['AP','VUS_PR','AUROC','VUS_ROC','fault_written_fraction','normal_B_FPR','normal_B_written_fraction','transition_written_fraction','fault_false_promotions','transition_period_promotions','transition_touching_promotions','normal_B_promotion_rate','time_to_safe_promotion_after_70h','promotion_starvation_hours','normal_B_max_unwritten_hours']
    u.groupby(['machine','arm','policy'])[cols].mean().to_csv(out/'case_robustness_means.csv')
    delta=[]
    for scope,df in [('primary_seed11_W1',primary),('robustness_mean',u.groupby(['machine','policy'])[cols].mean().reset_index())]:
        for c,g in df.groupby('machine'):
            tab=g.set_index('policy');cv=tab.loc['DEph_cv']
            for base in ['C_threshold','D_quarantine','D_trail512','DE_stab','A_no_update']:
                delta.append({'scope':scope,'machine':c,'baseline':base,**{'delta_'+k:cv[k]-tab.loc[base,k] for k in ['AP','VUS_PR','normal_B_FPR','fault_written_fraction','normal_B_written_fraction']}})
    pd.DataFrame(delta).to_csv(out/'case_deltas.csv',index=False)
    labeldf=pd.DataFrame(labelled);h=labeldf[(labeldf.policy=='H_hold')&(labeldf.phi_seed==11)&(labeldf.op=='W1')]
    h.groupby(['machine','start','state']).agg(n=('cv','size'),cv_median=('cv','median'),pass_cv=('pass_cv','mean'),pass_conjunction=('pass_conjunction','mean')).to_csv(out/'physical_segment_cv.csv')
    labeldf.groupby(['machine','phi_seed','op','policy','state']).agg(n=('cv','size'),cv_median=('cv','median'),pass_cv=('pass_cv','mean'),pass_conjunction=('pass_conjunction','mean')).to_csv(out/'checkpoint_pass_rates.csv')
    save(out/'complete.json',{'utc':utc(),'units':len(u),'physical_runs':5,'primary':'seed11/W1; other seeds/operators robustness only','benign_AP':'undefined (no faults); not relabelled as anomalies','rl_run':False,'retuned':False})

if __name__=='__main__':evaluate()
