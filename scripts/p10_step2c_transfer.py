"""Step 2c frozen observation-only runner. All policy mechanics imported unchanged from Step 2a/2b."""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
sys.path.insert(0,str(Path(__file__).resolve().parent))
from p10_step2c_data import MACHINES, ROOT, load_observations, sha256, utc, git, ProtocolViolation
from p10_step2a_stream import CFG2A, W1S, make_mem, run_policy, scale, scores
from p10_step2b_stream import CFG2B, FEATURES, run_seg_policy
from p10_step2b_posthoc import run_cv_policy, PH
from p10_step1a_oracle import Phi

CONFIG=dict(CFG2B,machines=list(MACHINES),cv_max=0.10,posthoc=False,
            rule="self <= 1.0 AND stat <= 0.5 AND cv <= 0.10",
            policies=["A_no_update","B_always","C_threshold","D_quarantine","D_trail512","DE_stab","DEph_cv","H_hold"],
            feature_selection="unchanged Step 2b; H_hold diagnostic only",
            claim="frozen exploratory machine-transfer")
CODE=["scripts/"+p for p in ("p10_step2c_data.py","p10_step2c_transfer.py","p10_step2c_eval.py",
      "p10_step2a_stream.py","p10_step2a_data.py","p10_step2b_stream.py","p10_step2b_posthoc.py",
      "p10_step1a_oracle.py","p10_gl1_core.py","p10_gl1_models.py")]+["tests/test_p10_step2c.py"]

def validate_config(cfg):
    if cfg!=CONFIG or PH["cv_max"]!=0.10: raise ProtocolViolation("frozen configuration mismatch")

def batched_scores(mem,K,V):
    # Pure retrieval batching bounds peak RAM; no writes or calibration changes.
    return np.concatenate([scores(mem,K[a:a+256],V[a:a+256]) for a in range(0,len(K),256)])

@threadpool_limits.wrap(limits=1)
def run_unit(machine,seed,root,out):
    cfg=CONFIG; validate_config(cfg)
    tr=load_observations(machine,"train",root); te=load_observations(machine,"test",root)
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

def main(root,out,manifest,procs):
    validate_config(CONFIG); out=Path(out); out.mkdir(parents=True,exist_ok=True)
    if git("branch","--show-current")!="research/p7-p10-segment-memory": raise ProtocolViolation("wrong branch")
    source=git("rev-parse","HEAD")
    for p in CODE:
        if git("hash-object",p)!=git("rev-parse",source+":"+p): raise ProtocolViolation("code must be committed before run: "+p)
    ds=json.loads(Path(manifest).read_text())
    if [d["machine"] for d in ds["datasets"]]!=list(MACHINES): raise ProtocolViolation("manifest machine order")
    for d in ds["datasets"]:
        for split in ("train","test"):
            p=Path(root)/f'{d["machine"]}_{split}.txt'
            if sha256(p)!=d["files"][split]["sha256"]: raise ProtocolViolation("raw hash changed")
    from multiprocessing import Pool
    jobs=[(m,s,root,str(out)) for m in MACHINES for s in CONFIG["phi_seeds"]]
    with Pool(procs) as pool: res=pool.starmap(run_unit,jobs)
    metas=[x for a,b in res for x in a]; checks=[x for a,b in res for x in b]
    (out/"runs.json").write_text(json.dumps(metas,indent=1)+"\n")
    pd.DataFrame(checks).to_csv(out/"checkpoints.csv.gz",index=False)
    (out/"policy_config.json").write_text(json.dumps(CONFIG,indent=2)+"\n")
    (out/"dataset_manifest.json").write_text(Path(manifest).read_text())
    (out/"machines.json").write_text(json.dumps(list(MACHINES),indent=2)+"\n")
    import subprocess, platform
    (out/"environment.json").write_text(json.dumps(dict(python=sys.version,platform=platform.platform(),
       packages=subprocess.check_output([sys.executable,"-m","pip","freeze"],text=True).splitlines()),indent=2)+"\n")
    files={r["file"]:sha256(out/r["file"]) for r in metas}
    for p in ("runs.json","checkpoints.csv.gz","policy_config.json","dataset_manifest.json","machines.json","environment.json"):
        files[p]=sha256(out/p)
    seal=dict(stage="step2c_label_blind",git_commit=source,machines=list(MACHINES),dataset_ids=[d["dataset_id"] for d in ds["datasets"]],
              phi_seeds=CONFIG["phi_seeds"],operators=CONFIG["ops"],frozen_policy_config=CONFIG,
              files=files,code={p:sha256(ROOT/p) for p in CODE},
              observations={d["machine"]+"/"+s:d["files"][s]["sha256"] for d in ds["datasets"] for s in ("train","test")},
              labels_read=0,cv_max=0.10,posthoc=False,utc=utc())
    (out/"seal.json").write_text(json.dumps(seal,indent=2,sort_keys=True)+"\n")
    print("SEAL SHA256",sha256(out/"seal.json"),flush=True)

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser(); a.add_argument("--root",required=True); a.add_argument("--out",required=True)
    a.add_argument("--manifest",required=True); a.add_argument("--procs",type=int,default=3)
    s=a.parse_args(); main(s.root,s.out,s.manifest,s.procs)
