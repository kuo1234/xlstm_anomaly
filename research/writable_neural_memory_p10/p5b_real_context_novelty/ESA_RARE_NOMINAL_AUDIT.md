# Rare nominal event audit — not new-normal truth

All **78 Mission1 +613 Mission2 =691** rare-event IDs individually recorded in [rare_nominal_audit.json](provenance/rare_nominal_audit.json). Unit: mission + source event ID, not channel rows. Anonymous Class/Subclass stays anonymous; no physical taxonomy inferred from length, priority, repetitions or timestamp.

| Mission | All-category interval rows | Unique IDs | Rare IDs | Anomaly IDs | Rare median union span | Max envelope | Rare IDs overlapping anomaly in time | Same-channel overlap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|1|3589|200|78|118|12h10m|23.7287d|11|4|
|2|11167|644|613|31|53m06.006s|2.0250d|5|0|

M1 also has four Communication Gap IDs. M2's604 plan-event rows do not equal its613 rare IDs; no mapping invented.

Duration=end-start, not sample count. Union merges overlapping channel intervals; envelope goes from earliest start to latest end. Annotation span is not settled-regime exposure. Temporal anomaly overlap uses merged rare intervals; same-channel overlap additionally requires common channel and intersecting source intervals. Source anomaly is not demonstrated unsafe state. No-overlap is not certified health.

## A2: per-event taxonomy

Every JSON row separately records taxonomy, old nominal support, changed-condition support, duration, command alignment, anomaly overlap, receipt and reference eligibility. **690 IDs remain UNKNOWN** for transient/reset-calibration/command-correlated/persistent-regime classification. M1 id_55 alone has paper-backed command correlation. No case qualifies as persistent healthy reference. Rare Event retains source nominal intent but lacks the narrower settled-reference contract.

[ESA paper](https://arxiv.org/abs/2406.17826), supplementary Table4/Figures9,20,21, describes id_55 as a unique command execution and id_155/id_159 as lengthy events with difficult timing. Its general rare-event definition includes resets/calibration but does not map every anonymous ID to an activity or persistent state.

## Adversarial eligibility examples

Longest rows are order statistics from fixed all-ID enumeration, not selections for a detector run.

| Mission / ID | Metadata envelope | Same-channel anomaly | Source-backed eligibility |
|---|---:|---|---|
|M1 id_14|23.7287d|id_179|Long nominal coexists with anomaly; changed reference UNKNOWN |
|M1 id_180|17.2171d|id_181|Same issue; channel rows not independent opportunities |
|M1 id_21|16.1341d envelope, 8.3970d union in2 intervals|none|Disjoint intervals cannot imply continuous settlement |
|M1 id_55|point,0s|none|Command-correlated point, not persistent support |
|M1 id_155|11.0713d|none|Long slow event; repeatable healthy reference/causal delivery UNKNOWN |
|M1 id_159|10.8770d|none|Long annotation, settled support UNKNOWN |
|M2 id_298|2.0250d|none|Anonymous activity; reference UNKNOWN |

id_14/id_180 caution against equating valid intent with fault absence. Any future context benchmark must allow fault under valid command, missing context under benign change, and identical available (X,C) under different hidden legitimacy. Source fault and unsafe operation stay separate.

**Qualified persistent cases:0 established, not0 asserted to exist.** No model, feature search, classification threshold, or favorable-interval search.
