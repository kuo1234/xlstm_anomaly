"""Coverage/annotation/native timestamp audit; no detectors, scores or training."""
import csv
import hashlib
import io
import json
from pathlib import Path
import runpy
import zipfile
import numpy as np
import pandas as pd
from sources import ROOT,CACHE,RESULT,fetch,sha


def save(name,obj):
    (RESULT/name).write_text(json.dumps(obj,indent=2,allow_nan=False,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+'\n')


def frame(name,data):pd.DataFrame(data).to_csv(RESULT/name,index=False,float_format='%.12g')


def main():
    fetch();RESULT.mkdir(exist_ok=True)
    # This inspected module contains only declarative trace/feature metadata.
    # It reads features.json; no dataset, detector or training module is imported.
    meta=runpy.run_path(str(CACHE/'divad/exathlon/utils/spark/metadata.py'))
    trees={name:json.loads((ROOT/'provenance'/f'{name}_tree.json').read_text()) for name in ['exathlon','divad']}
    released=set(Path(r['path']).stem for r in trees['exathlon']['tree'] if r['type']=='blob' and r['path'].startswith('data/raw/app') and r['path'].endswith('.zip'))
    assert released==set(meta['TRACE_NAMES']) and len(released)==93
    contexts=[]
    for name in sorted(released):
        parts=name.split('_');renamed=meta['TRACE_TO_RENAMED'].get(name,name)
        executor_mapping=meta['TRACE_TO_N_RUNNING_EXECUTORS'][name]
        conflict=renamed!=name and renamed in meta['TRACE_TO_N_RUNNING_EXECUTORS'] and meta['TRACE_TO_N_RUNNING_EXECUTORS'][renamed]!=executor_mapping
        contexts.append(dict(trace=name,app=int(parts[0]),trace_type=meta['TRACE_TYPES'][int(parts[1])],
                             nominal_input_rate=int(parts[2]),documented_corrected_input_rate=int(renamed.split('_')[2]),
                             trace_id=int(parts[3]),batch_interval=meta['TRACE_TO_BATCH_INTERVAL'][name],
                             executors=None if conflict else executor_mapping,executors_published_raw_name_value=executor_mapping,executor_context_conflict=conflict,max_executor_memory_gb=meta['TRACE_TO_MAX_EXEC_MEMORY'][name]))
    traces=pd.DataFrame(contexts).set_index('trace');frame('trace_context_inventory.csv',traces.reset_index())
    gt=pd.read_csv(CACHE/'ground_truth.csv')
    assert len(gt)==109 and set(gt.trace_name)<=released and gt.root_cause_start.notna().all() and gt.root_cause_end.notna().all()
    assert gt.root_cause_end.ge(gt.root_cause_start).all()
    assert (gt.extended_effect_end.isna()|gt.extended_effect_end.ge(gt.root_cause_end)).all()
    assert not gt.duplicated().any()
    gt['event_id']=[f'gt_row_{i+1:03}' for i in range(len(gt))]
    gt['app']=gt.trace_name.map(traces.app);gt['rci_elapsed_seconds']=gt.root_cause_end-gt.root_cause_start
    gt['eei_elapsed_seconds']=gt.extended_effect_end-gt.root_cause_end
    gt['point_rci']=gt.rci_elapsed_seconds.eq(0)
    gt['missing_eei']=gt.extended_effect_end.isna()
    gt['combined_end']=gt.extended_effect_end.fillna(gt.root_cause_end)
    for column in ['documented_corrected_input_rate','batch_interval','executors','max_executor_memory_gb']:
        gt[column]=gt.trace_name.map(traces[column])
    overlap=[]
    for name,g in gt.groupby('trace_name'):
        for i,a in g.iterrows():
            for j,b in g.iterrows():
                if j<=i:continue
                lo=max(a.root_cause_start,b.root_cause_start);hi=min(a.combined_end,b.combined_end)
                if hi>=lo:overlap.append(dict(trace=name,event_a=a.event_id,event_b=b.event_id,type_a=a.anomaly_type,type_b=b.anomaly_type,overlap_start=lo,overlap_end=hi,elapsed_seconds=hi-lo,boundary_only=hi==lo))
    frame('event_overlap.csv',pd.DataFrame(overlap,columns=['trace','event_a','event_b','type_a','type_b','overlap_start','overlap_end','elapsed_seconds','boundary_only']))
    gt['combined_overlap']=gt.event_id.isin({v for r in overlap for v in [r['event_a'],r['event_b']]})
    frame('event_coverage.csv',gt)
    type_app=[]
    for (type_,app),g in gt.groupby(['anomaly_type','app']):
        context_cols=['documented_corrected_input_rate','batch_interval','executors','max_executor_memory_gb']
        type_app.append(dict(anomaly_type=type_,app=app,events=len(g),traces=g.trace_name.nunique(),rci_median_seconds=g.rci_elapsed_seconds.median(),rci_min_seconds=g.rci_elapsed_seconds.min(),rci_max_seconds=g.rci_elapsed_seconds.max(),eei_count=int(g.eei_elapsed_seconds.notna().sum()),eei_median_seconds=g.eei_elapsed_seconds.median() if g.eei_elapsed_seconds.notna().any() else None,point_rci_events=int(g.point_rci.sum()),context_count=len(g[context_cols].drop_duplicates()),small_event_stratum=len(g)<3))
    frame('type_app_context_coverage.csv',type_app)
    context_keys=['documented_corrected_input_rate','batch_interval','executors','max_executor_memory_gb']
    normal=traces[traces.trace_type.eq('undisturbed')];disturbed=traces[~traces.trace_type.eq('undisturbed')]
    normals=[]
    for app,g in traces.groupby('app'):
        n=normal[normal.app.eq(app)];d=disturbed[disturbed.app.eq(app)]
        support={tuple(row) for row in n[context_keys].itertuples(index=False,name=None)}
        supported=[name for name,row in d.iterrows() if tuple(row[context_keys]) in support]
        normals.append(dict(app=app,undisturbed_runs=len(n),disturbed_runs=len(d),documented_normal_contexts=len(support),documented_test_contexts=len(d[context_keys].drop_duplicates()),disturbed_traces_with_exact_normal_context=len(supported),disturbed_traces_with_unknown_context=int(d.executors.isna().sum()),disturbed_traces_with_matching_input_rate_only=int(d.documented_corrected_input_rate.isin(n.documented_corrected_input_rate).sum()),exact_supported_traces='|'.join(supported),native_train_test='undisturbed_to_train_disturbed_to_test; original all-app excludes7/8',current_run_split='NOT_RUN'))
    frame('normal_trace_support.csv',normals)
    raw=[];alignment=[];normal_features=[];phase_bins=[]
    for source in json.loads((ROOT/'provenance/raw_sample_sources.json').read_text()):
        if source['status']!='retrieved':continue
        path=CACHE/source['cache_path'];name=path.stem
        with zipfile.ZipFile(path) as archive:
            member=next(m for m in archive.namelist() if m.endswith('.csv'))
            csv_bytes=archive.getinfo(member).file_size
            digest=hashlib.sha256()
            with archive.open(member) as h:
                while chunk:=h.read(1024*1024):digest.update(chunk)
            with archive.open(member) as h:columns=next(csv.reader(io.TextIOWrapper(h)))
            selected=[c for c in columns if c=='t' or c=='node5_CPU001_Idle%' or c.endswith('StreamingMetrics_streaming_lastCompletedBatch_processingDelay_value') or c.endswith('StreamingMetrics_streaming_lastCompletedBatch_schedulingDelay_value')]
            with archive.open(member) as h:df=pd.read_csv(h,usecols=selected)
        raw_t=df.t.to_numpy();assert np.isfinite(raw_t).all()
        # Keep raw ordering/duplicate evidence. Unique sorted timestamps are used
        # only to count observed annotation support, never to create model inputs.
        t=np.unique(raw_t)
        raw.append(dict(trace=name,archive_sha256=source['sha256'],csv_sha256=digest.hexdigest(),csv_bytes=csv_bytes,rows=len(raw_t),unique_timestamps=len(t),duplicate_timestamp_rows=len(raw_t)-len(t),raw_nonincreasing_steps=int((np.diff(raw_t)<=0).sum()),features=len(columns)-1,start=float(t[0]),end=float(t[-1]),min_step=float(np.diff(t).min()),max_step=float(np.diff(t).max()),non_1s_steps=int((np.diff(t)!=1).sum()),inspected_feature_columns='|'.join(selected[1:]),all_features_finite_verified=False))
        for _,event in gt[gt.trace_name.eq(name)].iterrows():
            r=(t>=event.root_cause_start)&(t<=event.root_cause_end);e=(t>event.root_cause_end)&(t<=event.extended_effect_end) if pd.notna(event.extended_effect_end) else np.zeros(len(t),bool)
            alignment.append(dict(event_id=event.event_id,trace=name,anomaly_type=event.anomaly_type,rci_observations=int(r.sum()),eei_observations=int(e.sum()),rci_point=event.point_rci,missing_eei=event.missing_eei,combined_end_minus_trace_end=float(event.combined_end-t[-1]),recovery_300s_right_censored=t[-1]<event.combined_end+300))
            r_bins=set((t[r]//15).astype(int));e_bins=set((t[e]//15).astype(int))
            phase_bins.append(dict(event_id=event.event_id,trace=name,anomaly_type=event.anomaly_type,candidate_bin_seconds=15,native_rci_observations=int(r.sum()),rci_occupied_bins=len(r_bins),eei_occupied_bins=len(e_bins),mixed_rci_eei_bins=len(r_bins&e_bins),status='observed_native_timestamp_phase_counts; not benchmark-score reproduction'))
        if traces.loc[name,'trace_type']=='undisturbed':
            for col in selected[1:]:
                values=df[col];valid=values[np.isfinite(values)&values.ge(0)]
                normal_features.append(dict(trace=name,app=int(traces.loc[name,'app']),metric=col[col.index('StreamingMetrics_'):] if 'StreamingMetrics_' in col else col,values=len(values),finite_nonnegative_count=len(valid),minus_one_sentinel_count=int(values.eq(-1).sum()),median=valid.median(),q25=valid.quantile(.25),q75=valid.quantile(.75),context=traces.loc[name,'documented_corrected_input_rate']))
    frame('raw_sample_audit.csv',raw);frame('raw_event_timestamp_support.csv',alignment);frame('normal_raw_feature_variation.csv',normal_features);frame('phase_bin_support.csv',phase_bins)
    shared=[]
    for (type_,start),g in gt.groupby(['anomaly_type','root_cause_start']):
        if g.trace_name.nunique()>1:shared.append(dict(anomaly_type=type_,root_cause_start=start,events=len(g),apps=g.app.nunique(),traces='|'.join(sorted(g.trace_name)),status='shared_start_dependency_candidate; not independent batches'))
    frame('shared_start_candidates.csv',shared)
    summary=gt.groupby('anomaly_type').agg(events=('event_id','size'),traces=('trace_name','nunique'),apps=('app','nunique'),point_rci=('point_rci','sum'),missing_eei=('missing_eei','sum')).reset_index()
    frame('type_summary.csv',summary)
    # No released binary model artifact is interpreted as safe to deserialize.
    artifact_rows=[]
    for repo,tree in trees.items():
        blobs=[r for r in tree['tree'] if r['type']=='blob']
        potential=[r['path'] for r in blobs if Path(r['path']).suffix.lower() in ['.npy','.npz','.pkl','.h5','.hdf5','.keras','.pt','.pth','.ckpt','.csv']]
        notebooks=[]
        for row in blobs:
            if row['path'].endswith('.ipynb'):
                nb=json.loads((CACHE/repo/row['path']).read_text());notebooks.append({'path':row['path'],'code_cells':sum(c['cell_type']=='code' for c in nb['cells']),'cells_with_output':sum(bool(c.get('outputs')) for c in nb['cells'])})
        artifact_rows.append(dict(repo=repo,commit=tree['sha'],tree_entries=len(tree['tree']),truncated=tree.get('truncated',False),potential_score_model_or_csv_paths=potential,notebooks=notebooks,score_vectors_found=False))
    save('artifact_tree_inventory.json',artifact_rows)
    save('source_status.json',dict(events=len(gt),trace_files=len(traces),undisturbed_runs=len(normal),disturbed_runs=len(disturbed),point_rci_events=int(gt.point_rci.sum()),missing_eei_events=int(gt.missing_eei.sum()),overlap_pairs=len(overlap),strict_overlap_pairs=sum(not x['boundary_only'] for x in overlap),source_ground_truth_sha256=sha(CACHE/'ground_truth.csv'),raw_inspected_traces=len(raw),raw_inspected_events=len(alignment),metadata_only_traces=len(traces)-len(raw),all_native_features_verified=False,score_vectors_available=False,metadata_module_executed='DIVAD declarative Spark metadata only; no model import',context_support_is_documented_not_reverified=True,orphan_executor_metadata_keys=sorted(set(meta['TRACE_TO_N_RUNNING_EXECUTORS'])-released)))
    print(json.dumps(json.loads((RESULT/'source_status.json').read_text()),indent=2))


if __name__=='__main__':main()
