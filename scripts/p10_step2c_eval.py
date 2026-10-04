"""Frozen evaluator: no policy fitting, point-adjust, threshold search or learned probe.
SMD y=0 means source non-anomaly, NEVER certified benign regime.
Primary diagnostic: H_hold seed11/W1 physical segment boundaries. Robustness separately across seeds/operators.
Fault checkpoint: >=50% trailing label1; nonanomaly: 0%; mixed excluded from direction/pass comparison.
Long fault: maximal source label1 run >=256 points. All timings are source point indices (zero-based, exclusive t).
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
sys.path.insert(0,str(Path(__file__).resolve().parent))
from p10_step2c_data import load_test_labels, verify_seal, utc, ProtocolViolation

def episodes(y):
    d=np.diff(np.r_[0,np.asarray(y,dtype=int),0])
    return list(zip(np.flatnonzero(d==1),np.flatnonzero(d==-1)))

def promotions_and_segments(r,sc,ck,cfg):
    """Replay segment endpoints from sealed scores only; no observations/labels or decisions recomputed."""
    pol=r["policy"]; rows=[]; promotions=[]; N=len(sc); B=cfg["block"]
    if pol not in ("D_quarantine","D_trail512","DE_stab","DEph_cv","H_hold"): return rows,promotions
    st=None; gap=0
    promoted=set(int(t) for t in ck.loc[ck.decision=="PROMOTE","t"]) if len(ck) else set()
    for j in range(0,N,B):
        t=min(j+B,N); exc=bool((sc[j:t]>r["tau"]).any())
        if st is None:
            if not exc: continue
            st=j; gap=0
        else: gap=0 if exc else gap+1
        discard=not exc if pol=="D_quarantine" else gap>cfg["seg_gap_blocks"]
        promote=(t-st>=cfg["quarantine_promote_blocks"]*B) if pol=="D_quarantine" else t in promoted
        if discard or promote:
            rows.append(dict(start=st,end=t,duration=t-st,action="PROMOTE" if promote else "DISCARD",censored=False))
            if promote: promotions.append(dict(start=st,t=t,write_start=st if pol=="D_quarantine" else t-cfg["trail"],delay=t-st))
            st=None
    if st is not None: rows.append(dict(start=st,end=N,duration=N-st,action="KEEP",censored=True))
    if len(promotions)!=r["promotions"]: raise ProtocolViolation("promotion reconstruction mismatch")
    return rows,promotions

def metric_job(job):
    from vus.metrics import get_metrics
    r,run,y,checks,cfg,reg=job; z=np.load(Path(run)/r["file"]); sc=z["score"].astype(float); wr=z["written"]
    if len(sc)!=len(y) or not np.isfinite(sc).all(): raise ProtocolViolation("trace/label alignment")
    v=get_metrics(sc,y,metric="vus",slidingWindow=cfg["vus_window"])
    pred=sc>r["tau"]; eps=episodes(y); segs,prom=promotions_and_segments(r,sc,checks,cfg)
    meta={k:r[k] for k in ("machine","phi_seed","op","policy")}
    prom=[dict(**meta,**p,anomaly_fraction=float(y[p["write_start"]:p["t"]].mean()),
               any_fault=bool(y[p["write_start"]:p["t"]].any()),
               majority_fault=bool(y[p["write_start"]:p["t"]].mean()>=0.5),benign_ground_truth="NOT_EVALUABLE") for p in prom]
    segs=[dict(**meta,**s) for s in segs]
    row=dict(**r,AP=float(average_precision_score(y,sc)),AUROC=float(roc_auc_score(y,sc)) if np.unique(y).size==2 else np.nan,
             VUS_PR=float(v["VUS_PR"]),VUS_ROC=float(v["VUS_ROC"]),
             point_recall=float(pred[y==1].mean()) if y.any() else np.nan,normal_FPR=float(pred[y==0].mean()),
             event_recall=float(np.mean([pred[a:b].any() for a,b in eps])) if eps else np.nan,
             anomaly_written_frac=float(wr[y==1].mean()) if y.any() else np.nan,
             fault_promotions=sum(p["any_fault"] for p in prom),majority_fault_promotions=sum(p["majority_fault"] for p in prom),
             nonanomaly_promotions=sum(not p["any_fault"] for p in prom),benign_promotions="NOT_EVALUABLE",
             mean_time_to_promotion=float(np.mean([p["delay"] for p in prom])) if prom else np.nan,
             mean_quarantine_duration=float(np.mean([s["duration"] for s in segs])) if segs else np.nan,
             PF_recall=float(pred[reg & (y==1)].mean()) if (reg & (y==1)).any() else np.nan,
             persistent_nonanomaly_FPR=float(pred[reg & (y==0)].mean()) if (reg & (y==0)).any() else np.nan)
    longs=[]
    for ei,(a,b) in enumerate(eps):
        if b-a<cfg["trail"]: continue
        ch=checks[(checks.t>a)&(checks.t<=b)]
        passes=ch[ch.cv<=cfg["cv_max"]]
        full=passes[(passes["self"]<=cfg["self_max"])&(passes.stat<=cfg["stat_max"])]
        pp=[p for p in prom if p["write_start"]<b and p["t"]>a]
        longs.append(dict(**meta,episode=ei,start=int(a),end=int(b),length=int(b-a),n_checkpoints=len(ch),
                          n_pass_cv=len(passes),n_pass_conjunction=len(full),
                          first_pass_time=int(passes.t.min()) if len(passes) else None,
                          first_conjunction_time=int(full.t.min()) if len(full) else None,
                          was_promoted=bool(pp),n_promotions_touching_fault=len(pp),fraction_fault_written=float(wr[a:b].mean()),
                          point_recall=float(pred[a:b].mean())))
    # Actual occupancy trajectory: move promoted writes from their point times to the decision time.
    # Nonpromoted segment clean tails are committed at DISCARD; remaining held points are never admitted.
    admission=np.full(len(y),-1,dtype=int); admission[wr]=((np.flatnonzero(wr)//cfg["block"])+1)*cfg["block"]
    admission[wr]=np.minimum(admission[wr],len(y))
    for p in prom: admission[p["write_start"]:p["t"]]=p["t"]
    for s in segs:
        if s["action"]=="DISCARD":
            ix=np.arange(s["start"],s["end"]); ix=ix[wr[ix]]; admission[ix]=s["end"]
    ts=np.arange(cfg["block"],len(y)+cfg["block"],cfg["block"]); ts=np.minimum(ts,len(y))
    # All operators here retain a provenance ledger. For W2/W3 occupancy is write count, not effective rank.
    counts=np.bincount(admission[admission>=0],minlength=len(y)+1).cumsum()
    occ=[dict(**meta,t=int(t),admitted_test=int(counts[t]),memory_ledger_occupancy=int((r["n_initial"] if r["op"]=="W1" else 0)+counts[t]),
              matrix_elements=0 if r["op"]=="W1" else cfg["dk"]*38,
              normalizer_elements=cfg["dk"] if r["op"]=="W2_f0995" else 0) for t in ts]
    return row,prom,segs,longs,occ

def main(run,seal_sha,root,out,procs=3):
    run,out=Path(run),Path(out); out.mkdir(parents=True,exist_ok=True)
    proof=verify_seal(run,seal_sha)
    (out/"evaluation_start.json").write_text(json.dumps(dict(**proof,utc=utc()),indent=2)+"\n")
    cfg=json.loads((run/"policy_config.json").read_text()); runs=json.loads((run/"runs.json").read_text())
    ck=pd.read_csv(run/"checkpoints.csv.gz")
    ys={m:load_test_labels(m,run=run,expected_sha=seal_sha,root=root,log_path=out/"label_access_log.json") for m in cfg["machines"]}
    ck["anomaly_fraction"]=[float(ys[m][int(t)-cfg["trail"]:int(t)].mean()) for m,t in zip(ck.machine,ck.t)]
    ck["cls"]=np.where(ck.anomaly_fraction>=.5,"fault",np.where(ck.anomaly_fraction==0,"nonanomaly","mixed"))
    ck["pass_cv"]=ck.cv<=cfg["cv_max"]
    ck["pass_conjunction"]=ck.pass_cv & (ck["self"]<=cfg["self_max"]) & (ck.stat<=cfg["stat_max"])
    ck.to_csv(out/"checkpoints_labelled.csv.gz",index=False)
    H=ck[ck.policy=="H_hold"]; regions={}
    for key,g in H.groupby(["machine","phi_seed","op"]):
        reg=np.zeros(len(ys[key[0]]),bool)
        for st,sg in g.groupby("start"): reg[int(st):int(sg.t.max())]=True
        regions[key]=reg
    jobs=[]
    for r in runs:
        key=(r["machine"],r["phi_seed"],r["op"])
        ch=ck[(ck.machine==key[0])&(ck.phi_seed==key[1])&(ck.op==key[2])&(ck.policy==r["policy"])]
        jobs.append((r,str(run),ys[key[0]],ch,cfg,regions.get(key,np.zeros(len(ys[key[0]]),bool))))
    from multiprocessing import Pool
    res=[]
    with Pool(procs) as pool:
        for i,x in enumerate(pool.imap(metric_job,jobs)):
            res.append(x)
            if (i+1)%8==0: print(f"metrics {i+1}/{len(jobs)}",flush=True)
    units=pd.DataFrame([r[0] for r in res]); units.to_csv(out/"metrics_units.csv",index=False)
    for j,name in [(1,"promotions.csv"),(2,"quarantine_segments.csv"),(3,"long_faults.csv"),(4,"memory_occupancy.csv.gz")]:
        pd.DataFrame([x for r in res for x in r[j]]).to_csv(out/name,index=False)
    nums=units.select_dtypes(include="number").columns.drop("phi_seed")
    macro=units.groupby(["machine","policy"])[nums].mean().reset_index(); macro.to_csv(out/"machine_results.csv",index=False)
    units.groupby(["machine","op","policy"])[nums].mean().to_csv(out/"machine_operator_results.csv")
    comparisons=[]
    for m,g in macro.groupby("machine"):
        a=g.set_index("policy"); cv=a.loc["DEph_cv"]
        for base in ("C_threshold","D_quarantine","D_trail512","DE_stab","A_no_update"):
            comparisons.append(dict(machine=m,baseline=base,delta_AP=cv.AP-a.loc[base].AP,delta_VUS_PR=cv.VUS_PR-a.loc[base].VUS_PR,
                                    delta_recall=cv.point_recall-a.loc[base].point_recall,delta_normal_FPR=cv.normal_FPR-a.loc[base].normal_FPR))
    pd.DataFrame(comparisons).to_csv(out/"machine_deltas.csv",index=False)
    # Source-label fault vs nonanomaly dynamics. Primary unit is physical segment in seed11/W1 reference;
    # rows from other seeds/operators are robustness trajectories, never independent physical cases.
    direction=[]; physical=[]; passrows=[]
    for scope,df in [("primary_seed11_W1",H[(H.phi_seed==11)&(H.op=="W1")]),("robustness_all",H)]:
        for m,g in df.groupby("machine"):
            f=g[g.cls=="fault"]; n=g[g.cls=="nonanomaly"]
            mf=float(f.cv.median()) if len(f) else np.nan; mn=float(n.cv.median()) if len(n) else np.nan
            direction.append(dict(scope=scope,machine=m,n_fault=len(f),n_nonanomaly=len(n),fault_cv_median=mf,nonanomaly_cv_median=mn,
                                  direction="consistent" if mf>mn else "REVERSED" if mf<mn else "unresolved",
                                  cv_AUROC=float(roc_auc_score((g[g.cls!="mixed"].cls=="fault").astype(int),g[g.cls!="mixed"].cv)) if len(f) and len(n) else np.nan))
        for (m,s,op,st),g in df.groupby(["machine","phi_seed","op","start"]):
            f=g[g.cls=="fault"]; n=g[g.cls=="nonanomaly"]
            physical.append(dict(scope=scope,machine=m,phi_seed=s,op=op,start=int(st),last_checkpoint=int(g.t.max()),
                                 n_checkpoints=len(g),n_fault=len(f),n_nonanomaly=len(n),fault_cv_median=f.cv.median(),nonanomaly_cv_median=n.cv.median(),
                                 n_pass_cv_fault=int(f.pass_cv.sum()),n_pass_conjunction_fault=int(f.pass_conjunction.sum())))
        for (m,c),g in df.groupby(["machine","cls"]):
            passrows.append(dict(scope=scope,machine=m,cls=c,n_checkpoints=len(g),pass_cv=float(g.pass_cv.mean()),
                                 pass_conjunction=float(g.pass_conjunction.mean()),cv_median=float(g.cv.median()),
                                 cv_q10=float(g.cv.quantile(.1)),cv_q90=float(g.cv.quantile(.9))))
    pd.DataFrame(direction).to_csv(out/"cv_direction.csv",index=False)
    pd.DataFrame(physical).to_csv(out/"physical_segments.csv",index=False)
    pd.DataFrame(passrows).to_csv(out/"checkpoint_pass_rates.csv",index=False)
    (out/"evaluation_complete.json").write_text(json.dumps(dict(utc=utc(),units=len(units),independent_machines=len(cfg["machines"]),
          new_normal_promotion="NOT EVALUABLE ON THIS DATASET",benign_reason="new-normal promotion not identifiable from source labels"),indent=2)+"\n")

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser(); a.add_argument("--run",required=True); a.add_argument("--seal-sha",required=True)
    a.add_argument("--root",required=True); a.add_argument("--out",required=True); a.add_argument("--procs",type=int,default=3)
    s=a.parse_args(); main(s.run,s.seal_sha,s.root,s.out,s.procs)
