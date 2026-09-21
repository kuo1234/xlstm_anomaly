# A+ protocol: temporally matched observable control

This is a post-G1 exploratory experiment.  It tests only whether the common
`internal234` increment survives when the residual observable control receives
the same causal decision-time span.  It does not alter G1, H2, H3a, or H3b and
does not create a confirmatory p-value family.

## Frozen information sets

At right-edge decision timestamp `t`, the frozen detector window is
`x[t-63:t+1]`.  The actual internal base18 row therefore depends only on raw
observations `[t-63,t]`.  `internal234` contains the current base18 plus, for
each base column, causal mean/std/OLS slope over decision rows ending at `t`
with widths 4, 8, 16, and 32.  The widest component uses rows `t-31..t`, so
its raw union is `[t-94,t]`; the first fully finite decision is `t=94`.

`O1` is the existing 128-column residual summary of the current W64 window.
`O1r` applies the identical feature-major transform to the dense O1 sequence:

```
O1r_t = [O1_t, rolling mean/std/slope(O1_{t-3:t}),
         rolling mean/std/slope(O1_{t-7:t}),
         rolling mean/std/slope(O1_{t-15:t}),
         rolling mean/std/slope(O1_{t-31:t})]
```

The rolling operation includes the current decision and never a future row.
Its dimension is `128 × 13 = 1664`, and its raw receptive field is also
`[t-94,t]`.  O1r remains purely observation/residual-derived; no labels,
event metadata, regime identifiers, or future observations enter extraction.
The transform is applied before the primary anomaly/drift row mask, so the
warmup and temporal alignment cannot be changed by filtering.

## Arms and fitting

The new arms are `H+O1r` and `H+O1r+I`, with the existing H/H+I and raw O1/O2
results retained as read-only references.  H14 and internal234 are constructed
with the exact existing implementations.  All new arms use the same examples,
source-disjoint folds (`1000..1009` train, `2000..2004` validation,
`3000..3009` test), scenarios, W64/stride-1 alignment, primary anomaly-versus-
legitimate-drift cohort, and detector seeds `11,22,33` for both xLSTM and
matched LSTM.  Mixed rows remain excluded.

Each new arm uses the existing L2 logistic regression (`lbfgs`, `max_iter=1000`),
train-only `StandardScaler`, C grid `{0.01, 0.1, 1, 10}`, pooled validation AP
selection, and smaller-C exact-tie rule.  The only primary metric is AP.  The
primary contrast is `AP(H+O1r+I) − AP(H+O1r)`, recorded by test source and
detector seed; source-first hierarchical bootstrap (10,000 draws, seed 901)
is descriptive only.  No p-values, Holm correction, or post-outcome tuning is
introduced.  The old `+0.02` value is a descriptive reference.

Support for temporal-span survival is classified descriptively when the mean
primary contrast is at least `+0.02` and at least two of three pooled-seed
contrasts are at least `+0.02`.  Otherwise the temporal-span explanation
remains unresolved or is supported descriptively; this is not a GO/STOP rule.

The existing dense observation cache is reused read-only.  Historical
`reports/phase_g1/*` files and prior strong-observable result files are never
overwritten.
