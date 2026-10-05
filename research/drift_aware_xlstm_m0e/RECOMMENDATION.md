# Final recommendation

**Final gate: `ENGINEERING_FEASIBLE_RESEARCH_GO_WITHHELD`. STOP for external review.**

This is a deliberately narrower verdict than `STATEFUL_XLSTM_TRACK_FEASIBLE`: complete model-state capture and native-step carry are feasible on the pinned random CPU fixture, but a useful drift/staleness effect, a valid streaming forecasting checkpoint, and a sufficiently distinct scientific claim are **not established**. Closest supplied engineering category: `FEASIBLE_BUT_ARCHITECTURE_CHANGE_REQUIRED`; it must not be read as research GO. No evidence currently requires xLSTM as the backbone.

## What survives the attempt to falsify it

1. A genuine persistent inference object exists at the **upstream recurrent stack** level. Both stacks' full cell/conv states can be enumerated, copied and restored. Native full output vs recurrent output agrees numerically; chunk-delivered recurrent output/state and snapshot replay agree exactly on the small fixture.
2. The improved xLSTMAD is nevertheless window-local, and the old forecasting route is also window-local. Direct carry over overlapping windows is invalid. A disjoint-token wrapper can preserve improved reconstruction architecture; a one-step forecasting head/objective would be a new, separately trained track.
3. One can design a falsifiable compatible-versus-incompatible history experiment with frozen weights, identical recent suffixes and fixed-context controls. This is a **proposal**, not evidence of harm. State staleness must not be conflated with unsupported target regimes or indefinite-carry instability.

## What fails or remains unresolved

- Broad “adapt/reset state instead of weights” novelty fails against known work. HSO, recurrent forgetting/reset, TTT and Leto are strong precedents; RSI is a direct TSAD intervention threat. Exact full-method overlap remains unresolved for the closest partial-access sources. **Do not conclude no prior-art saturation.**
- Reset itself is context truncation. Any contribution must identify when incompatible history hurts and when useful history should remain, exceeding simple fixed/periodic context controls at matched information/compute/latency.
- TSB-drift has series-level drift metadata, not independent benign transition/recovery truth. Historical acquisition covers 75 multivariate released series, including 28 simulated-source series; current all-series acquisition is not re-established. Real post-drift recovery claims are unavailable on current evidence.
- API feasibility does not establish frozen-weight representational sufficiency, anomaly sensitivity after reset, long-run trained-model stability, or xLSTM advantage. The controller's drift-versus-fault ambiguity cannot be solved merely by observing persistence.

## Recommended next decision for the reviewer

First decide whether a **mechanism study rather than a new controller** is worth pursuing. Require resolution of RSI's complete method/chronology and the direct anomaly-triggered LSTM reset thesis lead (or explicitly accept a narrower claim that does not depend on their absence); resolve Leto's bibliographic/version status. If the intended contribution remains merely xLSTM + residual trigger + RESET, **STOP for insufficient differentiation**.

If the reviewer still sees a specific gap, request a pre-outcome protocol for an architecture-neutral controlled mechanism diagnostic. Prefer native reconstruction for the smallest architecture/parity comparator and an encoder-only one-step forecaster only if new training is explicitly authorized. Include LSTM/GRU, native forget gates, fixed-L replay, stationary long-run controls, oracle-boundary diagnostic and simple causal trigger controls. Freeze acceptable target-regime fit, meaningful effect size, false-reset/anomaly-harm bounds, recovery censoring and source/seed/multiplicity treatment before running anything. An oracle benefit is not a deployable policy result.

Do not begin by building a bank, soft retention, confidence controller, learned drift detector or RL system. Do not scan TSB labels for a promising architecture. Do not choose a historical checkpoint by downstream performance. If fixed-context controls explain all benefit or matched LSTM matches the effect, withdraw the xLSTM-specific/memory-policy claim and decide whether a negative or architecture-neutral result is worth reporting.

## Authorization stop line

This delivery completes Issue #22's audit artifact, not M1 and not the historical H3b experiment. The files in `reports/m0_protocol.md` and historical experiments are unchanged. No training, optimizer steps, TSB performance, labeled probe fitting, performance sweep, state bank, retention controller or scientific checkpoint execution occurred. A follow-up Issue comment must define the next bounded task and any required protocol amendment. Positive random parity provides no automatic GO.
