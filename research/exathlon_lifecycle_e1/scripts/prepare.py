"""Pre-result raw acquisition, identity audit and causal feature materialization."""
import concurrent.futures, csv, hashlib, io, json, sys, urllib.request, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; REPO=ROOT.parents[1]
E0=REPO/'research/exathlon_semantic_failure_e0'; CACHE=REPO/'data/exathlon_lifecycle_e1'
PIN='4101f6087f902fa150e392b65c957976faa84e40'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
IDENTITY=['driver_StreamingMetrics_streaming_lastCompletedBatch_'+s+'_value' for s in ['processingDelay','schedulingDelay','totalDelay']]
DIFF=['driver_StreamingMetrics_streaming_'+s+'_value' for s in ['totalCompletedBatches','totalProcessedRecords','totalReceivedRecords','lastReceivedBatch_records']]+['driver_BlockManager_memory_memUsed_MB_value','driver_jvm_heap_used_value']+[f'node{i}_CPU_ALL_Idle%' for i in range(5,9)]
EXEC=['executor_filesystem_hdfs_write_ops_value','executor_cpuTime_count','executor_runTime_count','executor_shuffleRecordsRead_count','executor_shuffleRecordsWritten_count','jvm_heap_used_value']
INPUTS=IDENTITY+DIFF+[f'{i}_{s}' for s in EXEC for i in range(1,6)]
FEATURES=IDENTITY+['diff_'+s for s in DIFF]+['diff_avg_'+s for s in EXEC]
def normalize(c):
    if '_StreamingMetrics_' in c:return 'driver_StreamingMetrics_'+c.split('_StreamingMetrics_',1)[1]
    return c

def features(raw):
    """Deduplicate by first recorded row; insert 1s grid; bounded past fill only."""
    raw=raw.copy();raw.columns=[normalize(c) for c in raw.columns]
    assert raw.t.notna().all() and np.isfinite(raw.t).all()
    assert (raw.t==np.floor(raw.t)).all() and (np.diff(raw.t)>=0).all()
    assert not raw.columns.duplicated().any()
    raw=raw.drop_duplicates('t',keep='first').set_index('t')
    grid=np.arange(int(raw.index.min()),int(raw.index.max())+1)
    observed=np.isin(grid,raw.index);x=raw.reindex(grid)[INPUTS].astype(float)
    x=x.mask(~np.isfinite(x)|(x==-1))
    active=x.copy()  # Inactive executor sentinels never become active through per-slot fill.
    x=x.ffill(limit=5)
    base=x[IDENTITY].copy()
    for s in DIFF:base['diff_'+s]=x[s].diff()
    for s in EXEC:
        avg=active[[f'{i}_{s}' for i in range(1,6)]].mean(axis=1).ffill(limit=5)
        base['diff_avg_'+s]=avg.diff()
    arr=base[FEATURES].to_numpy(dtype=np.float32)
    return grid,arr,observed

def acquire(row):
    path=CACHE/'raw'/Path(row['path']).name;path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        req=urllib.request.Request(row['url'],headers={'User-Agent':'xlstm-anomaly-E1-audit'})
        with urllib.request.urlopen(req,timeout=180) as src,path.open('wb') as dst:
            while chunk:=src.read(1024*1024):dst.write(chunk)
    blob=hashlib.sha1(b'blob '+str(path.stat().st_size).encode()+b'\0')
    with path.open('rb') as h:
        while chunk:=h.read(1024*1024):blob.update(chunk)
    assert blob.hexdigest()==row['git_blob_sha'],path
    row['sha256']=sha(path);row['bytes']=path.stat().st_size;row['local_path']=str(path.relative_to(REPO))
    return row

