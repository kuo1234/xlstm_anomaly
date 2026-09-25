# M1-A protocol: source-native one-step forecasting on SMD

## Status and scope

This is a preregistration and implementation audit. No scientific detector result has been observed. The result-blind implementation amendment in [implementation_amendment.md](implementation_amendment.md) recorded `M1_SMD_PROTOCOL_READY — IMPLEMENTATION_PENDING` before any M1 model forward. The machine-readable preflight now passes and the current implementation status is `M1_SMD_READY_FOR_STAGE1_EXECUTION`; this is code readiness, not a detector result and not evidence that Stage 1 has started. The branch preserves scientific commit `44b5c050cce2a0500c0edc1369ac313a66c6f2e2` and has the latest main history merged normally.

The primary question is:

> On each SMD machine, does a causal one-step forecast provide useful point-anomaly evidence beyond simple causal predictors/statistics and the existing xLSTMAD reconstruction detector?

M1-A tests source-native fit-and-test on the same machine. It does not test source-to-target transfer, zero-shot operation, target adaptation, persistent hidden state, multi-horizon forecasts, quarantine, regime promotion, or whether a persistent benign shift can be distinguished from a fault. Passing M1-A is necessary evidence for a forecasting signal, not evidence for adaptive normality.

## Frozen cohort and data rules

Use all 28 official SMD machines in the pinned dataset manifest. Each machine is a separate evaluation unit and is fit independently. Do not pool channels or select machines using R0 results. The official upstream raw commit and all 84 file hashes are in dataset_manifest.md. All machines pass the current provenance and schema audit.

The upstream labels are pointwise binary test labels. Train normality follows the benchmark convention; there is no train-label file, so it is an assumption rather than independent row-wise verification. Test labels are evaluator-only. They may be opened only after model outputs and all choices are frozen, for metrics and descriptive label inventory.

For each machine with train length N, freeze contiguous train-only blocks as:
- fit: rows [0, floor(0.70 N));
- model validation: [floor(0.70 N), floor(0.85 N));
- normal-score calibration: [floor(0.85 N), N).

The first block alone fits preprocessing, trainable parameters, and the VAR coefficients. Validation chooses the lowest validation loss checkpoint, with earliest epoch on exact ties. The last block calibrates score-tail transforms and the operating threshold; it never updates model weights. No test labels or test scores select preprocessing, context, architecture, optimizer, threshold, or checkpoint.

## Frozen preprocessing

Use the train-fit-only hybrid robust transform specified in preprocessing_audit.md:
- center each of the 38 channels by its fit-block median;
- estimate scale by the larger of 1.4826 times the median absolute deviation and the fit-block 5th-to-95th percentile range divided by 3.2897072539;
- floor each channel scale at 0.05 times the machine-level median of positive channel robust scales;
- fail closed if a machine has no positive robust channel scale;
- transform with these frozen values, clip to [-50, 50], then cast to float32.

Keep every channel, including channels with zero robust central scale. Fit the transform once per machine on fit rows only. Apply it unchanged to validation, calibration, and test. It does not update online.

## Frozen causal context

Use one context length, W=256 samples. It is chosen by the train-only rule in preprocessing_audit.md: smallest value in {32, 64, 128, 256} at least the nearest-rank 90th percentile of the per-channel first absolute-autocorrelation 1/e crossing, computed on the first 70% train block across all 28 machines. That percentile is about 239 samples, so W=256. The source describes roughly one-minute cadence, but raw files have no timestamps; primary latency is in samples. Dominant normal-train spectral peaks are near one day, longer than W. M1-A is expressly a subdaily/local-dynamics test and cannot establish daily-seasonal forecasting ability.

At target index t, the forecasters receive only z[t-W:t] and must emit prediction for z[t] before z[t] is supplied to any model or baseline. Score after observing z[t]. Recompute each independent W-sample window from a fresh state; no state is carried between windows. The first W test points are warm-up and excluded for every arm; test labels in that prefix do not trigger filling or retrospective scoring. Reconstruction receives the trailing window z[t-W+1:t+1], uses no future sample, and is evaluated at its right edge on the same scored timestamps t >= W.

## Detector arms

