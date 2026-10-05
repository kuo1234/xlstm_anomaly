"""Post-pushed-seal frozen-model normal-only inference and multiplicity intervention."""
import hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
import pandas as pd
import torch
REPO=Path(__file__).resolve().parents[3];ROOT=REPO/'research/normal_evidence_multiplicity_n0';CACHE=REPO/'data/normal_evidence_multiplicity_n0';E1=REPO/'research/exathlon_lifecycle_e1'
sys.path.insert(0,str(E1/'scripts'))
from models import Predictor,pca_score,infer_lstm
from weights import quantile

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 proof=json.loads((CACHE/'seal.json').read_text());assert subprocess.check_output(['git','ls-remote','origin','refs/heads/'+proof['branch']],text=True).split()[0]==proof['sha']
 for path,h in proof['files'].items():assert sha(REPO/path)==h
 p=json.loads((ROOT/'configs/protocol.json').read_text());manifest=json.loads((ROOT/'configs/test_manifest.json').read_text());training=json.loads((E1/'results/training.json').read_text())
 oldcache=REPO/'data/exathlon_lifecycle_e1';assert sha(oldcache/'scaler.npz')==training['scaler_hash'];assert sha(oldcache/'lstm.pt')==training['checkpoints']['CAUSAL_LSTM_REFERENCE'];assert sha(oldcache/'pca.npz')==training['checkpoints']['PCA_SPE']
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);torch.manual_seed(21)
 scaler=np.load(oldcache/'scaler.npz');basis=np.load(oldcache/'pca.npz')['basis'];model=Predictor();model.load_state_dict(torch.load(oldcache/'lstm.pt',weights_only=True));model.eval()
 art=json.loads((E1/'provenance/score_artifacts.json').read_text());out=[];ledgers=[]
 for b in p['families']:
  groups=[]
  for name in p['fixed_calibration']:
   r=next(x for x in art if x['baseline']==b and x['trace']==name);assert sha(REPO/r['path'])==r['sha256'];v=pd.read_csv(REPO/r['path']).score.to_numpy();groups.append(v[np.isfinite(v)])
  scale=float(np.quantile(np.concatenate(groups),.75)-np.quantile(np.concatenate(groups),.25));assert scale>0
  tests={}
  for row in manifest:
   d=np.load(REPO/row['prepared_path']);t=d['t'];x=d['x'];obs=d['observed'];assert hashlib.sha256(t.tobytes()+x.tobytes()+obs.tobytes()).hexdigest()==row['array_sha256']
   z=((x-scaler['mean'])/scaler['std']).astype(np.float32)
   if b=='PCA_SPE':
    good=obs&np.isfinite(z).all(axis=1);score=np.full(len(t),np.nan);score[good]=pca_score(z[good],basis)
   else:score=infer_lstm(model,z,obs,32)
   dest=CACHE/(b+'_'+row['trace']+'.npz');np.savez_compressed(dest,t=t,score=score,observed=obs)
   tests[row['trace']]=score[np.isfinite(score)];ledgers.append({'baseline':b,'trace':row['trace'],'score_path':str(dest.relative_to(REPO)),'sha256':sha(dest),'scores':len(tests[row['trace']]),'model_hash':training['checkpoints'][b],'target_availability':'target timestamp; only observed finite targets','scaler_hash':training['scaler_hash']})
  for arm in p['arms']:
   for target in range(3):
    for dose in p['multiplicity']:
     mul=[1,1,1];mul[target]=dose;thr=quantile(groups,mul,arm,p['quantile'])
     for name,scores in tests.items():out.append({'baseline':b,'arm':arm,'duplicated_trace':p['fixed_calibration'][target],'dose':dose,'threshold':thr,'calibration_IQR':scale,'test_trace':name,'test_app':int(name.split('_')[0]),'FPR':float(np.mean(scores>thr)),'unique_calibration_scores':sum(map(len,groups)),'row_exposures':sum(len(g)*m for g,m in zip(groups,mul))})
 summary=[];frame=pd.DataFrame(out)
 for b in p['families']:
  data=frame[(frame.baseline==b)&frame.arm.eq('row_pooled')];witnesses=[]
  for name,g in data.groupby('test_trace'):
   for trace,h in g.groupby('duplicated_trace'):
    spread=float(h.FPR.max()-h.FPR.min());shift=float((h.threshold.max()-h.threshold.min())/h.calibration_IQR.iloc[0]);witnesses.append({'test_trace':name,'duplicated_trace':trace,'FPR_spread':spread,'threshold_range_IQR':shift,'material':spread>=.01 and shift>=1})
  for arm in ['trace_balanced','identity_deduplicated_pooled']:
   control=frame[(frame.baseline==b)&frame.arm.eq(arm)];assert all(g.threshold.nunique()==1 and g.FPR.nunique()==1 for _,g in control.groupby('test_trace'))
  summary.append({'baseline':b,'witnesses':witnesses,'material_test_traces':len({x['test_trace'] for x in witnesses if x['material']})})
 supported=all(x['material_test_traces']>=2 for x in summary)
 save(ROOT/'results/intervention.json',out);frame.to_csv(ROOT/'results/intervention.csv',index=False);save(ROOT/'provenance/scores.json',ledgers)
 save(ROOT/'results/gate.json',{'verdict':'MULTIPLICITY_EFFECT_REPLICATED' if supported else 'NO_MATERIAL_EXTERNAL_EFFECT','summary':summary,'method_design_GO':False,'novelty':'UNRESOLVED; generic weights/group mixture occupied','normal_only':True,'fault_recall_measured':False,'training_runs':0,'seal_sha':proof['sha']})
 print('verdict', 'MULTIPLICITY_EFFECT_REPLICATED' if supported else 'NO_MATERIAL_EXTERNAL_EFFECT',flush=True)
if __name__=='__main__':main()
