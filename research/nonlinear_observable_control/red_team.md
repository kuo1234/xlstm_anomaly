# Red-team review

- **Protocol provenance:** all six result files bind to implementation/protocol
  seal `61e57ef7894c8db7faaeb5efc2fd63fb5f58956e`; no result-dependent
  hyperparameter change was made.
- **Early stopping:** every candidate records `early_stopping=false` and
  `do_early_stopping=false`; `n_iter_` equals the requested budget. No sklearn
  internal validation split was enabled.
- **Fold leakage:** the A+ collector preserves train `1000..1009`, validation
  `2000..2004`, and test `3000..3009`; test AP is computed only after the two
  validation candidate APs select `max_iter`.
- **Arm fairness:** both arms use the same HGB constructor, random state,
  rows, labels, and no-scaler preprocessing. Only `internal234` differs.
- **Row identity:** each run rechecks A+ row counts and ordered row-key hashes;
  both arms use the same fold keys. The committed A+ and G1 trees remain
  unchanged.
- **Bootstrap unit:** the aggregate uses crossed source rows and seed columns,
  not the historical nested resampling. Source-only intervals are separately
  labelled, and three observed seeds are explicitly caveated.
- **Pooled versus source-level:** the source-level mean is primary; pooled
  per-seed deltas are descriptive only.
- **Interpretation:** no result is called information-theoretic, causal, or
  xLSTM-specific. The historical `+0.02` is descriptive only.
- **Execution discipline:** six runs were executed one at a time and each run
  was checkpointed before the next. The 159GB cache remained read-only.

Remaining limitation: `max_iter=100` or `300` is a fixed budget choice, and
`n_iter_ == max_iter` records budget exhaustion rather than proving numerical
convergence. Extending the budget was not authorized after observing outcomes.

The focused nonlinear/A+/strong-observable test set passed. A repository-wide
pytest collection was also attempted but remains blocked by pre-existing
optional dependency gaps (`tta` and `xlstmad`) in unrelated Phase D/mLSTM test
modules; no unrelated code was changed to bypass those imports.
