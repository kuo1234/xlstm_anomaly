# Pilot P2 — LEFT-style causal point-map feasibility

**Verdict: LEFT_POINT_EVIDENCE_NOT_SUPPORTED — pending review.** No retuning or second pilot. Review task: Issue #15 comment 5979301841, mirrored in #16.

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
- 0c6f11456825f29ce4c6d2848133cc519fec58ce: checkpoints and exact-timestamp observation-only maps/seal committed, pushed and remote SHA verified before evaluator. Seal SHA256: 37d50b1d51fb3c01c01e217432ce8cb05fa755bfd5512f680d46826bc371bd8b.
- Evaluator first source-state access: 2026-10-04T13:05:09.777429+00:00, after guard verified exact hashes and pushed seal ancestry (evaluation_start.json/label_access_log.json). Evaluation completed13:05:11 UTC. Earlier compatibility-curator metadata access remains explicitly disclosed.

## Verification and limitations

Twelve targeted tests passed before training: exact instrumented/upstream parity for both anchors, unchanged total formula, causal future-modification invariance, frozen inference weights/prototypes, window bounds, train-only deterministic scaler/constants, no cross-run windows, healthy-only numeric loader, runner without truth parsing and evaluator blocked without a seal. GB10 runtime torch2.13 differs from upstream1.10; random-tensor forward/backward/inference compatibility passed, not benchmark equivalence. Full raw weights remain ignored remotely; checkpoint manifests hash them.

Single model seed, three fault families with one realization each and three setpoint interventions provide pilot evidence only. Native-seed disjointness does not imply independent fault-family replication. Source labels establish disturbance provenance, not risk, and observed channel identifiability may limit weak-fault sensitivity. No controller, RL, xLSTM, P10 write change or full Safe Cycle is authorized by this pilot.

## Healthy training result

| Anchor | Parameters | Selected epoch / step | Healthy val loss | Train wall sec | Checkpoint SHA256 |
| --- | --- | --- | --- | --- | --- |
| PSM | 8395017 | 30 / 4770 | 1.253185 | 863.5 | 6ed2e85662270cb49805eb185258342008543d03359b5913baeefa20ff819703 |
| SMD | 13847860 | 30 / 4770 | 0.634281 | 851.7 | 9ac71c0f8ace345fb782fc491c11fa075fd6e2dad62f726ea9340231290c69fc |

Both reached the frozen30-epoch cap with validation loss still decreasing; no extension. Healthy train/validation gap remained small, all losses/maps finite. This establishes numerical feasibility, not optimal training or a general impossibility result. Training wall reservation totals1,715.3sec (0.4765h); extraction/evaluation additional. Seed robustness is NOT_EVALUATED.

## Detect — per physical fault run

| Case | Score | AP | AUROC | VUS-PR | Recall | NORMAL_A FPR | First alarm delay(h) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| left04 | R0 current | 0.8899 | 0.5920 | 0.8917 | 0.0050 | 0.0200 | 9.3000 |
| left04 | R0 shared | 0.9056 | 0.5842 | 0.9075 | 0.0136 | 0.0000 | 3.4500 |
| left04 | LEFT PSM | 0.9245 | 0.6340 | 0.9257 | 0.0043 | 0.0000 | 9.2500 |
| left04 | LEFT SMD | 0.9244 | 0.6160 | 0.9261 | 0.0100 | 0.0000 | 9.2000 |
| left05 | R0 current | 0.9999 | 0.9996 | 1.0000 | 0.9993 | 0.0700 | 0.0500 |
| left05 | R0 shared | 1.0000 | 1.0000 | 1.0000 | 0.9993 | 0.0050 | 0.0500 |
| left05 | LEFT PSM | 1.0000 | 0.9999 | 1.0000 | 0.9986 | 0.0050 | 0.0500 |
| left05 | LEFT SMD | 0.9999 | 0.9995 | 0.9999 | 0.9907 | 0.0050 | 0.0500 |
| left06 | R0 current | 0.8984 | 0.5681 | 0.8992 | 0.0178 | 0.0100 | 0.0500 |
| left06 | R0 shared | 0.8871 | 0.5405 | 0.8886 | 0.0064 | 0.0050 | 0.0500 |
| left06 | LEFT PSM | 0.8850 | 0.4947 | 0.8869 | 0.0043 | 0.0000 | 0.1000 |
| left06 | LEFT SMD | 0.9124 | 0.5937 | 0.9138 | 0.0014 | 0.0000 | 14.7500 |

