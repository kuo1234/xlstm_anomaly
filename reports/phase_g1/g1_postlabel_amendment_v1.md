# Phase G1 post-label reporting-only amendment — v1

Status: **PENDING_EXTERNAL_REDCHECK**

This prospective amendment is submitted after the first labeled G1 execution
failed during final manifest construction. It does not authorize estimation or
reinterpret any existing output.

## Cause

The launcher accepted the relative output directory
reports/phase_g. At the end of all 2,625 stream extractions it attempted to
serialize the relative primary-cache path with Path.relative_to(ROOT), where
ROOT is absolute. The resulting ValueError stopped execution before probe
fitting, AP, confirmatory statistics, secondary views and decision writing.

The complete v1 stream/cache attempt is recorded in
g1_postlabel_failure_v1.md/json and remains QUARANTINED.

## Narrow correction

The runner now canonicalizes output_dir exactly once at the run boundary with
Path(output_dir).expanduser().resolve(). All later artifact links are
serialized relative to the same absolute repository root.

This changes only path representation and directory handling. It does not
change observations, labels, feature extraction, model/checkpoint state,
optimizer state, row masks, probe fitting, AP, statistics, or decision rules.
The added regression test exercises only relative-path canonicalization and
does not load test data, join labels or fit a probe.

## Execution boundary

No patched post-processing, cache reuse, labeled rerun, AP calculation or
scientific interpretation has been performed. External red-check must decide
whether a fresh labeled execution or a separately audited cache
post-processing route is permitted. The quarantined v1 cache may not enter
estimation unless that route is explicitly authorized.
