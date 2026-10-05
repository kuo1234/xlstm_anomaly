# Architecture reality check

2026-10-05; Issue #22. Base repository `60fd1ce`. Independent static inspection of freshly fetched source, not an assumption copied from prior reports. [Code provenance](provenance/code_sources.json) records 40 source hashes, all matching the historical source seals. The PyPI wheel is verified against PyPI's published SHA256. No upstream code is patched.

## Pinned paths and actual behavior

| Path | Inspected behavior | Consequence |
|---|---|---|
| [Improved xLSTMAD e8b56ba, lines 15–36, 80–101](https://github.com/Nyderx/xlstmad/blob/e8b56ba27352733bb83729e85b1d6196dca70c99/xlstmad.py#L15) | Encoder and decoder each have `[sLSTM,sLSTM,mLSTM]`. Projection → full encoder sequence → full decoder sequence → GELU → projection. `forward(x)` has no state argument or returned state. | Causal token reconstruction inside a window; fresh recurrent/conv state per call. No cross-window memory. |
| [Improved loss and score, lines 103–130](https://github.com/Nyderx/xlstmad/blob/e8b56ba27352733bb83729e85b1d6196dca70c99/xlstmad.py#L103) | Training target is x itself, output `[B,W,D]`; test MSE averages time and channels. `predict_step` compares reconstruction to supplied target. | `predict_step` is a Lightning inference method, not evidence of forecasting. With native dataset, target is a scalar endpoint label, not a reconstruction target; use observation-only score wrapper, never this label-bearing API. |
| [Improved dataset, lines 13–21](https://github.com/Nyderx/xlstmad/blob/e8b56ba27352733bb83729e85b1d6196dca70c99/dataset.py#L13) | `N−W+1` windows, index i slices `[i:i+W]`; label is y[i+W−1]. | Adjacent windows overlap W−1 points. Carrying all W points from every call repeats observations; at W64 an interior sample can be ingested 64 times. |
| [Original forecasting 3a1b0b5, lines 56–72](https://github.com/Nyderx/xlstmad/blob/3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6/models/xlstmad_pred.py#L56) | Window encoder; last output seeds decoder input. Each forecast horizon calls stack `forward` on a singleton, repeatedly transforming the latent; no recurrent state argument between calls or windows. Returns `[P,B,D]`. | There is iterative latent feedback, but no decoder recurrent state carry. Not a native persistent streaming forecaster. |
| [Forecast dataset, lines 42–59](https://github.com/Nyderx/xlstmad/blob/3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6/models/forecast_dataset.py#L42) | X[i:i+W] → Y[i+W:i+W+P], stride 1; fit-prefix statistics can be supplied for validation/test. | Causal prediction targets are possible. Original `output.view` on `[P,B,D]` vs target `[B,P,D]` misaligns for P>1 and B>1. P=1 does not have this particular flattening mismatch. |
| [Original reconstruction, lines 57–73](https://github.com/Nyderx/xlstmad/blob/3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6/models/xlstmad_rec_ad.py#L57) | Last-encoder-output bottleneck and singleton decoder rollout; returns `[W,B,D]`. | Different architecture from improved E2. Historical E validity failure is retained; do not rehabilitate it by silently changing transpose/targets. |

The improved repository's pinned root tree contains `xlstmad.py`, `dataset.py`, an example, requirements and documentation; **no separate improved forecasting model**. Original forecasting is the inspected `XLSTMADPred` MSE route, not a claim that every optional SoftDTW variant was audited. No upstream training or evaluation entrypoint was run.

## Causal scoring is not the same as pointwise alignment

The improved per-token reconstruction at t depends on x≤t, including x_t; causal convolution, recurrent update, residual projection and feature-only normalization introduce no future dependence in this path. The reconstruction may learn a near-identity shortcut because the target is already an input. That makes it a clean engineering comparator but a weaker innovation score.

The native window score is available only at its right edge. It averages residuals at every position, whereas the supplied label is only the endpoint. This is a legal trailing-window statistic if explicitly named, not an instantaneous anomaly score, and cannot be backdated to the left edge. Switching to the last-token residual changes the score definition and calibration; retaining a trailing W residual average requires a separate ring buffer. It cannot make old fresh-window reconstructions equal to persistent-run reconstructions.

Original forecast scoring fills the first W+P−1 timestamps with `scores[0]` (lines 234–238): that backfills unavailable early predictions with future residuals and is unsuitable for strict streaming. Leave warmup unscored; never make padding look like measured recovery.

## Starting implementation and checkpoint

Use improved official E2 configuration as the **API/parity starting point**, xlstm==2.0.5, vanilla float32, D8/W64/E40; see [historical E2 seal](../../reports/phase_e2/amendment.md). It has aligned reconstruction and the inspected stack.step route. The new random fixture uses no scientific checkpoint.

For a later separately authorized reconstruction comparator, the existing Phase F v4 `xlstm_11/best.pt` is locally present and its raw SHA256 currently equals the [sealed manifest](../../reports/phase_f_v4/final_manifest.json): `4729a3ba385b285078aa987fce176e61fd382715c5357fc92f2635a929a0ae41`. This is a predeclared seed-11 candidate, **not selected by anomaly performance**. Its checkpoint was hashed but not loaded or evaluated here. D8 reconstruction training does not establish forecasting skill, variable-D TSB compatibility, or validity beyond W64. Other seeds remain necessary in any later approved comparison.

There is **no verified forecast-trained streaming checkpoint** in this audit. Reinterpreting a reconstruction output as x[t+1] is not a valid forecast model. A future encoder-only predictive objective/head would be an explicitly new track requiring approval and matched training. The original paper route and improved implementation must remain separately named.

## Protocol boundary

Issue #22 allows these static/API checks and bounded random prototypes. It does not revive historical H3b (conditional on H3a), alter old E/F/G decisions, or authorize TSB performance/training. All changes in this task live in this independent audit directory. Historical protocol and result files remain untouched.
