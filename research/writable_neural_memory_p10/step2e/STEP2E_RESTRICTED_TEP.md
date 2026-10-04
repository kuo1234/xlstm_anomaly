# Step 2e — Restricted TEP Fault-vs-Benign Pilot

**TRANSFER_NOT_SUPPORTED — pending review.**

Frozen stabilisation conjunction does not safely distinguish the two source semantics in this restricted pilot. It adapts both SP1 shifts, but does so during the predeclared WAIT interval and also promotes both long faults. This is a negative result for frozen admission logic on the selected simulator cases; no rule rescue or RL experiment.

## 1. Source, frozen protocol and selection

[Protocol](PROTOCOL.md), [selector](selection.json), [dataset manifest](dataset_manifest.json) and [evaluator metadata](evaluator_metadata.json). Review [5978181304](https://github.com/kuo1234/xlstm_anomaly/issues/15#issuecomment-5978181304) accepted Step2d audit PASS/full TEP PARTIAL and authorized restricted Step2e. Author thesis [official DTU PDF](https://backend.orbit.dtu.dk/ws/portalfiles/portal/262630763/Thesis_Christopher_Clarc_Reinartz.pdf), Appendix A.3.1–A.3.2 (PDF95–96/printed74–75), establishes nominal pre-event operation, event30h and conservative40h dynamics after the event for SP variation. Source SHA256 `5d4e73b7d676ae77517e509d2f6653a75d151f256d2507bd65746b6d78723d67`. SP: NORMAL_A<30h; TRANSITION[30,70); NORMAL_B>=70. Fault>=30 remains FAULT even if stationary. Source settling statement is conservative population support, not per-sample physical settling annotation. “Early/unsafe SP promotion” below means violating this **predeclared conservative WAIT protocol**, not proof that the process was physically unhealthy at that timestamp. ModeTransition not evaluated; ramp endpoint still not a primary settled truth.

Acquisition and execution on `ssh kuo` / spark-3994 only, raw under remote ignored `data/step2e/`; no local data download, full HDF5 download or mirror. Official DTU v1 DOI `10.11583/DTU.13385936.v1`, CC0. Selected case paths fixed 2026-10-04T08:43:08.147849+00:00 before detector outcomes. Partial official HDF5 range blocks have exact offsets/SHA256 in manifest; complete modefile checksum remains unverified.

| case | arm | path | native_seed |
| --- | --- | --- | --- |
| case01 | setpoint | Mode1/SpVariation/SimulationCompleted/SP1/tRamp_10/SpMagnitude105 | 3010001 |
| case02 | setpoint | Mode1/SpVariation/SimulationCompleted/SP1/tRamp_10/SpMagnitude95 | 3010001 |
| case03 | setpoint | Mode1/SpVariation/SimulationCompleted/SP2/tRamp_10/SpMagnitude105 | 3010001 |
| case04 | fault | Mode1/SingleFault/SimulationCompleted/IDV1/Mode1_IDVInfo_1_100/Run1 | 21812 |
| case05 | fault | Mode1/SingleFault/SimulationCompleted/IDV2/Mode1_IDVInfo_2_100/Run1 | 20819 |


All cases start in Mode1. **The three SP variants share native seed3010001 and byte-identical normal-train arrays.** They are correlated interventions on one benign seed family, not three independent benign replications. Fault seeds21812/20819 differ from the SP seed and each other; this is not a noise-matched fault-vs-benign causal pair. Five physical run files, **three native-seed families / one benign family**, nine seed/operator robustness trajectories each; no independent N=45 or checkpoints. Protocol shorthand “different native seeds” concerns cross-arm pairing and must not be read as independent SP seeds. Primary seed11/W1 per-case results below; all operators/seeds separately in [units.csv](results/units.csv).

Train actual time<20h:399SP/400fault points, M0 first80%, final20% tau q.99. Scaler fit on full normal train only, same Step2b/c convention; source-normal20–30h held out in test. No test normalization/threshold fitting; original53 channels, constants preserved, train-sd floor.02/clipping20. φ dimension-only53×8=424/dk128, seeds11/22/33. W1 kNN5; W2 f=.995; W3 beta=.1. Seven frozen policies and H_hold reference. Rule `self<=1 AND stat<=.5 AND cv<=.10`; block16, checkpoint256/every128/trail256, age512 arm and clean-gap executable semantics unchanged. No model/feature/threshold selection. At3min cadence: block.8h,256=12.8h,128=6.4h,512=25.6h.

## 2. Seal and evaluator chronology

Protocol/code/subset commit `453ce77` pushed before scoring; observation-only seal commit `572d27bb69f61cdde4669a267377f326ffcdf74c` pushed before evaluation. [Seal](run/seal.json) SHA256 `34c6b78e430b63978e86c4cd3714d080b17d3507a4c6fe142075cdf822f533f6`, labels_read_by_runner=0, prior_source_semantic_exposure=true, posthoc=false, cv_max=.10. Evaluator verified remote seal ancestry and all artifact/code/raw hashes; start 2026-10-04T08:52:12.489299+00:00. [Access log](results/label_access_log.json) records five state-generation accesses after the pushed seal. Source labels/metadata were already exposed by audit/review, so **frozen exploratory controlled simulator transfer**, not strict confirmatory. Paths/SP/IDV/native seed/mode/30–70truth are evaluator-only; policy runner consumes numeric train/test arrays without parsing timestamps or state labels.

## 3. Fault detection and contamination (primary seed11/W1)

AP/VUS are fault-vs-source-normal detection metrics. Test has200normal points then1401fault points (prevalence.8751); near-perfect AP here is an easy dense-fault setting, not broad benchmark evidence. All SP cases have no fault labels, so their AP/VUS are **N/A**, never fabricated by labelling transition as a fault. Threshold/no-update prevent fault writes. DEph_cv equals DE_stab in both primary fault trajectories.

| policy | AP_case04 | AP_case05 | VUS_PR_case04 | VUS_PR_case05 | fault_written_fraction_case04 | fault_written_fraction_case05 | fault_false_promotions_case04 | fault_false_promotions_case05 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_no_update | 1.0000 | 0.9998 | 1.0000 | 0.9998 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| B_always | 0.9270 | 0.8992 | 0.9377 | 0.9079 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| C_threshold | 1.0000 | 0.9998 | 1.0000 | 0.9999 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| DE_stab | 0.9688 | 0.9360 | 0.9736 | 0.9415 | 0.4226 | 0.7545 | 1.0000 | 1.0000 |
| DEph_cv | 0.9688 | 0.9360 | 0.9736 | 0.9415 | 0.4226 | 0.7545 | 1.0000 | 1.0000 |
| D_quarantine | 0.9489 | 0.9370 | 0.9566 | 0.9426 | 0.7602 | 0.9315 | 1.0000 | 1.0000 |
| D_trail512 | 0.9681 | 0.9360 | 0.9735 | 0.9415 | 0.4911 | 0.7545 | 2.0000 | 1.0000 |


Per-fault DEph_cv−threshold: IDV1 ΔAP−.031201 / ΔVUS-PR−.026396; IDV2 −.063823 / −.058345. Both directions negative; no single favorable machine driving a pooled positive claim. All five prespecified baseline comparisons are in [case_deltas.csv](results/case_deltas.csv). Robustness-mean threshold deltas are also negative on both faults (AP−.022197/−.033313; VUS−.019560/−.030414).

## 4. Actual new-normal adaptation and timing

| machine | policy | normal_B_FPR | normal_B_written_fraction | transition_written_fraction | transition_period_promotions | normal_B_safe_promotions | normal_B_max_unwritten_hours |
| --- | --- | --- | --- | --- | --- | --- | --- |
| case01 | A_no_update | 1.0000 | 0.0000 | 0.0000 | 0 | 0 | 30.0500 |
| case01 | B_always | 0.0017 | 1.0000 | 1.0000 | 0 | 0 | 0.0000 |
| case01 | C_threshold | 1.0000 | 0.0000 | 0.0000 | 0 | 0 | 30.0500 |
| case01 | D_quarantine | 0.0017 | 0.9734 | 0.9600 | 1 | 0 | 0.8000 |
| case01 | D_trail512 | 0.0017 | 0.9734 | 0.7700 | 1 | 0 | 0.8000 |
| case01 | DE_stab | 0.0017 | 0.9734 | 0.6100 | 1 | 0 | 0.8000 |
| case01 | DEph_cv | 0.0017 | 0.9734 | 0.6100 | 1 | 0 | 0.8000 |
| case02 | A_no_update | 1.0000 | 0.0000 | 0.0000 | 0 | 0 | 30.0500 |
| case02 | B_always | 0.0000 | 1.0000 | 1.0000 | 0 | 0 | 0.0000 |
| case02 | C_threshold | 1.0000 | 0.0000 | 0.0000 | 0 | 0 | 30.0500 |
| case02 | D_quarantine | 0.0000 | 1.0000 | 1.0000 | 1 | 0 | 0.0000 |
| case02 | D_trail512 | 0.0000 | 1.0000 | 0.9300 | 1 | 0 | 0.0000 |
| case02 | DE_stab | 0.0000 | 1.0000 | 0.7700 | 1 | 0 | 0.0000 |
| case02 | DEph_cv | 0.0000 | 1.0000 | 0.7700 | 1 | 0 | 0.0000 |
| case03 | A_no_update | 0.0915 | 0.0000 | 0.0000 | 0 | 0 | 30.0500 |
| case03 | B_always | 0.0100 | 1.0000 | 1.0000 | 0 | 0 | 0.0000 |
| case03 | C_threshold | 0.0216 | 0.7338 | 0.6300 | 0 | 0 | 1.6000 |
| case03 | D_quarantine | 0.0216 | 0.7338 | 0.6300 | 0 | 0 | 1.6000 |
| case03 | D_trail512 | 0.0200 | 0.6256 | 0.7500 | 1 | 0 | 5.6000 |
| case03 | DE_stab | 0.0516 | 0.3195 | 0.0600 | 0 | 0 | 8.8000 |
| case03 | DEph_cv | 0.0516 | 0.3195 | 0.0600 | 0 | 0 | 8.8000 |


On SP1+5%/-5%, threshold freezes after shift (post70 FPR1, write fraction0). DEph_cv improves FPR to.001664/0 and writes97.34%/100% of NORMAL_B. This is **real source-labelled adaptation benefit**, but it was achieved through early promotion, not a correctly delayed safe promotion. Both decisions occur51.95h, writing39.2–51.95h inside the conservative WAIT interval. On SP2+5%, DEph_cv is worse than threshold: post70FPR.051581 vs.021631; NORMAL_B writes31.95% vs73.38%; longest unwritten interval8.8h. Thus behavior depends on the setpoint intervention, despite the same starting trajectory.

No trajectory in any operator/seed has an entirely-NORMAL_B PROMOTE. First safe-promotion time / delay and post-safe-promotion FPR are N/A; promotion-wait time is right-censored30.05h on the sample-support convention70≤t<100.05 (physical recorded70–100h span30h). This is an action-opportunity measure, **not universal starvation**: SP1 has already adapted via early promotion, always writes100% without a PROMOTE action, and SP2 threshold adapts largely through clean writes. NORMAL_B unwritten fraction / max unwritten interval and FPR separately measure starvation. Full timing, durations/censoring and occupancy ledger in [promotions.csv](results/promotions.csv), [segments.csv](results/segments.csv), [occupancy.csv.gz](results/occupancy.csv.gz).

Primary DEph_cv decision/write intervals:

| machine | decision_hours | write_first_hours | write_last_hours | fault_written | transition_written | normal_B_written |
| --- | --- | --- | --- | --- | --- | --- |
| case01 | 51.9500 | 39.2000 | 51.9500 | 0 | 256 | 0 |
| case02 | 51.9500 | 39.2000 | 51.9500 | 0 | 256 | 0 |
| case04 | 71.9500 | 59.2000 | 71.9500 | 256 | 0 | 0 |
| case05 | 55.1500 | 42.4000 | 55.1500 | 256 | 0 | 0 |

## 5. CV transfer and long-fault checkpoint risk

| machine | start | state | n | cv_median | pass_cv | pass_conjunction |
| --- | --- | --- | --- | --- | --- | --- |
| case01 | 0 | MIXED | 4 | 0.3421 | 0.5000 | 0.5000 |
| case01 | 0 | NORMAL_B | 3 | 0.0104 | 1.0000 | 1.0000 |
| case01 | 0 | TRANSITION | 4 | 0.0140 | 0.7500 | 0.7500 |
| case02 | 0 | MIXED | 4 | 0.3369 | 0.5000 | 0.5000 |
| case02 | 0 | NORMAL_B | 3 | 0.0098 | 1.0000 | 1.0000 |
| case02 | 0 | TRANSITION | 4 | 0.0153 | 0.7500 | 0.7500 |
| case03 | 0 | MIXED | 2 | 0.1388 | 0.0000 | 0.0000 |
| case03 | 0 | TRANSITION | 3 | 0.1117 | 0.0000 | 0.0000 |
| case03 | 800 | MIXED | 1 | 0.1222 | 0.0000 | 0.0000 |
| case04 | 144 | FAULT | 9 | 0.0143 | 0.8889 | 0.4444 |
| case04 | 144 | MIXED | 1 | 0.5421 | 0.0000 | 0.0000 |
| case05 | 192 | FAULT | 9 | 0.0163 | 1.0000 | 0.8889 |
| case05 | 192 | MIXED | 1 | 0.3108 | 0.0000 | 0.0000 |


H_hold seed11/W1: IDV1 fault median CV.014349, IDV2.016313, settled SP1+.010397/SP1−.009820. Fault medians are slightly above the two observed settled-normal medians, so this small directional ordering holds. **Absolute threshold does not separate them**: .10 passes8/9 and9/9 fault checkpoints, while both settled-normal pass3/3. SP2 has no fully-NORMAL_B H_hold checkpoint (no eligible persistent segment then); direction not evaluable for that case. Transition SP1 windows also pass3/4; low CV detects stabilization, not fault-free semantics. Mixed windows retained separately, not assigned by label majority. No pooled checkpoint AUROC or independent-checkpoint evidence claim.

Long-fault table; H_hold is a diagnostic never-promote trajectory, actual DEph_cv is the executed policy:

| machine | policy | n_checkpoints | n_pass_cv | n_pass_conjunction | first_pass_time_hours | was_promoted | first_false_promotion_hours | fraction_fault_written |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| case04 | DEph_cv | 5 | 4 | 1 | 52.7500 | True | 71.9500 | 0.4226 |
| case04 | H_hold | 9 | 8 | 4 | 52.7500 | False | N/A | 0.0000 |
| case05 | DEph_cv | 2 | 2 | 1 | 48.7500 | True | 55.1500 | 0.7545 |
| case05 | H_hold | 9 | 9 | 8 | 48.7500 | False | N/A | 0.0000 |


IDV1 first CV pass52.75h; conjunction eventually passes at71.95h, promoting256fault points. IDV2 first pass48.75h, actual promotion55.15h writing256fault points. Final fault-written fractions42.26%/75.45% exceed the initial promoted suffix because subsequent admissions continue. A long stationary fault repeatedly supplies passing checkpoints; frozen self/stat/CV conjunction does not establish normality. No threshold, age, trailing window or rescue rule was changed after seeing this.

## 6. Operator/seed robustness (means and actual trajectory counts)

| machine | op | AP | fault_written | fault_promotions | NORMAL_B_FPR | NORMAL_B_written | early_promotions | safe_promotions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| case01 | W1 | N/A | N/A | 0 | 0.0266 | 0.7293 | 3 | 0 |
| case01 | W2_f0995 | N/A | N/A | 0 | 1.0000 | 0.0000 | 0 | 0 |
| case01 | W3_b01 | N/A | N/A | 0 | 0.0039 | 0.9645 | 3 | 0 |
| case02 | W1 | N/A | N/A | 0 | 0.0006 | 0.9911 | 3 | 0 |
| case02 | W2_f0995 | N/A | N/A | 0 | 1.0000 | 0.0000 | 0 | 0 |
| case02 | W3_b01 | N/A | N/A | 0 | 0.0028 | 0.9556 | 3 | 0 |
| case03 | W1 | N/A | N/A | 0 | 0.0976 | 0.1908 | 0 | 0 |
| case03 | W2_f0995 | N/A | N/A | 0 | 0.0355 | 0.4925 | 0 | 0 |
| case03 | W3_b01 | N/A | N/A | 0 | 0.0444 | 0.4842 | 0 | 0 |
| case04 | W1 | 0.9696 | 0.3578 | 3 | N/A | N/A | 0 | 0 |
| case04 | W2_f0995 | 1.0000 | 0.0000 | 0 | N/A | N/A | 0 | 0 |
| case04 | W3_b01 | 0.9637 | 0.3045 | 3 | N/A | N/A | 0 | 0 |
| case05 | W1 | 0.9423 | 0.5979 | 3 | N/A | N/A | 0 | 0 |
| case05 | W2_f0995 | 0.9998 | 0.0000 | 0 | N/A | N/A | 0 | 0 |
| case05 | W3_b01 | 0.9574 | 0.3198 | 3 | N/A | N/A | 0 | 0 |


DEph_cv: **12 false-fault promotions across18 fault trajectories**, all W1/W3 (3seeds ×2fault cases ×2operators); W2 has0 but does not adapt either SP1 shift (post70FPR1, writes0). Benign SP:12early promotions across27trajectories, all SP1/W1,W3;0entirely-safe NORMAL_B promotions. These are trajectory counts, not12 independent fault events or27 independent benign cases. SP2 across all3operators has higher post70FPR/lower admitted NORMAL_B fraction than threshold in the aggregate; no rescue from the third setpoint.

Relative DE_stab, CV removes only one of13 false-fault promotion events and lowers aggregate fault writes.2805→.2633; benign aggregates are identical. Better than always/age/quarantine in some contamination measures does not satisfy safe transfer versus threshold. Always has0“promotion”events but100%fault writes, so promotion count alone is not memory safety. Mean across correlated SP variants/seeds/operators is robustness description, not significance evidence.

## 7. Verification, limits and verdict

11 synthetic/contract tests PASS before run: boundaries incl70, fixed config, train-only scaling/constants, runner input isolation, missing/unpushed seal rejection, score-before-write, future invariance, conjunction/trailing256, distinction between no-promotion and unwritten starvation, fixed five-case manifest. Hash/seal ancestry verified before evaluation; no point-adjust, fitting, training or retuning. Reproduction on remote: `PYTHONPATH=data/step2e/runtime python3 scripts/p10_step2e_transfer.py` (committed code prerequisite), push its seal, then same runtime `python3 scripts/p10_step2e_eval.py`; pinned vus0.0.6/window100. Report script only reads evaluated results. Source/thesis and VUS runtime stay on remote; score traces are tracked, raw observations ignored.

Limits: one operating mode; one benign seed family, two fault seeds/types, fixed magnitudes/ramp10h; no independent benign held-out seed; short normal calibration; constants and scaling inherited; physical-time12.8h checkpoint/trail; partial HDF5 checksum verification only; conservative source-settling window not per-run exact settling annotation. No interpolation/rate ablation, normal-B labels on faults, hidden classifier or RL. These limits narrow the negative result to this pilot, rather than establish universal non-identifiability.

**TRANSFER_NOT_SUPPORTED.** Frozen rule admits stable faults and gives SP1 benefit by violating the conservative timing protocol; SP2 does not rescue the trade-off, and W2 protection accompanies SP1 starvation. There is now source-grounded evidence for both poisoning and new-normal starvation, but this task does **not** authorize learned stopping/RL. Stop after Step2e; await reviewer decision on external evidence, additional preregistered validation or repositioning.
