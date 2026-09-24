# M1-A preflight

## Status

Protocol and data preflight: **PASS**. Model implementation preflight: **PENDING**. No tests, detector forwards, training, score extraction, or GPU work were run in this research-only task.

The correct current decision is readiness of the frozen protocol, not evidence that any detector works. Before the first training run, a separately reviewed M1-only implementation must satisfy the checks below. This distinction prevents a protocol-ready status from being mistaken for completed experiment code.

## Data and provenance

- Pinned source is OmniAnomaly commit 7fb0e0acf89ea49908896bcc9f9e80fcfff6baf4.
- All 84 files for 28 machines (train, test, test_label) downloaded and parsed; every file has a recorded SHA-256 in dataset_manifest.md.
- All 28 machines pass finite numeric, D=38, row/label alignment, and binary-label schema checks.
- The existing local 28 test files byte-match the pinned source.
- No machine is removed and no R0-dependent machine selection is used.
- Before execution, reacquire the complete pinned source set or use a content-addressed retained copy, then verify all 84 hashes. The temporary download path is not an execution dependency.

## Frozen protocol choices

- Cohort: all 28 machines, fitted independently.
- Train blocks: first 70% fit; next 15% validation; final 15% normal-score calibration.
- Transform: fit-only per-machine/channel median center, hybrid robust scale, 5% machine-relative floor, clip ±50, float32; frozen for validation/calibration/test.
- Context: W=256, selected by fit-train ACF rule; no test labels used.
- Forecast: direct one-step p=1 from preceding W samples; target not passed to detector before prediction.
- Recurrent state: fresh for every context; no persistence.
- Scoring timestamps: test t>=256, common across arms; no padding, point adjustment, or segment filling.
- Stage 1: seed 11, 28 machines, three learned arms and all cheap arms.
- Stage 2: only if exact mechanical gate passes; seeds 22 and 33, unchanged design.

## Code and model checks required before Stage 1

The model implementation is not part of this documentation-only branch. Before any training:
1. Add a separate M1 data/model/runner implementation; do not change R0 modules.
2. Verify source raw hashes and train/test shapes against dataset_manifest.md.
3. Verify the scaler using stored hand-computed cases: median/MAD/quantile behavior, all-zero robust-scale fail-closed, near-constant floor, clipping endpoints, float32 conversion, and transform repeatability.
4. Verify each forecast sample uses exactly rows [t-W,t) as input and row t only as target; assert prediction is formed before target access in the scoring code.
5. Verify independent windows reset model hidden/cell state and no hidden state crosses timestamps.
6. Verify reconstruction windows end at t and are causal; keep reconstruction score endpoint aligned with the common timestamp list.
7. Verify parameter counts: xLSTMAD-R 75,934; xLSTMAD-F 80,510; capacity-matched LSTM-F 81,838. A mismatch blocks training.
8. Verify all scores and predictions are finite; calibration ranks and quantiles use only specified normal blocks.
9. Verify label access is absent from preprocessing, fitting, checkpoint selection, and score generation. Seal prediction/score file hashes before opening test labels.
10. Record package, hardware, seeds, model hashes, epoch curves, selected epochs, fit/validation/calibration row bounds, all configuration values, and wall times.

These are pre-execution acceptance conditions, not claims that they have passed. The future code review may add a stop if a check fails; it may not change a frozen choice using detector outcomes.

## Existing repository work: reuse map

| Existing component | Decision | Reason |
|---|---|---|
| R0 acquisition, SHA-256, finite/shape validation pattern | Reuse unchanged as a pattern | Provenance procedure is sound; build a separate 28-machine manifest/loader and verify new pinned source. |
| Official xLSTMAD R code / environment pins | Reuse unchanged for reconstruction | Current reconstruction path and pinned library are the required R arm. |
| Auditable matched-LSTM implementation methodology | Reuse as a pattern, not the R0 model class | Capacity matching and explicit parameter counts are useful; M1 needs a one-step forecaster with a new target contract. |
| R0 execution/preflight/run-record infrastructure | Reuse unchanged as operational pattern | Hash sealing, deterministic order, environment record, model hashes, and stop conditions support auditability. Do not copy R0’s task-specific split/feature extraction. |
| Current xLSTMAD-R reconstruction model | Reuse unchanged as baseline | It represents the existing reconstruction detector; keep its native architecture and objective. |
| R0 zero-std-only scaler | Do not reuse | It amplified machine-1-4 channel 17 because a tiny nonzero SD was treated as a safe denominator. |
| R0 internal234 probe | Do not reuse | M1 is a detector comparison, not a hidden-state utility probe; R0 did not resolve incremental internal-state utility. |
| R0 W=64 | Do not reuse as a default | M1 train-only timescale rule independently freezes W=256. |
| R0 reconstruction score / window-any label alignment | Do not reuse blindly | M1 uses point labels, a shared warm-up, and trailing-window score at the endpoint; no point adjustment. |
| R0 threshold calibration | Do not reuse | M1 uses the second half of its own normal calibration block, higher empirical 99th percentile; no R0 q95 or test-best threshold. |

## Readiness decision

No unresolved *scientific* choice blocks a prospective M1-A protocol: data source, cohort, train-only scaling, context, detector set, score alignment, metrics, and gate are frozen. The isolated xLSTMAD-F port and runner remain implementation prerequisites, clearly specified in forecasting_implementation_audit.md. The protocol can be handed to an implementation/execution phase, but model training must not begin until that code preflight is reviewed and a separate execution authorization is in place.
