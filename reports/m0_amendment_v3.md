# M0 v3: A1 strict anchor / A2 external stress test

2026-09-12, before any model-result inspection or generation. User-authorized scope amendment after accepting the provenance STOP at `ad97c4a643c3586c01a858497710f77c587d0a35`. Preserve `reports/phase_a/` and its seal unchanged. This amendment does not reinterpret that strict audit as PASS.

## Evidence levels and scientific rationale

A1: retain exactly the sealed raw and official CANDI preprocessing files for SMD machine-1-8 and machine-2-1. They alone remain the confirmatory real-data anchor for official CANDI reproduction, admission contamination and natural H1 analysis. Byte-verify all twelve assets against the existing seal; do not change splits/preprocessing. The original caveat about absent native train-label files remains.

A2: experimental unit is an official released TSB-drift series, identified by pinned StrAD metadata and released-file SHA256. Require source dataset/family, D/N, released cutoff, numeric finite D≥2 observations, binary labels, ≥320 prefix and ≥256 test observations, and an entirely normal original released prefix. Keep floor(0.8*cutoff) fit/calibration split and all original tags. Native file/crop mapping is desirable, not mandatory; record `native_provenance_unresolved` explicitly. Preserve contradictory or incomplete provenance notes. Dataset-level family is the released dataset identifier, not an invented physical identity.

Keep CD=1, the existing StrAD commit, synthetic exclusion (including CATSv2), and known overlap exclusions with fixed SMD. Do not duplicate a released filename or select two members of a **known** exact-duplicate / same-origin group. This conservative deduplication does not reinstate a requirement for twelve verified distinct native sources. Unknown native mappings are not treated as verified independent sources.

TSB is an external nonstationarity stress test, not causal drift-vs-anomaly evidence for H2/H3/H4a, and cannot rescue their GO criteria. Causal claims remain synthetic; SMD remains the strict reproduction anchor. Report family membership and limitations openly. Every TSB macro CI and statistical test clusters at source_family FIRST: equal-weight family means (series means within family, paired seed means within series), bootstrap whole families first and detector seeds second with paired series retained, and sign-flip whole family effects. Never count released series or windows as independent replicates. Use existing 10,000 draws and seeds 901/902. With fewer than two families a CI/test is N/A; with few families report exact attainable p-value resolution and no confirmatory generalization. In particular a single-family periodic bucket is descriptive only.

## Frozen deterministic A2 assignment algorithm

Freeze this algorithm and its implementation in a commit, push it, THEN generate the revised manifest. Inputs are only the immutable strict audit inventory, metadata, exact duplicate relations and raw-file hashes. No model scores, anomalies-in-test requirement, new numeric filtering or random selection.

1. Admit rows passing all numeric/prefix requirements, excluding synthetic and known fixed-SMD overlap. Waive only `unresolved_original_trace_mapping`; retain that flag. Use upstream_dataset as source_family. Union known exact duplicate/crop and documented same-origin groups. Require twelve unique released files and at most one per known group.
2. Buckets, in order: continuous, change_point, periodic, random_walk; exactly three files each. Multi-tag rows may fill one slot only.
3. Prevent avoidable within-bucket family dominance: for bucket b let F_b be the number of eligible families before assignment. Require exactly min(3,F_b) represented families and at most ceil(3/min(3,F_b)) files of any family in that bucket. Thus use three families if possible, a 2+1 split with two families, or three from the sole family. These are hard constraints; if globally infeasible, STOP for review, do not relax silently.
4. Among feasible assignments maximize the number of distinct families across all twelve slots (equivalently minimize repeated-family slots).
5. Among ties minimize the sum of squared global family counts, spreading unavoidable repetitions evenly.
6. Among remaining ties choose the lexicographically smallest concatenation of four internally filename-sorted triples in fixed bucket order. Implement by fixing optimal objectives, then scanning filenames lexicographically within each bucket: include each earliest remaining file if a feasible completion exists, otherwise exclude it. No heuristic solver tie-breaking determines selection. Integer constraints/objectives are rechecked independently on the final assignment. Solver failure is STOP, not permission to use a different assignment.

Write new artifacts under `reports/phase_a_v3/`: revised full inventory/exclusions, selected manifest, source families/counts, unresolved native flags, provenance, hashes, dimensions/cutoffs/intervals and exact assignment objectives. Old audit remains immutable. Check every candidate's released bytes against the strict inventory before selection; check the existing A1 seal. No generation of a new manifest until this rule commit is complete.

## Phase B authorization and remaining gates

After A1 checksum verification and this rule's commit/push, Phase B CPU scaffolding is authorized without complete native TSB provenance: causal evaluator, label isolation, D=8 generator, deterministic correlation invariants, metrics, score-before-update and identical-observation/opposite-label control. Commit executable correlation invariant tests BEFORE inspecting any generated observations. Store generator schedules/equations before any training. Dummy arithmetic fixtures for software tests are not detector experiments and are not reported as model results.

Keep all v2 H1–H5 rules, label isolation, calibration, causal score-before-update, probe controls, fixed-budget and reproduction/audit separation unchanged. No CANDI/xLSTM/LSTM fitting, GPU pilot, logistic probe, learned gate or other model-result generation is authorized. Phase C needs a subsequent review/authorization.
