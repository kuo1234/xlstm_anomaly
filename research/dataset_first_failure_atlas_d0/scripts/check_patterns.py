"""Predeclared family/method anti-confound checks, no model or selector fit."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from atlas import ROOT,RESULT,RULES,ONLINE,STREAM,keyed,summaries,csv,dump
from sources import CACHE


def main():
    frame=pd.read_csv(RESULT/'series_atlas.csv').set_index('file')
    src=CACHE/'StrAD';online=keyed(src/'results/benchmark_eval_results/online/AUC-PR.csv');stream=keyed(src/'results/benchmark_eval_results/streaming/AUC-PR.csv')
    contrasts={'change_point':frame.tag_change_point,'duration>100':frame.avg_anomaly_len.gt(100),'prevalence>0.05':frame.anomaly_ratio.gt(.05),'CD':frame.CD.eq(1)}
    rows=[]
    for removed in ['none']+['Online:'+m for m in ONLINE]+['Streaming:'+m for m in STREAM]:
        oo=[m for m in ONLINE if removed!='Online:'+m];ss=[m for m in STREAM if removed!='Streaming:'+m]
        gap=stream[ss].mean(axis=1)-online[oo].mean(axis=1)
        for name,mask in contrasts.items():
            for f,g in frame.groupby('family'):
                yes=g.index[mask.loc[g.index]];no=g.index[~mask.loc[g.index]]
                if min(len(yes),len(no))>=2:rows.append({'removed':removed,'contrast':name,'family':f,'n_yes':len(yes),'n_no':len(no),'effect':gap.loc[yes].mean()-gap.loc[no].mean()})
    csv('leave_method_feature_contrasts.csv',pd.DataFrame(rows))
    within=[]
    for tag in ['continuous','change_point','periodic','random_walk']:
        for f,g in frame[frame.CD.eq(1)].groupby('family'):
            yes=g[g['tag_'+tag]];no=g[~g['tag_'+tag]]
            if min(len(yes),len(no))>=2:within.append({'tag':tag,'family':f,'n_tag':len(yes),'n_other_drift':len(no),'gap_tag_minus_other_drift':yes.portfolio_gap.mean()-no.portfolio_gap.mean()})
    csv('within_drift_family_tag_contrasts.csv',pd.DataFrame(within,columns=['tag','family','n_tag','n_other_drift','gap_tag_minus_other_drift']))
    matched=[]
    for (f,prevalence),g in frame.groupby(['family','bin_prevalence']):
        for name,mask in [('change_point',g.tag_change_point),('duration>100',g.avg_anomaly_len.gt(100))]:
            yes=g[mask];no=g[~mask]
            if min(len(yes),len(no))>=2:matched.append({'contrast':name,'family':f,'prevalence_bin':prevalence,'n_yes':len(yes),'n_no':len(no),'effect':yes.portfolio_gap.mean()-no.portfolio_gap.mean()})
    csv('family_prevalence_matched_contrasts.csv',pd.DataFrame(matched,columns=['contrast','family','prevalence_bin','n_yes','n_no','effect']))
    fixed_pairs=[]
    for o in ONLINE:
        for s in STREAM:
            gap=stream[s]-online[o]
            for name,mask in contrasts.items():
                for f,g in frame.groupby('family'):
                    yes=g.index[mask.loc[g.index]];no=g.index[~mask.loc[g.index]]
                    if min(len(yes),len(no))>=2:fixed_pairs.append({'online':o,'streaming':s,'contrast':name,'family':f,'effect':gap.loc[yes].mean()-gap.loc[no].mean()})
    csv('fixed_pair_feature_contrasts.csv',pd.DataFrame(fixed_pairs))
    robustness={}
    for name in contrasts:
        rr=pd.DataFrame(rows);piece=rr[rr.contrast.eq(name)];summ=[]
        for removal,g in piece.groupby('removed'):
            effects=g.effect
            summ.append({'removed':removal,'families':len(g),'mean_family_effect':effects.mean(),'material_positive_families':g.loc[g.effect.ge(.02),'family'].tolist(),'material_negative_families':g.loc[g.effect.le(-.02),'family'].tolist()})
        robustness[name]=summ
    # Rank correlation at family level is descriptive; no p-values.
    correlations=[]
    for feature in ['anomaly_ratio','avg_anomaly_len','num_anomaly','features']:
        for maskname,mask in [('ALL',frame.index==frame.index),('CD',frame.CD.eq(1))]:
            g=frame.loc[mask]
            fam=g.groupby('family')[[feature,'portfolio_gap']].mean()
            correlations.append({'feature':feature,'subset':maskname,'family_count':len(fam),'family_spearman':fam[feature].rank().corr(fam.portfolio_gap.rank())})
    dump('method_robustness.json',robustness);dump('family_feature_associations.json',correlations)
    # Known duplicate group collapse sensitivity: average metrics within each known
    # group, then each family, without treating unknown mappings as verified unique.
    duplicate=frame.groupby(['family','duplicate_group']).portfolio_gap.mean().groupby('family').mean()
    dump('known_duplicate_sensitivity.json',{'before_equal_family_gap':frame.groupby('family').portfolio_gap.mean().mean(),'after_known_group_equal_family_gap':duplicate.mean(),'known_duplicate_collapse_only':True,'unknown_duplicates_not_resolved':True})
    print(json.dumps(robustness,indent=2))


if __name__=='__main__':main()
