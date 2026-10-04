"""Post-evaluation descriptive reporting only. Consumes result CSVs; no raw labels, runner or retuning."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def table(df):
    def cell(v):
        if isinstance(v,(float,np.floating)):return 'N/A' if not np.isfinite(v) else f'{v:.4f}'
        return str(v)
    return '| '+' | '.join(df.columns)+' |\n| '+' | '.join(['---']*len(df.columns))+' |\n'+'\n'.join('| '+' | '.join(cell(v) for v in row)+' |' for row in df.itertuples(index=False,name=None))+'\n'


def main(base,verdict,rationale):
    base=Path(base);out=base/'results';run=base/'run'
    units=pd.read_csv(out/'metrics_units.csv');machine=pd.read_csv(out/'machine_results.csv');delta=pd.read_csv(out/'machine_deltas.csv')
    ck=pd.read_csv(out/'checkpoints_labelled.csv.gz');direction=pd.read_csv(out/'cv_direction.csv');passes=pd.read_csv(out/'checkpoint_pass_rates.csv')
    longs=pd.read_csv(out/'long_faults.csv');prom=pd.read_csv(out/'promotions.csv');physical=pd.read_csv(out/'physical_segments.csv')
    cfg=json.loads((run/'policy_config.json').read_text());seal=json.loads((run/'seal.json').read_text());logs=json.loads((out/'label_access_log.json').read_text())
    cv=machine[machine.policy=='DEph_cv'].copy();primary=direction[direction.scope=='primary_seed11_W1'].set_index('machine').reindex(cfg['machines']).reset_index()
    primary['scope']='primary_seed11_W1';primary['n_fault']=primary.n_fault.fillna(0).astype(int);primary['n_nonanomaly']=primary.n_nonanomaly.fillna(0).astype(int);primary['direction']=primary.direction.fillna('no checkpoints')
    primary.to_csv(out/'cv_direction_primary_complete.csv',index=False)
    dp=delta[delta.baseline=='C_threshold'];merged=cv.merge(dp[['machine','delta_AP','delta_VUS_PR']],on='machine')
    # Two plain scientific figures; no new-normal trade-off figure without its ground truth.
    fig,ax=plt.subplots(figsize=(8,4));ax.bar(dp.machine.str.replace('machine-',''),dp.delta_AP);ax.axhline(0,color='k',lw=.7)
    ax.set(xlabel='Machine (mean within machine over 3 seeds × 3 operators)',ylabel='DEph_cv − threshold AP');fig.tight_layout();fig.savefig(base/'fig_machine_delta_AP.png',dpi=130);plt.close(fig)
    H=ck[(ck.policy=='H_hold')&(ck.phi_seed==11)&(ck.op=='W1')]
    fig,ax=plt.subplots(figsize=(9,4));vals=[];pos=[];labels=[]
    for i,m in enumerate(cfg['machines']):
        g=H[H.machine==m]
        for j,c in enumerate(['fault','nonanomaly']):
            v=g.loc[g.cls==c,'cv'].to_numpy()
            if len(v): vals.append(v);pos.append(i*3+j);labels.append(m.replace('machine-','')+' '+('F' if j==0 else 'N'))
    if vals:ax.boxplot(vals,positions=pos,showfliers=False,tick_labels=labels)
    ax.axhline(.1,color='r',ls='--',label='Frozen cv = 0.10');ax.legend();ax.set(ylabel='CV, primary H_hold seed11 / W1',xlabel='F = source anomaly; N = nonanomaly (not certified settled regime)')
    ax.tick_params(axis='x',rotation=60);fig.tight_layout();fig.savefig(base/'fig_cv_distribution.png',dpi=130);plt.close(fig)
    # A full primary long-event table; no selection by favorable outcomes.
    L=longs[(longs.policy=='DEph_cv')&(longs.phi_seed==11)&(longs.op=='W1')]
    HP=longs[(longs.policy=='H_hold')&(longs.phi_seed==11)&(longs.op=='W1')]
    lt=L[['machine','episode','start','end','length','n_checkpoints','n_pass_cv','n_pass_conjunction','first_pass_time','was_promoted','fraction_fault_written']].copy()
    lt=lt.merge(HP[['machine','episode','n_checkpoints','n_pass_cv']],on=['machine','episode'],suffixes=('','_H_hold'))
    ps=physical[physical.scope=='primary_seed11_W1']
    dependence=H.groupby(['machine','op','cls'])['cv'].agg(['size','median','min','max']).reset_index()
    # Additional descriptive robustness, never a policy or feature change.
    HH=ck[ck.policy=='H_hold'].copy()
    HH['age_bin']=pd.cut(HH.age,[0,512,1024,2048,np.inf],labels=['256-512','513-1024','1025-2048','2049+'])
    HH.groupby(['machine','op','cls','age_bin'],observed=True).agg(n=('cv','size'),median_cv=('cv','median'),pass_cv=('pass_cv','mean'),pass_conjunction=('pass_conjunction','mean')).to_csv(out/'cv_age_operator_diagnostic.csv')
    sg=pd.read_csv(out/'quarantine_segments.csv');sg=sg[sg.policy=='H_hold'][['machine','phi_seed','op','start','duration']]
    ht=HH.merge(sg,on=['machine','phi_seed','op','start'],how='left');ht['duration_bin']=pd.cut(ht.duration,[0,512,1024,2048,np.inf],labels=['256-512','513-1024','1025-2048','2049+'])
    ht.groupby(['machine','op','cls','duration_bin'],observed=True).agg(n=('cv','size'),median_cv=('cv','median'),pass_cv=('pass_cv','mean')).to_csv(out/'cv_segment_length_diagnostic.csv')
    HH.groupby(['machine','op','cls']).agg(n=('cv','size'),median_cv=('cv','median'),pass_cv=('pass_cv','mean'),pass_conjunction=('pass_conjunction','mean')).to_csv(out/'cv_operator_diagnostic.csv')
    op=units[units.policy=='DEph_cv'].groupby('op')[['AP','VUS_PR','normal_FPR','point_recall','anomaly_written_frac','fault_promotions','majority_fault_promotions']].mean().reset_index()
    counts=prom.groupby(['policy']).agg(promotion_trajectory_events=('t','size'),any_fault=('any_fault','sum'),majority_fault=('majority_fault','sum')).reset_index()
    # Counts here are events on replicate trajectories, not independent sample sizes.
    lines=[f'# Step 2c — Frozen Stabilisation Transfer Test\n\n**{verdict} — pending review.**\n\n{rationale}\n',
    '## 1. Exposure, source and scope\n\n[Step 2c-A audit](STEP2C_DATA_AUDIT.md) and [frozen protocol](PROTOCOL.md) provide the evidence index and candidate decisions. All 28 SMD labels were historically parsed, including the nine selected here. None of these nine participated in Step 2a/2b feature/rule development. This is **frozen exploratory machine-transfer**, not strict confirmatory. Priority A was not established; HAI 22.04 Git LFS unavailable and SWaT original restricted acquisition are BLOCKED. No fallback sources. Strict confirmatory validation remains unavailable.\n',
    'Official [OmniAnomaly raw source](https://github.com/NetManAIOps/OmniAnomaly/tree/7fb0e0acf89ea49908896bcc9f9e80fcfff6baf4/ServerMachineDataset) pinned at `7fb0e0acf89ea49908896bcc9f9e80fcfff6baf4`. Raw observation hashes/shapes/constant channels/URLs: [dataset_manifest.json](run/dataset_manifest.json). Full train/test files, no crop, source row/channel order retained, timestamps absent. Binary labels identify anomalies, not equipment fault type or legitimate operating-mode transitions. Source normal train assumption is not independently train-label verified.\n',
    '## 2. Frozen policy and detector\n\n`DEph_cv = self <= 1.0 AND stat <= 0.5 AND cv <= 0.10`. Rule was generated post-hoc on Step 2b development data; **this transfer run has posthoc=false**, no test-driven changes. Seven candidate policies plus H_hold diagnostic; [policy_config.json](run/policy_config.json). Window8, dk128 random ReLU, seeds11/22/33; W1 kNN5, W2 f=.995, W3 beta=.1. Same38 dimensions, no representation adaptation. Train-only scaling/clipping; M0 first80% of train, tau q.99 on final20%. Calibration remains part of the source train used for scaler as in Step 2b; test statistics never fit scaler/tau. Block16 score-before-write; age256 checkpoints every128; trail256 only for DE/trailing PROMOTE. Fixed512 whole-buffer D_quarantine baseline unchanged. Executable segment DISCARD uses gap>2 (third clean block); earlier prose mismatch disclosed before labels. No tuning/rescue/classifier/RL, no point-adjust.\n',
    '## 3. Label access chronology and integrity\n\n'+f'- Protocol/code/audit commit: `{seal["git_commit"]}` (pushed before full run).\n- Seal SHA256: `{logs[0]["seal_sha256"]}`.\n- Seal commit: `{logs[0]["seal_commit"]}`; remote verified `{logs[0]["remote_commit"]}` before each access.\n- Seal UTC: `{seal["utc"]}`, labels_read=0, cv_max=.10, posthoc=false.\n- First label parsing attempt UTC: `{logs[0]["utc"]}`; last `{logs[-1]["utc"]}`; **{len(logs)}** vectors, one per machine.\n- Full code/config/trace hashes checked, then committed seal bytes and remote ancestry checked by the label loader. Logs are self-reported execution evidence, not an OS-wide proof of historic nonaccess.\n',
    '[seal.json](run/seal.json), [label_access_log.json](results/label_access_log.json), [environment.json](run/environment.json). Raw labels remain ignored. Label-free smoke: 24 traces/seed11/machine1-1; all 23 prelabel tests passed. Complete run: '+str(len(units))+' score trajectories, '+str(len(ck))+' evidence checkpoints, 9 machines × 3 seeds × 3 operators; seeds/operators/checkpoints are **not independent N**. Independent physical entity unit available is machine, N=9; cross-machine source dependencies unknown.\n',
    '## 4. Machine results and gain concentration (Q5)\n\nEach cell below averages the 9 seed/operator trajectories **within that machine**. Operator-specific and every candidate-policy table are retained separately.\n\n'+table(merged[['machine','AP','VUS_PR','normal_FPR','point_recall','anomaly_written_frac','delta_AP','delta_VUS_PR']]),
    'All primary comparisons (DEph_cv minus baseline):\n\n'+table(delta[['machine','baseline','delta_AP','delta_VUS_PR']]),
    'Operator robustness (descriptive trajectory means, not extra independent machines):\n\n'+table(op),
    f'Against threshold, positive machine ΔAP: {int((dp.delta_AP>0).sum())}/9; negative: {int((dp.delta_AP<0).sum())}/9. Macro machine ΔAP={dp.delta_AP.mean():.4f}; ΔVUS-PR={dp.delta_VUS_PR.mean():.4f}. Remove each machine in turn: ΔAP mean range [{min(dp.drop(i).delta_AP.mean() for i in dp.index):.4f}, {max(dp.drop(i).delta_AP.mean() for i in dp.index):.4f}]. Positive-gain machines and every negative machine remain listed; no success gate based on pooled mean.\n\n![Machine AP differences](fig_machine_delta_AP.png)\n',
    'A promotion-specific comparison with the predeclared H_hold diagnostic separates segment admission semantics from CV-enabled promotion: DEph_cv−H_hold AP is '+', '.join(m+': '+f'{v:.4f}' for m,v in (machine.pivot(index='machine',columns='policy',values='AP').DEph_cv-machine.pivot(index='machine',columns='policy',values='AP').H_hold).items())+'. Six machines have identical DEph_cv/H_hold scores and no DEph_cv promotion; their threshold comparison gains cannot be attributed to stabilisation promotion. This diagnostic does not introduce a new policy.\n',
    '## 5. CV direction (Q1)\n\nPrimary reference is H_hold seed11/W1: each physical persistent segment comes from sealed label-free boundaries. Fault checkpoint = trailing256 anomaly fraction>=.5, nonanomaly =0, mixed separate. **Nonanomaly is not certified benign/settled normal.**\n\n'+table(primary),
    'All-seed/operator robustness direction, with reversals explicit (not additional independent N):\n\n'+table(direction[direction.scope=='robustness_all'])+'\nReversed machines in this robustness summary: '+', '.join(direction[(direction.scope=='robustness_all')&(direction.direction=='REVERSED')].machine.tolist())+'. A machine with only one class cannot establish direction. Primary paired-class support: '+str(int(((primary.n_fault>0)&(primary.n_nonanomaly>0)).sum()))+'/9.\n',
    'Every primary physical reference segment (not checkpoint-independent evidence):\n\n'+table(ps[['machine','start','last_checkpoint','n_checkpoints','n_fault','n_nonanomaly','fault_cv_median','nonanomaly_cv_median','n_pass_cv_fault','n_pass_conjunction_fault']]),
    'All-seed/operator medians and first/trajectory identities: [cv_direction.csv](results/cv_direction.csv), [physical_segments.csv](results/physical_segments.csv). Boundaries can differ across operators/seeds; those rows are robustness, not new physical entities.\n\n![CV distribution](fig_cv_distribution.png)\n',
    '## 6. Frozen 0.10 pass rates and promotions (Q2)\n\nCV-only and full self/stat/CV conjunction rates below use primary H_hold checkpoints. Fault/nonanomaly/mixed strata retained; no threshold search.\n\n'+table(passes[passes.scope=='primary_seed11_W1'].drop(columns='scope')),
    'Actual promotion events summed over replicate trajectories, **not independent cases**. Any-fault means the promoted write contains >=1 labelled anomaly; majority-fault means >=50%. Nonanomaly promotion is not benign promotion. Full times/windows in [promotions.csv](results/promotions.csv).\n\n'+table(counts),
    '## 7. Long-fault repeated opportunities (Q3)\n\nLong fault = maximal source label1 episode >=256. The table lists **every** such episode for DEph_cv seed11/W1, including episodes with no checkpoint. H_hold counts show opportunities absent policy promotion/reset; actual DEph_cv checkpoint counts stop/reset when promoted. First pass time is exclusive source index t; `fraction_fault_written` includes both clean-threshold leakage and promoted fault points. Promotion touching any fault point is conservative. Full 3-seed/3-operator/all-policy table: [long_faults.csv](results/long_faults.csv).\n\n'+table(lt),
    '**Critical safety limitation:** zero fault promotion does not mean zero contamination or successful fault detection. DEph_cv macro point recall is '+f'{cv.point_recall.mean():.4f}'+', anomaly-written fraction '+f'{cv.anomaly_written_frac.mean():.4f}'+'. There are '+str(len(L))+' physical long label1 episodes across '+str(L.machine.nunique())+' machines; long-fault written fractions reach '+f'{longs[longs.policy=="DEph_cv"].fraction_fault_written.max():.4f}'+'. Some long faults remain below tau and have no checkpoint, including machine-3-2; CV cannot reject points that bypass quarantine. Thus only **checkpoint promotion rejection**, not general contamination prevention, transfers here.\n',
    '## 8. New-normal starvation (Q4)\n\n**NOT EVALUABLE ON THIS DATASET.** New-normal promotion not identifiable from source labels. SMD has no approved benign-regime transition, no ground-truth settling time, and no independently annotated post-shift interval. Thus benign promotion count, post-shift FPR, adaptation time, promotion delay relative to real benign onset and post-promotion adaptation benefit are N/A. Generic persistent nonanomaly FPR is retained under that name only in metrics_units.csv; it cannot rescue the hypothesis. The PF-versus-new-regime figure is omitted.\n',
    '## 9. Verdict and limitations\n\n'+f'**{verdict}**. {rationale}\n\n',
    'No numerical gate was invented. Sampling-rate dependence is **NOT EVALUABLE** because SMD source files have no timestamps and no verified point cadence. Descriptive checkpoint-age / operator dependence is retained in [cv_age_operator_diagnostic.csv](results/cv_age_operator_diagnostic.csv) and [cv_operator_diagnostic.csv](results/cv_operator_diagnostic.csv); the physical-segment table retains observed duration through the last checkpoint, not a supplied benign-regime duration. Final H_hold segment-duration dependence is in [cv_segment_length_diagnostic.csv](results/cv_segment_length_diagnostic.csv), reporting-only future endpoint information that is never a policy input. These diagnostics never change the frozen primary policy. This transfer does not establish semantic drift-vs-fault identifiability. Frozen .10 is evaluated as supplied; no revised threshold, checkpoint age, trailing window, representation, extra feature, oracle appendix or rescue. Historical label exposure prevents strict confirmation; repeated checkpoint windows are correlated; machine groups may share sources; one φ family / one detector setup, point-index cadence only. “Fault” in tables means source anomaly, not a verified causal equipment fault taxonomy. Effects cannot be extrapolated to HAI/SWaT; their secondary runs are BLOCKED.\n',
    'Quarantine segment durations/censoring and promotion delays: [quarantine_segments.csv](results/quarantine_segments.csv). Memory trajectory: [memory_occupancy.csv.gz](results/memory_occupancy.csv.gz): W1 initial+test entries, W2/W3 retained test provenance ledger and separately fixed matrix/normalizer storage; entry count does not measure effective memory rank. Runs retain original operator end-size semantics. Full raw units, machine summaries, operator summaries and labelled checkpoints are reviewable under results/.\n\n**Stop after Step 2c. Step3 / learned stopping / RL requires reviewer decision and is not executed. README status: pending review.**\n']
    (base/'STEP2C_TRANSFER.md').write_text('\n'.join(lines))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--base',required=True);a.add_argument('--verdict',required=True,choices=['TRANSFER_SUPPORTED','PARTIAL_TRANSFER','TRANSFER_NOT_SUPPORTED']);a.add_argument('--rationale',required=True)
    s=a.parse_args();main(s.base,s.verdict,s.rationale)
