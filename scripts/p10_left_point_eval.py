"""Truth attaches only after pushed causal-map/model seal; no admission or point adjust."""
import json,sys,numpy as np,pandas as pd
from sklearn.metrics import average_precision_score,roc_auc_score
from p10_left_point_data import ROOT,OUT,RAW,verify,save,sha,utc,states
from p10_left_point_model import MAPS
sys.path.insert(0,str(ROOT/'data/step2e/runtime'))

def ranking(y,s):
 assert len(y)==len(s) and np.isfinite(s).all()
 return {'AP':float(average_precision_score(y,s)),'AUROC':float(roc_auc_score(y,s))}

def evaluate():
 proof=verify();run=OUT/'run';out=OUT/'results';out.mkdir(exist_ok=True);save(out/'evaluation_start.json',proof)
 entries=json.loads((run/'runs.json').read_text());meta={c['id']:c for c in json.loads((OUT/'evaluator_metadata.json').read_text())['cases']};times={};truth={};log=[]
 for c in meta:
  path=RAW/'arrays'/f'{c}_timestamps.npy';log.append({'case':c,'utc':utc(),'purpose':'P2 after pushed causal seal state evaluation','timestamp_sha256':sha(path)});t=np.load(path);times[c]=t;truth[c]=states(t,meta[c]['arm'])
 save(out/'label_access_log.json',log);units=[];windows=[];collapse=[];score_store={}
 from vus.metrics import get_metrics
 for entry in entries:
  c=entry['case'];t=times[c];y=truth[c];z=np.load(run/entry['file']);scores={k:z[k].mean(axis=1) for k in MAPS};scores.update({k:z[k] for k in ['R0_score','R0_shared_fit']});score_store[(entry['anchor'],entry['seed'],c)]=scores
  csv={'timestamp':t,'source_state':y,**scores};pd.DataFrame(csv).to_csv(out/f'{c}__{entry["anchor"]}_point_means.csv.gz',index=False)
  for key,s in scores.items():
   assert len(s)==len(t);tau=entry['R0_tau'] if key=='R0_score' else entry['R0_shared_tau'] if key=='R0_shared_fit' else entry['LEFT_tau'][key];pred=s>tau
   row={'case':c,'anchor':entry['anchor'],'seed':entry['seed'],'score':key,'tau':tau,'NORMAL_A_FPR':float(pred[y=='NORMAL_A'].mean()),'NORMAL_B_FPR':None,'TRANSITION_FPR':None,'fault_recall':None,'event_delay_hours':None,'event_detected':None,'AP':None,'AUROC':None,'VUS_PR':None}
   if np.any(y=='FAULT'):
    yy=y=='FAULT';row.update(ranking(yy,s));row['fault_recall']=float(pred[yy].mean());alarm=t[yy&pred];row['event_detected']=bool(len(alarm));row['event_delay_hours']=float(alarm[0]-30) if len(alarm) else None
    if key in ['score_total','R0_score','R0_shared_fit']:
     v=get_metrics(s,yy.astype(int),metric='vus',slidingWindow=16);row['VUS_PR']=float(v['VUS_PR'])
   else:
    row['NORMAL_B_FPR']=float(pred[y=='NORMAL_B'].mean());row['TRANSITION_FPR']=float(pred[y=='TRANSITION'].mean())
   units.append(row)
   for state in np.unique(y):
    a=s[y==state];collapse.append({'case':c,'anchor':entry['anchor'],'score':key,'state':state,'mean':float(a.mean()),'std':float(a.std()),'min':float(a.min()),'max':float(a.max()),'n':len(a),'finite':bool(np.isfinite(a).all())})
   for end in range(256,len(s)+1,128):
    start=end-256;yy=y[start:end];state=yy[0] if np.all(yy==yy[0]) else 'MIXED';windows.append({'case':c,'anchor':entry['anchor'],'seed':entry['seed'],'score':key,'start':start,'end':end,'state':state,'mean':float(s[start:end].mean()),'end_hours':float(t[end-1])})
 pd.DataFrame(units).to_csv(out/'point_results.csv',index=False);pd.DataFrame(collapse).to_csv(out/'component_range_checks.csv',index=False);w=pd.DataFrame(windows);w.to_csv(out/'windows.csv.gz',index=False)
 ends=set.intersection(*[set(w[(w.case==c)&w.state.isin(['FAULT','NORMAL_B'])].end) for c in meta]);assert ends,'BLOCKED no common state windows';q=w[w.end.isin(ends)&w.state.isin(['FAULT','NORMAL_B'])];q.to_csv(out/'matched_windows.csv',index=False)
 m=q.groupby(['anchor','seed','case','state','score'])['mean'].median().reset_index();m.to_csv(out/'case_component_medians.csv',index=False);pairs=[];metrics=[]
 for (anchor,seed),g in m.groupby(['anchor','seed']):
  table=g.pivot(index=['case','state'],columns='score',values='mean').reset_index();fy=table.state=='FAULT'
  for key in scores:metrics.append({'anchor':anchor,'seed':seed,'score':key,**ranking(fy,table[key]),'unit':'six physical-case medians, not correlated windows'})
  faults=table[fy];benigns=table[~fy]
  for _,f in faults.iterrows():
   for _,b in benigns.iterrows():
    for key in scores:pairs.append({'anchor':anchor,'seed':seed,'fault_case':f['case'],'benign_case':b['case'],'component':key,'fault_minus_benign':float(f[key]-b[key]),'R0_fault_minus_benign':float(f['R0_score']-b['R0_score']),'shared_R0_fault_minus_benign':float(f['R0_shared_fit']-b['R0_shared_fit']),'improves_wrong_R0_direction':bool(f[key]>b[key] and f['R0_score']<=b['R0_score'])})
 pd.DataFrame(pairs).to_csv(out/'case_component_pairs.csv',index=False);pd.DataFrame(metrics).to_csv(out/'validate_case_metrics.csv',index=False)
 # Same >=70h physical timestamps, every run same contribution, threshold-free cross-run point ranking (descriptive only).
 cross=[]
 for anchor,seed in {(e['anchor'],e['seed']) for e in entries}:
  for key in scores:
   values=[];ys=[]
   for c in meta:
    mask=times[c]>=70;values.append(score_store[(anchor,seed,c)][key][mask]);ys.append(truth[c][mask]=='FAULT')
   assert len(set(map(len,values)))==1
   cross.append({'anchor':anchor,'seed':seed,'score':key,**ranking(np.concatenate(ys),np.concatenate(values)),'scope':'FAULT vs NORMAL_B >=70h matched time across6runs; correlated points not N'})
 pd.DataFrame(cross).to_csv(out/'cross_run_point_metrics.csv',index=False)
 save(out/'evaluation_complete.json',{'utc':utc(),'matched_ends':sorted(ends),'point_adjust':False,'classifier_trained':False,'new_threshold':False,'test_training':False,'source_labels_policy_input':False})
if __name__=='__main__':evaluate()
