# Dataset qualification and final gate

**ADMISSION_BENCHMARK_READY** — P4-A only, pending Issue #17 review.

| Gate | Evidence | Boundary |
|---|---|---|
| Controlled timing truth frozen prospectively | e07b0b19093ce90b98c3d8f265e43867a054322a; five physical seeds, 15 streams, five independent read-only A probes, deterministic finite ramp | M2N2-style independent generator, not exact official generator reproduction |
| Settled endpoint independent of results | First target parameter law at transition+256, no detector/CV/loss used | Settled stochastic periodic law, not literal constant signal or physical safety |
| Real masked persistent drift group | 14/15 native-mapped SMD machines; 46/47 non-simulated candidates under frozen max-feature criterion | Cause/legitimacy UNKNOWN; mean sensitivity only8/15 SMD; historically exposed labels |
| Concrete prior-art overlap | M2N2 EMA and masked gradient; CANDI curated buffers, delayed updates and anomaly-selected counters; gated MemStream and conditional LODA semantics | Delayed selective updating is already prior art; novelty unresolved |
| Admission metrics fixed | FAR, purity, formal acceptance, censoring, effective baseline exposure, transition burden, anomaly and old-normal retention | Actual policy instrumentation/metrics NOT_RUN; native baseline formal TTAccept N/A_NATIVE |

Controlled native inputs consist of X, monotonic sample clock and A-only scaler. All arm IDs, seeds, events, settled times and truth stay outside the future runtime interface. Tests verify generator prefix causality, train-only scaler, invalid mixed payloads, exact semantic twins, original mask batches and classification support. They are data-contract tests; no online detector score-before-write execution or baseline instrumentation was tested in P4-A.

The semantic fault twin is exactly the benign X with opposite normative admission truth. An X-only deterministic policy must make identical decisions on both; paired randomized policies with matched randomness also have identical decision distributions. Thus universal legitimacy is unidentifiable without additional context. This does not make the controlled evaluator undefined: ground truth exists and failure can be counted, including unavoidable disagreement. The benchmark cannot claim that this evidence gap has been solved. Future P4-B must preserve the twin and avoid acceptance success claims that hide it.

## Provenance / access status

M2N2 official pin616b2270b6f2eab88ee5caa37c45507d2d041d22: no LICENSE in tree, UNKNOWN; original code not redistributed. Original injected anomalies can depend on full-series extrema, so this independently implemented finite-ramp protocol freezes analytic A severity and explicit timing. Same broad sinusoidal/amplitude/offset/noise mechanisms are traceable, not byte-equivalent.

CANDI official pin28c9679e503832f59e351208cde63657fcb51cad: modified MIT Non-Commercial with Permission. StrAD official pin7078876bbd9398481a65c22b7689702ce9e0d558: AGPL3 plus original notices. Exact source URLs, bytes, SHA256 and acquisition UTC in provenance/source_files.json. HAL full paper blocked by Anubis; no access bypass.

Official existing TSB archive SHA2567de86ac27f30eeb48d833bb061055670e3f3de07defd995cf2bd5db10ccc9a0d checked, every used CSV compared to historical manifest. 75 CD=1 entries retained, 28 simulated excluded, all47 others audited. SWaT here is a publicly released TSB derivative; original restricted raw source availability/terms are not certified. No new SWaT raw download, fork or mirror.

Raw observations and all labels were historically acquired/read in M0. No strict confirmatory claim. New masked access started 2026-10-04T17:31:08.022144+00:00 after freeze commit was pushed, remote SHA verified. Complete access chronology is provenance/qualification_access_log.json. No local raw download.

## Next step requiring reviewer task

If accepted, propose P4-B on all five physical controlled groups: frozen detector versus pinned M2N2 (native ordering and any named causal variant reported separately), CANDI-style selective adaptation and minimal quarantine/admission. Pre-register actual mutation instrumentation, baseline B-write endpoints and censoring before model results; preserve no-write and semantic-twin controls. Assess false normalization versus finite valid acceptance delay and retention, not just AP/F1. Real TSB remains only drift/fault robustness with no admission timing truth.

No P4-B/model/policy training, detector score, threshold tuning, memory writes or RL ran. Old P2 seal and previous experiment content were preserved.
