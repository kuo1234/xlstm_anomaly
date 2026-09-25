# M1-A execution handoff

## Status and scope

The protocol amendment first recorded the result-blind status
`M1_SMD_PROTOCOL_READY — IMPLEMENTATION_PENDING` before any M1 model forward.
The final machine-readable preflight now reports
`M1_SMD_READY_FOR_STAGE1_EXECUTION`, and the independent review reports
`M1_IMPLEMENTATION_RESULT_BLIND_PASS`. This handoff does not launch the
28-machine experiment. No Stage-1 detector result, test-label read, or anomaly
metric was produced during this implementation/preflight task.
ZERO_SHOT_NOT_STARTED.

## Data and provenance already checked

- The pinned manifest has 84 valid expected SHA-256/byte-count entries for 28
  train, test-observation, and test-label paths. The implementation preflight
  checks their manifest syntax and coverage without opening test-label files.
- The 56 train/test observation files are content-hash verified, finite, and
  match the manifest shapes and D=38 schema across all 28 machines.
- Raw test-label files are outside every M1 preprocessing, fit, validation,
  calibration, and scoring path. Their expected hashes are retained as
  manifest metadata and are not byte-verified until a separately authorized
  label-evaluation phase.

## Engineering budget

The measured GB10 canary covers the shortest, lower-median-rank, and longest
train machines, selected by train-row counts only. It measured one epoch for
each learned arm on fit/validation rows. The updated estimate for the frozen
Stage-1 configuration is 64.62 serial GB10-hours, or 80.78 hours with the 25%
engineering allowance. Two simultaneous fits are not budgeted under the
measured free-memory/headroom rule. Estimated staging disk is 0.672 GiB. See
[`compute_budget.md`](compute_budget.md) and
[`compute_estimate.json`](../../reports/adaptive_normality_m1_smd/compute_estimate.json).

## Before a future Stage-1 run

1. Confirm the committed machine-readable implementation preflight reports
   `M1_SMD_READY_FOR_STAGE1_EXECUTION` and the committed independent review
   says `M1_IMPLEMENTATION_RESULT_BLIND_PASS`.
2. Use the pinned runtime and all 28 machines, W=256, seed 11, batch size 128,
   at most 50 epochs, frozen models, and unchanged scientific gates.
3. Fit the transform, learned arms, VAR coefficients, and calibration values
   using the frozen train blocks only. Persist scaler values, checkpoints,
   source commit, environment, epoch history, calibration vectors/thresholds,
   and run records.
4. Generate all nine score arrays on each machine's exact timestamps
   `t=256,...,test_rows−1`, then seal the complete 28-machine inventory.
5. Commit the score artifacts and inventory manifest. Only the future
   metric-only entry point may load test labels, and only after it verifies all
   committed artifacts and the complete seal. That later metric phase is
   outside this implementation task.

Any provenance mismatch, parameter-count mismatch, index violation,
non-finite score, or label-guard failure stops execution. Readiness does not
start Stage 1 automatically. No transfer, Stage 2, zero-shot, persistent
memory, quarantine, or adaptation is included here. ZERO_SHOT_NOT_STARTED.
