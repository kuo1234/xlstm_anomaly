# Staged experimental plan

**Planning only.** No stage is authorized or executed by this document. Each stage is a gate that can terminate or narrow the proposal. Do not jump to an integrated method.

## M0 — prior-art and identifiability gate

**Question:** Is there a distinct, observable, useful problem left after prior art, and can any intended dataset identify it?
**Method:** literature audit, semantics audit and the observational-equivalence argument; no model training.
**Minimum comparison:** position M2N2, CANDI, MemTTA, AnDri, ARCUS and drift/model-pool methods.
**Decision:** GO only with a precise contribution not already represented and a dataset/context source that separates allowed regimes from persistent anomalies. REFRAME to Problem A if only normal-only target transfer is supportable. STOP if no useful target-normal resource or no distinguishable evaluation question exists.
**Current outcome:** REFRAME. Broad new-normal framing is prior art; Problem B lacks general observation-only identifiability; Problem A remains separable.

## M1 — source-native forecasting detector viability

**Question:** Is causal forecasting a useful anomaly detector at all on the chosen data?
**Primary comparison:** last-value predictor; moving mean/variance or first-difference score; a simple linear/AR forecast; capacity-matched LSTM; xLSTMAD reconstruction; xLSTM one-step forecast. Add GRU or SSM as a small architecture control only if budget permits. No adaptation.
**Protocol:** choose one source-native benchmark with reliable event labels and one industrial multivariate set; preserve source/time groups; keep threshold calibration separate from final labels.
**Kill:** if xLSTM forecasting is not practically competitive with simple predictors / reconstruction on AP, false-alarm burden and event metrics, stop xLSTM forecasting branch. If all learned forecasters lose to moving statistics, reconsider forecasting as the main signal.
**Proceed:** at least one causal forecast condition offers repeatable event-level benefit over cheap controls without unacceptable false alarms, across more than one source family.

## M2 — horizon and context audit

**Question:** Does multi-horizon scoring help with short/long events and anomalies entering the context?
**Comparisons:** one-step; direct or recursive multi-step; independent W lengths selected from cadence/event duration; current xLSTMAD reconstruction; moving-window statistics.
**Scenarios:** point anomalies, short segments, long segments, anomaly at stream onset, anomalous segment already in rolling context, segment end/recovery. Include controlled synthetic cases plus real events.
**Horizon selection:** infer candidate physical durations from training data or external event metadata, lock choices before final labels; do not freeze {1,4,16,64} by convenience.
**Aggregation:** horizon-specific calibrated residual vector first; test max and a predeclared calibrated combination as secondary.
**Kill:** if multi-horizon gives no event-level, onset or recovery benefit beyond moving statistics and one-step, remove the multi-horizon claim/component.

## M3 — persistent-memory audit

**Question:** Does state carried across windows help, or does it amplify contamination?
**Comparisons:** (1) independent W64 reset (current R0-style encoder); (2) persistent state that always updates; (3) protected state updated only after a normal gate; (4) freeze protected state under suspicion; (5) shadow/quarantine state; (6) rollback or multiple confirmed-regime states only if simpler policies fail.
**Controls:** identical timestamps, model capacity/objective, sample access and score-before-update timing. Include a matched LSTM; compare the effect against simple causal rolling features.
**Measurements:** false-positive persistence, anomaly score decay while anomaly remains, onset/recovery delay, cross-window contamination and per-machine effects.
**Kill:** if persistent state does not improve predeclared stream metrics over reset windows and observable rolling statistics, do not keep it for novelty.

## M4 — normal-only target transfer

**Question:** Does source pretraining reduce the amount of confirmed-normal target data required on a new machine?
**Design:** same-D leave-one-machine-out SMD first; exclude each target entirely from source training; then use target normal prefixes or disjoint target-normal samples and evaluate on a later anomaly-labeled suffix. Confirm channel ordering and target normality independently.
**Sample curve:** candidate counts N ∈ {0, 64, 128, 256, 512, 1024, full} are not accepted until semantics are audited. Count unique raw observations and duration, not overlapping W64 windows. Report actual windows/timestamps, coverage and update steps.
**Adaptation arms:** (1) target-only scratch; (2) source-pretrained + target normalization; (3) + score calibration; (4) + small adapter; (5) + last recurrent block; (6) + full fine-tuning. Use matched optimization/tuning budgets.
**Backbones:** xLSTM and capacity-matched LSTM are mandatory; include GRU or SSM if intended claim says recurrent architecture broadly.
**Primary quantity:** target-normal sample count/time needed to reach a prespecified fraction of the target full-normal reference AP/event utility, with per-machine curve and uncertainty.
**Kill:** no consistent sample-efficiency benefit over target-only scratch or conventional recurrent baseline; negative transfer on several targets; effect explained by normalization/calibration alone if claim is about recurrent pretraining.
**Proceed:** meaningful, stable reduction in confirmed-normal target data versus scratch on multiple held-out machines, with acceptable anomaly metrics and no leakage.

