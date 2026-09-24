# Branch consolidation and cleanup review

Execution date: 2026-09-25 00:27 Asia/Taipei (worktree and branch census timestamp)

## Scope and safety

The original working directory was `/home/p76141495/home/xlstm_anomaly`. It was on local `main` at `caa9b3ceb299ab3d05036f5c9c5dbd8104e46f61`, 56 commits behind `origin/main`, and dirty before consolidation began. Its pre-existing changes were left untouched.

The original directory's dirty paths were modified `AGENTS.md`, `reports/mlstm_mechanism_audit/architecture_audit.md`, `reports/mlstm_mechanism_audit/feature_schema.md`, and `reports/mlstm_mechanism_audit/mlstm_state_semantics.md`; untracked `.agents/`, `.codex/`, `.worktrees/`, `reports/phase_g/g1_execution_ledger.jsonl`, `reports/phase_g/g1_primary_cache/`, `reports/phase_g/g1_stderr.log`, `reports/phase_g/g1_stdout.log`, `reports/phase_g/hourly_monitor.log`, `reports/phase_g/hourly_monitor.sh`, `reports/phase_g/hourly_monitor_recovered.log`, `reports/phase_g1/failed_attempts/`, and `reports/phase_g1_recovered_execution_v1/`.

The dedicated worktree is `/home/p76141495/home/xlstm_anomaly-consolidation`, on `consolidation/r0-adaptive-research-2026-09`. It was created from refreshed `origin/main` at `b7ae44fafc4e9ea6671647c5cb73156ddaf26e5e` and was clean before consolidation.

The concurrently running M1 worktree and its branch were not modified, checked out, rebased, merged, reset, deleted, cleaned, or pruned. No other worktree was modified or removed. `git worktree prune` was never run.

At the audit snapshot, local M1 ref `research/adaptive-normality-m1-smd` and the completed remote adaptive-normality audit both pointed to `a04bccfe5ecb94e50de99c061011cb26acca755d`. The requested adaptive audit merge therefore brings that already-shared commit into `main`; no M1-only commit was merged, and the M1 branch ref and worktree were left at their original state.

## Worktree inventory

All worktrees other than the dedicated consolidation worktree were treated as active/protected. Dirty status was read with `git status --short --untracked-files=normal`; all were clean except the original working directory.

| Worktree path | Checked-out branch | HEAD at census | State |
|---|---|---|---|
| `/home/p76141495/home/xlstm_anomaly` | `main` | `caa9b3ceb299ab3d05036f5c9c5dbd8104e46f61` | dirty; preserved |
| `/home/p76141495/.codex/worktrees/196a/xlstm_anomaly` | detached | `caa9b3ceb299ab3d05036f5c9c5dbd8104e46f61` | clean; protected |
| `/home/p76141495/.codex/worktrees/d35a/xlstm_anomaly` | detached | `caa9b3ceb299ab3d05036f5c9c5dbd8104e46f61` | clean; protected |
| `/home/p76141495/home/xlstm_anomaly-consolidation` | `consolidation/r0-adaptive-research-2026-09` | `8ac32bbd73dcbb2fb64ead3654bd68c5d4c40321` | clean; this task |
| `/home/p76141495/home/xlstm_anomaly/.worktrees/adaptive-normality-m1-smd` | `research/adaptive-normality-m1-smd` | `a04bccfe5ecb94e50de99c061011cb26acca755d` | clean; active M1, protected |
| `/home/p76141495/home/xlstm_anomaly/.worktrees/aplus-solver-convergence-audit` | `experiment/aplus-solver-convergence-audit` | `ccb9a3d7e8fc1ced5707b5691de6b09a90f3736f` | clean; protected |
| `/home/p76141495/home/xlstm_anomaly/.worktrees/consolidate-research-2026-09` | detached | `da358afdc918cb108271573dc4313790a7e054b7` | clean; protected |
| `/home/p76141495/home/xlstm_anomaly/.worktrees/cuda-spark` | detached | `dd5ad9d1d1580be2e39313bc6cb7befa0f9cdf61` | clean; protected |
| `/home/p76141495/home/xlstm_anomaly/.worktrees/input-derived-observable-control` | `experiment/input-derived-observable-control` | `af6cc474cabe03640dfad6402f06329309d85942` | clean; protected |
| `/home/p76141495/home/xlstm_anomaly/.worktrees/integration-canary` | detached | `03d2975cf252b52103b78878e4bc1854ff00aaa4` | clean; protected |
| `/home/p76141495/home/xlstm_anomaly/.worktrees/lstm-standalone-diagnostic` | detached | `caa9b3ceb299ab3d05036f5c9c5dbd8104e46f61` | clean; protected |
| `/home/p76141495/home/xlstm_anomaly/.worktrees/mlstm-dense-attribution` | detached | `bece2656774fa85e07a18778b1d28b5645993c2a` | clean; protected |
| `/home/p76141495/home/xlstm_anomaly/.worktrees/mlstm-mechanism-audit` | detached | `b9a1a80e09aa4fe061878d4d66d67bc6ba22f490` | clean; protected |
| `/home/p76141495/home/xlstm_anomaly/.worktrees/nonlinear-observable-control` | `experiment/nonlinear-observable-control` | `0b00d6f97635f991c8f12c2e34be9b1073d7f33d` | clean; protected |
| `/home/p76141495/home/xlstm_anomaly/.worktrees/observer-optimization` | detached | `4c04b6a602838b0348eee644e5bbcbaff40997b6` | clean; protected |
| `/home/p76141495/home/xlstm_anomaly/.worktrees/real-data-r0-execution` | `experiment/real-data-r0-execution` | `ffae1da6e37b48076e2610390c249318acfbea2e` | clean; protected |
| `/home/p76141495/home/xlstm_anomaly/.worktrees/real-data-r0-protocol` | `research/real-data-r0-protocol` | `d7708586fe3264fcd6e5567504cccd97104c2a2e` | clean; protected |
| `/home/p76141495/home/xlstm_anomaly/.worktrees/strong-observable-control` | `experiment/strong-observable-control` | `f9014a2c78bf925b69d55d47c54c489e5999e74d` | clean; protected |
| `/home/p76141495/home/xlstm_anomaly/.worktrees/temporally-matched-observable-control` | `experiment/temporally-matched-observable-control` | `04e0abbd7a9a6a8c8d00052cd1b20c51e0a71d28` | clean; protected |
| `/home/p76141495/xlstm-an-research` | `research/adaptive-normality-xlstm` | `a04bccfe5ecb94e50de99c061011cb26acca755d` | clean; protected |

