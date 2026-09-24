# M1-A execution handoff

## Decision and scope

The research protocol, source manifest, train-only preprocessing/context audit, model audit, metrics, compute estimate, and Stage-1 gate are frozen in this directory. This is not an experiment result. No detector has been trained or evaluated.

Execution must begin only after the M1-specific code prerequisites below are reviewed and the user separately authorizes the Stage-1 run. This handoff does not authorize training or Stage 2. ZERO_SHOT_NOT_STARTED.

## Before any training

1. Create a separate M1 implementation for data loading, the frozen robust transform, xLSTMAD-F, matched LSTM-F, scoring, metrics, and run records. Leave all R0 modules and history unchanged.
2. Reacquire or stage the 84 exact SMD files from pinned OmniAnomaly commit 7fb0e0acf89ea49908896bcc9f9e80fcfff6baf4; verify every digest in dataset_manifest.md.
3. Complete the implementation checks in preflight.md, including sample-index assertions, parameter-count assertions, finite-value checks, same-timestamp alignment, no cross-window state, and sealed score files before label access.
4. Confirm the pinned runtime versions and an available GB10 allocation. The planning estimate for Stage 1 is about 190 GB10-hours; do not alter the frozen 28-machine cohort or configuration to fit a smaller allocation.
5. Produce an execution commit and protocol-head record, then review all changes against the M1 frozen spec.

## Stage-1 order and label boundary

- Fit preprocessing, three learned arms, VAR(1), and all normal validation/calibration quantities using train only.
- Do not open test labels during train, checkpoint selection, threshold calibration, or score generation.
- Generate all 28 test score arrays for every arm using the common eligible timestamp list t>=256; materialize the prediction before accessing the target for forecast arms.
- Seal the model and score output hashes and write the label-access audit record.
- Only then open labels through a metric-only path and compute the frozen point/event metrics and Stage-1 gate.

A failure of provenance, parameter count, index contract, numerical validity, or label separation stops execution for investigation; do not replace a failed arm or machine post hoc.

## Stage-1 decision

Apply the full mechanical gate from protocol.md once to the sealed Stage-1 result set. If it fails, publish FORECASTING_NOT_JUSTIFIED and do not run Stage 2. If it passes every component, Stage 2 becomes eligible for a new execution decision; it does not start automatically.

## Reuse and non-reuse

Reuse the established R0 file-hash/provenance pattern, run metadata fields, seed/order recording approach, package/hardware recording, capacity-match methodology, and GB10 timing records. Reuse the current xLSTMAD-R source unmodified as the reconstruction comparison.

Do not widen the R0 three-machine data loader or manifest, copy the zero-std-only scaler, use internal234, freeze W=64 by precedent, use R0 reconstruction/window-any score logic, use its q95 threshold, or modify R0 code/history. M1's held-out scores use point labels without adjustment and its own second-half calibration-block 99th-percentile operating threshold.

## Decision language

- Successful xLSTM forecast gate: source-native forecasting is viable enough to justify a separately designed next study; it proves nothing about adaptation or new normals.
- Only LSTM forecast passes: consider an architecture-agnostic forecasting reframe; no xLSTM-specific conclusion.
- Neither forecast route passes: FORECASTING_NOT_JUSTIFIED; adaptive-normality research must not rely on forecast residual as its core signal under this evidence.
- xLSTM and matched LSTM comparable: no xLSTM-specific advantage.
