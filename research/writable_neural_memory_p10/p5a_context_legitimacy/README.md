# P5-A — Contextual legitimacy feasibility audit

Final gate: **CONTROLLED_CONTEXT_ONLY / pending review**. This is a source-backed feasibility audit and proposed protocol, not an execution GO.

The information gap is unresolved in deployment. Independently recorded operational intent can change the plausibility of a deviation, but authorization is neither successful execution nor safe, settled operation. The proposed controlled test deliberately retains identical observation AND identical available-context benign/fault alternatives. Context may reduce uncertainty in some settings; it cannot universally remove it.

Issue [#19](https://github.com/kuo1234/xlstm_anomaly/issues/19) authorizes documentation, source inspection and design only. Base: research/p7-p10-segment-memory at c9e42c2d4bc962494a9c0a3708bb8439cbb7868c. P4-B was accepted in [review 5982918516](https://github.com/kuo1234/xlstm_anomaly/issues/18#issuecomment-5982918516), with its rank-2 linearAE / decoder SGD / gap0 / Q-family limits.

## Gate assessment

| Requirement for CONTEXT_ROUTE_READY | Evidence and decision |
|---|---|
| L1/L2 context with non-oracle meaning | Plausible L1 measured load/flight conditions and recorded commands; L2 authorization contract designed. No inspected dataset provides the complete L2 receipt/provenance contract. |
| Aligned healthy change and fault evaluation | ESA is the strongest real-source lead; causal delivery and persistent settled reference eligibility are unqualified. Machinery records support condition transfer, not continuous transition. Aircraft data are simulation. |
| Prior art does not fully cover the proposed intersection | Broad novelty contradicted. The narrower intersection remains UNRESOLVED: incomplete 2025/2026 full-text coverage and a strong validation-gated implementation threat. |
| Non-oracle controlled protocol | Defined in CONTROLLED_CONTEXT_PROTOCOL.md; overlapping context/truth cells and unresolved twins are mandatory. |
| Missing/delayed/wrong-context stress tests | Designed, NOT EXECUTED. |

Accordingly real admission readiness is not established. CONTROLLED_CONTEXT_ONLY means a plausible, falsifiable design exists, not that context has empirically helped. No CONTEXT_ROUTE_READY, universal safety, strict confirmatory, or novel-method claim is made.

## Reviewable evidence

- [Prior-art matrix](PRIOR_ART_OVERLAP.md): operating-condition transfer, conditional detection, selective TTA and validation before deployment.
- [Dataset audit](DATASET_CONTEXT_AUDIT.md): eight source questions per candidate, qualified vs unknown fields.
- [Context contract](CONTEXT_LEVELS.md): runtime allowlist, causal availability, trust and leakage boundaries.
- [Proposed controlled protocol](CONTROLLED_CONTEXT_PROTOCOL.md): design only; preserves ambiguity and error cases.
- [Shadow boundary](SHADOW_VERIFICATION_BOUNDARY.md): containment and exact-state lineage, not normative legitimacy.
- [Source inventory](source_inventory.json) and [provenance](provenance/README.md): official URLs, hashes, inspection coverage, access failures and exposure.

All acquisition/inspection/writes occurred on ssh kuo. Only small documents, official code and catalog metadata were acquired; no new raw datasets, detector runs, training, adaptation, policy writes or shadow models. Existing sealed P4 artifacts are unchanged. Paper examples and published label semantics WERE read; no new raw label file was opened. This is not a label-blind confirmatory study.

## Stop and proposed next review

STOP after this audit. A reviewer could authorize a bounded ESA command/metadata qualification and resolution of the 2026 validation-gated overlap before any experiment. That would need a pinned dataset release, receipt-time assumptions, an explicit decision on anonymized command semantics, healthy persistent-reference eligibility and exposed-label chronology. Mission-plan endpoints or retrospective annotations must not become runtime context. Alternatively review the controlled contract and its deliberately unsolvable cells. No next-stage execution is authorized here.
