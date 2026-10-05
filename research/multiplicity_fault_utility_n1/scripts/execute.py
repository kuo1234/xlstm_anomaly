import hashlib,json,sys,subprocess
from pathlib import Path
import numpy as np
import pandas as pd
import torch
REPO=Path(__file__).resolve().parents[3];ROOT=REPO/'research/multiplicity_fault_utility_n1';CACHE=REPO/'data/multiplicity_fault_utility_n1';E1=REPO/'research/exathlon_lifecycle_e1';N0=REPO/'research/normal_evidence_multiplicity_n0'
sys.path.insert(0,str(E1/'scripts'))
from models import Predictor,pca_score,infer_lstm
from utility import fraction
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 proof=json.loads((CACHE/'seal.json').read_text());assert subprocess.check_output(['git','ls-remote','origin','refs/heads/'+proof['branch']],text=True).split()[0]==proof['sha']
 for path,h in proof['files'].items():assert sha(REPO/path)==h
 p=json.loads((ROOT/'configs/protocol.json').read_text());manifest=json.loads((ROOT/'configs/test_manifest.json').read_text());events=json.loads((ROOT/'configs/events.json').read_text());points=pd.read_csv(N0/'results/intervention.csv')
 original=REPO/'data/exathlon_lifecycle_e1';training=json.loads((E1/'results/training.json').read_text());assert sha(original/'scaler.npz')==training['scaler_hash'];assert sha(original/'pca.npz')==training['checkpoints']['PCA_SPE'];assert sha(original/'lstm.pt')==training['checkpoints']['CAUSAL_LSTM_REFERENCE']
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);torch.manual_seed(21);scaler=np.load(original/'scaler.npz');basis=np.load(original/'pca.npz')['basis'];model=Predictor();model.load_state_dict(torch.load(original/'lstm.pt',weights_only=True));model.eval()
 rows=[];ledger=[];availability=[]
 for b in p['families']:
  operating=points[points.baseline.eq(b)].drop_duplicates(['arm','duplicated_trace','dose'])
  for data in manifest:
   d=np.load(REPO/data['prepared_path']);t=d['t'];x=d['x'];obs=d['observed'];assert hashlib.sha256(t.tobytes()+x.tobytes()+obs.tobytes()).hexdigest()==data['array_sha256'];z=((x-scaler['mean'])/scaler['std']).astype(np.float32)
   if b=='PCA_SPE':
    good=obs&np.isfinite(z).all(axis=1);s=np.full(len(t),np.nan);s[good]=pca_score(z[good],basis)
   else:s=infer_lstm(model,z,obs,32)
   dest=CACHE/(b+'_'+data['trace']+'.npz');np.savez_compressed(dest,t=t,score=s,observed=obs);ledger.append({'baseline':b,'trace':data['trace'],'score_path':str(dest.relative_to(REPO)),'sha256':sha(dest),'model_hash':training['checkpoints'][b],'scaler_hash':training['scaler_hash']})
   for ev in [e for e in events if e['trace_name']==data['trace']]:
    lo=int(ev['root_cause_start']);hi=int(ev['combined_end']);check=fraction(t,s,lo,hi,0)
    availability.append({'baseline':b,'event_id':ev['event_id'],'trace':data['trace'],'anomaly_type':ev['anomaly_type'],'primary':ev['anomaly_type'] in p['known_types'],**{k:check[k] for k in ['count','expected','coverage','eligible']}})
    if ev['anomaly_type'] not in p['known_types']:continue
    for op in operating.to_dict('records'):
     rows.append({'baseline':b,'trace':data['trace'],'event_id':ev['event_id'],'anomaly_type':ev['anomaly_type'],'arm':op['arm'],'duplicated_trace':op['duplicated_trace'],'dose':int(op['dose']),'threshold':op['threshold'],**fraction(t,s,lo,hi,op['threshold'])})
 frame=pd.DataFrame(rows);group=frame[frame.eligible].groupby(['baseline','trace','arm','duplicated_trace','dose'],as_index=False).alarm_fraction.mean();summary=[]
 for source in points.duplicated_trace.unique():
  families=[]
  for b in p['families']:
   normal=points[points.baseline.eq(b)&points.arm.eq('row_pooled')&points.duplicated_trace.eq(source)]
   normalspread=max(g.FPR.max()-g.FPR.min() for _,g in normal.groupby('test_trace'))
   fault=group[group.baseline.eq(b)&group.arm.eq('row_pooled')&group.duplicated_trace.eq(source)]
   spreads=[{'trace':tr,'fault_alarm_fraction_range':float(g.alarm_fraction.max()-g.alarm_fraction.min())} for tr,g in fault.groupby('trace')]
   families.append({'baseline':b,'eligible_traces':len(spreads),'material_traces':sum(s['fault_alarm_fraction_range']>=.10 for s in spreads),'paired_normal_max_FPR_spread':float(normalspread),'spreads':spreads})
  summary.append({'duplicated_trace':source,'families':families,'supported':all(x['eligible_traces']==3 and x['material_traces']>=2 and x['paired_normal_max_FPR_spread']<=.005 for x in families)})
 for arm in ['trace_balanced','identity_deduplicated_pooled']:
  control=frame[frame.arm.eq(arm)];assert all(g.alarm_fraction.nunique(dropna=False)==1 and g.threshold.nunique()==1 for _,g in control.groupby(['baseline','event_id']))
 insufficient=any(x['eligible_traces']<3 for ss in summary for x in ss['families'])
 verdict='FAULT_SCORE_SUPPORT_INSUFFICIENT' if insufficient else 'FAULT_UTILITY_EFFECT_REPLICATED' if any(x['supported'] for x in summary) else 'NO_REPLICATED_FAULT_UTILITY_EFFECT'
 save(ROOT/'results/event_operating_points.json',json.loads(frame.to_json(orient='records')));frame.to_csv(ROOT/'results/event_operating_points.csv',index=False);group.to_csv(ROOT/'results/trace_operating_points.csv',index=False);save(ROOT/'results/availability.json',availability);save(ROOT/'provenance/scores.json',ledger)
 save(ROOT/'results/gate.json',{'verdict':verdict,'all_sources':summary,'method_design_GO':False,'novelty_GO':False,'seal_sha':proof['sha'],'training_runs':0,'lifecycle_inference':False});print(verdict,flush=True)
if __name__=='__main__':main()
