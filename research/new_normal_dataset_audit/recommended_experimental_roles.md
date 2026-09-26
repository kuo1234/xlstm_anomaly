# Recommended experimental roles

These are research-design recommendations only. No model run, dataset download, or expansion of the M0 protocol is authorized by this audit.

## M6 semantic evaluation

1. **Primary follow-up: E-Energy Drift-Aware Smart Buildings, conditional.** It is the strongest direct real-data lead because the authors label normal, normal drift, and attack separately and explain schedule/setpoint semantics. First resolve the dataset license, pin exact CSV hashes, obtain or construct independently reviewed event IDs and intervals from the paper's scenario protocol, and establish whether labels represent distinct episodes or repeated sample windows. Add recurrence and event persistence only if independently supported. If those cannot be established, report sample-level three-class results only and do not call it a complete M6 benchmark.
2. **Complementary real-data audit: PreDist.** Select a version-pinned set of stations/configurations with long, low-gap records; use explicitly designated normal events and reported faults only after manual/source verification. Preserve unknown and unreported periods as unknown. It may answer whether new-normal handling survives real service context, but current annotations do not fully identify benign transition episodes or recurrent regimes.
3. **Controlled synthetic benchmark candidate: extended TEP.** Consider only after a metadata/schema gate establishes exact mode-change and fault event IDs/times, healthy/fault matched trajectories, recurrence design, and manageable storage. Keep results separate from real-data evidence.
4. **Do not use detector-only datasets to claim M6 semantics.** NoBOOM, Batch Distillation, C-MAPSS and CPS attack datasets can be useful controls for faults, transfer or context, but their existing labels do not tell an evaluator that a particular unlabeled distribution change is permitted new normal.

For a true M6 experiment, freeze transitions and event IDs before fitting; split by complete stream/entity/event; keep external context and labels evaluator-only; include stationary normal, transient anomaly, persistent fault, benign A→B, A→B→A, and ambiguous cases; report stable-new-normal false-positive persistence, fault contamination/false promotion, detection delay, old-regime retrieval, censoring, and event-level uncertainty. Keep real and simulated outcomes separate.

## M4 normal-only transfer

The repository's M4 design remains same-dataset SMD leave-one-machine-out: exclude the target machine from source training, then use only verified target-normal prefixes or disjoint target-normal samples and later anomaly-labeled suffix. Count distinct raw observations and duration. None of the datasets in this audit replaces that anchor or authorizes touching SMD labels.

Potential **external normal-only transfer extensions**, only after a separate protocol and provenance review:

- **PreDist:** strong industrial external candidate when grouping by configuration/common schema; use explicit normal-event windows or independently verified normal prefixes, never all unlabeled observations. It remains Class B for M6 until a specific allowed transition is independently annotated.
- **C-MAPSS:** possible engine-to-engine normal-prefix transfer only if nominal-prefix boundaries can be established independently; its cycles and simulated engine entities are not comparable to SMD machines.
- **NoBOOM:** cross-process normal-only transfer with process-family-held-out splits; schema and sampling differ by source, so treat it as external stress, not same-D transfer.
- **Batch Distillation:** recipe/run transfer using confirmed fault-free runs and complete experiment splits; not streaming adaptation across recipes unless a stream protocol is independently defined.
- **SWaT/WADI/BATADAL:** potential CPS domain transfer after access and version pinning; their normal/attack labels do not supply benign new-normal truth.
- **E-Energy:** same-rate multichannel streams could support a separate building-zone normal-only transfer study once licensing is resolved, but zones are not machines and drift labels should not enter M4 selection.
- **ReCATS (protocol reference, not a dataset):** its known task boundaries and per-task normal-only training define a task-incremental comparison. The underlying data/license were not audited here, and its information setting differs from boundary-free normal-only adaptation; it does not change M4.

## Non-M6 detector/context controls

- **NoBOOM:** anomaly phase, observability and residual-effect controls.
- **Batch Distillation:** recipe-aware run-level anomaly detection.
- **PATH:** robustness to nominal drive-cycle contexts and simulated anomaly scenarios; keep each drive cycle separate.
- **SWaT/WADI/BATADAL:** conventional industrial/CPS attack detection baselines under their respective access terms.
- **C-MAPSS:** degradation/prognostics and condition transfer, not benign shift classification.
- **Borg/UCI electricity:** descriptive normal workload/load distribution variation only; no fault classification claims.
- **DAYPSCI:** event-based causal sensor/actuator fault analysis if data access and schema are resolved.

## Go/no-go guard

The audit's `SEMANTIC_M6_DATA_PARTIALLY_AVAILABLE` status is a discovery result, not permission to expand M0 or execute M6. Before a new experiment, require an explicit dataset manifest with file hashes, independent semantic evidence, license clearance, event-level split, and a reviewed annotation completeness table. If only distribution changes are available, restrict claims to adaptation/shift robustness.
