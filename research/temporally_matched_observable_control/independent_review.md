# Independent review — A+ temporally matched observable control

**Repository** `kuo1234/xlstm_anomaly`
**Branch reviewed** `experiment/temporally-matched-observable-control` @ `04e0abbd7a9a6a8c8d00052cd1b20c51e0a71d28`
**Baseline** `main` @ `2810c346d40ceb3e011625f6fbf63db8833d9572`
**Protocol/implementation seal** `de76db713f72d1b34fc71ca67c6b40ed5b631799`
**Date** 2026-09-21

## Verdict

**PASS WITH REQUIRED FIXES**

The experiment is well constructed and the part that was hardest to get right — exact
temporal matching between `internal234` and `O1r` — is correct and independently
verified here at operator level. No defect I found changes the sign, the ordering,
or the qualitative conclusion. Two *published numbers* are nevertheless wrong or
ambiguous for the design, one *unrecorded engineering state* (solver convergence)
leaves a directionally adverse alternative explanation unexcluded, and one *claim-ladder
promotion* is written more broadly than the evidence. All four are fixable; three of
them without any refit.

## Scope and method of this review

Read-only. I did not modify the repository, rerun any experiment, or create any
result. The user's working clone was left at `main@2810c34` with a clean tree; all
git inspection was done in a separate throwaway clone. Verification used two routes
only:

1. **Arithmetic re-derivation from committed artifacts** — `results.json` and the six
   `results/results_{arch}_{seed}.json` files. Every number quoted in `results.md`
   that I checked reproduces exactly, including the full scenario-stratum table, the
   22/30 and 1/30 margin counts, the source-mean ranges, and the bootstrap intervals.
2. **Re-execution of the pure-NumPy feature operators on synthetic arrays** in a
   scratch copy of `scripts/`, to test receptive field and causality directly rather
   than by reading the code. No model, checkpoint, cache, or label was touched.

## 0. Seal integrity — clean

| check | result |
|---|---|
| `scripts/temporally_matched_observable_control.py` at seal vs HEAD | identical (`6bc2dd7…`) |
| `configs/temporally_matched_observable_control.json` at seal vs HEAD | identical (`bcf7077…`) |
| `tests/test_temporally_matched_observable_control.py` at seal vs HEAD | identical (`57c851d…`) |
| `research/.../protocol.md` at seal vs HEAD | identical (`df4e025…`) |
| first results file introduced | `50973fc`, i.e. **after** the seal |
| post-seal commits | `50973fc` (results/reports only), `04e0abb` (3 trailing-whitespace deletions) |
| `reports/phase_g1` changed vs `main` | no |
| `research/strong_observable_control` (reference source) changed | no |
| `scripts/strong_observable_control.py`, `m0/` changed | no |

**No result-dependent methodological change occurred after the seal.** The only code
touched anywhere on the branch is the three new A+ files.

One note on the seal commit itself: `de76db7` replaced the per-column loop in
`expand_o1r` with a reshape/transpose. I reimplemented the pre-seal loop and compared:
maximum absolute difference **4.44e-16** over a 200×1664 output. The commit message
says "mathematically identical"; it is identical to float64 round-off, which is
immaterial here, and the equivalence test in `tests/` was written *before* the
optimisation, which is the correct ordering.

## 1. Optimizer convergence — REQUIRED FIX (mandatory audit before the number travels)

**Confirmed.** No run file records `n_iter_`, a per-candidate convergence flag, the
solver tolerance, or which selected model converged. The committed fields are
`selected_C`, `validation_candidates`, `dimension`, row counts, class counts, and
SHA-256 hashes of the scaler and coefficients. Convergence state is **not recoverable**
from what was committed; `results.md` says only that "some" fits warned.

The concern is real and, importantly, **not symmetric between arms**:

| run | H+O1r C\* | H+O1r+I C\* | validation AP path for H+O1r (C = 0.01/0.1/1/10) |
|---|---:|---:|---|
| xlstm_11 | 1.0 | 0.01 | 0.911400 0.914967 **0.916377** 0.915797 |
| xlstm_22 | 1.0 | 0.01 | 0.905719 0.909518 **0.910777** 0.910500 |
| xlstm_33 | **10.0** | 0.01 | 0.907980 0.908310 0.908423 **0.908499** |
| lstm_11 | 1.0 | 1.0 | 0.937815 0.938895 **0.939270** 0.939218 |
| lstm_22 | **10.0** | 0.1 | 0.938475 0.940606 0.941654 **0.941861** |
| lstm_33 | **10.0** | 0.1 | 0.942976 0.945261 0.945530 **0.945689** |

