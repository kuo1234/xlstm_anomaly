"""Offline official cached HDF5 schema/profile inventory; no numerical event observations."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import h5py
import numpy as np
from p10_step2d_tep_inspect import OfficialRangeFile
from p10_p3a_response_audit import ROOT,OUT,MANIFEST,sha,save

class NoNetwork:
    def __init__(self): self.denied=[]
    def get(self,*args,**kwargs):
        self.denied.append({"url":args[0], "range":kwargs.get("headers",{}).get("Range")})
        raise RuntimeError("P3-A inventory cache miss; no network/data fallback")

def main():
    api_path=ROOT/"data/step2d/official/article_v1.json"
    api=json.loads(api_path.read_text())
    info=next(f for f in api["files"] if f["name"]=="TEP_Mode1.h5")
    cache=ROOT/"data/step2d/official/ranges_mode1"
    session=NoNetwork()
    ranges=OfficialRangeFile(info,cache,session=session)
    entries=json.loads(MANIFEST.read_text())["datasets"]
    checked=[]; accesses=[]; start=datetime.now(timezone.utc).isoformat()
    with h5py.File(ranges,"r") as f:
        for e in entries:
            g=f[e["source_path"]]
            # Profiles/attrs are evaluator/source audit only. Never read processdata values,
            # additional_meas values, economic_data values, or fault-period observations.
            sp=np.asarray(g["setpoint_init"][:])
            idv=np.asarray(g["idv_init"][:])
            ti=np.asarray(g["time_info"][:])
            attrs={k:np.asarray(v).tolist() for k,v in g.attrs.items()}
            if int(np.asarray(g.attrs["seed"]).ravel()[0])!=e["native_seed"]:
                raise ValueError("native seed provenance mismatch")
            if int(np.asarray(g.attrs["modeAtInit"]).ravel()[0])!=1:
                raise ValueError("operating mode mismatch")
            if sp.shape!=(3,12) or not np.array_equal(sp[0],sp[1]):
                raise ValueError("healthy commanded level not unchanged")
            if idv.shape!=(3,28) or np.any(idv[0]!=0) or np.any((idv[1]!=0)&(idv[2]<30)):
                raise ValueError("fault could occur inside healthy interval")
            schema={}
            for key in g.keys():
                try:
                    d=g[key]
                    schema[key]={"shape":list(d.shape),"dtype":str(d.dtype)}
                except RuntimeError as exc:
                    schema[key]={"status":"UNKNOWN_CACHE_MISS","reason":str(exc)}
            row={"id":e["id"],"source_path":e["source_path"],"native_seed":e["native_seed"],
                 "attrs":attrs,"datasets":schema,
                 "setpoint_profile_sha256":hashlib.sha256(sp.tobytes()).hexdigest(),
                 "idv_profile_sha256":hashlib.sha256(idv.tobytes()).hexdigest(),
                 "time_info_sha256":hashlib.sha256(ti.tobytes()).hexdigest(),
                 "initial_setpoint_values":sp[0].tolist(),"setpoint_no_change":True,
                 "no_active_fault_before30":True,"profile_is_evaluator_only":True,
                 "time_info":ti.tolist(),"values_read":["setpoint_init","idv_init","time_info","attrs"],
                 "processdata_additional_economic_values_read":False}
            checked.append(row)
            accesses.append({"utc":datetime.now(timezone.utc).isoformat(),"kind":"cached source profile/schema audit",
                             "id":e["id"],"source_path":e["source_path"],"numeric_healthy_diagnostic":False,
                             "fault_period_observations_read":False,"values_read":row["values_read"]})
    ledger=json.loads((cache/"hashes.json").read_text())
    # Record actual bounded-range provenance rather than invent a whole-file hash.
    result={"utc":datetime.now(timezone.utc).isoformat(),"status":"VERIFIED_CACHED_SOURCE",
            "source":"official Extended TEP v1","official_file_metadata":info,
            "whole_file_hash_verified":False,"new_network_bytes":ranges.transferred,
            "cache_bytes":sum(p.stat().st_size for p in cache.glob("*.bin")),
            "cache_ledger_sha256":sha(cache/"hashes.json"),"range_sha256":ledger,
            "runs":checked,"runtime_input_enabled":False,"denied_uncached_metadata_requests":session.denied,
            "alignment_status":"processdata Time preserved by old extraction; other datasets lack independently verified timestamps"}
    save(OUT/"source_inventory.json",result)
    log_path=OUT/"source_access_log.json"
    log=json.loads(log_path.read_text());log["cached_hdf5_audit"]={"start_utc":start,"reads":accesses,
                  "network_bytes":ranges.transferred,"source_inventory_sha256":sha(OUT/"source_inventory.json"),
                  "denied_uncached_metadata_requests":session.denied,
                  "prior_attempt":"first cache-only attempt stopped on uncached extra dataset schema after reading healthy100 profiles; no network bytes and no numeric observations"}
    save(log_path,log)
    print("source inventory",len(checked),"new bytes",ranges.transferred,"cache bytes",result["cache_bytes"])

if __name__=="__main__":main()
