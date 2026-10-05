"""Source-family descriptive atlas of released AUC-PR. No training/inference."""
import ast
import json
from pathlib import Path
import re
import sys
import numpy as np
import pandas as pd
from sources import ROOT,REPO,CACHE,PIN,sha,fetch

RESULT=ROOT/'results'
RULES=json.loads((ROOT/'provenance/analysis_rules.json').read_text())
ONLINE=RULES['online_portfolio'];STREAM=RULES['streaming_portfolio']


def dump(name,obj):
    def convert(v):
        if isinstance(v,dict):return {str(k):convert(x) for k,x in v.items()}
        if isinstance(v,(list,tuple)):return [convert(x) for x in v]
        if isinstance(v,np.generic):return convert(v.item())
        if isinstance(v,float) and not np.isfinite(v):return None
        return v
    (RESULT/name).write_text(json.dumps(convert(obj),indent=2,allow_nan=False)+'\n')


def csv(name,frame):frame.to_csv(RESULT/name,index=False,float_format='%.12g')


def literal(path,name):
    tree=ast.parse(Path(path).read_text())
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):return ast.literal_eval(node.value)
    raise ValueError(name)


def keyed(path,key='file'):
    frame=pd.read_csv(path)
    assert key in frame and not frame[key].isna().any() and frame[key].is_unique
    return frame.set_index(key).sort_index()


def summaries(frame,gap='portfolio_gap'):
    family=frame.groupby('family')[gap].mean()
    return {'series':len(frame),'families':frame.family.nunique(),'series_mean_gap':frame[gap].mean(),'series_median_gap':frame[gap].median(),'positive_series':int((frame[gap]>0).sum()),'negative_series':int((frame[gap]<0).sum()),'ties':int((frame[gap]==0).sum()),'equal_family_mean_gap':family.mean(),'family_median_gap':family.median(),'positive_families':family[family>0].index.tolist(),'negative_families':family[family<0].index.tolist()}


def masks(frame):
    return {'ALL_RELEASED':np.ones(len(frame),bool),'TSB_DRIFT':frame.CD.eq(1),'NON_DRIFT':frame.CD.eq(0),'MEASURED_SOURCE_ONLY':frame.origin.eq('MEASURED_FAMILY_DOCUMENTED'),'MEASURED_DRIFT':frame.origin.eq('MEASURED_FAMILY_DOCUMENTED')&frame.CD.eq(1),'SIMULATED_SOURCE':frame.origin.eq('SIMULATED_SOURCE'),'UNKNOWN_SOURCE':frame.origin.eq('UNKNOWN_SOURCE')}


def pareto(points,accuracy='auc_pr',speed='throughput'):
    result=[]
    for i,row in points.iterrows():
        others=points.drop(i)
        dominates=(others[accuracy]>=row[accuracy])&(others[speed]>=row[speed])&((others[accuracy]>row[accuracy])|(others[speed]>row[speed]))
        if not dominates.any():result.append(row['method'])
    return sorted(result)


def known_window(method,hps):
    point=['LOF','HBOS','KNN','MCD','OCSVM']
    if method in point:return 1,'driver_pointwise'
    if method in ['PCA','IForest']:return 100,'driver_fixed'
    if method in ['AutoEncoder','CBLOF','RobustPCA']:return None,'training_ACF_unknown_6_to_303'
    hp=hps.get(method,{})
    for key in hp:
        if 'win' in key.lower():return hp[key]+(1 if method in ['CNN','LSTMAD'] else 0),'candidate_TSB_pin_not_release_environment'
    return None,'unknown'


