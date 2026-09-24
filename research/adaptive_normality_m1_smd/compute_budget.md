# M1-A compute budget

## Existing timing evidence

The estimate uses committed R0 training records on NVIDIA GB10, not a new benchmark run:

- xLSTM reconstruction median training time: 2,235.9 seconds per machine/seed (50 epochs).
- Auditable matched-LSTM median: 1,121.5 seconds per machine/seed.
- R0 extraction medians were about 64.8 seconds for xLSTM and 35.2 seconds for LSTM per test stream of roughly 23,000 points at W=64.
- R0 used W=64 and an 80% training fit block. M1 uses W=256 and a 70% fit block.
- R0 run records used the GB10 environment with PyTorch 2.13.0+cu130, CUDA 13.0, xlstm 2.0.5, Python 3.12.3, four Torch threads, and deterministic cuDNN settings.

These are observed R0 source-native reconstruction/LSTM timings. They are not direct measurements of the new xLSTMAD-F implementation.

## Stage 1 estimate

Stage 1 has three learned arms on all 28 machines at one seed: xLSTMAD-R, matched LSTM-F, and xLSTMAD-F. A conservative per-fit scaling uses the context ratio 256/64 = 4 and fit-window ratio 70/80 = 0.875. This ignores the xLSTM-F one-step output savings and treats it as R0-like recurrent sequence work.

| Arm | R0 timing base | Estimated seconds per machine | 28-machine hours |
|---|---:|---:|---:|
| xLSTMAD-R | 2,235.9 s | 7,825 s | 60.9 h |
| xLSTMAD-F | 2,235.9 s | 7,825 s upper envelope | 60.9 h |
| capacity-matched LSTM-F | 1,121.5 s | 3,925 s | 30.5 h |
| Total learned training | — | — | 152.3 GB10-h |

Planning envelope: add 25% for validation, checkpoint I/O, startup, run-record generation, and timing/model mismatch: approximately 190 GB10-h for Stage 1 on one GB10. This is roughly eight continuous days on a single accelerator. Inference, data staging, and any implementation debugging may raise wall-clock cost.

The xLSTM-F model predicts one point, so its output head/decoder work per batch may be lower than the reconstruction path. The estimate does not credit that saving. Conversely, the estimate may be low if W=256 makes the backend memory-bound or if the historical forecast architecture is slower than the R0 reconstruction model.

Cheap baselines (last value, moving median, ridge VAR(1)), scaling, ACF audit, and metrics are CPU-scale compared with the neural fits; their exact runtime is not separately forecast because it is not an execution bottleneck.

## Stage 2 trigger and estimate

Stage 2 is mechanically unlocked only if every Stage-1 criterion in protocol.md passes. It adds seeds 22 and 33 for all three learned arms on all 28 machines, without changing configuration. The estimate is approximately 380 GB10-h incremental including the same 25% planning allowance, yielding roughly 570 GB10-h total for both stages. Stage 2 is not authorized or started by this protocol.

## Compute-aware stop

Do not begin the learned Stage-1 fits unless:
- a GB10 allocation of approximately 190 hours is scheduled or explicitly accepted;
- the M1-only data/model/score implementation passes the non-training preflight in preflight.md;
- all 28 input manifests and environment/package pins verify;
- the no-label feature-sealing order is implemented.

If resources are not available, record the experiment as not started. Do not silently reduce the number of machines, context length, epochs, seeds, or arms to fit an allocation.
