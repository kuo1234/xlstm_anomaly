# Dataset inventory

Checked 2026-09-26. “Not verified” means the source reviewed for this audit did not establish the value; it is not a claim that the metadata does not exist elsewhere. No dataset archive was downloaded.

| Dataset | Coverage and shape | Labels and context | Audit class | Main reason / caveat |
|---|---|---|---|---|
| Drift-Aware AD in Smart Buildings (E-Energy 2026) | Three building-zone streams; 10 numeric channels plus timestamp and label; 1-minute observations; 87,010–98,141 rows per zone | Row label 0 normal, 1 normal drift, 2 attack. After-hours/weekend HVAC state and selected setpoint changes are labeled normal drift. Three zones and date ranges documented. | A, conditional | Direct semantic normal/drift/attack signal. Public repo has no explicit dataset license; no incident IDs, recurrence protocol, or verified fault-persistence intervals. |
| PreDist district-heating substations | 93 anonymized substations (35 M1, 58 M2); 10-minute sampling; 10–41 features depending on configuration; 239 substation-years, mean 2.6 years | Reported faults, maintenance/disturbances, approximate possible anomaly starts/ends, and author-designated normal-event intervals. Configuration metadata in current Zenodo v2. | B (possible A only after independent transition annotation) | Real-world normal-event vs service-fault evidence, but normal intervals are not a complete taxonomy of benign transitions; unreported faults and unannotated shifts are known risks. |
| Extended Tennessee Eastman Process (TEP) reference data | Six modes; 28 process faults; 500 random repetitions/fault; simulations to 100 hours, 3-minute sampling; six large HDF5 files, 132.96 GB total | Deliberate mode/setpoint transitions and simulated fault families. Exact channel count, aligned healthy/fault counterfactual streams, and event timing require schema audit. | A, simulation-only conditional | Controlled mode and fault semantics are promising, but synthetic process, very large release, and within-stream event contract not yet established. |
| NoBOOM | Six process sources; per-source 18–244 variables, sequences and lengths vary; industrial, pilot, lab processes | Fault-free train sequences; test labels distinguish normal and anomaly phases, including hidden/observable cause and post-removal residual effect. | B | Strong anomaly/event-phase benchmark and normal-only transfer material; no ground-truth benign regime-change class. |
| Batch Distillation Anomaly Detection | 119 laboratory runs; sensor/actuator logs at 1 second, with recipes and experiment metadata; current multimodal release about 95.2 GB | Fault-free and induced-anomaly runs; full-experiment split and rich process metadata. Recipes are largely separate runs. | B | Useful normal-only recipe/domain transfer and fault evaluation, but not continuous benign in-stream transition or recurrence labels. |
| NASA C-MAPSS | Simulated engine cycles; 26 columns per cycle (ID, cycle, 3 settings, 21 sensor measures); 100–260 training and 100–259 test engines across FD001–FD004 | Engines begin in nominal state and degrade to failure in train; test trajectories are censored with RUL targets. FD002/004 include six conditions; FD003/004 two fault modes. | B | Operating-condition and degradation transfer source, but no explicit benign-shift episodes or fault start/recurrence labels. Simulation; licensing/access portals conflict. |
| PATH powertrain benchmark | 16 channels, 10 Hz raw; 3,273 nominal discrete test sequences across 33 drive cycles; simulated parameter-change anomalies | Nominal sequences vary initial temperature/SoC and drive profile; six anomaly types, with sequence- or subsequence-level labels and counterfactual controls. | C for M6; B for isolated context transfer | Fault labels and contextual variability are useful, but data are separated drive-cycle runs, not a stream with semantically labeled benign transitions. Large release (13.6 GB). |
| SWaT | Water-treatment CPS; commonly described release has 51 channels, 1 Hz, 7 normal days and 4 attack days; papers report 36 or 41 attacks depending on release/version | Normal/attack protocol; access is request-controlled under iTrust terms. | B | Normal-only source and attacks, but no benign operating-regime ground truth. Channel/attack counts must be pinned to a particular release. |
| WADI | Water-distribution CPS; published release version descriptions differ in channel count (about 123/127); 1 Hz; 14 normal days and 2 attack days in the cited release | Normal/attack labels, 15 attacks in the cited 2018 description; request-controlled access. | B | Useful transfer and attack source, no semantic new-normal labels; version-specific schema required. |
| BATADAL | Simulated C-Town water network; training includes a year-scale normal run and a later partly/approximately labeled attack run | Attack-detection challenge labels; precise shape/sample cadence not established by reviewed challenge page. | B | Operating-time variation and attack labels, but no benign transition annotations; simulation and version details matter. |
| Google Borg ClusterData 2019 | Eight Borg cell workload traces; CPU-use histograms at 5-minute intervals; compressed release reported around 2.4 TiB | Job/resource/workload context; no fault or anomaly labels. | B | Rich workload shifts for unsupervised adaptation, no fault truth or benign-transition event labels; impractically large for this bounded audit. |
| UCI Electricity Load Diagrams 2011–2014 | 370 customers; 15-minute load series over 2011–2014; 140,256 timestamps (370 columns, 678.1 MB principal text file; 249.2 MB download bundle) | Calendar, seasonal and customer variation; no fault labels or benign regime annotations. | B | Can describe changing normal load distributions, cannot ground fault-vs-new-normal semantics. |
| DAYPSCI | Event-based PLC industrial CPS testbed with real hardware and digital twin; variable inter-event times, not fixed-rate samples | Normal/fault injection categories, event ordering, scan IDs, binary sensors/actuators and external configuration/runtime truth described in 2026 paper. | B, conditional | Rich causal event context for fault studies; no verified benign stable new-normal class, public access/license/size unresolved. |
| SMD (existing project anchor; no new audit access) | Existing project protocol fixes two machines and train/test partitions; this audit did not open additional labels | Anomaly detector anchor under M0; not an independently labeled benign-drift source. | C for M6 | Do not inspect unopened labels. Keep M4 fixed same-D leave-one-machine-out design; this audit does not alter its manifest. |

