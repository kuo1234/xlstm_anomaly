"""Frozen lifecycle/control metrics, separated from detector training."""
import numpy as np

def summarize(t,s,start,end,effect_end,threshold,iqr,others=(),pre=300):
    t=np.asarray(t);s=np.asarray(s);assert len(t)==len(s) and np.all(np.diff(t)==1)
    overlap=np.zeros(len(t),bool)
    for lo,hi in others:overlap|=(t>=lo)&(t<=hi)
    stop=end if effect_end is None else effect_end
    masks={'rci':(t>=start)&(t<=end),'eei':(t>end)&(t<=stop),'pre':(t>=start-pre)&(t<start),'recovery':(t>stop)&(t<=stop+pre)}
    expected={'rci':int(end-start+1),'eei':0 if effect_end is None else int(effect_end-end),'pre':pre,'recovery':pre}
    row={};complete={};med={};runs={}
    for name,original in masks.items():
        mask=original&~overlap;valid=mask&np.isfinite(s);ids=np.flatnonzero(valid)
        # Include out-of-trace expected instants; remove only actual overlapping grid instants.
        n=expected[name]-int((original&overlap).sum());complete[name]=n>0 and int(valid.sum())==n
        med[name]=float(np.median(s[valid])) if valid.any() else None
        alarms=valid&(s>threshold);alarm_ids=np.flatnonzero(alarms)
        fragments=int(np.sum(np.r_[True,np.diff(alarm_ids)>1])) if len(alarm_ids) else 0
        splits=np.split(alarm_ids,np.flatnonzero(np.diff(alarm_ids)>1)+1) if len(alarm_ids) else []
        adjacent=np.diff(ids)==1
        continuity=float(np.median(np.abs(np.diff(s[ids]))[adjacent])/iqr) if adjacent.any() and iqr>0 else None
        row.update({name+'_count':int(valid.sum()),name+'_expected':n,name+'_coverage':int(valid.sum())/n if n>0 else None,name+'_median':med[name],name+'_alarm_time_fraction':float(np.mean(s[valid]>threshold)) if valid.any() else None,name+'_capture_observed':bool(alarms.any()) if valid.any() else None,name+'_alarm_fragments':fragments if valid.any() else None,name+'_longest_run':max(map(len,splits),default=0) if valid.any() else None,name+'_raw_continuity':continuity})
        if name in ['rci','eei']:row[name+'_overlap_excluded']=int((original&overlap).sum())
    rc=row['rci_capture_observed'];ec=row['eei_capture_observed']
    row['root_capture']=True if rc else False if complete['rci'] else None
    row['effect_only_alarm']=bool(not rc and ec) if complete['rci'] and ec is not None else None
    alarm=(masks['rci']|masks['eei'])&~overlap&np.isfinite(s)&(s>threshold)
    row['first_observed_alarm_delay']=int(t[alarm][0]-start) if alarm.any() else None
    row['detection_delay']=row['first_observed_alarm_delay'] if complete['rci'] and complete['eei'] and not(row['rci_overlap_excluded'] or row['eei_overlap_excluded']) else None
    row['recovery_right_censored']=bool(t[-1]<stop+pre)
    row['Z_RCI']=(med['rci']-med['pre'])/iqr if iqr>0 and med['rci'] is not None and med['pre'] is not None else None
    row['Z_EEI']=(med['eei']-med['pre'])/iqr if iqr>0 and med['eei'] is not None and med['pre'] is not None else None
    row['Delta_effect']=row['Z_EEI']-row['Z_RCI'] if row['Z_RCI'] is not None and row['Z_EEI'] is not None else None
    row['raw_eligible']=bool(iqr>0 and all(row[n+'_coverage'] is not None and row[n+'_coverage']>=.95 and row[n+'_count']>=k for n,k in [('rci',30),('eei',10),('pre',30)]))
    return row
