# Streaming options and falsification design

These are reviewable proposals for a later authorization, not a performance protocol seal or permission to train. No option is selected by test labels. Engineering closeness, causal validity and scientific value are separate questions.

## Score-path comparison

| Option | Architectural change and causality | Value and principal limitation |
|---|---|---|
| Stateful improved reconstruction | Preserve both stacks/projections and execute stack.step on each new x_t once; score x_t after ingest, before intervention. | Least change to native improved architecture; best first parity control. Target is visible through residual paths, so state harm may be weak/irrelevant and anomaly can already alter candidate state. Changing to point residual changes native score/calibration. |
| Chunked sequence reconstruction | Run disjoint chunks with complete carry; per-token causal model can emit as data arrive. | If implemented as repeated steps, just a delivery schedule, not a new scientific architecture. Waiting for full chunks adds latency; last-token bottleneck or bidirectional reconstruction cannot backdate earlier scores. |
| Encoder-only one-step prediction | Project x_t → recurrent encoder state → predictive head for x[t+1]. New shifted objective; existing reconstruction checkpoint is not a substitute. | Clearest pre-observation innovation and least unnecessary decoder history; preferred **future mechanism path**, subject to separate training approval. New track, not original xLSTMAD reproduction. |
| Stateful encoder/decoder forecast | Need a temporal contract separating encoder observation updates from decoder forecast rollouts and their states. | Can preserve more modules, but decoder horizon history has two clocks; do not repeatedly ingest pseudo-futures into the physical stream state. More machinery than required for one-step diagnosis. |
| Multi-step forecast | Queue predictions with issue time, target time, lead and model/state version. Score only when truth arrives. | Tests predictability at several horizons but increases warmup, scoring/latency ambiguity and error propagation; not the first gate. |
| Latent/state distance | Compare complete state/statistics to a reference using only past observations. | No automatic anomaly semantics, state scale/gauge and reset discontinuities contaminate the score; a reset trivially changes the measured object. No validated reference/calibration; keep exploratory, not a rescue metric. |

Forecasting is preferable for an **innovation** hypothesis, not because reconstruction is inherently noncausal. Smooth faults may be highly predictable; forecast accuracy alone does not establish detection quality. For TSB neither path supplies missing independent drift boundaries. Retain native windowed reconstruction as a separately named baseline, with valid endpoint alignment.

## Exact score/intervention clock

A proposed one-step streaming forecaster should use the following contract. `p_t` was issued at t−1 without access to x_t; scaler and weights are frozen.

1. At t receive x_t and finalize immutable residual `r_t = loss(p_t,x_t)`. At initial warmup without p_t, score is unavailable, not zero.
2. Observer updates from information available by t, including r_t if specified, and chooses a_t.
3. Choose effective **pre-ingestion** state: KEEP uses S[t−1]; RESET uses the complete native initial state. Consume x_t **once in the selected trajectory**, yielding S_t; issue p[t+1]. Reset excludes old history but includes current observation in the next prediction.
4. Log action, score availability, state/config hash, stream clock and ingest count. The action cannot alter r_t or p_t.

For reconstruction, x_t must first pass through a candidate state to produce its residual. Score it once, then KEEP commits that candidate or RESET discards it. The next observation begins fresh; x_t is **not replayed after reset**. This is the prototype's clock and it differs from the proposed forecast clock. A future design must choose one contract; “then update next state” alone is underspecified. In either clock, a reset triggered by an anomalous x_t can harm subsequent detection; there is no inference-time oracle of benign drift.

## Intervention comparison

| Intervention | Clean definition | Judgment / added gate |
|---|---|---|
| Whole-state hard reset | All encoder/decoder recurrent and conv states to native initial condition; preserve emitted scores and frozen parameters/scaler. | Clean first diagnostic; warmup cost and loss of useful context must be counted. |
| Selected layer / sLSTM-only / mLSTM-only | Clear the complete chosen layer state, including its conv; other layers retain history. | Useful attribution after whole-state evidence, not a shortcut to full reset. Preselect layers, do not search test labels. |
| Fixed carry horizon | Replay the last L available observations from fresh state for every prediction, or periodic reset with explicitly variable age. | Mandatory alternative explanation. Rolling replay and periodic reset have different context-age distributions and compute; report both. |
| External retention factor | Change the old-state contribution consistently with stabilized equations, rather than scaling an arbitrary state tuple. | New method and numerical analysis required; prohibited this round. Native forget gates already solve part of this task. |
| Warm-state restoration | Restore a complete compatible tuple whose observations all precede the decision. | Requires state/config/scaler identity, causal selection and snapshot copying. A bank/controller is prohibited this round and has broad prior-art threats. |
| Conv-only reset | Remove local preprocessing history while retaining cell memories. | Future negative/attribution control: if all benefit comes here, claim convolution transient correction rather than recurrent memory adaptation. |

