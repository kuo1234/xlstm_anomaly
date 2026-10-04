# Pilot P2 — LEFT-style causal point-map feasibility

Status: RUNNING; no scientific verdict before the pushed score/checkpoint seal and evaluation. Review task: Issue #15 comment 5979301841, mirrored in #16.

## Scientific target and semantic boundary

Test whether pinned LEFT total point evidence improves source-disturbance Detect coverage over R0 and whether its frozen components distinguish source FAULT from benign source NORMAL_B across physical interventions. These source labels do not establish unsafe operation. Following the user's explicit clarification, disturbance activation and operational safety remain distinct; unsafe-operation recall and safe normal-memory admission are NOT_EVALUABLE. Weak faults remain FAULT in every primary metric.

## Provenance, exposure and fixed physical cases

All acquisition, model training and numerical evaluation run on ssh kuo (GB10); no local raw download. Official Extended TEP v1 DOI 10.11583/DTU.13385936.v1, official TEP_Mode1.h5 bounded HTTP byte ranges. 705 fetched blocks total44.0625MiB. Hashes cover materialized arrays, metadata and fetched range blocks; a whole-HDF5 hash was not verified. No mirror or alternative release.

Healthy support: 50 Mode-1 pre-event physical runs for train, four disjoint runs for validation, four for calibration. Only t<30h observations materialized: 600 points × 53 channels per run. Native seeds are unique and roles/event seeds disjoint. Train contributes 30,000 points and 20,450 length-192 windows; validation 1,636 windows; calibration 1,636 endpoints. No window bridges physical runs. Independently recomputed scaler exactly matches all30,000train points; 11channels use the frozen std floor and train clipping fraction is0 (healthy_scaler_audit.json).

Prospective cases fixed before LEFT event scores:

| ID | Native intervention | Native seed |
|---|---|---:|
| left01 | SP1 +5%, ramp40h | 3010004 |
| left02 | SP2 -5%, ramp20h | 3010002 |
| left03 | SP3 +5%, ramp0h | 3010000 |
| left04 | IDV3 magnitude100 Run2 | 11455 |
| left05 | IDV4 magnitude100 Run2 | 23463 |
| left06 | IDV5 magnitude100 Run2 | 45290 |

Source profile/completion/seed metadata was inspected by the acquisition curator for compatibility, before training; the numeric runner does not receive state labels, timestamps or fault IDs. This is not globally label-blind data discovery. Fault-family semantics were known from prior pilots; benign native prefix seeds partly overlap previous SP studies. The event realizations did not participate in LEFT-score development, but this is frozen exploratory simulator evidence, not strict confirmatory validation.

Source convention: NORMAL_A before30h, benign TRANSITION30–70h and NORMAL_B from70h (author thesis A.3.2); fault cases remain FAULT from30h. This convention does not independently prove exact stochastic stationarity or operational safety. Every event has 1,601 test points from20h, including200 NORMAL_A points; faults have1,401 FAULT points. Benign transition/state supports are800/601 points.

## Frozen model, training, causal extraction and controls

Official DezhengWang/Left commit 3fadb4811797075e233076b9faceb0d8ec59b697. Primary PSM and robustness SMD configs are preserved exactly except enc_in=53. Both use192-point windows and seed11; no anchor winner selection. Loss, prototype training, curriculum and total score arithmetic are upstream code. Instrumentation exposes existing time/frequency/multiscale/gate/cross-path/cycle/total maps without changing their arithmetic.

Healthy-only Adam lr1e-4, batch128, float32, max30epochs, patience3. Checkpoints are eligible only after the official1000warmup+2000ramp steps, selected by healthy-validation official loss. Scaler train-only, std floor.02, clip±20; calibration independent healthy q.99 per total/component. Runtime budget3600sec/anchor, prespecified healthy-only throughput smoke. This pilot's scheduler/runtime differs from exact paper training; no event outcome can adjust it.

Primary inference uses [t-191,t], keeps only endpoint. Upstream symmetric moving-average padding repeats the current endpoint within this past-only window; no future observation enters. Preserve seven raw channel maps, aligned mean traces and frozen calibration thresholds. Evaluation does not update weights/prototypes. No test writes or admission decisions.

Current R0 is W1 seed11 fixed random ReLU, past8, per-event normal-prefix80% FIT/20% CAL; original score and chunk semantics retained. R0_shared_fit additionally uses the same50 healthy training runs, global train-only scaler and independent calibration support as LEFT. It bounds a training-support confound; representation capacity, past192 reconstruction versus past8 prediction, loss and context length remain unmatched. Neither control writes test observations.

Detect: per physical fault case FAULT vs NORMAL_A AP/AUROC/VUS-PR16, frozen-q.99 recall/FPR, first alarm delay and benign NORMAL_B FPR. Fault prevalence1,401/1,601=0.8751 makes AP alone insufficient. Validate: frozen fault-high components, matched256-point late windows (three shared endpoints), per-physical-case medians, all fault×benign contrasts and equally weighted matched late-point diagnostics. Correlated points/windows and two anchors are not independent N. No supervised probe, orientation flip, threshold tuning or point adjustment.

## Audit chronology

- f55f50cf6effac24ed51b2155dde24085d56f27d: protocol, selection, official anchors, code and tests pushed before acquisition.
- 380dbc43693b60afd94a485598d253b0d8cac03b: acquired manifests, numeric healthy roles, exposure/split audit and semantic boundary pushed before training.
- Checkpoint/score/seal commit: pending.
- Evaluator source-state access: pending; guarded by exact seal hashes and remote commit ancestry.

## Verification and limitations

Twelve targeted tests passed before training: exact instrumented/upstream parity for both anchors, unchanged total formula, causal future-modification invariance, frozen inference weights/prototypes, window bounds, train-only deterministic scaler/constants, no cross-run windows, healthy-only numeric loader, runner without truth parsing and evaluator blocked without a seal. GB10 runtime torch2.13 differs from upstream1.10; random-tensor forward/backward/inference compatibility passed, not benchmark equivalence. Full raw weights remain ignored remotely; checkpoint manifests hash them.

Single model seed, three fault families with one realization each and three setpoint interventions provide pilot evidence only. Native-seed disjointness does not imply independent fault-family replication. Source labels establish disturbance provenance, not risk, and observed channel identifiability may limit weak-fault sensitivity. No controller, RL, xLSTM, P10 write change or full Safe Cycle is authorized by this pilot.
