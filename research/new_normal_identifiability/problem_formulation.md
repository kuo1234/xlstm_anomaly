# Problem formulation

## 1. Observations, context, and hidden meaning

Let the detector receive a multivariate time series \(X_{1:t}=(X_1,\ldots,X_t)\), where each \(X_i\in\mathbb{R}^d\). It may also receive an optional context stream \(C_{1:t}\), such as recipe, setpoint, workload, operating phase, environment, maintenance event, operator action, device configuration, or machine identity.

Let \(Y\) describe the operational meaning of the process, which is not directly observed. The detector may also have a fixed learned parameter set \(\Theta\), reference history \(R\), and a decision policy \(\delta\). An X-only decision has the form \(\delta_t(X_{1:t};\Theta,R)\); a context-aware decision has the form \(\delta_t(X_{1:t},C_{1:t};\Theta,R)\). Training information in \(\Theta\) and reference information in \(R\) are additional information sources. They must not be described as evidence supplied by the current observation stream alone.

The central distinction is between:

- **statistical behavior:** the probability law of the observed sequence, including temporal and cross-channel structure; and
- **semantic status:** whether that behavior is authorized, acceptable, faulty, malicious, or expected in the current operation.

The same statistical behavior can have different semantic status under different commands, recipes, machine conditions, or causes.

## 2. Issue labels are separate axes

The issue lists normal, benign new normal, transient anomaly, persistent fault, recurrent known regime, and previously unseen regime. These should not be forced into one mutually exclusive flat classifier. They describe at least three dimensions:

| Dimension | Example values | Meaning |
|---|---|---|
| Operational semantics | authorized/benign; fault; attack; unknown | Whether the behavior is acceptable or indicates a problem |
| Temporal behavior | transient; persistent; gradual; recurring | How long or how often the behavior occurs |
| Relation to reference memory | known/recurrent; unseen; uncertain match | Whether a statistical pattern matches stored history |

A persistent fault may also be a previously unseen regime. A benign mode may be recurrent or novel. “Anomaly” may mean deviation from a statistical baseline, while “fault” is a claim about cause or acceptability. A transient event can be either a benign operation or a fault. Reporting these axes separately avoids encoding semantics in persistence or novelty.

| Issue term | Operational/temporal/reference interpretation |
|---|---|
| Normal | Accepted behavior under the current validated reference and applicable operating context |
| Benign new normal | Statistically changed or previously unseen behavior that is authorized/acceptable under context or policy |
| Transient anomaly | Short-lived statistical deviation from a declared reference; its cause can still be benign, faulty, or unknown |
| Persistent fault | Fault semantics plus persistence; it may form a stable and predictable statistical regime |
| Recurrent known regime | Statistical match to a prior regime; this does not inherit semantic approval unless its authorization is still valid |
| Previously unseen regime | No validated statistical match; “unseen” is epistemic and does not imply either benign or faulty |

These labels overlap rather than partition all streams. For example, a benign new normal can later become a recurrent known regime, and a persistent fault can recur. A future annotation schema should store semantic status, temporal behavior, and reference match in separate fields.

## 3. Statistical hypotheses

For an operational label \(y\), denote by \(P_y^{(t)}\) the probability law of the **entire observed path** \(X_{1:t}\) under that label. If context is observed, denote the joint path law by \(P_y^{(t)}(X,C)\). Considering the full path matters: equality of one-time marginals alone does not imply equality of temporal processes.

The semantic label is identifiable from \(X\) over a specified model class only if distinct labels imply distinguishable laws for the complete observations available to the decision rule. In particular, if a benign world and a fault world can both produce the same law,

\[
P_{\mathrm{benign}}^{(t)}(X_{1:t}) =
P_{\mathrm{fault}}^{(t)}(X_{1:t}) \quad \text{for every }t,
\]

then semantic classification from \(X\) alone is not identifiable over that model class. A prior may select one label as more likely, but that is a prior-driven decision, not information inferred from the sequence.

With context, the corresponding condition is whether \(P_{\mathrm{benign}}^{(t)}(X,C)\) and \(P_{\mathrm{fault}}^{(t)}(X,C)\) are distinguishable and whether the context is valid for the intended semantic rule. If these joint laws also coincide, adding that context has not resolved the ambiguity.

## 4. Four different tasks

1. **Shift detection:** test whether the current sequence differs from a declared historical or conditional reference.
2. **Anomaly detection:** score observations against a specified normal model, operating envelope, or physical constraint. The result depends on that reference.
3. **Regime clustering:** group statistically similar time segments. Cluster IDs have no inherent benign/fault meaning and are permutation-invariant.
4. **Semantic regime classification:** assign an operational meaning such as authorized mode, maintenance effect, sensor failure, or attack. This requires label-bearing assumptions, context, physical constraints, interventions, or human knowledge that separate those meanings.

Success at tasks 1–3 does not entail success at task 4.

## 5. Assumptions required for an identifiable semantic task

A future study must state:

- which channels and time history are observable;
- which context fields are available, time-aligned, and trusted;
- the candidate semantic classes and whether they may share an observation law;
- the reference model and the conditions under which it is valid;
- stationarity, ergodicity, mixing, excitation, or minimum-separation assumptions used by any statistical test;
- which labels or process knowledge were used to define acceptable behavior; and
- what output is produced when evidence is ambiguous or context is absent.

Without these restrictions, the class “benign new normal” is partly a policy judgment, and no distribution-free X-only classifier can determine it for every possible process.
