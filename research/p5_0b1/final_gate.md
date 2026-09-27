# P5-0B1 final gate

**Terminal status: `LABEL_BOUNDARY_BREACH`**

The archive download and checksum verification succeeded, but printing the root README exposed a table of known unlabelled anomaly time intervals. Per the P5-0B1 handoff, this triggers an immediate stop. No structural split/horizon analysis or P5-0B2 authorization recommendation is issued.

The handoff's four structural statuses do not describe this exception. It is neither `P5_0B1_STRUCTURALLY_READY_FOR_PREFIX_ADJUDICATION` nor a structural reframe/archive-layout/schema verdict.

## Access summary

- Official archive: downloaded; size and Zenodo MD5 verified; SHA-256 recorded in `download_manifest.json`.
- ZIP central directory: paths and sizes only.
- Label/event CSV payloads: not opened, parsed, or hashed.
- Raw operational time-series payloads: not opened or parsed.
- README: opened and printed; contained known unlabelled anomaly intervals. This is the recorded breach.
- Candidate source/target IDs, horizons, and schema compatibility: not computed.
- Tests: not run; no scripts were written after the mandatory stop.
- GPU/model/effectiveness experiment: none.

No further dataset work may proceed until a new explicit task reviews this incident and sets an allowed source boundary.
