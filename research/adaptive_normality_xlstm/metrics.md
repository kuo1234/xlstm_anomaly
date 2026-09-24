# Metrics and reporting rules

No single ranking metric answers whether an online detector is useful, sample-efficient or safe. Report score quality, event timing and update behavior separately.

## Detection

| Metric | Use | Reporting rule |
|---|---|---|
| Average precision / AUPRC | Primary ranking metric under rare anomalies | Report prevalence and exact point/event unit; avoid mixing window and timestamp AP. |
| AUROC | Secondary threshold-free ranking metric | Never use alone; it can look favorable under high false-positive burden and class imbalance. |
| Event-level precision/recall/F1 | Whether complete anomaly events are detected | Define event matching and overlap rule before evaluation. Report event counts and by-type values. |
| Point adjustment | May appear for compatibility with historical TSAD literature | Secondary only; it can inflate scores by crediting an entire event after one detected point. Show unadjusted scores alongside. |
| False-positive burden | Operational alert cost | Report false alarms per hour/day or per normal event, plus fraction of normal time in alarm. State threshold source. |
| Detection delay / onset latency | How late alarms occur after a true event starts | Report distribution by event type/duration, not only mean. Threshold and alarm persistence rule are frozen. |
| Recovery delay | How long alarm remains after anomaly ends or normal regime returns | Distinguish anomaly termination from benign regime transition; measure both. |
| Point and segment strata | Different anomaly structures stress different detectors | Report isolated point, short segment, long segment, contextual and persistent cases separately where labels support them. |

## Adaptation and safety

| Quantity | Operational definition |
|---|---|
| Target-normal sample efficiency | Number of unique confirmed-normal observations and elapsed time needed to achieve a prespecified fraction of full-target-reference performance. Give adaptation steps and data coverage too. |
| Adaptation compute/time | Wall-clock and number of optimizer/update steps on fixed hardware; include storage and forward pass count for multi-horizon models. |
| False adaptation rate | Fraction of update decisions or candidate promotions that use samples later labeled anomalous, computed only for offline evaluation. |
| Anomaly contamination rate | Anomalous samples or exposure time committed to protected normal weights/state, quarantine, shadow model and approved regime pool; report each separately. |
| False promotion rate | Persistent anomaly episodes promoted as normal divided by persistent anomaly episodes; also give benign promotion recall. |
| New-normal false-positive persistence | For a semantically confirmed benign change, time from change onset until normal alarm burden returns below a prespecified tolerance, plus residual alarmed fraction over fixed windows. This is a primary Problem B outcome. |
| Time to promote | Delay from verified benign mode onset to authorized promotion, measured under a rule fixed before test. |
| Time to reject persistent anomaly | Time from persistent fault/attack onset to a stable alarm or refusal to promote. Distinguish first alarm from candidate rejection. |
| Old-regime retention | When a confirmed historical normal regime recurs, score quality and retrieval delay relative to its prior reference. Include forgetting after intervening updates. |
| Rollback effectiveness | If a candidate is rejected, recovery of protected score calibration and detector behavior after rollback. |
| State contamination | Score degradation after anomalous history has entered a persistent state; compare reset, freeze, shadow and rollback policies. |

## Aggregation and uncertainty

- Keep machine, physical source, run and event as grouping units. Use cluster/hierarchical intervals or source-level paired effects, not timestamp IID intervals.
- Show per-machine/per-event values and the macro aggregate. A strong pooled metric cannot hide a target that fails catastrophically.
- For transfer, plot the full target-normal sample curve and the per-target curves. Do not summarize only the best N.
- For M0–M6, declare primary outcomes and acceptable margins before opening the final test labels.
- Thresholds must be selected on training/validation normal data or a clearly separate validation set. If anomaly labels guide thresholds, state that the detector is no longer fully unsupervised at that stage.
- Compare confidence intervals and practical thresholds; absence of statistical significance is not proof of equivalence.

## Forecast-specific score reporting

For each horizon h, compute residuals in the original or consistently normalized units and calibrate them using permitted normal validation data. Report horizon-wise residual/AP and preserve the vector as an evidence trace. Any max or combination score should use frozen per-horizon calibration and weights. Log forecasts made before x_t, later prediction errors, state writes and alarms to audit the prequential sequence.

Report point-anomaly versus segment-anomaly results and whether a segment becomes predictable after entering the context. Measure onset score before context contamination, score decay during an ongoing anomaly, and recovery after it ends.
