# Fixed-suffix evaluation and success contract

**P5-0B2R2 state:** Astra review is PASS; terminal status is
`P5_0B2R2_PROTOCOL_RESEALED`. P5-0B2R2 performed a result-blind protocol
reseal only. This terminal status authorizes only the P5-0B3 SOURCE-only
development/source model-readiness-parameter seal. TARGET labels, raw values,
scores, prefix adjudication, suffix evaluation, and efficacy remain
unauthorized.

## Information wall

The method process never receives suffix features, suffix scores, semantic
labels, event boundaries, or evaluator-only metrics. A separately permissioned
evaluator can unlock target suffix annotations only after the target
eligibility output, model/readiness seal, and all target score/READY
trajectories have been sealed. Evaluation cannot change detector, threshold,
readiness rule, target membership, target starts, acquisition horizon, or
eligibility.

## Suffix and labels

The suffix is raw rows 2,305 through the entity's final raw row; primary purge
is 0. A suffix outcome is evaluable only when suffix timestamps are valid and
nondecreasing in raw-row order (duplicates are allowed), the full suffix is
available, the annotation sources parse completely, and the normal/event
support gates below pass. The evaluator uses only the predeclared annotation tables and interval
normalization listed in the prefix contract, plus the same pinned structural
role/start seal. Eligible fault-report recall uses each `faults.csv` row with
`efd_possible=true` whose existing parsed interval overlaps at least one suffix
observation as one report. Duplicate records are retained separately without
semantic deduplication. A report is hit if any suffix score strictly exceeds
the READY threshold within its interval. This report-level unit is not unique
physical-fault recall and is not the paper's repeat-filtered event set; it is
identical to the unit used for `Recall_min_source_q10` and
`Recall_min_effective`. Future-normal FPR uses `normal_events.csv` intervals minus all
fault and disturbance intervals; only timestamped suffix rows inside that
remaining union are denominator points. `disturbance` rows are not counted
as separate eligible fault reports. Report annotated-normal coverage as the count of
future-normal observations divided by all suffix observations, alongside the
metric denominators. An outcome is suffix-evaluable only if the full suffix
is available, all three annotation sources parse completely, there are at
least 100 future-normal observations, and at least one eligible fault report.
Ambiguous,
unparseable, or incomplete suffix label provenance is `NOT_EVALUABLE` for that
evaluator outcome; it does not remove the target from the eligibility or
never-ready denominator and does not authorize a replacement.

## Required metrics

- **Primary anomaly-side outcome:** eligible fault-report recall (`eligible_fault_report_recall`): the fraction of
  eligible fault reports with at least one score strictly above the frozen
  READY threshold within the report interval.
  Report the number of reports and entities in each denominator.
- **Primary normal-side outcome:** pointwise future-normal FPR, false alarms
  divided by evaluator-confirmed normal suffix observations. Normal points
  are inside `normal_events.csv` intervals and outside every fault and
  disturbance interval. Also report
  false alarm episodes as a secondary operational summary, using a new
  episode after at least one non-alarm point. Do not substitute AP/AUROC for
  threshold-dependent outcomes.
- **Secondary anomaly timing:** detection delay in raw observations and
  elapsed time from each eligible report interval start to its first alarm. Unhit
  reports are right-censored at interval end and separately counted.
- **Acquisition cost:** both raw observation count at READY and elapsed days
  from the pinned first raw timestamp to READY. The primary scalar is
  `C=0.5*(raw_count/2304 + elapsed_days/64)`. For never-ready entities and
  prefix- or suffix-ineligible entities, report the fixed censoring point and
  assign `C=1` for both methods. Retain all 16 TARGET entities in every
  joint-success denominator.
- **Source detector qualification/background:** source-fold AP and AUROC
  only. Do not report TARGET AP/AUROC as the primary result or use them to
  tune any rule.

Report every one of the fixed 16 TARGET entities separately. Macro FPR and
eligible fault-report-recall summaries use only suffix-evaluable entities and state their
denominators; report micro numerators and denominators as well. Joint success
uses all pinned TARGET entities in each exact stratum as its denominator.
Prefix-`NOT_EVALUABLE`, targets in a stratum without a sealed SOURCE model or
margins, never-ready, and suffix-evaluator-ineligible entities are failures
for both the sequential method and fixed-N comparator and are never dropped
or replaced. For an entity where prefix or suffix evaluation is unavailable,
assign both methods the conservative maximum normalized acquisition cost of
1; otherwise include the observed cost for both methods.

