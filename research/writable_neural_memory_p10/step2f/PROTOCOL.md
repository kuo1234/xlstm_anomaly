# Step2f-A — Frozen preprocessing / residual evidence audit

Authorized task [5978542488](https://github.com/kuo1234/xlstm_anomaly/issues/15#issuecomment-5978542488). Not a controller, CV tuning, RL or LEFT experiment. Step2f-B only if A_NEEDS_LEARNED_TEMPORAL; no neural arm or optimizer in this A implementation.

## Fixed data and chronology

Same five literal source-event runs as Step2e; raw arrays remain remote on ssh kuo, ignored under data/step2e. Labels previously exposed in Step2e, so exploratory diagnostic, not confirmation. Three SP interventions share one seed/prefix; five runs/three seed families (one benign). No new acquisition or independent benign replication claim.

Freeze code/config/split → commit/push → observation-only evidence run/seal → commit/push seal → state evaluator. Labels/30–70h timestamps/path/SP-IDV/seed unavailable to runner. Sealed source metadata Git blob checked by evaluator. Output IDs only identify arrays, never representation features.

Primary FIT_NORMAL: first80% of each prior0–20h source-normal train; SP319/fault320 points. CAL_NORMAL: remaining80points. TEST: unchanged>=20h. FIT fits scaler, M0, residual manifold and PCA. CAL only q.99 score calibration; never scaler/model/manifold fitting. TEST no fitting, writes or optimizer. Train count is small; manifold is a feasibility diagnostic, not a well-estimated population model.

Three frozen views:

1. `step2e_regression_clip`: exact prior full-train scaler with sd_floor.02 / clip20 and M0 first80%. **Historical regression control only**, explicitly reproduces the previous fit/cal scaler overlap; not the corrected primary arm.
2. `fit_only_clip`: strict FIT-only scaler, original clip20; primary corrected diagnostic.
3. `fit_only_no_clip`: same strict scaler, no clipping; predetermined diagnostic comparison, not a selected new operational clip value.

A fixed-prediction value-no-clip score additionally removes value clipping while retaining each view's predictions/keys to isolate output saturation from key changes. Never tune a new clip. Per-point residual vector and norm, clipping mask and normal-fit statistics sealed before state labels. Clipping means strict `abs(preclip z)>20`; boundary exactly20 is not clipped. Near-constant channels: raw FIT std<.02, fixed engineering sd floor. Zero-based original residual channels0–40 measurements,41–52 manipulated variables, constants retained.

## Representation and evidence

R0 fixed random ReLU φ only, 53×8→dk128; seeds11/22/33; W1 kNN5/W2f=.995/W3beta=.1. M0 receives only FIT keys/values; **frozen no-update reference**, CAL/TEST never writes. Residual is53-D `r=x−M(phi(past8))`; score=norm(r). This audits scalar compression independently of online policy feedback. Does not rerun Step2e promotion policies. Regression compares all45 control trajectories to prior A_no_update float32 scores.

Normal-only residual manifold: mean/covariance of FIT residuals, shrinkage.1 to diagonal and ridge1e-6I; nearest single healthy residual prototype / Mahalanobis point & centroid distance. Residual channel scales fitted on FIT, floor.02. Covariance/correlation distance and PCA top5 derived from FIT only. FIT residuals include in-bank queries: optimistic normal-manifold reference, disclosed; no CAL fitting to fix it. No feature/tuning search.

Fixed windows: ends256,384,... every128; trailing256, no source age/event selection in extraction. Source-labelled evaluation matches same end indices across cases and requires full windows FAULT or NORMAL_B. This ensures same time-since-event in primary comparison, not mismatched early-fault/late-benign. Mixed/TRANSITION retained for diagnostics, never relabelled healthy/fault. Scientific comparison uses source ages only in evaluator, not policy input. Primary seed11/W1; seeds/operators robustness, not independent N.

A0: log(mean scalar score), CV. A1: A0 +53 signed window-mean residual coordinates normalized by FIT residual sd. A2: A0 + normal-fit Mahalanobis point/centroid distance, covariance/correlation deviation, manipulated energy, near-constant-channel energy, top5 energy concentration, cosine of mean direction to healthy prototype. Also state/channel mean/sd/signed direction/covariance/top5 patterns. No frequency/LEFT fusion or trainable temporal layer.

## Frozen supervised upper-bound diagnostic

Fixed logistic probe C=1, solver defaults, seed731, max_iter2000; StandardScaler fits only labelled probe train folds (not representation or detector fitting). State labels allowed **offline diagnostic supervised upper bound only**, never admission policy. Equal total weight per physical run, not checkpoint sample inflation.

Two disjoint run/intervention-family folds:

- Train SP2+IDV2 (case03/05), test both SP1 variants+IDV1 (case01/02/04).
- Reverse: train SP1 variants+IDV1, test SP2+IDV2.

No physical run or SP-intervention family shared across train/test. **Benign source seed is nevertheless shared across folds**, so not held-out healthy noise/seed validation. Age windows correlated; report case-averaged prediction AUROC/AP separately from window diagnostics; 2–3 heldout runs per fold, no significance estimate. Unknown/empty classes fail closed; no label-driven fallback/fold changes.

## Gate, before outcomes

Assess preprocessing first. PREPROCESSING_CONFOUND_FOUND only if clipping materially causes the low-CV fault interpretation: compare fixed clip/no-clip counterparts, CV pass at the existing.10 diagnostic threshold, magnitudes, affected channels/energy, and whether low-CV faults persist without clipping. High clipping rate alone does not prove it causes stationary-fault aliasing. If confound is the main explanation, stop model claim and ask reviewer to amend preprocessing; no new clip tuning or primary admission rerun.

Otherwise assess incremental evidence over A0: physical-case direction/prototype consistency, both intervention-heldout probe folds, robustness seeds/operators, clip/no-clip sensitivity. Do not choose a best feature/seed/operator/threshold. Stable residual incremental separation supports A_PASS_RESIDUAL_SUFFICIENT and stops before NN; insufficient residual structure with credible temporal signal is A_NEEDS_LEARNED_TEMPORAL and alone authorizes B. No consistent observable signal → A_NO_OBSERVABLE_SIGNAL, no forced NN rescue. These are qualitative evidence gates, no outcome-convenient numerical success threshold.

Final task verdict from allowed list: RESIDUAL_EVIDENCE_SUFFICIENT / LEARNED_TEMPORAL_EVIDENCE_SUPPORTED / LEARNED_TEMPORAL_EVIDENCE_NOT_SUPPORTED / PREPROCESSING_CONFOUND_FOUND / NO_OBSERVATION_ONLY_SIGNAL. If B not authorized, explicitly NEURAL_ARM_NOT_RUN. No prospective rule, controller, RL or full LEFT. Stop for review and post impact note #16.
