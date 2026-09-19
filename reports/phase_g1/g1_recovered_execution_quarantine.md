# Recovered Phase-G1 execution quarantine

The recovered continuation completed under seal `069cdd227e26c1c4e3633bc6088b31fd71a3ae92`, but the independent recovered post-run audit returned `STOP_RESULT_UNRESOLVED`.

Blocking discrepancy: the execution manifest contains the continuation-ledger hash from before the final `continuation_complete` event was appended. The current ledger therefore has a different SHA256. The scientific output directory is preserved at `reports/phase_g1_recovered_execution_v1/` and is not authoritative.

No H2/H3a result is interpreted. No repair, rerun, cache mutation, or executable/config change is authorized by this record.
