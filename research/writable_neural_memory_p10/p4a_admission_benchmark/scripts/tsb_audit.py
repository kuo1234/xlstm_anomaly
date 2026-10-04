"""Offline label-masked drift qualification; no online detector/model/updates."""
import io,json,zipfile,importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from common import ROOT,OUT,RAW,sha,save,freeze_check,utc

def persistent(curve,valid,threshold=.10):
    hit=np.array(valid,dtype=bool)&(np.array(curve,dtype=float)>=threshold)
    hit[0]=False
    return bool(np.any(hit[:-1]&hit[1:]))
def classify(raw,masked,valid,ratio,c):
    valid=np.array(valid,dtype=bool)
    if len(valid)<3 or not valid[0] or not np.any(valid[1:-1]&valid[2:]):
        return "INSUFFICIENT_SERIES_LENGTH / SUPPORT"
    rawp=persistent(raw,np.ones(len(raw),dtype=bool),c["persistence_JS_nats_min"])
    maskp=persistent(masked,valid,c["persistence_JS_nats_min"])
    retained=ratio is not None and ratio>=c["mask_retention_ratio_min"]
    if maskp and retained:return "REAL_DRIFT_SUPPORTED"
    if rawp and not(maskp and retained):return "DRIFT_ANOMALY_CONFOUNDED"
    return "DRIFT_CAUSE_UNRESOLVED"
def clean_json_array(x):
    return [float(v) if np.isfinite(v) else None for v in x]
def mask_batches(values,labels,batch_len,edges,up,c):
    n=len(values)//batch_len
    counts=np.array([np.sum(labels[k*batch_len:(k+1)*batch_len]==0) for k in range(n)])
    required=max(c["support_min_count"],int(np.ceil(c["support_min_fraction"]*batch_len)))
    valid=counts>=required;P=[]
    for k in np.flatnonzero(valid):
        v=values[k*batch_len:(k+1)*batch_len]
        neg=labels[k*batch_len:(k+1)*batch_len]==0
        P.append(up._hist_probs(v[neg],edges,c["alpha"]))
    M=np.full((n,n),np.nan)
    if P:
        good=np.flatnonzero(valid);M[np.ix_(good,good)]=up.jsd_matrix_from_probs(np.array(P))
    return M,counts,valid,required

