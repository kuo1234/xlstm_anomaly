# Adversarial review of the current evidence

Written as a skeptical reviewer with access to the repository. Every number is recomputed from the
committed result tables; the recomputation is stated in §0 so it can be checked.

Sources: `research/strong_observable_control/results_{xlstm,lstm}.md` and `scenario_results.md` on
`experiment/strong-observable-control` (`f9014a2`); `research/lstm_standalone_diagnostic/results.md`,
`research/mlstm_dense_attribution/{stride1_results,family_ablation,architecture_audit}.md` and
`research/CURRENT_STATUS.md` on `main` (`caa9b3c`).

---

## 0. Recomputed evidence table

Pooled test AP, mean over detector seeds 11/22/33.

| arm | xLSTM | LSTM |
|---|---:|---:|
| H14 | 0.788072 | 0.796634 |
| H+I | 0.930342 | 0.938267 |
| H+O1 | 0.898133 | 0.931473 |
| H+O1+I | 0.937717 | 0.946744 |
| H+O2 | 0.864101 | 0.893569 |
| H+O2+I | 0.935319 | 0.946596 |

Mean increments:

| increment | xLSTM | LSTM |
|---|---:|---:|
| `I|H` | +0.142270 | +0.141634 |
| `O1|H` | +0.110061 | +0.134839 |
| `O2|H` | +0.076029 | +0.096935 |
| `I|H+O1` | **+0.039584** | **+0.015271** |
| `I|H+O2` | +0.071218 | +0.053027 |

Per-seed `I|H+O1`: xLSTM `+0.042685, +0.033769, +0.042297`; LSTM `+0.017132, +0.016851, +0.011830`.
Seeds clearing the `+0.02` practical reference: xLSTM 3/3, LSTM **0/3**.
The O1 control removes 72.2% of the xLSTM internal increment and **89.2%** of the LSTM one.

---

## 1. Weak-control argument — **the attack succeeds**

The question was whether O1/O2 sufficiently address observable residual information. Two defects,
one of them decisive.

### 1a. The arms are not matched on temporal span (decisive)

Verifiable in `scripts/strong_observable_control.py` at `f9014a2`:

```
history14()        score, delta, + rolling(mean,std,slope) over widths 4,8,16,32   -> 14 cols
expand_internal()  per base column: current + rolling(mean,std,slope) over 4,8,16,32
                   -> 18 x 13 = 234 cols
_make_records()    "O1": arrays["o1"][keep]              <- raw, 128 cols, no rolling
                   "O2": [R, R**2] flattened             <- raw, 1024 cols, no rolling
```

`ROLLING_WIDTHS = (4, 8, 16, 32)` is the same frozen G1 constant (`scripts/phase_g1_core.py:39`).
The internal arm therefore sees a 13x causal multi-scale expansion over the last 4–32 decisions;
the observable residual arms see the current W64 window only, and the sole cross-window observable
is the 14-column score history. The reported effect is "internal summaries *with* multi-scale
temporal context beat residual descriptions *without* it".

The scenario strata behave exactly as that explanation predicts and are difficult to reconcile with
a state-specific one:

| scenario | xLSTM `I|H+O2` | LSTM `I|H+O2` | cross-window context required? |
|---|---:|---:|---|
| abrupt | +0.004952 | +0.007928 | no — one post-shift window shows it |
| correlation | +0.013368 | −0.001534 | no — O1 contains the covariance (36) and correlation (28) columns |
| gradual | +0.035525 | +0.037092 | yes — a trend spans several windows |
| recurring | +0.096762 | +0.056064 | yes — requires memory of an earlier regime |

The two strata where the current window already suffices retain essentially nothing; the two that
require history retain everything. `interpretation.md` records "recurring regimes carry the largest
remaining increment" as a descriptive hypothesis about *mechanism*; the simpler reading is that
recurring is where the control arm is most handicapped.

This is not a fatal objection to the project — it is a missing arm, and the arm is cheap. But until
it is run, paper spine A's sentence "observable residuals are insufficient under matched
low-capacity probes" contains a word (*matched*) that the protocol does not support.

### 1b. No arm contains the observations

`scripts/strong_observable_control.py` caches `timestamp, score, internal_base18, residual, o1`.
The reconstruction output and the scaled input window are not retained, so `X` is not recoverable
from the cache and no arm in the ladder is a function of the observations as such. The internal
state is a deterministic function of the input window; the claim "internal state adds beyond
observable *residuals*" is literally what was tested, but the claim a reviewer will hear is
"internal state adds beyond what is observable", and that is not what was tested. For a
*drift*-versus-anomaly task, where the defining event is a change in the input distribution, the
input trajectory is the most natural observable control and it is absent.

