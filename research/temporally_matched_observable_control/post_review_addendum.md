# Post-review addendum (2026-09-23, docs only)

The files in this directory are the historical A+ record and are intentionally unchanged. Read
them together with the later evidence below.

- **Independent review:** commit `f1967b6a9d3801bf1a3c962def32fc3a08b30732`
  (`independent_review.md`, `independent_review_numbers.csv`,
  `independent_review_recompute.py` in this directory once merged). Verdict: PASS WITH
  REQUIRED FIXES.
- **Interval:** the `results.md` interval `[+0.022959, +0.030312]` comes from a nested
  source-then-seed bootstrap that does not match the crossed design. The design-appropriate
  crossed interval is `[+0.01950949, +0.03258161]` for xLSTM and `[+0.00780522, +0.01281719]`
  for matched LSTM (`research/aplus_solver_convergence_audit/statistical_reassessment.md`).
- **Estimand:** the primary estimand is the source-level 10×3 mean (`+0.02671045` /
  `+0.01022015`). The per-seed columns in `results.md` are pooled deltas and are descriptive.
- **Convergence:** A+S found every `lbfgs` fit converged at `max_iter=10000`, with the result
  qualitatively stable under the expanded C grid. The nested-superset regression
  `AP(H+O1r+I) < AP(H+O1+I)` persists for xLSTM and is disclosed in A+S `results.md`.
- **Backbone asymmetry:** the "xLSTM survives, LSTM does not" reading in
  `scientific_assessment.md` is a linear-probe statement. Under the fixed HGB decoder
  (`research/nonlinear_observable_control/`), the xLSTM increment falls to +0.015165 and the
  LSTM increment stays at +0.011252. The gap shrinks from +0.01649 to +0.00391 and tracks the
  lower xLSTM observable-only baseline. See `research/nonlinear_observable_control/post_review_addendum.md`.
- **Scope:** O1r is residual-derived. The input-derived control `P1r` has not been run.
