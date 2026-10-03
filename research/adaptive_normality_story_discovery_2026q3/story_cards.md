# Story cards

Each card follows the requested schema. The status labels are `STRONG_CANDIDATE`, `PROMISING_BUT_THREATENED`, `WEAK / COMPONENT_ONLY` and `ALREADY_OCCUPIED`. No numeric scores are used. Evidence levels (full text, abstract, metadata only) for every cited record are listed in [papers.json](papers.json). Several decisive threats were read only at abstract level. Where a status depends on one of them, the card says so.

Part I covers the eight requested stories (A–H) and seven gap-derived stories (N1–N7). Part II merges the survivors into five programme stories (P1–P5), which are the ones carried into [recommended_research_program.md](recommended_research_program.md).

---

## Part I: Requested and discovered stories

### Story A: Reversible normality lifecycle

**Problem.** Given an unsupervised stream and no online oracle, does explicit `confirmed → quarantine → candidate → promoted → inactive → reactivated / rollback` state management reach a better point on the fault-absorption versus benign-adaptation-delay frontier than immediate or selective adaptation, *beyond what a single delay parameter provides*?

**Closest prior art.** [Park et al. 2025](https://doi.org/10.1145/3746252.3761481) (candidate patterns, active/inactive status, admission criteria, reactivation); [Li et al. 2024a](https://doi.org/10.1016/j.datak.2024.102365) (STAD: maps each stream period to a state and adapts through state transitions); [Zhu et al. 2024](https://doi.org/10.14778/3636218.3636233) (evidential "unknown" state and deferred window update); [Le et al. 2026](https://doi.org/10.1145/3744255.3811742) (buffer, persistence criterion, selective contamination-free update, reports contamination rate); [Qin et al. 2026](https://arxiv.org/abs/2604.08059) (seven-stage candidate → sandbox → shadow → gated activation → monitor → rollback → audit pipeline, non-TSAD); [Aftab et al. 2026](https://arxiv.org/abs/2607.02687) (provisional activation committed only if macro-F1 is preserved, else rollback; supervised IDS).

**What is already known.** Every lifecycle state has a published precedent. Candidate admission and reactivation are in AnDri, and state libraries with transitions are in STAD. Deferral is in METER, and buffered selective update with a contamination rate is in the e-Energy system. Staged activation with rollback and an unsafe-activation-versus-success trade-off has been measured for versioned AI components: naive upgrades reached 60% unsafe activation, while governed upgrades had none at slightly lower task success ([Qin et al. 2026](https://arxiv.org/abs/2604.08059)). Version control with post-exposure counterfactual rollback exists for LLM agent memory ([Su et al. 2026](https://arxiv.org/abs/2607.27773)). Protected per-regime banks exist in image AD ([Fang et al. 2026](https://doi.org/10.1016/j.neucom.2026.135021)).

**Residual gap.** All rollback-capable systems above decide commit or rollback with an online validation signal: macro-F1, injected known-faulty candidates, or labeled anchors. Unsupervised TSAD has no such signal. The open question is whether *reversibility* has measurable value when the only rollback trigger is delayed, partial external evidence. The alternative is that all benefit comes from waiting, as with quarantine. This question is unanswered for TSAD.

**Proposed contribution.** A controlled test of whether optimistic promotion with versioned rollback dominates pessimistic quarantine as a function of confirmation latency, in unsupervised TSAD.

**Falsifiable claim.** At a fixed time-integrated amount of unconfirmed promoted influence, optimistic promotion with versioned rollback gives strictly lower benign adaptation delay than quarantine-then-promote whenever confirmation latency is below a threshold that the experiment estimates. Above that threshold, quarantine dominates.

**Minimum experiment.** Four policies on streams with evaluator-side truth: immediate update, fixed-dwell quarantine, optimistic promote plus rollback, and no adaptation. Sweep dwell, confirmation latency L and confirmation coverage c. Report the frontier of fault-absorbed time against benign false-alarm time, plus residual contamination after rollback.

**Required datasets.** Controlled synthetic streams with benign A→B, A→B→A, persistent fault and observationally equivalent pairs; existing datasets are not sufficient on their own (see [dataset_requirements.md](dataset_requirements.md)).

**Main baseline threats.** AnDri-style candidate admission, METER-style deferral, STAD-style state transitions, e-Energy-style selective update, and a single-knob dwell baseline.

**Kill criterion.** Abandon the lifecycle as a contribution if, at every tested latency L, a dwell-only baseline tuned to the same false-alarm budget reproduces the lifecycle frontier within the pre-registered margin. That result would mean reversibility adds nothing beyond delay.

**Novelty confidence.** `PROMISING_BUT_THREATENED` only in the reversibility-versus-delay form above. As a new lifecycle mechanism the story is `WEAK / COMPONENT_ONLY`.

**Kind of novelty.** New decision/risk formulation; state-management mechanism (not new by container). Not an architecture.

---

### Story B: Adaptation as a risk-constrained decision

**Problem.** Can streaming TSAD adaptation be posed as minimising benign adaptation delay subject to a certified bound on fault absorption? If a label-free guarantee on false promotion is impossible, which quantity can be certified instead?

**Closest prior art.** [Schirmer et al. 2025](https://doi.org/10.52202/085713-2705) (sequential risk monitoring of a model under TTA without test labels); [Amoukou et al. 2024](https://doi.org/10.52202/079017-4107) and [Podkopaev & Ramdas 2021](https://arxiv.org/abs/2110.06177) (sequential harmful-shift detection); [Prinster et al. 2025](https://arxiv.org/abs/2505.04608) (weighted conformal test martingales that adapt to mild shift and flag harmful shift); [Angelopoulos et al. 2022](https://arxiv.org/abs/2208.02814) and [Hultberg et al. 2026](https://arxiv.org/abs/2602.04364) (conformal and anytime-valid risk control); [Wang et al. 2026a](https://arxiv.org/abs/2609.20700) (per-case adapt/skip router that reduces a "harmful accepted area"); [Kloft & Laskov 2012](https://arxiv.org/abs/1003.0078) (bounded-contamination analysis of online centroid AD); [Han & Qu 2026](https://arxiv.org/abs/2608.30502) (anytime-valid gating of online updates fires on 135/135 clean real streams).

**What is already known.** The statistical machinery is mature: conformal risk control, anytime-valid confidence sequences and weighted conformal martingales. It has been attached to adapting models ([Schirmer et al. 2025](https://doi.org/10.52202/085713-2705)) and used to route adaptation per case under a harm measure ([Wang et al. 2026a](https://arxiv.org/abs/2609.20700)). Contamination-rate reporting exists in drift-aware TSAD ([Le et al. 2026](https://doi.org/10.1145/3744255.3811742)), and budgets on retraining cost exist ([Mahadevan & Mathioudakis 2024](https://doi.org/10.1016/j.knosys.2024.111610), [Piaseczny et al. 2025](https://arxiv.org/abs/2505.24149)). In real TSAD streams, the off-the-shelf anytime-valid route has a documented failure mode ([Han & Qu 2026](https://arxiv.org/abs/2608.30502)).

**Residual gap.** Label-free monitors certify a proxy risk, not a semantic one. The project's identifiability boundary implies that no label-free rule can bound the rate at which persistent faults are promoted on the observationally equivalent stratum, except by abstaining there. No located TSAD paper (i) states this impossibility for adaptation, or (ii) replaces false-promotion control with a certifiable quantity such as *time-integrated unconfirmed influence on the persistent normal model*, controlled with delayed confirmation.

**Proposed contribution.** A risk formulation of TSAD adaptation that budgets unverified influence on persistent normality, together with the impossibility result that motivates it and an achievability result under delayed confirmation.

**Falsifiable claim.** A policy with an exposure budget of β achieves its budget exactly (deterministic accounting) and has lower benign delay than a false-promotion-calibrated conformal gate at matched realised fault absorption on streams with delayed confirmation. Separately, every label-free gate's false-promotion rate on the equivalent stratum is at least the prior-weighted floor implied by the identifiability theorem.

**Minimum experiment.** On P1-style streams (see Part II), compare exposure-budget policies with a conformal/anytime-valid gate, M2N2-style masking and no adaptation, sweeping budget and confirmation latency.

**Required datasets.** Synthetic streams with an equivalent stratum and a delayed-confirmation channel. The e-Energy smart-building data serve as a partial real check (normal / normal-drift / attack labels).

**Main baseline threats.** Schirmer et al.; WATCH; the Wang et al. router; the e-Energy selective updater; and Kloft & Laskov's contamination analysis, which reviewers will cite as the adversarial special case.

**Kill criterion.** Drop the formulation if a standard conformal or anytime-valid gate calibrated on clean data already keeps realised fault absorption within budget on the equivalent stratum (contradicting the theory, which would indicate a generator defect), or if exposure budgeting never improves benign delay at matched absorption.

**Novelty confidence.** `PROMISING_BUT_THREATENED`.

**Kind of novelty.** New decision/risk formulation; new theoretical result (impossibility + achievability).

---

### Story C: Detectability-aware adaptation (`ADAPT / FREEZE / UNRESOLVED`)

**Problem.** Can a streaming detector output `UNRESOLVED` exactly when current evidence cannot separate benign-new-normal from persistent-fault hypotheses? Does a three-way output outperform binary adapt/skip rules?

**Closest prior art.** [Jiang et al. 2026](https://arxiv.org/abs/2609.08367) (introduces "selective adaptation": decide per sample whether to adapt or skip); [Wang et al. 2026a](https://arxiv.org/abs/2609.20700) (per-case adapt/skip under a harm measure); [Majumdar & Saha 2026](https://arxiv.org/abs/2608.22233) (condition-level help/harm/inactive taxonomy); [Solozobov 2026](https://arxiv.org/abs/2604.15740) (evidence-sufficiency and decision-readiness gate under delayed ground truth); [Zhu et al. 2024](https://doi.org/10.14778/3636218.3636233) (explicit unknown state); [Chow 1970](https://doi.org/10.1109/tit.1970.1054406), [Geifman & El-Yaniv 2017](https://arxiv.org/abs/1705.08500) and [Sobel & Wald 1949](https://doi.org/10.1214/aoms/1177729944) (reject option and three-decision sequential tests).

**What is already known.** "Should this be adapted?" was posed three times in the six weeks before the cutoff ([Majumdar & Saha 2026](https://arxiv.org/abs/2608.22233), [Jiang et al. 2026](https://arxiv.org/abs/2609.08367), [Wang et al. 2026a](https://arxiv.org/abs/2609.20700)), all in vision or segmentation TTA. Abstention with a third output is classical ([Chow 1970](https://doi.org/10.1109/tit.1970.1054406)) and deployed ([Shashikumar et al. 2021](https://doi.org/10.1038/s41746-021-00504-6)). Evidence-sufficiency gating with explicit blind spots per drift type exists for delayed-label risk systems ([Solozobov 2026](https://arxiv.org/abs/2604.15740)). A title-level future-issue lead ([Yang 2026](https://doi.org/10.1016/j.asoc.2026.116360)) claims that representation stability does not imply detectability for frozen time-series foundation models. That is the very premise this story was going to motivate.

**Residual gap.** Whether a hypothesis pair is identifiable is a property of the hypothesis classes, not of one data segment. `UNRESOLVED` can therefore be computed only relative to a declared library of benign modes and fault signatures, as a composite three-decision sequential test. What remains is to give `UNRESOLVED` decision-theoretic meaning (it triggers waiting, querying or probing, with bounded duration) in streaming TSAD. That is a component of Story B, not a standalone formulation.

**Proposed contribution.** An indifference-zone three-decision test whose `UNRESOLVED` state has a bounded expected duration and triggers information acquisition, used as the action space of the P2 policy.

**Falsifiable claim.** On streams where the equivalent stratum is known to the evaluator, the rate of `UNRESOLVED` verdicts is at least X times higher on equivalent pairs than on separable pairs, at matched overall abstention. Forcing a binary decision at `UNRESOLVED` steps increases fault absorption by more than the pre-registered margin.

**Minimum experiment.** Same streams as P1; compare the three-way test with the Jiang et al.-style skip rule, METER-style unknown and a binary conformal gate.

**Required datasets.** Synthetic equivalent/separable strata are required, because real data never label identifiability.

**Main baseline threats.** Jiang et al.; Wang et al.; METER; Solozobov; classical Sobel–Wald tests.

**Kill criterion.** Abandon as a separate story if `UNRESOLVED` does not concentrate on the equivalent stratum, or if replacing it with `FREEZE` changes neither absorption nor delay.

**Novelty confidence.** `WEAK / COMPONENT_ONLY` as a standalone story; it survives as P2's action space.

**Kind of novelty.** Decision formulation (component).

---

### Story D: Context-authorized normality

**Problem.** When trusted external context exists (setpoints, operating mode, recipe, workload, maintenance, operator confirmation), can promotion be restricted to the part of a shift that the authorised context explains? Can faults that coincide with authorised changes still be detected?

**Closest prior art.** [Song et al. 2007](https://doi.org/10.1109/tkde.2007.1009) (conditional AD: context attributes condition the expected behaviour); recipe-conditioned reference models ([Lane et al. 2001](https://doi.org/10.1016/s0959-1524%2899%2900063-3)); [Le et al. 2026](https://doi.org/10.1145/3744255.3811742) (setpoint- and occupancy-driven drift separated from attacks, 100 labeled anchors per class); [Choi et al. 2018](https://doi.org/10.1145/3243734.3243752) (commanded inputs as ground truth for physical invariants); digital-twin residual monitoring ([Gao et al. 2021](https://doi.org/10.1145/3450267.3450533)) and batch-versus-incremental twin updates under drift ([Abdoune et al. 2026](https://doi.org/10.1016/j.eswa.2025.130062), metadata only); [Lotto et al. 2026](https://arxiv.org/abs/2609.28170) (separates telemetry visibility, estimator influence and state-changing authority); [Bosch environment/system anomaly patent (US 11,686,651)](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11686651) (a context-plausibility model gates a context-conditioned system model).

**What is already known.** Conditioning scores on context is a 20-year-old subfield. Selecting reference models from recipe or mode metadata is standard multimode process monitoring. Using commanded inputs as ground truth is standard control-invariant attack detection. The CPS zero-trust architecture of [Lotto et al. 2026](https://arxiv.org/abs/2609.28170) already separates *seeing* an observation from letting it *influence* an estimator, which conceptually is quarantine with authorisation. Human-in-the-loop edits of an AD normal memory exist ([Abbas et al. 2026](https://arxiv.org/abs/2608.17775), [Deng et al. 2024](https://arxiv.org/abs/2405.03234)).

**Residual gap.** If trusted context fully separates the hypotheses, "promote iff authorised" is trivial. The non-trivial and unevaluated cases are (i) *authorisation scope*: an authorised change explains only part of the observed shift, and a fault can coincide with it; (ii) *novel context*: a new setpoint or recipe for which the conditional model has no support; (iii) delayed, partial or untrusted context. No located TSAD work measures coincident-fault absorption under authorised changes.

**Proposed contribution.** Authorization-scoped promotion: only the context-explained component of a shift enters persistent normality, and the unexplained residual stays under detection, evaluated by coincident-fault absorption.

**Falsifiable claim.** At matched benign false-alarm time, scoped promotion absorbs fewer faults injected at authorised change points than both "promote iff authorised" and context-conditioned scoring without gating.

**Minimum experiment.** Semi-synthetic coincident faults at documented setpoint or mode changes: the extended TEP simulator, the e-Energy setpoint schedule, or synthetic streams with a context channel. Four arms: statistical-only, conditional scoring, authorised-gate, scoped promotion.

**Required datasets.** Authorisation events with timestamps plus coincident faults. No public dataset provides both. TEP can simulate them; e-Energy has setpoint semantics but its licence and event IDs are unresolved.

**Main baseline threats.** Conditional AD; digital-twin residual monitors; control-invariant detectors; the e-Energy selective updater; SA-ZT-style influence mediation.

**Kill criterion.** Stop if "promote iff authorised" or conditional scoring matches scoped promotion on coincident-fault absorption, or if no dataset or simulator yields authorisation events with coincident faults (feasibility kill).

**Novelty confidence.** `PROMISING_BUT_THREATENED`. It is best framed as hybrid process monitoring with authorisation scope, not as semantic identification or security.

**Kind of novelty.** New scientific problem formulation (authorisation scope, coincident faults); new evaluation methodology.

---

### Story E: Recurrence without forgetting

**Problem.** For recurring regimes A→B→A, can old normality be recovered without relearning while faults are kept out of persistent memory?

**Closest prior art.** [Li et al. 2026b](https://doi.org/10.1016/j.knosys.2026.116530) (unsupervised TSAD pool that classifies sudden, incremental and recurrent drift, with a bounded pool, and explicitly targets overwriting of recurring regimes); [Yoon et al. 2022](https://doi.org/10.1145/3534678.3539348) and its extensions ([Li et al. 2024b](https://doi.org/10.1109/cac63892.2024.10865256), [Ma et al. 2024](https://doi.org/10.1109/msn63567.2024.00054), [Liu et al. 2025b](https://doi.org/10.1109/smartiot66867.2025.00068), [Li et al. 2025c](https://doi.org/10.1109/isctis65944.2025.11066053)); [Park et al. 2025](https://doi.org/10.1145/3746252.3761481) (pattern reactivation); [Smendowski et al. 2026](https://doi.org/10.1007/s10723-026-09846-5) (Selective Temporal Replay with novelty-gated admission and retention-aware replacement; the only strategy with positive backward transfer on all four datasets); [Faber et al. 2026](https://arxiv.org/abs/2607.18289) (continual-AD scenario taxonomy including recurring regimes); [Museba et al. 2021](https://doi.org/10.1155/2021/5533777) (recurring-concept ensembles).

**What is already known.** Store, do not retrain, and reactivate on recurrence is solved at the mechanism level in supervised recurring-drift learning and, since 2022, in unsupervised streaming AD. ADAPTS (online 2026-06, issue 2026-09) names the exact failure mode.

**Residual gap.** None of the pool papers located measures *pool contamination*: a fault admitted as a "recurring regime" that later makes reuse unsafe. None tests A→B→A where B was ambiguous and had to be held back. That residual is an evaluation axis, not a new mechanism.

**Proposed contribution.** None standalone. Fold "fault-days in pool" and "A→B→A recovery with a contaminated B" into P1 as evaluation axes.

**Falsifiable claim.** An explicit admission margin on the pool lowers fault-days-in-pool against ADAPTS/ARCUS-style reliability gating at matched recurrence recall.

**Minimum experiment.** A P1 recurrence scenario with adversarially timed fault regimes that mimic recurrence.

**Required datasets.** Synthetic recurrence with labeled B type; NAB or other ADAPTS benchmarks for sanity.

**Main baseline threats.** ADAPTS; ARCUS lineage; AnDri; Selective Temporal Replay.

**Kill criterion.** Already met for the mechanism story. For the evaluation axis: drop it if ADAPTS-style gating shows the same fault-days-in-pool as an admission-margin variant.

**Novelty confidence.** `ALREADY_OCCUPIED`.

---

### Story F: Normal-only rapid commissioning

**Problem.** With source-trained normal dynamics, how much verified target-normal data does a new machine need before its detector matches the full-data detector, and when can commissioning be declared complete?

**Closest prior art.** [Holly et al. 2025](https://arxiv.org/abs/2501.13052) (one-class domain adaptation via meta-learning: "rapid adaptation using normal operational data"); [Frikha et al. 2021](https://arxiv.org/abs/2007.04146) (few-shot one-class meta-learning); [Roelofs et al. 2024](https://arxiv.org/abs/2404.03011) and [Jonas & Meyer 2025](https://arxiv.org/abs/2504.17709) (wind-turbine normal-behaviour transfer with shrinking target data; the generative mapping beats fine-tuning from 1 to 8 weeks); [Shentu et al. 2025](https://arxiv.org/abs/2405.15273), [Lan et al. 2025](https://arxiv.org/abs/2509.21190) and [Ekambaram et al. 2025](https://arxiv.org/abs/2505.13033) (zero-shot TSAD); [Darban et al. 2025](https://doi.org/10.1109/tkde.2025.3569909) and [Ragab et al. 2023](https://doi.org/10.1145/3580305.3599507) (domain and source-free adaptation); [One-liners paper (ICLR 2026)](https://openreview.net/forum?id=H27kvyG4qf) (foundation models do not beat one-liner baselines).

**What is already known.** Few-shot normal-only adaptation, cross-machine transfer with sample-efficiency curves, zero-shot foundation detectors and source-free adaptation all exist. The K = 0 limit is served by DADA, TSPulse and Time-RCD, and one-liners are a mandatory sanity baseline.

**Residual gap.** No standard protocol compares these families on one held-out-entity curve (target-normal amount on the x-axis, with zero-shot and one-liner reference lines). No located work gives a *stopping rule* that certifies a target false-alarm rate from a verified-normal prefix under temporal dependence.

**Proposed contribution.** A held-out-entity commissioning protocol with a certified-false-alarm stopping rule, evaluated across at least two entity families.

**Falsifiable claim.** Source-pretrained normal models reach the full-target-data detection level with at least k-fold less verified-normal data than target-only training, and beat zero-shot and one-liner baselines at that amount, on at least two entity families.

**Minimum experiment.** SMD leave-one-machine-out (same D = 38) plus one external family, varying the prefix length; baselines are zero-shot FMs, one-liners, OC-MAML-style meta-learning, fine-tuning and target-only training.

**Required datasets.** SMD is usable but exploratory, because label-exposure provenance is compromised (Issue #4). A confirmatory family is needed, for example PreDist substations or a public wind-turbine SCADA fleet.

**Main baseline threats.** DADA/TSPulse/Time-RCD; OC-DA MAML; wind-turbine transfer; one-liners.

**Kill criterion.** Abandon if a zero-shot FM or a one-liner is within the pre-registered margin of source-pretrained adaptation at the shortest tested prefix on both families.

**Novelty confidence.** `ALREADY_OCCUPIED` as a method. `PROMISING_BUT_THREATENED` as an evaluation-protocol and stopping-rule paper (P5).

**Kind of novelty.** New evaluation methodology; possibly a small theoretical result (effective-sample-size stopping rule).

---

### Story G: Semantic-shift benchmark

**Problem.** Is there room for a benchmark that scores *adaptation decisions* (benign A→B, A→B→A, transient anomaly, persistent predictable fault, false promotion, contamination, recovery, context availability) rather than point-level anomaly accuracy?

**Closest prior art.** [Cao et al. 2024](https://doi.org/10.1007/s10462-024-10995-w) (SCAR generator with customisable anomalies and drifts, 76 synthesised datasets, 13 algorithms); [Li et al. 2024a](https://doi.org/10.1016/j.datak.2024.102365) (synthetic streams with separately labeled drift and anomaly positions); [Jacob et al. 2020](https://arxiv.org/abs/2010.05073) (root-cause plus extended-effect intervals); [Liu & Paparrizos 2024b](https://doi.org/10.52202/079017-3437) (TSB-AD); [Dragoi et al. 2022b](https://arxiv.org/abs/2206.15476); [Faber et al. 2026](https://arxiv.org/abs/2607.18289) (continual-AD scenarios). On the name "StrAD": two independent passes did not locate a streaming-TSAD benchmark with that name. The only hits were an audio-description benchmark (arXiv 2608.12549) and a structural-similarity TSAD method (arXiv 2509.20184).

**What is already known.** Drift-plus-anomaly generators exist (SCAR, STAD, [Michailoudis et al. 2026](https://doi.org/10.1016/j.softx.2026.102995), GutenTAG/TimeEval). Recovery intervals exist in Exathlon. Label-quality critiques are mature (TSB-AD, [Kim et al. 2022](https://doi.org/10.1609/aaai.v36i7.20680), [Wagner et al. 2025](https://arxiv.org/abs/2510.17562), [Lyu 2026](https://arxiv.org/abs/2607.11969)).

**Residual gap.** No located benchmark (i) labels *promotion correctness*, (ii) contains strata that are observationally equivalent by construction, so the Bayes floor is known, or (iii) varies context availability and reliability as an experimental factor. The taxonomy-only version of G is threatened by SCAR/STAD extensions. The identifiability-stratified, decision-level version is not.

**Proposed contribution.** See P1.

**Falsifiable claim.** See P1.

**Minimum experiment.** See P1.

**Required datasets.** A new generator plus e-Energy and TEP as semi-real anchors.

**Main baseline threats.** SCAR; STAD; Exathlon; TSB-AD; the Faber et al. 2026 scenarios.

**Kill criterion.** Stop if the eight categories can be produced by a trivial parameterisation of SCAR or STAD and add no decision-level metric; that result makes G a note.

**Novelty confidence.** `PROMISING_BUT_THREATENED` as a broad taxonomy benchmark. `STRONG_CANDIDATE` in the identifiability-stratified form (P1).

**Kind of novelty.** New evaluation methodology; new dataset/benchmark.

---

### Story H: Resource-constrained continual TSAD

**Problem.** Can adaptation be optimised jointly for detection quality, retention, update frequency and energy?

**Closest prior art.** [Smendowski et al. 2026](https://doi.org/10.1007/s10723-026-09846-5) (evaluation protocol that jointly measures detection quality, retention and energy for concept-incremental TSAD; more than 5,400 experiments, including SMD); [Piaseczny et al. 2025](https://arxiv.org/abs/2505.24149) (drift-triggered updates under a resource budget, with guarantees); [Mahadevan & Mathioudakis 2024](https://doi.org/10.1016/j.knosys.2024.111610) and [Dasari 2026](https://arxiv.org/abs/2608.19488) (retraining schedules under cost); [Frederiksen et al. 2025](https://arxiv.org/abs/2512.13340) and [Marinova et al. 2026](https://arxiv.org/abs/2603.07507) (energy-aware IoT continual AD).

**What is already known.** Three of the four axes are jointly measured on TSAD (Smendowski et al., online 2026-09-01). The update-frequency axis is covered by retraining-schedule work.

**Residual gap.** Only a possible interaction between update frequency and retention remains.

**Proposed contribution.** None standalone.

**Falsifiable claim.** The energy-optimal update cadence changes when retention is scored.

**Minimum experiment.** Add a cadence sweep to the Smendowski et al. protocol.

**Required datasets.** Yahoo A1, SMD (as in the closest threat).

**Main baseline threats.** Selective Temporal Replay; RCCDA.

**Kill criterion.** No interaction effect beyond the pre-registered margin.

**Novelty confidence.** `ALREADY_OCCUPIED` (residual interaction: `WEAK / COMPONENT_ONLY`).

---

### Story N1: Promotion rules as an attack surface

**Gap logic.** Poisoning of online normality models is a mature literature ([Kloft & Laskov 2012](https://arxiv.org/abs/1003.0078), [Rubinstein et al. 2009a](https://doi.org/10.1145/1644893.1644895); ICS autoencoders in [Kravchik & Shabtai 2020](https://arxiv.org/abs/2002.02741) and [Kravchik et al. 2021](https://doi.org/10.1145/3412841.3441892); drift detectors in [Korycki Ł. & Krawczyk 2022](https://doi.org/10.1007/s10994-022-06177-w); TTA in [Cong et al. 2024](https://arxiv.org/abs/2308.08505)). The newer safe-adaptation designs (dwell, recurrence, coherence and admission margins in A/E) publish an *acceptance specification*. No located work measures how cheaply an adversary can meet that specification.

**Problem.** For a staged promotion rule with published dwell, recurrence or coherence criteria, what is the minimum attacker budget to get a chosen fault regime promoted, and does staging raise it relative to an online-retrained baseline?

**Closest prior art.** Kloft & Laskov; ANTIDOTE; Kravchik & Shabtai 2020 (SWaT autoencoders resisted all ten relevant attacks); Korycki & Krawczyk; TePA; [Abedzadeh & Bhattacharjee 2025](https://doi.org/10.3390/info16060428) (certified bounds under bounded-fraction poisoning).

**What is already known.** Bounded per-round poisoning can shift centroid and PCA detectors. Online-trained ICS autoencoders can be surprisingly resilient. TTA update rules can be attacked.

**Residual gap.** There is no attack-cost analysis of *staged* promotion rules, where the rule itself defines what the adversary must imitate.

**Proposed contribution.** Attack-cost curves and a bound for dwell and recurrence gates that extend the Kloft–Laskov analysis to staged promotion.

**Falsifiable claim.** For dwell-only gates, attack cost grows at most linearly in dwell. Adding an admission margin on the candidate's distance to confirmed regimes raises it super-linearly.

**Minimum experiment.** Synthetic plus SWaT-style streams; a white-box attacker against four gates; measure the budget until promotion.

**Required datasets.** Synthetic streams; SWaT/WADI under their access terms.

**Main baseline threats.** Kloft & Laskov (reviewers may see the result as a corollary); ANTIDOTE.

**Kill criterion.** Drop if staged gates show no budget advantage over one-shot retraining, which would make the result a restatement of known poisoning facts.

**Novelty confidence.** `PROMISING_BUT_THREATENED`. It works best as the adversarial section of P2.

**Kind of novelty.** New evaluation methodology; theoretical result (attack-cost bound).

---

### Story N2: Peer-corroborated normality (fleet evidence)

**Gap logic.** Boundary #4 allows identification with independent measurements. In a fleet, peer entities are independent measurements of common causes. Fleet baselines exist ([de Novaes Pires Leite et al. 2023](https://doi.org/10.1016/j.engappai.2023.106859), [Tveten et al. 2022](https://doi.org/10.1214/21-aoas1508), [Smith et al. 2024](https://arxiv.org/abs/2402.19295)), and 2009-era work used cross-site correlation to update anomaly sensors ([Stavrou et al. 2009](https://doi.org/10.1145/1654988.1655000)). None formalises when peer synchrony licenses *promotion*, or how many compromised peers break it.

**Problem.** Under a common-cause model of benign change and an idiosyncratic model of faults, when does simultaneous change across k of n peers make benign-versus-fault identifiable, and at what attacker-controlled fraction does this fail?

**Closest prior art.** Stavrou et al. 2009; Tveten et al. 2022; fleet wind-turbine AD; [Bera et al. 2026](https://arxiv.org/abs/2606.31789) (shared memory across entities, metadata only).

**What is already known.** Pooling across a fleet sharpens baselines, and cross-site correlation was used heuristically in intrusion detection.

**Residual gap.** No identifiability statement exists for peer-corroborated promotion, and there is no adversarial-fraction threshold.

**Proposed contribution.** An identifiability condition and a k-of-n promotion rule with an adversarial-fraction bound for fleet TSAD.

**Falsifiable claim.** With common-cause benign changes, k-of-n corroboration lowers false promotion against single-entity promotion at matched delay. The benefit vanishes above a derivable attacker fraction.

**Minimum experiment.** A synthetic fleet generator. Descriptive co-occurrence of shifts across SMD machine groups (label-free; no semantic claim). A real fleet with change logs if one can be acquired.

**Required datasets.** A real fleet with documented fleet-wide benign changes (software rollouts, seasonal) is not in hand.

**Main baseline threats.** Correlation voting; hierarchical Bayesian fleet models.

**Kill criterion.** Drop if the benefit disappears at attacker fractions of 10% or less, or if no fleet dataset with change documentation can be obtained.

**Novelty confidence.** `PROMISING_BUT_THREATENED`.

**Kind of novelty.** New problem formulation; theoretical result.

---

### Story N3: Interventional disambiguation (active probing)

**Gap logic.** Active fault diagnosis designs auxiliary inputs that make observationally equivalent hypotheses separable ([Nikoukhah & Campbell 2003](https://doi.org/10.23919/ecc.2003.7085087), [Wang et al. 2019](https://doi.org/10.1007/s12555-019-0182-6), [Wang et al. 2023](https://doi.org/10.1002/rnc.6660)). It has reached industrial AD only as offline data generation ([Wang et al. 2025b](https://doi.org/10.1016/j.engappai.2025.111991)). No located work uses probing to gate an online adaptation decision.

**Problem.** When passive observation leaves benign and fault hypotheses equivalent, is there a bounded-cost intervention that separates them before promotion?

**Closest prior art.** Nikoukhah & Campbell 2003; online auxiliary signal design; integrated AFD and control; artificial-fault-data generation for industrial AD.

**What is already known.** Auxiliary signal design restores identifiability for known plant models.

**Residual gap.** Application to black-box learned detectors and to the promotion decision.

**Proposed contribution.** A probe-or-wait policy for promotion on a controllable simulator.

**Falsifiable claim.** On TEP, a bounded probe cuts false promotion on the equivalent stratum to below the passive floor.

**Minimum experiment.** Extended TEP with actuator perturbations.

**Required datasets.** A controllable simulator only.

**Main baseline threats.** Classical AFD; reviewers will call it an application of AFD.

**Kill criterion.** Drop if the admissible probes in target domains violate safety or controllability assumptions, or if the result is a direct instance of AFD theory.

**Novelty confidence.** `WEAK / COMPONENT_ONLY` for TSAD. It is valuable as a remark in P2 (probing is one way out of `UNRESOLVED`).

---

### Story N4: Query-budgeted regime authorization

**Gap logic.** Active learning for anomalies queries *instances* ([Das et al. 2018](https://arxiv.org/abs/1809.06477), [Deep AD under labeling budget constraints (ICML 2023)](https://proceedings.mlr.press/v202/li23x/li23x.pdf), [Perini et al. 2023](https://arxiv.org/abs/2301.02909)). Verification latency is studied for stream classification ([Castellani et al. 2022](https://arxiv.org/abs/2204.06822)). A regime-level answer ("B is the new normal") covers a whole stretch of stream and has latency. No located work schedules such queries.

**Problem.** Under a query budget and verification latency, when should an operator be asked to confirm a candidate regime rather than an instance?

**Closest prior art.** Das et al. 2018; Perini et al. 2023; Castellani et al. 2022; [Deng et al. 2024](https://arxiv.org/abs/2405.03234).

**What is already known.** Budgeted instance-level feedback and latency-aware budget reallocation.

**Residual gap.** Regime-level queries with latency, interacting with quarantine exposure.

**Proposed contribution.** A regime-query policy as an action inside P2.

**Falsifiable claim.** Regime queries dominate instance queries in absorption–delay at an equal number of queries.

**Minimum experiment.** Simulated operator with latency L on P1 streams.

**Required datasets.** Synthetic; a real deployment log would be needed for external validity.

**Main baseline threats.** Castellani et al.; Perini et al.

**Kill criterion.** "Query once at each detected change point" is within margin of the optimised policy.

**Novelty confidence.** `PROMISING_BUT_THREATENED` (folded into P2/P3).

---

### Story N5: Retroactive decontamination (regime retraction versus rollback)

**Gap logic.** When delayed evidence reveals that a promoted regime was a fault, a system can either roll back to a checkpoint or unlearn the regime. Rollback discards legitimate later learning, while unlearning may leave residual contamination.

**Problem.** Can the influence of one retracted regime be removed while later legitimate learning is kept, with a bounded residual?

**Closest prior art.** [Du et al. 2019](https://doi.org/10.1145/3319535.3363226) (unlearning corrects a deep AD model when a false negative or false positive is labeled); [Artelt et al. 2022](https://arxiv.org/abs/2211.12989); [Machine unlearning for streaming forgetting (OpenReview 2024)](https://openreview.net/forum?id=bIoWuzFm6r); [Su et al. 2026](https://arxiv.org/abs/2607.27773) (post-exposure counterfactual rollback); [Kabashkin 2025](https://doi.org/10.3390/electronics14152968).

**What is already known.** Du et al. already correct *wrongly-normal* samples retroactively in lifelong AD, which is closer to this story than the discovery track suggested. Streaming unlearning is formalised. Counterfactual rollback evaluation exists for agent memory.

**Residual gap.** Retraction at the regime level for continuous-state detectors, with an entanglement cost measured against checkpoint rollback.

**Proposed contribution.** A retraction-versus-rollback comparison as the reversibility arm of P2.

**Falsifiable claim.** Regime retraction restores recall on the retracted fault class to within ε of the pre-promotion level while keeping ≥ (1−δ) of later benign adaptation, which rollback cannot.

**Minimum experiment.** Promote a fault regime, then retract it after latency L; compare rollback, unlearning and no correction.

**Required datasets.** Synthetic, with a delayed-relabel protocol.

**Main baseline threats.** Du et al.; checkpoint rollback.

**Kill criterion.** Retraction offers no retention advantage over rollback.

**Novelty confidence.** `PROMISING_BUT_THREATENED` (downgraded from the discovery track's `STRONG_CANDIDATE` after reading the Du et al. abstract).

---

### Story N6: Adaptation-induced masking (collateral detectability loss)

**Gap logic.** Contamination measures the absorbed fault itself. Masking is the loss of sensitivity to *other* faults that resemble an absorbed benign regime. Fault-versus-model-drift diagnosis ([Anzai & Pinto 2026](https://doi.org/10.3390/pr14050859)) shows that faults and mode shifts can have distinct contribution signatures. Continual-AD forgetting metrics ([Li et al. 2022](https://doi.org/10.1145/3503161.3548232), [Frikha et al. 2020](https://arxiv.org/abs/2008.04042)) are generic averages.

**Problem.** After adapting to a benign regime R, how much recall does a detector lose on a held-out fault class F whose observables resemble R?

**Closest prior art.** Anzai & Pinto 2026; continual-AD forgetting metrics; [Kim et al. 2024](https://doi.org/10.1609/aaai.v38i12.29210) (which acknowledges ambiguity between normality, anomaly and drift).

**What is already known.** Generic forgetting and fault-versus-drift diagnosis.

**Residual gap.** A paired (R, F) protocol that isolates post-adaptation detectability loss.

**Proposed contribution.** A masking metric within P1.

**Falsifiable claim.** Adaptive detectors lose significantly more recall on F after adapting to R than a frozen detector does.

**Minimum experiment.** Paired scenarios in the P1 generator.

**Required datasets.** Synthetic paired scenarios.

**Main baseline threats.** Reviewers may call it 1 − recall; the pairing protocol has to carry the novelty.

**Kill criterion.** No systematic loss across pairs.

**Novelty confidence.** `PROMISING_BUT_THREATENED` (as a P1 axis).

---

### Story N7: Contamination-blind evaluation

**Gap logic.** This story rests on an invalid common evaluation assumption. Under point adjustment (PA), a ground-truth anomaly segment counts as fully detected if any point in it is flagged. A detector that alarms at the onset of a persistent fault and then absorbs it into normality therefore loses nothing under PA-F1. Event-existence metrics behave the same way. PA's inflation of random scores is known ([Kim et al. 2022](https://doi.org/10.1609/aaai.v36i7.20680)), and metric-property work is active ([Wagner et al. 2025](https://arxiv.org/abs/2510.17562), [Lyu 2026](https://arxiv.org/abs/2607.11969), [Yang et al. 2025](https://arxiv.org/abs/2511.18739), [Velasco & Zafra 2026](https://doi.org/10.1016/j.neucom.2026.134154)). No located work analyses how metrics interact with *test-time adaptation*, where absorption is the failure of interest. Separately, delayed-label evaluation ([Grzenda et al. 2019](https://doi.org/10.1007/s10618-019-00654-y), [Ceschin et al. 2020](https://arxiv.org/abs/2010.16045)) and performative drift ([Gower-Winter et al. 2024](https://arxiv.org/abs/2412.10545)) show that streaming protocols overstate performance when their feedback assumptions are unrealistic.

**Problem.** Do standard TSAD metrics and protocols reward normality absorption, and do rankings of adaptive detectors change under absorption-aware scoring?

**Closest prior art.** Kim et al. 2022; Wagner et al. 2025 (LARM, 37 metrics); Lyu 2026; Grzenda et al. 2019; Ceschin et al. 2020; [Patra & Ben Taieb 2025](https://arxiv.org/abs/2510.21296) (test-time correction of models trained on contaminated data).

**What is already known.** PA is unreliable. Many metrics fail formal properties. Streaming evaluations with instant labels overstate performance.

**Residual gap.** No analysis of metric sensitivity to post-detection absorption. No re-scoring of published adaptive TSAD methods by contamination-aware criteria.

**Proposed contribution.** An analytic characterisation of which metrics are blind to absorption, and a re-scoring of adaptive detectors (see P1).

**Falsifiable claim.** Under PA-F1 and event-existence recall, an immediately adapting detector that absorbs persistent faults after the first alarm scores the same as a non-absorbing one. Point-wise AP and absorption-aware metrics separate them, and they reorder at least one pair of published adaptive methods.

**Minimum experiment.** A proof for the PA family, then re-scoring of 5–6 open-source adaptive detectors on P1 streams.

**Required datasets.** P1 streams; public TSAD benchmarks for reproduction.

**Main baseline threats.** LARM's property set, which may already contain an equivalent property; must be checked in full text.

**Kill criterion.** If LARM or TSADmetrics already define an absorption-sensitive property or metric, the analytic claim becomes a corollary. If rankings agree (Kendall τ ≥ 0.8 in every scenario family), the empirical claim fails.

**Novelty confidence.** `STRONG_CANDIDATE` (as part of P1).

**Kind of novelty.** New evaluation methodology; theoretical result (metric blindness proposition).

---

## Part II: Programme stories (merged survivors)

### P1: Identifiability-stratified, contamination-aware evaluation of adaptive TSAD

**Problem.** Can adaptive TSAD methods be evaluated so that information failure (the benign-versus-fault question is non-identifiable from X alone) is separated from method failure, and so that the harm of adaptation (absorption, masking, lost recovery) is scored directly instead of being hidden by point-level metrics?

**Merges.** G, N7, N6, E's residual axis, and the context-availability axis from D.

**Closest prior art.** [Cao et al. 2024](https://doi.org/10.1007/s10462-024-10995-w) (SCAR); [Li et al. 2024a](https://doi.org/10.1016/j.datak.2024.102365) (STAD); [Jacob et al. 2020](https://arxiv.org/abs/2010.05073); [Liu & Paparrizos 2024b](https://doi.org/10.52202/079017-3437) (TSB-AD); [Kim et al. 2022](https://doi.org/10.1609/aaai.v36i7.20680); [Wagner et al. 2025](https://arxiv.org/abs/2510.17562); [Faber et al. 2026](https://arxiv.org/abs/2607.18289); [Le et al. 2026](https://doi.org/10.1145/3744255.3811742) (real normal / normal-drift / attack labels).

**What is already known.** Drift-plus-anomaly generators, recovery intervals, metric critiques and continual-AD scenarios exist. Contamination rate has been reported once for a drift-aware detector.

**Residual gap.** No located benchmark has (a) strata that are equivalent by construction with a known Bayes floor, (b) decision-level labels for promotion correctness, absorption and recovery, (c) context availability and reliability as a factor, or (d) an analysis of which standard metrics are blind to absorption.

**Proposed contribution.** A benchmark and evaluation contract whose episodes are labeled by identifiability class (X-separable, separable only with context C, non-identifiable). It scores adaptation decisions with absorption, masking and recovery metrics, and it proves which standard metrics cannot see absorption.

**Falsifiable claim.** (i) On the non-identifiable stratum, no evaluated method beats the theoretical floor, which checks the generator. (ii) Method rankings under standard metrics (PA-F1, VUS-PR, AP) differ materially from rankings under absorption-aware metrics (Kendall τ < 0.8 in at least one scenario family).

**Minimum experiment.** A generator with six episode types and three identifiability strata, plus a context channel with reliability ρ ∈ {0, 0.5, 0.9, 1}. Evaluate 6–8 open-source detectors or policies on CPU: no adaptation, sliding-window retraining, MemStream, M2N2, ARCUS, ADAPTS if code is available, and a METER-like deferral. No project detector and no M1 artefact is needed.

**Required datasets.** A new generator, written independently of the protocol-frozen `m0.synthetic`, with e-Energy (once licensed) and TEP as semi-real anchors.

**Main baseline threats.** SCAR/STAD extensions; LARM property analysis; TSADmetrics.

**Kill criterion.** K1: rankings concordant (τ ≥ 0.8) in every family. K2: LARM or TSADmetrics already contain an absorption-sensitive property. K3: a suite of simple classifiers beats chance on the equivalent stratum by more than the pre-registered margin, meaning the generator leaks. K4: SCAR, STAD or e-Energy already provide promotion-correctness labels.

**Novelty confidence.** `STRONG_CANDIDATE`.

**Kind of novelty.** New evaluation methodology; new dataset/benchmark; new theoretical result (metric-blindness proposition; Bayes floor by construction).

### P2: Adaptation under a budget of unverified influence

**Problem.** With delayed and partial confirmation, which adaptation policy minimises benign delay subject to a budget on unconfirmed influence on persistent normality? When does reversibility (optimistic promotion plus rollback or retraction) beat waiting?

**Merges.** A, B, C, N4, N5 (N1 as adversarial evaluation, N3 as a remark).

**Closest prior art.** [Schirmer et al. 2025](https://doi.org/10.52202/085713-2705); [Wang et al. 2026a](https://arxiv.org/abs/2609.20700); [Jiang et al. 2026](https://arxiv.org/abs/2609.08367); [Prinster et al. 2025](https://arxiv.org/abs/2505.04608); [Han & Qu 2026](https://arxiv.org/abs/2608.30502); [Park et al. 2025](https://doi.org/10.1145/3746252.3761481); [Zhu et al. 2024](https://doi.org/10.14778/3636218.3636233); [Qin et al. 2026](https://arxiv.org/abs/2604.08059); [Du et al. 2019](https://doi.org/10.1145/3319535.3363226); [Kloft & Laskov 2012](https://arxiv.org/abs/1003.0078).

**What is already known.** Risk-monitoring, selective-adaptation, deferral, staged-rollback and unlearning mechanisms exist separately, in other domains or with labels.

**Residual gap.** A TSAD decision formulation that is certifiable without labels (exposure accounting), states the impossibility of false-promotion guarantees on the equivalent stratum, and tests the value of reversibility against delay across confirmation latencies.

**Proposed contribution.** An exposure-budgeted adaptation policy with actions `ADAPT-with-rollback / QUARANTINE / FREEZE / QUERY`, with an impossibility-plus-achievability analysis and a latency-dependent dominance test.

**Falsifiable claim.** A latency threshold L* exists below which optimistic promotion with rollback dominates quarantine at equal exposure. The estimated L* is finite and above the smallest tested latency.

**Minimum experiment.** P1 streams, four policies, sweeps of budget, latency and coverage; an adversarial arm per N1.

**Required datasets.** P1 generator; e-Energy as a partial real check.

**Main baseline threats.** Dwell-only baseline; Schirmer et al.; Wang et al. router; AnDri/METER.

**Kill criterion.** Optimistic promotion with rollback never dominates at any tested latency, or a dwell-only baseline reproduces the frontier.

**Novelty confidence.** `PROMISING_BUT_THREATENED`.

**Kind of novelty.** New decision/risk formulation; new theoretical result; state-management mechanism (versioned rollback). No architecture claim.

### P3: Authorization-scoped promotion and coincident-fault absorption

Story D in its sharpened form (see card D). `PROMISING_BUT_THREATENED`; feasibility-gated by data. Kind: problem formulation plus evaluation methodology.

### P4: Peer-corroborated normality under adversarial fleets

Story N2 plus the N1 adversarial fraction (see cards N2 and N1). `PROMISING_BUT_THREATENED`; feasibility-gated by fleet data with change logs. Kind: problem formulation plus theoretical result.

### P5: Normal-only commissioning protocol with a certified stopping rule

Story F in its evaluation form (see card F). `PROMISING_BUT_THREATENED`; separate from the lifecycle line. Kind: evaluation methodology.