### 1c. The headline was taken against the weaker of two controls

O1 (128 engineered columns) outperforms O2 (1024 raw columns) under the linear probe for both
backbones — `O1|H` `+0.110061` / `+0.134839` versus `O2|H` `+0.076029` / `+0.096935`. The
pre-registered *primary* contrast is `I|H+O2`, i.e. against the weaker control. Nothing was tuned
after the fact, and both contrasts were declared in `protocol.md` — but the defensible headline
number is the **minimum over available controls**: `+0.039584` (xLSTM) and `+0.015271` (LSTM), not
`+0.0712` / `+0.0530`. Reporting the O2 contrast as the primary result while the O1 contrast is
2–3.5x smaller will read as control selection whether or not it was.

**Consequence.** Under the strongest observable control already available, the matched LSTM's
internal increment (`+0.015271`, 0/3 seeds above margin) is **below the project's own practical
margin**. Any statement of the form "recurrent internal state carries drift-versus-anomaly
information beyond observables" currently rests on a single architecture and an unmatched control.

---

## 2. Nonlinear-accessibility argument — **the attack succeeds, but it is second in line**

Could a modest nonlinear observable-only model recover the apparent internal gain? Very likely in
part, and the repository's own numbers say so indirectly: a 128-column *engineered nonlinear
summary* of the residual (O1 — RMS, absolute means, slopes, lag-1 autocorrelation, covariance and
correlation entries) beats the 1024-column *raw* residual by `+0.034` (xLSTM) and `+0.038` (LSTM) AP
under the same L2 probe. The probe cannot extract from raw `R` what hand-built nonlinear statistics
hand it. The recurrent cell is, among other things, a nonlinear feature extractor over the same
window; part of `I|H+O2` is therefore a statement about *linear accessibility*, which
`interpretation.md` correctly says, and not about information content.

Two further reasons the linear-probe framing is fragile:

- `results_xlstm.md` and `results_lstm.md` both record that high-dimensional `lbfgs` fits hit the
  frozen `max_iter=1000` ceiling for some arms. Non-convergence in the *control* arm inflates the
  increment. The protocol was correctly not changed after seeing outcomes, but the direction of the
  bias is not neutral and is not quantified.
- The arms differ in dimension by an order of magnitude (`H+O2` = 1038 versus `H+O2+I` = 1272 versus
  `H+O1` = 142). L2 with a four-value `C` grid selected on pooled validation AP is a reasonable but
  not a capacity-matched control; there is no random-projection or shuffled-internal arm anywhere in
  the study to bound how much of the increment is available from 234 arbitrary columns.

**But it is second.** A nonlinear observable-only probe answers "is the internal state a useful
*representation*". The temporal-matching arm answers "is the internal state carrying *different
evidence*". If the increment is a temporal-span artifact, the nonlinear result is uninterpretable
whichever way it comes out, so §1 has to be resolved first. When the nonlinear test is run, it must
be run on **both** arms of the same class (observable-only and observable+internal), or the
comparison measures the probe rather than the features.

---

## 3. Synthetic-only argument — **damaging in a specific, bounded way**

The honest position is that the measurement *cannot currently be made anywhere else*. Both
literature sweeps failed to find a public dataset with per-timestamp drift-versus-anomaly ground
truth; the pre-G1 map records this as family F4's principal gap, and the refresh did not overturn
it. The estimand requires evaluator-side truth about which changes are legitimate, and that truth
only exists where the data were generated. So "synthetic-only" is a property of the question, not a
shortcut — and that is a defensible paragraph in a paper.

What is *not* defensible, and what a reviewer will press:

- **One generator, one dimensionality, one window.** D=8 channels, W64, 10 test sources, 4 scenarios
  x 5 conditions. Every number in this review comes from that one object. The effect sizes are very
  large (`I|H` ≈ `+0.14` on an `H14` baseline of `0.79`); large effects on a single synthetic family
  are the classic signature of a generator-specific regularity.
