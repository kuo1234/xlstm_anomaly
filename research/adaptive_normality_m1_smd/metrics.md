# M1-A metrics and alignment

## Primary and secondary metrics

Primary metric is sklearn average_precision_score, reported as point-level AP/AUPRC per machine. AP is not pooled across machines for the primary result. Report the equal-machine macro mean, median, range, all 28 machine values, and the test-label prevalence beside every machine AP.

Secondary metric is point-level AUROC per machine and equal-machine macro summary. Report AP/prevalence per machine and the count of machines where AP exceeds prevalence. Micro-pooled point metrics may appear only as descriptive context; they cannot determine the gate.

## Causal timestamp alignment

For each original test stream, omit the first W=256 timestamps as the common warm-up. Every remaining timestamp t has one detector score and the original point label y_t. Forecasts for z_t are produced from z_(t-W:t) before z_t enters the model or rolling baseline; only then is the residual scored. xLSTMAD-R uses the trailing window ending at t and attaches its mean W×D reconstruction error to t. All scores use the same valid timestamp set. No score padding, retrospective filling, point adjustment, or anomaly-segment expansion is allowed.

For contextual score fusion only, each raw detector score is mapped to a training-normal empirical upper-tail severity using the first half of calibration scores: tail(s) = (1 + count(calibration score >= s))/(n + 1), severity = -log10(tail). `R-native-window` and `R-endpoint` are separate score inputs from one unchanged reconstruction model. The control-only fusion is the maximum severity over last-value, moving median, VAR(1), `R-native-window`, and `R-endpoint`. The forecast-plus-control fusion is the maximum of those five severities and xLSTM-F severity. This mapping is fixed without labels. It is not a learned detector. The standalone AP comparator, called the **oracle control envelope**, takes the maximum test AP among those five controls and is test-label-dependent; it is a scientific gate only, not a deployable detector or one operational baseline.

## Event and operating-point metrics

A label event is one maximal contiguous run of test y=1 points for a machine. It is an operational proxy, not a ground-truth incident identity; the dataset does not provide incident IDs for this protocol.

For each detector and machine report:
- event detection rate: fraction of contiguous label runs containing at least one threshold alarm;
- onset delay: first threshold alarm index within a run minus its first labeled point, in samples; report misses as censored at event length and include the miss fraction;
- normal-point false-positive rate: false-alarm points divided by labeled-normal scored points;
- false-positive burden: false-alarm points per 10,000 scored normal points and contiguous false-alarm runs per 10,000 normal points;
- score recovery after an anomaly run: samples from the run’s exclusive end to the first 10 consecutive scores below the frozen threshold; right-censor at the test end and report censoring.

The fixed operating threshold for each raw score or fixed fusion is its higher empirical 99th percentile on the second half of the normal calibration block. No test-best threshold, anomaly-label threshold search, segment filling, hysteresis tuning, or threshold change after viewing test behavior. The 99th percentile is a nominal 1% training-normal alarm point; test FPR is measured, not assumed.

Report event metrics machine by machine and as an equal-machine macro. Also show micro-event values as descriptive only. Do not infer that a stable/persistent event is benign from these metrics.

## Uncertainty and decision summaries

For paired AP gains, resample the 28 machines as whole units 10,000 times with fixed seed 901 and report 95% percentile intervals. Stage 1 has one seed, so this interval quantifies cross-machine heterogeneity only. If Stage 2 is unlocked, report each seed and a machine-first, seed-second paired bootstrap over the three fixed seeds. Keep all per-machine values visible; a favorable aggregate cannot hide a catastrophic machine.

No metric in this protocol uses point adjustment. AP/AUROC are computed once on raw point scores and labels; event metrics are secondary and separately defined.
