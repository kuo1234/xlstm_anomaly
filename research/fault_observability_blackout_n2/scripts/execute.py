"""Post-pushed-seal event/control feasibility; no detector fit/inference."""
import hashlib,json,subprocess
from pathlib import Path
import numpy as np
import pandas as pd
from masks import summarize,masks
REPO=Path(__file__).resolve().parents[3];ROOT=REPO/'research/fault_observability_blackout_n2';CACHE=REPO/'data/fault_observability_blackout_n2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 proof=json.loads((CACHE/'seal.json').read_text());remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+proof['branch']],text=True).split()[0];assert remote==proof['sha']
 for path,digest in proof['files'].items():assert sha(REPO/path)==digest
 p=json.loads((ROOT/'configs/protocol.json').read_text());data=json.loads((ROOT/'configs/test_manifest.json').read_text());events=json.loads((ROOT/'configs/events.json').read_text());controls=json.loads((ROOT/'configs/controls.json').read_text())
 rows=[];secondary=[];ctr=[];ledger=[];recovery=[]
 for source in data:
  arr=np.load(REPO/source['prepared_path']);t=arr['t'];x=arr['x'];obs=arr['observed'];assert hashlib.sha256(t.tobytes()+x.tobytes()+obs.tobytes()).hexdigest()==source['array_sha256'];contracts=masks(x,obs,p['availability_contracts'])
  dest=CACHE/(source['trace']+'_availability.npz');np.savez_compressed(dest,t=t,**{f'W{k}':v for k,v in contracts.items()});ledger.append({'trace':source['trace'],'path':str(dest.relative_to(REPO)),'sha256':sha(dest)})
  for ev in [e for e in events if e['trace_name']==source['trace']]:
   a=int(ev['root_cause_start']);b=int(ev['combined_end']);row={**ev,**summarize(t,x,obs,a,b,p['availability_contracts'])}
   (rows if ev['anomaly_type']=='driver_failure' else secondary).append(row)
   if ev['anomaly_type']!='driver_failure':continue
   # Report observed input-recovery episodes, without assuming an alarm occurs.
   finite=np.isfinite(x).all(axis=1);bad=(t>=a)&(t<=b)&~finite
   ends=np.flatnonzero(bad & np.r_[finite[1:],False])
   for end_id in ends:
    first=end_id+1;future=np.flatnonzero(contracts[32]& (np.arange(len(t))>=first))
    recovery.append({'event_id':ev['event_id'],'trace':source['trace'],'current_features_recovered_at':int(t[first]),'first_W32_available_at':int(t[future[0]]) if len(future) else None,'availability_lag_seconds':int(t[future[0]]-t[first]) if len(future) else None,'within_annotation_end':bool(len(future) and t[future[0]]<=b),'not_detection_delay':True})
  for c in [v for v in controls if v['trace']==source['trace']]:
   if c['eligible']:ctr.append({**c,**summarize(t,x,obs,c['start'],c['end'],p['availability_contracts'])})
 supported=[]
 for r in rows:
  cv=[c for c in ctr if c['event_id']==r['event_id']];r['eligible_pre_controls']=len(cv);r['evaluation_supported']=r['grid_extent_complete'] and bool(cv)
  r['material_history_amplification']=r['evaluation_supported'] and r['W32_additional_fraction']>=.25
  if r['material_history_amplification']:supported.append(r)
 usable=[r for r in rows if r['evaluation_supported']];appcount=len({r['app'] for r in supported});control_median=float(np.median([c['W32_additional_fraction'] for c in ctr])) if ctr else None
 if len(usable)<4 or len({r['app'] for r in usable})<3 or any(c['W0_fraction']<.95 for c in ctr):verdict='CONTROL_SUPPORT_INSUFFICIENT'
 elif len(supported)>=4 and appcount>=3 and control_median is not None and control_median<=.01:verdict='FAULT_SELECTIVE_BLACKOUT_REPLICATED'
 else:verdict='NO_REPLICATED_FAULT_SELECTIVE_AMPLIFICATION'
 save(ROOT/'results/primary_events.json',rows);pd.DataFrame(rows).to_csv(ROOT/'results/primary_events.csv',index=False);save(ROOT/'results/secondary_events.json',secondary);save(ROOT/'results/controls.json',ctr);save(ROOT/'results/input_recovery.json',recovery);save(ROOT/'provenance/mask_artifacts.json',ledger)
 save(ROOT/'results/gate.json',{'verdict':verdict,'primary_events':len(rows),'usable_events':len(usable),'material_events':len(supported),'material_apps':appcount,'eligible_controls':len(ctr),'all_fixed_controls_W0_fraction_at_least95pct':all(c['W0_fraction']>=.95 for c in ctr),'control_median_history_only_loss_fraction':control_median,'method_design_GO':False,'novelty_GO':False,'detector_training_or_scoring_runs':0,'seal_sha':proof['sha'],'inferential_scope':'Conditional finite-history availability contract under exact fixed causal19-feature preprocessing, not all temporal detectors or independent physical units.'});print(verdict,flush=True)
if __name__=='__main__':main()
