# Claim boundary

Five claims are independent. A result supporting one does not establish another.

| Claim | Precisely scoped possible claim | Minimum evidence | Current boundary |
|---|---|---|---|
| **Transfer claim** | Source pretraining reduces the amount of confirmed-normal target data needed to reach a specified detector utility on a held-out machine. | Leave-machine-out source training; normal-only target sample curve; later disjoint target test; scratch, normalization/calibration, adapter, last-block and full-tune arms; machine-level results; matched LSTM and other relevant baselines. | Untested. R0 is within-machine Design B and not transfer. |
| **Detection claim** | Forecasting or persistent memory improves anomaly detection over reconstruction and simple observable baselines. | M1/M2/M3 with causal timing, event-level and point-level metrics, moving-statistic/last-value controls, LSTM and xLSTMAD reconstruction. | Not established by R0. G1 internal-state utility is not a forecasting or persistent-state result. |
| **New-normal claim** | Selective adaptation lowers false-positive persistence after a legitimate, independently verified operating-mode change without unacceptable loss on anomalies. | Semantically labeled benign modes and transient/persistent faults; a causal state policy; external mode truth if observations are ambiguous; per-event outcomes. | M2N2 already establishes the broad new-normal problem and TTA. Current public benchmark labels are insufficient to claim safe distinction. |
| **Safety claim** | Quarantine or protected state prevents anomalous observations from contaminating the normal detector. | Controlled contamination study with committed-sample accounting, false promotion and persistent-attack rejection; compare update-all, gate, quarantine, freeze and rollback. | Untested. A quarantine buffer is not proof of safe adaptation. |
| **xLSTM-specific claim** | xLSTM offers value beyond a capacity-matched conventional recurrent/SSM model on the same task. | Matched architecture, data, tuning and compute; multiple machines/sources/seeds; paired practical margin and uncertainty; same input and state policy. | Unsupported as a claim about internal-state superiority. Matched LSTM reproduces G1-scale signal, A+/A+S/P1r attenuate it, and R0 resolves no increment for either backbone. A new task could still show a different result. |

## Forbidden conflations

- A target-normal warm start with N > 0 is few-shot transfer, not zero-shot.
- Fewer target samples for matching quality does not prove online new-normal adaptation.
- Fewer false alarms under distribution shift does not prove the shift was benign.
- Anomaly-free source pretraining does not mean every unlabeled test observation is normal.
- Low forecast error, high persistence or a coherent candidate does not prove safety.
- A positive xLSTM detector result does not show xLSTM is necessary unless compared to matched alternatives.
- R0’s recurrent-state readout is distinct from a persistent state update policy.
