# xLSTMAD-F implementation audit

## Audit scope

This is a static architecture and source inspection. No model forward pass, training step, optimizer step, detector score, or GPU experiment was run. The inspected local official xLSTMAD checkout used by R0 is the improved reconstruction implementation at commit e8b56ba27352733bb83729e85b1d6196dca70c99, with xlstm 2.0.5. The original forecasting implementation is preserved in the official repository history at commit 3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6.

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

Faithfulness is conditional on reproducing the documented historical forecast path while applying the M1 transform and p=1 protocol. The historical training code's per-window normalization must be disabled, score padding removed, and output timestamp aligned to the future endpoint. The exact target and alignment above are mandatory parity conditions for a future implementation.

## M1-only code that must be added for execution

A separate M1 module/runner must be added after this protocol review and before an authorized training execution. It should contain:
- a forecaster builder ported from the historical xLSTMAD-F path;
- a capacity-matched LSTM with the same input/output contract;
- a dataset/window builder with explicit input and target indices;
- the frozen robust scaler implementation in a separate M1 data utility;
- score extraction that predicts before target exposure, applies common warm-up and endpoint alignment, and saves output hashes before labels are opened.

Do not edit real_data_r0_models.py, real_data_r0_data.py, or any R0 history. Do not represent the new code as already implemented. A future implementation review must compare module names, parameter counts, shapes, target indices, and normalization behavior to this audit before Stage 1 is allowed to start.

## Audit conclusion

Existing local code can faithfully run the xLSTMAD-R reconstruction baseline. It cannot implement xLSTMAD-F by a loss-only change. A faithful one-step forecaster is specified by the official historical formulation and requires an isolated M1-only port. This is a known implementation task, not an unresolved scientific configuration choice.
