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
`H+O1r+internal234 − H+O1r` increment is `+0.026710` for xLSTM (historical
nested-bootstrap interval `[+0.022959,+0.030312]`; corrected crossed
source×seed reassessment `[+0.019509,+0.032582]`, 2/3 seed means at the old
`+0.02` reference) and `+0.010220` for the matched LSTM (historical interval
`[+0.007861,+0.012566]`, 0/3 seed means at the reference). All source-seed
directions are positive, but the backbones are heterogeneous. This provides
exploratory support that the xLSTM increment is not fully explained by this
temporally matched residual control; it is not a causal or information-
theoretic result and does not alter G1/H3a/H3b.

The historical O1/O2 results remain a **rich within-window residual control**
or a **residual-controlled linear-probe result**, not a matched control. A+
tests the narrower temporally matched O1r question; neither result licenses an
information-theoretic claim about residual observables.

### A+S solver/convergence audit

The post-hoc A+S audit found no unresolved `lbfgs` convergence failure at
`max_iter=10000`. The fixed expanded C grid changes some selected C values but
preserves the qualitative result: pooled xLSTM ΔAP remains positive and above
the historical +0.02 descriptive reference, while matched-LSTM ΔAP remains
positive but below it. The corrected crossed source×seed uncertainty is
reported separately from the historical nested bootstrap. The xLSTM
nested-superset regression persists after converged refitting. A+S is
exploratory and does not alter G1/H2/H3a/H3b.

### Bounded nonlinear observable-control stress test

The fixed `HistGradientBoostingClassifier` audit on the same A+ rows and
temporally matched O1r retained positive internal increments for all 30
source×seed cells: xLSTM source-level mean `+0.015165` (crossed exploratory
interval `[+0.012488,+0.018226]`) and matched LSTM `+0.011252` (interval
`[+0.008952,+0.013475]`). Relative to the A+S S2 linear references, the
xLSTM increment attenuated while the matched-LSTM increment stayed similar.
This is bounded nonlinear-decoder evidence only; it is not information-
theoretic, causal, or xLSTM-specific evidence, and it does not alter G1 or
reopen H3a/H3b.

Estimand note (consolidation review, 2026-09-23): the S2 references are means
of pooled per-seed deltas. The like-for-like pooled change is `−0.010904`
(−42.0 %) for xLSTM and `+0.000603` for matched LSTM. Against the A+
source-level matrix, the paired change is `−0.011545` (crossed
`[−0.018090,−0.004396]`) for xLSTM and `+0.001032`
(`[−0.002232,+0.003821]`) for LSTM. The xLSTM attenuation occurs because
HGB raises the observable-only `H+O1r` arm by `+0.029182`, more than the whole
linear increment. The xLSTM − LSTM increment gap shrinks from `+0.016490`
(linear) to `+0.003913` and tracks the lower xLSTM observable-only baseline.
See `nonlinear_observable_control/post_review_addendum.md`.

### P1r input-derived observable control (sealed; last synthetic observable control)

P1r is the scaled `[64,8]` input window summarised by the frozen 128-column O1
statistic family, followed by the identical causal 4/8/16/32 expansion (1,664
columns, support `[t−94, t]`). It is a bounded input-derived observable summary,
not the complete observation. The six sealed runs used the frozen HGB decoder on
the A+ rows and were executed on the GB10 cache host under seal `90b2470`. The
estimand is the source-level mean of `AP(H+P1r+internal234) − AP(H+P1r)` over
10 sources × 3 seeds:

| backbone | mean ΔAP | crossed interval (exploratory) | positive cells | outcome |
|---|---:|---:|---:|---|
| xLSTM | −0.000233 | [−0.000761, +0.000291] | 14/30 | `NO_RESOLVED_ADDITIONAL_UTILITY` |
| matched LSTM | +0.000289 | [−0.000415, +0.000959] | 17/30 | `NO_RESOLVED_ADDITIONAL_UTILITY` |

Under the frozen HGB decoder, no additional predictive/decodable utility of
`internal234` beyond P1r is resolved for either backbone. P1r closes the
predeclared synthetic input-derived-control stage, not every possible
observable representation. See `input_derived_observable_control/`.

## Current claim ladder

