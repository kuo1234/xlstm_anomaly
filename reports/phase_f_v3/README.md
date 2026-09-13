# Phase F-v3 prospective scope

This directory contains the pre-outcome F-v3 amendment. The diagnostic that
qualifies it is recorded under
[Phase F-v2](../phase_f_v2/spark_cudnn_diagnostic.json): condition A (cuDNN
enabled) fails the known trained LSTM partition gate; condition B (cuDNN
disabled only inside matched LSTM execution) passes every original gate.

The complete config and rationale are in
[prospective.md](prospective.md). The prospective amendment and mechanical
gates were committed before any optimizer step. The subsequent fixed grid was
fail-fast stopped when `lstm_33` failed the epoch canary; see
[stop_decision.md](stop_decision.md) and [stop_summary.json](stop_summary.json).
No F-v2 quarantined weights were eligible for reuse, and the incomplete F-v3
artifacts are not Phase G evidence.
