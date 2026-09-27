# P5-0B2R2 result-blind non-degeneracy amendment

**Review state:** Astra review is PASS; terminal status is
`P5_0B2R2_PROTOCOL_RESEALED`. The prior P5-0B2R seal remains superseded.
P5-0B2R2 performed a result-blind protocol reseal only. This terminal status
authorizes only the P5-0B3 SOURCE-only development/source
model-readiness-parameter seal. TARGET labels, raw values, scores, prefix
adjudication, suffix evaluation, and efficacy remain unauthorized.

This result-blind amendment adds a predeclared non-degeneracy floor while
retaining the prior report-level metric, FPR cap, candidate grid, and
structural projection. It does not access semantic labels, operational sensor
values, model outcomes, or TARGET evaluation data.

## Frozen structural inputs

The controlling base is commit
`758c48b23e54bd775a71bc0542fb008cd7e2e426`. The P5-0B1R role seal is pinned
by SHA-256
`00e0cec62d238c78f2d0b3c79910c0ffaf1122d1582c28c8848022fb3e10e33f`.
The fixed inventory is 74 SOURCE, 16 TARGET, and 3 unsupported entities in
five exact eligible `(manufacturer, configuration_type)` strata. Target starts
remain the first raw-row timestamps. Acquisition uses raw timestamped rows at
looks 144, 288, 576, 1152, and 2304; `N_max=2304`, elapsed cap 64 days, primary
purge 0, and the common suffix starts strictly after raw observation 2304.
Hashes for the referenced P5-0B1R structural artifacts are recorded in
`structural_inputs_seal.json`.

`feature_projection.json` freezes a deterministic ASCII-lexical projection
from each eligible stratum's committed common intersection. In ASCII-lexical
stratum order, projected D changes from `[10, 13, 10, 14, 10]` to
`[8, 11, 8, 12, 8]` after excluding `*_meter_energy` and `*_meter_volume`.
It retains temperatures/setpoints, control-valve positions/setpoints,
`*_meter_flow`, and `*_meter_heat_power`. No counter transform or value-based
reconsideration is introduced.

## Frozen primary outcomes

The absolute primary future-normal pointwise FPR ceiling is
`PRIMARY_ABSOLUTE_FPR_CAP = 0.03`. `FPR_q90_source_fixedN_diagnostic` is
diagnostic only and never controls or relaxes that cap. Freeze
`PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR = 0.50`. Define
`Recall_min_source_q10` as the type-7 q10 of SOURCE fixed-N eligible
fault-report recall, giving each evaluable SOURCE pseudo-target task equal
weight, and define
`Recall_min_effective = max(0.50, Recall_min_source_q10)`. Every SOURCE and
TARGET primary joint-success gate requires READY within budget, future-normal
pointwise FPR no greater than 0.03, and
`eligible_fault_report_recall >= Recall_min_effective`.
If every readiness candidate has zero tasks satisfying the full joint gate in
a stratum, mark that stratum `SOURCE_MODEL_NOT_EVALUABLE`; do not seal the
tie-break winner, lower either floor, relax the FPR cap, or change the
candidate grid. The 0.50 floor is a predeclared protocol non-degeneracy rule;
this amendment makes no claim that it comes from or is equivalent to any
paper-reported 60% result.

Each `faults.csv` row with `efd_possible=true` whose existing parsed interval
overlaps suffix observations is one eligible report. Duplicates remain
separate; this report-level metric is not unique physical-fault recall and is
not the paper's repeat-filtered event set. The same unit defines
`Recall_min_source_q10`, `Recall_min_effective`, and TARGET evaluation.

## Selected detector reference

The specified commit `ced470e1386066931bad32f3cb6e24bac9c5bb89` is EnergyFaultDetector
v0.7.1, not v0.3.0. The paper-cited v0.3.0 tag resolves to
`9e0d65074c88e51e180e3bf37f580280bbb54496` and does not contain the later
PreDist loader. The primary reference is explicitly corrected to v0.7.1's
generic dense autoencoder and row-wise RMSE components. The event-specific
PreDist loader/protocol is excluded. See `detector_backbone_audit.md`.

## Phase boundary

No source or target semantic label payload, operational sensor value, model
outcome, TARGET score, prefix eligibility result, or PreDist model is accessed
or produced in this phase. Public code/docs and the pinned P5-0B1R role/schema
metadata are used. The previously disclosed path-only metadata read is
classified for this reseal as
`RAW_PATH_METADATA_READ=STRUCTURAL_METADATA_DEVIATION`; it did not cross a
semantic boundary or expose an outcome:
`SEMANTIC_BOUNDARY_BREACH=NO` and `OUTCOME_LEAKAGE=NO`. No operational
manifest content, data, or label payload is opened by this amendment. TARGET
label access, scoring, prefix adjudication, suffix evaluation, and efficacy
claims remain unauthorized. The terminal
`P5_0B2R2_PROTOCOL_RESEALED` status authorizes only the P5-0B3 SOURCE-only
development/source model-readiness-parameter seal.

The fixed TARGET counts across the five strata are `5, 1, 4, 4, 2`. The
pooled success denominator remains all 16 entities, and unavailable outcomes
count as failures; there is no minimum suffix-evaluable count per stratum.
An unavailable SOURCE model or frozen margin bars a pooled claim.

## Artifact map

The normative documents and their hashes are listed in `protocol_seal.json`.
`canonical_sequence.md` defines the only permitted phase order. The
P5-0B2R2 reseal records the floor, reviewer clearance, Astra disposition, and
the restricted next-stage authorization.
