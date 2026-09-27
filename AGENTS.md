# Project instructions

Read and follow `/home/p76141495/.codex/RTK.md` when available.

## Persistent user preference

- After completing project work that changes tracked files, commit the completed changes and push to the configured GitHub remote before reporting completion. The user explicitly authorized this ongoing workflow on 2026-09-12; do not ask for push confirmation again.
- Include any previously completed local commits awaiting push. Preserve unrelated uncommitted changes. Never force-push or overwrite remote history to satisfy this preference.
- Verify the push succeeded. If it fails, report the failure and the remaining unpushed commits rather than claiming synchronization.

## Research constraints

Follow `reports/m0_protocol.md` for revised M0 execution order, data-manifest requirements, and conditional GO/STOP gates. Authorization to commit and push does not bypass research gates or authorize larger experiments.

## GitHub Issue workflow

Use the GitHub Issue and its comment thread as the project work queue and review record:

1. ChatGPT reviews the Issue and the applicable protocol, then updates the protocol or records a decision when needed.
2. An Issue comment from ChatGPT defines the next Codex task. Treat that comment as the task scope and follow its acceptance criteria, this file, and applicable research gates.
3. Codex performs the task, commits the completed changes, and pushes them to the configured remote.
4. Codex replies in the same Issue with a concise summary, commit SHA, verification evidence, and any remaining risks or blockers.
5. ChatGPT reviews the Issue, the pushed commit, and its evidence against the protocol, then posts the next task comment or records a GO/STOP decision.
6. Continue only from the next task comment. A STOP decision halts the workflow; a GO decision advances it subject to any conditions recorded in the protocol.
