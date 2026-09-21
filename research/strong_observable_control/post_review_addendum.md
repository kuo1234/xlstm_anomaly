# Post-review addendum (2026-09)

This note is an **interpretation addendum**, added after an independent review of the completed
study. It changes no protocol, no arm definition, no numerical output and no historical file:
`protocol.md`, `residual_schema.md`, `extraction_validation.md`, `compute_benchmark.md`,
`results_xlstm.md`, `results_lstm.md`, `scenario_results.md`, `results*.json` and
`scripts/strong_observable_control.py` are unchanged. The study remains **exploratory**; nothing
here promotes it to a confirmatory result or creates a new p-value family or GO/STOP rule.

## 1. O1 is the empirically stronger observable control, not O2

`O2` (1,024 raw residual-trajectory columns) was predeclared as the primary control and that
prioritization stands as protocol history. It is **not** the empirically strongest observable-only
arm. Under the same frozen L2 probe the 128-column engineered summary `O1` reaches a higher
observable-only AP for both backbones:

| observable-only increment over `H14` | xLSTM | matched LSTM |
|---|---:|---:|
| `O1 \| H` | +0.110061 | +0.134839 |
| `O2 \| H` | +0.076029 | +0.096935 |

Consequently the internal increment conditional on `O1` is the smaller, and therefore the more
conservative, number:

| internal increment | xLSTM | matched LSTM |
|---|---:|---:|
| `I \| H+O1` | **+0.039584** | **+0.015271** |
| `I \| H+O2` (predeclared primary) | +0.071218 | +0.053027 |

Per-seed `I|H+O1`: xLSTM `+0.042685, +0.033769, +0.042297`; matched LSTM
`+0.017132, +0.016851, +0.011830`. Seeds clearing the `+0.02` practical reference: xLSTM 3/3,
matched LSTM **0/3**.

**Reporting rule going forward.** Documentation must not imply that `O2` is the strongest
observable control merely because it has the most dimensions. Describe the two arms as:

- `O2` — high-dimensional **raw residual-trajectory** control (predeclared primary);
- `O1` — **empirically stronger engineered residual control** under the current linear probe.

Where a single summary figure is quoted, quote the **minimum over available controls**
(`+0.039584` xLSTM, `+0.015271` matched LSTM) and state which control produced it.

## 2. The arms are not temporally matched

Verified in `scripts/strong_observable_control.py` (unchanged):

- `history14()` — current value, first difference, plus causal rolling mean/std/slope at widths
  `4, 8, 16, 32` → 14 columns.
- `expand_internal()` — the **same** causal rolling expansion applied to each of the 18 internal
  base columns → `18 x 13 = 234` columns.
- `_make_records()` — `O1` (128) and `O2` (1024) are inserted **raw**, with no rolling expansion.
  Both describe the current W64 window only.

The only cross-window observable available to a control arm is the 14-column score history. The
internal arm therefore carries multi-scale causal context over the last 4–32 decisions that no
residual arm has. **The reported internal increment may partly or largely measure cross-window
temporal context rather than an internal-state-specific representation.**

The scenario strata in `scenario_results.md` are consistent with that reading: the
residual-controlled increment is small where a single window already exposes the change
(abrupt `+0.004952` / `+0.007928`; correlation `+0.013368` / `−0.001534`, and `O1` carries the
covariance and correlation entries directly) and largest where cross-window context is required
(gradual `+0.035525` / `+0.037092`; recurring `+0.096762` / `+0.056064`). This is an alternative
explanation, not a demonstrated one — it is exactly what the planned `A+` experiment tests.

A second, weaker gap: the observation cache stores `timestamp, score, internal_base18, residual,
o1` and no model output, so the scaled input window is not recoverable from it and **no arm in the
ladder is a function of the observations themselves**.

## 3. Wording constraints until `A+` resolves

Do **not** describe the current study as a *matched observable control*, a *temporally matched*
control, or as showing that *observable residuals are insufficient*. Use **rich within-window
residual control** or **residual-controlled linear-probe result**.

Do **not** describe the common-state effect as *generic across recurrent architectures*. Only two
backbones were tested. Use **replicated in both xLSTM and a capacity-matched LSTM**, or **the
common-state effect is not xLSTM-specific within the two tested recurrent backbones**.

## 4. What this addendum does not change

The scientific conclusion of the study is intact in its narrow form: under a frozen detector and
the frozen L2 probe, internal summaries retain a positive increment after a rich within-window
residual control, positive in 30/30 source×seed units for each backbone under `O2`. The
classification `STRONG_OBSERVABLE_SURVIVAL` in `interpretation.md` refers to that narrow statement
and is unchanged. What the addendum removes is the stronger reading — that the residual controls
were matched, or that residuals demonstrably lack the information.

Full analysis: `../framing-refresh-2026-09/evidence_red_team.md` §1; planned resolution:
`../framing-refresh-2026-09/next_experiment_decision.md`.
