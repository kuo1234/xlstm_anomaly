# Limitations and unresolved questions

## Audit boundary

This review was performed on 2026-09-26 from primary publisher pages, papers, official dataset repositories, and official project documentation where available. It is a bounded documentation audit, not a full raw-data/schema reproduction. No full archives were downloaded; one 1,200-byte HTTP range probe checked a CSV header/cadence, one HEAD request checked a legacy C-MAPSS resource, and one small TEP readme request was denied. Storage estimates are publisher-reported unless explicitly marked as a probe. Public records, files, licenses and branches can change.

## Semantic gaps

- E-Energy labels rows as normal/drift/attack but does not, in reviewed evidence, provide stable event identity, recurrence, event duration convention, or a persistent-fault taxonomy. Its attack is control-logic intervention; it is not interchangeable with an equipment fault.
- PreDist incident reporting is incomplete by design. No report does not mean no fault; low-impact issues may not be reported; approximate onset/end may be absent; normal-event windows are not an exhaustive label of regime transitions. Long gaps and commissioning periods complicate continuity.
- TEP is a simulator and its exact within-stream event schema was not inspected. Mode labels and fault scenario names alone do not establish matched trajectories or event recurrence.
- Other sources mainly offer normal-vs-anomaly labels, fault-free training periods, or varying contexts. They do not establish benign-new-normal semantics.
- No reviewed real source has been verified for all M6 needs in one fixed, licensed, event-disjoint release.

## Metadata and acquisition gaps

- Exact sample cadence and dimensions vary by process or release for NoBOOM, Batch Distillation, SWaT/WADI, BATADAL and DAYPSCI; do not generalize a familiar version's values to every release.
- E-Energy's public data have no explicit dataset license in the reviewed repository. This prevents treating a public GitHub URL as reuse authorization.
- C-MAPSS catalog availability and license statements conflict across Data.gov and NASA Open Data pages.
- DAYPSCI's public data endpoint, data license, storage size and complete schema were not resolved from the paper metadata reviewed.
- For very large TEP, Borg and Batch Distillation releases, the storage burden is material; subset selection must be declared without reference to model outcomes.
- This audit did not independently compute checksums, inspect data schemas beyond the small E-Energy header probe, or reconstruct event labels from arrays.

## Project protocol constraints

- No GPU, model, or experimental artifact was run or changed.
- No Stage1A/B artifact was opened or touched.
- No unopened SMD labels were accessed. Existing M0/M4 protocol remains authoritative; SMD remains the fixed anchor and external datasets do not replace its exact same-D design.
- No source in this report establishes real-data drift-vs-anomaly probe labels unless the source itself already provides the relevant semantic annotation. Never invent event boundaries from model output or distribution statistics.

## Follow-up questions before any candidate is used

1. Can the E-Energy maintainers provide explicit reuse terms and event-level protocol/IDs, including attack episode duration and whether the normal-drift examples cover A→B→A?
2. Which PreDist station/configuration subsets have independently reviewed normal events, complete fault records, stable channels, and contiguous timestamps? How are labels censored around maintenance?
3. Does TEP release a machine-readable event manifest and healthy counterpart for every transition/fault, and is an event-disjoint split already specified?
4. Which file-level licenses apply to individual modalities/releases in NoBOOM and Batch Distillation, and can a compact sensor-only subset preserve the intended protocol?
5. What are the exact release/version and data terms for the accessible C-MAPSS, BATADAL, SWaT/WADI and DAYPSCI files?
