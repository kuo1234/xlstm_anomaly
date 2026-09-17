# Design space for safe normality adaptation

The project's long-term framing assumes a particular shape for the eventual mechanism: a
**stable/plastic memory split**, an **ACCEPT / QUARANTINE / REJECT** admission decision, a **delayed
COMMIT**, and a **ROLLBACK**. This document asks whether that shape is necessary, which parts are
already standard practice, and what the alternatives are. It is a design survey, not a proposal, and
it deliberately argues against parts of the project's own assumed architecture.

Nothing here depends on a G1 outcome. Where a design choice would only matter under a particular
outcome, that is stated.

---

## 1. Is the assumed shape necessary?

Taking the four assumed primitives one at a time. Where this section says a primitive is "already
standard", §7 names the retrieved papers that occupy it — including two that already combine the
entire four-part shape on simpler detectors.

### ACCEPT / REJECT (selective update)

**Already standard.** Selecting which unlabeled samples may update a model is the core of
test-time-adaptation sample selection and of curated adaptation in TSAD — the project's own baseline
already performs curation (score-based masks plus memory-based candidate selection). A mechanism
whose novelty rests on "we only update on selected samples" has no novelty.

**Necessary?** Yes in some form, but note that a binary admission decision is only one option; see
§3 (soft weighting) for a version that may dominate it when the underlying classifier is weak.

### QUARANTINE (deferred decision)

**Partly standard, and often mis-specified.** Deferring a decision until more evidence arrives is an
old idea (sequential testing, delayed labelling, "wait and see"). What is frequently wrong is the
accounting, and the project already has the right observation in its protocol: **for a fixed cohort
that is eventually fully committed, delay cannot change the contamination fraction.** FIFO
scheduling moves *when* windows are committed, not *whether*. Therefore:

> Quarantine is only useful if it has an exit rule that can **reject**, and if the evidence available
> at the exit is materially better than the evidence at entry.