def main():
    RESULT.mkdir(exist_ok=True);fetch();src=CACHE/'StrAD';ref=CACHE/'references'
    online=keyed(src/'results/benchmark_eval_results/online/AUC-PR.csv')
    static=keyed(src/'results/benchmark_eval_results/static/AUC-PR.csv')
    streaming=keyed(src/'results/benchmark_eval_results/streaming/AUC-PR.csv')
    meta=keyed(src/'meta_features.csv','file_name');cd=keyed(src/'results/benchmark_eval_results/CD.csv')
    throughput=keyed(src/'results/benchmark_eval_results/time/mean_throughput.csv')
    variance=keyed(src/'results/benchmark_eval_results/time/std_inference.csv')
    for frame in [static,streaming,meta,cd,throughput,variance]:assert frame.index.equals(online.index)
    assert len(online)==180 and cd.CD.sum()==75
    for frame in [online,static,streaming]:assert frame.notna().all().all() and np.isfinite(frame.to_numpy()).all() and ((frame>=0)&(frame<=1)).all().all()
    assert (throughput>0).all().all() and np.isfinite(throughput).all().all()
    assert (variance>=0).all().all() and np.isfinite(variance).all().all()
    assert np.allclose(meta.anomaly_ratio,meta.anomaly_len/meta.ts_len,atol=1e-12)
    assert np.allclose(meta.avg_anomaly_len,meta.anomaly_len/meta.num_anomaly,atol=1e-10)
    frame=meta.join(cd,validate='one_to_one');frame.index.name='file'
    frame['family']=frame.index.to_series().str.split('_').str[1]
    frame['origin']=np.where(frame.family.isin(RULES['simulation_families']),'SIMULATED_SOURCE',np.where(frame.family.eq('CreditCard'),'UNKNOWN_SOURCE','MEASURED_FAMILY_DOCUMENTED'))
    frame['declared_train_cutoff']=frame.index.to_series().str.extract(r'_tr_(\d+)_1st_',expand=False).astype(int)
    frame['declared_first_anomaly']=frame.index.to_series().str.extract(r'_1st_(\d+)\.csv$',expand=False).astype(int)
    frame['train_ratio']=frame.declared_train_cutoff/frame.ts_len
    assert frame.declared_train_cutoff.between(1,frame.ts_len-1).all()
    frame['point_flag_stratum']=np.where(frame.point_anomaly.eq(1),'POINT_AND_SEQUENCE_FLAG','SEQUENCE_FLAG_ONLY')
    frame['online_portfolio']=online[ONLINE].mean(axis=1);frame['streaming_portfolio']=streaming[STREAM].mean(axis=1)
    frame['portfolio_gap']=frame.streaming_portfolio-frame.online_portfolio
    cross=np.stack([(streaming[s]-online[o]).to_numpy() for s in STREAM for o in ONLINE],axis=1)
    frame['cross_pair_stream_win_share']=(cross>0).mean(axis=1)
    frame['cross_pair_online_win_share']=(cross<0).mean(axis=1)
    frame['oracle_online']=online.max(axis=1);frame['oracle_streaming']=streaming.max(axis=1);frame['oracle_gap']=frame.oracle_streaming-frame.oracle_online
    # Tie winner names are preserved, not silently assigned to a favored method.
    frame['oracle_stream_winner']=streaming.apply(lambda r:'|'.join(r.index[r.eq(r.max())]),axis=1)
    frame['oracle_online_winner']=online.apply(lambda r:'|'.join(r.index[r.eq(r.max())]),axis=1)
    gap_variants=[]
    for o in ONLINE:gap_variants.append(streaming[STREAM].mean(axis=1)-online[[x for x in ONLINE if x!=o]].mean(axis=1))
    for s in STREAM:gap_variants.append(streaming[[x for x in STREAM if x!=s]].mean(axis=1)-online[ONLINE].mean(axis=1))
    gv=pd.concat(gap_variants,axis=1)
    frame['streaming_lomo_min_gap']=gv.min(axis=1);frame['online_lomo_min_margin']=-gv.max(axis=1)
    inventory=json.loads((REPO/'reports/phase_a_v4/candidate_inventory.json').read_text());historical={r['file']:r for r in inventory}
    groups=json.loads((REPO/'reports/phase_a/source_groups.json').read_text())['exact_feature_groups'];duplicate_map={name:'known_duplicate_'+str(i) for i,g in enumerate(groups) for name in g}
    frame['duplicate_group']=[duplicate_map.get(n,'unverified_unique_'+n) for n in frame.index]
    frame['historical_raw_audit']=frame.index.isin(historical)
    frame['native_provenance']=[historical.get(n,{}).get('provenance_status','unknown_uninspected') for n in frame.index]
    frame['historical_training_anomaly_count']=[historical.get(n,{}).get('training_anomaly_count',np.nan) for n in frame.index]
    frame['first_actual_anomaly_historical']=[historical.get(n,{}).get('first_actual_anomaly',np.nan) for n in frame.index]
    frame['historical_dimension_matches']=[historical[n]['D']==frame.loc[n,'features'] if n in historical else None for n in frame.index]
    frame['historical_length_matches']=[historical[n]['N']==frame.loc[n,'ts_len'] if n in historical else None for n in frame.index]
    types=['continuous','change_point','periodic','random_walk']
    for t in types:frame['tag_'+t]=frame['type'].fillna('').str.split().map(lambda tags:t in tags)
    bins={'dimensions':('features',RULES['dimension_bins']),'duration':('avg_anomaly_len',RULES['duration_bins']),'prevalence':('anomaly_ratio',RULES['prevalence_bins']),'events':('num_anomaly',RULES['event_count_bins']),'train_ratio':('train_ratio',RULES['train_ratio_bins']),'length':('ts_len',RULES['length_bins'])}
    for name,(column,edges) in bins.items():frame['bin_'+name]=pd.cut(frame[column],[-np.inf]+edges+[np.inf]).astype(str)
    csv('series_atlas.csv',frame.reset_index())
    dump('coverage.json',{'join_rows':len(frame),'families':frame.family.value_counts().to_dict(),'online_methods':list(online.columns),'streaming_methods':list(streaming.columns),'static_methods':list(static.columns),'static_only_methods':sorted(set(static)-set(online)),
                           'method_property_rows':len(pd.read_csv(src/'AD_multi.csv')),'CD_tag_counts':{t:int(frame['tag_'+t].sum()) for t in types},'point_sequence_combinations':frame.groupby(['point_anomaly','seq_anomaly']).size().to_dict(),
                           'metadata_identity_checks':True,'historical_dimensions_mismatched':frame[frame.historical_dimension_matches.eq(False)].index.tolist(),'historical_lengths_mismatched':frame[frame.historical_length_matches.eq(False)].index.tolist(),
                           'declared_first_vs_actual_mismatched':frame[frame.first_actual_anomaly_historical.notna()&frame.first_actual_anomaly_historical.ne(frame.declared_first_anomaly)].index.tolist(),
                           'known_duplicate_groups':groups,'raw_model_score_vectors_available':False})
    overall={};oracle={};composition=[]
    for name,mask in masks(frame).items():
        selected=frame.loc[mask];overall[name]=summaries(selected)
        overall[name]|={'equal_family_online':selected.groupby('family').online_portfolio.mean().mean(),'equal_family_streaming':selected.groupby('family').streaming_portfolio.mean().mean(),'series_online_mean':selected.online_portfolio.mean(),'series_streaming_mean':selected.streaming_portfolio.mean()}
        oracle[name]=summaries(selected,'oracle_gap')|{'label':'ORACLE_ENVELOPE','online_winners':selected.oracle_online_winner.value_counts().to_dict(),'streaming_winners':selected.oracle_stream_winner.value_counts().to_dict(),'stream_win_winner_concentration':selected[selected.oracle_gap>0].oracle_stream_winner.value_counts().to_dict()}
        for f,g in selected.groupby('family'):composition.append({'subset':name,'family':f,'n':len(g),'origin':g.origin.iloc[0],'online':g.online_portfolio.mean(),'streaming':g.streaming_portfolio.mean(),'portfolio_gap':g.portfolio_gap.mean(),'oracle_streaming_wins':int((g.oracle_gap>0).sum()),'portfolio_streaming_wins':int((g.portfolio_gap>0).sum()),'D_min':g.features.min(),'D_max':g.features.max(),'prevalence':g.anomaly_ratio.mean(),'avg_anomaly_length':g.avg_anomaly_len.mean()})
    dump('portfolio_summary.json',overall);dump('oracle_envelope.json',oracle);csv('family_summary.csv',pd.DataFrame(composition))
    strata=[]
    stratum_masks={'CD=1':frame.CD.eq(1),'CD=0':frame.CD.eq(0),'POINT_AND_SEQUENCE_FLAG':frame.point_anomaly.eq(1),'SEQUENCE_FLAG_ONLY':frame.point_anomaly.eq(0)}
    stratum_masks|={t:frame['tag_'+t] for t in types}
    for axis in bins:
        stratum_masks|={axis+':'+str(label):frame['bin_'+axis].eq(label) for label in frame['bin_'+axis].unique()}
    for label,mask in stratum_masks.items():
        g=frame.loc[mask]
        if len(g):strata.append({'stratum':label,**summaries(g),'origin_counts':g.origin.value_counts().to_dict(),'family_counts':g.family.value_counts().to_dict()})
    dump('strata.json',strata)
    family_conditioned=[]
    contrasts={'CD':frame.CD.eq(1),'highD>80':frame.features.gt(80),'point_flag':frame.point_anomaly.eq(1),'duration>100':frame.avg_anomaly_len.gt(100),'prevalence>0.05':frame.anomaly_ratio.gt(.05),'events>10':frame.num_anomaly.gt(10),'train_ratio>0.2':frame.train_ratio.gt(.2),'length>20000':frame.ts_len.gt(20000)}|{t:frame['tag_'+t] for t in types}
    for name,mask in contrasts.items():
        for family,g in frame.groupby('family'):
            yes=g.loc[mask.loc[g.index]];no=g.loc[~mask.loc[g.index]];eligible=min(len(yes),len(no))>=RULES['paired_family_stratum_min_series_each']
            family_conditioned.append({'contrast':name,'family':family,'n_yes':len(yes),'n_no':len(no),'supported':eligible,'effect_gap_yes_minus_no':yes.portfolio_gap.mean()-no.portfolio_gap.mean() if eligible else None})
    csv('family_conditioned_contrasts.csv',pd.DataFrame(family_conditioned))
    candidate_checks=[]
    for name in contrasts:
        valid=[r for r in family_conditioned if r['contrast']==name and r['supported']];values=[r['effect_gap_yes_minus_no'] for r in valid]
        material=[r['family'] for r in valid if r['effect_gap_yes_minus_no']>=RULES['candidate_feature_effect_margin']]
        negative=[r['family'] for r in valid if r['effect_gap_yes_minus_no']<=-RULES['candidate_feature_effect_margin']]
        loo=[float(np.mean([v for j,v in enumerate(values) if i!=j])) for i in range(len(values))] if len(values)>1 else []
        candidate_checks.append({'contrast':name,'supported_families':len(valid),'material_positive_families':material,'material_negative_families':negative,'mean_family_contrast':np.mean(values) if values else None,'leave_one_family_mean_range':[min(loo),max(loo)] if loo else None,'descriptive_replicated_positive':len(material)>=3 and bool(loo) and min(loo)>0,'causal_artifact_exclusion':'NOT_ESTABLISHED_without_raw_scores'})
    dump('candidate_pattern_checks.json',candidate_checks)
    lfo=[]
    for removed in [[]]+RULES['leave_family_out_sets']+[[f] for f in sorted(frame.family.unique())]:
        label='none' if not removed else '+'.join(removed)
        for subset,mask in masks(frame).items():
            g=frame.loc[mask&~frame.family.isin(removed)]
            if len(g):lfo.append({'removed':label,'subset':subset,**summaries(g),'oracle_series_mean_gap':g.oracle_gap.mean(),'oracle_streaming_wins':int((g.oracle_gap>0).sum())})
    csv('leave_family_out.csv',pd.DataFrame(lfo).drop_duplicates(['removed','subset']))
    feature_ranks=[]
    for feature in ['jsd','jsd_mean','CD_rate','features','avg_anomaly_len','num_anomaly','anomaly_ratio','ts_len','train_ratio']:
        for family,g in frame.groupby('family'):
            rho=g[feature].rank(method='average').corr(g.portfolio_gap.rank(method='average')) if len(g)>=3 and g[feature].nunique()>1 and g.portfolio_gap.nunique()>1 else None
            feature_ranks.append({'feature':feature,'family':family,'n':len(g),'spearman_descriptive':rho})
    csv('family_rank_associations.csv',pd.DataFrame(feature_ranks))
    properties=keyed(src/'AD_multi.csv','AD_name');method_stats=[];family_method=[]
    for mode,matrix in [('online',online),('streaming',streaming),('static',static)]:
        for method in matrix:
            for subset,mask in masks(frame).items():
                ids=frame.index[mask];values=matrix.loc[ids,method]
                if not len(ids):continue
                fm=values.groupby(frame.loc[ids,'family']).mean()
                props=properties.loc[method].to_dict() if method in properties.index else {'class':'UNKNOWN_STATIC_ONLY','type':'unknown','GPU':None,'streaming':None,'tuning':None}
                method_stats.append({'mode':mode,'method':method,'subset':subset,'n':len(ids),'series_mean_auc_pr':values.mean(),'family_mean_auc_pr':fm.mean(),'family_median_auc_pr':fm.median(),'released_zero_count':int(values.eq(0).sum()),**props})
                for f,v in fm.items():family_method.append({'mode':mode,'method':method,'subset':subset,'family':f,'auc_pr':v})
    csv('fixed_method_summary.csv',pd.DataFrame(method_stats));csv('family_method_accuracy.csv',pd.DataFrame(family_method))
    property_rows=[]
    method_frame=pd.DataFrame(method_stats)
    for (mode,subset),g in method_frame.groupby(['mode','subset']):
        for property_name in ['class','type','GPU','tuning']:
            for value,h in g.groupby(property_name,dropna=False):
                property_rows.append({'mode':mode,'subset':subset,'property':property_name,'value':str(value),'methods':len(h),'family_balanced_method_mean_auc_pr':h.family_mean_auc_pr.mean(),'members':'|'.join(sorted(h.method))})
    csv('method_property_summary.csv',pd.DataFrame(property_rows))
    pair_rows=[]
    for s in STREAM:
        for o in ONLINE:
            for subset,mask in masks(frame).items():
                selected=frame.loc[mask].copy();selected['pair_gap']=streaming.loc[selected.index,s]-online.loc[selected.index,o]
                if len(selected):pair_rows.append({'streaming':s,'online':o,'subset':subset,**summaries(selected,'pair_gap')})
    dump('fixed_method_pairs.json',pair_rows)
    # Oracle winner concentration is diagnostic, never primary selector accuracy.
    winner=[]
    for subset,mask in masks(frame).items():
        for f,g in frame.loc[mask].groupby('family'):
            winners=g[g.oracle_gap>0].oracle_stream_winner.value_counts()
            for name,n in winners.items():winner.append({'subset':subset,'family':f,'oracle_winning_method':name,'series_count':int(n),'label':'ORACLE_ENVELOPE'})
    csv('oracle_winner_concentration.csv',pd.DataFrame(winner))
    hps=literal(ref/'TSB_HP_list.py','Optimal_Multi_algo_HP_dict');warm=[];delta=[]
    shared=sorted(set(online)&set(static))
    unsupervised=literal(src/'exp/static_model_wrapper.py','Unsupervise_AD_Pool')
    for method in shared:
        w,status=known_window(method,hps)
        for file,row in frame.iterrows():
            warm.append({'file':file,'family':row.family,'method':method,'candidate_window':w,'window_status':status,'padded_prefix_points':w-1 if w else None,'warmup_fraction':(w-1)/row.ts_len if w else None,'first_declared_anomaly_in_warmup':row.declared_first_anomaly<w-1 if w else None,'first_actual_historical_in_warmup':row.first_actual_anomaly_historical<w-1 if w and np.isfinite(row.first_actual_anomaly_historical) else None,'online_minus_static':online.loc[file,method]-static.loc[file,method],'anomaly_ratio':row.anomaly_ratio,'series_length':row.ts_len,'fit_scope_comparable':method not in unsupervised})
        for subset,mask in masks(frame).items():
            ids=frame.index[mask];d=online.loc[ids,method]-static.loc[ids,method]
            if len(ids):delta.append({'method':method,'subset':subset,'n':len(ids),'online_minus_static_series_mean':d.mean(),'online_minus_static_family_mean':d.groupby(frame.loc[ids,'family']).mean().mean(),'online_wins':int((d>0).sum()),'static_wins':int((d<0).sum()),'ties':int((d==0).sum()),'candidate_window':w,'fit_scope_comparable':method not in unsupervised})
    csv('warmup_and_static_online.csv',pd.DataFrame(warm));csv('static_online_summary.csv',pd.DataFrame(delta))
    efficiency=[];fronts={}
    for subset,mask in masks(frame).items():
        ids=frame.index[mask]
        if not len(ids):continue
        points=[]
        for mode,matrix in [('online',online),('streaming',streaming)]:
            for method in matrix:
                acc=matrix.loc[ids,method].groupby(frame.loc[ids,'family']).mean().mean()
                speeds=throughput.loc[ids,method];fam_median=speeds.groupby(frame.loc[ids,'family']).median();fam_harm=speeds.groupby(frame.loc[ids,'family']).apply(lambda s:len(s)/np.sum(1/s))
                v=variance.loc[ids,method].groupby(frame.loc[ids,'family']).median().mean()
                points.append({'subset':subset,'method':method,'mode':mode,'auc_pr':acc,'throughput':fam_median.mean(),'series_arithmetic_throughput':speeds.mean(),'family_harmonic_throughput':fam_harm.mean(),'family_median_inference_std':v,'GPU_flag':int(properties.loc[method,'GPU']),'throughput_units':'published_inference_calls_per_second; LEAP emits32 scores only on chunk calls' if method=='LEAP' else 'published_throughput; per-point equivalence unverified'})
        point_frame=pd.DataFrame(points);pf=pareto(point_frame);harm_pf=pareto(point_frame,speed='family_harmonic_throughput');series_pf=pareto(point_frame,speed='series_arithmetic_throughput')
        fronts[subset]={'family_balanced_front':pf,'family_harmonic_front':harm_pf,'series_arithmetic_speed_front':series_pf}
        for r in points:r['family_front']=r['method'] in pf;r['harmonic_front']=r['method'] in harm_pf;r['series_speed_front']=r['method'] in series_pf
        efficiency+=points
    csv('efficiency.csv',pd.DataFrame(efficiency));dump('pareto_fronts.json',fronts)
    # Sentinel selection is intentionally a later separate command.
    dump('analysis_status.json',{'status':'ATLAS_COMPUTED_BEFORE_SENTINELS','source_commit':PIN,'no_models_run':True,'no_iid_significance':True,'source_keys_verified':True})
    print(json.dumps({'portfolio':overall,'oracle_summary':{k:{j:v for j,v in val.items() if j in ['series','positive_series','negative_series','series_median_gap']} for k,val in oracle.items()}},indent=2))


if __name__=='__main__':main()
