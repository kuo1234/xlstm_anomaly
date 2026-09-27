# Readiness-rule development and selection contract

**P5-0B2R2 state:** Astra review is PASS; terminal status is
`P5_0B2R2_PROTOCOL_RESEALED`. P5-0B2R2 performed a result-blind protocol
reseal only. This terminal status authorizes only the P5-0B3 SOURCE-only
development/source model-readiness-parameter seal; TARGET labels, raw values,
scores, prefix adjudication, suffix evaluation, and efficacy remain
unauthorized.

## Rule boundary

The anomaly score and model are frozen by the detector/source-model seal.
Readiness consumes only finite score values from the currently released
prefix, the fixed source-fitted score scale, and the scheduled look index. It
cannot consume target labels, event metadata, future observations, suffix
scores, or target-specific structural detail. It cannot alter the detector
or retroactively change earlier decisions.

Readiness is a normal-side empirical commissioning decision. It is not a
certificate, a future-FPR guarantee, or an anomaly-discrimination guarantee.
No neural stopper, Meta-RL, learned controller, or naive maximum/fusion rule
is in the candidate set.

## Shared look eligibility

Evaluate rules only at raw looks 144, 288, 576, 1,152, and 2,304, subject to
the 64-day cap. A look is score-supported only when the cumulative prefix has
at least 200 finite scores and the most recent 64 finite scores exist. A
finite score requires at least one observed numeric feature in its raw row;
all-missing rows are invalid scores but remain in the raw count. Unsupported
looks are `NOT_READY`. The raw-144 fixed-N candidate is consequently always
unsupported by the 200-score minimum; retain it as a declared candidate and
record `NOT_READY`. Once `READY`, do not revise the decision or take a new
look for that entity.

## Frozen candidate grid

All distances use the finite RMSE score sequence in raw chronological order.
The source-only score IQR (`IQR_SOURCE`) is calculated from the selected
detector candidate's five SOURCE out-of-fold pseudo-target streams, restricted
to SOURCE observations outside known fault/disturbance intervals, using
float64 type-7 `Q75-Q25`. It is frozen with the source model/readiness seal.
No other detector candidate's score stream contributes to this scale. The
grid is deliberately finite:

1. **Fixed-N baseline:** READY at each one of the five looks, if supported.
2. **Always-ready baseline:** READY at the first supported scheduled look.
3. **Maximum-horizon baseline:** READY only at raw look 2,304, if supported.
4. **Threshold stability:** At a look, compute the empirical q99 threshold on
   the entire finite prefix. Compare it only with the immediately preceding
   scheduled look's supported threshold. A transition is stable when both thresholds are
   positive and `abs(log(tau_current / tau_previous)) <= eps`, where `eps` is
   one of `{0.01, 0.025, 0.05, 0.10}`. A zero/negative threshold is an
   unsupported transition. An unsupported/unstable transition resets the
   run. The initial supported threshold is not a transition. Require 2 or 3
   consecutive stable transitions.
5. **Score-distribution stability:** Compare the latest 64 finite scores with
   the immediately preceding 64 finite scores. The two-sample KS statistic is
   the maximum absolute difference between their right-continuous empirical
   CDFs over the pooled distinct score values (no p-value). A look is stable
   if it is at most one of `{0.05, 0.10, 0.15, 0.20}`. Require 1 or 2
   consecutive stable looks; an unsupported or unstable look resets the run.
6. **Prefix-internal hold-forward exceedance:** Estimate q99 on all finite
   scores before the last 64, then compute the fraction of the last 64 above
   that threshold. A look passes if this fraction is at most one of
   `{0.01, 0.025, 0.05, 0.10}`. Require 1 or 2 consecutive passing looks.
   At least 128 earlier finite scores and 64 recent finite scores are
   required. An unsupported or failing look resets its consecutive-pass run.
7. **Marginal-gain plateau:** Compare medians of the preceding and latest
   64 finite scores; pass when absolute median change divided by
   `max(IQR_SOURCE, 1e-12)` is at most one of `{0.05, 0.10, 0.20, 0.40}`.
   Require 2 consecutive stable looks; an unsupported or failing look resets
   the run.
8. **Transparent conjunctions:** pairwise AND of threshold-stability with
   score-distribution stability, threshold-stability with hold-forward
   exceedance, or score-distribution stability with hold-forward exceedance.
   Each conjunct uses one parameter combination above. No OR or max rule is
   allowed.
9. **Never-ready negative stopping control:** never emit READY.

For stability rules, a consecutive transition/look sequence may begin only
after all windows and thresholds needed for that rule are supported. Every
candidate uses the threshold calculated at its first READY look, frozen for
its entire evaluator suffix. For an always-ready or fixed-N baseline, READY
is emitted at its specified supported look and uses that look's q99. A
never-ready task has zero eligible fault-report recall and zero alarm rate for candidate
tie-break metrics, but remains a joint-success failure and has acquisition
cost 1.

This enumerates 228 candidates: five fixed-N looks; always-ready;
maximum-horizon; never-ready; 8 threshold-stability settings; 8
score-distribution settings; 8 hold-forward settings; 4 plateau settings; and
64 settings for each of the three permitted pairwise conjunction families.
Consecutive stability settings use 2 or 3 transitions for threshold
stability, 1 or 2 looks for score-distribution and hold-forward rules, and
exactly 2 looks for the plateau rule. A skipped/unsupported scheduled look
breaks a consecutive sequence; no look is interpolated or skipped.

