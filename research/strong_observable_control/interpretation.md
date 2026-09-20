# Interpretation

## Classification

- xLSTM: **STRONG_OBSERVABLE_SURVIVAL**.  The strong residual-control
  increment is `+0.071217 AP` pooled over seeds (source-by-seed macro
  `+0.070879`), positive for every source/seed unit and every detector seed.
- matched LSTM: **STRONG_OBSERVABLE_SURVIVAL**.  The corresponding pooled mean
  is `+0.053028 AP` (source-by-seed macro `+0.052761`), again positive for all
  source/seed units and all detector seeds.

Both backbones reproduce the old approximately `+0.14` H14-relative internal
increment, and both retain a positive increment after the 1,024-dimensional
observable residual trajectory is supplied to the same low-capacity L2 probe.
The result therefore supports the narrower statement:

> Internal recurrent summaries provide additional linearly accessible
> anomaly-vs-drift evidence beyond a strong observable reconstruction-residual
> control under the matched probe protocol.

It does **not** show that residuals fundamentally lack the information.  A
nonlinear observable-only probe could recover additional structure and remains
an important follow-up.

The comparable survival in xLSTM and matched LSTM supports a generic recurrent-
representation interpretation for the common scalar internal schema.  It does
not establish equivalence, superiority, or a global xLSTM-over-LSTM claim.
Post-G1 mLSTM-specific evidence remains a separate exploratory line and is not
included here.

Recurring regimes carry the largest remaining increment for both architectures;
this is a descriptive hypothesis only.  Correlation-only behavior is
heterogeneous and should not be overinterpreted.

The original authoritative G1 result remains unchanged: H2 GO, H3a STOP, and
H3b LOCKED.  This stress test does not reopen H3b, establish online safety,
long-context memory, persistent state, or deployment benefit.
