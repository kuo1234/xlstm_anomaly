"""Post-execution phase decomposition and prospectively specified controls/gates."""
import hashlib,json
import numpy as np
import pandas as pd
from prepare import ROOT,REPO,E0,sha,save
from metrics import summarize

def clean_records(frame):return json.loads(frame.to_json(orient='records'))
def median(values):
    a=[x for x in values if x is not None and np.isfinite(x)];return float(np.median(a)) if a else None

def main():
    p=json.loads((ROOT/'configs/protocol.json').read_text());events=json.loads((ROOT/'configs/event_manifest.json').read_text())
    manifest=json.loads((ROOT/'configs/data_manifest.json').read_text());art=json.loads((ROOT/'provenance/score_artifacts.json').read_text());thresholds=json.loads((ROOT/'results/thresholds.json').read_text())
    inventory=pd.read_csv(E0/'results/trace_context_inventory.csv');norm=inventory[inventory.trace_type.eq('undisturbed')]
    calnames={m['trace'] for m in manifest if m['role']=='calibration'}
    calmeta=inventory[inventory.trace.isin(calnames)]
    data={}
    for r in art:
        assert sha(REPO/r['path'])==r['sha256']
        d=pd.read_csv(REPO/r['path']);finite=np.isfinite(d.score)
        assert (d.available_at[finite]<=d.target_timestamp[finite]).all()
        assert d.target_observed[finite].all() and d.checkpoint_hash.eq(r['checkpoint_hash']).all()
        data[(r['baseline'],r['trace'])]=(d.target_timestamp.to_numpy(),d.score.to_numpy())
    rows=[];controls=[];normal_stats=[]
    for baseline in p['baselines']:
        threshold=next(x for x in thresholds if x['baseline']==baseline and x['app'] is None)
        thr=threshold['threshold'];iqr=threshold['IQR']
        for r in art:
            if r['baseline']!=baseline or r['role'] not in ['validation','calibration','normal_control']:continue
            t,s=data[(baseline,r['trace'])];finite=s[np.isfinite(s)];app=int(r['trace'].split('_')[0]);athr=next(x['threshold'] for x in thresholds if x['baseline']==baseline and x['app']==app)
            normal_stats.append({'baseline':baseline,'trace':r['trace'],'app':app,'role':r['role'],'scores':len(finite),'median':float(np.median(finite)),'IQR':float(np.quantile(finite,.75)-np.quantile(finite,.25)),'global_FPR':float(np.mean(finite>thr)),'app_threshold_FPR':float(np.mean(finite>athr))})
        for ev in events:
            name=ev['trace_name']
            if (baseline,name) not in data:continue
            t,s=data[(baseline,name)];start=int(ev['root_cause_start']);end=int(ev['root_cause_end']);effect=ev['extended_effect_end'];effect=None if effect is None else int(effect)
            others=[(int(e['root_cause_start']),int(e['combined_end'])) for e in events if e['trace_name']==name and e['event_id']!=ev['event_id']]
            row={**ev,'baseline':baseline,**summarize(t,s,start,end,effect,thr,iqr,others)}
            keys=['documented_corrected_input_rate','batch_interval','executors','max_executor_memory_gb']
            n=norm[norm.app.eq(ev['app'])];c=calmeta[calmeta.app.eq(ev['app'])]
            row['exact_normal_context_support']=bool(((n[keys]==pd.Series({k:ev[k] for k in keys})).all(axis=1)).any())
            row['input_rate_only_normal_support']=bool(n.documented_corrected_input_rate.eq(ev['documented_corrected_input_rate']).any())
            row['input_rate_only_calibration_support']=bool(c.documented_corrected_input_rate.eq(ev['documented_corrected_input_rate']).any())
            row['exact_context_unknown']=any(ev[k] is None for k in keys)
            athr=next(x['threshold'] for x in thresholds if x['baseline']==baseline and x['app']==ev['app'])
            secondary=summarize(t,s,start,end,effect,athr,iqr,others)
            row['app_threshold_effect_only_alarm']=secondary['effect_only_alarm'];row['app_threshold_root_alarm_time_fraction']=secondary['rci_alarm_time_fraction']
            rows.append(row)
            if ev['stratum']=='negative_no_impact':
                controls.append({'event_id':ev['event_id'],'baseline':baseline,'control_kind':'no_impact_post60_pseudo_effect','trace':name,'pseudo_phase':True,**summarize(t,s,start,end,end+60,thr,iqr,others)})
            if ev['stratum']!='primary':continue
            rlen=end-start+1;elen=effect-end
            # Fixed10 evenly spaced placements in heldout normal traces, with identical phase durations.
            for m in manifest:
                if m['role']!='normal_control':continue
                ct,cs=data[(baseline,m['trace'])];lo=int(ct[0])+300+32;hi=int(ct[-1])-rlen-elen+1
                if hi<lo:continue
                positions=np.unique(np.linspace(lo,hi,10,dtype=int))
                for pos in positions:
                    controls.append({'event_id':ev['event_id'],'baseline':baseline,'control_kind':'stationary_normal','trace':m['trace'],'pseudo_phase':True,'control_start':int(pos),**summarize(ct,cs,int(pos),int(pos+rlen-1),int(pos+rlen+elen-1),thr,iqr)})
            # Same-trace pre-control ends301s before event. Reject any annotated contamination.
            pos=start-300-rlen-elen
            cend=pos+rlen+elen-1
            if pos-300>=t[0] and not any(hi>=pos-300 and lo<=cend for lo,hi in others):
                controls.append({'event_id':ev['event_id'],'baseline':baseline,'control_kind':'pre_event','trace':name,'pseudo_phase':True,'control_start':pos,**summarize(t,s,pos,pos+rlen-1,cend,thr,iqr)})
    f=pd.DataFrame(rows);c=pd.DataFrame(controls);n=pd.DataFrame(normal_stats)
    save(ROOT/'results/event_metrics.json',clean_records(f));save(ROOT/'results/control_metrics.json',clean_records(c));save(ROOT/'results/normal_scores.json',clean_records(n))
    f.to_csv(ROOT/'results/event_metrics.csv',index=False);n.to_csv(ROOT/'results/normal_scores.csv',index=False)
    # Event->trace->family medians; type/app cells retain non-independent counts.
    aggregation=[];family=[]
    for b in p['baselines']:
        eligible=f[(f.baseline==b)&f.stratum.eq('primary')&f.raw_eligible]
        primary=f[(f.baseline==b)&f.stratum.eq('primary')]
        stationary=c[(c.baseline==b)&c.control_kind.eq('stationary_normal')&c.raw_eligible]
        event_controls=stationary.groupby('event_id').Delta_effect.median()
        ctrl_counts=stationary.groupby('event_id').size()
        paired=eligible.set_index('event_id').Delta_effect.subtract(event_controls).dropna()
        trace_delta=eligible.groupby('trace_name').Delta_effect.median()
        alarm_rows=eligible[eligible.effect_only_alarm.notna()]
        # Native score gaps can prevent alarm absence claims; keep explicit N/A.
        alarm_normal=stationary.groupby('event_id').effect_only_alarm.mean()
        alarm_excess=alarm_rows.set_index('event_id').effect_only_alarm.astype(float).subtract(alarm_normal).dropna()
        family.append({'baseline':b,'primary_events':len(primary),'eligible_events':len(eligible),'eligible_fraction':len(eligible)/len(primary),'eligible_types':eligible.anomaly_type.nunique(),'eligible_apps':eligible.app.nunique(),'trace_macro_Delta':median(trace_delta),'event_median_Delta':median(eligible.Delta_effect),'stationary_event_balanced_Delta':median(event_controls),'paired_normal_excess_Delta':median(paired),'events_with_5_normal_controls':int((ctrl_counts.reindex(eligible.event_id,fill_value=0)>=5).sum()),'complete_RCI_alarm_events':len(alarm_rows),'complete_RCI_alarm_fraction':len(alarm_rows)/len(eligible) if len(eligible) else 0,'effect_only_rate':median(alarm_rows.groupby('trace_name').effect_only_alarm.mean()),'effect_only_excess_vs_normal':median(alarm_excess),'pre_normal_offset_abs_IQR':median(abs(eligible.pre_median-n[(n.baseline==b)&n.role.eq('normal_control')]['median'].median())/next(t['IQR'] for t in thresholds if t['baseline']==b and t['app'] is None)), 'heldout_normal_FPR':float(n[(n.baseline==b)&n.role.eq('normal_control')].global_FPR.mean())})
        for key in ['anomaly_type','app']:
            for value,g in eligible.groupby(key):
                aggregation.append({'baseline':b,'group':key,'value':str(value),'events':len(g),'traces':g.trace_name.nunique(),'trace_macro_Delta':median(g.groupby('trace_name').Delta_effect.median()),'median_Z_RCI':median(g.Z_RCI),'median_Z_EEI':median(g.Z_EEI),'median_root_alarm_time_fraction':median(g.rci_alarm_time_fraction),'median_effect_alarm_time_fraction':median(g.eei_alarm_time_fraction)})
    save(ROOT/'results/aggregations.json',aggregation);save(ROOT/'results/family_summary.json',family)
    material=p['material'];resolution=any(x['eligible_fraction']<.5 or x['eligible_types']<2 or x['eligible_apps']<3 or x['events_with_5_normal_controls']<x['eligible_events']/2 for x in family)
    passed=[x['trace_macro_Delta'] is not None and x['trace_macro_Delta']>=1 for x in family]
    alarms=[x['effect_only_excess_vs_normal'] is not None and x['effect_only_excess_vs_normal']>=.1 for x in family]
    signs=all(g['trace_macro_Delta'] is not None and g['trace_macro_Delta']>0 for g in aggregation)
    if resolution:verdict='PHASE_RESOLUTION_INSUFFICIENT';reason='Insufficient prospective raw phase/type/app or duration-matched normal support.'
    elif not any(passed) and any(alarms):verdict='THRESHOLD_ARTIFACT_ONLY';reason='Threshold-only excess without either raw material family contrast.'
    elif not any(passed):verdict='NO_ROOT_EFFECT_GAP';reason='Neither family reaches the prespecified1-normal-IQR trace-macro effect increase.'
    elif sum(passed)==1:verdict='MODEL_SPECIFIC_ONLY';reason='Only one family reaches material raw phase contrast.'
    elif not signs:verdict='NO_ROOT_EFFECT_GAP';reason='Pooled raw phase increases do not repeat consistently across frozen type/app cells; no stable shared panel mechanism.'
    elif any(x['stationary_event_balanced_Delta'] is None or x['stationary_event_balanced_Delta']>=.5 or x['paired_normal_excess_Delta'] is None or x['paired_normal_excess_Delta']<1 for x in family):
        context=all(x['pre_normal_offset_abs_IQR'] is not None and x['pre_normal_offset_abs_IQR']>=2 for x in family)
        verdict='CONTEXT_SHIFT_DOMINANT' if context else 'NO_ROOT_EFFECT_GAP'
        reason='Normal ramp/excess-control corroboration fails'+(' with measured>=2IQR pre-normal baseline offsets in both families; descriptive unmatched-context confounding, no causal proof.' if context else '; no stable event-specific panel mechanism is established.')
    elif not all(alarms) or any(x['complete_RCI_alarm_fraction']<.5 for x in family):verdict='PHASE_RESOLUTION_INSUFFICIENT';reason='Raw contrast is material but strict complete-native RCI alarm support/excess cannot corroborate the positive lifecycle gate.'
    else:verdict='ROOT_CAUSE_EFFECT_GAP_SUPPORTED';reason='Both families pass frozen raw, alarm, type/app and heldout-normal controls; residual is phase-specific beyond native unionAD3.'
    save(ROOT/'results/final_gate.json',{'verdict':verdict,'reason':reason,'method_design_GO':False,'family_evidence':family,'all_type_app_directions_positive':signs,'native_LSTM_reproduction':False,'baseline_C_run':False,'detector_seeds':[21],'kill_route':verdict in ['NO_ROOT_EFFECT_GAP','MODEL_SPECIFIC_ONLY','PHASE_RESOLUTION_INSUFFICIENT','EXECUTION_SEAL_FAIL'],'inferential_scope':'descriptive bounded single-seed global19-feature panel; no universal absence/causal dominance/novelty proof','prior_art_residual':'RCI/EEI within-event standardized contrast, duration-matched normal burden and explicit available-at differ from native unionAD3; unvalidated novelty, method GO withheld'})
    print(json.dumps({'verdict':verdict,'reason':reason,'families':family},indent=2))
if __name__=='__main__':main()
