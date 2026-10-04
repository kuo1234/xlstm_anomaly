"""P3-A healthy-only descriptive audit. No predictor, labels or event arrays."""
import hashlib
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/writable_neural_memory_p10/p3a_response_support"
CONFIG = OUT / "audit_config.json"
MANIFEST = ROOT / "research/writable_neural_memory_p10/left_point_pilot/healthy_train_manifest.json"
ARRAYS = ROOT / "data/left_point_pilot/arrays"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")

def utc():
    return datetime.now(timezone.utc).isoformat()

def check_config(c):
    expected = {"train_ids":[f"healthy{i}" for i in range(100,150)],
                "validation_ids":[f"healthy{i}" for i in range(150,154)],
                "calibration_ids":[f"healthy{i}" for i in range(154,158)],
                "pooled_train_history_lengths":[1,8,16],
                "prefix_lengths":[1,8,128,600], "autocorrelation_lags":list(range(1,17)),
                "relative_eigenvalue_cutoffs":[1e-10,1e-8,1e-6,1e-4],
                "per_run_history_length":1, "channels":53, "n_rows":600,
                "sampling_hours":0.05, "mode":1, "pre_event_only":True,
                "models":0, "anomaly_scores":0, "fault_arrays_read":0,
                "new_inputs_enabled":False, "feature_selection":False,
                "dataset_manifest":str(MANIFEST.relative_to(ROOT)),
                "arrays_dir":str(ARRAYS.relative_to(ROOT))}
    for k,v in expected.items():
        if c.get(k) != v:
            raise ValueError(f"frozen audit config mismatch: {k}")

def load_healthy(entry, root=ARRAYS):
    # Fixed cohort/path allowlist, including symlink escape prevention.
    rid = entry["id"]
    if rid not in {f"healthy{i}" for i in range(100,158)} or entry["file"] != rid+".npy":
        raise ValueError("healthy-only allowlist")
    expected_role = "train" if int(rid[7:])<150 else ("validation" if int(rid[7:])<154 else "calibration")
    if entry["role"] != expected_role:
        raise ValueError("role changed")
    if entry["source_path"] != f"Mode1/SingleFault/SimulationCompleted/IDV1/Mode1_IDVInfo_1_100/Run{rid[7:]}":
        raise ValueError("source path changed")
    if entry["shape"] != [600,53] or entry["time_first"] != 0 or entry["time_last"] != 29.95:
        raise ValueError("healthy prefix contract changed")
    path = root / entry["file"]
    if path.resolve().parent != root.resolve():
        raise ValueError("array escaped healthy directory")
    if sha(path) != entry["sha256"]:
        raise ValueError("healthy hash mismatch")
    x = np.load(path, allow_pickle=False)
    if x.shape != (600,53) or x.dtype != np.float64 or not np.isfinite(x).all():
        raise ValueError("invalid healthy array")
    return x

def train_scale(arrays):
    z = np.concatenate(arrays)
    return z.mean(0), np.maximum(z.std(0),0.02), z.std(0)

def lag_rows(x,p):
    if p<1 or p>=len(x):
        raise ValueError("invalid history length")
    # A row for point t contains only t-1,...,t-p; row boundaries are run boundaries.
    return np.concatenate([x[p-k:len(x)-k] for k in range(1,p+1)],axis=1)

def spectrum(x,cutoffs):
    constant = np.ptp(x,axis=0)==0
    z = x-x.mean(0)
    z[:,constant] = 0
    eig = np.linalg.eigvalsh(z.T@z)[::-1]
    peak = max(float(eig[0]),0)
    bound = 100*np.finfo(np.float64).eps*x.shape[1]*peak
    if np.min(eig)<-bound:
        raise ValueError("Gram spectrum outside roundoff bound")
    eig[np.abs(eig)<=bound] = 0
    eig = np.maximum(eig,0)
    total = float(eig.sum())
    prob = eig[eig>0]/total if total else np.array([])
    return {"rows":len(x),"columns":x.shape[1],
            "singular_values":np.sqrt(eig).tolist(),
            "gram_eigenvalues":eig.tolist(),"roundoff_bound":bound,
            "entropy_effective_rank":float(np.exp(-np.sum(prob*np.log(prob)))) if total else 0,
            "stable_rank":total/peak if peak else 0,
            "resolved_rank_by_relative_eigenvalue":{str(c):int(np.sum(eig>peak*c)) if peak else 0 for c in cutoffs},
            "constant_regressor_columns":np.flatnonzero(constant).tolist(),
            "estimator":"centered float64 Gram eig; near-null singular values are estimates",
            "not_a_plant_identification":True}

