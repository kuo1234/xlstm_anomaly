# Step 2c — Frozen Stabilisation Transfer Test

Frozen before new evaluation labels. Branch `research/p7-p10-segment-memory`, baseline `65c0ed9`; Issue #15 review 5975468315. The owner's task authorizes this bounded CPU transfer run and supersedes the older M0 experiment queue only for Step 2c. Historical M0 gates/results remain intact; no training or Step 3.

1. Static exposure audit → protocol/code/tests + observation manifest **commit/push**.
2. Observation-only smoke seed 11 (no metrics/labels); then all nine machines × seeds 11/22/33 × W1/W2_f0995/W3_b01 × seven policies, plus H_hold diagnostic. Run score/checkpoint/manifest/config hashes → seal **commit/push**. No evaluation label read/download before successful push.
3. Evaluator independently checks committed seal bytes, all code/config/artifact hashes and that seal commit is an ancestor of configured remote research branch; then downloads and logs nine label vectors. Preserve labels outside Git. Evaluation cannot tune/run policies.

## Frozen method

`DEph_cv`: PROMOTE iff **self <= 1.0 AND stat <= 0.5 AND cv <= 0.10**. No new features, checkpoint schedules, thresholds, conjunctions, rescues, classifier or oracle threshold appendix. `posthoc=false` for this transfer run; the rule's provenance is **Step 2b post-hoc development**.

Seven evaluated policies: A_no_update, B_always, C_threshold, D_quarantine (whole buffer fixed512 Step 2a), D_trail512, DE_stab, DEph_cv. H_hold is an always-KEEP reference diagnostic, not an eighth candidate. Exact executable source imported unchanged; validation forbids all config changes.

Fixed random ReLU φ; window8, dk128, seeds11/22/33, W1 kNN5, W2 f=.995, W3 beta=.1. Same SMD 38-channel schema; no dimension adaptation required. Train-only z-score (the entire source-designated normal train, including calibration), SD floor .02, clipping ±20; M0 first80%, tau q.99 on final20%. This preserves Step 2b protocol: calibration influences scaler as already specified, but **test never fits normalization or tau**. Source train normality is an assumption, not verified by unavailable train labels. Pure memory retrieval batched at 256 queries for peak RAM; no intervening writes, scientific operator unchanged.

Block16 score-before-write, 16-step delayed causal admission. Evidence at age256 then every128, trailing256, self quantile .9, stat_max .5. PROMOTE in D_trail512/DE policies writes only trailing256, older held points discarded. D_trail512 promotes at age>=512. **Executable clean-gap semantics retained:** `gap > 2`, i.e. DISCARD on the **third** consecutive clean block, commit that clean tail. Earlier prose said two; not corrected/tuned in Step 2c. H_hold/evidence features and trial-copy logic remain Step 2b. Frozen future-M0 scores are pointwise frozen retrieval, never test-normalization fitting.

## Selection, data and admissible claims

Nine machines in `p10_step2c_data.MACHINES`, first3 per numeric group after fixed exclusions; full streams, no label/detector screening. Official OmniAnomaly `7fb0e0a…`; observation hashes sealed. All labels historically exposed by M1 audit. **Frozen exploratory machine-transfer**, never strict confirmatory. HAI LFS unavailable / SWaT restricted: BLOCKED, no silent fallback. Audit considers AnDri and other drift candidates; no protocol-compatible unexposed safe-transition source established.

## Frozen evaluation definitions

- Each machine/seed/operator/policy: AP, VUS-PR (vus0.0.6/window100), secondary VUS-ROC/AUROC, tau point/event recall and nonanomaly FPR, anomaly/overall written fractions, promotion counts/times, quarantine duration/censoring, time-to-promotion and memory occupancy trajectory. Event = maximal label1 run; event hit if any score exceeds tau, **no point-adjust**. Occupancy is retained entry/ledger count; W2/W3 fixed matrix storage separately, not effective memory rank.
- Primary machine table averages **within machine** over all3 seeds/all3 operators; operator-specific means and raw units separate. ΔAP/ΔVUS-PR against C_threshold/D_quarantine/D_trail512/DE_stab/A_no_update. Nine available machine entities; 81 seed/operator trajectories do not create N=81.
- H_hold physical diagnostic primary: **seed11/W1** segment/checkpoint boundaries (label-free); each machine CV medians, each physical reference segment, direction agreement. Other seed/operator checkpoints are robustness only. Class fault if trailing label1 fraction>=.5; nonanomaly if0; otherwise mixed. Report CV-only and full-conjunction pass rates at frozen .10. Nonanomaly is NOT approved settled benign regime.
- Long fault = maximal label1 run >=256. Per entity/seed/operator/policy report checkpoint opportunities whose t-1 is inside event, n_pass_cv, n_pass_conjunction, first pass times, promotion touching event, fraction written; all label1 episodes listed regardless of checkpoint presence. Promotion fault count conservatively includes **any** anomalous point; majority-fault count separately for compatibility with development reporting. A label-free normal checkpoint promotion can contain context of prior faults; it is not certified safe admission.
- Generic persistent nonanomaly FPR may be described, but **Q4 / benign promotion / post-shift adaptation = NOT EVALUABLE ON THIS DATASET**. No pseudo benign-ground-truth plot.

Qualitative review verdict only: TRANSFER_SUPPORTED requires consistent independent-source dynamics, low long-fault promotion, broadly distributed benefit and actual benefit on identifiable benign cases without tuning. PARTIAL_TRANSFER if safety transfers but benign adaptation unavailable or directions mixed. TRANSFER_NOT_SUPPORTED for direction reversals, substantial fault promotion or broadly worse frozen rule. No new numerical gate. A negative result stops; positive result still waits reviewer. No RL, learned stopping, mLSTM arm, SOTA, checkpoint-level significance or Step3.
