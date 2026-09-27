# P5-0B2R result-blind reviewer amendment

Status: Astra review PASS; terminal disposition `P5_0B2R_REFRAME` pending
Issue #9 adjudication of the disclosed initial path-metadata read. The four
amendments use P5-0B2 documents and pinned P5-0B1R structural names and role
counts. No operational values, label payloads, scores, or model outcomes
informed them.

## Amendments

1. **Freeze an absolute primary FPR ceiling.** Primary SOURCE pseudo-target
   and TARGET joint success requires READY within budget, normal-side
   pointwise FPR no greater than `PRIMARY_ABSOLUTE_FPR_CAP = 0.03`, and
   `eligible_fault_report_recall >= Recall_min_source`. The SOURCE fixed-N
   q90 is renamed `FPR_q90_source_fixedN_diagnostic`; it is diagnostic only
   and cannot relax the cap. Paper §4.4's normal-event pointwise accuracy of
   at least 0.97 motivates this operating ceiling, but event-averaged normal
   accuracy need not equal pooled timestamp FPR mathematically. The 0.03
   value is our frozen operating ceiling, not a guarantee. With no qualifying
   SOURCE candidate, use `SOURCE_MODEL_NOT_EVALUABLE` / the negative path.
   If every readiness candidate has zero SOURCE pseudo-targets satisfying
   all three primary joint-success conditions in a stratum, do not seal its
   tie-break winner; mark that stratum `SOURCE_MODEL_NOT_EVALUABLE`.

2. **Bound provenance language.** TARGET's class is
   `REFERENCE_CLEAN_PRIMARY`, described as a reference-clean commissioning
   prefix that is record-clean under available annotations. The absence of
   known fault, disturbance, or maintenance annotation does not prove physical
   normality; unlabelled faults may remain. This is not verified/known
   normality, and no `safe`, `certified`, or `guaranteed READY` claim is made.

3. **Reduce the projection using structural names only.** Exclude names ending
   `*_meter_energy` and `*_meter_volume`; retain temperatures and setpoints,
   control-valve position and setpoint, `*_meter_flow`, and
   `*_meter_heat_power`. Preserve ASCII lexical order. D in ASCII lexical
   stratum order changes from `[10, 13, 10, 14, 10]` to
   `[8, 11, 8, 12, 8]`. Recompute D-dependent `[4D, 2D]` encoder widths from
   the reduced projection. No CounterDiffTransformer or value-based
   reconsideration is introduced.

4. **Use one fault-report recall unit.** Each `faults.csv` row with
   `efd_possible=true` whose existing parsed interval overlaps suffix
   observations is one eligible report. Duplicate rows remain separate, with
   no semantic deduplication; a hit is any suffix score above the frozen
   threshold within the report interval. This is report-level recall, not
   unique physical-fault recall or the paper's repeat-filtered event set.
   SOURCE `Recall_min_source` and TARGET `eligible_fault_report_recall` use
   exactly this unit.

## Static projection check

The projection manifest retains all five strata and derives the listed D
values solely by filtering the pinned common-intersection names. No values,
labels, or operational files are used. The underlying role seal, roles/folds,
start, looks, Nmax, cap, purge, q99, minimum finite scores, candidate
families, firewall logic, and information sequence are not amended here.

## Verification-boundary disclosure

During initial integration, the inherited validator opened
`research/p5_0b1r/entity_manifest.csv` and parsed all `raw_path` strings for a
uniqueness check; it did not use any path to open an operational file. No raw
sensor value or semantic label payload was accessed. The final B2R validator
does not open the path-bearing entity/download manifests and checks their
committed digest tokens only. The scope of this path-metadata read is referred
to GPT via Issue #9; until adjudicated, P5-0B3 is not authorized.
