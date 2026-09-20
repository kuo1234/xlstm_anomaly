# Final decision

**DENSE_MLSTM_SIGNAL_NOT_MATRIX_SPECIFIC**

The old stride-32 seed-11 result reproduces from a single dense base cache.
At true stride 1, mLSTM summaries still add `+0.145661 AP` over history and
`+0.016657 AP` after the validated sLSTM representation. However, the
matrix-memory C ablation is `-0.000592 AP` in the H-only comparison and only
`+0.006610 AP` conditional on sLSTM; M_noC already preserves the broad mLSTM
gain. This supports a layer-state signal, not a matrix-memory-specific claim.

No p-values or confirmatory inference were computed. Only seed 11 was run.
The next appropriate study is a separately proposed three-seed dense
replication, not H3b, persistent state, or long-context training.
