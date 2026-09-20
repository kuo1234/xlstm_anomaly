# mLSTM mechanism-audit architecture review

This is an inference-only audit of the frozen vanilla-trained seed-11 xLSTMAD
checkpoint.  It is not H3b, does not reopen H3b, and does not change any Phase
F/G artifact.

Pinned implementation: improved official `Nyderx/xlstmad`, commit
`e8b56ba27352733bb83729e85b1d6196dca70c99`, with `xlstm==2.0.5` and
`lightning==2.6.1`.

The instantiated model has three encoder and three decoder blocks.  Blocks 0
and 1 use sLSTM; block 2 uses mLSTM.  The actual mLSTM cells are:

* `encoder.blocks.2.xlstm.mlstm_cell`
* `decoder.blocks.2.xlstm.mlstm_cell`

Each mLSTM cell has inner embedding 80, four recurrent heads, and head width
20.  The q/k/v projections use 16 projection heads.  The decoder is a full
window decoder; it is not the invalid singleton decoder path found in v1.
Each independent W=64 window starts with a fresh recurrent state.

The CUDA comparison uses the existing SM121 compatibility overlay and the
validated vanilla-to-CUDA recurrent-layout adapter.  No weights are retrained
or overwritten.

The mLSTM cell's normal parallel path returns normalized hidden output only.
It does not expose C/n/m history.  The audit therefore captures q/k/v at the
native cell hook and replays the pinned recurrence read-only to obtain compact
state summaries.  The replay is not a replacement cell and is not used for
model output.
