# Fixed two-family panel

| baseline | family | settings |
| --- | --- | --- |
| PCA_SPE | non-neural pointwise reconstruction | 8components, float64 SVD, standardized SPE/MSE |
| CAUSAL_LSTM_REFERENCE | one-step recurrent forecast | 19→32 LSTM1layer→19 linear; W32;10epochs; Adam1e-3 |

LSTM prediction consumes only t−32..t−1; score is residual when target t arrives. This is a named reference, not native TensorFlow LSTM reproduction. PCA score uses current observed t. Both fit once, same normal scaler/roles/seed; their objectives/optimization differ and there is no parameter-budget parity claim.

DIVAD pinned TranAD has custom encoder/decoder forward signatures without modern PyTorch2.9 causal kwargs. The older native environment/framework parity and compatibility overlay have not been sealed. BaselineC NOT_RUN is fixed prospectively under Issue26’s optional-C rule; no alternate model will be selected. [Static runtime evidence](provenance/runtime.json).

Final checkpoint only; no anomaly-trained tuning, early stopping or epoch choice. Fixed normal validation loss remains visible so failure to learn is not hidden. A small single-seed reference panel can falsify its proposed shared mechanism but cannot establish universal detector behavior.
