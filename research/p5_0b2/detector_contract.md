# Detector contract

## Status and scope

This is the pre-label method contract. It selects the generic dense autoencoder (AE) design referenced by EnergyFaultDetector v0.7.1, with per-row RMSE. It freezes the inference interface and information boundary; numerical hyperparameters, source-only model selection, and readiness state are defined by the source-development and readiness contracts. No model training, TARGET scoring, or target-prefix adjudication occurs under this document.

Reference pin: [`AEFDI/EnergyFaultDetector` v0.7.1, commit `ced470e1386066931bad32f3cb6e24bac9c5bb89`](https://github.com/AEFDI/EnergyFaultDetector/commit/ced470e1386066931bad32f3cb6e24bac9c5bb89). This project contract is deliberately narrower than the package API. The audit and version correction are recorded in [detector_backbone_audit.md](detector_backbone_audit.md).

## Frozen inference contract

For each `(manufacturer, configuration_type)` source stratum that passes the source-support gate:

1. Apply the deterministic raw-to-model projection in [`feature_projection.json`](feature_projection.json): select the frozen reduced ordered continuous-feature allowlist from the committed `automated_common_feature_intersection`, and discard all other raw columns before model-schema validation. Raw union-only and excluded status/mode columns therefore do not count as projected extras. After projection, require the exact ordered schema and hash; a missing required feature, duplicate header/name, or failed numeric cast is handled by the fail-closed preprocessing rules. The manifest pins the P5-0B1R schema artifact and role-seal hashes. ASCII lexical stratum-order D changes from `[10, 13, 10, 14, 10]` to `[8, 11, 8, 12, 8]` after excluding `*_meter_energy` and `*_meter_volume`; retain temperatures/setpoints, control-valve position/setpoint, `*_meter_flow`, and `*_meter_heat_power`. No CounterDiffTransformer or value-based reconsideration is allowed. Validate selected-column numeric usability using SOURCE fit data only, then persist the ordered names, dtype policy, and schema hash in the source model manifest before target-prefix adjudication. Never use target-based schema discovery.
2. Fit preprocessing, the AE, and all residual-independent model state on the designated SOURCE training fold only. Validation-fold use is allowed solely by the sealed source-only selection procedure. Use EFD's pinned `MultilayerAutoencoder` class directly on the already source-preprocessed arrays; do not call `FaultDetector.fit` or its `DataPreprocessor`. No target data may enter fitting, selection, early stopping, feature filtering, scaling, imputation statistics, or score fitting.
3. The frozen AE produces a reconstruction for each valid row. The residual is `r[i,j] = x_preprocessed[i,j] - reconstruction[i,j]`. The scalar score is `sqrt(mean_j(r[i,j]^2))`, over the fixed ordered schema. For each reduced projected dimension D, the encoder remains `[4D, 2D]` and decoder `[2D, 4D]`; recompute every D-dependent dimension from the revised projection. Larger scores indicate greater reconstruction error. This formula has no fitted residual scaling, no feature weights, no window aggregation, and no multivariate covariance term.
4. Inference is deterministic for a fixed model artifact, input row, and software/runtime manifest. It applies the sealed imputer/scaler, calls the frozen AE reconstruction path, and computes the external RMSE score only. Do not call `FaultDetector.predict` (which also applies EFD's threshold selector) or any fit/update/refit path, adaptive normalization, model reload from an unpinned location, or any operation that changes preprocessing, model weights, or score semantics.
5. Return one finite score or an explicit invalid-score status for every raw observation presented to scoring. Preserve input observation identity/order in the output; do not compress the acquisition count when preprocessing or model scoring fails.

## Fit and split boundary

The final model is one model per exact SOURCE stratum, never a pooled cross-stratum model and never a merged substitute when a stratum is unsupported. Source development uses entity-grouped folds within the exact stratum; all observations from one entity stay in one fold. The fold salt/assignment, candidate grid, random seeds, budget, selection objective, tie-break, and refit policy must be frozen in the accompanying source-development protocol before any model is trained. Only SOURCE labels may be consumed by the dedicated SOURCE label firewall and only if the sealed procedure explicitly requires them. The detector fitting process itself does not open a manufacturer label CSV.

## Fixed score vs readiness state

The score function and model remain frozen for an entity's full acquisition. Any permitted online state belongs to the separately sealed threshold/readiness contract and may consume only eligible prefix scores and the prefix-adjudication output. Such state may change a threshold or readiness decision only; it cannot change the input schema, transform, AE, residual definition, RMSE formula, prior scores, look schedule, or acquisition budget. After READY, the threshold/readiness state freezes as required by that contract.

## Fail-closed outcomes

- Insufficient SOURCE entity support or failed source-only qualification: mark that stratum `SOURCE_MODEL_NOT_EVALUABLE`; do not merge it with another stratum.
- Schema mismatch, non-finite input after the prescribed source-fitted imputation, invalid AE output, non-finite residual, or non-finite RMSE: emit invalid score for that raw observation, with a reason code and no value-dependent detail in logs. Do not silently drop the observation, adapt the schema, or refit.
- A score-invalid row remains part of the raw acquisition/look count. If the sealed readiness contract's minimum valid-score support is not met at a scheduled look, emit `NOT_READY`. If still insufficient at raw observation 2304, the result is never-ready/commissioning failure; do not extend acquisition.
- Runtime nondeterminism or inability to guarantee transform-only inference is a backbone admissibility failure. No target-driven fallback is allowed.

## Audit artifacts

The source-development handoff must record the code/environment identity, source stratum, ordered schema and schema hash, fold and training provenance hashes, preprocessing/model/score artifact hashes, seed and determinism settings, valid/invalid inference counts, and the exact source-only gate outcome. Artifacts and logs must not contain target identifiers, target timestamps, target labels, target scores, or target event text during this pre-label and SOURCE-only phase. No statistical claim (including a population FPR guarantee) follows from this detector contract alone.
