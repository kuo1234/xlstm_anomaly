# Executive assessment — post-G1 framing refresh (2026-09)

Scope: a research-level reassessment of the project against the **current** evidence state, not
against the pre-G1 narrative. The pre-G1 package (`research/framing-2026-09`, commit `8b9ed1a`) is
treated as a historical snapshot and is not modified. G1 artifacts are read-only.

**Evidence base for this review**

| Source | Commit | What it supplies |
|---|---|---|
| `main` | `caa9b3c` | authoritative G1 summary; post-hoc standalone-LSTM diagnostic; dense stride-1 mLSTM attribution; CUDA/observer engineering |
| `experiment/strong-observable-control` | `f9014a2` | O1/O2 residual-control stress test, seeds 11/22/33, xLSTM + matched LSTM |
| `research/framing-2026-09` | `8b9ed1a` | prior literature sweep (78 records, 61 full texts), claim ladder, positioning table |
| literature refresh | 2026-09 | OpenAlex + arXiv targeted sweep; see `direct_prior_art.md` |

All numeric values quoted below were recomputed from the committed result tables, not copied from
prose. The two-line summary of the recomputation is in `evidence_red_team.md` §1.

---

## The four questions, answered

### 1. What is actually novel now?

**One thing, and it is narrower than the project's current framing.**

> Under a frozen detector and a fixed low-capacity probe, *causally-expanded recurrent internal
> summaries* retain incremental average-precision for the anomaly-versus-legitimate-drift
> distinction after a strong within-window observable reconstruction-residual control.

What is novel is the **measurement contract**, not the construct and not the mechanism: frozen
detectors so adaptation cannot confound the estimate, evaluator-side per-timestamp drift/anomaly
truth, a pre-registered practical margin, an observable control ladder, and a protocol that reports
a null (H3a STOP was reported, not buried). Nothing retrieved in either literature sweep measures
incremental information about the drift-versus-anomaly distinction against a residual-trajectory
control at a fixed backbone.

**What is *not* novel, and must be stated as prior art rather than contribution:**

- *Internal recurrent state as the anomaly statistic instead of prediction error.* MD-RS
  (`10.36227/techrxiv.22678774`, 2023) detects anomalies from the Mahalanobis distance of
  **reservoir states** and reports superiority over prediction-error methods **on the same
  reservoir**. That is a head-to-head "recurrent state beats the residual" result, three years old.
  It is anomaly-versus-normal, not anomaly-versus-drift, and the states are untrained random
  features — but the *construct* is occupied.
- *Internal quantities gating adaptation under normality shift.* CANDI, COMET, M2N2, MemStream,
  EATA and the 2026 safety-gated CPS framework all do this.
- *Separating legitimate drift from true anomaly online.* SCALE (`10.1145/3770855.3817912`) does it
  with two decoupled model-derived criteria and ships a multi-domain benchmark for the setting.
- *A dynamic normal model that activates, deactivates and adds normal patterns.* AnDri
  (`arXiv:2506.15831`; demo `10.1145/3746252.3761481`) does this. **This closes the one mechanism
  slot the pre-G1 package had identified as genuinely unoccupied** — "reverse one normality
  commitment while preserving others". See `direct_prior_art.md`.

### 2. What is already covered by prior work?

Everything in the *mechanism* half of the project. Admission control on a normality buffer, deferred
commitment, drift-triggered reset, stable/plastic memory, drift-type-conditioned replay
(ADA-ADF, `10.1016/j.asoc.2025.113903`), safety-gated adaptation on a recurrent detector
(`10.1109/icaiset66439.2026.11541767`), and multi-regime normality with deactivation (AnDri) are all
published. The four-part shape the project assumed is instantiated at least twice on simple
detectors and now at least once on a GRU autoencoder in a CPS benchmark.

Three slots remain weakly occupied and are listed with their evidence in `paper_spines.md` §5:
contamination-harm accounting, a bounded-risk update policy derived from an explicit cost
asymmetry, and calibrated adaptation confidence on non-exchangeable streams.

### 3. Should xLSTM remain central?

**No. Decision: B — xLSTM becomes one recurrent case study, not the central architecture.**

The evidence for demotion:

- The authoritative common-state effect is **not** xLSTM-specific: xLSTM `+0.142519` versus matched
  LSTM `+0.142966`, 50/50 source×seed units positive. H3a is STOP.
- Under the strong observable control the matched LSTM reaches a **higher absolute ceiling** on the
  task: pooled-seed mean AP `H+O1+I` = `0.946744` (LSTM) versus `0.937717` (xLSTM).
- The larger xLSTM residual-controlled increment is substantially an artifact of a **weaker
  control arm**: xLSTM `H+O1` = `0.898133` versus LSTM `H+O1` = `0.931473`, a `0.033339` AP deficit
  in the observable baseline that mechanically leaves more headroom for `I`.
- The mLSTM-specific mechanism story did not survive its own attribution screen: matrix memory `C`
  is `-0.000592` in the H-only contrast and `+0.006610` conditional on sLSTM, so the layer signal is
  carried by hidden/normalizer/stabilizer summaries. One seed, no residual control, no
  dimension-matched control.

The evidence against outright removal (option D):

