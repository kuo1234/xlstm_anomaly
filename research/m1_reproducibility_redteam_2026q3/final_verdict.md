# Final verdict

## M1_REPRODUCIBILITY_AUDIT_BLOCKED

The independent static audit of tracked M1 code at AUDITED_M1_SHA found no direct source-level test-label leakage into training, forecast input, score generation, calibration, or fusion. The forecast path follows the frozen past-window-to-current-target order, score timestamps align without padding, q=.99 higher thresholds derive from the train calibration split, and the Stage-1A futility decision matches its frozen rule.

The audit is blocked on the mandatory label-exposure acceptance condition. The committed dataset manifest says test labels for all 28 machines were fetched, parsed, and summarized. The later Stage-1A access log claims only nine evaluator reads and labels the remaining 19 unopened. The log may support the narrow claim that those 19 were not read during that Stage-1A post-seal metric pass, but it cannot establish they were never opened or exposed during project preparation. The historical log is self-reported and no independent OS-level file-access trace is committed.

This verdict does not assert that model weights, score formulas, or the Stage-1A nine-machine selection were driven by labels. The selection code uses train-row counts and result/gate artifacts match the frozen futility rule. It does mean the project cannot pass an acceptance test requiring 19 globally untouched labels or call those machines untouched confirmatory evidence without qualifying the exposure history.

## Acceptance checklist

- AUDITED_M1_SHA: 2eda60d024d2a9149d62de5161ca76916a085942
- Remote ref frozen at audit start: origin/research/adaptive-normality-m1-smd
- Worktree: /home/p76141495/home/xlstm_anomaly-m1-redteam
- Branch: research/m1-reproducibility-redteam-2026q3
- Final red-team branch tip SHA: recorded in the final response after publication.
- Tests run: none; static audit only.
- Tests skipped: CPU tests and all runtime checks; no source changes were made and task scope was a static audit.
- Raw protected SMD label files opened by this audit: 0.
- Raw SMD observation files opened by this audit: 0.
- Model training, GPU calls, Stage-1A recomputation, and Stage1B execution by this audit: 0.
- Findings: 1 BLOCKER, 0 confirmed RESULT_AFFECTING findings, 4 REPRODUCIBILITY_RISK findings, 1 DOCUMENTATION_ONLY finding.
- Active M1 branch/ref: never checked out in the red-team worktree, modified, committed to, or pushed by this audit. Only origin fetch and read-only ref inspection were performed.
- Main branch and unrelated root-worktree changes: left untouched.

## Conditions to clear the blocker

The history cannot be changed retroactively. Correct the public claim to distinguish the all-28 descriptive label inventory from the later nine-machine Stage-1A metric read set. If M1 needs untouched confirmation, approve a new prospective protocol and use genuinely unexposed labels or data. Do not open more labels or alter frozen gates as part of this audit.
