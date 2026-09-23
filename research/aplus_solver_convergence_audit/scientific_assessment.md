# Scientific assessment

## Q1 — solver convergence

Pass. Every S1 candidate and selected final refit for both backbones converged
at `max_iter=10000`, with no convergence warning and no fit reaching the
iteration cap. The xLSTM A+ increment remains positive after this audit.

## Q2 — C-grid sensitivity

The fixed expanded grid changes selected C values and some pooled APs, but it
does not change the qualitative interpretation. xLSTM remains positive with a
mean above the historical +0.02 descriptive reference in both S1 and S2;
matched LSTM remains positive but below that reference. No further grid
expansion was performed.

## Q3 — matched LSTM

The matched-LSTM increment is stable as a qualitative finding: it is positive
for all three seeds after convergence and remains below +0.02 on average. Its
selected C values and APs are more grid-sensitive than xLSTM, so the exact
effect size should not be over-precisely reported.

## Classification

Using the preregistered audit meaning—no unresolved convergence failure and no
qualitative change under the fixed expanded grid—the classifications are:

```text
xLSTM: STABLE
LSTM:  STABLE
```

These labels do not mean every selected C is interior or that numerical AP is
unchanged. They mean the scientific interpretation does not depend on a
non-converged fit and survives the fixed grid sensitivity.

## Boundaries

This is a post-hoc exploratory audit. It does not add a Holm member, create a
new GO gate, or alter the original A+ result. The original A+ source-level
estimate and historical nested bootstrap remain intact. The xLSTM
nested-superset regression persists after convergence and therefore remains a
real diagnostic observation, not an optimizer artifact established by this
audit.

The nonlinear observable-control experiment is not automatically justified as
a repair for A+S and was not run. It could be considered only under a new
reviewed protocol because it asks a different, nonlinear-probe question. No
claim here is information-theoretic, causal, or a reopening of H3a/H3b.
