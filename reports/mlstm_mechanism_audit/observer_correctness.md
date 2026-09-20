# mLSTM observer correctness

The observer is read-only.  It captures q/k/v at the two native mLSTM cells,
replays C/n/m/h from zero state, and summarizes detached tensors.  It does not
modify parameters, recurrent state, model output, or the reconstruction loss.

Checks executed by `mlstm_inference_canary.py` include:

* finite state/features and expected `[B,64,18]`/`[B,18]` shapes;
* native-vs-replayed normalized hidden parity;
* observer ON/OFF reconstruction output and score invariance;
* B=1/B=8/B=128 batch behavior;
* duplicate-window reset invariance;
* batch permutation invariance;
* prefix causality;
* vanilla-vs-CUDA output/score/sLSTM/mLSTM parity.

The exact errors and failed-element counts are in
`reports/mlstm_mechanism_audit/inference_parity.json`.  No independent native
C/n/m history exists in the pinned parallel implementation, so the
replayed-state equivalence is established against the native normalized hidden
output and recurrence semantics, not against an unavailable second C/n/m
implementation.  That limitation is retained explicitly.

The observation-identical/opposite-semantic control is recorded in
`semantic_control.json`: observations are byte-identical while evaluator labels
differ, and score, sLSTM base, and mLSTM base tensors are exactly identical.
