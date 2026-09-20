# Observer and extraction correctness

The observer receives only scaled observation windows. It has no argument for
labels, regime identity, event age/end, severity, condition, or generator
metadata. Evaluator rows are reconstructed offline only after each stream's
observation extraction returns.

The frozen observer contracts retained here are independent-window zero-state
reset, finite states/features, parameter/state non-mutation, batch
permutation/reset invariance, and observer-on/off reconstruction invariance.
The B128/B256 bounded canary used the same checkpoint and observations and
reported allclose for output, reconstruction score, sLSTM base18, and mLSTM
base18 with `atol=1e-5`, `rtol=1e-4`.

The dense cache has 500 files, each with exactly 21,441 timestamps (`63..21503`)
and the named observation-only arrays. The manifest records `labels_in_cache:
false`; all arrays are finite float32 except int64 timestamps. No separate
inference was performed for sparse versus dense analyses.