def main():
    CACHE.mkdir(parents=True,exist_ok=True)
    tree=json.loads((E0/'provenance/exathlon_tree.json').read_text())['tree']
    trace=pd.read_csv(E0/'results/trace_context_inventory.csv');gt=pd.read_csv(E0/'results/event_coverage.csv')
    apps=[6,9,10];roles=['fit','validation','calibration','normal_control'];selection=[]
    single={Path(r['path']).stem:r for r in tree if r['type']=='blob' and r['path'].startswith('data/raw/app') and r['path'].count('/')==3 and r['path'].endswith('.zip')}
    for app in apps:
        n=trace[trace.app.eq(app)&trace.trace_type.eq('undisturbed')]
        names=sorted((x for x in n.trace if x in single),key=lambda x:(single[x]['size'],int(x.split('_')[-1])))[:4]
        names=sorted(names,key=lambda x:int(x.split('_')[-1]));assert len(names)==4
        selection += [dict(trace=name,role=role) for name,role in zip(names,roles)]
    primary_types=['bursty_input','stalled_input','cpu_contention']
    names=sorted(set(gt.loc[gt.app.isin(apps)&gt.anomaly_type.isin(primary_types),'trace_name']))
    selection += [dict(trace=n,role='disturbed') for n in names]
    selection.append(dict(trace='10_2_1000000_67',role='crash_control'))
    rows=[]
    for s in selection:
        r=single[s['trace']];rows.append({**s,'path':r['path'],'git_blob_sha':r['sha'],'url':f'https://raw.githubusercontent.com/exathlonbenchmark/exathlon/{PIN}/{r["path"]}'})
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(acquire,rows))
    save(ROOT/'provenance/raw_sources.json',rows)
    audits=[];mat=[]
    for row in rows:
        path=REPO/row['local_path']
        with zipfile.ZipFile(path) as z:
            member=next(x for x in z.namelist() if x.endswith('.csv'))
            digest=hashlib.sha256()
            with z.open(member) as h:
                while chunk:=h.read(1024*1024):digest.update(chunk)
            with z.open(member) as h:columns=next(csv.reader(io.TextIOWrapper(h)))
            chosen=[c for c in columns if c=='t' or normalize(c) in INPUTS]
            assert len(chosen)==len(INPUTS)+1,(row['trace'],len(chosen))
            with z.open(member) as h:raw=pd.read_csv(h,usecols=chosen)
        t,x,obs=features(raw)
        dest=CACHE/'prepared'/f'{row["trace"]}.npz';dest.parent.mkdir(exist_ok=True)
        # Arrays are deterministic; zip/container bytes are not used for identity.
        np.savez_compressed(dest,t=t,x=x,observed=obs)
        array_hash=hashlib.sha256(t.tobytes()+x.tobytes()+obs.tobytes()).hexdigest()
        audits.append({**row,'csv_member':member,'csv_sha256':digest.hexdigest(),'raw_rows':len(raw),'duplicate_rows':len(raw)-raw.t.nunique(),'grid_rows':len(t),'missing_timestamps':int((~obs).sum()),'all_selected_features_valid_rows':int(np.isfinite(x).all(axis=1).sum()),'prepared_array_sha256':array_hash,'columns':chosen,'start':int(t[0]),'end':int(t[-1])})
        mat.append({**row,'prepared_path':str(dest.relative_to(REPO)),'prepared_array_sha256':array_hash})
        print('prepared',row['trace'],len(t),flush=True)
    save(ROOT/'provenance/raw_audit.json',audits);save(ROOT/'configs/data_manifest.json',mat)
    event_rows=[]
    for _,e in gt.iterrows():
        why='outside_selected_apps_or_traces';stratum='excluded'
        if e.trace_name in names:
            why='eligible_positive_duration_known_application_effect';stratum='primary'
            if e.anomaly_type=='unknown':why='unknown_mechanism';stratum='secondary_unknown'
            elif e.anomaly_details=='no_application_impact':why='no_application_impact';stratum='negative_no_impact'
            elif e.anomaly_details=='application_crash':why='crash_descriptor';stratum='secondary_crash'
            elif e.anomaly_type not in primary_types:why='point_or_other_type';stratum='excluded'
            elif pd.isna(e.extended_effect_end):why='absent_EEI';stratum='secondary_no_EEI'
        elif e.trace_name=='10_2_1000000_67':why='crash_censoring_only';stratum='secondary_crash'
        event_rows.append({**{k:(None if pd.isna(v) else v) for k,v in e.to_dict().items()},'stratum':stratum,'selection_reason':why})
    save(ROOT/'configs/event_manifest.json',event_rows)
    save(ROOT/'configs/features.json',{'inputs':INPUTS,'outputs':FEATURES,'source':'Exathlon SPARK_BUNDLES[0] feature definitions, causal variant (bounded fill and retained1s grid)','source_commit':PIN})
    print('manifest',len(rows),'traces; selected strata',pd.Series([r['stratum'] for r in event_rows]).value_counts().to_dict())
if __name__=='__main__':main()
