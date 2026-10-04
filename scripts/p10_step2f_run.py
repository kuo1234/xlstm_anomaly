"""Observation-only frozen residual audit. No source states, neural optimizer or test writes."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from p10_step2f_data import ROOT,OUT,RAW,CONFIG,load_numeric,sha,save,git,utc
from p10_step1a_oracle import Phi
from p10_step2a_stream import make_mem,W1S

CODE=['scripts/'+x for x in ['p10_step2f_data.py','p10_step2f_run.py','p10_step2f_eval.py','p10_step2e_data.py','p10_step2a_stream.py','p10_step1a_oracle.py','p10_gl1_core.py','p10_gl1_models.py']]+['tests/test_p10_step2f.py']


def scaling(fit,cal,test,view):
    basis=np.concatenate([fit,cal]) if view=='step2e_regression_clip' else fit
    mu=basis.mean(0);raw_sd=basis.std(0);sd=np.maximum(raw_sd,CONFIG['sd_floor'])
    no=[(x-mu)/sd for x in (fit,cal,test)]
    z=no if view=='fit_only_no_clip' else [np.clip(x,-CONFIG['clip'],CONFIG['clip']) for x in no]
    return z,no,mu,sd,raw_sd


def residuals(mem,K,V):
    # Same16-point retrieval chunks as historical A_no_update for exact regression.
    return np.concatenate([V[a:a+16]-mem.read(K[a:a+16]) for a in range(0,len(K),16)])


def manifold(R):
    mean=R.mean(0);cov=np.cov(R,rowvar=False);diag=np.diag(np.diag(cov))
    regular=(1-CONFIG['manifold_shrinkage'])*cov+CONFIG['manifold_shrinkage']*diag+CONFIG['manifold_ridge']*np.eye(53)
    inv=np.linalg.inv(regular);rsd=np.maximum(R.std(0),.02)
    eig,U=np.linalg.eigh(cov);order=np.argsort(eig)[::-1]
    return {'mean':mean,'cov':cov,'inv':inv,'rsd':rsd,'pca':U[:,order[:5]],'pca_evr':np.maximum(eig[order[:5]],0)/max(np.trace(cov),1e-12)}


def summaries(R,normal,raw_sd):
    mu=R.mean(0);e=(R**2).mean(0);total=max(e.sum(),1e-12)
    cov=np.cov(R,rowvar=False);norm_cov=normal['cov']
    def corr(c):
        sd=np.sqrt(np.maximum(np.diag(c),1e-12));return c/sd[:,None]/sd[None,:]
    delta=R-normal['mean'];md=np.einsum('ni,ij,nj->n',delta,normal['inv'],delta)
    mean_delta=mu-normal['mean']
    score=np.linalg.norm(R,axis=1)
    out={'log_score':float(np.log(max(score.mean(),1e-9))),'cv':float(score.std()/max(score.mean(),1e-9)),
     'maha_mean':float(np.sqrt(np.maximum(md,0)).mean()),'maha_centroid':float(np.sqrt(max(mean_delta@normal['inv']@mean_delta,0))),
     'cov_distance':float(np.linalg.norm(cov-norm_cov)/max(np.linalg.norm(norm_cov),1e-12)),
     'corr_distance':float(np.linalg.norm(corr(cov)-corr(norm_cov))/53),
     'manip_energy':float(e[41:].sum()/total),'near_constant_energy':float(e[raw_sd<.02].sum()/total),
     'top5_energy':float(np.sort(e)[-5:].sum()/total),
     'direction_cosine':float(mu@normal['mean']/max(np.linalg.norm(mu)*np.linalg.norm(normal['mean']),1e-12))}
    out.update({f'mean_r_{j}':float(mu[j]/normal['rsd'][j]) for j in range(53)})
    return out


@threadpool_limits.wrap(limits=1)
def job(d,seed):
    fit,cal,test=load_numeric(d);nfit=len(fit);ntrain=nfit+len(cal);w=CONFIG['w'];C=53
    run=OUT/'run';(run/'traces').mkdir(exist_ok=True)
    entries=[];features=[]
    for view in CONFIG['views']:
        z,pre,mu,sd,raw_sd=scaling(fit,cal,test,view);zf,zc,zt=z;train=np.concatenate([zf,zc]);phi=Phi(C,w,CONFIG['dk'],seed)
        ids=np.arange(w,nfit);K0=phi(train,ids);V0=train[ids]
        Kc=phi(train,np.arange(nfit,ntrain));Vc=zc
        ext=np.concatenate([train[-w:],zt]);Kt=phi(ext,np.arange(w,len(ext)))
        for op in CONFIG['ops']:
            mem=make_mem(op,len(K0)+len(Kt)+16,CONFIG['dk'],C,CONFIG['k'])
            mem.write(K0,V0,-np.ones(len(K0),np.int64)) if isinstance(mem,W1S) else mem.write(K0,V0)
            rfit=residuals(mem,K0,V0);rcal=residuals(mem,Kc,Vc);rtest=residuals(mem,Kt,zt)
            norm=manifold(rfit);sc=np.linalg.norm(rtest,axis=1);tau=float(np.quantile(np.linalg.norm(rcal,axis=1),.99))
            name=f'traces/{d["id"]}__s{seed}__{op}__{view}.npz'
            np.savez_compressed(run/name,residual=rtest,score=sc,value_no_clip_score=np.linalg.norm(rtest+(pre[2]-zt),axis=1),clip_mask=np.abs(pre[2])>20,raw_train_sd=raw_sd,
              scaler_mean=mu,scaler_sd=sd,normal_mean=norm['mean'],normal_cov=norm['cov'],normal_inv=norm['inv'],normal_rsd=norm['rsd'],pca=norm['pca'],pca_evr=norm['pca_evr'])
            error=None
            if view=='step2e_regression_clip':
                old=np.load(ROOT/f'research/writable_neural_memory_p10/step2e/run/traces/{d["id"]}__s{seed}__{op}__A_no_update.npz')['score']
                error=float(np.max(np.abs(sc.astype(np.float32)-old)));assert np.allclose(sc.astype(np.float32),old,atol=1e-5,rtol=1e-6),'regression mismatch'
            entries.append({'case':d['id'],'seed':seed,'op':op,'view':view,'file':name,'tau':tau,'regression_max_abs_error':error,'fit_count':nfit,'cal_count':len(cal),'test_count':len(test),'n_initial':len(K0),'test_writes':0})
            for end in range(CONFIG['start_end'],len(test)+1,CONFIG['stride']):
                start=end-CONFIG['window'];features.append({'case':d['id'],'seed':seed,'op':op,'view':view,'start':start,'end':end,**summaries(rtest[start:end],norm,raw_sd)})
    print(d['id'],'seed',seed,'complete',flush=True)
    return entries,features


def main():
    assert CONFIG['neural_training'] is False
    source=git('rev-parse','HEAD');assert git('branch','--show-current')=='research/p7-p10-segment-memory'
    for p in CODE:assert git('hash-object',p)==git('rev-parse',source+':'+p),'uncommitted code '+p
    manifest=json.loads((OUT/'data_split_manifest.json').read_text());assert [d['id'] for d in manifest['datasets']]==CONFIG['cases']
    run=OUT/'run';run.mkdir(exist_ok=True)
    from multiprocessing import Pool
    with Pool(3) as pool:results=pool.starmap(job,[(d,s) for d in manifest['datasets'] for s in CONFIG['seeds']])
    save(run/'runs.json',[x for a,b in results for x in a]);pd.DataFrame([x for a,b in results for x in b]).to_csv(run/'window_evidence.csv.gz',index=False)
    for p in ['data_split_manifest.json','representation_config.json']:(run/p).write_bytes((OUT/p).read_bytes())
    files={str(p.relative_to(run)):sha(p) for p in run.rglob('*') if p.is_file() and p.name!='seal.json'}
    raw={f['file']:f['sha256'] for d in manifest['datasets'] for f in d['files'].values()}
    save(run/'seal.json',{'stage':'step2f_A_observation_only','git_commit':source,'utc':utc(),'labels_read':0,'config':CONFIG,'files':files,'raw':raw,'code':{p:sha(ROOT/p) for p in CODE},'source_metadata_git_blob':manifest['source_metadata_git_blob'],'neural_arm':'NOT_RUN','source_semantics_historically_exposed':True})
    print('SEAL',sha(run/'seal.json'),flush=True)

if __name__=='__main__':main()
