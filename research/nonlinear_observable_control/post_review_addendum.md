# Post-review addendum (2026-09-23, docs only)

This addendum records corrections from the consolidation review
(`research/consolidation_review_2026-09/consolidation_review.md`). It changes no result,
protocol, run file or seal. All numbers come from `reviewer_recompute.py` applied to committed
artifacts.

## 1. The linear comparison mixes estimands

The A+S S2 references (`+0.02596099` xLSTM, `+0.01076562` matched LSTM) are **means of pooled
per-seed test deltas**. S1/S2 did not persist source-level APs. `results.md` compares them with
the NL **source-level** mean. Like-for-like values:

| comparison | xLSTM | matched LSTM |
|---|---:|---:|
| pooled: NL `+0.01505744` / `+0.01136827` minus S2 | −0.01090355 (−42.0 %) | +0.00060264 |
| as documented (source-level NL − pooled S2) | −0.01079596 (−41.6 %) | +0.00048641 |
| source-level: NL − A+ linear, same 30 cells | −0.01154542, crossed [−0.01808989, −0.00439573], 27/30 cells lower | +0.00103188, crossed [−0.00223226, +0.00382090], 11/30 cells lower |

The difference between estimands is about 0.0001 AP, so it does not affect any conclusion.

## 2. Where the xLSTM attenuation comes from

Mean pooled test AP over seeds 11/22/33:

| arm | xLSTM S2 → HGB | LSTM S2 → HGB |
|---|---|---|
| `H+O1r` | 0.90779605 → 0.93697843 (+0.02918238) | 0.93584318 → 0.94582957 (+0.00998640) |
| `H+O1r+I` | 0.93375704 → 0.95203587 (+0.01827883) | 0.94660880 → 0.95719784 (+0.01058904) |

For xLSTM, the nonlinear decoder recovers more from O1r alone than the whole linear internal
increment. The attenuated share is O1r information that the linear probe could not extract, not
spurious internal signal. The linear xLSTM seed heterogeneity also disappears under HGB. Pooled
per-seed deltas go from +0.0281 / +0.0163 / +0.0335 (S2) to +0.0152 / +0.0148 / +0.0152 (HGB).

## 3. Backbone comparison (not a superiority test)

The xLSTM − LSTM increment gap is +0.00391301 under HGB, with reviewer crossed interval
[+0.00036699, +0.00743939], down from +0.01649030 under A+ linear. O1r is built from each
backbone's own residuals, so the observable-only baselines differ. The xLSTM HGB `H+O1r` is
0.00885 AP lower, and absolute `H+O1r+I` is higher for the LSTM in every seed. As a share of
headroom `1 − AP(H+O1r)`, the HGB increments are 0.2391 (xLSTM) and 0.2100 (LSTM), a ratio of
1.14×. The gap is consistent with a weaker observable baseline and does not support xLSTM
superiority.

## 4. Budget

With `early_stopping=False`, `n_iter_ == max_iter` is the fixed boosting budget and not a
convergence failure. The increment does not depend on the selection path. The validation-fold
increment at a fixed budget is +0.01743310 (100) versus +0.01610632 (300) for xLSTM, and
+0.00951683 versus +0.00937298 for LSTM. The xLSTM value falls from 100 to 300 in 3/3 seeds.
The attenuation is therefore not shown to have saturated at this decoder budget. This
observation is descriptive and does not justify further decoders.
