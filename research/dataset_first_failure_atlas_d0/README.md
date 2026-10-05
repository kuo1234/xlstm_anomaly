# Issue #24 — Dataset-first failure atlas D0

**FAMILY_CONFOUNDED. D1_GO=false. STOP for reviewer.** Audited 2026-10-06.

The official oracle counts reproduce, but a source-family-balanced fixed panel still favors Online. All high-D Streaming candidates belong to OPPORTUNITY, and robust Streaming-win cases occur in only two families. Benchmark execution/availability semantics and raw-score provenance remain unresolved. The atlas provides reproducible descriptors and candidate trace cases; it does not establish a new method or causal adaptation benefit.

[Issue #24](https://github.com/kuo1234/xlstm_anomaly/issues/24) and [scope snapshot](provenance/issue24_scope.json) authorize D0 released-result/metadata reading, independently of prior M0 result-reading gates. No historical P4/P5/M0-S file is edited. [Analysis plan](ANALYSIS_PLAN.md) and [rules](provenance/analysis_rules.json) specify fixed methods, bins, margins and selection before sentinel selection.

| Requirement | Artifact |
|---|---|
| Benchmark modes, warm-up, score/time semantics | [STRAD_PROTOCOL_AUDIT.md](STRAD_PROTOCOL_AUDIT.md) |
| Origin, native identity, labels/duplicates | [DATA_PROVENANCE.md](DATA_PROVENANCE.md) |
| Q1–Q5 fixed-method failure map | [FAILURE_ATLAS.md](FAILURE_ATLAS.md) |
| Family/method/prevalence/duplicate checks | [FAMILY_CONFOUND_AUDIT.md](FAMILY_CONFOUND_AUDIT.md) |
| Methods/class/type/GPU/tuning/static deltas | [METHOD_FAMILY_ANALYSIS.md](METHOD_FAMILY_ANALYSIS.md) |
| Conditional accuracy/throughput fronts | [EFFICIENCY_PARETO.md](EFFICIENCY_PARETO.md) |
|12 conditional trace cases,10 families | [SENTINEL_SELECTION.md](SENTINEL_SELECTION.md) |
| Final conditions and STOP | [FINAL_GATE.md](FINAL_GATE.md) |

Evidence:180 exactly joined released rows;17 family groups;75 drift rows;19 Online/10 Streaming methods (Static includes one extra Donut).151 documented measured-family rows,28 simulated and1 unresolved-origin row. No series-iid p-value or window-as-N inference. Portfolio mean is not an ensemble, per-file maximum is ORACLE_ENVELOPE, and morphology uses label-derived metadata only as evaluation context.

Run from repository root with pandas/numpy using the bundled Python runtime returned by load_workspace_dependencies. Matplotlib is optional for figures; the bundled runtime lacks it, so the existing temporary analysis environment supplies only figure rendering. No benchmark dependency is installed or algorithm invoked. The only executed upstream bodies are two inspected wrapper input methods in no-model index spies.

```sh
D0_PY=/Users/kuo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
$D0_PY research/dataset_first_failure_atlas_d0/scripts/sources.py
$D0_PY research/dataset_first_failure_atlas_d0/scripts/atlas.py
$D0_PY research/dataset_first_failure_atlas_d0/scripts/check_patterns.py
$D0_PY research/dataset_first_failure_atlas_d0/scripts/semantics_trace.py
$D0_PY research/dataset_first_failure_atlas_d0/scripts/select_sentinels.py
$D0_PY research/dataset_first_failure_atlas_d0/scripts/reports.py
$D0_PY research/dataset_first_failure_atlas_d0/scripts/verify.py
# Optional figure refresh, using a Python environment with matplotlib:
python3 research/dataset_first_failure_atlas_d0/scripts/plots.py
```

Immutable inputs are in ignored data/d0_issue24_sources and refetched by URL/SHA validation. Results CSV/JSON, original source/archival hashes, no-model traces, complete method/stratum support and verification are committed. Full result tables remain available rather than favorable subsets only. Raw native series and model-score vectors are not acquired; sensitivity N/A is explicit. Review requires the saved sources/rules and final-gate evidence, not a claim of novel failure-policy design.
