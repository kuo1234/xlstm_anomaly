# Positioning table and novelty boundary

One row per retrieved paper, with the attributes that bear on the two questions this package has to
answer: **what would still be novel if the current probe hypotheses succeed**, and **which parts of
"Safe Continual Normality Adaptation" already exist under another name**.

The authoritative per-paper record — with verbatim supporting quotes, dataset/protocol notes and the
separation between what each paper demonstrates and how it was interpreted — is
`literature_records.json` (78 records). This file is the compressed view plus the conclusions drawn
from it.

## How to read it, and how not to

- **`Ev` (evidence level) governs everything else in the row.** `FT` = full text read; `AB` = abstract
  only; `SN` = search snippet or metadata only. For `AB`/`SN` rows the mechanism columns are mostly
  `?`, and **`?` means "not settleable from what was retrieved", never "no"**.
- 17 of 78 records are `AB`/`SN`, and full text was unobtainable for seven works. Their rows are
  present for family coverage and must not be cited as negative findings.
- Attribute extraction over the 61 full texts read only the first ~55-60k characters of each paper,
  so a mechanism introduced late in a long experimental section can be missed; 23 of 61 extractions
  were truncated (14 recovered by direct keyword-window reading, 9 left partially populated), and
  each record carries an `extraction_completeness` flag.
- `online_labels_available` and `requires_retraining` are the least reliably stated fields in the
  source papers and are omitted from this compressed table; consult the JSON.

Columns: **Contam** = is anomaly contamination of the update path prevented; **D!=A** = is drift
explicitly distinguished from anomaly; **Defer** = deferred/quarantined commitment; **Rb** =
rollback/reset; **Int** = model-internal state used as evidence. Values: `Y` yes, `~` partial,
`n` no / not addressed / assumed clean, `?` unknown.

