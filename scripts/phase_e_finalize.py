"""Phase E reporting/sealing only; no fitting and no Phase D recomputation."""
import json,math,subprocess,sys
from pathlib import Path
from phase_e_common import ROOT,REPORT,OFFICIAL,sha
from phase_e_schema import BASE_COLUMNS,EXPANDED_COLUMNS

if __name__=='__main__':
    pilot=json.loads((REPORT/'reference_pilot.json').read_text());t=pilot['timings']
    source=json.loads((REPORT/'source_hashes.json').read_text())
    assert all(sha(ROOT/p)==h for p,h in source.items())
    oldseal=ROOT/'reports/phase_d_v2/SHA256SUMS'
    for line in oldseal.read_text().splitlines():
        h,p=line.split('  ',1);assert sha(ROOT/p)==h
    assert not subprocess.check_output(['rtk','git','diff','4f0ad09','--','reports/phase_d_v2'],text=True).strip()
    assert not subprocess.check_output(['rtk','git','-C',str(OFFICIAL),'status','--porcelain'],text=True).strip()
    for p in ('reports/phase_e/prospective.md','scripts/phase_e_schema.py'):
        assert subprocess.check_output(['rtk','git','show',f'f5ac068:{p}'])==(ROOT/p).read_bytes()
    launch={p.stem.removesuffix('.launch'):json.loads(p.read_text()) for p in (REPORT/'logs').glob('*.launch.json')}
    assert launch['schema_tests']['returncode']==0
    assert launch['reference_pilot_fixed']['returncode']==0
    assert launch['reference_pilot']['returncode']==1  # retained harness-only fixture error
    total=sum(r['wall_seconds'] for r in launch.values());assert total<1800
    tsb=json.loads((ROOT/'reports/phase_a_v4/manifest.json').read_text())
    smd=json.loads((ROOT/'reports/phase_a/smd_seal.json').read_text())
    count=lambda n:max(0,n-63)
    real=[dict(file=r['file'],D=r['D'],N=r['N'],fit_windows=count(r['fit_interval'][1]-r['fit_interval'][0]),
        test_windows=count(r['test_interval'][1]-r['test_interval'][0])) for r in tsb]
    real += [dict(file=r['machine'],D=r['D'],N=r['N'],fit_windows=count(r['audit_fit_interval'][1]),
        test_windows=count(r['test_N'])) for r in smd]
    synthetic_training_windows=10*count(4096)
    train_batches=math.ceil(synthetic_training_windows/128)*50*5
    validation_batches=math.ceil(5*count(4096)/128)*50*5
    extraction=25*5*4*5*count(21504)
    compute=dict(status='ILLUSTRATIVE_ONLY_E_BLOCKED',measured_backend='vanilla float32, D8 W64 embedding40 B128',
        pilot_total_process_wall_seconds=total,limit_seconds=1800,
        E_training_assumption='Illustrative 50-epoch cap, five detectors, ten clean fit source prefixes; NOT an approved F/G training plan.',
        E_synthetic_forward_backward_hours=train_batches/t['forward_backward_no_optimizer']['batches_per_second']/3600,
        E_synthetic_validation_hours=validation_batches/t['observer_off']['batches_per_second']/3600,
        G_extraction_assumption='Upper accounting example:25 sources*5 scenarios*4 conditions*5 detectors; all21504 samples, W64 stride1, no labels.',
        G_synthetic_windows=extraction,G_synthetic_observer_hours=extraction/t['observer_on']['decisions_per_second']/3600,
        real_lengths=real,real_test_windows=sum(r['test_windows'] for r in real),
        real_five_detector_observer_hours_D8_proxy=5*sum(r['test_windows'] for r in real)/t['observer_on']['decisions_per_second']/3600,
        real_proxy_limitation='Only D8 timed; actual D differs, so this is not validated real-data throughput.',
        F_matched_LSTM_measured_runtime=None,F_reason='Matched model/training not authorized; architecture/readout match unresolved.',
        G_logistic_runtime=None,G_reason='No probe fit authorized; labeled cohort/fit size not measured.',
        native_CUDA_throughput=None,native_to_reference_slowdown=None,
        native_reason='CUDA link failure; cannot certify the >5x fallback-cost gate.',
        observer_overhead_ratio=t['observer_overhead_ratio'],long_run_authorized=False)
    schema=dict(base_columns=BASE_COLUMNS,expanded_columns=EXPANDED_COLUMNS,
        counts=dict(base=18,combined=234,hidden=52,gates=130,memory=52,history=14,history_plus_combined=248),
        scalar_cells=['lstm_encoder.blocks.1.xlstm.slstm_cell','lstm_decoder.blocks.1.xlstm.slstm_cell'],
        pooling='Equal within-head moments, then equal heads, then equal scalar layers. Final invocation per cell.',
        effective_gates='i=exp(i_raw-m_new);f=exp(m_prev+logsigmoid(f_raw)-m_new)',
        memory='c/n; no tanh substitution, no mLSTM flattening',
        delta_origin='Own cell-call zero state; final decoder singleton has zero previous state.',
        gate_warning='stabilized retention need not have ordinary LSTM sigmoid interpretation; first-step retention may exceed1.',
        relative_delta_warning='zero previous memory yields norm(u)/1e-8; finite but potentially large, not clipped.',
        decoder_warning='decoder singleton dynamics are not a temporal trajectory of physical input samples.',
        window_warmup='external trailing summaries require complete history; NaN until enough decisions, excluded not zero-padded',
        executable_sha256=sha(ROOT/'scripts/phase_e_schema.py'),freeze_commit='f5ac068',labels_extracted=False,
        feature_availability='Reference available; confirmatory extraction blocked pending native/readout validity')
    (REPORT/'schema.json').write_text(json.dumps(schema,indent=2)+'\n')
    (REPORT/'compute.json').write_text(json.dumps(compute,indent=2)+'\n')
    status=dict(Phase_E='BLOCKED',H3a='NOT_TESTED_IMPLEMENTATION_BLOCKED',required_scalar_features_missing=False,
        reference_observation='PASS',native_CUDA_reference_parity='NOT_ESTABLISHED_LINK_FAILURE',
        native_score_batch_permutation='FAIL',native_score_batch_partition='FAIL',
        H1_controlled_harm='STOP',H1_natural_harm='NOT_RUN',H1_harm_overall='UNRESOLVED',H4a='LOCKED',H4b='LOCKED',
        no_probe_fit=True,no_matched_LSTM_training=True,no_cross_window_carry=True,no_optimizer_steps=True,
        D_v2_unchanged=True,original_xlstmad_unchanged=True,dependency_xlstm_unchanged=True)
    (REPORT/'status.json').write_text(json.dumps(status,indent=2)+'\n')
    packages=json.loads((REPORT/'environment.json').read_text())['packages']
    compatibility=dict(official_repo='https://github.com/Nyderx/xlstmad',
        official_commit='3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6',xlstm='2.0.3',
        upstream_source_diff='',reference_overlay='phase_e_common.config_overlay: vanilla backend and all sLSTM dtype fields float32 only',
        python_headers='libpython3.12-dev 3.12.3-1ubuntu0.17 arm64, downloaded and extracted under data/phase_e only; no system install',
        header_url='http://ports.ubuntu.com/ubuntu-ports/pool/main/p/python3.12/libpython3.12-dev_3.12.3-1ubuntu0.17_arm64.deb',
        header_sha256=sha(ROOT/'data/phase_e/libpython3.12-dev_3.12.3-1ubuntu0.17_arm64.deb'),
        build_env=dict(MAX_JOBS=2,XLSTM_EXTRA_INCLUDE_PATHS='data/phase_e/python_headers/usr/include/python3.12:data/phase_e/python_headers/usr/include'),
        wheel_urls=['https://pypi.org/project/xlstm/2.0.3/','https://pypi.org/project/TSB-AD/1.5/','https://pypi.org/project/ninja/1.11.1.4/'],
        environment_deviations=dict(python='3.12.3; upstream README3.11',pandas=f'{packages.get("pandas")}; upstream2.2.3; not used by observation fixtures',
            pysdtw='Not installed/imported; DTW track excluded. No claim of full historical environment reproduction.'),
        first_pilot_fixture_error='Noncontiguous slice passed to exact native view; fixed only the test to score original contiguous singleton outputs; failed log retained.',
        native_attempts=['native_backend.json','headers_native_backend.json','headers_float32_backend.json'])
    (REPORT/'compatibility.json').write_text(json.dumps(compatibility,indent=2)+'\n')
    code={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'scripts').glob('phase_e*.py'))}
    code['tests/test_phase_e_schema.py']=sha(ROOT/'tests/test_phase_e_schema.py')
    (REPORT/'code_hashes.json').write_text(json.dumps(code,indent=2)+'\n')
    p=t['observer_on'];b=t['forward_backward_no_optimizer']
    text=f'''# Phase E — BLOCKED, not a hypothesis STOP

Pinned xLSTMAD `v1-submission-version` at
`3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6`, with required xlstm2.0.3.
H1 reporting correction was committed/pushed at839cc08; schema/pilot freeze atf5ac068.
H1 controlled=STOP, natural=NOT_RUN, overall=UNRESOLVED; H4 remains LOCKED.
All D-v2 files and results remain unchanged.

## Architecture actually resolved

Native script: W50, embedding40, B128, lr0.005; class defaults W100/hidden20
are not the script configuration. Common diagnostic: W64, D8, same embedding40.
Encoder and decoder each have [mLSTM,sLSTM,mLSTM]:4 matrix and2 scalar cells total.
sLSTM has4 heads ×10 hidden scalars; states y,c,n,m each40 scalars/window.
mLSTM projects40→160 and splits into80+80;4 memory heads ×20 dimensions;
per-head C is20×20, n is20×1 and stabilizer scalar. QKV projections use16 blocks
of5, not16 recurrent memory heads. Scalar FFN expands to64 (rounded), GELU.
Trainable parameters D8:78,080; identical count from native metadata-only construction
and reference instantiation. Native metadata skipped kernel loading, not a forward PASS.

Input projection D→40; encoder runs the full window, keeps only last embedding.
Decoder applies its complete three-block stack W times to singleton embeddings,
feeding its embedding output back to itself; GELU+linear40→D forms reconstruction.
It does NOT pass recurrent/conv state between decoder calls or input windows.
Each decoder scalar call has sequence length1, so no within-call temporal history.
Raw model output is [W,B,D]; target is [B,W,D]. Original training and scoring
both flatten with view(-1,W*D) without a time/batch transpose.

## Two independent blockers

1. **Native score batch permutation FAIL**: W64 max absolute difference0.08668685;
   batch partition difference0.05854225; native-W50 reference difference0.03026044.
   Model tensor permutation itself is bitwise PASS. A CPU marker fixture proves
   changing only window3's output changes window0's score via native flattening.
   This is an original readout/loss-layout defect, not an observer effect. No fix applied.
2. **Native CUDA/reference parity NOT ESTABLISHED**: initial compile lacked Python.h.
   Headers were extracted locally and added via external include paths. CUDA13
   linking then failed on undefined SLSTMPointwiseForward<false/true>, both native
   bfloat16 and explicit float32 configs. No cell/kernel source was patched.

The original multivariate dataset also returns N samples and repeats the final
window over the last W positions; those are not independent causal endpoint
decisions. The native wrapper fits MinMaxScaler on test scores. Both behaviors
remain documented, not silently carried into a common causal track or corrected here.

## What passed (reference-only, not native reproduction)

Observer OFF/ON outputs and native-shaped scores: bitwise identical.
Scalar hidden/final state replay: maximum differences5.96e-8/2.98e-8.
Finite scalar states/common18-column summary: PASS. Independent window reset,
batch permutation of raw outputs, fixed-prefix future perturbation: bitwise PASS.
Shorter encoder prefix: max8.34e-7; encoder parallel/within-window step:max2.15e-6;
mLSTM parallel/recurrent:max3.58e-6, all within frozen atol1e-5/rtol1e-4.
Nonzero recurrent-weight CPU unit fixture also passes (5.96e-8); detector random
initial recurrent matrices were not modified. These tests cannot substitute for
the missing native CUDA comparison. No cross-window carry or H3b was run.

All four required scalar quantities are observable in the reference; none was
substituted with mLSTM-only statistics. Effective roles follow cell concatenation,
not the reversed fgate/igate projection attribute names. Schema18→234 columns,
history+combined248, frozen before any labeled extraction; no labels extracted.
Five schema tests pass, including zero-origin deltas, equal pooling, missing-feature
rejection, rolling causality/warmup and batch permutation. See schema.json for
decoder and large zero-origin relative-delta interpretation limitations.

## Bounded throughput / compute

Reference float32 D8 W64 B128, random data, no optimizer updates:

| Mode | batches/s | window evaluations/s |
|---|---:|---:|
| Observer OFF | {t['observer_off']['batches_per_second']:.3f} | {t['observer_off']['decisions_per_second']:.3f} |
| Observer ON | {p['batches_per_second']:.3f} | {p['decisions_per_second']:.3f} |
| Forward+backward, no optimizer | {b['batches_per_second']:.3f} | N/A |

Observer cost ratio {t['observer_overhead_ratio']:.3f}× ({100*(t['observer_overhead_ratio']-1):.1f}% time overhead).
Observer peak allocated/reserved {p['peak_allocated_bytes']/2**20:.2f}/{p['peak_reserved_bytes']/2**20:.2f} MiB;
backward {b['peak_allocated_bytes']/2**20:.2f}/{b['peak_reserved_bytes']/2**20:.2f} MiB.
These are window-evaluation rates, NOT valid native streaming decisions/sec, because
the native score mapping fails. Native CUDA throughput and CUDA/reference slowdown N/A.
Sum of bounded process walls {total:.2f}s (<30min), including unsuccessful diagnostics;
no long run. First reference test had a noncontiguous test-slice error; only fixture
handling was corrected, original failed log preserved.

Illustrative five-detector50-epoch synthetic fit backward cost
{compute['E_synthetic_forward_backward_hours']:.2f} GPU workload hours, validation
{compute['E_synthetic_validation_hours']:.2f}h; full synthetic extraction accounting
{compute['G_synthetic_windows']:,} windows ≈{compute['G_synthetic_observer_hours']:.2f}h.
Actual sealed14-real-series test windows:{compute['real_test_windows']:,}; five-detector
pass ≈{compute['real_five_detector_observer_hours_D8_proxy']:.2f}h using D8 proxy only.
These are unapproved workload extrapolations, not training plans or measurements
on real datasets. F matched-LSTM and G logistic runtime are unmeasured/N/A;
native/reference >5× gate cannot be assessed. E/F/G total is therefore unresolved.

## Minimal next steps requiring external review

Keep E blocked. A separate compatibility proposal must resolve native kernel
linking without changing equations, then establish native float32 parity.
A separately authorized readout/dataset alignment audit must define whether a
corrected variant is scientifically acceptable; transposing output changes the
original training loss/scoring and cannot be called unchanged reproduction.
No such detector fix, retraining, probe, matched LSTM, natural-SMD harm, H4,
H3b, rollback, dual memory or learned gate was run. Do not lower any tolerance
or practical margin, and do not switch xLSTMAD commits.

Artifacts: architecture.json, native_architecture_metadata.json, reference_pilot.json,
independent_diagnostics.json, schema.json, compute.json, compatibility.json,
source_hashes.json, environment.json, commands.txt and logs/.
'''
    (REPORT/'README.md').write_text(text)
    print('Phase E BLOCKED; reports finalized; all D-v2 seals unchanged; pilot walls',total)