## Detailed observations

### Drift-Aware smart buildings

The paper and official repository describe three zones: L4, L14 MR1, L14 MR2. Row counts are respectively 97,062, 87,010 and 98,141. Each CSV has a timestamp, ten numeric sensor channels and a class label; the first 1,200-byte range probe showed one-minute timestamps. The paper reports the chronological collection windows and the three-class label semantics. It also reports 100 labeled sample anchors per class and 5,000 normal training samples, with remaining windows used for evaluation. The CSV class counts are in datasets.json. The source is the closest real-data match to normal-versus-benign-drift-versus-attack, but “attack” is an injected setpoint/control-logic event and should not be relabeled as generic equipment fault.

### PreDist

The current Zenodo v2 release describes 93 district-heating substations, variable sensor configuration, ten-minute records, and extensive maintenance/incident metadata. The README warns about unknown or unreported faults, long gaps, commissioning/maintenance in early records, and behavior changes not represented by a complete state-transition ontology. `normal_events.csv` denotes author-selected expected-normal intervals; `faults.csv` records incident descriptions and only approximate anomaly timing where possible. The data are valuable, but annotation completeness is not equivalent to ground truth for every regime transition.

### Extended TEP

The DTU publisher describes mode transitions, setpoint changes, process faults and six operating modes across a very large simulated release. It is a strong designed-scenario lead, but this audit did not download HDF5 files or verify array schemas. A follow-up should establish channel count, whether each fault has its own event timestamps and healthy counterpart on the same transition schedule, and whether the intended normal transitions recur within each stream.

### NoBOOM per-process inventory

The paper reports different feature counts, train/test sequence counts, and total steps per process; these differences make a single pooled sample-rate or “dataset length” misleading. Values below follow the paper's table; anomaly-run count and test anomaly prevalence are included to expose class imbalance.

| Process | Features | Train sequences / steps | Test sequences / steps | Test anomaly runs / prevalence |
|---|---:|---:|---:|---:|
| bpw | 18 | 28 / 189,444 | 63 / 395,712 | 77 / 21% |
| abm | 18 | 8 / 30,216 | 16 / 69,558 | 13 / 24% |
| wat | 20 | 15 / 57,284 | 11 / 37,250 | 20 / 25% |
| but | 34 | 7 / 2,390 | 8 / 4,082 | 24 / 41% |
| ome | 20 | 5 / 2,447 | 3 / 986 | 4 / 36% |
| ind | 244 | 8 / 215,841 | 16 / 1,842,436 | 361 / 17% |

These are per-paper process totals, not a claim of a fixed cadence common to all six. The test anomaly runs can be useful event-grouped detector outcomes, but they are not benign regime-change labels.

### Other transfer sources

NoBOOM, Batch Distillation, C-MAPSS, SWaT/WADI/BATADAL, Borg and electricity demand provide useful normal-only source domains or conventional fault/anomaly evaluation. Their data do not establish an allowed benign new-normal label aligned to a particular transition. PATH is an additional useful nominal-context/anomaly source, but its independent cycle structure prevents treating varied test runs as one continuously adapting stream.
