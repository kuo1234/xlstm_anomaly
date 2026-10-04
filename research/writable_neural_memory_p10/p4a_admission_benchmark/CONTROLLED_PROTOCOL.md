# Frozen controlled admission protocol v1

Issue #17 GO is protocol/dataset qualification only. No detector, learner, policy, memory write or P4-B runs. Config, code, metrics and literal schedules are committed/pushed before full stream smoke/label-masked TSB analysis.

## Traceable generator and admissibility semantics

Reference: carrtesy/M2N2 pinned616b2270b6f2eab88ee5caa37c45507d2d041d22, data/univariate_generator.py and multivariate_generator.py. They expose sinusoid/cosine noise/offset/amplitude and anomaly injection, but do not specify new-normal admission timing. Some outlier functions use full-series extrema or two-sided local std. We do not execute/copy those outlier functions; this is an independently implemented traceable M2N2-style extension, not an official benchmark reproduction. Pinned M2N2 tree has no LICENSE: record UNKNOWN and do not redistribute its code.

For each point t and channel j:
x[t,j] = amplitude[t,j]*(sin(2π frequency[j] t + phase[j]) + .05 epsilon[t,j]) + offset[t,j].
epsilon is independent standard normal from NumPy PCG64 SeedSequence([physical_seed,0]). Ramp weight=clip((t−start)/256,0,1); amplitudes/offsets are convex A/B interpolation. Fixed functions use current t and epsilon only: no reset, AR infinite settling tail, rolling future statistic, outcome-selected seed or empirical variance threshold.

Dimensions4, length6144; A-fit[0,1024), A-calibration[1024,1536), evaluation[1536,6144). A parameters, affected dimensions0/1/2, B parameters, five native seeds and exact per-run schedules are in controlled_config.json. NORMAL_A → BENIGN_TRANSITION[start,start+256) → NORMAL_B_SETTLED[start+256,...), with two disjoint TRUE_ANOMALY_UNDER_B episodes: additive+3 analytic A SD on channel0 for128 samples, −3 analytic A SD on channel1 for512 samples. Severity uses sqrt(a_A²/2+(a_A*.05)²), not measured test statistics.

t_settled_B is exactly start+256, the first point generated fully by the intended B periodic/noise law. Settled here is completion of a deterministic parameter change into a cyclostationary law, not flat signal or physical process safety. Normality is normative generator intent, not a proof inferable from X. Episodes and endpoints are evaluator-only. BENIGN_TRANSITION is label-anomaly0 but not yet eligible for a settled-B reference cohort.

Scaling: fit per-channel mean/population SD ONLY initial1024 A observations; std<1e−8 gets scale1. All channels retained, no clipping, no test-normalizer fit. Calibration interval is reserved for a future frozen detector protocol; no threshold fitted here.

## Arm roles, counterfactual and observability boundary

Five seed groups each produce: primary benign-B-with-anomalies; primary stationary-A-with-matched-anomalies; mandatory secondary semantic-fault-twin. Stationary control has no B admissibility truth. The twin reuses EXACT benign-arm observations but labels the deviation from transition start onward as a non-benign persistent fault. This tests the information limit: any X-only causal policy must make identical decisions for the pair, so universal safe admission is impossible without extra normative/context information. It is not a solvable classification challenge and is never pooled as independent N or hidden after failure.

Primary arms exercise post-B anomaly assimilation and adaptation cost under the declared synthetic intent. They do not prove a persistent deviation is legitimate in deployment. We keep the indistinguishable fault alternative visible; benchmark readiness means evaluable/falsifiable, not a promise it can be solved safely. No external context labels are added to the runtime interface.

Runtime only x_t/time/initial scaler; no arm/seed/event/onset/settled metadata, no labels, no future points. Schedules differ across seeds; future implementations must not hardcode known schedules. Five physical groups,15 counterfactual streams, not N=15. This P4-A contains no learned model/selection/admission policy.

## Evaluator action semantics and fixed readouts

WAIT is the normative lower-bound action before the settled target law for unsettled B cohorts. PROMOTE_ALLOWED after settled applies only to fully label-clean settled-B payloads. DISCARD_REQUIRED for anomaly/non-benign payloads. The evaluator never supplies those truths to policy; generated truth is not deployed safety truth. A timestamp≥settled cannot make a mixed trailing buffer admissible.

Candidate B identity is policy-local; evaluator maps a formal commit to the post-transition opportunity by its explicit point-ID payload, not an oracle runtime regime ID. Commit timing, unique written points, repeated/weighted loss exposure and every mutable state path are logged separately. Selecting/queuing samples is not an admission.

Formal TTAccept requires a real explicit regime commit. Native M2N2/CANDI have no such event, so report N/A_NATIVE and separate time-to-first-B-effective-exposure/FPR recovery; do not quietly rename first SGD to regime acceptance. Raw max(0,commit−settled) is reported alongside premature/invalid indicators; it cannot reward an early wrong commit as a valid zero-delay success. Valid acceptance coverage is censored at each run's first B anomaly onset. Late acceptance is secondary, with the original censor disclosed.

Independent512-point A probes use RNG stream2; only future read-only snapshot evaluation, never adaptation. Old-normal retention differs from recurrence. A→B→A is not generated in primary; recurrence metric is N/A. No outcome-oriented rescue or primary seed drop.

All evaluator metrics/denominators/censoring are in metrics_contract.json / METRICS_CONTRACT.md. P4-B requires a new GO and its own baseline/causality/protocol seal; this task runs dataset smoke only.