The **baseline** arm systematically selects weak regularization (C = 1 or 10) and the
**internal** arm for xLSTM selects the strongest grid point (C = 0.01) in all three
seeds. In sklearn's parameterisation the penalty is `0.5·wᵀw + C·Σloss`, so C = 10 at
n = 697,430 and d = 1,678 is an essentially unpenalised fit on a heavily collinear
design (the 13 features per base column are overlapping rolling statistics of the same
series). Those are exactly the fits lbfgs is least likely to finish in 1,000 iterations,
and a truncated lbfgs solution behaves like an over-regularised one — i.e. it *lowers*
`AP(H+O1r)` and therefore **inflates** the reported increment. The risk is concentrated
on the side that would manufacture the effect.

Two pieces of committed evidence bound, but do not close, this:

* The whole C grid moves validation AP by at most **0.005058** in any of the twelve
  fits. If truncation acts like extra regularization, its plausible scale is the scale
  of the regularization axis itself — ~5× smaller than the xLSTM increment (0.026710)
  but only ~2× the LSTM increment (0.010220).
* `AP(H+O1r)` is **+0.007555** (xLSTM) / **+0.004165** (LSTM) *above* the lower-dimensional
  `AP(H+O1)`, so the baseline is not grossly broken. For truncation alone to explain the
  full xLSTM increment, a converged `H+O1r` would have to reach ≈0.932 — a gain over
  `H+O1` 4.6× larger than observed, and equal to what `internal234` itself buys.

That makes the convergence explanation improbable for the xLSTM result but **not
excluded**, and for the **matched LSTM** (+0.010220, same order as the 0.005 regularization
axis) it is not even improbable. Since the interpretively load-bearing statement in
`scientific_assessment.md` is the *asymmetry* between the two backbones, the weaker of
the two numbers is the one carrying the claim.

**Decision: a bounded solver/convergence sensitivity audit is mandatory before any
nonlinear probe and before the +0.026710 figure is quoted outside this branch.**

### Related, same root cause (not in the brief)

**(a) C selection sits at a grid boundary in 6 of 12 fits**, and the boundary direction
differs by arm: three `H+O1r` fits select C = 10 (the path is still rising — the arm wants
*less* regularization than the grid allows) and all three xLSTM `H+O1r+I` fits select
C = 0.01 with a monotonically *decreasing* path (the arm wants *more*). Both are
constrained optima, so both APs are lower bounds within the model family, and the two
biases push the increment in opposite directions. The audit should extend the grid one
step in each direction; this is cheap and removes an ambiguity that currently has no
determinate sign.

**(b) A nested-superset regression that is not disclosed anywhere in the branch.**
`O1r` column `13k` is exactly `O1` column `k` (confirmed: the sealed test asserts it and
I reproduced it), so `H+O1r ⊃ H+O1` and `H+O1r+I ⊃ H+O1+I` as *exact* column-set
inclusions. The observable baseline behaves as expected, but the internal arm does not:

| contrast | xLSTM | matched LSTM |
|---|---:|---:|
| `AP(H+O1r) − AP(H+O1)` (richer arm, expect ≥ 0) | **+0.007555** | +0.004165 |
| `AP(H+O1r+I) − AP(H+O1+I)` (richer arm, expect ≥ 0) | **−0.005246** | −0.000760 |

The xLSTM `H+O1r+I` arm *lost* 0.005246 AP relative to its own strict subset — a loss
larger than that arm's entire C-grid spread (0.001031–0.002729). Model selection on
validation can legitimately lose on test, but at this magnitude it is better read as
the 1,912-dimensional fit not reaching the quality the 376-dimensional fit reached.

This matters for how the headline shrinkage is narrated. The internal increment fell
from `I|H+O1 = +0.039584` to `I|H+O1r = +0.026783`, a shrink of 0.012801. That decomposes
**exactly** as +0.007555 (control genuinely improved — the intended A+ effect) and
+0.005246 (internal arm degraded — a fitting artifact). **41% of the apparent
"temporal span explains part of it" result is the internal arm getting worse, not the
control getting better.** This artifact is *conservative* with respect to the A+
conclusion, but it belongs in `results.md`, and it is the same diagnostic the
convergence audit should resolve.

## 2. Crossed source × seed uncertainty — REQUIRED FIX (result-level, no refit needed)

**Confirmed, and the reference numbers in the brief are correct.** `_bootstrap()` draws
`source_indices` of shape `(draws, 10)` and then `seed_indices` of shape
`(draws, 10, 3)` — an independent seed resample *inside every sampled source slot*.
That is the correct scheme for a design in which each source receives its own
independently drawn detector seeds. The actual design is **crossed**: the same three
seeds (11, 22, 33) are used for all ten test sources, so a seed's deviation is perfectly
shared across sources. Resampling it independently ten times destroys that correlation
and divides the seed variance component by ≈30 instead of ≈3.

