# G1-R2 recovered post-run auditor self-review

Reviewed committed implementation: `bf093c4ebafe8648693834bd3f86c76853f2c615`.

Verdict: `PASS_RECOVERED_POSTRUN_AUDIT_FOR_EXTERNAL_REVIEW`

This exact-commit review covers the recovered-cache lineage contract, the
accepted continuation review seal, immutable cache provenance, and the full
future primitive-artifact scientific audit path. The ordinary Stage-C
`phase_g1_postrun_audit.py` was not called at its top-level `audit()` entry
point; only its pure recomputation helpers are referenced by the recovered
orchestration.

Checks passed:

- Recovered execution requires the original pre-label seal
  `5622376087aaa97249ff9a055f201b250efbf1c2` and an explicit continuation
  execution seal.
- The continuation review is bound to reviewed implementation
  `25a67addabf2de30c706824e47e8e280c2ab4ff3`, with exact hashes for all four
  reviewed executables. Current, reviewed-implementation, and execution-seal
  bytes were compared.
- The continuation code hash is checked separately from the accepted
  reporting-patch `phase_g1_run.py` hash.
- The five accepted cache/provenance artifacts and the quarantined ledger are
  checked by exact SHA256; cache use is required to be read-only and
  `PASS_CACHE_REUSABLE`.
- The protected scientific-file set and `duration_severity_matching.status ==
  RESOLVED` are checked before future result recomputation.
- The future recovered audit independently replays scaler/probe primitives,
  validation-C selection, test predictions, source/scenario AP, all four
  effects, bootstrap, sign-flip, Holm correction, robustness, semantic
  non-identifiability, and H2/H3a/H3b Boolean consequences.

Adversarial fixture tests rejected invalid lineage, hash, authorization,
prediction, statistic, and decision mutations. The 12 new recovered-auditor
tests, 13 continuation tests, and 37 original Phase-G1 adversarial tests all
passed; Python compilation passed.

No real recovered G1 output exists at this review boundary. No primary-cache
arrays, labels, probe fits, AP/AUROC, bootstrap, sign-flip, Holm, H2, or H3a
result was read or computed. The 118 GB cache remains untouched.

The implementation commit contains only the recovered auditor and its tests;
this report is deliberately committed separately as the report-only execution
review seal.
