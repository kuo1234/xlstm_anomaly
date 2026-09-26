# Sources

## Search procedure

Six parallel literature tracks ran on 2026-09-26: Lifecycle (Stories A, E), Risk (B, C), Context (D, with process monitoring, multi-mode fault diagnosis, and causal/physics-informed AD), Transfer (F), Benchmarks (G, H) and Discovery (gap leads N1–N7). Their combined search logs contain 292 logged queries: Risk 89, Lifecycle 80, Context 39, Discovery 34, Transfer 27, Benchmarks 23. The logs are stored per track in [papers.json](papers.json) under `search_logs`. Sources were OpenAlex (API key), CrossRef, the arXiv API, Semantic Scholar and general web search. The lead agent then merged the tracks, deduplicated by DOI, arXiv ID and normalised title, and ran a CrossRef sweep for records whose issue dates fall after the cutoff (twelve queries, listed below).

The areas searched were streaming TSAD; continual anomaly detection; test-time adaptation; concept drift, including recurring drift; uncertainty, abstention, selective prediction and the reject option; risk-controlled online learning (conformal, anytime-valid, e-values); regime and multimode process monitoring; recurrent and memory state management, versioning and rollback; fault diagnosis under varying operating conditions; context-aware, causal and physics-informed AD; digital twins; continual learning with energy or resource accounting; shift detectability and harmful-shift testing; TTA failure analysis; change-point and quickest change detection; poisoning of online detectors; fleet/population monitoring; active fault diagnosis; active and human-in-the-loop AD; unlearning; delayed-label and performative evaluation; and TSAD metric critiques. Switching state-space models, as a separate literature, were covered only through multimode monitoring and Markovian RNNs.

Future-issue sweep queries (CrossRef, `from-pub-date:2026-09-27`): `time series anomaly detection concept drift`; `streaming anomaly detection adaptation`; `continual anomaly detection time series`; `test-time adaptation anomaly detection`; `online anomaly detection drift normal pattern`; `anomaly detection new normal operating mode`; `drift aware anomaly detection industrial`; `multivariate time series anomaly detection online update`; `fault detection mode change adaptive monitoring`; `anomaly detection model pool recurring drift`; `anomaly detection contamination online`; `selective adaptation distribution shift abstain`.

## Identifier checks and corrections

The register holds 340 records. Identifiers were resolved against CrossRef (181 records), the arXiv API (149), or a publisher/proceedings/patent URL only (10). Titles, authors and dates in this register come from those registries, not from the track annotations. Track-supplied DOIs for six records resolved to unrelated papers or did not resolve; they were replaced by CrossRef-matched DOIs. Several track keys carried wrong author names. The audit notes below record every correction, plus two cases where the lead agent's reading of an abstract changed how a record should be characterised.

Evidence levels (deepest level at which the record was read by a track or by the lead agent): abstract: 244, metadata_only: 68, as recorded in prior audit: 23, full_text: 5. A `full_text` label means the methods text was read. Most decisive threats are `abstract` only, and the story cards carry that limitation.

### Audit notes

