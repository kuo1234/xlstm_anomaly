"""Observation-only orchestration; runtime receives no arm/group/schedule/truth."""
import json,sys,time,io,gzip,csv
from pathlib import Path
import numpy as np
from base import ROOT,OUT,RAW,A,sha,ah,save,freeze,utc
from core import LinearAE,run_array
def write_ledger(path,rows):
 with Path(path).open("wb") as raw:
  with gzip.GzipFile(filename="",fileobj=raw,mode="wb",mtime=0) as gz:
   with io.TextIOWrapper(gz,encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
    for r in rows:
     w.writerow({k:json.dumps(v,separators=(",",":")) if isinstance(v,(list,dict)) else v for k,v in r.items()})
def load_observations(meta):
 path=Path(meta["path"])
 if not path.name.endswith("_observations.npy"):raise ValueError("runtime observation path contract")
 if sha(path)!=meta["sha256"]:raise ValueError("observation hash mismatch")
 x=np.load(path,allow_pickle=False)
 if x.ndim!=2 or x.shape[1]!=4 or not np.isfinite(x).all():raise ValueError("observation finite/dimension contract")
 return x
def main():
 proof=freeze();cfg=json.loads((OUT/"configs/pilot.json").read_text());obs=json.loads((OUT/"configs/observations.json").read_text())["records"]
 RAW.mkdir(parents=True,exist_ok=True);models={};records=[];fit_manifest=[];began=utc();clock=time.perf_counter()
 for group in cfg["physical_groups"]:
  rec=next(r for r in obs if r["group"]==group and r["arm"]=="benign_B_with_anomalies")
  f=Path(rec["observation"]["path"]);assert sha(f)==rec["observation"]["sha256"]
  x=load_observations(rec["observation"])
  # No B passed to fit: initial A-only slices are fixed by pre-result config.
  model=LinearAE.fit(x[:1024],x[1024:1536],cfg);models[group]=model
  path=RAW/f"model_{group}.npz"
  np.savez_compressed(path,mu=model.mu,sd=model.sd,encoder=model.encoder,decoder=model.decoder,tau=np.array(model.tau),
     refs_h=model.refs_h,refs_m=model.refs_m,invcov=model.invcov)
  fit_manifest.append({"physical_group":group,"path":str(path),"sha256":sha(path),"state_hash":model.state_hash(),
    "tau":model.tau,"fit":[0,1024],"cal":[1024,1536],"fit_observations_hash":ah(x[:1024]),"cal_observations_hash":ah(x[1024:1536]),
    "parameter_count_decoder":12,"latent_dim":2,"history":1,"A_cal_FPR":float(np.mean([model.score(v)[0]>model.tau for v in x[1024:1536]]))})
 for rec in obs:
  f=Path(rec["observation"]["path"]);assert sha(f)==rec["observation"]["sha256"];x=load_observations(rec["observation"])
  for policy in cfg["policies"]:
   rid=rec["id"]+"_"+policy;rows,states,pending=run_array(x,models[rec["group"]],policy,cfg["eval_start"])
   ledger=RAW/(rid+".csv.gz");write_ledger(ledger,rows)
   path=RAW/(rid+".npz");np.savez_compressed(path,decoder_post=states,
      score=np.array([r["score"] for r in rows]),alarm=np.array([r["alarm"] for r in rows],dtype=np.uint8))
   # Validate complete causal ledger even before reading evaluator truth.
   for r in rows:
    assert r["score_time"]<r["decision_time"]
    assert not r["parameter_mutation"] or r["mutation_time"]>r["decision_time"]
    assert all(i<=r["point_id"] for i in r["loss_ids"])
    assert len(r["loss_ids"])==len(r["loss_weights"])
    assert bool(r["parameter_mutation"])==(r["full_state_pre_hash"]!=r["full_state_post_hash"])
    assert not any(r[k] for k in ["adapter_mutation","optimizer_state_mutation","scaler_EMA_mutation","reference_mutation","calibration_mutation","encoder_mutation"])
   records.append({"id":rid,"physical_group":rec["group"],"arm":rec["arm"],"policy":policy,
      "observation_sha256":rec["observation"]["sha256"],"initial_state_hash":models[rec["group"]].state_hash(),
      "ledger":{"path":str(ledger),"sha256":sha(ledger),"rows":len(rows)},
      "arrays":{"path":str(path),"sha256":sha(path),"decoder_post_array_hash":ah(states)},
      "final_state_hash":rows[-1]["full_state_post_hash"],"pending_ids_at_end":pending,
      "mutations":sum(r["parameter_mutation"] for r in rows),"loss_exposures":sum(len(r["loss_ids"]) for r in rows),
      "selected_count":sum(len(r["selected_ids"]) for r in rows),"formal_promotions":sum(r["decision"]=="PROMOTE" for r in rows),
      "rollback":"NOT_IMPLEMENTED"})
   print(rid,"mutations",records[-1]["mutations"],"promotions",records[-1]["formal_promotions"],flush=True)
 twin_checks=[];parity=[]
 for group in cfg["physical_groups"]:
  for policy in cfg["policies"]:
   benign=next(r for r in records if r["physical_group"]==group and r["arm"]=="benign_B_with_anomalies" and r["policy"]==policy)
   twin=next(r for r in records if r["physical_group"]==group and r["arm"]=="semantic_fault_twin" and r["policy"]==policy)
   ok=benign["ledger"]["sha256"]==twin["ledger"]["sha256"] and benign["arrays"]["decoder_post_array_hash"]==twin["arrays"]["decoder_post_array_hash"] and benign["final_state_hash"]==twin["final_state_hash"]
   twin_checks.append({"group":group,"policy":policy,"exact_equal":ok});assert ok,"semantic twin equality failed"
  for arm in cfg["arms"]:
   im=next(r for r in records if r["physical_group"]==group and r["arm"]==arm and r["policy"]=="IMMEDIATE_UPDATE")
   q=next(r for r in records if r["physical_group"]==group and r["arm"]==arm and r["policy"]=="QUARANTINE_1")
   ok=im["arrays"]["decoder_post_array_hash"]==q["arrays"]["decoder_post_array_hash"] and im["final_state_hash"]==q["final_state_hash"]
   parity.append({"group":group,"arm":arm,"mutation_equal":ok});assert ok,"Q1 immediate parity failed"
 save(OUT/"results/run_manifest.json",{"started_utc":began,"completed_utc":utc(),**proof,"runtime_labels_read":0,
      "no_runtime_truth_paths":True,"physical_N":5,"technical_replicates":1,"trajectories":records,"initial_models":fit_manifest,
      "twin_equality":twin_checks,"Q1_immediate_parity":parity,"seconds":time.perf_counter()-clock,
      "config_sha256":sha(OUT/"configs/pilot.json"),"host":"ssh kuo","local_raw_downloads":0})
 print("135 observation-only trajectories complete; labels not read",flush=True)
if __name__=="__main__":main()