| level | claim | status |
|---|---|---|
| **L1a** | internal state adds over score/history | **SUPPORTED** (G1 H2 GO; reproduced in both backbones) |
| **L1b** | the increment survives rich within-window residual controls | **PARTIALLY SUPPORTED** — exploratory |
| **L1c** | the increment survives a temporally matched **residual-derived** observable control (O1r) under the fixed L2 logistic probe | **PARTIALLY SUPPORTED** (A+/A+S, exploratory; converged, grid-stable; the backbone asymmetry here is largely a linear-probe effect, see L1c-NL) |
| **L1c-NL** | the same O1r increment survives a fixed bounded nonlinear decoder (HGB) | **PARTIALLY SUPPORTED** (exploratory; `+0.015165` / `+0.011252`, 30/30 cells each, both below the `+0.02` reference; xLSTM attenuated about 42 %, LSTM unchanged) |
| **L1c-P** | `internal234` retains additional predictive/decodable utility under the fixed decoder beyond the temporally matched **input-derived observable summary** P1r (the last bounded input-derived control) | **NOT SUPPORTED at this resolution** — `NO_RESOLVED_ADDITIONAL_UTILITY` for both backbones (xLSTM −0.000233 [−0.000761, +0.000291]; LSTM +0.000289 [−0.000415, +0.000959]); closes the predeclared synthetic input-derived-control stage, not every possible observable representation |
| — | information-theoretic superiority of `internal234` over the full causal observation | **OUT OF SCOPE IN PRINCIPLE** — `internal234` is a deterministic function of the causal input window |
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

The synthetic ladder is now complete. The measurement claim holds relative
to score/history (L1a) and, in exploratory studies, relative to residual-derived
summaries (L1b, L1c, L1c-NL). Relative to the bounded input-derived summary P1r
(L1c-P), no additional predictive/decodable utility is resolved.

## Next experiment

The synthetic observable-control ladder is complete: A+, A+S, the bounded
nonlinear audit and P1r, the last bounded input-derived control. As
predeclared, P1r authorises no further observable summary, decoder, HGB budget,
MLP/CNN, W128/W256, persistent-state experiment or post-hoc rescue control.

**The next scientific stage is R0: real-data recurrent-state measurement
validation.** Its protocol is sealed on `research/real-data-r0-protocol`
(`research/real_data_r0/`): three SMD machines (machine-1-8, machine-2-1,
machine-1-4), H vs H+internal234, Design B (within-machine blocked probe; the
comparability audit found 4/18 base statistics polarity-dependent across
independently trained detectors), 18 planned detector fits (xLSTM 75,934 /
matched LSTM w=38 74,100 parameters at D=38). Raw bytes are verified (9/9) and
preserved git-ignored under `data/external_real/r0_smd/` in the GB10 primary
checkout; the result-blind preflight passed.

**Execution status: R0_EXECUTION_BLOCKED** (branch
`experiment/real-data-r0-execution`). Six of 18 detectors were trained
(xLSTM, machine-1-8 and machine-2-1); the checkpoint parity gate of
machine-2-1 / xLSTM / seed 22 failed (1 of 311,296 canary reconstruction
outputs beyond the frozen vanilla-vs-CUDA tolerance; score and common18 agree
to ≤ 3.6e-7), so R0 stopped fail-closed. No label was read, no probe was fitted
and no R0 result exists (not a null result). Continuing needs an owner-approved,
result-blind amendment; see `research/real_data_r0/execution.md`.

**r0-v1.1 (owner Option 2: vanilla/reference xLSTM extraction): R0_V1_1_EXECUTION_BLOCKED.**
All nine xLSTM detectors are trained/reused and extracted on the single vanilla
path (six v1 checkpoints reused without retraining; five v1 CUDA caches
invalidated). The sealed matched-LSTM observer then failed its replay-parity
check on one of 185 test batches of machine-1-8 / LSTM / seed 11 (max |Δ|
3.08e-5 in `decoder.2` hidden sequence), so R0 stopped again: 10/18 detector
fits, 9/18 feature caches, nothing sealed, no label read, no result. Owner
decision required (`execution.md`, r0-v1.1 section).

- **No SMD training** outside the sealed R0 execution contract.
- **Feasibility worktree.** Its SMD bytes are now copied to the stable GB10
  location and are reproducible from the pinned public URL; it still holds
  non-SMD feasibility files, so pruning it remains the owner's decision.
- **R1** (HAI 22.04) is recorded prospectively and is gated only on acquisition,
  provenance and compatibility, never on the R0 outcome.

## Branches

`research/framing-2026-09` (`8b9ed1a`) is the pre-G1 Claude Science framing
snapshot and intentionally remains on a separate branch. The completed
strong-observable-control study and the post-G1 framing refresh are
consolidated into `main`.

The post-G1 observable-control line (A+ `04e0abb`, A+S `ccb9a3d`, nonlinear
`0b00d6f`), the consolidation review `aa0860c` and the independent A+ review
`f1967b6` are consolidated into `main` through
`consolidation/observable-control-line`. `f1967b6` was merged explicitly
because it is not an ancestor of `0b00d6f`. Validation is in
`consolidation_review_2026-09/final_consolidation_report.md`.
The P1r line (seal `90b2470`, preflight `4c22e52`, six run commits,
aggregate `af6cc47`, assessments and red-team) is consolidated into `main` from
`experiment/input-derived-observable-control`.
`research/real-data-feasibility-audit` (`8f6ee87`) is a data-provenance record
kept on its own branch.
