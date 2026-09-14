# Phase G1 pre-label adversarial self-review

Reviewed worktree base commit: `5c707618e78749f119bbdc722fc6c163e73f5a83`

Verdict: **STOP_PROTOCOL_AMBIGUITY**

No real Phase-G labels were read. No probe classifier, StandardScaler, AP,
AUROC, bootstrap, sign-flip statistic, or scientific checkpoint execution was
run.

## Review method

I inspected the frozen M0/G0/G0.1/F-v4 manifests, the complete G1 source and
dependency closure, and the executable Stage-A/adversarial reports. I traced
the protocol requirements to actual code paths rather than relying on design
intent. Stage-A preflight passed and the bounded adversarial suite passed 18/18
fixtures, including row-order/cohort, fold/scaler, CANDI alignment/shared
control, label-argument, subtraction-direction, Holm-family, and unresolved
duration-protocol rejection tests.

## Protocol-to-code result

The implementation positively verifies source-disjoint folds; pooled four-
scenario fitting and validation-only C selection; observation-only feature
extraction; evaluator-only label joining; common row-key intersection; sealed
feature dimensions and causal rolling summaries; the four eligible xLSTM
sLSTM cells and all six LSTM layers from the sealed observers; native W10
CANDI alignment at common right-edge `t >= 63`; train-only scaling; source-
pooled primary AP effects; fixed bootstrap/sign-flip/Holm settings; frozen
decision directions; secondary strata/specificity/natural-prevalence reports;
dependency/hash seals; and independent post-run recomputation/forensics.

One requirement is not executable yet: M0/G1 requires a duration/severity-
matched analysis to support H2/H3a, but does not define its legitimate
comparison cohort, matching algorithm, source/event weighting, or AP estimand.
The sealed generator's `semantic="legitimate"` path is explicitly an
observation-identical, opposite-semantic pair. That is the separately
specified non-identifiability control; duplicating those features with the
opposite label would force AP/incremental ties and cannot be used as the
supportive matched analysis.

To prevent accidental conversion of this unresolved definition into a
scientific negative result, `configs/phase_g1.json` records
`UNRESOLVED_PROTOCOL`, `require_duration_matching_resolution()` fails before
checkpoint loading or stream generation, and the post-run auditor rejects any
run made without a resolved estimand. The control remains available only as a
separately labelled diagnostic after a future amendment.

## Required resolution

Before any label access, an external prospective amendment must define the
legitimate-excursion duration/severity cohort, fixed matching variables and
algorithm, source/event weighting, AP estimand, support criteria for H2 and
each H3a comparison, and its artifact/audit contract. The existing
identical-observation/opposite-semantic control must remain separate. After
that amendment, all Stage-A tests and this adversarial review must be rerun
from the beginning; no pre-label seal is created by this review.

The complete machine-readable mapping, hashes, fixture list, and exact
unresolved issue are in
[`g1_self_review_prelabel.json`](g1_self_review_prelabel.json).
