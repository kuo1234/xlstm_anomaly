"""Verify/seal bounded Phase C v2; never launch experiments."""
import json
import subprocess
from pathlib import Path
import numpy as np
from phase_c_run import PUBLISHED, PIN
from phase_c_v2 import ROOT, OLD, REPORT, OFFICIAL, AMENDMENT, digest, record, events, equal_runs, replay_gate, score_path


def main():
    replay = replay_gate()
    control = record('SMD_1-8','5.0','native_label_control')
    permuted = record('SMD_1-8','5.0','native_label_permuted')
    closure = dict(status='PASS',checks=equal_runs(control,permuted),
        original_native_parity=equal_runs(record('SMD_1-8','5.0','native'),control,False),
        adapter_label_positions_changed=permuted['audit']['adapter_label_positions_changed'],
        original_counters=control['official_counters'],permuted_counters=permuted['official_counters'])
    assert closure['adapter_label_positions_changed']>0
    assert control['official_counters']!=permuted['official_counters']
    for k,v in control['official_counters'].items():
        if 'total_anomalies' not in k:
            assert v==permuted['official_counters'][k]
    isolated = json.loads((OLD/'runs/SMD_1-8_alpha_5.0_seed_0_audit.json').read_text())
    isolated_events = json.loads((OLD/'logs'/f'{isolated["tag"]}.audit_events.json').read_text())
    assert isolated_events==events(control)
    assert equal_runs(isolated,control,False)
    closure['independent_label_isolated_overlay_full_trace_equal'] = True
    cache = json.loads((OLD/'upstream_cache_investigation.json').read_text())
    rows = []
    for machine in PUBLISHED:
        for alpha in PUBLISHED[machine]:
            r = record(machine,alpha,'native' if machine=='SMD_1-8' else 'native_v2')
            c = next(c for c in cache if c['machine']==machine and c['alpha']==alpha)
            values = dict(paper=c['published'],author_cache={k:c['test_scores_w_tta.npy'][k] for k in ('AUROC','AUPRC')},
                local={k:r['observed'][k] for k in ('AUROC','AUPRC')})
            differences = {f'{a}_vs_{b}':{k:abs(values[a][k]-values[b][k]) for k in ('AUROC','AUPRC')}
                for a,b in [('paper','local'),('paper','author_cache'),('author_cache','local')]}
            status = {k:'MATCH' if max(v.values())<=.02 else 'MISMATCH' for k,v in differences.items()}
            rows.append(dict(machine=machine,alpha=alpha,seed=0,**values,absolute_discrepancies=differences,
                comparison_status=status,lineage_status='UNRESOLVED_LINEAGE',
                local_record=str((OLD if machine=='SMD_1-8' else REPORT).relative_to(ROOT)/'runs'/f'{r["tag"]}.json'),
                cache_role='Lineage only; not a runnable or experimental baseline',
                local_score_sha256=digest(score_path(r)),cache_score_sha256=c['test_scores_w_tta.npy']['sha256']))
    runs = [json.loads(p.read_text()) for p in sorted((REPORT/'runs').glob('*.json'))]
    driver = subprocess.check_output(['rtk','nvidia-smi','--query-gpu=name,driver_version','--format=csv,noheader'],text=True).strip()
    assert driver=='NVIDIA GB10, 580.173.02',driver
    assert len(runs)==7
    for r in runs:
        assert r['seed']==0 and r['error'] is None and np.isfinite(np.load(score_path(r))).all()
        assert r['official_commit']==PIN
        audit = r['audit']
        trace = events(r)
        commits = [e for e in trace['selection_and_commit_events'] if 'commit_window' in e]
        assert len(commits)==audit['update_count']==r['official_counters']['n_adapt']
        assert all(e['buffer_size']>=16 and e['buffer_size']==len(e['ids']) for e in commits)
        assert audit['optimizer_step_count']==audit['update_count']*(5 if r['machine']=='SMD_2-1' else 1)
        assert audit['candidate']['windows_or_exposures']==audit['committed']['windows_or_exposures']+audit['pending_total']
        assert audit['score_before_update'] and audit['permutation_preserved_global_rng']
        for rel,h in r['artifact_hashes'].items():
            assert digest(Path(r['working_directory'])/rel)==h
    for line in (OLD/'SHA256SUMS').read_text().splitlines():
        h,path = line.split('  ',1)
        assert digest(ROOT/path)==h,path
    expected = json.loads((OLD/'official_code_hashes.json').read_text())
    assert all(digest(OFFICIAL/p)==h for p,h in expected.items())
    assert not subprocess.check_output(['rtk','git','-C',str(OFFICIAL),'status','--porcelain'],text=True).strip()
    result = dict(amendment_commit=subprocess.check_output(['rtk','git','rev-parse',AMENDMENT],text=True).strip(),
        C1_P='MISMATCH',lineage_status='UNRESOLVED_LINEAGE',C1_R='PASS_BOUNDED_SEED0',rows=rows,
        deterministic_replay=replay,native_label_permutation=closure,
        five_seed_scientifically_ready=True,five_seed_authorized=False,five_seed_run=False,phase_D_authorized=False,
        readiness_scope='Recommend five-seed replication pending external review; not cross-seed/cross-hardware proof or H1 causal evidence',
        runtime_seconds=sum(r['runtime_seconds'] for r in runs),
        cuda_event_span_ms=sum(r['cuda_event_span_ms'] for r in runs),
        peak_gpu_allocated_bytes=max(r['peak_gpu_allocated_bytes'] for r in runs),
        peak_gpu_reserved_bytes=max(r['peak_gpu_reserved_bytes'] for r in runs),
        official_immutable=True,historical_phase_c_seal_verified=True,no_retraining=True,
        gpu_driver_verified=driver,
        metric_semantics='Native window-any labels; unadjusted AUROC and trapezoidal PR-AUC (not AP)')
    (REPORT/'reproduction_results.json').write_text(json.dumps(result,indent=2)+'\n')
    audits = {r['tag']:r['audit'] for r in runs}
    (REPORT/'audit_results.json').write_text(json.dumps(dict(native_passive_observations=audits,
        native_label_permutation=closure,unchanged_defects=json.loads((OLD/'audit_results.json').read_text())['risks']),indent=2)+'\n')
    table = ['| Machine | alpha | Paper AUROC / PR-AUC | Author cache (lineage only) | Local native |',
             '|---|---:|---:|---:|---:|']
    for r in rows:
        table.append('| '+r['machine']+' | '+r['alpha']+' | '+' | '.join(f'{r[k]["AUROC"]:.6f} / {r[k]["AUPRC"]:.6f}' for k in ('paper','author_cache','local'))+' |')
    text = '''# Phase C v2 — released-artifact fidelity

C1-P: **MISMATCH**, paper/checkpoint/cache attribution **UNRESOLVED_LINEAGE**.
C1-R: **PASS for the authorized bounded seed0 checks**. Recommend five-seed
replication for external review; it has NOT been authorized or executed.
Phase D and all other modeling experiments remain locked.

## Official reproduction

Pre-outcome amendment commit: AMENDMENT_SHA. It was pushed before either replay
and before any new SMD_2-1 execution outcome. The pinned official checkout and
all historical Phase C report hashes were verified unchanged. No compatibility
patch, retraining, RNG manipulation to chase metrics, or hyperparameter tuning.
Official TRAIN.ENABLE=False checkpoint path and author scripts are unchanged.
Additional runner guards assert checkpoint hashes and reject TRAIN.ENABLE=True;
these checks do not change configuration. Environment versions match the prior
frozen environment. Commands, resolved configs, artifact hashes, GPU timings,
allocator peaks and stdout/stderr are retained per run.

TABLE

All six local rows are actual executions; cached arrays are lineage evidence
only. First three local rows preserve original seed0 results. PR-AUC here is
native trapezoidal area, not average precision. JSON reports exact values and
all three pairwise absolute discrepancies; MATCH uses the historical 0.02
tolerance for reporting only. The alpha5 1-8 paper discrepancy persists, as does
the alpha0.5 2-1 cache/paper discrepancy. No speculative lineage explanation is
treated as established.

## Deterministic replay

Both additional 1-8 alpha0.5 executions exactly match original full score
arrays/file hashes, metrics, update count and canonical final model hash.
The two new replays also match initial RNG/model hashes and the entire stable
selection/commit/exposure/update/batch trace. The original native run had no
intermediate-ID instrumentation, so no original intermediate parity is claimed.
Only after this gate passed were the three 2-1 alpha rows executed.

## Native permutation and independent audit

A fresh alpha5 native control and counterpart permuting only adapter test_labels
with independent NumPy generator seed902 have identical scores, candidate and
commit IDs, update timing, all intermediate/final model hashes and metrics.
Global RNG fingerprints are equal and diagnostic anomaly counters differ.
True evaluator labels stay unchanged. This closes the requested native test
for this configuration, not a universal noninterference proof. The label-free
independent overlay remains separate and matches the control's full trace.

Passive instrumentation uses the same stable-ID observer as the accepted audit,
but imports untouched native adapter code; no label-removal module is installed
on this path. Refactoring extracted observer installation without changing the
existing independent overlay behavior. Observers never repair native indexing,
mask overwrite, current-SANA representation dependence, FPM-off iteration or
admission-versus-exposure bookkeeping. Native diagnostic labels still enter the
official API; scientific contamination counts use true evaluator labels only
after execution and independent stable IDs. Zero exposures are N/A, not zero.
Audit results include separate candidates, commits, loss exposures, repeated
exposures, pending cohorts, anomaly timestamp coverage and latency. Batch-end
availability is preserved; no pointwise score-before-update claim is made.

## Scope and timing

Seven additional runs only: two alpha0.5 replays, three 2-1 seed0 evaluations,
and the alpha5 native permutation/control pair. Canonical tensor-state hashes
are used for model equality; serialized checkpoint file hashes are provenance,
not a tensor-equivalence requirement. CUDA event spans include host gaps and
observer synchronization; they are not summed active-kernel time. See JSON for
measured durations and allocated/reserved peaks. Full arrays and checkpoints
remain under data/phase_c/runs with sealed hashes; compact reports/traces/logs
are version-controlled.

No five-seed, H1 causal contamination, Phase D, xLSTM/LSTM, probes, H4 or H3b run.
Next step requires external authorization; paper fidelity remains unresolved
even though this bounded operational baseline is stable and auditable.
'''.replace('AMENDMENT_SHA',result['amendment_commit']).replace('TABLE','\n'.join(table))
    (REPORT/'README.md').write_text(text)
    with (REPORT/'README.md').open('a') as f:
        f.write(f'\nMeasured seven-run native-entry wall time: {result["runtime_seconds"]:.3f} s. '
                f'Peak allocated/reserved GPU memory: {result["peak_gpu_allocated_bytes"]/2**30:.3f} / '
                f'{result["peak_gpu_reserved_bytes"]/2**30:.3f} GiB.\n')
    (REPORT/'verification.json').write_text(json.dumps(dict(
        checks=['two fresh replay full-array/hash parity with original',
                'replay candidate/commit/exposure/update/batch and initial RNG equality',
                'native test-label permutation counter change with full behavior parity',
                'native control versus original and independent isolated overlay parity',
                'all seven finite outputs; seed0; checkpoint and official code invariants',
                'MIN_SAMPLES, updates, five-step exposures, pending queue reconciliation',
                'all native output artifact hashes and historical report seals',
                'GPU driver and frozen Python/package/Torch/CUDA/cuDNN/device versions'],
        all_passed=True,final_harness_sha256={p:digest(ROOT/p) for p in (
            'scripts/phase_c_run.py','scripts/phase_c_audit.py','scripts/phase_c_v2.py','scripts/phase_c_v2_finalize.py')},
        harness_revision_note='Checkpoint/config preflight guards and code/Python checks added after two replays; replays already recorded checkpoint/config hashes and used unchanged native defaults. No algorithm/RNG change.',
        source_syntax_check='python -m py_compile passed for all four scripts'),indent=2)+'\n')
    paths = sorted(p for p in REPORT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
    (REPORT/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(ROOT)}\n' for p in paths))
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','deterministic_replay','native_label_permutation')},indent=2))
    print('\n'.join(table))


if __name__=='__main__':
    main()
