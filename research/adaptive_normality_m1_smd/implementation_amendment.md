# M1-A result-blind implementation amendment

Date: 2026-09-25

## Result-blind status correction

This wording correction is recorded before any M1 detector result exists and
before any M1 model forward, training, score extraction, or anomaly metric has
been run. No scientific detector result has been observed.

The status recorded at amendment time was:

`M1_SMD_PROTOCOL_READY — IMPLEMENTATION_PENDING`

`M1_SMD_READY_FOR_EXECUTION` is reserved for a later status record after the
implementation preflight in `preflight.md` passes. Protocol readiness alone
does not imply executable code or authorize Stage 1.

## Post-preflight readiness update

On 2026-09-25, the final machine-readable implementation preflight passed all
checks and the independent result-blind review returned
`M1_IMPLEMENTATION_RESULT_BLIND_PASS`. The current implementation status is
`M1_SMD_READY_FOR_STAGE1_EXECUTION`. This records executable implementation
readiness only; the 28-machine Stage-1 detector experiment has not started,
and no anomaly result or metric exists.

## Frozen reconstruction scores

The xLSTMAD-R architecture, training objective, data, and checkpoint rule remain
unchanged. The same reconstruction output at trailing window ending at original
timestamp `t` yields two predeclared scores:

- `R-native-window`: the faithful published/native window score,
  `mean_{W,D}((z_window - zhat_window)^2)`, attached to `t`.
- `R-endpoint`: the endpoint-aligned diagnostic score,
  `mean_D((z_t - zhat_t)^2)`, using only the final reconstructed position.

Both scores are computed from the same input window and model output and refer
to the same original timestamp as the forecast score. `R-native-window` stays
present so that the native duration dilution/window behavior remains visible.
`R-endpoint` supplies the point residual comparison that aligns with forecasting
at `t`; it does not alter the reconstruction objective or retrain the model.

The non-forecast control set now contains last-value, moving median, ridge
VAR(1), `R-native-window`, and `R-endpoint`. The operational control-only and
forecast-plus-control diagnostics remain fixed, label-free maximum tail-rank
fusions over those five controls, and over those five plus xLSTMAD-F,
respectively. Calibration and threshold rules are unchanged.

## Standalone comparator terminology

The standalone route takes, for each machine, the maximum test AP among the
non-forecast controls. This is named the **oracle control envelope** throughout
M1 reports. It is a predeclared, test-label-dependent scientific gate. It is
not a deployable detector, not one operational baseline, and not a single
control selected without labels. The separate fixed label-free tail-rank
fusion remains the operational complement diagnostic.

The numerical gate and all other scientific choices remain unchanged. This
amendment adds one diagnostic score from existing reconstruction output and
clarifies language only.

## Changes that remain unauthorized

This amendment does not change the 28-machine cohort, W=256, train/validation/
calibration boundaries, seed, optimizer, epoch budget, model dimensions,
forecast target, reconstruction objective, detector arms, or any scientific
gate. It does not authorize Stage 1, Stage 2, transfer, zero-shot, persistent
memory, quarantine, or adaptation.
