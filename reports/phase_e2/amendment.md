# Phase E2 pre-outcome implementation amendment — 2026-09-13

User-authorized switch solely because v1 implementation validity failed before
H2/H3 labels or results were observed. Immutable audit: d56efa6; no v1 files,
results, loss, dataset or CUDA repair. This is NOT a performance-driven selection.

Pin Nyderx/xlstmad e8b56ba27352733bb83729e85b1d6196dca70c99;
xlstm==2.0.5, lightning==2.6.1. Name: **improved official xLSTMAD implementation**,
not reproduction of original v1 TSB-AD-M. Confirmatory slstm_backend=vanilla,
float32, no autocast; CUDA is optional and its failure cannot block vanilla.
No CUDA attempt is needed in this bounded phase.

Freeze audit configuration D8, W64, embedding40, lr0.001 (improved default),
model seed11, fixture torch generator710, B128/3/1 and permutations. No parameter
search. Resolve actual architecture: encoder/decoder both [sLSTM,sLSTM,mLSTM],
full-window decoder, not v1 singleton rollout. All actual scalar cells contribute
equally by head/layer. Keep18 semantic features and18→234 causal rolling columns;
decoder differences use real within-window previous state. No matrix substitutions.
Executable E2 schema and dependency/architecture hashes must be committed before
any labeled extraction. Neither labels nor scientific probe outputs are authorized.

Validity gates: output[B,W,D], coordinate-aligned native MSE, batch permutation/
partition and B128/3/1 score invariance, exact chronological N−W+1 windows without
tail repetition, no recurrent carry, window reset, prefix causality, no test-fitted
scaler/threshold in common path, observation-only model/feature API. Native test_step
uses labels for evaluator metrics only; common extraction must not call it.

Instrumentation: observer OFF/ON bitwise on same deterministic backend; float32
reference atol1e-5/rtol1e-4 (unchanged); finite states, hidden/final state recurrence,
prefix/reset/batch tests and schema warmup. Batch partition and numerical reference
are assessed at those frozen tolerances; any failure is an implementation blocker,
not permission to relax tolerance. Report exact-equality separately.

Random unlabeled fixtures only. <=1800 seconds cumulative bounded pilot process
time, 2 warmups/5 timed forward batches, 1 warmup/3 forward-backward batches with
zero optimizer steps. Report vanilla throughput, observer overhead, allocated/
reserved GPU and process CPU peak memory; E/F/G extrapolations distinguish measured
from unavailable costs. No scientific checkpoints, optimizer updates, logistic
probes, matched LSTM, H3b/H4/natural-H1, rollback or learned mechanisms. Return for
external review before F/G. H1 thresholds/statistics/datasets unchanged.