## M5 — online contamination gate

**Question:** Does adaptation avoid learning anomalies without blocking legitimate update?
**Comparisons:** update every observation; score-gated update; CANDI-style curated/selective update; bounded quarantine; protected/frozen baseline with shadow candidate; rollback only as a separate policy if needed. Include M2N2-style adaptation and a simple change-point/update baseline.
**Study:** use labeled chronological streams or controlled anomaly injection where stream order, update opportunities and anomaly status are known. Report the actual fraction of anomalous samples or windows committed to each update.
**Kill:** gates admit persistent anomalies at a rate that degrades alarms, or safe policies prevent any useful response to independently confirmed benign shifts. Also stop if update benefit is no better than a simple threshold or moving statistic.

## M6 — controlled new-normal study

**Question:** Can the method lower persistent false alarms on legitimate new regimes without absorbing faults?
**Data requirement:** independently annotated benign regime changes, transient anomalies, persistent anomalies and recurring old regimes; external mode/command truth where observations alone cannot distinguish cases. The ACM E-Energy 2026 smart-building method is the closest direct prior baseline and should be included if its data and protocol are available; it uses 100 labeled samples per class. Candidate sources also include NoBOOM, Batch Distillation, HAI/HAIEnd and DAYPSCI after a sample-level metadata audit; none is pre-approved. Add controllable synthetic streams for causal mechanism tests.
**Cases:** abrupt benign shift; gradual benign drift; transient anomaly; persistent fault/attack; A→B→A recurrence; unmatched unknown regime.
**Policy:** candidate regime remains shadow-only until prospective confirmation rule is satisfied. Score the original detector before any promotion.
**Primary outcome:** new-normal false-positive persistence; safety outcomes: contamination, persistent-anomaly rejection time, false promotion, old-normal retrieval.
**Kill:** indistinguishable stable anomalies are promoted without external evidence, or reducing benign alarms materially delays/reduces persistent fault detection. If required metadata is unavailable, narrow the scientific claim.

## M7 — integrated method

Combine components only if M1–M6 each justify the component, its added cost, and its evaluation. Preregister the full state machine, promotion rule, baselines, split, dimensions, horizons, memory capacity and metrics before execution. Include ablations that remove each part. This stage is not justified by architectural novelty alone.

## Baseline budget

| Stage | Minimum meaningful comparators |
|---|---|
| M1 | last-value / moving-statistic; simple linear/AR; LSTM; current xLSTMAD reconstruction; xLSTM forecast |
| M2 | one-step vs multi-horizon; fixed-window reconstruction; calibrated horizon evidence; moving-statistic |
| M3 | reset-window LSTM/xLSTM; persistent always-update; normal-gated/frozen state; rolling observable control |
| M4 | scratch; pretrained+normalization; +calibration; +adapter; last block; full tuning; matched LSTM and xLSTM |
| M5 | update-all; score gate; M2N2-style; CANDI-style curated adaptation; change-point + conventional detector; quarantine/protected state |
| M6 | best M1 detector; simple change-point detector; M2N2/CANDI-style; AnDri/normal prototype or model-pool comparator; confirmed-regime oracle as an upper bound |
| M7 | only the small set that survived earlier gates, plus component ablations |

MEMTO/MemMambaAD/PAMA/PC-UAD are relevant memory references. They need not all enter an online new-normal baseline zoo because their memory purposes differ; include one prototype/memory comparator only if M3/M6 establish that explicit prototypes are needed.

## Leakage and protocol rules

- Split by machine, source, run and event, not random overlapping windows.
- Use causal feature availability; the score for x_t precedes any write of x_t.
- Target-normal samples are counted as unique observations and elapsed time; overlapping windows do not count as independent samples.
- No target test values for normalization, early stopping, threshold selection, horizon choice, or model selection.
- When target labels are used to select a detector or calibrate a threshold, call that supervised validation and separate it from the normal-only adaptation claim.
- Report results per machine, event type and source family before an aggregate.
- Every adjustment has a frozen protocol and an explicit stopping rule.
