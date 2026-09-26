# P1–P6 implementation-oriented research review

Review status as of 2026-09-27. This branch contains research analysis and proposed experiment designs only. No detector code, experiment, training run, dataset download, or label inspection is authorized or performed here.

The source literature plan is the documentation-only branch `research/adaptive-normality-story-discovery-2026q3` at `a09253b922e27c246883e6d6d02d8d1f07ac028b`. Its reports, story cards, prior-art register, dataset requirements, kill criteria, and recommended research program were read before reviewing the six open GPT directions. GitHub issues #1–#4 were also read for prior findings; the six directions are GitHub issues #5–#10, labeled P1–P6.

## Work order

| Order | Direction | GitHub issue | Status |
|---:|---|---:|---|
| 1 | P5 — detector commissioning and READY stopping | [#9](https://github.com/kuo1234/xlstm_anomaly/issues/9) | Complete: Astra review 2 PASS for research/design assessment |
| 2 | P3 — authorization-scoped promotion | [#7](https://github.com/kuo1234/xlstm_anomaly/issues/7) | Complete: Astra review 2 PASS for research/design assessment |
| 3 | P6 — meta-RL recommissioning controller | [#10](https://github.com/kuo1234/xlstm_anomaly/issues/10) | Complete: Astra review 2 PASS for research/design assessment; execution remains gated on a completed P5 baseline and separate authorization |
| 4 | P2 — exposure budget and rollback versus waiting | [#6](https://github.com/kuo1234/xlstm_anomaly/issues/6) | Complete: Astra review 2 PASS for research/design assessment; execution remains gated on P1's evaluation contract and separate authorization |
| 5 | P4 — peer-corroborated fleet normality | [#8](https://github.com/kuo1234/xlstm_anomaly/issues/8) | Complete: Astra review 2 PASS for research/design assessment; execution remains gated on P1's evaluation contract and separate authorization |
| 6 | P1 — identifiability-stratified adaptive-TSAD evaluation | [#5](https://github.com/kuo1234/xlstm_anomaly/issues/5) | Complete: Astra review 2 PASS for research/design assessment; TSADmetrics/e-Energy full-text and reuse audits remain required before any study |

Each direction will receive its own feasibility assessment, literature comparison, proposed experiment, stop criteria, and independent Astra review before being marked complete.

## Review routing and research gates

P5, P3, and P6 record the `gpt-6-astra` reviewer fallback used while the Astra orchestrator skill was unavailable. The skill became available during P2 and has been used since then for delegated research and independent Astra review; the review disposition is recorded with each direction. Each direction still receives a separate Astra review before completion.

All proposed studies remain plans. `reports/m0_protocol.md` is unchanged; it does not authorize these new experiments. Any execution would need its own sealed protocol, frozen data manifest, and applicable GO/STOP review. Existing protected M1 worktrees and labels remain out of scope.
