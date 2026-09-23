# A+S statistical reassessment (S0)

This is a post-hoc uncertainty audit of the committed A+ result. It does not
replace the historical A+ bootstrap and it is not a new confirmatory test.

The primary estimand is the mean of the ten source-level AP differences, with
the three detector seeds retained as a crossed factor. The pooled-test AP
differences from the six A+ runs remain descriptive. The crossed bootstrap
resamples source rows and seed columns independently once per replicate
(10,000 draws, seed 901). The source-only bootstrap resamples source rows while
conditioning on the three observed seeds (also 10,000 draws, seed 901).

| backbone | source-level mean | crossed interval | source-only interval | historical nested interval |
|---|---:|---:|---:|---:|
| xLSTM | +0.02671045 | [+0.01950949, +0.03258161] | [+0.02425693, +0.02936110] | [+0.02295938, +0.03031202] |
| LSTM | +0.01022015 | [+0.00780522, +0.01281719] | [+0.00848018, +0.01186431] | [+0.00786058, +0.01256640] |

The crossed intervals are the appropriate reassessment for a source-by-seed
matrix. Only three detector-seed levels are available, so neither interval
should be described as precisely calibrated for a population of detector
seeds. The historical nested-bootstrap values are retained unchanged as a
reference in `s0_results.json`.
