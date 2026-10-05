# Provenance

Remote root: /home/p76141495/home/xlstm_anomaly/.worktrees/p7-p10-segment-memory. Ignored cache: data/p5b_real_context_novelty/. Acquired only through ssh kuo; tracked facts/hashes/derived audit, no source PDFs, raw CSV copies or observation arrays.

- [Audit plan](audit_plan.json): Mission1/2, all named metadata, caps fixed before retrieval.
- [Member receipts](metadata_receipts.json): release12528696, member path/offset/CRC/length/SHA256; publisher archive MD5 separate from computed member hash.
- [Range receipts](range_receipts.json): exact URL, inclusive requested range, UTC,206, Content-Range, body SHA256. Footer/directory cached; header/compressed-member bodies hashed at acquisition but not all retained separately.
- [Source receipts](source_receipts.json): official code/doc/discovery acquisition or403; code pins in exact URLs.
- [Reused sources](reused_sources.json): P5-A official ESA sources; file hashes checked.
- [Web inspection](web_inspection.json): publisher search previews, query scope, full-text limitation; no invented full-file hash.
- [Chronology](chronology.json): labels ARE exposed. No label-blind evaluation or confirmatory transfer.
- [Rare audit](rare_nominal_audit.json): all691 derived mission/event rows; anonymous tokens stay anonymous.
- [Claim matrix](claim_matrix.json)
- [Verification](verification.json): actual checks and limitations.

Whole archives not downloaded; publisher archive MD5 not locally verified. Member CRC validates ZIP transport consistency, not semantic truth or complete archive identity. Metadata is not a permission/health certificate.

Reproduce through official release12528696 content URLs: request last65557bytes; parse ZIP EOCD; bounded central directory; local header/compressed payload for named CSVs only. Require exact206/Content-Range before body read; reject200, oversized/encrypted/unknown compression; deflate and check length/CRC before member SHA256. No fallback full download.
