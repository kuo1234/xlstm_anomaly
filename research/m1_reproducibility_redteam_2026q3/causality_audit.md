# Forecast causality and score-alignment audit

**Scope:** static source review at AUDITED_M1_SHA; no model forward pass was executed by this audit.

## Verdict

**PASS for the default one-step forecast data path.** Each forecast input is constructed from the W rows before target t, model output is materialized, and only then is z[t] copied into residual construction. Test endpoints start at t=W and remain aligned without padding.

**Important distinction:** xLSTMAD-R is a contemporaneous reconstruction comparator. Its trailing window includes z[t]; it does not forecast z[t]. It is causal in the no-future-sample sense and aligned to t, but must not be described as a past-only prediction.

## Forecast input and target ordering

The protocol freezes [t-W,t) -> predict t -> then score with z[t], with fresh state for every independent window. It gives R the trailing window [t-W+1,t+1) and evaluates reconstruction at the right edge. Evidence: research/adaptive_normality_m1_smd/protocol.md:37-41.

forecast_predictions_then_score validates t in [W, stream length), constructs each context from stream[t-W:t], calls model(x), then copies stream[t] into batch_targets. Only after the prediction exists does score_forecaster call the point-residual function. Evidence: scripts/adaptive_normality_m1_execute.py:353-381, 384-387.

Stage-1A and full score paths use forecast targets and require exact endpoints arange(W, test_rows), with no padded first-window scores. Evidence: scripts/adaptive_normality_m1_execute.py:390-411; Stage-1A run validation checks the same exact timestamp vector at scripts/adaptive_normality_m1_stage1a.py:279-290.

The result-blind score-construction function installs the label-access guard and accepts train/test arrays, transforms, models, and a device, but no label argument. Evidence: scripts/adaptive_normality_m1_execute.py:390-399.

## Reconstruction alignment

At target t, reconstruction windows are z[t-W+1:t+1]. reconstruction_scores computes both mean squared residual over the full W-by-D window and the last-position residual. Both are assigned to timestamp t. Evidence: scripts/adaptive_normality_m1_execute.py:406-412 and scripts/adaptive_normality_m1_scores.py:46-59.

The baseline specification describes R-native-window as the faithful window mean and R-endpoint as the point-aligned final-position diagnostic. It says both use no future sample and map to the same t as forecast scores: research/adaptive_normality_m1_smd/baseline_spec.md:25-38.

Since R sees z[t] in its input window, R is not an independent one-step-ahead forecast. Comparisons must preserve that distinction; R-endpoint does not make R past-only.

## Baseline causality and timestamp checks

The score helpers use preceding values for last-value, moving median, and train-fit VAR(1), then align outputs to the same forecast timestamp vector. Evidence: scripts/adaptive_normality_m1_scores.py:71-100 and scripts/adaptive_normality_m1_execute.py:414-420. Fusion helpers require identical timestamp vectors across every arm: scripts/adaptive_normality_m1_scores.py:161-191.

Raw files have no timestamps; evaluation uses positional sample indices and latency is measured in samples. Evidence: research/adaptive_normality_m1_smd/protocol.md:39.

## Limits of this conclusion

This is a code-path inspection, not a runtime trace or independent proof of external package internals. The committed forecasting implementation audit reports a synthetic parity/index check, but this red-team audit did not execute it. This audit does not certify runtime determinism, GPU kernels, or that historical execution used the exact tracked bytes.
