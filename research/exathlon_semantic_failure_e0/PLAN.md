# Exathlon E0 Semantic Failure Audit Implementation Plan

> **For agentic workers:** Execute this audit inline with superpowers:executing-plans; the independent prior-art search uses superpowers:dispatching-parallel-agents. No model experiment is implicit in this plan.

**Goal:** Determine what Exathlon lifecycle failures are identifiable from released labels and scores, preserving RCI versus EEI and reporting one Issue #25 gate.

**Architecture:** Immutable official source snapshots and ignored data cache feed separate coverage and artifact inventories. Prespecified lifecycle metrics reject missing timestamps/scores and overlapping events. Audit/protocol freeze is committed and pushed before any conditional baseline execution.

**Tech Stack:** Bundled Python, pandas/numpy, stdlib CSV/JSON/zipfile; no benchmark dependency installation during audit.

**Spec:** [Issue scope](provenance/issue25_scope.json).

## Global Constraints

- E0 only; no new model, controller, selector, smoothing method, domain generalization variant or hyperparameter sweep.
- Preserve historical P4/P5/M0-S/D0 artifacts; write only this directory, keep native raw data ignored.
- No test anomaly labels for training, calibration, threshold or model selection.
- RCI includes its endpoints; EEI is strictly after root_cause_end through extended_effect_end. Missing EEI is absent, not zero score.
- Process-failure point RCI is a timestamp, not a positive-duration interval. Missing causal score availability is not model failure.
- Small strata, shared executions, crash censoring and normal-context support remain explicit.
- Commit A freezes metrics, source/coverage/prior-art and any conditional panel. Commit B reports evidence and gate; push/reply Issue/STOP.

## Review Focus

1. Point RCI or skipped timestamp cannot be called an effect-only failure.
2. Event overlap cannot assign one score/alarm to two scientific instances unnoticed.
3. Missing EEI and crash/no recovery cannot be converted into normal recovery.
4. Thresholds and score timestamps must be from normal-only fit/calibration with causal availability.
5. Generic known Exathlon/DIVAD failure must not become a novelty claim.

### Task 1: Immutable source and ground-truth reality check

**Files:** provenance/source_inventory.json, *_tree.json, wiki_sources.json; scripts/sources.py, audit_data.py; results/event_coverage.csv, type_app_context_coverage.csv, normal_trace_support.csv, source_status.json.

**Interfaces:** Official ground_truth.zip and repository tree -> audited events and trace identity/context inventory; no score field inferred from labels.

- [ ] Pin both repos and archive ground-truth SHA256; acquire only bounded timestamp/feature inspection samples when necessary.
- [ ] Check unique traces, interval ordering, zero-duration RCIs, unknown/no-effect cases, overlap, normal/type/context support and published-count discrepancies.
- [ ] Compare original versus DIVAD split/label/downsampling/feature treatment; distinguish source metadata from inspected raw bytes.
- [ ] Expected: every GT row maps to a released trace; unsupported raw/context checks remain UNKNOWN.

### Task 2: Artifact/prior-art inventory and metric freeze (Commit A)

**Files:** DATA_GROUND_TRUTH_AUDIT.md, TYPE_APP_CONTEXT_COVERAGE.md, PRIOR_ART_OVERLAP.md, SCORE_ARTIFACT_INVENTORY.md, FAILURE_METRICS.md, provenance/protocol.json; scripts/lifecycle_metrics.py, test_metrics.py.

**Interfaces:** Task 1 support tables + official output searches -> declared score requirements and conditional run decision.

- [ ] Inventory repos/releases/notebook cells/wiki for actual per-trace scores, models, thresholds, timestamps and AD1–AD4 tables; code that generates an output is not an output.
- [ ] Fix F1 medians/separation and normal-calibrated alarms, F2 raw score and alarm continuity, F3 normal trace location/scale and thresholds, F4 cluster-aware aggregation before reading any detector result.
- [ ] Write/run failing metric contract tests, implement functions, rerun tests: point/missing/overlap/censoring and no fabricated measurement.
- [ ] Record prior-art overlap from primary sources and bounded search; NOT_FOUND_IN_SCOPE is not novelty evidence.
- [ ] Freeze and push audit/protocol. Training conditional: only after concrete verified input/split/environment/causal-score manifest. If these prerequisites cannot be sealed, record DATA_OR_ARTIFACT_INSUFFICIENT, not invented experiments or a substitute native model.

### Task 3: Authorized evidence analysis and final gate (Commit B)

**Files:** ROOT_CAUSE_EFFECT_ANALYSIS.md, CALIBRATION_ANALYSIS.md, FRAGMENTATION_ANALYSIS.md, FINAL_GATE.md, README.md; results/failure_decomposition_status.json; provenance/verification.json.

**Interfaces:** Frozen metric definitions + admissible score manifest (if available) -> event-level measurements; absent manifest -> explicit unmeasured cells and concrete bounded rerun prerequisites.

- [ ] Compute only admissible evidence. A bounded rerun is necessary if missing scores prevent F1–F4, but do not train until the required complete causal inputs, normal splits and native runtime are verified.
- [ ] Report one gate with evidence, remaining unknowns and what makes inference invalid; distinguish data identifiability from a measured detector failure.
- [ ] Verify source hashes, coverage arithmetic, local report links, deterministic replay, tests and tracked scope; inspect figures if any.
- [ ] Fresh independent review of scope/methodology, resolve material findings, then commit/push; confirm remote SHA and clean tracked state; reply Issue #25 and STOP for reviewer.
