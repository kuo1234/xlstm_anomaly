# Canonical label and information sequence

The following order is mandatory. A later stage cannot begin until the prior
stage's required artifact and review are sealed.

1. **Structural role/schedule seal.** Reuse the immutable P5-0B1R role, start,
   schema, and horizon inputs pinned in `structural_inputs_seal.json`; do not
   change target roles, starts, looks, N_max, elapsed budget, purge, or suffix.
2. **Full method-development procedure seal.** Freeze the backbone,
   preprocessing/score, source folds and candidates, prefix decision,
   readiness grid and objective, threshold, evaluation/success logic, and
   information boundary. This P5-0B2 directory is that seal.
3. **Source-label firewall seal.** Freeze firewall source/dependencies,
   synthetic tests, output schema, and hashes before it reads a label table.
4. **SOURCE-only development and model/readiness seal.** Execute the firewall
   and SOURCE-only procedure. Seal per-stratum schema/model/score artifacts,
   readiness parameters, margins, runtime, failures, and source metrics.
   TARGET remains unavailable.
5. **TARGET prefix-only adjudication.** A separate restricted adjudicator
   returns only `ELIGIBLE | NOT_EVALUABLE` plus a provenance hash per opaque
   role digest. It does not open the suffix or report reasons/counts.
6. **TARGET score/READY trajectory and seal.** Score only adjudicated
   eligible prefixes, obeying raw looks and elapsed cap. Retain every one of
   the fixed 16 TARGET entities in the denominator; `NOT_EVALUABLE` receives
   no scores and is never replaced. Seal every produced score trajectory and
   READY/never-ready result, plus the complete fixed-population status map,
   before any suffix access.
7. **Suffix evaluator unlock.** Only now may a separate evaluator read the
   fixed suffix annotations after raw observation 2,304.
8. **Outcome scoring.** Compute only the metrics and success logic in
   `evaluation_contract.md`; no method or protocol changes follow.

Any information-boundary breach stops the affected stage, preserves the
record, and requires a versioned protocol amendment before resumption. A
reviewer or operator cannot convert a breach into a new start, target,
threshold, or horizon.
