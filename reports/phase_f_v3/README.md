# Phase F-v3 prospective scope

This directory contains the pre-outcome F-v3 amendment. The diagnostic that
qualifies it is recorded under
[Phase F-v2](../phase_f_v2/spark_cudnn_diagnostic.json): condition A (cuDNN
enabled) fails the known trained LSTM partition gate; condition B (cuDNN
disabled only inside matched LSTM execution) passes every original gate.

The complete config and rationale are in
[prospective.md](prospective.md). F-v3 has not yet run its gates or training;
this file must be committed and pushed before any optimizer step. No F-v2
quarantined weights are eligible for reuse.