All six required comparisons are frozen in baseline_spec.md:
1. last-value predictor;
2. robust moving-median predictor, plus explicit reporting that squared first difference is exactly the last-value squared-error score;
3. train-fit ridge VAR(1);
4. current official xLSTMAD reconstruction architecture, trained with its unchanged native window reconstruction objective and yielding both `R-native-window` and `R-endpoint` scores from the same causal trailing-window output;
5. capacity-matched LSTM one-step forecaster;
6. xLSTMAD-F-formulation xLSTM one-step forecaster.

No multi-horizon model, persistent state, learned fusion, anomaly memory, or online update is included.

## Learned model budget

Use one fixed Stage-1 seed, 11, for every learned arm and all 28 machines. The learned arms use batch 128, at most 50 epochs, Adam with learning rate 1e-3, float32, and the same deterministic per-epoch window permutation. Select a checkpoint by the corresponding normal validation loss; no test-based checkpoint choice. Forecast models train one-step MSE on past-window-to-current-target pairs. The xLSTMAD-R arm trains its native window reconstruction MSE. Model width, parameter matching, and counts are frozen in baseline_spec.md.

If and only if the mechanical Stage-1 viability gate below passes, Stage 2 adds seeds 22 and 33 for all three learned arms, on all 28 machines, with no configuration changes. There is no informal inspection exception.

## Stage-1 viability and kill gate

The machine is the primary unit. AP is calculated per machine, then macro-averaged equally across machines. Paired 95% confidence intervals use 10,000 machine-cluster bootstrap resamples with seed 901; this reflects machine heterogeneity, not a random sample of all production machines.

The xLSTM forecaster passes the discrimination part by either route:

**Standalone route:** mean machine-level AP gain of at least 0.02 over the **oracle control envelope** on each machine, where that comparator is the maximum test AP among last-value, moving median, VAR(1), `R-native-window`, and `R-endpoint`. This is a predeclared test-label-dependent scientific gate, not a deployable detector or one operational baseline. The paired machine-bootstrap 95% lower bound must exceed zero, and the xLSTM forecaster must win on at least 20 of 28 machines.

**Complement route:** a fixed, label-free tail-rank max fusion of xLSTM forecast evidence with the five non-forecast control scores improves macro machine AP by at least 0.02 over the control-only fusion, with paired 95% lower bound above zero and a positive difference on at least 20 of 28 machines. Tail-rank calibration uses only the first half of the normal calibration block; the second half is reserved for operating thresholds. This is a fixed diagnostic fusion, not a trained model or a test-selected weight.

The successful candidate (xLSTM forecast alone or its fixed fusion) must also:
- exceed that machine’s test-label prevalence on at least 20/28 machines, with median AP/prevalence at least 1.5;
- detect at least 50% of contiguous label runs on the equal-machine macro event-detection metric at the frozen threshold;
- have equal-machine macro normal-point test FPR no greater than 2%, with no more than two machines above 5%;
- have no more than two catastrophic machines, where catastrophic means both AP <= that machine’s prevalence and event detection rate <= 0.10.

Thresholds are fixed separately per detector from the second half of the train-normal calibration block at its 99th score percentile using the higher empirical quantile. This is a nominal 1% train-normal false-positive operating point, not a test-best threshold.

If neither xLSTM route passes all of these conditions, record **FORECASTING_NOT_JUSTIFIED** and stop before Stage 2. The adaptive-normality project must not use xLSTM forecasting as its core signal on the basis of this study. If only the capacity-matched LSTM passes, report that result as a possible architecture-agnostic reframe; it does not unlock the xLSTM branch. If xLSTM and LSTM are equal, forecasting may still be useful but there is no xLSTM-specific claim.

Stage 2 confirms stability only if the same gain margin and machine-win conditions hold on the three-seed mean, the gain direction is positive in at least two of three seeds, the prevalence/event/FPR/catastrophic checks still pass, and the paired machine bootstrap lower bound remains above zero. Failure stops the forecasting-core claim. xLSTM-specific value additionally requires a replicated xLSTM-minus-matched-LSTM AP gain of at least 0.02 with a positive 95% machine-bootstrap lower bound.

## Execution boundary

The protocol is frozen and the implementation preflight has passed. `M1_SMD_READY_FOR_STAGE1_EXECUTION` does not itself launch Stage 1. No transfer or zero-shot stage is scheduled here. ZERO_SHOT_NOT_STARTED.
