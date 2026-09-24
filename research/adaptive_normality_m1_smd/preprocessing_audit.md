# M1-A preprocessing and context audit

## What was inspected

All 28 pinned SMD train traces were parsed as finite 38-column numeric matrices. Preprocessing candidates and temporal scales were computed from the first 70% of each machine’s original train split only. The test-label vectors were not parsed until the scale and context choices described here had been selected. Test observations were later transformed with the frozen rule only to confirm finite numerical behavior; they did not change the rule.

The fit block contains 18,843,174 channel values across the family. A standardized channel is never removed or permuted.

## Candidate scaling rules

R0 used per-channel mean and population standard deviation, replacing only exact zero standard deviations with 1.0. That leaves rare-deviation channels with tiny nonzero denominators and can amplify them by thousands.

The train-only candidates were:
1. R0 mean/std with exact-zero fallback only, retained as a comparison diagnostic;
2. median center with 1.4826 MAD scale and a machine-relative positive-scale floor;
3. a hybrid robust scale that takes the larger of MAD scale and central 5–95% range scale, with the same floor;
4. clipping bounds of 20, 50, and 100 robust units, audited only on normal fit values.

For the hybrid, let b_j = max(1.4826 MAD_j, (Q95_j - Q05_j)/3.2897072539). The per-machine floor is alpha times the median of positive b_j. The candidate screen used alpha in {0.01, 0.05, 0.10} and clipping in {20, 50, 100}; it inspected only fit-block distributions and clipping rates, never anomaly AP/AUROC.

## Frozen M1 transform

Freeze alpha = 0.05 and clip = 50:
1. center_j = median of channel j in the first 70% train-fit block;
2. b_j = max(1.4826 MAD_j, (Q95_j - Q05_j)/3.2897072539);
3. scale_j = max(b_j, 0.05 median_k(b_k where b_k > 0));
4. z_j = clip((x_j - center_j)/scale_j, -50, 50), then float32.

If no channel has positive b_k, fail the machine closed. Constant and near-constant channels stay in the matrix and receive the same positive machine-relative floor. No online center/scale update, per-test refit, label-based feature removal, or test normalization is allowed.

For alpha=0.05 and clip=50, 6,933 of 18,843,174 fit values (0.0368%) clip; the highest machine-level fit clipping rate is 0.1356%. With the transform frozen, all 28 test matrices were finite; 0.3178% of test values clip overall, with a maximum machine rate of 2.4127%. That is a numerical audit, not a reason to revise the bound.

The train-only zero-robust-scale count is 276 of 1,064 machine-channel pairs. Those channels are retained and scaled by the floor. For machine-1-4, zero-based channel 17 (the 18th CSV column) has fit standard deviation 1.63e-5, MAD scale 0, and central 5–95% scale 0. The M1 scale floor is 0.00145873, about 89.5 times the M1 fit standard deviation and 86.5 times the 1.6854e-5 R0 denominator recorded for that channel. The R0 no-floor rule produced scaled test magnitude around 3.3e3 on the near-constant path; dividing by the new denominator reduces the same raw deviation to about 38 before clipping. This prevents the R0 machine-1-4 amplification failure without dropping the channel or using its test label. The ±50 cap also bounds any remaining extreme input and squared-error contribution.

The alpha/clipping choice is numerical and prospective: alpha=0.05 gives a meaningful floor while retaining more channel contrast than alpha=0.10; at the frozen bound, the normal fit clipping rate remains below 0.14% on every machine. No anomaly metric informed this choice.

## Context and cadence audit

The raw SMD files have no timestamps. Published SMD protocol descriptions give roughly five weeks and one-minute sampling; therefore 256 samples is nominally about 4 hours 16 minutes, but all primary delays are in sample counts.

For each nonconstant channel in the fit block, the audit computed the demeaned autocorrelation by FFT and recorded the first lag where absolute autocorrelation is <= 1/e. Constant channels were assigned lag zero. Across 1,064 machine-channel pairs, the 50th, 75th, 90th, 95th, and 99th percentiles were approximately 18.5, 174.3, 238.7, 708.5, and 3,051.7 samples. The context rule frozen before label inspection was to select the smallest of 32, 64, 128, 256 at least the nearest-rank 90th percentile, yielding W=256.

As an independent timescale description, the strongest non-DC periodogram bin per nonconstant channel had median period about 1,425 samples and 75th percentile about 1,456 samples, close to a nominal day. This peak statistic can reflect trend or periodic structure and is descriptive, not proof of a stable daily cycle. W=256 does not cover that period. The M1 question is deliberately limited to a subdaily, one-step source-native forecast. A result cannot rule out a longer-context seasonal model.

## Why this is not test-label tuning

Both the transform and context were derived from the first 70% of each normal-assumption train split and aggregated over all 28 machines. No machine was chosen or removed based on R0 performance, test values, test labels, AP, AUROC, or detector outputs. The test-value clipping check occurred only after the rule was fixed and used no labels.

## Risks kept visible

The floor couples channels through a within-machine median scale; this may downweight legitimate quiet sensors with different units. Clipping can suppress extreme but valid or anomalous amplitudes. The central quantiles are robust to rare values but the training split itself is only assumed normal. These choices are frozen for M1; they are not adjusted after seeing detector outcomes.
