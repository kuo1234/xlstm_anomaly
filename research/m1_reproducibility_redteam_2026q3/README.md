# M1 reproducibility red-team audit

## Audit identity

- Audited M1 commit (AUDITED_M1_SHA): 2eda60d024d2a9149d62de5161ca76916a085942
- Remote ref at fetch: origin/research/adaptive-normality-m1-smd
- Worktree: /home/p76141495/home/xlstm_anomaly-m1-redteam
- Branch: research/m1-reproducibility-redteam-2026q3
- Audit type: static inspection of tracked source, protocol, and committed artifacts
- Verdict: M1_REPRODUCIBILITY_AUDIT_BLOCKED
- Final red-team branch tip is reported after publication in the final response; the report does not claim a self-referential commit identifier.

This review followed issue #4 and its isolation rules. The M1 worktree and ref were inspected before and after the audit. Work was done only in the dedicated red-team worktree. No M1 or main ref was checked out, reset, rebased, merged, committed to, or pushed.

## Executive summary

The default Stage-1A source path implements train-only fitting, causal one-step forecasting, timestamp alignment, label-free calibration, and immutable score/artifact checks. Static inspection found no direct path by which test labels enter model fitting, forecast inputs, score construction, calibration thresholds, or fixed score fusion.

The mandatory label-exposure acceptance condition is not met. The committed dataset manifest says all 28 label vectors were fetched and parsed, and reports positive-point counts, prevalences, and label-run inventories for all 28 machines. A later Stage-1A access log says only nine machines were opened for that metric pass and labels the other 19 “unopened.” Those claims are consistent only if “unopened” is narrowly limited to the later Stage-1A evaluator. The log cannot support a claim that the other 19 labels were never opened or never visible to the research process. No independent OS-level access log is committed.

The Stage-1A selection code and recorded futility decision follow their frozen rules. Selection uses train-row counts; both futility routes correctly continue under the amendment. No committed protocol, architecture, threshold, seed, or subset change was found after the nine-machine result. The later standalone-gate feasibility note is an arithmetic consequence of the frozen full-cohort gate and does not edit it.

### Findings by severity

- BLOCKER: global “other 19 labels unopened” / untouched-confirmatory exposure claim is contradicted by the all-28 label inventory and cannot be independently audited.
- RESULT_AFFECTING: no confirmed source-level result-affecting leakage or post-result scientific-setting change found.
- REPRODUCIBILITY_RISK: Stage-1A does not bind its recorded HEAD to a clean execution tree; non-default cross-repository APIs can mix module-root code/artifacts with the supplied repository; independent worktrees have no shared run lock.
- DOCUMENTATION_ONLY: the LSTM width-search rationale is not reproducible from a declared range.

Parity scope and the train-normality convention are disclosed protocol limits, not separately counted findings.

The BLOCKER is about the requested exposure/provenance acceptance condition and confirmatory status, not a finding that labels were fed into the model.

## Audit boundaries and execution record

- Raw SMD test-label files opened by this audit: 0.
- Raw SMD train/test observation files opened by this audit: 0.
- Model training, detector scoring, GPU calls, Stage-1A recomputation by this audit: 0.
- Tests run: none. Tests were skipped because the task was a static audit and no implementation change was made.
- Live, untracked Stage1B runtime artifacts in the active M1 worktree inspected: 0.
- Read: tracked source, research protocol/specifications, committed reports, JSON summaries, and commit metadata at AUDITED_M1_SHA.

Result tables and access logs cited below are committed derived artifacts, not raw label files. The audit does not present the self-reported access log as an independently verified system trace.

## Findings index

- [Data leakage and label exposure](data_leakage_audit.md)
- [Forecast causality and score alignment](causality_audit.md)
- [Calibration and model integrity](calibration_audit.md)
- [Artifact provenance and seals](artifact_integrity_audit.md)
- [Stage-1A selection and futility protocol](stage1a_protocol_audit.md)
- [Concurrency and resume behavior](concurrency_resume_audit.md)
- [Consolidated risk register](reproducibility_risks.md)
- [Proposed remediation](proposed_fixes.md)
- [Final verdict](final_verdict.md)
