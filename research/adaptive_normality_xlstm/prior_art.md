# Prior-art search and literature audit

**Search cutoff:** 2026-09-24. This is a focused, reproducible search record, not a claim that every paper in every language or venue has been found.

## Search method and coverage

Discovery used scholarly web search and citation chaining, with primary-source checks on arXiv, OpenReview, AAAI proceedings, ICLR proceedings, NeurIPS proceedings, PMLR/ICML, IJCAI, IEEE ICDM records, ACM KDD records, publisher pages (ScienceDirect and Springer), university repositories, and author GitHub repositories where available. Google-Scholar-equivalent scholarly discovery was used through indexed scholarly records/citation pages and paper metadata; primary proceedings or publisher pages were preferred for claims. The search also checked exact combinations of “new normal,” “test-time adaptation,” “quarantine,” “selective update,” “candidate regime,” “model pool,” “recurrent drift,” “multi-horizon forecasting,” and “normal memory.” It was not a systematic review with a formal PRISMA protocol.

**Coverage count:** 37 unique papers, theses, surveys or technical reports are positioned below or in novelty_matrix.md, plus benchmark/dataset resources. “Read/positioned” means the abstract and available method/venue details were inspected; papers explicitly marked abstract-only were not treated as fully audited implementations. Code was checked for the closest works where a public repository was found. The 37-source count excludes duplicate arXiv/venue versions and excludes datasets.

### Source and version caveats

- The mandatory ICLR 2026 one-liners paper is published in the official ICLR proceedings. Its headline comparison is directly relevant: for five time-series foundation-model families and varied size/context, reconstruction/forecast anomaly detection did not significantly outperform moving-window variance or squared difference. Its claim should be scoped to the models, datasets and protocol it studied, not generalized automatically to every trained recurrent forecaster.
- xLSTMAD is an ICDM 2025 paper with arXiv full text and a public GitHub implementation. It has two variants: xLSTMAD-R reconstructs its input; xLSTMAD-F iteratively forecasts future values. “Forecasting” here does not establish persistent state across successive deployment windows.
- M2N2 is peer-reviewed at AAAI 2024 and has an official repository. It explicitly names the “new normal problem”; therefore this phrase and the broad problem framing are prior art.
- CANDI is a peer-reviewed AAAI 2026 paper and public GitHub code was located. Its curated, selective TTA closely overlaps safe adaptation of putative false positives.
- MemTTA is a February 2026 master's thesis in the Korea University repository, not a peer-reviewed conference paper found in this search. Its abstract describes a normal-pattern memory updated during inference with selective updates intended to reduce anomaly contamination. It is a serious architecture overlap signal, but its publication type and available validation should not be conflated with a top-tier conference paper.
- PAMA was available as an OpenReview paper under ICLR 2026 review / preprint by the audit cutoff. Its two memories encode normal and generated pseudo-anomalous prototypes during learning. It is not live quarantine memory. PC-UAD is a 2026 journal article describing a learned normal prototype dictionary and synthetic negative contrastive learning, not online regime promotion.
- AnDri was found as an arXiv extended report and author-hosted paper/code materials. It explicitly combines anomaly detection and concept drift with a dynamic normal-pattern model. Venue status was not inferred from the extended report.
- ADAPTS was discovered on a ScienceDirect record whose publication date shown by the result is 2026-09-27, three days after this audit cutoff. That record is excluded from the as-of-date novelty verdict. Its described functions overlap prior drift/model-pool approaches, so this exclusion does not create a gap.
- A 2026 IEEE CPS safety-gated online adaptation item was discoverable by DOI/abstract records, but its full text could not be independently inspected in this pass. It is included as abstract-only caution in the matrix, not used to support a fine-grained claim.
- The ACM E-Energy 2026 smart-building study was inspected from its publication record and accessible paper details. It directly separates normal operation, normal drift and attack and updates selectively, but uses 100 labeled examples per class to map clusters to semantics. It is the closest direct Problem B paper found in this audit.
- WWW 2026 contributes both streaming TSAD with an evolving proxy (DESS) and online forecasting with recurring/emergent drift experts (DynaME). These increase the overlap on online memory/model reuse and forecast under drift, respectively.

## Findings by question

### xLSTM and anomaly detection / forecasting

The original xLSTM paper introduces sLSTM and mLSTM variants with modified gates and memory structures; it is an architecture paper, not a normal-only transfer or adaptive anomaly-detection method. xLSTMTime and xLSTM-Mixer apply xLSTM-style blocks to time-series forecasting, showing the backbone is not limited to reconstruction. Neither establishes anomaly-specific online state protection or safe promotion of new regimes.

