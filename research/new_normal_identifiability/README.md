# Identifiability boundary: benign new normal vs persistent fault

**Issue:** [#3](https://github.com/kuo1234/xlstm_anomaly/issues/3)

**Research cutoff:** 2026-09-26
**Final status:** **IDENTIFIABILITY_BOUNDARY_ESTABLISHED**

## Finding

From an observation stream alone, a persistent distributional change may be detectable, but its semantic status as an authorized benign mode or a fault is not identifiable in general. If those two explanations induce the same probability law for the complete observed history, every classifier that sees only that history has the same output distribution in both worlds. With equal class priors, its minimum error is one half, even with unlimited history. A recurrent model, longer memory, quarantine, or promotion rule cannot overcome that information limit.

Classification can become possible under explicit restrictions on the hypothesis classes, an informative and trusted context stream, independent measurements, known physical/control constraints, interventions, or operator confirmation. Even then it is identifiable only if the additional evidence separates the competing explanations. More context does not automatically resolve ambiguity.

## Worktree and scope

- Issue branch: research/new-normal-identifiability
- Worktree: /home/p76141495/home/xlstm_anomaly-identifiability
- Base: origin/main at 537fc7d4a15ae603f285c3511b80ce0c0eba3e99
- Protected M1 branch at start: research/adaptive-normality-m1-smd, SHA 2eda60d024d2a9149d62de5161ca76916a085942
- Analysis only. No protected data, unopened labels, GPU, model training, or detector experiment was used. The counterexamples are symbolic constructions, not generated data.

## Deliverables

- problem_formulation.md — semantic labels, observable variables, assumptions and task boundaries.
- identifiability_theorems_and_counterexamples.md — formal impossibility result and concrete observationally equivalent worlds.
- observable_vs_semantic.md — shift taxonomy across twelve signal changes and four distinct inference questions.
- context_requirements.md — context sources, what each can resolve, and trust limits.
- adaptation_threat_model.md — persistent and coordinated faults that can be absorbed by adaptation.
- architecture_implications.md — what memory, quarantine, promotion, rollback and recurrence can and cannot do.
- claim_boundaries.md — direct answers to issue questions and claims a future paper must avoid.
- recommended_M6_design.md — a research design that separates detection from semantic authorization.
- sources.md — primary and authoritative sources with evidence notes.

## Protocol boundary

The analysis follows reports/m0_protocol.md. It authorizes no M0 implementation or experiment. That protocol explicitly gates and restricts adaptation mechanisms; this report does not amend it. The M6 recommendations are conceptual design requirements for a separately reviewed future protocol, not execution permission.
