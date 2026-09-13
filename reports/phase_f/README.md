# Phase F — STOP_IMPLEMENTATION_VALIDITY (before training)

Prospective config and reporting-only E2 clarification were committed/pushed as
`4c76e07` **before** the Phase F mechanical checks. E2 `4d49f1d` remains unchanged.
The old native-predict check did not test the upstream dataset/predict interface;
see [the correction](e2_predict_reporting_amendment.md).

## Completed scope

- Fixed improved official xLSTMAD pin/backend/architecture, 73,504 parameters.
- Implemented H38 standard six-layer full-window LSTM: 71,790 parameters.
- Prepared only train1000–1009 and validation2000–2004 stationary/none observation
  prefixes0:4096. Per-source scalers, raw/transformed arrays and all five
  50-epoch orders are sealed in [preprocessing_manifest.json](preprocessing_manifest.json).
  No test-source observations or anomaly/event/regime labels entered this path.
- Froze executable [LSTM common18 schema](lstm_common18_schema.json): all six
  layers, full H38 statistics, equal pooling, h/i/f/c, unchanged18 names and
  E2 trailing4/8/16/32 expansion. This is not yet a valid trained feature source.
- Fail-closed native predict guard passes the common forward/loss/score path;
  its negative control raises on attempted native predict_step. The actual
  upstream predict interface is **not** repaired or declared valid.

## Gate outcome

[mechanical_gates.json](mechanical_gates.json) records all checks, including
negative findings. Both models pass finite loss/gradients, nonzero recurrent
gradients, identical Adam settings, observation-only API, unchanged weights
and native-predict exclusion. xLSTM seed11 initial hash matches sealed E2 and
all its random-unlabeled parity checks pass.

LSTM passes output/score batch permutation and partition (B128/B3/B1), reset,
finite states, prefix causality, common18 shape/finite, observer OFF/ON bitwise
output/score, and feature permutation/partition. **Its manual recurrence versus
native h/c reference fails the frozen atol1e-5/rtol1e-4 in all six layers.**
Encoder0 maximum sequence-h error is 0.0001920592; final-c error is 0.0001974478.
Small final detector-output differences do not excuse an internal-state failure.

Thus Phase F is stopped before any scientific optimizer step. There are zero
scientific trained checkpoints, zero epoch curves, and no post-trained parity
claim. No anomaly performance was used as a gate. This is an implementation
STOP, not evidence for or against H2/H3.

## Bounded diagnosis, not a backend switch

[reference_diagnostic.json](reference_diagnostic.json) preserves an additional
random-unlabeled, no-update comparison using identical weights and observations:

| Execution condition | Manual/native h/c parity |
|---|---|
| Frozen CUDA with cuDNN TF32 allowed | FAIL |
| Diagnostic only: cuDNN TF32 disabled | PASS |
| Diagnostic only: CPU | PASS |

Disabling only cuDNN TF32 changes final output by up to 6.7353e-6 relative to
the frozen path; CPU differs by 6.6217e-6. All model hashes remain unchanged.
This isolates a backend-numerics cause for the observed reference discrepancy,
not a license to silently alter execution semantics. The diagnostic restores
the frozen flag before exit. No tolerance, architecture, seed, source, schema,
optimizer, training budget or scientific backend was revised.

Minimal proposed next step **requires external approval**: a pre-training
amendment explicitly disabling cuDNN TF32 for the matched float32 training
track, followed by fresh mechanical/reference gates for BOTH models and
verification against E2's unchanged xLSTM behavior. Do not train under that
setting merely because its numerical diagnostic passes. Phase G remains locked.

## Compute and completeness

Mechanical script body: 9.1653 seconds, zero optimizer steps. Cold one-batch
forward/backward plus an extra score took 0.9147s xLSTM and 0.0517s LSTM. CUDA
allocator peaks were 750,471,680 and 796,743,680 bytes, respectively (same
process; includes live input/other allocations, not standalone model memory).
The cold-batch training extrapolation is 21.21 summed run-hours, explicitly
not measured full training and excluding Adam/validation; E2's warm throughput
estimate remains in the prospective note. No full run was launched. Diagnostic
runtime and environment are included in its JSON; full-training runtime is N/A.

Training runners were not retained/launched after this blocker. Deliverables
requiring training (ten best checkpoints, epoch curves, selected epochs,
trained recurrent-weight changes and post-training parity) are **NOT_RUN**.
Only backward gradients were computed for mechanical checks; model hashes did
not change. No labeled feature extraction, probe fitting/scaler/AP, test anomaly
evaluation, H3b, H4, natural-H1 harm, rollback or learned gate was run.

Evidence seal: [SHA256SUMS](SHA256SUMS). Local prefix/order/scaler references
are separately sealed; they are local artifacts under ignored data/phase_f,
not falsely presented as uploaded checkpoints. E2 integrity verification checks
hashes only and does not recompute its sealed tests.
