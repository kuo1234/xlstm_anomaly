"""Evaluator-only quantities; no values returned to training or model selection."""
import numpy as np
from common import load_config


def average_precision(labels,scores):
    labels=np.asarray(labels).ravel(); scores=np.asarray(scores).ravel()
    if not labels.any():return None
    order=np.argsort(-scores,kind='stable'); y=labels[order]; s=scores[order]
    ends=np.r_[np.flatnonzero(np.diff(s)),len(s)-1]
    tp=np.cumsum(y)[ends]; precision=tp/(ends+1); recall=tp/y.sum()
    return float(np.sum(np.diff(np.r_[0.,recall])*precision))


def detection_metrics(labels,scores,threshold,events):
    alarms=scores>threshold; normal=labels==0; anomalous=~normal
    detected=[bool(alarms[e['replicate'],e['onset']:e['onset']+e['duration']].any()) for e in events]
    return {'point_average_precision':average_precision(labels,scores),
            'event_recall':float(np.mean(detected)),
            'normal_false_alarm_rate':float(alarms[normal].mean()),
            'normal_false_alarms_per_1000':float(1000*alarms[normal].mean()),
            'post_reset_missed_anomaly_point_rate':float((~alarms[anomalous]).mean()),
            'mean_anomaly_score':float(scores[anomalous].mean()),
            'threshold':float(threshold),'events':len(events),'anomaly_points':int(anomalous.sum()),'normal_points':int(normal.sum())}


def duration_summary(harm,denominator):
    cfg=load_config()['inference']; curve=np.mean(harm,axis=0)/denominator
    positive=np.maximum(curve,0); peak_index=int(np.argmax(positive)); peak=float(positive[peak_index])
    onset=next((i for i,v in enumerate(curve) if v>=load_config()['gates']['history_harm_min_normalized']),None)
    half=next((i for i in range(peak_index+1,len(curve)) if positive[i]<=peak/2),None) if peak>0 else None
    width=cfg['sustained_recovery_width']; epsilon=cfg['epsilon']
    recovery=next((i for i in range(peak_index+1,len(curve)-width+1) if np.max(np.abs(curve[i:i+width]))<=epsilon),None)
    return {'harm_onset_offset':onset,'peak_offset':peak_index,'peak_normalized':peak,
            'half_life_after_peak':None if half is None else half-peak_index,
            'time_to_within_epsilon':recovery,'recovery_censored':recovery is None,
            'epsilon':epsilon,'required_consecutive_points':width,
            'definition':'descriptive unsmoothed replicate-mean paired loss curve; no duration used for GO'}


def group_decision(seed_records):
    cfg=load_config(); gates=cfg['gates']; required=gates['model_seeds_required']; n=len(seed_records)
    def at_least(predicate):return sum(bool(predicate(r)) for r in seed_records)>=required
    support=at_least(lambda r:r['b_support']['pass'])
    harm=at_least(lambda r:r['mechanism']['history_harm_normalized']>=gates['history_harm_min_normalized'])
    recovered=at_least(lambda r:r['mechanism']['reset_recovery_fraction'] is not None and r['mechanism']['reset_recovery_fraction']>=gates['oracle_recovery_min_fraction'])
    stationary=at_least(lambda r:max(r['mechanism']['stationary_deterioration_normalized'].values())<=gates['stationary_deterioration_max_normalized'])
    long_context=all(at_least(lambda r:r['mechanism']['long_context_benefit_normalized'][str(l)]>=gates['long_context_benefit_min_normalized']) for l in cfg['inference']['fixed_l'])
    # A single predeclared L that matches reset recovery and compatible KEEP
    # prevents a claim that all short-context alternatives were ruled out.
    context_suffices=any(at_least(lambda r:r['mechanism']['replay_vs_reset_normalized'][str(l)]<=gates['long_context_benefit_min_normalized'] and r['mechanism']['long_context_benefit_normalized'][str(l)]<=gates['long_context_benefit_min_normalized']) for l in cfg['inference']['fixed_l'])
    def valid(r):
        q=r['mechanism']
        return r['b_support']['pass'] and q['history_harm_normalized']>=gates['history_harm_min_normalized'] and q['reset_recovery_fraction'] is not None and q['reset_recovery_fraction']>=gates['oracle_recovery_min_fraction'] and max(q['stationary_deterioration_normalized'].values())<=gates['stationary_deterioration_max_normalized']
    joint=at_least(valid)
    joint_long=at_least(lambda r:valid(r) and all(r['mechanism']['long_context_benefit_normalized'][str(l)]>=gates['long_context_benefit_min_normalized'] for l in cfg['inference']['fixed_l']))
    return {'seed_count':n,'support':support,'harm':harm,'oracle_recovery':recovered,'stationary_control':stationary,
            'long_context_benefit':long_context,'context_suffices':context_suffices,
            'mechanism_pre_ad':joint,
            'all_forecast_gates':joint_long}
