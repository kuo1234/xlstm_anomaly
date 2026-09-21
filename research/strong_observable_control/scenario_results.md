# Scenario-stratified strong-control effects

Entries are the primary contrast `AP(H+O2+I) − AP(H+O2)` for each detector
seed.  They are exploratory strata; no scenario was selected or tuned after
inspection.

| architecture | scenario | seed 11 | seed 22 | seed 33 | mean |
|---|---|---:|---:|---:|---:|
| xLSTM | abrupt | +0.005172 | +0.005366 | +0.004317 | +0.004952 |
| xLSTM | gradual | +0.051411 | +0.039769 | +0.015395 | +0.035525 |
| xLSTM | recurring | +0.086750 | +0.068815 | +0.134722 | +0.096762 |
| xLSTM | correlation | +0.002225 | -0.008925 | +0.046804 | +0.013368 |
| LSTM | abrupt | +0.008801 | +0.007113 | +0.007869 | +0.007928 |
| LSTM | gradual | +0.024731 | +0.036672 | +0.049873 | +0.037092 |
| LSTM | recurring | +0.093171 | +0.038576 | +0.036443 | +0.056064 |
| LSTM | correlation | +0.006094 | -0.006068 | -0.004626 | -0.001534 |

Recurring regimes retain the largest mean residual-controlled increment for
both backbones.  Abrupt shifts show little remaining increment, and the
correlation stratum is heterogeneous (positive for xLSTM on average but mixed
by seed; slightly negative for LSTM on average).  These patterns are
descriptive hypotheses, not evidence for a causal mechanism or a global
xLSTM-over-LSTM ranking.
