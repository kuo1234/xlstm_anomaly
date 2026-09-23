# A+S results

## Scope

A+S reuses the committed A+ cache, rows, folds, features, scalers and probe
definition. It performs no model inference or training and does not modify any
`reports/phase_g1/*` artifact. S1 changes only `max_iter` to 10,000. S2 uses
the fixed, predeclared expanded C grid `{0.001, 0.01, 0.1, 1, 10, 100}`.

## Convergence

All six S1 runs and all six S2 runs completed. Every validation candidate and
every selected final refit recorded `ConvergenceWarning = false`,
`hit_max_iter = false`, and `converged = true`. Therefore S1 is not
`CONVERGENCE_UNRESOLVED`, and S2 was allowed under the protocol.

## Pooled test deltas

These are pooled-test AP diagnostics from each fixed detector seed; the S0
source-level estimate above remains the primary A+ reassessment.

| backbone | seed | original A+ ΔAP | S1 ΔAP | S2 ΔAP |
|---|---:|---:|---:|---:|
| xLSTM | 11 | +0.02895224 | +0.02812832 | +0.02812832 |
| xLSTM | 22 | +0.01957113 | +0.01567009 | +0.01629509 |
| xLSTM | 33 | +0.03182504 | +0.03015386 | +0.03345957 |
| **xLSTM mean** | — | **+0.02678280** | **+0.02465076** | **+0.02596099** |
| LSTM | 11 | +0.01148583 | +0.01089080 | +0.01132454 |
| LSTM | 22 | +0.01059071 | +0.00988728 | +0.01194444 |
| LSTM | 33 | +0.00896195 | +0.00902789 | +0.00902789 |
| **LSTM mean** | — | **+0.01034616** | **+0.00993532** | **+0.01076562** |

All 3/3 detector-seed deltas are positive in S1 and S2 for both backbones.
The xLSTM S1/S2 means remain above the historical descriptive +0.02
reference, while the LSTM means remain below it (0/3 seed means at or above
the reference in both stages).

## Selected C and boundary sensitivity

Original A+ → S1 → S2 selected C values, in seed order 11/22/33:

| backbone/arm | original | S1 | S2 |
|---|---|---|---|
| xLSTM H+O1r | 1, 1, 10 | 1, 10, 10 | 1, 100, 100 |
| xLSTM H+O1r+I | 0.01, 0.01, 0.01 | 0.01, 0.01, 0.01 | 0.01, 0.001, 0.001 |
| LSTM H+O1r | 1, 10, 10 | 1, 10, 1 | 1, 10, 1 |
| LSTM H+O1r+I | 1, 0.1, 0.1 | 0.01, 10, 1 | 0.001, 0.001, 1 |

The xLSTM baseline reaches the new upper boundary for seeds 22/33, and its
internal arm reaches the new lower boundary for seeds 22/33. The xLSTM
increment nevertheless remains positive and above +0.02 on average. The LSTM
selected C values move, especially for its internal arm, but its qualitative
small-positive, below-+0.02 interpretation is unchanged.

The complete candidate paths, iteration counts, warning flags and coefficient
hashes are in `convergence_table.csv` and the per-run JSON files.

## Nested-superset regression diagnostic

The historical xLSTM comparison
`AP(H+O1r+I) - AP(H+O1+I)` averaged `-0.00524637`. It remains negative for
all three seeds after converged S1 fitting (mean `-0.00524637`) and after S2
(mean `-0.00395990`, all three seeds still negative). Thus the xLSTM
regression is not explained by the original selected fit being non-converged;
the expanded grid changes its magnitude but does not remove it.

For LSTM the historical mean was `-0.00075971`, S1 was `-0.00096502`, and S2
was `-0.00013472`; S2 has one slightly positive seed. This is a small,
heterogeneous diagnostic effect rather than evidence of a common optimizer
failure.
