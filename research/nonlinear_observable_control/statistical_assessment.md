# Statistical assessment

This is a post-protocol exploratory summary. It is not a new confirmatory
family and does not alter G1, H2, H3a, or H3b.

## Primary estimand

The primary estimand is the mean of the `10 source × 3 detector-seed` matrix
of test AP differences:

```text
AP(H+O1r+internal234) - AP(H+O1r)
```

The matrices are in `source_seed_effects.csv`; each row is one architecture and
detector seed, with columns ordered by test source `3000..3009`.

| architecture | source-level mean | crossed 95% interval | source-only 95% interval | positive source×seed cells |
|---|---:|---:|---:|---:|
| xLSTM | +0.01516504 | [+0.01248823, +0.01822553] | [+0.01292439, +0.01779533] | 30/30 |
| matched LSTM | +0.01125203 | [+0.00895238, +0.01347492] | [+0.00932228, +0.01319770] | 30/30 |

Both intervals use 10,000 bootstrap draws and seed `901`. The crossed
bootstrap independently resamples source rows and detector-seed columns once
per replicate. The source-only bootstrap conditions on the three observed
detector seeds. Three detector-seed levels are too few for either interval to
be described as a precisely calibrated population confidence interval.

## Pooled descriptive effects

| architecture | seed 11 | seed 22 | seed 33 | mean of pooled deltas |
|---|---:|---:|---:|---:|
| xLSTM | +0.01520113 | +0.01476300 | +0.01520820 | +0.01505744 |
| matched LSTM | +0.01125104 | +0.01163674 | +0.01121702 | +0.01136827 |

The source-level mean, rather than the mean of pooled deltas, is the primary
summary. The historical `+0.02` value is retained only as a descriptive
reference; it is not a significance threshold here.

## Scenario summaries

Mean test AP increments by scenario are:

| scenario | xLSTM | matched LSTM |
|---|---:|---:|
| abrupt | +0.00222750 | +0.00291585 |
| gradual | +0.01657065 | +0.01170206 |
| recurring | +0.01065174 | +0.01290133 |
| correlation | +0.01261890 | +0.01037618 |

These are descriptive strata, not independent hypothesis tests.
