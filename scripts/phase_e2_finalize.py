"""Reporting/integrity only; no model result generation or scientific fitting."""
import json,math,subprocess
from pathlib import Path
from phase_e2_common import ROOT,REPORT,OFFICIAL,sha

if __name__=='__main__':
    v=json.loads((REPORT/'validity_verified.json').read_text())
    initial=json.loads((REPORT/'validity.json').read_text())
    perf=json.loads((REPORT/'throughput.json').read_text());t=perf['timings']
    assert v['status']=='PASS' and all(x['pass_'] for x in v['checks'].values())
    assert perf['status']=='PASS' and perf['optimizer_steps']==0 and perf['parameters_unchanged']
    assert json.loads((REPORT/'nonzero_recurrence_test.json').read_text())['status']=='PASS'
    changed=[k for k in v['checks'] if v['checks'][k]!=initial['checks'][k]]
    assert changed==['no_fitted_test_scaler_or_threshold']
    # Fresh repeat produced identical arrays despite the checker-only correction.
    for key,h in initial['artifacts'].items():
        path=ROOT/key;assert sha(path)==h
        new=ROOT/'data/phase_e2/verified'/path.name
        assert sha(new)==h
    for key,h in v['artifacts'].items():assert sha(ROOT/key)==h
    sources=json.loads((REPORT/'source_hashes.json').read_text())
    assert all(sha(ROOT/p)==h for p,h in sources.items())
    for folder in ('phase_d_v2','phase_e'):
        for line in (ROOT/'reports'/folder/'SHA256SUMS').read_text().splitlines():
            h,p=line.split('  ',1);assert sha(ROOT/p)==h
        assert not subprocess.check_output(['rtk','git','diff','d56efa6','--',f'reports/{folder}'],text=True).strip()
    for p in ('reports/phase_e2/architecture.json','reports/phase_e2/schema.json','scripts/phase_e2_common.py',
              'scripts/phase_e2_observer.py','scripts/phase_e2_schema.py'):
        assert subprocess.check_output(['rtk','git','show',f'0b669b0:{p}'])==(ROOT/p).read_bytes()
    assert not subprocess.check_output(['rtk','git','-C',str(OFFICIAL),'status','--porcelain'],text=True).strip()
    runs={p.stem.removesuffix('.launch'):json.loads(p.read_text()) for p in (REPORT/'logs').glob('*.launch.json')}
    assert all(r['returncode']==0 for r in runs.values())
    assert runs['schema_tests']['returncode']==0
    total=sum(r['wall_seconds'] for r in runs.values());assert total<1800
    # No training budget is chosen here.50 epochs below is an illustration only.
    nw=lambda n:max(0,n-63)
    train_batches=math.ceil(10*nw(4096)/128)*5
    val_batches=math.ceil(5*nw(4096)/128)*5
    extraction=25*5*4*5*nw(21504)
    tsb=json.loads((ROOT/'reports/phase_a_v4/manifest.json').read_text())
    smd=json.loads((ROOT/'reports/phase_a/smd_seal.json').read_text())
    lengths=[dict(file=r['file'],D=r['D'],N=r['N'],fit_windows=nw(r['fit_interval'][1]),test_windows=nw(r['N']-r['cutoff'])) for r in tsb]
    lengths += [dict(file=r['machine'],D=r['D'],N=r['N'],fit_windows=nw(r['audit_fit_interval'][1]),test_windows=nw(r['test_N'])) for r in smd]
    compute=dict(status='MEASURED_PILOT_WITH_CONDITIONAL_EXTRAPOLATIONS',pilot_total_process_wall_seconds=total,
        pilot_limit_seconds=1800,backend='official vanilla float32; GPU tensors, no custom CUDA extension',
        timing_configuration='D8,W64,embedding40,B128;2warmups/5forward;1warmup/3backward; zero optimizer steps',
        E_fit_hours_per_epoch_five_detectors=train_batches/t['forward_backward']['batches_per_second']/3600,
        E_validation_hours_per_epoch_five_detectors=val_batches/t['vanilla']['batches_per_second']/3600,
        E_fit_validation_hours_illustrative50epochs=50*(train_batches/t['forward_backward']['batches_per_second']+val_batches/t['vanilla']['batches_per_second'])/3600,
        E_assumption='10 clean train prefixes4096,5 validation prefixes4096,5detectors.50epoch illustration only; no epoch/config selection authorized.',
        G_synthetic_extraction_windows=extraction,G_synthetic_extraction_hours=extraction/t['observer']['decisions_per_second']/3600,
        G_assumption='25sources*5scenarios*4conditions*5detectors*(21504−64+1); includes prefix/history, no class selection.',
        real_lengths=lengths,real_total_test_windows=sum(r['test_windows'] for r in lengths),
        real_five_detector_extraction_hours_D8_proxy=5*sum(r['test_windows'] for r in lengths)/t['observer']['decisions_per_second']/3600,
        real_limitation='D8 throughput proxy only; actual D up to248, no real input benchmark or labels inspected.',
        F_measured_runtime=None,F_reason='Matched architecture/training not authorized; cannot claim measured F cost.',
        G_probe_fit_runtime=None,G_probe_reason='No logistic fit authorized; sample support and solver cost unmeasured.',
        total_EFG_runtime=None,total_reason='F and probe fitting unmeasured, training budget not frozen; not a complete160h cost certification.',
        optional_CUDA='NOT_RUN_NOT_REQUIRED',backend_selection_performance_based=False,
        observer_time_ratio=perf['observer_time_ratio'],long_runs_authorized=False)
    (REPORT/'compute.json').write_text(json.dumps(compute,indent=2)+'\n')
    compatibility=dict(implementation_name='improved official xLSTMAD implementation',
        source_url='https://github.com/Nyderx/xlstmad/tree/e8b56ba27352733bb83729e85b1d6196dca70c99',
        pinned_commit='e8b56ba27352733bb83729e85b1d6196dca70c99',dependencies={'xlstm':'2.0.5','lightning':'2.6.1'},
        optional_dependencies={'pytorch-lightning':'2.6.1','torchmetrics':'1.8.2','lightning-utilities':'0.15.2'},
        upstream_source_diff='',backend='vanilla',dtype='float32',
        config_overlay='Set all sLSTM dtype fields float32, no autocast. Public slstm_backend=vanilla. No layer/readout/equation changes.',
        common_boundary='ObservationWindows passes only internal dummy zeros to native dataset then discards labels; score/extract accept model,x only.',
        native_predict_caveat='predict_step expects reconstruction target, not anomaly labels. Common track scores x_hat against x and never passes dataset y as target.',
        native_test_caveat='test_step uses labels for AUROC only; not called by common feature/score extraction.',
        preprocessing='No scaler fitted by model/extractor. Future common scaler remains train-prefix-only under m0_protocol; none fitted in this pilot.',
        earlier_false_block='validity.json string scan matched threshold in no-threshold docstring. Only checker changed to executable AST calls; validity_verified.json authoritative. All other checks and saved arrays identical.',
        warnings='Native dataset torch.tensor(tensor) copy warnings retained; no patch.',
        v1_audit_immutable=True,original_v1_reproduction_claim=False)
    (REPORT/'compatibility.json').write_text(json.dumps(compatibility,indent=2)+'\n')
    status=dict(E2='PASS_BOUNDED_IMPLEMENTATION_AND_INSTRUMENTATION',validity_checks=40,schema_tests=7,
        nonzero_recurrence_test='PASS',primary_backend='vanilla_float32',CUDA_required=False,
        H2='NOT_TESTED',H3a='NOT_TESTED',H1_controlled_harm='STOP',H1_natural_harm='NOT_RUN',H1_harm_overall='UNRESOLVED',
        H4a='LOCKED',H4b='LOCKED',Phase_F='AWAITING_EXTERNAL_REVIEW',Phase_G='AWAITING_EXTERNAL_REVIEW',
        labels_extracted=False,scientific_checkpoints_trained=False,optimizer_steps=0,matched_LSTM_trained=False,
        H3b_run=False,natural_H1_run=False,all_prior_evidence_unchanged=True)
    (REPORT/'status.json').write_text(json.dumps(status,indent=2)+'\n')
    cells=v['checks']['observer_reference']['details']
    max_hidden=max(c['max_hidden_abs'] for c in cells);max_state=max(c['max_state_abs'] for c in cells)
    b=t['forward_backward'];o=t['observer'];f=t['vanilla']
    report=f'''# Phase E2 — PASS (bounded validity/instrumentation only)

**Improved official xLSTMAD implementation**, Nyderx/xlstmad
`e8b56ba27352733bb83729e85b1d6196dca70c99`; xlstm2.0.5 and lightning2.6.1.
Primary backend is preselected official **vanilla float32**, not a fallback
selected by anomaly/probe performance. No optional custom CUDA test was needed.
This is NOT reproduction of the original v1 TSB-AD-M implementation.

Pre-outcome amendment cfb981f; dependency/architecture/executable schema seal
0b669b0, both committed/pushed before the bounded pilot. Switch reason: v1 training
loss and scoring mixed sample/time coordinates, with repeated tail dataset windows.
No H2/H3 labels, probe results or anomaly performance were inspected to choose this
implementation. The v1 audit atd56efa6 and D-v2 controlled evidence are unchanged.

## Material architecture differences

| Component | Improved official configuration |
|---|---|
| Common pilot input | D8, W64, embedding40, model seed11 |
| Encoder / decoder | each [sLSTM,sLSTM,mLSTM] |
| Scalar layers / heads |4 layers ×4 heads;10 scalars/head, hidden40 |
| Scalar state | y,c,n,m each40 scalars per layer/window |
| Matrix layers |2 layers; inner80,4 heads×20; C20×20/head, n20×1/head |
| QKV projections |16 groups×5, distinct from4 memory heads |
| Trainable parameters |73,504 (v1 D8:78,080) |
| Readout | input D→40, full encoder→full decoder→GELU→40→D |
| Output / objective |[B,W,D], coordinate-aligned reconstruction MSE |
| Reset | fresh recurrent/conv state every window; full within-window decoder history |

No last-token bottleneck or repeated singleton decoder from v1. Actual four scalar
cell paths and resolved configs/parameter shapes are in architecture.json. The
upstream example uses W20/B32; our W64/B128 timing is the declared common diagnostic,
not an unchanged example benchmark. lr0.001 is recorded but no optimizer was created
or stepped. Vanilla executes all recurrent tensors in float32 without autocast.

## Validity and instrumentation results

All40 checks in validity_verified.json PASS. Seven schema tests and the independent
nonzero-recurrent-weight scalar fixture also PASS. Tests use only random unlabeled
observations and dummy/evaluator markers, not synthetic drift/anomaly classes.

| Check | Result |
|---|---|
| Output shape / native train and validation MSE coordinates | PASS;[131,64,8], exact loss agreement |
| Output and score batch permutation | PASS |
| B128+finalB3 score agreement | bitwise PASS on131 windows |
| B128+finalB1 score agreement | bitwise PASS on129 windows |
| B3/B1 repartition of131 windows | numerical PASS; max2.38e-7/1.19e-7, not bitwise |
| Native SlidingWindowDataset | N194,W64→131 exact chronological unique-index windows; no tail repeat |
| N=W / short input |1 window; common boundary rejects too-short input, no padding |
| Independent reset / no carry | output and feature reset bitwise PASS |
| Model, scalar and schema prefix causality | PASS, including full-window decoder |
| No test-fitted scaler/threshold | PASS; no fit in common score/feature path |
| Evaluator label isolation | PASS; common API receives model,x only |
| Observer OFF/ON output/score | bitwise identical; RNG unchanged |
| Scalar hidden / final reference states | max{max_hidden:.3g}/{max_state:.3g}; finite float32 |
| Full model parallel / within-window recurrent steps | max5.66e-7, numerical PASS |
| Feature batch partition | max1.19e-7, numerical PASS |
| Parameters/buffers after tests and backward pilot | unchanged; no scientific checkpoint saved |

Numerical PASS uses the unchanged atol1e-5/rtol1e-4; exact equality is separately
reported. Batch partition is not claimed bitwise identical. Within-window step
tests are not H3b or cross-window carry. Nonzero recurrent weights occur only in
an isolated CPU unit fixture, not in the detector; this addresses the triviality
of testing only the untrained detector's zero-initialized recurrent matrices.

The initial reporting checker falsely matched the word threshold in extract's
"no ... threshold" docstring and marked a block. It now checks executable AST
calls. The first log/validity.json remain intact; the fresh rerun changed no other
check and produced identical saved arrays. No detector, schema, backend, tolerance
or observation fixture was changed. This was a checker error, not an implementation
repair or waived scientific gate.

## Executable common18 schema

The same18 names are frozen in phase_e2_schema.py/schema.json: hidden4, input5,
retention5, c/n memory4. Actual cells are encoder.blocks.0/1 and decoder.blocks.0/1
scalar cells, each with4 heads. Compute per-head moments/quantiles, then equal
heads/layers; no learned weights or mLSTM-only columns. Population std, linear
q10/q90, relative norm denominator norm(previous)+1e-8. Hidden and gate differences
use t−1; **decoder uses its real within-window previous state**, not singleton zero.
Only a genuine first timestep uses zero state. xlstm2.0.5 caps effective i/f at1;
the observer follows those exact equations and gate-slot order, not projection names.

18 base columns + trailing mean/std/OLS slope over4/8/16/32 decisions→234 internal
columns; hidden52/gates130/memory52; history+internal248. Incomplete history is NaN
warmup, excluded rather than padded or fitted. No feature scaler or logistic model
was fitted. Equal semantic capacity does not establish H2/H3 signal or complete
equivalence with an unimplemented matched LSTM. Labels have not been extracted.

## Bounded throughput and resource use

Random float32 D8/W64/B128;2 warmups and5 timed forward batches;1 warmup and3
timed backward batches; zero optimizer steps. NVIDIA GB10, PyTorch2.13.0+cu130,
CUDA13.0, cuDNN92000. Vanilla uses normal GPU tensor operations, no custom sLSTM CUDA.

| Mode | batches/s | decisions/s | GPU allocated/reserved peak MiB |
|---|---:|---:|---:|
| Vanilla score |{f['batches_per_second']:.3f}|{f['decisions_per_second']:.3f}|{f['peak_allocated_bytes']/2**20:.2f}/{f['peak_reserved_bytes']/2**20:.2f}|
| Score + observer |{o['batches_per_second']:.3f}|{o['decisions_per_second']:.3f}|{o['peak_allocated_bytes']/2**20:.2f}/{o['peak_reserved_bytes']/2**20:.2f}|
| Forward + backward, no optimizer |{b['batches_per_second']:.3f}|N/A|{b['peak_allocated_bytes']/2**20:.2f}/{b['peak_reserved_bytes']/2**20:.2f}|

Observer time ratio{perf['observer_time_ratio']:.3f}×, +{(perf['observer_time_ratio']-1)*100:.1f}%.
Peak CPU process RSS {perf['cpu_process_peak_rss_kib']/2**20:.3f}GiB; on unified-memory
GB10 this is process RSS, not independent total device memory accounting. GPU peaks
are allocator per-process maxima with fixture tensors resident, not incremental
observer memory. Pilot body{perf['total_seconds']:.2f}s; cumulative process walls
including first checker failure/verification/tests{total:.2f}s, well below1800s.
Five timing iterations are a short throughput sample, not a production benchmark.

Conditional compute examples (not chosen scientific training budgets):5 detectors,
10 clean4096 fit prefixes gives{compute['E_fit_hours_per_epoch_five_detectors']:.3f}h
forward/backward per epoch;5 validation prefixes gives
{compute['E_validation_hours_per_epoch_five_detectors']:.3f}h/epoch. Illustrative50epochs
fit+validation≈{compute['E_fit_validation_hours_illustrative50epochs']:.2f}h before
optimizer/I/O overhead. G extraction accounting25sources×5scenarios×4conditions×
5detectors×21441 decisions={extraction:,}, ≈{compute['G_synthetic_extraction_hours']:.2f}h.
Sealed14-real-series test lengths total{compute['real_total_test_windows']:,} W64 windows;
five passes≈{compute['real_five_detector_extraction_hours_D8_proxy']:.2f}h using only
the measured D8 proxy (actual D up to248). F matched-LSTM and G logistic runtime
are unmeasured; complete E/F/G cost and the160h envelope cannot yet be certified.
No optional CUDA/reference speed gate is required because vanilla is primary.

## Scope and handoff

E2 PASS establishes bounded implementation/instrumentation validity, not detector
performance, scalar signal, H3a superiority or trained-state parity for all possible
weights. No scientific checkpoint training, optimizer updates, logistic probe,
matched LSTM, H3b/H4/natural-H1 harm or learned mechanism was run.
H1 controlled STOP; natural NOT_RUN; overall UNRESOLVED. H4 remains LOCKED.
Return for external review before F/G; no next-phase execution is automatic.

See architecture.json, schema.json, validity_verified.json, throughput.json,
compute.json, compatibility.json, environment.json, source_hashes.json,
dependency_install.json, commands.txt and logs/. Original upstream files are immutable.
'''
    (REPORT/'README.md').write_text(report)
    (REPORT/'final_verification.json').write_text(json.dumps(dict(status='PASS',validity_checks=40,schema_tests=7,
        scalar_nonzero_reference='PASS',frozen_schema_and_observer_unchanged=True,upstream_dependency_hashes_unchanged=True,
        v1_and_Dv2_report_seals_unchanged=True,checker_only_change=changed,rerun_diagnostic_arrays_bitwise_identical=True,
        no_labeled_extraction=True,no_optimizer_updates=True),indent=2)+'\n')
    print('E2 PASS;40validity/7schema/nonzero reference; all prior evidence unchanged; process walls',total)
