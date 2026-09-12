"""Seal failed implementation evidence without making a harm inference."""
import csv
import json
import subprocess
import numpy as np
import torch
from phase_d_operator import ROOT,REPORT,DATA,OFFICIAL,NOTE,tensor_hash
from phase_c_run import digest
from phase_d_statistics import paired_summary,holm
from config import get_cfg_defaults
from datasets.build import build_dataset


def main():
    stop=json.loads((REPORT/'execution_stop.json').read_text())
    assert stop['status']=='STOP_IMPLEMENTATION_VALIDITY'
    diagnostics=json.loads((REPORT/'repeat_failure_diagnostic.json').read_text())
    default,fixed=diagnostics['conditions']
    assert not default['cudnn_deterministic'] and fixed['cudnn_deterministic']
    assert all(c['pre_states_exact'] for r in (default,fixed) for c in r['comparisons'])
    assert all(not c['model_exact'] and not c['scores_exact'] for c in default['comparisons'])
    assert all(c['model_exact'] and c['scores_exact'] and c['optimizer_exact'] for c in fixed['comparisons'])
    capture=torch.load(DATA/'real_operator_capture.pth',map_location='cpu',weights_only=False)
    cfg=get_cfg_defaults();cfg.merge_from_other_cfg(type(cfg).load_cfg(capture['config']));cfg.DATA.BASE_DIR=str(OFFICIAL/'data')
    ds=build_dataset(cfg,'test')
    exact=torch.from_numpy(np.stack([ds[i][0] for i in capture['event']['ids']]))
    assert torch.equal(exact,capture['buffer'])
    assert torch.equal(torch.from_numpy(np.stack([ds[i][0] for i in range(256,512)])),capture['segment'])
    native=json.loads((REPORT/'runs/SMD_1-8_alpha_5.0_seed_0_native_d0.json').read_text())
    old=json.loads((ROOT/'reports/phase_c_v2/runs/SMD_1-8_alpha_5.0_seed_0_native_label_control.json').read_text())
    def native_scores(r):
        return np.load(__import__('pathlib').Path(r['working_directory'])/'results/SMD_1-8/MLP/5.0/test_scores_w_tta.npy')
    assert np.array_equal(native_scores(native),native_scores(old))
    assert native['final_model_sha256']==old['final_model_sha256']
    assert json.loads((REPORT/'logs'/f'{native["tag"]}.audit_events.json').read_text())==json.loads(
        (ROOT/'reports/phase_c_v2/logs'/f'{old["tag"]}.audit_events.json').read_text())
    zero=paired_summary(np.zeros((10,5,4)));constant=paired_summary(np.full((10,5,4),.03))
    assert zero['p_two_sided']==1 and zero['ci95']==[0,0]
    assert constant['p_two_sided']==2/1024 and np.allclose(constant['ci95'],[.03,.03])
    assert holm([.01,.02,1])==[.03,.04,1]
    pairs=[json.loads(p.read_text()) for p in sorted((REPORT/'rows').glob('*.json'))]
    assert len(pairs)==83
    rows=[r for pair in pairs for r in pair['rows']]
    assert len(rows)==498
    output=[]
    for r in rows:
        assert digest(ROOT/r['score_path'])==r['score_sha256']
        item={k:r[k] for k in ('source','scenario','condition','detector_seed','c','parameter_delta_l2','runtime_seconds','score_path','score_sha256')}
        item.update(r['metrics']);item['valid_for_H1_inference']=False
        output.append(item)
    with (REPORT/'quarantined_partial_results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(output[0]),lineterminator='\n');w.writeheader();w.writerows(output)
    artifacts={str(p.relative_to(ROOT)):digest(p) for p in sorted(DATA.rglob('*')) if p.is_file()}
    partial=[p.name for p in (DATA/'grid').iterdir() if not (REPORT/'rows'/f'{p.name}.json').exists()]
    assert len(partial)==1
    env=json.loads((REPORT/'environment.json').read_text())
    environment_audit=dict(binary_version_reference_sha256=digest(ROOT/'reports/phase_c/environment.json'),
        captured_D0_environment_sha256=digest(REPORT/'environment.json'),
        reference_commit_field_note='environment.json was produced by reused C-v2 recorder and retains a8e0730 reference; actual Phase D prospective commit is9018e86',
        D0_native_flags='Native main calls set_seeds: cudnn.deterministic=True and benchmark=False',
        synthetic_training_flags='Official set_seeds called per seed before training and SANA initialization',
        synthetic_grid_flags=diagnostics['fresh_process_flags'],
        mismatch='Same package versions are insufficient: synthetic fresh-process restore_rng omitted backend determinism flags',
        prospective_commit=NOTE,production_grid_repaired=False)
    (REPORT/'execution_environment_audit.json').write_text(json.dumps(environment_audit,indent=2)+'\n')
    launches=[json.loads(p.read_text()) for p in (REPORT/'logs').glob('*.launch.json')]
    summary=dict(D0='STOP_IMPLEMENTATION_VALIDITY',real_official_operator_parity='PASS_BITWISE',
        synthetic_repeat_parity='FAIL',H1_harm='INCONCLUSIVE_NOT_VALIDLY_TESTED',qualifying_comparisons=[],
        qualifying_note='Not evaluated, not evidence that no comparison would qualify',
        statistical_tests_on_harm='NOT_COMPUTED',curves='No valid contamination-performance curves; partial results quarantined',
        complete_rows=498,planned_rows=4800,complete_pairs=83,partial_pairs=partial,
        no_later_phase_run=True,grid_process_stopped=True,
        complete_pair_seconds=sum(p['total_seconds'] for p in pairs),
        complete_arm_seconds=sum(r['runtime_seconds'] for r in rows),
        complete_arm_peak_allocated_bytes=max(r['peak_gpu_allocated_bytes'] for r in rows),
        complete_arm_peak_reserved_bytes=max(r['peak_gpu_reserved_bytes'] for r in rows),
        logged_process_seconds_sum=sum(p['wall_seconds'] for p in launches),
        process_time_note='Includes overlapping training processes, setup, data generation and diagnostic overhead; not total elapsed or pure GPU-kernel time',
        no_outcomes_discarded=True,no_threshold_relaxation=True,no_automatic_repair_or_grid_restart=True)
    (REPORT/'statistical_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (REPORT/'artifact_manifest.json').write_text(json.dumps(dict(artifacts=artifacts,partial_pairs=partial,
        all_grid_artifacts_quarantined=True,backbones_and_real_capture_retained=True),indent=2)+'\n')
    verification=dict(status='STOP_WITH_EVIDENCE_SEALED',native_buffer_order_independently_reconstructed_exact=True,
        native_full_run_scores_final_model_and_all_audit_events_match_sealed_control=True,
        native_next_segment_independently_reconstructed_exact=True,
        cpu_buffer_tests=json.loads((REPORT/'pre_curve_tests.json').read_text()),
        statistics_unit_tests='PASS zero/constant-difference bootstrap/sign-flip and Holm fixtures; no experimental statistics evaluated',
        synthetic_default_repeat='FAIL',synthetic_deterministic_flag_diagnostic='PASS3/3 repeats for one c10 buffer, not blanket validation',
        exact_buffer_sha256=tensor_hash(exact),
        source_hashes={str(p.relative_to(ROOT)):digest(p) for p in sorted((ROOT/'scripts').glob('*phase_d*.py'))})
    for directory in ('phase_c','phase_c_v2','phase_c3'):
        for line in (ROOT/'reports'/directory/'SHA256SUMS').read_text().splitlines():
            h,p=line.split('  ',1);assert digest(ROOT/p)==h
    code=json.loads((ROOT/'reports/phase_c/official_code_hashes.json').read_text())
    assert all(digest(OFFICIAL/p)==h for p,h in code.items())
    assert not subprocess.check_output(['rtk','git','-C',str(OFFICIAL),'status','--porcelain'],text=True).strip()
    verification['previous_C_reports_and_official_code_unchanged']=True
    (REPORT/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    max_score=max(c['max_score_abs_difference'] for c in default['comparisons'])
    max_param=max(c['max_parameter_abs_difference'] for c in default['comparisons'])
    decision=f'''# Phase D — implementation-validity STOP

D0 as an end-to-end gate: **STOP**. The captured real SMD official-operator
replay itself **PASSes bitwise**, but synthetic fresh-process repeat parity fails.
H1-harm: **INCONCLUSIVE / not validly tested**. H1-admission remains GO separately.
This is not a modeling-hypothesis STOP and not evidence of absence of harm.

## Evidence and root cause

Prospective protocol9018e86 was committed/pushed before harm. D0 captured native
SMD_1-8 alpha5 seed0 update1 (242 ordered moderate windows). Native and harness
loss0.20451687276363373, post-model/optimizer/RNG and next256-window scores match
exactly. An independent official dataset reconstruction also confirms buffer
order and fixed score segment. The official checkout remains immutable.

All five D8 backbone/scaler/calibration/SANA/optimizer/RNG states and160 buffer
layouts were committed/pushed (combined manifest3485a61) before the first harm
arm. The first dry preflight failed closed because the combined manifest had
not reached the earlier commit; no arm ran then. After sealing, the dry-run
took2.696s and projected4397.705s (1.22h) conservatively, passing the24h gate.

Engineering failure: the synthetic grid restored random generator states but
did not restore `torch.backends.cudnn.deterministic=True`. Native main and
backbone training call official set_seeds and enable it; a new grid process
defaults to False. Equal checkpoint/RNG states did not guarantee equal execution.
The extra D8 repeat/label-isolation test was run after grid expansion rather than
before it; this ordering was insufficient and must be corrected in a new version.

Unpermuted identical-buffer diagnosis reproduces the failure: identical pre-model,
optimizer and RNG, same loss, but post-tensors/optimizer/scores differ. Maximum
parameter difference {max_param:.12g}; maximum score difference {max_score:.12g}.
Thus this is not evidence that evaluator labels affect adaptation. In the bounded
diagnostic ONLY, setting the native cuDNN deterministic flag produced three exact
repeats. No tolerance was widened and the production grid was not repaired/restarted.

## Quarantine and missing results

The grid was terminated with83 complete pairs (498 rows) and one partial pair,
not4800 completed rows. All existing positives/negatives/null outcomes and raw
scores remain retained in rows/, quarantined_partial_results.csv and the local
artifact manifest; none is admissible for confirmatory H1 inference. No qualifying
comparison, hierarchical CI/Holm test or valid contamination-performance curve is
reported. An empty qualifying list means NOT EVALUATED, not a negative result.
Do not combine these rows with any corrected rerun or retain only convenient arms.

## Minimal proposed correction (requires review)

1. Version the harness and explicitly pin/assert/capture backend determinism,
   cuDNN benchmark and relevant precision settings alongside model/optimizer/RNG.
2. Run official real parity plus D8 identical-buffer and actual label-permutation
   closure BEFORE any new dry-run/expansion; include both positive and zero-update
   controls. One successful diagnostic is not sufficient full validation.
3. Preserve current quarantine, backbones and protocol. Verify whether sealed
   backbone states/calibration remain reusable under the corrected flags. Reuse
   only after integrity tests; no outcome-based retraining/config changes.
4. Obtain approval, reseal the corrected implementation and rerun the entire grid
   in new paths. Keep all original hypotheses, slots, seeds and statistical gates.

## Runtime and scope

Completed-pair generation/update/evaluation sum: {summary['complete_pair_seconds']:.3f}s;
completed-arm sum: {summary['complete_arm_seconds']:.3f}s. Completed-grid peak
allocated/reserved: {summary['complete_arm_peak_allocated_bytes']/2**30:.3f}/
{summary['complete_arm_peak_reserved_bytes']/2**30:.3f}GiB (per-process allocator,
not total device peak). Full per-process training/parity/dry/grid/diagnostic wall
times are in logs; overlapping trainings must not be summed as elapsed wall.

Five score-free buffer/metric tests and CPU statistical fixture tests pass.
Original C/Cv2/C3 seals and official code remain unchanged. No natural-SMD harm,
H4a/H4b, xLSTM/LSTM, probes, H3b, rollback or dual memory ran. Return for external
review; the launcher and statistical finalizer now reject execution_stop.json.
'''
    (REPORT/'decision.md').write_text(decision)
    (REPORT/'README.md').write_text('# Phase D — STOP\n\nSee [decision](decision.md). '
        'D0 real operator parity PASS, synthetic repeat parity FAIL; H1-harm is not validly tested. '
        'All partial grid results are quarantined, not confirmatory evidence.\n\n'
        'Key files: prospective.md, operator_parity.json, synthetic_backbone_manifest.json, buffer_manifest.json, '
        'repeat_failure_diagnostic.json, execution_stop.json, statistical_summary.json, quarantined_partial_results.csv, '
        'artifact_manifest.json, execution_environment_audit.json, verification.json, logs/, SHA256SUMS.\n')
    files=sorted(p for p in REPORT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
    (REPORT/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(ROOT)}\n' for p in files))
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
