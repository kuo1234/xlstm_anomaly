# Scientific assessment

## Observation

Under the fixed nonlinear tree probe, adding `internal234` to `H+O1r` improves
test AP for every source and detector seed in this three-seed screen. The
source-level mean increment is `+0.01516504` for xLSTM and `+0.01125203` for
matched LSTM. The xLSTM effect is below the historical `+0.02` descriptive
reference on average, while the matched-LSTM effect is also below it.

The nonlinear probe improves the interpretation of the control comparison but
does not create a new confirmatory gate. The xLSTM linear A+S S2 reference was
`+0.02596099`; the bounded nonlinear result is smaller. The matched-LSTM
linear reference was `+0.01076562`; its nonlinear result is very similar.

## Interpretation

The xLSTM result is best classified as **attenuated nonlinear survival**:
the effect does not close under this bounded nonlinear decoder, but the
increment is reduced relative to the linear probe and is below the historical
`+0.02` reference. This means the previous A+ increment is not shown to be
solely a linear-accessibility artifact of O1r, but the experiment does not show
that residual observables lack the information.

The matched-LSTM result is a small, consistently positive incremental utility
under the same nonlinear decoder. It remains compatible with a generic
recurrent-state contribution under this tested probe, but it is not evidence
of xLSTM superiority.

Scenario effects are heterogeneous but positive in every reported scenario.
For xLSTM, gradual is largest; for matched LSTM, recurring is largest. The
three seeds do not justify a claim about a uniquely favored regime.

## Claim boundaries

This is a bounded nonlinear-decoder stress test. It does not establish mutual
information, unique information, causality, intrinsic representation quality,
safe adaptation, long-context benefit, or xLSTM-over-LSTM superiority. It does
not reopen G1/H2/H3a/H3b and does not incorporate mLSTM-specific features.

The result supports only the narrow statement that, under the frozen source
split and fixed HGB decoder, `internal234` retains positive incremental
predictive utility beyond temporally matched O1r for both tested backbones.

## Next decision

Do not automatically run another probe. P1r remains the unresolved
scaled-input observable control if the project explicitly chooses to continue;
real-data external validation would answer a different question. The current
evidence does not justify moving directly to safe adaptation or claiming a
backbone-specific mechanism.