def main():
    sealed=freeze_check();c=json.loads((OUT/"tsb_audit_config.json").read_text())
    archive=Path(c["archive_path"])
    if sha(archive)!=c["archive_sha256"]:raise ValueError("archive hash mismatch; no fallback")
    code=ROOT/"data/p4a_admission_benchmark/sources/StrAD/TSB-drift/jsd_drift.py"
    src=next(x for x in json.loads((OUT/"provenance/source_files.json").read_text()) if x["upstream_path"]=="TSB-drift/jsd_drift.py")
    if sha(code)!=src["sha256"]:raise ValueError("pinned audit code changed")
    spec=importlib.util.spec_from_file_location("pinned_jsd",code);up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up)
    previous={x["file"]:x for x in json.loads((ROOT/"reports/phase_a/candidate_inventory.json").read_text())}
    candidate={x["file"]:x for x in json.loads((OUT/"tsb_candidate_inventory.json").read_text())}
    outputs=[];access=[];rawout=RAW/"tsb";rawout.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as z:
      for file in c["assessed_files"]:
        began=utc();blob=z.read(c["archive_member_prefix"]+file)
        import hashlib
        h=hashlib.sha256(blob).hexdigest()
        if h!=previous[file]["raw_sha256"]:raise ValueError("CSV bytes differ from existing source manifest")
        frame=pd.read_csv(io.BytesIO(blob))
        if "Label"!=frame.columns[-1]:raise ValueError("label column contract")
        x=frame.iloc[:,:-1].to_numpy(dtype=float);y=frame.Label.to_numpy()
        n,D=x.shape;B=int(file[:-4].split("_")[-3]);nb=n//B
        record={**candidate[file],"raw_csv_sha256":h,"N":n,"D":D,"batch_length":B,
            "full_batches":nb,"excluded_tail_rows":n%B,"raw_label_counts":{str(k):int(np.sum(y==k)) for k in np.unique(y)},
            "training_label_anomaly_count":int(np.sum(y[:B]!=0)),
            "future_healthy_prefix_eligible":bool(np.all(y[:B]==0)),
            "distribution_drift_cause":"UNKNOWN","legitimate_new_normal":"UNKNOWN",
            "PROMOTE_timing_truth":"NOT_EVALUABLE","operational_unsafe":"NOT_EVALUABLE"}
        access.append({"utc":began,"file":file,"sha256":h,"labels_read":True,
          "purpose":"authorized qualification mask only; not policy training/adaptation",
          "historical_label_exposure":True})
        if not np.isfinite(x).all() or not np.isin(y,[0,1]).all() or nb<3:
            record.update({"qualification":"INSUFFICIENT_SERIES_LENGTH / SUPPORT","reason":"invalid numeric/binary-label or fewer than3 full batches"})
            outputs.append(record);continue
        normalized,_=up.normalize_df_zscore(frame)
        mats,_,edges=up.compute_kl_matrices(normalized,B,features=list(frame.columns[:-1]),
                  bins="auto",alpha=c["alpha"],metric="jsd",drop_incomplete=True)
        rawmax=np.zeros((nb,nb));rawmean=np.zeros((nb,nb));maskmax=np.zeros((nb,nb));maskmean=np.zeros((nb,nb))
        valid=None;support=None;edgeinfo={}
        for name,M in mats.items():
            rawmax=np.maximum(rawmax,M);rawmean+=M/D
            MM,support,valid,required=mask_batches(normalized[name].to_numpy(),y,B,edges[name],up,c)
            if np.ptp(normalized[name].to_numpy())<=1e-12:
                MM[np.isfinite(MM)]=0
            maskmax=np.maximum(maskmax,MM);maskmean+=MM/D
            edgeinfo[name]={"n_bins":len(edges[name])-1,"edges_sha256":hashlib.sha256(np.array(edges[name]).tobytes()).hexdigest()}
        rawcurve=rawmax[0];maskcurve=maskmax[0]
        use=np.flatnonzero(valid & np.isfinite(maskcurve));use=use[use>0]
        rawstrength=float(np.mean(rawcurve[use])) if len(use) else None
        maskstrength=float(np.mean(maskcurve[use])) if len(use) else None
        ratio=maskstrength/rawstrength if rawstrength is not None and rawstrength>1e-12 else None
        qual=classify(rawcurve,maskcurve,valid,ratio,c)
        path=rawout/(file[:-4]+".npz");np.savez_compressed(path,raw_max=rawmax,raw_mean=rawmean,
           masked_max=maskmax,masked_mean=maskmean,normal_counts=support,valid=valid)
        off=~np.eye(nb,dtype=bool)
        maxoff=float(np.max(rawmax[off]));fullmean=float(rawmax.mean())
        record.update({"qualification":qual,"normal_counts_by_batch":support.tolist(),
          "required_normal_count":required,"supported_batches":valid.tolist(),
          "raw_max_feature_anchor_curve":clean_json_array(rawcurve),
          "masked_max_feature_anchor_curve":clean_json_array(maskcurve),
          "raw_mean_feature_anchor_curve":clean_json_array(rawmean[0]),
          "masked_mean_feature_anchor_curve":clean_json_array(maskmean[0]),
          "raw_anchor_strength_common_support":rawstrength,"masked_anchor_strength_common_support":maskstrength,
          "mask_strength_ratio":ratio,"raw_persistence":persistent(rawcurve,np.ones(nb,dtype=bool)),
          "masked_persistence":persistent(maskcurve,valid),
          "raw_reproduction":{"global_max_maxfeature":maxoff,"full_matrix_mean_maxfeature":fullmean,
           "offdiagonal_mean_maxfeature":float(rawmax[off].mean()),
           "global_max_minus_metadata_jsd":maxoff-record["upstream_jsd"],
           "full_mean_minus_metadata_jsd_mean":fullmean-record["upstream_jsd_mean"],
           "original_75_selection_script_verified":False},
          "histogram_edges":edgeinfo,"matrix_file":str(path),"matrix_sha256":sha(path),
          "constant_columns":np.flatnonzero(np.ptp(x,axis=0)==0).tolist(),
          "source_mask_conditioning_not_benign_proof":True})
        outputs.append(record)
        print(file,qual,"ratio",None if ratio is None else round(ratio,3),flush=True)
    valid_ranking=[r for r in outputs if r.get("raw_anchor_strength_common_support") is not None and r.get("masked_anchor_strength_common_support") is not None]
    rho=spearmanr([r["raw_anchor_strength_common_support"] for r in valid_ranking],
                 [r["masked_anchor_strength_common_support"] for r in valid_ranking])
    summary={"utc":utc(),**sealed,"config_sha256":sha(OUT/"tsb_audit_config.json"),
       "archive_sha256":c["archive_sha256"],"series":outputs,"original_inventory_count":75,
       "assessed_count":47,"excluded_simulated":28,
       "classification_counts":{k:sum(r["qualification"]==k for r in outputs) for k in set(r["qualification"] for r in outputs)},
       "rank_diagnostic":{"N_series":len(valid_ranking),"spearman_raw_masked":float(rho.statistic) if np.isfinite(rho.statistic) else None,
                         "p_value":"NOT_REPORTED: traces/families not iid significance units"},
       "strict_confirmatory":False,"no_legitimate_new_normal_claim":True,"models":0,"admission_runs":0}
    save(OUT/"tsb_audit_results.json",summary)
    save(OUT/"provenance/qualification_access_log.json",{"reads":access,"utc":utc(),"host":"ssh kuo","downloads_to_local":False,
       "config_sha256":sha(OUT/"tsb_audit_config.json"),"freeze":sealed,"labels_role":"offline mask qualification only",
       "historical_labels_already_exposed":True,"normal_label_is_not_legitimacy":True,"detector_runs":0})
    print("TSB audit complete",summary["classification_counts"])
if __name__=="__main__":main()
