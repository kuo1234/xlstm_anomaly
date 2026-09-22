# A+S red-team review

## Scope and provenance

- Starting scientific commit: `04e0abbd7a9a6a8c8d00052cd1b20c51e0a71d28`.
- Independent review evidence: `f1967b6a9d3801bf1a3c962def32fc3a08b30732`.
- The A+ cache is read-only; no model forward, training, label regeneration or
  nonlinear probe was run.
- `git diff 04e0abb -- reports/phase_g1` is empty.
- Original A+ six per-run JSON files are unchanged.

## Checks attempting to falsify the audit

1. `_ensure_rows` compares every train/validation/test row metadata object to
   the committed A+ reference before fitting; a row-key change raises.
2. Both arms are built from the same collected records and their keys are
   checked against the fold keys before fitting.
3. StandardScaler is fit on train only; C is selected from pooled validation
   AP; test AP is evaluated only after selected-C refit.
4. Every candidate and selected final fit serializes warning, cap, iteration,
   coefficient and intercept metadata. All recorded fits converge.
5. The C grid is exactly the declared S1 grid and the one-step declared S2
   grid; it was not expanded again after seeing results.
6. The crossed S0 bootstrap samples source rows and seed columns once per
   replicate and is deterministic at seed 901.
7. The historical H+O1+I comparison is read-only and is reported separately;
   it is not replaced by a post-hoc re-fit.
8. No command in this audit writes `reports/phase_g1`.

An initial attempt to run the complete S1 loop was manually interrupted after
its first printed fit while assessing runtime. It produced no result file and
none of its partial values were used. The authoritative S1 outputs came from
the complete, bounded `fit-one` runs committed in `0353114`; S2 seed 11, 22
and 33 were likewise completed and checkpointed before final aggregation.

## Remaining limitations

Only three detector seeds are available. S1/S2 report pooled-test AP per seed;
the source-level crossed uncertainty applies to the historical A+ matrix, not
to newly refit source-level S1/S2 arrays. The +0.02 value remains a descriptive
reference only. A positive linear-probe increment does not establish unique
information, causality, or superiority of xLSTM.
