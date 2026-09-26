# Candidate stories

The eight requested stories (A–H) were tested against the literature up to 2026-09-26. Seven further stories (N1–N7) were derived from gaps found during the search, and all fifteen were then merged into five programme stories (P1–P5). A story survives only if it asks a question the literature has not answered. A new arrangement of known components does not count. Full cards are in [story_cards.md](story_cards.md).

## Disposition of the requested stories

| Story | One-line question | Status | Where it goes |
|---|---|---|---|
| A. Reversible normality lifecycle | Does explicit lifecycle state management improve the absorption–delay frontier? | `PROMISING_BUT_THREATENED` only as "does reversibility beat delay?"; `WEAK / COMPONENT_ONLY` as a mechanism | P2 |
| B. Risk-constrained adaptation | Minimise benign delay subject to a fault-absorption budget | `PROMISING_BUT_THREATENED` | P2 (core) |
| C. `ADAPT / FREEZE / UNRESOLVED` | Abstain when evidence is insufficient | `WEAK / COMPONENT_ONLY` | P2 action space |
| D. Context-authorized normality | Promote only what trusted context explains | `PROMISING_BUT_THREATENED` | P3 |
| E. Recurrence without forgetting | Recover A after A→B→A without letting faults into memory | `ALREADY_OCCUPIED` | P1 evaluation axis |
| F. Normal-only commissioning | Few verified-normal target samples | `ALREADY_OCCUPIED` (method); `PROMISING_BUT_THREATENED` (protocol) | P5 |
| G. Semantic-shift benchmark | Score adaptation decisions rather than point accuracy | `PROMISING_BUT_THREATENED` (taxonomy); `STRONG_CANDIDATE` (identifiability-stratified) | P1 |
| H. Resource-constrained continual TSAD | Joint quality, retention, frequency and energy | `ALREADY_OCCUPIED` | dropped |

### What changed relative to the pre-existing boundaries

Four findings move the boundaries beyond the Issue #1 audit.

