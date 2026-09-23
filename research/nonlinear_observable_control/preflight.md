# Label-blind preflight

This preflight was executed before any nonlinear fit. It inspected only the
existing read-only A+ cache manifests and frozen row/dimension metadata.

- scikit-learn: `1.9.0`
- architectures: xLSTM and matched LSTM
- detector seeds: `11, 22, 33`
- folds: train `1000..1009`, validation `2000..2004`, test `3000..3009`
- rows per fold: train `697430`, validation `348715`, test `697430`
- dimensions: `H+O1r=1678`, `H+O1r+I=1912`
- cache manifests: six complete manifests, 500 streams each
- probe: `HistGradientBoostingClassifier`, `early_stopping=False`,
  `random_state=901`, `max_iter` candidates `{100,300}`
- approximate memory: recorded in `preflight.json`

No labels were joined and no nonlinear estimator was fitted. The pre-result
implementation seal is `61e57ef7894c8db7faaeb5efc2fd63fb5f58956e`.
