# M1-A detector and baseline specification

All inputs use the frozen per-machine robust transform and W=256 context. The dataset split, timestamp convention, train budget, and score eligibility are in protocol.md. Scores are evaluated at the current timestamp; no detector sees future values.

## Cheap causal controls

### 1. Last-value predictor

For each t, predict z_t by z_(t-1). Score:

s_last(t) = mean over channels of (z_t - z_(t-1))^2.

This is exactly the squared first-difference score. It is counted once, not presented as an independent winning arm.

### 2. Robust moving-median predictor

Predict each channel by the coordinate-wise median of the preceding W observations, z_(t-W:t). Score the mean squared residual from z_t. The median uses past values only, and the rolling buffer updates without labels. It has O(WD) naive calculation and O(D) stored values with an order-statistics implementation.

The baseline intentionally updates its past window unconditionally. That exposes whether a simple moving statistic already explains forecast behavior; it is not a safe online adapter.

### 3. Linear AR / VAR(1)

Fit a separate per-machine ridge VAR(1) on the fit block only: current z_t is predicted from an intercept and z_(t-1), with ridge penalty lambda=1 on slope coefficients and no penalty on the intercept. No order search or test-label selection. The score is mean squared residual across 38 channels. It has 1,482 fitted scalar coefficients (38×38 slopes plus 38 intercepts) and negligible inference cost.

## Reconstruction control: native and endpoint scores

### 4. xLSTMAD-R

Use the current improved official xLSTMAD source pinned at e8b56ba27352733bb83729e85b1d6196dca70c99, with D=38, embedding 40, W=256, float32, and vanilla sLSTM backend. Train the aligned window reconstruction objective on fit windows only; select by normal validation reconstruction loss.

At time t, the decoder reconstructs exactly the trailing window `z[t-W+1:t+1]`. Freeze two deterministic scores from that same output:

* `R-native-window = mean_{W,D}((z_window - zhat_window)^2)`. This is the faithful published/native reconstruction behavior. Attach it only to the window’s right edge t; preserve its duration dilution and post-event tail as detector behavior.
* `R-endpoint = mean_D((z_t - zhat_t)^2)`. This is the endpoint-aligned diagnostic reconstruction score, using only the final reconstructed position for original timestamp t. It gives a same-timestamp point-residual comparison to the forecast arms.

Both scores use no future sample, refer to the same t as each forecast score, and are evaluated against point label y_t (not a window-any label). The second score does not change the model, objective, or training.

Trainable parameters: 75,934, matching the audited R0 xLSTM reconstruction model at D=38; context length changes do not add parameters.

## One-step forecasters

### 5. Capacity-matched LSTM

Use an input projection 38→40, three encoder nn.LSTM layers of width 40, three decoder nn.LSTM layers of width 40, GELU, and output projection 40→38. The encoder processes z_(t-W:t); the decoder receives the final encoder representation for one step; project that output to predict z_t. Score mean squared point residual. All hidden state is fresh per window.

Parameter formula for width w and D=38 is 48w² + 125w + 38. At w=40 this is 81,838 parameters, 1.65% above the xLSTMAD-F count below. This is the nearest width in the configured search range and is within the frozen ±10% match criterion.

### 6. xLSTMAD-F-formulation xLSTM

Port the original xLSTMAD forecasting architecture at commit 3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6 into a separate M1 module. Use D=38, embedding 40, W=256, three encoder/decoder xLSTM blocks, and the original forecasting configuration with slstm_at=[1]. Use a supported vanilla sLSTM backend for this audit. The decoder starts from the final encoder output and predicts one future step in latent space; the forecast is projected through GELU and a linear head. Only past context is used.

A CPU-only constructor/count audit with xlstm 2.0.5 gives 80,510 trainable parameters. It executed no model forward, training step, optimizer, or GPU call. The count is independent of W. The capacity-matched LSTM has 81,838 parameters.

The reconstruction and forecast architectures are not interchangeable: R uses the current improved official architecture and aligned full-window decoder; F uses the original forecasting architecture and one-step future target. Keep both in M1-only source files. Do not edit or “convert” real_data_r0_models.py.

## Common training and scoring behavior

All neural models use the same first-70% fit rows, W=256 context, seed, batch size, maximum epochs, Adam learning rate, precision, data transform, validation split, and checkpoint-selection rule. The loss target differs by task: xLSTMAD-R reconstructs its aligned window; both forecasters predict the next point. Train windows never cross the fit boundary. Validation contexts use only observations available before their target timestamp.

For forecasting at t, create the complete prediction from z_(t-W:t) before passing z_t to the scoring path. Then calculate point MSE against z_t. No forecast is recursively fed back as an observed value. The model state resets for every independent window; the only recurrence is within that window and the one-step decoder call.

For xLSTMAD-R at t, provide z_(t-W+1:t+1), compute all W reconstructions, and score their mean squared residual. This is causal but uses the observed target. The score may remain high after an event leaves the window; metrics.md defines the recovery measure.

## Stage-1 control set and comparison intent

The non-forecast score set for comparison and the fixed control-only fusion is last-value, moving median, VAR(1), `R-native-window`, and `R-endpoint`. The forecast-plus-control fusion adds xLSTMAD-F. The standalone comparator is the per-machine **oracle control envelope**: the maximum AP among those five controls. It is explicitly test-label-dependent and is not a deployable detector or one operational baseline.

Last-value / first difference tests whether the neural forecaster does more than local persistence. Moving median tests whether adaptive local location explains gains. VAR(1) tests linear cross-channel forecasting. xLSTMAD-R tests whether future prediction adds value beyond reconstruction. The matched LSTM separates a forecasting effect from an xLSTM-specific effect.
