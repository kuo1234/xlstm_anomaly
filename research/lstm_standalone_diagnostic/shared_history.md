# Shared-CANDI-history diagnostic

The desired secondary contrast is:

```text
Delta_L_shared =
  AP(CANDI history + LSTM internal) - AP(CANDI history)
```

The committed G1 result summary preserves H3a-C as a difference of xLSTM and
LSTM shared-CANDI increments, but it does not preserve the two component LSTM
AP arrays needed to separate `Delta_L_shared`. The recovered-cache payload and
large per-arm artifacts are not part of the consolidated repository.

Therefore this analysis is explicitly:

```text
NOT_RECOVERABLE_FROM_CONSOLIDATED_ARTIFACTS
```

No checkpoint loading, probe refit, inference, or cache access was used to
recreate it. This limitation does not weaken the standalone `Delta_L_own`
algebraic reconstruction.
