# R0 results — source-native SMD recurrent-state measurement (Design B, r0-v1.2)

Protocol `d7708586fe3264fcd6e5567504cccd97104c2a2e` with implementation amendments r0-v1.1 (xLSTM features from the vanilla backend + scalar reference observer) and r0-v1.2 (capacity-matched auditable LSTM implementation, one recurrence for training and extraction). Estimand per cell: `ΔAP = AP_test(H+internal234) − AP_test(H)` on the frozen probe-test block of one machine and one detector. Design B is an offline within-machine diagnostic, not unseen-machine transfer. Intervals are exploratory resampling intervals (3 machines × 3 seeds), not calibrated population 95% CIs.

## xLSTM

| machine | seed 11 | seed 22 | seed 33 | machine mean |
|---|---:|---:|---:|---:|
| machine-1-8 | +0.0690 | +0.0492 | -0.2013 | -0.0277 |
| machine-2-1 | -0.0554 | -0.0558 | -0.0843 | -0.0652 |
| machine-1-4 | +0.1989 | +0.1484 | +0.3061 | +0.2178 |
| seed mean | +0.0708 | +0.0473 | +0.0068 | +0.0416 |

Mean ΔAP +0.0416; positive cells 5/9; two-way interval [-0.1035, +0.2010]; machine-only interval [-0.0652, +0.2178].

**Classification: `R0_NO_RESOLVED_INCREMENT`.** R0 does not resolve additional real-data predictive utility of internal state beyond score/history under the frozen diagnostic.

| cell | AP(H) | AP(H+I) | ΔAP | selected max_iter H / H+I |
|---|---:|---:|---:|---|
| machine-1-8_xlstm_11 | 0.2935 | 0.3625 | +0.0690 | 100 / 100 |
| machine-1-8_xlstm_22 | 0.2421 | 0.2913 | +0.0492 | 300 / 300 |
| machine-1-8_xlstm_33 | 0.2911 | 0.0898 | -0.2013 | 100 / 300 |
| machine-2-1_xlstm_11 | 0.7271 | 0.6717 | -0.0554 | 300 / 300 |
| machine-2-1_xlstm_22 | 0.7783 | 0.7225 | -0.0558 | 300 / 300 |
| machine-2-1_xlstm_33 | 0.7423 | 0.6579 | -0.0843 | 300 / 300 |
| machine-1-4_xlstm_11 | 0.3070 | 0.5059 | +0.1989 | 100 / 300 |
| machine-1-4_xlstm_22 | 0.3207 | 0.4692 | +0.1484 | 100 / 300 |
| machine-1-4_xlstm_33 | 0.2764 | 0.5825 | +0.3061 | 100 / 300 |

## Capacity-matched auditable LSTM (R0-v1.2)

| machine | seed 11 | seed 22 | seed 33 | machine mean |
|---|---:|---:|---:|---:|
| machine-1-8 | +0.1108 | -0.3165 | -0.1809 | -0.1289 |
| machine-2-1 | +0.0517 | -0.1147 | -0.0268 | -0.0299 |
| machine-1-4 | +0.1117 | +0.2057 | +0.3908 | +0.2361 |
| seed mean | +0.0914 | -0.0752 | +0.0611 | +0.0258 |

Mean ΔAP +0.0258; positive cells 5/9; two-way interval [-0.2093, +0.2361]; machine-only interval [-0.1289, +0.2361].

**Classification: `R0_NO_RESOLVED_INCREMENT`.** R0 does not resolve additional real-data predictive utility of internal state beyond score/history under the frozen diagnostic.

