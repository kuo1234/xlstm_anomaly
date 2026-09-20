# Recommendation

## Decision

**GO for engineering use of the optimized observer on the validated Spark
CUDA overlay, with the existing V0 observer retained as an audit/canary
reference.** Do not alter Phase-F/G scientific artifacts or rerun G1 as part
of this change.

The target of >2x observer speedup is exceeded: 4.68x at B=128 and 4.72x on
the bounded cache-style workload. The optimized observer is numerically
equivalent to V0 for the complete four-cell traces and common18 under the
existing tolerance.

## Answers to the engineering questions

1. **Dominant bottleneck:** duplicate scalar recurrence, expressed as a Python
   timestep loop for each of four cells.
2. **Important synchronization:** per-step `bool(torch.all(...))`, plus
   `allclose`, `max`, and `isfinite().all()` parity checks. They account for
   hundreds of stream synchronizations and amplify launch overhead.
3. **Duplicate replay:** yes; it is the main cost (`0.03466 s` of `0.04321 s`
   V0 B=128 observer time).
4. **Selected optimization:** capture native CUDA `all_states` at `_impl()` and
   reconstruct only gates in a batched `(B,T)` operation; use an audit-free
   semantic common18 reduction.
5. **Rejected alternatives:** deferred Python replay does not remove the
   recurrence; a custom gate-cache CUDA ABI is invasive; compile/graphs/streams
   had no demonstrated end-to-end win; multiple CUDA processes are not
   justified by a launch-bound single-GPU workload.
6. **Equivalence:** all B=1/8/128 trace fixtures pass; maximum trace error is
   `1.73e-6`, common18 `2.38e-7`, with zero frozen-tolerance failures.
7. **Baseline:** 2,958 decisions/s at B=128 in the final comparison (2,962 in
   the initial profile).
8. **Optimized:** 13,856 decisions/s at B=128; 17,198 at B=256; 17,146 at
   B=512.
9. **End-to-end:** 2,917 -> 13,767 decisions/s on the fixed 2,048-window
   extraction/cache workload, 4.72x.
10. **Future extraction impact:** if the same observer/replay mix dominates a
    larger job, expect roughly 4--5x on the observer component. CPU window
    construction, CANDI, host transfers, and file I/O will reduce whole-job
    speedup; no exact G1 wall-time claim is made.
11. **Additional parallelism:** not currently useful. Optimize batching and
    keep one GPU owner; use CPU workers only if a future end-to-end profile
    shows input or cache I/O dominating.
12. **mLSTM support:** the capture seam can be reused, but mLSTM needs a
    separate state/matrix-memory adapter and schema. The current fast adapter
    fails closed on non-sLSTM layouts.
13. **Residual risks:** `_impl` and CUDA state layout are xLSTM 2.0.5 internal
    interfaces; upstream changes require re-running the full trace-equivalence
    canary. The fast path omits hot-path audit checks by design.

## Recommended next step

Integrate the optimized observer only in a future, separately reviewed
engineering extraction path. Before any scientific use, run V0 and optimized
observers on fixed random and frozen-checkpoint canary batches, compare full
trace/common18 tensors, and seal the environment/backend hashes. Do not use
this branch to alter G1 conclusions. A future mLSTM feature project should be
planned as a new adapter/schema review rather than silently extending
common18.
