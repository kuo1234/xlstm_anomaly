# Concurrency and resume audit

**Scope:** static inspection only. No concurrent jobs were started and no runtime artifact directory in the active M1 worktree was inspected.

## Verdict

**Generally fail-closed for a single repository/output root; incomplete coordination across independent worktrees.** Immutable writes, mkdir with exist_ok=False, exact artifact hashes, and source checks reduce overwrite and partial-resume risk. They do not provide a shared experiment lock or independently bind Python-loaded code to a caller-supplied repository path.

## Resume and partial-run behavior

Stage-1A checks an existing machine run. If the directory exists without a complete run record, it raises and refuses overwrite; if complete, it validates the record before reuse. New run directories use mkdir with exist_ok=False. Evidence: scripts/adaptive_normality_m1_stage1a.py:184-193, 350-368.

Stage1B-R similarly validates existing run records, source SHA, and artifact hashes before reuse, and refuses to replace an existing run directory. Evidence: scripts/adaptive_normality_m1_stage1b_r.py:301-355. Artifact writers publish with hard links to absent targets. These are useful create-if-absent protections.

Two writers targeting the same machine/output directory may both pass an initial absence check, but only one should create the directory/artifact; the other should fail rather than silently replace it. Partial directories fail closed and may need operator diagnosis. No race stress test was run.

## REPRODUCIBILITY_RISK: no shared lock across worktrees

The runners do not acquire a lock keyed by dataset, protocol, machine, and output root. Independent worktrees can duplicate expensive computation. Separate worktrees have separate filesystem artifacts, so a duplicate job need not overwrite another’s files; concurrent publication or later cherry-pick/push of conflicting seals still requires operator coordination. Create-if-absent hard links are not a cross-worktree execution lock.

At AUDITED_M1_SHA, Stage1B-R has no committed run artifacts or seals. The audit did not inspect active/untracked outputs and makes no claim about live execution state or any actual concurrent Stage1B-R run.

## REPRODUCIBILITY_RISK: custom repository path mismatch in Stage-1A

run_stage1a(repo=...) computes root from the argument and records that root’s HEAD, but then calls run_stage1a_machine(), whose run loading and output paths use module-global ROOT. selected_machines() also reads its selection JSON from global ROOT. Evidence: scripts/adaptive_normality_m1_stage1a.py:31-39, 77-80, 184-193, 350-367, 459-470.

With the normal default repo, global ROOT and root are the same checkout. With a non-default repo argument, validation/sealing can operate on one checkout while machine runs read/write another. This API mismatch should be fixed or explicitly unsupported.

## REPRODUCIBILITY_RISK: custom repository path mismatch in Stage1B-R

run_stage1b_r(repo=B) checks source files and records B’s HEAD, but implementation and imported modules are loaded from the checkout that imported the module. It also calls stage1a.selected_machines(), which reads the imported Stage-1A module’s global ROOT. Evidence: scripts/adaptive_normality_m1_stage1b_r.py:20-39, 520-543 and scripts/adaptive_normality_m1_stage1a.py:31-39, 77-97.

A cross-checkout repo argument can therefore make source SHA/artifacts refer to B while code objects from A execute. This is a non-default direct-API scenario, not evidence of historical misuse. No committed Stage1B-R execution evidence is present at AUDITED_M1_SHA; live/untracked execution state was not assessed.

## Protected refs and active execution

The audit used a separate worktree based exactly at AUDITED_M1_SHA. It did not check out or mutate the protected M1 branch ref and did not inspect live untracked Stage1B-R outputs. Final branch/ref verification is recorded in the audit response.