| Record | Note |
|---|---|
| [Jiang et al. 2026](https://arxiv.org/abs/2609.08367) | arXiv first author is Jiang (Jiang, Liang & Liang); track key used a different name. |
| [Zhang et al. 2015](https://doi.org/10.1016/j.ifacol.2015.09.147) | DOI corrected via CrossRef (track DOI resolved to an unrelated paper). |
| [Li et al. 2025a](https://doi.org/10.1016/j.neucom.2025.130137) | DOI corrected via CrossRef (track DOI did not resolve). |
| [Liu et al. 2023](https://doi.org/10.1016/j.cie.2023.109502) | DOI corrected via CrossRef (track DOI resolved to an unrelated paper). |
| [Lv et al. 2023](https://doi.org/10.1016/j.ipm.2023.103383) | DOI corrected via CrossRef (track DOI resolved to an unrelated paper). |
| [Ray & Dash 2022](https://doi.org/10.1016/j.jksuci.2021.11.014) | DOI corrected via CrossRef (track DOI resolved to an unrelated paper). |
| [Abdoune et al. 2026](https://doi.org/10.1016/j.eswa.2025.130062) | Track key used the wrong author; CrossRef lists Abdoune, Nouiri, Cardin (ESWA, 2026-03). DOI corrected from a non-matching DOI supplied by the track. |
| [Lotto et al. 2026](https://arxiv.org/abs/2609.28170) | Lead-agent audit of the abstract: SA-ZT separates raw telemetry visibility, automated (estimator) influence and state-changing authority via a Safety Engine and Telemetry Broker; the track annotation's 'provenance+plausibility+freshness trust fusion' wording is not supported by the abstract. |
| [Abouelkheir 2026](https://doi.org/10.3390/s26185695) | Track key used the wrong author; CrossRef lists Abouelkheir (Sensors, 2026-09-08). |
| [Kravchik & Shabtai 2020](https://arxiv.org/abs/2002.02741) | arXiv author list is Kravchik & Shabtai; the track key used a wrong author name. |
| [Nikoukhah & Campbell 2003](https://doi.org/10.23919/ecc.2003.7085087) | CrossRef lists Nikoukhah & Campbell (ECC 2003); the track key used a wrong author name. |
| [Castellani et al. 2022](https://arxiv.org/abs/2204.06822) | arXiv author list is Castellani et al.; the track key used a wrong author name. |
| [Du et al. 2019](https://doi.org/10.1145/3319535.3363226) | Lead-agent audit of the abstract: the unlearning framework corrects the model when a false negative OR a false positive is labeled, so it directly covers retroactive correction of wrongly-normal samples; the track annotation describing it as the 'mirror image' understates the overlap. |
| [Grzenda et al. 2019](https://doi.org/10.1007/s10618-019-00654-y) | CrossRef lists Grzenda, Gomes & Bifet (DMKD 2019); the track attributed it to Zliobaite. |
| [Fang et al. 2026](https://doi.org/10.1016/j.neucom.2026.135021) | Issue date 2026-12 is after the cutoff; the article was available online before the cutoff (recorded in the prior audit), so it is treated as current evidence. |
| [Kuhn et al. 2026](https://doi.org/10.1016/j.actaastro.2026.07.065) | Issue date 2026-12 is after the cutoff; the article was available online before the cutoff (recorded in the prior audit), so it is treated as current evidence. |
| [MemTTA thesis (Korea Univ. 2026)](https://dc.korea.ac.kr/srch/srchDetail/000000308007) | DOI 10.23186/korea.000000308007 did not resolve at doi.org on 2026-09-26; institutional URL used. |
| [Yang et al. 2025](https://arxiv.org/abs/2511.18739) | Journal version 10.1016/j.neucom.2026.134547 carries issue date 2026-11 (future); arXiv version is current. |

## Register by story

Stories: A–H as requested; N1–N7 discovered; F-prefixed keys denote future-issue leads (see [future_dated_leads.md](future_dated_leads.md)). A record can appear under several stories.

### A: Reversible normality lifecycle (39 records)

| ID | Work | Venue | Date | Evidence | Threat |
|---|---|---|---|---|---|
| SD245 | [Qin et al. 2026](https://arxiv.org/abs/2604.08059): Governed Capability Evolution: Lifecycle-Time Compatibility Checking and Rollback for AI-Component-B… | arXiv preprint | 2026-04-09 | full_text | direct |
| SD247 | [Aftab et al. 2026](https://arxiv.org/abs/2607.02687): RES-DARE: Failure-Aware Expert Adaptation and Rollback-Safe Self-Repair for Intrusion Detection | arXiv preprint | 2026-07-02 | abstract | direct |
| SD290 | [Kim et al. 2026](https://doi.org/10.1609/aaai.v40i17.38524): CANDI: Curated Test-Time Adaptation for Multivariate Time-Series Anomaly Detection | AAAI | 2026-03-14 | as recorded in prior audit | direct |
| SD295 | [Le et al. 2026](https://doi.org/10.1145/3744255.3811742): Drift-Aware Online Anomaly Detection in Smart Buildings via Temporal Variational Autoencoder Gradien… | ACM e-Energy | 2026-06-22 | as recorded in prior audit | direct |
| SD296 | [Li et al. 2026c](https://doi.org/10.24963/ijcai.2026/503): Beyond Uniform Updates: Drift Pattern Aware Online Time Series Forecasting (PADRE) | IJCAI | 2026-09 | as recorded in prior audit | direct |
| SD297 | [Fang et al. 2026](https://doi.org/10.1016/j.neucom.2026.135021): Normality-preserving continual industrial anomaly detection via orthogonal LoRA banks | Neurocomputing | 2026-12 | as recorded in prior audit | direct · future issue 2026-12 |
| SD298 | [Kuhn et al. 2026](https://doi.org/10.1016/j.actaastro.2026.07.065): Validation-gated continual learning for anomaly detection in satellite telemetry | Acta Astronautica | 2026-12 | as recorded in prior audit | direct · future issue 2026-12 |
| SD299 | [Lu et al. 2026](https://doi.org/10.1145/3770855.3817912): SCALE: Style-Causal Disentanglement with Adaptive Lifelong E... (online latent-domain MTSAD) | ACM | 2026-08-08 | as recorded in prior audit | direct |
| SD300 | [Chilukury et al. 2026](https://doi.org/10.1109/icaiset66439.2026.11541767): Safety-Gated Continual Learning for Drift-Aware Anomaly Detection in CPS | ICAISET | 2026-04-21 | as recorded in prior audit | direct |
| SD301 | [Park et al. 2026](https://arxiv.org/abs/2602.01635): COMET: Codebook-based Online-adaptive Multi-scale Embedding for TSAD | arXiv | 2026-02-02 | as recorded in prior audit | direct |
| SD305 | [Wei et al. 2026](https://doi.org/10.1145/3774904.3792440): Evolving Proxy Kills Drift: Data-Efficient Streaming Time Series Anomaly Detection | WWW | 2026-04-12 | as recorded in prior audit | direct |
| SD293 | [Park et al. 2025](https://doi.org/10.1145/3746252.3761481): Adaptive Anomaly Detection in the Presence of Concept Drift (AnDri) | CIKM demo / arXiv | 2025-06-18 | as recorded in prior audit | direct |
| SD289 | [Kim et al. 2024](https://doi.org/10.1609/aaai.v38i12.29210): When Model Meets New Normals: Test-Time Adaptation for Unsupervised Time-Series Anomaly Detection | AAAI | 2024-03-24 | as recorded in prior audit | direct |
| SD292 | [Zhu et al. 2024](https://doi.org/10.14778/3636218.3636233): METER: A Dynamic Concept Adaptation Framework for Online Anomaly Detection | PVLDB | 2024-03-05 | as recorded in prior audit | direct |
| SD310 | [Song et al. 2023](https://arxiv.org/abs/2312.02530): MEMTO: Memory-guided Transformer for Multivariate Time Series Anomaly Detection | NeurIPS | 2023-12-05 | as recorded in prior audit | direct |
| SD291 | [Bhatia et al. 2022](https://doi.org/10.1145/3485447.3512221): MemStream: Memory-Based Streaming Anomaly Detection | WWW | 2022-04-25 | as recorded in prior audit | direct |
| SD306 | [Wang et al. 2022](https://arxiv.org/abs/2203.13591): Continual Test-Time Domain Adaptation (CoTTA) | CVPR | 2022-03-25 | as recorded in prior audit | direct |
| SD246 | [Su et al. 2026](https://arxiv.org/abs/2607.27773): ChronoMem: Version Control and Semantic Rollback for Large Language Model Agent Memory | arXiv preprint | 2026-07-30 | abstract | strong_component |
| SD311 | [MemTTA thesis (Korea Univ. 2026)](https://dc.korea.ac.kr/srch/srchDetail/000000308007): MemTTA for time-series anomaly detection (Korea University master's thesis) | Korea University thesis | 2026 | as recorded in prior audit | strong_component |
| SD322 | [Angiulli et al. 2026](https://doi.org/10.1016/j.neucom.2026.135118): A comprehensive survey on continual anomaly detection | Neurocomputing | 2026-09-17 | metadata_only | strong_component · future issue 2027-01 |
| SD248 | [Kabashkin 2025](https://doi.org/10.3390/electronics14152968): Federated Unlearning Framework for Digital Twin–Based Aviation Health Monitoring Under Sensor Drift … | Electronics | 2025-07-24 | abstract | strong_component |
| SD259 | [Alotaibi & Maffeis 2024](https://doi.org/10.1145/3678890.3678901): Mateen: Adaptive Ensemble Learning for Network Anomaly Detection | The 27th International Symposium on Research  | 2024-09-30 | abstract | strong_component |
| SD182 | [Katz 2026](https://arxiv.org/abs/2604.06438): Cost-sensitive retraining via posterior learning debt | arXiv preprint | 2026-04-07 | abstract | adjacent |
| SD251 | [Du et al. 2026](https://doi.org/10.1016/j.neunet.2026.108695): A noise robust and distribution-adaptive framework for multivariate time series anomaly detection | Neural Networks | 2026-07 | metadata_only | adjacent |
| SD261 | [Pastore et al. 2026](https://doi.org/10.3390/info17020117): Intelligent Fusion: A Resilient Anomaly Detection Framework for IoMT Health Devices | Information | 2026-01-26 | abstract | adjacent |
| SD321 | [Zhang et al. 2026a](https://doi.org/10.1016/j.compchemeng.2026.109749): Adaptive continual fault detection for industrial processes with evolving data distributions | Computers & Chemical Engineering | 2026-06-13 | metadata_only | adjacent · future issue 2026-10 |
| SD330 | [Zhang et al. 2026b](https://doi.org/10.1016/j.asoc.2026.115975): Industrial large model-driven online early fault warning: A novel incremental anomaly detection fram… | Applied Soft Computing | 2026-07-16 | metadata_only | adjacent · future issue 2026-11 |
| SD333 | [Abedin et al. 2026](https://doi.org/10.1016/j.epsr.2026.113501): Streaming self-supervised graph learning for evidence-aware anomaly detection in cyber–physical smar… | Electric Power Systems Research | 2026-06-25 | metadata_only | adjacent · future issue 2027-01 |
| SD334 | [Tan et al. 2026](https://doi.org/10.1016/j.patcog.2026.113843): RoCA: Robust Contrastive Adaptation for unsupervised anomaly detection | Pattern Recognition | 2026-04-29 | metadata_only | adjacent · future issue 2026-11 |
| SD252 | [Mou et al. 2025](https://arxiv.org/abs/2503.18385): RoCA: Robust Contrastive One-class Time Series Anomaly Detection with Contaminated Data | arXiv preprint | 2025-03-24 | abstract | adjacent |
| SD254 | [Li et al. 2025b](https://arxiv.org/abs/2501.02107): Online Detection of Water Contamination Under Concept Drift | arXiv preprint | 2025-01-03 | abstract | adjacent |
| SD249 | [Jiang et al. 2024](https://arxiv.org/abs/2403.14233): SoftPatch: Unsupervised Anomaly Detection with Noisy Data | NeurIPS 2022 / arXiv | 2024-03-21 | abstract | adjacent |
| SD250 | [Ho & Armanfard 2023](https://arxiv.org/abs/2308.12563): Contaminated Multivariate Time-Series Anomaly Detection with Spatio-Temporal Graph Conditional Diffu… | arXiv preprint | 2023-08-24 | abstract | adjacent |
| SD253 | [Hojjati & Armanfard 2026](https://arxiv.org/abs/2603.25956): ARTA: Adversarial-Robust Multivariate Time--Series Anomaly Detection via Sparsity-Constrained Pertur… | arXiv preprint | 2026-03-26 | abstract | background |
| SD256 | [Eken et al. 2025](https://doi.org/10.1145/3747346): A Multivocal Review of MLOps Practices, Challenges and Open Issues | ACM Computing Surveys | 2025-09-08 | abstract | background |
| SD255 | [Kreuzberger et al. 2023](https://doi.org/10.1109/access.2023.3262138): Machine Learning Operations (MLOps): Overview, Definition, and Architecture | IEEE Access | 2023 | abstract | background |
| SD257 | [Bayram et al. 2022](https://doi.org/10.1016/j.knosys.2022.108632): From concept drift to model degradation: An overview on performance-aware drift detectors | Knowledge-Based Systems | 2022-06 | abstract | background |
| SD258 | [Lavin et al. 2021](https://doi.org/10.21203/rs.3.rs-133138/v1): Technology Readiness Levels for Machine Learning Systems | Nature Communications | 2021-01-12 | metadata_only | background |
| SD260 | [De Lange & Tuytelaars 2021](https://doi.org/10.1109/iccv48922.2021.00814): Continual Prototype Evolution: Learning Online from Non-Stationary Data Streams | 2021 IEEE/CVF International Conference on Com | 2021-10 | abstract | background |

### B: Risk-constrained adaptation (45 records)

| ID | Work | Venue | Date | Evidence | Threat |
|---|---|---|---|---|---|
| SD022 | [Dasari 2026](https://arxiv.org/abs/2608.19488): When to Retrain: An Empirical Study of Retraining Policies for Streaming ML Under Concept Drift, Bud… | arXiv | 2026-08-19 | abstract | direct |
| SD026 | [Kwon & Kim 2026](https://doi.org/10.1038/s41598-026-40637-w): Conformal selective prediction with cost aware deferral for safe clinical triage under distribution … | Scientific Reports | 2026-02-20 | abstract | direct |
| SD027 | [Wang et al. 2026a](https://arxiv.org/abs/2609.20700): Should This Case Be Adapted? Prediction Fragmentation Controls Test-Time Adaptation | arXiv | 2026-09-17 | abstract | direct |
| SD290 | [Kim et al. 2026](https://doi.org/10.1609/aaai.v40i17.38524): CANDI: Curated Test-Time Adaptation for Multivariate Time-Series Anomaly Detection | AAAI | 2026-03-14 | as recorded in prior audit | direct |
| SD295 | [Le et al. 2026](https://doi.org/10.1145/3744255.3811742): Drift-Aware Online Anomaly Detection in Smart Buildings via Temporal Variational Autoencoder Gradien… | ACM e-Energy | 2026-06-22 | as recorded in prior audit | direct |
| SD299 | [Lu et al. 2026](https://doi.org/10.1145/3770855.3817912): SCALE: Style-Causal Disentanglement with Adaptive Lifelong E... (online latent-domain MTSAD) | ACM | 2026-08-08 | as recorded in prior audit | direct |
| SD300 | [Chilukury et al. 2026](https://doi.org/10.1109/icaiset66439.2026.11541767): Safety-Gated Continual Learning for Drift-Aware Anomaly Detection in CPS | ICAISET | 2026-04-21 | as recorded in prior audit | direct |
| SD302 | [Han & Qu 2026](https://arxiv.org/abs/2608.30502): When the Martingale Never Stops Firing: Anytime-Valid Gating ... (real forecast streams) | arXiv | 2026-08-31 | as recorded in prior audit | direct |
| SD012 | [Farzaneh & Simeone 2025](https://arxiv.org/abs/2505.01783): Online Conformal Anomaly Detection with Prediction-Powered Data Acquisition | arXiv (IEEE Access, in review) | 2025-05-03 | full_text | direct |
| SD015 | [Schirmer et al. 2025](https://doi.org/10.52202/085713-2705): Monitoring Risks in Test-Time Adaptation | Advances in Neural Information Processing Sys | 2025 | full_text | direct |
| SD029 | [Wang et al. 2025a](https://arxiv.org/abs/2510.10193): SAFER: Risk-Constrained Sample-then-Filter in Large Language Models | ICLR 2026 | 2025-10-11 | metadata_only | direct |
| SD011 | [Krönert et al. 2024](https://arxiv.org/abs/2402.03565): Breakpoint based online anomaly detection | arXiv | 2024-02-05 | abstract | direct |
| SD014 | [Amoukou et al. 2024](https://doi.org/10.52202/079017-4107): Sequential Harmful Shift Detection Without Labels | Advances in Neural Information Processing Sys | 2024 | abstract | direct |
| SD020 | [Mahadevan & Mathioudakis 2024](https://doi.org/10.1016/j.knosys.2024.111610): Cost-aware retraining for machine learning | Knowledge-Based Systems | 2024-06 | abstract | direct |
| SD289 | [Kim et al. 2024](https://doi.org/10.1609/aaai.v38i12.29210): When Model Meets New Normals: Test-Time Adaptation for Unsupervised Time-Series Anomaly Detection | AAAI | 2024-03-24 | as recorded in prior audit | direct |
| SD010 | [Krönert et al. 2023](https://arxiv.org/abs/2312.01969): FDR Control for Online Anomaly Detection | arXiv | 2023-12-04 | abstract | direct |
| SD021 | [Mahadevan & Mathioudakis 2023](https://arxiv.org/abs/2310.04216): Cost-Effective Retraining of Machine Learning Models | arXiv (preprint of the KBS 2024 paper) | 2023-10-06 | abstract | direct |
| SD013 | [Podkopaev & Ramdas 2021](https://arxiv.org/abs/2110.06177): Tracking the risk of a deployed model and detecting harmful distribution shifts | arXiv / ICML 2022 | 2021-10-12 | abstract | direct |
| SD030 | [Zhou et al. 2026](https://arxiv.org/abs/2604.01170): Online Reasoning Calibration: Test-Time Training Enables Generalizable Conformal LLM Reasoning | arXiv | 2026-04-01 | metadata_only | strong_component |
| SD031 | [Hultberg et al. 2026](https://arxiv.org/abs/2602.04364): Anytime-Valid Conformal Risk Control | arXiv | 2026-02-04 | abstract | strong_component |
| SD033 | [Ye et al. 2026](https://doi.org/10.3390/math14152847): Finite-Sample Conformal Risk Bounds for Joint Value-at-Risk and Expected-Shortfall Forecasting Under… | Mathematics | 2026-08-06 | metadata_only | strong_component |
| SD320 | [Altay 2026](https://doi.org/10.1016/j.knosys.2026.116716): Response inertia in sequential detection: A policy-level framework for selective temporal adaptation | Knowledge-Based Systems | 2026-07-29 | metadata_only | strong_component · future issue 2026-10 |
| SD016 | [Prinster et al. 2025](https://arxiv.org/abs/2505.04608): WATCH: Adaptive Monitoring for AI Deployments via Weighted-Conformal Martingales | arXiv | 2025-05-07 | abstract | strong_component |
| SD032 | [Blot et al. 2024](https://arxiv.org/abs/2406.17819): Automatically Adaptive Conformal Risk Control | arXiv | 2024-06-25 | abstract | strong_component |
| SD034 | [Xu et al. 2024](https://arxiv.org/abs/2406.10490): Active, anytime-valid risk controlling prediction sets | arXiv | 2024-06-15 | metadata_only | strong_component |
| SD002 | [Farinhas et al. 2023](https://arxiv.org/abs/2310.01262): Non-Exchangeable Conformal Risk Control | arXiv | 2023-10-02 | abstract | strong_component |
| SD005 | [Angelopoulos et al. 2023](https://doi.org/10.52202/075280-1000): Conformal PID Control for Time Series Prediction | Advances in Neural Information Processing Sys | 2023 | abstract | strong_component |
| SD006 | [Bhatnagar et al. 2023](https://arxiv.org/abs/2302.07869): Improved Online Conformal Prediction via Strongly Adaptive Online Learning | arXiv / ICML 2023 | 2023-02-15 | abstract | strong_component |
| SD008 | [Bates et al. 2023](https://doi.org/10.1214/22-aos2244): Testing for outliers with conformal p-values | The Annals of Statistics | 2023-02-01 | abstract | strong_component |
| SD009 | [Barber et al. 2023](https://doi.org/10.1214/23-aos2276): Conformal prediction beyond exchangeability | The Annals of Statistics | 2023-04-01 | abstract | strong_component |
| SD019 | [Shin et al. 2023](https://doi.org/10.51387/23-nejsds51): E-detectors: A Nonparametric Framework for Sequential Change Detection | The New England Journal of Statistics in Data | 2023-12-01 | abstract | strong_component |
| SD001 | [Angelopoulos et al. 2022](https://arxiv.org/abs/2208.02814): Conformal Risk Control | arXiv / ICLR 2024 | 2022-08-04 | abstract | strong_component |
| SD004 | [Zaffran et al. 2022](https://arxiv.org/abs/2202.07282): Adaptive Conformal Predictions for Time Series | arXiv / ICML 2022 | 2022-02-15 | abstract | strong_component |
| SD003 | [Gibbs & Candès 2021](https://arxiv.org/abs/2106.00170): Adaptive Conformal Inference Under Distribution Shift | arXiv / NeurIPS 2021 | 2021-06-01 | abstract | strong_component |
| SD024 | [Göpfert et al. 2018](https://doi.org/10.1007/978-3-030-01418-6_45): Mitigating Concept Drift via Rejection | Lecture Notes in Computer Science | 2018-09-27 | abstract | strong_component |
| SD313 | [Geifman & El-Yaniv 2017](https://arxiv.org/abs/1705.08500): Selective Classification for Deep Neural Networks | NeurIPS | 2017-05-23 | abstract | strong_component |
| SD023 | [Loeffel et al. 2015](https://doi.org/10.1109/dsaa.2015.7344808): Classification with a reject option under Concept Drift: The Droplets algorithm | 2015 IEEE International Conference on Data Sc | 2015-10 | abstract | strong_component |
| SD028 | [Wang et al. 2026b](https://arxiv.org/abs/2602.03814): Conformal Thinking: Risk Control for Reasoning on a Compute Budget | arXiv | 2026-02-03 | metadata_only | adjacent |
| SD323 | [Zuo et al. 2026](https://doi.org/10.1016/j.neunet.2026.109567): ContaminationAD: Anomaly detection with contaminated data | Neural Networks | 2026-08-30 | abstract | adjacent · future issue 2027-01 |
| SD325 | [Jun & Ohn 2026](https://doi.org/10.1016/j.patcog.2026.114406): Online conformal inference with retrospective adjustment for faster adaptation to distribution shift | Pattern Recognition | 2026-07-09 | abstract | adjacent · future issue 2026-12 |
| SD007 | [Angelopoulos et al. 2025](https://doi.org/10.1214/24-aoas1998): Learn then test: Calibrating predictive algorithms to achieve risk control | The Annals of Applied Statistics | 2025-06-01 | abstract | background |
| SD025 | [Hendrickx et al. 2024](https://doi.org/10.1007/s10994-024-06534-x): Machine learning with a reject option: a survey | Machine Learning | 2024-03-29 | abstract | background |
| SD018 | [Ramdas et al. 2023](https://doi.org/10.1214/23-sts894): Game-Theoretic Statistics and Safe Anytime-Valid Inference | Statistical Science | 2023-11-01 | abstract | background |
| SD017 | [Shafer 2021](https://doi.org/10.1111/rssa.12647): Testing by Betting: A Strategy for Statistical and Scientific Communication | Journal of the Royal Statistical Society Seri | 2021-05-05 | abstract | background |
| SD315 | [Sobel & Wald 1949](https://doi.org/10.1214/aoms/1177729944): A Sequential Decision Procedure for Choosing One of Three Hypotheses Concerning the Unknown Mean of … | Annals of Mathematical Statistics | 1949 | abstract | background |

### C: ADAPT / FREEZE / UNRESOLVED (41 records)

| ID | Work | Venue | Date | Evidence | Threat |
|---|---|---|---|---|---|
| SD026 | [Kwon & Kim 2026](https://doi.org/10.1038/s41598-026-40637-w): Conformal selective prediction with cost aware deferral for safe clinical triage under distribution … | Scientific Reports | 2026-02-20 | abstract | direct |
| SD027 | [Wang et al. 2026a](https://arxiv.org/abs/2609.20700): Should This Case Be Adapted? Prediction Fragmentation Controls Test-Time Adaptation | arXiv | 2026-09-17 | abstract | direct |
| SD035 | [Jiang et al. 2026](https://arxiv.org/abs/2609.08367): To Adapt or Not to Adapt? Selective Adaptation for Vision-Language Models | arXiv | 2026-09-08 | full_text | direct |
| SD036 | [Majumdar & Saha 2026](https://arxiv.org/abs/2608.22233): When Test-Time Adaptation Helps, Harms, or Becomes Inactive: A Condition-Level Study on CIFAR-10-C | arXiv | 2026-08-23 | abstract | direct |
| SD046 | [Solozobov 2026](https://arxiv.org/abs/2604.15740): Evidence Sufficiency Under Delayed Ground Truth: Proxy Monitoring for Risk Decision Systems | arXiv | 2026-04-17 | abstract | direct |
| SD290 | [Kim et al. 2026](https://doi.org/10.1609/aaai.v40i17.38524): CANDI: Curated Test-Time Adaptation for Multivariate Time-Series Anomaly Detection | AAAI | 2026-03-14 | as recorded in prior audit | direct |
| SD301 | [Park et al. 2026](https://arxiv.org/abs/2602.01635): COMET: Codebook-based Online-adaptive Multi-scale Embedding for TSAD | arXiv | 2026-02-02 | as recorded in prior audit | direct |
| SD302 | [Han & Qu 2026](https://arxiv.org/abs/2608.30502): When the Martingale Never Stops Firing: Anytime-Valid Gating ... (real forecast streams) | arXiv | 2026-08-31 | as recorded in prior audit | direct |
| SD015 | [Schirmer et al. 2025](https://doi.org/10.52202/085713-2705): Monitoring Risks in Test-Time Adaptation | Advances in Neural Information Processing Sys | 2025 | full_text | direct |
| SD293 | [Park et al. 2025](https://doi.org/10.1145/3746252.3761481): Adaptive Anomaly Detection in the Presence of Concept Drift (AnDri) | CIKM demo / arXiv | 2025-06-18 | as recorded in prior audit | direct |
| SD308 | [Bandyopadhyay et al. 2025](https://arxiv.org/abs/2504.18599): A Hybrid Framework for Real-Time Data Drift and Anomaly Identification (HTM+SPRT) | arXiv | 2025-04-24 | as recorded in prior audit | direct |
| SD014 | [Amoukou et al. 2024](https://doi.org/10.52202/079017-4107): Sequential Harmful Shift Detection Without Labels | Advances in Neural Information Processing Sys | 2024 | abstract | direct |
| SD289 | [Kim et al. 2024](https://doi.org/10.1609/aaai.v38i12.29210): When Model Meets New Normals: Test-Time Adaptation for Unsupervised Time-Series Anomaly Detection | AAAI | 2024-03-24 | as recorded in prior audit | direct |
| SD292 | [Zhu et al. 2024](https://doi.org/10.14778/3636218.3636233): METER: A Dynamic Concept Adaptation Framework for Online Anomaly Detection | PVLDB | 2024-03-05 | as recorded in prior audit | direct |
| SD041 | [Garg et al. 2022](https://arxiv.org/abs/2201.04234): Leveraging Unlabeled Data to Predict Out-of-Distribution Performance | arXiv / ICLR 2022 | 2022-01-11 | abstract | direct |
| SD307 | [Niu et al. 2022](https://arxiv.org/abs/2204.02610): Efficient Test-Time Model Adaptation without Forgetting (EATA) | ICML | 2022-04-06 | as recorded in prior audit | direct |
| SD013 | [Podkopaev & Ramdas 2021](https://arxiv.org/abs/2110.06177): Tracking the risk of a deployed model and detecting harmful distribution shifts | arXiv / ICML 2022 | 2021-10-12 | abstract | direct |
| SD319 | [Yang 2026](https://doi.org/10.1016/j.asoc.2026.116360): Representation stability is not detectability: A leakage-free evaluation of frozen time series found… | Applied Soft Computing | 2026-09-07 | metadata_only | strong_component · future issue 2027-01 |
| SD320 | [Altay 2026](https://doi.org/10.1016/j.knosys.2026.116716): Response inertia in sequential detection: A policy-level framework for selective temporal adaptation | Knowledge-Based Systems | 2026-07-29 | metadata_only | strong_component · future issue 2026-10 |
| SD016 | [Prinster et al. 2025](https://arxiv.org/abs/2505.04608): WATCH: Adaptive Monitoring for AI Deployments via Weighted-Conformal Martingales | arXiv | 2025-05-07 | abstract | strong_component |
| SD043 | [Xie et al. 2024a](https://arxiv.org/abs/2405.18979): MANO: Exploiting Matrix Norm for Unsupervised Accuracy Estimation Under Distribution Shifts | arXiv | 2024-05-29 | abstract | strong_component |
| SD044 | [Xie et al. 2024b](https://arxiv.org/abs/2401.08909): Leveraging Gradients for Unsupervised Accuracy Estimation under Distribution Shift | arXiv | 2024-01-17 | abstract | strong_component |
| SD037 | [Zhao et al. 2023](https://arxiv.org/abs/2306.03536): On Pitfalls of Test-Time Adaptation | arXiv / ICML 2023 (TTAB benchmark) | 2023-06-06 | abstract | strong_component |
| SD052 | [Sun et al. 2023](https://doi.org/10.1016/j.patter.2023.100687): Continuous diagnosis and prognosis by controlling the update process of deep neural networks | Patterns | 2023-02 | abstract | strong_component |
| SD040 | [Fisch et al. 2022](https://arxiv.org/abs/2208.12084): Calibrated Selective Classification | arXiv / TMLR | 2022-08-25 | abstract | strong_component |
| SD045 | [Fang et al. 2022](https://arxiv.org/abs/2210.14707): Is Out-of-Distribution Detection Learnable? | arXiv / NeurIPS 2022 | 2022-10-26 | abstract | strong_component |
| SD049 | [Xie 2022](https://doi.org/10.1109/isit50566.2022.9834530): Minimax Robust Quickest Change Detection using Wasserstein Ambiguity Sets | 2022 IEEE International Symposium on Informat | 2022-06-26 | abstract | strong_component |
| SD042 | [Chen et al. 2021](https://arxiv.org/abs/2106.15728): Detecting Errors and Estimating Accuracy on Unlabeled Data with Self-training Ensembles | arXiv | 2021-06-29 | abstract | strong_component |
| SD050 | Quickest Change Detection with Non-stationary an (2021) (no public identifier) — Quickest Change Detection with Non-stationary and Composite Post-change Distribution | arXiv | 2021-10-04 | abstract | strong_component |
| SD051 | [Shashikumar et al. 2021](https://doi.org/10.1038/s41746-021-00504-6): Artificial intelligence sepsis prediction algorithm learns to say “I don’t know” | npj Digital Medicine | 2021-09-09 | abstract | strong_component |
| SD039 | [Jiang et al. 2018](https://arxiv.org/abs/1805.11783): To Trust Or Not To Trust A Classifier | arXiv / NeurIPS 2018 | 2018-05-30 | abstract | strong_component |
| SD048 | [Molloy & Ford 2017](https://doi.org/10.1109/tsp.2017.2740202): Misspecified and Asymptotically Minimax Robust Quickest Change Detection | IEEE Transactions on Signal Processing | 2017-11-01 | abstract | strong_component |
| SD313 | [Geifman & El-Yaniv 2017](https://arxiv.org/abs/1705.08500): Selective Classification for Deep Neural Networks | NeurIPS | 2017-05-23 | abstract | strong_component |
| SD047 | [Banerjee & Veeravalli 2015](https://doi.org/10.1109/tit.2015.2458864): Data-Efficient Minimax Quickest Change Detection With Composite Post-Change Distribution | IEEE Transactions on Information Theory | 2015-09 | abstract | strong_component |
| SD025 | [Hendrickx et al. 2024](https://doi.org/10.1007/s10994-024-06534-x): Machine learning with a reject option: a survey | Machine Learning | 2024-03-29 | abstract | background |
| SD038 | [Yu et al. 2023](https://arxiv.org/abs/2307.03133): Benchmarking Test-Time Adaptation against Distribution Shifts in Image Classification | arXiv | 2023-07-06 | abstract | background |
| SD054 | [Luo et al. 2022](https://arxiv.org/abs/2211.09916): Online Distribution Shift Detection via Recency Prediction | arXiv | 2022-11-17 | abstract | background |
| SD055 | [Zhang et al. 2022](https://arxiv.org/abs/2210.10769): "Why did the Model Fail?": Attributing Model Performance Changes to Distribution Shifts | arXiv | 2022-10-19 | abstract | background |
| SD053 | [Kulinski et al. 2021](https://arxiv.org/abs/2107.06929): Feature Shift Detection: Localizing Which Features Have Shifted via Conditional Distribution Tests | arXiv | 2021-07-14 | abstract | background |
| SD314 | [Chow 1970](https://doi.org/10.1109/tit.1970.1054406): On optimum recognition error and reject tradeoff | IEEE Trans. Information Theory | 1970 | abstract | background |
| SD315 | [Sobel & Wald 1949](https://doi.org/10.1214/aoms/1177729944): A Sequential Decision Procedure for Choosing One of Three Hypotheses Concerning the Unknown Mean of … | Annals of Mathematical Statistics | 1949 | abstract | background |

### D: Context-authorized normality (incl. process monitoring, CPS, physics/causal) (67 records)

| ID | Work | Venue | Date | Evidence | Threat |
|---|---|---|---|---|---|
| SD088 | [Chahine & Noura 2026](https://doi.org/10.3390/fi18060308): Features over Architecture: Physics-Informed Anomaly Detection in Industrial Control Systems | Future Internet | 2026-06-06 | abstract | direct |
| SD102 | [Weiß et al. 2026](https://arxiv.org/abs/2607.08373): Self-Adaptive Anomaly Detection with Reinforcement Learning and Human Feedback in Connected Vehicles | arXiv | 2026-07-09 | abstract | direct |
| SD109 | [Abbas & Xu 2026](https://arxiv.org/abs/2609.06306): MARS: Detecting Unauthorized Variable Manipulations in Multi-Application PLC Runtimes | arXiv | 2026-09-05 | abstract | direct |
| SD110 | [Lotto et al. 2026](https://arxiv.org/abs/2609.28170): Safety-Aware Zero Trust Enforcement for IoT and Cyber-Physical Systems | arXiv | 2026-09-23 | abstract | direct |
| SD111 | [Abouelkheir 2026](https://doi.org/10.3390/s26185695): A Provenance-Driven Trust Framework with Physics-Consistent Validation for Secure Wireless Sensor Ne… | Sensors | 2026-09-08 | abstract | direct |
| SD115 | [Li et al. 2026a](https://doi.org/10.24963/ijcai.2026/503): Beyond Uniform Updates: Drift Pattern Aware Online Time Series Forecasting Under Delayed Feedback | Proceedings of the Thirty-Fifth International | 2026-09 | metadata_only | direct |
| SD116 | [Shang et al. 2026](https://doi.org/10.32604/cmc.2026.084688): A Multi-Scale Time-Series Anomaly Detection Approach for Modeling the Time-Lagged Effects of Exogeno… | Computers, Materials &amp; Continua | 2026 | abstract | direct |
| SD295 | [Le et al. 2026](https://doi.org/10.1145/3744255.3811742): Drift-Aware Online Anomaly Detection in Smart Buildings via Temporal Variational Autoencoder Gradien… | ACM e-Energy | 2026-06-22 | as recorded in prior audit | direct |
| SD296 | [Li et al. 2026c](https://doi.org/10.24963/ijcai.2026/503): Beyond Uniform Updates: Drift Pattern Aware Online Time Series Forecasting (PADRE) | IJCAI | 2026-09 | as recorded in prior audit | direct |
| SD097 | [Giannoulidis et al. 2025](https://doi.org/10.1109/access.2025.3592775): Leveraging Feedback and Causality-Enriched Multimodal Context for Predictive Maintenance | IEEE Access | 2025 | abstract | direct |
| SD100 | [Deng et al. 2024](https://arxiv.org/abs/2405.03234): A Reliable Framework for Human-in-the-Loop Anomaly Detection in Time Series | arXiv | 2024-05-06 | abstract | direct |
| SD064 | [Vaska et al. 2022](https://doi.org/10.1109/case49997.2022.9926631): Context-Dependent Anomaly Detection with Knowledge Graph Embedding Models | 2022 IEEE 18th International Conference on Au | 2022-08-20 | abstract | direct |
| SD065 | [Bosch environment/system anomaly patent (US 11,686,651)](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11686651): Method and device for detecting anomalies in technical systems (environment + conditional system ano… | US Patent 11,686,651 / 11,536,630 / 11,867,59 | 2022 | abstract | direct |
| SD094 | [Yang et al. 2022](https://arxiv.org/abs/2206.15033): A Causal Approach to Detecting Multivariate Time-series Anomalies and Root Causes | arXiv | 2022-06-30 | abstract | direct |
| SD096 | [Giannoulidis & Gounaris 2022](https://doi.org/10.1007/s10844-022-00744-2): A context-aware unsupervised predictive maintenance solution for fleet management | Journal of Intelligent Information Systems | 2022-09-17 | abstract | direct |
| SD083 | [Gao et al. 2021](https://doi.org/10.1145/3450267.3450533): An anomaly detection framework for digital twin driven cyber-physical systems | Proceedings of the ACM/IEEE 12th Internationa | 2021-05-19 | abstract | direct |
| SD108 | [SAVIOR (USENIX Security 2020)](https://www.usenix.org/conference/usenixsecurity20/presentation/quinonez): SAVIOR: Securing Autonomous Vehicles with Robust Physical Invariants | USENIX Security 2020 | 2020 | abstract | direct |
| SD105 | [Choi et al. 2018](https://doi.org/10.1145/3243734.3243752): Detecting Attacks Against Robotic Vehicles | Proceedings of the 2018 ACM SIGSAC Conference | 2018-10-15 | abstract | direct |
| SD104 | [Fawzi et al. 2014](https://doi.org/10.1109/tac.2014.2303233): Secure Estimation and Control for Cyber-Physical Systems Under Adversarial Attacks | IEEE Transactions on Automatic Control | 2014-06 | abstract | direct |
| SD056 | [Song et al. 2007](https://doi.org/10.1109/tkde.2007.1009): Conditional Anomaly Detection | IEEE Transactions on Knowledge and Data Engin | 2007-05 | abstract | direct |
| SD068 | [Lane et al. 2001](https://doi.org/10.1016/s0959-1524%2899%2900063-3): Performance monitoring of a multi-product semi-batch process | Journal of Process Control | 2001-02 | abstract | direct |
| SD075 | [Wang et al. 2026c](https://arxiv.org/abs/2605.22028): Replay-guided Test-time Adaptation for Fault Diagnosis Under Unseen Operating Conditions | arXiv | 2026-05-21 | abstract | strong_component |
| SD076 | [Zhao et al. 2026a](https://arxiv.org/abs/2605.24457): Asymmetric Adaptation-based Real-time Fault Diagnosis Under Transitional Operating Conditions | arXiv | 2026-05-23 | abstract | strong_component |
| SD085 | [Abdoune et al. 2026](https://doi.org/10.1016/j.eswa.2025.130062): Digital twin-based anomaly detection under concept drift: A comparison between iterative batch learn… | Expert Systems with Applications | 2026-03 | metadata_only | strong_component |
| SD086 | [Sayghe et al. 2026](https://doi.org/10.1038/s41598-026-53863-z): A digital twin and deep-learning ensemble for cyber attack detection in industrial control systems a… | Scientific Reports | 2026-05-22 | metadata_only | strong_component |
| SD087 | [Erkek & Irmak 2026](https://doi.org/10.1007/s10207-026-01274-6): Explainable digital twin–driven ensemble anomaly detection framework for cyber-physical infrastructu… | International Journal of Information Security | 2026-05-25 | abstract | strong_component |
| SD090 | [Bai et al. 2026](https://arxiv.org/abs/2604.25655): Residual-loss Anomaly Analysis of Physics-Informed Neural Networks: An Inverse Method for Change-poi… | arXiv | 2026-04-28 | abstract | strong_component |
| SD092 | [Khosravinia et al. 2026](https://arxiv.org/abs/2604.17998): Causally-Constrained Probabilistic Forecasting for Time-Series Anomaly Detection | arXiv | 2026-04-20 | abstract | strong_component |
| SD095 | [Wang et al. 2026d](https://arxiv.org/abs/2607.08555): CAAD: Causality-Aware Multivariate Time Series Anomaly Detection via Multi-Scale Alignment and Struc… | arXiv | 2026-07-09 | abstract | strong_component |
| SD101 | [Abbas et al. 2026](https://arxiv.org/abs/2608.17775): Training-Free Human-in-the-Loop Anomaly Detection via Memory Bank Correction | arXiv | 2026-08-18 | abstract | strong_component |
| SD061 | [Bindini et al. 2025](https://arxiv.org/abs/2507.04490): Dealing with Uncertainty in Contextual Anomaly Detection | arXiv | 2025-07-06 | abstract | strong_component |
| SD074 | [Li et al. 2025a](https://doi.org/10.1016/j.neucom.2025.130137): A dynamic anchor-based online semi-supervised learning approach for fault diagnosis under variable o… | Neurocomputing | 2025-07 | metadata_only | strong_component |
| SD091 | [Soni et al. 2025](https://arxiv.org/abs/2508.11528): Physics-Informed Diffusion Models for Unsupervised Anomaly Detection in Multivariate Time Series | arXiv | 2025-08-15 | abstract | strong_component |
| SD060 | [Calikus et al. 2024](https://doi.org/10.1007/s41060-024-00586-x): Context discovery for anomaly detection | International Journal of Data Science and Ana | 2024-06-18 | abstract | strong_component |
| SD078 | [Cheng et al. 2023](https://doi.org/10.1007/s12555-022-0241-2): Just-in-time Learning-aided Nonlinear Fault Detection for Traction Systems of High-speed Trains | International Journal of Control, Automation  | 2023-08-29 | metadata_only | strong_component |
| SD080 | [Müller et al. 2023](https://arxiv.org/abs/2305.16907): CyPhERS: A Cyber-Physical Event Reasoning System providing real-time situational awareness for attac… | arXiv / Journal | 2023-05-26 | abstract | strong_component |
| SD069 | [Zhang et al. 2021](https://arxiv.org/abs/2012.07044): Monitoring multimode processes: a modified PCA algorithm with continual learning ability | Journal of Process Control | 2020-12-13 | abstract | strong_component |
| SD107 | [Giraldo et al. 2018](https://doi.org/10.1145/3203245): A Survey of Physics-Based Attack Detection in Cyber-Physical Systems | ACM Computing Surveys | 2018-07-25 | abstract | strong_component |
| SD112 | [Shoukry et al. 2017](https://doi.org/10.1109/tac.2017.2676679): Secure State Estimation for Cyber-Physical Systems Under Sensor Attacks: A Satisfiability Modulo The… | IEEE Transactions on Automatic Control | 2017-10 | metadata_only | strong_component |
| SD106 | [Urbina et al. 2016](https://doi.org/10.1145/2976749.2978388): Limiting the Impact of Stealthy Attacks on Industrial Control Systems | Proceedings of the 2016 ACM SIGSAC Conference | 2016-10-24 | abstract | strong_component |
| SD057 | [Valko et al. 2011](https://doi.org/10.1109/icdm.2011.40): Conditional Anomaly Detection with Soft Harmonic Functions | 2011 IEEE 11th International Conference on Da | 2011-12 | metadata_only | strong_component |
| SD058 | [Catterson et al. 2010](https://doi.org/10.1109/tpwrd.2010.2049754): Online Conditional Anomaly Detection in Multivariate Data for Transformer Monitoring | IEEE Transactions on Power Delivery | 2010-10 | metadata_only | strong_component |
| SD067 | [Lu et al. 2004](https://doi.org/10.1002/aic.10024): Sub‐PCA modeling and on‐line monitoring strategy for batch processes | AIChE Journal | 2004-01-23 | abstract | strong_component |
| SD063 | [Mishra et al. 2026a](https://arxiv.org/abs/2601.22868): Conditional Compatibility Learning for Context-Dependent Anomaly Detection | arXiv | 2026-01-30 | abstract | adjacent |
| SD084 | [Oluwatosin 2026](https://doi.org/10.21203/rs.3.rs-8555566/v1): Digital Twins for Detecting Anomalous Sensor behavior in Process Industries | Research Square preprint | 2026-01-13 | metadata_only | adjacent |
| SD093 | [Mishra et al. 2026b](https://arxiv.org/abs/2604.17616): Conditional Attribution for Root Cause Analysis in Time-Series Anomaly Detection | arXiv | 2026-04-19 | abstract | adjacent |
| SD321 | [Zhang et al. 2026a](https://doi.org/10.1016/j.compchemeng.2026.109749): Adaptive continual fault detection for industrial processes with evolving data distributions | Computers & Chemical Engineering | 2026-06-13 | metadata_only | adjacent · future issue 2026-10 |
| SD324 | [Azadi et al. 2026](https://doi.org/10.1016/j.epsr.2026.114221): Learning fuzzy normal-operation regimes for interpretable power system anomaly detection | Electric Power Systems Research | 2026-09-19 | abstract | adjacent · future issue 2027-04 |
| SD329 | [Wang et al. 2026f](https://doi.org/10.1016/j.conengprac.2026.107246): Adaptive temporal sparse manifold representation for reliable fault detection in multimode industria… | Control Engineering Practice | 2026-09-10 | metadata_only | adjacent · future issue 2027-01 |
| SD333 | [Abedin et al. 2026](https://doi.org/10.1016/j.epsr.2026.113501): Streaming self-supervised graph learning for evidence-aware anomaly detection in cyber–physical smar… | Electric Power Systems Research | 2026-06-25 | metadata_only | adjacent · future issue 2027-01 |
| SD077 | [Li et al. 2023](https://arxiv.org/abs/2305.00169): An Evidential Real-Time Multi-Mode Fault Diagnosis Approach Based on Broad Learning System | arXiv | 2023-04-29 | abstract | adjacent |
| SD098 | [Papadopoulos et al. 2026](https://doi.org/10.1145/3802119): The Power of Anomaly Detection in Predictive Maintenance: [Experiments &amp; Analysis] | Proceedings of the ACM on Management of Data | 2026-05-18 | abstract | background |
| SD089 | [Shang et al. 2025](https://arxiv.org/abs/2511.06894): COGNOS: Universal Enhancement for Time Series Anomaly Detection via Constrained Gaussian-Noise Optim… | arXiv | 2025-11-10 | abstract | background |
| SD099 | [Mateo et al. 2024](https://arxiv.org/abs/2405.11960): Dynamic classifier auditing by unsupervised anomaly detection methods: an application in packaging i… | arXiv | 2024-05-20 | metadata_only | background |
| SD071 | [Guo et al. 2023](https://doi.org/10.1016/j.measurement.2023.113700): Multimode process identification and monitoring based on hierarchical fluctuation window strategy | Measurement | 2023-12 | metadata_only | background |
| SD079 | [Liu et al. 2023](https://doi.org/10.1016/j.cie.2023.109502): Multi-scale adaptive multivariate state estimation fault detection enhancement for time-varying indu… | Computers &amp; Industrial Engineering | 2023-09 | metadata_only | background |
| SD081 | [Lv et al. 2023](https://doi.org/10.1016/j.ipm.2023.103383): Adaptive Multivariate Time-Series Anomaly Detection | Information Processing &amp; Management | 2023-07 | metadata_only | background |
| SD103 | [Jakubowski et al. 2023](https://doi.org/10.1145/3605390.3610830): Poster: Human-in-the-Loop Anomaly Detection in Industrial Data Streams | Proceedings of the 15th Biannual Conference o | 2023-09-20 | metadata_only | background |
| SD072 | [Ma & Zhang 2022](https://doi.org/10.3390/app12147207): Progress of Process Monitoring for the Multi-Mode Process: A Review | Applied Sciences | 2022-07-18 | abstract | background |
| SD082 | [Ray & Dash 2022](https://doi.org/10.1016/j.jksuci.2021.11.014): IoT-edge anomaly detection for covariate shifted and point time series health data | Journal of King Saud University - Computer an | 2022-11 | metadata_only | background |
| SD062 | [Calikus et al. 2021](https://arxiv.org/abs/2101.11560): Wisdom of the Contexts: Active Ensemble Learning for Contextual Anomaly Detection | arXiv | 2021-01-27 | metadata_only | background |
| SD114 | [Pocock 2021](https://arxiv.org/abs/2110.03022): Tribuo: Machine Learning with Provenance in Java | arXiv | 2021-10-06 | metadata_only | background |
| SD070 | [Song et al. 2016](https://doi.org/10.1016/j.jprocont.2016.09.006): Key principal components with recursive local outlier factor for multimode chemical process monitori… | Journal of Process Control | 2016-11 | metadata_only | background |
| SD073 | [Zhang et al. 2015](https://doi.org/10.1016/j.ifacol.2015.09.147): Process Monitoring Based on Recursive Probabilistic PCA for Multi-mode Process∗∗The work is supporte… | IFAC-PapersOnLine | 2015 | metadata_only | background |
| SD113 | [Yap & Tomlinson 2015](https://doi.org/10.1109/trustcom.2015.428): Provenance-Based Attestation for Trustworthy Computing | 2015 IEEE Trustcom/BigDataSE/ISPA | 2015-08 | metadata_only | background |
| SD059 | [Hayes & Capretz 2014](https://doi.org/10.1109/bigdata.congress.2014.19): Contextual Anomaly Detection in Big Sensor Data | 2014 IEEE International Congress on Big Data | 2014-06 | metadata_only | background |
| SD066 | [Nomikos & MacGregor 2004](https://doi.org/10.1002/aic.690400809): Monitoring batch processes using multiway principal component analysis | AIChE Journal | 2004-06-17 | abstract | background |

### E: Recurrence without forgetting (50 records)

| ID | Work | Venue | Date | Evidence | Threat |
|---|---|---|---|---|---|
| SD262 | [Li et al. 2026b](https://doi.org/10.1016/j.knosys.2026.116530): Adaptive drift aware continual learning with pool-based model reuse for time series applications | Knowledge-Based Systems | 2026-09 | abstract | direct |
| SD296 | [Li et al. 2026c](https://doi.org/10.24963/ijcai.2026/503): Beyond Uniform Updates: Drift Pattern Aware Online Time Series Forecasting (PADRE) | IJCAI | 2026-09 | as recorded in prior audit | direct |
| SD297 | [Fang et al. 2026](https://doi.org/10.1016/j.neucom.2026.135021): Normality-preserving continual industrial anomaly detection via orthogonal LoRA banks | Neurocomputing | 2026-12 | as recorded in prior audit | direct · future issue 2026-12 |
| SD305 | [Wei et al. 2026](https://doi.org/10.1145/3774904.3792440): Evolving Proxy Kills Drift: Data-Efficient Streaming Time Series Anomaly Detection | WWW | 2026-04-12 | as recorded in prior audit | direct |
| SD265 | [Li et al. 2025c](https://doi.org/10.1109/isctis65944.2025.11066053): Research on Adaptive Model Pooling Method for Data Stream Anomaly Detection Based on Concept Drift I… | 2025 5th International Symposium on Computer  | 2025-05-16 | abstract | direct |
| SD267 | [Liu et al. 2025b](https://doi.org/10.1109/smartiot66867.2025.00068): Global-Local Normalization based Model Pool for Online Anomaly Detection in IIoT | 2025 IEEE International Conference on Smart I | 2025-11-17 | abstract | direct |
| SD268 | [Li et al. 2025d](https://doi.org/10.1109/bigdata66926.2025.11400923): AURORA: An Adaptive and Unsupervised Framework for Robust Anomaly Detection via Historical Model Reu… | 2025 IEEE International Conference on Big Dat | 2025-12-08 | metadata_only | direct |
| SD293 | [Park et al. 2025](https://doi.org/10.1145/3746252.3761481): Adaptive Anomaly Detection in the Presence of Concept Drift (AnDri) | CIKM demo / arXiv | 2025-06-18 | as recorded in prior audit | direct |
| SD304 | [Li et al. 2025f](https://doi.org/10.1016/j.asoc.2025.113903): An unsupervised framework for drift-aware anomaly detection (ADA-ADF) | Applied Soft Computing | 2025-12 | as recorded in prior audit | direct |
| SD263 | [Li et al. 2024b](https://doi.org/10.1109/cac63892.2024.10865256): Research on Adaptive Model Pooling Method for Data Stream Anomaly Detection Based on Variational Aut… | 2024 China Automation Congress (CAC) | 2024-11-01 | abstract | direct |
| SD264 | [Ma et al. 2024](https://doi.org/10.1109/msn63567.2024.00054): Adaptive Time Window Enabled Model Pool for Online Deep Anomaly Detection in IIoT | 2024 20th International Conference on Mobilit | 2024-12-20 | abstract | direct |
| SD289 | [Kim et al. 2024](https://doi.org/10.1609/aaai.v38i12.29210): When Model Meets New Normals: Test-Time Adaptation for Unsupervised Time-Series Anomaly Detection | AAAI | 2024-03-24 | as recorded in prior audit | direct |
| SD291 | [Bhatia et al. 2022](https://doi.org/10.1145/3485447.3512221): MemStream: Memory-Based Streaming Anomaly Detection | WWW | 2022-04-25 | as recorded in prior audit | direct |
| SD294 | [Yoon et al. 2022](https://doi.org/10.1145/3534678.3539348): Adaptive Model Pooling for Online Deep Anomaly Detection from a Complex Evolving Data Stream (ARCUS) | KDD | 2022-08-14 | as recorded in prior audit | direct |
| SD322 | [Angiulli et al. 2026](https://doi.org/10.1016/j.neucom.2026.135118): A comprehensive survey on continual anomaly detection | Neurocomputing | 2026-09-17 | metadata_only | strong_component · future issue 2027-01 |
| SD248 | [Kabashkin 2025](https://doi.org/10.3390/electronics14152968): Federated Unlearning Framework for Digital Twin–Based Aviation Health Monitoring Under Sensor Drift … | Electronics | 2025-07-24 | abstract | strong_component |
| SD266 | [Chen et al. 2025](https://doi.org/10.1145/3746252.3761088): Stamp: Semantic-Aware Sub-trajectory Anomaly Detection with Diffusion Multi-model Pool for Evolving … | Proceedings of the 34th ACM International Con | 2025-11-10 | abstract | strong_component |
| SD281 | [Li et al. 2025e](https://doi.org/10.3390/a18060359): ADDAEIL: Anomaly Detection with Drift-Aware Ensemble-Based Incremental Learning | Algorithms | 2025-06-11 | abstract | strong_component |
| SD259 | [Alotaibi & Maffeis 2024](https://doi.org/10.1145/3678890.3678901): Mateen: Adaptive Ensemble Learning for Network Anomaly Detection | The 27th International Symposium on Research  | 2024-09-30 | abstract | strong_component |
| SD270 | [Wan et al. 2024](https://doi.org/10.1145/3637528.3672016): Online Drift Detection with Maximum Concept Discrepancy | Proceedings of the 30th ACM SIGKDD Conference | 2024-08-24 | abstract | strong_component |
| SD282 | [Liu et al. 2024](https://doi.org/10.1609/aaai.v38i4.28153): Unsupervised Continual Anomaly Detection with Contrastively-Learned Prompt | Proceedings of the AAAI Conference on Artific | 2024-03-24 | abstract | strong_component |
| SD229 | [Li et al. 2022](https://doi.org/10.1145/3503161.3548232): Towards Continual Adaptation in Industrial Anomaly Detection | Proceedings of the 30th ACM International Con | 2022-10-10 | abstract | strong_component |
| SD279 | [Museba et al. 2021](https://doi.org/10.1155/2021/5533777): Recurrent Adaptive Classifier Ensemble for Handling Recurring Concept Drifts | Applied Computational Intelligence and Soft C | 2021-06-10 | abstract | strong_component |
| SD280 | [Zhao et al. 2019](https://doi.org/10.1007/s10994-019-05835-w): Handling concept drift via model reuse | Machine Learning | 2019-10-10 | metadata_only | strong_component |
| SD283 | [Wiewel & Yang 2019](https://doi.org/10.1109/icassp.2019.8682702): Continual Learning for Anomaly Detection with Variational Autoencoder | ICASSP 2019 - 2019 IEEE International Confere | 2019-05 | abstract | strong_component |
| SD269 | [Zhao et al. 2026b](https://doi.org/10.1007/978-981-95-5640-3_6): Global-Memory and Local-Representation Based Framework for Streaming Anomaly Detection | Lecture Notes in Computer Science | 2026-01-30 | metadata_only | adjacent |
| SD321 | [Zhang et al. 2026a](https://doi.org/10.1016/j.compchemeng.2026.109749): Adaptive continual fault detection for industrial processes with evolving data distributions | Computers & Chemical Engineering | 2026-06-13 | metadata_only | adjacent · future issue 2026-10 |
| SD324 | [Azadi et al. 2026](https://doi.org/10.1016/j.epsr.2026.114221): Learning fuzzy normal-operation regimes for interpretable power system anomaly detection | Electric Power Systems Research | 2026-09-19 | abstract | adjacent · future issue 2027-04 |
| SD328 | [Lee et al. 2026](https://doi.org/10.1016/j.neucom.2026.134460): Continual-MEGA: A large-scale benchmark for generalizable continual anomaly detection | Neurocomputing | 2026-07-08 | abstract | adjacent · future issue 2026-11 |
| SD330 | [Zhang et al. 2026b](https://doi.org/10.1016/j.asoc.2026.115975): Industrial large model-driven online early fault warning: A novel incremental anomaly detection fram… | Applied Soft Computing | 2026-07-16 | metadata_only | adjacent · future issue 2026-11 |
| SD332 | [Lin et al. 2026](https://doi.org/10.1016/j.knosys.2026.116700): Interformer: Interpretable large time series model for concept drift adaptation | Knowledge-Based Systems | 2026-08-03 | metadata_only | adjacent · future issue 2026-10 |
| SD336 | [CLEAR (2026)](https://doi.org/10.1016/j.knosys.2026.116878): CLEAR: A continual learning framework for zero-day and anomaly-based intrusion detection | Knowledge-Based Systems | 2026-08-19 | metadata_only | adjacent · future issue 2026-10 |
| SD337 | [De Paola et al. 2026](https://doi.org/10.1016/j.jnca.2026.104556): HOIDS: Concept drift aware hybrid online intrusion detection system | Journal of Network and Computer Applications | 2026-07-23 | metadata_only | adjacent · future issue 2026-10 |
| SD254 | [Li et al. 2025b](https://arxiv.org/abs/2501.02107): Online Detection of Water Contamination Under Concept Drift | arXiv preprint | 2025-01-03 | abstract | adjacent |
| SD271 | [Liu et al. 2025c](https://doi.org/10.1145/3717071): Detecting Both Seen and Unseen Anomalies in Time Series | ACM Transactions on Knowledge Discovery from  | 2025-02-20 | abstract | adjacent |
| SD288 | [Nguyen & Park 2025](https://doi.org/10.3390/electronics14142756): EL-GNN: A Continual-Learning-Based Graph Neural Network for Task-Incremental Intrusion Detection Sys… | Electronics | 2025-07-09 | abstract | adjacent |
| SD286 | [Miao et al. 2024](https://doi.org/10.1109/icde60146.2024.00085): A Unified Replay-Based Continuous Learning Framework for Spatio-Temporal Prediction on Streaming Dat… | 2024 IEEE 40th International Conference on Da | 2024-05-13 | abstract | adjacent |
| SD287 | [Benzaïd et al. 2024](https://doi.org/10.1109/wcnc57260.2024.10570951): A Federated Continual Learning Framework for Sustainable Network Anomaly Detection in O-RAN | 2024 IEEE Wireless Communications and Network | 2024-04-21 | abstract | adjacent |
| SD189 | [Faber et al. 2024](https://doi.org/10.1109/access.2024.3377690): Lifelong Continual Learning for Anomaly Detection: New Challenges, Perspectives, and Insights | IEEE Access | 2024 | abstract | background |
| SD272 | [Suárez-Cetrulo et al. 2023](https://doi.org/10.1016/j.eswa.2022.118934): A survey on machine learning for recurring concept drifting data streams | Expert Systems with Applications | 2023-03 | abstract | background |
| SD285 | [Lee et al. 2023](https://doi.org/10.1145/3583780.3615236): Look At Me, No Replay! SurpriseNet: Anomaly Detection Inspired Class Incremental Learning | Proceedings of the 32nd ACM International Con | 2023-10-21 | abstract | background |
| SD257 | [Bayram et al. 2022](https://doi.org/10.1016/j.knosys.2022.108632): From concept drift to model degradation: An overview on performance-aware drift detectors | Knowledge-Based Systems | 2022-06 | abstract | background |
| SD260 | [De Lange & Tuytelaars 2021](https://doi.org/10.1109/iccv48922.2021.00814): Continual Prototype Evolution: Learning Online from Non-Stationary Data Streams | 2021 IEEE/CVF International Conference on Com | 2021-10 | abstract | background |
| SD284 | [Doshi & Yilmaz 2020](https://doi.org/10.1109/cvprw50498.2020.00135): Continual Learning for Anomaly Detection in Surveillance Videos | 2020 IEEE/CVF Conference on Computer Vision a | 2020-06 | abstract | background |
| SD278 | [Al-Khateeb et al. 2016](https://doi.org/10.1109/tkde.2015.2507123): Recurring and Novel Class Detection Using Class-Based Ensemble for Evolving Data Stream | IEEE Transactions on Knowledge and Data Engin | 2016-10-01 | abstract | background |
| SD275 | [Li et al. 2012](https://doi.org/10.1145/2089094.2089105): Mining Recurring Concept Drifts with Limited Labeled Streaming Data | ACM Transactions on Intelligent Systems and T | 2012-02 | abstract | background |
| SD277 | [Al-Khateeb et al. 2012](https://doi.org/10.1109/icdm.2012.125): Stream Classification with Recurring and Novel Class Detection Using Class-Based Ensemble | 2012 IEEE 12th International Conference on Da | 2012-12 | abstract | background |
| SD276 | [Masud et al. 2011](https://doi.org/10.1109/icdm.2011.49): Detecting Recurring and Novel Classes in Concept-Drifting Data Streams | 2011 IEEE 11th International Conference on Da | 2011-12 | abstract | background |
| SD273 | [Gama & Kosina 2009](https://doi.org/10.1007/978-3-642-04686-5_35): Tracking Recurring Concepts with Meta-learners | Lecture Notes in Computer Science | 2009 | metadata_only | background |
| SD274 | [Katakis et al. 2009](https://doi.org/10.1007/s10115-009-0206-2): Tracking recurring contexts using ensemble classifiers: an application to email filtering | Knowledge and Information Systems | 2009-04-24 | metadata_only | background |

### F: Normal-only commissioning (42 records)

| ID | Work | Venue | Date | Evidence | Threat |
|---|---|---|---|---|---|
| SD143 | [Jonas & Meyer 2026](https://arxiv.org/abs/2608.30323): Generative multi-domain transfer learning for fault detection in data-scarce wind turbines | arXiv preprint | 2026-08-31 | abstract | direct |
| SD149 | [Nie et al. 2026](https://arxiv.org/abs/2606.22261): Learning a Normal World Model for Few-Shot Boundary-Calibrated Abnormality Detection | arXiv preprint | 2026-06-20 | abstract | direct |
| SD117 | [Shentu et al. 2025](https://arxiv.org/abs/2405.15273): Towards a General Time Series Anomaly Detector with Adaptive Bottlenecks and Dual Adversarial Decode… | ICLR 2025 | 2024-05-24 | abstract | direct |
| SD118 | [Lan et al. 2025](https://arxiv.org/abs/2509.21190): Towards Foundation Models for Zero-Shot Time Series Anomaly Detection: Leveraging Synthetic Data and… | arXiv preprint (code release cites ICML 2026) | 2025-09-25 | abstract | direct |
| SD119 | [Ekambaram et al. 2025](https://arxiv.org/abs/2505.13033): TSPulse: Tiny Pre-Trained Models with Disentangled Representations for Rapid Time-Series Analysis | arXiv preprint (IBM Research) | 2025-05-19 | abstract | direct |
| SD127 | [Darban et al. 2025](https://doi.org/10.1109/tkde.2025.3569909): DACAD: Domain Adaptation Contrastive Learning for Anomaly Detection in Multivariate Time Series | IEEE Transactions on Knowledge and Data Engin | 2025-08 | abstract | direct |
| SD130 | [Jacob & Diao 2025](https://arxiv.org/abs/2503.23060): Unsupervised Anomaly Detection in Multivariate Time Series across Heterogeneous Domains | arXiv preprint | 2025-03-29 | abstract | direct |
| SD135 | [Holly et al. 2025](https://arxiv.org/abs/2501.13052): One-Class Domain Adaptation via Meta-Learning | arXiv preprint | 2025-01-22 | abstract | direct |
| SD142 | [Jonas & Meyer 2025](https://arxiv.org/abs/2504.17709): Fault Detection in New Wind Turbines with Limited Data by Generative Transfer Learning | arXiv preprint | 2025-04-24 | abstract | direct |
| SD145 | [He et al. 2025](https://doi.org/10.1016/j.nucengdes.2025.113956): Cross-Domain Few-Shot Anomaly Detection for equipment in nuclear power plants | Nuclear Engineering and Design | 2025-05 | abstract | direct |
| SD303 | [Faber et al. 2025](https://doi.org/10.1109/icdm65498.2025.00032): xLSTMAD: A Powerful xLSTM-based Method for Anomaly Detection | ICDM | 2025-06-28 | as recorded in prior audit | direct |
| SD120 | [Gao et al. 2024](https://doi.org/10.52202/079017-4463): UniTS: A Unified Multi-Task Time Series Model | Advances in Neural Information Processing Sys | 2024 | abstract | direct |
| SD128 | [He et al. 2024a](https://doi.org/10.1145/3663573): Variate Associated Domain Adaptation for Unsupervised Multivariate Time Series Anomaly Detection | ACM Transactions on Knowledge Discovery from  | 2024-07-26 | abstract | direct |
| SD141 | [Roelofs et al. 2024](https://arxiv.org/abs/2404.03011): Transfer learning applications for anomaly detection in wind turbines | Data-Centric Engineering (Cambridge) / arXiv | 2024-04-03 | abstract | direct |
| SD148 | [Reiss et al. 2024](https://arxiv.org/abs/2405.20341): From Zero to Hero: Cold-Start Anomaly Detection | arXiv preprint | 2024-05-30 | abstract | direct |
| SD129 | [Lai et al. 2023](https://arxiv.org/abs/2304.07453): Context-aware Domain Adaptation for Time Series Anomaly Detection | SIAM International Conference on Data Mining  | 2023-04-15 | abstract | direct |
| SD136 | [Moon et al. 2023](https://doi.org/10.1016/j.jobe.2023.106099): Anomaly detection using a model-agnostic meta-learning-based variational auto-encoder for facility m… | Journal of Building Engineering | 2023-06 | abstract | direct |
| SD134 | [Frikha et al. 2021](https://arxiv.org/abs/2007.04146): Few-Shot One-Class Classification via Meta-Learning | AAAI 2021 | 2020-07-08 | abstract | direct |
| SD123 | [Yang et al. 2026a](https://arxiv.org/abs/2602.16681): VETime: Vision Enhanced Zero-Shot Time Series Anomaly Detection | arXiv preprint | 2026-02-18 | metadata_only | strong_component |
| SD132 | [Meng et al. 2026](https://arxiv.org/abs/2606.23120): Temporal-Spectral Alignment with Frequency Adaptation for Source-Free Time-Series Adaptation | arXiv preprint | 2026-06-22 | abstract | strong_component |
| SD146 | [Wang et al. 2026e](https://arxiv.org/abs/2606.24459): An LLM-based Two-Stage Transformer Framework for Cross-Domain Bearing Fault Diagnosis with Limited D… | arXiv preprint | 2026-06-23 | abstract | strong_component |
| SD319 | [Yang 2026](https://doi.org/10.1016/j.asoc.2026.116360): Representation stability is not detectability: A leakage-free evaluation of frozen time series found… | Applied Soft Computing | 2026-09-07 | metadata_only | strong_component · future issue 2027-01 |
| SD340 | [One-liners paper (ICLR 2026)](https://openreview.net/forum?id=H27kvyG4qf): When Foundation Models are One-Liners: Limitations and Future Directions for Time Series Anomaly Det… | ICLR 2026 (OpenReview) | 2026 | abstract | strong_component |
| SD122 | [Cheng et al. 2025](https://arxiv.org/abs/2510.16014): STAR: Boosting Time Series Foundation Models for Anomaly Detection through State-aware Adapter | arXiv preprint | 2025-10-15 | abstract | strong_component |
| SD125 | [Han & Lee 2025](https://arxiv.org/abs/2509.12650): Leveraging Intermediate Representations of Time Series Foundation Models for Anomaly Detection | arXiv preprint | 2025-09-16 | metadata_only | strong_component |
| SD133 | [Jeong et al. 2025](https://doi.org/10.3390/s25144383): Source-Free Domain Adaptation Framework for Rotary Machine Fault Diagnosis | Sensors | 2025-07-13 | abstract | strong_component |
| SD138 | [Aqeel et al. 2025](https://arxiv.org/abs/2508.17789): Robust Anomaly Detection in Industrial Environments via Meta-Learning | arXiv preprint | 2025-08-25 | abstract | strong_component |
| SD139 | [Zhang et al. 2025](https://doi.org/10.3390/e27101063): Dynamic MAML with Efficient Multi-Scale Attention for Cross-Load Few-Shot Bearing Fault Diagnosis | Entropy | 2025-10-14 | metadata_only | strong_component |
| SD137 | [Xie et al. 2024c](https://doi.org/10.1016/j.cose.2024.104075): Anomaly detection for multivariate time series in IoT using discrete wavelet decomposition and dual … | Computers &amp; Security | 2024-11 | abstract | strong_component |
| SD150 | [Zero-faulty sample machinery fault detection via (2024)](https://www.sciencedirect.com/science/article/abs/pii/S0952197624019122): Zero-faulty sample machinery fault detection via relation network with out-of-distribution data augm… | Engineering Applications of Artificial Intell | 2024-12 | abstract | strong_component |
| SD131 | [Ragab et al. 2023](https://doi.org/10.1145/3580305.3599507): Source-Free Domain Adaptation with Temporal Imputation for Time Series Data | Proceedings of the 29th ACM SIGKDD Conference | 2023-08-04 | abstract | strong_component |
| SD144 | [Liu et al. 2022](https://doi.org/10.3390/s22093288): A Model-Agnostic Meta-Baseline Method for Few-Shot Fault Diagnosis of Wind Turbines | Sensors | 2022-04-25 | metadata_only | strong_component |
| SD151 | [Yin et al. 2026](https://doi.org/10.1016/b978-0-44-344291-9.00010-2): Generalized zero-sample industrial fault diagnosis with domain bias | INTELLIGENT FAULT DIAGNOSIS AND PROGNOSIS FOR | 2026 | metadata_only | adjacent |
| SD327 | [Liu et al. 2026](https://doi.org/10.1016/j.ast.2026.111972): Few-shot anomaly detection for aerospace telemetry data based on model-agnostic meta-learning | Aerospace Science and Technology | 2026-02-26 | metadata_only | adjacent · future issue 2026-10 |
| SD126 | [Lorik et al. 2025](https://arxiv.org/abs/2510.03911): THEMIS: Unlocking Pretrained Knowledge with Foundation Model Embeddings for Anomaly Detection in Tim… | arXiv preprint | 2025-10-04 | metadata_only | adjacent |
| SD147 | [He et al. 2024b](https://arxiv.org/abs/2406.11917): Modulated differentiable STFT and balanced spectrum metric for freight train wheelset bearing cross-… | arXiv preprint | 2024-06-17 | metadata_only | adjacent |
| SD140 | [Xue & Yan 2022](https://arxiv.org/abs/2207.00705): Multivariate Time Series Anomaly Detection with Few Positive Samples | arXiv preprint / GE Research | 2022-07-02 | abstract | adjacent |
| SD152 | [Sui et al. 2026](https://doi.org/10.1049/gtd2.70361): Zero‐Shot‐Motivated Intelligent Fault Diagnosis: A Survey of Methods, Applications, and Future Direc… | IET Generation, Transmission &amp; Distributi | 2026-06-23 | abstract | background |
| SD121 | [Liu & Paparrizos 2024a](https://doi.org/10.52202/079017-3437): The Elephant in the Room: Towards A Reliable Time-Series Anomaly Detection Benchmark | Advances in Neural Information Processing Sys | 2024 | abstract | background |
| SD124 | [Shyalika et al. 2024](https://arxiv.org/abs/2412.19286): Time Series Foundational Models: Their Role in Anomaly Detection and Prediction | arXiv preprint | 2024-12-26 | abstract | background |
| SD153 | [Yan et al. 2024](https://doi.org/10.1109/access.2023.3349132): A Comprehensive Survey of Deep Transfer Learning for Anomaly Detection in Industrial Time Series: Me… | IEEE Access | 2024 | abstract | background |
| SD154 | [Zamanzadeh Darban et al. 2024](https://doi.org/10.1145/3691338): Deep Learning for Time Series Anomaly Detection: A Survey | ACM Computing Surveys | 2024-10-07 | abstract | background |

### G: Semantic-shift benchmark (33 records)

| ID | Work | Venue | Date | Evidence | Threat |
|---|---|---|---|---|---|
| SD295 | [Le et al. 2026](https://doi.org/10.1145/3744255.3811742): Drift-Aware Online Anomaly Detection in Smart Buildings via Temporal Variational Autoencoder Gradien… | ACM e-Energy | 2026-06-22 | as recorded in prior audit | direct |
| SD160 | [Cao et al. 2024](https://doi.org/10.1007/s10462-024-10995-w): Revisiting streaming anomaly detection: benchmark and evaluation | Artificial Intelligence Review | 2024-11-07 | abstract | direct |
| SD166 | [Liu & Paparrizos 2024b](https://doi.org/10.52202/079017-3437): The Elephant in the Room: Towards A Reliable Time-Series Anomaly Detection Benchmark | Advances in Neural Information Processing Sys | 2024 | abstract | direct |
| SD168 | [Li et al. 2024a](https://doi.org/10.1016/j.datak.2024.102365): State-transition-aware anomaly detection under concept drifts | Data &amp; Knowledge Engineering | 2024-11 | abstract | direct |
| SD309 | [Dragoi et al. 2022b](https://arxiv.org/abs/2206.15476): AnoShift: A Distribution Shift Benchmark for Unsupervised Anomaly Detection | NeurIPS D&B | 2022-06-30 | as recorded in prior audit | direct |
| SD162 | [Faber et al. 2026](https://arxiv.org/abs/2607.18289): Towards Principled Continual Anomaly Detection: A Systematic Framework and Benchmark Scenarios | arXiv preprint | 2026-06-30 | abstract | strong_component |
| SD163 | [Asadi 2026](https://arxiv.org/abs/2607.16811): Dimension-Calibrated Unexplained Mass: An Interpretable Drift Statistic for Contamination Monitoring… | arXiv preprint | 2026-07-18 | abstract | strong_component |
| SD171 | [Gower-Winter et al. 2026](https://arxiv.org/abs/2602.06456): The Window Dilemma: Why Concept Drift Detection is Ill-Posed | arXiv preprint | 2026-02-06 | abstract | strong_component |
| SD173 | [Michailoudis et al. 2026](https://doi.org/10.1016/j.softx.2026.102995): SDG: A domain-specific language for the automated synthesis of stream data generators with multi-typ… | SoftwareX | 2026-09 | abstract | strong_component |
| SD322 | [Angiulli et al. 2026](https://doi.org/10.1016/j.neucom.2026.135118): A comprehensive survey on continual anomaly detection | Neurocomputing | 2026-09-17 | metadata_only | strong_component · future issue 2027-01 |
| SD338 | [Velasco & Zafra 2026](https://doi.org/10.1016/j.neucom.2026.134154): TSADmetrics: A library for evaluating time series anomaly detection methods | Neurocomputing | 2026-06-05 | abstract | strong_component · future issue 2026-10 |
| SD316 | [Wagner et al. 2025](https://arxiv.org/abs/2510.17562): Formally Exploring Time-Series Anomaly Detection Evaluation Metrics | arXiv | 2025-10-20 | abstract | strong_component |
| SD169 | [Lukats et al. 2024](https://doi.org/10.1007/s41060-024-00620-y): A benchmark and survey of fully unsupervised concept drift detectors on real-world data streams | International Journal of Data Science and Ana | 2024-08-27 | abstract | strong_component |
| SD158 | [Wenig et al. 2022](https://doi.org/10.14778/3554821.3554873): TimeEval | Proceedings of the VLDB Endowment | 2022-09-29 | abstract | strong_component |
| SD312 | [Kim et al. 2022](https://doi.org/10.1609/aaai.v36i7.20680): Towards a Rigorous Evaluation of Time-Series Anomaly Detection | AAAI | 2022-06-28 | abstract | strong_component |
| SD174 | [Jacob et al. 2020](https://arxiv.org/abs/2010.05073): Exathlon: A Benchmark for Explainable Anomaly Detection over Time Series | Proceedings of the VLDB Endowment (arXiv prep | 2020-10-10 | abstract | strong_component |
| SD164 | [Lyu 2026](https://arxiv.org/abs/2607.11969): Did We Actually Fix It? An Independent Adversarial Stress-Test of Post-Point-Adjustment Evaluation M… | arXiv preprint | 2026-07-12 | abstract | adjacent |
| SD170 | [Cerqueira et al. 2026](https://arxiv.org/abs/2606.07789): A Framework for Evaluating and Benchmarking Concept Drift Detection Methods | KDD 2026 | 2026-06-05 | abstract | adjacent |
| SD172 | [Youssef 2026](https://arxiv.org/abs/2605.24696): Stream Assembly Is an Uncontrolled Treatment in Streaming Intrusion-Detection Benchmarks | arXiv preprint | 2026-05-23 | abstract | adjacent |
| SD317 | [Li et al. 2026d](https://arxiv.org/abs/2603.06131): DQE: A Semantic-Aware Evaluation Metric for Time Series Anomaly Detection | arXiv | 2026-03-06 | abstract | adjacent |
| SD328 | [Lee et al. 2026](https://doi.org/10.1016/j.neucom.2026.134460): Continual-MEGA: A large-scale benchmark for generalizable continual anomaly detection | Neurocomputing | 2026-07-08 | abstract | adjacent · future issue 2026-11 |
| SD331 | [Cabrera Martin et al. 2026](https://doi.org/10.1016/j.eswa.2026.133370): Cluster-specific localized drift detection for efficient batch model adaptation under controlled dis… | Expert Systems with Applications | 2026-06-26 | abstract | adjacent · future issue 2026-12 |
| SD339 | [Yang et al. 2026b](https://doi.org/10.1016/j.neucom.2026.134547): A problem-oriented taxonomy of evaluation metrics for time series anomaly detection | Neurocomputing | 2026-07-20 | metadata_only | adjacent · future issue 2026-11 |
| SD318 | [Yang et al. 2025](https://arxiv.org/abs/2511.18739): A Problem-Oriented Taxonomy of Evaluation Metrics for Time Series Anomaly Detection | arXiv; Neurocomputing (issue 2026-11) | 2025-11-24 | abstract | adjacent · future issue 2026-11 |
| SD156 | [Paparrizos et al. 2022a](https://doi.org/10.14778/3529337.3529354): TSB-UAD | Proceedings of the VLDB Endowment | 2022-06-22 | abstract | adjacent |
| SD175 | [Dragoi et al. 2022a](https://arxiv.org/abs/2206.15476): AnoShift: A Distribution Shift Benchmark for Unsupervised Anomaly Detection | NeurIPS 2022 Datasets & Benchmarks Track | 2022-06-30 | abstract | adjacent |
| SD165 | [Pinet et al. 2026](https://arxiv.org/abs/2606.02670): Anomalies in Multivariate Time Series Benchmarks Are Mostly Univariate | arXiv preprint | 2026-06-01 | abstract | background |
| SD161 | [Röchner et al. 2025](https://arxiv.org/abs/2507.15584): We Need to Rethink Benchmarking in Anomaly Detection | arXiv preprint | 2025-07-21 | abstract | background |
| SD167 | [Liu et al. 2025a](https://doi.org/10.14778/3749646.3749699): TSB-AutoAD: Towards Automated Solutions for Time-Series Anomaly Detection | Proceedings of the VLDB Endowment | 2025-09-04 | abstract | background |
| SD157 | [Paparrizos et al. 2022b](https://doi.org/10.14778/3551793.3551830): Volume under the surface | Proceedings of the VLDB Endowment | 2022-09-29 | abstract | background |
| SD176 | [Han et al. 2022](https://doi.org/10.2139/ssrn.4266498): ADBench: Anomaly Detection Benchmark | NeurIPS 2022 Datasets & Benchmarks Track | 2022 | abstract | background |
| SD155 | [Wu & Keogh 2021](https://doi.org/10.1109/tkde.2021.3112126): Current Time Series Anomaly Detection Benchmarks are Flawed and are Creating the Illusion of Progres… | IEEE Transactions on Knowledge and Data Engin | 2021 | abstract | background |
| SD159 | [Lavin & Ahmad 2015](https://arxiv.org/abs/1510.03336): Evaluating Real-time Anomaly Detection Algorithms - the Numenta Anomaly Benchmark | IEEE ICMLA 2015 (NAB) | 2015-10-12 | abstract | background |

### H: Resource-constrained continual TSAD (18 records)

| ID | Work | Venue | Date | Evidence | Threat |
|---|---|---|---|---|---|
| SD022 | [Dasari 2026](https://arxiv.org/abs/2608.19488): When to Retrain: An Empirical Study of Retraining Policies for Streaming ML Under Concept Drift, Bud… | arXiv | 2026-08-19 | abstract | direct |
| SD177 | [Smendowski et al. 2026](https://doi.org/10.1007/s10723-026-09846-5): Bridging Continual Learning and Green Cloud Computing: Foundations for Sustainable Time Series Anoma… | Journal of Grid Computing | 2026-09-01 | full_text | direct |
| SD020 | [Mahadevan & Mathioudakis 2024](https://doi.org/10.1016/j.knosys.2024.111610): Cost-aware retraining for machine learning | Knowledge-Based Systems | 2024-06 | abstract | direct |
| SD162 | [Faber et al. 2026](https://arxiv.org/abs/2607.18289): Towards Principled Continual Anomaly Detection: A Systematic Framework and Benchmark Scenarios | arXiv preprint | 2026-06-30 | abstract | strong_component |
| SD185 | [Marinova et al. 2026](https://arxiv.org/abs/2603.07507): Online Continual Learning for Anomaly Detection in IoT under Data Distribution Shifts | arXiv preprint | 2026-03-08 | abstract | strong_component |
| SD180 | [Vázquez et al. 2025](https://arxiv.org/abs/2510.06910): Vacuum Spiker: A Spiking Neural Network-Based Model for Efficient Anomaly Detection in Time Series | arXiv preprint | 2025-10-08 | abstract | strong_component |
| SD181 | [Piaseczny et al. 2025](https://arxiv.org/abs/2505.24149): RCCDA: Adaptive Model Updates in the Presence of Concept Drift under a Constrained Resource Budget | NeurIPS 2025 | 2025-05-30 | abstract | strong_component |
| SD184 | [Frederiksen et al. 2025](https://arxiv.org/abs/2512.13340): Link-Aware Energy-Frugal Continual Learning for Fault Detection in IoT Networks | arXiv preprint | 2025-12-15 | abstract | strong_component |
| SD178 | [Weatherly & Lin 2026](https://arxiv.org/abs/2605.24251): Rethinking Continual Anomaly Detection on the Edge: Benchmarking Under Realistic Industrial Conditio… | ECCV 2026 | 2026-05-22 | abstract | adjacent |
| SD179 | [Barusco et al. 2026](https://arxiv.org/abs/2604.06435): Continual Visual Anomaly Detection on the Edge: Benchmark and Efficient Solutions | arXiv preprint | 2026-04-07 | abstract | adjacent |
| SD182 | [Katz 2026](https://arxiv.org/abs/2604.06438): Cost-sensitive retraining via posterior learning debt | arXiv preprint | 2026-04-07 | abstract | adjacent |
| SD188 | [Jung et al. 2026](https://arxiv.org/abs/2608.15277): Memory-Bounded Continuation of Greedy Sampling for Continual Anomaly Detection | arXiv preprint | 2026-08-15 | abstract | adjacent |
| SD331 | [Cabrera Martin et al. 2026](https://doi.org/10.1016/j.eswa.2026.133370): Cluster-specific localized drift detection for efficient batch model adaptation under controlled dis… | Expert Systems with Applications | 2026-06-26 | abstract | adjacent · future issue 2026-12 |
| SD183 | [Beytur et al. 2025](https://arxiv.org/abs/2512.12816): Optimal Resource Allocation for ML Model Training and Deployment under Concept Drift | arXiv preprint | 2025-12-14 | abstract | adjacent |
| SD186 | [Rüb et al. 2024](https://arxiv.org/abs/2409.07114): A Continual and Incremental Learning Approach for TinyML On-device Training Using Dataset Distillati… | arXiv preprint | 2024-09-11 | abstract | background |
| SD189 | [Faber et al. 2024](https://doi.org/10.1109/access.2024.3377690): Lifelong Continual Learning for Anomaly Detection: New Challenges, Perspectives, and Insights | IEEE Access | 2024 | abstract | background |
| SD190 | [Hurtado et al. 2023](https://doi.org/10.1016/j.iswa.2023.200251): Continual learning for predictive maintenance: Overview and challenges | Intelligent Systems with Applications | 2023-09 | abstract | background |
| SD187 | [Ravaglia et al. 2021](https://doi.org/10.1109/jetcas.2021.3121554): A TinyML Platform for On-Device Continual Learning With Quantized Latent Replays | IEEE Journal on Emerging and Selected Topics  | 2021-12 | abstract | background |

### N1: Promotion rules as an attack surface (14 records)

| ID | Work | Venue | Date | Evidence | Threat |
|---|---|---|---|---|---|
| SD291 | [Bhatia et al. 2022](https://doi.org/10.1145/3485447.3512221): MemStream: Memory-Based Streaming Anomaly Detection | WWW | 2022-04-25 | as recorded in prior audit | direct |
| SD198 | [Kravchik et al. 2021](https://doi.org/10.1145/3412841.3441892): Poisoning attacks on cyber attack detectors for industrial control systems | Proceedings of the 36th Annual ACM Symposium  | 2021-04-22 | abstract | direct |
| SD194 | [Kravchik & Shabtai 2020](https://arxiv.org/abs/2002.02741): Can't Boil This Frog: Robustness of Online-Trained Autoencoder-Based Anomaly Detectors to Adversaria… | arXiv preprint | 2020-02-07 | abstract | direct |
| SD191 | [Kloft & Laskov 2012](https://arxiv.org/abs/1003.0078): Security Analysis of Online Centroid Anomaly Detection | Journal of Machine Learning Research (JMLR) 1 | 2010-02-27 | abstract | direct |
| SD192 | [Rubinstein et al. 2009a](https://doi.org/10.1145/1644893.1644895): ANTIDOTE | Proceedings of the 9th ACM SIGCOMM conference | 2009-11-04 | abstract | direct |
| SD199 | [Ozbek et al. 2026](https://arxiv.org/abs/2608.23547): Robustness of Anomaly Detection Models for Industrial Control Systems under Training-Time Data Conta… | arXiv preprint | 2026-08-24 | metadata_only | strong_component |
| SD201 | [Salish & S 2026](https://arxiv.org/abs/2606.14987): Continual Backdoor Training in IoT/CPS | arXiv preprint | 2026-06-12 | metadata_only | strong_component |
| SD200 | [Abedzadeh & Bhattacharjee 2025](https://doi.org/10.3390/info16060428): Mitigating Impact of Data Poisoning Attacks on CPS Anomaly Detection with Provable Guarantees | Information | 2025-05-23 | abstract | strong_component |
| SD196 | [Cong et al. 2024](https://arxiv.org/abs/2308.08505): Test-Time Poisoning Attacks Against Test-Time Adaptation Models | IEEE Symposium on Security and Privacy (S&P)  | 2023-08-16 | abstract | strong_component |
| SD195 | [Korycki Ł. & Krawczyk 2022](https://doi.org/10.1007/s10994-022-06177-w): Adversarial concept drift detection under poisoning attacks for robust data stream mining | Machine Learning | 2022-06-02 | abstract | strong_component |
| SD193 | [Rubinstein et al. 2009b](https://doi.org/10.1145/1639562.1639592): Stealthy poisoning attacks on PCA-based anomaly detectors | ACM SIGMETRICS Performance Evaluation Review | 2009-10-16 | abstract | strong_component |
| SD336 | [CLEAR (2026)](https://doi.org/10.1016/j.knosys.2026.116878): CLEAR: A continual learning framework for zero-day and anomaly-based intrusion detection | Knowledge-Based Systems | 2026-08-19 | metadata_only | adjacent · future issue 2026-10 |
| SD197 | [Su et al. 2024](https://arxiv.org/abs/2410.04682): On the Adversarial Risk of Test Time Adaptation: An Investigation into Realistic Test-Time Data Pois… | arXiv preprint (extends ICML 2024 'Uncovering | 2024-10-07 | abstract | adjacent |
| SD202 | [Abbasi et al. 2023](https://arxiv.org/abs/2311.11995): BrainWash: A Poisoning Attack to Forget in Continual Learning | arXiv preprint | 2023-11-20 | metadata_only | adjacent |

### N2: Peer-corroborated normality (7 records)

| ID | Work | Venue | Date | Evidence | Threat |
|---|---|---|---|---|---|
| SD203 | [Stavrou et al. 2009](https://doi.org/10.1145/1654988.1655000): Keep your friends close | Proceedings of the 2nd ACM workshop on Securi | 2009-11-09 | abstract | direct |
| SD208 | [Bera et al. 2026](https://arxiv.org/abs/2606.31789): Distributed Hierarchical Temporal Memory with Shared Associative Memory for Cross-Entity Preemptive … | arXiv preprint | 2026-06-30 | metadata_only | strong_component |
| SD205 | [Smith et al. 2024](https://arxiv.org/abs/2402.19295): Anomaly Detection in Offshore Wind Turbine Structures using Hierarchical Bayesian Modelling | arXiv preprint | 2024-02-29 | metadata_only | strong_component |
| SD206 | [de Novaes Pires Leite et al. 2023](https://doi.org/10.1016/j.engappai.2023.106859): A robust fleet-based anomaly detection framework applied to wind turbine vibration data | Engineering Applications of Artificial Intell | 2023-11 | abstract | strong_component |
| SD204 | [Tveten et al. 2022](https://doi.org/10.1214/21-aoas1508): Scalable change-point and anomaly detection in cross-correlated data with an application to conditio… | The Annals of Applied Statistics | 2022-06-01 | abstract | strong_component |
| SD207 | [Giobergia et al. 2024](https://arxiv.org/abs/2408.14682): Detecting Interpretable Subgroup Drifts | arXiv preprint | 2024-08-26 | abstract | adjacent |
| SD209 | [Multitenant Sharing Anomaly Cyberattack Campaign (2018)](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11888870): Multitenant Sharing Anomaly Cyberattack Campaign Detection | US Patent (image-ppubs.uspto.gov filing 11888 | 2018 | metadata_only | adjacent |

### N3: Interventional disambiguation (7 records)

| ID | Work | Venue | Date | Evidence | Threat |
|---|---|---|---|---|---|
| SD214 | [Wang et al. 2025b](https://doi.org/10.1016/j.engappai.2025.111991): Boosting industrial anomaly detection performance using generated artificial fault data | Engineering Applications of Artificial Intell | 2025-11 | abstract | direct |
| SD210 | [Nikoukhah & Campbell 2003](https://doi.org/10.23919/ecc.2003.7085087): Auxiliary signal design for failure detection in uncertain sampled-data systems | 2003 European Control Conference (ECC) | 2003-09 | abstract | direct |
| SD211 | [Wang et al. 2023](https://doi.org/10.1002/rnc.6660): An integrated design method for active fault diagnosis and control | International Journal of Robust and Nonlinear | 2023-03-20 | abstract | strong_component |
| SD213 | [Tzortzis & Polycarpou 2021](https://arxiv.org/abs/2108.05091): Active Fault Diagnosis for a Class of Nonlinear Uncertain Systems: A Distributionally Robust Approac… | arXiv preprint | 2021-08-11 | metadata_only | strong_component |
| SD212 | [Wang et al. 2019](https://doi.org/10.1007/s12555-019-0182-6): On-line Auxiliary Input Signal Design for Active Fault Detection and Isolation Based on Set-membersh… | International Journal of Control, Automation  | 2019-07-26 | abstract | strong_component |
| SD215 | [Ramadoss & Muthiah 2023](https://doi.org/10.1007/s00202-023-01784-9): Machine learning approach to differentiate excitation failure in synchronous generators from power s… | Electrical Engineering | 2023-03-19 | abstract | adjacent |
| SD216 | [Rish et al. 2004](https://doi.org/10.1109/noms.2004.1317650): Real-time problem determination in distributed systems using active probing | 2004 IEEE/IFIP Network Operations and Managem | 2004 | abstract | adjacent |

### N4: Query-budgeted regime authorisation (7 records)

| ID | Work | Venue | Date | Evidence | Threat |
|---|---|---|---|---|---|
| SD218 | [Perini et al. 2023](https://arxiv.org/abs/2301.02909): How to Allocate your Label Budget? Choosing between Active Learning and Learning to Reject in Anomal… | arXiv preprint | 2023-01-07 | abstract | direct |
| SD217 | [Castellani et al. 2022](https://arxiv.org/abs/2204.06822): Stream-based Active Learning with Verification Latency in Non-stationary Environments | arXiv preprint / journal extension | 2022-04-14 | abstract | direct |
| SD222 | [Deep AD under labeling budget constraints (ICML 2023)](https://proceedings.mlr.press/v202/li23x/li23x.pdf): Deep Anomaly Detection under Labeling Budget Constraints | ICML 2023 (PMLR vol. 202) | 2023-07 | abstract | strong_component |
| SD220 | [Bodor et al. 2022](https://arxiv.org/abs/2201.10323): Little Help Makes a Big Difference: Leveraging Active Learning to Improve Unsupervised Time Series A… | arXiv preprint | 2022-01-25 | abstract | strong_component |
| SD221 | [Guo et al. 2022](https://arxiv.org/abs/2212.14621): Label-Efficient Interactive Time-Series Anomaly Detection | arXiv preprint | 2022-12-30 | metadata_only | strong_component |
| SD219 | [Das et al. 2018](https://arxiv.org/abs/1809.06477): Active Anomaly Detection via Ensembles | arXiv preprint | 2018-09-17 | abstract | strong_component |
| SD326 | [Zhong et al. 2026](https://doi.org/10.1016/j.patcog.2026.113899): Stable region enhanced online learning method for intermediate verification latency and concept drif… | Pattern Recognition | 2026-04-30 | metadata_only | adjacent · future issue 2026-11 |

### N5: Retroactive decontamination (6 records)

| ID | Work | Venue | Date | Evidence | Threat |
|---|---|---|---|---|---|
| SD223 | [Du et al. 2019](https://doi.org/10.1145/3319535.3363226): Lifelong Anomaly Detection Through Unlearning | Proceedings of the 2019 ACM SIGSAC Conference | 2019-11-06 | abstract | direct |
| SD225 | [Machine unlearning for streaming forgetting (OpenReview 2024)](https://openreview.net/forum?id=bIoWuzFm6r): Machine Unlearning for Streaming Forgetting | OpenReview preprint | 2024-10 | abstract | strong_component |
| SD224 | [Artelt et al. 2022](https://arxiv.org/abs/2211.12989): Unsupervised Unlearning of Concept Drift with Autoencoders | arXiv preprint | 2022-11-23 | abstract | strong_component |
| SD227 | [Santana & Cordeiro 2026](https://arxiv.org/abs/2608.30046): Forget or Fine-tune? A Comparative Study of Machine Unlearning Strategies for Noisy Label Correction | arXiv preprint | 2026-08-30 | metadata_only | adjacent |
| SD202 | [Abbasi et al. 2023](https://arxiv.org/abs/2311.11995): BrainWash: A Poisoning Attack to Forget in Continual Learning | arXiv preprint | 2023-11-20 | metadata_only | adjacent |
| SD226 | [Kaplan et al. 2026](https://arxiv.org/abs/2609.05329): Machine Unlearning as Private Retroactive Algorithms | arXiv preprint | 2026-09-04 | metadata_only | background |

### N6: Adaptation-induced masking (5 records)

| ID | Work | Venue | Date | Evidence | Threat |
|---|---|---|---|---|---|
| SD228 | [Anzai & Pinto 2026](https://doi.org/10.3390/pr14050859): Distinguishing Process Faults from Model Drift Through Variable Contribution Analysis: A Novel Persp… | Processes | 2026-03-07 | abstract | direct |
| SD230 | [Dahmardeh & Setti 2025](https://arxiv.org/abs/2512.15323): MECAD: A multi-expert architecture for continual anomaly detection | arXiv preprint | 2025-12-17 | metadata_only | strong_component |
| SD229 | [Li et al. 2022](https://doi.org/10.1145/3503161.3548232): Towards Continual Adaptation in Industrial Anomaly Detection | Proceedings of the 30th ACM International Con | 2022-10-10 | abstract | strong_component |
| SD231 | [Frikha et al. 2020](https://arxiv.org/abs/2008.04042): ARCADe: A Rapid Continual Anomaly Detector | arXiv preprint / ICPR 2020 | 2020-08-10 | abstract | strong_component |
| SD232 | [Pezze et al. 2022](https://arxiv.org/abs/2212.11192): Continual Learning Approaches for Anomaly Detection | arXiv preprint (journal version: Evolving Sys | 2022-12-21 | abstract | background |

### N7: Contamination-blind evaluation (28 records)

| ID | Work | Venue | Date | Evidence | Threat |
|---|---|---|---|---|---|
| SD302 | [Han & Qu 2026](https://arxiv.org/abs/2608.30502): When the Martingale Never Stops Firing: Anytime-Valid Gating ... (real forecast streams) | arXiv | 2026-08-31 | as recorded in prior audit | direct |
| SD242 | [Patra & Ben Taieb 2025](https://arxiv.org/abs/2510.21296): An Evidence-Based Post-Hoc Adjustment Framework for Anomaly Detection Under Data Contamination | NeurIPS 2025 | 2025-10-24 | abstract | direct |
| SD160 | [Cao et al. 2024](https://doi.org/10.1007/s10462-024-10995-w): Revisiting streaming anomaly detection: benchmark and evaluation | Artificial Intelligence Review | 2024-11-07 | abstract | direct |
| SD241 | [Contamination-factor distribution estimation (ICML 2023)](https://icml.cc/virtual/2023/poster/24694): Estimating the Contamination Factor's Distribution in Unsupervised Anomaly Detection | ICML 2023 (PMLR vol. 202) | 2023-07 | abstract | direct |
| SD013 | [Podkopaev & Ramdas 2021](https://arxiv.org/abs/2110.06177): Tracking the risk of a deployed model and detecting harmful distribution shifts | arXiv / ICML 2022 | 2021-10-12 | abstract | direct |
| SD233 | [Ceschin et al. 2020](https://arxiv.org/abs/2010.16045): Machine Learning (In) Security: A Stream of Problems | arXiv preprint (journal version: ACM Digital  | 2020-10-30 | abstract | direct |
| SD235 | [Alencar et al. 2026](https://doi.org/10.1016/j.dsp.2026.106325): Concept drift detection in delayed and partially labeled data streams: An experimental survey | Digital Signal Processing | 2026-10 | abstract | strong_component |
| SD244 | [Singh 2026](https://arxiv.org/abs/2607.17336): When Drift Detectors cry Wolf: False Alarm Rates in continuous ML Monitoring | arXiv preprint | 2026-07-19 | metadata_only | strong_component |
| SD319 | [Yang 2026](https://doi.org/10.1016/j.asoc.2026.116360): Representation stability is not detectability: A leakage-free evaluation of frozen time series found… | Applied Soft Computing | 2026-09-07 | metadata_only | strong_component · future issue 2027-01 |
| SD338 | [Velasco & Zafra 2026](https://doi.org/10.1016/j.neucom.2026.134154): TSADmetrics: A library for evaluating time series anomaly detection methods | Neurocomputing | 2026-06-05 | abstract | strong_component · future issue 2026-10 |
| SD340 | [One-liners paper (ICLR 2026)](https://openreview.net/forum?id=H27kvyG4qf): When Foundation Models are One-Liners: Limitations and Future Directions for Time Series Anomaly Det… | ICLR 2026 (OpenReview) | 2026 | abstract | strong_component |
| SD016 | [Prinster et al. 2025](https://arxiv.org/abs/2505.04608): WATCH: Adaptive Monitoring for AI Deployments via Weighted-Conformal Martingales | arXiv | 2025-05-07 | abstract | strong_component |
| SD316 | [Wagner et al. 2025](https://arxiv.org/abs/2510.17562): Formally Exploring Time-Series Anomaly Detection Evaluation Metrics | arXiv | 2025-10-20 | abstract | strong_component |
| SD236 | [Gower-Winter et al. 2024](https://arxiv.org/abs/2412.10545): Identifying Predictions That Influence the Future: Detecting Performative Concept Drift in Data Stre… | AAAI 2025 (arXiv preprint 2024) | 2024-12-13 | abstract | strong_component |
| SD243 | [Masakuna et al. 2024](https://arxiv.org/abs/2408.07718): Impact of Inaccurate Contamination Ratio on Robust Unsupervised Anomaly Detection | arXiv preprint | 2024-08-14 | metadata_only | strong_component |
| SD239 | [Ginsberg et al. 2022](https://arxiv.org/abs/2212.02742): A Learning Based Hypothesis Test for Harmful Covariate Shift | arXiv preprint / ICLR 2023 | 2022-12-06 | abstract | strong_component |
| SD312 | [Kim et al. 2022](https://doi.org/10.1609/aaai.v36i7.20680): Towards a Rigorous Evaluation of Time-Series Anomaly Detection | AAAI | 2022-06-28 | abstract | strong_component |
| SD234 | [Grzenda et al. 2019](https://doi.org/10.1007/s10618-019-00654-y): Delayed labelling evaluation for data streams | Data Mining and Knowledge Discovery | 2019-11-16 | abstract | strong_component |
| SD317 | [Li et al. 2026d](https://arxiv.org/abs/2603.06131): DQE: A Semantic-Aware Evaluation Metric for Time Series Anomaly Detection | arXiv | 2026-03-06 | abstract | adjacent |
| SD323 | [Zuo et al. 2026](https://doi.org/10.1016/j.neunet.2026.109567): ContaminationAD: Anomaly detection with contaminated data | Neural Networks | 2026-08-30 | abstract | adjacent · future issue 2027-01 |
| SD326 | [Zhong et al. 2026](https://doi.org/10.1016/j.patcog.2026.113899): Stable region enhanced online learning method for intermediate verification latency and concept drif… | Pattern Recognition | 2026-04-30 | metadata_only | adjacent · future issue 2026-11 |
| SD334 | [Tan et al. 2026](https://doi.org/10.1016/j.patcog.2026.113843): RoCA: Robust Contrastive Adaptation for unsupervised anomaly detection | Pattern Recognition | 2026-04-29 | metadata_only | adjacent · future issue 2026-11 |
| SD335 | [Takahashi et al. 2026](https://doi.org/10.1016/j.neucom.2026.135134): Deep positive-unlabeled anomaly detection for contaminated unlabeled data | Neurocomputing | 2026-09-16 | abstract | adjacent · future issue 2027-01 |
| SD339 | [Yang et al. 2026b](https://doi.org/10.1016/j.neucom.2026.134547): A problem-oriented taxonomy of evaluation metrics for time series anomaly detection | Neurocomputing | 2026-07-20 | metadata_only | adjacent · future issue 2026-11 |
| SD318 | [Yang et al. 2025](https://arxiv.org/abs/2511.18739): A Problem-Oriented Taxonomy of Evaluation Metrics for Time Series Anomaly Detection | arXiv; Neurocomputing (issue 2026-11) | 2025-11-24 | abstract | adjacent · future issue 2026-11 |
| SD237 | [Lee & Zrnic 2026](https://arxiv.org/abs/2606.07890): Partially Performative Prediction | arXiv preprint | 2026-06-05 | metadata_only | background |
| SD240 | [Vovk et al. 2021](https://arxiv.org/abs/2102.10439): Retrain or not retrain: Conformal test martingales for change-point detection | PMLR (Symposium on Conformal and Probabilisti | 2021-02-20 | abstract | background |
| SD238 | [Perdomo et al. 2020](https://arxiv.org/abs/2002.06673): Performative Prediction | ICML 2020 | 2020-02-16 | abstract | background |

Records without a story tag: 0.
