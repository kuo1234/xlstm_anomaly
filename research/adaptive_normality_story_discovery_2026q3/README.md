# Adaptive-normality research-story discovery (2026 Q3)

**Research cutoff:** 2026-09-26 · **Decision:** `MULTI_STORY_PROGRAM_RECOMMENDED` (Path 3: evaluation/theory paper first, method later)

## Decision in one paragraph

No new adaptation *mechanism* survives the current literature. Lifecycle-with-rollback, recurring-regime pools, selective "should I adapt?" rules, label-free risk monitoring of adapting models, and joint retention/energy accounting were all published by the cutoff, several of them in the final eight weeks. What survives sits at the evaluation and decision level. The strongest candidate is **P1, an identifiability-stratified, contamination-aware evaluation of adaptive TSAD**. It uses streams whose benign-versus-fault question is non-identifiable by construction, so the Bayes floor is known, and it scores adaptation decisions with absorption, masking and recovery metrics. It also carries an analytic result: point-adjusted metrics cannot penalise a detector that alarms once at fault onset and then absorbs the fault. **P2** (adaptation under a budget of unverified influence, where reversibility is tested against waiting) is the method paper that P1 makes evaluable. **P5** (normal-only commissioning protocol) is a separate line. **P3** (authorisation-scoped promotion) and **P4** (peer-corroborated fleet normality) depend on data that is not yet available. None of the five needs xLSTM, and none depends on the running M1 experiment.

## Top research stories

| ID | One-sentence problem | Status |
|---|---|---|
| P1 | Can adaptive TSAD be evaluated so that information failure is separated from method failure, and adaptation harm is scored directly? | `STRONG_CANDIDATE` |
| P2 | With delayed, partial confirmation, which policy minimises benign delay under a budget on unconfirmed influence, and when does reversibility beat waiting? | `PROMISING_BUT_THREATENED` |
| P3 | When an authorised change explains only part of a shift, can faults that coincide with it still be kept out of normality? | `PROMISING_BUT_THREATENED` |
| P4 | When does simultaneous change across fleet peers license promotion, and how many compromised peers break it? | `PROMISING_BUT_THREATENED` |
| P5 | How much verified target-normal data does a new machine need, and when can commissioning be certified complete? | `PROMISING_BUT_THREATENED` |

The requested stories map as follows: A and B go into P2; C becomes P2's action space; D becomes P3; E is `ALREADY_OCCUPIED` and becomes a P1 axis; F becomes P5; G becomes P1; H is `ALREADY_OCCUPIED`. Seven gap-derived stories (N1–N7) are carded in [story_cards.md](story_cards.md).

## Isolation record

- Branch `research/adaptive-normality-story-discovery-2026q3`, created from `origin/main` at `275fa99`. It contains documentation only, and only under `research/adaptive_normality_story_discovery_2026q3/`.
- A linked worktree could not be created: the sandbox that produced this report cannot write under `.git/worktrees/`. The commit was therefore built with git plumbing (temporary index, `commit-tree`, `update-ref`), so no working tree was checked out anywhere. The primary checkout was not modified.
- The protected M1 ref `origin/research/adaptive-normality-m1-smd` was at `2eda60d` before and after this work. It was not checked out, merged, rebased, reset or pushed. No `git worktree prune` was run.
- No training, GPU use, detector code change, dataset download, label inspection or M1 result reading took place.

## Files

- [candidate_stories.md](candidate_stories.md): dispositions of A–H, the gap-derived N1–N7, and the merge into P1–P5.
- [story_cards.md](story_cards.md): a full card for every story, following the requested schema.
- [closest_prior_art.md](closest_prior_art.md): closest primary sources per story and what each occupies.
- [novelty_threat_matrix.md](novelty_threat_matrix.md): story × threat-family matrix and the kind of novelty for each survivor.
- [kill_criteria.md](kill_criteria.md): literature kills to check before building, and empirical kills to pre-register.
- [dataset_requirements.md](dataset_requirements.md): per-story data needs, sufficiency, and generator constraints for P1.
- [recommended_research_program.md](recommended_research_program.md): path choice, sequencing, and the eight red-team answers.
- [future_dated_leads.md](future_dated_leads.md): records with issue dates after the cutoff, plus a monitoring plan.
- [sources.md](sources.md): search procedure, identifier corrections, and the register by story.
- [papers.json](papers.json): machine-readable register with per-track search logs.

## Limits of this evidence

Most decisive threats were read at abstract level, and several 2026 records only at title level. Every status that depends on such a record is marked, and the literature kills in [kill_criteria.md](kill_criteria.md) list the full-text checks that must precede any build. At least seven directly relevant papers appeared within eight weeks of the cutoff, so the novelty picture is moving quickly. The name "StrAD" was not resolved to a streaming-TSAD benchmark in two independent passes. G and P1 are compared against SCAR, STAD, Exathlon, TSB-AD, AnoShift and the 2026 continual-AD scenario framework instead.

## Relation to earlier project documents

This report builds on `research/adaptive_normality_prior_art_2026q3/` (Issue #1), `research/new_normal_dataset_audit/` (Issue #2) and `research/new_normal_identifiability/` (Issue #3), and it does not repeat their findings. It amends none of `reports/m0_protocol.md` and authorises no experiment.
