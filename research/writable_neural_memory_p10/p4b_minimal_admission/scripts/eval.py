"""Evaluator-only normative truth access, after pushed trace seal."""
import json,subprocess
import numpy as np
from base import ROOT,OUT,A,sha,save,freeze,utc
from core import LinearAE,probe
from read_ledger import read
def mean(v):return float(np.mean(v)) if len(v) else None
def ratio(n,d):return n/d if d else None
def events_for(run,arm,c):
 if arm=="semantic_fault_twin":return [{"id":"persistent_nonbenign_twin","start":run["t_transition_start"],"end":c["length"]}]
 return run["events"]
def recover(alarm,states,start,censor,cfg):
 b=cfg["recovery"]["block"];k=cfg["recovery"]["consecutive"];good=[]
 for lo in range(start,censor-b+1,b):
  mask=np.isin(states[lo:lo+b],["NORMAL_B_SETTLED"])
  ok=int(mask.sum())>=cfg["recovery"]["min_clean_points"] and float(alarm[lo:lo+b][mask].mean())<=cfg["recovery"]["max_FPR"]
  good.append((lo,ok))
 for i in range(len(good)-k+1):
  if all(o for _,o in good[i:i+k]):return {"first_block_start":good[i][0],"confirmation_time":good[i+k-1][0]+b-1,"latency":good[i+k-1][0]+b-1-start}
 return {"censored":True,"censor_time":censor}
