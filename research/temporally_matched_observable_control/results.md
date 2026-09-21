# A+ results: temporally matched observable control

This is a post-G1 exploratory analysis.  It does not alter the authoritative
G1 artifacts, H2/H3a/H3b decisions, or the original strong-observable results.
No model inference was rerun: the dense observation cache was opened read-only
and the two new arms were fitted offline.

## Primary result

The primary contrast is `AP(H+O1r+internal234) - AP(H+O1r)`.  It uses the same
source-disjoint folds, W64/right-edge rows, L2 `lbfgs` probe, train-only
StandardScaler, pooled validation C selection, and four-value C grid for every
arm.  The intervals below are descriptive source-first hierarchical bootstrap
intervals (10,000 draws, seed 901), not confirmatory tests.

| backbone | seed 11 | seed 22 | seed 33 | mean | median | exploratory 95% CI |
|---|---:|---:|---:|---:|---:|---:|
| xLSTM | +0.028952 | +0.019571 | +0.031825 | **+0.026710** | +0.027749 | [+0.022959, +0.030312] |
| matched LSTM | +0.011486 | +0.010591 | +0.008962 | **+0.010220** | +0.009831 | [+0.007861, +0.012566] |

All 30 source-by-seed effects are positive for each backbone.  The old `+0.02`
value is only a descriptive reference: xLSTM has 22/30 source-seed units at or
above it and 2/3 seed means at or above it; LSTM has 1/30 units and 0/3 seed
means at or above it.

| backbone | H+O1r AP (11/22/33) | H+O1r+I AP (11/22/33) | source mean range |
|---|---|---|---:|
| xLSTM | 0.905798 / 0.912523 / 0.898743 | 0.934750 / 0.932094 / 0.930568 | 0.020758–0.034968 |
| matched LSTM | 0.933734 / 0.933568 / 0.939611 | 0.945220 / 0.944158 / 0.948573 | 0.004647–0.015108 |

The complete 10×3 matrices, row-key hashes, selected C values, scaler and
coefficient hashes, class counts, and per-arm validation candidates are in
`results/results_{architecture}_{seed}.json`; the aggregate is in
`results.json`.

## Scenario strata

Scenario values are AP differences from the same frozen arm fits, reported
descriptively (seed 11 / 22 / 33, followed by their mean).

| scenario | xLSTM | matched LSTM |
|---|---:|---:|
| abrupt | +0.002247 / +0.000401 / +0.003668 (mean +0.002105) | +0.000239 / +0.001649 / +0.000895 (mean +0.000927) |
| gradual | +0.024574 / +0.021709 / +0.022656 (mean +0.022980) | +0.010484 / +0.009651 / +0.008511 (mean +0.009549) |
| recurring | +0.030889 / +0.000514 / +0.045032 (mean +0.025478) | +0.010007 / +0.014836 / +0.011549 (mean +0.012131) |
| correlation | +0.016946 / +0.004125 / +0.013096 (mean +0.011389) | +0.006055 / +0.001424 / +0.007167 (mean +0.004882) |

The largest mean stratum is gradual for xLSTM and recurring for LSTM, but the
recurring xLSTM value is heterogeneous across seeds.  No scenario was used for
feature, C, or arm selection.

## Historical references

The original arms were copied read-only from the committed strong-observable
summaries.  They are not temporally matched and are included only for context.

| backbone | old I\|H mean | old I\|H+O1 mean | old I\|H+O2 mean |
|---|---:|---:|---:|
| xLSTM | +0.142270 | +0.039584 | +0.071217 |
| matched LSTM | +0.141633 | +0.015271 | +0.053028 |

The historical H/H+I APs were reproduced by reference lookup with identical
row counts (697,430 train/test and 348,715 validation for every seed and
backbone).  A+ does not refit or reinterpret those historical arms.

## Execution notes

The fixed 1664-column O1r fits are materially more expensive than the original
O1/O2 fits.  The run retained all rows and the fixed four-C `lbfgs` budget;
some high-dimensional fits emitted the existing sklearn convergence warning at
the frozen 1,000-iteration cap.  No solver, tolerance, row count, or C grid was
changed in response to an observed result.

