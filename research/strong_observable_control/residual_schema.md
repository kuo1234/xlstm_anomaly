# Residual feature schema (frozen before label analysis)

For every right-edge W64 window, let `R = X_scaled - Xhat_scaled`, shape
`[64, 8]`.  All reductions use float64 on the cached float32 residual for
deterministic probe inputs.  Raw O2 flattening is C-order: time first, then
channel.

## O1 (128 columns)

For channels `0..7`, append these eight statistics in the stated order:

1. mean signed residual;
2. population standard deviation;
3. RMS;
4. mean absolute residual;
5. final signed residual;
6. final absolute residual;
7. OLS slope against `t=0..63` (centered denominator);
8. lag-1 Pearson autocorrelation between `R[:-1,c]` and `R[1:,c]`.

Then append the upper triangle of the population covariance matrix, including
the diagonal (`36` columns, row-major `(i,j)` with `i<=j`), followed by the
upper triangle of the correlation matrix excluding the diagonal (`28` columns,
`i<j`).  A zero-variance correlation entry is exactly `0.0`; finite diagonal
entries are `1.0`.

## O2 (1024 columns)

`R.reshape(512, order="C")` followed by
`(R*R).reshape(512, order="C")`.

## Probe arms

`H` = H14; `I` = existing G1 common internal234; `H+I`, `H+O1`,
`H+O1+I`, `H+O2`, and `H+O2+I` are the required arms.  Optional raw O2-only
arms are not needed for the primary decision.

The residual schema is independent of labels, event metadata, scenario names,
and detector outcomes.  No per-scenario feature deletion or tuning is allowed.