def stats(x,lags):
    mean,std=x.mean(0),x.std(0)
    ptp=np.ptp(x,axis=0)
    ac=[]
    for lag in lags:
        a,b=x[:-lag],x[lag:]
        a=a-a.mean(0);b=b-b.mean(0)
        denom=np.sqrt(np.sum(a*a,axis=0)*np.sum(b*b,axis=0))
        values=np.divide(np.sum(a*b,axis=0),denom,out=np.zeros_like(denom),where=denom>0)
        ac.append([float(v) if d>0 and span>0 else None for v,d,span in zip(values,denom,ptp)])
    return {"raw_min":x.min(0).tolist(),"raw_max":x.max(0).tolist(),"raw_mean":mean.tolist(),
            "raw_std":std.tolist(),"raw_ptp":ptp.tolist(),
            "step_rms":np.sqrt(np.mean(np.diff(x,axis=0)**2,axis=0)).tolist(),
            "unchanged_step_fraction":np.mean(np.diff(x,axis=0)==0,axis=0).tolist(),
            "constant_observation_indices":np.flatnonzero(ptp==0).tolist(),
            "numerical_near_constant_indices":np.flatnonzero(std/np.maximum(np.abs(mean),1)<1e-6).tolist(),
            "autocorrelation_lags":lags,"autocorrelation":ac}

def duplicate_audit(entries,arrays,prefix_lengths):
    groups={}
    for n in prefix_lengths:
        bucket=defaultdict(list)
        for e,x in zip(entries,arrays):
            bucket[hashlib.sha256(np.ascontiguousarray(x[:n]).tobytes()).hexdigest()].append(e["id"])
        groups[str(n)]=[{"ids":v,"prefix_sha256":k} for k,v in bucket.items() if len(v)>1]
    pair_prefixes=[]
    for i,a in enumerate(arrays):
        for j in range(i+1,len(arrays)):
            eq=np.all(a==arrays[j],axis=1)
            n=int(np.flatnonzero(~eq)[0]) if not eq.all() else len(a)
            if n:
                pair_prefixes.append({"run_a":entries[i]["id"],"run_b":entries[j]["id"],
                   "rows":n,"cross_role":entries[i]["role"]!=entries[j]["role"]})
    seeds=defaultdict(list)
    for e in entries:seeds[e["native_seed"]].append(e["id"])
    return {"exact_prefix_groups":groups,"pairs_with_nonzero_exact_prefix":pair_prefixes,
            "duplicate_native_seeds":{str(k):v for k,v in seeds.items() if len(v)>1},
            "native_seed_group_count":len(seeds),
            "scope":"all58 and cross roles; exact saved floating values; no RNG independence proof"}

def verify_frozen_sources():
    for source in json.loads((OUT/"source_evidence.json").read_text()).values():
        for path_key,hash_key in [("path","sha256"),("metadata_path","sha256"),
                                  ("text_path","text_sha256"),("code_path","code_sha256")]:
            if path_key in source and sha(ROOT/source[path_key])!=source[hash_key]:
                raise ValueError("source evidence hash mismatch")

def freeze_commit():
    paths=[str(CONFIG.relative_to(ROOT)),str(Path(__file__).resolve().relative_to(ROOT)),
           "tests/test_p10_p3a_response_audit.py",
           str((OUT/"channel_manifest.json").relative_to(ROOT)),
           str((OUT/"source_evidence.json").relative_to(ROOT))]
    for p in paths:
        if subprocess.check_output(["git","show",f"HEAD:{p}"])!=(ROOT/p).read_bytes():
            raise ValueError("uncommitted audit inputs")
    commit=subprocess.check_output(["git","log","-1","--format=%H","--",str(CONFIG.relative_to(ROOT))],text=True).strip()
    remote=subprocess.check_output(["git","ls-remote","origin","refs/heads/research/p7-p10-segment-memory"],text=True).split()[0]
    subprocess.run(["git","merge-base","--is-ancestor",commit,remote],check=True)
    return commit,remote

