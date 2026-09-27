# SOURCE label firewall design and seal contract

## Phase status

This is a design/code seal, not an execution record. No manufacturer label
CSV or semantic label payload was opened for P5-0B2. In the next SOURCE-only
phase, this dedicated process is the sole component allowed to read the
manufacturer-level label tables. Detector and readiness code receive only its
canonical SOURCE-only artifact. They must not open a manufacturer label CSV
directly.

## Inputs and role filter

The role authority is the immutable
`research/p5_0b1r/role_split_seal.json`, SHA-256
`00e0cec62d238c78f2d0b3c79910c0ffaf1122d1582c28c8848022fb3e10e33f`.
Build an internal lookup keyed by exact `(manufacturer, entity_id)` from that
seal. Reject duplicate keys or any ambiguous entity key before reading label
tables. The public v0.7.1 PreDist source identifies the label inputs as
semicolon-delimited `faults.csv`, `normal_events.csv`, and `disturbances.csv`
with `substation ID` as the entity field. This contract does not use or
instantiate `PreDistDataset`. The pinned manufacturer keys are exactly
`manufacturer 1` and `manufacturer 2` (lowercase); do not case-fold or
normalize them. Synthetic tests use those sealed key spellings, including a
test against the pinned structural role index.

Before iteration, validate that every required table header occurs exactly
once without reading row content. Extra header columns are ignored; duplicate
headers, missing required headers, or an unexpected table fail closed. The CSV
parser runs in strict mode and each header/data record must occupy exactly one
physical line; malformed quotes or multiline records fail the entire table
with a generic error because row boundaries cannot be trusted. For each
parseable row, inspect only its identity field to classify the role. If TARGET or
unsupported, discard it immediately without checking field values/counts or
parsing dates, type, description, or other semantic fields; do not append it
to an intermediate table. For SOURCE rows only, verify all header cells are
present and there are no excess cells before parsing interval fields. A short
or overlong SOURCE record, unknown entity, missing identity, duplicate role
key, malformed source interval, or unexpected schema fails closed: delete
partial output and emit only a generic failure status, never the offending
row, entity, date, event, or target count.

## Canonical SOURCE-only artifact

The only data artifact passed to source development is a deterministically
sorted canonical table with exactly these fields:

`role_digest, annotation_source, annotation_kind, interval_start,
interval_end`.

`annotation_source` is one of `faults`, `normal_events`, or `disturbances`.
`annotation_kind` is a fixed enum: `KNOWN_FAULT`, `REFERENCE_NORMAL_EVENT`,
`DISTURBANCE_FAULT`, or `DISTURBANCE_OTHER`. `role_digest` is the SOURCE
entity digest in the role seal. No raw entity ID, Event ID, free-text
description, original row, target count, target date, or target-derived
summary is emitted. Rows sort by role digest, interval start, interval end,
source enum, and kind enum. The artifact is UTF-8, canonical JSON Lines with
sorted keys and one LF per row. Timestamps retain the dataset's naive local
clock values and precision; explicit timezone offsets fail closed. The
elapsed-day calculation later uses the same recorded timestamp axis without
inferring or applying a timezone shift.

## Interval normalization

The adapter is frozen to the public v0.7.1 field names and interval mapping;
it must not call the EFD PreDist loader:

1. A `faults.csv` row is `KNOWN_FAULT`. Start is `Possible anomaly start`, or
   `Report date - 48 hours` when the possible start is absent. End is
   `Possible anomaly end`, or `Report date + 24 hours` when the possible end
   is absent. If a required fallback date is absent, the source table is
   invalid and the firewall fails closed.
2. A `normal_events.csv` row is `REFERENCE_NORMAL_EVENT`, with interval
   `Event start` through `Event end`. These annotations do not certify any
   unannotated timestamp as normal.
3. For a `disturbances.csv` row with `type=fault`, use start `floor(Event
   start, 10 minutes) - 48 hours` through `floor(Event start, 10 minutes) + 24
   hours` and kind `DISTURBANCE_FAULT`. For any other disturbance type, use
   `floor(Event start, 10 minutes)` through midnight at the start date plus
   one day, inclusive, and kind `DISTURBANCE_OTHER`. A missing/unparseable
   `Event start` fails the table. The EFD loader's duplicate fault suppression
   is not applied because both independent interval sources are retained and
   unioned; duplicates cannot make an interval appear clean.

Intervals are closed at both ends, matching the public loader's inclusive
time slicing. Description and event-name text is discarded. `Training start`
and `Training end` do not select or tune intervals. A `faults.csv` row is
included only if the public `efd_possible` flag parses as true; false rows are
discarded and missing/unknown flag values fail closed. The timestamp parser
preserves naive local time as stored and never assumes UTC or another zone.

## Output, audit, and log rules

The firewall emits exactly three files in a restricted output directory:

1. `source_labels.jsonl`: canonical SOURCE-only table above;
2. `source_labels.sha256`: SHA-256 of the exact artifact bytes;
3. `access_audit.json`: firewall version, role-seal hash, input table names
   and SHA-256 values, output hash, SOURCE entity count, SOURCE record count,
   schema/version identifiers, and booleans `target_rows_emitted=false`,
   `target_identifiers_logged=false`, `target_semantics_logged=false`.

`source_entity_count` is the number of SOURCE role entries in the pinned role
seal, including entities with no emitted annotation rows; it is not a count
derived from TARGET rows. `source_record_count` is the number of emitted
SOURCE intervals. The audit must not include total input row counts, number
of suppressed rows, TARGET entity IDs, TARGET dates, event types/descriptions,
per-target missingness, or any target-derived error detail. Stdout and stderr contain
only a fixed success/failure token and artifact hashes; exceptions are
redacted. Do not print parser/library warnings. The method-development process
does not receive raw input hashes unless the access auditor explicitly
releases them; it receives the canonical artifact hash and SOURCE-only audit
fields.

Write to a temporary restricted directory, validate the full output, fsync,
then atomically publish. Any failure deletes temporary output and leaves no
partial artifact. Pin Python/parser dependencies and the firewall source hash
in `protocol_seal.json`. The firewall itself and its tests may use synthetic
records only before the source-only stage. No actual label table is used to
test or execute it during P5-0B2.

## Required synthetic tests

Before any future execution, tests must demonstrate:

- mixed synthetic SOURCE/TARGET/unsupported rows emit only SOURCE role
  digests and SOURCE intervals;
- target IDs, timestamps, event strings, and input-row counts are absent from
  artifact, audit, stdout, stderr, and exceptions;
- a TARGET row with deliberately malformed semantic fields is discarded
  before the semantic parser touches those fields;
- unknown and duplicate entity keys fail closed and publish no partial output;
- strict CSV parsing rejects an unterminated quoted field without publishing
  a partial artifact or exposing the quote contents/path in a traceback;
- short SOURCE CSV records fail before interval normalization;
- same synthetic input and role seal yield byte-identical output and hashes;
- intervals use the declared boundaries, fallbacks, and naive timestamp rules;
- method-facing code can consume the canonical artifact without access to raw
  manufacturer paths.
