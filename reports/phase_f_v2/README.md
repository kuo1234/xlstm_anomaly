# Phase F-v2 — STOP_IMPLEMENTATION_VALIDITY

F-v2 was amended and pushed as `1b5256c` before any scientific optimizer step.
The pre-training gates were sealed as `9edbf0f` and passed under
`torch.backends.cudnn.allow_tf32=False`; the E2 seed-11 TF32-on/off comparison
also passed at the unchanged `atol=1e-5, rtol=1e-4`. E2 and F-v1 reports remain
immutable.

The fixed ten-condition grid was then started. LSTM seed-11 completed its
prescribed 50 epochs, but its best checkpoint failed the mandatory post-training
batch-partition validity check: B128 versus B1 output differed by
`2.9087067e-5`, above the frozen tolerance. Its manual six-layer h/c/i/f replay,
finite states, reset, prefix causality and score partition checks passed; this
does not waive the output check. The launcher fail-closed terminated the partial
xLSTM seed-11 process and did not start seeds 22/33/44/55. xLSTM had reached
epoch 2 (its partial checkpoint is also quarantined).

All generated artifacts are permanently quarantined in
[quarantine.json](quarantine.json). The LSTM run includes all 50 train/validation
MSE rows and initial/final/best checkpoint hash references; the xLSTM run has
only a partial epoch-1 curve/checkpoint. They are implementation-audit evidence,
not valid scientific checkpoints and are excluded from every estimate or future
probe. No rerun, tolerance relaxation, backend switch, or outcome-based tuning
was performed.

No anomaly labels, test sources, anomaly AP/AUROC, H2/H3 feature extraction,
probe scaling/fitting, H3b, H4, natural-H1 harm, rollback or learned gate was
run. H1 controlled harm remains STOP, natural harm NOT_RUN, and overall H1 is
UNRESOLVED. Phase G is locked pending external direction on the implementation
failure.

Details: [status.json](status.json), [execution.json](execution.json),
[mechanical_gates.json](mechanical_gates.json), [cross_backend.json](cross_backend.json),
and per-run manifests under [runs](runs). Hashes are in [SHA256SUMS](SHA256SUMS).
