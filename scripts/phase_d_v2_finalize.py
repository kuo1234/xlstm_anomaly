"""Validate only the complete NEW grid; reuse frozen H1 statistics unchanged."""
import json
from pathlib import Path
import subprocess
import time
import numpy as np
import phase_d_finalize as frozen
from phase_c_run import ROOT,digest
from phase_d_operator import tensor_hash
from phase_d_buffers import compose,SCENARIOS,TYPES,CS
from phase_d_backbone import SEEDS
from m0.metrics import metrics

REPORT=ROOT/'reports/phase_d_v2'
DATA=ROOT/'data/phase_d_v2'


def main():
    started=time.perf_counter()
    assert not (REPORT/'execution_stop.json').exists()
    complete=json.loads((REPORT/'grid_complete.json').read_text())
    assert complete['status']=='PASS' and complete['rows']==4800
    assert complete['validated_sources']==list(range(3000,3010))
    gates=json.loads((REPORT/'pre_grid_gates.json').read_text())
    assert gates['status']=='PASS'
    canaries=[json.loads(line) for line in (REPORT/'canaries.jsonl').read_text().splitlines()]
    assert [r['tag'] for r in canaries]==['before_grid',*[f'after_source_{s}' for s in range(3000,3010)],'after_grid']
    reference=gates['gate2']['behavior']
    assert all(r['status']=='PASS' and r['behavior']==reference for r in canaries)
    codes=json.loads((REPORT/'implementation_integrity.json').read_text())['code_sha256']
    assert all(digest(ROOT/p)==h for p,h in codes.items())
    for p in ('amendment.md','backend_seal.json','pre_grid_gates.json','reuse_verification.json'):
        assert subprocess.check_output(['rtk','git','show',f'909b326:reports/phase_d_v2/{p}'])==(REPORT/p).read_bytes()
    paths=sorted((REPORT/'rows').glob('*.json'));assert len(paths)==800
    pairs={p.stem:json.loads(p.read_text()) for p in paths}
    backbones={r['detector_seed']:r for r in json.loads((REPORT/'synthetic_backbone_manifest.json').read_text())['rows']}
    manifest=json.loads((REPORT/'buffer_manifest.json').read_text())['rows']
    artifacts={}
    verified=0
    # Evaluator-only truth; no model is created or updated in this program.
    for source in range(3000,3010):
        for scenario in SCENARIOS:
            for kind in TYPES:
                arms,x,y,primary,layout=compose(source,scenario,kind)
                assert layout==next(m for m in manifest if (m['source'],m['scenario'],m['condition'])==(source,scenario,kind))
                for seed in SEEDS:
                    tag=f'{source}_{scenario}_{kind}_{seed}';pair=pairs[tag]
                    assert pair['tag']==tag and [r['c'] for r in pair['rows']]==[None,*CS]
                    b=backbones[seed]
                    for row in pair['rows']:
                        assert (row['source'],row['scenario'],row['condition'],row['detector_seed'])==(source,scenario,kind,seed)
                        assert row['backend_fingerprint']==gates['backend_fingerprint']
                        assert row['backend_seal_sha256']==digest(REPORT/'backend_seal.json')
                        assert row['version']=='D-v2' and row['quarantined_v1_reused'] is False
                        assert row['pre_model_sha256']==b['initial_model_sha256']
                        assert row['pre_optimizer_sha256']==b['optimizer_sha256'] and row['pre_rng_sha256']==b['rng_sha256']
                        assert row['fixed_threshold']==b['threshold']
                        c=row['c']
                        assert row['buffer_sha256']==(None if c is None else layout['arms'][str(c)]['buffer_sha256'])
                        path=ROOT/row['score_path']
                        assert path.parent==DATA/'grid'/tag
                        assert digest(path)==row['score_sha256'];artifacts[row['score_path']]=row['score_sha256']
                        scores=np.load(path,allow_pickle=False)
                        assert len(scores)==len(y) and np.isfinite(scores).all()
                        assert metrics(y[primary],scores[primary],b['threshold'])==row['metrics']
                        assert metrics(y[~primary],scores[~primary],b['threshold'])==row['stress_metrics']
                        assert row['clean_normal_fpr']==row['metrics']['fpr']
                        verified+=1
        print('Independent full-score/metric verification source',source,'rows',verified,flush=True)
    assert verified==4800 and len(artifacts)==4800
    # Exact frozen analysis, including 22-way Holm and inconclusive semantics.
    # Routing only: no scientific change to its statistical implementation.
    frozen.REPORT=REPORT;frozen.DATA=DATA
    frozen.main()
    summary=json.loads((REPORT/'statistical_summary.json').read_text())
    grid_start=json.loads((REPORT/'grid_start.json').read_text())
    grid_wall=complete['time']-grid_start['time']
    launches={p.stem.removesuffix('.launch'):json.loads(p.read_text()) for p in (REPORT/'logs').glob('*.launch.json')}
    assert launches['full_grid']['returncode']==0
    assert all(r['returncode']==0 for k,r in launches.items() if k!='unit_tests')
    assert json.loads((REPORT/'unit_tests_fixed.json').read_text())['status']=='PASS'
    process_records=[json.loads(p.read_text()) for p in (REPORT/'processes').glob('*.json')]
    assert all(p['backend_fingerprint']==gates['backend_fingerprint'] and p['device_uuid']==gates['device_uuid'] for p in process_records)
    runtime=dict(grid_wall_seconds=grid_wall,grid_process_wall_seconds=launches['full_grid']['wall_seconds'],
        grid_arm_runtime_seconds=summary['measured_arm_seconds'],grid_pair_runtime_seconds=summary['measured_pair_total_seconds'],
        canary_runtime_seconds=sum(c['runtime_seconds'] for c in canaries),canaries=12,
        peak_gpu_allocated_bytes=summary['peak_gpu_allocated_bytes'],peak_gpu_reserved_bytes=summary['peak_gpu_reserved_bytes'],
        process_walls={k:v['wall_seconds'] for k,v in launches.items()},
        gpu_time_note='GPU workload wall time, not active-kernel time; allocator peak is not full device memory.',
        reused_backbones=5,retraining_seconds=0)
    environment=json.loads((ROOT/'reports/phase_c/environment.json').read_text())
    environment.update(version='D-v2',backend=json.loads((REPORT/'backend_seal.json').read_text()),
        backend_fingerprint=gates['backend_fingerprint'],device_uuid=gates['device_uuid'],
        amendment_commit=subprocess.check_output(['rtk','git','rev-parse','a40634b'],text=True).strip(),
        parity_gate_commit=subprocess.check_output(['rtk','git','rev-parse','909b326'],text=True).strip(),
        frozen_code_sha256=codes,
        analysis_code_sha256={p:digest(ROOT/p) for p in ('scripts/phase_d_v2_finalize.py',
            'scripts/phase_d_v2_tests.py','scripts/phase_d_v2_seal.py','tests/test_phase_d_v2.py')})
    (REPORT/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
    (REPORT/'runtime.json').write_text(json.dumps(runtime,indent=2)+'\n')
    summary.update(version='D-v2',four_parity_gates='PASS_BITWISE',canaries='12/12_PASS_BITWISE',
        quarantined_v1_rows_used=0,verified_new_score_arrays=verified,backend_fingerprint=gates['backend_fingerprint'])
    (REPORT/'statistical_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    curves=json.loads((REPORT/'curves.json').read_text())
    lines=['# Phase D v2 controlled H1 decision','',
        f'D0 **PASS**. **H1-HARM {summary["H1_harm"]}** under the unchanged frozen decision rule.',
        '', 'All four pre-grid gates and all 12 canaries passed bitwise. The complete 4,800-row grid is new; '
        'zero quarantined v1 rows entered estimation, plots, CIs, tests or decisions. The five sealed backbones '
        'were reused without retraining. Correction: restore accepted execution backend state, including '
        'cuDNN deterministic=True; deterministic_algorithms remains False.',
        '', '## All comparisons, including negative/null and stress results','',
        '| Type | c% | AP(clean) − AP(c) | Paired 95% CI | Holm p (22) | Positive seeds/scenarios | GO |',
        '|---|---:|---:|---|---:|---|---|']
    for r in summary['comparisons']:
        lines.append(f'| {r["condition"]} | {r["c"]} | {r["mean"]:.6f} | [{r["ci95"][0]:.6f}, {r["ci95"][1]:.6f}] | '
            f'{r["holm_p"]:.6f} | {r["positive_detector_seeds"]}/5; {r["positive_scenarios"]}/4 | {r["qualifies"]} |')
    lines+=['', 'c30 is stress-only and cannot qualify. No natural-SMD harm alternative was run (six p=1 placeholders). '
        'Hierarchical bootstrap: 10,000 draws, seed901; exact two-sided source-cluster sign flips; '
        '10 sources first, five paired detector seeds second, all four scenarios kept jointly.',
        '', '## All contamination curves and no-update controls','',
        '| Type | c% / control | Macro AP | Macro AUROC | Fixed FPR | Fixed recall |',
        '|---|---|---:|---:|---:|---:|']
    for r in curves:
        lines.append(f'| {r["condition"]} | {"no update" if r["c"] is None else r["c"]} | {r["mean_ap"]:.6f} | '
            f'{r["mean_auroc"]:.6f} | {r["mean_fpr"]:.6f} | {r["mean_recall"]:.6f} |')
    lines+=['', '![Contamination curves](contamination_curves.png)','',
        '## Interpretation and limits','',
        'H1-admission remains GO from independent C3 evidence; admission is not harm. This test compares one '
        'clean versus contaminated pinned SANA update, not sequential natural-stream harm. Negative effects '
        'mean contaminated AP exceeded clean AP in this intervention, not universal safety. Failure to reach '
        'the practical margin is not proof of no smaller harm. Any H1-HARM STOP is bounded to this frozen test, '
        'not a global safe-adaptation research STOP.',
        '', 'The intervention is an ordered 100-window buffer: selective replacement of overlapping windows '
        'need not correspond to one globally consistent corrupted raw stream. Event-onset windows do not '
        'isolate long-duration effects. Severity/duration and latent source are paired; they are not independently '
        'randomized causal factors. The synthetic D8 MLP is not a released SMD checkpoint or xLSTM reproduction.',
        '', 'No-update loss/gradient exposure is N/A, not evidence of 0% contamination. Updated arms have exactly '
        '100 loss exposures and one optimizer step, with c anomalous windows/exposures; repeated events/windows '
        'are not independent statistical replicates. AP is unadjusted average precision, not native trapezoidal PR-AUC. '
        'Thresholds are the sealed calibration values; no test-best threshold or outcome-dependent selection.',
        '', '## Runtime and integrity','',
        f'Full grid wall: {grid_wall:.3f}s ({grid_wall/3600:.3f}h); process wall: {runtime["grid_process_wall_seconds"]:.3f}s. '
        f'Arm runtime sum: {summary["measured_arm_seconds"]:.3f}s; 12 canaries: {runtime["canary_runtime_seconds"]:.3f}s. '
        f'Peak GPU allocated/reserved: {summary["peak_gpu_allocated_bytes"]/2**30:.3f}/{summary["peak_gpu_reserved_bytes"]/2**30:.3f} GiB. '
        'Wall figures are not active CUDA kernel-time measurements.',
        '', 'Every new score array was rehashed and every primary/stress metric recomputed independently from '
        'sealed evaluator-only labels. Every buffer/layout, pre-state and fixed threshold was matched to its input seal. '
        'All original report seals, including the permanent v1 quarantine, remain intact.',
        '', 'The supplementary CPU test launcher initially omitted the project root from sys.path, causing two '
        'test-module import errors before those tests executed. That launcher-only path issue was corrected; '
        'the original failed log/JSON and the complete successful rerun are both retained. All five backend '
        'negative-control tests already passed on the first run. No grid, model, backend or scientific code changed.',
        '', 'No H4a/H4b, xLSTM/LSTM, H2/H3/H3b, natural-SMD harm, rollback, dual memory or learned commit '
        'mechanism was run. Return for external review; this report does not authorize the next phase.', '']
    (REPORT/'decision.md').write_text('\n'.join(lines))
    (REPORT/'README.md').write_text('# Phase D v2\n\n'
        f'**D0 PASS; H1-HARM {summary["H1_harm"]}.** All 4,800 new rows complete; four parity gates and 12 canaries PASS bitwise.\n\n'
        'See [decision and complete negative results](decision.md), [amendment](amendment.md), '
        '[unchanged prospective design](../phase_d/prospective.md), [backend seal](backend_seal.json), '
        '[reuse verification](reuse_verification.json), [pre-grid gates](pre_grid_gates.json), '
        '[real operator parity](operator_parity.json), [canaries](canaries.jsonl), '
        '[all results](all_results.csv), [statistics](statistical_summary.json), '
        '[buffer manifest](buffer_manifest.json), [environment](environment.json), and [runtime](runtime.json).\n\n'
        'Pre-outcome amendment a40634b; pre-grid seal 909b326, both pushed before corrected full-grid outcomes. '
        'Backend restoration only; no scientific rule changed, no backbone retrained, no quarantined row reused. '
        'Native CANDI code remains immutable. External review required before any later phase.\n')
    for r in backbones.values():
        for p,h in r['artifacts'].items():assert digest(ROOT/p)==h;artifacts[p]=h
    for p in (REPORT/'gates').glob('*.json'):
        for a,h in json.loads(p.read_text())['artifacts'].items():assert digest(ROOT/a)==h;artifacts[a]=h
    real=json.loads((REPORT/'operator_parity.json').read_text())
    assert digest(ROOT/real['snapshot_path'])==real['snapshot_sha256']
    artifacts[real['snapshot_path']]=real['snapshot_sha256']
    (REPORT/'local_artifact_SHA256SUMS').write_text(''.join(f'{h}  {p}\n' for p,h in sorted(artifacts.items())))
    for folder in ('phase_c','phase_c_v2','phase_c3','phase_d'):
        for line in (ROOT/'reports'/folder/'SHA256SUMS').read_text().splitlines():
            h,p=line.split('  ',1);assert digest(ROOT/p)==h
    (REPORT/'final_verification.json').write_text(json.dumps(dict(status='PASS',new_rows_verified=verified,
        new_score_metrics_recomputed=verified,canaries_bitwise=12,all_input_seals_valid=True,
        original_report_seals_unchanged=True,quarantined_outcomes_used=False,
        seconds=time.perf_counter()-started),indent=2)+'\n')
    print('D-v2 FINAL',summary['H1_harm'],'qualifying',len(summary['qualifying']),'rows',verified,flush=True)


if __name__=='__main__':main()
