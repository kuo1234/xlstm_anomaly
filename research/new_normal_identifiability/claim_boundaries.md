# Claim boundaries and required answers

## Required final answers

### 1. Can time series alone distinguish benign new normal from persistent fault in general?

**No.** The task is not identifiable in general. If a benign new operating mode and a persistent fault induce the same law for the complete observed history, every X-only decision rule has the same output distribution in both worlds. With equal priors its error cannot be less than \(1/2\), regardless of model size or observation duration.

This does not say all cases are impossible. A shift may be detectable and some fault/benign classes may have distinct laws. The limitation is the unqualified general claim.

### 2. Under what additional assumptions can it?

It can be statistically distinguishable when the class-conditional laws are separated under a declared model and the sampling/dependence assumptions support enough evidence. Semantic classification can be made identifiable when there is trusted context, a process model, physical constraints, independent sensors, controlled excitation/intervention, prior labeled knowledge, or operator confirmation that differs between the hypotheses.

The source must be time-valid, relevant, and trustworthy. A command or log can itself be faulty or malicious; context is not an automatic oracle. State assumptions on minimum effect size, duration, noise, stationarity/mixing, fault modes, and context integrity.

### 3. What claims must a future paper avoid?

- “Time series alone knows whether a persistent shift is benign or faulty.”
- “Persistence, regularity, low prediction error, recurrence, or cluster coherence proves normality.”
- “Quarantine or promotion solves drift-versus-anomaly identification.”
- “A protected/multi-regime recurrent memory provides semantic safety.”
- “Hidden state contains information beyond the complete input history.”
- “xLSTM is necessary or uniquely suited to resolve this problem.”
- “No false promotion” or “safe adaptation” without a bounded, explicit threat model and evidence.

### 4. What context makes the task identifiable?

No universal context list guarantees identification. Potentially useful sources are recipe/product ID, authorized and executed setpoint/controller state, workload/throughput, production phase, environment, maintenance/calibration records, operator action, versioned device configuration/topology, machine identity, independent sensors, process constraints, and security telemetry. Context helps only when the combined law \(P(X,C\mid\text{benign})\) differs from \(P(X,C\mid\text{fault})\), with valid provenance. Human/operational confirmation may be the only source that establishes authorization.

### 5. Does quarantine/promotion solve identification, or only manage risk?

It manages risk. Quarantine can reduce exposure of a trusted memory to ambiguous samples. Promotion applies a policy after selected evidence. Neither policy supplies information that is absent from \(X\) and any valid \(C\). A persistent fault can satisfy dwell, recurrence, or coherence criteria.

## Safe, bounded paper wording

> “From an unlabelled time series alone, a persistent distributional change can sometimes be detected, but it cannot in general be identified as benign drift versus fault. Our method therefore separates statistical novelty from operational authorization and treats candidates as unresolved until stated assumptions or independent context support a disposition.”

If a future paper evaluates only anomaly labels or synthetic processes, qualify all claims to those labels and generators. A synthetic semantic label is identifiable to the evaluator because the generator knows it; that does not mean the label is inferable from the observations when the generator creates an observationally equivalent pair.

## Final status

**IDENTIFIABILITY_BOUNDARY_ESTABLISHED** — the X-only impossibility boundary is established by a direct proof and explicit counterexamples. Context-dependent identification remains conditional on source validity and separating assumptions. This status does not certify a particular application context or dataset.
