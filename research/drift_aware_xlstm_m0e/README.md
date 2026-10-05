# Issue #22 — M0-E stateful xLSTM architecture audit

2026-10-05. **`ENGINEERING_FEASIBLE_RESEARCH_GO_WITHHELD` — STOP for reviewer.**

Complete model-state carry/reset is feasible on a small pinned CPU fixture. The existing detector is window-local; a predictive streaming track needs a new contract/objective. Broad state-adaptation novelty has substantial prior-art collisions, and TSB-drift cannot independently validate exact benign-drift recovery. This audit is an attempt to falsify the proposed direction, not a justification to start M1.

Task source: [Issue #22](https://github.com/kuo1234/xlstm_anomaly/issues/22), which had no comments at initial retrieval. Its detailed body defines the current bounded task; [snapshot](provenance/issue22_scope.json). Read alongside [existing protocol](../../reports/m0_protocol.md). The Issue authorizes static inspection, primary-source audit and minimal unlabeled prototypes, not historical conditional H3b or scientific performance. Original experiment/report files are preserved.

## Review map

| Issue requirement | Artifact |
|---|---|
| A1 code/checkpoint/window reality | [ARCHITECTURE_REALITY_CHECK.md](ARCHITECTURE_REALITY_CHECK.md) |
| A2–A3 complete sLSTM/mLSTM and system-state boundary | [STATE_BOUNDARY.md](STATE_BOUNDARY.md) |
| B1–B3 scoring/interventions/context confound; G alternatives | [STREAMING_DESIGN_OPTIONS.md](STREAMING_DESIGN_OPTIONS.md) |
| C1–C3 parity/reset/causal-order feasibility | [PARITY_FEASIBILITY.md](PARITY_FEASIBILITY.md) |
| D collision audit, sources and unknowns | [PRIOR_ART.md](PRIOR_ART.md) |
| E dataset fitness, present vs historical evidence | [DATASET_FIT.md](DATASET_FIT.md) |
| F reviewer attacks and falsifiers | [RED_TEAM.md](RED_TEAM.md) |
| J defined final gate and stopping rule | [RECOMMENDATION.md](RECOMMENDATION.md) |

## Evidence summary

- Fresh pinned upstream source and PyPI wheel inspection: **40 source hashes match historical seals**; both reconstruction and original MSE forecasting inspected. No upstream patch.
- **19/19 random CPU API checks passed**, using nonzero scalar recurrent fixture weights; full native/recurrent output max difference `3.13e-7`, chunked recurrent output/full-state and serialization replay exact. Conv-history negative control differs by `0.1098`, proving that clearing only cell state is insufficient. No anomaly/dataset performance inference follows.
- Literature audit: **19 source entries**, including explicit partial/unresolved leads. Full-source search limits remain visible; no claim of exhaustive novelty clearance.
- Current pinned TSB metadata verified; raw-series dimensionality/eligibility is from historical byte audits, not a new download. Current archive HEAD403 is not proof all download routes fail.
- The local Phase F v4 seed11 reconstruction checkpoint's byte hash matches its manifest. It was **not loaded or evaluated**; it is not a forecast checkpoint.

Provenance includes [source hashes](provenance/code_sources.json), [probe output](provenance/state_probe.json), [runtime](provenance/probe_environment.txt), [dataset source ledger](provenance/dataset_sources.json), [literature search/source ledger](provenance/prior_art_sources.json) and [verification record](provenance/verification.json). Code/source and checkpoint evidence is current; historical dataset facts are explicitly marked. Source contents are evidence, not instructions.

## Scope of completed work

The independent audit directory is the only tracked change. Allowed random-input inference ran on CPU; no scientific checkpoint/model benchmark, optimizer, labels, training, learned observer, retention coefficient, bank or RL was used. Numerical parity is verified only for the documented fixture and runtime. Optimized chunk kernels, forecasting, asynchronous row resets, long streams and deployment-system snapshotting remain future gates, not hidden completed work.

Commit/push and an Issue summary are part of this delivery. They do not authorize experiments. Wait for the next reviewer task comment.
