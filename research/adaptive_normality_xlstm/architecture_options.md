# Architecture options and state/memory audit

At most three candidate architectures are considered. They are hypotheses for later testing, not implementation instructions.

## Option A — full recurrent adaptive normality system

### Block diagram

~~~text
source-machine normal streams
          ↓ normal-only source pretraining
xLSTM (multi-horizon forecast) + calibration
          ↓
small confirmed-normal target prefix
          ↓ target adapter / calibration
protected normal state ───── historical regime pool
          ↓ forecast evidence                    ↑ retrieval
incoming x_t → pre-update score → NORMAL / SUSPICIOUS / CANDIDATE
                                  │           │            │
                                  │           └→ quarantine/shadow state
                                  │                        ↓
                                  └──── selective update ← external mode approval
~~~

**Inputs:** multivariate causal context, incoming observation, and potentially mode/setpoint or maintenance metadata.
**State/memory:** protected recurrent/model state, a quarantine buffer or shadow model, and a bounded historical-regime pool.
**Prediction targets:** one or several future horizons plus optional latent/representation prediction.
**Update logic:** score before update; normal gate may adapt; suspicious freezes protected state; candidate remains shadow-only.
**Adaptation logic:** source pretrained weights plus target-normal calibration/adapter, then metadata-approved regime promotion.
**Score:** calibrated vector of horizon-specific forecast residuals, novelty/change evidence and process-constraint violations; do not collapse prematurely.
**Supervision:** source normal; confirmed target-normal warm start; anomaly labels for evaluation; external mode/fault/approval truth for safe promotion.
**Cost:** highest, multiple forward passes/horizons, shadow and historical models, nontrivial state management.
**Novelty overlap:** high. CANDI/MemTTA overlap with selective updates; AnDri/ARCUS/model pools overlap regime memory; xLSTMAD and recurrent multi-step forecasting overlap the predictor.
**Failure modes:** semantic false promotion, memory contamination, catastrophic forgetting, stale thresholds, unpredictable long horizons, complex ablation burden, no xLSTM-specific advantage.

This option assembles too many unvalidated components and should not be built now.

## Option B — transfer-first, no online regime memory

### Block diagram

~~~text
source normal machines ──→ reusable detector initialization
                                      ↓
held-out target Q: N confirmed-normal samples
                                      ↓
normalization / score calibration / small adapter / last block / full tune
                                      ↓
causal detector on later Q stream
                                      ↓
point + event anomaly scores
~~~

Run the same study for capacity-matched xLSTM and conventional recurrent/SSM alternatives. Candidate detector heads are first an honest one-step forecast and current reconstruction baseline; multi-horizon enters only if M1/M2 support it.

**Inputs:** fixed-D source and target sensor arrays; target adaptation data are explicitly normal.
**State/memory:** model parameters and any within-window recurrent state; no dynamic normal bank, quarantine, or regime pool.
**Prediction targets:** one-step first; multi-step only after horizon audit.
**Update logic:** offline target adaptation is isolated from test; no online updating.
**Adaptation logic:** source initialization followed by target normalization/calibration/adapter/last-block/full fine-tune arms.
**Score:** standardized forecast or reconstruction residual calibrated on target-normal validation only.
**Supervision:** source normal and target confirmed-normal samples; labels only for final evaluation/tuning under a sealed protocol.
**Cost:** low-to-medium; a manageable adaptation curve.
**Novelty overlap:** moderate; transfer and few-shot adaptation are established, but the precise same-D normal-only sample-efficiency protocol may be useful if rigorous.
**Failure modes:** target normal sample is unrealistic; machine semantics may be misaligned; source pretraining can negative-transfer; changes in preprocessing can dominate.

This is the smallest candidate for a later Problem A study. It is not the full adaptive-new-normal method.

## Option C — context-confirmed regime promotion

### Block diagram

~~~text
protected baseline detector ───────────────→ live alarm path
          │
          └→ causal shift detector → suspicious quarantine
                                      ↓ persistence/coherence
                               shadow candidate detector
                                      ↓ external mode / operator confirmation
                         bounded approved regime registry (old regime preserved)
~~~

Use a simple detector family first; do not assume xLSTM. Promotion requires independent semantics, not just a low prediction error.

**Inputs:** sensor stream plus trusted operation-mode/setpoint/maintenance/security context, or a small labeled anchor set for normal, drift and attack classes as in the E-Energy 2026 smart-building method. These are distinct supervision regimes and must not be blended.
**State/memory:** protected baseline, temporary quarantine, shadow candidate and bounded pool of confirmed regimes.
**Prediction targets:** only those justified by M1/M2; may be one-step forecasts or conventional residuals.
**Update logic:** prequential scoring; suspicious/candidate observations do not update the protected baseline.
**Adaptation logic:** train/adapt a regime-specific model only after external approval; preserve ability to retrieve former normal regimes.
**Score:** anomaly score plus shift score and context-consistency result, reported separately.
**Supervision:** confirmed target normal for initialization; event-level benign-mode and anomaly truth; either trusted context for promotion or explicitly budgeted labeled class anchors. An anchor-based closed set may fail on unseen faults or modes.
**Cost:** high governance and metadata integration, moderate compute.
**Novelty overlap:** substantial with AnDri, ARCUS, MemTTA and drift-aware model pools.
**Failure modes:** metadata unavailable or untrusted; approval comes too late; faulty controller context; pool growth/selection errors; same observable law under benign and anomalous semantics.

