"""Observation-only residual transfer; frozen FIT M0, no classifier or adaptation."""
import json,numpy as np,pandas as pd
from threadpoolctl import threadpool_limits
from p10_decision_pilot1_data import ROOT,OUT,RAW,CONFIG,load_numeric,save,sha,git,utc
from p10_step2f_run import scaling,residuals,manifold,summaries,CODE as BASE_CODE
from p10_step1a_oracle import Phi
from p10_step2a_stream import make_mem,W1S
CODE=BASE_CODE+['scripts/p10_decision_pilot1_data.py','scripts/p10_decision_pilot1_run.py','scripts/p10_decision_pilot1_eval.py','tests/test_p10_decision_pilot1.py']
@threadpool_limits.wrap(limits=1)
def job(d,seed):
 fit,cal,test=load_numeric(d);w=CONFIG['w'];nfit=len(fit);ntrain=nfit+len(cal);run=OUT/'run';entries=[];features=[]
 for view in CONFIG['views']:
  z,pre,mu,sd,raw_sd=scaling(fit,cal,test,view);zf,zc,zt=z;train=np.concatenate([zf,zc]);phi=Phi(53,w,128,seed)
  ids=np.arange(w,nfit);K0=phi(train,ids);V0=train[ids];Kc=phi(train,np.arange(nfit,ntrain));ext=np.concatenate([train[-w:],zt]);Kt=phi(ext,np.arange(w,len(ext)))
  for op in CONFIG['ops']:
   mem=make_mem(op,len(K0)+len(Kt)+16,128,53,5)
   mem.write(K0,V0,-np.ones(len(K0),np.int64)) if isinstance(mem,W1S) else mem.write(K0,V0)
   norm=manifold(residuals(mem,K0,V0));rc=residuals(mem,Kc,zc);rt=residuals(mem,Kt,zt);score=np.linalg.norm(rt,axis=1)
   name=f'traces/{d["id"]}__s{seed}__{op}__{view}.npz';np.savez_compressed(run/name,residual=rt,score=score,clip_mask=np.abs(pre[2])>20,scaler_mean=mu,scaler_sd=sd,raw_fit_sd=raw_sd)
   entries.append({'case':d['id'],'seed':seed,'op':op,'view':view,'file':name,'tau':float(np.quantile(np.linalg.norm(rc,axis=1),.99)),'test_writes':0,'fit_count':nfit,'cal_count':len(cal),'test_count':len(test)})
   for end in range(256,len(test)+1,128):
    s=summaries(rt[end-256:end],norm,raw_sd);features.append({'case':d['id'],'seed':seed,'op':op,'view':view,'start':end-256,'end':end,**{k:s[k] for k in CONFIG['features']}})
 print(d['id'],seed,'done',flush=True);return entries,features

def main():
 source=git('rev-parse','HEAD');assert git('branch','--show-current')=='research/p7-p10-segment-memory'
 for p in CODE:assert git('hash-object',p)==git('rev-parse',source+':'+p),'uncommitted code'
 manifest=json.loads((OUT/'dataset_manifest.json').read_text());assert manifest['config']==CONFIG
 assert [d['id'] for d in manifest['datasets']]==CONFIG['cases']
 run=OUT/'run';run.mkdir(exist_ok=True);assert not (run/'seal.json').exists(),'do not overwrite seal';(run/'traces').mkdir(exist_ok=True)
 from multiprocessing import Pool
 with Pool(3) as pool:results=pool.starmap(job,[(d,s) for d in manifest['datasets'] for s in CONFIG['seeds']])
 save(run/'runs.json',[x for a,b in results for x in a]);pd.DataFrame([x for a,b in results for x in b]).to_csv(run/'window_evidence.csv.gz',index=False)
 for p in ['dataset_manifest.json','representation_config.json']:(run/p).write_bytes((OUT/p).read_bytes())
 save(run/'seal.json',{'git_commit':source,'utc':utc(),'labels_read_by_runner':0,'curator_metadata_read_before_seal':True,'config':CONFIG,'files':{str(p.relative_to(run)):sha(p) for p in run.rglob('*') if p.is_file() and p.name!='seal.json'},'code':{p:sha(ROOT/p) for p in CODE},'raw':{f['file']:f['sha256'] for d in manifest['datasets'] for f in d['files'].values()},'protocol_files':{p:sha(OUT/p) for p in ['selection.json','evaluator_metadata.json','dataset_manifest.json','representation_config.json','PROTOCOL.md','RESEARCH_DECISION.md']}})
 print('SEAL',sha(run/'seal.json'),flush=True)
if __name__=='__main__':main()
