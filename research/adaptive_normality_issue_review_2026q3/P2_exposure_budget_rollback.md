# P2 — Unverified exposure budget: rollback versus waiting

Review status: research/design assessment only (2026-09-27). No code, simulator, model, dataset, or labels were used for this assessment. No experiment is authorized here.

## Recommendation

**Keep P2 as a conditional policy-comparison question; do not execute it under the current M0 protocol.** M0 explicitly excludes rollback, delay-plus-revalidation, and new adaptation behavior. Its H1 controlled harm route is STOP, its natural-harm route is NOT_RUN, overall H1 harm is UNRESOLVED, and H4a/H4b remain locked. H5 requires H1-harm and H4a to pass; none of these gates authorizes P2. M0 must remain unchanged.

The broad idea is not novel: delayed-feedback learning, test-time adaptation for new normals, selective/risk-aware adaptation, source-state restoration, and general delayed-label risk controllers all have prior art. The remaining plausible contribution is narrower: a controlled, TSAD-specific comparison of waiting for delayed semantic confirmation against provisional live adaptation with rollback, under common prespecified exposure and compute caps. The policies' realized unverified exposure is an outcome and will generally differ: waiting has no live unverified update influence, while provisional adaptation does. The claim is conditional on an explicit identifiability control, operational exposure accounting, valid current-time rollback semantics, and a meaningful difference from simple dwell or selective-admission policies. A fuller literature search would still be required before any novelty claim.

The requested P2-before-P1 order is respected here as a design assessment. Any later protocol or execution must adopt the evaluation and identifiability contract established by P1, or document a reviewed reason for a different contract. No simulator or data work should begin before then.

## Feasibility and claim boundary

| Dimension | Assessment | Reason |
|---|---|---|
| Policy comparison | Medium | The policies can be compared in a controlled stream if the update operator, confirmation channel, and rollback state are pinned. |
| Semantic validity | Low on public benchmarks; high in a controlled simulator | Public TSAD datasets generally do not record when a human or independent process confirmed that a changed pattern was benign. Synthetic truth can establish causal ground truth, but cannot by itself establish deployment validity. |
| Rollback engineering | Medium | It is straightforward only if a transaction snapshot includes every state element that can affect future outputs. Restoring weights alone is not rollback. |
| Statistical power | Unknown until P1's independent unit and evaluation contract are set | Windows and overlapping events are not independent replications. The complete stream/configuration or independent simulator episode must be the inference unit. |
| Incremental novelty | Low/conditional | Close components are established. The potential gap is a TSAD-specific policy frontier under common caps, not a new rollback or adaptation mechanism. |
| Current M0 compatibility | None for execution | M0 prohibits the required rollback/new adaptation behavior and does not establish H1 harm. |

P2 asks when a policy should wait versus adapt provisionally and roll back, while minimizing benign-shift adaptation delay under a limit on unverified influence. The target claim must be policy-level. Do not frame this as an xLSTM contribution or introduce a new cell, learned gate, or adaptation architecture.

### Define exposure as a vector

“Unverified exposure” cannot be a single unexplained count. For each decision and update episode, record at least:

1. **Unique-window exposure:** distinct candidate windows used by an update while their semantic status is unconfirmed.
2. **Optimizer exposure:** candidate-window × optimizer-step multiplicity, including repeats, replay, and batch reuse.
3. **Raw-time coverage:** unique raw timestamps covered by those windows, separately from overlapping-window counts.
4. **State-component exposure:** unverified influence on weights, scaler/normalizer, thresholds, replay buffers, optimizer state, and any other persistent component.
5. **Residual exposure:** how much of that influence remains after rejection or rollback, measured by state comparison and output comparison on a fixed input suite.

Keep proposed, selected, pending, applied, committed, rejected, and rolled-back counts separate. Report both unique counts and repeated update exposure. A cap is an experimental constraint, not a statistical risk certificate. Treat the main budget as a vector of caps; do not collapse it to one scalar unless operational costs and weights are set before outcome access. Compare policies at the same caps and plot the benign-delay versus fault-risk frontier.

### Observability limit

