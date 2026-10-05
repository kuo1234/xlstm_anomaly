# Issue #25 — Exathlon Semantic Failure Audit E0

**DATA_OR_ARTIFACT_INSUFFICIENT — method design withheld; STOP for reviewer.**

This audit preserves native root cause intervals (RCI), extended effects (EEI), unknown events, crash censoring and context support. It answers what can be identified from public artifacts before assigning a detector failure or selecting a new method. [Issue #25](https://github.com/kuo1234/xlstm_anomaly/issues/25) authorizes E0 independently of the stopped M0/D0 hypotheses; historical P4/P5/M0-S/D0 results are unchanged.

| Artifact | Purpose |
|---|---|
| [DATA_GROUND_TRUTH_AUDIT.md](DATA_GROUND_TRUTH_AUDIT.md) | Native fields, timestamps, overlap, crash and downsampling |
| [TYPE_APP_CONTEXT_COVERAGE.md](TYPE_APP_CONTEXT_COVERAGE.md) | Complete type×app coverage and normal support |
| [PRIOR_ART_OVERLAP.md](PRIOR_ART_OVERLAP.md) | Primary-source occupancy and modern artifacts |
| [SCORE_ARTIFACT_INVENTORY.md](SCORE_ARTIFACT_INVENTORY.md) | Released-output search and bounded rerun prerequisites |
| [FAILURE_METRICS.md](FAILURE_METRICS.md) | Prespecified measurement definitions |
| [ROOT_CAUSE_EFFECT_ANALYSIS.md](ROOT_CAUSE_EFFECT_ANALYSIS.md) | F1 identifiability and unmeasured score fields |
| [CALIBRATION_ANALYSIS.md](CALIBRATION_ANALYSIS.md) | F3 support/occupancy limits |
| [FRAGMENTATION_ANALYSIS.md](FRAGMENTATION_ANALYSIS.md) | F2 score-contract limits |
| [FINAL_GATE.md](FINAL_GATE.md) | Single evidence gate and STOP |

Evidence:109 native annotation events across34 disturbed traces;59 undisturbed runs; seven bounded raw archives inspected, no detector scores recovered. Prior-art inventory reads seven primary papers and official code; bounded absence is not novelty. The declared gate is not proof of model success/failure. Source checksums, full coverage, conditional run decision and unmeasured fields are retained.

[Plan](PLAN.md), [protocol](provenance/protocol.json), [scope](provenance/issue25_scope.json) and provenance ledgers are the review record. Raw assets stay in ignored data/exathlon_e0_sources. The source loader downloads only hashed snapshots and seven43MB raw inspection archives, not the full3GB repository. It does not execute model code.

```sh
E0_PY=/Users/kuo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
$E0_PY research/exathlon_semantic_failure_e0/scripts/sources.py
$E0_PY research/exathlon_semantic_failure_e0/scripts/audit_data.py
$E0_PY research/exathlon_semantic_failure_e0/scripts/readout_trace.py
$E0_PY research/exathlon_semantic_failure_e0/scripts/test_metrics.py -v
$E0_PY research/exathlon_semantic_failure_e0/scripts/reports.py --final
```

No score resampling, interpolation, future fill, native-runtime parity, training/normal calibration or scientific detector failure is silently declared complete. A bounded rerun is needed to produce admissible evidence, after a concrete execution seal; this E0 branch does not invent scores from figures, reconstruct anomaly detector outputs from telemetry or replace native baselines with unverified imitations.