## Branch census and ancestry classification

At the refreshed pre-merge audit, the local branches and upstream state were:

| Local branch | Tip | Upstream/state | Disposition |
|---|---|---|---|
| `consolidation/r0-adaptive-research-2026-09` | `8ac32bbd73dcbb2fb64ead3654bd68c5d4c40321` | `origin/main`, ahead after merges | retain; this task |
| `experiment/aplus-solver-convergence-audit` | `ccb9a3d7e8fc1ced5707b5691de6b09a90f3736f` | upstream gone | `ACTIVE_KEEP`; checked out |
| `experiment/input-derived-observable-control` | `af6cc474cabe03640dfad6402f06329309d85942` | `origin/experiment/input-derived-observable-control`, behind 5 | `ACTIVE_KEEP`; checked out |
| `experiment/nonlinear-observable-control` | `0b00d6f97635f991c8f12c2e34be9b1073d7f33d` | upstream gone | `ACTIVE_KEEP`; checked out |
| `experiment/real-data-r0-execution` | `ffae1da6e37b48076e2610390c249318acfbea2e` | matching origin branch | `ACTIVE_KEEP`; checked out |
| `experiment/strong-observable-control` | `f9014a2c78bf925b69d55d47c54c489e5999e74d` | upstream gone | `ACTIVE_KEEP`; checked out |
| `experiment/temporally-matched-observable-control` | `04e0abbd7a9a6a8c8d00052cd1b20c51e0a71d28` | upstream gone | `ACTIVE_KEEP`; checked out |
| `main` | `caa9b3ceb299ab3d05036f5c9c5dbd8104e46f61` | `origin/main`, behind 56; original tree dirty | `ACTIVE_KEEP`; checked out |
| `research/adaptive-normality-m1-smd` | `a04bccfe5ecb94e50de99c061011cb26acca755d` | local-only | `ACTIVE_KEEP`; current M1, checked out |
| `research/adaptive-normality-xlstm` | `a04bccfe5ecb94e50de99c061011cb26acca755d` | matching origin branch | `ACTIVE_KEEP`; checked out |
| `research/real-data-r0-protocol` | `d7708586fe3264fcd6e5567504cccd97104c2a2e` | no upstream configured | `ACTIVE_KEEP`; checked out |

The refreshed remote branch set was `main`, `experiment/input-derived-observable-control`, `experiment/real-data-r0-execution`, `research/adaptive-normality-xlstm`, `research/framing-2026-09`, `research/real-data-feasibility-audit`, and `research/real-data-r0-protocol`. The active M1 branch was local-only at this census. Branches absent from GitHub but still checked out locally remain protected.