xLSTMAD is the direct xLSTM anomaly baseline. Its reconstruction and iterative forecasting variants should be compared as distinct score-generating methods. Its public implementation currently emphasizes reconstruction, while the paper reports both variants. The paper does not establish a few-shot target-normal adaptation curve, an online quarantine gate, semantic benign-drift detection, or model-pool retention.

The ICLR 2026 one-liners audit makes forecasting error an empirical hypothesis, not an assumed anomaly signal. It reports that popular TS foundation models under the evaluated settings do not significantly beat moving-window variance/squared difference for reconstruction/forecast anomaly scoring. It discusses that a single-step rolling forecast can cease to find an anomaly surprising after anomalous observations enter context; longer horizons can delay detection and accumulate uncertainty. It motivates measuring point, segment, onset and context-contamination effects directly. Its results do not prove xLSTM forecasting is ineffective, but they make simple baselines and horizon ablations mandatory.

Forecast error is only one scoring family. Latent/representation evidence is already used in MTSAD: MEMTO combines input-space and latent-space deviation; prototype methods such as MEMTO, PAMA and PC-UAD compare representations with learned normal (and, for PAMA, synthetic pseudo-anomaly) prototypes; CANDI uses latent distance to curate adaptation samples. These scores can catch relational changes that a per-channel residual misses, but they can also treat a benign domain shift as novelty or absorb anomalies into a learned representation. A later detector study should report forecast, input reconstruction and representation/prototype scores separately before combining them. Latent novelty is not semantic evidence that a regime is a fault or is safe to promote.

### New normal, test-time adaptation and selected updates

M2N2 is the most important problem-level prior. It describes the same high-level issue—normality evolves between training and test—and applies trend estimation and self-supervised test-time updates. It demonstrates that the broad “adapt to new normal” question is not new. Its update criterion is model-based and therefore exposed to false-normal admission; it does not supply semantic evidence that a persistent, predictable shift is safe.

CANDI directly studies TTA for multivariate TSAD under distribution shift. It mines candidate false positives using anomaly score and latent similarity to normal validation samples, then trains a low-capacity spatiotemporal adapter while keeping the backbone fixed. This overlaps selective updates, retaining a protected detector and using a selected target subset. Its target test stream is unlabeled for adaptation, but no semantic oracle distinguishes legitimate new normal from persistent stable anomaly.

MemTTA's thesis abstract describes a neural memory of normal patterns that updates online, with selective gating intended to mitigate memory contamination. That makes “normal memory plus selective update” itself non-novel as a block concept. The accessible abstract is insufficient to assert it has an explicit quarantine or candidate-regime state, persistent recurrent state, or semantics-aware promotion.

The closest direct match to the **Problem B** core is *Drift-Aware Online Anomaly Detection in Smart Buildings via Temporal Variational Autoencoder Gradient Profile* (ACM E-Energy 2026). It explicitly separates normal operation, normal drift and attack for a building-management/HVAC stream, uses a normal-trained TCN-VAE and input-gradient profiles, maps clusters to the three semantic classes, and updates only on samples classified as normal or drift. Its reported classifier uses a small labeled anchor set of 100 samples per class (normal, normal drift, attack); code is public. It therefore demonstrates the central drift-versus-attack selective-update behavior in a specific CPS setting, while not solving the candidate's **normal-only target warm start** setting. It is not evidence that unlabeled observations alone resolve intent, and its cross-floor evaluation is not general cross-machine transfer.

SDA (spectral decomposition and adaptation for non-stationary TSAD) and FS-ADAPT cover non-stationary adaptation/domain transfer using different decomposition or few-shot/domain-adaptation setups. They reinforce that adaptation is an existing direction, but they do not appear to solve the combined semantic decision in Problem B. iADCPS uses incremental meta-learning and limited evolving-normal samples for cyber-physical systems; DoKnowAD studies transfer knowledge from auxiliary data and notes negative transfer/semantic mismatch risks. These are relevant to Problem A but do not justify xLSTM-specificity.

### Concept drift, recurring normality and model pools

AnDri is a particularly close conceptual overlap: it frames the difficulty of telling concept drift from anomalies, dynamically activates/deactivates/adds normal patterns, and aims to handle abrupt, gradual and recurring drift. It is a pattern/clustering model rather than a recurrent forecasting model. Its own problem analysis explicitly recognizes drift–anomaly ambiguity, including recurring anomalies that mimic new normal patterns.

ARCUS (KDD 2022) performs online deep anomaly detection with concept-driven inference and drift-aware updates to a model pool. Its base can be an autoencoder and the paper notes that other models such as RNNs could instantiate it. This is strong prior art for historical model reuse and evolving streams. It does not provide a semantic guarantee that a new concept is benign.

