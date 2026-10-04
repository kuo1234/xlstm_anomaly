# Pilot P1 — structural transfer not supported (pending review)

**STRUCTURAL_TRANSFER_NOT_SUPPORTED** for the frozen universal fault-high concentration direction. Six new physical simulations / six native seeds; not strict confirmatory or a real-world deployment test. Stop this route; no rescue rule, alternate feature/threshold, new case selection or second pilot. The initial decision memo remains unchanged, preserving why this experiment was chosen before outcomes.

## Task / provenance / exposure

[Open research decision authorization](https://github.com/kuo1234/xlstm_anomaly/issues/15#issuecomment-5978818835). [Decision memo](RESEARCH_DECISION.md) compares six fundamentally different routes, selects structural transfer for information per cost and explicit falsification; not mechanical adherence to Step2g. [Protocol](PROTOCOL.md) froze the literal cases/features/runs before acquisition and evaluator. All bytes and compute on ssh kuo, none downloaded locally. Official DTU DOI10.11583/DTU.13385936.v1, exact API metadata and official bounded byte ranges; source hashes recorded. Full-file HDF5 SHA unknown/not acquired, no mirror. Cache remains below64MiB cap.

Exposure audit searches prior tracked documents/scripts/README and all-ref exact-path commit hits. It finds no evidenced pre-pilot extraction at these paths (own selection commit listed); absence of external/untracked access cannot be proven. Source family labels/semantics known from development. Curator inspects profiles/activation timestamps before runner to verify compatibility, nominal prefix and native seeds: this source-metadata exposure is explicitly logged, not falsely called label-blind. Runner sees only numeric train/test arrays (hashes timestamps without parsing); point/source-state vectors attached only by evaluator after pushed seal. Claim: **frozen exploratory simulator transfer**.

Author thesis Appendix A.3.2 applies30-40-30 split to SP variations as well as fault simulations. SP NORMAL_B>=70h is this source interpretation, not endpoint chosen from scores; profile initialization and30h activation verified. With ramp0/20/30, changes finish30/50/60h. A blanket source split is conservative metadata convention, not proof that every realized stochastic trajectory is exactly stationary at70h. Fault>=30h remains FAULT regardless score/CV.

## Independent source / split audit

| id | native_seed | ramp_hours | fit | cal | test |
| --- | --- | --- | --- | --- | --- |
| pilot01 | 3010000 | 0.000000 | 319 | 80 | 1601 |
| pilot02 | 3010002 | 20.000000 | 319 | 80 | 1601 |
| pilot03 | 3010003 | 30.000000 | 319 | 80 | 1601 |
| pilot04 | 34990 | 1.000000 | 320 | 80 | 1601 |
| pilot05 | 47570 | 1.000000 | 320 | 80 | 1601 |
| pilot06 | 40737 | 1.000000 | 320 | 80 | 1601 |

pilot01=SP1+5% ramp0,02=SP1−5% ramp20,03=SP2+5% ramp30;04=IDV3,05=IDV4,06=IDV5, magnitude100 literalRun1. All completed. No replacement. All native seeds differ from old development seeds; no matching old train/test SHA. No duplicate selected native seeds or train/test files. Independence is simulation realization within one plant/model/mode, not six independent physical industrial plants. Ramp and SP seed change together, so no causal attribution of changes to seed alone.

Strict FIT first80% of source-normal<20h prefix; CAL remaining80points only q.99 score calibration; TEST>=20h1601points no fitting/writes. Frozen M0/R0, random ReLUφ53×8→128, W1/W2f=.995/W3β=.1, seeds11/22/33, sd_floor.02, clip20 and predetermined no-clip. No representation training or classifier. Registered top5=largest5 channel mean residual² /total; scalar norm/CV controls. Fault-high direction preserved, not flipped after seeing AUROC<.5.

## Seal chronology

Decision/code/selection commit869398f27177265d37ab1d47fabe6f416429dee1 pushed before acquisition. Manifest/source audit commitf66764bb1acca1173c670eb0f563b2673572b91f pushed before extraction. Observation-only seal9040cf558db4427649220dfb7c94e39fd101ee51 pushed BEFORE evaluation.

Seal SHA256 c90be5c47d825044c388de59fc99882b8df7c5340c81201c0668a3234bebd528, UTC2026-10-04T10:25:52.888657+00:00. labels_read_by_runner=0; curator_metadata_read_before_seal=true. Evaluator verifies exact pushed seal blob, ancestry, all raw/code/config/trace/protocol/source-metadata hashes; first state evaluation UTC2026-10-04T10:26:15.691599+00:00. Access logs committed. No sealed code/config/folds/features altered after outcomes.

108traces=6cases×3seeds×3operators×2views. Extraction every trailing256points with ends256 stride128. Evaluator matches same wholly FAULT/NORMAL_B ends1280/1408/1536 (83.95/90.35/96.75h). Three correlated windows per run, seeds/operators robustness only. Nine pair comparisons are dependent comparisons sharing six runs, not independent N=9. Physical-case median AUROC/AP below are descriptive on3fault/3benign; no significance claim or interval.

## Outcomes

Primary W1/seed11 clip, physical-case medians:

| view | seed | op | case | state | log_score | cv | top5_energy | mean_score_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fit_only_clip | 11 | W1 | pilot01 | NORMAL_B | 4.243002 | 0.010631 | 0.428518 | 69.616535 |
| fit_only_clip | 11 | W1 | pilot02 | NORMAL_B | 4.216591 | 0.007421 | 0.450277 | 67.801963 |
| fit_only_clip | 11 | W1 | pilot03 | NORMAL_B | 1.994276 | 0.122644 | 0.233583 | 7.346880 |
| fit_only_clip | 11 | W1 | pilot04 | FAULT | 1.969975 | 0.119745 | 0.173284 | 7.170495 |
| fit_only_clip | 11 | W1 | pilot05 | FAULT | 3.061503 | 0.018120 | 0.901679 | 21.359627 |
| fit_only_clip | 11 | W1 | pilot06 | FAULT | 1.970156 | 0.113904 | 0.146406 | 7.171798 |

Full no-clip medians:

| view | seed | op | case | state | log_score | cv | top5_energy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fit_only_no_clip | 11 | W1 | pilot01 | NORMAL_B | 5.141699 | 0.008435 | 0.827043 |
| fit_only_no_clip | 11 | W1 | pilot02 | NORMAL_B | 5.143139 | 0.006346 | 0.846310 |
| fit_only_no_clip | 11 | W1 | pilot03 | NORMAL_B | 1.994276 | 0.122644 | 0.233583 |
| fit_only_no_clip | 11 | W1 | pilot04 | FAULT | 1.969975 | 0.119745 | 0.173284 |
| fit_only_no_clip | 11 | W1 | pilot05 | FAULT | 3.474084 | 0.029897 | 0.956555 |
| fit_only_no_clip | 11 | W1 | pilot06 | FAULT | 1.970156 | 0.113904 | 0.146406 |

Primary fault-minus-benign concentration at each matched age:

| view | seed | op | fault_case | benign_case | min_delta | max_delta | median_delta | fault_high_fraction | matched_ages |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fit_only_clip | 11 | W1 | pilot04 | pilot01 | -0.257609 | -0.251149 | -0.252838 | 0.000000 | 3 |
| fit_only_clip | 11 | W1 | pilot04 | pilot02 | -0.279368 | -0.268645 | -0.277751 | 0.000000 | 3 |
| fit_only_clip | 11 | W1 | pilot04 | pilot03 | -0.060299 | -0.055453 | -0.056198 | 0.000000 | 3 |
| fit_only_clip | 11 | W1 | pilot05 | pilot01 | 0.468750 | 0.475556 | 0.475074 | 1.000000 | 3 |
| fit_only_clip | 11 | W1 | pilot05 | pilot02 | 0.450643 | 0.453315 | 0.451254 | 1.000000 | 3 |
| fit_only_clip | 11 | W1 | pilot05 | pilot03 | 0.664445 | 0.676485 | 0.668096 | 1.000000 | 3 |
| fit_only_clip | 11 | W1 | pilot06 | pilot01 | -0.286133 | -0.275768 | -0.284637 | 0.000000 | 3 |
| fit_only_clip | 11 | W1 | pilot06 | pilot02 | -0.307892 | -0.300681 | -0.302133 | 0.000000 | 3 |
| fit_only_clip | 11 | W1 | pilot06 | pilot03 | -0.088941 | -0.083229 | -0.084723 | 0.000000 | 3 |

IDV3 and5 are BELOW EVERY benign case at EVERY primary age, contrary to development; IDV4 remains above every benign. No-clip retains primary ordering. IDV5 is fault-low against all benign in every seed/operator; IDV3 remains below both SP1 cases, with SP2 comparison changing sign for some W2/W3 cells. Retain all reversals and mixed comparisons; do not select the best operator.

Primary physical-case metrics (frozen fault-high orientation; no trained classifier):

| view | seed | op | feature | case_AUROC_fault_high | case_AP_fault_high | n_physical_cases |
| --- | --- | --- | --- | --- | --- | --- |
| fit_only_clip | 11 | W1 | log_score | 0.111111 | 0.411111 | 6 |
| fit_only_clip | 11 | W1 | cv | 0.666667 | 0.638889 | 6 |
| fit_only_clip | 11 | W1 | top5_energy | 0.333333 | 0.633333 | 6 |

All frozen robustness cells:

| view | feature | min | max | mean |
| --- | --- | --- | --- | --- |
| fit_only_clip | cv | 0.666667 | 0.777778 | 0.703704 |
| fit_only_clip | log_score | 0.111111 | 0.222222 | 0.148148 |
| fit_only_clip | top5_energy | 0.333333 | 0.444444 | 0.345679 |
| fit_only_no_clip | cv | 0.666667 | 0.777778 | 0.703704 |
| fit_only_no_clip | log_score | 0.111111 | 0.222222 | 0.148148 |
| fit_only_no_clip | top5_energy | 0.333333 | 0.444444 | 0.345679 |

Top5 AUROC primary.333333; robustness.333333–.444444. CV.666667–.777778 is a descriptive ranking, not a tuned rule or evidence that instability always signals fault. Scalar log-score.111111–.222222. Do not invert scores or choose CV as a replacement method after outcomes. AP is reported for the fixed3/3prevalence only.

### Crucial boundary: stable-fault vs all-fault

Primary CV pass at existing.10: SP1±3/3ages, SP2 0/3; IDV3 0/3, IDV4 3/3, IDV5 0/3. IDV3/5 mean score~7.17 with CV~.12/.11; IDV4 score~21.36/CV.01812. Both fail the low-CV criterion here; this pilot did not run the quarantine/admission gate. This pilot falsifies **universal fault-high concentration**, not every conditional concentration rule among high-deviation low-CV segments. Only ONE new fault represents that conditional subgroup and it is concentration-high; subgroup generalization remains insufficiently tested. Cases retained as frozen; do not relabel/drop weak faults, filter by outcome to rescue success, or add new faults now.

This distinction also raises a Detect-stage issue: some source faults barely depart in this scalar representation. It is unsafe to treat diffuse/low-deviation residuals as evidence of legal new normal. Observed concentration is not a universal health semantic.

## Decision update and stop

The original finding is fault-family-dependent. Benign new seeds preserve the same broad contrast (SP1 concentrated more than SP2), but unseen faults can fall below all benign, and one IDV3/SP2 comparison is operator-sensitive. This supports limiting Step2f structural PASS to its development cases; it cannot authorize a generic top5 PROMOTE/DISCARD rule. No operational safety measured, no classification policy, no adaptation trial.

Stop the selected structural-universality route. No NN/LEFT/graph/Verify second experiment or rescue tuning in this task. Passive future prediction improvement would still not certify health because memory writes do not change plant behavior. Source-state labels cannot be substituted as operational context. Review should choose a new, explicit hypothesis on observable process-response/context or conditional stable-fault evidence; no automatic model/cycle expansion is justified. Failure does not prove all observation-only evidence impossible.

## Checks and limitations

11 new targeted tests +13 reused Step2f correctness tests PASS: timestamp/source isolation, FIT/CAL separation, baseline config parity, top5 formula, raw loader reads train/test only, missing/tampered seal blocked, FIT-only writes, profile nominal prefix, and prior causality/clip/residual-norm/third-clean-block behavior. Sealed runner reuses unchanged Step2f extraction primitives; Step2f previously audited45regression traces error0 (not rerun as new empirical controls here). git diff --check and full seal hash/remote verification PASS.

Controlled simulator only; six realization families in one mode;3fault IDs/3SP conditions; ramp/seed confounded; historically known source taxonomy; curation exposure before extraction; old-path history audits cannot prove absence of all untracked reads; finite late windows and conditional low-CV subgroup only1fault; source settling convention; scaling/clip influence margins. Strict confirmatory validation and safe admission remain unavailable. Raw arrays ignored remote; derived traces/hashes/results tracked.
