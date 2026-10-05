# ESA context qualification

**Real runtime context UNQUALIFIED; persistent reference unavailable in inspected support.** Recorded operating evidence is plausible L1, but is not a demonstrated receipt stream and does not become L2 authorization.

## Sources and acquisition

Official dataset [esa/anomaly-dataset](https://github.com/esa/anomaly-dataset/tree/a969698e464788c961dbb646d3da24595c7c7a2b), release [Zenodo12528696](https://zenodo.org/records/12528696); official [ESA-ADB code pin](https://github.com/kplabs-pl/ESA-ADB/tree/67194d389c4aa33a9a61fa0715ebdac3002b11b2). Exact member URL/ranges/hashes and publisher MD5 in [metadata receipts](provenance/metadata_receipts.json) and [range receipts](provenance/range_receipts.json). No whole-archive hash is claimed.

Fixed scope before metadata: Mission1 and Mission2, all available channels/telecommands/labels/anomaly_types/events CSVs. ZIP directory identified filenames only; all channel/TC pickles excluded. HTTP206 and exact Content-Range were required before body read; CSV decompression checked length and CRC32. These minimum slices were necessary because published schema alone does not reveal whether the event table supplies receipt/authority fields. No large raw slice was necessary.

## A1: recorded form versus deployment contract

| Source object | Observed/documented schema | Timestamp/alignment | Meaning / availability | Classification |
|---|---|---|---|---|
| Raw telecommands/*.zip | Documented timestamp-indexed single-column Pandas pickle; directory inventoried, contents NOT read | Documented mission-clock timestamps compatible with channels | General stream issuance vs execution vs status UNKNOWN; receipt, authority, latency and decision availability UNKNOWN | **UNQUALIFIED** runtime contract; potential recorded L1 |
| telecommands.csv | M1 698 / M2 123 rows; Telecommand,Priority | No timestamp | Anonymous IDs/priority; no instance, authority, signature or approval | **UNQUALIFIED** as runtime evidence; static descriptor is not event delivery |
| Mission2 events.csv |604 rows, Event,StartTime,EndTime | Interval boundaries; no issued/received/publication/revision fields | Historical plan intervals; no proof when plan was learned, no TC-ID/channel/approval join | **UNQUALIFIED** runtime publication; evaluator table available |
| labels.csv + anomaly_types.csv | Channel intervals linked to anonymous Class/Subclass and Category | Evaluator event intervals | Rare Event/Anomaly category cannot be runtime permission | **RETROSPECTIVE_ONLY** |
| Official prepared matrix | TC pulses and resampled observations with label columns | M1 30s / M2 18s grids | Whole-series preparation uses future initialization and label-informed restoration | **EVENT_ONLY_NONCAUSAL** in inspected preparation |
| L2 authorization ledger | No inspected object has approved intent, affected eligible scope, independent receipt or validity | None established | Priority/binary value does not imply permission, healthy execution or settled reference | **UNQUALIFIED** |

[ESA paper](https://arxiv.org/abs/2406.17826), supplementary §2.4, documents timestamp-indexed compressed records and a Mission2 table derived from mission plans. That table helped create retrospective rare-event annotations. It supplies neither plan publication history nor receipt time. Anonymization preserves mission timeline relationships but hides physical command/channel meaning.

Raw TC remains UNQUALIFIED rather than alleging its native records are proven noncausal. An event-time-as-arrival, zero-latency replay would be an explicit assumption, not source-backed real receipt semantics. No replay ran. A documented execution example does not settle the global timestamp contract.

## Static preprocessing audit

Pinned notebooks/data-prep/Mission1_semisupervised_prep_from_raw.py123–142 initializes the first resampling bin from a later first observation and restores missed samples based on annotation labels. Lines185–186 fill in both directions. Mission2 counterparts:130–148 and191–192. utils.py1–9 declares Rare Event=2;13–25 synthesizes zero entries around TC peaks. Inspected only, not executed.

These are benchmark preparation choices; they do not mean authors claimed an authorization ledger. They prevent treating prepared features as proof that causal receipt-based input already exists. No resampling repair was introduced to make qualification pass.

## A3: persistent-reference eligibility

| Required support | Finding |
|---|---|
| Old healthy nominal reference |No prefix certified; absence of labels does not certify mode or safety. Arrays not read. |
| Candidate changed condition |Rare intervals exist; operating-state identity and settled reference UNKNOWN. |
| Duration |Exact annotation envelope and union per ID. Long span does not measure repeatable settled-condition exposure. |
| Command/context alignment |Metadata lacks event-to-TC/channel join; TC arrays not read. Paper example is not receipt proof. |
| Fault within candidate |Source anomaly overlap computed; Anomaly is distinct from unsafe operation. Nominal interval need not be clean throughout. |
| Temporal order |Source mission-clock order retained; causal knowledge-arrival order UNKNOWN. |
| Legitimate changed reference |Independent reference eligibility, stable/healthy support and authorized scope not established. |

**REAL_PERSISTENT_REFERENCE_UNAVAILABLE** on this scope. Generic non-anomaly points or rare-event endpoints do not substitute for post-shift truth. Mission3 and all arrays were outside fixed scope; source-owner clarification or newly authorized metadata may change qualification.
