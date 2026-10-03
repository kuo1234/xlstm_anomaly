# P4 — Peer corroboration as evidence for fleet normality promotion

Review status: research/design assessment only (2026-09-27). No code, simulator, model, fleet data, or labels were used for this assessment. No experiment is authorized here.

## Recommendation

**Keep P4 as a conditional fleet-level evidence-fusion question; treat its novelty as threatened.** Peer-group anomaly detection, cross-machine comparisons, fleet-median filtering, cross-correlated change detection, and Byzantine-resilient distributed detection all have prior art. The broad claim that peer agreement can improve fleet anomaly detection is occupied.

The remaining plausible question is narrower: under what assumptions does peer evidence improve a target machine's normality-promotion/adaptation decision, beyond a target-only rule, while preserving local- and common-cause-fault detection under correlated or compromised peers? This has not been established as novel by the current search and requires a fuller search before any paper claim.

**Peer synchrony is evidence of a common change, not proof that it is benign.** If benign fleet-wide change and common-cause fault produce identical policy-visible information, peers cannot reliably distinguish their semantics on that stratum. This does not rule out probabilistic peer evidence elsewhere under explicit distributional assumptions. For the safety-oriented primary promotion policy, require an independent allowed context or confirmation signal; evaluate peer-only promotion separately and describe it as probabilistic evidence with no guarantee on the indistinguishable stratum.

The issue's proposed output labels should therefore separate `LOCAL_FAULT_CANDIDATE`, `COMMON_CHANGE_CANDIDATE`, and `UNRESOLVED` from any later `NORMAL_PROMOTION`. Peer evidence alone may generate the common-change candidate. Promotion requires a separately declared policy/anchor and remains evaluator-only in this assessment. This tests an evidence path, not a new detector or xLSTM mechanism.

## Feasibility and novelty

| Dimension | Assessment | Reason |
|---|---|---|
| Controlled algorithm study | Medium-high | Synthetic fleets can vary group size, shared shifts/faults, dependence, context, and bad-peer strategies with known truth. |
| Real fleet validation | Low/uncertain | Published examples establish fleet measurements and failure records, but I did not verify an accessible dataset with synchronized benign-shift semantics, common-cause-fault labels, peer integrity, and promotion/confirmation times. |
| Statistical power | Low until independent fleets/configurations are inventoried | Machines, peer links, windows, and events inside one fleet share shocks. The fleet episode/configuration, not each machine or edge, is the unit for inference. |
| Incremental novelty | Low/conditional | Peer comparison and fleet pooling are established. A narrow adaptation-promotion decision under explicit common-cause and compromised-peer strata remains plausible but unproven. |
| Current M0 compatibility | None for execution | The proposed promotion/adaptation behavior is new research behavior; M0 does not authorize it. M0's status does not provide a P4 GO. |

### Main identifiability constraint

Construct paired fleet worlds with identical **complete policy-visible histories** through a decision time: sensor observations, trusted context, peer payloads, roster/membership, event/receipt timing, missingness, prior actions, and coupled policy randomness, but opposite semantic labels. The policy's action distribution must match on that stratum; reliable semantic separation there is impossible without additional information. This result does not rule out probabilistic discrimination on distinguishable strata under declared assumptions. Any separation inside the identical-history pair signals leakage, post-event grouping, or accidental use of evaluator metadata.

The potentially identifiable strata are those with information that differs before the decision: for example, an externally reported operating-mode/setpoint change that is causally available to the policy, or a target-local deviation that peers do not share. The study must distinguish this allowed context from the hidden semantic label; an evaluator label cannot be relabeled as an operational context feature.

## Prior work and alternatives

