# P5-0B1R final gate

**Final status: P5_0B1R_STRUCTURALLY_READY**

This means only that the deterministic structural inventory is suitable for
review before a separate prefix-only adjudication stage. It does not authorize
label access, detector fitting, readiness efficacy evaluation, or outcome
scoring.

## Gate evidence

- The pinned archive size, MD5, and SHA-256 match the recorded values.
- Central-directory validation found 93 configured entities with 93 exact,
  unambiguous operational-data paths. Four exact metadata members were read.
  All raw members were opened through the installed exact allowlist. The
  opened-path log contains no denied member, including the archive-root
  README.
- The immutable split contains 16 TARGET, 74 SOURCE, and 3
  UNSUPPORTED_FOR_ENTITY_SPLIT entities. Independent recomputation confirms
  the frozen salt, digest ordering, and target quota. No overrides or stratum
  merges were used.
- All 93 parsed series have a parseable timestamp in the first raw data row,
  zero timestamp parse failures, zero timezone-mismatch rows, and zero
  out-of-order rows.
- All five split-eligible strata have a nonempty deterministic feature-name
  intersection and are classified
  SCHEMA_COMPATIBLE_WITH_PREDECLARED_COMMON_SUBSET. Three singleton strata
  remain unsupported. One has missing configuration metadata; two have a
  repeated measurement header, which is preserved for audit and classified
  SCHEMA_INCOMPATIBLE. None was promoted into SOURCE or TARGET.
- Every TARGET reaches each fixed elapsed-time point through 64 days.
  At 64 days, target actual row counts range from 3,513 to 10,486 (median
  9,216); median missing-cell fraction is about 0.0704, with a maximum of
  about 0.8022. The largest target gap is 3,365,400 seconds. These are
  structural availability and data-quality measurements, not evidence of
  normal exposure or a usable continuous prefix.

## Conditions for the next stage

Before any prefix-status source is opened, an independent reviewer must freeze
the exact look schedule, N_max, purge, and fixed suffix boundary. An
independent prefix-only adjudicator must return only ELIGIBLE or
NOT_EVALUABLE plus a provenance hash. Failed prefix or suffix checks remain
NOT_EVALUABLE; no target, first-row start, cut, or horizon may be replaced.
The remaining P5-0B2 sequence is specified in label_boundary_protocol.md and
was not executed here.

## Verification and review

- All 18 synthetic access-policy, parser, split, chronology, horizon, and
  fixed-grid tests pass.
- Two complete builds produced byte-identical download, access, role-seal,
  entity, schema, and horizon artifacts.
- Independent Astra code/artifact review: PASS. The reviewer did not open the
  source archive.
- This recovery opened no archive-root README or semantic label/event payload.
