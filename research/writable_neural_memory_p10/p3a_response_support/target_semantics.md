# Four distinct truth targets

User decision: 分開定義，避免把 fault label 等同 unsafe。

| Target | Source-backed truth available now | Runtime availability / limit | Claim permitted |
|---|---|---|---|
| Source disturbance occurred | Extended TEP idv_init/path/profile, verified event convention (author A.3.2/A.3.4/Table A.3) | Evaluator-only; fault ID/schedule is not input | Simulated disturbance onset/persistence can be evaluated under its source contract; compensation or observability are separate |
| Legitimate operating regime / adjustment | Author A.3.1 identifies nominal SP variation and mode-transition families | Current healthy cohort is only constant-setpoint Mode1; SP schedule is evaluator metadata, no verified timestamp-valid authorization stream | Source-legitimate adjustment is identifiable in eligible source families, not established runtime command causality or hazard freedom |
| Operationally unsafe | No independently validated physical hazard envelope/risk annotation in the accepted cohort | NOT_EVALUABLE | Do not turn FAULT into unsafe, non-FAULT into safe, low residual into safe, or a simulated completed run into safety certification |
| Safe normal-reference admissibility | No source field establishes reference-writing safety | NOT_ESTABLISHED; new-normal promotion truth NOT_EVALUABLE | Requires independent admissibility endpoint/verification and write-consequence evaluation; cannot be derived from disturbance absence or authorized adjustment |

Evidence: source_evidence.json thesis Appendix A.3.1–A.3.4; existing left_point_pilot/SEMANTIC_BOUNDARY.md and new_normal_identifiability/observable_vs_semantic.md. This audit creates no new labels and does not relabel previous cases.

A disturbance may be controller-compensated without unsafe operation, but compensation is a hypothesis unless observed/verified. A legitimate command and a fault can coexist; do not assume mutual exclusivity. Economic actual production/quality or successful simulation termination alone cannot define the unsafe or admissibility targets. Controller override/emergency shutdown conventions may supply additional source events if audited later, not a complete safety ground truth.

Any future P3-B must select its target explicitly. Closed-loop prediction of observed histories, source disturbance monitoring, command-aware causality and safe reference admission have different required evidence and cannot exchange success claims.
