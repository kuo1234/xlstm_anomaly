# M1-A implementation preflight

## Result-blind status

Before the first M1 model forward, the result-blind wording amendment recorded
the precise status `M1_SMD_PROTOCOL_READY — IMPLEMENTATION_PENDING`. It recorded
that no scientific detector result existed and reserved execution readiness
until the implementation preflight passed. The bounded engineering canary
described in `compute_budget.md` is a timing measurement only; it is not a
Stage-1 detector run or anomaly result.

The machine-readable acceptance record is
[`implementation_preflight.json`](../../reports/adaptive_normality_m1_smd/implementation_preflight.json).
The final record reports 14/14 checks passed, including the test record and
independent red-team verdict. A failed item blocks Stage 1.

## Data and label boundary

- The pinned manifest contains 84 structurally valid expected digest/byte-count
  entries for 28 machines × `{train,test,test_label}`. This preflight validates
  all 84 manifest entries without opening raw test-label files.
- It reads and verifies the content hashes of the 56 permitted train/test
  observation files, then checks finite numeric `[N,38]` matrices and the
  manifest row count for all 28 machine pairs.
- Test-label file reads and opens are forbidden throughout preprocessing,
  fitting, validation, normal-score calibration, and test-score generation.
  The future metric entry point permits a label loader only after the exact
  committed 28-machine score inventory and its seal have passed verification.
- No test anomaly labels or label-derived metric were used to select the
  canary machines, timing policy, implementation, or compute estimate.

## Frozen execution contract

- Cohort: all 28 machines; train-relative fit/validation/calibration bounds are
  `[0,floor(.70N))`, `[floor(.70N),floor(.85N))`, and `[floor(.85N),N)`.
- The transform is fit on fit rows only: median center; maximum of
  `1.4826×MAD` and `(Q95−Q05)/3.2897072539`; floor at 5% of the machine median
  positive robust scale; clip to ±50; cast to float32; fail closed if no
  positive scale exists.
- Forecast input for target `t` is exactly `[t−256,t)` and the target is `t`.
  Fit targets remain within fit rows. Validation and calibration first targets
  use the preceding 256 observations already available at `t`, including rows
  from earlier train blocks; neither target is used to fit model parameters.
- Reconstruction uses the trailing input `[t−255,t+1)` and scores its right
  edge. `R-native-window` averages squared residual over `W×D`; `R-endpoint`
  averages only the final D residuals. Both are frozen scores from the same
  unchanged official xLSTMAD-R output.
- Test score timestamps start exactly at `t=256`; all nine Stage-1 arrays share
  the same timestamps and no warm-up score is padded.
- xLSTMAD-R and the historical official xLSTMAD-F port keep their frozen
  architectures/objectives; LSTM-F is capacity matched. Counts are 75,934,
  80,510, and 81,838 trainable parameters, respectively.
- Normal tail references use the first half of the train calibration block;
  the second half supplies the higher empirical 99th-percentile threshold for
  each of the nine raw/fused score arrays. Test data and labels do not enter
  calibration.
- The per-machine maximum test AP among non-forecast controls is the
  test-label-dependent **oracle control envelope**, used only as a conservative
  scientific gate. The fixed label-free control tail-rank fusion remains the
  operational complement diagnostic.

## Required checks

The machine-readable preflight covers manifest and observation provenance,
scaler exactness and the machine-1-4 near-constant-channel regression, sample
indices and target causality, reconstruction alignment/corruption cases,
parameter counts and synthetic forwards, deterministic seed behavior, fresh
state, timestamp equality, calibration separation, label isolation, score-seal
enforcement, pinned environment versions, timing-canary completion, R0
regression tests, and result-blind red-team review. Its completion record also
asserts zero test-label opens/reads, no M1 anomaly metric, and no full Stage-1
training.

The detailed M1-specific implementations live in the isolated `scripts/`
modules and `tests/test_adaptive_normality_m1_*.py`; no R0 source or R0 output
is changed. Historical xLSTMAD-F source parity and the measured engineering
canary are documented in
[`forecasting_implementation_audit.md`](forecasting_implementation_audit.md)
and [`compute_budget.md`](compute_budget.md).

## Readiness rule

The machine-readable record reports
`M1_SMD_READY_FOR_STAGE1_EXECUTION`; the independent review reports
`M1_IMPLEMENTATION_RESULT_BLIND_PASS`. Readiness does not itself start the
28-machine Stage-1 experiment. No Stage 2, transfer, zero-shot, persistent
memory, quarantine, or adaptation is included here. ZERO_SHOT_NOT_STARTED.
