# P5-0B1R PreDist deterministic structural recovery

## Purpose

This worktree implements the recovery handoff on Issue #9 after the accepted
P5-0B1 label-boundary incident. It produces deterministic, label-blind
structural manifests for the pinned PreDist v2 archive. It does not run a
readiness or anomaly-detection experiment, open event labels, choose an
efficacy horizon, or authorize P5-0B2 label access.

The structural outputs describe raw-file availability, schema, chronology,
data quality, deterministic entity roles, and fixed-grid elapsed-time
availability. Availability is not evidence that a prefix is normal.

## Pinned archive

- Zenodo record: https://zenodo.org/records/19496480
- File: predist_dataset.zip
- Size: 266,814,500 bytes
- MD5: 298b6425df12ee0d93c05bd67efa3b75
- SHA-256: bbd95677835110a953146441f2215ad4ebd207bf3aca70496ce799605cfc218e

The archive is read from an external path and is not committed. The builder
checks the size and both hashes before reading member payloads.

## Access boundary

The builder reads the ZIP central directory first. It then opens only these
exact metadata paths:

- manufacturer N/configuration_types.csv
- manufacturer N/feature_descriptions.csv

The raw allowlist is derived from those entity IDs and exact central-directory
paths of the form
manufacturer N/operational_data/substation_ID.csv. Every non-directory
member under operational_data/ must match one configured identity. Unknown
CSV members fail closed. No file contents are inspected to decide whether a
path is a label or a raw series.

The archive-root README.md and paths containing normal-event, fault,
disturbance, maintenance, report, event, anomaly, or label terms are denied.
They may be listed from the central directory and their compressed-archive
integrity is covered by the whole-archive hash, but their member payloads are
never opened. Raw headers containing forbidden semantic outcome fields also
fail before the full raw member is parsed.

One configuration metadata row has an empty configuration type. Its entity
is retained in the structural inventory but marked
UNSUPPORTED_FOR_ENTITY_SPLIT; it is not silently grouped with another
entity. Repeated measurement names in raw headers are preserved using
deterministic occurrence suffixes for structural parsing, recorded in the
manifest, and force that exact stratum's schema classification to
SCHEMA_INCOMPATIBLE. No repeated field is silently dropped. Any other
identity or path ambiguity stops the build.

## Deterministic roles and chronology

Within each exact (manufacturer, configuration_type) stratum, the role
digest is:

SHA256(UTF8(salt || manufacturer || configuration_type || entity_id))

The salt is
P5-PREDIST-V2|209e1f55ee19bbaf71ee6e658938e4e14788ad46. Digests sort in
ascending lexical order. For n < 5, all members are
UNSUPPORTED_FOR_ENTITY_SPLIT and strata are never merged. Otherwise,
max(1, floor(n/5)) entities are TARGET and the rest SOURCE. There are no
manual overrides. An entity's structural start is the timestamp in its first
raw data row. If that timestamp is invalid, the entity has no evaluable start;
the builder never substitutes the minimum later timestamp or a cleaner span.
Any timestamp parse failure, timezone mixture, or out-of-order row marks
chronology invalid and blocks the final gate for a SOURCE or TARGET entity.

The fixed elapsed-time grid is 1, 2, 4, 8, 16, 32, and 64 days. Nominal
10-minute row equivalents (144 through 9,216) are reference values only.
Actual rows, elapsed-time reach, timestamp gaps, missingness, and numeric
validity are reported separately.

## Rebuild and tests

From the repository root, with the pinned archive at the external path:

~~~sh
python3 research/p5_0b1r/scripts/build_manifest.py \
  --archive /tmp/predist_dataset-v2-19496480.zip \
  --output-dir research/p5_0b1r
python3 research/p5_0b1r/scripts/audit_horizons.py \
  --entity-manifest research/p5_0b1r/entity_manifest.csv \
  --output research/p5_0b1r/horizon_coverage.csv
python3 -m unittest discover -s research/p5_0b1r/tests -v
~~~

access_policy.json records the exact opened-member path log and asserts that
every opened member belongs to the metadata or raw allowlist. The scripts
write canonical JSON and stable-order CSVs so a repeated build can be
byte-compared. The archive and raw observations are never copied into the
repository.

## Scope boundary

The label_boundary_protocol.md specifies the later P5-0B2 sequence. This
recovery does not perform prefix adjudication, detector fitting, readiness
evaluation, suffix-label access, or outcome scoring. Structural readiness,
if reached, is only readiness for a separately reviewed prefix-adjudication
stage.
