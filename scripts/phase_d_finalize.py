"""Verify every paired arm, statistical decision and full negative results."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import torch
from phase_d_operator import ROOT,REPORT,DATA,OFFICIAL,NOTE,tensor_hash
from phase_d_backbone import SEEDS
from phase_d_buffers import SCENARIOS,TYPES,CS
from phase_d_statistics import paired_summary,holm
from phase_c_run import digest
from m0.metrics import metrics


def main():
    assert not (REPORT/'execution_stop.json').exists(), 'Quarantined incomplete grid cannot support H1 statistics'
    rows=[]
    paths=sorted((REPORT/'rows').glob('*.json'))
    assert len(paths)==800
    for p in paths:
        records=json.loads(p.read_text())['rows']; assert len(records)==6
        assert [r['c'] for r in records]==[None,*CS]
        assert len({r['pre_model_sha256'] for r in records})==1
        assert len({r['pre_optimizer_sha256'] for r in records})==1
        assert len({r['pre_rng_sha256'] for r in records})==1
        assert len({r['fixed_threshold'] for r in records})==1
        for r in records:
            assert digest(ROOT/r['score_path'])==r['score_sha256']
            assert r['optimizer_steps']==(0 if r['c'] is None else 1)
            assert r['anomalous_loss_exposures']==(r['c'] or 0)
            assert r['loss_exposures']==(0 if r['c'] is None else 100)
            assert np.isfinite(list(r['score_summary']['quantiles'])).all()
            if r['c'] is None:
                assert r['parameter_delta_l2']==0 and r['final_model_sha256']==r['pre_model_sha256']
            rows.append(r)
    keys={(r['source'],r['scenario'],r['condition'],r['detector_seed'],r['c']):r for r in rows}
    assert len(keys)==4800
    comparisons=[]
    for kind in TYPES:
        for c in CS[1:]:
            delta=np.array([[[keys[(s,scenario,kind,seed,0)]['metrics']['ap']-
                keys[(s,scenario,kind,seed,c)]['metrics']['ap'] for scenario in SCENARIOS] for seed in SEEDS] for s in range(3000,3010)])
            summary=paired_summary(delta)
            comparisons.append(dict(condition=kind,c=c,**summary))
    adjusted=holm([r['p_two_sided'] for r in comparisons]+[1.]*6)
    for r,p in zip(comparisons,adjusted):
        r['holm_p']=p
        r['qualifies']=bool(r['c']<=20 and r['mean']>=.02 and r['ci95'][0]>0 and p<.05 and
            r['positive_detector_seeds']>=4 and r['positive_scenarios']>=3)
    qualifying=[r for r in comparisons if r['qualifies']]
    status='GO' if qualifying else 'INCONCLUSIVE' if any(r['c']<=20 and r['ci95'][0]<=.02<=r['ci95'][1] for r in comparisons) else 'STOP'
    costs=json.loads((REPORT/'compute_preflight.json').read_text())
    summary=dict(D0='PASS',H1_harm=status,qualifying=qualifying,comparisons=comparisons,
        natural_SMD_comparisons=[dict(status='NOT_AUTHORIZED',p=1.) for _ in range(6)],
        family_size=22,statistical_unit='10 source clusters ×5 paired detector seeds;4 scenarios retained jointly',
        bootstrap_draws=10000,bootstrap_seed=901,sign_flip='Exact two-sided2^10 source-cluster signs',
        grid_rows=len(rows),curve_pairs=len(paths),all_negative_null_results_reported=True,
        measured_pair_total_seconds=sum(json.loads(p.read_text())['total_seconds'] for p in paths),
        measured_arm_seconds=sum(r['runtime_seconds'] for r in rows),
        peak_gpu_allocated_bytes=max(r['peak_gpu_allocated_bytes'] for r in rows),
        peak_gpu_reserved_bytes=max(r['peak_gpu_reserved_bytes'] for r in rows),compute_preflight=costs,
        no_later_phase=True,H1_admission='GO separately established; no new inference here')
    (REPORT/'statistical_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    flat=[]
    for r in rows:
        row={k:r[k] for k in ('source','scenario','condition','detector_seed','c','parameter_delta_l2','fixed_threshold',
            'anomalous_loss_exposures','optimizer_steps','runtime_seconds','score_sha256','final_model_sha256')}
        row.update(r['metrics']); row['update_loss']=r['update_losses'][0] if r['update_losses'] else None
        flat.append(row)
    with (REPORT/'all_results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(flat[0]),lineterminator='\n');w.writeheader();w.writerows(flat)
    curves=[]
    for kind in TYPES:
        for c in [None,*CS]:
            selected=[r for r in rows if r['condition']==kind and r['c']==c]
            curves.append(dict(condition=kind,c=c,mean_ap=float(np.mean([r['metrics']['ap'] for r in selected])),
                mean_auroc=float(np.mean([r['metrics']['auroc'] for r in selected])),
                mean_fpr=float(np.mean([r['metrics']['fpr'] for r in selected])),
                mean_recall=float(np.mean([r['metrics']['recall'] for r in selected]))))
    (REPORT/'curves.json').write_text(json.dumps(curves,indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for kind in TYPES:
        points=[r for r in curves if r['condition']==kind and r['c'] is not None]
        axes[0].plot(CS,[r['mean_ap'] for r in points],marker='o',label=kind)
        effects=[0]+[r['mean'] for r in comparisons if r['condition']==kind]
        axes[1].plot(CS,effects,marker='o',label=kind)
    axes[0].set_ylabel('Macro AP'); axes[1].set_ylabel('AP(clean) - AP(contaminated)')
    axes[1].axhline(.02,color='black',linestyle='--',label='Practical margin .02')
    for ax in axes: ax.set_xlabel('Contaminated windows /100'); ax.legend(fontsize=8); ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(REPORT/'contamination_curves.png',dpi=160);plt.close(fig)
    lines=['# Phase D controlled H1 decision','',f'D0 **PASS**. H1-harm **{status}** for this frozen single-update intervention.',
        '',f'Qualifying comparisons: {len(qualifying)}. All16 positive-c comparisons follow below; c30 cannot qualify.',
        '', '| Type | c% | AP clean−contaminated |95% CI| Holm p |Positive seeds/scenarios|Qualifies|',
        '|---|---:|---:|---|---:|---|---|']
    for r in comparisons:
        lines.append(f'| {r["condition"]} | {r["c"]} | {r["mean"]:.6f} | [{r["ci95"][0]:.6f}, {r["ci95"][1]:.6f}] | {r["holm_p"]:.6f} | {r["positive_detector_seeds"]}/5; {r["positive_scenarios"]}/4 | {r["qualifies"]} |')
    lines += ['', '## Interpretation and boundaries','',
        'H1-admission remains independently established. Harm here means an AP drop after one contaminated pinned SANA update relative to an identically initialized clean update; no-update is separately reported. Negative effects mean contaminated AP exceeded clean AP, not evidence of universal safety. No later phase is automatically authorized.',
        '', 'The controlled buffer is a window-level intervention, not necessarily one globally consistent corrupted raw stream: selectively replacing overlapping windows can leave shared raw timestamps normal in unselected rows. The pairing unit is the ordered100-window buffer, and inference clusters whole source realizations. Event-onset windows do not isolate long-duration effects. Severity/duration composition is paired within each c comparison, not a separate causal duration study.',
        '', 'Synthetic backbone is newly trained D8 official MLP family, not an SMD checkpoint transplant or xLSTM reproduction. Only train/validation source prefixes select checkpoints; all five states were committed/pushed before harm. Full oracle composition metadata, state/RNG hashes, denominator checks, and all4800 rows are retained. No natural-SMD harm, H4, xLSTM/LSTM, probes or H3b ran.',
        '', '## Operational notes','',
        'Initial dry preflight failed closed because the combined backbone manifest was not yet committed; no arm executed. The manifest was then committed/pushed and dry-run retried. No methodological selection rule changed. Seed11 training timed alone; four remaining backbone trainings ran concurrently in fresh processes. Per-process allocator maxima are not aggregate device memory.',
        '', f'Measured pair-generation/update/evaluation total: {summary["measured_pair_total_seconds"]:.3f}s; arm runtime sum: {summary["measured_arm_seconds"]:.3f}s. GPU allocated/reserved peak: {summary["peak_gpu_allocated_bytes"]/2**30:.3f}/{summary["peak_gpu_reserved_bytes"]/2**30:.3f}GiB. See logs for process walls and compute_preflight.json for prospective extrapolation.',
        '', '![Full contamination curves](contamination_curves.png)','']
    (REPORT/'decision.md').write_text('\n'.join(lines))
    (REPORT/'README.md').write_text('# Phase D\n\nSee [decision](decision.md), [prospective freeze](prospective.md), '
        '[operator parity](operator_parity.json), [backbone manifest](synthetic_backbone_manifest.json), '
        '[buffer manifest](buffer_manifest.json), [all rows](all_results.csv), and [statistics](statistical_summary.json).\n')
    for d in ('phase_c','phase_c_v2','phase_c3'):
        for line in (ROOT/'reports'/d/'SHA256SUMS').read_text().splitlines():
            h,p=line.split('  ',1);assert digest(ROOT/p)==h
    assert not subprocess.check_output(['rtk','git','-C',str(OFFICIAL),'status','--porcelain'],text=True).strip()
    files=sorted(p for p in REPORT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
    (REPORT/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(ROOT)}\n' for p in files))
    print(json.dumps({k:v for k,v in summary.items() if k not in ('comparisons','compute_preflight')},indent=2))


if __name__=='__main__': main()
