# Extraction validation contract

Before analysis, every stream must pass these mechanical checks:

- output shape equals input shape and all values are finite;
- residual shape is `[N,64,8]` and finite;
- residual MSE equals the saved scalar score within `atol=1e-5,
  rtol=1e-4`;
- common internal base has exactly 18 finite columns;
- timestamps are exactly `63..N-1`, ordered, unique, and right-edge causal;
- the observation extractor accepts only the observation matrix and cannot
  access evaluator labels or metadata;
- frozen model parameters are unchanged by extraction;
- the same observation stream under dummy opposite labels produces identical
  score, residual, and internal arrays.

The cache is observation-only.  Analysis joins truth after extraction, applies
the same `anomaly`/`drift` primary cohort used by G1, and intersects finite
warmup masks identically for all arms.  Row keys contain seed, source,
scenario, condition, and timestamp and are checked before fitting.

The high-dimensional O2 solver is `sklearn.linear_model.LogisticRegression`
with L2 penalty, `lbfgs`, `max_iter=1000`, and the frozen four-value C grid.
Any operational benchmark is recorded separately and cannot alter the arm or
solver definitions after test outcomes.
