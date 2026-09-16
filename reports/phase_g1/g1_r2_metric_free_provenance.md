# G1-R2 metric-free provenance report

The recovered auditor review at implementation commit
`bf093c4ebafe8648693834bd3f86c76853f2c615` rehashed the accepted cache and
lineage metadata only. It did not open any primary-cache array, join labels,
fit a probe, compute AP/AUROC, or start continuation.

`g1_cache_audit_v1.json` remains `PASS_CACHE_REUSABLE`; the quarantined cache
is read-only and unchanged. The accepted cache audit, inventory, incident,
reporting authorization, reporting-patch audit, and quarantined execution
ledger matched their sealed SHA256 values. The protected scientific-file set
and resolved duration/severity protocol also matched their sealed hashes.

No recovered G1 result manifest exists at this boundary. This report is
provenance evidence only, not a scientific outcome.
