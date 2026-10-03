# Semantic label audit

## Required distinction

A changed distribution is an observation. “Allowed new normal,” “transient anomaly,” and “persistent fault” are semantic judgments that need independent operational evidence, such as an operator-approved mode/recipe, external command or maintenance record, explicit injection protocol, or reviewed incident annotation. A large run of anomalous samples is not by itself an incident identity, and a normal-only training interval is not by itself a labeled benign transition.

For a full M6 evaluation, the ideal annotation contract is per-stream transition IDs and times; allowed regime identity and external command/context; benign/transient/persistent classes; fault/event IDs and start/end or censoring; old-regime return (A→B→A) labels; stable-new-normal intervals; and fixed, event-disjoint train/test membership. No reviewed source establishes this entire contract in a released and licensed dataset.

## A — semantic new-normal candidates

### Drift-Aware AD in Smart Buildings (conditional, real data)

The paper explicitly labels normal (0), normal drift (1), and attack (2). The examples distinguish after-hours/weekend system shutdown and selected setpoint changes from office-hour malicious setpoint changes paired with valve inconsistency. This is unusually direct evidence that the authors distinguish intended schedule/operation changes from attack behavior.

The labels are per sample. The documentation reviewed does not expose stable incident IDs, event start/end conventions, recurrence IDs, or persistent-fault status. The attack generation uses repeated fixed-interval setpoint toggling and reports frequent valve actuation; it is better described as a control-logic attack than a generic machine fault. The paper's train/evaluation construction is documented, but we did not verify an event-disjoint split or whether all evaluation windows are independent events. Dataset license is absent from the official GitHub repository metadata and no LICENSE file was found. Class A therefore means “direct semantic class candidate,” not M6-ready or reusable without resolving terms.

### Extended TEP (conditional, simulation only)

The publisher describes six operating modes, setpoint transitions and 28 simulated process faults with repeated trials. A documented simulator protocol can give stronger causal labels than observational archives and can distinguish a legitimate operating-mode change from an injected fault in principle.

Before assigning any M6 result, inspect the small readme/schema and verify transition timestamps, the healthy mode-change trajectory, exact fault start/persistence, repeat/event identifiers, recurrence, and fixed split. This audit did not download or inspect large HDF5 arrays; those requirements remain unresolved. Label it Class A only as a designed-scenario candidate, never as real-world evidence.

## B — adaptation or transfer, not semantic new-normal truth

### PreDist (conditional, real data; also B for transfer)

The dataset README separates author-designated normal-event intervals from faults and maintenance/incident records. Fault records include descriptions/problem categories, possible anomaly start/end, and training ranges. The README explicitly acknowledges incomplete incident reporting, unlabeled changes, long gaps, commissioning effects and sensor faults. This provides a second semantic source for testing whether labeled normal operating/maintenance-related intervals can be separated from reported faults.

However, “normal event” intervals are safe/expected normal windows, not a complete ontology saying a particular distribution change is an approved regime transition. Possible fault starts/ends are approximate and can be unavailable; incident IDs, persistence, recurrence, and counterfactual behavior are not assured. A subset-specific annotation audit would be mandatory before an M6 claim. On current evidence it is Class B. Upgrade to a Class A candidate only if a particular allowed transition is independently identified and linked to the corresponding fault/event timeline; its normal-event and fault annotations alone do not meet Class A.


- **NoBOOM:** fault-free training sequences and labeled anomaly phases (including observable/hidden cause and residual effect after cause removal) support anomaly detection and cross-process normal-only transfer. There is no separate benign transition class.
- **Batch Distillation:** fault-free runs, recipe/setpoint metadata, and induced anomalies support domain/recipe transfer. Different recipes are generally separate experiments; no in-stream approved transition label is established.
- **C-MAPSS:** varied operating settings and simulated degradation support transfer and prognostics. Nominal initial wear/manufacturing variation does not identify a benign regime transition; fault onset is not an explicit per-cycle event label in the reviewed description.
- **SWaT, WADI, BATADAL:** normal/attack protocols support detector baselines and normal-only transfer. Attack presence is not a benign-shift semantic label; version-dependent schemas and gated data limit reproducibility.
- **Borg ClusterData 2019:** workload/resource variation is valuable for normal adaptation studies, but there is no fault or anomaly truth.
- **UCI Electricity Load Diagrams:** seasonal/customer load patterns can test distribution-change sensitivity, but no fault or allowed-shift event ground truth exists.
- **DAYPSCI:** controlled fault injection plus external configuration/runtime state supports causal sensor/actuator fault analysis. The reviewed description does not label a stable benign new-normal regime or recurrence.
- **PreDist for transfer:** its `normal_events` and reported fault records support normal-event/fault transfer studies, but it remains Class B until a specific allowed regime transition is independently established. Do not infer every unlabeled period is normal.

## C — detector-only for this question

- **PATH:** anomaly scenarios and nominal variability are documented, but the nominal variation is spread over independent drive-cycle sequences. A sequence boundary is not a benign regime-change event. It can be a detector/context robustness dataset, not direct evidence for online transition handling.
- **SMD:** the project's fixed anchor has anomaly labels, not an independently labeled benign transition set. This audit did not access still-unopened labels and does not amend the M0 or M4 protocol.

## What would change the status

Status could advance only after an independent annotation/provenance review verifies a licensed, version-pinned subset with benign transition identity, fault episode identity and duration, aligned external context, recurring regimes, and event-disjoint evaluation. A source that only demonstrates shift magnitude does not satisfy this criterion. A list of high-quality detector datasets does not substitute for these semantics.