- **Marginals move in three of four scenarios.** Only the correlation scenario has analytically
  matched marginals (Phase B). In abrupt/gradual/recurring, drift changes the observable marginal
  distribution, so a summary that tracks input level or scale will separate the classes. `claim_map`
  E3 already prohibits the semantic reading; the synthetic design makes the trivial reading *likely*
  rather than merely possible. Note that the correlation stratum — the one with matched marginals —
  is where the residual-controlled increment is smallest and, for the LSTM, negative
  (`−0.001534`).
- **External validity has no route from here.** The A2/TSB stress set has no drift/anomaly truth and
  the pre-G1 package already records that its benchmark citation does not resolve. There is no
  incremental path to a real-data L1; there is only a substitution (adopt a CPS benchmark with
  documented process changes and documented fault windows — HAI 22.04, used by
  `10.1109/icaiset66439.2026.11541767`, is the nearest candidate) and that substitution changes the
  estimand from "drift versus anomaly" to "documented-change versus documented-fault".

**Verdict.** Synthetic-only caps the venue, not the validity. It makes spine A a solid
methods/measurement paper and blocks a top-tier empirical claim. It does not justify abandoning the
measurement, and it is not a reason to move to adaptation — an adaptation experiment on the same
generator inherits every one of these limits and adds new ones.

---

## 4. Architecture argument — **the attack succeeds; xLSTM should not be central**

The common-state effects are indistinguishable: `+0.142519` (xLSTM, authoritative H2) versus
`+0.142966` (matched LSTM, post-hoc reconstruction, 50/50 units positive, 5/5 seeds, 10/10 sources,
bootstrap CI `[0.137904, 0.147702]`). H3a is STOP. The matched LSTM increment is, if anything,
*larger*.

The strong-control study is sometimes read as restoring an xLSTM advantage (`+0.0712` versus
`+0.0530`). It does not, for three reasons:

1. **The absolute ceiling favours the LSTM.** `H+O1+I` = `0.946744` (LSTM) versus `0.937717`
   (xLSTM); `H+O2+I` = `0.946596` versus `0.935319`. On the task itself, the conventional LSTM plus
   its internal state is the better system.
2. **The xLSTM advantage in the *increment* is an advantage in having a worse baseline.** The
   observable control arms are `0.033339` AP weaker for xLSTM at `H+O1` and `0.029468` weaker at
   `H+O2`. A larger increment onto a lower floor that ends at a lower ceiling is not an advantage.
3. **No paired inference exists across architectures.** The two backbones were analysed in separate
   runs with separate probes; there is no source-level paired contrast, no multiplicity control, and
   the cross-architecture comparison was not a declared contrast of the strong-control protocol.

The one datum that genuinely discriminates: under O1, xLSTM clears the `+0.02` reference in 3/3
seeds and the LSTM in 0/3. If real, it says the xLSTM state is *harder to replace with residual
statistics*. It is confounded by (2), it is three seeds, and it was not pre-registered. It is a
hypothesis to test in the matched-control experiment, not a result.

**Verdict.** Decision **B** — xLSTM as one recurrent case study. The matched pair stays as the
control that licenses the not-xLSTM-specific claim. See `executive_assessment.md` §3.

---

## 5. Mechanism argument — **the mLSTM story loses its distinctiveness**

`ΔC_history = −0.000592` and `ΔC_given_sLSTM = +0.006610`, with `H+M_noC = 0.936035` already
*above* `H+M_full = 0.935443`. The repository's own classification is
`DENSE_MLSTM_SIGNAL_NOT_MATRIX_SPECIFIC`, and that is the correct reading. What remains is
"the mLSTM block's hidden/normalizer/stabilizer summaries add `+0.016657` after sLSTM, on one seed".
Four independent problems with using that as a paper spine:

- **No dimension control.** `H+S` is 248 columns and `H+S+M_full` is 482. The `+0.016657` increment
  is measured by adding 234 columns to an L2 probe. The study's *own* dimension-matched comparison
  (`H+M_full` 248 versus `H+S` 248) is `+0.002034` — an order of magnitude smaller. No
  random-projection or shuffled-feature arm exists to bound the capacity contribution.
- **No residual control.** The mLSTM screen predates O1/O2 and was never run against them. Given
  that O1 removes 72–89% of the common internal increment, the expected surviving mLSTM increment
  after a residual control is a small fraction of `+0.016657`.
