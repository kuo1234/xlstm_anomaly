"""Prespecified E0 measurement contract. No detector/model code or fitting."""
import numpy as np


def phase_masks(timestamps, start, end, effect_end, context_seconds=300):
    t=np.asarray(timestamps,dtype=float)
    if not np.isfinite([start,end]).all() or end<start:
        raise ValueError('invalid RCI')
    has_effect=effect_end is not None and np.isfinite(effect_end)
    if has_effect and effect_end<end:
        raise ValueError('invalid EEI')
    r=(t>=start)&(t<=end)
    e=(t>end)&(t<=effect_end) if has_effect else np.zeros(len(t),dtype=bool)
    stop=effect_end if has_effect else end
    return r,e,(t>=start-context_seconds)&(t<start),(t>stop)&(t<=stop+context_seconds)


def normal_threshold(scores, calibration_labels, q=.995):
    s=np.asarray(scores,dtype=float);y=np.asarray(calibration_labels)
    if s.ndim!=1 or s.shape!=y.shape or not len(s) or not np.isfinite(s).all() or np.any(y!=0):
        raise ValueError('threshold requires finite, explicitly normal calibration scores')
    return float(np.quantile(s,q,method='linear'))


def _continuity(t,s,phase,valid,threshold,scale,cadence):
    ids=np.flatnonzero(phase&valid);alarms=ids[s[ids]>threshold]
    runs=[]
    for i in alarms:
        if runs and i==runs[-1][-1]+1 and np.isclose(t[i]-t[runs[-1][-1]],cadence):
            runs[-1].append(i)
        else:runs.append([i])
    adjacent=(np.diff(ids)==1)&np.isclose(np.diff(t[ids]),cadence) if len(ids)>1 else np.array([],bool)
    variation=float(np.median(np.abs(np.diff(s[ids]))[adjacent])/scale) if adjacent.any() else None
    return {'score_count':len(ids),'valid_score_fraction':len(ids)/int(phase.sum()) if phase.any() else None,
            'median':float(np.median(s[ids])) if len(ids) else None,
            'alarm_dropout_rate':float(np.mean(s[ids]<=threshold)) if len(ids) else None,
            'alarm_fragments':len(runs) if len(ids) else None,
            'longest_alarm_run_seconds':max((len(run)*cadence for run in runs),default=0) if len(ids) else None,
            'median_adjacent_absolute_score_change_scaled':variation}


def event_summary(timestamps,scores,available_at,start,end,effect_end,threshold,normal_iqr,
                  other_ranges=(),context_seconds=300,cadence=1):
    t=np.asarray(timestamps,dtype=float);s=np.asarray(scores,dtype=float);a=np.asarray(available_at,dtype=float)
    if t.ndim!=1 or t.shape!=s.shape or t.shape!=a.shape or not len(t) or np.any(np.diff(t)<=0) or not np.isfinite(t).all():
        raise ValueError('unique increasing timestamps and matching score/availability arrays required')
    if not np.isfinite(threshold) or not np.isfinite(normal_iqr) or normal_iqr<=0 or not np.isfinite(cadence) or cadence<=0:
        raise ValueError('normal-only threshold, positive fixed scale/cadence required')
    # The expected grid is anchored at epoch zero. Extra off-grid samples must
    # never compensate for missing native timestamps; use absolute tolerance
    # because a relative tolerance would accept fractions at Unix-time scale.
    if not np.isclose(t/cadence,np.rint(t/cadence),rtol=0,atol=1e-6).all():
        raise ValueError('timestamps must lie on the epoch-zero native cadence grid')
    r,e,pre,post=phase_masks(t,start,end,effect_end,context_seconds)
    original_r=r.copy();original_e=e.copy();overlap=np.zeros(len(t),bool)
    for lo,hi in other_ranges:overlap|=(t>=lo)&(t<=hi)
    r&=~overlap;e&=~overlap;pre&=~overlap;post&=~overlap
    valid=np.isfinite(s)&np.isfinite(a)&(a<=t)
    result={'point_rci':bool(start==end),'overlap_observed_rci_count':int((original_r&overlap).sum()),
            'overlap_observed_eei_count':int((original_e&overlap).sum()),
            'future_unavailable_score_count':int((np.isfinite(s)&np.isfinite(a)&(a>t)).sum())}
    for name,mask in [('rci',r),('eei',e),('pre_rci',pre),('recovery',post)]:
        result.update({name+'_'+k:v for k,v in _continuity(t,s,mask,valid,threshold,normal_iqr,cadence).items()})
    has_effect=effect_end is not None and np.isfinite(effect_end) and effect_end>end
    stop=effect_end if has_effect else end
    # Native-grid coverage includes timestamps absent from the score table.
    # Counting only observed rows would convert missing evidence into no alarm.
    grid=np.arange(np.ceil((start-context_seconds)/cadence)*cadence,
                   np.floor((stop+context_seconds)/cadence)*cadence+cadence/2,cadence)
    masks=phase_masks(grid,start,end,effect_end,context_seconds)
    grid_overlap=np.zeros(len(grid),bool)
    for lo,hi in other_ranges:grid_overlap|=(grid>=lo)&(grid<=hi)
    result['overlap_excluded_rci_count']=int((masks[0]&grid_overlap).sum())
    result['overlap_excluded_eei_count']=int((masks[1]&grid_overlap).sum())
    for name,mask in zip(['rci','eei','pre_rci','recovery'],masks):
        expected=int((mask&~grid_overlap).sum())
        result[name+'_expected_native_score_count']=expected
        result[name+'_valid_score_fraction']=result[name+'_score_count']/expected if expected else None
    enough_r=result['rci_score_count']>0;enough_e=result['eei_score_count']>0
    complete_r=enough_r and result['rci_score_count']==result['rci_expected_native_score_count']
    complete_e=enough_e and result['eei_score_count']==result['eei_expected_native_score_count']
    result['status']='MISSING_RCI_SCORE' if not enough_r else 'NO_EEI' if not has_effect else 'MISSING_EEI_SCORE' if not enough_e else 'MEASURED'
    if result['status']=='MEASURED' and not (complete_r and complete_e):result['status']='MEASURED_PARTIAL_PHASE_SUPPORT'
    root_alarm=bool(np.any(r&valid&(s>threshold)));effect_alarm=bool(np.any(e&valid&(s>threshold)))
    captured=True if root_alarm else False if complete_r else None
    effect_capture=True if effect_alarm else False if complete_e else None
    result['root_cause_capture']=captured
    result['effect_capture']=effect_capture
    result['effect_only_detection']=bool(not captured and effect_capture) if captured is not None and effect_capture is not None else None
    alarm=(r|e)&valid&(s>threshold)
    observed_delay=float(t[alarm][0]-start) if alarm.any() else None
    result['first_observed_alarm_delay_seconds']=observed_delay
    complete_event=complete_r and (not has_effect or complete_e) and not result['overlap_excluded_rci_count'] and not result['overlap_excluded_eei_count']
    result['detection_delay_seconds']=observed_delay if complete_event else None
    result['rci_vs_eei_scaled_median_gap']=(result['rci_median']-result['eei_median'])/normal_iqr if enough_r and enough_e else None
    result['rci_vs_pre_scaled_median_gap']=(result['rci_median']-result['pre_rci_median'])/normal_iqr if enough_r and result['pre_rci_score_count'] else None
    result['recovery_right_censored']=bool(t[-1]<stop+context_seconds)
    return result
