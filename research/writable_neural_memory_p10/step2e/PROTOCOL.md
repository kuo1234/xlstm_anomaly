# Step 2e — Restricted TEP Fault-vs-Benign Pilot (frozen protocol)

Authorized by [Issue #15 review 5978181304](https://github.com/kuo1234/xlstm_anomaly/issues/15#issuecomment-5978181304). Step 2d audit PASS; full TEP remains PARTIAL. No RL, classifier, encoder training, SOTA benchmark, point-adjust or rescue tuning.

## Source amendment (preserves Step 2d historical audit)

The author thesis is available from the [official DTU repository](https://backend.orbit.dtu.dk/ws/portalfiles/portal/262630763/Thesis_Christopher_Clarc_Reinartz.pdf): Reinartz (2021), *Automating causal analysis for online diagnosis and planning in complex industrial processes*. Downloaded only on ssh kuo; 4,513,001 bytes, SHA256 `5d4e73b7d676ae77517e509d2f6653a75d151f256d2507bd65746b6d78723d67`. PDF pp95–96 / printed pp74–75, Appendix A.3.1–A.3.2 independently verify nominal initial30h, event activation30h, nominal setpoint changes, and conservative 30–40–30 split. This supersedes the previous UNKNOWNs **for restricted SP/fault evaluation**, without pretending the profile row schema is fully documented or a mode-transition ramp endpoint is settled. Stationary fault dynamics remain FAULT, never NORMAL_B.

SP truth: `[0,30)` NORMAL_A, `[30,70)` TRANSITION/WAIT, `[70, last_time+dt)` NORMAL_B/PROMOTE-safe. Fault: `[0,30)` NORMAL_A, `[30,last_time+dt)` FAULT/PROMOTE-unsafe. Emergency-stopped cases are ineligible; no replacement if a literal selector is missing/stopped. No detector/CV defines endpoints. Source states are evaluator-only; WAIT/safe-write semantics are the reviewer-authorized protocol, not original action annotations.

## Frozen selection, split and inputs

[selection.json](selection.json) fixed before detector outcomes: Mode1 SP1/ramp10h/105%; SP1/ramp10h/95%; SP2/ramp10h/105%; IDV1/100%/Run1; IDV2/100%/Run1. Native seeds/profiles recorded in evaluator_metadata.json. No ModeTransition primary/secondary run added. All initial Mode1, different native seeds; same-mode semantic pairing, not common-random-number causal pairing.

Train: actual timestamps `<20h`, 399 SP / 400 fault points. Scaler uses only this full source-normal train, same protocol as Step2b/c; M0 first80%, final20% calibration q.99. Held-out test timestamps `>=20h`, including pre-event normal20–30h. No fitted/test statistics, test label fitting or early-prefix burn-in deletion. Constant channels retained; source warm-up exclusion is not needed given verified nominal prefix. Numeric53 original measured/manipulated channels, Time removed; no additional/economic channels, mode/case identity, native seed, event time, labels or30/70 truth in policy. Runner loads only train/test arrays; timestamps and source metadata are read by evaluator after seal. IDs only identify outputs, not a policy feature.

φ dimension-only adaptation: window8 ×53=424, dk128 fixed random ReLU, seeds11/22/33. Operators W1 kNN5, W2 f=.995, W3 beta=.1; unchanged score-before-write, block16 causal delayed admission. Seven candidate policies A_no_update, B_always, C_threshold, D_quarantine, D_trail512, DE_stab, DEph_cv; H_hold diagnosis only. `PROMOTE iff self<=1 AND stat<=.5 AND cv<=.10`. Check age256, every128, trail256; executable clean-gap termination remains gap>2 (third clean block), Step2a whole-buffer quarantine512 unchanged. Existing implementations imported, no policy edits.

At3-min cadence: block16=.8h; checkpoint/trail256=12.8h; spacing128=6.4h; fixed512=25.6h. No time-normalized rescue/ablation.

## Seal and access chronology

Protocol/code/subset committed + pushed before scores. Observation-only run writes traces, checkpoints, config, code/raw SHA256 and seal; `labels_read_by_runner=0`, `posthoc=false`, `.10` frozen. Source semantics were exposed in audit/review, so this is **frozen exploratory controlled simulator transfer, not strict confirmatory**. Seal must be committed/pushed before source-state evaluation. Evaluator verifies sealed file/code/raw hashes, source metadata Git blob and remote seal ancestry before reading timestamps/states. Raw data and VUS runtime stay ignored on remote; no complete HDF5 hash claim. Partial-range provenance remains documented.

## Metrics frozen before results

Primary robustness view: seed11/W1 per physical simulation run. Seeds/operators separate robustness trajectories, not independent N. Three SP conditions and two fault types in one initial mode do not prove independent plant replication; no p-value or numerical success gate.

Fault: AP/VUS-PR; secondary VUS-ROC/AUROC; point/event recall; written fraction, false-promotion count/first time; long-fault checkpoint count, .10 and conjunction pass counts/firstpass, promotion and fault-written fraction. Benign all-fault-free traces have **undefined AP/VUS**, retained N/A, not relabelled as faults to manufacture detection metrics.

SP: NORMAL_A FPR; transition FPR/write fraction; transition-period promotion decision count and separately transition-touching write count; post70 NORMAL_B FPR/write fraction; entirely-NORMAL_B promotion count/rate, first time/delay after70; right-censored promotion-wait duration, never-promote; post-safe-promotion FPR; longest unwritten NORMAL_B interval. Never promoting does not alone mean starvation: threshold/always may admit clean blocks without a PROMOTE action; written fraction and FPR are necessary context.

Decision time is latest scored sample in the block (`t[end-1]`), since admission occurs after scoring. A decision after70 that writes a trailing window reaching before70 is separately unsafe-boundary-touching, not an entirely-safe NORMAL_B promotion. Fault promotion means any written fault point; no label majority relaxation. Promotion-wait cost capped at observed horizon (last timestamp+dt); censoring explicit, not imputed first event. Global written fraction, occupancy provenance ledger, segment durations/delays and per-case deltas also reported. Occupancy is retained entries/write ledger, not effective matrix rank.

Checkpoints classified by whole trailing256 source state; mixed windows separate. H_hold seed11/W1 physical-segment CV distributions and .10 pass rates are descriptive; no fitted threshold or independent-checkpoint claim. Machine/case-level ΔAP and ΔVUS only for fault arms; benign ΔFPR/Δwritten separately. No pooled mean-only success claim.

## Qualitative verdict and stop

Report whether frozen logic distinguishes fault rejection from actual settled-normal admission, including early/late trade-off and bypassing quarantine. No tuned gate. Use TRANSFER_SUPPORTED / PARTIAL_TRANSFER / TRANSFER_NOT_SUPPORTED, with physical-case evidence and limits. Even positive findings do not authorize Step3/RL. Stop for review.
