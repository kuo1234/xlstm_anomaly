# Data leakage and label-exposure audit

**Scope:** static review at AUDITED_M1_SHA. No raw SMD labels or observation arrays were opened during this audit.

## Verdict

**BLOCKER — exposure-boundary claim.** The repository cannot support the broad claim that the other 19 machines’ test labels remained unopened or unavailable to the project. This is a provenance and confirmatory-status blocker, not evidence that the M1 model consumed labels.

**No direct source-level model leakage confirmed.** The default training, preprocessing, forecasting, calibration, and score-fusion paths accept observations and calibration values, not labels. The metric evaluator is the intended label-consuming path.

## Label-exposure evidence

The committed data manifest says the preprocessing rule and W=256 were frozen before label values were parsed; all 84 train, test, and test-label files were fetched; every label vector was parsed and checked as binary and length-aligned; positive-point counts, prevalence, and contiguous label-run counts are listed for every machine.

Evidence: research/adaptive_normality_m1_smd/dataset_manifest.md:3-10, 15-47, 53 onward. Stated totals include 29,444 positive test points and 327 contiguous label runs across all 28 machines.

The later Stage-1A access log reports nine metric reads and sets other_19_unopened=true. Evidence: reports/adaptive_normality_m1_smd/stage1a_screen/label_access_log.json:2-39. Its other fields qualify the claim: labels_read_before_prelabel_sha is 0, and the recorded pre-label SHA is bcdd348e1d6609f4af357506d1c6b328eaac638a. This supports the narrower claim that the Stage-1A metric pass read the selected nine after the pre-label seal and claims it did not read the other 19 during that pass.

The Stage-1A result report contains metric rows for the selected nine only. That does not erase the earlier all-machine descriptive inventory. No committed process-level or OS audit record independently proves all file opens, so the access log is self-reported and cannot establish a complete access history.

### Interpretation

“Other 19 unopened” is false if it means never opened or parsed during M1 preparation. It is consistent with the committed history only if qualified as “not loaded by the Stage-1A metric evaluator after the Stage-1A score seal.” Issue #4’s broader acceptance condition is therefore not met.

The all-28 statistics were committed with the initial M1 protocol before the Stage-1A screen amendment. They disclose label-derived information, although the Stage-1A selection rule itself does not use it. This prior exposure must be disclosed when describing the nine as prospective and when making claims about untouched confirmation.

## Source-level leakage checks

### Split and preprocessing

The split helper makes fit, validation, and calibration blocks from train rows only: 70%, 15%, and 15%. The robust transform fits the first 70% prefix. Evidence: scripts/adaptive_normality_m1_data.py:233-238, 255-275. The protocol specifies the same partition and states train normality is a benchmark assumption because no train-label file exists: research/adaptive_normality_m1_smd/protocol.md:17-35.

No raw test labels are needed by these operations. Train normality is assumed, not independently verifiable row by row; report this as an assumption rather than proof that every fit/calibration point is normal.

### Model fitting and input paths

The Stage-1A selected-machine runner loads train and test observations, creates the train-only transform, and fits the frozen arms. It does not call the metric label loader during training or score creation. Evidence: scripts/adaptive_normality_m1_stage1a.py:350-378. The observation allow-list has only train/test observation splits: scripts/adaptive_normality_m1_data.py:95-138.

The metric entry point validates sealed score, threshold, execution, checkpoint, scaler, and calibration artifacts before loading labels. Stage-1A validation checks the recorded no-label/no-metric flags, score inventories, and timestamps: scripts/adaptive_normality_m1_stage1a_metrics.py:153-205. These are code-level barriers, not a historical OS audit.

### Selection and result-driven changes

The nine-machine selection is computed from train_rows and machine-name ranks by group. The amendment excludes label prevalence, anomaly properties, and detector behavior; the selection JSON records its train-only basis. Evidence: research/adaptive_normality_m1_smd/stage1a_futility_amendment.md:7-11 and research/adaptive_normality_m1_smd/stage1a_machines.json:1-4.

The commit diff from the pre-label seal to the Stage-1A result adds only result/access artifacts. The subsequent commit to AUDITED_M1_SHA adds the Stage1B-R feasibility note and runner/feasibility code/tests; it does not edit the frozen protocol, baseline specification, Stage-1A settings, or futility amendment. This supports “no committed scientific setting changed after the nine-machine result,” but cannot prove process intent or absence of uncommitted historical code.

## Required wording

Describe the nine as the **Stage-1A evaluator subset** and say the other 19 were **not opened by that post-seal metric pass according to its self-reported log**. Do not call the other 19 globally unopened or claim a fully label-blind M1 preparation history.
