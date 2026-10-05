# Prospective E0 failure metrics — frozen before any detector results

Exact rules are in provenance/protocol.json and scripts/lifecycle_metrics.py. No detector result, model, threshold or selected test subset was inspected. The helper is tested on artificial boundary fixtures only; it does not train or score telemetry.

RCI=[start,end], including point events. EEI=(end,effect_end], absent if no effect endpoint. Pre-RCI and recovery windows are300 native seconds, excluding all labeled event support; recovery right-censored at trace end. Shared event times are excluded from unique attribution and counted. Coverage uses the epoch-zero native1s grid, including absent timestamps; off-grid score timestamps are rejected. Overlap exclusions count expected native instants even if unobserved, with observed overlap counts reported separately. No observed root alarm with incomplete RCI evidence is N/A, not false. Score absence, future availability, native missing times, mixed-phase sampled bins and zero normal scale are explicit non-estimability, never model failure.

| Metric | Fixed definition |
|---|---|
| Root-Cause Capture | Any eligible causal raw score strictly above normal-only threshold during RCI; report eligible support, normal FPR and duration-matched normal false-alarm capture alongside |
| Effect-Only Detection | Complete eligible native RCI evidence, none alarm; eligible EEI alarm exists. Incomplete RCI or missing EEI -> N/A |
| Detection Delay | First causal event alarm minus RCI start only with full native event support/no ambiguous overlap; first observed partial alarm stored separately |
| RCI-vs-EEI contrast | (median RCI − median EEI) / heldout normal calibration IQR; zero IQR -> N/A |
| Pre-RCI contrast | (median RCI − median pre-RCI normal) / same fixed scale |
| Raw continuity | Median absolute adjacent score change / normal calibration IQR, only contiguous valid native timestamps |
| Alarm fragments | Runs of score>threshold, consecutive native1s timestamps; missingness breaks runs |
| High-score run length | Native seconds in each alarm run; longest run + support counts |
| Within-event dropout | Valid phase scores at/below threshold divided by eligible scores; missing score fraction separately |
| Normal calibration | Median/IQR/quantiles, normal heldout FPR by trace/app/context; global vs app threshold only where app ID is available |

Threshold = normal-validation score quantile0.995, linear quantile interpolation. Fit/validation/calibration are normal-only; helper refuses positive calibration labels. No test-anomaly threshold sweep, oracle winner or polarity change. App conditioning requires deployment-visible app ID and supported normal calibration. Per-trace test-label threshold, if ever diagnostic, is ORACLE and excluded from deployment results; none is computed here.

Any-alarm capture in a long interval can occur by chance at nonzero normal false-positive rate. Capture alone never supports a positive gate: raw phase separation and duration-matched heldout-normal alarm references must agree. A point RCI has one instant of score evidence, not a positive-duration scientific segment. Do not widen it into EEI or treat confirmation after onset as a root-time alarm.

Native AD1–AD4 are range-based union-label metrics, with AD3 favoring onset and AD4 penalizing duplicates. They cannot prove effect-only failure or replace RCI/EEI metrics. If later computed, retain native union secondary metrics and phase-specific primary metrics with identical split/scorer provenance. Report joint point AP and range/early/exactly-once behavior; do not choose a result-informed same-AP subset.

Aggregation is descriptive event/trace/app/context hierarchy; shared cluster executions and small1–2-event cells remain explicit. A positive gate needs repeated failure over multiple types/apps and distinct baseline families, no crash/sampling/threshold explanation, preserved raw-score separation, and a residual beyond original Exathlon/DIVAD. No iid p-value, windows-as-N, new model claim or automatic xLSTM choice.
