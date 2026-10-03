# Observable change vs semantic meaning

## Four separate inference questions

| Task | Question it answers | Required reference or assumption | What it cannot establish by itself |
|---|---|---|---|
| Shift detection | Has the statistical behavior of the stream changed? | A baseline, change model, or comparison window; adequate sampling and false-alarm policy | Whether the cause is benign, faulty, planned, or malicious |
| Anomaly detection | Is this observation or segment inconsistent with an accepted reference? | A declared normal distribution, conditional model, physical envelope, or labeled anomaly definition | That every low-likelihood point is a fault, or every familiar point is safe |
| Regime clustering | Which time segments have similar statistical behavior? | A distance/representation, clustering assumptions, and enough separation/data | Operational meaning; cluster IDs can be permuted without changing the clusters |
| Semantic regime classification | Is this behavior an authorized mode, a fault, maintenance effect, or attack? | Trusted labels/context, physical/causal constraints, intervention, or an assumption separating class-conditional laws | A distribution-free answer when semantic classes can share the same observable law |

A change-point may be an anomaly against the old model and normal under an authorized new mode. An anomaly score can correctly report surprise while semantic classification remains unknown.

## Signal-shift taxonomy

“Detect” below means detect relative to an available statistical or physical reference. A shift can be invisible to a chosen statistic even when the full distribution changes. Semantic classification always needs a link from signal behavior to operational meaning.

| Shift type | 1. Detect shift | 2. Detect anomaly | 3. Cluster regime | 4. Classify semantics |
|---|---|---|---|---|
| Mean / amplitude | Location change is testable with enough data | Compare to fixed or context-conditioned limits | Cluster by level or amplitude profile | Needs recipe, setpoint, or load context |
| Variance | Variance change is testable, subject to sample size | Compare with expected conditional variability | Cluster variance/noise profiles | Needs workload, environment, phase, or sensor-noise context |
| Trend | Slope/change-point methods can detect a trend change | Compare with an expected trajectory or rate bound | Cluster slope and trajectory shapes | Needs planned-ramp, maintenance, workload, or failure context |
| Periodicity / frequency | Spectral or cycle statistics can detect changed frequency | Compare with the expected cycle | Cluster spectra and cycle signatures | Needs machine speed, schedule, recipe, or production phase |
| Cross-channel correlation | Test changed dependence in the joint series | Check against a reference dependency model | Cluster relationship profiles | Needs mode, topology/configuration, and validated channel meanings |
| Phase relation | Detect altered lag or phase relationships | Compare synchronization with physical/control constraints | Cluster phase/lag patterns | Needs synchronization source and production-step context |
| Covariance | Estimate a changed joint covariance under sample assumptions | Use conditional covariance or physical residual limits | Cluster covariance states | Covariance shift does not reveal cause; requires context or validated causal constraints |
| Temporal dynamics | Compare transition law, autocorrelation, or response dynamics | Check against an identified plant/controller model | Cluster dynamic regimes | Needs operating mode, setpoint, controller/configuration, and often excitation |
| Missingness | Detect a changed missing-data rate/pattern | Anomaly only if those measurements were expected to arrive | Cluster telemetry-availability patterns | Needs maintenance, network, sensor-health, and sampling context |
| Calibration | Detect a changed measurement map if a reference exists | Compare against calibration standards or redundant measures | Cluster instrument states | Needs calibration records, check standards, or independent reference measurement |
| Workload | Detect a change if load is represented in observations | Often expected after conditioning on measured workload | Cluster load/throughput regimes | Needs orders, schedules, production counters, or resource allocation |
| Topology | Detect schema or channel-map changes; graph change if observed | Test expected graph/physical constraints | Cluster configuration graphs | Needs time-valid asset-management and configuration history |

This taxonomy distinguishes a statistically observable change from a semantic explanation. For example, an amplitude increase may be a detectable mean shift; whether it is an anomaly depends on an operating envelope; clustering can assign it a new group; “authorized high-load mode” requires workload/command context.

## Important qualifications

- Mean and variance equality do not imply process equality. Temporal dependence, phase, and cross-channel relationships may still distinguish two statistical regimes.
- Conversely, changed marginals do not prove different semantic causes. A fault can reproduce the full joint, temporal law of a valid mode.
- Statistical anomaly is reference-relative. If the reference model is contaminated or does not condition on operating mode, the score may call an expected mode anomalous.
- Clusters are representations of similarity. A semantic name attached after clustering comes from context, labels, process rules, or human knowledge.
- Change detection can be consistent only under a stated sampling model and enough signal. It does not guarantee useful detection delay or low false-alarm rate in every finite stream.

Liu et al. discuss the practical similarity between sudden concept change and anomaly, while also distinguishing change-point detection from point anomaly detection. Their algorithm illustrates a possible method under its modeling assumptions; it does not remove the semantic identifiability limit. NIST manufacturing work uses data-driven models, physics-based models, multiple setpoints, and subject-matter expertise to separate expected process anomalies from cyberattacks. See sources.md.
