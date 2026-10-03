# Closest prior art

For each story this file lists the closest primary sources and what each one already occupies. The evidence level is the deepest level at which the record was read, taken from [papers.json](papers.json) (`full_text`, `abstract` or `metadata_only`). Several decisive threats were read only at abstract level, and those limits carry into the status decisions in [story_cards.md](story_cards.md).

## A: Reversible normality lifecycle

Every lifecycle state has a precedent. The one distinction left in TSAD is that the rollback trigger must be delayed external evidence, not an online validation oracle.

| Work | Venue / date | Evidence | What it occupies |
|---|---|---|---|
| [Park et al. 2025](https://doi.org/10.1145/3746252.3761481): Adaptive Anomaly Detection in the Presence of Concept Drift (AnDri) | CIKM demo / arXiv (2025-06-18) | as recorded in prior audit | candidate normal patterns, active/inactive status, admission criteria, reactivation |
| [Li et al. 2024a](https://doi.org/10.1016/j.datak.2024.102365): State-transition-aware anomaly detection under concept drifts | Data &amp; Knowledge Engineering (2024-11) | abstract | maps stream periods to states; adapts through state transitions |
| [Zhu et al. 2024](https://doi.org/10.14778/3636218.3636233): METER: A Dynamic Concept Adaptation Framework for Online Anomaly Detection | PVLDB (2024-03-05) | as recorded in prior audit | evidential unknown state; deferred window update |
| [Le et al. 2026](https://doi.org/10.1145/3744255.3811742): Drift-Aware Online Anomaly Detection in Smart Buildings via Temporal Variational Autoencod… | ACM e-Energy (2026-06-22) | as recorded in prior audit | buffered selective update; separates normal drift from attack; reports contamination rate |
| [Qin et al. 2026](https://arxiv.org/abs/2604.08059): Governed Capability Evolution: Lifecycle-Time Compatibility Checking and Rollback for AI-C… | arXiv preprint (2026-04-09) | full_text | candidate → sandbox → shadow → gated activation → monitor → rollback → audit (non-TSAD) |
| [Aftab et al. 2026](https://arxiv.org/abs/2607.02687): RES-DARE: Failure-Aware Expert Adaptation and Rollback-Safe Self-Repair for Intrusion Dete… | arXiv preprint (2026-07-02) | abstract | provisional activation committed only if macro-F1 preserved, else rollback (supervised IDS) |
| [Su et al. 2026](https://arxiv.org/abs/2607.27773): ChronoMem: Version Control and Semantic Rollback for Large Language Model Agent Memory | arXiv preprint (2026-07-30) | abstract | versioned memory with semantic rollback and post-exposure counterfactual evaluation (LLM agents) |

## B: Risk-constrained adaptation

Certified sequential risk control exists and has been attached to adapting models. What is missing in TSAD is a quantity that can be certified without labels, together with the impossibility result that rules out false-promotion guarantees on the equivalent stratum.

| Work | Venue / date | Evidence | What it occupies |
|---|---|---|---|
| [Schirmer et al. 2025](https://doi.org/10.52202/085713-2705): Monitoring Risks in Test-Time Adaptation | Advances in Neural Information Processin (2025) | full_text | risk monitoring of TTA models with confidence sequences, no test labels |
| [Amoukou et al. 2024](https://doi.org/10.52202/079017-4107): Sequential Harmful Shift Detection Without Labels | Advances in Neural Information Processin (2024) | abstract | label-free sequential harmful-shift detection via an error proxy |
| [Prinster et al. 2025](https://arxiv.org/abs/2505.04608): WATCH: Adaptive Monitoring for AI Deployments via Weighted-Conformal Martingales | arXiv (2025-05-07) | abstract | weighted conformal test martingales; adapt to mild shift, flag harmful shift |
| [Angelopoulos et al. 2022](https://arxiv.org/abs/2208.02814): Conformal Risk Control | arXiv / ICLR 2024 (2022-08-04) | abstract | conformal risk control for monotone losses |
| [Wang et al. 2026a](https://arxiv.org/abs/2609.20700): Should This Case Be Adapted? Prediction Fragmentation Controls Test-Time Adaptation | arXiv (2026-09-17) | abstract | per-case adapt/skip router minimising harmful accepted area |
| [Han & Qu 2026](https://arxiv.org/abs/2608.30502): When the Martingale Never Stops Firing: Anytime-Valid Gating ... (real forecast streams) | arXiv (2026-08-31) | as recorded in prior audit | anytime-valid gating of online updates fires on 135/135 clean real streams |
| [Kloft & Laskov 2012](https://arxiv.org/abs/1003.0078): Security Analysis of Online Centroid Anomaly Detection | Journal of Machine Learning Research (JM (2010-02-27) | abstract | bounded-contamination analysis of online centroid AD |

## C: ADAPT / FREEZE / UNRESOLVED

The binary skip-or-adapt question is published three times within six weeks of the cutoff, and the reject option is classical. UNRESOLVED is meaningful only relative to a declared hypothesis library.

| Work | Venue / date | Evidence | What it occupies |
|---|---|---|---|
| [Jiang et al. 2026](https://arxiv.org/abs/2609.08367): To Adapt or Not to Adapt? Selective Adaptation for Vision-Language Models | arXiv (2026-09-08) | full_text | introduces selective adaptation: decide per sample whether to adapt or skip |
| [Majumdar & Saha 2026](https://arxiv.org/abs/2608.22233): When Test-Time Adaptation Helps, Harms, or Becomes Inactive: A Condition-Level Study on CI… | arXiv (2026-08-23) | abstract | condition-level taxonomy: TTA helps, harms or is inactive |
| [Wang et al. 2026a](https://arxiv.org/abs/2609.20700): Should This Case Be Adapted? Prediction Fragmentation Controls Test-Time Adaptation | arXiv (2026-09-17) | abstract | case-level adapt/skip under a harm measure |
| [Solozobov 2026](https://arxiv.org/abs/2604.15740): Evidence Sufficiency Under Delayed Ground Truth: Proxy Monitoring for Risk Decision System… | arXiv (2026-04-17) | abstract | evidence-sufficiency and decision-readiness gate under delayed labels |
| [Zhu et al. 2024](https://doi.org/10.14778/3636218.3636233): METER: A Dynamic Concept Adaptation Framework for Online Anomaly Detection | PVLDB (2024-03-05) | as recorded in prior audit | explicit unknown state in online AD |
| [Sobel & Wald 1949](https://doi.org/10.1214/aoms/1177729944): A Sequential Decision Procedure for Choosing One of Three Hypotheses Concerning the Unknow… | Annals of Mathematical Statistics (1949) | abstract | three-decision sequential test |
| [Yang 2026](https://doi.org/10.1016/j.asoc.2026.116360): Representation stability is not detectability: A leakage-free evaluation of frozen time se… | Applied Soft Computing (2026-09-07) | metadata_only | future-issue lead: representation stability is not detectability (title level) |

## D: Context-authorized normality

Context conditions scores (contextual AD), selects reference models (multimode monitoring) or serves as ground truth (control invariants). Scoped promotion with coincident faults is not evaluated anywhere located.

| Work | Venue / date | Evidence | What it occupies |
|---|---|---|---|
| [Song et al. 2007](https://doi.org/10.1109/tkde.2007.1009): Conditional Anomaly Detection | IEEE Transactions on Knowledge and Data  (2007-05) | abstract | conditional AD: expected behaviour conditioned on context attributes |
| [Lane et al. 2001](https://doi.org/10.1016/s0959-1524%2899%2900063-3): Performance monitoring of a multi-product semi-batch process | Journal of Process Control (2001-02) | abstract | recipe/product-specific reference models in multi-product process monitoring |
| [Choi et al. 2018](https://doi.org/10.1145/3243734.3243752): Detecting Attacks Against Robotic Vehicles | Proceedings of the 2018 ACM SIGSAC Confe (2018-10-15) | abstract | control invariants between commanded inputs and physical state |
| [Gao et al. 2021](https://doi.org/10.1145/3450267.3450533): An anomaly detection framework for digital twin driven cyber-physical systems | Proceedings of the ACM/IEEE 12th Interna (2021-05-19) | abstract | digital-twin residual monitoring under the same commanded inputs |
| [Lotto et al. 2026](https://arxiv.org/abs/2609.28170): Safety-Aware Zero Trust Enforcement for IoT and Cyber-Physical Systems | arXiv (2026-09-23) | abstract | separates telemetry visibility, estimator influence and state-changing authority |
| [Bosch environment/system anomaly patent (US 11,686,651)](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11686651): Method and device for detecting anomalies in technical systems (environment + conditional … | US Patent 11,686,651 / 11,536,630 / 11,8 (2022) | abstract | context-plausibility model gating a context-conditioned system model |
| [Le et al. 2026](https://doi.org/10.1145/3744255.3811742): Drift-Aware Online Anomaly Detection in Smart Buildings via Temporal Variational Autoencod… | ACM e-Energy (2026-06-22) | as recorded in prior audit | setpoint/occupancy drift separated from attacks with labeled anchors |

## E: Recurrence without forgetting

Occupied at the mechanism level, including in unsupervised streaming TSAD. Only pool contamination remains, and it is an evaluation axis.

| Work | Venue / date | Evidence | What it occupies |
|---|---|---|---|
| [Li et al. 2026b](https://doi.org/10.1016/j.knosys.2026.116530): Adaptive drift aware continual learning with pool-based model reuse for time series applic… | Knowledge-Based Systems (2026-09) | abstract | drift-type classification incl. recurrent; bounded pool; targets recurring-regime overwriting |
| [Yoon et al. 2022](https://doi.org/10.1145/3534678.3539348): Adaptive Model Pooling for Online Deep Anomaly Detection from a Complex Evolving Data Stre… | KDD (2022-08-14) | as recorded in prior audit | reliability-weighted autoencoder pool with train/merge |
| [Liu et al. 2025b](https://doi.org/10.1109/smartiot66867.2025.00068): Global-Local Normalization based Model Pool for Online Anomaly Detection in IIoT | 2025 IEEE International Conference on Sm (2025-11-17) | abstract | global-local normalisation with adaptive model pool (IIoT) |
| [Smendowski et al. 2026](https://doi.org/10.1007/s10723-026-09846-5): Bridging Continual Learning and Green Cloud Computing: Foundations for Sustainable Time Se… | Journal of Grid Computing (2026-09-01) | full_text | novelty-gated replay admission, retention-aware replacement, backward transfer |
| [Faber et al. 2026](https://arxiv.org/abs/2607.18289): Towards Principled Continual Anomaly Detection: A Systematic Framework and Benchmark Scena… | arXiv preprint (2026-06-30) | abstract | continual-AD scenario taxonomy incl. recurring regimes |
| [Museba et al. 2021](https://doi.org/10.1155/2021/5533777): Recurrent Adaptive Classifier Ensemble for Handling Recurring Concept Drifts | Applied Computational Intelligence and S (2021-06-10) | abstract | recurring-concept ensemble archive |

## F: Normal-only commissioning

Few-shot one-class adaptation, fleet transfer with sample-efficiency curves and zero-shot detectors all exist. Only a standard protocol and a certified stopping rule remain.

| Work | Venue / date | Evidence | What it occupies |
|---|---|---|---|
| [Holly et al. 2025](https://arxiv.org/abs/2501.13052): One-Class Domain Adaptation via Meta-Learning | arXiv preprint (2025-01-22) | abstract | one-class domain adaptation via meta-learning using normal operational data |
| [Frikha et al. 2021](https://arxiv.org/abs/2007.04146): Few-Shot One-Class Classification via Meta-Learning | AAAI 2021 (2020-07-08) | abstract | few-shot one-class meta-learning |
| [Jonas & Meyer 2025](https://arxiv.org/abs/2504.17709): Fault Detection in New Wind Turbines with Limited Data by Generative Transfer Learning | arXiv preprint (2025-04-24) | abstract | generative transfer for new wind turbines with 1–8 weeks of data |
| [Roelofs et al. 2024](https://arxiv.org/abs/2404.03011): Transfer learning applications for anomaly detection in wind turbines | Data-Centric Engineering (Cambridge) / a (2024-04-03) | abstract | fine-tuning threshold/decoder/full NBM with shrinking target data |
| [Shentu et al. 2025](https://arxiv.org/abs/2405.15273): Towards a General Time Series Anomaly Detector with Adaptive Bottlenecks and Dual Adversar… | ICLR 2025 (2024-05-24) | abstract | general zero-shot TSAD detector |
| [One-liners paper (ICLR 2026)](https://openreview.net/forum?id=H27kvyG4qf): When Foundation Models are One-Liners: Limitations and Future Directions for Time Series A… | ICLR 2026 (OpenReview) (2026) | abstract | foundation models do not beat one-liner baselines |

## G: Semantic-shift benchmark

Generators with drift and anomalies, recovery intervals and label-quality critiques exist. Decision-level labels, equivalent-by-construction strata and a context factor do not.

| Work | Venue / date | Evidence | What it occupies |
|---|---|---|---|
| [Cao et al. 2024](https://doi.org/10.1007/s10462-024-10995-w): Revisiting streaming anomaly detection: benchmark and evaluation | Artificial Intelligence Review (2024-11-07) | abstract | SCAR generator: customisable anomalies and concept drifts, 76 datasets |
| [Li et al. 2024a](https://doi.org/10.1016/j.datak.2024.102365): State-transition-aware anomaly detection under concept drifts | Data &amp; Knowledge Engineering (2024-11) | abstract | synthetic streams with separately labeled drift and anomaly positions |
| [Jacob et al. 2020](https://arxiv.org/abs/2010.05073): Exathlon: A Benchmark for Explainable Anomaly Detection over Time Series | Proceedings of the VLDB Endowment (arXiv (2020-10-10) | abstract | root-cause and extended-effect (recovery) intervals |
| [Liu & Paparrizos 2024b](https://doi.org/10.52202/079017-3437): The Elephant in the Room: Towards A Reliable Time-Series Anomaly Detection Benchmark | Advances in Neural Information Processin (2024) | abstract | TSB-AD curated benchmark |
| [Faber et al. 2026](https://arxiv.org/abs/2607.18289): Towards Principled Continual Anomaly Detection: A Systematic Framework and Benchmark Scena… | arXiv preprint (2026-06-30) | abstract | continual-AD scenarios |
| [Michailoudis et al. 2026](https://doi.org/10.1016/j.softx.2026.102995): SDG: A domain-specific language for the automated synthesis of stream data generators with… | SoftwareX (2026-09) | abstract | DSL for multi-drift stream generators |

## H: Resource-constrained continual TSAD

Three of the four axes are measured jointly for TSAD, and update frequency is covered by retraining-schedule work.

| Work | Venue / date | Evidence | What it occupies |
|---|---|---|---|
| [Smendowski et al. 2026](https://doi.org/10.1007/s10723-026-09846-5): Bridging Continual Learning and Green Cloud Computing: Foundations for Sustainable Time Se… | Journal of Grid Computing (2026-09-01) | full_text | joint detection quality, retention and energy protocol for concept-incremental TSAD |
| [Piaseczny et al. 2025](https://arxiv.org/abs/2505.24149): RCCDA: Adaptive Model Updates in the Presence of Concept Drift under a Constrained Resourc… | NeurIPS 2025 (2025-05-30) | abstract | drift-triggered updates under resource budget with guarantees |
| [Mahadevan & Mathioudakis 2024](https://doi.org/10.1016/j.knosys.2024.111610): Cost-aware retraining for machine learning | Knowledge-Based Systems (2024-06) | abstract | cost-aware retraining schedules |
| [Dasari 2026](https://arxiv.org/abs/2608.19488): When to Retrain: An Empirical Study of Retraining Policies for Streaming ML Under Concept … | arXiv (2026-08-19) | abstract | retraining policies under drift, budget and latency |

## N1: Promotion rules as an attack surface

Poisoning of online normality is mature. Attack cost against staged promotion specifications is not measured.

| Work | Venue / date | Evidence | What it occupies |
|---|---|---|---|
| [Kloft & Laskov 2012](https://arxiv.org/abs/1003.0078): Security Analysis of Online Centroid Anomaly Detection | Journal of Machine Learning Research (JM (2010-02-27) | abstract | security analysis of online centroid AD |
| [Rubinstein et al. 2009a](https://doi.org/10.1145/1644893.1644895): ANTIDOTE | Proceedings of the 9th ACM SIGCOMM confe (2009-11-04) | abstract | poisoning and robust defence for PCA detectors |
| [Kravchik & Shabtai 2020](https://arxiv.org/abs/2002.02741): Can't Boil This Frog: Robustness of Online-Trained Autoencoder-Based Anomaly Detectors to … | arXiv preprint (2020-02-07) | abstract | poisoning online-trained ICS autoencoders; SWaT model resilient |
| [Korycki Ł. & Krawczyk 2022](https://doi.org/10.1007/s10994-022-06177-w): Adversarial concept drift detection under poisoning attacks for robust data stream mining | Machine Learning (2022-06-02) | abstract | poisoning drift detectors |
| [Cong et al. 2024](https://arxiv.org/abs/2308.08505): Test-Time Poisoning Attacks Against Test-Time Adaptation Models | IEEE Symposium on Security and Privacy ( (2023-08-16) | abstract | test-time poisoning of TTA models |

## N2: Peer-corroborated normality

Fleet pooling exists, but no identifiability statement or adversarial-fraction bound for peer-licensed promotion has been published.

| Work | Venue / date | Evidence | What it occupies |
|---|---|---|---|
| [Stavrou et al. 2009](https://doi.org/10.1145/1654988.1655000): Keep your friends close | Proceedings of the 2nd ACM workshop on S (2009-11-09) | abstract | cross-site collaboration to update anomaly sensors |
| [Tveten et al. 2022](https://doi.org/10.1214/21-aoas1508): Scalable change-point and anomaly detection in cross-correlated data with an application t… | The Annals of Applied Statistics (2022-06-01) | abstract | change-point/anomaly detection in cross-correlated populations |
| [de Novaes Pires Leite et al. 2023](https://doi.org/10.1016/j.engappai.2023.106859): A robust fleet-based anomaly detection framework applied to wind turbine vibration data | Engineering Applications of Artificial I (2023-11) | abstract | fleet-based wind-turbine vibration AD |
| [Smith et al. 2024](https://arxiv.org/abs/2402.19295): Anomaly Detection in Offshore Wind Turbine Structures using Hierarchical Bayesian Modellin… | arXiv preprint (2024-02-29) | metadata_only | hierarchical Bayesian population modelling for turbines |

## N3: Interventional disambiguation

Auxiliary signal design is classical; TSAD applies it only offline.

| Work | Venue / date | Evidence | What it occupies |
|---|---|---|---|
| [Nikoukhah & Campbell 2003](https://doi.org/10.23919/ecc.2003.7085087): Auxiliary signal design for failure detection in uncertain sampled-data systems | 2003 European Control Conference (ECC) (2003-09) | abstract | auxiliary signal design for failure detection |
| [Wang et al. 2019](https://doi.org/10.1007/s12555-019-0182-6): On-line Auxiliary Input Signal Design for Active Fault Detection and Isolation Based on Se… | International Journal of Control, Automa (2019-07-26) | abstract | online auxiliary input design, set-membership |
| [Wang et al. 2023](https://doi.org/10.1002/rnc.6660): An integrated design method for active fault diagnosis and control | International Journal of Robust and Nonl (2023-03-20) | abstract | joint AFD and control design |
| [Wang et al. 2025b](https://doi.org/10.1016/j.engappai.2025.111991): Boosting industrial anomaly detection performance using generated artificial fault data | Engineering Applications of Artificial I (2025-11) | abstract | artificial fault data for industrial AD (passive vs active AD) |

## N4: Query-budgeted regime authorisation

Instance-level budgeted feedback and verification latency exist. Regime-level queries do not.

| Work | Venue / date | Evidence | What it occupies |
|---|---|---|---|
| [Das et al. 2018](https://arxiv.org/abs/1809.06477): Active Anomaly Detection via Ensembles | arXiv preprint (2018-09-17) | abstract | active anomaly discovery with ensembles |
| [Perini et al. 2023](https://arxiv.org/abs/2301.02909): How to Allocate your Label Budget? Choosing between Active Learning and Learning to Reject… | arXiv preprint (2023-01-07) | abstract | active learning vs learning-to-reject under a label budget |
| [Castellani et al. 2022](https://arxiv.org/abs/2204.06822): Stream-based Active Learning with Verification Latency in Non-stationary Environments | arXiv preprint / journal extension (2022-04-14) | abstract | stream active learning with verification latency and drift-dependent budget |
| [Deng et al. 2024](https://arxiv.org/abs/2405.03234): A Reliable Framework for Human-in-the-Loop Anomaly Detection in Time Series | arXiv (2024-05-06) | abstract | human-in-the-loop AD |

## N5: Retroactive decontamination

Du et al. already correct wrongly-normal samples. Only the regime-level, continuous-state version measured against rollback remains.

| Work | Venue / date | Evidence | What it occupies |
|---|---|---|---|
| [Du et al. 2019](https://doi.org/10.1145/3319535.3363226): Lifelong Anomaly Detection Through Unlearning | Proceedings of the 2019 ACM SIGSAC Confe (2019-11-06) | abstract | unlearning corrects false negatives or false positives in lifelong deep AD |
| [Artelt et al. 2022](https://arxiv.org/abs/2211.12989): Unsupervised Unlearning of Concept Drift with Autoencoders | arXiv preprint (2022-11-23) | abstract | map drifted data back to pre-drift manifold |
| [Machine unlearning for streaming forgetting (OpenReview 2024)](https://openreview.net/forum?id=bIoWuzFm6r): Machine Unlearning for Streaming Forgetting | OpenReview preprint (2024-10) | abstract | streaming unlearning requests |
| [Su et al. 2026](https://arxiv.org/abs/2607.27773): ChronoMem: Version Control and Semantic Rollback for Large Language Model Agent Memory | arXiv preprint (2026-07-30) | abstract | post-exposure counterfactual rollback evaluation |

## N6: Adaptation-induced masking

Generic forgetting metrics and per-event fault-versus-drift diagnosis exist. A paired masking protocol does not.

| Work | Venue / date | Evidence | What it occupies |
|---|---|---|---|
| [Anzai & Pinto 2026](https://doi.org/10.3390/pr14050859): Distinguishing Process Faults from Model Drift Through Variable Contribution Analysis: A N… | Processes (2026-03-07) | abstract | counterfactual contribution analysis separates process faults from mode-shift model drift |
| [Li et al. 2022](https://doi.org/10.1145/3503161.3548232): Towards Continual Adaptation in Industrial Anomaly Detection | Proceedings of the 30th ACM Internationa (2022-10-10) | abstract | continual industrial AD with forgetting metrics |
| [Frikha et al. 2020](https://arxiv.org/abs/2008.04042): ARCADe: A Rapid Continual Anomaly Detector | arXiv preprint / ICPR 2020 (2020-08-10) | abstract | rapid continual anomaly detector |

## N7: Contamination-blind evaluation

Metric critiques are active but have not analysed test-time adaptation. Delayed-label and performative critiques exist for classification streams.

| Work | Venue / date | Evidence | What it occupies |
|---|---|---|---|
| [Kim et al. 2022](https://doi.org/10.1609/aaai.v36i7.20680): Towards a Rigorous Evaluation of Time-Series Anomaly Detection | AAAI (2022-06-28) | abstract | point adjustment inflates random detectors; PA%K |
| [Wagner et al. 2025](https://arxiv.org/abs/2510.17562): Formally Exploring Time-Series Anomaly Detection Evaluation Metrics | arXiv (2025-10-20) | abstract | verifiable metric properties across 37 metrics |
| [Lyu 2026](https://arxiv.org/abs/2607.11969): Did We Actually Fix It? An Independent Adversarial Stress-Test of Post-Point-Adjustment Ev… | arXiv preprint (2026-07-12) | abstract | adversarial stress test of post-PA metrics |
| [Grzenda et al. 2019](https://doi.org/10.1007/s10618-019-00654-y): Delayed labelling evaluation for data streams | Data Mining and Knowledge Discovery (2019-11-16) | abstract | delayed-labelling evaluation for streams |
| [Ceschin et al. 2020](https://arxiv.org/abs/2010.16045): Machine Learning (In) Security: A Stream of Problems | arXiv preprint (journal version: ACM Dig (2020-10-30) | abstract | instant-label assumptions overstate streaming security ML |
| [Patra & Ben Taieb 2025](https://arxiv.org/abs/2510.21296): An Evidence-Based Post-Hoc Adjustment Framework for Anomaly Detection Under Data Contamina… | NeurIPS 2025 (2025-10-24) | abstract | test-time evidence-based correction of contaminated AD models |
