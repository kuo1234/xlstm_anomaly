# P1 — Identifiability-stratified evaluation of adaptive TSAD

Review status: research/design assessment only (2026-09-27). No detector, simulator, model, dataset, or labels were used for this assessment. No experiment or data access is authorized here.

## Recommendation

**Keep P1 as a conditional evaluation-and-theory study, with a substantially narrower novelty claim than the issue proposes.** Point adjustment is already known to over-credit event detection; temporal metric/property frameworks can reflect shortened alarm coverage; recent online building anomaly detection already reports the fraction of abnormal samples admitted to updates with post-update detection quality. P1 cannot claim a new metric family simply because these existing measures may miss adaptation effects.

The defensible residual is a joint, detector-agnostic evaluation contract that: (1) distinguishes what a policy could know from hidden semantic truth; (2) includes benign/fault worlds with identical policy-visible histories as a formal lower-bound control; and (3) traces fault-tainted evidence into adaptive state and tests its downstream effect on a matched fault suffix, including masking after an initial alarm. Whether this is genuinely new remains conditional on a full-text audit of TSADmetrics and direct comparison to the closest contamination-rate work. If those works already cover the same state-exposure and post-update masking estimands, P1 should become a benchmark application or stop.

P1 does not depend on xLSTM or a positive M0 result. It is a separate evaluation/theory proposal. It must use a new independent generator and protocol if later authorized; it cannot reuse M0's generator, seed folds, datasets, manifests, or protected M1 artifacts.

## Feasibility and novelty

| Dimension | Assessment | Reason |
|---|---|---|
| Identifiability theory | High, if stated at the level of policy-visible histories and named metrics | Equality of observable-history laws gives a direct decision-theoretic lower bound. Partial overlap, priors, and context reliability need explicit treatment; there is no universal 0.5 floor for every metric. |
| Controlled evaluation | Medium-high | A new paired generator can provide exact semantic truth, identical-history controls, and known fault exposure. The generator must be independent of M0 and sealed before outcome access. |
| Baseline coverage | Medium | A six-to-eight-method CPU-first comparison is plausible, but online update APIs, checkpoints, and causal semantics may differ. The study needs an implementation inventory before promising coverage. |
| Real-data transfer | Low/uncertain | Exathlon has root-cause and extended-effect intervals useful for recovery analysis, but not verified benign-shift/promotion semantics. e-Energy is a close contamination comparator, but licensing and event-ID reconstruction remain unresolved. No located public source supports all semantic strata and operational context channels. |
| Statistical power | Low until independent configurations are counted | Windows/events within one generated configuration or source series are not independent replications. The generator family/configuration is the primary inference unit. |
| Incremental novelty | Low/conditional | LARM, TSADmetrics, SCAR, STAD, StrAD, and e-Energy cover important pieces. The paired impossibility control plus update-state exposure and same-suffix masking may remain distinctive, but this gap is not established. |
| Current M0 compatibility | None for execution | M0's controlled-harm gate is STOP, natural-harm status is NOT_RUN, overall H1 status is UNRESOLVED, and H4a/H4b remain LOCKED. None of these supplies P1 evidence or authorization. |

## Formal information boundary and identifiability strata

Let `Y` be evaluator-only semantic truth (benign new normal versus fault), and let the policy's information at decision time `t` be the filtration

`F_t = σ(X_≤t, C_≤t, released confirmations/queries, prior actions and state, policy randomness)`,

where `X` is the observed stream and `C` contains only context actually available to the policy by `t`. The exact allowed channels, timestamps, missingness, and reliability are part of the protocol. Future observations, event boundaries, labels, generator parameters, and evaluator annotations are not in `F_t`.

Identifiability is a property of the declared semantic hypothesis families, observation channel, and decision horizon, not a retrospective name assigned to an individual segment:

1. **X-identifiable:** the declared benign and fault history laws differ using `X` by the frozen decision horizon under a stated Bayes-error or likelihood-separation criterion.
2. **Context-identifiable:** the `X` history laws are equal or insufficient under that criterion, but the joint `(X,C)` laws differ using an operational context channel available by the decision time.
3. **Non-identifiable at the horizon:** the complete policy-visible history laws are equal through every decision in the horizon. Construct at least one exact paired control with the same complete `X/C` prefix, missingness, released-message schedule, candidate IDs, initial policy state, and coupled policy random seed, but opposite evaluator-only `Y`.

