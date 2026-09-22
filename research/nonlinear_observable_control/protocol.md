# Nonlinear Observable Control Protocol

Status: exploratory; fixed before nonlinear fitting.

## Question

Test whether the A+ temporally matched residual-derived observable control
(`H+O1r`) leaves incremental predictive utility for the frozen common internal
representation (`internal234`) when both arms use the same bounded nonlinear
decoder. This is a low-capacity predictive-utility test, not an
information-theoretic, causal, or architecture-superiority test.

## Frozen data and rows

- Source folds: train `1000..1009`, validation `2000..2004`, test `3000..3009`.
- Detector seeds: `11, 22, 33`; architectures: xLSTM and matched LSTM.
- The read-only A+ cache is the only model-output source. No detector inference,
  retraining, label regeneration, or `reports/phase_g1/*` access is required.
- Feature construction, warmup filtering, primary anomaly-versus-drift cohort,
  timestamp keys, scenarios, and conditions are inherited exactly from
  `scripts/temporally_matched_observable_control.py`.
- Both arms use the exact same ordered rows and row-key hashes per fold.

## Arms and features

- Observable-only: `H+O1r` (14 history columns plus 1,664 O1r columns = 1,678).
- Observable plus internal: `H+O1r+internal234` (1,912 columns).
- No StandardScaler is fitted. O1r and internal234 are the frozen A+ numerical
  features; tree fitting receives finite arrays directly.

## Probe and selection

Every arm uses exactly `sklearn.ensemble.HistGradientBoostingClassifier`:

```python
HistGradientBoostingClassifier(
    loss="log_loss", learning_rate=0.1, max_leaf_nodes=31, max_depth=6,
    min_samples_leaf=100, l2_regularization=1.0, max_bins=255,
    categorical_features=None, early_stopping=False, random_state=901,
    class_weight=None, max_iter=max_iter,
)
```

The only candidate is `max_iter in {100, 300}`. Each candidate is fitted on
train only; pooled validation AP selects the larger value, with an exact tie
selecting `100`. Test predictions are generated once, after selection. No
internal validation split or automatic early stopping is permitted.

## Primary estimand

For each architecture, source, and detector seed:

```text
AP(H+O1r+internal234) - AP(H+O1r)
```

The primary summary is the mean of the `10 x 3` source-by-seed matrix. Also
report per-seed pooled AP differences and scenario/source strata.

## Uncertainty

Use exploratory two-way crossed bootstrap with 10,000 draws and seed `901`:
sample 10 source rows with replacement and 3 detector-seed columns with
replacement once per replicate, then average the selected cells. Also report a
source-only bootstrap conditional on the three observed seeds. Three seed
levels are insufficient for a precisely calibrated population interval; all
intervals are exploratory.

The historical A+S S2 linear results are references only and are not refit or
used for nonlinear selection.

## Boundaries

No P1r, mLSTM replication, real-data experiment, nonlinear model beyond this
fixed HGB family, W128+, adaptation, or G1/H2/H3a/H3b modification is allowed.
The historical `+0.02` value is descriptive only.

Pre-result implementation seal: recorded in the result artifacts after the
protocol/implementation commit.
