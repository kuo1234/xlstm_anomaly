"""Source states allowed only after exact observation-only seal is pushed."""
import json,numpy as np,pandas as pd
from sklearn.metrics import roc_auc_score,average_precision_score
from p10_decision_pilot1_data import OUT,RAW,CONFIG,verify,save,sha,utc,states

def evaluate():
 audit=verify();out=OUT/'results';out.mkdir(exist_ok=True);save(out/'evaluation_start.json',audit)
 meta=json.loads((OUT/'evaluator_metadata.json').read_text());mapping={x['id']:x for x in meta['cases']};windows=pd.read_csv(OUT/'run/window_evidence.csv.gz');log=[];rows=[]
 for case in CONFIG['cases']:
  path=RAW/f'{case}_timestamps.npy';log.append({'case':case,'utc':utc(),'purpose':'sealed evaluator source states','timestamp_sha256':sha(path)});t=np.load(path);y=states(t,mapping[case]['arm'])
  for row in windows[windows.case==case].to_dict('records'):
   yy=y[row['start']:row['end']];state=yy[0] if np.all(yy==yy[0]) else 'MIXED';rows.append({**row,'state':state,'end_hours':float(t[row['end']-1])})
 save(out/'label_access_log.json',log);d=pd.DataFrame(rows);d.to_csv(out/'windows_labelled.csv.gz',index=False)
 ends=set.intersection(*[set(d[(d.case==c)&d.state.isin(['FAULT','NORMAL_B'])].end) for c in CONFIG['cases']]);assert ends,'PROTOCOL_INCOMPATIBLE no common windows'
 q=d[d.end.isin(ends)&d.state.isin(['FAULT','NORMAL_B'])].copy();q.to_csv(out/'age_matched_evidence.csv',index=False)
 m=q.groupby(['view','seed','op','case','state'])[CONFIG['features']].median().reset_index();m.to_csv(out/'physical_case_medians.csv',index=False)
 comparisons=[];metrics=[]
 for (view,seed,op),cell in q.groupby(['view','seed','op']):
  cm=m[(m.view==view)&(m.seed==seed)&(m.op==op)];fault=cm.state=='FAULT'
  for f in CONFIG['features']:metrics.append({'view':view,'seed':seed,'op':op,'feature':f,'case_AUROC_fault_high':float(roc_auc_score(fault,cm[f])),'case_AP_fault_high':float(average_precision_score(fault,cm[f])),'n_physical_cases':len(cm)})
  for fc in cell[cell.state=='FAULT'].case.unique():
   for bc in cell[cell.state=='NORMAL_B'].case.unique():
    a=cell[cell.case==fc].set_index('end');b=cell[cell.case==bc].set_index('end');delta=a.loc[sorted(ends),'top5_energy']-b.loc[sorted(ends),'top5_energy'];comparisons.append({'view':view,'seed':seed,'op':op,'fault_case':fc,'benign_case':bc,'min_delta':float(delta.min()),'max_delta':float(delta.max()),'median_delta':float(delta.median()),'fault_high_fraction':float((delta>0).mean()),'matched_ages':len(ends)})
 pd.DataFrame(comparisons).to_csv(out/'pair_directions.csv',index=False);pd.DataFrame(metrics).to_csv(out/'physical_case_metrics.csv',index=False)
 save(out/'evaluation_complete.json',{'utc':utc(),'matched_end_indices':sorted(ends),'primary_unit':'physical run/native family; pair/window/seed/operator not independent N','classifier_fitted':False,'new_threshold':False,'controller':False})
if __name__=='__main__':evaluate()