def evaluate(rows,post,initial,states,y,run,arm,probe_x,cfg):
 N=len(states);start=cfg["eval_start"];score=np.full(N,np.nan);alarm=np.zeros(N,dtype=bool)
 for r in rows:score[r["point_id"]]=r["score"];alarm[r["point_id"]]=r["alarm"]
 eff=set(i for r in rows for i in r["effective_written_ids"])
 negative={i for i in eff if y[i]==1};exp=[(i,w) for r in rows for i,w in zip(r["loss_ids"],r["loss_weights"])]
 episodes=events_for(run,arm,json.loads((A/"controlled_config.json").read_text()))
 ev=[]
 for e in episodes:
  ids=np.arange(e["start"],e["end"]);hits=ids[alarm[ids]]
  ev.append({**e,"admitted":bool(eff.intersection(ids.tolist())),"written_fraction":sum(i in eff for i in ids)/len(ids),
      "point_recall":float(alarm[ids].mean()),"event_recall":int(bool(len(hits))),"detection_delay":int(hits[0]-e["start"]) if len(hits) else None})
 promotes=[r for r in rows if r["decision"]=="PROMOTE"]
 fault_promotes=[r["point_id"] for r in promotes if any(y[i]==1 for i in r["effective_written_ids"])]
 out={"FAR_admit":mean([e["admitted"] for e in ev]),"negative_episodes":len(ev),"negative_episodes_admitted":sum(e["admitted"] for e in ev),
      "events":ev,"mutations":sum(r["parameter_mutation"] for r in rows),"selected":sum(len(r["selected_ids"]) for r in rows),
      "unique_effective_ids":len(eff),"negative_unique_effective_ids":len(negative),"contaminated_purity":ratio(len(negative),len(eff)),
      "loss_exposure_count":len(exp),"repeated_loss_exposures":len(exp)-len(set(i for i,w in exp)),
      "loss_weight_total":sum(w for i,w in exp),"negative_loss_weight":sum(w for i,w in exp if y[i]==1),
      "weighted_contamination":ratio(sum(w for i,w in exp if y[i]==1),sum(w for i,w in exp)),
      "formal_promotions":len(promotes),"fault_promotion_times":fault_promotes,"fault_promotion_count":len(fault_promotes),
      "native_formal_acceptance":"N/A_NATIVE","rollback":"NOT_IMPLEMENTED",
      "normal_FPR":mean(alarm[np.arange(N)>=start][y[start:]==0].tolist()),
      "all_anomaly_point_recall":mean(alarm[start:][y[start:]==1].tolist()),
      "all_anomaly_event_recall":mean([e["event_recall"] for e in ev])}
 if arm!="benign_B_with_anomalies":
  out.update({"valid_B_acceptance":"NOT_APPLICABLE","TTAccept":None,"valid_before_censor":False,
              "invalid_formal_promotions":len(promotes),"old_A":"N/A_NO_LEGITIMATE_B_COMMIT"})
  return out
 settled=run["t_settled_B"];censor=run["acceptance_censor_time"];transition=run["t_transition_start"]
 valid=[r for r in promotes if r["point_id"]>=settled and r["point_id"]<censor and r["effective_written_ids"]
        and all(states[i]=="NORMAL_B_SETTLED" for i in r["effective_written_ids"])]
 first=valid[0] if valid else None
 invalid=[r["point_id"] for r in promotes if states[r["point_id"]]!="NORMAL_B_SETTLED" or not all(states[i]=="NORMAL_B_SETTLED" for i in r["effective_written_ids"])]
 first_B=next((r["point_id"] for r in rows if r["parameter_mutation"] and any(i>=transition for i in r["effective_written_ids"])),None)
 first_clean=next((r["point_id"] for r in rows if r["parameter_mutation"] and r["effective_written_ids"] and all(states[i]=="NORMAL_B_SETTLED" for i in r["effective_written_ids"])),None)
 firstformal=promotes[0]["point_id"] if promotes else censor
 clean=np.where(states=="NORMAL_B_SETTLED")[0];window=np.arange(censor-256,censor)
 burden_end=min(firstformal,censor);bi=np.arange(transition,burden_end);bi=bi[y[bi]==0]
 baseline_end=min(first_B,censor) if first_B is not None else censor;bbi=np.arange(transition,baseline_end);bbi=bbi[y[bbi]==0]
 out.update({"TTAccept":int(first["point_id"]-settled) if first else None,"formal_status":"VALID" if first else ("N/A_NATIVE" if not rows[0].get("policy_is_Q",False) and not any(r["decision"]=="PROMOTE" for r in rows) else "CENSORED"),
   "valid_commit_time":first["point_id"] if first else None,"valid_before_censor":bool(first),"censor_time":censor,
   "premature_formal_times":[r["point_id"] for r in promotes if r["point_id"]<settled],
   "invalid_formal_times":invalid,"invalid_formal_promotions":len(invalid),
   "first_effective_B_exposure":first_B,"first_wholly_clean_settled_B_exposure":first_clean,
   "first_effective_B_latency_from_settled":first_B-settled if first_B is not None else None,
   "transition_burden":{"alarms":int(alarm[bi].sum()),"clean_points":len(bi),"rate":mean(alarm[bi].tolist()),"duration":burden_end-transition,"endpoint":firstformal},
   "baseline_exposure_aligned_burden":{"alarms":int(alarm[bbi].sum()),"clean_points":len(bbi),"rate":mean(alarm[bbi].tolist()),"duration":baseline_end-transition},
   "clean_B_FPR":mean(alarm[clean].tolist()),"preanomaly_B_FPR":float(alarm[window].mean()),
   "recovery_supplement":recover(alarm,states,settled,censor,cfg),
   "post_valid_commit_event_recall":mean([e["event_recall"] for e in ev]) if first else None,
   "post_valid_commit_point_recall":mean(alarm[np.concatenate([np.arange(e["start"],e["end"]) for e in ev])].tolist()) if first else None,
   "post_baseline_clean_exposure_event_recall":mean([e["event_recall"] for e in ev if first_clean is not None and first_clean<e["start"]]),
   "old_A":"N/A_NO_VALID_B_COMMIT"})
 out["common_old_A_snapshots"]={"initial":probe(initial,initial.decoder,probe_x),
    "pre_first_anomaly":probe(initial,post[censor-start-1],probe_x),"final":probe(initial,post[-1],probe_x)}
 out["common_old_A_snapshots"]["preanomaly_delta_initial"]=out["common_old_A_snapshots"]["pre_first_anomaly"]["FPR"]-out["common_old_A_snapshots"]["initial"]["FPR"]
 if first:
  t=first["point_id"];pre=initial.decoder if t==start else post[t-start-1];after=post[t-start];horizon=post[censor-start-1]
  stats={"initial":probe(initial,initial.decoder,probe_x),"pre_commit":probe(initial,pre,probe_x),"post_commit":probe(initial,after,probe_x),
      "pre_first_anomaly":probe(initial,horizon,probe_x),"final":probe(initial,post[-1],probe_x)}
  stats["same_commit_FPR_delta"]=stats["post_commit"]["FPR"]-stats["pre_commit"]["FPR"]
  stats["gate_max_FPR_delta_initial"]=max(stats[k]["FPR"]-stats["initial"]["FPR"] for k in ["post_commit","pre_first_anomaly"])
  out["old_A"]=stats
 return out
