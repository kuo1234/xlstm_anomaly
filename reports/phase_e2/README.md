# Phase E2 — PASS (bounded validity/instrumentation only)

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
| Scalar hidden / final reference states | max5.96e-08/5.96e-08; finite float32 |
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
| Vanilla score |23.993|3071.052|150.81/184.00|
| Score + observer |12.819|1640.842|169.99/208.00|
| Forward + backward, no optimizer |6.350|N/A|641.88/654.00|

Observer time ratio1.872×, +87.2%.
Peak CPU process RSS 2.101GiB; on unified-memory
GB10 this is process RSS, not independent total device memory accounting. GPU peaks
are allocator per-process maxima with fixture tensors resident, not incremental
observer memory. Pilot body17.79s; cumulative process walls
including first checker failure/verification/tests49.37s, well below1800s.
Five timing iterations are a short throughput sample, not a production benchmark.

Conditional compute examples (not chosen scientific training budgets):5 detectors,
10 clean4096 fit prefixes gives0.069h
forward/backward per epoch;5 validation prefixes gives
0.009h/epoch. Illustrative50epochs
fit+validation≈3.91h before
optimizer/I/O overhead. G extraction accounting25sources×5scenarios×4conditions×
5detectors×21441 decisions=53,602,500, ≈9.07h.
Sealed14-real-series test lengths total718,999 W64 windows;
five passes≈0.61h using only
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
