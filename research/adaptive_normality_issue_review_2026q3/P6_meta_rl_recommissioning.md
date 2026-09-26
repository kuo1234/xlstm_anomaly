# P6 — Meta-RL for cross-machine detector recommissioning

Review status: research/design assessment only (2026-09-27). No controller, training run, simulation, dataset download, or label inspection is authorized or performed. P6 is a proposed later extension of P5, not an experiment currently permitted by M0.

## Decision

**Do not start with Meta-RL, and do not run P6 now.** The core idea is technically plausible, but its own prerequisite—a completed simple P5 recommissioning baseline—does not exist. Under the current project protocol, learned adaptation gates and new adaptation behavior are explicitly out of scope. A future P6 study therefore needs a separately authorized research protocol, an eligible sealed data manifest, and a completed P5 baseline before any simulator or dataset work.

The method-level novelty is low: Meta-RL for anomaly detection, RL detector selection, RL threshold control, and cross-machine meta-learning for industrial anomaly detection all have prior work. A narrower possible contribution is a **deployment controller** that uses only a held-out machine's verified-normal commissioning prefix to choose among frozen, bounded adaptation, and readiness actions, and demonstrably beats P5's simple rules on unseen entities. That gap is plausible, not established. It depends on showing that sequential choices change future commissioning state and that the gain transfers across machines or sites.

The first viable comparison should be fixed-N P5 versus score/threshold-stability heuristics. Add a contextual bandit only if source selection or another one-shot choice remains useful. Add sequential RL only if actions alter later model state or evidence. Add Meta-RL only if it improves over both a non-meta sequential policy and the best simple policy on fresh machines excluded from P5 development, policy development, and all stage-promotion decisions.

## Source proposal and interpretation

