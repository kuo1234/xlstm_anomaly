# R0 claim boundary

## New rung: L1d — source-native real-data measurement replication

L1d asks whether the L1a measurement phenomenon (internal state adds predictive/decodable utility over causal
score/history) replicates on source-native real multivariate telemetry. It sits beside the synthetic rungs; it does
not revise them.

| rung | status before R0 | what R0 can change |
|---|---|---|
| L1a (synthetic: internal state adds utility over score/history) | supported | nothing |
| L1c-P (synthetic: utility beyond the bounded input-derived control P1r) | NOT SUPPORTED at P1r resolution (terminal) | nothing — R0 does not attempt to rescue it |
| **L1d** (real SMD, within-machine, over score/history) | untested | set by the §8 wording map of `protocol.md` |
| L5 and above | not reached | **never promoted by R0** |

## Permitted statements

| R0 class (per backbone) | the only permitted statement |
|---|---|
| `R0_POSITIVE_INCREMENT` | "Recurrent internal-state features retain additional anomaly predictive/decodable utility over causal score/history in the tested source-native SMD within-machine diagnostic (Design B; exploratory uncertainty; not unseen-machine transfer)." |
| `R0_NO_RESOLVED_INCREMENT` | "R0 does not resolve additional real-data predictive utility of internal state beyond score/history under the frozen diagnostic." |
| `R0_NEGATIVE_INCREMENT` | the negative increment is reported directly, with its cells, means and exploratory intervals |

L1d is **supported** only for a backbone classified `R0_POSITIVE_INCREMENT`; it is reported per backbone. A split
outcome (one backbone positive, the other not) is reported as such and is not a backbone comparison.

## Never claimed from R0

* internal information unavailable in the raw input (R0 has no observable control beyond score/history);
* contradiction of P1r (different question, different data, different control);
* xLSTM superiority over LSTM, or any backbone ranking;
* benign-drift discrimination (SMD labels are anomaly/non-anomaly only; no drift labels are derived);
* unseen-machine or unseen-detector transfer (Design B is within-machine);
* cross-domain generality (one dataset family, three machines);
* deployment validity, alarm quality or operational thresholds;
* online-adaptation value or safety;
* a calibrated population confidence interval (three machines × three seeds; intervals are exploratory).

## R1 (recorded prospectively)

R1 = HAI 22.04 distinct-domain ICS/SCADA replication with source-native attack labels. R1 execution is gated only on
acquisition, provenance and schema/model compatibility, and never on the R0 outcome. R0 results may not be used to
decide whether HAI is attempted, nor to tune any R1 design choice.
