# Shadow verification boundary — conceptual audit only

A candidate can be evaluated in isolation before committing an active reference/model. That can contain mutation harm; it does not decide whether the candidate regime is normatively legitimate.

| Layer / evidence | Can assess or contain | Cannot establish |
|---|---|---|
| Protected old-normal probes | Measured forgetting/regression on supported old anchors | New-regime legitimacy or global retention outside support |
| Independent candidate shadow | Candidate learning without active-state mutation, if isolation is complete | Fault-free candidate labels inferred only from its fit |
| Response consistency / reconstruction loss | Predictability and regression under declared checks | Safe operation or permission; stable fault can fit well |
| Read-only independent physics/support checks | Supported physical violations/contradictions | Universal safety where physics/context is missing or compromised |
| Complete snapshot and atomic restore | Computational state recovery and audit lineage | Undoing external plant actions, prior false alarms or already-used decisions |
| X-only verifier on semantic twins | Identical outputs; repeatable ambiguity | Opposite normative truths under identical observations |
| Verifier using X and ambiguous context | A scoped risk test with unresolved cases | Separation of identical-(X,C) alternatives |

## State required for a future exact-rollback claim

Snapshot and restore parameters, optimizer slots/counters, all adapters, normalization/scaler state, thresholds/calibration, memory and candidate/replay buffers, admission ledger, feature/embedding/schema versions, RNG, pending delayed writes, context ledger interpretation and correction version. Capture state hashes, parent lineage, effective point-ID exposures and decision clock. Restoring only model weights is not exact rollback. Protected probes must not be trained upon, selected after outcomes or polluted by candidate updates.

Shadow isolation means score/decision happens on the old active state, then candidate-only mutation. A rejected candidate must not alter active normalization, threshold, buffers or representation. Commit must be explicit and atomic across mutable state; partial failures/corrections remain auditable. These are design requirements, NOT verified implemented behavior in this task.

Post-write verification of ACTIVE mutation already incurs interim exposure. Measure harm until restore, stale pending actions, irreversible outputs and residual effect after restore. Pre-commit shadow evaluation may avoid active contamination but can still overfit the verification set. Finite probes offer empirical support, not an assurance beyond their domain.

If both twins produce the same X and same received context, any verifier using only those inputs and the same initial state must produce the same result. Independent authenticated intent may narrow possibilities, yet command failure/coincident fault remains. Report normative legitimacy as unresolved wherever the evidence overlaps.

[Validation-gated CL](https://github.com/DerKuhno/validation-gated-continual-learning/tree/636ac05995f52d3a12b6c7186646757a28c900eb) is a direct comparator for validation-selected updates/weight restoration. Its inspected label-filtered learning pool and restoration scope differ from this proposed full-state contract; this is a bounded code observation, not a proof that all versions lack rollback. Do not build a shadow model in P5-A.
