# Phase F-v4 validity-contract amendment (pre-outcome)

This amendment is committed before any F-v4 optimizer step.  It changes only
the validity classification of raw reconstruction tensors; it does not change
the detector architecture, initialization, backend, data/scalers/orders,
optimizer, epochs, checkpoint selection, detector seeds, tolerances, or H2/H3
rules.  The reason is the accepted F3-R diagnosis: seed33 epoch29 had one
raw-output B128/B1 element outside the frozen allclose rule after every
recurrent stage, GELU, score, common18, observer/reference, reset, and prefix
check passed.

## Frozen execution

F-v4 inherits the improved official xLSTMAD implementation
`e8b56ba27352733bb83729e85b1d6196dca70c99` (`xlstm==2.0.5`,
`lightning==2.6.1`), vanilla float32 xLSTM, H38 six-layer matched LSTM,
W64/B128, Adam `lr=0.001`, 50 full epochs, sealed train sources 1000--1009,
validation sources 2000--2004, sealed per-source scalers/orders, and detector
seeds `{11,22,33,44,55}`.  Matched `nn.LSTM` calls retain the scoped cuDNN-
disabled execution from F-v3.  Backend flags and `atol=1e-5, rtol=1e-4` are
unchanged.

## Hard validity gates

The following remain fail-closed for every epoch and post-training checkpoint:

- reconstruction-score batch partition/permutation;
- common18 batch partition/permutation;
- manual/native recurrent sequence-h, final-h, final-c, finite-state and
  input/forget gate-range checks for all six real LSTM layers;
- same-batch observer OFF/ON output and score parity;
- reset and prefix causality;
- output/feature finite values and expected shapes;
- no native `predict_step`; no labels, test sources, or probe fitting.

All hard comparisons use the unchanged `torch.allclose(atol=1e-5,
rtol=1e-4)` semantics, with bitwise checks retained where already frozen.

## Raw-output diagnostics

Raw `[B,W,D]` reconstruction output partition allclose is diagnostic-only.  It
is still logged at every epoch and post-training for B128 vs B1 and B128 vs B3
with `torch.allclose`, bitwise flag, max absolute error, mean absolute error,
failed-element count, total element count, shape, and finite/shape status.
Raw output remains a hard finite/shape requirement.  Same-batch observer
OFF/ON output/score parity remains hard.  This policy is symmetric for xLSTM
and matched LSTM and never changes optimization or checkpoint selection.

## Run disposition

The existing sealed F3 `lstm_11` and `lstm_22` runs are carried forward by
reference, without copying or retraining: both completed 50 epochs and passed
the stricter F3 post-training validity contract.  Their original checkpoint
paths and SHA256 hashes are recorded in `carry_forward.json`.

Fresh F4 initialization is required for `lstm_33`, `lstm_44`, `lstm_55` and
`xlstm_11`, `xlstm_22`, `xlstm_33`, `xlstm_44`, `xlstm_55`.  The F3 partial or
replay states for `lstm_33` and `xlstm_11` are quarantined and forbidden.
Every fresh run uses the existing sealed initialization/data/orders and a
separate F4 data/report path.  Any hard-gate failure stops the entire queue.

F4 PASS requires all ten entries (two carried plus eight fresh) to have
complete 50-epoch traces, valid checkpoint selection, hard score/common18/
recurrent/reference/observer/reset/prefix/finite checks, and sealed manifests
and hashes.  Raw-output partition statistics are transparency diagnostics and
cannot alone stop a run unless finite/shape validity fails.

No anomaly AP/AUROC, test source, H2/H3 labels, probe fitting, H3b, H4, or
natural-H1 analysis is authorized by this amendment.  Phase G remains locked
until external review of all ten sealed F4 entries.