## Distinguishing harmful history from shorter context

A hard reset **is** context truncation for a deterministic frozen recurrence. There is no identifiable “staleness versus truncation” separation from a reset–carry comparison alone. Define staleness operationally as **harm due to incompatible remote history after controlling recent observations and capacity to model the target regime**, then test that interaction.

Proposed controlled paired diagnostic (not run): construct two equally long prehistories, A and B, followed by the **same exact B-regime suffix**. One history is compatible with B; the other comes from a different, already learnable regime A. Freeze weights, scale, thresholds, random seeds and the suffix, and compare at identical positions after the same L recent observations. Both arms consumed the same number of points; only remote content differs. Include A→A, B→B stationary controls, A→B and recurrence B→A→B, plus no-anomaly, transient anomaly and mixed shift/anomaly conditions. Ground-truth boundaries are evaluator-only.

Before interpreting state harm, establish that the *same frozen weights* can model independently sampled B under a compatible-history control using a predeclared adequate-fit margin. If B is outside modeled support and both carry/reset fail, this is weight/model misspecification, not demonstrated state staleness. A level-scale drift may instead expose fixed-scaler mismatch; report normalization-only controls without letting test statistics leak.

Compare KEEP, oracle-boundary RESET (diagnostic only), fixed-L rolling replay, periodic reset, a simple causal residual/change-point trigger and a reset-count/age-matched nonadaptive schedule. The latter may use an evaluated policy's reset count only as an explicitly retrospective diagnostic, never for deployed decision-making. Hold available observed prefix, forecast lead, calibration and anomaly events fixed. Charge repeated replay operations and warmup abstention; do not pretend equal data availability means equal compute.

Evidence of harmful incompatible history would require a predeclared adverse prefix-content effect on the common suffix, while useful compatible long history still helps, and intervention reverses that adverse effect without losing anomaly sensitivity. If fixed-L context matches all gains, report **context truncation suffices**, not a new memory mechanism. If LSTM/GRU reproduce it, withdraw xLSTM specificity. If an oracle reset cannot help under matched semantics, there is no reason to build a detector-triggered reset controller. Known boundaries and labels remain outside the deployed model/observer.

This requires a later protocol with numerical effect margins, source/seed sampling, censoring, latency, warmup, multiplicity and failure criteria frozen **before** outcomes. Existing H3b thresholds do not silently transfer to a different forecasting architecture.

## Alternatives requested by Issue #22

| Alternative | Why cleaner / claim | Required data | Largest threat | Minimum future cost |
|---|---|---|---|---|
| Architecture-neutral KEEP/RESET diagnostic | Common input/state/score contract isolates history harm before choosing a backbone. | Controlled regimes supported by each frozen model; independently labeled anomalies. | Reset/forgetting, HSO, RSI and selective SSM literature. | A small predeclared LSTM or GRU and xLSTM pair; frozen diagnostic inference after separately approved matched training. |
| Fixed-horizon replay | Exact recent-history semantics, no drift observer; tests whether short context alone suffices. | Same sequences and checkpoint. | Standard context truncation. | No new model training; O(L) step replay per scored token, explicitly charged. |
| Stateful improved reconstruction | Existing validated modules and checkpoint, two explicit stack states. | D8 compatible synthetic observation streams first. | Identity shortcut, training/carry context mismatch; weak novelty. | Random parity is already done; scientific checkpoint comparison remains unauthorized. |
| Encoder-only predictive track | One observation clock, one state stack, no decoder rollout ambiguity. | Normal training prefix covering candidate regimes and controlled shifts. | Generic recurrent forecasting/state control. | One new objective/head and matched baseline training, only after reviewer approval. |
| Layer/conv attribution | Identifies where harmful history lives; no learned policy. | Same controlled suffix experiment. | Ordinary ablation; multiple comparisons. | Several predeclared inference arms; no trainable controller. |
| State bank, dual-timescale state, confidence/entropy controller | Potentially useful under recurrence, but presently **less** clean than hard reset because selection/state compatibility add hypotheses. | Repeated regimes, known chronology, independent semantics, calibrated uncertainty. | MemDA/Leto/RSI, recurrent state retrieval, learned gating; no verified novelty gap. | Larger design and evaluation; reject for the next minimal gate, do not implement now. |
