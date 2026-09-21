# Matched-LSTM strong-observable results

This is a post-G1 exploratory linear-probe stress test using the frozen matched
LSTM checkpoints for detector seeds 11, 22, and 33.  No retraining was done.
The primary contrast is `AP(H+O2+I) − AP(H+O2)` with the same O2 residual basis
and probe protocol used for xLSTM.

## Pooled test AP by detector seed

| seed | H14 | H+I | H+O1 | H+O1+I | H+O2 | H+O2+I |
|---:|---:|---:|---:|---:|---:|---:|
| 11 | 0.800150 | 0.940235 | 0.928641 | 0.945773 | 0.889712 | 0.944407 |
| 22 | 0.793635 | 0.939096 | 0.928131 | 0.944982 | 0.893429 | 0.948389 |
| 33 | 0.796116 | 0.935471 | 0.937646 | 0.949476 | 0.897566 | 0.946993 |

The sanity internal increment `H+I − H` is `+0.141633 AP` averaged over the
three pooled seed evaluations (range `+0.139354` to `+0.145461`), reproducing
the expected matched-LSTM scale.

## Increments

| seed | I\|H | O1\|H | O2\|H | I\|H+O1 | **I\|H+O2 (primary)** |
|---:|---:|---:|---:|---:|---:|
| 11 | +0.140085 | +0.128491 | +0.089562 | +0.017132 | **+0.054695** |
| 22 | +0.145461 | +0.134496 | +0.099793 | +0.016851 | **+0.054961** |
| 33 | +0.139354 | +0.141530 | +0.101449 | +0.011829 | **+0.049427** |

The primary pooled-seed mean is **+0.053028 AP**.  Across the 30
source-by-seed primary effects, the mean is `+0.052761`, median `+0.048319`,
range `+0.036481..+0.078326`; all 30 are positive and all 30 exceed the old
`+0.02` reference margin.  The exploratory source-first bootstrap (10,000
draws, seed 901) gives mean `+0.052729` and 95% interval
`[+0.046168, +0.058372]`.  This is descriptive only and is not a new
confirmatory test.

The O2 control improves over H14 by `+0.096935 AP` on average, while I still
adds a positive increment after O2.  Thus the strong observable control does
not explain away the matched-LSTM internal-state signal under this linear
probe.

As with xLSTM, some high-dimensional `lbfgs` fits reached the frozen iteration
limit.  The protocol was not changed after seeing outcomes.
