# P5 — Normal-only detector commissioning with a defensible READY rule

**Source issue:** [GitHub #9](https://github.com/kuo1234/xlstm_anomaly/issues/9)
**Assessment date:** 2026-09-27
**Status:** Literature and design only; no data were downloaded or opened.

## Feasibility assessment

**Algorithmic feasibility: high. Confirmatory-study feasibility: medium-low until normal-label provenance is resolved. Novelty: narrow and conditional.** The operational sequence is simple: start from a source detector, reveal target observations in order, and decide when it may be activated. But the public candidates found so far do not establish that a target prefix is independently verified as normal *at deployment time*. PreDist supplies report-based fault/maintenance labels and curated normal events; CARE supplies retrospective turbine-status/event labels, not a prospective sign-off record. Thus the study must either obtain genuinely verified commissioning prefixes or reframe its public-data arm as **reference-normal commissioning under possible label contamination**. Do not call the latter verified-normal commissioning.

The method claim is already crowded. Few-shot one-class learning, normal-only domain adaptation, cross-turbine transfer, target threshold recalibration, and zero-shot TSAD all exist. The defensible residual is a *deployment protocol and stopping rule*: compare fixed-N, simple stability rules, and, only if these fail, a learned rule on the same held-out-entity target-normal learning curves. A sample-efficiency curve alone is not a novelty claim. Any success claim also requires evaluator-only noninferiority in future fault detection at matched normal-risk performance; otherwise an always-normal detector could appear ready by never alarming.

There is a plausible two-family *candidate* path. PreDist documents 93 district-heating substations, report-based fault and maintenance labels, and predefined normal events. CARE to Compare describes 36 wind turbines across three farms and fault-event labels. However, the PreDist paper notes that some faults may be unreported, and CARE's labels are retrospective and differ by farm. Both therefore need a label-provenance audit before any prefix can be described as independently verified normal. PreDist is a single-utility dataset; CARE is made of event-centered sequences, and its anonymized cross-sequence dates must not be stitched into a fleet timeline. CARE v6 is the corrected release; v3 contains a duplicate-timestamp warning and earlier label issues. The exact entity/time coverage, prefix status available to an operator, license, and event grouping must be audited before any fitting. [PreDist dataset record](https://zenodo.org/records/19496480), [PreDist paper](https://doi.org/10.1016/j.energy.2026.141178), [CARE dataset paper](https://arxiv.org/abs/2404.10320), [CARE Zenodo v6](https://zenodo.org/records/15846963)

## Closest prior art and what remains open

| Work | Overlap with P5 | Consequence for novelty |
|---|---|---|
| Holly et al., *One-Class Domain Adaptation via Meta-Learning* (2025) | Learns rapid one-class adaptation across domains using normal target observations; includes industrial vibration data. | Rules out “few normal samples adapt a detector” as the contribution. [Paper](https://arxiv.org/abs/2501.13052) |
| Frikha et al., *Few-Shot One-Class Classification via Meta-Learning* (AAAI 2021) | Few-shot one-class adaptation; includes time-series tasks and an industrial manufacturing sensor use case. | Requires a direct baseline or clear distinction in deployment objective. [Paper](https://arxiv.org/abs/2007.04146) |
| Roelofs et al., *Transfer learning applications for anomaly detection in wind turbines* (2024) | Compares target-data scarcity, source transfer, decoder/model fine-tuning, and threshold-only transfer. | The transfer/sample-scarcity curve is substantially occupied. [Paper](https://doi.org/10.1016/j.egyai.2024.100373) |
| Jonas & Meyer, *Fault Detection in New Wind Turbines with Limited Data by Generative Transfer Learning* (Energy and AI, 2025) | Evaluates transfer across seven turbines and 1–8 weeks of target data. | A second direct warning against novelty claims based on target-normal sample efficiency alone. [Paper](https://doi.org/10.1016/j.egyai.2025.100626) |
| Jonas & Meyer, *Generative multi-domain transfer learning for fault detection in data-scarce wind turbines* (arXiv, 2026-08) | Adds an anomaly-free score proxy for selecting source mappings and stopping model training; its target data are limited normal SCADA observations. | Very close signal-level overlap. Distinguish **stopping optimization over a fixed target sample** from **stopping acquisition of more target-normal samples**; include the proxy as a baseline or ablation. [Paper](https://arxiv.org/abs/2608.30323) |
| Shentu et al., DADA (ICLR 2025) and Lan et al., TimeRCD (2025) | General/zero-shot TSAD can remove or reduce target commissioning data. | Frozen zero-shot detectors must be comparison arms. [DADA](https://arxiv.org/abs/2405.15273), [TimeRCD](https://arxiv.org/abs/2509.21190) |
| Zhu et al., *When Foundation Models are One-Liners* (ICLR 2026) | Finds moving-window variance and squared-difference baselines competitive with several time-series foundation-model anomaly detectors. | Include very cheap one-liners and avoid assuming the neural source detector is useful. [OpenReview paper](https://openreview.net/forum?id=H27kvyG4qf) |
| WindADBench (public benchmark repository; paper/venue not independently verified in this pass) | Offers cross-turbine and cross-farm tracks on CARE to Compare and broad detector coverage. | New lead since the Claude report's 2026-09-26 cutoff. Check its protocol before claiming that held-out-entity benchmarking is itself new. [Repository](https://github.com/ZJU-DAILY/WindADBench) |

The remaining claim should be narrow: **does a target-normal-only readiness rule reduce the number of observations or elapsed time needed to meet a predeclared deployment-risk/quality target, compared with fixed-N and simple stability rules, on unseen entities?** The certification part is the largest technical risk. A threshold that looks stable over a serially dependent prefix does not by itself certify future false-alarm risk. Any formal guarantee must name and justify the calibration assumptions at the unit actually used (for example, exchangeable non-overlapping blocks); absent defensible assumptions, results must be called empirical readiness rather than certified readiness.

## Proposed research question

Given a source-trained detector and a stream of **independently verified normal** observations from a held-out target entity, can a stopping policy declare `READY` using fewer target observations or less elapsed time than a fixed-N policy while controlling a prespecified upper bound on future normal false-alarm risk? After `READY`, does the frozen deployed detector retain anomaly-detection performance on a hidden future segment?

The controller may consume only the revealed normal prefix and detector outputs available by that time. Future labels, event boundaries, and post-prefix target samples are evaluator-only. `READY` means “meets the declared normal-risk condition”; it must not be presented as certification of anomaly recall, which cannot be inferred from normal-only calibration data.

## Proposed experimental architecture

### 0. Data and protocol gate

Before fitting any model, conduct a metadata-only audit and then seal a dataset manifest. Require two distinct entity families with independent target entities, timestamped verified-normal intervals, labeled future fault/anomaly intervals for evaluator-only scoring, and legal access for research. Audit acquisition time, sampling cadence, missingness, normal-prefix duration, fault-event IDs, entity aliases, and version history. Do not split sequences from one physical entity across source and target folds.

Candidate families are PreDist (district-heating substations) and CARE to Compare (wind turbines). For PreDist, stratify results by manufacturer/configuration and recognize that all entities come from one utility; audit whether each proposed target prefix was known to be normal from information available at the time, rather than merely later designated a normal event. For CARE, pin **Zenodo v6** (`10.5281/zenodo.15846963`), not the older v3 record; the dataset authors document corrected labels and timestamp issues in prior releases. Do not combine distinct anonymized event sequences into a single chronology. Use the shared semantic feature set for cross-farm comparisons if farm schemas differ. WindADBench is a comparison lead, but its recent benchmark protocol should be inspected before finalizing novelty claims.

If neither candidate can supply independently verified prefixes, the confirmatory claim must be narrowed to reference-normal data with a prespecified contaminated-prefix stress arm; report this limitation plainly. A third-party or operator-confirmed commissioning record is needed before calling the result a real deployment certificate.

If two eligible families cannot be sealed, downgrade the study to one-family feasibility only. SMD must not be the confirmatory substitute: the repository's prior label-provenance audit invalidated the claim that the other SMD machines were untouched. Any SMD analysis would need a separately justified exploratory status and zero access to protected labels in this research task.

### 1. Entity-disjoint commissioning episodes

For each family, hold out whole physical entities. Use remaining entities only to train source models and, where applicable, the readiness policy. Within each held-out target, reveal a chronological verified-normal prefix in fixed increments. Report both observation count and elapsed wall-clock duration; raw counts are not comparable across 1-minute, 10-minute, or irregularly sampled systems. Use non-overlapping blocks for stability summaries and freeze block construction from training metadata before target outcomes are evaluated.

Each episode has three non-overlapping roles, with every block assigned once and never reassigned from risk evaluation into fitting:

1. **Source fit:** train or choose the source detector using non-target entities only.
2. **Commissioning prefix:** reveal target-normal observations sequentially; permit only predeclared normal-only recalibration or adaptation. Reserve disjoint blocks for model fitting, threshold calibration, and a risk-audit stream. Count every sample in all three roles as commissioning cost.
3. **Hidden deployment segment:** use one common, sealed chronological suffix that starts after the maximum commissioning budget `N_max` for every arm on a target. At `N_READY`, freeze that model; do not give it observations after its own stopping time. Apply its frozen model to the same common suffix as all other arms. The policy receives no suffix labels or samples. Evaluator-only labels are used afterward to report false alarms, event detection, AP, and delay. Per-policy “immediately after READY” performance may be shown as secondary only, since those intervals start at different times.

Use a matched full-target-normal reference as an offline ceiling, trained on a separate normal interval from the same held-out entity. Do not train that reference on the hidden test interval. Fix `N_max` and the common suffix before outcomes are opened; report suffix duration and fault-event support per entity.

### 2. Detector and readiness comparisons

Use one pinned source detector as the primary backbone and at least one lightweight non-neural normal-behaviour/one-class comparator. Keep source training budget, target samples, score definition, and threshold semantics matched across arms.

Compare:

- frozen source detector / zero-shot detector (`N=0`);
- fixed-N target-only fit and fixed-N source-to-target adaptation;
- threshold-only target recalibration, separated from model-weight updates;
- normal-only fine-tuning or one-class adaptation, including OC-DA-MAML if a maintained implementation and comparable task setup are available;
- fixed-window-score and moving-variance / squared-difference one-liners;
- simple readiness rules: `N` fixed, score-quantile stability over `K` non-overlapping blocks, threshold stability, and a predeclared marginal-gain plateau;
- the published Jonas–Meyer anomaly-free proxy for model selection, if its released implementation supports the chosen target data; treat its optimization-step stopping as a separate baseline, not as a target-sample-acquisition policy;
- only if the simple policies leave a measurable gap, one learned stopping rule developed on source entities only. Split source entities into policy-fit and policy-validation groups, then hold out target entities and at least one entity family from both. The offline training target may use evaluator-only future outcomes on source development tasks to identify the earliest prefix that satisfies the predeclared joint condition; the deployed policy features remain limited to data available from the normal prefix. Evaluate held-out target outcomes once, after the policy is frozen; they cannot trigger another development or selection round;
- retrospective oracle stopping as an upper bound only, using hidden evaluator outcomes after all primary comparisons are frozen.

At each candidate `READY`, freeze the deployed detector. Do not let the readiness policy keep adapting after deployment in this first study; commissioning and continual online adaptation are different problems. If a public dataset's reference-normal prefix contains a fault according to evaluator-only labels, flag it in a separate contaminated-prefix stress arm; never expose that label to the policy.

### 3. Normal-risk rule and certification conditions

Pre-register a concrete risk estimand, such as the probability a normal block triggers at least one alarm over a fixed block duration, and an operational target `≤ α` with one-sided confidence `1−δ`. State the block duration and alarm aggregation rule. The stopping rule may declare `READY` only when its risk procedure passes and minimum coverage requirements are met. A separate fit set, calibration set, and audit set are required; repeated testing across candidate sample counts and model versions must use a predeclared simultaneous bound (for example, a valid alpha-spending procedure) or a sequentially valid risk process. Non-overlap alone does not establish independence or exchangeability.

Before using the word **certified**, prove that the chosen risk procedure covers reuse of data for model choice, threshold calibration, and repeated looks, and is valid under explicit normal-prefix/future-block assumptions. Standard exchangeable conformal ranks do not automatically remain valid under arbitrary serial dependence or nonstationarity. Non-overlapping blocks alone establish neither independence nor exchangeability. Otherwise report empirical risk estimates and confidence intervals, and use `READY_EMPIRICAL` by default.

This study can certify a declared normal false-alarm condition only. AP, fault recall, and early-warning performance are future evaluator measurements, not quantities observable to a normal-only commissioning rule.

### 4. Outcomes and analysis

Primary outcome: target-normal observations and elapsed time required to reach the same predeclared *joint* deployment condition. A rule only succeeds if it reaches the normal-risk target and, on evaluator-only common-suffix outcomes, is noninferior to the full-target-normal reference in predeclared anomaly-detection quality (for example, AP/event recall within a domain-selected margin) while saving target-normal acquisition cost versus fixed-N baselines. Normal-only observations cannot certify anomaly recall; this joint condition is a study-level success test, not an input to the readiness policy. Include an always-normal/no-alarm detector as a negative control.

Count a target as a commissioning failure if the policy has not declared `READY` by `N_max`. Report both the non-ready fraction among **all** eligible target entities and the cost capped at `N_max`; never compute mean collection cost only among targets that became ready. Report false-ready declarations over all target entities and conditional on READY declarations. Also report any evaluator-identified fault in a reference-normal prefix as contamination and any event exposure before activation; these remain stress diagnostics and never enter the policy.

Report, per target entity and then macro-averaged by family:

- `N_READY`, wall-clock time, and whether the policy never becomes ready;
- false-ready rate and future normal FPR on the hidden segment;
- post-ready AP/AUPRC, event recall/F-score, false alarms per unit time, and detection lead time;
- gap to the separate full-target-normal reference;
- readiness calibration/coverage, compute cost, and sensitivity to source-target dissimilarity;
- separate threshold-only gains from detector-weight adaptation.

Use a nested analysis: physical entity is the primary resampling cluster, with fault events nested within entity; do not treat events from one entity as independent or bootstrap individual overlapping windows. Manufacturer, farm, and utility are shared higher-level conditions. Report strata and leave-one-site/farm-out sensitivity analyses where identifiers permit. PreDist covers one utility and CARE to Compare only three wind farms, so neither by itself supports broad site-level generalization. For an initial sealed protocol, choose the practical quality margin, FPR target, confidence level, and minimum cost saving with domain owners before opening test outcomes. The sample-efficiency claim must pass in both families or be explicitly family-limited.

## Feasibility gates and kill criteria

**Proceed to a protocol draft only if** the metadata audit confirms adequate entity and chronological normal/fault coverage, and a full-text check of WindADBench and recent source-free / zero-shot baselines does not already answer the same stopping-rule question. Predeclare the intended claim level: use a formal normal-risk certification route only if its sequential validity assumptions can be defended; otherwise retain the empirical `READY_EMPIRICAL` route and drop certification language. Two eligible entity families are required for the cross-family confirmatory claim; one family supports feasibility analysis only.

**Stop or reframe if**:

- zero-shot/frozen detectors are already within the predeclared margin of the full-target reference at `N=0`;
- fixed-N or a simple threshold-stability rule matches the learned stopper's data/time cost;
- readiness features fail to predict hidden future normal risk across held-out entities;
- apparent data efficiency disappears when target episodes are entity-disjoint and future segments are strictly held out;
- the claimed false-alarm certificate depends on an unverified independence/exchangeability assumption;
- no dataset or operator record can establish which target observations were believed normal at the time of commissioning; in that case rename the study to reference-normal commissioning and drop deployment-certification claims;
- no dataset version has auditable normal-prefix and event provenance.

## Current recommendation

P5 remains a promising **implementation-oriented** candidate, but the public-data route is not yet confirmed: neither PreDist nor CARE alone proves a target-normal prefix was prospectively verified by an operator. The strongest study would require a defensible normal-data source and a common evaluation suffix, and would compare data/time cost only at matched joint FPR and anomaly-detection quality. Novelty is narrow: Jonas & Meyer (2026) already propose a normal-only model-quality proxy, and WindADBench may occupy the broad cross-entity benchmark framing. Introduce a learned stopper only if fixed-N and simple stability policies leave a verified gap. Do not claim a new transfer detector or a general certificate until the assumptions survive independent review.

No implementation or experiment is authorized by this proposal. M0's current protocol remains unchanged, and a future execution requires a separately sealed research protocol and data manifest.

## Sources checked for this pass

- [GitHub issue #9: P5 proposal](https://github.com/kuo1234/xlstm_anomaly/issues/9)
- Holly et al. 2025, [One-Class Domain Adaptation via Meta-Learning](https://arxiv.org/abs/2501.13052)
- Frikha et al. 2021, [Few-Shot One-Class Classification via Meta-Learning](https://arxiv.org/abs/2007.04146)
- Roelofs et al. 2024, [Transfer learning applications for anomaly detection in wind turbines](https://doi.org/10.1016/j.egyai.2024.100373)
- Jonas & Meyer 2025, [Fault Detection in New Wind Turbines with Limited Data by Generative Transfer Learning](https://doi.org/10.1016/j.egyai.2025.100626)
- Jonas & Meyer 2026, [Generative multi-domain transfer learning for fault detection in data-scarce wind turbines](https://arxiv.org/abs/2608.30323). Its anomaly-free model-selection proxy is a close signal-level comparator; the stopping target is training optimization, not target-data acquisition.
- Shentu et al. 2025, [DADA: Towards a General Time Series Anomaly Detector](https://arxiv.org/abs/2405.15273)
- Lan et al. 2025, [TimeRCD: Towards Foundation Models for Zero-Shot TSAD](https://arxiv.org/abs/2509.21190)
- Zhu et al. 2026, [When Foundation Models are One-Liners](https://openreview.net/forum?id=H27kvyG4qf)
- Gück et al. 2024, [CARE to Compare dataset paper](https://arxiv.org/abs/2404.10320); [corrected Zenodo v6 record](https://zenodo.org/records/15846963)
- Roelofs et al. 2026, [PreDist dataset paper](https://doi.org/10.1016/j.energy.2026.141178); [current Zenodo record](https://zenodo.org/records/19496480)
- [WindADBench repository](https://github.com/ZJU-DAILY/WindADBench), recent lead; publication metadata not independently established
- Rebjock et al. 2022, [Online false discovery rate control for anomaly detection in time series](https://arxiv.org/abs/2112.03196). This is relevant sequential-risk prior art, but FDR control is not the same estimand as FPR certification and should not be substituted without a derivation.

## Astra review log

**Review 1: `REVISE` (gpt-6-astra).** The reviewer required: joint evaluator-only quality and normal-risk success rather than FPR alone; correction of CARE to v6 and caution about retrospective/possibly contaminated normal labels; common hidden evaluation suffix and explicit never-ready handling; a data-splitting/repeated-look procedure for any risk claim; inclusion of Jonas & Meyer (2026); simple-first stopping-rule scope; and explicit new authorization/protocol gates. The design above adopts these changes.

**Review 2: `PASS` (gpt-6-astra), literature/design assessment only.** The reviewer accepted the revised design and requested that the future-risk certification route be distinguished from the empirical `READY_EMPIRICAL` route, that entity—not event—be the primary resampling cluster, and that target results be evaluated once after freezing the learned policy. These clarifications are included above. This PASS does not make the proposal an execution-ready protocol and grants no experiment or data-access authorization.

**Authorization boundary:** current M0 does not authorize any P5 fitting, adaptation, readiness-gate, or evaluation run. A future execution requires explicit project authorization, a committed protocol amendment where required, and a sealed eligible-data manifest before data/model outcomes are accessed.