- One qualitative architecture divergence does survive the strongest control and should be reported:
  under the O1 control the internal increment clears the project's `+0.02` practical reference in
  **3/3** xLSTM seeds (`+0.039584` mean) and **0/3** matched-LSTM seeds (`+0.015271` mean). This is
  confounded by the unequal `H+O1` baselines above and was not a pre-registered contrast, so it is a
  hypothesis, not a result — but it is the only architecture-discriminating signal in the corpus.
- The xLSTM-TSAD literature is still exactly two papers (`arXiv:2405.04517`, `arXiv:2506.22837`),
  neither of which touches internal state. A careful negative or neutral result is the first
  published evidence either way.
- The matched xLSTM/LSTM pair (F-v4 PASS) is what makes the not-xLSTM-specific claim credible. It
  is the control, and controls are not discarded.

Fallback: if the three-seed dense mLSTM replication is null, drop to **C** (secondary mechanism
analysis) — xLSTM survives only as an ablation appendix.

### 4. Which next experiment has the highest information value?

A **temporally-matched observable control**, not the nonlinear probe. Full ranking, costs and
decision rules in `next_experiment_decision.md`; the reason is in `evidence_red_team.md` §1 and is
summarized immediately below because it changes the project's headline claim.

---

## The finding that dominates this review

The internal arm and the observable arms are **not matched on temporal span**, and this is
verifiable in committed source rather than inferred.

In `scripts/strong_observable_control.py` (commit `f9014a2`):

- `history14()` expands the scalar score with causal rolling mean/std/slope at widths `4, 8, 16, 32`
  → 14 columns.
- `expand_internal()` applies the **same** causal rolling expansion to each of the 18 internal base
  columns → `18 x 13 = 234` columns.
- `O1` (128 columns) and `O2` (1024 columns) are inserted **raw**, with no rolling expansion at all
  (lines 329–330). Both are *within-window* residual descriptions of the current W64 window.

So the only cross-window observable evidence available to the control arms is the 14-column score
history, while the internal arm carries a 13x multi-scale causal expansion over the last 4–32
decisions. "Internal state beats residuals" is therefore confounded with "multi-scale temporal
context beats a single-window snapshot".

The scenario strata are exactly what that confound predicts, and are hard to explain otherwise:

| scenario | xLSTM `I|H+O2` | LSTM `I|H+O2` | what the observable arm already sees |
|---|---:|---:|---|
| abrupt | +0.004952 | +0.007928 | a single post-shift window shows the level change — nothing left |
| correlation | +0.013368 | -0.001534 | O1 carries the covariance and correlation upper triangles — nothing left |
| gradual | +0.035525 | +0.037092 | needs several windows of trend — only the internal arm has them |
| recurring | +0.096762 | +0.056064 | needs memory of a previously seen regime — only the internal arm has it |

The increment concentrates precisely in the two regimes where cross-window context is required and
vanishes in the two where the current window suffices. That is a complete alternative explanation of
the headline result that costs the project nothing to test: the fix is a probe refit on the existing
observation cache, with the identical rolling expansion applied to the 128 O1 columns
(`128 x 13 = 1664`).

A second, weaker asymmetry: the cache stores `timestamp, score, internal_base18, residual, o1` only.
The model output and the input window are not retained, so **no arm in the ladder contains the
observations themselves**. The internal state is a deterministic function of the input; "internal
adds beyond the residual" is not yet distinguished from "the input adds beyond the residual".

---

## Bottom line

- The project has a **real, replicated, control-resistant measurement** at L1, and no evidence at
  all at L2–L5. That asymmetry is wider than the pre-G1 package assumed, because the post-G1 work
  strengthened L1 and the literature refresh weakened the mechanism novelty.
- The single strongest claim available today is replicated in both xLSTM and a capacity-matched
  LSTM — the common-state effect is not xLSTM-specific within the two tested recurrent backbones,
  which is not the same as a claim about recurrent architectures in general — and it is currently
  **one missing control away from being a temporal-span artifact**.
- Online adaptation is premature, and the refresh supplies an empirical reason beyond
  "we haven't run it": `arXiv:2608.30502` shows an off-the-shelf anytime-valid gate on a deployed
  detector's own score stream fired in **135 of 135 clean-stream runs**, and the gated filter
  amplified the transient it was meant to prevent. The statistical machinery the project planned to
  borrow for L2 has a documented failure mode on real streams.

## Where the required outputs live

| output | file |
|---|---|
| OUTPUT 1 — updated claim map (8 columns) | `updated_claim_map.md` Part 2 |
| L1–L5 reassessment with statuses | `updated_claim_map.md` Part 1 |
| OUTPUT 2 — direct prior art (20 works, threat levels) | `direct_prior_art.md` |
| OUTPUT 3 — paper position | `paper_spines.md` §"OUTPUT 3" |
| OUTPUT 4 — `DO_NEXT` and two conditional branches | `next_experiment_decision.md` §"OUTPUT 4" |
| Red-team of the six named attacks (+ two unanticipated) | `evidence_red_team.md` |
| Paper spines A–D scored | `paper_spines.md` |
| Safe-adaptation differentiation | `paper_spines.md` §5 |
| Nonlinear-control decision and frozen specification | `next_experiment_decision.md` |
| xLSTM decision | this file §3, supported by `evidence_red_team.md` §4 |