| Remote branch | Refreshed tip | Classification at audit | Cleanup disposition |
|---|---|---|---|
| `main` | `b7ae44fafc4e9ea6671647c5cb73156ddaf26e5e` | starting point | consolidate into this history |
| `experiment/input-derived-observable-control` | `1f4296f62fe3f0a514171a94afe3ce8bc1686986` | `ALREADY_IN_MAIN` | preserve as `ACTIVE_KEEP`; checked out in another worktree |
| `research/real-data-r0-protocol` | `d7708586fe3264fcd6e5567504cccd97104c2a2e` | `NEEDS_CONSOLIDATION` | included through adaptive branch; preserve as `ACTIVE_KEEP`, checked out |
| `experiment/real-data-r0-execution` | `ffae1da6e37b48076e2610390c249318acfbea2e` | `NEEDS_CONSOLIDATION` | included through adaptive branch; preserve as `ACTIVE_KEEP`, checked out |
| `research/adaptive-normality-xlstm` | `a04bccfe5ecb94e50de99c061011cb26acca755d` | `NEEDS_CONSOLIDATION` | merged; preserve as `ACTIVE_KEEP`, checked out |
| `research/real-data-feasibility-audit` | `8f6ee870e1c8d0809d4d1352e8fde0fd450b56d5` | `NEEDS_CONSOLIDATION` | merged; eligible for deletion after pushed-main ancestry/worktree checks |
| `research/framing-2026-09` | `8b9ed1afbfc5b9f575186c4d3207475e8ac2a4c2` | `HISTORICAL_ARCHIVE` | not merged; eligible for deletion only after remote archive-tag verification |

The R0 protocol is an ancestor of R0 execution, and R0 execution is an ancestor of the adaptive-normality tip. The R0 protocol and execution branches were not separately merged. Their history was included in the adaptive-normality merge.

## Consolidation and archive

- `PRE_CONSOLIDATION_MAIN`: `b7ae44fafc4e9ea6671647c5cb73156ddaf26e5e`.
- R0 plus adaptive-normality non-squash merge: `86c166a340c4bde7cd0c54dab167071fece385ef`.
- Feasibility/provenance non-squash merge: `8ac32bbd73dcbb2fb64ead3654bd68c5d4c40321`.
- Required ancestry checks passed for R0 protocol `d7708586fe3264fcd6e5567504cccd97104c2a2e`, R0 final execution `ffae1da6e37b48076e2610390c249318acfbea2e`, adaptive audit `a04bccfe5ecb94e50de99c061011cb26acca755d`, and feasibility audit `8f6ee870e1c8d0809d4d1352e8fde0fd450b56d5`.
- P1r tip `1f4296f62fe3f0a514171a94afe3ce8bc1686986` was already an ancestor of starting `origin/main`.
- The framing branch was not merged. Annotated tag `archive/pre-g1-framing-2026-09` was created locally and resolves to `8b9ed1afbfc5b9f575186c4d3207475e8ac2a4c2`; remote publication and verification are part of the final push gate.

## Scientific-file integrity

Compared against `a04bccfe5ecb94e50de99c061011cb26acca755d`, all of the following were unchanged: `research/real_data_r0/results.json`, `research/real_data_r0/results.md`, `research/real_data_r0/scientific_assessment.md`, `research/real_data_r0/red_team_execution_v1_2.md`, and the full `research/adaptive_normality_xlstm/` directory.

The authoritative R0 result files still classify both xLSTM and the capacity-matched auditable LSTM as `R0_NO_RESOLVED_INCREMENT`. The scientific assessment retains L1d as **NOT SUPPORTED at R0 resolution**. No conclusion or result was edited during consolidation.

## Verification

No model training, R0 execution, M1 execution, GPU research run, or data acquisition was performed. `reports/m0_protocol.md` conditional GO/STOP gates govern research execution; this history cleanup did not start a research phase or generate results.

Pytest was run from a temporary dependency target directory; no dependency or test configuration was added to the repository.

- A full `tests/` collection found missing environment dependencies `xlstmad` and `tta` in two unrelated test modules. Excluding those two modules, the core suite collected 196 tests: 195 passed and one R0 v1.2 feature-schema test could not complete because `xlstmad` is unavailable.
- The focused R0 plus feasibility run passed 56 tests. One additional R0 v1.2 test required unavailable `xlstmad`; the acquired-manifest hash test required absent raw data at `data/external_real/smd`.
- Re-running available R0 v1.2 tests yielded 10 passed and one deselected for the missing `xlstmad` dependency. Available feasibility/provenance tests yielded 5 passed and one deselected for the absent SMD data.
- No test was altered, and no raw dataset was fetched.

## Branches eligible for deletion and explicit protections

After the new `origin/main` is pushed and its ancestry rechecked, `research/real-data-feasibility-audit` is eligible for deletion if its tip remains `8f6ee870e1c8d0809d4d1352e8fde0fd450b56d5`, no worktree checks it out, and it has no new unique commits. `research/framing-2026-09` is eligible only after the remote archive tag is verified to resolve to `8b9ed1afbfc5b9f575186c4d3207475e8ac2a4c2` and the branch tip remains unchanged.

Explicitly protected branches include current M1 `research/adaptive-normality-m1-smd`; checked-out P1r `experiment/input-derived-observable-control`; checked-out R0 protocol `research/real-data-r0-protocol`; checked-out R0 execution `experiment/real-data-r0-execution`; checked-out adaptive audit `research/adaptive-normality-xlstm`; original `main`; and all other branches checked out in the worktree inventory above. No local branch ref was eligible for deletion because every local branch other than this consolidation branch was checked out in a protected worktree.
