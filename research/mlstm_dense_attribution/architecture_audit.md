# Architecture and state audit

The frozen model is the improved official xLSTMAD implementation pinned at
`e8b56ba27352733bb83729e85b1d6196dca70c99` (`xlstm==2.0.5`). It has three
encoder and three decoder blocks. In each stack blocks 0 and 1 are sLSTM and
block 2 is mLSTM. The two observed cells are exactly:

* `encoder.blocks.2.xlstm.mlstm_cell`
* `decoder.blocks.2.xlstm.mlstm_cell`

Each mLSTM has four heads, inner embedding 80, and head dimension 20. The
parallel native implementation exposes normalized hidden output, but not a
history of C/n/m. The existing read-only observer captures q/k/v at each cell
and replays the pinned stabilized recurrence from zero state for summaries.
This is the same validated observer used in the previous mLSTM audit; no model
equation, parameter, reset behavior, or output path was changed.

The dense cache uses the frozen vanilla-trained seed-11 checkpoint through the
validated CUDA recurrent-layout adapter. The bounded B128/B256 canary passed
for output, score, sLSTM base18, and mLSTM base18 at the existing numerical
contract before the cache was generated.
