"""Verify bounded C1 investigation and C2 audit evidence; seal deliverables."""
import json
import subprocess
from pathlib import Path
import numpy as np
from phase_c_run import ROOT,OFFICIAL,REPORT,PUBLISHED,PIN,digest


def main():
    records = [json.loads(p.read_text()) for p in sorted((REPORT/'runs').glob('*.json'))]
    native = [r for r in records if r['mode']=='native']
    assert len(native)==3 and any(r['status']=='INVESTIGATE' for r in native)
    assert all(r['seed']==0 and r['machine']=='SMD_1-8' for r in records)
    rows = []
    for machine in PUBLISHED:
        for alpha,published in PUBLISHED[machine].items():
            observed = next((r for r in native if r['machine']==machine and r['alpha']==alpha),None)
            rows.append(dict(machine=machine,alpha=alpha,published=dict(zip(('AUROC','AUPRC'),published)),
                observed=observed['observed'] if observed else None,
                absolute_discrepancy=observed['discrepancy'] if observed else None,
                status=observed['status'] if observed else 'NOT_RUN_STOP_GATE'))
    reproduction = dict(C1='INVESTIGATE',source='https://arxiv.org/html/2604.01845v1#S4.T1',
        metric_semantics='Native window-any labels, W=10 stride=1, unadjusted sklearn AUROC and trapezoidal PR-AUC, not AP',
        rows=rows,five_seed_replication_allowed=False,phase_D_ready=False,
        stop_reason='SMD_1-8 alpha 5 PR-AUC discrepancy 0.026996 > 0.02; expansion stopped before SMD_2-1',
        native_total_seconds=sum(r['runtime_seconds'] for r in native),
        all_runs_total_seconds=sum(r['runtime_seconds'] for r in records),
        peak_allocated_bytes=max(r['peak_gpu_allocated_bytes'] for r in records),
        peak_reserved_bytes=max(r['peak_gpu_reserved_bytes'] for r in records),
        investigation='Pinned upstream cached alpha=5 PR-AUC also ~0.4500, not paper 0.423. Baseline cached PR-AUC ~0.36775 vs paper 0.332. Paper-to-release checkpoint/result lineage unresolved; do not tune to paper.',
        native_code_modified=False,compatibility_patches=[])
    a = next(r for r in records if r['mode']=='audit')
    b = next(r for r in records if r['mode']=='audit_permuted')
    n = next(r for r in native if r['alpha']=='5.0')
    events_a = json.loads((REPORT/'logs'/f'{a["tag"]}.audit_events.json').read_text())
    events_b = json.loads((REPORT/'logs'/f'{b["tag"]}.audit_events.json').read_text())
    assert events_a==events_b,'Label isolation trajectory failed'
    assert a['final_model_sha256']==b['final_model_sha256']==n['final_model_sha256']
    def scores(r):
        return np.load(Path(r['working_directory'])/'results/SMD_1-8/MLP/5.0/test_scores_w_tta.npy',allow_pickle=False)
    assert np.array_equal(scores(a),scores(b)) and np.array_equal(scores(a),scores(n))
    assert a['audit']['candidate']['anomalous']!=b['audit']['candidate']['anomalous'],'Permutation did not affect evaluator truth'
    commits = [e for e in events_a['selection_and_commit_events'] if 'commit_window' in e]
    assert all(e['buffer_size']>=16 for e in commits)
    assert len(commits)==len(events_a['optimizer_steps'])==n['official_counters']['n_adapt']
    assert all(len(e['ids'])==e['buffer_size'] for e in commits)
    assert sum(e['buffer_size'] for e in commits)==a['audit']['committed']['windows_or_exposures']
    source = (OFFICIAL/'tta/candi/adapter_candi.py').read_text()
    no_fpm = source.split('if not self.cfg.TEST.TTA.CANDI.USE_FPM:')[1].split('representations = self.model.get_representations')[0]
    assert 'return' in no_fpm and 'self.iter += 1' not in no_fpm
    assert 'mask_moderate_score = scores < self.thresholder.threshold' in source
    risk = dict(score_before_adapt='Runtime PASS at native batch granularity, not pointwise within batch',
        min_samples='Runtime: all hard/moderate commits >=16, hard before moderate; pending tail not flushed',
        final_batch='Runtime: 138 windows; true offset 23552, native iter*len(scores)=12696. Selected ID23629 misindexed as12773. Both labels happen normal; aggregate anomaly count unchanged for this run.',
        official_counters='Admission counts, not committed counts: moderate9747 selected vs9746 committed; 1 pending',
        moderate_mask='Static verified: Q1-Q3 test mask overwritten by scores<threshold; reference remains validation Q1-Q3. Unchanged.',
        use_fpm_false='Static verified: early return skips iter increment; NOT executed as alternate detector configuration.',
        representation='Static: get_representations applies sana_in then frozen encoder and L2 normalization; representations can change with SANA.',
        normalization='Static native loader: split raw train80/20 first, StandardScaler.fit_transform(train80%), transform val/test. No online scaler. TRAIN_RATIO>=1 fallback uses test as val but inactive.',
        optimizer='Actual native SGD settings preserved; configured gradient-clip flag not applied by adapt loop (no clip call). No correction.',
        scope='Runtime audit only SMD_1-8 alpha5 seed0; other machine/alpha audits N/A after C1 stop')
    audit = dict(status='BOUNDED_AUDIT_PASS_NOT_FULL_C2',scope=a['tag'],natural=a['audit'],risks=risk,
        label_permutation=dict(status='PASS_LABEL_ISOLATED_OVERLAY',scores_exact=True,candidate_commit_ids_exact=True,
            update_timing_exact=True,every_optimizer_step_and_batch_model_hash_exact=True,
            final_model_exact=True,evaluator_counts_changed=True,
            note='Permutation is evaluator-only after algorithm execution by design; no evaluator labels enter isolated adapter. This does not certify the untouched official label-passing API.'),
        native_overlay_parity=dict(scores_bitwise_equal=True,final_model_hash_equal=True,
            native_intermediate_trajectory='Not instrumented; do not claim every native intermediate state was compared',
            counters='Diagnostic anomaly counters intentionally suppressed in isolated overlay; algorithm/selection totals preserved'))
    (REPORT/'reproduction_results.json').write_text(json.dumps(reproduction,indent=2)+'\n')
    (REPORT/'audit_results.json').write_text(json.dumps(audit,indent=2)+'\n')
    expected = json.loads((REPORT/'official_code_hashes.json').read_text())
    assert all(digest(OFFICIAL/p)==h for p,h in expected.items())
    assert not subprocess.check_output(['rtk','git','-C',str(OFFICIAL),'status','--porcelain'],text=True).strip()
    verification = dict(official_commit=PIN,official_clean=True,code_hashes_verified=len(expected),
        checks=['native/audit exact scores and final state','permuted/unpermuted exact all audit events and every step model hash',
                'queue/admission/commit/exposure reconciliation','MIN_SAMPLES>=16','FPM-off static early return','native stop gate'],
        no_phase_D=True)
    (REPORT/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    paths = sorted(p for p in REPORT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
    (REPORT/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(ROOT)}\n' for p in paths))
    print(json.dumps(reproduction,indent=2))
    print('C2 parity and artifact verification PASS; C1 remains INVESTIGATE')


if __name__=='__main__':
    main()