IDV3 (left04): LEFT AP gains against current R0 are+0.0347/+0.0345 (PSM/SMD), but frozen recall is only0.0043/0.0100 versus current0.0050 and shared0.0136; first alarm occurs9.25/9.20h after activation, later than shared3.45h. IDV5 (left06): AP changes are-0.0134/+0.0141; recall0.0043/0.0014 versus current0.0178 and shared0.0064. No consistent weak-family coverage increment. IDV4 (left05) remains near-perfect for every detector; LEFT does not add useful coverage there. All six fault-anchor rows produce at least one postactivation alarm, but isolated alarms with<1.1% weak-fault recall are not sustained coverage. Thresholds are frozen healthy q.99, not selected from these events.

## Benign source NORMAL_B false alarms

| Case | Score | NORMAL_A FPR | TRANSITION FPR | NORMAL_B FPR |
| --- | --- | --- | --- | --- |
| left01 | R0 current | 0.0000 | 0.9550 | 1.0000 |
| left01 | R0 shared | 0.0000 | 0.9563 | 1.0000 |
| left01 | LEFT PSM | 0.0000 | 0.9375 | 1.0000 |
| left01 | LEFT SMD | 0.0000 | 0.9350 | 1.0000 |
| left02 | R0 current | 0.0200 | 0.0125 | 0.0133 |
| left02 | R0 shared | 0.0150 | 0.0250 | 0.0416 |
| left02 | LEFT PSM | 0.0100 | 0.0050 | 0.0116 |
| left02 | LEFT SMD | 0.0200 | 0.0050 | 0.0083 |
| left03 | R0 current | 0.0200 | 0.0600 | 0.0250 |
| left03 | R0 shared | 0.0350 | 0.1013 | 0.0283 |
| left03 | LEFT PSM | 0.0050 | 0.0275 | 0.0050 |
| left03 | LEFT SMD | 0.0250 | 0.0350 | 0.0033 |

SP1's settled source NORMAL_B remains100% alarmed by every detector. LEFT reduces SP2/SP3 late false alarms, but does not solve the large coherent setpoint case. No memory writes/adaptation are performed, so this measures detection false alarms, not admission or adaptation benefit.

## Validate — physical-case direction and disagreement

| Score | PSM AP | PSM AUROC | PSM correct pairs | SMD AP | SMD AUROC | SMD correct pairs |
| --- | --- | --- | --- | --- | --- | --- |
| R0_score | 0.5556 | 0.4444 | 4/9 | 0.5556 | 0.4444 | 4/9 |
| R0_shared_fit | 0.4667 | 0.2222 | 2/9 | 0.4667 | 0.2222 | 2/9 |
| score_total | 0.4667 | 0.2222 | 2/9 | 0.4667 | 0.2222 | 2/9 |
| score_time | 0.4667 | 0.2222 | 2/9 | 0.4667 | 0.2222 | 2/9 |
| score_freq | 0.4667 | 0.2222 | 2/9 | 0.4667 | 0.2222 | 2/9 |
| score_ms | 0.4667 | 0.2222 | 2/9 | 0.4667 | 0.2222 | 2/9 |
| cycle | 0.4667 | 0.2222 | 2/9 | 0.5333 | 0.4444 | 4/9 |
| prototype_gate | 0.4111 | 0.1111 | 1/9 | 0.5889 | 0.5556 | 5/9 |
| cross_path_consistency | 0.4667 | 0.2222 | 2/9 | 0.7556 | 0.6667 | 6/9 |

