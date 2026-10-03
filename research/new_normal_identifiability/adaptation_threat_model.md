# Adaptation threat model

## Threat model

The adaptation threat is that an online learner updates a detector or normal reference from observations that later prove faulty, attacked, or otherwise unacceptable. The relevant question is not only whether a stream is statistically novel. It is whether the system can establish, using the information it has, that an observation is eligible to influence the future reference.

Assume the algorithm observes \(X\), may have a historical model \(R\), and may receive context \(C\). An attacker or fault process may be persistent, predictable, gradual, or coordinated. If \(C\) is absent, we make no assumption that regularity means benignness.

## Threat cases and safeguards

| Threat | What X alone may reveal | Risk to adaptation | Safeguards possible without semantic context | What needs independent context or confirmation |
|---|---|---|---|---|
| Slowly developing failure | Trend, residual, parameter, or relationship changes if they exceed model/noise limits | A learner can track the degradation and absorb it into its baseline; small per-step changes can evade abrupt-shift thresholds | Freeze or cap update exposure; preserve immutable reference; monitor cumulative residual and derivative; compare to physical bounds; maintain an unresolved state | Whether the gradual operating change is planned, whether maintenance was authorized, and which operating envelope is acceptable |
| Stable sensor bias or gain fault | Offset/gain may be visible relative to other channels or a known reference; it may be invisible if only that channel is available | Persistent bias can become the new normal estimate; downstream residuals may normalize | Redundant-sensor consistency, range/rate checks, fixed reference, known excitation, calibration drift monitor | Calibration record, traceable standard, independent sensor, or hardware diagnostics; X alone cannot assign cause if it matches an allowed process change |
| Stuck-at sensor | Constant or repeated values, zero variance, frozen timestamps, or disagreement with related channels may be observable | A constant fault may be absorbed as a stable mode; a truly steady process can trigger the same rule | Check variance/heartbeat and cross-channel/process constraints; preserve raw data; do not update from degenerate channels without validation | Independent measurement, expected-excitation policy, device health signal, or operator inspection |
| Periodic attack or fault | Periodicity, phase, or correlation may be visible if unlike the reference | Recurrence-based memory can match and promote a repeated malicious pattern | Keep known-good reference; test predictable cycles against secure schedule; anomaly score conditional on operating phase | Authorized schedule, security telemetry, command provenance, and response by operations/security |
| Persistent predictable anomaly | Low residual or high predictability can occur after the learner sees repeated examples | The detector can learn the anomaly and reduce its future score | Separate training/monitoring/evaluation streams; limit adaptation from uncertain data; freeze updates on independent fault indicators | Semantic acceptability, fault labels, or a trusted policy defining allowed behavior |
| Coordinated multichannel fault / attack | Dependency residuals or violated physical constraints may reveal inconsistency | Jointly manipulated channels can preserve correlations and fool multivariate memory | Cross-channel invariants, actuator/sensor redundancy, causal process constraints, independent secure reference | Trusted controller commands, topology/configuration history, security logs, independent physical references, or human confirmation |

These are conditional safeguards. A residual test can flag a deviation from its model but cannot guarantee that a model captures every fault. If a malicious or faulty process can reproduce the full expected observation law and all untrusted context, X-only statistical protection has no remaining distinguishing evidence.

## What is fundamentally unavailable from X alone

Without additional assumptions or context, the system cannot guarantee:

- the intent behind a persistent pattern;
- whether a new regime was authorized;
- whether a change is due to maintenance or failure;
- whether a recurrence is safe rather than a repeated attack;
- semantic fault localization when two causes have the same observable law; or
- that an anomaly-free-looking stream is healthy when a fault can remain within the observed envelope.

This boundary is consistent with industrial control security work: stealthy attacks may follow expected system behavior closely while introducing enough manipulation to meet an attacker's objective. It is also consistent with fault-diagnosis notions of detectability and isolability, which depend on whether competing faults produce distinguishable outputs under the available model and excitation.

## Update policy implications

Risk controls can be useful even though they do not identify semantics:

- score before update and log the score/input/state used;
- keep confirmed reference state immutable during candidate evaluation;
- quarantine uncertain samples instead of allowing immediate writes;
- cap candidate age, size, and write rate;
- require independent promotion evidence where available;
- keep rollback/reversion possible and record every transition; and
- never interpret persistence, recurrence, or low prediction error as proof of benignness.

These are conceptual safeguards only. The revised M0 protocol does not authorize implementing rollback, stable/plastic memory, a learned gate, or delay-and-revalidation in the current milestone.
