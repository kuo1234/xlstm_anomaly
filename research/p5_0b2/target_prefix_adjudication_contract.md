# TARGET prefix-only adjudication contract (design only)

## Release gate

No adjudication is performed in P5-0B2. It may be run only after the
SOURCE-only detector/readiness procedure has been executed, all source model
and readiness parameters have been hashed and sealed, and an independent
review has accepted that seal. The adjudicator is a separate process from the
method-development and scoring process.

If a stratum's SOURCE model or margins are `SOURCE_MODEL_NOT_EVALUABLE`, do
not open any TARGET timestamps, sensor rows, or labels for that stratum. After
the failure seal, emit only the generic `NOT_EVALUABLE` token and a
provenance hash for its TARGET entries; the reason stays in the restricted
SOURCE audit compartment.

## Primary provenance class

The sole primary class is `REFERENCE_CLEAN_PRIMARY`. It means only that the
prefix is retrospectively free of overlap with the available, predeclared
`KNOWN_FAULT`, `DISTURBANCE_FAULT`, and `DISTURBANCE_OTHER` intervals under
the rules frozen in `source_label_firewall.md`. Non-fault disturbance
intervals include recorded tasks/maintenance activities. It is not “verified
normal,” proof of physical normality, or evidence about suffix outcomes.
There is no secondary class and no fallback class; no class may be added
because primary eligibility is low.

## Exact interval and eligibility rule

For each TARGET entity, preserve its first raw-row timestamp from the pinned
role seal. Let row 1 denote that first raw observation; the primary
commissioning interval is the closed interval from row 1's timestamp through
the timestamp of raw observation 2,304. The adjudicator also checks the
fixed 64-day elapsed boundary. The task is `ELIGIBLE` only if all predeclared
annotation sources for that manufacturer exist and parse completely, the
first timestamp is valid, timestamps through row 2,304 are nondecreasing in
raw-row order (duplicates are allowed), raw observation 2,304 occurs no later
than 64 recorded timestamp days after the start, all relevant annotation
intervals are bounded and parseable, and no `KNOWN_FAULT`,
`DISTURBANCE_FAULT`, or `DISTURBANCE_OTHER` interval overlaps the
commissioning interval. `faults.csv` rows are included only when
`efd_possible=true`; malformed or missing flags fail closed. Normal-event
annotations do not certify unannotated gaps. Any overlap, missing required
source, failed/truncated table read, malformed interval, decreasing timestamp,
missing #2304, or elapsed-budget violation is `NOT_EVALUABLE`. Timestamps
remain the dataset's naive recorded values; elapsed days are computed on that
recorded axis with no timezone inferred or applied.

The adjudicator may read only raw timestamp columns through row 2,304; it
must stop before reading any sensor value or any row after #2,304. Label
access must use a restricted prefix projection that returns only whether a
predeclared annotation overlaps the prefix and a provenance commitment. It
must not expose a suffix event/date/description or the fixed suffix contents
to the adjudicator or method process. If the label store cannot enforce this
projection, do not perform target adjudication; report an information-boundary
block rather than opening the full target annotation table.

The annotation source inventory is fixed to the public PreDist tables
`faults.csv`, `normal_events.csv`, and `disturbances.csv`; normalization uses
the locked rules in `source_label_firewall.md`. A restricted service must
perform the interval-overlap operation and return only the overlap decision
and a provenance commitment for this prefix. The adjudicator must not receive
full annotation rows, future interval endpoints, or suffix annotation
payloads. Do not use descriptions, README content, target performance, or
suffix outcomes to change a decision. The suffix at raw indices strictly
after 2,304 is never opened by the adjudicator.

## Minimal output and separation

For each adjudication request, output exactly one status token
`ELIGIBLE` or `NOT_EVALUABLE` and one `provenance_hash` committing to the
structural seal hash, annotation source hashes, parser/version hash, and
prefix-boundary specification. Do not return a reason, overlap flag, event
type, date, count, entity ID, source row, or target-specific summary to the
method process. Keep the per-entity routing handle outside the method-facing
payload; it is a presealed opaque role digest and carries no semantic reason.
The denominator is the fixed 16 TARGET entities and five exact strata in the
structural role seal; `NOT_EVALUABLE` entries remain in every joint-success
denominator and cannot be replaced. The method-facing eligibility payload
contains no aggregate eligibility count. A privacy/access auditor may retain sealed adjudication inputs in its
restricted compartment, but it does not expose them to method development.

## Boundary failures

Any unexpected label source, unreadable or ambiguous annotation, failed or
truncated source read, provenance mismatch, or attempted suffix access stops
adjudication and returns `NOT_EVALUABLE` without detail. A target may not be replaced, its
start/cut/horizon may not move, and failed targets remain in the fixed
denominator. Re-adjudication requires a versioned protocol amendment before
any target trajectory or suffix outcome is inspected.
