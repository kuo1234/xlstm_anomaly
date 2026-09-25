# xLSTMAD-F implementation audit

## Audit scope

The historical/source description below is a static architecture audit. The
implementation preflight later added a synthetic CPU forward parity check and
an engineering-only GB10 canary; no 28-machine Stage-1 detector result, test
label read, anomaly metric, or scientific detector result exists. The local
official xLSTMAD checkout used by R0 is the improved reconstruction
implementation at commit e8b56ba27352733bb83729e85b1d6196dca70c99, with
xlstm 2.0.5. The original forecasting implementation is preserved in the
official repository history at commit 3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6.

References:
- xLSTMAD paper: https://arxiv.org/abs/2506.22837
- improved official repository: https://github.com/Nyderx/xlstmad
- original forecast model source: https://github.com/Nyderx/xlstmad/blob/3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6/models/xlstmad_pred.py
- original forecast dataset source: https://github.com/Nyderx/xlstmad/blob/3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6/models/forecast_dataset.py

## Current local reconstruction path

The improved checkout constructs an embedding from each complete input window, runs its encoder to obtain an aligned sequence, sends that aligned sequence through its decoder, and projects every decoder position back to the observation dimension. Its objective is same-window MSE. Its anomaly score averages squared reconstruction residual over the window and channels.

The R0 wrapper uses W=64 and a trailing-window score. The reconstruction decoder sees the observation that contributes to the score. This is a causal reconstruction score because no future point is used, but it is not a forecast of that observation. The implementation does not offer a flag that turns it into a future predictor. Changing only the loss target or shifting the dataset target would leave the decoder consuming the aligned input sequence and would therefore not implement a valid causal forecaster.

The current improved public implementation focuses on reconstruction; the original forecasting implementation exists in the earlier official code history. Do not infer xLSTMAD-F architecture by editing the current reconstruction model in place.

## Original xLSTMAD-F formulation

The historical forecasting data wrapper makes an input sequence from rows [i, i+W) and a future target from [i+W, i+W+p). It also applies its own per-window normalization. For M1, use the already-frozen train-fit transform and disable this second normalization; otherwise target scale and scoring semantics would differ from the other arms.

The forecast model:
1. embeds and encodes the context window;
2. initializes the decoder from the final encoder latent;
3. advances the decoder recurrently for the requested prediction length;
4. projects decoder latents through GELU and a linear output head to channel space.

For the published multi-step path, decoder latents are advanced autoregressively, but predicted observation values are not fed back as decoder inputs. This distinction should be retained in the faithful port. M1 sets p=1, so it evaluates only the direct one-step case; it does not test multi-horizon utility.

Training target is future observation MSE over forecast horizon and channels. At each scored M1 target timestamp t the prescribed operation is precisely:

past window z[t-W:t] -> model prediction p[t] -> expose observation z[t] to the scoring path -> mean-channel squared error between p[t] and z[t].

The prediction must be materialized before the target is passed to the model or baseline. Every test timestamp starts from a fresh W-sample context and fresh recurrent state. There is no online state carry, target feedback, or cross-window memory.

The original code pads initial forecast-score timestamps with the first available score. M1 must not use that padding: first W test samples are a common warm-up and excluded. Score each forecast at its actual endpoint.

## Faithfulness and parameter audit

A static CPU constructor/count audit used the official xLSTM package version and M1 dimensions D=38, embedding width 40, three encoder and three decoder blocks, slstm_at=[1], and vanilla sLSTM backend. It reports 80,510 trainable parameters. The count is independent of context length. This constructor audit did not execute forward, train, score, or touch a GPU.

The M1-only capacity-matched LSTM has 81,838 parameters (1.65% above xLSTMAD-F), within the frozen ±10% criterion. The current xLSTMAD-R reconstruction arm has 75,934 parameters at D=38 and embedding width 40. Counts and the frozen model definitions are recorded in baseline_spec.md.

The M1-only implementation in `scripts/adaptive_normality_m1_models.py` ports
the historical xLSTMModel p=1 path. It retains the 3-block encoder and decoder,
E=40, the final encoder latent as a one-token decoder input, GELU, and the
D-channel output projection. The port uses the required vanilla sLSTM backend
and float32 configuration, disables per-window normalization, resets state for
independent windows, and omits historical score padding. A CPU parity test
loads the historical class from the pinned official Git object, loads the same
state dict into both implementations, and confirms exact synthetic forward
parity. Synthetic index tests confirm `[t-256,t)` -> `t`, target access after
prediction, and common unpadded test endpoints beginning at 256.

The measured GB10 canary ran one training epoch per arm on three machines
selected by train lengths only. Those fit/validation-only engineering runs
measured throughput; they did not load test observations or labels or create
anomaly scores. The canary is not a detector result.

## M1-only implementation inventory

The isolated implementation and tests have been added in M1-only source files:

- `scripts/adaptive_normality_m1_data.py`: pinned observation loader, block
  boundaries, robust transform, and lazy forecasting/reconstruction datasets;
- `scripts/adaptive_normality_m1_models.py`: official xLSTMAD-R adapter,
  historical xLSTMAD-F p=1 port, and capacity-matched LSTM-F;
- `scripts/adaptive_normality_m1_execute.py`: fit/validation, causal score
  materialization, calibration, persistent run records, and future runner;
- `scripts/adaptive_normality_m1_scores.py`: native/endpoint reconstruction,
  controls, fixed fusion, immutable score inventory and seals;
- `scripts/adaptive_normality_m1_metrics.py`: metric-only entry point that
  verifies committed/sealed Stage-1 inventory before its label-loader window.

The machine-readable implementation preflight and test suite verify these
contracts before any full Stage-1 run.

The M1 implementation is isolated from `real_data_r0_models.py`,
`real_data_r0_data.py`, and all R0 scientific-result modules. A final
result-blind review must confirm the source parity, parameter counts, shapes,
target indices, and normalization behavior before Stage 1 can start.

## Audit conclusion

The historical xLSTMAD-F port passed exact synthetic forward parity for p=1,
under the frozen M1 backend/precision overlay. A loss shift to the current
reconstruction model would not satisfy that audit and was not used. The
machine-readable preflight passed and the independent review returned
`M1_IMPLEMENTATION_RESULT_BLIND_PASS`; the canary is engineering evidence
only, and the full Stage-1 detector experiment has not started.
