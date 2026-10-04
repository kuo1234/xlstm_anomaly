"""Additive evaluator/report boundary correction; no fit/policy rerun or gate change."""
import json
import numpy as np
from base import OUT,A,sha,save,utc
from read_ledger import read
def clipped_burden(alarm,labels,start,endpoint,censor):
 end=max(start,min(endpoint,censor))
 ids=np.arange(start,end);ids=ids[labels[ids]==0]
 return {"alarms":int(alarm[ids].sum()),"clean_points":int(len(ids)),
    "rate":float(alarm[ids].mean()) if len(ids) else None,"duration":int(end-start),"endpoint":int(end)}
def main():
 metrics=json.loads((OUT/"results/metrics.json").read_text())
 manifest=json.loads((OUT/"results/run_manifest.json").read_text())
 sources={r["id"]:r for r in json.loads((A/"controlled_manifest.json").read_text())["records"]}
 runs={r["seed"]:r for r in json.loads((A/"controlled_config.json").read_text())["physical_runs"]}
 corrections=[]
 for x in metrics["results"]:
  if x["arm"]!="benign_B_with_anomalies":continue
  rec=next(r for r in manifest["trajectories"] if r["id"]==x["trajectory"])
  assert sha(rec["ledger"]["path"])==rec["ledger"]["sha256"]
  rows=list(read(rec["ledger"]["path"]));src=sources[f"seed{x['physical_group']}_{x['arm']}"];yp=src["files"]["truth_anomaly"]
  assert sha(yp["path"])==yp["sha256"];y=np.load(yp["path"],allow_pickle=False);alarms=np.zeros(len(y),dtype=bool)
  for r in rows:alarms[r["point_id"]]=r["alarm"]
  run=runs[x["physical_group"]];start=run["t_transition_start"];settled=run["t_settled_B"];censor=run["acceptance_censor_time"]
  formal=[r["point_id"] for r in rows if r["decision"]=="PROMOTE"]
  pre=[t for t in formal if t<start];during=[t for t in formal if start<=t<settled]
  post=[t for t in formal if t>=start]
  endpoint=post[0] if post else censor
  corrected=clipped_burden(alarms,y,start,endpoint,censor)
  valid=clipped_burden(alarms,y,start,x["valid_commit_time"] if x["valid_commit_time"] is not None else censor,censor)
  corrections.append({"trajectory":x["trajectory"],"physical_group":x["physical_group"],"policy":x["policy"],
    "frozen_raw_burden":x["transition_burden"],"raw_duration_negative":x["transition_burden"]["duration"]<0,
    "pre_transition_formal_times":pre,"transition_premature_formal_times":during,
    "first_formal_at_or_after_transition":post[0] if post else None,
    "burden_until_first_in_transition_formal":corrected,"burden_until_valid_B_commit_secondary":valid})
 save(OUT/"results/reporting_boundary_correction.json",{"utc":utc(),"purpose":"additive report correction only",
    "frozen_metrics_sha256":sha(OUT/"results/metrics.json"),"raw_primary_gate":metrics["gate"],"gate_changed":False,
    "raw_metrics_preserved":True,"policy_or_detector_rerun":False,"cutoff_or_Q_change":False,"affected_raw_negative_durations":sum(r["raw_duration_negative"] for r in corrections),
    "root_cause":"first global PROMOTE precedes transition; raw end-start negative. Formal A point must not terminate a later B-transition interval.",
    "rows":corrections})
 print("reporting-only boundary correction",sum(r["raw_duration_negative"] for r in corrections),"negative raw durations",flush=True)
if __name__=="__main__":main()
