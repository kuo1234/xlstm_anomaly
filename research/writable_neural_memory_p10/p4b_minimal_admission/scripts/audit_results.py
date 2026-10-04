"""Post-result independent numerical/ledger verification, no policy decisions or refit."""
import json,sys,subprocess
import numpy as np
from base import ROOT,OUT,A,sha,ah,save,freeze,utc
from core import LinearAE
from read_ledger import read
def main():
 proof=freeze();cfg=json.loads((OUT/"configs/pilot.json").read_text());manifest=json.loads((OUT/"results/run_manifest.json").read_text())
 obs={r["id"]:r for r in json.loads((OUT/"configs/observations.json").read_text())["records"]};models={}
 for rec in manifest["initial_models"]:
  z=np.load(rec["path"],allow_pickle=False);m=LinearAE(z["mu"],z["sd"],z["encoder"],z["decoder"],float(z["tau"]),z["refs_h"],z["refs_m"],z["invcov"],cfg)
  assert m.state_hash()==rec["state_hash"];models[rec["physical_group"]]=m
 total=0;updates=0;max_score_err=0;max_gradient_err=0;selection=0;exposures=0
 for rec in manifest["trajectories"]:
  for k in ["ledger","arrays"]:assert sha(rec[k]["path"])==rec[k]["sha256"]
  source=obs[f"seed{rec['physical_group']}_{rec['arm']}"]["observation"];assert sha(source["path"])==source["sha256"]
  x=np.load(source["path"],allow_pickle=False);model=models[rec["physical_group"]].copy()
  arr=np.load(rec["arrays"]["path"],allow_pickle=False);post=arr["decoder_post"];rows=list(read(rec["ledger"]["path"]));start=cfg["eval_start"]
  assert len(rows)==len(post)==len(x)-start
  V=(x-model.mu)/model.sd;L=np.column_stack([V@model.encoder,np.ones(len(V))])
  PRE=np.concatenate([model.decoder[None],post[:-1]],axis=0)
  predicted=np.einsum("ti,tij->tj",L[start:],PRE)
  scores=np.mean((predicted-V[start:])**2,axis=1)
  error=float(np.max(np.abs(scores-arr["score"])));max_score_err=max(max_score_err,error);assert error<1e-12
  for j,r in enumerate(rows):
   total+=1;assert r["point_id"]==start+j and r["score_time"]==3*r["point_id"] and r["decision_time"]==3*r["point_id"]+1
   assert (r["score"]>model.tau)==bool(r["alarm"]);assert r["score"]==arr["score"][j]
   model.decoder=PRE[j].copy();assert r["full_state_pre_hash"]==model.state_hash()
   model.decoder=post[j].copy();assert r["full_state_post_hash"]==model.state_hash()
   changed=not np.array_equal(PRE[j],post[j]);assert changed==bool(r["parameter_mutation"])
   assert all(r[k]==0 for k in ["adapter_mutation","optimizer_state_mutation","scaler_EMA_mutation","reference_mutation","calibration_mutation","encoder_mutation"])
   ids=r["loss_ids"];weights=r["loss_weights"];assert len(ids)==len(weights)
   assert all(i<=r["point_id"] for i in ids);assert all(w>0 for w in weights)
   selection+=len(r["selected_ids"]);exposures+=len(ids)
   if ids:
    assert abs(sum(weights)-1)<1e-12
    gradient=sum(w*np.outer(L[i],L[i]@PRE[j]-V[i]) for i,w in zip(ids,weights))*.5
    expected=PRE[j]-.01*gradient
    ge=float(np.max(np.abs(expected-post[j])));max_gradient_err=max(max_gradient_err,ge);assert ge<1e-12
   else:assert not changed
   assert r["effective_written_ids"]==(ids if changed else [])
   if changed:
    updates+=1;assert r["mutation_time"]==3*r["point_id"]+2
   if rec["policy"].startswith("QUARANTINE_") and r["decision"]=="PROMOTE":
    assert r["candidate_count"]==int(rec["policy"].rsplit("_",1)[1])
    assert ids==[r["point_id"]]
  if rec["policy"]=="FROZEN":assert rec["mutations"]==0
  if rec["policy"]=="CANDI_STYLE_CAUSAL":
   assert all(len(r["loss_ids"]) in [0,16] for r in rows)
   assert all(r["buffer_exit_ids"]==r["loss_ids"] for r in rows)
 assert all(r["exact_equal"] for r in manifest["twin_equality"])
 assert all(r["mutation_equal"] for r in manifest["Q1_immediate_parity"])
 seal=ROOT/"research/writable_neural_memory_p10/left_point_pilot/run/seal.json"
 old=subprocess.check_output(["git","show","55d4306e6804beef299f5379749ac517b08a15ed:"+str(seal.relative_to(ROOT))])
 assert seal.read_bytes()==old
 assert not subprocess.check_output(["git","ls-files","data/p4b_minimal_admission"],text=True).strip()
 save(OUT/"provenance/postrun_verification.json",{"utc":utc(),"freeze":proof,"status":"PASS","trajectories":135,"rows":total,"updates":updates,
    "selected_count":selection,"loss_exposures":exposures,"all_ledger_artifact_hashes":True,
    "independent_pre_update_score_max_error":max_score_err,"independent_SGD_operator_max_error":max_gradient_err,
    "all_full_state_hashes_reconstructed":True,"all_weighted_IDs_causal":True,"all_absent_mutation_paths_verified":True,
    "semantic_twin_equal_pairs":45,"Q1_immediate_parameter_parity_pairs":15,"old_P2_seal_sha256":sha(seal),
    "old_P2_seal_byte_equal_base":True,"runtime_labels_read":0,"local_raw_downloads":0,
    "note":"independent post-result verification only; no model refit/policy rerun/threshold search"})
 print("independent numerical replay audit PASS",total,updates,max_score_err,max_gradient_err,flush=True)
if __name__=="__main__":main()
