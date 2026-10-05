"""Apply predeclared D0 rules after atlas. Conditional list, never model execution."""
from collections import Counter
import json
import pandas as pd
from atlas import ROOT,RESULT,RULES,csv,dump


def eligible(frame,category):
    r=RULES
    if category=='robust_streaming_win':return frame.portfolio_gap.ge(r['sentinel_robust_gap_margin'])&frame.cross_pair_stream_win_share.ge(r['sentinel_pairwise_win_share'])&frame.streaming_lomo_min_gap.ge(r['sentinel_leave_one_method_min_margin'])
    if category=='robust_online_win':return (-frame.portfolio_gap).ge(r['sentinel_robust_gap_margin'])&frame.cross_pair_online_win_share.ge(r['sentinel_pairwise_win_share'])&frame.online_lomo_min_margin.ge(r['sentinel_leave_one_method_min_margin'])
    if category=='near_tie':return frame.portfolio_gap.abs().le(r['sentinel_near_tie_absolute_gap_max'])
    if category=='high_dim':return frame.features.gt(r['sentinel_high_dim_min_exclusive'])
    if category=='sequence_candidate':return frame.avg_anomaly_len.ge(r['sentinel_sequence_average_length_min'])&frame.seq_anomaly.eq(1)
    raise ValueError(category)


def choose(frame):
    selected=[];used_files=set();used_groups=set();families=Counter();shortfalls={};candidate_counts={}
    for category in RULES['sentinel_selection_order']:
        candidates=frame[eligible(frame,category)].copy();candidate_counts[category]=len(candidates)
        count=0
        for _ in range(RULES['sentinel_slots'][category]):
            remaining=candidates[~candidates.file.isin(used_files)&~candidates.duplicate_group.isin(used_groups)].copy()
            if remaining.empty:break
            remaining['origin_rank']=remaining.origin.map({'MEASURED_FAMILY_DOCUMENTED':0,'UNKNOWN_SOURCE':1,'SIMULATED_SOURCE':2})
            remaining['selected_family_count']=remaining.family.map(families).fillna(0)
            if category=='robust_streaming_win':remaining['rank_value']=-remaining.portfolio_gap
            elif category=='robust_online_win':remaining['rank_value']=remaining.portfolio_gap
            elif category=='near_tie':remaining['rank_value']=remaining.portfolio_gap.abs()
            elif category=='high_dim':remaining['rank_value']=-remaining.features
            else:remaining['rank_value']=-remaining.avg_anomaly_len
            row=remaining.sort_values(['origin_rank','selected_family_count','rank_value','file'],kind='stable').iloc[0]
            fields=['file','family','origin','CD','type','features','ts_len','anomaly_ratio','num_anomaly','avg_anomaly_len','point_anomaly','seq_anomaly','portfolio_gap','cross_pair_stream_win_share','cross_pair_online_win_share','streaming_lomo_min_gap','online_lomo_min_margin','duplicate_group','native_provenance','historical_raw_audit','historical_training_anomaly_count']
            item={key:row[key] for key in fields};item['category']=category;item['status']='CONDITIONAL_D1_CANDIDATE_NOT_AUTHORIZED';selected.append(item)
            used_files.add(row.file);used_groups.add(row.duplicate_group);families[row.family]+=1;count+=1
        shortfalls[category]=RULES['sentinel_slots'][category]-count
    return selected,{'candidate_counts':candidate_counts,'shortfall':shortfalls,'selected_count':len(selected),'family_counts':dict(families),'family_target_met':len(families)>=RULES['sentinel_families_target'],'rules_relaxed':False,'D1_executed':False}


def main():
    status=json.loads((RESULT/'analysis_status.json').read_text());assert status['status']=='ATLAS_COMPUTED_BEFORE_SENTINELS'
    frame=pd.read_csv(RESULT/'series_atlas.csv');rows,status=choose(frame)
    assert len(rows)<=12 and len(set(r['file'] for r in rows))==len(rows) and len(set(r['duplicate_group'] for r in rows))==len(rows)
    csv('sentinels.csv',pd.DataFrame(rows));dump('sentinel_selection_status.json',status)
    print(json.dumps(status,indent=2));print([(r['category'],r['family'],r['file']) for r in rows])


if __name__=='__main__':main()