Each candidate ID is `family|<canonical-parameters-json>`. Family IDs are
`fixed_n`, `always_ready`, `maximum_horizon`, `threshold_stability`,
`score_distribution_stability`, `hold_forward_exceedance`,
`marginal_gain_plateau`, `and`, and `never_ready`. The JSON object uses
ASCII-sorted keys, compact separators, decimal values exactly as written in
the grid, and ASCII escaping. An `and` candidate stores its two component IDs
as `left` and `right` after sorting those IDs lexically. Equality tie breaks
therefore do not depend on source row order or runtime-generated labels.

No candidate is tuned or expanded after source outcomes are computed.
`no-alarm detector` is a separate evaluator negative control (no anomaly
alarms); it is not a readiness rule and cannot be selected as a detector.

## Source-only margin and parameter selection

Only source pseudo-target folds defined in `source_development_protocol.md`
may set numerical success margins and select a readiness candidate. Use the
OOF streams from the already-selected detector candidate only. For each
source pseudo-target, first score the fixed-N q99 baseline through the
suffix from raw row 2,305 to the entity's final raw row. Define
`FPR_q90_source_fixedN_diagnostic` as the type-7 empirical 90th percentile of
per-entity fixed-N future-normal pointwise FPR. It is diagnostic only and is
never a primary cap. Freeze `PRIMARY_ABSOLUTE_FPR_CAP = 0.03` and
`PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR = 0.50`. Define
`Recall_min_source_q10` as the predeclared type-7 empirical q10 of SOURCE
fixed-N eligible fault-report recall across evaluable SOURCE pseudo-target
tasks, giving each task equal weight. Then define
`Recall_min_effective = max(0.50, Recall_min_source_q10)`. The report unit is
each `faults.csv` row
with `efd_possible=true` whose existing parsed interval overlaps suffix
observations; duplicate rows remain separate reports, without semantic
deduplication. A report is hit if any suffix score strictly exceeds the
frozen threshold within its interval. This is report-level recall, not unique
physical-fault recall and not the paper's repeat-filtered event set. Use the
same unit for `Recall_min_source_q10`, `Recall_min_effective`, and TARGET
evaluation. If fewer than four evaluable pseudo-targets exist in a stratum,
that stratum is
`SOURCE_MODEL_NOT_EVALUABLE`.

Primary SOURCE pseudo-target joint success requires READY within budget, normal-side
future-normal pointwise FPR at most `PRIMARY_ABSOLUTE_FPR_CAP`, and
`eligible_fault_report_recall >= Recall_min_effective`. The q90 fixed-N FPR
statistic remains diagnostic only and cannot replace or relax the 0.03 cap;
the recall floor cannot be lowered by a source result. Never-ready is failure
and remains in the denominator. Choose a candidate lexicographically
by: (1) highest fraction of source pseudo-target tasks jointly successful;
(2) lowest mean acquisition cost among all tasks, where `raw_count` is the
scheduled raw-row count at READY and `elapsed_days` is the recorded timestamp
difference from the first raw row to the READY look; never-ready costs 1.
The fixed-N reference for primary comparison is specifically READY at raw
row 2,304 (when score-supported). Candidate-grid fixed-N baselines at earlier
looks remain calibration comparators only. Cost is
`0.5*(raw_count/2304 + elapsed_days/64)`;
(3) highest macro eligible fault-report recall; (4) lowest macro pointwise FPR; (5) fewer
conjuncts; (6) fixed candidate ID in ASCII lexical order. The candidate set
includes fixed-N baselines, so if no adaptive rule improves this objective,
the source seal records that fixed-N was selected and claims no adaptive
stopping benefit. All margins and the selected candidate are hashed before
TARGET prefix eligibility is run.

Before applying tie-breaks, count each candidate's tasks that satisfy all
three primary joint-success conditions. If every candidate has zero such
tasks within a stratum, do not seal the lexicographic winner as an operational
readiness rule: mark that stratum `SOURCE_MODEL_NOT_EVALUABLE` and take the
negative-result path. Apply this independently by exact stratum; any affected
stratum bars a five-stratum pooled success claim.

The 0.03 ceiling is our frozen operating ceiling. Paper §4.4 reports
normal-event pointwise accuracy >=0.97 as motivation, but its event-averaged
normal accuracy is not necessarily mathematically identical to our pooled
timestamp FPR; this protocol makes no guarantee from that correspondence.
The 0.50 floor is a predeclared protocol non-degeneracy rule. It is not
derived from or claimed equivalent to any paper-reported 60% result. Source
recall quantiles are empirical engineering rules, not population guarantees.

## Sealed output

For each evaluable stratum, seal the exact selected family, all numeric
parameters, the fixed 0.03 primary cap, fixed
`PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR = 0.50`, diagnostic
`FPR_q90_source_fixedN_diagnostic`, `Recall_min_source_q10`,
`Recall_min_effective`, source fold outcomes, score-support policy,
code/dependency hashes, and tie-break result. If source selection yields no
evaluable candidate or no candidate has any jointly
successful pseudo-target under the frozen primary rule, mark the stratum
`SOURCE_MODEL_NOT_EVALUABLE`. No target eligibility, target score, or target
trajectory can revise these values.