| Work | What it establishes | Consequence for P4 |
|---|---|---|
| Hendrickx et al. (2020), [A General Anomaly Detection Framework for Fleet-Based Condition Monitoring of Machines](https://doi.org/10.1016/j.ymssp.2019.106585) | Online comparisons across similar electrical machines; the method assumes most machines are healthy and flags deviating machines, without requiring historical data. | Directly occupies peer-based fleet anomaly detection. P4 must be about licensing target normality promotion under semantic ambiguity, not adding peer comparisons to anomaly detection. |
| Giannoulidis & Gounaris (published 2022; volume 2023), [A Context-Aware Unsupervised Predictive Maintenance Solution for Fleet Management](https://doi.org/10.1007/s10844-022-00744-2) | Defines peer groups among similar equipment in the same operating context and uses peer behavior to detect target deviations in streaming fleet maintenance. | Close overlap for context-matched peer evidence. Its objective is anomaly/predictive-maintenance detection rather than a controlled comparison of peer-licensed model updates under common-cause faults. |
| de Novaes Pires Leite et al. (2023), [A Robust Fleet-Based Anomaly Detection Framework Applied to Wind Turbine Vibration Data](https://doi.org/10.1016/j.engappai.2023.106859) | Evaluates unsupervised fault detection on operational vibration from 12 turbines; expert condition labels are used for validation/test. | Direct wind-fleet precedent. It studies fleet detection/generalization, not peer agreement as a semantic normality-promotion gate. |
| Tveten, Eckley & Fearnhead (2022), [Scalable Change-Point and Anomaly Detection in Cross-Correlated Data with an Application to Condition Monitoring](https://doi.org/10.1214/21-AOAS1508) | Detects anomalous mean structure in a subset of cross-correlated time series and demonstrates the method in condition monitoring. | Collective/cross-series change evidence is established; P4 must address dependence and semantic interpretation rather than claim synchronized-change detection itself. |
| Zhang & Doganaksoy (2022), [Change Point Detection and Issue Localization Based on Fleet-Wide Fault Data](https://doi.org/10.1080/00224065.2021.1937409) | Uses wind-park fault logs to detect shared change points and localize affected turbines; the motivating case involved a surge in vibration-induced shutdowns. | Synchrony can be caused by fleet faults. Common-cause faults must be a primary adversarial stratum, not a minor robustness check. |
| Vervlimmeren et al. (2025), [Scalable SCADA-Driven Failure Prediction for Offshore Wind Turbines Using Autoencoder-Based NBM and Fleet-Median Filtering](https://doi.org/10.5194/wes-10-2615-2025) | Filters anomaly scores against a windowed fleet median and assumes most turbines are healthy at a time. The study reports proprietary data and code. | Fleet-level filtering and the majority-healthy assumption are established; its data are not an immediately reusable public validation set. |
| Yao et al. (2026), [CrossSTLLM: A Continually Adaptive Spatiotemporal Large Language Model for Anomaly Detection and Fault Localization in Wind Turbines with Diverse Distribution](https://doi.org/10.1016/j.apenergy.2026.128058) | Publisher record describes continual cross-turbine transfer and anomaly/fault localization across two real wind farms. | Further weakens generic “cross-turbine adaptive anomaly detection” novelty. Evidence checked here is publisher-record/abstract level; a full-text comparison remains necessary. |
| Bayraktar & Lai (2015), [Byzantine Fault Tolerant Distributed Quickest Change Detection](https://doi.org/10.1137/130924445) | Studies distributed sequential change detection with an unknown compromised subset sending arbitrary or fabricated observations; proposes robust alternatives. | Robust distributed change detection is established. Its iid-sensor setup is not heterogeneous machinery or semantic normality promotion, so P4 must state its threat-model difference. |
| Stavrou et al. (2009), [Keep Your Friends Close: The Necessity for Updating an Anomaly Sensor with Legitimate Environment Changes](https://doi.org/10.1145/1654988.1655000) | Studies model updates for anomaly sensors after controlled legitimate environment changes in network/host monitoring. | Environment-driven anomaly-model updates have precedent. P4's possible differentiator is what fleet evidence contributes to a target promotion decision, not legitimate-change adaptation by itself. |

The prior-art search therefore changes issue #8's initial novelty framing: “peer evidence for normality-promotion decisions” may be narrower than fleet anomaly detection, but it is not established as a gap merely by the absence of a named peer-promotion module in a short survey. Compare directly against fleet peer detectors, context-aware fleet methods, robust sequential voting, and continual cross-turbine adaptation. The closest methods have different objectives, but their existence limits broad combination claims.

## Proposed controlled study — only after P1 and separate authorization

### Policy interface and isolation

Use one pinned local detector and one fixed local update operator for every policy arm. Candidate windows come from a frozen causal target-only proposal rule. Peers do not provide raw training samples, gradients, or model parameters to the target in the primary study; they send only timestamped causal summaries from their own pre-update detectors, such as a standardized change statistic, anomaly score, allowed operating-context fields, and data-quality/availability flags. Keep peer models frozen during each primary decision episode so the tested treatment is evidence fusion, not propagation of peer adaptation.

Use peer evidence only to alter the target's promotion decision. Separate the stages:

1. The target-only rule raises a local candidate from the target's current data.
2. A peer module estimates whether comparable peers show a contemporaneous change and outputs `LOCAL_FAULT_CANDIDATE`, `COMMON_CHANGE_CANDIDATE`, or `UNRESOLVED`.
3. A predeclared promotion policy either queues/rejects the target candidate or requires independent allowed context/confirmation before local adaptation.

Include a peer-only promotion arm to measure its failure mode directly. The safety-oriented primary policy requires an independently available, trusted context/confirmation signal in addition to a common-change candidate. Include a context-only arm and a context-plus-peer arm to estimate the incremental value of peers conditional on that signal. Do not treat peer messages as ground truth or as proof that a shared change is benign.

### Fleet construction and scenarios

Generate new controlled fleet streams with fixed family identity, per-machine baseline parameters, shared environmental/operating factors, machine-specific noise, and configurable cross-machine dependence. Do not reuse M0's generator, datasets, selected series, or seed folds. The evaluator retains all semantic labels; each policy receives only features/context/messages observed by its decision time.

Cross these event types:

- benign common shift on a subset or all of a comparable peer group;
- local fault on the target while peers remain stable;
- common-cause fault affecting many or all peers;
- benign shift with a coincident local fault;
- common operating shift with staggered peer onset, missing peers, or delayed messages;
- exact paired benign/common-fault observations with opposite hidden semantics;
- corrupted, stale, faulty, or compromised peer messages, including coordinated in-range/mimic behavior;
- family mismatch and context changes that should cause abstention rather than promotion.

Vary fleet/peer-group size, benign-shift prevalence, local and common-cause fault prevalence, onset skew, sensor correlation/shared-shock strength, peer staleness/missingness, peer quality, and adversarial strategy. Candidate fleet sizes such as 5/10/20/40 and corruption fractions spanning no bad peers through minority and majority cases can seed the design; P1 and the later sealed protocol must choose the actual levels and independent configuration count. Do not assume a universal “honest majority” threshold; estimate a breakdown curve under explicitly named random, correlated, and strategic peer models.

Define peer membership from pre-event engineering metadata and/or a frozen past-only similarity rule. Freeze group membership, comparability thresholds, feature transforms, quorum, tie/fallback behavior, freshness limits, and missing-peer treatment before test outcomes. Never select peers using the target's post-onset response, test labels, or future regime. Keep same-source, same-farm, family, and counterfactual variants together in data splits. If fewer than the minimum permitted fresh peers are available, output `UNRESOLVED` and do not promote.

### Threat boundary and message clock

For the primary threat model, assume an authenticated, pre-enrolled roster with Sybil-resistant identities. The corruption denominator is **all rostered peers eligible under the pre-event group rule at that decision**, including eligible peers that are unavailable or stale; also report corruption among responders, but do not change the primary denominator to hide missing peers. The primary attacker may control and coordinate a subset of authenticated peers' reported sensor summaries, may send plausible in-range or adversarially chosen values, and knows the peer rule. Separate stress arms allow the attacker to delay, suppress, replay, or manipulate messages within a frozen bound. The primary attacker cannot alter the target's raw sensors, trusted context source, enrolled roster/identities, clock service, or external confirmation; test these as separate trust-boundary failures or explicitly exclude them. A physical common-cause fault is not a Byzantine peer and must be reported as its own event type. State these assumptions and roster counts alongside every robustness curve.

Every peer report records both **observation/event time** and **target receipt time**. A report is usable only if it arrived by the target's decision cutoff and its underlying observations precede that receipt and cutoff. Freeze allowable clock skew, cross-machine alignment window, maximum message age, duplicate/replay handling, and the waiting/quorum deadline in the later sealed protocol. Late reports cannot be backdated into a prior decision; they may enter a later decision only if still fresh under the frozen rule. Report raw eligible, received, fresh, stale, and excluded peer counts separately.

### Baselines and pairing

The primary episode contains one target candidate and at most one target update. Its candidate proposal is generated from a frozen local reference trajectory and is not changed by an earlier peer decision or adapted target state. Compare paired policies on the same fleet realization, candidate, initial target state, decision timestamp, update operator, maximum candidate exposure, and evaluator suffix:

1. frozen local detector with adaptation disabled;
2. target-only evidence and target-only promotion using the fixed update;
3. peer mean/reference aggregation;
4. k-of-n peer corroboration;
5. robust median/trimmed or bounded-influence aggregation;
6. pre-event similarity-weighted robust aggregation;
7. peer evidence used only to filter/re-rank anomaly outputs, with target updates disabled;
8. peer-only promotion;
9. external-context-only promotion and context-plus-peer promotion;
10. an evaluator oracle that knows the true semantic class, as an upper bound only.

Use identical candidate proposal and update semantics in the primary target-only versus peer-gated comparison. The frozen control uses that same candidate proposal but never updates. Gate/aggregation baselines that make different admission choices must be compared under the same candidate, delay, update-compute and exposure caps; report actual admitted candidates and peer-derived exposure separately. Include an equal-update diagnostic over the common admitted subset, marked secondary. If a secondary multi-candidate episode is studied, candidate proposals must still come from the frozen reference trajectory, independent of the adapted target state. No peer sharing/transfer arm should enter the primary comparison, since it would confound corroboration with training-data transfer.

Paired semantic worlds must share the entire observable fleet prefix: each machine's sensor/context trace, peer roster and messages, receipt timing, missingness, candidate IDs, initial state, and coupled policy randomness. In the identical-prefix arm, actions must match. Split whole generator families/configurations and sites before episodes; keep all machines and peer-set variants from one fleet realization in a single split and inference cluster.

### Measures and analysis

P1 must freeze the primary joint endpoint, operational margins, event unit, inference hierarchy, multiplicity, and power target before P4 execution. Candidate measures are:

- benign-shift promotion/adaptation delay and fraction never promoted;
- false promotion of local faults and, separately, common-cause faults;
- local fault and common-cause fault event recall, detection delay, missed events, and post-promotion masking;
- false alarms during benign common shifts and stable-normal specificity;
- target-state changes, proposed/admitted/rejected candidates, candidate exposure, peer-derived influence, and adaptation cost;
- robustness curves over bad-peer fraction, strategy, timing, similarity, correlation, and stale/missing messages, including minimum peer quality/fraction needed for any claimed benefit;
- unresolved/abstention rate and the fraction of cases whose semantics are unidentifiable from available information;
- communication, decision latency, memory, and privacy-relevant data fields transmitted.

The candidate primary claim is that peer evidence lowers benign-shift adaptation delay versus target-only promotion while meeting P1-frozen limits for local-fault and common-cause-fault harm at equal candidate delay, update compute, and exposure caps. Realized peer evidence/exposure and policy abstention remain outcomes. Estimate uncertainty by resampling or randomizing independent fleet configurations/sites first, with nested machine/run factors only if supported by P1. Machines, windows, and peer edges in one fleet are not independent replications.

### Stop criteria

Stop or narrow the peer-promotion claim if:

- the peer method does not beat target-only promotion on the P1-frozen joint endpoint at the same delay, compute, and exposure caps;
- fixed k-of-n, robust aggregation, or context-only rules match the proposed method within the prespecified margin;
- a common-cause fault is promoted as benign beyond the P1-frozen limit, or local-fault recall/masking breaches its bound;
- a modest, predeclared correlated or strategic bad-peer fraction erases the gain, or the minimum usable peer quality cannot be estimated;
- the policy separates the identical-prefix opposite-semantics worlds before any allowed information differs;
- peer selection, message freshness, or context use depends on post-onset/future information or evaluator labels;
- the result fails on held-out families/sites or is supported only by many windows/peer edges from a few fleets;
- claimed real-world validation requires synchronized benign-shift/common-fault labels that the selected data source cannot provide.

If common peers help only to identify that a change is fleet-wide, report that result as common-change localization, not normality promotion. If context supplies the semantic evidence and peer messages add no value conditional on context, drop the peer-promotion claim. A synthetic positive result without a suitable real fleet source is a controlled methods result, not deployment evidence.

## Data feasibility and authorization boundary

Published operational examples show that multi-turbine data exist, but they do not establish a ready P4 validation corpus. The 2025 WES fleet-median study reports proprietary data and unavailable code; its fleet median filters anomaly scores under a majority-healthy assumption. The 2023 wind-turbine vibration study uses 12 turbines and expert condition labels for held-out evaluation, but accessible provenance for synchronized benign shifts, common-cause faults, and promotion times is not established here. Treat either as a future access lead only, not as approved data.

This document analyzes GitHub [issue #8](https://github.com/kuo1234/xlstm_anomaly/issues/8); it does not authorize implementation, fleet-data access, simulation, training, label inspection, or changes to M0/M1. M0 expressly excludes new adaptation behavior. Its H1 controlled harm status is STOP, natural harm is NOT_RUN, overall harm is UNRESOLVED, and H4a/H4b remain locked; none of these statuses grants a P4 GO. Any future execution requires P1's evaluation/identifiability contract, a separate P4 protocol and sealed fleet/configuration manifest, and independent authorization/review. P1 remains outstanding in the requested order.

## Sources checked

- Project proposal: [GitHub issue #8](https://github.com/kuo1234/xlstm_anomaly/issues/8)
- [Hendrickx et al., fleet-based condition monitoring](https://doi.org/10.1016/j.ymssp.2019.106585), [Giannoulidis & Gounaris, context-aware fleet maintenance](https://doi.org/10.1007/s10844-022-00744-2), and [de Novaes Pires Leite et al., wind-turbine fleet anomaly detection](https://doi.org/10.1016/j.engappai.2023.106859)
- [Tveten et al., cross-correlated change/anomaly detection](https://doi.org/10.1214/21-AOAS1508), [Zhang & Doganaksoy, fleet-wide fault change points](https://doi.org/10.1080/00224065.2021.1937409), and [Vervlimmeren et al., fleet-median filtering](https://doi.org/10.5194/wes-10-2615-2025)
- [CrossSTLLM](https://doi.org/10.1016/j.apenergy.2026.128058), [Byzantine distributed quickest change detection](https://doi.org/10.1137/130924445), and [Stavrou et al., legitimate-environment anomaly-sensor updates](https://doi.org/10.1145/1654988.1655000)
- Project protocol boundary: [revised M0 protocol](../../reports/m0_protocol.md), [H1 status](../../reports/h1_status.json), and [M0 review](../../reports/m0_review.md)

## Astra review log

**Review 1: REVISE (gpt-6-astra), assessment only.** The reviewer required: restrict the indistinguishability result to the full identical-information stratum; declare the attacker trust boundary, Sybil assumption, and registered-peer corruption denominator; define causal use by receipt time and freeze skew/alignment/replay/deadline rules; add a frozen no-update control and freeze the primary candidate/update trajectory; and correct the complete CrossSTLLM and Tveten titles. These revisions are incorporated above. This review authorizes no experiment.

**Review 2: PASS (gpt-6-astra), research/design assessment only.** The reviewer accepted the bounded identifiability result, defined peer trust/timing assumptions, frozen no-update control, fixed primary candidate/update trajectory, and corrected titles. P1, a sealed P4 protocol/manifest, and separate authorization remain prerequisites. This PASS authorizes no implementation, data access, simulation, or experiment.
