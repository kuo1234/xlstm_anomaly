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

## G0.1 prospective CANDI-control amendment

The external protocol resolution supersedes the earlier unresolved-control
paragraph above, before any Phase-G labels, feature extraction, scaler fitting,
classifier fitting, or metric computation. The shared H3a-C history control is
the existing Phase-D D=8 synthetic CANDI family, paired by detector seed:

| detector seed | frozen pre-intervention state |
|---:|---|
| 11 | `data/phase_d/backbone_11/pre_intervention.pth` |
| 22 | `data/phase_d/backbone_22/pre_intervention.pth` |
| 33 | `data/phase_d/backbone_33/pre_intervention.pth` |
| 44 | `data/phase_d/backbone_44/pre_intervention.pth` |
| 55 | `data/phase_d/backbone_55/pre_intervention.pth` |

These are the official CANDI commit
`28c9679e503832f59e351208cde63657fcb51cad` with frozen pre-intervention
MLP/SANA states, no adaptation, no optimizer step, no FPM selection, and no
truth access. The native CANDI window remains W=10; it is not retrained or
converted to W=64. At each shared right-edge timestamp `t >= 63`, xLSTM/LSTM
consume `raw[t-63:t+1]` and CANDI consumes `raw[t-9:t+1]`. Only CANDI scores
at those common timestamps enter the 14-column causal history; all earlier
scores are forbidden and incomplete rolling histories remain NaN warmup.

The exact mapping, Phase-D manifest hash, preprocessing/scaler values and
derived preprocessing hashes are sealed in
[`candi_control_manifest.json`](candi_control_manifest.json). SMD/Phase-C
native controls are explicitly excluded because they are domain/dimension
mismatched for the D=8 synthetic source-paired track. The amendment status is
`PENDING_CANDI_PREFLIGHT` in its prospective commit; G0 could become PASS
only if the original ten-backbone preflight remained PASS and the alignment
preflight passed. The resulting status is recorded below.

## G0.1 alignment preflight outcome

The label-blind CANDI alignment preflight passed for all five seed mappings;
the original ten-backbone preflight also remained PASS. Therefore the current
G0 status is `PASS`. The sealed report is
[`candi_preflight.json`](candi_preflight.json) (SHA256
`6bb3e7cec12584d8c334ef6f5e252ca5b94f63e019e0f66f255f2c1516976b2c`). It
verified common right-edge timestamps 63--191, CANDI W=10 versus xLSTM/LSTM
W=64 windows from one raw observation stream, 14-column causal history with
97 valid rows after warmup, paired history reuse and byte-identical row keys,
future-perturbation causality, reset, finite outputs, state/hash immutability,
and dummy-label invariance. No labels, test metrics, scaler fitting,
classifier fitting, optimizer, adaptation, or FPM selection was used.
