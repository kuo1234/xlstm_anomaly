# Phase C v2: paper fidelity versus released-artifact fidelity

Pre-execution amendment to 499de38, authorized by external review. Historical
Phase C reports remain unchanged. No new SMD_2-1 execution outcome has been
inspected at amendment time. Author caches previously inspected are lineage
evidence only, never experimental results.

## C1-P — paper fidelity

Report paper, author-committed cache, and local native execution separately for
each of the six seed0 machine/alpha rows, with absolute pairwise discrepancies.
Per comparison MATCH means both AUROC and native trapezoidal PR-AUC differ by
at most 0.02 absolute; otherwise MISMATCH. Attribution of paper/checkpoint/cache
lineage remains UNRESOLVED_LINEAGE unless independently established. Neither
tuning nor retraining nor changing initialization RNG to chase agreement is
permitted. Paper mismatch is not alone an operational-baseline stop condition.

## C1-R — released-artifact operational fidelity

The primary operational baseline is immutable CANDI commit
28c9679e503832f59e351208cde63657fcb51cad, the already sealed released pretrained
checkpoint for each machine, official preprocessing and release-default
checkpoint evaluation (TRAIN.ENABLE=False). FPM, SANA, losses, optimizer,
batching, selection, update steps, counters, score ordering and native defects
remain untouched. Use the existing reports/phase_c/environment.json environment
and author scripts, recording resolved configuration and seed0. No code
compatibility patch is currently needed. Environment drift must be investigated
before execution, not silently accepted.

Prospective bounded gates and ordering:

1. Run two additional fresh SMD_1-8 alpha0.5 release-default seed0 executions.
   Require bitwise equality of full score arrays and their hashes, native
   metrics, final canonical model-state hash and update count against the
   original run. Require identical candidate IDs, commit IDs, update timing and
   per-step model hashes between the two instrumented replays. The original
   uninstrumented run has no stable-ID trace; do not invent one. Initial model
   and RNG fingerprints must agree between new replays. Any failure STOPs
   expansion, without changing RNG or TRAIN.ENABLE.
2. Only after replay PASS, execute SMD_2-1 alpha0.5, 1, 5, seed0, once each from
   the same released initial artifact. Require complete finite native scores,
   unchanged baseline invariants and auditable update trajectory. These single
   executions do not establish multi-seed or cross-hardware reproducibility.
3. On SMD_1-8 alpha5 run a native observed control and native label-permuted
   counterpart from identical observations/checkpoint/global RNG. A separate
   local RNG permutes only the adapter's test_labels argument; retain true
   evaluator labels and never permute observations. Require exact scores,
   selections/commit IDs, update timing, per-step and final model hashes.
   Diagnostic anomaly counters alone may differ. Any behavioral difference
   STOPs. Preserve the existing label-isolated overlay as the independent
   scientific audit; native permutation invariance does not imply a label-free
   native API.

C1-R PASS requires all three gates plus immutable artifact/environment checks.
Otherwise INVESTIGATE (or STOP on behavioral instability/leakage). A PASS can
justify recommending five-seed replication for external authorization, but does
not authorize executing it. A C1-P mismatch remains visible even with C1-R PASS.

## Unchanged limitations and locked work

Preserve variable-final-batch offset misindexing, admission counter versus
committed/optimizer-exposure discrepancy, moderate mask overwrite, current-SANA
representation dependence and inactive USE_FPM=False iteration issue. Stable
external IDs, not native counters, determine scientific contamination counts.
Passive observers may record but never correct these behaviors. Zero-update
contamination remains N/A. Existing independent overlay is unchanged.

No five-seed replication, Phase D/H1 interventions, xLSTM/LSTM, probes, H4/delay
or H3b is authorized. Commit and push this amendment before the bounded runs;
commit/push their versioned evidence and return for external review afterward.
