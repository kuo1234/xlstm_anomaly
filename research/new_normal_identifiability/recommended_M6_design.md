# Recommended M6 design: separate detection from authorization

This is a conceptual research design requested by issue #3. It is not an implementation plan, M0 amendment, or authorization to run an experiment.

## 1. Objective

Design a system that detects statistical change, evaluates fault risk against a declared reference, and exposes semantic uncertainty when the available evidence does not establish whether a change is benign. Do not make “learn a new normal from X” the hidden objective.

## 2. Input contract

Define:

- \(X_{1:t}\): sensor and process observations, with channel units and sampling semantics;
- \(C_{1:t}\): optional context with source, event time, ingestion time, trust/provenance, and missing/stale flags;
- \(R\): immutable reference model/version and its validated operating envelope; and
- \(\Pi\): approved operating policy, including which context fields can authorize a mode.

The method must distinguish measured signals from commanded values and inferred context. It must not silently use evaluator-only labels, future data, or post-event outcomes.

## 3. Separate outputs

At each decision time, emit a structured result with independent fields:

| Field | Example values | Meaning |
|---|---|---|
| Statistical status | baseline-like, shifted, unknown | Relationship of X to a declared statistical reference |
| Fault/anomaly evidence | low, elevated, high, unavailable | Evidence relative to a fixed conditional/physical model |
| Regime match | known regime ID, novel candidate, ambiguous | Statistical similarity, not a semantic label |
| Context status | valid, missing, stale, contradictory, untrusted | Whether context can support a semantic decision |
| Operational disposition | authorized, suspected fault, unresolved | Policy/confirmation outcome |
| Update permission | frozen, candidate-only, approved update | State mutation policy, logged separately from detection |

“Novel candidate” must never be automatically rewritten as “normal.”

## 4. Decision flow

1. Score \(X_t\) against the frozen/reference model and any context-conditioned expected model before mutating state.
2. Emit an immutable score and record which model/context version produced it.
3. If observations are shifted, start or extend a candidate record. Candidate formation groups statistical behavior; it does not assign benign semantics.
4. If fault evidence is high, context is contradictory, or a threat indicator fires, freeze adaptation and return suspected fault or unresolved.
5. If trusted policy context confirms an authorized mode, evaluate the stream against that mode's declared envelope. Keep its semantic authorization evidence separate from data-derived similarity.
6. If context is absent or does not distinguish explanations, preserve the unresolved result. Use operator/security/maintenance workflow if a semantic decision is required.
7. Permit future promotion only under a separately specified policy that identifies independent evidence, authority, reversion, and audit requirements. Persistence alone is insufficient.
8. If an old statistical regime returns, report a statistical match. Reuse is permitted only if the associated semantic authorization remains valid for the current context.

## 5. Required cases and evaluation controls

Any future evaluation should report four tasks separately: change detection, anomaly scoring against a reference, statistical regime clustering, and semantic classification. Include:

- paired cases with identical \(X_{1:t}\) and opposite benign/fault semantic labels; an X-only model should not be rewarded for separating them;
- distinct full-history distributions that are statistically separable;
- missing, stale, and contradictory context;
- mode changes with a valid command versus identical measured response without authorization;
- sensor bias/gain and stuck-at examples with and without independent references;
- predictable recurring attacks and repeated benign cycles;
- gradual and coordinated multichannel faults;
- context provenance corruption, including a faulty or malicious command log; and
- adaptation ablations showing state exposure, freeze behavior, and rollback cost.

Report statistical detection delay/false alarms separately from semantic classification accuracy and operator escalation rate. On paired identical-X cases, report the irreducible uncertainty and prior-driven baseline explicitly.

## 6. Architecture comparison

Start architecture-agnostically. Compare matched-history LSTM/GRU, SSM, xLSTM, and simple observable-history controls only if a later approved empirical phase asks which representation helps with detection or compression. Keep parameters, history, context, updates, and policies matched. Architecture cannot be credited with solving the semantic ambiguity.

## 7. Gate and M0 compliance

Before any experiment, create a separate versioned protocol and data manifest, obtain the gates required by reports/m0_protocol.md, and state the allowed compute/data/label scope. M0 currently restricts adaptation mechanisms; this M6 note does not authorize rollback, dual memory, a learned gate, training, GPU work, or access to protected labels.
