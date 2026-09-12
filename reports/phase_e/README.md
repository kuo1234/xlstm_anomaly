# Phase E — BLOCKED, not a hypothesis STOP

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
| Observer OFF | 10.736 | 1374.247 |
| Observer ON | 7.438 | 952.012 |
| Forward+backward, no optimizer | 3.187 | N/A |

Observer cost ratio 1.444× (44.4% time overhead).
Observer peak allocated/reserved 151.02/186.00 MiB;
backward 478.74/546.00 MiB.
These are window-evaluation rates, NOT valid native streaming decisions/sec, because
the native score mapping fails. Native CUDA throughput and CUDA/reference slowdown N/A.
Sum of bounded process walls 47.61s (<30min), including unsuccessful diagnostics;
no long run. First reference test had a noncontiguous test-slice error; only fixture
handling was corrected, original failed log preserved.

Illustrative five-detector50-epoch synthetic fit backward cost
6.89 GPU workload hours, validation
1.02h; full synthetic extraction accounting
53,602,500 windows ≈15.64h.
Actual sealed14-real-series test windows:718,999; five-detector
pass ≈1.05h using D8 proxy only.
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
