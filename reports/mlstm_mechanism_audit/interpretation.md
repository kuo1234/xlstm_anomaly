# Scientific interpretation boundary

The frozen checkpoints and observer support the following limited result:

* mLSTM compact state summaries add substantial exploratory information beyond
  score/history on the fixed W=64 reset screen (`M|H` mean +0.1531 across
  seeds 11/22/33, positive in every seed and scenario).
* Adding mLSTM summaries after the existing sLSTM summaries is positive in all
  three pooled seeds (`M|H+S` mean +0.0181), but the increment is not uniform:
  correlation is negative for seeds 22 and 33 and duration strata are
  heterogeneous.  This is evidence worth replication, not an established
  xLSTM-specific superiority claim.

The result does not prove safe adaptation, contamination robustness, deployment
improvement, persistent cross-window memory, long-context superiority, or
causality of matrix memory.  It also does not alter the earlier H3a STOP and
does not satisfy or reopen H3b.  The observer's C/n/m histories are a
read-only replay because the pinned parallel implementation exposes no native
history; only normalized hidden output supplied an independent native parity
target.