I reimplemented the committed scheme (reproduces the published interval to all printed
digits) and a two-way crossed cluster bootstrap (resample source rows and seed columns
once each per replicate, take the intersection cells), same 10,000 draws, same seed 901:

| backbone | scheme | 95% interval | width | sd of replicate mean |
|---|---|---|---:|---:|
| xLSTM | committed (nested, published) | [+0.022959, +0.030312] | 0.007353 | 0.001881 |
| xLSTM | **crossed source × seed** | **[+0.019509, +0.032582]** | 0.013072 | 0.003437 |
| xLSTM | sources only, seeds fixed | [+0.024257, +0.029361] | 0.005104 | 0.001301 |
| LSTM | committed (nested, published) | [+0.007861, +0.012566] | 0.004706 | 0.001185 |
| LSTM | **crossed source × seed** | **[+0.007805, +0.012817]** | 0.005012 | 0.001255 |
| LSTM | sources only, seeds fixed | [+0.008480, +0.011864] | 0.003384 | 0.000863 |

This independently confirms the brief's reference figures ([0.0195, 0.0325] and
[0.0078, 0.0129]). The mechanism checks out analytically. Variance components of the
10 × 3 matrices:

| backbone | source main-effect sd | seed main-effect sd | interaction rms |
|---|---:|---:|---:|
| xLSTM | 0.004095 | **0.005207** | 0.005435 |
| LSTM | 0.002694 | 0.000833 | 0.004314 |

Crossed sd should be `√(σ²_src/10 + σ²_seed/3 + σ²_int/30)` = 0.003420 (observed 0.003437);
nested sd should be `√(σ²_src/10 + (σ²_seed + σ²_int)/30)` = 0.001888 (observed 0.001881).
The xLSTM interval is understated by a factor of **1.78** purely because its seed main
effect is large (seed 22 at +0.019571 against +0.028952 and +0.031825); the LSTM interval
is barely affected (1.07×) because its seed main effect is small.

**Should the bootstrap be revised? Yes — required.** The correction consumes only the
committed 10 × 3 `source_seed_matrix`; it needs no refit, no cache access, and no new
experiment, so it should be done before merge. Two caveats to carry with it:

* With **three** levels of the seed factor, no resampling scheme gives a calibrated 95%
  interval — the 2.5% tail is driven by replicates that draw the same seed three times.
  The crossed interval is *less wrong*, not correct. Report it alongside the
  conditional-on-seeds interval and say plainly that the seed factor has n = 3.
* The published xLSTM interval currently lies entirely above the +0.02 reference margin
  that the same documents use as their yardstick; the crossed interval does not
  (+0.019509). No *stated* claim depends on this — `scientific_assessment.md` claims only
  "an exploratory interval above zero", which survives both schemes — but
  `CURRENT_STATUS.md` places the interval next to "2/3 seed means at the old +0.02
  reference", which invites exactly the reading that fails.

### Estimand consistency — confirmed inconsistent, but immaterial in magnitude

`results.md` puts pooled test-set AP differences in the `seed 11 / 22 / 33` columns and
the mean of the **source-level** AP differences in the `mean` column, so the row's mean
is not the mean of its own entries. Same mixing in the decision rule: the `mean ≥ 0.02`
clause reads `matrix.mean()` (source-level) while the `2/3 seeds ≥ 0.02` clause reads
`primary.delta` (pooled).

Measured gap between the two estimands, per run: **at most 0.000373** (xLSTM
−0.000014 / +0.000059 / +0.000172; LSTM +0.000244 / +0.000373 / −0.000239). Grand means
differ by 0.000072 (xLSTM) and 0.000126 (LSTM). The descriptive classification is
unchanged either way (2/3 xLSTM seeds ≥ 0.02 under both definitions; 0/3 LSTM).

**Not result-affecting — a reporting-clarity defect.** Fix by declaring one estimand
(the source-level mean is the natural one, since it is what the bootstrap and the
per-source reporting use) and labelling the columns accordingly. Note that seed 22's
pooled value, +0.019571, sits just under the margin under both definitions, so the
"2 of 3" clause passes with no spare seed.

## 3. Temporal matching — VERIFIED, no defect

I did not accept the nominal window length. I re-executed the operators on synthetic
arrays and measured the support directly by single-row perturbation.

