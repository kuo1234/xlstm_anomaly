"""Independent M2N2-style dataset generator only. No detector/admission implementation."""
import json
import numpy as np
from common import OUT,RAW,sha,save,freeze_check,utc
def law_parameters(t,run,c,stationary=False):
    w=np.zeros(len(t)) if stationary else np.clip((t-run["t_transition_start"])/256,0,1)
    a=np.array(c["amplitude_A"])[None,:]*(1-w[:,None])+np.array(c["amplitude_B"])[None,:]*w[:,None]
    mu=np.array(c["offset_A"])[None,:]*(1-w[:,None])+np.array(c["offset_B"])[None,:]*w[:,None]
    return a,mu
def series(c,run,arm):
    t=np.arange(c["length"]);stationary=arm=="stationary_A_with_anomalies"
    a,mu=law_parameters(t,run,c,stationary)
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([run["seed"],0])))
    eps=rng.normal(size=(len(t),c["dimensions"]))
    x=a*(np.sin(2*np.pi*t[:,None]*np.array(c["frequency"])[None,:]+np.array(c["phase"]))+c["noise_amp"]*eps)+mu
    states=np.full(len(t),"NORMAL_A",dtype="U32");anomaly=np.zeros(len(t),dtype=np.uint8)
    start,settled=run["t_transition_start"],run["t_settled_B"]
    if not stationary:
        states[start:settled]="BENIGN_TRANSITION";states[settled:]="NORMAL_B_SETTLED"
    sdA=np.sqrt(np.array(c["amplitude_A"])**2*(.5+c["noise_amp"]**2))
    for e in run["events"]:
        lo,hi=e["start"],e["end"]
        for d in e["dimensions"]:
            x[lo:hi,d]+= (1 if e["id"]=="collective_under_B" else -1)*e["severity_sd_A"]*sdA[d]
        states[lo:hi]="TRUE_ANOMALY_UNDER_A" if stationary else "TRUE_ANOMALY_UNDER_B"
        anomaly[lo:hi]=1
    if arm=="semantic_fault_twin":
        states[start:]="NON_BENIGN_PERSISTENT_FAULT";anomaly[start:]=1
    return x,states,anomaly
def fit_scale(x,fit):
    train=x[slice(*fit)]
    mu=train.mean(0);sd=train.std(0)
    return mu,np.where(sd<1e-8,1,sd)
def admissible_payload(states,ids):
    ids=np.array(ids,dtype=int)
    return bool(len(ids) and np.all(states[ids]=="NORMAL_B_SETTLED"))
def old_A_probe(c,run):
    # Separate RNG stream/time extension; never fed to an online algorithm.
    t=np.arange(c["old_A_probe_length"])+c["length"]
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([run["seed"],c["old_A_probe_rng_stream"]])))
    a=np.array(c["amplitude_A"]);mu=np.array(c["offset_A"])
    return a*(np.sin(2*np.pi*t[:,None]*np.array(c["frequency"])+np.array(c["phase"]))+c["noise_amp"]*rng.normal(size=(len(t),c["dimensions"])))+mu
def main():
    sealed=freeze_check();c=json.loads((OUT/"controlled_config.json").read_text())
    raw=RAW/"controlled";raw.mkdir(parents=True,exist_ok=True)
    records=[]
    for run in c["physical_runs"]:
        ref=None
        for arm in c["arms"]:
            x,states,y=series(c,run,arm)
            assert x.shape==(6144,4) and np.isfinite(x).all()
            if arm=="benign_B_with_anomalies":ref=x
            if arm=="semantic_fault_twin":assert np.array_equal(ref,x)
            mu,sd=fit_scale(x,c["fit"])
            rid=f"seed{run['seed']}_{arm}"
            files={}
            for key,v in [("observations",x),("truth_state",states),("truth_anomaly",y),("scaler_mean",mu),("scaler_sd",sd)]:
                p=raw/(rid+"_"+key+".npy");np.save(p,v,allow_pickle=False)
                files[key]={"path":str(p),"sha256":sha(p)}
            vals,counts=np.unique(states,return_counts=True)
            records.append({"id":rid,"physical_group":run["seed"],"arm":arm,"shape":list(x.shape),
                "files":files,"state_counts":dict(zip(vals.tolist(),counts.tolist())),
                "t_transition_start":None if arm=="stationary_A_with_anomalies" else run["t_transition_start"],
                "t_settled_B":run["t_settled_B"] if arm=="benign_B_with_anomalies" else None,
                "events":run["events"],"normality_truth":"synthetic normative intent; not operational unsafe",
                "runtime_has_truth":False})
        p=raw/f"seed{run['seed']}_old_A_probe.npy";np.save(p,old_A_probe(c,run),allow_pickle=False)
        records.append({"id":f"seed{run['seed']}_old_A_probe","physical_group":run["seed"],
          "role":"read-only future snapshot evaluator only","shape":[512,4],"path":str(p),"sha256":sha(p)})
    save(OUT/"controlled_manifest.json",{"utc":utc(),**sealed,"config_sha256":sha(OUT/"controlled_config.json"),
         "physical_N":5,"stream_count":15,"records":records,"models":0,"scores":0,"memory_writes":0,
         "formal_acceptance_not_measured":True})
    print("controlled generator smoke PASS:5 groups,15 streams,5 read-only probes")
if __name__=="__main__":main()
