# Phase G1 Stage-B adversarial self-review (exact committed implementation)

Verdict: PASS_FOR_LABEL_ACCESS

Reviewed/implemented commit: fe507084b9a1aba0c67a4536c5bb938ea89a4945.
This review was performed against the committed tree, not an uncommitted
worktree. No real Phase-G labels, AP/AUROC values, probe outcomes, or test
source results were read.

## Protocol-to-code audit

| Requirement | Executable path | Evidence | Status |
|---|---|---|---|
| Source-disjoint folds and four shifted scenarios | scripts/phase_g1_core.py assertions; phase_g1_run.py run | Stage-A and adversarial suite pass | PASS |
| Observation-only extraction and label boundary | phase_g1_run.py observation helpers; phase_g1_pipeline.py join_evaluator_labels | API signature and label-isolation tests pass | PASS |
| Common W64/right-edge rows and warmup exclusion | phase_g1_run.py primary_binary_mask/select_primary_rows | Exact row-key intersection and causal fixtures pass | PASS |
| Shared native CANDI W10 history, t>=63 | phase_g1_pipeline.py extract_candi_history; G0.1 manifest checks | CANDI alignment/shared-control tests pass | PASS |
| Frozen feature dimensions and eligible cells/layers | phase_g1_core.py build_feature_groups; sealed E2/F4 observers | dimensions, reset, finite and schema checks pass | PASS |
| xLSTM four eligible sLSTM cells; LSTM all six-layer equal pooling | sealed E2/F4 extraction paths | no alternate confirmatory feature path | PASS |
| Pooled train fitting, train-only scaling, pooled validation C | phase_g1_core.py fit_probe_pooled | C-grid/tie/fold guards and cache fixture pass | PASS |
| Test-only evaluation and fixed AP cohort | phase_g1_run.py difference/source AP helpers | paired cohort hashes and source AP shape guards pass | PASS |
| Four-member Holm family and frozen directions | phase_g1_pipeline.py build_confirmatory_statistics; core holm_adjust | fifth-member/reversed-subtraction fixtures pass | PASS |
| Duration/severity robustness, no refit/rescale, fixed bins | phase_g1_run.py duration selection/report helpers | G1.1 fixed-bin/no-merge/refit fixtures pass | PASS |
| Semantic non-identifiability is separate negative control | phase_g1_run.py secondary streaming pass | semantic-support rejection and invariance fixtures pass | PASS |
| Hierarchical bootstrap/sign-flip and conditional H3a | statistics builder and final decision block | exact family and decision guards pass | PASS |
| Resource-bounded primary/secondary execution | primary chunk cache, seed-local fit loop, secondary streaming pass | bounded primary and secondary fixtures pass; no cross-seed feature matrices retained | PASS |
| No native predict_step, optimizer, or parameter mutation | core extractor and launcher guards | entrypoint, mutation and no-predict-step tests pass | PASS |

## Adversarial negative tests

The committed suite reports 36/36 PASS (reports/phase_g1/adversarial_tests.json).
It rejects permuted/removed row cohorts, fold/scaler leakage, shifted CANDI
timestamps, distinct shared controls, reversed contrasts, a fifth Holm member,
per-scenario C selection, extractor metadata/label arguments, source reordering,
unresolved or merged duration bins, stratum refitting/rescaling, semantic
control misuse, and missing G1.1 exclusions. The bounded primary-cache and
secondary-streaming fixtures additionally pass without executing a metric
branch or reading real labels.

## Defects and fixes

The prior review found full-grid memory retention. The exact committed
implementation fixes this by persisting each primary stream/arm chunk,
pooling and fitting one detector seed at a time, writing its artifacts, then
releasing the feature workspace. Secondary native-prevalence, specificity,
semantic and robustness views are regenerated stream-by-stream; robustness
chunks are materialized one seed/arm/stratum at a time. No additional defect
remains in this review.

## Resource and label-blind evidence

- scripts/phase_g1_stage_a.py: PASS; bounded primary cache fixture
  (max_feature_bytes=896, 24 chunks) and secondary fixture (6 chunks,
  4 materialized artifacts).
- scripts/phase_g1_adversarial.py: PASS, 36/36.
- Real Phase-G labels read: false.
- AP/AUROC/probe outcomes observed: false.
- Scientific optimizer/checkpoint mutation: false.

Scientific file hashes sealed by this review are recorded in the JSON report.
No post-review scientific code or configuration change is permitted. A
report-only enclosing commit will serve as G1_REVIEW_COMMIT; its SHA is
derived by the launcher and is intentionally not embedded here.