If a benign shift and a fault produce exactly the same observations up to confirmation time, a sensor-only policy cannot distinguish them during that prefix. In that paired control, any policy must make the same decision distribution in both semantic worlds. No early benign benefit can be claimed without also accepting the corresponding fault exposure. The study should include both this impossibility case and cases where context or the observation stream provides increasing evidence. Any gain is conditional on that available evidence or on the arrival of the external confirmation signal.

## Prior work and alternatives

| Work | What it establishes | Consequence for P2 |
|---|---|---|
| Lamaakal et al. (2026), [Drift-to-Action Controllers / Drift2Act](https://arxiv.org/abs/2603.08578), also published at the CAO Workshop at ICLR 2026 | A general drift controller uses delayed labels, a risk certificate, intervention costs, and actions including adaptation, abstention, rollback, and retraining. | Strongly weakens a generic “budgeted controller chooses rollback or wait” novelty claim. P2 would need to establish TSAD-specific value under its exposure and fault-absorption measures, beyond the generic controller. |
| Han et al. (2023), [Anomaly Detection in the Open World (OWAD)](https://www.ndss-symposium.org/ndss-paper/anomaly-detection-in-the-open-world-normality-shift-detection-explanation-and-adaptation/) | Studies normality shift for security anomaly detection, including detection, explanation, adaptation, long-running application data, and an initial SCADA deployment. | Rules out broad claims that normality-shift-aware anomaly detection or adaptation is itself new. The paper does not establish P2's rollback-versus-wait comparison. |
| Kim, Park & Choo (AAAI 2024), [When Model Meets New Normals](https://doi.org/10.1609/aaai.v38i12.29210) | Test-time adaptation for unsupervised time-series anomaly detection learns new normality during inference. | Direct TSAD overlap for the benign adaptation objective; P2 must isolate the delayed-confirmation and reversibility question. |
| Huang et al. (2026 preprint), [When Normality Shifts: Risk-Aware Test-Time Adaptation for Unsupervised Tabular Anomaly Detection](https://arxiv.org/abs/2605.10242) | Selectively updates using high-confidence pseudo-normal samples while constraining likely anomalies. | Risk-aware selective admission is a close comparator and may remove any gain attributed merely to filtering. It is tabular AD, not the proposed TSAD policy comparison. |
| Sun et al. (2024 preprint), [Continuous Test-time Domain Adaptation for Efficient Fault Detection under Evolving Operating Conditions](https://arxiv.org/abs/2406.06607) | Applies continuous TTA to pump fault detection under evolving operating conditions. | Establishes adjacent operational TTA. P2 should compare confirmation policies around the same fixed update method, not claim continuous fault-detection adaptation is new. |
| Wang et al. (CVPR 2022), [CoTTA](https://openaccess.thecvf.com/content/CVPR2022/html/Wang_Continual_Test-Time_Domain_Adaptation_CVPR_2022_paper.html) | Stochastically restores selected weights toward source parameters to limit forgetting during continual TTA. | Restoration has precedent, but periodic partial restoration is not rollback after delayed semantic confirmation or proof of exact state recovery. |
| Ambekar et al. (2024 preprint), [Selective Test-Time Adaptation for Unsupervised Anomaly Detection](https://arxiv.org/abs/2410.03306) | Selective test-time adaptation for medical-image anomaly detection avoids adapting on suspected pathology while keeping the source model frozen. | Selective/curated admission belongs in the comparator set; it also highlights that rollback is not the only route to limit contamination. |
| Zhu et al. (PVLDB 17(4), 2023), [METER](https://www.vldb.org/pvldb/vol17/p794-zhu.pdf) | Uses an evidential drift controller and hypernetwork-generated parameter shifts for dynamic concept adaptation. | Controller-driven adaptation is established; compare against well-defined wait/dwell and selective rules before attributing value to rollback. |
| Joulani, György & Szepesvári (ICML 2013), [Online Learning under Delayed Feedback](https://proceedings.mlr.press/v28/joulani13.html) | Analyzes delayed feedback and its impact on online-learning regret. | Waiting has a formal cost in general online learning. This does not prove that provisional adaptation helps TSAD or that rollback limits anomaly risk. |

Related restoration, delayed-verification, and adaptation-control work further reduces broad novelty. The residual gap is not established until P1's search and evaluation contract and a more complete full-text search are complete.

## Proposed controlled study — only after separate authorization

### Study question and test environment

Use a new, task-specific synthetic streaming environment with known latent semantics and evaluator-only truth. Do not reuse the M0 generator, seed folds, selected datasets, or protected M1 artifacts. Freeze one existing detector and one deterministic online update operator before evaluation; use that exact operator across all policy arms. Select the detector/operator based on implementation feasibility and a separate development set, never on test outcomes. The result tests update timing and recovery policy, not an xLSTM architecture.

The primary environment should generate independent stream episodes with:

- normal-only regime change, including abrupt and gradual benign shifts;
- faults without benign shift, including transient and persistent faults;
- benign shift coincident with fault, with controlled overlap and severity;
- an ambiguous prefix where paired benign and fault histories have identical sensor observations until a specified confirmation time;
- optional context conditions in which a permitted external context feature makes the regimes more distinguishable.

The evaluator knows the semantic class and confirmation schedule. The policy receives only sensor/context values available by the current decision time and any external confirmation actually released by that time. Labels, event boundaries, and future values remain evaluator-only. Confirmation delay, fault duration, benign-shift duration, context availability, severity, overlap, and exposure caps are crossed as sealed factors. Candidate values such as confirmation delays of 0, 4, 16, and 64 decision windows can seed the protocol design, but are not authorized or final until P1 and a separate protocol freeze. The M0 H4b K grid remains specific to its FIFO scheduling control and must not be treated as P2 authorization.

A later replication on a process simulator such as [pyTEP](https://doi.org/10.1016/j.softx.2022.101053) or [COSTEP](https://doi.org/10.1016/j.dche.2026.100328) is conditional on access review and an explicit mapping from simulator states to normal-shift/fault semantics and confirmation times. Fault identifiers in a simulator do not automatically provide an independent confirmation process. Public SMD/SWaT/industrial datasets can provide descriptive detector checks only; absent provenance for verified benign shifts and real confirmation latency, they cannot confirm the semantic P2 claim.

### Confirmation and rollback semantics

Model confirmation as an external adjudication channel with recorded issue time, release time, coverage, and correctness. The controller cannot infer or read the adjudicated class before release. The primary channel should be deterministic and correct so the policy contrast is interpretable. Prespecified stress tests can add noisy, partial, missing, or censored confirmations, and a separate query policy may pay explicit query cost and delay.

For the primary causal comparison, use a deterministic window-reset detector with no carried recurrent state, organize updates into fixed candidate cohorts, and allow only one unresolved provisional cohort at a time. Select each primary cohort by a frozen causal rule independently of the adapted trajectory. Before applying it, snapshot every mutable detector/update component that can affect later outputs: weights, optimizer and scheduler, scaler/normalizer, threshold, and any mutable model buffer. Keep the stream clock, raw observations, confirmation records, alarms/actions, exposure ledger, immutable candidate cohort, and wall-time counters outside the rollback transaction. Pending cohorts are inert storage and cannot influence scores or updates. The provisional arm applies the pinned update and uses the adapted model state for live predictions while confirmation is pending; because the detector resets its per-window state, restoring the model/update snapshot at the current stream time does not rewind runtime history or stale queues. If the cohort is certified safe, retain it; if any member is confirmed faulty or remains ambiguous at its declared deadline, restore the snapshot. The wait arm buffers the same candidate cohort, makes no update while pending, and applies the identical update only if the cohort is certified safe. This deliberately makes a mixed or uncertified cohort fail closed for both arms; per-sample adjudication is a secondary design only if separately specified. If a stateful/recurrent detector is later used, it needs a predeclared clean shadow/replay procedure over every intervening observation; restoring an old recurrent state alone is invalid.

Record alarms and operator-facing actions issued before rollback: state restoration cannot retract them. If provisional adaptation is evaluated only in shadow mode, it cannot claim earlier live adaptation benefit. Verify restoration by state equality where deterministic execution permits and by output parity on a frozen input suite. A rollback residual above the declared tolerance invalidates the reversible-policy result. Snapshot-only checks must cover every mutable state component that can influence subsequent decisions.

Enforce both a **cumulative episode cap** and an **outstanding provisional-influence cap** for unique windows, optimizer exposures, and live decisions. Historical exposure remains charged after rollback; rollback only clears outstanding influence. Before an update, reject the entire cohort if applying it would exceed either cap; do not partially truncate it. If the confirmation deadline or live-decision cap is reached unresolved, roll back immediately, mark the cohort rejected/censored, and continue in wait/frozen mode. Late confirmation is logged for evaluation and cannot retroactively change the model. Record pending-buffer size, but because pending storage is inert it does not count as model-update exposure; account for its memory and latency cost separately.

### Baselines and pairing

For the primary rollback-versus-wait comparison, pair the same stream episode, initial checkpoint, frozen candidate cohort, update operator, and evaluator suffix. Admission-gate baselines may select different cohorts; compare them under the same caps and report both their policy-level result and any candidate-matched diagnostic separately. Include:

1. frozen/no-adaptation;
2. wait for external cohort confirmation, then adapt on certified cohorts;
3. fixed dwell-time admission without semantic revalidation;
4. causal score-gated admission;
5. selective low-risk candidate admission with its rule frozen on development streams;
6. provisional live adaptation with exact rollback;
7. provisional live adaptation without rollback, as an exposure-risk ablation;
8. an oracle-clean cohort arm as an evaluator upper bound, never as an online policy.

The primary comparison is provisional-plus-rollback versus wait on the same candidate cohorts under equal prespecified cumulative/outstanding exposure caps and equal compute ceilings. The actual unverified exposure and actual work are policy outcomes and must be reported separately; rejected provisional updates still consume compute and historical exposure. Compare fixed dwell and score/selective gates under the same caps. Report candidate selection differences separately from timing differences. Include an equal-update-count replay diagnostic on the common accepted-cohort subset, clearly marked as a conditional diagnostic rather than the primary policy estimand. If a query action is introduced, price its cost and latency separately rather than hiding it in the wait arm.

Use development stream configurations to choose any score gate or update hyperparameters, validation configurations to freeze them, and untouched test configurations for the final paired comparison. Paired semantic worlds must share the entire observable prefix, including sensor and context values, confirmation absence/timing, candidate cohort, initial state, and coupled policy randomness. Keep paired semantic variants and all episodes from a shared generator configuration/family in the same split and inference cluster; independent episode seeds alone do not establish independent configurations. The sample size, resampling hierarchy, and power target must be set under P1's evaluation contract; overlapping windows and events are not independent n.

### Outcomes and decision rule

Report full tradeoff frontiers rather than one weighted score. At minimum measure:

- benign adaptation delay: time from known benign-shift onset to the first state that meets the prespecified benign false-alarm/recovery criterion;
- false promotion: fraction of fault-containing cohorts retained as normal; report admission of semantically ambiguous cohorts separately;
- cumulative unique-window, optimizer, raw-time, and component-specific unverified exposure (which rollback never erases), plus outstanding and residual influence after rollback;
- fault absorption: fault exposure retained in state and its effect on future fault recall, false alarms, and detection delay;
- alarm burden and missed detections issued while provisional state is active, before confirmation/rollback;
- post-confirmation detection quality on the same evaluator suffix, plus baseline-to-adapted difference;
- rollback residual in state and output space, restoration time, and recovery delay;
- compute, query, memory, and decision-latency cost; and censoring for never-confirmed or never-recovered episodes.

The final quality measures, event unit, margins, confidence intervals, multiplicity family, and required number of independent configurations must follow P1. The candidate primary estimand is whether provisional-plus-rollback reaches benign adaptation earlier than wait, under the same exposure caps and compute ceiling, while meeting both (a) P1-defined post-confirmation fault-detection/false-alarm limits and (b) a prespecified noninferiority bound on live pre-confirmation fault harm, such as missed-fault rate or detection delay. Do not replace this joint condition with lower adaptation delay or post-confirmation quality alone.

### Stop criteria

Stop or narrow the claim if any of these occur:

- the paired identical-prefix control shows a claimed pre-confirmation separation of benign and fault cases; this indicates leakage or an invalid information boundary;
- fixed dwell or score/selective admission matches the provisional-plus-rollback frontier within the P1-frozen margin;
- a provisional latency advantage disappears when candidate cohorts and compute ceilings are common, or is reported without the different realized exposure levels;
- the policy violates either exposure cap, erases historical exposure after rollback, or counts pending/rejected windows as committed success;
- full rollback does not restore state and outputs within the frozen tolerance;
- alarms and missed detections issued before rollback erase the benign-delay benefit under the declared operational costs;
- the policy breaches the P1-frozen noninferiority bound on live pre-confirmation fault harm;
- the result depends on oracle labels, event metadata, future context, or a test-selected gate;
- confirmation noise, missingness, or delay makes performance unacceptable at the prespecified stress level;
- support is limited to overlapping windows from a few streams rather than independent episodes/configurations.

If waiting lies on the same or better frontier, stop the rollback method claim. If rollback helps only when benign and fault observations are distinguishable, state that condition explicitly. If synthetic evidence is positive but no suitable confirmation provenance exists in real streams, report a controlled policy result only; do not claim deployment safety.

## Current authorization boundary

This document analyzes GitHub [issue #6](https://github.com/kuo1234/xlstm_anomaly/issues/6); it does not authorize implementation, simulation, training, dataset use, label inspection, or changes to M0 or M1. Current M0 records controlled H1 harm as STOP, natural harm as NOT_RUN, overall harm as UNRESOLVED, and H4a/H4b as LOCKED. M0 explicitly prohibits rollback, delay-plus-revalidation, learned adaptation gates, and new adaptation behavior. Any future P2 execution needs the P1 evaluation contract, a separate versioned protocol, a sealed data/configuration manifest, independent GO/STOP review, and authorization consistent with the research gates. P4 and P1 remain outstanding in the review sequence.

## Sources checked

- Project proposal: [GitHub issue #6](https://github.com/kuo1234/xlstm_anomaly/issues/6)
- [Drift2Act](https://arxiv.org/abs/2603.08578), [OWAD](https://www.ndss-symposium.org/ndss-paper/anomaly-detection-in-the-open-world-normality-shift-detection-explanation-and-adaptation/), [When Model Meets New Normals](https://doi.org/10.1609/aaai.v38i12.29210), and [RTTAD](https://arxiv.org/abs/2605.10242)
- [Continuous Test-time Domain Adaptation for Fault Detection](https://arxiv.org/abs/2406.06607), [CoTTA](https://openaccess.thecvf.com/content/CVPR2022/html/Wang_Continual_Test-Time_Domain_Adaptation_CVPR_2022_paper.html), [Selective TTA for Unsupervised Anomaly Detection](https://arxiv.org/abs/2410.03306), [METER](https://www.vldb.org/pvldb/vol17/p794-zhu.pdf), [pyTEP](https://doi.org/10.1016/j.softx.2022.101053), and [COSTEP](https://doi.org/10.1016/j.dche.2026.100328)
- Joulani, György & Szepesvári, [Online Learning under Delayed Feedback](https://proceedings.mlr.press/v28/joulani13.html)
- Project protocol boundary: [revised M0 protocol](../../reports/m0_protocol.md), [H1 status](../../reports/h1_status.json), and [M0 review](../../reports/m0_review.md)

## Astra review log

**Review 1: REVISE (gpt-6-astra), assessment only.** The reviewer required: compare policies under common exposure/compute caps while treating realized exposure and work as outcomes; define rollback at the current stream time and keep irreversible history outside the transaction; enforce cumulative and outstanding caps with deadline/overflow semantics; pair both semantic worlds on the complete observable prefix and cluster shared generator configurations; add a pre-confirmation fault-harm noninferiority guard; and correct METER's description/year. These revisions are incorporated above. This review authorizes no experiment.

**Review 2: PASS (gpt-6-astra), research/design assessment only.** The reviewer accepted the common-cap versus realized-exposure distinction, current-time rollback semantics, persistent accounting, full-prefix paired control and configuration-level clustering, and a pre-confirmation fault-harm guard. Exact parameters, update-state behavior, and inferential choices remain obligations for a separately reviewed protocol after P1. This PASS authorizes no implementation, data access, simulation, or experiment.
