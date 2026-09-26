# Consolidated reproducibility risk register

| ID | Severity | Finding | Evidence / scope | Effect |
|---|---|---|---|---|
| R1 | BLOCKER | “Other 19 labels unopened” is not true as a global M1 preparation claim. The committed manifest reports all 28 label vectors parsed and publishes label-derived counts/prevalence/runs; the Stage-1A log only supports a narrower claim about its post-seal metric pass. | dataset_manifest.md:3-10, 15-47; stage1a_screen/label_access_log.json:2-39. No independent OS access trace is committed. | Fails issue’s untouched-label acceptance criterion and prevents an unqualified untouched-confirmatory claim. Does not demonstrate model-input leakage. |
| R2 | REPRODUCIBILITY_RISK | Stage-1A records HEAD but does not require or seal a clean worktree/source blob set. | stage1a.py:459-470; stage1a_metrics.py:168-199. No evidence historical execution was dirty. | Artifacts could theoretically be attributed to a commit while modified or untracked code ran. |
| R3 | REPRODUCIBILITY_RISK | Stage-1A custom repo argument conflicts with module-global ROOT paths. | stage1a.py:31-39, 77-80, 184-193, 350-367, 459-470. | Non-default multi-checkout use may read/write one checkout while sealing another. |
| R4 | REPRODUCIBILITY_RISK | Stage1B-R custom repo argument can check/hash one checkout while already-imported code from another executes. | stage1b_r.py:20-39, 520-543; stage1a.py:31-39, 77-97. | Non-default direct API use can misattribute code SHA; no committed Stage1B-R execution evidence is present at audited SHA. |
| R5 | REPRODUCIBILITY_RISK | No shared run lock coordinates duplicate work across independent worktrees. | Stage-1A and Stage1B-R run/resume and create-if-absent paths. | Can duplicate compute; create-if-absent behavior makes silent overwrite less likely, but does not coordinate jobs. |
| R6 | DOCUMENTATION_ONLY | LSTM width is described as nearest in a configured search range, but the range is not frozen/documented. | baseline_spec.md:42-47. | Parameter count and ±10% match remain valid; selection rationale is not independently reproducible. |


## Residual protocol limits (not severity findings)

- The historical parity evidence covers a synthetic p=1 forward with shared weights, not end-to-end training/runtime parity. Evidence: forecasting_implementation_audit.md:54-63. The report scopes its claim to that test; no defect was found in the stated scope.
- Train normality is an explicit benchmark assumption without row-wise labels. Evidence: protocol.md:17. Calibration threshold interpretation is conditional on that disclosed assumption.

## Negative findings

- No direct source-level path was found that feeds test labels to model fitting, prediction inputs, calibration, score construction, or fixed fusion.
- No timestamp padding or future window was found in the audited forecast scoring path.
- No tracked protocol or scientific configuration change was found after the Stage-1A result.
- The futility rule’s recorded continuation outcome is mechanically consistent with its frozen conjunction.
