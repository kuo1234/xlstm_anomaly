# Context requirements

## 1. When context can make the problem identifiable

Let \(B\) denote benign new normal and \(F\) persistent fault. With class priors \(\pi_B,\pi_F\),

\[
\frac{P(B\mid X,C)}{P(F\mid X,C)}
=
\frac{\pi_B}{\pi_F}
\frac{p(X,C\mid B)}{p(X,C\mid F)}.
\]

Context \(C\) helps only when it is available and its conditional relationship to the two semantic hypotheses differs. If the pair \((X,C)\) is still observationally equivalent under \(B\) and \(F\), context has not resolved the issue. If context is missing, stale, unauthenticated, or caused by the fault itself, a system must preserve an unknown/ambiguous result rather than silently treat it as ground truth.

The marginal probability \(P(B\mid X)\) averages across contexts. It can be ambiguous because the same signal is benign under one recipe and faulty under another. A conditional \(P(B\mid X,C)\) can be more informative, but only if \(C\) is time-aligned, relevant, and trustworthy.

## 2. Context-source audit

| Context field | What it can explain or constrain | Requirements for trustworthy use | Residual ambiguity |
|---|---|---|---|
| Recipe / product ID | Expected operating envelope, channel correlations, and recipe-specific trajectories | Time-valid recipe identity, verified changeover, mapping from recipe to accepted behavior | A recipe can be wrong, unauthorized, or paired with a fault |
| Commanded setpoint | Distinguishes intended target changes from uncommanded output shifts | Signed/audited command, timestamps, confirmation of command execution and controller state | A faulty or malicious controller can issue the command; the command alone does not prove healthy response |
| Workload / throughput | Explains load-dependent level, variance, temperature, current, and response time | Independent counters/orders with synchronized timestamps and defined units | Workload can be misreported, and overload/fault can coincide with higher work |
| Production phase / operating mode | Selects phase-specific limits and expected transients | Explicit state machine or trusted cycle markers; well-defined transitions | A fault can occur during the same phase or mimic its transient |
| Environmental variables | Conditions expected behavior on ambient temperature, humidity, pressure, or other external drivers | Independent sensors, calibration, alignment, and coverage | Environment can co-occur with fault; unmeasured variables remain confounders |
| Maintenance record | Indicates when an intervention was intended and which component was serviced | Authenticated work order, asset/time identity, completion status | A record does not prove repair success or correct calibration |
| Calibration record / reference | Separates changes in process value from changes in sensor response | Traceable reference standard/check standard and calibration validity interval | Reference instrument can fail; calibration can be incorrectly applied |
| Operator action | Provides authorization and operational intent | Identity, timestamp, audit integrity, and authority scope | Logged intent can differ from executed action; account compromise or incomplete logging |
| Device configuration / topology | Defines channel meaning, wiring, firmware, graph relations, and controller dynamics | Versioned and time-valid asset/configuration history, signed changes | Configuration drift or a faulty update may itself be causal |
| Machine identity | Selects machine-specific baseline and known capability envelope | Stable identity, provenance, and time-valid asset record | Identity alone does not declare a new machine healthy; machine-specific fault can be confounded with baseline |

The [NIST digital-twin framework](https://www.nist.gov/publications/digital-twin-based-cyber-attack-detection-framework-cyber-physical-manufacturing) is a concrete example of using runtime measurements together with physics-based models and subject-matter expertise to distinguish expected anomalies from attacks across controller setpoints. NIST's explanation of that system places a human expert at the final interpretation/decision step. This is evidence for the practical value of context and expert rules, not a universal proof that those fields resolve every case.

## 3. Minimum context contract for a future system

For every context item, record:

1. source system and owner;
2. asset, channel, and event identity;
3. event time, ingestion time, and clock uncertainty;
4. whether the field is commanded, executed, measured, inferred, or manually entered;
5. authorization/provenance mechanism and tamper assumptions;
6. missing, stale, contradictory, and out-of-vocabulary behavior; and
7. which semantic decision the field is permitted to support.

Do not treat an inferred context value as an independently observed label. For example, inferring “production phase” from the same \(X\) used by the detector does not add independent information to an exact observational-equivalence pair. It may still be a useful deterministic feature under a restricted model, but its provenance should be explicit.

## 4. Without context

An X-only system can still:

- flag distributional change;
- detect out-of-envelope values under a valid reference;
- detect inconsistency with known physical relationships;
- cluster recurring sequences; and
- quarantine uncertain samples to reduce their effect on adaptation.

It should report “unknown,” “unresolved,” or “statistical shift” when semantic evidence is absent. Rebranding one of those outputs as “benign normal” is unsupported.

## 5. Context still does not guarantee identification

The extra information must separate the hypotheses. If a fault and an authorized mode change produce the same \((X,C)\), a classifier cannot tell them apart. This can happen when a command is itself corrupted, when an attacker controls telemetry and command logs, when maintenance records are incomplete, or when the distinguishing physical state is unmeasured. Independent references, causal constraints, secure provenance, active excitation, or human/operational adjudication may then be required.
