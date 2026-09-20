# Deferred mLSTM mechanism-audit plan

This plan is **not authorized for execution** because Canary B is BLOCKED.
It becomes eligible only after a future backend/training-validity review.

The audit should reuse the existing frozen checkpoints first. For each common
W=64 decision, expose the actual mLSTM matrix-memory state directly (or through
a read-only validated observer), preserving reset and right-edge causality.
Compare the following fixed low-capacity arms on source-disjoint synthetic
folds:

1. score/history control;
2. score/history + existing sLSTM common18;
3. score/history + mLSTM matrix-memory summaries;
4. score/history + sLSTM + mLSTM summaries.

Use equal-capacity semantic summaries, train-only scaling, pooled train/validation
logistic fitting, frozen test cohorts, paired source/event row keys, and the
existing bootstrap/sign-flip/Holm discipline. Report whether mLSTM adds
incremental information beyond history and sLSTM, while treating matrix-memory
statistics as descriptive until feature-level observer equivalence is proven.
Do not infer safe adaptation, persistent cross-window memory, or deployment
benefit from this information-content audit.
