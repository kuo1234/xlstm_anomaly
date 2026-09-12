# Phase C v2 — released-artifact fidelity

C1-P: **MISMATCH**, paper/checkpoint/cache attribution **UNRESOLVED_LINEAGE**.
C1-R: **PASS for the authorized bounded seed0 checks**. Recommend five-seed
replication for external review; it has NOT been authorized or executed.
Phase D and all other modeling experiments remain locked.

## Official reproduction

Pre-outcome amendment commit: a8e07307dd6db8361c2ad5503eb13be5c55da55f. It was pushed before either replay
and before any new SMD_2-1 execution outcome. The pinned official checkout and
all historical Phase C report hashes were verified unchanged. No compatibility
patch, retraining, RNG manipulation to chase metrics, or hyperparameter tuning.
Official TRAIN.ENABLE=False checkpoint path and author scripts are unchanged.
Additional runner guards assert checkpoint hashes and reject TRAIN.ENABLE=True;
these checks do not change configuration. Environment versions match the prior
frozen environment. Commands, resolved configs, artifact hashes, GPU timings,
allocator peaks and stdout/stderr are retained per run.

| Machine | alpha | Paper AUROC / PR-AUC | Author cache (lineage only) | Local native |
|---|---:|---:|---:|---:|
| SMD_1-8 | 0.5 | 0.872000 / 0.432000 | 0.866576 / 0.447760 | 0.852404 / 0.438389 |
| SMD_1-8 | 1.0 | 0.872000 / 0.434000 | 0.853216 / 0.438935 | 0.853212 / 0.438938 |
| SMD_1-8 | 5.0 | 0.867000 / 0.423000 | 0.868101 / 0.449996 | 0.868101 / 0.449996 |
| SMD_2-1 | 0.5 | 0.725000 / 0.319000 | 0.691252 / 0.306374 | 0.691252 / 0.306373 |
| SMD_2-1 | 1.0 | 0.711000 / 0.314000 | 0.710918 / 0.314446 | 0.710935 / 0.314461 |
| SMD_2-1 | 5.0 | 0.780000 / 0.348000 | 0.779845 / 0.347811 | 0.774139 / 0.331829 |

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

Measured seven-run native-entry wall time: 184.506 s. Peak allocated/reserved GPU memory: 2.523 / 3.340 GiB.