- **The observed quantity is partly reconstructed, not read.** `architecture_audit.md` states that
  the native parallel mLSTM implementation exposes the normalized hidden output but **not** a
  history of `C`, `n`, `m`; the observer captures q/k/v and *replays the pinned stabilized recurrence
  from zero state*. The mLSTM "internal state" is therefore an independent-window re-derivation, not
  the state the trained detector actually carried. That is fine for a diagnostic and awkward for a
  mechanism claim, and it also means the mLSTM arm has no persistent-state content by construction.
- **One seed.** Acknowledged in the repository.

**Verdict.** The mLSTM line is an ablation subsection at most. It cannot carry spine B. If it is
pursued, the three-seed replication must add the two missing controls (dimension-matched
random-feature arm; O1 residual control) or it will reproduce an uninterpretable number three times.

---

## 6. Prior-art argument — **the attack partly succeeds and has got worse since the pre-G1 sweep**

*"CANDI already uses anomaly score + latent similarity to identify potential false positives under
distribution shift — what exactly is different here?"*

The honest answer has three parts, and only the first survives scrutiny.

1. **Different object.** CANDI's False Positive Mining is a *selection heuristic* validated through
   downstream AUROC (up to +14%). It never asks how much information the latent similarity carries,
   never compares it against a residual control, and has no per-timestamp truth about which windows
   are drift and which are anomalies. The project measures the quantity CANDI assumes. That
   difference is real and is the whole contribution.
2. **Different evidence source** — *weak*. CANDI uses a static latent distance; the project uses
   causally-expanded recurrent state dynamics. But MD-RS (`10.36227/techrxiv.22678774`) already
   established the general form "recurrent internal state is a better anomaly statistic than the
   prediction error from the same recurrent model", and iADCPS (`arXiv:2504.04374`) already drives
   incremental adaptation from a state-space model's learned latent dynamics. The evidence *source*
   is occupied; only the *accounting* is not.
3. **Different setting** — *weak and shrinking*. SCALE separates domain drift from true anomalies
   online with two decoupled model-derived criteria and publishes a benchmark for exactly this
   setting. AnDri co-detects anomalies and drift with a dynamic normal model whose patterns are
   activated, deactivated and added. The setting is crowded.

**New since the pre-G1 sweep, and materially damaging:** the pre-G1 package's one clean mechanism
gap was reset *semantics* — "every retrieved reset reverts toward a fixed source model; none
reverses a single normality commitment while preserving others". AnDri's deactivation of an
individual normal pattern is that operation. The slot is no longer clean.

**Verdict.** The project may claim a measurement and an accounting. It may not claim the construct,
the framing, the mechanism shape, or the reset semantics.

---

## 7. Two attacks the project has not anticipated

**7a. The borrowed statistics have a documented failure mode.** The pre-G1 design space recommends
borrowing anytime-valid machinery for the eventual operating point. `arXiv:2608.30502` measures that
route end-to-end: a conformal test martingale gating online updates of a Kalman adapter over frozen
forecasting models fired in **at most 1 of 60** runs on exchangeable synthetic streams and in
**135 of 135** clean-stream runs on real data at α = 0.05, with repeated fires holding the gate's
drift response active and the gated filter amplifying the transient it was meant to prevent. Any L2
proposal that assumes a conformal/e-value gate will supply calibrated error control on a detector's
own score stream now has to answer this paper directly.

**7b. The feedback-endogeneity argument is load-bearing and nearly undocumented.** The pre-G1
self-review flagged that it appears only inside one discussion section. It matters more now: once a
gate acts on internal state, the internal state it reads is a function of its own past decisions, so
every offline estimate in this project — including all of the numbers in §0 — is an estimate under
the *frozen*-detector regime and does not transfer to the closed loop. This should be stated in the
limitations of any paper built on spine A, not just in a design document.

---

## 8. What survives the review

- `L1a` — internal summaries add information beyond the scalar score/history control. **Survives**:
  confirmatory (H2 GO, all frozen gates), replicated on a matched LSTM, 50/50 units, and reproduced
  independently in the strong-control study's sanity arm (`I|H` `+0.142270` / `+0.141634`).
- `L1b` — the increment survives a strong *within-window* observable residual control. **Survives as
  exploratory**, with the caveats of §1c: 30/30 source×seed units positive for both backbones under
  O2; under O1 it clears the practical margin for xLSTM only.
- `L1c` — the increment survives a *temporally matched* observable control. **Not tested.** This is
  the load-bearing claim for spine A and the subject of `next_experiment_decision.md`.
- Everything at L2 and above. **Not tested**, and the refresh has made two of those levels harder,
  not easier.