That turns "quarantine" into two testable requirements rather than a mechanism: (i) evidence must
improve with delay (this is exactly H4a's question), and (ii) the exit rule must be able to discard.
A quarantine that always eventually commits is a latency change with no safety content.

### Delayed COMMIT

**Necessary only if (i) holds.** If information does not improve with delay, the optimal policy under
any reasonable cost model is to decide immediately — delay then purchases false-positive exposure
with no reduction in absorption risk. This makes H4a, not the mechanism, the load-bearing experiment.

### ROLLBACK

**Standard in continual test-time adaptation** (reset/restore-based methods are an established family)
and **cheap or expensive depending on the representation** — see §4. Two problems the project's
framing does not yet address:

1. **Rollback needs a trigger,** and the trigger is the same detection problem one level up: who
   decides, without labels, that a past adaptation was wrong? A monitor on held-out clean data is the
   usual answer, and the project has a clean frozen prefix that could serve — but a monitor evaluated
   on a *fixed* prefix cannot distinguish "the adaptation was wrong" from "the world moved further".
2. **Rollback interacts badly with legitimate drift.** Rolling back a correct adaptation restores a
   stale normality model, so an aggressive rollback policy converts absorption risk into staleness
   risk. The trade-off must be stated as a frontier, not as a safety feature.

### Stable/plastic dual memory

**Standard in continual learning**, and in anomaly detection it appears as memory banks and prototype
sets. It is *necessary* only for a specific requirement: representing **multiple coexisting normals**
(and therefore recurrence A→B→A). If the deployment only ever has one current normal, a single
adaptable model with bounded movement is simpler and equally safe.

### Summary of §1

The assumed four-state machine is a recombination of known primitives. If the project's contribution
is the state machine, there is no contribution. The parts that could be new are:

- the **evidence** driving the transitions (internal recurrent state — H2/H3a's question),
- the **accounting** (stable-ID contamination across four separate exposure denominators: candidate,
  queue-admitted, committed-for-update, optimizer-loss-exposed), which is rarer in this literature
  than it should be, and
- an explicit **cost-asymmetric decision-theoretic treatment** of the delay, which is what turns
  "quarantine" from a heuristic into a derived policy.

---

## 2. Alternative formalizations

Seven framings that would replace, not decorate, the assumed shape. Each is listed with what it buys,
what it costs, and what it would require from this project.

| # | Formalization | Adaptation decision becomes | Buys | Costs / requirements |
|---|---|---|---|---|
| F1 | **Bayes-risk sequential decision.** Costs: `c_absorb` (commit an anomaly), `c_stale` per window of un-adapted operation under a real shift, `c_delay`. | An optimal stopping problem: adapt when the posterior of "legitimate new normal" crosses a cost-determined boundary. | Makes "how long to wait" *derived* rather than tuned; makes the asymmetry explicit; gives a principled operating point. | Needs a cost model (which the project does not have) and a likelihood or calibrated posterior. |
| F2 | **Two-hypothesis change-point test.** `H_drift`: parameter change persists; `H_anomaly`: transient excursion returns to baseline. | A sequential likelihood-ratio / GLR / CUSUM test on a *persistence* statistic. | Directly targets the actual distinction; classical finite-sample properties; no labels. | The discriminating statistic is duration/persistence — and the project's generator deliberately pairs legitimate excursions with equal-duration anomalies, so this route is weakest exactly where the benchmark is hardest. Honest tension worth stating. |
| F3 | **Conformal / e-value martingale.** Accumulate anytime-valid evidence against exchangeability with the incumbent normal. | Adapt when the accumulated e-value (or conformal martingale) exceeds a threshold. | No labels; anytime-valid error control on *wrong adaptations*, which is precisely the quantity a safety claim needs; detector-agnostic (needs only scores). | Guarantees are about exchangeability violation, not about semantics: a persistent fault also violates exchangeability persistently. Controls the statistical error, not the identifiability problem. |
| F4 | **Incumbent-versus-candidate model race.** Fit a candidate normality model on the ambiguous segment; compare both models' predictive scores on *subsequent* data; promote on persistent victory. | Model selection instead of sample classification. | Sidesteps per-window labelling entirely; naturally handles gradual drift; the "evidence improves with delay" requirement is satisfied by construction. | Two models to maintain; promotion criteria need multiplicity control; a candidate fitted on anomalous data will win if the anomaly persists (see §5). |
| F5 | **Regime-switching / mixture normality.** Normality is a *set* of regimes; anomaly = low likelihood under all regimes; new normal = a new regime with persistent occupancy. | Posterior regime occupancy plus a birth process for new regimes. | Handles multiple coexisting normals and A→B→A recurrence natively; rollback becomes "stop occupying the regime", which is reversible by construction. | Identifiability and complexity; regime birth is exactly the absorption risk in another form. |
| F6 | **Contamination-tolerant updating.** Do not gate; weight. Per-sample weights `∝ 1 − p̂(anomaly)`, trimmed/Huberized reconstruction loss, influence bounding. | A continuous weighting rather than a discrete admission. | Degrades gracefully when the anomaly classifier is weak — which is the regime the project may actually be in; no threshold to calibrate; no quarantine bookkeeping. | Harder to audit ("what was committed?" has no crisp answer, which conflicts with the project's exposure-denominator accounting); no hard guarantee against a large coordinated contamination. |
| F7 | **Bounded-movement adaptation.** Cap total parameter movement per unit time (trust region, anchored/EWC-style penalty, or adapt only a low-dimensional subspace). | A budget, not a decision. | Makes harm *bounded by construction* rather than prevented by detection; composes with every other option. | Bounds harm and benefit symmetrically: a genuinely large legitimate shift cannot be tracked either. |

**The comparison that matters.** F6 and F7 are the strongest competitors to the project's framing,
because they do not require the drift-versus-anomaly decision to be solvable at all. If H2 returns a
modest gain, a soft-weighted or movement-bounded scheme may outperform a gated scheme *using the same
weak signal*, and the project should expect a reviewer to ask exactly that. F1 and F3 are the
strongest complements: they supply the operating point and the error control that an information
result alone cannot provide.

---

## 3. Adaptation at different levels

"Adapt" is used loosely in this literature. The level chosen determines the risk, the reversibility
and the amount of evidence needed to justify it.

| Level | What changes | Reversibility | Risk of absorbing an anomaly | Capacity to represent a new normal |
|---|---|---|---|---|
| **Threshold / calibration** | Decision threshold or score calibration only | trivial | very low | none (cures post-shift FPR partially, cannot represent a new shape) |
| **Normalization statistics** | Input scaler, per-channel moments, normalization-layer statistics | trivial (recompute) | low | substantial for the common real cases: recalibration, setpoint change, gain change |
| **Recurrent state** | Carried hidden/cell state; no weights | trivial (reset) | low | limited and short-lived |
| **Memory / prototypes / retrieval set** | Add or remove exemplars, prototypes, kNN entries | **O(1) deletion** — genuinely cheap rollback | medium and *local* | good, and supports multiple coexisting normals |
| **Parameters** | Weight updates (what the project's baseline does) | expensive: needs checkpoints, and interacts with optimizer state | high and *global* | high |
| **Architecture / capacity** | New cells, new heads | n/a in this setting | n/a | n/a |

Two design implications the project has not drawn yet:

1. **Rollback cost is a property of the representation, not of the policy.** In a retrieval or
   prototype detector, "unlearn this window" is a delete. In a parametrically adapted detector it
   requires checkpointing and still leaves optimizer-state effects. If reversibility is a design
   goal, the representation should be chosen for it — that is a stronger and cheaper contribution
   than a rollback policy bolted onto a parametric model.
2. **The cheapest levels are missing from the project's baselines.** A normalization-statistics-only
   adapter and a threshold-only adapter are trivial to implement, are what many deployed systems
   actually do, and would establish how much of the post-shift false-positive problem is solved
   without touching the normality model. Without them, any mechanism result lacks its most important
   comparison.

---

## 4. Scenarios the design must handle

| Scenario | What breaks | Design consequence |
|---|---|---|
| **Multiple coexisting normals** | A single-model parameter update overwrites normal A while learning normal B | Needs memory/prototypes (F5 or the retrieval level), not a gate |
| **Recurring A→B→A** | Re-learning A from scratch each cycle; hysteresis and repeated adaptation cost | Requires retention with recall; a "forget-free" store is what makes recurrence cheap |
| **Gradual drift** | Change-point and quarantine machinery never triggers — there is no boundary to defer | Favours continuous low-rate adaptation (F6/F7) over discrete admission; the project's gradual scenario is where a gated design is least useful |
| **Abrupt shift** | Un-adapted FPR spikes immediately; delay is directly costly | Favours fast decisions with reversibility rather than long quarantine |
| **Persistent fault** | *Fundamental limit.* A persistent, self-consistent fault is observationally indistinguishable from a new normal by any persistence-based rule | No amount of waiting fixes this. The only escapes are asymmetric cost with reversibility (accept absorption but keep it cheap to undo), or **external/structural evidence** (§6) |
| **Anomaly poisoning (adversarial)** | An adversary that makes anomalies gradual and persistent is optimally shaped to be absorbed | Turns the problem from average-case to worst-case; argues for bounded movement (F7) and for audit trails rather than for better detection |
| **Detector-agnostic deployment** | A mechanism that needs architecture-specific internals cannot be dropped into an existing detector | See §5 — this is in direct tension with the project's own H3a |

---

## 5. Two conceptual issues that could materially change the project

### 5.1 A positive H3a is a double-edged result

H3a asks whether the drift-versus-anomaly information is **xLSTM-specific**. Suppose it is. Then the
eventual mechanism depends on having an xLSTM-class detector with accessible scalar-cell internals —
which makes it *less* portable, harder to adopt, and harder to evaluate against the deployed
detectors that motivated the work. The scientifically interesting outcome (architecture specificity)
and the practically valuable outcome (a detector-agnostic mechanism) point in opposite directions.

This deserves a decision, not a discovery after the fact:

- If the project's goal is a **deployable mechanism**, then the most useful H3a outcome is a *null* —
  it licenses a score/history-plus-generic-internals gate that any recurrent detector can supply.
- If the goal is a **scientific claim about xLSTM**, a positive H3a is the interesting result, and the
  mechanism work should be framed as a demonstration rather than as a deployment proposal.

Both are legitimate; they imply different papers, different baselines and different reviewers. Being
explicit about which one is being pursued would change how the results are framed in either
direction.

### 5.2 Persistence is not enough, and there is an unused evidence axis

Every formalization in §2 that relies on the *temporal* axis inherits the persistent-fault limit:
persistence cannot separate a lasting fault from a lasting new normal. The project's own generator
includes a persistent-fault stratum precisely because this is the adversarial case.

There is, however, a second evidence axis the project has not considered at all: **cross-entity
agreement.** In fleet settings — and the strict anchor dataset is itself a 28-machine fleet — a
distribution shift that appears *simultaneously across independent entities* is far more likely to be
a legitimate global change (software release, ambient condition, load pattern), while a shift
isolated to one entity is far more likely to be a fault. This is:

- **available in the project's own data sources** (multiple machines, multiple served entities),
- **orthogonal** to both the internal-state and the delayed-evidence axes, so it composes with them,
- **cheap** to test descriptively before any mechanism is built, and
- **absent from the current hypothesis chain**, which is framed entirely per-stream.

A minimal pre-registered test would ask whether cross-entity shift agreement discriminates
drift-from-anomaly windows better than the within-stream score/history control — the same estimand
family as H2, on a different evidence axis. If it does, the mechanism design changes substantially:
the gate becomes a fleet-level statistic, and the internal-state question becomes a secondary
refinement rather than the main route.

---

## 6. What this means for the project's next mechanism design

Ordered by what would strengthen the eventual claim the most per unit of work:

1. **Add the cheap baselines** (threshold-only, normalization-statistics-only adapter). Without them,
   no mechanism result is interpretable.
2. **Write the cost model down** (F1). "Safe" is undefined without the asymmetry between absorbing an
   anomaly and delaying a legitimate adaptation; with it, the operating point stops being a
   hyperparameter.
3. **Choose the representation for reversibility** (memory/prototype or bounded-movement parametric),
   so rollback is a property rather than a subsystem.
4. **Treat quarantine as a hypothesis, not a component**: it is worth building only if delayed
   evidence measurably improves and the exit rule can reject.
5. **Test the cross-entity evidence axis descriptively** before committing to a within-stream
   mechanism.
6. **Decide explicitly** whether the target is a portable mechanism or an xLSTM claim (§5.1).


---

## 7. Prior-art mapping for everything above

Every primitive, formalization and level in this document, mapped to what the literature sweep
actually retrieved (78 records, 61 full texts; see `related_work_map.md` and
`positioning_table.md`). `none retrieved` means nothing in *this* search occupies the slot — it is
weak evidence of a gap, not proof, and where a topic was outside the search scope that is stated
instead.

### The four assumed primitives

| Primitive | Status in the retrieved literature | Instances |
|---|---|---|
| ACCEPT / REJECT admission on a normality buffer | **occupied — treat as baselines** | CANDI (`10.1609/aaai.v40i17.38524`), COMET (`arXiv:2602.01635`), M2N2 (`arXiv:2312.11976`), MemStream (`arXiv:2106.03837`) |
| QUARANTINE / deferred commitment | **occupied as a construct**; what it buys is never quantified | HTM+SPRT (`arXiv:2504.18599`), METER (`arXiv:2312.16831`), Quilt (`arXiv:2312.09691`), pending-transition buffer (`arXiv:2607.08373`), verification latency (`arXiv:2204.06822`) |
| Delayed COMMIT conditional on accumulated evidence | **occupied**; METER's accumulate-then-commit and the martingale's skip/sustain actions are the closest | `arXiv:2312.16831`, `arXiv:2608.30502` |
| ROLLBACK / reset | **occupied for timing, open for semantics** — all revert toward a *fixed source model* | CoTTA (`arXiv:2203.13591`), EATA (`arXiv:2204.02610`), SAR (`arXiv:2302.12400`), PETAL (`arXiv:2212.09713`), RDumb (`arXiv:2306.05401`), adaptive selective reset (`arXiv:2603.03796`), RDumb++ (`arXiv:2601.15544`) |
| Stable/plastic dual memory | **standard architecture** | DualNet (`arXiv:2110.00175`), CLS-ER (`arXiv:2201.12604`); in AD as prototypes/coresets/codebooks (`arXiv:2401.01010`, `arXiv:2511.08634`, `arXiv:2602.01635`) |

Two of the retrieved full-text papers already instantiate **the entire four-part shape** — internal
evidence, deferral, an explicit drift-versus-anomaly decision, and reset: the HTM+SPRT framework
(`arXiv:2504.18599`) and anytime-valid martingale gating (`arXiv:2608.30502`). Both do it on a simple
detector (hierarchical temporal memory; a linear Kalman filter) rather than a learned deep
multivariate detector, and neither measures contamination harm. That is the precise shape of what is
left.

### The seven alternative formalizations (§2)

| # | Occupied? | Nearest retrieved work |
|---|---|---|
| F1 Bayes-risk / optimal stopping with explicit cost asymmetry | **no TSAD instance retrieved** — the closest supply error control but not a cost model | HTM+SPRT (`arXiv:2504.18599`, SPRT error probabilities), segmented confidence sequences (`arXiv:2508.06638`) |
| F2 Two-hypothesis change-point test on persistence | **partly occupied** | STAD (`10.1016/j.datak.2024.102365`), HTM+SPRT, MACS/CUSUM-style regime change (`arXiv:2508.06638`) |
| F3 Conformal / e-value martingale | **occupied** | anytime-valid gating (`arXiv:2608.30502`), conformal uncertainty indicator (`arXiv:2502.02998`), segmented confidence sequences (`arXiv:2508.06638`) |
| F4 Incumbent-versus-candidate model race | **substantially occupied** — this is the streaming field's structural answer | ARCUS (`10.1145/3534678.3539348`), METER (`arXiv:2312.16831`), SCALE's expandable expert pool (`10.1145/3770855.3817912`) |
| F5 Regime-switching / multiple normals | **partly occupied** | STAD's discrete states (incl. revisiting a previously seen state), ReCATS multi-regime (`10.1145/3770855.3817985`), DeCoFlow prototype routing (`arXiv:2606.26687`), ETF prototypes (`arXiv:2609.03406`) |
| F6 Contamination-tolerant soft updating | **partly occupied, and closer than expected** — the martingale paper's action table includes an explicit `huberize` action, and entropy-weighted losses are standard in CTTA | `arXiv:2608.30502`, EATA (`arXiv:2204.02610`), RDumb (`arXiv:2306.05401`) |
| F7 Bounded-movement adaptation | **occupied** | Fisher-weighted anti-forgetting (`arXiv:2204.02610`), Fisher-selected restoration (`arXiv:2212.09713`), stochastic restore (`arXiv:2203.13591`), orthogonal-subspace LoRA banks (`arXiv:2606.02042`) |

The consequence for §2's own recommendation: F1 (a written-down cost model) is the only formalization
in the list with no retrieved TSAD instance, which makes it the cheapest genuinely unoccupied move
available — and it is a modelling decision, not an experiment.

### The adaptation levels (§3)

| Level | Retrieved instances |
|---|---|
| Threshold / calibration only | gated calibration in forecasting (TAFAS, `10.1609/aaai.v39i17.33965`) |
| Normalization statistics | instance-wise BN statistics with a prediction-balanced reservoir (NOTE, `arXiv:2208.05117`) |
| Recurrent / latent state | learned latent dynamics driving incremental adaptation (iADCPS, `arXiv:2504.04374`); memory contents as scoring and gating signal (MemStream) |
| Memory / prototypes / retrieval | MemStream, UCAD (`arXiv:2401.01010`), CADIC (`arXiv:2511.08634`), COMET, ONER (`arXiv:2412.03907`) |
| Parameters | CANDI's residual module, M2N2, and the whole CTTA family |

Note what this table says about §3's claim that the cheap levels are missing from the project's
baselines: they are not missing from the *literature* — they are established, which makes their
absence from the project's comparison set a straightforward reviewer objection rather than an open
question.

### The scenarios (§4) and the two conceptual issues (§5)

- **Recurring A→B→A**: partly addressed — STAD explicitly treats revisiting a previously seen state as
  a state transition, and ReCATS models multiple regimes.
- **Persistent fault versus new normal**: **no retrieved paper addresses this indistinguishability
  limit explicitly.** Given that 25 of 78 records have unknown mechanism attributes, this is weak
  evidence of a gap — but it is consistent with the F11 family's practice of taking per-task normal
  data as clean by definition, which makes the question unaskable inside that setting.
- **Adversarial anomaly poisoning**: **outside the scope of this search.** Data-poisoning and
  adversarial-robustness literature was not among the 16 families, so nothing here licenses a novelty
  claim on it; it should be searched before the framing is used.
- **Cross-entity / fleet agreement as an evidence axis (§5.2)**: **also outside the scope of this
  search.** No family covered multi-entity or fleet-level drift evidence, so the idea's status in the
  literature is *unassessed*, not novel. It remains worth testing descriptively — but it needs its own
  targeted search first (candidate vocabulary: fleet-level anomaly detection, multi-entity drift,
  cross-machine/cross-device normality, federated drift detection).
- **§5.1 (a positive architecture-specific result reduces portability)**: this is an argument, not a
  literature finding; the relevant literature fact is that the xLSTM-TSAD literature is two papers
  (`arXiv:2405.04517`, `arXiv:2506.22837`), neither of which examines internal state, so there is no
  external evidence either way about portability.

### Net effect on this document's recommendations

Recommendations 1 (cheap baselines) and 2 (write down the cost model) survive unchanged and are
strengthened: the baselines exist in the literature and the cost model does not. Recommendation 3
(choose the representation for reversibility) is partly anticipated by the memory/prototype families,
so it should be framed as a design consequence rather than a novel idea. Recommendation 4 (treat
quarantine as a hypothesis) is reinforced — deferral is a published construct, so only its measured
benefit can be a contribution. Recommendation 5 (cross-entity axis) must be preceded by a targeted
literature search, which this sweep did not perform.
