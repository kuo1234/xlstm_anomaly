# Recommended research program

**Decision: `MULTI_STORY_PROGRAM_RECOMMENDED`, with Path 3 as the publication path.** The first paper should be an evaluation and theory paper (P1). The method paper (P2) follows and is evaluated on P1's contract. Commissioning (P5) runs as a separate, independently gated line. P3 (context) and P4 (fleet) stay conditional on data acquisition. This is a sequenced program with one primary first deliverable, not five parallel papers.

## Why not the other paths

**Path 1 (one lifecycle/risk method paper) is not recommended as the first paper.** The literature leaves no room for a lifecycle *mechanism*. Candidate admission and reactivation ([Park et al. 2025](https://doi.org/10.1145/3746252.3761481)), state libraries with transitions ([Li et al. 2024a](https://doi.org/10.1016/j.datak.2024.102365)), deferral ([Zhu et al. 2024](https://doi.org/10.14778/3636218.3636233)), buffered selective update with contamination reporting ([Le et al. 2026](https://doi.org/10.1145/3744255.3811742)), recurring-regime pools ([Li et al. 2026b](https://doi.org/10.1016/j.knosys.2026.116530)), staged candidate–shadow–gated-activation–rollback pipelines ([Qin et al. 2026](https://arxiv.org/abs/2604.08059), [Aftab et al. 2026](https://arxiv.org/abs/2607.02687)), per-sample selective adaptation ([Jiang et al. 2026](https://arxiv.org/abs/2609.08367)) and risk monitoring of adapting models ([Schirmer et al. 2025](https://doi.org/10.52202/085713-2705)) are all published. A new lifecycle paper would be judged on a frontier that no accepted benchmark currently measures. Its evaluation would have to be invented inside the method paper, which reviewers read as self-serving.

**Path 2 (lifecycle paper plus commissioning paper) is partly adopted.** Commissioning is correctly a separate paper: its estimand (target-normal sample efficiency) involves no semantic ambiguity, so it can be run under a cleaner protocol. But the method space there is also occupied ([Holly et al. 2025](https://arxiv.org/abs/2501.13052), [Jonas & Meyer 2025](https://arxiv.org/abs/2504.17709), [Shentu et al. 2025](https://arxiv.org/abs/2405.15273)), so it survives only as an evaluation-protocol and stopping-rule paper (P5), not as a method paper.

**Path 4 (abandon adaptive normality) is not justified.** P1 has a concrete residual gap: equivalent-by-construction strata, decision-level labels, context as an experimental factor, and metric blindness to absorption. It also has one analytically certain lever: point adjustment cannot penalise post-detection absorption. It uses assets the project already has, namely the identifiability theorem (Issue #3), fail-closed pre-registration practice, evaluator-side truth, and the earlier observation that contamination-harm accounting is unoccupied.

## Sequenced program

1. **P1: evaluation and theory paper.** Formalise the identifiability strata and prove the metric-blindness proposition. Build an independent generator (do not modify the protocol-frozen `m0.synthetic`). Re-score 6–8 public adaptive detectors on CPU. Gate: kill criteria K1–K4 in [kill_criteria.md](kill_criteria.md). The first step before any build is a full-text check of the LARM property set ([Wagner et al. 2025](https://arxiv.org/abs/2510.17562)) and the 34 TSADmetrics metrics ([Velasco & Zafra 2026](https://doi.org/10.1016/j.neucom.2026.134154)) for an existing absorption-sensitive property.
2. **P2: method paper on P1's contract.** An exposure-budgeted policy with `ADAPT-with-rollback / QUARANTINE / FREEZE / QUERY` actions, the impossibility-plus-achievability analysis, the latency-dominance test, and an N1 adversarial arm. Gate: the dwell-only kill criterion.
3. **P5: separate commissioning line.** Held-out-entity sample-efficiency protocol with zero-shot and one-liner reference lines and a certified stopping rule. SMD LOMO is exploratory only (Issue #4 label-exposure provenance). A confirmatory entity family (PreDist or a wind-turbine fleet) must be pinned first.
4. **Conditional extensions.** P3 starts only if e-Energy licensing and event IDs are resolved or a TEP coincident-fault scenario is generated and sealed. P4 starts only if a fleet dataset with documented fleet-wide benign changes is found.

## Required red-team answers

### 1. Is there still enough novelty after AnDri, ARCUS, M2N2, CANDI, MemStream, PADRE, recent continual-normality work and current streaming benchmarks?

For a new adaptation *mechanism*: no. Since the Issue #1 audit, the space has filled further. [Li et al. 2026b](https://doi.org/10.1016/j.knosys.2026.116530) explicitly targets recurring-regime overwriting in unsupervised streaming TSAD. [Smendowski et al. 2026](https://doi.org/10.1007/s10723-026-09846-5) adds novelty-gated replay admission with retention and energy accounting. [Jiang et al. 2026](https://arxiv.org/abs/2609.08367), [Wang et al. 2026a](https://arxiv.org/abs/2609.20700) and [Majumdar & Saha 2026](https://arxiv.org/abs/2608.22233) pose "should this be adapted?" in TTA, and [Qin et al. 2026](https://arxiv.org/abs/2604.08059) publishes a full staged rollback pipeline. Enough novelty remains in three places: (a) evaluation that separates information failure from method failure and scores absorption (P1); (b) a label-free-certifiable decision formulation under delayed confirmation, with an explicit impossibility result (P2); and (c) authorisation scope for coincident faults (P3). None of these is a new model component.

### 2. Is a "reversible normal-state lifecycle" genuinely different from a model pool or memory bank?

Not as a container. A set of versioned normal states is a model pool, and AnDri's active/inactive patterns are a bank with lifecycle status. Two properties could make it operationally different: write isolation (candidate evidence cannot influence confirmed-state scoring before promotion) and reversible commit (a promoted state can be retracted with bounded residual when delayed evidence arrives). ARCUS-style merging is irreversible. AnDri's deactivation is a partial reversal. [Su et al. 2026](https://arxiv.org/abs/2607.27773) and [Aftab et al. 2026](https://arxiv.org/abs/2607.02687) implement reversibility outside TSAD. Reversibility therefore becomes a contribution only if it is shown to beat waiting (the P2 latency test). Otherwise the lifecycle is a relabelled pool.

### 3. Is the "contamination–recovery frontier" already a standard evaluation framing somewhere else?

The frontier is not standard under that name in TSAD, but its components are. Selective prediction has used risk–coverage trade-offs for years ([Geifman & El-Yaniv 2017](https://arxiv.org/abs/1705.08500)). The Wang et al. router reports harmful accepted area at matched Dice ([Wang et al. 2026a](https://arxiv.org/abs/2609.20700)). [Qin et al. 2026](https://arxiv.org/abs/2604.08059) reports unsafe activation against task success. [Le et al. 2026](https://doi.org/10.1145/3744255.3811742) reports contamination rate alongside AUC. [Smendowski et al. 2026](https://doi.org/10.1007/s10723-026-09846-5) reports backward transfer and retention. Presenting the frontier as a new framing would be relabelling. It is defensible only as a TSAD instantiation with evaluator-side truth and identifiability strata, and that is exactly P1's role.

### 4. Is `ADAPT / FREEZE / UNRESOLVED` a sufficiently distinct scientific formulation?

No, not as a standalone formulation. It is a three-way decision with a reject option ([Chow 1970](https://doi.org/10.1109/tit.1970.1054406), [Sobel & Wald 1949](https://doi.org/10.1214/aoms/1177729944)). METER's "unknown" and AnDri's candidates are operational equivalents, and three recent TTA papers pose the binary version. There is also a sharper problem. Whether a segment is identifiable depends on the hypothesis classes, not on the segment, so `UNRESOLVED` can be computed only against a declared library of benign modes and fault signatures. The formulation becomes scientifically distinct only when `UNRESOLVED` has value-of-information semantics (wait, query or probe, with bounded duration) inside a risk-constrained policy. That is why it lives in P2.

### 5. Can external context create a stronger story than another adaptive detector?

Yes in principle. Context is the only route to semantic claims that is consistent with the identifiability boundary. The context story is stronger only if three conditions hold. First, it must avoid the trivial case ("promote iff authorised") by studying authorisation *scope* and faults that coincide with authorised changes. Second, it must not rely on context being incorruptible; the CPS literature already mediates influence under zero trust ([Lotto et al. 2026](https://arxiv.org/abs/2609.28170)). Third, a dataset or simulator must exist. The third condition is the binding one. The data audit found no dataset with the full semantic contract, e-Energy is licence- and event-ID-gated, and TEP is simulated. The context story is therefore scientifically stronger but less feasible, and it is scheduled after P1.

### 6. Is normal-only rapid commissioning more defensible and less crowded than online new-normal adaptation?

It is more defensible: "verified-normal prefix" is an operational fact rather than a semantic judgement, and the estimand is identifiable. It is not less crowded as a method: OC-MAML/OC-DA-MAML, wind-turbine transfer, zero-shot foundation detectors and source-free adaptation all compete, and one-liners remain a strong sanity baseline ([One-liners paper (ICLR 2026)](https://openreview.net/forum?id=H27kvyG4qf)). It is less crowded as an evaluation protocol with a certified stopping rule. An SMD-only version inherits the Issue #4 label-exposure caveat and would be exploratory.

### 7. Which story is least dependent on xLSTM specifically?

P1 does not depend on any detector architecture: it evaluates policies and published detectors. P2 is policy-level and detector-agnostic. P3, P4 and P5 are also backbone-agnostic. None of the five programme stories needs xLSTM. That is deliberate, since the prior work established that xLSTM is not a novelty claim and that recurrent state cannot hold information beyond the input history.

### 8. What story survives even if the current R-only M1 experiment is negative?

P1 survives completely. It needs no M1 artefact, no SMD label and no project detector, and its central results are an analytic proposition, a generator with a known Bayes floor, and a re-scoring of public methods. P2 also survives, because it is evaluated on P1 streams with any base detector. P5 can proceed on a separate entity family. This report does not read, interpret or depend on any M1 result.

## Program-level risks

- **Recency risk.** At least seven directly relevant items appeared within eight weeks of the cutoff, and several decisive ones were read only at abstract level. The monitoring list is in [future_dated_leads.md](future_dated_leads.md).
- **Synthetic-only criticism.** P1 must include one real anchor (e-Energy once licensed, or an Exathlon-style recovery-interval dataset) and must report whether conclusions transfer.
- **Evaluation-paper venue risk.** P1 fits a datasets-and-benchmarks track or an evaluation-methodology venue. It should not be presented as a method paper.

## Gates

This report authorises no training, GPU use, dataset download, label inspection or protocol change. Each programme step needs its own sealed protocol under `reports/m0_protocol.md` conventions and an explicit owner decision.