def main():
    c=json.loads(CONFIG.read_text());check_config(c);verify_frozen_sources()
    commit,remote=freeze_commit()
    entries=json.loads(MANIFEST.read_text())["datasets"]
    ids=c["train_ids"]+c["validation_ids"]+c["calibration_ids"]
    if len(entries)!=58 or [e["id"] for e in entries]!=ids:
        raise ValueError("literal cohort changed")
    access=[];arrays=[]
    for e in entries:
        started=utc();x=load_healthy(e);arrays.append(x)
        access.append({"utc":started,"kind":"healthy-only numeric diagnostic",
                       "id":e["id"],"path":str((ARRAYS/e["file"]).relative_to(ROOT)),
                       "sha256":e["sha256"],"role":e["role"],"rows":600,"channels":53,
                       "fault_or_event_array":False})
    train=[x for e,x in zip(entries,arrays) if e["role"]=="train"]
    mu,sd,rawstd=train_scale(train)
    runs=[]
    for e,x in zip(entries,arrays):
        runs.append({**e,"physical_group":e["source_path"],"mode":1,
            "eligible_interval_hours":"[0,30)","observed_elapsed_hours":29.95,
            "nominal_record_coverage_hours":30,"healthy_transition_windows":0,
            "stats":stats(x,c["autocorrelation_lags"]),
            "history1_spectrum":spectrum(lag_rows((x-mu)/sd,1),c["relative_eigenvalue_cutoffs"])})
    pooled=[]
    for p in c["pooled_train_history_lengths"]:
        rows=np.concatenate([lag_rows((x-mu)/sd,p) for x in train])
        print("spectrum history",p,rows.shape,flush=True)
        pooled.append({"history_steps":p,"history_minutes":3*p,
                       **spectrum(rows,c["relative_eigenvalue_cutoffs"])})
    byrole={}
    for role in ["train","validation","calibration"]:
        chosen=[x for e,x in zip(entries,arrays) if e["role"]==role]
        # No cross-run steps/autocorrelation: separate global marginal spread from per-run summaries.
        y=np.concatenate(chosen)
        byrole[role]={"runs":len(chosen),"rows":len(y),"raw_min":y.min(0).tolist(),
                     "raw_max":y.max(0).tolist(),"raw_mean":y.mean(0).tolist(),
                     "raw_std":y.std(0).tolist(),"raw_ptp":np.ptp(y,axis=0).tolist(),
                     "constant_observation_indices":np.flatnonzero(np.ptp(y,axis=0)==0).tolist(),
                     "numerical_near_constant_indices":np.flatnonzero(y.std(0)/np.maximum(np.abs(y.mean(0)),1)<1e-6).tolist()}
    result={"utc":utc(),"freeze_commit":commit,"remote_commit_before_numeric_audit":remote,
       "audit_config_sha256":sha(CONFIG),"script_sha256":sha(__file__),"manifest_sha256":sha(MANIFEST),
       "input_role":"source-verified healthy prefixes only; no new global label blindness claim",
       "healthy_source_contract":"existing source profiles activated at30h; P3-A does not reclassify by scores",
       "operating_modes":[1],"healthy_command_transition_windows":0,
       "total_runs":58,"train_rows":30000,"runs":runs,"by_role":byrole,
       "duplicate_audit":duplicate_audit(entries,arrays,c["prefix_lengths"]),
       "train_scale":{"mean":mu.tolist(),"sd":sd.tolist(),"raw_std":rawstd.tolist(),
                      "floor_indices":np.flatnonzero(rawstd<0.02).tolist(),"fits_on":"train50 only","clipping":False},
       "pooled_train_lag_spectra":pooled,"models":0,"new_scores":0,"feature_selection":False,
       "sampling_limits":{"saved_minutes":3,"ideal_Nyquist_period_minutes":6,
          "same_tick_ordering":"UNKNOWN","sub_grid_response":"not observable without alias assumptions",
          "response_identified":False,"long_command_response_source_hours":[24,48],
          "training_duration_per_run_hours":30,"eligible_pre_event":True}}
    save(OUT/"healthy_support_manifest.json",result)
    prior=json.loads((OUT/"source_access_log.json").read_text())
    save(OUT/"audit_access_log.json",{"started_from":commit,"audit_config_sha256":sha(CONFIG),
       "execution_host":"ssh kuo","raw_download_to_local":False,
       "source_stage":prior,"healthy_observation_reads":access,"numeric_completed_utc":utc(),
       "fault_arrays_read_in_p3a":0,"labels_evaluator_runs":0,"models":0,"scores":0,
       "historical_source_metadata_exposure":True,
       "additional_or_economic_numeric_values_read_in_p3a":False,
       "protected_p2_seal_not_modified":True})
    print("audit complete",OUT,flush=True)

if __name__=="__main__":main()
