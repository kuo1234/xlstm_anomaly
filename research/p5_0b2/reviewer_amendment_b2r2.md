# P5-0B2R2 reviewer amendment

**Status:** Astra review is PASS; terminal status is
`P5_0B2R2_PROTOCOL_RESEALED`. P5-0B2R2 performed a result-blind protocol
reseal only. This terminal status authorizes only the P5-0B3 SOURCE-only
development/source model-readiness-parameter seal. TARGET labels, raw values,
scores, prefix adjudication, suffix evaluation, and efficacy remain
unauthorized.

## Scope

P5-0B2R2 repairs the non-degeneracy gate exposed during review. It retains the
P5-0B2R report-level eligible fault-report metric, the fixed candidate grid,
the `PRIMARY_ABSOLUTE_FPR_CAP = 0.03`, the feature projection, and all
structural role/schema constraints. No operational manifest content, sensor
data, semantic labels, target values, scores, or outcomes are used.

## Frozen recall floor

Freeze:

```text
PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR = 0.50
```

For each exact stratum, define `Recall_min_source_q10` as the type-7 q10 of
SOURCE fixed-N eligible fault-report recall across evaluable SOURCE
pseudo-target tasks, giving each task equal weight. Define:

```text
Recall_min_effective = max(
    PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR,
    Recall_min_source_q10,
)
```

Every SOURCE and TARGET primary joint-success condition requires READY within
budget, future-normal pointwise FPR at most `0.03`, and
`eligible_fault_report_recall >= Recall_min_effective`. The 0.50 floor is a
predeclared protocol non-degeneracy rule. This amendment does not claim that
the floor comes from or is equivalent to any paper-reported 60% result.

The eligible report remains one `faults.csv` row with `efd_possible=true`
whose existing parsed interval overlaps suffix observations. Duplicate rows
remain separate. A report is detected when any suffix score strictly exceeds
the frozen threshold inside its interval. This remains report-level recall,
not unique physical-fault recall and not the paper's repeat-filtered event
set.

## Negative-result behavior

If every readiness candidate has zero SOURCE pseudo-target tasks satisfying
the full frozen joint gate in a stratum, the stratum is
`SOURCE_MODEL_NOT_EVALUABLE` and follows the negative-result path. The floor,
the `0.03` FPR cap, and the candidate grid cannot be lowered, relaxed, or
changed to manufacture a success. An affected stratum bars a pooled
five-stratum success claim.

## Reviewer clearance

The review disposition is recorded exactly as:

```text
RAW_PATH_METADATA_READ=STRUCTURAL_METADATA_DEVIATION
SEMANTIC_BOUNDARY_BREACH=NO
OUTCOME_LEAKAGE=NO
```

The earlier path-only metadata read is treated as a structural metadata
deviation. It did not open operational files or expose semantic labels or
outcomes. No operational manifest content, data, or label payload is accessed
by this amendment.

## Authorized next stage

`TARGET_LABEL_ACCESS=NOT_AUTHORIZED` remains in force. The terminal
`P5_0B2R2_PROTOCOL_RESEALED` status authorizes only the P5-0B3 SOURCE-only
development/source model-readiness-parameter seal. TARGET labels, raw values,
scores, prefix adjudication, suffix evaluation, and efficacy remain
unauthorized. P5-0B2R2 records only the result-blind protocol reseal.
