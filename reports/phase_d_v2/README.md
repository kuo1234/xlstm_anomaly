# Phase D v2 — backend-state repair

Pre-outcome amendment: `a40634b`. Scientific design remains
[the original prospective protocol](../phase_d/prospective.md).
Only accepted backend execution state is restored; deterministic algorithms
remain disabled. See [backend seal](backend_seal.json).

Pre-grid status: all four gates PASS bitwise. See
[gate results](pre_grid_gates.json), [native parity](operator_parity.json),
[sealed state reuse](reuse_verification.json) and
[unchanged implementation/statistics checks](implementation_integrity.json).
Three update and three zero-update arms ran in distinct fresh processes;
the separate label-permuted arm produced identical algorithm behavior.
The native buffer/order and next score segment were independently reconstructed
from the official dataset. Full arrays/checkpoints have artifact hashes in gates/.

Five existing backbones, scalers, calibration arrays/thresholds, SANA/optimizer/RNG
states and all 160 buffer layouts passed integrity checks. No retraining.
Conservative grid forecast: 5,588.723 seconds plus generation/startup/canary overhead,
within the 24-hour gate. These pre-grid records are committed/pushed before launch.

No corrected full-grid outcome has yet been generated at this checkpoint.
All 498 v1 rows remain permanently quarantined and excluded from inference.
The v1 report seal was checked by file digests only, not by parsing outcomes.
No later phase is authorized or executed.
