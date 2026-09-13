# Phase F-v3 implementation stop

Status: **STOP_IMPLEMENTATION_VALIDITY**

The fixed F-v3 grid was stopped fail-closed after `lstm_33` failed the
per-epoch random-unlabeled B128-vs-B1 canary.  The failure occurred at the
canary after epoch 28 (there is no epoch-29 curve row because the canary raises
before the row is written).  The traceback in `logs/lstm_33.log` identifies the
failed check as `raw_output`; the frozen canary uses
`torch.allclose(atol=1e-5, rtol=1e-4)`.  The runner exited with code 1 after
770.1265053749084 seconds.  The launcher then terminated the concurrently
running `xlstm_11`, as required by the fixed fail-fast queue.

This is an implementation-validity stop, not a detector or scientific
hypothesis result.  No anomaly labels, test sources, anomaly AP/AUROC,
probes, H2/H3 features, H4, or natural-H1 analysis were accessed.  The failed
canary is a random unlabeled execution invariant only.  No tolerance,
backend, architecture, optimizer, data, seed, or checkpoint-selection rule
was changed in response.

## Run disposition

| run | disposition | evidence |
|---|---|---|
| `lstm_11` | PASS, complete, post-training parity PASS | `runs/lstm_11/manifest.json`, `post_training_parity.json` |
| `lstm_22` | PASS, complete, post-training parity PASS | `runs/lstm_22/manifest.json`, `post_training_parity.json` |
| `lstm_33` | QUARANTINED partial; epochs 1--28 canary PASS, epoch-29 raw-output canary FAIL | `logs/lstm_33.log`, `runs/lstm_33/curves.json` |
| `xlstm_11` | QUARANTINED partial; epochs 1--20 canary PASS, launcher-terminated before completion | `logs/xlstm_11.log`, `runs/xlstm_11/curves.json` |
| `xlstm_22`, `xlstm_33`, `lstm_44`, `xlstm_44`, `xlstm_55`, `lstm_55` | NOT STARTED | fixed launcher queue |

The two completed LSTM runs are valid implementation evidence for their fixed
seeds, but they do not unlock Phase G and cannot be treated as a ten-run
replication.  All partial checkpoint artifacts are retained solely for
provenance and are ineligible for reuse or scientific estimation.

## Immutable scope retained

F-v3 still refers to the improved official xLSTMAD implementation
`e8b56ba27352733bb83729e85b1d6196dca70c99`, `xlstm==2.0.5`, `lightning==2.6.1`,
vanilla float32 xLSTM, H38 matched LSTM, W64, batch 128, Adam `lr=0.001`, 50
epochs, sealed train/validation prefixes and orders, detector seeds
`{11,22,33,44,55}`, and the scoped matched-LSTM cuDNN-disabled execution.
The F-v2 artifacts and the quarantined F-v1/v2 grids remain immutable.

H1 reporting remains `controlled_harm=STOP`, `natural_harm=NOT_RUN`,
`overall=UNRESOLVED`; this Phase F stop does not change those results.

## Next authorization

Phase G, labeled extraction, probe fitting, matched-LSTM/xLSTM comparisons,
H3b, H4, and all anomaly-performance claims remain **LOCKED** pending external
review and a separately approved implementation amendment.  A rerun may not
reuse any F-v3 partial or completed weights unless a future protocol explicitly
authorizes it; the current prospective protocol requires fresh initialization.