For the exact equal-law case, every `F_t`-measurable policy has the same action/score distribution in both semantic worlds. The simple floors below apply only to **classification of the semantic world `Y` at the same declared decision unit and horizon**. With equal class priors, the optimal classification error is one half, AUROC is 0.5, and population AP is the class prevalence (randomized tie handling is interpreted in expectation). For unequal priors, the optimal decision is the prior-favored rule and its error is the corresponding Bayes floor. Pooled pointwise/event detection AUROC or AP do not automatically inherit these floors: shared normal prefixes, onset structure, point weighting, and repeated windows can change those quantities. For noisy/partial context or nonidentical overlapping laws, derive a metric-specific Bayes bound from the laws and evaluation units. Do **not** claim that every event metric, delay measure, or finite-sample estimator has a universal 0.5 floor.

The exact-pair control is a generator and evaluator integrity check. For the floor test, use one semantic-world classification score per paired episode at the declared horizon; specify class priors, episode weighting, tie convention, and the finite-sample null before the run. Test paired-world discrimination against the analytic bound with uncertainty/resampling at the independent generator-configuration level (and retain each exact pair within one cluster). A result above that matched bound beyond uncertainty means the claimed identical-history stratum leaked information or was implemented incorrectly; it does not show that a model beat an information-theoretic limit. Do not apply this inference to pooled pointwise labels. Separately include overlapping but not identical histories to estimate performance as a function of available evidence. A context-only result is valid only when its availability timestamp, error rate, missingness/corruption process, and operational source are specified; a hidden label copied into `C` is leakage.

Freeze the hypothesis families, horizon, priors, context channel, and separation criterion before generation. Do not tune the boundary between identifiable and non-identifiable strata after looking at method outcomes. The simple-classifier leakage audit is a diagnostic, not a way to redefine a failed stratum.

## What the prior art changes

