# Phase G0 prospective seal

This is a pre-label protocol seal for H2/H3a. It was generated only from the accepted Phase F-v4 seal, the improved official xLSTMAD E2 schema, and already committed Phase C/D metadata/artifact hashes. No anomaly labels, regime/event truth, test-result arrays, scaler fitting, classifier fitting, AP/AUROC, or optimizer update was read or executed.

## Frozen checkpoints

The ten best checkpoints are exactly those in [checkpoint_manifest.json](checkpoint_manifest.json). LSTM seeds 11/22 are the F-v3 carry-forward references; all other entries are F-v4 best checkpoints. `final.pt` is forbidden when it differs from `best.pt`; F-v1/F-v2, F-v3 partial, and F3-R diagnostic artifacts are forbidden. Models are inference-only in G.

## Frozen probe track

Synthetic folds remain source-disjoint: train 1000--1009, validation 2000--2004, test 3000--3009. Confirmatory shifted scenarios are abrupt, gradual, recurring A→B→A, and correlation-only; stationary/none is a specificity control. The common track is W=64, stride=1, right-edge decisions, with no cross-window state carry and no optimizer updates.

The primary binary labels are evaluator-only: anomaly windows are positive; anomaly-free early-transition/gradual windows are negative. Mixed drift+anomaly windows are a separate stress stratum. The feature extractor API receives observations only.

## Frozen features and statistics

The schema is sealed in [schema_binding.json](schema_binding.json): history control 14, internal base 18, hidden 52, gate 130, memory 52, combined 234, and history+combined 248. xLSTM uses only the four actual scalar sLSTM cells/heads; LSTM pools all six actual recurrent layers. Rolling summaries (4/8/16/32) are causal trailing mean/population standard deviation/OLS slope. No learned pooling, layer selection, zero padding, or mLSTM-only confirmatory feature is allowed.

The confirmatory p-value family is sealed in [confirmatory_family.json](confirmatory_family.json): H2 primary plus H3a A/B/C (four Holm members). H3a is interpreted only after H2 passes. Practical/reproducibility/duration-severity gates remain those in `reports/m0_protocol.md`; descriptive ablations cannot be promoted post-outcome.

## CANDI history-control resolution

The existing artifacts expose more than one plausible frozen CANDI control: five D=8 synthetic seed-wise `pre_intervention.pth` states (native W=10) and multiple SMD/native W=10 score sources. None is a sealed singular D=8/W=64 common-track stream, and the existing M0 text does not pre-register a choice or a W=10-to-W=64 alignment. This is recorded as `UNRESOLVED_PRELABEL` in the schema/config. The G0 stop rule therefore blocks labeled extraction until an external protocol amendment resolves the exact artifact, seed pairing, and timestamp/window alignment. No probe outcome is used to choose among them.

## Label-blind preflight and stop boundary

The accompanying preflight is allowed to load frozen checkpoints and use random unlabeled tensors only. It verifies hashes, finite output/score/features, dimensions, causal rolling transforms, reset, permutation/partition invariance, observer OFF/ON parity, no native `predict_step`, no optimizer/parameter mutation, and identical-observation/dummy-opposite-label invariance. It must not calculate a test metric or join labels. If the CANDI control remains unresolved, the report is a fail-closed pre-label STOP even if backbone-only checks pass.

Phase G0 does not authorize any labeled feature extraction, StandardScaler/logistic fitting, C selection, AP/AUROC/statistics, H3b, H4, natural-H1, or architecture/backend change.
