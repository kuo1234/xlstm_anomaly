# G1.1 prospective matched-analysis amendment

This amendment resolves the pre-label ambiguity identified in the G1 review of
`3a7b474`. It is prospective: no Phase-G labels, probe fits, AP values, or H2/
H3a outcomes were inspected when this file was written.

## Separate estimands

`duration_severity_stratified_robustness` is the only supportive robustness
analysis. It evaluates the already-frozen pooled probe on the ordinary
`semantic="anomaly"` test stream, with positive rows stratified by one
non-stress anomaly event's fixed duration (`1, 16, 64, 256`) or severity
(`1, 2, 3`). The negative rows are the same eligible anomaly-free
drift/transition cohort used by the primary binary task. Persistent-fault,
mixed, and windows touching more than one anomaly event are excluded; no
negative duration/severity label is invented.

The probe, scaler, C, cohort definition, and predictions are frozen before
subgroup evaluation. No subgroup refitting, rescaling, bin merging, or
threshold tuning is permitted. Unsupported prespecified strata are reported
as `INSUFFICIENT_SUPPORT` and cannot be merged or made to pass.

For H2, duration and severity contrasts are the frozen
`AP(history+combined) - AP(history)` per-stratum values. Equal-weight duration
macro requires at least `0.02` and at least 3/4 positive strata; severity macro
requires at least `0.02` and at least 2/3 positive strata. H3a uses the same
strata for A/B/C; A requires `>=0.02`, while B/C require a strictly positive
macro, with the same positive-stratum counts. These subgroup robustness gates
are not added to the four-member Holm family and cannot rescue a failed primary
comparison.

`semantic_nonidentifiability_control` is a separate negative control. The
`semantic="anomaly"` and `semantic="legitimate"` counterparts intentionally
share observations and timestamps while reversing evaluator truth on event
rows. The extractor and frozen probe must therefore produce identical features
and predictions. Its AP is never used as H2/H3a support, and no classifier is
required to distinguish the pair. A difference caused only by semantic
metadata is an implementation defect.

## Provenance and seal sequence

The implementation/configuration is committed first as
`G1_IMPLEMENTATION_COMMIT`, without a PASS self-review report. A fresh
adversarial review then reads that exact committed tree and records its SHA and
scientific-file hashes. Only a report-only `G1_REVIEW_COMMIT` may contain the
`PASS_FOR_LABEL_ACCESS` review. The labelled launcher accepts only that review
commit, verifies that the reviewed implementation is an ancestor, and checks
that every scientific file is byte-identical between the two commits and the
working tree. The review JSON records the reviewed implementation SHA but does
not embed `G1_REVIEW_COMMIT` itself; the latter is derived from the immutable
seal argument supplied to the launcher, avoiding an impossible Git
self-reference.

The historical pre-label STOP evidence from `3a7b474` is preserved unchanged;
this amendment does not overwrite or reinterpret it.
