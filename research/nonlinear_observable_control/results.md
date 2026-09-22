# Nonlinear observable-control results

## Scope

Six fixed runs completed on the read-only A+ cache: xLSTM and matched LSTM,
detector seeds `11,22,33`. No detector inference, retraining, P1r, nonlinear
model comparison, or G1 artifact modification occurred. The implementation
seal was `61e57ef7894c8db7faaeb5efc2fd63fb5f58956e`; the run records retain it
as `protocol_seal`.

The probe was exactly `HistGradientBoostingClassifier` with the frozen
parameters in `protocol.md`, `early_stopping=False`, `random_state=901`, and
only `max_iter ∈ {100,300}`. Each candidate used train-only fitting and pooled
validation AP selection; test data was evaluated once after selection.

## Primary results

| architecture | source-level mean ΔAP | crossed 95% interval | pooled seed 11 | pooled seed 22 | pooled seed 33 |
|---|---:|---:|---:|---:|---:|
| xLSTM | +0.01516504 | [+0.01248823,+0.01822553] | +0.01520113 | +0.01476300 | +0.01520820 |
| matched LSTM | +0.01125203 | [+0.00895238,+0.01347492] | +0.01125104 | +0.01163674 | +0.01121702 |

All 30 source-by-seed effects are positive for each architecture. The old
linear A+S S2 references were xLSTM `+0.02596099` and matched LSTM
`+0.01076562`; they were read-only references and were not refit.

Selected pooled test AP by arm:

| architecture | seed | AP(H+O1r) | AP(H+O1r+I) |
|---|---:|---:|---:|
| xLSTM | 11 | 0.93448083 | 0.94968195 |
| xLSTM | 22 | 0.93838540 | 0.95314840 |
| xLSTM | 33 | 0.93806905 | 0.95327725 |
| matched LSTM | 11 | 0.94411540 | 0.95536643 |
| matched LSTM | 22 | 0.94655021 | 0.95818695 |
| matched LSTM | 33 | 0.94682311 | 0.95804012 |

## Selection path

| architecture | seed | H+O1r selected max_iter | H+O1r+I selected max_iter |
|---|---:|---:|---:|
| xLSTM | 11 | 100 | 100 |
| xLSTM | 22 | 300 | 100 |
| xLSTM | 33 | 300 | 300 |
| matched LSTM | 11 | 100 | 300 |
| matched LSTM | 22 | 300 | 300 |
| matched LSTM | 33 | 300 | 300 |

For every candidate and selected refit, `n_iter_` equaled its requested
`max_iter`, `do_early_stopping_` was false, and no internal validation split
was used. This records budget exhaustion, not a claim of convergence in the
optimization-theory sense.

## Comparison with linear A+S

The nonlinear xLSTM increment is positive and consistent, but its mean is
about `0.010796` AP below the linear S2 reference (roughly a 41.6% reduction).
The matched-LSTM nonlinear increment is essentially unchanged from its linear
S2 reference (about `+0.000486` AP higher). Thus the bounded nonlinear decoder
attenuates the xLSTM linear increment, while the matched-LSTM increment remains
small and similar in magnitude.

The nonlinear observable-only arm was not treated as a claim of observable
sufficiency or insufficiency. A stronger decoder can learn more from O1r, and
this experiment measures only incremental predictive utility under the fixed
HGB family.