## Frozen success logic

Before target prefix adjudication, the source-only seal fixes per-stratum
`Recall_min_source_q10` as the type-7 q10 of SOURCE fixed-N eligible
fault-report recall and defines
`Recall_min_effective = max(0.50, Recall_min_source_q10)` using the procedure
in `readiness_rule_contract.md`. Freeze
`PRIMARY_ABSOLUTE_FPR_CAP = 0.03` and
`PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR = 0.50`. Primary TARGET joint
success is READY within budget AND future-normal pointwise FPR <= 0.03 AND
`eligible_fault_report_recall >= Recall_min_effective`. The q90 statistic is
never a primary cap and never relaxes 0.03; the recall floor is never lowered
by a source result. If no SOURCE candidate qualifies, follow the
`SOURCE_MODEL_NOT_EVALUABLE` / negative path. Never-ready counts as not successful. Prefix-`NOT_EVALUABLE` and
suffix-evaluator-ineligible cases also count as not successful for both
methods. The primary fixed-N comparison is READY
at raw row 2,304 and applies the same source model, q99 estimator, target
prefix, suffix, annotations, and margins. Compare target-specific rules to
fixed-N over all 16 pinned TARGET entities; no entity-level result can be
removed after outcomes are exposed. An unavailable model/margin makes its
stratum unresolved and bars the five-stratum pooled claim as specified below.

The fixed TARGET counts in ASCII lexical stratum order are `5, 1, 4, 4, 2`.
The primary dataset-level paired comparison always uses all 16 fixed TARGET
entities. A prefix-ineligible, suffix-evaluator-ineligible, never-ready, or
otherwise unavailable outcome is a failure with acquisition cost `C=1`, so
the pooled success fraction does not condition on evaluator availability.
There is no minimum per-stratum suffix-evaluable count: imposing four in each
stratum would make the predeclared five-stratum claim impossible by design.
Report FPR and eligible fault-report-recall metrics for every evaluable entity/stratum with
their actual denominators, including zero or small denominators; these
conditional metric summaries do not replace the fixed-population success
denominator.

The sequential procedure supports the predeclared fixed-cohort empirical
efficiency claim only if the entity-stratified paired bootstrap 95% percentile
interval for the success-fraction difference (sequential minus fixed-N) has
lower bound at least 0, and the corresponding interval for mean
acquisition-cost difference has upper bound below 0. Resample all TARGET
entities with replacement separately inside each of the five exact strata,
preserving each stratum's fixed TARGET count and the paired method
outcomes/costs. For each replicate, in stratum order, draw `n_s` indices with
replacement from `0..n_s-1` using `Generator.integers(0, n_s, size=n_s)`;
compute each replicate's means over the fixed 16-entity denominator. Sort
each stratum by opaque role digest; process strata in ASCII lexical
`(manufacturer, configuration_type)` order; use one NumPy `Generator(PCG64)`
initialized with seed `20260927`; and compute the 2.5th and 97.5th percentile
interval endpoints with type-7/linear quantiles from 10,000 replicates. The
one-target stratum is necessarily degenerate under this fixed-stratum
bootstrap; report the interval as a small-cohort empirical summary, not a
population generalization or FPR guarantee. If a SOURCE model or frozen
margins are unavailable for any stratum, report the affected fixed entities
and stratum as unresolved and make no five-stratum pooled success claim.
The 0.03 ceiling is our frozen operating ceiling. Paper §4.4 reports
normal-event pointwise accuracy >=0.97 as motivation, but event-averaged
normal accuracy is not necessarily mathematically identical to pooled
timestamp FPR. This empirical logic is not a future-FPR guarantee. The 0.50
recall floor is a predeclared protocol non-degeneracy rule; this contract does
not claim that it comes from or is equivalent to any paper-reported 60% result.

No stopping-rule revision, margin change, new target class, endpoint
selection, or alternative success condition is allowed after any target
eligibility or suffix outcome is seen. Any revision requires a new versioned
protocol before outcome access.