| Paper | Yr | Identifier | Pub | Fam | Ev | Regime | Contam | D!=A | Defer | Rb | Int | Model-specific? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Self-Adaptive Forecasting for Improved Deep Learning on… | 2022 | arXiv:2202.02403 | pre | F1,F6 | FT | test-time | n | n | n | Y | Y | agnostic |
| When Model Meets New Normals: Test-Time Adaptation for… | 2024 | arXiv:2312.11976 | pub | F1,F2,F14 | FT | test-time | Y | Y | n | n | Y | agnostic |
| Battling the Non-stationarity in Time Series Forecasting… | 2025 | arXiv:2501.04970 | pub | F1 | FT | UNKNOWN | ? | ? | ? | ? | ? | UNKNOWN |
| Augmented Contrastive Clustering with Uncertainty-aware… | 2025 | 10.1145/3690624.3709239 | pub | F1,F7,F15 | AB | test-time | ? | n | n | ? | Y | agnostic (method… |
| COMET: Codebook-based Online-adaptive Multi-scale… | 2026 | arXiv:2602.01635 | pre | F1,F13 | FT | test-time | ? | n | ? | ? | ? | UNKNOWN |
| CANDI: Curated Test-Time Adaptation for Multivariate… | 2026 | arXiv:2604.01845 | pub | F1,F2,F7 | FT | test-time | ? | ? | ? | ? | ? | UNKNOWN |
| CALAD: Channel-Aware contrastive Learning for… | 2026 | arXiv:2605.23139 | pub | F1 | FT | offline | n | n | n | n | Y | specific:… |
| MemStream: Memory-Based Streaming Anomaly Detection | 2022 | arXiv:2106.03837 | pub | F2,F6 | FT | online/streaming | Y | Y | n | Y | Y | specific: denoising… |
| Continual Adaptation for Unsupervised Time Series Anomaly… | 2024 | 10.1109/icsp62122.2024.10743267 | pub | F2,F3 | SN | UNKNOWN | ? | ? | ? | ? | ? | UNKNOWN |
| iADCPS: Time Series Anomaly Detection for Evolving… | 2025 | arXiv:2504.04374 | pre | F2,F6 | FT | online/streaming | n | Y | n | n | Y | specific: state-space… |
| SCALE: Style-Causal Disentanglement with Adaptive… | 2026 | 10.1145/3770855.3817912 | pub | F2,F14 | AB | online/streaming | ? | Y | ? | n | Y | specific:… |
| Unsupervised real-time anomaly detection for streaming… | 2017 | 10.1016/j.neucom.2017.04.070 | pub | F3,F6,F16 | SN | online/streaming | ? | ? | ? | ? | ? | specific: HTM |
| Online anomaly detection with concept drift adaptation… | 2018 | 10.1145/3152494.3152501 | pub | F3,F6 | SN | online/streaming | ? | ? | ? | ? | ? | specific: RNN |
| Time-Series Anomaly Detection Service at Microsoft | 2019 | arXiv:1906.03821 | pub | F3,F16 | FT | online/streaming | n | n | n | n | n | specific: Spectral… |
| Adaptive Model Pooling for Online Deep Anomaly Detection… | 2022 | arXiv:2206.04792 | pub | F3 | FT | UNKNOWN | ? | ? | ? | ? | ? | UNKNOWN |
| METER: A Dynamic Concept Adaptation Framework for Online… | 2023 | arXiv:2312.16831 | pub | F3,F8,F15 | FT | online/streaming | n | Y | Y | n | Y | specific: MLP-based… |
| Continual Learning Approaches for Anomaly Detection | 2024 | arXiv:2212.11192 | pre | F3,F10 | FT | offline | n | n | n | n | n | agnostic |
| Drift-Aware Online Dynamic Learning for Nonstationary… | 2026 | arXiv:2604.09358 | pre | F3,F8 | FT | online/streaming | n | Y | Y | n | Y | specific: MS-BCNN… |
| ReCATS: Replay-Free Continual Anomaly Detection for… | 2026 | 10.1145/3770855.3817985 | pub | F3,F10 | AB | online/streaming… | ? | ? | ? | ? | ? | specific:… |
| Safety-Gated Continual Learning for Drift-Aware Anomaly… | 2026 | 10.1109/icaiset66439.2026.11541767 | pub | F3,F4,F8 | SN | online/streaming… | ? | ? | ? | ? | ? | UNKNOWN |
| A Hybrid Framework for Real-Time Data Drift and Anomaly… | UNKNOWN | arXiv:2504.18599 | pub | F4,F6,F8,F14,F15 | FT | online/streaming | n | Y | Y | Y | Y | specific:… |
| A survey on concept drift adaptation | 2014 | 10.1145/2523813 | pub | F4 | SN | online/streaming | ? | ? | ? | ? | ? | n/a |
| Drift-Aware Methodology for Anomaly Detection in Smart… | 2019 | 10.1109/access.2019.2891315 | pub | F4 | SN | UNKNOWN | ? | ? | ? | ? | ? | UNKNOWN |
| From concept drift to model degradation: An overview on… | 2022 | 10.1016/j.knosys.2022.108632 | pub | F4 | AB | online/streaming | ? | ~ | ? | ? | ~ | agnostic |
| Localizing Anomalies in Critical Infrastructure using… | 2024 | arXiv:2310.15830 | pre | F4 | FT | offline | n | n | n | n | Y | agnostic |
| State-transition-aware anomaly detection under concept… | 2024 | 10.1016/j.datak.2024.102365 | pub | F4,F14 | AB | online/streaming | ? | Y | ? | ~ | Y | specific:… |
| DriftGuard: A Hierarchical Framework for Concept Drift… | 2026 | arXiv:2601.08928 | pre | F4,F14 | FT | offline | n | Y | n | n | Y | agnostic |
| RDumb++: Drift-Aware Continual Test-Time Adaptation | 2026 | arXiv:2601.15544 | pre | F4,F9 | FT | test-time | n | n | n | Y | Y | specific: ResNet-50… |
| xLSTM: Extended Long Short-Term Memory | 2024 | arXiv:2405.04517 | pub | F5 | FT | none | n | n | n | n | n | specific: xLSTM… |
| xLSTMAD: A Powerful xLSTM-based Method for Anomaly… | 2025 | arXiv:2506.22837 | pub | F5 | FT | offline | n | n | n | n | n | specific:… |
| UNKNOWN | UNKNOWN | arXiv:2104.01478 | pre | F6 | AB | UNKNOWN | ? | ? | ? | ? | ? | UNKNOWN |
| Gate Activation Signal Analysis for Gated Recurrent… | 2017 | arXiv:1703.07588 | pre | F6 | AB | UNKNOWN | ? | ? | ? | ? | ? | UNKNOWN |
| Learning When to Adapt | 2026 | arXiv:2605.19028 | pre | F6 | FT | offline | ? | n | n | n | Y | specific: LoRA-style… |
| When the Martingale Never Stops Firing: Anytime-Valid… | 2026 | arXiv:2608.30502 | pre | F6,F8,F15 | FT | online/streaming | n | Y | Y | Y | Y | specific: a linear… |
| Efficient Test-Time Model Adaptation without Forgetting | 2022 | arXiv:2204.02610 | pub | F7,F9 | FT | test-time | Y | n | n | Y | Y | specific:… |
| NOTE: Robust Continual Test-time Adaptation Against… | 2022 | arXiv:2208.05117 | pub | F7 | FT | test-time | n | n | n | n | Y | specific: requires… |
| Towards Stable Test-Time Adaptation in Dynamic Wild World | 2023 | arXiv:2302.12400 | pub | F7,F9 | FT | test-time | n | n | n | Y | Y | agnostic |
| Continual Test-time Domain Adaptation via Dynamic Sample… | 2023 | arXiv:2310.03335 | pub | F7 | FT | test-time | n | n | n | n | ? | UNKNOWN |
| Quilt: Robust Data Segment Selection against Concept… | 2023 | arXiv:2312.09691 | pub | F7,F8 | FT | online/streaming | n | n | Y | Y | Y | specific: neural… |
| Entropy Is Not Enough for Test-Time Adaptation: From the… | 2024 | arXiv:2403.07366 | pub | F7 | FT | test-time | Y | n | n | n | Y | agnostic |
| ETAGE: ENHANCED TEST TIME ADAPTATION WITH INTEGRATED… | 2024 | arXiv:2409.09251 | pre | F7 | FT | test-time | n | n | n | n | ? | UNKNOWN |
| Stream-based Active Learning with Verification Latency in… | 2022 | arXiv:2204.06822 | pub | F8 | FT | online/streaming | n | n | Y | n | Y | agnostic |
| Self-Adaptive Anomaly Detection with Reinforcement… | 2026 | arXiv:2607.08373 | pub | F8 | FT | online/streaming | Y | Y | Y | n | n | specific: factorized… |
| Reliability-Gated Source Anchoring for Continual… | UNKNOWN | arXiv:2605.14063 | pre | F9 | FT | test-time | n | n | n | Y | Y | agnostic |
| Continual Test-Time Domain Adaptation | 2022 | arXiv:2203.13591 | pub | F9 | FT | online/streaming | ? | ? | ? | ? | ? | UNKNOWN |
| A Probabilistic Framework for Lifelong Test-Time… | 2023 | arXiv:2212.09713 | pub | F9 | FT | test-time | n | n | n | Y | Y | agnostic |
| RDumb: A simple approach that questions our progress in… | 2023 | arXiv:2306.05401 | pre | F9 | FT | test-time | n | n | n | Y | Y | agnostic |
| When and Where to Reset Matters for Long-Term Test-Time… | 2026 | arXiv:2603.03796 | pub | F9,F15 | FT | test-time | n | n | n | Y | Y | agnostic |
| ONER: Online Experience Replay for Incremental Anomaly… | 2024 | arXiv:2412.03907 | pre | F10 | FT | offline | n | n | n | n | Y | specific: pretrained… |
| ReplayCAD: Generative Diffusion Replay for Continual… | 2025 | arXiv:2505.06603 | pub | F10 | FT | offline | n | n | n | n | n | agnostic |
| CADIC: Continual Anomaly Detection Based on Incremental… | 2025 | arXiv:2511.08634 | pre | F10,F13 | FT | offline | ? | ? | ? | ? | ? | UNKNOWN |
| DeCoFlow: Structural Decomposition of Normalizing Flows… | 2026 | arXiv:2606.26687 | pub | F10 | FT | offline | n | n | n | n | Y | specific:… |
| Unsupervised Continual Anomaly Detection with… | 2024 | arXiv:2401.01010 | pub | F11,F13 | FT | offline | ? | ? | ? | ? | ? | UNKNOWN |
| Continual-MEGA: A Large-scale Benchmark for Generalizable… | 2026 | arXiv:2506.00956 | pre | F11 | FT | offline | ? | ? | ? | ? | ? | UNKNOWN |
| Normality-Preserving Continual Industrial Anomaly… | 2026 | arXiv:2606.02042 | pre | F11 | FT | offline | n | n | n | n | Y | specific: Stable… |
| TaskFusion: Continual Anomaly Detection for Heterogeneous… | 2026 | arXiv:2606.11844 | pre | F11 | FT | offline | n | ? | ? | ? | ? | UNKNOWN |
| Towards Principled Continual Anomaly Detection: A… | 2026 | arXiv:2607.18289 | pre | F11 | FT | offline | n | Y | n | n | n | agnostic |
| Neural-Collapse-guided Task-Free Continual Anomaly… | 2026 | arXiv:2609.03406 | pre | F11 | FT | online/streaming | n | Y | n | n | n | specific: frozen DINO… |
| Generalized Out-of-Distribution Detection: A Survey | UNKNOWN | arXiv:2110.11334 | pre | F12,F14 | FT | UNKNOWN | ~ | Y | n | n | Y | agnostic |
| AnoShift: A Distribution Shift Benchmark for Unsupervised… | 2022 | arXiv:2206.15476 | pub | F12,F14 | FT | offline | n | n | n | n | Y | agnostic |
| Anomaly Detection under Distribution Shift | 2023 | arXiv:2303.13845 | pub | F12 | FT | test-time | n | n | n | n | Y | specific: built on… |
| Open-Set Multivariate Time-series Anomaly Detection | 2024 | arXiv:2310.12294 | pub | F12 | FT | offline | n | n | n | n | n | specific: TCN-based… |
| DualNet: Continual Learning, Fast and Slow | 2021 | arXiv:2110.00175 | pre | F13 | FT | online/streaming | n | n | Y | n | Y | specific: ResNet18… |
| Learning Fast, Learning Slow: A General Continual… | 2022 | arXiv:2201.12604 | pub | F13 | FT | online/streaming | n | ? | n | n | Y | agnostic |
| Conformal Uncertainty Indicator for Continual Test-Time… | 2025 | arXiv:2502.02998 | pre | F15 | FT | test-time | ? | ? | ? | ? | ? | UNKNOWN |
| Segmented Confidence Sequences and Multi-Scale Adaptive… | 2025 | arXiv:2508.06638 | pre | F15 | FT | online/streaming | n | Y | n | n | n | agnostic |
| Precision and Recall for Time Series | 2018 | arXiv:1803.03639 | pub | F16 | FT | none | n | n | n | n | n | agnostic |
| Towards a Rigorous Evaluation of Time-series Anomaly… | 2022 | arXiv:2109.05257 | pub | F16 | FT | none | n | n | n | n | n | agnostic |
| Navigating the Metric Maze: A Taxonomy of Evaluation… | 2023 | arXiv:2303.01272 | pub | F16 | FT | none | n | n | n | n | n | agnostic |
| Multivariate Time Series Anomaly Detection: Fancy… | 2023 | arXiv:2308.13068 | pub | F16 | FT | none | n | n | n | n | n | agnostic |
| StreamAD: A cloud platform metrics-oriented benchmark for… | 2023 | 10.1016/j.tbench.2023.100121 | pub | F16 | AB | online/streaming | n | ? | n | n | ? | agnostic |
| The Elephant in the Room: Towards A Reliable Time-Series… | 2024 | 10.52202/079017-3437 | pub | F16 | SN | none | ? | ? | ? | ? | ? | UNKNOWN |
| Deep Learning for Time Series Anomaly Detection: A Survey | 2024 | 10.1145/3691338 | pub | F16 | AB | none | ? | ? | ? | ? | ? | n/a |
| VUS: Effective and Efficient Accuracy Measures for… | 2025 | arXiv:2502.13318 | pre | F16 | FT | none | n | n | n | n | n | agnostic |
| An Improved Time Series Anomaly Detection by Applying… | 2025 | arXiv:2509.20184 | pre | F16 | FT | offline | n | n | n | n | n | agnostic |
| MSAD: A Deep Dive into Model Selection for Time series… | 2025 | arXiv:2510.26643 | pub | F16 | FT | offline | n | n | n | n | n | agnostic |
| TAB: Unified Benchmarking of Time Series Anomaly… | 2025 | 10.14778/3746405.3746407 | pub | F16 | SN | none | ? | ? | ? | ? | ? | UNKNOWN |
| Did We Actually Fix It? An Independent Adversarial… | 2026 | arXiv:2607.11969 | pre | F16 | FT | none | n | n | n | n | n | agnostic |


---

## What the table computes

Counts over all 78 records (`Y` / `~` / `n` / `?`):

| Attribute | yes | partial | no | unknown |
|---|---|---|---|---|
| Contamination of the update path prevented | 5 | 1 | 46 | 25 (+1 other) |
| Drift explicitly distinguished from anomaly | 15 | 1 | 39 | 23 |
| Deferred / quarantined commitment | 8 | 0 | 45 | 25 |
| Rollback / reset | 12 | 1 | 41 | 24 |
| Model-internal state used as evidence | 34 | 1 | 18 | 25 |

The single most informative line is the last one: **using a model-internal quantity as adaptation
evidence is the majority practice, not a gap** — 34 of 78 records do it explicitly, and the 18 `n`
values are concentrated in benchmarks, surveys and evaluation critiques rather than in mechanism
papers.

Restricting to the 61 full-text records, where an `n` is informative rather than merely unretrieved:

- **4 records combine internal-state evidence + deferred commitment + an explicit drift-versus-anomaly
  distinction**: METER (`arXiv:2312.16831`), the HTM+SPRT hybrid framework (`arXiv:2504.18599`),
  drift-aware online dynamic learning (`arXiv:2604.09358`), and anytime-valid martingale gating
  (`arXiv:2608.30502`).
- **2 of those 4 also include rollback/reset**: `arXiv:2504.18599` and `arXiv:2608.30502`. In other
  words the full four-part mechanism shape the project assumes is *already instantiated twice* in the
  retrieved literature — in both cases on simple detectors (hierarchical temporal memory; a linear
  Kalman filter) rather than on a learned deep multivariate detector.
- **0 records describe measuring the causal cost of admitting a true anomaly into a normality buffer
  under a prespecified harm margin.** A keyword sweep for causal/harm-margin language across the
  contamination and contribution fields returns exactly one hit, and it is SCALE's method name
  ("style-causal disentanglement"), not harm accounting.

Those three computed facts are the backbone of the novelty assessment below. Their limits are the
25 records with unknown mechanism attributes and the 7 works whose full text was unobtainable — so
each is a statement about what was retrieved, not a proof of absence.

---

## Answer to (a): what would remain novel if the probe hypotheses succeed

Four separable claims, ordered from strongest to weakest, each with the prior art it must clear.

**A1. Internal-state evidence for drift-versus-anomaly, treated as a measurement.** The retrieved
literature uses internal quantities as *gates* — entropy, Fisher information, batch-norm statistics,
latent Mahalanobis distance, codebook activation, evidential uncertainty, filter innovation — and
validates them only through downstream task performance. What is absent is the prior question posed
as a measurement: given frozen detectors and evaluator-side truth about which changes are drift and
which are anomalies, how much incremental information do internal summaries carry *beyond
score-and-history controls*? The novel objects are the control set, the frozen-detector design that
removes adaptation as a confound, and a protocol willing to report a null. **Must clear:** F7/F9/F15
on "internal signals are usable" (established — so the claim cannot be that), and `arXiv:2608.30502`
on "internal state can feed a drift-versus-anomaly decision" (established as a construct — so the
claim must be measurement, not construction).

**A2. The xLSTM-specific version of that measurement.** Nothing retrieved connects xLSTM's
exponential gating or matrix memory to drift, anomaly or adaptation: the xLSTM-TSAD literature is two
papers, the architecture paper (`arXiv:2405.04517`, no AD or drift claim) and xLSTMAD
(`arXiv:2506.22837`, offline, no adaptation, no internal-state use). A capacity-matched comparison
against a conventional LSTM under one probe and one control set would be the first published evidence
either way. **Least threatened by prior art, most threatened by external validity** — a difference
between two backbones on a synthetic stream is not a statement about deployed detectors.

**A3. Causal contamination accounting.** Deferral mechanisms exist and admission guards exist; the
*accounting* does not. No retrieved record measures the causal cost of an admitted anomaly against a
prespecified margin, and the closest anchor — CANDI — reports contamination as present and argues
only for robustness to it, listing failure recovery as future work. A contribution here is an
evaluation contract (controlled contamination interventions, a prespecified margin, effect sizes with
uncertainty, separate exposure denominators), not a new gate. **This claim survives a null on A1 and
A2**, because it is about what is measured.

**A4. The combination as a deployable mechanism.** Gated admission on measured internal evidence,
commitment deferred until a sequential test resolves, and a reversal that does not discard a
legitimately learned new normal. Every component is occupied separately, and — per the computed
cross-tab — the full four-part shape is already instantiated twice on simple detectors. What is
genuinely unoccupied is the **reset semantics**: every reset mechanism retrieved reverts toward a
*fixed source model*, none reverses a single normality commitment while preserving others.
**"Not yet combined" is the weakest form of novelty** and becomes a contribution only if the
components are shown to be load-bearing — which is what A1 is testing.

---

## Answer to (b): which parts already exist under another name

| Project component | Already published as | Retrieved instances | Disposition |
|---|---|---|---|
| Admission control on a normality buffer using a model-internal quantity | curated / selective test-time adaptation; codebook-evidence filtering; score-masked updating; threshold-gated memory | CANDI (`10.1609/aaai.v40i17.38524`), COMET (`arXiv:2602.01635`), M2N2 (`arXiv:2312.11976`), MemStream (`arXiv:2106.03837`) | **Baselines, not related work.** A mechanism paper that does not compare against these has no admission contribution. |
| Deferring the adapt/ignore decision until evidence accumulates | sequential testing on the detector's own output; accumulate-then-commit; post-drift waiting; verification latency | HTM+SPRT (`arXiv:2504.18599`), martingale gating (`arXiv:2608.30502`), METER (`arXiv:2312.16831`), Quilt (`arXiv:2312.09691`), stream-based AL with verification latency (`arXiv:2204.06822`) | **Prior art for the construct.** Novelty can only be in what the deferral is shown to buy. |
| Reset / rollback triggered by internal drift evidence | continual test-time adaptation with restore | CoTTA (`arXiv:2203.13591`), EATA (`arXiv:2204.02610`), SAR (`arXiv:2302.12400`), PETAL (`arXiv:2212.09713`), RDumb (`arXiv:2306.05401`), adaptive selective reset (`arXiv:2603.03796`), RDumb++ (`arXiv:2601.15544`) | **Solved sub-problem** for reset *timing*; open only for reset *semantics* under normality change. |
| Stable/plastic dual memory | continual-learning architecture | DualNet (`arXiv:2110.00175`), CLS-ER (`arXiv:2201.12604`); in AD as prototypes/coresets/codebooks (`arXiv:2401.01010`, `arXiv:2511.08634`, `arXiv:2602.01635`) | **Standard architecture.** No novelty in the split itself; the open part is the gating policy for entry under contaminated input. |
| The framing "learn the new normal without learning the anomaly" | online separation of domain drift from true anomalies | SCALE (`10.1145/3770855.3817912`) — two decoupled model-derived criteria, unobserved shift times, expandable expert pool | **Anticipated.** The framing cannot be the contribution. |
| Multi-regime continual MTSAD with normality preservation | replay-free continual MTSAD; normality-preserving continual AD | ReCATS (`10.1145/3770855.3817985`), orthogonal-LoRA normality preservation (`arXiv:2606.02042`), principled continual AD (`arXiv:2607.18289`) | **Adjacent and assumes clean per-task normal data** — precisely the assumption the admission question examines. |

---

## Three things to do before any novelty claim is written

1. **Read SCALE in full** (`10.1145/3770855.3817912`). It was assessed at abstract level and it is the
   closest framing prior art. If it evaluates its drift-versus-anomaly separation against
   timestamp-level truth, claim A1's novelty narrows sharply; if the separation is asserted by
   construction, A1 stands.
2. **Obtain the safety-gated CPS paper** (`10.1109/icaiset66439.2026.11541767`), retrieved as metadata
   only. Its title names the project's mechanism family in one phrase and it cites M2N2. This is the
   single largest unquantified novelty risk in the map.
3. **Re-check the project's own external-benchmark citation at source.** The drift benchmark named in
   the protocol ("StrAD / TSB-drift") did not resolve to a drift benchmark in this search: "StrAD"
   returns a streaming audio-description benchmark (`arXiv:2608.12549`, a search hit noted in the
   sweep's coverage record and not itself entered as a relevant paper) and a structural-similarity
   TSAD method (`arXiv:2509.20184`), and "TSB-drift" returns nothing. The A2 files themselves are real
   and hashed in `reports/phase_a_v4/manifest.json`, so this is a *citation* question, not a data
   question — but a paper cannot cite a benchmark by a name that does not resolve. The nearest
   retrievable artefacts are TSB-AD (`10.52202/079017-3437`), TAB (`10.14778/3746405.3746407`) and
   AnoShift (`arXiv:2206.15476`).
