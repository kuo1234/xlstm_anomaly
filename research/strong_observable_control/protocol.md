# Strong observable residual control (exploratory)

This branch tests whether the common G1 recurrent-state increment survives a
much richer, directly observable reconstruction-residual control.  It is a
post-G1 exploratory stress test; it does not alter G1, H2, H3a, or H3b.

## Frozen design

- Frozen best checkpoints, no optimizer and no retraining.
- Detector seeds: `11, 22, 33`; both `xLSTM` and matched `LSTM`.
- Source folds: train `1000..1009`, validation `2000..2004`, test
  `3000..3009`.
- Four shifted scenarios: abrupt, gradual, recurring, correlation.
- Conditions: none, spike, collective, dependency, mixture.
- Window 64, stride 1, right-edge timestamp; mixed windows are excluded from
  the primary anomaly-vs-drift cohort.
- Extraction receives observations only.  Evaluator labels are joined after a
  stream has been cached.
- Residual is `R = X_scaled - Xhat_scaled` in the exact normalized model input
  space.  `mean(R**2, axis=(1,2))` must reproduce the scalar score.

## Frozen observable ladder

`H14` is the existing G1 scalar score history.  `O1` is the 128-dimensional
compact residual summary and `O2` is `[R.flatten(C), R.square().flatten(C)]`
with 1024 dimensions.  The exact column order and zero-variance rule are in
`residual_schema.md`.

For each architecture and detector seed the same pooled L2 logistic probe is
fit for each arm independently: train-only `StandardScaler`, `C` in
`{0.01, 0.1, 1, 10}`, pooled validation AP selection, exact ties to smaller
`C`, and one test evaluation.  No test result selects a feature or solver.

Primary arms are `H`, `H+I`, `H+O1`, `H+O1+I`, `H+O2`, and `H+O2+I`, where `I`
is the existing common internal234 representation.  The primary stress
contrast is `AP(H+O2+I) - AP(H+O2)`.  This is a linearly accessible,
low-capacity-probe diagnostic, not an information-theoretic sufficiency test.

No new confirmatory p-value family or GO/STOP rule is created.  Source-level
effects, seed/scenario tables, and an exploratory source-first bootstrap are
reported descriptively.  The old `+0.02` margin is only a reference.

## Execution boundary

The observation cache is written once per seed/backbone/source/scenario/
condition and contains no labels.  Analysis regenerates evaluator metadata
only after extraction.  G1 artifacts and conclusions are read-only.
