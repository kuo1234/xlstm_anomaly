# A+S protocol

This is a bounded post-hoc audit of the committed A+ temporally matched
observable-control experiment. It starts at A+ commit
`04e0abbd7a9a6a8c8d00052cd1b20c51e0a71d28` and uses review evidence from
`f1967b6a9d3801bf1a3c962def32fc3a08b30732`. Neither reviewed branch is
modified. No model inference, training, G1 rerun, nonlinear probe, or change
to the original A+ files is permitted.

## S0: statistical reassessment without fitting

The primary estimand is the mean of the ten source-level AP differences in each
of the existing 10×3 source-by-detector-seed matrices. The pooled test AP
difference retained in each A+ run is descriptive only. A corrected crossed
bootstrap draws ten source rows and three detector-seed columns independently
once per replicate, then averages the resulting intersection cells. A second
bootstrap resamples source rows while conditioning on all three observed seeds.
Both use 10,000 draws and seed 901. The historical A+ nested-bootstrap result
is preserved as a reference, not overwritten. With only three seed levels,
neither interval is described as a precisely calibrated 95% population interval.

## S1: convergence-only audit

The exact A+ arms (`H+O1r`, `H+O1r+I`), architectures (xLSTM and matched LSTM),
detector seeds (11, 22, 33), rows, folds, feature construction, read-only
cache, train-only StandardScaler, L2 `lbfgs` logistic regression, `tol=1e-4`,
C grid `{0.01, 0.1, 1, 10}`, validation-only C selection, and smaller-C tie
rule are unchanged. Only `max_iter` changes from 1,000 to 10,000.

Every validation candidate and selected final refit records C, validation AP,
`n_iter_`, `ConvergenceWarning`, max-iteration status, coefficient hash, and
intercept hash. Test AP is computed only after validation selects C. Any
candidate or selected final fit that is not converged makes S1
`CONVERGENCE_UNRESOLVED` and prevents S2.

## S2: fixed C-grid sensitivity

S2 runs only when every S1 candidate and selected final refit converges. It
uses the same fitting process and rows but the predeclared one-step-expanded
grid `{0.001, 0.01, 0.1, 1, 10, 100}`. The grid is not expanded again after
observing results. S2 is sensitivity evidence, not a retroactive change to
the A+ protocol or a new confirmatory test.

## Interpretation

The +0.02 value remains only a historical descriptive reference. The audit
reports separately whether xLSTM and matched LSTM are solver-stable and
grid-stable; no new significance gate or Holm family is created. The nested
superset regression is diagnosed by comparing the A+ and S1/S2 selected fits;
it is not assumed to be an optimizer artifact.