ADA-ADF and recent drift-aware stream methods classify sudden, incremental and recurrent shifts and choose update/reuse strategies. ADAPTS as described in a future-dated publisher record likewise integrates drift detection/classification, adaptation, and bounded historical model reuse; it is excluded from cutoff. General continual/concept-drift learning already distinguishes abrupt, gradual, incremental and recurrent drift and studies parameter-update/model-structure strategies. A time-series anomaly method can inherit this large literature even when its detector backbone changes.

Two WWW 2026 results further narrow the composition claim. *Evolving Proxy Kills Drift* (DESS) is a streaming TSAD framework that preserves historical knowledge through evolving synthetic proxies and uses lightweight parameter-efficient adaptation; it supports cross-domain stream sequences. It does not provide semantic benign-drift-versus-attack promotion. *Dynamic Multi-period Experts* (DynaME) is an online forecaster that explicitly handles recurring versus emergent drift with historical period experts and a general expert. It is not an anomaly detector, but it overlaps forecast-under-drift and regime reuse.

### Memory and normal prototypes

MEMTO, the ICML prototype-oriented MTSAD work, MemMambaAD, PAMA and PC-UAD establish many forms of learned normal-pattern memory or prototype dictionaries. Their usual purpose is training-time reconstruction, representation or contrastive discrimination. PAMA adds a pseudo-anomaly prototype memory generated from synthetic perturbations. Those are not the same as storing live suspicious samples in quarantine, and must not be described as such.

MemStream and streaming anomaly detectors demonstrate memory update policies under online operation. METER explores deferred/accumulate-commit concepts in streaming detection. These works are relevant to write policies, but a memory module alone does not solve the semantic normal-versus-persistent-fault problem. The minimum design should therefore avoid a “second memory” unless it serves a distinct, measurable purpose.

## Full-system overlap audit

The candidate list combines recurrent state, anomaly detection, multi-horizon forecasting, source normal pretraining, a small confirmed-normal target warm start, selective online update, quarantine, persistent-shift/candidate-regime logic and retention of past normal regimes.

No single publicly available work inspected here was found to present and validate all ten elements in exactly that configuration. That is a bounded search finding, not proof that none exists. More importantly, the candidate’s principal scientific claims are already distributed across close prior art:

- new normal plus test-time update: M2N2;
- score/latent-selected target adaptation with frozen base: CANDI;
- online normal memory with selective contamination protection: MemTTA thesis;
- normal-pattern activation and recurring drift: AnDri;
- deep detector plus model pool for evolving streams: ARCUS;
- explicit normal prototypes: MEMTO, MemMambaAD, PC-UAD;
- normal and synthetic anomaly dual prototypes: PAMA;
- recurrent multi-step forecasting/adaptation: older online RNN-AD work and broader online forecasting / drift literature;
- normal-only transfer and limited evolving-normal learning: iADCPS and few-shot/domain adaptation work.

A recombination of these blocks is not a novelty claim by itself. A plausible remaining contribution would need to be narrowly stated and experimentally distinguished—for example, a rigorous same-D cross-machine target-normal sample-efficiency evaluation with matched LSTM/GRU/SSM baselines, or a metadata-conditioned, semantically labeled test of selective regime promotion. Whether that protocol is publishable novelty remains unresolved until venue-specific citation tracing and a source-data audit.

Problem B should not be pitched as the first system to distinguish benign drift from attacks or selectively update a detector: the ACM E-Energy 2026 study already does so with limited examples of all three classes. A defensible difference would need to be explicit, such as removing the need for labeled drift/attack anchors while retaining trustworthy semantics, or showing transfer efficiency from source machines using only confirmed-normal target samples. The first cannot be guaranteed for observationally equivalent processes; the second remains an empirical question.

## Selected references

