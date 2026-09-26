# Identifiability theorem and counterexamples

## 1. Exact observational-equivalence result

Consider two semantic hypotheses: \(H_B\), benign new normal, and \(H_F\), persistent fault. Let \(P_B^{(t)}\) and \(P_F^{(t)}\) be the laws of the full observed path \(X_{1:t}\). A possibly randomized classifier \(\delta_t\) sees only that path and outputs \(B\) or \(F\).

**Proposition.** If \(P_B^{(t)}=P_F^{(t)}\) for every \(t\), no X-only classifier can have different decision behavior in the two worlds. If class priors are equal, its error probability is at least \(1/2\) for every history length, including an unlimited history.

**Proof.** For any decision event \(A=\{\delta_t(X_{1:t})=B\}\), equality of the observation laws gives \(P_B(A)=P_F(A)=q\). Under equal priors, the error is \(\tfrac12(1-q)+\tfrac12q=\tfrac12\). Randomization is already included in the event probability. Since this holds for every \(t\), adding more samples cannot help. With unequal priors \(\pi_B,\pi_F\), the best possible rule under exact equality is to always choose the more probable class, with error \(\min(\pi_B,\pi_F)\). The output does not update the prior odds because the likelihood ratio is one. \(\square\)

For a finite observation horizon and equal priors, the optimal binary classification error is

\[
R_t^* = \frac{1-\operatorname{TV}(P_B^{(t)},P_F^{(t)})}{2},
\quad
\operatorname{TV}(P,Q)=\sup_A |P(A)-Q(A)|.
\]

This states the softer boundary too: overlap leaves irreducible error at that horizon. If the full path laws are equal, total variation is zero for every horizon. If they differ and become increasingly separable with time, consistent classification may be possible under additional sampling and process assumptions. A distinct law can support statistical discrimination; it still does not name its cause without a semantic model.

This is a non-identifiability result, not a statement that no anomaly detector can ever help. A detector can find deviations from a fixed reference, identify a change point, or distinguish hypotheses that have been restricted to different observable laws.

## 2. Constructive worlds with the same observations

In each row below, the two worlds have the same law for all channels available to the X-only detector. They differ in a hidden command, cause, or acceptability label. The examples are symbolic and do not use project data.

| Hidden explanation A | Hidden explanation B | Identical observed stream construction | Information that could separate them |
|---|---|---|---|
| Authorized production-mode change | Controller or actuator fault that moves the plant to that same operating point | Let \(X_t=\mu_1+\epsilon_t\) with the same noise and joint temporal law in both worlds. In A an authorized recipe/setpoint changes from mode 0 to mode 1; in B the faulty controller produces mode-1 output without authorization. | Time-valid recipe, authorized command, controller state, actuator feedback, and a validated model linking commands to response |
| Planned maintenance or intended recalibration | Sensor bias/gain fault | Let the recorded channel be \(X_t=aZ_t+b+\eta_t\) after the event in both worlds. In A maintenance deliberately changes \(a,b\); in B the sensor electronics drift to the same \(a,b\). | Calibration certificate, maintenance record plus post-maintenance check, reference instrument, or redundant sensor |
| Genuinely stable process | Stuck-at sensor | The observed channel is \(X_t=c\) for the full interval. In A the true process is stable at \(c\); in B the sensor is frozen at \(c\) while its unobserved input varies. | Independent sensor, known excitation, actuator-to-sensor response, heartbeat/diagnostic, or process constraint |
| Expected workload increase | Fault-induced overload or loss of efficiency | Choose a common output law \(Q\) for throughput, current, temperature, and vibration. A workload increase under a healthy machine and a fault under a different hidden load both generate the same \(Q\). | Orders, throughput counter, resource allocation, environment, and workload-conditioned physical limits |
| Scheduled periodic operation | Periodic attack or repeating fault | Both produce the same phase-aligned waveform \(X_t=s(t\bmod p)+\epsilon_t\), including the same cross-channel phase relations. | Authorized schedule, command provenance, security telemetry, or known operational phase |
| Valid configuration/topology change | Coordinated multichannel fault that imitates the new configuration | The complete observed vector has the same path law \(Q\) after the event in both worlds; channel relations are chosen to match. | Signed asset/configuration history, independent topology check, actuator/control logs, conservation or physics constraints not controlled by the fault |

These are not merely finite-sample failures. They are pairs of possible worlds that are observationally equivalent by construction. A more expressive network cannot distinguish two inputs that have the same distribution unless it also uses different external information, learned prior assumptions, or labels.

## 3. Why “persistent” and “predictable” do not break the proof

Persistence is a property of the sequence law, not an authorization record. Both an approved new operating mode and a stable fault can persist indefinitely. Likewise, recurrence can indicate a familiar production cycle or a repeated attack. A candidate can be statistically coherent under either label. A dwell-time threshold may reduce promotion of short transients, but a long-lived fault can pass it.

Suppose a recurrence matcher stores regime \(Q\) and a future stream again follows \(Q\). It can identify a statistical match to the stored regime. It cannot infer whether the original occurrence of \(Q\) was authorized if that semantic label was never supplied or encoded in a valid context source.

## 4. Finite samples and near-equivalence

Exact equality is the sharp impossibility case. In practical systems, benign and faulty laws may be close rather than equal. Then finite data may have small total variation and large optimal error. This means the distinction may be formally possible with an ideal infinite-data experiment yet operationally unreliable at the available duration, noise level, sampling rate, or false-alarm budget.

If one assumes conditionally independent samples and distinct class-conditional distributions, repeated evidence may drive error down. Time series usually require assumptions about dependence, regime duration, stationarity within segments, excitation, and change timing. Those assumptions should be stated and tested; a long stream alone does not validate them.

## 5. Context changes the observable experiment

For equal priors and observations \(O=(X,C)\), the posterior odds are

\[
\frac{P(H_B\mid X,C)}{P(H_F\mid X,C)}
=
\frac{P(H_B)}{P(H_F)}
\frac{p(X,C\mid H_B)}{p(X,C\mid H_F)}.
\]

Context makes the decision data-identifiable only if it changes the likelihood ratio in a way that separates the hypotheses. A new context field that is equally distributed in benign and fault worlds adds no information. A timestamped recipe command may help distinguish authorized and unauthorized transitions; a command log that can itself be faulted, forged, or issued by an attacker may not.

If \(P_B(X,C)=P_F(X,C)\), the same impossibility result applies to the combined input. The input contract must therefore include provenance and a policy for missing, stale, contradictory, or untrusted context.
