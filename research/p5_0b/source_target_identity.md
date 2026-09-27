# Source detector / held-out target identity

P5 core identity is:

```text
source-entity data -> frozen source detector -> held-out physical target
    -> chronological reference-normal prefix -> READY
    -> same target's sealed future normal/anomaly evaluator after N_max
```

A different sample ID, fault event, operating setting, farm, or same-entity later block is not automatically a held-out physical target. A target split must be fixed without evaluator outcomes.

| Candidate | Physical source/target entity split | Existing detector relation | Assessment |
|---|---|---|---|
| PreDist v2 | 93 substation IDs; within-M1 or within-M2 disjoint split possible; same utility limits domain | No frozen source-trained detector is in this repo; one would be specified/trained only in a later authorized phase | Closest retrospective entity-disjoint candidate; label-blind manifest can freeze identity/time structure but cannot prove suffix normal/fault label coverage |
| CARE v6 | 36 turbines; asset IDs permit same-farm held-out turbine split; farm transfer also changes schema/domain | WindADBench documents held-out turbine and cross-farm benchmark tracks; its detectors are benchmark runs, not an existing locked P5 source model | Historical/event-level design only; timestamp alignment across event files limits continuous acquisition claim |
| WindADBench | No new entities/data; it points to CARE | Benchmark harness only | Mechanics only; cannot count as separate source dataset |
| COLDSTART + voraus-AD | One Yu-Cobot cell; PRE_A/PRE_B are setting variants, not separate robots | Current protocol’s “source/target” setting comparison does not hold out a physical unit | Fixed-N mechanics; original dataset permits single-unit chronological retrospective replay only |
| AURSAD | One UR3e screwdriving setup; no unit IDs | No cross-unit detector transfer | Mechanics only |
| SMD / M1 | 28 machine IDs, but common feature semantics are undocumented | Stage1A/Stage1B-R models/scores are fitted per machine and evaluated source-native on that same machine | Existing outputs are not target recommissioning; mechanics-only. See M1 protocol and manifest at frozen SHA in [candidate audit](dataset_admissibility.md) |

## Required Track A identity if PreDist is later approved

- **Source entities:** a predeclared set of substations; entity membership and manufacturer/configuration role frozen using metadata only.
- **Target entities:** disjoint physical substations held out from source fitting/selection; exact IDs remain `TO_BE_FROZEN_BEFORE_EXECUTION`.
- **Detector:** score function and preprocessing frozen after source-side qualification; target prefix cannot update weights/representation.
- **Target prefix:** only a predeclared chronological reference-normal interval; normal status may be retrospectively established for this replay, but must not be described as known prospectively at deployment.
- **Evaluator:** same target’s strictly later suffix after common `N_max`; normal/fault masks are evaluator-only and opened after all READY outputs and thresholds are sealed.

This identity is not yet admissible: the separately authorized prefix-normal adjudication and suffix evaluator sequence has not been demonstrated, and label-blind metadata alone cannot prove suffix normal/fault coverage. If PreDist cannot provide the frozen sequence without consulting future labels to choose IDs/cuts, it fails this identity and P5-0C remains blocked. P5-0A M1 artifacts cannot fill the source-detector role: they are outputs from same-machine source-native detectors, not a source detector transferred to held-out target.
