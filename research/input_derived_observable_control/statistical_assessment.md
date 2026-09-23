# Statistical assessment — P1r

This is an exploratory summary under the sealed protocol. It creates no confirmatory family and
does not alter G1, H2, H3a or H3b.

## Primary estimand

For each backbone, the estimand is the mean of the 10 source × 3 detector-seed matrix of test AP
differences:

```text
AP(H+P1r+internal234) − AP(H+P1r)
```

| backbone | source-level mean | crossed interval | source-only interval | positive cells |
|---|---:|---:|---:|---:|
| xLSTM | −0.00023259 | [−0.00076128, +0.00029149] | [−0.00047119, +0.00002557] | 14/30 |
| matched LSTM | +0.00028937 | [−0.00041494, +0.00095887] | [−0.00006616, +0.00063865] | 17/30 |

Both bootstraps use 10,000 draws and RNG seed 901.

- **Crossed bootstrap.** Source rows and detector-seed columns are resampled once each per
  replicate.
- **Source-only bootstrap.** Conditions on the three observed seeds.

The consolidation red-team reproduced both intervals independently from the committed matrices,
exactly. With only three detector-seed levels, neither interval is a precisely calibrated
population 95 % confidence interval. Both are exploratory.

## Frozen classification

The crossed interval contains zero for both backbones, so the frozen rule in `protocol.md` gives
`NO_RESOLVED_ADDITIONAL_UTILITY` for xLSTM and for matched LSTM.

## Descriptive context

- **Cell signs.** They are mixed: 14/30 positive cells for xLSTM and 17/30 for LSTM. No cell
  reaches the historical +0.02 descriptive reference.
- **Seed-level means.** They straddle zero for both backbones: xLSTM −0.00041730, +0.00019222,
  −0.00047268; LSTM +0.00018156, +0.00084303, −0.00015647. Pooled per-seed deltas agree with
  the seed-level means to within 0.00007 and are descriptive only.
- **Interval width.** Both crossed intervals are narrow. The largest increment compatible with
  them is +0.00029 AP for xLSTM and +0.00096 AP for LSTM. For comparison, the nonlinear O1r
  increments were +0.01516504 and +0.01125203.
- **Backbone comparison.** Any difference between the two backbones is descriptive. It is not
  interpreted.