GitHub issue [#10](https://github.com/kuo1234/xlstm_anomaly/issues/10) proposes a policy over sequential deployment choices: collect more verified-normal data, keep a source detector frozen, adapt it, select a source model or temporal window, and declare `READY`. A machine/domain is one task. The policy may observe score and threshold stability, residual/loss trends, prefix-only source/target similarity, normal-data count, model/window choice, operating-mode coverage, recent adaptation gain, and adaptation cost. Any “adaptation gain” available to the policy must be a predeclared **normal-only surrogate** computed from data revealed so far; it cannot mean hidden anomaly-detection quality. Hidden future labels may shape reward on source-side training tasks, but must never enter controller observations or held-out target decisions.

One action-definition problem should be fixed before any design freeze: `KEEP_FROZEN` is not distinct from `COLLECT_MORE` if both reveal another batch while preserving the same detector. Use the smallest meaningful action set first:

- `COLLECT_NEXT_BATCH`: reveal the next fixed-size verified-normal batch and leave the detector unchanged;
- `ADAPT`: apply one predeclared, bounded update using only eligible fit-prefix data; it incurs compute and elapsed-time cost, and its effect is judged on a later, previously unused normal-only monitoring batch;
- `READY_EMPIRICAL`: stop commissioning, freeze the current model and threshold, and deploy for evaluator-only scoring.

Source-model choice and dynamic-window choice should remain ablations until the core action set has a measurable gap. A normal-only prefix can inform empirical readiness but cannot establish future anomaly recall. The `READY` name must be tied to the declared empirical normal-risk criterion; it must not imply a formal false-alarm guarantee unless P5's risk assumptions and repeated-look validity are proved.

## Feasibility and main risks

| Dimension | Assessment | Main reason |
|---|---|---|
| Algorithmic feasibility | Medium | Offline simulation and historical episodes can provide repeated sequential tasks; continuous online exploration on a real plant is inappropriate for initial research. |
| Data feasibility | Low/uncertain | Need multiple independent machines, verified-normal commissioning histories, chronological future outcomes, and enough held-out tasks. Public anomaly datasets often do not establish that an operator knew the prefix was normal when it was acquired. |
| Statistical feasibility | Low until task inventory is known | Thousands of windows do not replace a small number of independent machines/sites. Meta-RL estimates can be dominated by source-task reuse and policy search. |
| Incremental novelty | Low/conditional | Broad combinations already exist. The narrow recommissioning control objective may be novel, but no corpus-level novelty search has established that claim. |
| M0 compatibility | None for execution | M0 prohibits a learned adaptation gate and new adaptation behavior. Its locked H4/H5 branches do not authorize P6. |

The main scientific risk is that the proposed state is a collection of summaries and current choices, while the useful decision may be only a stopping rule. It is not established as a Markov state; unobserved operating modes and serial dependence can make the problem partially observable. If no action affects what data arrive, what model is active, or later scores, then this is not a meaningful sequential-control advantage: a calibrated stopping rule or contextual policy is simpler. If each decision does change the future state, the evaluation must compare against pooled RL trained from scratch and simple intervention schedules, not only a fixed detector.

Other risks are:

- **Normality is not stationarity.** A stable score or threshold over recent blocks does not establish that unseen future data are normal or that future false alarms are bounded.
- **Readiness cannot see recall.** Future anomaly labels may be evaluator outcomes in source-side offline learning, but cannot be used by the target policy, threshold selector, stopping rule, or test-set model selection.
- **Reward design can hide safety tradeoffs.** A weighted sum can trade a few false-ready events against sample savings. Define hard safety and quality constraints first; treat cost as the optimization target within those constraints.
- **Meta-task count may be inadequate.** Splitting one machine's periods into many tasks creates pseudo-replication. Entire physical machines must be held out; site/family holdout is needed for cross-domain claims.
- **Adaptation and threshold effects can be conflated.** Keep threshold-only recalibration separate from model-weight updates and report the frozen-source arm.
- **Repeated policy search can leak test information.** Test machine outcomes must be opened once after policy, actions, reward, and analysis are frozen.
- **Test-time task adaptation can leak through the reward channel.** A policy described as observation-only can still ingest hidden rewards through recurrent inputs, replay, gradients, or task embeddings. Define that channel explicitly and prohibit target hidden-suffix rewards and anomaly labels from every adaptation pathway.
- **Simulation can overstate transfer.** Simulated machine diversity supports method debugging, not evidence of real cross-site deployment.

## Prior work and feasible alternatives

| Work | Relevance to P6 | Consequence for claim/design |
|---|---|---|
| Chang, Tsai & Chen (2024), [Self-Adaptive Server Anomaly Detection Using Ensemble Meta-Reinforcement Learning](https://doi.org/10.3390/electronics13122348) | Applies model-agnostic meta-RL/TRPO to adapt an ensemble of HMM, VAE, TCN-AE and BiLSTM detectors across changing server-resource tasks. | Directly rules out “Meta-RL for anomaly detection” as the novelty. P6 must distinguish the deployment/recommissioning objective, verified-normal-only target interface, and cost/readiness constraints. |
| Zhang, Wu & Boulet (2022), [Time Series Anomaly Detection via Reinforcement Learning-Based Model Selection](https://doi.org/10.1109/CCECE49351.2022.9918216) | Uses RL to dynamically select among candidate anomaly detectors. | `SELECT_SOURCE_i` is not novel by itself. Include detector/source selection as a simple baseline or later ablation. |
| Yang, Howley & Schukat (published online 2024; 2025 volume), [Agent-based Dynamic Thresholding for Anomaly Detection](https://doi.org/10.1007/s00521-024-10536-0) and [CPS study](https://doi.org/10.1016/j.cose.2024.103825) | Models thresholding as an MDP and uses DQN to choose anomaly thresholds from score/environment summaries. | Threshold-control overlap is substantial; P6 must separate recommissioning readiness from dynamic threshold control and compare against a fixed threshold-stability rule. |
| Weiß et al. (2026), [Self-Adaptive Anomaly Detection with Reinforcement Learning and Human Feedback in Connected Vehicles](https://arxiv.org/abs/2607.08373) | A factorized DQN selects detectors across connected-vehicle microservices; drift alarms and human-triggered retraining close an online supervisory loop. | Close deployment-loop overlap. P6's differentiator would need to be held-out machine recommissioning from verified-normal-only prefixes without target labels or human retraining feedback. |
| McClement et al. (2021), [A Meta-Reinforcement Learning Approach to Process Control](https://arxiv.org/abs/2103.14060) | Meta-trains a process controller to adapt to new dynamics/objectives. | Industrial process meta-RL is prior art. Position P6 as anomaly-detector lifecycle control, not industrial Meta-RL generally. |
| Woo et al. (2025), [Meta-Learning-Based LSTM-Autoencoder for Low-Data Anomaly Detection in Retrofitted CNC Machine](https://doi.org/10.3390/systems13070534) | Uses multiple machines as meta-tasks for low-data adaptation to a retrofitted CNC machine. | Cross-machine meta-learning for anomaly detection exists without RL. The P6 question must be policy value over detector value. The study uses a small related-machine set and does not by itself validate P6's sequential verified-normal commissioning claim. |
| Dogru et al. (2024), [Reinforcement Learning in Process Industries: Review and Perspective](https://doi.org/10.1109/JAS.2024.124227) | Reviews RL across process control, fault detection, planning, and other industrial roles. | General industrial RL framing is crowded; claim only the specific recommissioning protocol and its evidence. |

Feasible alternatives, in increasing complexity:

1. **P5 fixed-N and simple rules:** frozen-source `N=0`, fixed commissioning budgets, threshold-only recalibration, score/threshold stability over `K` non-overlapping blocks, and a marginal-gain plateau. These are the primary comparators and may be sufficient.
2. **Supervised stopping or survival model:** train only on source development tasks to estimate a future-readiness event/cost curve. It is easier to fit and audit than RL, though it still needs source-side evaluator outcomes and strict target holdout.
3. **Contextual bandit:** choose a source or one preconfigured adaptation recipe from the current prefix when each choice has a one-step evaluation and does not affect later choices. Compare with random and fixed choice under equal information.
4. **Pooled sequential RL:** use when `ADAPT` or acquisition actions change future model/evidence state; compare with the same RL algorithm trained without meta-learning.
5. **Meta-RL:** consider only if there are enough independent source machines/tasks and adaptation to a held-out target is better than pooled RL, supervised stopping, and P5 rules at equal data, compute, and action budgets.

For window choice, separately compare fixed `W`, a target-specific `W*` chosen from training/commissioning data, and an online `W_t`. Do not include window, source, update-strength, threshold, and readiness choices in one large action space at the outset.

## Proposed gated study — only after authorization

### Gate 0: prerequisite and scope

1. Complete and report a P5 simple recommissioning baseline first. It must define its fixed-N and stability rules, acquisition cost, empirical readiness semantics, common future suffix, and never-ready accounting.
2. Separately authorize P6 in a versioned protocol. Current M0 has no authorization for a learned adaptation gate, P6 adaptation actions, simulator runs, or reuse of its locked branches. Do not change M0 or touch protected M1 work.
3. Perform a metadata-only eligibility audit, then seal data provenance, machine/site identities, verified-normal history, source/future cutoffs, checksums, event labels, and all task folds before model or label outcomes are examined.

If a data source cannot establish independently verified normal commissioning periods and evaluator-only later outcomes, downgrade the work to a synthetic or retrospective method study and do not call it real deployment recommissioning. Public-data leads from P5 (PreDist and CARE to Compare) require source-level review for this exact provenance question before selection.

### Gate 1: task construction and observation firewall

- A task is a complete physical machine/domain episode, not an arbitrary time-series window. Keep whole machines disjoint among policy/meta-train, policy-validation, and meta-test. Reserve at least one site/family for a cross-domain test only if the manifest supports it; otherwise restrict claims to unseen machines in the observed family.
- Keep all periods, products, faults, and overlapping windows from a machine within its assigned fold. Report task count by machine, site, and family. If independent machine count is too small for a held-out evaluation, stop the Meta-RL claim and report a P5 feasibility study instead.
- At target test time, expose only sequential batches from a timestamped verified-normal prefix and features causally computed from that prefix: score/threshold summaries, residual trend, operating-mode coverage observed so far, prefix-only source similarity, sample/time cost, selected model, and action history. No future suffix values, anomaly labels, event boundaries, or future-derived normalization may enter.
- Training reward on source tasks may use their sealed future evaluator labels to score a completed deployment trajectory. Such reward is an offline training signal, not a policy feature. Test-task labels remain sealed until all policy choices are frozen and are used once for final evaluation.
- For an admissible Meta-RL design, meta-train the controller on source-task trajectories, then freeze all policy weights before target evaluation. At a held-out target, task adaptation occurs only through recurrent/context state updated from causally observed normal-prefix features and previous actions; there are no target gradient updates, reward-conditioned state, replay, anomaly labels, or hidden-suffix reward. If a test-time normal-only reward proxy is used, define it before training and compute it only from revealed prefix data. Compare pooled and meta-trained policies with matched architecture, memory, data, optimizer/search budget, and target update opportunities.
- Freeze detector and policy separately. Include an always-frozen source detector and a threshold-only update arm so an apparent controller gain cannot be attributed ambiguously to the backbone or threshold.
- P5 design choices and any outcomes used to decide whether P6 should proceed count as development evidence. They cannot later be called an untouched P6 test. Reserve fresh machines/sites before those outcomes are opened; otherwise any reuse is exploratory. Choose all A→E promotions and controller variants on source development/validation machines only. Open the reserved meta-test set once, after the policy, action set, reward, and analysis are frozen.

### Gate 2: common episode protocol

For each held-out target, reveal verified-normal data in predeclared fixed-size batches. Preserve P5's fit, threshold-calibration, and risk-audit roles, and add a distinct adaptation-monitor role: a block is assigned once and never reused across roles. Every role contributes to commissioning cost, and `ADAPT` cannot use protected risk-audit blocks. A normal-only adaptation diagnostic must use a newly revealed monitor batch that is separate from the update's fit data, threshold calibration, and risk audit. Count every observation used for fitting, threshold calibration, risk audit, monitoring, or policy decisions as commissioning cost. Record both sample count and elapsed time. Every policy has a fixed `N_max` and a common evaluator suffix beginning after `N_max`; the controller cannot access any suffix data or labels.

At each reveal point, the policy chooses to collect another batch unchanged, perform one bounded predeclared adaptation, or stop as `READY_EMPIRICAL`. Each `ADAPT` consumes a fresh fit batch, a later normal-only monitor batch to assess a predeclared surrogate, elapsed time, and compute; do not permit repeated refitting on the same prefix without a new monitored transition. Cap the number of updates and cumulative compute/time per target in the sealed protocol. Once a cap is reached, mask `ADAPT`; the policy may collect within `N_max` or remain not-ready, but exhaustion never forces READY. Any threshold recalibration uses only its calibration role, and risk-audit blocks remain protected under the P5 repeated-look procedure. Freeze the exact detector, threshold, and state at stop. For a policy that never reaches READY, report failure for that target and its cost capped at `N_max`; for completeness, evaluate its final `N_max` state on the same common suffix as a secondary diagnostic, clearly marked as not-ready. Do not compute cost only over successful targets.

Use one common suffix for every arm on a target, regardless of `N_READY`. Evaluator-only labels on this suffix measure post-ready AP/AUPRC, event recall/F-score, normal FPR, false alarms per unit time, and detection delay. Any prefix contamination found by the evaluator is reported as a separate stress stratum; it is never sent to the policy. `READY_EMPIRICAL` only denotes the frozen empirical normal-risk rule. Formal risk certification is out of scope unless P5's repeated-look and dependence assumptions are independently justified.

### Gate 3: staged controller comparisons

Use the same source detector(s), target prefix, available features, and per-target sample/compute budget across arms. Select variants and promote or stop stages A→E using source development/validation outcomes only. The reserved meta-test machines/sites cannot inform stage promotion, action/reward revision, or controller selection; freeze the candidate policy family before opening those outcomes.

| Stage | Controller | Question / promotion condition |
|---|---|---|
| A | Fixed `N`, frozen source, threshold-only recalibration | Establish P5 commissioning and detector reference curves. |
| B | Score/threshold stability and marginal-gain heuristics | Is there a reproducible gap after matching the same normal-risk rule and future quality? |
| C | Contextual bandit or supervised stopping | Does current prefix context improve a one-step choice/stopping estimate at equal information? If this matches the heuristic, stop. |
| D | Sequential RL without meta-training | Do action-dependent transitions (especially `ADAPT`) provide value across a full episode beyond C? If actions do not change future state, stop here and do not call it sequential control. |
| E | Meta-RL across machines | Does task-level adaptation improve held-out-machine outcomes over D and C, without using target labels and under equal training/search budgets? Only this incremental result supports P6. |

Promote one stage at a time. Failure or inconclusive support at one stage does not justify skipping to a more complex controller. Report source-target choice and dynamic-window selection as separate later ablations.

### Objectives, analysis, and reporting

Separate deployable rules from offline study criteria. At target time, action masks and `READY_EMPIRICAL` eligibility may depend only on the revealed prefix, predeclared normal-only risk procedure, and available compute/data budgets. Hidden-suffix anomaly quality, false-ready status, and future normal FPR are evaluator outcomes; they cannot control target actions or certify recall. Source-task hidden outcomes may shape offline RL training rewards, and source development/validation outcomes may determine controller selection, but the reserved meta-test outcomes are opened once for final study success only. The offline promotion condition is that the policy meets predeclared normal-risk and post-ready quality limits, false-ready limits, and then reduces capped commissioning cost/delay against the P5 reference. These hard study-level constraints do not become observable target-time guarantees. If a scalar reward is needed by an RL algorithm, prespecify it from domain costs before outcomes, disclose each component, and provide sensitivity/Pareto results; never let a high cost saving compensate for a breached safety constraint.

Primary comparisons should be paired by held-out machine and use physical machine as the minimum cluster; site/family are higher-level clusters. Report every target, number of independent entities/sites, confidence intervals, all never-ready targets, and false-ready results over all eligible targets and conditional on READY. Bootstrap whole entities (and sites where enough exist), not windows or fault events independently. If there are too few independent clusters for useful intervals or a prespecified power target, report descriptive feasibility only and do not claim cross-machine Meta-RL superiority.

Report at least:

- target-normal observations and elapsed time to READY, cost capped at `N_max`, and never-ready fraction;
- false-ready rate over all eligible targets, empirical future normal FPR, and risk-rule coverage;
- hidden-suffix AP/AUPRC, event recall/F-score, false alarms per time, detection delay, and gap to the reference;
- negative-transfer frequency and magnitude, plus per-machine and per-family outcomes;
- adaptation compute, training/search budget, decision latency, and policy variance across seeds;
- policy value relative to fixed-N, heuristic, contextual/supervised, and pooled sequential-RL arms;
- separate frozen-source, threshold-only, and detector-update effects.

Never infer target anomaly recall from verified-normal prefixes. Report it only as a blinded evaluator outcome.

## Stop and kill criteria

Stop before any run if the P5 baseline is absent, the P6 protocol and data manifest are not separately authorized/sealed, verified-normal provenance cannot be established, or machine-level folds cannot be formed without leakage.

Kill the Meta-RL layer or narrow the claim if any of these hold:

- P5 heuristic or contextual/supervised stopping matches Meta-RL within the predeclared quality and cost margins;
- action choices do not alter future acquisition, detector state, or available evidence;
- pooled sequential RL performs as well as Meta-RL on held-out machines;
- Meta-RL's advantage disappears on a held-out site/family or is supported only by windows from a few machines;
- policy requires target anomaly labels, future samples, or retrospective event metadata;
- false-ready, normal-risk, or post-ready quality constraints fail even when data cost improves;
- controller gain is explained by detector or threshold choice and no controller benefit remains under matched backbones;
- adaptation adds cost or negative transfer without a predeclared improvement in the joint deployment outcome;
- dynamic-window action is no better than fixed or target-specific `W*` selection;
- synthetic results are the only positive evidence: retain a simulator methods result, but make no real deployment claim.

## Current recommendation and authorization boundary

P6 is **conditional research, not GO for execution**. First complete a separately authorized P5 baseline; then verify a data source can support machine-disjoint episodes with prospective/independent normal-prefix provenance and hidden future labels. If P5 rules already meet the target, close P6 without Meta-RL. If a sequential gap remains and actions genuinely change future state, compare contextual and pooled sequential methods before meta-training.

M0 remains unchanged. Its explicit prohibition on learned adaptation gates and new adaptation behavior directly excludes P6 execution under the current protocol. The M0 H4a/H4b branches are still locked pending H1-harm, H5 requires H1-harm and H4a, and none of these conditions authorizes P6. This document only analyzes the proposal; it does not run a simulator, train a controller, inspect labels, authorize data use, or alter M1.

## Sources checked

- [GitHub issue #10: P6 proposal](https://github.com/kuo1234/xlstm_anomaly/issues/10)
- Chang, Tsai & Chen (2024), [Self-Adaptive Server Anomaly Detection Using Ensemble Meta-Reinforcement Learning](https://doi.org/10.3390/electronics13122348)
- Zhang, Wu & Boulet (2022), [Time Series Anomaly Detection via Reinforcement Learning-Based Model Selection](https://doi.org/10.1109/CCECE49351.2022.9918216); [arXiv version](https://arxiv.org/abs/2205.09884)
- Yang, Howley & Schukat (published online 2024; 2025 volume), [Agent-based Dynamic Thresholding](https://doi.org/10.1007/s00521-024-10536-0); [CPS study](https://doi.org/10.1016/j.cose.2024.103825)
- Weiß et al. (2026), [Self-Adaptive Anomaly Detection with Reinforcement Learning and Human Feedback in Connected Vehicles](https://arxiv.org/abs/2607.08373)
- McClement et al. (2021), [A Meta-Reinforcement Learning Approach to Process Control](https://doi.org/10.1016/j.ifacol.2021.08.321). Preprint: [arXiv:2103.14060](https://arxiv.org/abs/2103.14060)
- Woo et al. (2025), [Meta-Learning-Based LSTM-Autoencoder for Low-Data Anomaly Detection in Retrofitted CNC Machine](https://doi.org/10.3390/systems13070534)
- Dogru et al. (2024), [Reinforcement Learning in Process Industries: Review and Perspective](https://doi.org/10.1109/JAS.2024.124227)
- P5 prerequisite: [P5 commissioning review](P5_commissioning.md)
- Protocol boundary: [revised M0 protocol](../../reports/m0_protocol.md) and [H1 status](../../reports/h1_status.json)

## Astra review log

**Review 1: `REVISE` (gpt-6-astra).** The reviewer required: an explicit target-time meta-adaptation channel with all hidden target rewards excluded; finite adaptation/update/compute limits and P5 role separation; fresh P6 test machines not used in P5 or stage selection; and a separation between prefix-observable deployment rules and evaluator-only future quality/safety criteria. These changes are included above.

**Review 2: `PASS` (gpt-6-astra), literature/design assessment only.** The reviewer accepted the clarified recurrent-state-only target adaptation, bounded `ADAPT` transitions, P5 audit separation, fresh meta-test holdout, and division between deployable rules and evaluator-only criteria. Exact meta-training objective and pooled-RL comparator remain for a future execution protocol. This PASS authorizes no experiment, dataset access, or M0/M1 change.
