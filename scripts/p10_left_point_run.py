"""Frozen LEFT endpoint maps and two immutable R0 controls; no source state input."""
import json,torch,numpy as np,pandas as pd,time
from threadpoolctl import threadpool_limits
from p10_left_point_data import ROOT,OUT,RAW,UP,check_upstream,healthy_numeric,event_numeric,sha,save,git,utc
from p10_left_point_model import create,endpoint,MAPS
from p10_left_point_train import transform
from p10_step1a_oracle import Phi
from p10_step2a_stream import make_mem,W1S
from p10_step2f_run import scaling,residuals

CODE=['scripts/p10_left_point_'+k+'.py' for k in ['data','model','train','run','eval']]+['tests/test_p10_left_point.py','scripts/p10_step2d_tep_inspect.py','scripts/p10_step2e_data.py','scripts/p10_decision_pilot1_data.py','scripts/p10_step2f_run.py','scripts/p10_step2f_data.py','scripts/p10_step1a_oracle.py','scripts/p10_step2a_stream.py','scripts/p10_gl1_core.py','scripts/p10_gl1_models.py']
PROTOCOL=['selection.json','healthy_train_manifest.json','healthy_numeric_manifest.json','dataset_manifest.json','evaluator_metadata.json','upstream_manifest.json','left_config_primary.json','left_config_robustness.json','training_config.json','RESEARCH_QUESTION.md','UPSTREAM_AUDIT.md','TRAINING_PROTOCOL.md']

@threadpool_limits.wrap(limits=4)
def main():
 check_upstream();source=git('rev-parse','HEAD')
 for p in CODE:assert git('hash-object',p)==git('rev-parse',source+':'+p),'uncommitted code'
 run=OUT/'run';assert not (run/'seal.json').exists();(run/'traces').mkdir(exist_ok=True)
 manifests=json.loads((run/'checkpoints_manifest.json').read_text());events=json.loads((OUT/'dataset_manifest.json').read_text())['datasets'];sc=np.load(run/'scaler.npz');mu,sd=sc['mean'],sc['sd'];cal=transform(healthy_numeric('calibration'),mu,sd);train=transform(healthy_numeric('train'),mu,sd)
 # Shared FIT reference keys never bridge run boundaries.
 phi=Phi(53,8,128,11);ks=[phi(a,np.arange(8,len(a))) for a in train];vs=[a[8:] for a in train];K=np.concatenate(ks);V=np.concatenate(vs);shared=make_mem('W1',len(K)+32,128,53,5);shared.write(K,V,-np.ones(len(K),np.int64))
 shared_cal=np.concatenate([np.linalg.norm(residuals(shared,phi(a,np.arange(191,len(a))),a[191:]),axis=1) for a in cal]);shared_tau=float(np.quantile(shared_cal,.99));entries=[]
 for model in manifests:
  cp=RAW/'checkpoints'/model['checkpoint_file'];assert sha(cp)==model['sha256'];saved=torch.load(cp,map_location='cuda',weights_only=False);net=create(saved['config']);net.load_state_dict(saved['state_dict']);net.eval();prefix=f'{model["anchor"]}_s{model["seed"]}'
  weights_before={k:v.detach().cpu().clone() for k,v in net.state_dict().items()};cal_components={k:[] for k in MAPS}
  for a in cal:
   result=endpoint(net,a,np.arange(192,len(a)+1))
   for k in MAPS:cal_components[k].append(result[k].mean(axis=1))
  taus={k:float(np.quantile(np.concatenate(v),.99)) for k,v in cal_components.items()}
  save(run/f'{prefix}_calibration.json',{'tau':taus,'R0_shared_tau':shared_tau,'healthy_calibration_points':sum(len(a)-191 for a in cal),'threshold_rule':'q.99 of independent healthy calibration endpoint means; not test stats'})
  for d in events:
   tr,te=event_numeric(d);both=np.concatenate([tr,te]);z=np.clip((both-mu)/sd,-20,20);ends=np.arange(len(tr)+1,len(both)+1);result=endpoint(net,z,ends)
   # Historical R0: per-run FIT/CAL scaler, no writes, query current point from past8.
   n=d['fit_count'];zs,_,_,_,_=scaling(tr[:n],tr[n:],te,'fit_only_clip');zf,zc,zt=zs;normal=np.concatenate([zf,zc]);k0=phi(normal,np.arange(8,n));v0=normal[8:n];mem=make_mem('W1',len(k0)+32,128,53,5);mem.write(k0,v0,-np.ones(len(k0),np.int64));r0cal=np.linalg.norm(residuals(mem,phi(normal,np.arange(n,len(normal))),zc),axis=1)
   ext=np.concatenate([normal[-8:],zt]);r0=np.linalg.norm(residuals(mem,phi(ext,np.arange(8,len(ext))),zt),axis=1)
   r0shared=np.linalg.norm(residuals(shared,phi(z,np.arange(len(tr),len(both))),z[len(tr):]),axis=1)
   file=f'traces/{d["id"]}__{prefix}.npz';np.savez_compressed(run/file,**{k:a.astype(np.float32) for k,a in result.items()},R0_score=r0.astype(np.float32),R0_shared_fit=r0shared.astype(np.float32))
   means={'point':np.arange(len(te)),'R0_score':r0,'R0_shared_fit':r0shared,**{k:result[k].mean(axis=1) for k in MAPS}};pd.DataFrame(means).to_csv(run/f'traces/{d["id"]}__{prefix}_means.csv.gz',index=False)
   entries.append({'case':d['id'],'anchor':model['anchor'],'seed':model['seed'],'file':file,'R0_tau':float(np.quantile(r0cal,.99)),'R0_shared_tau':shared_tau,'LEFT_tau':taus,'count':len(te),'timestamp_file':d['files']['timestamps']['file'],'timestamp_sha256':d['files']['timestamps']['sha256'],'alignment':'index0=firsttestpoint; same raw timestamp array for all scores; wrapper never parses time','causal':'past192 endpoint only','test_writes':0});print(d['id'],prefix,'point maps complete',flush=True)
  for k,v in net.state_dict().items():assert torch.equal(v.cpu(),weights_before[k]),'inference changed weights/prototypes'
  del net;torch.cuda.empty_cache()
 save(run/'runs.json',entries)
 raw={f['file']:f['sha256'] for d in events for f in d['files'].values()};raw.update({d['file']:d['sha256'] for d in json.loads((OUT/'healthy_numeric_manifest.json').read_text())['datasets']})
 save(run/'seal.json',{'git_commit':source,'utc':utc(),'labels_read_by_runner':0,'source_curator_metadata_access':True,'files':{str(p.relative_to(run)):sha(p) for p in run.rglob('*') if p.is_file() and p.name!='seal.json'},'code':{p:sha(ROOT/p) for p in CODE},'protocol_files':{p:sha(OUT/p) for p in PROTOCOL},'raw':raw,'checkpoints':{m['checkpoint_file']:m['sha256'] for m in manifests},'test_training':False,'causal_endpoint':True,'no_admission':True})
 print('SEAL',sha(run/'seal.json'),flush=True)
if __name__=='__main__':main()
