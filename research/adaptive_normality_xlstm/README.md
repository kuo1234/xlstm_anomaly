# Adaptive normality and xLSTM: research audit

**Status:** literature audit, problem definition, evidence review and experiment planning only
**Repository base:** ffae1da6e37b48076e2610390c249318acfbea2e
**Branch:** research/adaptive-normality-xlstm
**Audit cutoff:** 2026-09-24
**Implementation / training / GPU runs:** none

This branch asks whether a reusable recurrent initialization can help a new machine learn normal behavior from a small, explicitly confirmed-normal target sample, and whether a detector can later track legitimate operating changes without absorbing a fault. It does not assume xLSTM is needed, and it keeps target-machine transfer separate from online new-normal detection.

## Decision at this audit

**Prior-art classification: PARTIALLY_OVERLAPPING.** The “new normal” problem and test-time adaptation are already explicit in M2N2 (AAAI 2024). ACM E-Energy 2026 directly studies normal / normal-drift / attack separation with selective updates using a small labeled anchor set. Selective adaptation also appears in CANDI (AAAI 2026) and MemTTA (a 2026 master's thesis); dynamic normal-pattern and historical model pools appear in AnDri, ARCUS, WWW 2026 DESS and other drift-aware systems. Forecasting, memory, transfer, and online adaptation are individually established. The search did not identify one public work that verifies every item in the proposed ten-part combination, but that absence is not enough to support a novelty claim.

**Architecture recommendation: DO_NOT_BUILD_YET.** Problem A, few-shot normal-only target transfer, is testable as a small, backbone-neutral study after a source-native detector viability gate. Problem B, deciding whether a stable unseen regime is benign or a persistent fault, is not identifiable from observations alone in general. Existing public datasets reviewed here mostly label anomalies or distribution shift; they do not label the semantic boundary required by that claim.

**Research decision: ADAPTIVE_NORMALITY_RESEARCH_REFRAME.** Reframe the near-term question around same-dimensional, normal-only machine transfer and sample efficiency. Keep new-normal handling as a later, metadata- or operator-confirmed problem. Do not implement the integrated system until the stage gates in experiment_plan.md pass.

## Documents

- [problem_definition.md](problem_definition.md) separates new-machine transfer from new-normal drift and states the identifiability limit.
- [prior_art.md](prior_art.md) records the search scope, evidence, publication status and closest work.
- [novelty_matrix.md](novelty_matrix.md) compares the important methods against the requested system dimensions.
- [existing_evidence_map.md](existing_evidence_map.md) classifies completed repository work without revising its claims.
- [dataset_audit.md](dataset_audit.md) matches datasets to the questions they can actually answer.
- [architecture_options.md](architecture_options.md) compares three bounded candidates and memory/update choices.
- [experiment_plan.md](experiment_plan.md) gives M0–M7 gates and kill criteria; it authorizes no experiment.
- [metrics.md](metrics.md) defines detection, adaptation, safety and regime metrics.
- [claim_boundary.md](claim_boundary.md) keeps five possible claims independent.
- [red_team.md](red_team.md) lists scientific failure modes and their risk classes.
- [final_assessment.md](final_assessment.md) answers the ten requested questions.

## Scope and handling

The worktree was created from the exact requested commit. All edits are confined to this research branch. The repository's separate main worktree had unrelated local changes, which were left untouched. This branch adds research documents only; there are no result files, model changes, training runs, D0 runs, zero-shot runs, merges, or edits to earlier G1, P1r, A+, A+S or R0 history.