| cell | AP(H) | AP(H+I) | ΔAP | selected max_iter H / H+I |
|---|---:|---:|---:|---|
| machine-1-8_lstm_11 | 0.2618 | 0.3726 | +0.1108 | 300 / 100 |
| machine-1-8_lstm_22 | 0.4515 | 0.1350 | -0.3165 | 100 / 300 |
| machine-1-8_lstm_33 | 0.3037 | 0.1228 | -0.1809 | 100 / 300 |
| machine-2-1_lstm_11 | 0.5667 | 0.6184 | +0.0517 | 300 / 100 |
| machine-2-1_lstm_22 | 0.6458 | 0.5311 | -0.1147 | 100 / 100 |
| machine-2-1_lstm_33 | 0.6249 | 0.5981 | -0.0268 | 300 / 100 |
| machine-1-4_lstm_11 | 0.3717 | 0.4834 | +0.1117 | 100 / 100 |
| machine-1-4_lstm_22 | 0.2863 | 0.4920 | +0.2057 | 100 / 300 |
| machine-1-4_lstm_33 | 0.3065 | 0.6973 | +0.3908 | 100 / 300 |

## Detector sanity (diagnostic context only; computed after the probe matrices were sealed)

| detector | AP | AUROC | recall@thr | FPR@thr | window prevalence | flag |
|---|---:|---:|---:|---:|---:|---|
| machine-1-8_xlstm_11 | 0.2950 | 0.6561 | 0.7603 | 0.7204 | 0.0849 |  |
| machine-1-8_xlstm_22 | 0.3075 | 0.6724 | 0.7524 | 0.6426 | 0.0849 |  |
| machine-1-8_xlstm_33 | 0.3091 | 0.6873 | 0.8824 | 0.6949 | 0.0849 |  |
| machine-2-1_xlstm_11 | 0.6393 | 0.8491 | 0.6712 | 0.0546 | 0.0842 |  |
| machine-2-1_xlstm_22 | 0.6711 | 0.8595 | 0.6405 | 0.0404 | 0.0842 |  |
| machine-2-1_xlstm_33 | 0.6341 | 0.8508 | 0.6747 | 0.0790 | 0.0842 |  |
| machine-1-4_xlstm_11 | 0.2071 | 0.6791 | 0.1145 | 0.0254 | 0.0624 |  |
| machine-1-4_xlstm_22 | 0.1875 | 0.6025 | 0.1145 | 0.0254 | 0.0624 |  |
| machine-1-4_xlstm_33 | 0.1918 | 0.6092 | 0.1145 | 0.0254 | 0.0624 |  |
| machine-1-8_lstm_11 | 0.3053 | 0.7205 | 0.9088 | 0.7006 | 0.0849 |  |
| machine-1-8_lstm_22 | 0.3158 | 0.7434 | 0.9547 | 0.6223 | 0.0849 |  |
| machine-1-8_lstm_33 | 0.3412 | 0.7799 | 0.9317 | 0.6076 | 0.0849 |  |
| machine-2-1_lstm_11 | 0.5231 | 0.8012 | 0.5948 | 0.1146 | 0.0842 |  |
| machine-2-1_lstm_22 | 0.5250 | 0.7890 | 0.6149 | 0.1351 | 0.0842 |  |
| machine-2-1_lstm_33 | 0.5554 | 0.8203 | 0.7019 | 0.1374 | 0.0842 |  |
| machine-1-4_lstm_11 | 0.2145 | 0.6760 | 0.1145 | 0.0254 | 0.0624 |  |
| machine-1-4_lstm_22 | 0.2008 | 0.6376 | 0.1145 | 0.0254 | 0.0624 |  |
| machine-1-4_lstm_33 | 0.1800 | 0.5611 | 0.1145 | 0.0254 | 0.0624 |  |

Near-constant fit channels (sealed zero-std-only scaler; no post-hoc repair): machine-1-8: zero-std [4, 7, 16, 17, 26, 28, 36, 37], smallest non-zero std channel 22 (0.00508); machine-2-1: zero-std [7, 26, 28, 36, 37], smallest non-zero std channel 17 (0.00152); machine-1-4: zero-std [7, 16, 26, 28, 36, 37], smallest non-zero std channel 17 (1.69e-05).

Never claimed from R0: internal information unavailable in raw input; contradiction of P1r; xLSTM superiority over LSTM; benign-drift discrimination; cross-domain generality; unseen-machine transfer (Design B); deployment validity; online adaptation value.
