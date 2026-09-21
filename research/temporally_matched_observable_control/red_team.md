# A+ red-team review

## Checks performed

1. `internal234` was traced through `expand_internal`: current base18 plus
   causal rolling mean/std/slope at decision widths 4, 8, 16, and 32.  Its
   widest raw union is `[t-94,t]`.
2. `expand_o1r` applies the same operator to every O1 column.  It computes the
   four rolling widths before the evaluator mask and transposes the grouped
   result into feature-major order.  O1r is 1664 columns and has no future row.
3. The cache loader verifies contiguous right-edge timestamps.  The first
   finite O1r timestamp is 94.  Future-row perturbation and target-time tests
   pass.
4. Every architecture/seed has identical ordered row-key hashes for the two
   new arms; the hashes and row counts match the historical H/H+I cohorts.
5. The extractor-side cache contains observations/scores/states only.  Labels
   are joined after observation arrays are transformed; no labels, event
   metadata, or regime identifiers are function arguments to `expand_o1r`.
6. All six runs used the same source folds, four scenarios, five conditions,
   three seeds, StandardScaler-on-train, L2 `lbfgs`, C grid, pooled
   validation selection, and one test evaluation.  No per-scenario tuning was
   added.
7. The historical G1 tree is unchanged (`git diff --quiet 2810c34 --
   reports/phase_g1`), and the A+ script never writes there.

## Falsification attempts and residual risks

* A nominally equal W64 tensor would have failed the temporal check; the test
  instead checks the actual `[t-94,t]` union and causal target alignment.
* A row-mask mismatch would have changed row-key hashes; the two-arm hashes
  are byte-identical for every fold and run.
* A different probe budget would have changed C selection; each result stores
  the complete validation candidates, selected C, scaler hashes, coefficient
  hashes, and row counts.
* O1r is not raw-input observable control.  It cannot support the stronger
  statement that all detector observables are insufficient.
* The fixed high-dimensional `lbfgs` fits emitted convergence warnings at the
  existing 1,000-iteration cap.  This is a documented engineering limitation,
  not a result-dependent solver change; a future nonlinear or solver-sensitivity
  audit should be separately specified.
* The study is exploratory.  No p-value, Holm family, or confirmatory gate was
  introduced after observing the outcome, and the matched-LSTM asymmetry is not
  promoted to an xLSTM-specific claim.

## Verdict

The implementation and row/temporal/probe checks support treating the A+ output
as a valid exploratory temporally matched-control analysis.  It does not
support an information-theoretic or causal conclusion.
