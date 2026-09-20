# Dense stride-1 mLSTM attribution

This directory records the seed-11-only exploratory diagnosis of the earlier
stride-32 mLSTM result. It answers whether the result survives the original
dense decision semantics and whether the matrix-memory family C is responsible
for the signal.

The execution uses the existing frozen checkpoint and a single observation
cache. No retraining, additional detector seeds, persistent state, W128+ study,
H3b, or G1 modification is permitted.

See `dense_cache_design.md`, `stride32_reproduction.md`, `stride1_results.md`,
`family_ablation.md`, and `next_decision.md` after analysis completes.
