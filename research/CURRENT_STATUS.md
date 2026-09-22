# Current research status (2026-09)

This document is a compact status snapshot for the consolidated repository.
It does not replace the pre-G1 framing or the frozen protocol.

## Authoritative G1 result

- H2: **GO**, mean ΔAP = `+0.14251889179304736`.
- H3a: **STOP** under the frozen common-capacity comparison.
- H3b: **LOCKED** under the frozen protocol.

The original G1 artifacts and decision rules are unchanged.

## Post-G1 engineering evidence

- The DGX Spark/GB10 CUDA path is usable with the validated SM121/CUDA 13
  compatibility overlay. The CUDA investigation documents the
  `static-global-template-stub` linkage issue and its scoped workaround.
- FastObserver captures native sLSTM states instead of replaying a duplicate
  scalar recurrence. Trained-checkpoint parity passed, with roughly 4.7x
  bounded extraction speedup.
- CUDA training was substantially faster in the bounded canary (about 5.3x),
  but vanilla and CUDA training trajectories are not interchangeable. This is
  an engineering result, not a new scientific checkpoint or G1 result.

## Exploratory mLSTM evidence

The frozen seed-11 dense W64 audit found an exploratory mLSTM-layer signal:

- `M_full | H ≈ +0.145661 AP`
- `M_full | H+S ≈ +0.016657 AP`
- `ΔC_history ≈ -0.000592`
- `ΔC_given_sLSTM ≈ +0.006610`

The current classification is **DENSE_MLSTM_SIGNAL_NOT_MATRIX_SPECIFIC**:
the mLSTM state summary carries information in this exploratory screen, but the
evidence does not isolate matrix-memory `C` as its main source.

## Post-hoc matched-LSTM diagnostic

`Delta_L_own ≈ +0.142966` (50/50 source×seed units positive), reconstructed
algebraically from the committed G1 audit. The common recurrent-state effect is
therefore **not xLSTM-specific within the two tested recurrent backbones**.
Scenario and shared-CANDI components are not recoverable from the compact
artifacts. Post-hoc and exploratory; not a member of the Holm family.

## Strong observable residual control (exploratory, seeds 11/22/33)

Rich **within-window** residual controls under the frozen L2 probe. Both arms
retain a positive internal increment; neither control is temporally matched to
the internal arm (see the next section).

| increment | xLSTM | matched LSTM |
|---|---:|---:|
| `I \| H` | +0.14227 | +0.14163 |
| `I \| H+O1` | +0.03958 | +0.01527 |
| `I \| H+O2` (predeclared primary) | +0.07122 | +0.05303 |

**O1 versus O2.** `O2` is the high-dimensional (1,024-column) raw
residual-trajectory control and was predeclared as primary. `O1` is the
128-column engineered residual summary and is, empirically, the **stronger
observable-only control under the current linear probe**
(`O1|H` `+0.11006` / `+0.13484` versus `O2|H` `+0.07603` / `+0.09694`).
Dimension is not strength here. The defensible summary is the minimum over
available controls — `+0.03958` (xLSTM) and `+0.01527` (matched LSTM, below the
`0.02` practical reference in 0/3 seeds). See
`strong_observable_control/post_review_addendum.md`. The historical protocol and
result files are unchanged.

## Open confound: temporal-span mismatch (most important unresolved issue)

Verified in `scripts/strong_observable_control.py`:

- `history14` — current/delta plus causal rolling statistics at widths 4/8/16/32.
- `internal234` — each of the 18 internal base features receives causal rolling
  mean/std/slope at widths 4/8/16/32 (`18 x 13 = 234`).
- `O1` — current W64 residual summary only, inserted raw.
- `O2` — current W64 residual trajectory only, inserted raw.

The internal and observable arms are therefore **not temporally matched**. The
observed internal increment may partly or largely measure **cross-window
temporal context** rather than an internal-state-specific representation. The
scenario strata are consistent with this: the residual-controlled increment is
small in abrupt and correlation (where one window suffices) and largest in
gradual and recurring (where it does not).

