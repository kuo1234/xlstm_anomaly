# Frozen admission metric contract
Machine-readable authority: metrics_contract.json (p4a-metrics-v1). This is evaluator design, not an executed policy.

All times are sample indices, intervals [start,end). Future P4-B must score from pre-update full state, emit an immutable alarm, decide, then update. Truth is evaluator-only. A native baseline with different ordering must be disclosed separately; changing it is a named causal variant.

| Endpoint | Denominator / censoring / interpretation |
|---|---|
| FAR-admit, primary | Negative episodes with at least one effective normality exposure / all negative opportunity episodes. Include each injected anomaly and semantic-fault episode; all paired variants share one physical seed group. |
| Contaminated admission purity | Unique invalid admitted IDs / all unique admitted IDs; zero writes = N/A_NO_WRITES. Report repeated/weighted loss exposure separately. |
| Formal TTAccept | max(0,formal commit minus generator settled_B), with premature and invalid payload flags separately. Primary valid acceptance is clean settled-B cohort before first B anomaly; no success = right-censored at first anomaly, not dropped. |
| Native baseline endpoints | No explicit regime commit = N/A_NATIVE for formal TTAccept. Separately first B effective write, first wholly clean-settled-B exposure and FPR recovery; none proves acceptance. |
| Premature admission | Formal B commit before settled_B. A commit after settled time containing transition/fault IDs remains invalid, even if not premature. |
| Transition FP burden | Count, rate, duration on legitimate transition and settled-B clean points until formal commit or censor. Native baseline exposure-aligned burden is separate. |
| Post-admission anomaly retention | Unadjusted point/event recall and delay on fixed B events after valid acceptance; no prior valid acceptance = N/A with coverage. Compare identical events with frozen detector. Baselines use separately labelled exposure-conditioned results. |
| Old-normal retention | Independent read-only A probe FPR before/after valid commit; never used for adaptation, no state side effects; no valid acceptance = N/A. |
| Recurrence reactivation | Secondary N/A: no A-return stream in initial protocol. |
| FPR recovery | Supplementary clean settled-B alarm-rate trajectory at original timestamps; no post-hoc recovery cutoff or conversion to formal acceptance. |

A write means effective persistent mutation of normality memory, model/adapter/optimizer, scaler, calibration, or reference state. Track all paths separately plus their union, exact contributing point IDs, and nonzero loss weights. Buffer selection is pending, not automatically committed exposure. Per-update contamination and whole-segment formal admission are separate outcomes.

An always-WAIT policy may have zero false admissions but acceptance coverage zero, censored delay and undefined purity: not successful adaptation. A formal PROMOTE does not override invalid payload truth. Report all five physical groups and stationary/twin controls; no window/update/variant inflation of N. Episodes within a group are correlated.

TSB has no legitimate-settled or acceptance timing truth; corresponding metrics are NOT_EVALUABLE. Anomaly/disturbance truth is not unsafe truth. Semantic twins have identical X but opposite normative admissibility: report the unavoidable disagreement, without claiming an X-only universal safety solution.

The user explicitly confirmed splitting formal acceptance from baseline first-write/FPR recovery; see provenance/metric_decision.json.