def gate(results,cfg,instrument_ok=True):
 if not instrument_ok:return "PROTOCOL_OR_INSTRUMENTATION_FAIL",[]
 def get(pol,arm):return sorted([r for r in results if r["policy"]==pol and r["arm"]==arm],key=lambda r:r["physical_group"])
 frozen=get("FROZEN","benign_B_with_anomalies");g=cfg["gates"]
 expressed=sum(r["preanomaly_B_FPR"]>=g["expression_FROZEN_B_FPR_min"] for r in frozen)>=g["expression_groups_min"]
 utility={}
 for pol in cfg["policies"]:
  b=get(pol,"benign_B_with_anomalies")
  utility[pol]=sum(f["preanomaly_B_FPR"]-r["preanomaly_B_FPR"]>=g["utility_FPR_decrease_min"] for f,r in zip(frozen,b))
 if not expressed or max(utility.values())<g["utility_groups_min"]:return "ADAPTATION_PROBLEM_NOT_EXPRESSED",[]
 checks=[];im=get("IMMEDIATE_UPDATE","stationary_A_with_anomalies")
 for Q in cfg["Q"]:
  pol="QUARANTINE_"+str(Q);b=get(pol,"benign_B_with_anomalies");st=get(pol,"stationary_A_with_anomalies")
  val=[r for r in b if r["valid_before_censor"]];d=mean([i["FAR_admit"]-r["FAR_admit"] for i,r in zip(im,st)])
  reductions=sum(r["FAR_admit"]<i["FAR_admit"] for i,r in zip(im,st))
  recall_drop=max([f["all_anomaly_event_recall"]-r["post_valid_commit_event_recall"] for f,r in zip(frozen,b) if r["valid_before_censor"]],default=None)
  old=max([r["old_A"]["gate_max_FPR_delta_initial"] for r in val],default=None)
  latency=float(np.median([r["TTAccept"] for r in val])) if val else None
  crit={"coverage":len(val)/5>=g["coverage_min"],"latency":latency is not None and latency<=g["valid_TTA_median_max"],
      "stationary_FAR":d is not None and d>=g["stationary_FAR_decrease_min"] and reductions>=g["stationary_improvement_groups_min"] and sum(r["mutations"] for r in st)>0,
      "event_retention":recall_drop is not None and recall_drop<=g["event_recall_drop_max"],
      "old_A_retention":old is not None and old<=g["old_A_FPR_increase_max"],"ledger":True,"twins_revealed":True}
  checks.append({"Q":Q,"criteria":crit,"all_pass":all(crit.values()),"coverage":len(val)/5,"median_TTA":latency,
    "stationary_FAR_reduction":d,"stationary_improved_groups":reductions,"max_event_recall_drop":recall_drop,"max_old_A_FPR_delta":old,"utility_groups":utility[pol]})
 if any(r["all_pass"] for r in checks):return "SAFE_DELAY_TRADEOFF_SUPPORTED",checks
 if any(r["utility_groups"]>=g["utility_groups_min"] and (r["max_old_A_FPR_delta"] is not None and r["max_old_A_FPR_delta"]>g["old_A_FPR_increase_max"] or r["max_event_recall_drop"] is not None and r["max_event_recall_drop"]>g["event_recall_drop_max"]) for r in checks):
  return "ADAPTATION_HARMS_RETENTION",checks
 duration=False
 for Q in cfg["Q"]:
  st=get("QUARANTINE_"+str(Q),"stationary_A_with_anomalies")
  short=sum(r["events"][0]["admitted"] for r in st);long=sum(r["events"][1]["admitted"] for r in st)
  twin=get("QUARANTINE_"+str(Q),"semantic_fault_twin")
  if short<sum(r["events"][0]["admitted"] for r in im) and long>0 and any(r["negative_episodes_admitted"] for r in twin):duration=True
 return ("DELAY_ONLY_DURATION_FILTER" if duration else "NO_INCREMENT_OVER_EXISTING_ADAPTATION"),checks
