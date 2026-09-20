# Trained-checkpoint inference parity

Checkpoint: `data/phase_f_v4/runs/xlstm_11/best.pt`, epoch 50, SHA256
`4729a3ba385b285078aa987fce176e61fd382715c5357fc92f2635a929a0ae41`.

The fixed observation fixture contains stationary, abrupt, gradual, recurring,
correlation, and anomaly-containing windows.  The extractor received only
scaled observation windows.  Vanilla and CUDA used the same checkpoint and
the validated recurrent layout adapter.  Tolerance is `atol=1e-5,
rtol=1e-4`.

The machine-readable measurements are in `inference_parity.json`.  B=1, 8,
and 128 all pass for reconstruction output, score, existing sLSTM common18,
and compact mLSTM base18.  The captured mLSTM replay hidden, after the native
cell output normalization, also matches the native mLSTM output at all tested
batches.  Observer ON/OFF output and score are identical; duplicated windows
reset independently; batch permutation is invariant; and changing the future
half of a window does not alter the causal first 32 output steps.

This is inference equivalence only.  It makes no claim about the previously
failed CUDA training-trajectory equivalence.
