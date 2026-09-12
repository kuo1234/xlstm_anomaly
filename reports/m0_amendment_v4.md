# M0 v4 — final pre-model A2 assignment amendment

User-authorized after review of `9fc305d41a76c347ccf3b7a8df1efb13ec100731`. All prior audit artifacts remain historical and unchanged. A1 and Phase B PASS stand; A2's previous STOP was selection-rule infeasibility, not research failure.

## Unchanged eligibility and inference

Exactly three released files per bucket, in order continuous/change_point/periodic/random_walk. Retain official metadata, released-file hashes, real multivariate finite data, binary labels, unchanged normal-prefix cutoff/minimum lengths, original tags, fit/calibration intervals, fixed-SMD overlap exclusions, and no duplicated released file. Select at most one member of a known exact-duplicate/crop/same-origin group. Exclude synthetic sources including CATSv2 and GHL. Native mappings may remain explicitly unresolved; neither a released filename nor that flag proves statistical independence.

TSB is external stress testing only; all statistical analysis remains source_family-first under v3. Single-family buckets, including periodic if all SMD, are descriptive only and cannot support family-generalized inference. No TSB causal evidence for H2/H3/H4a. All other M0 scientific thresholds and restrictions are unchanged.

## Frozen exact lexicographic optimization

Remove v3's HARD min(3,F_b) family count and associated within-bucket family cap. Preserve all other feasibility constraints. Optimize sequentially, fixing each exact integer optimum before the next:

1. Maximize distinct source_families across all twelve files.
2. Maximize sum of distinct-family counts within the four buckets.
3. Minimize sum over families of squared global file counts.
4. Choose lexicographically smallest concatenation of internally sorted filename triples in the fixed bucket order.

The executable implementation uses `select(..., objective_version=4)` in `scripts/phase_a_v3.py`, preserving v3 as its default historical mode. Binary bucket-family indicators equal presence, not a relaxed proxy; monotone family-count slots encode exact squares. Sequential integer solves use zero relative gap, validate rounded integer constraints, then fix each filename inclusion greedily in lexicographic order only if an optimal feasible completion exists. No random solver tie determines selection. Verify final file/group uniqueness, bucket counts and integer objective values independently. If infeasible, STOP without another relaxation.

Commit and push this rule before running `scripts/phase_a_v4.py`. New artifacts go to `reports/phase_a_v4/`. Explicit summary fields: `selected_count`, `inventory_native_provenance_unresolved`, `selected_native_provenance_unresolved` (null if no selection), plus eligible-inventory unresolved count. Do not rewrite the ambiguous historical v3 summary; this version replaces its reporting convention.

## CPU generator validation authorization

Run every registered source seed (10 train, 5 validation, 10 test) × all five scenarios: 125 base cases. Validate the unchanged generator/configuration from the accepted Phase B; no parameter tuning or seed rejection. Each case checks all five conditions (none/spike/collective/dependency/mixture), exact regeneration, paired opposite-semantic observations, finite arrays, clean fit/calibration prefix, non-overlapping bounded event schedule, severity/duration coverage, disjoint folds, analytical correlation invariants and separate observation/truth serialization. Record per-case checks, canonical array/metadata SHA256, saved-file hashes and aggregate outcome, including every failure. This is CPU validation only, not a model experiment. No detector/probe/model results, GPU training, or Phase C until external review returns.