## A+ temporally matched observable control (exploratory)

The fixed W64/stride-1 A+ analysis applies the same causal `[t-94,t]`
decision-span expansion to all 128 O1 residual columns. The primary
`H+O1r+internal234 − H+O1r` increment is `+0.026710` for xLSTM (exploratory
95% bootstrap interval `[+0.022959,+0.030312]`, 2/3 seed means at the old
`+0.02` reference) and `+0.010220` for the matched LSTM (interval
`[+0.007861,+0.012566]`, 0/3 seed means at the reference). All source-seed
directions are positive, but the backbones are heterogeneous. This provides
exploratory support that the xLSTM increment is not fully explained by this
temporally matched residual control; it is not a causal or information-
theoretic result and does not alter G1/H3a/H3b.

The historical O1/O2 results remain a **rich within-window residual control**
or a **residual-controlled linear-probe result**, not a matched control. A+
tests the narrower temporally matched O1r question; neither result licenses the
claim that *observable residuals are insufficient*.

### A+S solver/convergence audit

The post-hoc A+S audit found no unresolved `lbfgs` convergence failure at
`max_iter=10000`. The fixed expanded C grid changes some selected C values but
preserves the qualitative result: pooled xLSTM ΔAP remains positive and above
the historical +0.02 descriptive reference, while matched-LSTM ΔAP remains
positive but below it. The corrected crossed source×seed uncertainty is
reported separately from the historical nested bootstrap. The xLSTM
nested-superset regression persists after converged refitting. A+S is
exploratory and does not alter G1/H2/H3a/H3b.

## Current claim ladder

| level | claim | status |
|---|---|---|
| **L1a** | internal state adds over score/history | **SUPPORTED** (G1 H2 GO; reproduced in both backbones) |
| **L1b** | the increment survives rich within-window residual controls | **PARTIALLY SUPPORTED** — exploratory |
| **L1c** | the increment survives a temporally matched residual-derived observable control (O1r) | **PARTIALLY SUPPORTED** (A+/A+S, exploratory and backbone-heterogeneous) |
| **L2** | usable online decision rule without evaluator labels | **NOT TESTED** |
| **L3** | xLSTM specificity | **UNSUPPORTED** (H3a STOP) |
| **L3'** | mLSTM complementary mechanism | **PARTIALLY SUPPORTED** — exploratory only, one seed |
| **L4** | safe adaptation / contamination benefit | **NOT TESTED** |
| **L5** | real-world longitudinal deployment | **NOT TESTED** |

These results do not establish online safe adaptation, contamination
robustness, a global xLSTM-over-LSTM advantage, long-context superiority, or
persistent cross-window memory.

## Current paper position

The recommended spine is **recurrent internal-state evidence as a measurement**
— not an xLSTM-specific mechanism, and not yet safe continual adaptation.
xLSTM is currently **one recurrent case study in a matched xLSTM/LSTM
comparison**, not the source of the headline novelty. The mLSTM line remains a
secondary exploratory mechanism analysis. Rationale and prior-art boundary:
`framing-refresh-2026-09/`.

## Next experiment

`A+` is complete as an exploratory temporally matched residual-control study.
The unresolved conditional secondary control `P1r` remains in the forward plan:
the same observable statistic family and temporal expansion computed from the
scaled input windows. `P1r` was not run in A+S. A nonlinear observable-only
probe is a separate future question and is not automatically justified or
started by A+S. Do not start `P1r`, that nonlinear probe, mLSTM seeds 22/33,
online adaptation, a safe-adaptation gate, W128/W256, or persistent recurrent
state automatically from this result.

## Branches

`research/framing-2026-09` (`8b9ed1a`) is the pre-G1 Claude Science framing
snapshot and intentionally remains on a separate branch. The completed
strong-observable-control study and the post-G1 framing refresh are
consolidated into `main`.