1. [xLSTM, NeurIPS 2024 / arXiv 2405.04517](https://arxiv.org/abs/2405.04517); [official code](https://github.com/NX-AI/xlstm).
2. [xLSTMAD, ICDM 2025 / arXiv 2506.22837](https://arxiv.org/abs/2506.22837); [author code](https://github.com/Nyderx/xlstmad).
3. [xLSTMTime, arXiv 2407.10240](https://arxiv.org/abs/2407.10240).
4. [xLSTM-Mixer, arXiv 2410.16928](https://arxiv.org/abs/2410.16928).
5. [When Foundation Models are One-Liners, ICLR 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/cf70320e93c08b39b1b29a348097a376-Abstract-Conference.html); [replication data](https://rdr.kuleuven.be/dataset.xhtml?persistentId=doi%3A10.48804%2FMCVI4N).
6. [M2N2, AAAI 2024](https://ojs.aaai.org/index.php/AAAI/article/view/29210); [arXiv](https://arxiv.org/abs/2312.11976); [official code](https://github.com/carrtesy/M2N2).
7. [CANDI, AAAI 2026](https://ojs.aaai.org/index.php/AAAI/article/view/38524); [official code](https://github.com/kimanki/CANDI).
8. [MemTTA, Korea University master's thesis, 2026](https://dc.korea.ac.kr/srch/srchDetail/000000308007).
9. [AnDri, arXiv extended report](https://arxiv.org/abs/2506.15831); [author-hosted paper](https://www.cas.mcmaster.ca/~fchiang/pubs/andri.pdf); [code](https://github.com/mac-dsl/AnDri).
10. [ARCUS, KDD 2022](https://arxiv.org/abs/2206.04792); [official code](https://github.com/kaist-dmlab/ARCUS).
11. [AnoShift, NeurIPS Datasets & Benchmarks 2022](https://proceedings.neurips.cc/paper_files/paper/2022/hash/d3bcbcb2a7b0b4716bf24ce4b2ea8d60-Abstract.html); [code](https://github.com/bit-ml/AnoShift).
12. [MemMambaAD, Engineering Applications of AI, 2025](https://www.sciencedirect.com/science/article/pii/S0952197625013107).
13. [PAMA, OpenReview ICLR 2026 under review](https://openreview.net/pdf?id=YTgJA2m5B0).
14. [PC-UAD, CMC 2026](https://www.techscience.com/cmc/v88n1/67270/html).
15. [MEMTO, arXiv 2312.02530](https://arxiv.org/abs/2312.02530).
16. [Prototype-oriented unsupervised MTS anomaly detection, ICML 2023 / PMLR](https://proceedings.mlr.press/v202/li23d.html).
17. [Spectral decomposition and adaptation for non-stationary TSAD, ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0925231225026505).
18. [FS-ADAPT, Information Sciences 2023](https://www.sciencedirect.com/science/article/pii/S0020025523011957).
19. [iADCPS, arXiv 2504.04374](https://arxiv.org/abs/2504.04374).
20. [DoKnowAD, AAAI 2026](https://doi.org/10.1609/aaai.v40i32.39927).
21. [ADA-ADF, Applied Soft Computing 2025](https://www.sciencedirect.com/science/article/pii/S1568494625012165).
22. [ADAPTS publisher record, excluded as future-dated at cutoff](https://www.sciencedirect.com/science/article/abs/pii/S0950705126012566).
23. [METER, PVLDB](https://arxiv.org/abs/2312.16831).
24. [MemStream, arXiv 2106.03837](https://arxiv.org/abs/2106.03837).
25. [SAND: Streaming Subsequence Anomaly Detection, PVLDB](https://helios2.mi.parisdescartes.fr/~themisp/SAND/).
26. [Online RNN anomaly detection with multi-step forecasting, Manchester thesis record](https://research.manchester.ac.uk/en/studentTheses/a-fully-online-approach-for-anomaly-and-change-point-de/).
27. [Concept drift adaptation survey, IJCAI 2022](https://www.ijcai.org/proceedings/2022/788).
28. [Regional Concept Drift Detection and Density Synchronized Drift Adaptation, IJCAI 2017](https://www.ijcai.org/proceedings/2017/317).
29. [LEAF, IJCAI 2025](https://www.ijcai.org/proceedings/2025/542).
30. [PADRE, IJCAI 2026](https://www.ijcai.org/proceedings/2026/503).
31. [OneNet, NeurIPS 2023](https://proceedings.neurips.cc/paper_files/paper/2023/file/dd6a47bc0aad6f34aa5e77706d90cdc4-Paper-Conference.pdf).
32. [Online false discovery rate control for time-series anomaly detection, NeurIPS 2021](https://proceedings.neurips.cc/paper/2021/hash/def130d0b67eb38b7a8f4e7121ed432c-Abstract.html).
33. [Concept drift anomaly/change-point detection, Springer 2023](https://link.springer.com/article/10.1007/s11280-023-01181-z).
34. [Safety-gated continual adaptation in CPS, IEEE ICAISET 2026 DOI record](https://doi.org/10.1109/icaiset66439.2026.11541767) (abstract-only inspection).
35. [Evolving Proxy Kills Drift: Data-Efficient Streaming TSAD, WWW 2026](https://doi.org/10.1145/3774904.3792440).
36. [Dynamic Multi-period Experts for Online Time Series Forecasting, WWW 2026](https://doi.org/10.1145/3774904.3792731).
37. [Drift-Aware Online Anomaly Detection in Smart Buildings, ACM E-Energy 2026](https://doi.org/10.1145/3744255.3811742); [code](https://github.com/illinois-arcs/Drift-Aware_AD).
