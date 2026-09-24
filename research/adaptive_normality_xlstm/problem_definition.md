# Problem definition

## Motivation

The motivating failure is not simply an inability to classify anomalous samples. A deployed monitor learns a model of normal behavior, but the process can later change legitimately: a workload is reconfigured, a machine is serviced, ambient conditions change, or an industrial controller enters another permitted operating mode. A fixed detector may alarm for the entire new regime. An adaptive detector may remove those alarms by updating itself, but could thereby teach itself that a persistent fault or attack is normal.

The research question is:

> Given a time series whose operating distribution changes, when can a detector recognize that a persistent new pattern is an allowed operating regime, and adapt without incorporating transient or persistent anomalies into protected normality?

A practical deployment question adds transfer:

> Can a reusable initialization learned from source machines reach useful target-machine detection quality from a small amount of target data whose normality has been confirmed, then continue to operate as allowed normal behavior changes?

xLSTM is a candidate sequence model, not a premise. It must be compared with simpler LSTM, GRU, state-space, forecasting, change-point and moving-statistic methods.

## Two different problems

### Problem A: new-machine adaptation

Let source machines be A…Z and a held-out target be Q. Source training produces reusable parameters. The target supplies N observations, windows or duration of explicitly confirmed normal data. A detector is calibrated or adapted on those data and then scored on a temporally later target test stream containing independently labeled anomalies.

This is **transfer plus normal-only few-shot adaptation**. When N is positive, it is not strict zero-shot. The study asks whether pretraining lowers target data requirements compared with scratch training, and which low-cost adaptation is sufficient.

Problem A does not ask the detector to infer which unlabeled target samples are safe. The confirmed-normal designation comes from the study protocol or an independent operational source. This assumption should be measured and discussed as a deployment constraint, not hidden inside “unsupervised adaptation.”

### Problem B: a new normal over time

A single deployed machine follows allowed regime A, then undergoes an unknown shift. The incoming stream could reflect benign regime B, a transient fault, or a persistent attack/failure. The detector must protect the old normal reference while deciding whether and how to make B part of normality. It may also need to recognize a return from B to A.

This is online adaptation under concept/regime drift with contamination risk. It is not implied by a successful target warm start in Problem A. It needs data where benign modes and faults have separate ground truth, or external operating-mode/maintenance/approval metadata.

## Formal separation

Write the stream observation as x_t in R^D; let z_t be the latent physical operating mode and y_t the anomaly/fault status. The monitor sees x_1:t and may have context c_t such as setpoint, controller mode, maintenance record or operator approval.

Problem A estimates a detector family θ_Q from source parameters θ_S and a confirmed-normal target sample X_Q^N of size N:

- θ_Q = Adapt(θ_S, X_Q^N)
- evaluate false-positive and anomaly-detection performance on a later, disjoint target interval
- compare the target sample efficiency curve against scratch, normalization, calibration and partial/full update alternatives.

Problem B must decide whether a change point at τ denotes allowed mode change z_τ or anomaly y_τ. Its update policy is causal: the score for x_t is produced before x_t can alter protected model state. A proposed policy may maintain a protected state, a suspicious buffer and a candidate-mode predictor. Promotion is an action with consequences, not a label that can be inferred from persistence alone.

## Identifiability boundary

Suppose a benign new regime B and a persistent anomaly A induce the same conditional distribution over all observations available to the detector, P(x_τ:∞ | B) = P(x_τ:∞ | A), and no external context distinguishes them. Every detector that only sees those observations has the same evidence under both cases. It cannot guarantee both “eventually accept B” and “never accept A.” This is an observational-identifiability limit, not a weakness unique to xLSTM.

Persistence, low forecast error, temporal coherence, low uncertainty, cross-channel correlation or similarity to an old prototype can establish that a change is structured. None establishes that it is authorized or safe. A failure mode or attack can be persistent, predictable, coherent and unlike historical data. Conversely, a legitimate operating mode can be rare and unlike all stored prototypes.

Potential disambiguating evidence, in decreasing order of directness:

1. **External semantics:** controller/setpoint mode, product recipe, work order, maintenance record, security/attack state, signed operator confirmation.
2. **Physical or causal constraints:** known conservation laws, actuator/sensor consistency, process safety envelope, topology and interlock rules.
3. **Historical retrieval:** a prior, independently confirmed regime returns; useful for recurrence only when source identity and operating context are reliable.
4. **Return and recovery pattern:** supports a transient-versus-change interpretation but can also describe temporary faults.
5. **Change-point shape, cross-channel coherence, density, predictive uncertainty:** evidence about statistical structure, not benign intent.
6. **Persistence plus internal predictability:** insufficient by itself.

Without evidence in categories 1–2 or an explicit accepted risk policy, the system should report “persistent unclassified regime shift,” retain the protected detector and request review. It should not silently promote the regime.

## Candidate state machine as a research hypothesis

- **NORMAL:** score observations against a protected, pre-update normal model. Updates can use only observations permitted by a clearly evaluated gate.
- **SUSPICIOUS:** raise evidence of novelty/anomaly; freeze protected weights, state and threshold; place observations in a bounded quarantine buffer. Continue scoring with the protected detector.
- **CANDIDATE_NEW_NORMAL:** a shift is persistent, internally coherent and perhaps predictive. Maintain a separate shadow model; do not let it replace the protected detector. Candidate status means “eligible for independent confirmation,” not “benign.”

Promotion would require prospective criteria fixed before testing, plus external normal-mode evidence or a defined human/operational approval signal. The old regime remains retrievable. A persistent anomaly that passes statistical criteria but lacks the external confirmation must remain unpromoted. This policy may be too conservative for applications that cannot provide context; that is a scope limit to report, not a reason to overclaim automatic discrimination.

## Hypotheses and nulls

1. **Transfer efficiency:** source pretraining reduces the number of confirmed-normal target samples needed to reach a predeclared fraction of the target full-normal reference performance. Null: no material reduction versus a capacity-matched LSTM/GRU/SSM or target-only scratch training.
2. **Detector value:** causal forecasting improves anomaly-event detection over simple last-value, moving statistics and current reconstruction. Null: no useful improvement, or gains disappear under event-level/false-alarm metrics.
3. **Persistent-state value:** protected state improves onset, false-alarm persistence or recovery relative to independent windows. Null: persistent state only propagates contamination or duplicates recent input statistics.
4. **Safe update:** quarantine/selective update reduces contamination without unacceptable delay or false-positive persistence. Null: gate admits persistent faults, or rejects benign modes so long that adaptation is not useful.
5. **Semantic identification:** available external context distinguishes accepted modes from persistent faults. Null: labels/context are missing, ambiguous or unavailable at deployment.

## Evaluation unit

The unit for machine transfer is a held-out **machine**, not a randomly split window. The unit for new-normal detection is a **change event/regime transition**, grouped by stream and physical source. Window-level point metrics are secondary if they overcount long, correlated events. All splits must preserve temporal ordering and source identity; no overlapping target-normal windows may leak into later evaluation as distinct independent samples.
