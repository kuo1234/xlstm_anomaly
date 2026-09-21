# A+ scientific assessment

## Observation

The temporal span was matched in code, not just by nominal dimensions.  The
internal arm's widest causal expansion sees raw observations `[t-94,t]`; O1r
uses the same current-plus-4/8/16/32 decision-width causal expansion over all
128 O1 columns and therefore sees the same raw union `[t-94,t]`.  Both arms use
the same right-edge decision rows, masks, folds, and low-capacity probe.

The primary increment is positive for every source-by-seed unit.  Its mean is
`+0.026710` for xLSTM and `+0.010220` for matched LSTM.  The descriptive
bootstrap intervals are `[+0.022959,+0.030312]` and `[+0.007861,+0.012566]`.

## Statistical evidence

These intervals are an exploratory source-first hierarchical bootstrap summary,
not a new confirmatory family.  No p-values, Holm adjustment, or GO/STOP gate
was added.  The old `+0.02` margin is a reference only.  xLSTM has 2/3 seed
means at or above that reference; LSTM has 0/3.  All individual source-seed
directions are positive, but the LSTM effect is consistently below the
reference margin.

## Interpretation

For xLSTM, the temporally matched residual control does not explain the full
previous internal increment under this fixed linear probe: a positive
`+0.026710` increment remains, with all three seed directions positive and an
exploratory interval above zero.  This supports the narrow descriptive label
`INTERNAL234_GT_O1R` under the frozen A+ reference criterion.

For the matched LSTM, a positive increment remains but is smaller
(`+0.010220`) and below the old practical reference in every seed mean.  Thus
the temporal-span explanation is not cleanly ruled out for the LSTM at the
reference margin.  The two backbones are heterogeneous under A+; this is not a
generic superiority result.

The result supports only the following wording:

> Under a fixed L2 probe, xLSTM internal summaries retain additional linearly
> accessible anomaly-vs-drift evidence beyond an O1 residual control given the
> same causal temporal span; the matched LSTM retains a smaller positive
> increment below the historical practical reference.

This is not a causal test and does not establish that residuals lack the
information.  It tests linear accessibility under one fixed detector,
synthetic source split, and three detector seeds.

## Remaining alternatives and limits

* O1r is a residual-derived observable control, not the raw scaled input
  trajectory.  A+ therefore does not close the separate input-observability
  gap.
* The 1664-dimensional observable arm and 234-dimensional internal arm are
  intentionally not dimension matched; both use the same classifier family,
  scaler rule, C grid, and validation budget.
* Some fixed high-dimensional `lbfgs` candidates reached the frozen iteration
  cap.  This was recorded rather than repaired post hoc.
* Three seeds and a single synthetic generator remain exploratory.  No new
  architecture, nonlinear probe, mLSTM feature, long-context, persistent-state,
  or adaptation claim follows.

## Claim-level consequence

A+ supplies exploratory evidence for the previously untested temporal-span
claim (L1c), but it does not promote it to a confirmatory result.  It preserves
the authoritative G1 H2=GO, H3a=STOP, H3b=LOCKED status, and leaves L2/L3/L4/L5
unchanged.  The narrow L1c reading is asymmetric: xLSTM survives the
descriptive reference while matched LSTM does not.  The next scientifically
justified stress test is a predeclared nonlinear observable-only control on
the same matched O1r arms, subject to a separate protocol review; do not start
it from this branch automatically.
