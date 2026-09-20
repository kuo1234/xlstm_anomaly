# Current research status (2026-09)

This document is a compact status snapshot for the consolidated repository.
It does not replace the pre-G1 framing or the frozen protocol.

## Authoritative G1 result

- H2: **GO**, mean ΔAP = `+0.14251889179304736`.
- H3a: **STOP** under the frozen common-capacity comparison.
- H3b: **LOCKED** under the frozen protocol.

The original G1 artifacts and decision rules are unchanged.

## Post-G1 engineering evidence

- The DGX Spark/GB10 CUDA path is usable with the validated SM121/CUDA 13
  compatibility overlay. The CUDA investigation documents the
  `static-global-template-stub` linkage issue and its scoped workaround.
- FastObserver captures native sLSTM states instead of replaying a duplicate
  scalar recurrence. Trained-checkpoint parity passed, with roughly 4.7x
  bounded extraction speedup.
- CUDA training was substantially faster in the bounded canary (about 5.3x),
  but vanilla and CUDA training trajectories are not interchangeable. This is
  an engineering result, not a new scientific checkpoint or G1 result.

## Exploratory mLSTM evidence

The frozen seed-11 dense W64 audit found an exploratory mLSTM-layer signal:

- `M_full | H ≈ +0.145661 AP`
- `M_full | H+S ≈ +0.016657 AP`
- `ΔC_history ≈ -0.000592`
- `ΔC_given_sLSTM ≈ +0.006610`

The current classification is **DENSE_MLSTM_SIGNAL_NOT_MATRIX_SPECIFIC**:
the mLSTM state summary carries information in this exploratory screen, but the
evidence does not isolate matrix-memory `C` as its main source.

## Claim boundaries and next questions

These results do not establish online safe adaptation, contamination
robustness, a global xLSTM-over-LSTM advantage, long-context superiority, or
persistent cross-window memory. Immediate unresolved questions are a standalone
LSTM H2 comparison, a stronger observable/residual baseline, and multi-seed
dense mLSTM replication.

`research/framing-2026-09` is a pre-G1 Claude Science framing snapshot and
intentionally remains on a separate branch for later reconciliation.
