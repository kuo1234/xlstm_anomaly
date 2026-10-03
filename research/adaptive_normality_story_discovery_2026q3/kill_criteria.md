# Kill criteria

Each criterion must be frozen, with its numeric margin, in a sealed protocol before any result is examined. This follows the project's practice of pre-declared margins and fail-closed gates. Here "margin" always means a value fixed in that protocol. This document proposes the form of the criteria, not the numbers.

## Literature kills: check before any build

| ID | Story | Check | Kill if |
|---|---|---|---|
| L1 | P1/N7 | Full text of [Wagner et al. 2025](https://arxiv.org/abs/2510.17562) (37-metric property analysis) and the 34 metrics in [Velasco & Zafra 2026](https://doi.org/10.1016/j.neucom.2026.134154) | Any property or metric already penalises post-detection absorption of a persistent anomaly by an adapting detector. The metric-blindness claim then becomes a corollary; downgrade P1 to benchmark-only. |
| L2 | P1/G | Full text of [Cao et al. 2024](https://doi.org/10.1007/s10462-024-10995-w) (SCAR), [Li et al. 2024a](https://doi.org/10.1016/j.datak.2024.102365) (STAD), [Faber et al. 2026](https://arxiv.org/abs/2607.18289) | Any of them provides promotion-correctness or observationally-equivalent strata. |
| L3 | P2/A | Full text of [Qin et al. 2026](https://arxiv.org/abs/2604.08059), [Park et al. 2025](https://doi.org/10.1145/3746252.3761481) and [Wang et al. 2026a](https://arxiv.org/abs/2609.20700) | Any already compares optimistic-commit-plus-rollback with delay-only admission across validation latencies. |
| L4 | P2/B | Full text of [Schirmer et al. 2025](https://doi.org/10.52202/085713-2705) and [Prinster et al. 2025](https://arxiv.org/abs/2505.04608) | Either already states an impossibility of label-free harm guarantees under observationally equivalent harmful/benign shifts and proposes exposure accounting. |
| L5 | P3/D | Full text of [Le et al. 2026](https://doi.org/10.1145/3744255.3811742), [Lotto et al. 2026](https://arxiv.org/abs/2609.28170) and [Abdoune et al. 2026](https://doi.org/10.1016/j.eswa.2025.130062) (metadata only so far) | Any evaluates faults that coincide with authorised changes and scoped promotion. |
| L6 | N5 | Full text of [Du et al. 2019](https://doi.org/10.1145/3319535.3363226) | Its unlearning already handles regime-scale retractions in continuous-valued detectors with a rollback comparison. |
| L7 | all | Re-run the searches in [future_dated_leads.md](future_dated_leads.md) before submission | A future-dated item turns out to occupy the core claim. |

## Empirical kills

| ID | Story | Kill if |
|---|---|---|
| K1 | P1 | Rankings of ≥6 adaptive methods under standard metrics (PA-F1, VUS-PR, AP) and absorption-aware metrics are concordant (Kendall τ ≥ 0.8) in every scenario family. |
| K2 | P1 | Some method beats the theoretical floor on the non-identifiable stratum beyond sampling error. This signals generator leakage: fix the generator or stop. |
| K3 | P1 | A pre-registered suite of simple classifiers (window statistics, spectra, HGB on lags) separates benign from fault on the non-identifiable stratum above chance by more than the margin. This signals leakage. |
| K4 | P1 | Absorption-aware metrics add no information over point-wise AP (rank correlation ≥ 0.95 with AP across all runs). |
| K5 | P2 | At every tested confirmation latency, a dwell-only baseline tuned to the same benign false-alarm budget reproduces the lifecycle frontier within the margin. Reversibility then adds nothing beyond delay. |
| K6 | P2 | Residual contamination after rollback or retraction is not below the margin for the chosen state container, so rollback is not a reversal. |
| K7 | P2 | The exposure-budgeted policy never improves benign delay over a conformal/anytime-valid gate at matched realised absorption. |
| K8 | C | UNRESOLVED verdicts do not concentrate on the equivalent stratum, or replacing UNRESOLVED with FREEZE changes neither absorption nor delay. |
| K9 | P3 | "Promote iff authorised" or conditional scoring matches scoped promotion on coincident-fault absorption at matched benign false alarms. |
| K10 | P3 | Feasibility: no dataset or simulator yields authorisation events with coincident faults under a sealed manifest within the scoping budget. |
| K11 | P4 | k-of-n corroboration gives no reduction in false promotion over single-entity promotion at matched delay, or the benefit disappears when an adversary controls ≤ 10% of entities. |
| K12 | P4 | Feasibility: no fleet dataset with documented fleet-wide benign changes can be pinned. |
| K13 | P5 | A zero-shot foundation detector or a one-liner baseline ([One-liners paper (ICLR 2026)](https://openreview.net/forum?id=H27kvyG4qf)) is within the margin of source-pretrained adaptation at the shortest tested prefix on both entity families. |
| K14 | P5 | Sample-efficiency curves of all adaptation families are indistinguishable. P5 then becomes a benchmark note. |
| K15 | N1 | Staged gates show no attack-budget advantage over one-shot retraining. |

## Program-level kill

Abandon adaptive normality as a primary direction (Path 4) if L1 and L2 both fire and K1 fires. That combination would mean the evaluation gap is already closed and the remaining method stories have no accepted yardstick.

## What does not count as a kill

- A negative or null M1 result. No programme story depends on M1. This report does not read or interpret M1.
- xLSTM failing to beat matched recurrent or non-recurrent baselines. No story claims xLSTM value.
- A method that fails to beat the Bayes floor on the non-identifiable stratum. That is the expected result, and it confirms the generator.
