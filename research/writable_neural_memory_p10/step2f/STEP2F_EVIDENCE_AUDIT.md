# Step2f evidence audit — pending review

**A_PASS_RESIDUAL_SUFFICIENT / RESIDUAL_EVIDENCE_SUFFICIENT. NEURAL_ARM_NOT_RUN.** Limited structural sufficiency on existing five cases, not validated admission, confirmatory transfer or generalizable classifier. Combined probes fail the reverse fold.

[Authorized task](https://github.com/kuo1234/xlstm_anomaly/issues/15#issuecomment-5978542488). All acquisition/raw/computation on ssh kuo, no local download or new acquisition. Official Extended TEP DTU v1 DOI10.11583/DTU.13385936.v1 and source-author thesis A.3.2; literal source paths, hashes and range provenance remain Step2e manifest/evaluator metadata. Full HDF5 hash unavailable; do not imply whole-file acquisition. Labels previously exposed: exploratory diagnostic only.

Case01 SP1+5%,02 SP1−5%,03 SP2+5%,04 IDV1,05 IDV2. Three SPs share native seed3010001 and identical normal prefix; faults21812/20819. Five physical files, three native seed families, ONE benign family, not independent benign replications.

## Freeze / exposure chronology

Protocol a9424f996213d11fb0884805c5ad343dafecdb09; residual seal0ae7f1de284a12b8d632aaf080e01a20b2eb5365 pushed before evaluator and remote ancestry verified. Seal SHA256 bd9e655814b15a423eef17778925167c26535bbe252dccea3898abd2742a0190. Extraction UTC2026-10-04T09:46:18.064676+00:00 labels_read=0 for THIS extraction (historically exposed=true); first evaluator2026-10-04T09:47:02.136511+00:00. Per-case access logs/evaluator commit tracked. No sealed code/config/features/folds changed after states. Recognizing a member of the preregistered battery after outcomes is exploratory, not independent feature confirmation or new policy selection.

135traces=5cases×3seeds×3operators×3views. Fixed ReLU φ53×8→128, seeds11/22/33, W1k5/W2f=.995/W3β=.1; frozen M0, score before any write, no test updates. FIT-only scaling/manifold; CAL threshold only. Root split/config are exact copies of sealed run files. FIT manifold shrinkage.1/ridge1e-6, residual scales floor.02; in-bank FIT residual queries make normal prototype optimistic. Normal-only PCA top5 explained variance in results/fit_pca_summary.csv for45primary cells, no test fitting. [Preprocessing audit](PREPROCESSING_AUDIT.md).

## Physical-case evidence

Source NORMAL_A<30h, SP TRANSITION[30,70), NORMAL_B>=70; fault>=30 remains FAULT even when stationary. Runner extracts all trailing256 windows every128; evaluator matches wholly FAULT/NORMAL_B common ends1280/1408/1536 (83.95/90.35/96.75h). Three correlated windows per run, not independent N. Mixed/TRANSITION retained, not relabelled healthy. No transient-vs-settled mismatch.

Primary W1/seed11 medians:

| view | seed | op | case | state | log_score | cv | maha_mean | maha_centroid | cov_distance | corr_distance | manip_energy | near_constant_energy | top5_energy | direction_cosine |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fit_only_clip | 11 | W1 | case01 | NORMAL_B | 4.271602 | 0.010413 | 140.403772 | 140.061587 | 1.213275 | 0.151205 | 0.464875 | 0.159080 | 0.396316 | -0.130636 |
| fit_only_clip | 11 | W1 | case02 | NORMAL_B | 4.266036 | 0.010074 | 139.030565 | 138.705902 | 0.971663 | 0.136699 | 0.467161 | 0.167133 | 0.396414 | 0.115253 |
| fit_only_clip | 11 | W1 | case03 | NORMAL_B | 2.056817 | 0.115523 | 11.215486 | 4.096179 | 1.218325 | 0.105843 | 0.166135 | 0.055187 | 0.250223 | -0.108930 |
| fit_only_clip | 11 | W1 | case04 | FAULT | 3.674726 | 0.013104 | 214.060514 | 213.790472 | 1.452048 | 0.107845 | 0.518791 | 0.259026 | 0.950230 | 0.403928 |
| fit_only_clip | 11 | W1 | case05 | FAULT | 3.832565 | 0.015741 | 104.910133 | 104.424618 | 1.305930 | 0.110968 | 0.297378 | 0.061994 | 0.653014 | -0.008528 |

Scalar score/CV reverses across SP interventions. Normal-manifold distances/correlation/direction/manipulated energy also reverse. Healthy distance is not legitimacy evidence. But preregistered top5-energy concentration is fault-high for BOTH faults vs EVERY SP at EVERY matched age in EVERY frozen seed/operator/view, including no-clip. No-clip medians SP1+ .843406,SP1− .843530,SP2 .250223,IDV1 .994478,IDV2 .893459. Clipping strongly changes margins; no universal threshold claim. No single-feature rescue classifier, threshold fitting or policy rerun. This structure is lost in scalar magnitude/CV and present in both heldout case sets.

All feature directions (fault-greater fraction min/max/mean, robustness cells not N):

| view | feature | min | max | mean |
| --- | --- | --- | --- | --- |
| fit_only_clip | corr_distance | 0.000000 | 1.000000 | 0.339506 |
| fit_only_clip | cov_distance | 0.000000 | 1.000000 | 0.530864 |
| fit_only_clip | cv | 0.000000 | 1.000000 | 0.666667 |
| fit_only_clip | direction_cosine | 0.000000 | 1.000000 | 0.339506 |
| fit_only_clip | log_score | 0.000000 | 1.000000 | 0.333333 |
| fit_only_clip | maha_centroid | 0.000000 | 1.000000 | 0.666667 |
| fit_only_clip | maha_mean | 0.000000 | 1.000000 | 0.666667 |
| fit_only_clip | manip_energy | 0.000000 | 1.000000 | 0.666667 |
| fit_only_clip | near_constant_energy | 0.000000 | 1.000000 | 0.654321 |
| fit_only_clip | top5_energy | 1.000000 | 1.000000 | 1.000000 |
| fit_only_no_clip | corr_distance | 0.000000 | 1.000000 | 0.567901 |
| fit_only_no_clip | cov_distance | 0.000000 | 1.000000 | 0.481481 |
| fit_only_no_clip | cv | 0.000000 | 1.000000 | 0.660494 |
| fit_only_no_clip | direction_cosine | 0.000000 | 1.000000 | 0.296296 |
| fit_only_no_clip | log_score | 0.000000 | 1.000000 | 0.333333 |
| fit_only_no_clip | maha_centroid | 0.000000 | 1.000000 | 0.333333 |
| fit_only_no_clip | maha_mean | 0.000000 | 1.000000 | 0.333333 |
| fit_only_no_clip | manip_energy | 0.000000 | 1.000000 | 0.500000 |
| fit_only_no_clip | near_constant_energy | 0.000000 | 0.000000 | 0.000000 |
| fit_only_no_clip | top5_energy | 1.000000 | 1.000000 | 1.000000 |
| step2e_regression_clip | corr_distance | 0.000000 | 1.000000 | 0.339506 |
| step2e_regression_clip | cov_distance | 0.000000 | 1.000000 | 0.530864 |
| step2e_regression_clip | cv | 0.000000 | 1.000000 | 0.666667 |
| step2e_regression_clip | direction_cosine | 0.000000 | 1.000000 | 0.351852 |
| step2e_regression_clip | log_score | 0.000000 | 1.000000 | 0.333333 |
| step2e_regression_clip | maha_centroid | 0.000000 | 1.000000 | 0.666667 |
| step2e_regression_clip | maha_mean | 0.000000 | 1.000000 | 0.666667 |
| step2e_regression_clip | manip_energy | 0.000000 | 1.000000 | 0.666667 |
| step2e_regression_clip | near_constant_energy | 0.000000 | 1.000000 | 0.598765 |
| step2e_regression_clip | top5_energy | 1.000000 | 1.000000 | 1.000000 |

## Diagnostic supervised upper bound

Fixed logistic C1/seed731; probe-train-only StandardScaler and equal physical-run weights. Representation/detector normal-only. Fold0 trains SP2/IDV2, tests SP1±/IDV1; fold1 reverses. No shared physical run/intervention family; benign native seed shared. No classifier deployed to admission.

Primary results: case-averaged AUROC/AP separately from window scores:

| fold | arm | case_AUROC | case_AP | AUROC | AP | train_cases | test_cases |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | A0 | 0.000000 | 0.333333 | 0.000000 | 0.242063 | case03,case05 | case01,case02,case04 |
| 0 | A1 | 1.000000 | 1.000000 | 0.944444 | 0.916667 | case03,case05 | case01,case02,case04 |
| 0 | A2 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | case03,case05 | case01,case02,case04 |
| 1 | A0 | 0.000000 | 0.500000 | 0.000000 | 0.383333 | case01,case02,case04 | case03,case05 |
| 1 | A1 | 0.000000 | 0.500000 | 0.000000 | 0.383333 | case01,case02,case04 | case03,case05 |
| 1 | A2 | 0.000000 | 0.500000 | 0.000000 | 0.383333 | case01,case02,case04 | case03,case05 |

All case-AUROC robustness:

| view | fold | arm | min | max | mean |
| --- | --- | --- | --- | --- | --- |
| fit_only_clip | 0 | A0 | 0.000000 | 0.000000 | 0.000000 |
| fit_only_clip | 0 | A1 | 0.500000 | 1.000000 | 0.555556 |
| fit_only_clip | 0 | A2 | 1.000000 | 1.000000 | 1.000000 |
| fit_only_clip | 1 | A0 | 0.000000 | 0.000000 | 0.000000 |
| fit_only_clip | 1 | A1 | 0.000000 | 0.000000 | 0.000000 |
| fit_only_clip | 1 | A2 | 0.000000 | 0.000000 | 0.000000 |
| fit_only_no_clip | 0 | A0 | 0.000000 | 0.000000 | 0.000000 |
| fit_only_no_clip | 0 | A1 | 0.500000 | 1.000000 | 0.555556 |
| fit_only_no_clip | 0 | A2 | 1.000000 | 1.000000 | 1.000000 |
| fit_only_no_clip | 1 | A0 | 0.000000 | 0.000000 | 0.000000 |
| fit_only_no_clip | 1 | A1 | 0.000000 | 0.000000 | 0.000000 |
| fit_only_no_clip | 1 | A2 | 0.000000 | 0.000000 | 0.000000 |
| step2e_regression_clip | 0 | A0 | 0.000000 | 0.000000 | 0.000000 |
| step2e_regression_clip | 0 | A1 | 0.500000 | 0.500000 | 0.500000 |
| step2e_regression_clip | 0 | A2 | 0.000000 | 1.000000 | 0.777778 |
| step2e_regression_clip | 1 | A0 | 0.000000 | 0.000000 | 0.000000 |
| step2e_regression_clip | 1 | A1 | 0.000000 | 0.000000 | 0.000000 |
| step2e_regression_clip | 1 | A2 | 0.000000 | 0.000000 | 0.000000 |

A2 fold0 succeeds across primary seeds/operators, fold1 ALL arms AUROC0; A1 fold0 varies. **Combined A2 probe fails generalization.** Concentration ordering coexists with failed multivariate extrapolation from tiny train folds. No replacement classifier after results; no LSTM/xLSTM performance inference.

## Gate and limitations

The question first asks whether scalar compression discards observable separable structure. Consistent ordering in a preregistered residual summary across both heldout case sets and all frozen comparisons demonstrates incremental structure on this pilot. Thus A_PASS_RESIDUAL_SUFFICIENT is limited to structural evidence sufficiency, not all probes working or safe residual-only admission. Negative prototype/probe results remain material. We assess them alongside concentration without selecting a new feature, threshold, seed or operator. A_NO_OBSERVABLE_SIGNAL contradicts preserved structure; one failed probe does not establish a need for learned temporal rescue when raw residual information remains clear. No credible NEED for learned temporal representation demonstrated.

NEURAL_ARM_NOT_RUN: conditional B gate not reached, no healthy neural-run acquisition/training/optimizer, no LSTM/xLSTM result. Reviewer may authorize prospective frozen evidence/rule testing and independent benign seeds; none implemented here. Stable!=healthy remains valid; concentration is NOT a validated PROMOTE test. Unresolved safety evidence remains quarantined.

Limits: two fault runs/one benign native seed; historical exposure; only three late matched ages; small FIT319/320 with optimistic in-bank manifold; concentration identified within prespecified battery is not independent validation; margins clip-sensitive. Other faults/healthy modes/seeds may reverse it. No chosen threshold, controller safety/FPR/adaptation test, p-value or checkpoint-independent-N. No RL/fullLEFT/Step3.

## Verification

13 targeted tests PASS: runner label/timestamp isolation; FIT-only scaler/CAL invariance; neural training absent; FIT-only memory; future causality; score-before-write/frozen M0; exact clipping/constants; residual norm recovery; regression scaler; frozen config/seeds/windows; missing seal blocked; physical/intervention fold separation; executable third-clean-block close. Neural tests certify no A loader/optimizer, NOT an unimplemented B loader.

45 Step2e A_no_update control traces maximum absolute score error 0.0. Raw ignored remote; evidence/hashes tracked. Test command: python3 -m unittest discover -s tests -p test_p10_step2f.py -v. Do not overwrite historical seal when reproducing; evaluator checks raw/code/evidence hashes and pushed ancestry before states.
