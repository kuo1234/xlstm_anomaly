# Architecture implications

## 1. What an architecture can add

A model can improve how efficiently it represents history, how well it detects a departure from a reference, or how well it predicts under a stated process family. Learned parameters can also encode assumptions or information learned from prior data. These can be valuable engineering advantages.

They do not let the model distinguish two semantic worlds that supply the same current input and the same model state/reference. If both worlds induce the same observable path law and use the same \(\Theta\), \(R\), and policy, the model has no evidence with which to give different answers.

For a deterministic recurrent update

\[
h_t=f_\Theta(h_{t-1},X_t),\qquad h_0 \text{ fixed},
\]

there is a function \(F_\Theta\) such that

\[
h_t=F_\Theta(X_{1:t},h_0).
\]

Conditioned on fixed \(\Theta\) and \(h_0\), the state is a summary of the observed history, not information beyond that history. In information-theoretic form, for a semantic label \(Y\), \(I(Y;h_t\mid\Theta,h_0)\le I(Y;X_{1:t}\mid\Theta,h_0)\), because \(h_t\) is a deterministic function of \(X_{1:t}\). A recurrent representation can still compress long history better than a fixed window or residual. It cannot resolve exact observational equivalence. If \(\Theta\) carries supervised or external process knowledge, state that information source separately.

## 2. Component-by-component boundary

| Component | What it can do | What it cannot identify by itself |
|---|---|---|
| Persistent recurrent memory | Retain a compact history summary and support stateful forecasting/scoring | Whether a learned pattern is operationally authorized or faulty |
| Quarantine | Delay writes and limit how much ambiguous data reaches a reference | The semantic label of quarantined data |
| Candidate-regime formation | Collect samples with similar statistical behavior | Whether the candidate is benign, attack, or fault |
| Promotion | Apply a policy to commit a candidate after evidence/approval | Derive a correct semantic rule from identical observations |
| Rollback | Restore earlier state after a detected regression or policy trigger | Determine the original intent/cause absent a distinguishing signal |
| Multi-regime memory | Retain statistical alternatives and retrieve a matching old pattern | Declare a retrieved regime safe merely because it has been seen before |
| Persistence/dwell threshold | Reduce acceptance of short transients under an assumed duration model | Reject a long-lived or recurring fault that satisfies the same threshold |
| xLSTM or another sequence model | Learn a useful sequence representation under its training/data assumptions | Break an information-theoretic equivalence shared by all X-only decision rules |

Thus, quarantine, candidate memory, promotion, rollback, and multi-regime retention are best framed as **risk management and state control**, not as semantic identification. Their value may be to bound exposure, preserve options, or make decisions reversible.

## 3. xLSTM is not necessary for the identifiability result

The impossibility proposition is independent of model architecture. A decision tree, LSTM, GRU, SSM, xLSTM, transformer, Bayesian filter, or human who sees only the same X and assumptions faces the same observational equivalence.

xLSTM may be an implementation candidate for long-history compression. Any empirical claim about that benefit requires matched comparisons to LSTM/GRU, a relevant state-space model, and simple observable controls. Hold constant:

- input history and context access;
- training data and labels;
- parameter and optimizer budget;
- score head and update policy;
- quarantine/promotion rules;
- update frequency and inference latency; and
- data splits and evaluation labels.

Include fixed-window, explicit lag/seasonal, and cross-channel residual controls. A gain over a short window demonstrates a useful summary relative to that window, not additional information beyond the complete observed history.

## 4. Keep three outputs separate

A future system should expose separate fields for:

1. **Statistical shift:** evidence that the observed law changed.
2. **Fault/anomaly risk:** evidence relative to a fixed, conditional, or physics-based reference.
3. **Operational disposition:** authorized benign, suspected fault, or unresolved, based on trusted context/policy/human review.

Conflating these fields makes a low anomaly score look like semantic confirmation. The output “unknown” is a valid and necessary result when context does not distinguish the candidate interpretations.

## 5. Current M0 boundary

reports/m0_protocol.md states that no rollback, stable/plastic dual memory, new xLSTM cell, learned adaptation gate, or delay-plus-revalidation mechanism is authorized in the revised M0. The theoretical analysis here neither implements nor recommends bypassing that gate. Any future M6 implementation needs its own versioned protocol and explicit authorization.