| property | `internal234` | `O1r` | H14 |
|---|---|---|---|
| decision rows affected by perturbing decision row 100 | [100, 131] | [100, 131] | [100, 131] |
| forward span | 31 decisions | 31 decisions | 31 decisions |
| backward (future→past) leakage | none | none | none |
| first fully finite decision index → raw timestamp | 31 → **t = 94** | 31 → **t = 94** | 31 → **t = 94** |
| dimension | 18 × 13 = 234 | 128 × 13 = 1664 | 14 |

* **Raw receptive field.** The base row at decision `t` comes from a single independent
  `[t−63, t]` window: `dense_windows` builds disjointly-indexed 64-step slices and
  `model(batch)` is called per window with no state carried between windows, so
  `internal_base18` and `o1` both depend only on raw `[t−63, t]`. Adding the 31-decision
  causal expansion gives a raw union of `[t−94, t]` — 95 raw steps — **for both arms,
  exactly**. The protocol's claim is accurate.
* **Operator identity.** `expand_o1r` per-column blocks are bit-comparable to
  `expand_internal` applied to the same columns (max abs difference 4.44e-16 over 18
  shared columns), so it is literally the same operator, not a look-alike.
* **Target-time alignment.** `build_evaluator_rows` sets `label_t = any(labels[t−63 : t+1])`
  and the stratum from the same closed window — strictly causal, right-edge, no
  lookahead. Features may reach back to `t−94` while the target depends only on
  `[t−63, t]`; that is symmetric across arms and therefore contrast-neutral.
* **Transformation before filtering.** `_make_records` computes `history14`,
  `expand_internal`, and `expand_o1r` on the full contiguous stream and applies the
  finite ∧ primary-cohort mask afterwards, after asserting the timestamp vector is
  exactly `arange(63, 63+N)`. Filtering cannot compress the time axis.
* **Row/sample identity.** The ordered row-key SHA-256 is identical between `H+O1r` and
  `H+O1r+I` in every fold of every run, identical across all six runs, and equal to the
  hashes recomputed from the stacked matrices; row counts (697,430 / 348,715 / 697,430)
  match the historical reference exactly, and test class counts are [248,590; 448,840]
  (prevalence 0.6436) throughout.

This part of A+ is the strongest part and I found nothing to correct.

## 4. Probe interpretation — one required fix, rest is well calibrated

