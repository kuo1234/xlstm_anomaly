# M1-A claim boundary

M1-A tests source-native anomaly detection on each SMD machine. It does not test adaptive normality, cross-machine transfer, or regime changes.

## Claims this study may support

### Forecasting detector claim

If the predeclared Stage-1/Stage-2 gate passes, one-step forecast residuals may be described as a useful source-native anomaly signal on this audited SMD family, relative to the named cheap controls and xLSTMAD reconstruction. Scope is local subdaily dynamics, the frozen scaler/context, and benchmark train-normal assumption.

### xLSTM-specific claim

Only a replicated, predeclared xLSTM-F versus capacity-matched LSTM-F gain can support an xLSTM-specific advantage. Similar performance means forecasting may be useful while xLSTM-specific value remains unsupported.

### Complementarity claim

Only the frozen tail-rank max-fusion route may support that forecast scores add useful discrimination beyond the five non-forecast scores (last-value, moving median, VAR(1), `R-native-window`, and `R-endpoint`). It is a fixed score combination, not evidence for a learned ensemble. The standalone route uses a test-label-dependent oracle control envelope as a conservative scientific gate; that envelope is not a deployable detector or one operational baseline.

## Claims this study cannot support

- Source-to-target transfer or few-shot target-normal sample efficiency.
- Strict zero-shot performance or deployment to an unseen machine.
- Persistent recurrent memory: all test windows reset.
- Selective adaptation, quarantine, protection from anomaly contamination, or rollback.
- Recognizing benign new-normal regimes versus persistent failures.
- Multi-horizon forecasting or daily/seasonal forecasting.
- Universal arbitrary-D modeling or cross-machine channel-semantic transfer.
- That hidden state contains information unavailable in observable inputs.
- A broad industrial performance claim from SMD alone.

## Negative and non-transferable evidence

The repository’s R0 study found no resolved incremental real-data utility of internal234 for either xLSTM or capacity-matched LSTM under its frozen probe. The synthetic internal-state advantage was also similar for matched LSTM; stronger observable controls attenuated the increment, and P1r found no further increment over the strong input-derived control. R0 additionally exposed machine-1-4 near-constant-channel scaler amplification. M1 addresses a different detector question with a new scaler and forecast target. It does not erase or reinterpret these results, and a successful M1 forecast result would not reverse the internal234 conclusions.

The first Stage-1 result is a viability gate only. Even a pass does not authorize M1 transfer, zero-shot, or online-adaptation experiments. Those need separate questions, protocols, and approval.