def main():
 proof=freeze();cfg=json.loads((OUT/"configs/pilot.json").read_text());manifest=json.loads((OUT/"results/run_manifest.json").read_text())
 tracecommit=subprocess.check_output(["git","log","-1","--format=%H","--",str((OUT/"results/run_manifest.json").relative_to(ROOT))],text=True).strip()
 subprocess.run(["git","merge-base","--is-ancestor",tracecommit,proof["verified_remote_SHA"]],check=True)
 # Runtime artifacts verified BEFORE normative arrays are opened.
 for rec in manifest["trajectories"]:
  for k in ["ledger","arrays"]:assert sha(rec[k]["path"])==rec[k]["sha256"]
 a=json.loads((A/"controlled_manifest.json").read_text());c=json.loads((A/"controlled_config.json").read_text());lookup={r["id"]:r for r in a["records"]};runs={r["seed"]:r for r in c["physical_runs"]}
 initial={}
 for m in manifest["initial_models"]:
  assert sha(m["path"])==m["sha256"];z=np.load(m["path"],allow_pickle=False)
  initial[m["physical_group"]]=LinearAE(z["mu"],z["sd"],z["encoder"],z["decoder"],float(z["tau"]),z["refs_h"],z["refs_m"],z["invcov"],cfg)
  assert initial[m["physical_group"]].state_hash()==m["state_hash"]
 results=[];reads=[]
 for rec in manifest["trajectories"]:
  src=lookup[f"seed{rec['physical_group']}_{rec['arm']}"];statespath=src["files"]["truth_state"];ypath=src["files"]["truth_anomaly"]
  assert sha(statespath["path"])==statespath["sha256"] and sha(ypath["path"])==ypath["sha256"]
  states=np.load(statespath["path"],allow_pickle=False);y=np.load(ypath["path"],allow_pickle=False)
  probe_rec=lookup[f"seed{rec['physical_group']}_old_A_probe"];assert sha(probe_rec["path"])==probe_rec["sha256"];probe_x=np.load(probe_rec["path"],allow_pickle=False)
  rows=list(read(rec["ledger"]["path"]));arr=np.load(rec["arrays"]["path"],allow_pickle=False)
  outcome=evaluate(rows,arr["decoder_post"],initial[rec["physical_group"]],states,y,runs[rec["physical_group"]],rec["arm"],probe_x,cfg)
  outcome.update({"physical_group":rec["physical_group"],"arm":rec["arm"],"policy":rec["policy"],"trajectory":rec["id"]})
  if rec["arm"]=="benign_B_with_anomalies" and not outcome["valid_before_censor"]:
   outcome["formal_status"]="CENSORED" if rec["policy"].startswith("QUARANTINE_") or rec["policy"]=="FROZEN" else "N/A_NATIVE"
  results.append(outcome);reads.append({"utc":utc(),"trajectory":rec["id"],"truth_sha256":statespath["sha256"],"labels_sha256":ypath["sha256"],"role":"evaluator only"})
 good=all(r["exact_equal"] for r in manifest["twin_equality"]) and all(r["mutation_equal"] for r in manifest["Q1_immediate_parity"])
 verdict,checks=gate(results,cfg,good)
 save(OUT/"results/metrics.json",{"utc":utc(),"freeze":proof,"pushed_trace_commit":tracecommit,"physical_N":5,"technical_replicates":1,"gate":verdict,"Q_gate_checks":checks,"results":results,"strict_confirmatory":False,"no_posthoc_rescue":True})
 save(OUT/"provenance/evaluation_access_log.json",{"utc":utc(),"pushed_trace_commit":tracecommit,"freeze":proof,"runtime_labels_read":0,"historical_truth_exposed":True,"evaluator_reads":reads})
 print(verdict,flush=True)
if __name__=="__main__":main()
