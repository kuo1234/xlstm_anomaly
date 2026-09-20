# xLSTM strong-observable results

This is a post-G1 exploratory linear-probe stress test.  It uses frozen
vanilla-trained checkpoints for detector seeds 11, 22, and 33; no model was
retrained and no G1 artifact was changed.  `I` is the existing common G1
internal234 representation.  The primary contrast is `H+O2+I − H+O2`, where
O2 is the 1,024-dimensional signed/squared normalized residual trajectory.

## Pooled test AP by detector seed

| seed | H14 | H+I | H+O1 | H+O1+I | H+O2 | H+O2+I |
|---:|---:|---:|---:|---:|---:|---:|
| 11 | 0.789781 | 0.935251 | 0.896810 | 0.939495 | 0.867157 | 0.938278 |
| 22 | 0.785797 | 0.929863 | 0.905976 | 0.939745 | 0.879583 | 0.936501 |
| 33 | 0.788638 | 0.925911 | 0.891614 | 0.933911 | 0.845562 | 0.931177 |

The sanity internal increment `H+I − H` is `+0.142270 AP` averaged over the
three pooled seed evaluations (range `+0.137273` to `+0.145470`), consistent
with the known G1-scale effect.

## Increments

| seed | I\|H | O1\|H | O2\|H | I\|H+O1 | **I\|H+O2 (primary)** |
|---:|---:|---:|---:|---:|---:|
| 11 | +0.145470 | +0.107028 | +0.077376 | +0.042686 | **+0.071120** |
| 22 | +0.144066 | +0.120179 | +0.093786 | +0.033769 | **+0.056917** |
| 33 | +0.137273 | +0.102976 | +0.056924 | +0.042297 | **+0.085615** |

The primary pooled-seed mean is **+0.071217 AP**.  Across the 30
source-by-seed primary effects, the mean is `+0.070879`, median `+0.070451`,
range `+0.040248..+0.093878`; all 30 are positive and all 30 exceed the old
`+0.02` reference margin.  The exploratory source-first bootstrap (10,000
draws, seed 901) gives mean `+0.070861` and 95% interval
`[+0.056497, +0.084523]`.  This interval is descriptive only; no new
confirmatory p-value or GO gate was created.

The O2 control improves over H14 by `+0.076029 AP` on average.  Adding I on
top of O2 therefore removes much, but not all, of the original internal-state
increment; the residual-controlled increment remains well above the old
practical reference.

## Scope and caveats

The high-dimensional `lbfgs` fits emitted convergence warnings for some arms at
the frozen `max_iter=1000`; no solver, C grid, feature, or seed was changed in
response.  This result tests linearly accessible information under a matched
L2 probe, not information-theoretic sufficiency of residuals.
