"""Prespecified verdict hierarchy and physical-group summaries."""
import argparse
import json
from pathlib import Path
import numpy as np
from common import load_config,write_json


def anomaly_harm(rows,mechanism,backbone):
    cfg=load_config();failures=[]
    for regime in ('A','B'):
        for kind in cfg['anomalies']['types']:
            for onset in cfg['anomalies']['onsets']:
                bad_groups=[]
                for group in cfg['groups']:
                    seeds=[]
                    for record in rows:
                        if record['job'][:3]!=[mechanism,group,backbone]:continue
                        row=next(r for r in record['rows'] if r['target_regime']==regime and r['type']==kind['name'] and r['onset']==onset)
                        delta=row['reset_minus_keep'];gate=cfg['gates']
                        seeds.append(delta['point_ap'] < -gate['anomaly_ap_drop_max'] or delta['event_recall'] < -gate['anomaly_event_recall_drop_max'] or delta['missed_point_rate'] > gate['anomaly_missed_rate_increase_max'])
                    if sum(seeds)>=cfg['gates']['model_seeds_required']:bad_groups.append(group)
                if len(bad_groups)>=cfg['gates']['support_groups_required']:failures.append({'target_regime':regime,'type':kind['name'],'onset':onset,'groups':bad_groups})
    return failures


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--results',type=Path,required=True);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args();cfg=load_config()
    def read(name):return json.loads((args.results/name).read_text())
    support=read('support_gate.json');groups=read('group_gates.json');records=read('mechanism.json');ad=read('anomalies.json');execution=read('execution.json');support_records=read('support.json')
    verdicts={};group_values={};study=[]
    for mechanism in cfg['mechanisms']:
        group_values[mechanism]={};details={}
        if not all(support[mechanism][b]['pass'] for b in cfg['backbones']):
            verdict='MODEL_SUPPORT_INSUFFICIENT'
        else:
            for b in cfg['backbones']:
                values=[]
                for g in cfg['groups']:
                    r=[x for x in records if x['job'][:3]==[mechanism,g,b]]
                    values.append({'group':g,'mean_history_harm':float(np.mean([x['mechanism']['history_harm_normalized'] for x in r])),'median_history_harm':float(np.median([x['mechanism']['history_harm_normalized'] for x in r])),'seed_harms':[x['mechanism']['history_harm_normalized'] for x in r],
                                   'mean_reset_recovery':float(np.mean([x['mechanism']['reset_recovery_normalized'] for x in r])),'long_context_benefit':{str(l):float(np.mean([x['mechanism']['long_context_benefit_normalized'][str(l)] for x in r])) for l in cfg['inference']['fixed_l']}})
                group_values[mechanism][b]=values
            x=groups[mechanism]['xlstm'];l=groups[mechanism]['lstm'];need=cfg['gates']['support_groups_required']
            harm_failures=anomaly_harm(ad,mechanism,'xlstm');details['anomaly_harm_conditions']=harm_failures
            x_signal=sum(g['mechanism_pre_ad'] for g in x)>=need
            x_all=sum(g['all_forecast_gates'] for g in x)>=need
            l_signal=sum(g['mechanism_pre_ad'] for g in l)>=need
            context=sum(g['context_suffices'] for g in x)>=need
            gap=[a['mean_history_harm']-b['mean_history_harm'] for a,b in zip(group_values[mechanism]['xlstm'],group_values[mechanism]['lstm'])]
            details['paired_xlstm_minus_lstm_group_harm']=gap
            if not x_signal:verdict='NO_STATE_STALENESS_SIGNAL'
            elif harm_failures:verdict='RESET_HARMS_ANOMALY_DETECTION'
            elif context:verdict='CONTEXT_TRUNCATION_SUFFICES'
            elif not x_all:verdict='STATE_STALENESS_INCONCLUSIVE_CONTEXT_CONTROL'
            elif l_signal and sum(abs(d)<cfg['gates']['xlstm_minus_lstm_harm_min_normalized'] for d in gap)>=need:verdict='ARCHITECTURE_NEUTRAL_STALENESS'
            elif sum(d>=cfg['gates']['xlstm_minus_lstm_harm_min_normalized'] for d in gap)>=need:verdict='XLSTM_SPECIFIC_SIGNAL'
            else:verdict='STATE_STALENESS_SUPPORTED'
        verdicts[mechanism]={'verdict':verdict,**details};study.append(verdict)
    priority=['RESET_HARMS_ANOMALY_DETECTION','XLSTM_SPECIFIC_SIGNAL','ARCHITECTURE_NEUTRAL_STALENESS','STATE_STALENESS_SUPPORTED','CONTEXT_TRUNCATION_SUFFICES','STATE_STALENESS_INCONCLUSIVE_CONTEXT_CONTROL','NO_STATE_STALENESS_SIGNAL','MODEL_SUPPORT_INSUFFICIENT']
    final=next(v for v in priority if v in study)
    summary={'final_gate':final,'per_mechanism':verdicts,'group_values':group_values,'support_gate':support,'scope':'controlled training-supported stationary synthetic processes only','interpretation':'protocol decision; no deployment/novelty claim','scientific_n':5,'groups_per_mechanism':5,'total_group_mechanism_units':15,'independent_cross_mechanism_n':False}
    write_json(args.results/'summary.json',summary)
    lines=['# M0-S results','',f'**Final gate: `{final}`. STOP for reviewer.**','',f"Protocol freeze: `{execution['freeze_commit']}`. {execution['training_runs']} training runs, {execution['support_runs']} support audits, {execution['mechanism_runs']} paired mechanism runs, {execution['anomaly_runs']} anomaly extensions. Anomaly stage: `{execution['anomaly_status']}`.",'',
           'Three mechanisms are reported independently. Scientific N=5 physical groups within each mechanism; model seeds and eight common-suffix realizations are paired replicates. Mechanisms reuse the same five group transforms and are not pooled as N=15 independent evidence. No iid p-values, model-seed bootstrap or winner selection.','',
           '| Mechanism | Final gate | xLSTM support groups | LSTM support groups |','|---|---|---|---|']
    for m in cfg['mechanisms']:lines.append(f"| {m} | `{verdicts[m]['verdict']}` | {support[m]['xlstm']['groups_passed']}/5 | {support[m]['lstm']['groups_passed']}/5 |")
    lines+=['','## B-support gate','', 'Each group requires >=2/3 seeds with B-compatible MSE <=0.98 times the best last-value/moving-mean baseline AND <=1.25 times independently B-trained linear AR. If either backbone fails >=4/5 group support, that mechanism stops before incompatible-history inference. This is a task-fit gate, not evidence that every regime/forecast setup is learnable.','',
            '| Mechanism | Group | Backbone | Seeds passing | Median ratio vs simple | Median ratio vs B-AR |','|---|---|---|---|---|---|']
    for m in cfg['mechanisms']:
        for g in cfg['groups']:
            for b in cfg['backbones']:
                r=[x for x in support_records if x['job'][:3]==[m,g,b]]
                lines.append(f"| {m} | {g} | {b} | {sum(x['b_support']['pass'] for x in r)}/3 | {np.median([x['b_support']['vs_best_simple_ratio'] for x in r]):.4f} | {np.median([x['b_support']['vs_b_ar_ratio'] for x in r]):.4f} |")
    for m in cfg['mechanisms']:
        lines+=['',f'## {m}: `{verdicts[m]["verdict"]}`','']
        if not group_values[m]:lines+=['Paired history experiment NOT_RUN_GATED: insufficient matched model support. Do not call any A→B state effect.'];continue
        lines+=['Primary offsets 32–63: all compared recent suffix observations already identical. Values below are physical-group averages over three fixed model seeds; gates require >=2 seeds jointly, not separate witnesses. Recovery is KEEP-minus-oracle-reset divided by compatible primary MSE.','',
                '| Group | Backbone | Mean H | Seed H range | Mean R | Long benefit L8 | Long benefit L32 | Pre-AD gate | Full forecast gate |','|---|---|---|---|---|---|---|---|---|']
        for b in cfg['backbones']:
            for row,gate in zip(group_values[m][b],groups[m][b]):
                harms=row['seed_harms'];lines.append(f"| {row['group']} | {b} | {row['mean_history_harm']:.6f} | [{min(harms):.6f}, {max(harms):.6f}] | {row['mean_reset_recovery']:.6f} | {row['long_context_benefit']['8']:.6f} | {row['long_context_benefit']['32']:.6f} | {gate['mechanism_pre_ad']} | {gate['all_forecast_gates']} |")
            values=[x['mean_history_harm'] for x in group_values[m][b]]
            lines.append(f"\n{b}: group median H={np.median(values):.6f}, range=[{min(values):.6f},{max(values):.6f}], signs={['+' if v>0 else '-' if v<0 else '0' for v in values]}.")
        rows=[r for r in records if r['job'][0]==m]
        lines+=['','Offset-bin summaries (mean of five group means; descriptive, never windows-as-N):','', '| Backbone | Offsets | H normalized | R normalized |','|---|---|---|---|']
        for b in cfg['backbones']:
            rb=[r for r in rows if r['job'][2]==b]
            for i,offsets in enumerate(cfg['inference']['reported_bins']):lines.append(f"| {b} | {offsets[0]}–{offsets[1]-1} | {np.mean([r['mechanism']['bins'][i]['history_harm_normalized'] for r in rb]):.6f} | {np.mean([r['mechanism']['bins'][i]['reset_recovery_normalized'] for r in rb]):.6f} |")
        lines+=['','Onset/peak/half-life/recovery/censoring are retained for every fixed run in `mechanism.json`. The unsmoothed replicate-mean curve is descriptive and can oscillate; duration is never used to select a gate or model.','']
        am=[x for x in ad if x['job'][0]==m]
        if not am:lines+=['AD extension NOT_RUN_GATED: fewer than four xLSTM groups pass the pre-AD mechanism gate. No AP, event recall, attenuation or reset-safety conclusion is claimed.']
        else:
            lines+=['AD extension ran in both A/B target regimes with the same event design and frozen calibration; all 18 conditions are retained in anomalies.json. Any predeclared condition with material AD harm in >=4 groups / >=2 seeds triggers the reset-harm gate.','', '| Backbone | Regime | Type | Onset | AP RESET−KEEP | Event recall RESET−KEEP | Missed points RESET−KEEP | Anomaly score ratio |','|---|---|---|---|---|---|---|---|']
            for b in cfg['backbones']:
                for reg in ['A','B']:
                    for typ in cfg['anomalies']['types']:
                        for onset in cfg['anomalies']['onsets']:
                            rr=[q['reset_minus_keep'] for x in am if x['job'][2]==b for q in x['rows'] if q['target_regime']==reg and q['type']==typ['name'] and q['onset']==onset]
                            lines.append(f"| {b} | {reg} | {typ['name']} | {onset} | {np.mean([r['point_ap'] for r in rr]):.4f} | {np.mean([r['event_recall'] for r in rr]):.4f} | {np.mean([r['missed_point_rate'] for r in rr]):.4f} | {np.mean([r['anomaly_score_ratio'] for r in rr]):.4f} |")
    lines+=['','## Limits and stop','', 'The result concerns these fixed Gaussian VAR mechanisms, model capacities, training budget, primary offsets and finite horizon. No effect outside that setup is excluded. Spliced history is a controlled counterfactual; independently sampled common suffixes are not asserted to be physically continuous transitions. Continuous stationary A/B controls diagnose long-carry artifacts.','',
            'All selected checkpoints were chosen using only stationary validation forecasting MSE. Scalers use balanced normal training samples, thresholds (if AD runs) use separate stationary calibration only, and test weights remain frozen. The first boundary score is immutable; RESET changes ingestion of the first suffix observation and forecasts from offset1 onward. No unscored warmup timestamps are erased from comparison.','',
            'No TSB-drift, real labels, detector/controller, retention coefficient, bank, RL or parameter TTA was run. An oracle reset is a diagnostic. A positive result is neither novelty evidence nor authorization for a deployable policy; a negative or model-support failure does not justify tuning after outcomes.','',
            'Stop here for external review. Protocol changes require a separately documented amendment before another run.']
    args.report.write_text('\n'.join(lines)+'\n')
    if records:
        import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
        fig,axes=plt.subplots(1,3,figsize=(14,4),sharex=True)
        for ax,m in zip(axes,cfg['mechanisms']):
            for b,color in [('xlstm','#2563eb'),('lstm','#d97706')]:
                r=[x for x in records if x['job'][0]==m and x['job'][2]==b]
                if not r:continue
                curves=[]
                for g in cfg['groups']:
                    curves.append(np.mean([x['mechanism']['suffix_trace']['history_harm_normalized'] for x in r if x['job'][1]==g],axis=0))
                curves=np.array(curves);ax.plot(np.arange(256),curves.mean(0),color=color,label=b)
                ax.fill_between(np.arange(256),curves.min(0),curves.max(0),color=color,alpha=.12)
            ax.axhline(.05,color='black',ls='--',lw=.8);ax.axvspan(32,63,color='#94a3b8',alpha=.15);ax.set_title(m);ax.set_xlabel('Suffix offset');ax.axhline(0,color='grey',lw=.7)
        axes[0].set_ylabel('Paired history harm / compatible MSE');axes[-1].legend();fig.suptitle('Physical-group mean and range; primary offsets shaded; no confidence interval');fig.tight_layout();fig.savefig(args.results/'history_harm.png',dpi=160);plt.close(fig)
    print(json.dumps({'final_gate':final,'per_mechanism':verdicts},indent=2))


if __name__=='__main__':main()
