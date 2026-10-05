# Score fragmentation / continuity — evidence status

**Detector raw continuity, alarm run lengths, dropouts and fragment counts are NOT_MEASURED.** The original paper’s LSTM spikes are prior-art evidence, not a new reproduction. Raw telemetry gaps/duplicates are input quality observations, not detector fragmentation.

Original AE enclosing-window averaging, its constant-window tail readout,15s feature/label bins and DIVAD EWMA/warmup masks alter time continuity. The no-model source fixture shows readout behavior without assigning any actual score/AP/AD2/AD3/AD4 gap to it. Do not call a suspected artifact dominant.

Native range/early/exactly-once performance and raw continuity need the same scored trace/split and normal-only threshold. Phase-specific fragments must exclude unresolved overlap/availability and report missing support. TEMPORAL_FRAGMENTATION_DOMINANT is unavailable from aggregate F1 or absent raw outputs.

Generic score spikes, smoothing, voting and range continuity are ALREADY_EXPLICIT. No smoothing method, range objective or xLSTM benefit is proposed.
