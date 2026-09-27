# P5-0B2 label-boundary protocol design

This is a design only. P5-0B1R does not execute any of these steps or authorize
label access.

1. **Seal structural roles and starts.** Hash and freeze
   role_split_seal.json, the entity manifest, and the schema/horizon
   summaries. Every eligible target start remains the timestamp in its first
   raw data row. An invalid first timestamp means NOT_EVALUABLE; it is never
   replaced with a later valid timestamp. No target, source, start, cut, or
   horizon may be changed after seeing eligibility or outcome information.
2. **Reviewer freezes the schedule.** Before prefix adjudication, an
   independent reviewer specifies the exact look schedule, maximum
   commissioning horizon (N_max), purge, and fixed suffix boundary. This
   structural audit does not select them.
3. **Independent prefix-only adjudication.** A separate adjudicator receives
   only the predeclared target prefixes and approved prefix-status sources.
   The adjudicator must not open the fixed suffix or any event/fault outcome
   payload.
4. **Minimal adjudication output.** The adjudicator emits only
   ELIGIBLE or NOT_EVALUABLE plus a provenance hash. The output contains no
   label, event, or suffix summary.
5. **Freeze detector and readiness rule.** Freeze the Track-A detector,
   preprocessing, look schedule, readiness rule, and all thresholds before
   trajectory computation.
6. **Compute and seal trajectories.** Compute normal-side trajectories only
   from the eligible prefix. Seal their code, inputs, and outputs before any
   suffix is unlocked.
7. **Independent fixed-suffix evaluation.** A separate evaluator opens only
   the fixed suffix labels after steps 1–6 are sealed. The evaluator receives
   no authority to change targets, starts, cuts, or horizons.
8. **Compute outcomes.** Compute the predeclared future normal-risk and
   reported-fault outcomes from the fixed suffix. Keep outcome access and
   scoring separate from readiness decisions.

Any failed prefix check, insufficient suffix, or provenance failure produces
NOT_EVALUABLE. It never permits replacing a target or moving a start, cut,
or horizon. A future label-boundary breach requires stopping and recording
the incident; it does not permit an independent restart.

## Current recovery boundary

P5-0B1R opens only approved configuration/feature metadata and exact
allowlisted raw operational members. It does not inspect normal_events,
faults, disturbances, maintenance/report/event/anomaly labels, or any future
outcome field. Structural availability is not normal coverage, prefix
eligibility, detector readiness, or efficacy.
