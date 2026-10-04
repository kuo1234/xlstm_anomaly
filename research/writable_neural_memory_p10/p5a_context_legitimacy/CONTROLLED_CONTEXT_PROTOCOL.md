# Proposed non-oracle contextual twin protocol — NOT EXECUTED

Purpose: test incremental information from independently delivered intent, distinguish normative ambiguity from mutation harm, and expose failures when the context is unreliable. This is a design for review, not a policy, implementation or authorization to run. P4-A/P4-B generators, frozen Q family and outputs are unchanged.

## Structural design

Read-only reuse of the P4 controlled observation law is a future option under a separate GO. The physical A-to-B response and semantic fault twin retain bit-identical X/scaler/calibration. A separate operational-intent ledger defines issued commands BEFORE realized plant response; a transport/trust layer creates the RECEIVED context stream without access to evaluator labels. Evaluator truth is a third, inaccessible stream. Mock authority in a controlled environment must be declared simulation, not field provenance.

One contrast has legitimate intended change with a received scoped authorization versus the identical-X non-benign twin without authorization. That contrast alone is an oracle shortcut. It is NEVER the sole primary cohort or a success claim. Every physical group also contains all four overlap cells:

| Evaluator outcome | Valid available authorization | Missing/absent authorization |
|---|---|---|
| Legitimate settled B | Authorized intent with successful physical change | Legitimate intent but dropped/delayed evidence |
| Persistent fault / ineligible B-like response | Valid unrelated/failed command or authorized change with concurrent fault | Uncommanded fault with identical X |

Some benign/fault alternatives must have identical X AND identical full RECEIVED context, not merely the same event bit. Those cells are structurally unresolved and remain primary. An event-only classifier cannot perfectly predict truth; payload target, issuer, timing, identity or expiry cannot encode a hidden answer. A valid authorization can occur during fault; lack of evidence can occur during legitimate operation.

Balance each cell within each physical group for the identifiability stress test. In that balanced identical-(X,C) test no aggregate Bayes improvement is expected: it is a boundary control. Any claim of incremental operational information additionally needs a prospectively justified, non-deterministic joint intent/fault/transport model in which context distributions differ. That model and prevalence must be reviewed/frozen before generation; no favorable mixture is selected here. Report conditional cells and all declared prevalence sensitivities; do not let the easy commanded/uncalled pair dominate the safety conclusion. Plausibility of such a deployment prior is unverified.

## Mandatory context-error axes

| Axis | Predeclared mechanism to vary under a future freeze | Required failure readout |
|---|---|---|
| Delay/jitter | Issuance independent of settling; receipt jitter including receipt after response | Premature/late admission, censoring, decisions before receipt |
| Missing context | Drop valid event at transport; intent remains unchanged | Legitimate starvation versus abstention |
| Stale authorization | Correct asset but expired/revoked scope; receipt-aware corrections | False use of stale permission |
| Spurious authorization | Invalid issuer or mismatched scope; ALSO valid command with no causal relevance | Provenance rejection and fault admission despite valid but irrelevant evidence |
| Command fails | Valid command received, physical transition fails or response stays abnormal | Approval mistaken for completion |
| Authorized change + anomaly | Both before/after settling; contamination inside candidate payload | Fault exposure and reference eligibility error |
| Clock/order conflict | Jitter/reordering/duplicate/correction, uncertain clock | No backdated decisions; unresolved chronology |
| Unsupported target/mode | Legitimate request outside initial support | Explicit abstention, no inferred benign mapping |

Missing/erroneous evidence is not restricted to faults. Authorization need not always precede response by the same delay, and neither TTL nor receipt time is t_settled_B. Cross every feasible error axis with benign and fault outcomes; preserve opposite-semantic twins and failure cells. Numeric severities, counts, seeds, delivery bounds, TTL and trust model are NOT frozen in this audit. They must be chosen from an explicit engineering scenario before labels/results under a later task. No experiment can legitimately call this document a completed executable preregistration.

## Proposed future contrasts and units

L0 controls; L1 condition-aware residual/normality controls; L2 context-only eligibility/abstention diagnostic; L2 plus response evidence; and containment as a separate factor. No new learner is selected. A review must establish information parity with selective TTA and validation-gated CL; oracle-label-assisted baselines must be labelled as such, not a deployable competitor.

Physical observation groups are independent units. Context variants, twins, seeds reused on the same X, candidate snapshots and repeated checkpoints are paired robustness cases, not extra N. Initial train/calibration/protected anchors stay separate; no test normalization or outcome-based regime-support fitting.

Preserve explicit formal commit semantics: action WAIT/REJECT/PROMOTE, exact point-ID payload, context receipt IDs, state lineage and effective exposure. Native baselines without commit get N/A_NATIVE for TTAccept; report first actual B exposure and FPR recovery separately. This distinction follows the user's approved P4 metric contract.

Proposed evaluator readouts: valid settled-clean B acceptance coverage and delay; premature/contaminated commits; actual unique/weighted anomaly exposures; response false alarms/recall; old-normal retention; active-state mutation despite abstention; context error/availability stratification; rollback residual harm. Keep fault occurrence, reference admissibility and operational unsafety separate. Unsafety is NOT_EVALUABLE under the current synthetic truth. Report unresolved twins as unresolved, never discard them to improve accuracy.

## Falsification and next gate

Context does not universally break the boundary if opposite truths share available (X,C). Support for partial narrowing would require benefits in the declared informative subproblem, bounded contamination/retention harm under overlapping contexts, and honest abstention where evidence is ambiguous. Context cannot be called useful just because access to an authorization flag predicts a deliberately label-coded arm.

No success cutoff is invented. If context is truth-equivalent, use ORACLE_ONLY; if it adds no incremental evidence, report CONTEXT_DOES_NOT_BREAK_BOUNDARY for that tested construction. If a justified joint process or supported source cannot be specified, STOP rather than run a disguised oracle benchmark. Reviewer must choose/approve that evidence model before any implementation or model execution.
