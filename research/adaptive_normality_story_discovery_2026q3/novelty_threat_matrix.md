# Novelty threat matrix

Threat levels: **Occ** means the family already occupies the story's core claim. **High** means a direct competitor that a reviewer will cite on page one. **Med** means a strong component threat. **Low** means adjacent. **—** means not relevant. These are qualitative judgements from the evidence in [closest_prior_art.md](closest_prior_art.md), not scores.

## Threat families

| Code | Family | Representative closest works |
|---|---|---|
| T1 | Normality memory, pools and lifecycles in streaming AD | [Park et al. 2025](https://doi.org/10.1145/3746252.3761481), [Li et al. 2026b](https://doi.org/10.1016/j.knosys.2026.116530), [Yoon et al. 2022](https://doi.org/10.1145/3534678.3539348), [Li et al. 2024a](https://doi.org/10.1016/j.datak.2024.102365), [Zhu et al. 2024](https://doi.org/10.14778/3636218.3636233), [Bhatia et al. 2022](https://doi.org/10.1145/3485447.3512221) |
| T2 | Staged activation and rollback outside TSAD | [Qin et al. 2026](https://arxiv.org/abs/2604.08059), [Aftab et al. 2026](https://arxiv.org/abs/2607.02687), [Su et al. 2026](https://arxiv.org/abs/2607.27773) |
| T3 | Selective and risk-monitored TTA | [Jiang et al. 2026](https://arxiv.org/abs/2609.08367), [Wang et al. 2026a](https://arxiv.org/abs/2609.20700), [Schirmer et al. 2025](https://doi.org/10.52202/085713-2705), [Majumdar & Saha 2026](https://arxiv.org/abs/2608.22233) |
| T4 | Conformal, sequential and anytime-valid control | [Angelopoulos et al. 2022](https://arxiv.org/abs/2208.02814), [Prinster et al. 2025](https://arxiv.org/abs/2505.04608), [Amoukou et al. 2024](https://doi.org/10.52202/079017-4107), [Han & Qu 2026](https://arxiv.org/abs/2608.30502) |
| T5 | Drift-aware selective TSAD with semantics | [Le et al. 2026](https://doi.org/10.1145/3744255.3811742), [Kim et al. 2024](https://doi.org/10.1609/aaai.v38i12.29210), [Kim et al. 2026](https://doi.org/10.1609/aaai.v40i17.38524), [Li et al. 2026c](https://doi.org/10.24963/ijcai.2026/503) |
| T6 | Context, multimode and physics-based process monitoring | [Song et al. 2007](https://doi.org/10.1109/tkde.2007.1009), [Lane et al. 2001](https://doi.org/10.1016/s0959-1524%2899%2900063-3), [Choi et al. 2018](https://doi.org/10.1145/3243734.3243752), [Gao et al. 2021](https://doi.org/10.1145/3450267.3450533) |
| T7 | CPS security, trust and poisoning | [Lotto et al. 2026](https://arxiv.org/abs/2609.28170), [Kloft & Laskov 2012](https://arxiv.org/abs/1003.0078), [Kravchik & Shabtai 2020](https://arxiv.org/abs/2002.02741), [Cong et al. 2024](https://arxiv.org/abs/2308.08505) |
| T8 | Streaming and continual-AD benchmarks | [Cao et al. 2024](https://doi.org/10.1007/s10462-024-10995-w), [Faber et al. 2026](https://arxiv.org/abs/2607.18289), [Jacob et al. 2020](https://arxiv.org/abs/2010.05073), [Liu & Paparrizos 2024b](https://doi.org/10.52202/079017-3437) |
| T9 | TSAD metric critiques | [Kim et al. 2022](https://doi.org/10.1609/aaai.v36i7.20680), [Wagner et al. 2025](https://arxiv.org/abs/2510.17562), [Lyu 2026](https://arxiv.org/abs/2607.11969), [Velasco & Zafra 2026](https://doi.org/10.1016/j.neucom.2026.134154) |
| T10 | Transfer, few-shot and zero-shot normality | [Holly et al. 2025](https://arxiv.org/abs/2501.13052), [Jonas & Meyer 2025](https://arxiv.org/abs/2504.17709), [Shentu et al. 2025](https://arxiv.org/abs/2405.15273), [One-liners paper (ICLR 2026)](https://openreview.net/forum?id=H27kvyG4qf) |
| T11 | Continual learning with resource accounting | [Smendowski et al. 2026](https://doi.org/10.1007/s10723-026-09846-5), [Piaseczny et al. 2025](https://arxiv.org/abs/2505.24149) |
| T12 | Unlearning and retroactive correction | [Du et al. 2019](https://doi.org/10.1145/3319535.3363226), [Machine unlearning for streaming forgetting (OpenReview 2024)](https://openreview.net/forum?id=bIoWuzFm6r) |
| T13 | Fleet/population and active fault diagnosis | [Tveten et al. 2022](https://doi.org/10.1214/21-aoas1508), [de Novaes Pires Leite et al. 2023](https://doi.org/10.1016/j.engappai.2023.106859), [Nikoukhah & Campbell 2003](https://doi.org/10.23919/ecc.2003.7085087) |

## Matrix

| Story | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | T10 | T11 | T12 | T13 | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A lifecycle | Occ | High | Med | Low | High | Low | Low | — | — | — | — | Med | — | `PROMISING_BUT_THREATENED` (reversibility form) / `WEAK` (mechanism) |
| B risk budget | Med | Low | High | High | Med | — | Med | — | — | — | Low | — | — | `PROMISING_BUT_THREATENED` |
| C three-way | Med | — | Occ | High | Low | — | — | — | — | — | — | — | — | `WEAK / COMPONENT_ONLY` |
| D context | Low | — | — | — | High | High | High | — | — | — | — | — | — | `PROMISING_BUT_THREATENED` |
| E recurrence | Occ | Low | — | — | Med | Med | — | Med | — | — | Med | — | — | `ALREADY_OCCUPIED` |
| F commissioning | — | — | — | — | — | Low | — | Low | — | Occ | — | — | Med | `ALREADY_OCCUPIED` (method) |
| G benchmark | Low | — | — | — | Med | — | — | High | Med | — | — | — | — | `PROMISING_BUT_THREATENED` |
| H resources | Med | — | — | — | — | — | — | Med | — | — | Occ | — | — | `ALREADY_OCCUPIED` |
| N1 attack surface | Med | — | Low | — | Low | — | High | — | — | — | — | — | — | `PROMISING_BUT_THREATENED` |
| N2 peers | — | — | — | — | — | Low | Med | — | — | Low | — | — | High | `PROMISING_BUT_THREATENED` |
| N3 probing | — | — | — | — | — | Med | — | — | — | — | — | — | Occ | `WEAK / COMPONENT_ONLY` |
| N4 regime queries | Low | — | Low | — | Low | Med | — | — | — | — | — | — | — | `PROMISING_BUT_THREATENED` |
| N5 retraction | Low | High | — | — | — | — | — | — | — | — | — | High | — | `PROMISING_BUT_THREATENED` |
| N6 masking | Med | — | — | — | Low | Med | — | Med | Low | — | — | — | — | `PROMISING_BUT_THREATENED` |
| N7 metric blindness | — | — | — | Low | — | — | — | Med | High | — | — | — | — | `STRONG_CANDIDATE` |
| **P1** | Low | — | — | Low | Med | — | — | High | High | — | — | — | — | `STRONG_CANDIDATE` |
| **P2** | High | High | High | High | Med | — | Med | — | — | — | — | Med | Low | `PROMISING_BUT_THREATENED` |
| **P3** | Low | — | — | — | High | High | High | — | — | — | — | — | — | `PROMISING_BUT_THREATENED` |
| **P4** | — | — | — | — | — | Low | High | — | — | Low | — | — | High | `PROMISING_BUT_THREATENED` |
| **P5** | — | — | — | — | — | — | — | Med | — | High | — | — | Med | `PROMISING_BUT_THREATENED` |

## Kind of novelty for surviving stories

Systems integration alone is never listed as algorithmic novelty.

| Story | Problem formulation | Decision / risk formulation | State-management mechanism | Architecture | Evaluation methodology | Dataset / benchmark | Theoretical result |
|---|---|---|---|---|---|---|---|
| P1 | | | | | ✔ | ✔ | ✔ (metric blindness; Bayes floor by construction) |
| P2 | | ✔ | ✔ (versioned rollback; not new as a container) | | | | ✔ (impossibility + achievability; latency dominance) |
| P3 | ✔ (authorisation scope, coincident faults) | ✔ | | | ✔ | | |
| P4 | ✔ | | | | | | ✔ (identifiability under common cause; adversarial fraction) |
| P5 | | | | | ✔ | (✔ if a cross-family suite is released) | (✔ stopping rule, if derived) |
| N1 | | | | | ✔ | | ✔ (attack-cost bound) |

No surviving story involves a new architecture, and xLSTM does not appear in any claim.

## Threats with highest reviewer salience

1. [Li et al. 2026b](https://doi.org/10.1016/j.knosys.2026.116530) for anything about recurrence, pools or drift-type-aware adaptation in unsupervised streaming TSAD.
2. [Qin et al. 2026](https://arxiv.org/abs/2604.08059) and [Aftab et al. 2026](https://arxiv.org/abs/2607.02687) for anything called a lifecycle with rollback.
3. [Jiang et al. 2026](https://arxiv.org/abs/2609.08367), [Wang et al. 2026a](https://arxiv.org/abs/2609.20700) and [Schirmer et al. 2025](https://doi.org/10.52202/085713-2705) for anything about deciding whether to adapt.
4. [Le et al. 2026](https://doi.org/10.1145/3744255.3811742) for anything about separating benign drift from attack with contamination-free updates.
5. [Cao et al. 2024](https://doi.org/10.1007/s10462-024-10995-w) (SCAR) and [Li et al. 2024a](https://doi.org/10.1016/j.datak.2024.102365) (STAD) for any drift-plus-anomaly benchmark.
6. [Wagner et al. 2025](https://arxiv.org/abs/2510.17562) and [Velasco & Zafra 2026](https://doi.org/10.1016/j.neucom.2026.134154) for any metric-property claim; both need a full-text check before P1's analytic claim is made.