| Work | What it establishes | Consequence for P1 |
|---|---|---|
| Kim et al. (2022), [Towards a Rigorous Evaluation of Time-Series Anomaly Detection](https://arxiv.org/abs/2109.05257) | Point adjustment can award an entire contiguous event after a single predicted point; this can substantially overstate event performance. | “Point-adjustment criticism” is not a contribution. A hit-at-onset followed by absorption illustrates one PA-F1 failure mode, but unadjusted point and temporal-coverage metrics may penalize the later missing alarms. |
| Wagner et al. (AISTATS 2026), [Formally Exploring Time-Series Anomaly Detection Evaluation Metrics](https://proceedings.mlr.press/v300/wagner26a.html) (LARM) | Defines nine core and 18 advanced properties for fixed ground-truth/prediction comparisons, including detection extent/count, false alarms, timing, and early/late alarms. The properties do not consume update traces, model state, sample influence, rollback residual, or matched post-update counterfactuals. | LARM is a material threat to broad metric novelty. It can reflect a shortened predicted alarm; P1 must not say it cannot penalize a shortened output. Its apparent gap is attribution to adaptation and retained-state consequences, not alarm duration itself. |
| Velasco & Zafra (2026), [TSADmetrics](https://www.sciencedirect.com/science/article/pii/S0925231226015523) and [package taxonomy](https://pypi.org/project/tsadmetrics/) | Catalogs 34 metrics across point accuracy, temporal coverage, event alignment, tolerance, and delay. The primary full paper was not retrievable in this audit. The publisher volume date is 14 Oct 2026, after this review date; earlier online/package chronology needs verification. | Full-text audit remains a hard novelty gate. If a property consumes adaptation state/update influence or already measures post-promotion carryover, kill the metric novelty claim. Current evidence suggests output metrics, but is insufficient to close the audit. |
| Ma et al., [SCAR: Revisiting Streaming Anomaly Detection: Benchmark and Evaluation](https://link.springer.com/article/10.1007/s10462-024-10995-w) and [official generator](https://github.com/yixiaoma666/SCAR) | Provides streaming data with separately labeled drift positions and anomaly injection, including several drift types; reports score-based detection evaluation. | Combined drift/anomaly streams and drift labels are established. The reviewed paper/repository did not show promotion correctness, exact equivalent-history strata, or post-promotion state/masking accounting. |
| Li et al., [STAD: State-transition-aware anomaly detection under concept drifts](https://www.sciencedirect.com/science/article/pii/S0169023X24000892) | Models recurring distribution states and transitions, and evaluates anomaly detection under drift. | State reuse and drift-aware detection are close alternatives. The material reviewed did not establish semantic promotion correctness or an identical-history lower-bound stratum. Compare the full 2024 paper before asserting this gap. |
| StrAD/TSB-drift (KDD 2026), [official project](https://github.com/magaliparrino/StrAD), [paper DOI](https://doi.org/10.1145/3770855.3817495) | Compares 29 static/online/streaming methods on 17 real datasets and 75 drift-selected series in a unified batch-train/online-test setting. | Weakens any claim that no realistic cross-method streaming comparison exists. Statistical distributional drift selection is not adjudicated benign normality; reviewed materials do not show equivalent benign/fault pairs or adaptation-state contamination attribution. |
| Le et al. (e-Energy 2026), [online anomaly detection in smart buildings](https://doi.org/10.1145/3744255.3811742) | Explicitly defines contamination rate as the fraction of updates that are abnormal, compares no/full/selective update policies, and reports post-update AUC/F2/recall. | This is a close TSAD contamination precedent and already occupies scalar abnormal-update-rate plus later detection-quality reporting. P1 must compare its exact denominator and decision granularity. Any residual claim must center on time-resolved state exposure/influence, matched post-hit persistent-fault masking, and semantic identifiability—not merely “we report contamination and post-update quality.” Licensing and event-ID reconstruction also remain open for reuse. |
| Faber et al. (2026), [Towards Principled Continual Anomaly Detection](https://arxiv.org/abs/2607.18289) | Directly addresses continual anomaly detection principles and adaptation evaluation. | Full-text comparison is required for retention, contamination, and state-transition overlap; it is another prior-art kill check, not evidence of a gap. |
| Bock et al. (2021), [Exathlon](https://arxiv.org/abs/2010.05073) | Labels root-cause and extended-effect intervals in cloud-service traces. | Could anchor post-event recovery and extended effects. Those intervals do not by themselves establish benign regime changes, candidate promotion truth, or a context channel. |

These sources leave a plausible but narrow question: can a controlled semantic-identifiability design show when alarm metrics miss **adaptation-attributable** fault absorption, after accounting for what existing output metrics and update-contamination rates already measure? The current search does not establish that answer. No claim that “no TSAD method measures masking” is supported by this audit.

## Candidate estimands and reporting

Do not collapse the study to one composite metric. Report standard output quality beside separate state and causal diagnostics; show their trajectories and joint frontier. Define the policy's normality state before the study (for example, candidate evidence, promoted evidence, and confirmed normal reference) and state exactly which transitions count as promotion or influence.

Capture the complete mutable state that can affect future behavior at each decision: parameters, optimizer/scheduler/momentum, normalization, thresholds, replay/memory, recurrent/cache state, counters, and policy RNG. Record candidate, selected, queued, optimizer-consumed, retained, and rolled-back evidence separately. This lets the evaluator distinguish a missed alarm from a state update that later changes the alarm.

Candidate measures include:

- **Detection output:** point AP/AUPRC and AUROC; unadjusted point metrics; event recall/precision, false alarms per unit time, and detection delay with frozen event matching; PA-F1 only as a named legacy sensitivity analysis; and selected LARM/TSADmetrics properties after their formula audit.
- **False promotion:** the fraction of fault-tainted candidate evidence that the policy designates/promotes as normal, with candidate and committed denominators shown separately.
- **Exposure:** unique fault-labeled windows reaching any update path; proportion and count entering optimizer/replay/normalizer/state; time-resolved exposure before and after the first alarm; and the subset retained in state. Report separately from the e-Energy-style update contamination fraction so denominator differences are visible.
- **Fault absorption/masking:** after an initial alarm on a persistent fault, first sustained alarm failure under a frozen alarm rule; alarm trace and score trajectory against a paired no-adaptation/frozen-state trajectory on the same continued fault; detection loss on a fixed later fault suffix; and residual state/output effect after the fault ends or a declared rollback. A missed detection alone is not evidence that adaptation caused contamination.
- **Benign adaptation:** A→B adaptation delay and false-alarm burden; A→B→A old-regime recovery; recovery censoring; and fault/benign-shift coincidence reported as its own stratum.
- **Joint summaries:** quality-versus-fault-exposure and benign-adaptation-delay-versus-fault-masking frontiers, with uncertainty. Avoid one weighted score unless operational weights and tradeoffs are frozen in a later protocol.

For causal attribution, pair each adaptive trajectory with an initially identical frozen/no-update trajectory on the same stream. This estimates the **total effect of the adaptation policy**; it does not isolate fault-tainted updates from benign updates, threshold changes, or other state evolution. Claim a fault-update-specific effect only in an evaluator-only matched intervention that clones the full pre-update state and toggles admission/consumption of a declared fault-tainted cohort while holding the update operator, schedule/step count, all other evidence, and post-update suffix fixed. If an existing method cannot support that intervention without changing its semantics, report total adaptation-associated masking and mark fault-update-specific attribution unavailable. Exposure membership or parameter distance alone does not prove retained influence of a particular sample. For rollback comparisons, also clone the complete relevant state at the intervention point and replay the same fixed probe suite and post-event suffix. Report state distance as well as output parity; score parity on one stream is not proof that mutable state was restored.

## Proposed controlled study — only after a separate protocol and authorization

### Independent stream design

Use a new generator and source families, independent of M0's equations/configuration/seed ranges and independent of its selected datasets. P1's theory and generator validation must not inspect or reuse M0 outputs. A later protocol should specify the generator equations, code/version hash, RNGs, scenarios, and manifest before any run.

The design should cross distinct cases rather than treating “drift” and “anomaly” as mutually exclusive labels:

- stationary normal and stationary normal with transient anomalies;
- benign abrupt/gradual A→B and benign A→B→A;
- transient and persistent faults, including a persistent fault that first triggers an alarm and then continues after the adaptive state changes;
- benign shift with a coincident local fault;
- X-identifiable and context-identifiable pairs with evidence becoming available at declared times;
- exact identical-observation/opposite-semantic pairs through a fixed horizon;
- noisy/partial context, missingness, out-of-support context, and overlapping-but-not-identical histories.

Keep evaluator truth, event IDs, drift/fault status, and future suffix hidden from policies. Context is a policy input only when its source/time is operationally specified. The “non-identifiable” arm should couple every policy-visible input and policy randomness, not only the sensor vector at one timestamp.

### Methods and controls

After an implementation/access inventory, choose six to eight existing methods whose causal online behavior can be audited on a common stream: a frozen/static detector; naive online retraining; one or more selective-update methods; a memory/replay method; a published adaptive/TTA baseline with usable code; and a no-update/frozen reference. Include an evaluator-only oracle update arm only as an upper bound. This is a candidate set, not a guarantee that all methods can be fairly ported or run on CPU.

Separate two comparisons:

1. **Policy-native comparison:** each method runs its published or documented causal update rule, with resolved settings and its actual candidate/exposure trace logged.
2. **Matched intervention comparison:** for methods that support the same frozen candidate cohort and update operator, clone the identical pre-intervention state and compare update/no-update or retain/rollback on a fixed identical suffix. If a method cannot support that intervention without changing its semantics, mark it unavailable rather than silently modifying it.

Report a clearly named common candidate cohort and equal-update diagnostic where possible. Do not interpret different candidate selection as an update-quality effect. No method receives semantic labels or future samples. Preserve method-native evaluation as a separate result if a fair common wrapper cannot be built.

### Splits, units, and analysis

Split whole generator configurations/families, latent templates, and seeds into development, validation, and untouched test groups before episodes are generated. Keep all windows, recurring regimes, paired semantic worlds, counterfactual copies, and suffixes from one source configuration together. Thresholds and hyperparameters may be selected on development and frozen on validation; inspect the held-out test configs once.

Use an independent generator configuration (or, for a later real-data anchor, independent source/site) as the primary inference unit. Pair method contrasts within that unit; cluster bootstrap/randomization at the configuration level, with nested episode/site factors only if the design supports them. Windows and events within a stream are not `n`. Predeclare sample size/power, practical margins, confidence intervals, multiplicity, operating points, event matching, censoring, and missing-data treatment in a sealed protocol. The discovery-level gates below are candidate criteria only, not frozen experiment thresholds.

Include predeclared leakage classifiers using observable lags, window statistics, spectra, and available context. Train them on development configurations and evaluate on untouched configurations. For an exact non-identifiable stratum, train/evaluate on the same paired-episode semantic classification unit and weighting used by the analytic floor; keep both worlds of each pair and configuration in the same split/cluster. Compare to a pair-preserving label-swap/randomization null, with uncertainty clustered by generator configuration. Above-null separation invalidates that construction; pooled pointwise detection performance is not this leakage test. It must not be repaired after test outcomes are viewed.

### Real-data anchor

Exathlon's extended-effect intervals may support a secondary check of alarm/recovery behavior, but cannot supply semantic normality-promotion truth without additional independent annotation. e-Energy is a closer candidate for update-contamination analysis, but licensing, version, event-ID provenance, and data availability need resolution first. SCAR/STAD or StrAD can support comparative streaming/detection results after their label and protocol semantics are audited; distributional drift tags are not ground-truth benign normality. If no anchor provides independent semantic labels and authorized access, present the study as a controlled theory/benchmark result and make no claim of real-world promotion correctness. No dataset download or label inspection is authorized in this assessment.

## Kill and downgrade criteria

Complete the remaining full-text/prior-art audit before implementation: TSADmetrics; STAD's full 2024 paper; Faber; e-Energy's exact contamination denominator and sample/update granularity; and direct formula comparisons for the LARM/TSADmetrics properties. Then freeze any numeric criteria in a separate protocol before outcome access.

The source discovery plan supplies candidate gates:

- **L1 — metric overlap:** if TSADmetrics or another existing framework already consumes update/state exposure and measures subsequent absorption/carryover equivalently, kill the new metric-family claim. This alone does not invalidate an independently justified identifiability result. If overlap is limited to alarm-output duration, narrow the claim to adaptation attribution and state carryover.
- **L2 — benchmark/semantic overlap:** if SCAR, STAD, StrAD, e-Energy, Faber, or another benchmark already supplies equivalent-by-construction benign/fault strata plus promotion correctness and subsequent masking, downgrade or stop P1's novelty claim. Existing drift/anomaly labels alone do not establish that equivalence.
- **K1 — ranking similarity:** if standard and state-aware metric method rankings have Kendall `τ ≥ 0.8` in every prespecified scenario family, treat this as a proposed gate against an added-ranking-value claim. High rank correlation alone does not prove that state-aware measures add no information or causal value; the later protocol must also define a decision-relevant comparison and practical margin.
- **K2 — impossible-stratum violation:** a method performing above the analytic Bayes floor on the exact non-identifiable stratum beyond uncertainty means leakage or a faulty construction; repair only under a pre-outcome protocol amendment, otherwise stop.
- **K3 — observable leakage:** a predeclared simple classifier separates the purported non-identifiable stratum beyond the frozen chance margin; invalidate the stratum and stop or rebuild before test outcomes are used.
- **K4 — ranking redundancy:** if state-aware measures have candidate rank correlation `≥ 0.95` with AP across the prespecified runs, treat this as evidence of ranking redundancy, not proof of no information or no causal value. The protocol must define an additional decision-relevance criterion before this can support a broader metric-value stop.
- **Program-level stop:** if both L1 and L2 establish equivalent prior art and the separate P1-frozen decision-relevance analysis finds no practically meaningful distinction, stop the proposed P1 contribution. K1/K4 correlations alone are not sufficient.

K1/K4 thresholds are discovery proposals, not established scientific constants. A later protocol must define the decision-relevance endpoint, margins, which methods/families enter the correlations, treatment of ties/missing methods, and uncertainty. Failure of K2/K3 is a validity failure, not a negative model result.

## Protocol items to freeze before any future run

The separate P1 protocol must specify: formal `F_t` and allowed context/confirmation channels; semantic hypothesis families and priors; horizon and identifiability/separation criteria; exact-equivalence construction and metric-specific Bayes floors; generator equations/version/hash/RNGs; scenarios/onsets/durations/severity/overlap; policy state and promotion definitions; all methods/checkpoints/hyperparameters/update schedules; paired seeds and source-disjoint splits; tuning budget; event matching and complete metric formulas; candidate/committed/optimizer/retained exposure denominators; masking and counterfactual suffix definitions; rollback-state schema and frozen probe suite if rollback is studied; sample size/power/inference unit; practical margins, CIs, multiplicity, stopping rules; missing/censor/exclusion rules; compute/time caps; dataset license/version/hash and allowed label-access process; and a manifest plus independent GO/STOP review.

This list defines future protocol obligations. It does not authorize building a generator, benchmarking methods, accessing a dataset, or inspecting labels now.

## Current authorization boundary

This document assesses GitHub [issue #5](https://github.com/kuo1234/xlstm_anomaly/issues/5). It authorizes no code, simulation, model execution, data download, label inspection, M0 change, or M1 access. The [revised M0 protocol](../../reports/m0_protocol.md) prohibits the relevant new adaptation behavior and locks H4a/H4b; [H1 status](../../reports/h1_status.json) is controlled STOP, natural NOT_RUN, overall UNRESOLVED. Any later P1 study requires its own independent generator, versioned sealed protocol, data manifest, applicable GO/STOP review, and separate authorization. Existing protected M1 artifacts remain out of scope.

## Sources checked

- Project proposal: [GitHub issue #5](https://github.com/kuo1234/xlstm_anomaly/issues/5)
- [Kim et al., point-adjustment evaluation analysis](https://arxiv.org/abs/2109.05257); [Wagner et al., LARM/AISTATS 2026](https://proceedings.mlr.press/v300/wagner26a.html); [TSADmetrics publisher record](https://www.sciencedirect.com/science/article/pii/S0925231226015523) and [package taxonomy](https://pypi.org/project/tsadmetrics/)
- [SCAR paper](https://link.springer.com/article/10.1007/s10462-024-10995-w) and [official generator](https://github.com/yixiaoma666/SCAR); [STAD](https://www.sciencedirect.com/science/article/pii/S0169023X24000892); [StrAD](https://github.com/magaliparrino/StrAD) and [KDD 2026 DOI](https://doi.org/10.1145/3770855.3817495)
- [Le et al., e-Energy 2026](https://doi.org/10.1145/3744255.3811742); [Faber et al., continual anomaly detection](https://arxiv.org/abs/2607.18289); [Exathlon](https://arxiv.org/abs/2010.05073)
- Project boundaries: [revised M0 protocol](../../reports/m0_protocol.md) and [H1 status](../../reports/h1_status.json). The source discovery program's L1/L2/K1–K4 gates are summarized above; its documentation-only branch was reviewed as background.

## Astra review log

**Review 1: REVISE (gpt-6-astra), assessment only.** The reviewer required: scope the equal-law AUROC/AP floor to semantic-world classification at a matched decision unit/horizon rather than pooled pointwise detection; distinguish total adaptation effect from fault-update-specific causal attribution; and treat K1/K4 rank correlations as ranking-redundancy heuristics rather than proof of no information or causal value. The report now states the unit/weighting/tie/null requirements, adds a matched fault-cohort intervention for specific attribution, and narrows the gates. This review does not authorize execution.

**Review 2: PASS (gpt-6-astra), research/design assessment only.** The reviewer accepted the matched semantic-world decision-unit floors and leakage null, the distinction between total adaptation effect and fault-update-specific matched intervention, and the narrower interpretation of K1/K4. The design is concrete enough for a later protocol while retaining open literature, implementation, and data-access gates. This PASS authorizes no implementation, experiment, dataset access, label inspection, or M0/M1 change.