The core sentence in `scientific_assessment.md` is correctly bounded: it says "under a
fixed L2 probe", "linearly accessible", "an O1 residual control", and it explicitly
disclaims causality, information-theoretic insufficiency, and generic superiority.
`red_team.md` adds the right limit ("cannot support the stronger statement that all
detector observables are insufficient"). I would not change any of that.

Three problems, in descending severity:

**(a) REQUIRED — the claim-ladder promotion is broader than the evidence, and the thing
that bounded it was deleted in the same commit.** `CURRENT_STATUS.md` promotes
**L1c — "the increment survives a temporally matched observable control"** from NOT TESTED
to PARTIALLY SUPPORTED. A+ tested a temporally matched **residual-derived** control. The
pre-A+ plan named a *secondary* control `P1r` — the same statistic family and temporal
expansion computed from the **scaled input windows** — and the same diff that promotes
L1c also deletes the paragraph that specified `P1r`, leaving no trace of it in the
forward plan. The limitation is stated in `scientific_assessment.md` ("O1r is a
residual-derived observable control, not the raw scaled input trajectory") and in
`red_team.md`, so this is a bookkeeping failure rather than concealment — but a future
reader gets a generically-worded rung and no record that half the predeclared control
was never run. Restate the rung as "…survives a temporally matched **residual**
observable control (O1r); input-trajectory control P1r not run", and put P1r back in
the forward plan.

**(b) The label `INTERNAL234_GT_O1R` reads as a general ordering between two feature
sets.** It is defined by a frozen criterion in the protocol, so it is bounded *in situ*,
but the string travels better than its definition. Consider
`INTERNAL234_GT_O1R_UNDER_L2_PROBE_AT_0P02` or equivalent.

**(c) The backbone asymmetry is the one comparison A+ leans on interpretively and the
one it never quantifies.** "The narrow L1c reading is asymmetric: xLSTM survives the
descriptive reference while matched LSTM does not" is inferred by thresholding two point
estimates separately against +0.02 — no interval on the difference, and no adjustment
for the fact that the two backbones start from different AP levels. From the committed
matrices, paired by test source and seed label:

* paired difference (xLSTM − LSTM) mean **+0.016490**, 28/30 cells positive, crossed
  95% interval **[+0.008697, +0.023725]**;
* but the LSTM's `H+O1r` baseline is **0.029950** higher (0.935638 vs 0.905688), so there
  is less headroom for an increment. As a fraction of remaining headroom `1 − AP` the
  increments are **28.4%** (xLSTM) and **16.1%** (LSTM) — the ratio falls from **2.59×** to
  **1.77×**.

This is the same ceiling confound already on record for the strong-observable study.
The asymmetry survives it directionally, but the assessment should quantify it rather
than derive it from two independent threshold crossings, and should note the baseline
gap. Per the review brief I am not assessing generic xLSTM superiority; I am flagging
that the asymmetry statement currently rests on a comparison A+ never performed.

## Required output

**Verdict: PASS WITH REQUIRED FIXES.**

**Strongest conclusion currently supported.**
> Under a fixed L2 logistic probe on frozen W64/stride-1 right-edge rows, with the
> residual observable control given the identical causal `[t−94, t]` decision span and
> the identical ordered rows, a positive `internal234` increment remains for the xLSTM
> backbone: **+0.026710** mean AP (source-level), positive in **30/30** source × seed
> units, with a design-appropriate exploratory interval of **[+0.019509, +0.032582]** that
> excludes zero but not the +0.02 practical reference. Matched temporal span therefore
> accounts for part of the previously reported `I|H+O1 = +0.039584` but not all of it.
> The matched LSTM retains a smaller increment (**+0.010220**, crossed interval
> [+0.007805, +0.012817]) that is below the practical reference in every seed. This is a
> statement about linear accessibility under one probe, one control family, one
> synthetic generator, and three seeds; it is not causal, not information-theoretic, not
> evidence that residual observables lack the information, and not an xLSTM-specificity
> or generic-superiority result. It is **conditional on an unperformed solver-convergence
> audit** (below).

**Result-affecting defect: none that changes sign, ordering, or qualitative conclusion.**
The published xLSTM 95% interval is misspecified for the design and must be restated
(1.78× too narrow; lower bound moves from +0.022959 to +0.019509, crossing the +0.02
reference). The convergence gap is an *unexcluded* alternative explanation rather than a
demonstrated defect — but it is directionally adverse and it is unrecoverable from what
was committed, so the number cannot be treated as settled.

**Should the bootstrap be revised? Yes — required, and before merge.** Replace the
nested source-then-seed resample with a two-way crossed resample over sources and seeds,
report the conditional-on-seeds interval alongside it, and state that the seed factor
has three levels so neither interval is calibrated. This is pure re-aggregation of the
committed 10 × 3 matrices — no refit, no cache access, no new result.

**Is convergence sensitivity mandatory? Yes.** It is the only unexcluded mechanism that
could manufacture the primary effect, it is concentrated on the arm that would inflate
it, and the branch preserved no evidence either way.

**May A+ be merged into main before the sensitivity check? Yes, conditionally** — as an
exploratory record, provided the following land first:

1. bootstrap re-aggregated as crossed (documents and `results.json` restated);
2. a single estimand declared and the `results.md` table relabelled;
3. `results.md` / `red_team.md` record the convergence limitation concretely (which arms
   warned, if it can be recovered from run logs; otherwise state that it was not
   captured) **and** the `AP(H+O1r+I) < AP(H+O1+I)` nested-superset regression;
4. `CURRENT_STATUS.md` L1c narrowed to the residual-derived control, `P1r` restored to
   the forward plan, and the rung annotated "pending solver-convergence audit".

The +0.026710 figure should not be cited outside the repository, and no downstream
experiment should be predicated on it, until the audit completes.

**Single next experiment: (a) bounded solver/convergence sensitivity audit of the
existing linear O1r comparison.**

Not the nonlinear control. A nonlinear probe layered on a linear comparison whose
optimisation state is unknown inherits the defect at higher cost and would confound a
new capacity axis with an unresolved fitting axis. The audit is narrow, needs no model
inference (same read-only cache, same rows, same arms), and settles four open items at
once: the truncation risk on the high-C baseline arms, the 6/12 grid-boundary
selections, the nested-superset regression, and whether the LSTM's +0.010220 — currently
only ~2× the 0.005058 regularization-axis spread — is separable from fitting noise at
all. Suggested bounded form: refit the twelve existing arms recording `n_iter_`,
convergence flag and final gradient norm; raise `max_iter` to a level where every fit
converges (or report the ones that still do not); extend the C grid one step in each
direction to 0.001 and 100; declare in advance that the audit reports the recomputed
increments and replaces the A+ numbers whatever they show. If the increments survive
within, say, ±0.005, the nonlinear control becomes the right next step and can be
specified against a solid baseline.
