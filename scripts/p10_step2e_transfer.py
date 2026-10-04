"""Step 2e frozen point-count transfer runner; numeric train/test files only."""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from p10_step2e_data import ROOT,OUT,RAW,sha,utc,git,save
from p10_step2a_stream import CFG2A,W1S,make_mem,run_policy,scale,scores
from p10_step2b_stream import CFG2B,run_seg_policy
from p10_step2b_posthoc import run_cv_policy,PH
from p10_step1a_oracle import Phi

CONFIG=dict(CFG2B,machines=[f"case{i:02}" for i in range(1,6)],cv_max=.10,posthoc=False,
 policies=["A_no_update","B_always","C_threshold","D_quarantine","D_trail512","DE_stab","DEph_cv","H_hold"],
 rule="self <= 1.0 AND stat <= 0.5 AND cv <= 0.10",claim="restricted controlled simulator pilot; exploratory frozen transfer")
CODE=["scripts/"+x for x in ["p10_step2e_data.py","p10_step2e_transfer.py","p10_step2e_eval.py","p10_step2d_tep_inspect.py","p10_step2a_stream.py","p10_step2b_stream.py","p10_step2b_posthoc.py","p10_step1a_oracle.py","p10_gl1_core.py","p10_gl1_models.py","p10_step2c_eval.py"]]+["tests/test_p10_step2e.py"]

def validate_config():
 assert PH['cv_max']==.10
 for key in ['w','dk','block','check_start','check_every','trail','self_max','stat_max','seg_gap_blocks','fit_frac','calib_q','base_win','promote_age_trail','sd_floor','z_clip','ops','phi_seeds']:
  assert CONFIG[key]==CFG2B[key],key
 assert CONFIG['cv_max']==.10 and CONFIG['posthoc'] is False

def batched_scores(mem,K,V):
 return np.concatenate([scores(mem,K[a:a+256],V[a:a+256]) for a in range(0,len(K),256)])
@threadpool_limits.wrap(limits=1)
def run_unit(machine,seed,root,out):
    cfg=CONFIG; validate_config()
    tr=np.load(Path(root)/f"{machine}_train.npy"); te=np.load(Path(root)/f"{machine}_test.npy")
    ztr,zte=scale(tr,te,cfg); C,w=ztr.shape[1],cfg["w"]
    phi=Phi(C,w,cfg["dk"],seed); fit_end=int(len(tr)*cfg["fit_frac"])
    tfit=np.arange(w,fit_end); tcal=np.arange(fit_end,len(tr))
    K0,V0=phi(ztr,tfit),ztr[tfit]; Kc,Vc=phi(ztr,tcal),ztr[tcal]
    ext=np.concatenate([ztr[-w:],zte]); Kt,Vt=phi(ext,np.arange(w,len(ext))),zte
    cap=len(K0)+len(Kt)+16; zb=np.concatenate([ztr[-cfg["base_win"]:],zte])
    def builder_for(op):
        def builder():
            m=make_mem(op,cap,cfg["dk"],C,cfg["knn_k"])
            m.write(K0,V0,-np.ones(len(K0),np.int64)) if isinstance(m,W1S) else m.write(K0,V0)
            return m
        return builder
    taus={}; low={}; frozen={}
    for op in cfg["ops"]:
        mem=builder_for(op)(); sc=batched_scores(mem,Kc,Vc)
        taus[op]=float(np.quantile(sc,cfg["calib_q"])); low[op]=float(np.quantile(sc,cfg["lb_q"]))
        frozen[op]=batched_scores(mem,Kt,Vt)
    out=Path(out); (out/"traces").mkdir(parents=True,exist_ok=True); metas=[]; checks=[]
    for op in cfg["ops"]:
        builder=builder_for(op)
        ctx=dict(cfg=cfg,tau=taus[op],tau_low=low[op],Kt=Kt,Vt=Vt,K0=K0,
                 zbase=lambda st:zb[st:st+cfg["base_win"]],frozen=frozen,taus=taus)
        for pol in cfg["policies"]:
            if pol in ("A_no_update","B_always","C_threshold","D_quarantine"):
                r=run_policy(pol,op,builder,Kt,Vt,taus[op],dict(CFG2A)); r["checks"]=[]
            elif pol=="DEph_cv": r=run_cv_policy(builder,ctx)
            else: r=run_seg_policy(pol,builder,ctx)
            name=f"traces/{machine}__s{seed}__{op}__{pol}.npz"
            np.savez_compressed(out/name,score=r["score"],written=r["written"])
            e=r["events"]
            metas.append(dict(machine=machine,phi_seed=seed,op=op,policy=pol,tau=taus[op],file=name,
                              n_test=len(Kt),n_initial=len(K0),written_frac=float(r["written"].mean()),
                              mem_size_end=r["mem_size"],promotions=e.get("promotions",0),discards=e.get("discards",0),
                              quarantined_points=e.get("quarantined_points",0),n_checks=len(r["checks"]),runtime_s=r["runtime_s"]))
            for c in r["checks"]: checks.append(dict(machine=machine,phi_seed=seed,op=op,policy=pol,**c))
        print(f"{machine} seed={seed} {op} complete",flush=True)
    return metas,checks

def main():
 validate_config();run=OUT/'run';run.mkdir(exist_ok=True)
 source=git('rev-parse','HEAD');assert git('branch','--show-current')=='research/p7-p10-segment-memory'
 for p in CODE:assert git('hash-object',p)==git('rev-parse',source+':'+p),'uncommitted code '+p
 manifest=json.loads((OUT/'dataset_manifest.json').read_text())
 assert [d['id'] for d in manifest['datasets']]==CONFIG['machines']
 raw={}
 for d in manifest['datasets']:
  for name,f in d['files'].items():assert sha(RAW/f['file'])==f['sha256'];raw[f['file']]=f['sha256']
 from multiprocessing import Pool
 with Pool(3) as pool:result=pool.starmap(run_unit,[(c,s,str(RAW),str(run)) for c in CONFIG['machines'] for s in CONFIG['phi_seeds']])
 save(run/'runs.json',[x for a,b in result for x in a]);pd.DataFrame([x for a,b in result for x in b]).to_csv(run/'checkpoints.csv.gz',index=False)
 save(run/'policy_config.json',CONFIG)
 (run/'dataset_manifest.json').write_bytes((OUT/'dataset_manifest.json').read_bytes())
 import platform, subprocess
 save(run/'environment.json',{'python':sys.version,'platform':platform.platform(),'packages':subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True).splitlines(),'vus':'0.0.6 in ignored data/step2e/runtime'})
 files={str(p.relative_to(run)):sha(p) for p in run.rglob('*') if p.is_file() and p.name!='seal.json'}
 save(run/'seal.json',{'stage':'step2e_observation_only','git_commit':source,'utc':utc(),'frozen_config':CONFIG,'files':files,'code':{p:sha(ROOT/p) for p in CODE},'raw':raw,'cv_max':.10,'posthoc':False,'labels_read_by_runner':0,'prior_source_semantic_exposure':True,'evaluator_metadata_git_blob':git('rev-parse',source+':research/writable_neural_memory_p10/step2e/evaluator_metadata.json')})
 print('seal',sha(run/'seal.json'),flush=True)

if __name__=='__main__':main()
