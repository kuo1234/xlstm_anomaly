# Threshold and calibration-state contract

## Fixed score, changing state

The source-sealed model, preprocessing, score formula, and ordered feature
schema never change during a target acquisition. Only the empirical target
threshold state and the readiness state may change, at scheduled looks and
under the rules below. This threshold is an operating point, not a statistical
certificate.

## Estimator

At each supported look, sort all finite scores observed from raw observation
1 through that look. Estimate the threshold as the empirical 99th percentile
using NumPy `quantile(method="linear")` (Hyndman-Fan type 7), with exact
float64 arithmetic and no smoothing or rounding. At least 200 finite scores
are required; otherwise the look is `NOT_READY` and the threshold is absent.
An undefined/non-finite quantile is invalid and cannot be repaired from later
values.

The threshold uses the cumulative eligible prefix, not only the most recent
block. Missing/invalid row scores are omitted from the quantile but their raw
observations remain in look counts. Scores are never imputed. The threshold
is computed before applying readiness at that look.

## State transition and post-READY behavior

At each look, recompute the cumulative q99 from all finite prefix scores and
evaluate the selected readiness rule. If not ready, retain that look's
threshold only as the preceding-look stability state; the next look recomputes
from the full cumulative prefix. The first supported look where the selected
rule says READY emits READY and seals that exact q99. After READY, both the
threshold and readiness decision are frozen. No later prefix scores may
update or revalidate them.

If the 64-day cap occurs before a scheduled look, take no unscheduled look.
If raw observation 2,304 is reached with insufficient finite support or no
selected rule passing, mark never-ready/commissioning failure. There is no
extension, reselection, or threshold fallback. A model/feature/schema failure
is not treated as evidence that more commissioning observations are needed.

## Interpretation

The q99 rule is empirical and chosen to align with a public PreDist threshold
direction, but the project implementation and source-only model are fixed
independently. It does not imply 1% future FPR: scores may be serially
dependent, the prefix is finite, and repeated looks are adaptive. No IID
binomial guarantee or unapproved conformal claim is made.
