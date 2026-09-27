# Detector backbone audit: EnergyFaultDetector

## Scope and disposition

This is a public-code audit only. No PreDist loader was instantiated, no dataset or label payload was opened, no project sensor values were inspected, and no model was trained. The source inspected is the public `AEFDI/EnergyFaultDetector` repository at the two immutable commits below.

**Recommended primary reference pin:** EnergyFaultDetector **v0.7.1**, commit [`ced470e1386066931bad32f3cb6e24bac9c5bb89`](https://github.com/AEFDI/EnergyFaultDetector/commit/ced470e1386066931bad32f3cb6e24bac9c5bb89), using its generic `FaultDetector` / dense `MultilayerAutoencoder` / `RMSEScore` concepts as a reference. The protocol adaptation is a fixed numeric-input autoencoder with per-row RMSE, source-only fitted preprocessing, and fixed inference. It does **not** adopt EFD's PreDist benchmark loader, event-specific benchmark procedure, threshold selector, or target adaptation. Treat this pin as the named design reference; actual implementation and source-only qualification remain a later, separately gated task.

## Version identity correction

The commit `ced470e1386066931bad32f3cb6e24bac9c5bb89` resolves to tag **v0.7.1**, not v0.3.0. The v0.3.0 tag resolves to [`9e0d65074c88e51e180e3bf37f580280bbb54496`](https://github.com/AEFDI/EnergyFaultDetector/commit/9e0d65074c88e51e180e3bf37f580280bbb54496). The v0.3.0 tree does not contain the PreDist loader/notebook workflow. Therefore claims about the PreDist loader or later generic API must not be attributed to v0.3.0. The selected reference is v0.7.1, as requested by the handoff's correction.

## Public-source findings

The following are observations from the v0.7.1 source, not protocol decisions:

| Finding | Official source |
|---|---|
| The generic `FaultDetector` is a composition of preprocessing, autoencoder, anomaly scoring, and threshold selection. Its `predict` path transforms with the fitted preprocessor, reconstructs, computes reconstruction error, transforms that error to a score, then applies the threshold selector. | [`energy_fault_detector/fault_detector.py`](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/fault_detector.py), especially `predict` and `predict_anomaly_score` |
| The package exposes dense `MultilayerAutoencoder` alongside several temporal/conditional architectures. Its base class defines fitting and reconstruction-error interfaces. | [`energy_fault_detector/autoencoders/multilayer_autoencoder.py`](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/autoencoders/multilayer_autoencoder.py); [`energy_fault_detector/core/autoencoder.py`](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/core/autoencoder.py) |
| `RMSEScore` computes one root-mean-square value across each row of the reconstruction-error matrix. Its optional `scale=True` fits mean and standard deviation of residuals; constant residual dimensions use centering only, and infinities after scaling are replaced with zero. | [`energy_fault_detector/anomaly_scores/rmse_score.py`](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/anomaly_scores/rmse_score.py) |
| The configurable `DataPreprocessor` can include imputation, scaling, category encoding, filtering, and domain transforms. Defaults can filter features and impute/scale; such implicit defaults are unsuitable as an unrecorded project contract. | [`energy_fault_detector/data_preprocessing/data_preprocessor.py`](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/data_preprocessing/data_preprocessor.py); [`energy_fault_detector/config/quickstart_config.py`](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/config/quickstart_config.py) |
| The generic `fit` API accepts `normal_index`, and the package has label-driven threshold options as well as quantile/adaptive options. Those capabilities are not authorization to read target labels or use target outcomes in this protocol. | [`energy_fault_detector/fault_detector.py`](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/fault_detector.py); [`energy_fault_detector/threshold_selectors/`](https://github.com/AEFDI/EnergyFaultDetector/tree/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/threshold_selectors) |
| The PreDist-specific loader is a distinct evaluation helper, separate from the generic detector. It is explicitly out of bounds for this work phase, even though its public source may be cited. | [`energy_fault_detector/evaluation/predist_dataset.py`](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/evaluation/predist_dataset.py) |

### Component-level PreDist and generic-path findings

- The public PreDist helper reads `faults.csv`, `normal_events.csv`, and
  `disturbances.csv`; its `get_event_data` uses fault descriptions/event
  intervals to choose training and evaluation slices. It is therefore not
  called by the project firewall or source-development process. Its table
  schema and interval semantics are audited only to define an independent
  source-only parser and the later prefix/evaluator boundaries. See
  [`predist_dataset.py` loader](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/evaluation/predist_dataset.py#L28-L207).
- The generic `FaultDetector.fit` path filters `normal_index` before fitting
  the preprocessor and AE. Optional `DataClipper` fitting happens before that
  mask, so this protocol excludes the default detector pipeline and uses the
  dense AE component with its own explicitly source-only preprocessing.
  [`fit` implementation](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/fault_detector.py#L40-L180).
- Generic preprocessing defaults include column filters, mean imputation,
  one-hot encoding for declared categoricals, and scaling. At fit time the
  imputer drops all-NaN columns; a later missing fitted column raises. An
  all-NaN inference row is imputed and may still be scored. Unknown
  categories can be logged by value, while undeclared object columns are
  dropped. The project excludes categorical/status fields, fixes its numeric
  schema, rejects missing columns, marks all-NaN rows invalid, and suppresses
  value-bearing logs. See [pipeline configuration](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/data_preprocessing/data_preprocessor.py#L331-L409), [imputer](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/data_preprocessing/imputer.py#L91-L135), and [categorical encoder](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/data_preprocessing/categorical_encoder.py#L31-L131).
- PreDist's loader maps selected pump/valve states (`EIN`/`AUS`) and German
  control modes to numeric values; unknown values become missing. Those
  categorical/status conversions are event- and schema-specific and are
  excluded from detector inputs. The loader drops duplicate timestamps
  keeping the first without conflict checks; the project does not delegate
  timestamp cleanup to it.
- `RMSEScore` can standardize residual dimensions using fitted residual
  statistics but has no NaN handling. The sealed score instead computes
  unweighted per-row RMSE over the fixed feature schema and marks a non-finite
  residual invalid. Mahalanobis uses PCA plus `MinCovDet` without exposed
  random states and has dimension/small-sample sensitivity, so it is not a
  candidate. See [RMSE](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/anomaly_scores/rmse_score.py#L13-L71) and [Mahalanobis](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/anomaly_scores/mahalanobis_score.py#L15-L112).
- `predict` transforms with fitted preprocessing and computes scores without
  fitting on inference rows. A quantile selector can be fitted from a normal
  mask; its empirical quantile does not certify future FPR. Target inference
  will not call EFD's fit or threshold selector: it applies the sealed RMSE
  model, then the project's fixed-prefix q99 threshold state. See
  [prediction path](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/fault_detector.py#L300-L407) and [quantile selector](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/threshold_selectors/quantile_threshold.py#L20-L58).
- `FaultDetector.predict` applies its configured selector and returns both
  scores and anomaly flags. `predict_anomaly_score` returns scores without
  thresholding. The generic `MultilayerAutoencoder.fit(x, x_val=None,
  **kwargs)` forwards Keras fit options; `shuffle=False` is supported there,
  but `FaultDetector.fit` does not forward extra Keras kwargs. The protocol
  therefore uses the pinned autoencoder class directly on the sealed
  source-preprocessed arrays and implements fixed RMSE/threshold logic
  outside the wrapper. See [autoencoder fit](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/core/autoencoder.py#L194-L264) and [detector scoring APIs](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/fault_detector.py#L300-L407).
- The public package does not establish deterministic training by itself:
  its train/validation split lacks `random_state`, the AE adds TensorFlow and
  NumPy random noise, and requirements allow TensorFlow 2.15–2.18. The source
  contract pins the runtime, sets all seeds, runs CPU-only deterministic ops
  with one thread, and has an explicit repeatability gate. If that gate fails,
  do not proceed to target adaptation. See [split](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/core/fault_detection_model.py#L188-L220), [AE randomization](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/energy_fault_detector/core/autoencoder.py#L522-L552), and [requirements](https://github.com/AEFDI/EnergyFaultDetector/blob/ced470e1386066931bad32f3cb6e24bac9c5bb89/pyproject.toml#L12-L28).

The v0.7.1 generic base config uses 0.95 threshold quantile and contains
preprocessing/training defaults that are overridden here. The public PreDist
notebook configurations use 0.99 but are not copied; q99 is chosen in this
protocol as a simple empirical calibration direction and is not a 1% FPR
claim. The paper describes event-specific interval selection, feature
filtering, and anomaly/normal event tuning; those operations remain excluded.

## Protocol decisions and limits

The project's selection of a generic dense AE plus per-row RMSE is a **protocol choice**, not an EFD default requirement and not a claim of benchmark superiority. The detector fit is SOURCE-only. Data transformations are fitted on SOURCE training folds only; inference applies those frozen transformations and the frozen autoencoder without calling any fit/update/refit path. The score function is fixed before any TARGET prefix eligibility or values are available. Only the separately specified readiness/calibration state may be updated from eligible target-prefix scores; it cannot alter features, preprocessing, AE weights, or the score formula.

The EFD paper/notebooks include benchmark practices that depend on fault/event-specific information, feature selection, or per-event tuning. Those practices are not imported. No TARGET value, score, distribution, semantic label, event identity, or outcome may be used to choose this backbone or tune its settings. EFD's threshold selector is not the project's readiness rule. Mahalanobis scoring is not selected: it adds fitted residual-distribution state, while the handoff calls for per-row RMSE and a distinct, explicit calibration/readiness protocol. The package's presence of a Mahalanobis implementation does not establish that it is required or admissible here.

The v0.7.1 source audit supports a generic detector design, but this document alone does not demonstrate compatibility with the project environment, numerical stability on any project data, deterministic training, or source-stratum evaluability. Those are SOURCE-only gates in the later phase. If the pinned generic dense AE cannot be implemented under the sealed numeric schema and information boundary, report `BACKBONE_NOT_ADMISSIBLE`; do not substitute target-adaptive processing or reopen a method-choice decision using target performance.
