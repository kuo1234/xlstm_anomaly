# Phase F-v4

This directory records the pre-outcome raw-output validity-contract amendment
and its versioned execution artifacts.  F3 remains immutable evidence.  See
[prospective.md](prospective.md) for the frozen scope and
[carry_forward.json](carry_forward.json) for the two eligible carried runs.

The complete validity run is sealed in [final_manifest.json](final_manifest.json)
and [SHA256SUMS](SHA256SUMS). Eight fresh runs completed the fixed 50 epochs and
passed all hard score/common18/recurrent/reference/observer/reset/prefix and
finite/shape gates. `lstm_11` and `lstm_22` are reference-only carry-forwards;
their F3 checkpoints were neither copied nor retrained. Raw reconstruction
partition allclose is retained as a diagnostic, including the known projection
numeric drift, and is not a stop criterion. No anomaly labels, test sources,
probe fitting, or anomaly metrics were used. Phase G remains locked pending
external review.