The six case medians use the same three256-point windows ending1280/1408/1536, wholly within source FAULT/NORMAL_B. N=6 physical realizations; repeated windows/anchors are not independent observations. Current R0 results repeat across anchors and are listed for alignment only.

| Case | Source state | PSM cross-path median | SMD cross-path median |
| --- | --- | --- | --- |
| left01 | NORMAL_B | 1.5098 | 0.6074 |
| left02 | NORMAL_B | 0.3223 | 0.2659 |
| left03 | NORMAL_B | 0.2804 | 0.2458 |
| left04 | FAULT | 0.2485 | 0.2609 |
| left05 | FAULT | 0.4769 | 0.7622 |
| left06 | FAULT | 0.2320 | 0.2827 |

PSM cross-path: IDV3 and IDV5 lie below every benign case; only IDV4 exceeds SP2/SP3. No wrong current-R0 contrast is corrected. SMD cross-path provides a real partial positive diagnostic: IDV4 exceeds all three benign cases and IDV5 exceeds SP2/SP3, correcting three wrong current-R0 pairs. IDV3 exceeds only SP3 and loses a current-R0-correct comparison against SP2. These changes reverse across anchors, and both weak faults remain below SP1. Keep this result; do not select SMD, flip PSM direction, remove SP1 or promote it to a stable Validate feature. Its matched late-point AUROC0.5858 is descriptive, lower than the case-median0.6667; correlated timestamps cannot inflate N.

All maps are finite and nonconstant. Prototype gate is narrowly distributed and high: PSM source NORMAL_B/SP1 mean gate is about0.975, std0.00023, higher than faults; SMD ranges overlap states. The high, narrow uncertainty range limits interpretation; it does not establish prototype collapse or legitimate operation. Prototype cluster occupancy was not audited. Complete min/max/std and every physical fault×benign component margin are retained in component_range_checks.csv and case_component_pairs.csv. Neither component orientation nor threshold is rescued. No supervised probe or fitted conditional-information model: pair corrections bound incremental rank evidence only.

## Verdict and stop

**LEFT_POINT_EVIDENCE_NOT_SUPPORTED for the frozen primary causal pilot.** Detect does not materially cover both weak families under frozen calibration relative to both controls. Primary PSM total/disagreement does not distinguish source fault from NORMAL_B; the partial SMD-only cross-path signal is anchor-dependent and does not establish stable cross-family legitimacy evidence. This is not a claim that LEFT, other training schedules or richer measurements can never help. It is a negative result for this pinned healthy-only protocol.

STOP pending Issue review. No alpha/config/threshold tuning, replacement cases, orientation rescue, classifier, admission, controller, RL, xLSTM, P10 online writes or full #16 cycle. Before future operational Safe Cycle work, source disturbance activation and independently established unsafe-operation ground truth must be defined separately. Controller compensation / measured-channel observability is a possible explanation, not verified for these runs. Do not reinterpret poor source-fault recall as unsafe-operation recall, nor relabel weak source faults safe.

## Final verification and artifacts

The same12targeted tests passed again after evaluation; exact seal/protocol/code/raw/checkpoint hashes and remote seal ancestry verified at2026-10-04T13:10:39.743172Z. git diff --check passed. No scoring/training/evaluation code changed after the protocol commit or after seeing results. All original sealed maps remain byte-identical.

[Per-run point results](results/point_results.csv), [case component medians](results/case_component_medians.csv), [all physical-case pair margins](results/case_component_pairs.csv), [component range checks](results/component_range_checks.csv), [late-point descriptive metrics](results/cross_run_point_metrics.csv), [evaluation access proof](results/evaluation_start.json), [label access chronology](results/label_access_log.json), [checkpoint manifest](run/checkpoints_manifest.json), [seal](run/seal.json), [exposure audit](exposure_audit.json), [split audit](split_audit.json), [semantic boundary](SEMANTIC_BOUNDARY.md). Complete timestamp/source-state component means are results/*.csv.gz; channel maps remain run/traces/*.npz.
