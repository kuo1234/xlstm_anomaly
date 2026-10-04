# Context levels and proposed runtime contract

This is an interface design, not implemented code. Level denotes meaning, not reliability; every level still needs provenance, freshness, support and conflict checks.

| Level | Candidate fields | What it can mean | What it cannot certify |
|---|---|---|---|
| L0 | observation x, derived score/latent/mode, observed actuator included in X | Internal response evidence | Independent legitimacy |
| L1 | asset identity; separately measured ambient/load/speed; recorded mode/command ID; pre-issued schedule | Condition/intent clue with causal delivery | Approval, successful execution, settled or safe |
| L2 | authenticated command/recipe approval, commissioning/maintenance event with declared authority and receipt | Permission for a scoped intended change | Actual cause of X, clean payload, successful transition, immediate admission |
| L3 | fault/anomaly truth, NORMAL_B, regime ID, exact settled endpoint, safe/unsafe bit, retrospective benign annotation, RUL/hs/theta | Evaluator/offline eligibility truth | Any allowed runtime input |

A field named mode is L3 if created from a hidden regime label. A mode inferred from X remains L0. An operating ID acquired independently can be L1 even when numeric. A maintenance completion record can be L2 only for its documented scope, never a universal safety certificate. Source fault occurrence and operational unsafety are separate evaluator concepts; unsafety stays NOT_EVALUABLE without independent safety criteria.

## Allowlisted payload and causal availability

Proposed runtime input: observation/measurement time and receipt time; context events received so far; static, predeployment engineering contract. Event schema:

| Field | Required meaning / provenance |
|---|---|
| event_id, source_id, asset_id | Stable identity, producer and matching asset; no filename/arm encoded evaluator identity |
| context_level, event_kind | L1 observation/operating signal or L2 scoped approval; never truth type |
| issued_at, effective_not_before | Producer clock, uncertainty and intended start; no exact actual settling |
| received_at, sequence_no | Actual ingestion clock and order; append-only deduplication |
| target, units, approved_scope | Intended command/configuration and declared authority; no outcome-selected target |
| authorization_proof, issuer_role | Verifiable issuer and scoped permission, or UNKNOWN for L1 |
| expires_at, revoked_at, correction_of | Predeclared validity/correction; revocation/correction usable only on receipt |
| provenance_hash, schema_version | Audit lineage; versioned interpretation |
| quality, uncertainty, support_status | Missing/delayed/stale/conflicting/unsupported explicitly represented |

At decision time t only events with received_at <= t may be used. Issued_at cannot backdate knowledge. Future effective_not_before is a known intention, not a realized regime. expires_at is authorization validity, not a settling endpoint. Earliest accepted clock ordering must account for uncertainty; chronology violations invalidate context. Optional absent fields stay null/UNKNOWN, not silently filled from labels or future observations.

Join rule: asset identity plus most recently RECEIVED supported event; separate event time and observation time. Never nearest-neighbor time joins using a future event, backfills rewriting past decisions, global test-mode clustering or hindsight interpolation. A late correction triggers a new decision/containment assessment, never retroactive success.

Authorization proof, matching scope, timeliness and validity make an event interpretable as permission. They do not constitute a PROMOTE rule. Context missing/unknown/conflicting/out-of-support yields UNRESOLVED; keep active reference unchanged. Supported context may allow consideration of a candidate while response evidence can veto. Uncertainty is recorded instead of coerced to false fault or true benign.

## Independence and leak checks proposed for a future GO

Trace each context value to its producer, clock and channel. Ban anomaly/type tables, settled/truth files, derived fault IDs, oracle encoder features, post-outcome operator review and label-selected command mappings. Preplanned events need demonstrable issuance history; otherwise evaluator only. If the source only logs command execution/status, classify L1 rather than inventing authority. Metadata availability and data arrival are distinct.

A future test must show: context mutation after time t does not change past decisions; label/truth files cannot be reached by the runtime loader; event IDs carry no arm/seed semantics; validation partitions and supported ranges use training/engineering inputs only; no hidden truth through target values or perfect onset synchrony. Audit labels may assess receipt errors, not create the receipt stream.

No trust/TTL/delay tuning is permitted on evaluation outcomes. Numeric engineering assumptions and an explicit simulated-authority model need reviewer approval and a separate pre-execution freeze; this document is not that executable seal.
