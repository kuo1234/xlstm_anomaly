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

Until `A+` runs, current O1/O2 results must be described as a **rich
within-window residual control** or a **residual-controlled linear-probe
result**, never as a *matched observable control* and never as
*observable residuals are insufficient*.

## Current claim ladder

| level | claim | status |
|---|---|---|
| **L1a** | internal state adds over score/history | **SUPPORTED** (G1 H2 GO; reproduced in both backbones) |
| **L1b** | the increment survives rich within-window residual controls | **PARTIALLY SUPPORTED** — exploratory |
| **L1c** | the increment survives a temporally matched observable control | **NOT TESTED** |
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

```
DO_NEXT: A+ — temporally matched observable control
```

Primary planned comparison `H+O1r` versus `H+O1r+I`, where `O1r` applies to
every `O1` feature exactly the causal temporal expansion used by `internal234`
(current, rolling mean/std/slope at widths 4/8/16/32). Secondary planned
control `P1r`: the same observable statistic family and temporal expansion
computed from the scaled input windows. Specification:
`framing-refresh-2026-09/next_experiment_decision.md`. **Not implemented in
this repository yet.**

Dependency order — `A+`, then (if it survives) a bounded nonlinear observable
control, then (if that survives) the mLSTM replication and later decisions. Do
not start the nonlinear probe, mLSTM seeds 22/33, online adaptation, a
safe-adaptation gate, W128/W256, or persistent recurrent state before `A+`
resolves.

## Branches

`research/framing-2026-09` (`8b9ed1a`) is the pre-G1 Claude Science framing
snapshot and intentionally remains on a separate branch. The completed
strong-observable-control study and the post-G1 framing refresh are
consolidated into `main`.
