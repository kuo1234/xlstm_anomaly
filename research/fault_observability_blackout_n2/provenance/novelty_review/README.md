# Novelty review evidence, 2026-10-06

Task record: issue29_snapshot.json, reviewer comment 6008999873. This is a source/methodology and data-feasibility review, not model evaluation.

- sources.json: five complete primary methodology/evaluation sources plus failed/metadata-only publisher retrievals. HTTP success does not imply full-text access; M2SC2's redirect is explicitly not full text.
- additional_sources.json: pinned 3W schema metadata, pinned QAPPD author README, supplementary primary articles and SRE chapter. `retrieved` means bytes acquired, not independently reproduced scientific claims.
- 3w_tree_summary.json / 3w_sources.json: exact pinned release, tree inventory and selected file identities (Git blob + SHA256). Three lexicographic WELL samples from directories 0/2/3, selected before null/label inspection; no favorable sample replacement.
- 3w_sample_inspection.json: observed schema, released label counts and null fractions, including unknowns. All-null channel installation semantics remain unknown.
- replay_feasibility.py: read-only schema/label/null parity against cached exact bytes. Requires duckdb==1.4.3; no model dependencies. Run from repository root:

```sh
python3 -m venv /tmp/issue29-data-audit
/tmp/issue29-data-audit/bin/python -m pip install duckdb==1.4.3
/tmp/issue29-data-audit/bin/python research/fault_observability_blackout_n2/provenance/novelty_review/replay_feasibility.py
```

Reacquire missing cached assets from the exact `url` in the ledger to `local_path` (or `path` for articles), then verify SHA256 and Git blob before replay. Do not substitute current HEAD or a nearby dataset release. Raw files and full article assets stay under ignored data/fault_observability_blackout_n2/novelty_review/; they are not committed. Re-fetching a dynamic publisher page may change its HTML hash; that is a new source snapshot, not a reason to silently update this evidence.

QAPPD Zenodo version1.0 (DOI 10.5281/zenodo.20287835) was inspected via official public metadata; its arrays were not downloaded/unpickled. This release's ten datasets/fourteen channels differ from LSD's sixteen traces/fifteen variates; bridge unknown. No inference of native observation loss.

Access blockers: SFAFormer, M2SC2-AD and RC-WMRAD full publisher pages returned 403; MoPIN's earlier direct retrieval returned 418. Use an authorized publisher/institutional copy if subsequently supplied, record version/hash and rerun method/evaluation comparison. Indexed primary excerpts are not full-text clearance. Wind-study data are covered by an industrial NDA and not public; no access bypass or contact was performed.

verification.json records hash checks, exact-byte data replay, preservation of baseline tracked files, scope/requirements review and limits. It does not certify model performance, cross-dataset replication, novelty or corpus completeness.