This is a defensible direction for a future claim about *safe* new-normal promotion, but it is no longer unoccupied: the ACM E-Energy 2026 smart-building work directly studies normal / normal-drift / attack separation with a small labeled anchor set and selective update. A future study must beat or materially extend that baseline, and current dataset evidence still needs auditing.

## Forecast design audit

| Formulation | Causal interpretation | Strength | Main failure mode | Evidence needed |
|---|---|---|---|---|
| Reconstruction: X[t−W+1:t] → reconstruct X[t−W+1:t] | Uses the whole input window; pointwise scores within it may use later samples than the point being scored | Can capture a segment pattern with one pass; direct continuation of existing xLSTMAD/R0 | Over-generalizes anomalies; reconstruction can be good for abnormal patterns; window score may be non-causal for onset | Score only at a declared window endpoint or use masked/causal reconstruction; compare moving variance and simple reconstruction |
| One-step forecast: X[t−W:t−1] → predict x_t | Prediction is made before observing x_t | Clean online timing; unexpected onset is scored before entering context | Once anomaly enters history, subsequent anomalous values may become predictable and scores fall; contamination via next update | Point vs segment scoring, onset/recovery, score-before-state-update discipline |
| Direct multi-step forecast: X[t−W:t] → predict X[t+1:t+h] | Future truth arrives later; training/inference loss changes with horizon | A sustained event may remain outside context for several forecast lead times; short and long scales can be represented | Long-horizon uncertainty and stale forecast grows; max aggregation can inflate benign transition scores; target feedback is delayed | Horizon-by-event-duration curves; compare direct vs recursive forecast and calibrated separate horizon scores |
| Persistent streaming forecast: state_t + accepted observations → future | Carries history beyond finite W if state is retained | Long memory and O(1) incremental update | State can absorb an anomaly, and recent context can contaminate even if protected state is frozen | Independent-window vs persistent state; normal-only state; shadow/freeze/rollback; measure contamination and recovery |

Do not freeze W=64. It is the current implementation window only. A future study may retain both a finite input context and persistent state: the context provides explicit local evidence; state carries longer context. Their contribution must be isolated.

## Horizon choice and aggregation

Candidate horizons such as {1, 4, 16, 64} are a hypothesis, not a preset. First inspect sample cadence and training-only / external event-duration metadata. Pick horizons that cover short, intermediate and sustained events in physical time, then freeze them before test labels are opened. If sampling rates differ by dataset, compare duration-based horizons or report the mismatch.

Keep a vector [e_h1, e_h2, …] of calibrated horizon residuals as the primary evidence. Compare:

1. each horizon separately;
2. maximum after per-horizon normal calibration;
3. weighted maximum with weights fixed on normal validation or development streams;
4. calibrated combination trained only on allowed validation labels, if that label access is a distinct supervised detector claim.

A raw max over uncalibrated residuals favors high-variance horizons. Do not tune horizons or weights on final anomaly labels.

## Persistent-state policy audit

| Policy | Benefit | Risk | Minimum measurement |
|---|---|---|---|
| Always-update | Fastest tracking of true normal change | Every transient or persistent anomaly can rewrite the state | contamination curve, anomaly recall after update, recovery |
| Normal-only update gate | Simple protected adaptation | False negatives in the gate admit anomalies; false positives starve adaptation | false admission and new-normal alarm persistence |
| Freeze on suspicion | Protects baseline during alarms | A long transition may trigger indefinite freeze | benign shift delay/FP burden and persistent-anomaly rejection |
| Shadow/quarantine state | Keeps suspicious data available without changing baseline | Shadow can become a second unprotected model; buffer may fill or bias promotion | buffer lifetime/capacity, contamination, promotion rule |
| Rollback-able candidate state | Allows recovery after a bad update | Snapshot and score comparisons are policy-sensitive; rollback may be late | rollback rate, latency and restoration check |
| Multiple approved normal-regime states | Supports recurrence and prevents overwriting old normal | Wrongly admitted regimes persist; pool grows and retrieval can misroute | old-regime recall, false promotion, pool size/use |

The simplest defensible design is protected scoring plus a **bounded temporary quarantine buffer** only if M5 demonstrates a need. Do not name it an “anomaly memory”: it contains suspicious, unconfirmed samples and should expire or be reviewed. A historical regime pool should contain independently confirmed normal regimes only. Pseudo-anomaly prototypes are a separate training-time technique and are not required for the first study.