First, lifecycle-with-rollback is published outside TSAD at full generality. [Qin et al. 2026](https://arxiv.org/abs/2604.08059) builds a seven-stage candidate-to-rollback pipeline and reports unsafe activation against success. [Aftab et al. 2026](https://arxiv.org/abs/2607.02687) commits provisional adaptations only when macro-F1 holds. [Su et al. 2026](https://arxiv.org/abs/2607.27773) versions agent memory and evaluates post-exposure rollback. The TSAD residual is therefore narrower than "a lifecycle". It is whether reversibility helps when the rollback trigger is delayed external evidence rather than an online oracle.

Second, the Story E mechanism is occupied inside unsupervised streaming TSAD itself. [Li et al. 2026b](https://doi.org/10.1016/j.knosys.2026.116530) classifies sudden, incremental and recurrent drift and reuses a bounded model pool, explicitly to stop recurring regimes being overwritten.

Third, "should this be adapted?" became an active TTA question in the six weeks before the cutoff: [Majumdar & Saha 2026](https://arxiv.org/abs/2608.22233), [Jiang et al. 2026](https://arxiv.org/abs/2609.08367) and [Wang et al. 2026a](https://arxiv.org/abs/2609.20700). Monitoring an adapting model's risk without labels was already published ([Schirmer et al. 2025](https://doi.org/10.52202/085713-2705)). Story C cannot stand alone.

Fourth, Story H's joint axes are measured for TSAD by [Smendowski et al. 2026](https://doi.org/10.1007/s10723-026-09846-5), published online on 2026-09-01.

## Discovered stories (gap-derived)

Each discovered story comes from one of the discovery patterns in the brief. The pattern is named in brackets.

- **N1. Promotion rules as an attack surface.** [Two areas with an unaddressed interface] Poisoning of online normality models ([Kloft & Laskov 2012](https://arxiv.org/abs/1003.0078), [Rubinstein et al. 2009a](https://doi.org/10.1145/1644893.1644895), [Cong et al. 2024](https://arxiv.org/abs/2308.08505)) meets staged safe-adaptation rules that publish an acceptance specification. No located work prices the attack on that specification. `PROMISING_BUT_THREATENED`.
- **N2. Peer-corroborated normality.** [A theoretically identifiable subproblem not evaluated] Boundary #4 permits identification with independent measurements. Fleet peers are such measurements for common causes, yet fleet AD ([de Novaes Pires Leite et al. 2023](https://doi.org/10.1016/j.engappai.2023.106859), [Tveten et al. 2022](https://doi.org/10.1214/21-aoas1508), [Stavrou et al. 2009](https://doi.org/10.1145/1654988.1655000)) never states when peer synchrony licenses promotion. `PROMISING_BUT_THREATENED`.
- **N3. Interventional disambiguation.** [Two areas with an unaddressed interface] Auxiliary signal design ([Nikoukhah & Campbell 2003](https://doi.org/10.23919/ecc.2003.7085087)) restores identifiability, but TSAD uses it only for offline data generation ([Wang et al. 2025b](https://doi.org/10.1016/j.engappai.2025.111991)). `WEAK / COMPONENT_ONLY`.
- **N4. Query-budgeted regime authorisation.** [An operational requirement systematically omitted] Budgeted feedback exists only at instance level ([Das et al. 2018](https://arxiv.org/abs/1809.06477), [Perini et al. 2023](https://arxiv.org/abs/2301.02909)). Latency is studied for classification ([Castellani et al. 2022](https://arxiv.org/abs/2204.06822)). Regime-level queries with latency are missing. `PROMISING_BUT_THREATENED`.
- **N5. Retroactive decontamination.** [An operational requirement systematically omitted] Rollback discards later legitimate learning, while unlearning may leave residue. [Du et al. 2019](https://doi.org/10.1145/3319535.3363226) already corrects wrongly-normal samples in lifelong AD, so only the regime-level, continuous-state version against a rollback baseline remains. `PROMISING_BUT_THREATENED`.
- **N6. Adaptation-induced masking.** [A failure mode no TSAD method manages] Adaptation can hide *other* faults that resemble an absorbed regime. Existing measures are generic forgetting ([Li et al. 2022](https://doi.org/10.1145/3503161.3548232)) or per-event diagnosis ([Anzai & Pinto 2026](https://doi.org/10.3390/pr14050859)). `PROMISING_BUT_THREATENED`.
- **N7. Contamination-blind evaluation.** [An invalid common evaluation assumption] Under point adjustment, a detector that alarms at the onset of a persistent fault and then absorbs it gets full segment credit. Metric critiques ([Kim et al. 2022](https://doi.org/10.1609/aaai.v36i7.20680), [Wagner et al. 2025](https://arxiv.org/abs/2510.17562), [Lyu 2026](https://arxiv.org/abs/2607.11969)) have not analysed the interaction with test-time adaptation. `STRONG_CANDIDATE` (inside P1).

Proposals from the literature tracks that were folded rather than kept separate:

- *Real-stream stress test of anytime-valid TTA monitors* (Risk track). The project's own anchor [Han & Qu 2026](https://arxiv.org/abs/2608.30502) already reports the key failure (135/135 clean-stream firings), so this becomes a P2 baseline condition.
- *Red-teaming the authorisation channel* (Context track). Folded into P3's adversarial arm.
- *Adversarial-recurrence identifiability benchmark* and *context-gated regime classification* (Lifecycle and Benchmark tracks). These are P1.
- *Commissioning failure-mode diagnosis* (Transfer track). Folded into P5.
- *Energy-accounting standardisation* (Benchmark track). Dropped as too small to stand alone.

## Programme stories

| ID | Title | Merges | Status |
|---|---|---|---|
| P1 | Identifiability-stratified, contamination-aware evaluation of adaptive TSAD | G, N7, N6, E-axis, D-axis | `STRONG_CANDIDATE` |
| P2 | Adaptation under a budget of unverified influence (delayed confirmation, reversibility vs delay) | A, B, C, N4, N5 (+N1, N3) | `PROMISING_BUT_THREATENED` |
| P3 | Authorisation-scoped promotion and coincident-fault absorption | D, N4 | `PROMISING_BUT_THREATENED` |
| P4 | Peer-corroborated normality under adversarial fleets | N2, N1 | `PROMISING_BUT_THREATENED` |
| P5 | Normal-only commissioning protocol with a certified stopping rule | F | `PROMISING_BUT_THREATENED` |
