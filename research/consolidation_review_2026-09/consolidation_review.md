# Consolidation review — post-G1 observable-control line

Independent scientific consolidation review, 2026-09-23. Docs only: no experiment was run, no
model was fitted or retrained, no cache was opened, and no historical result JSON, protocol, or
experimental artifact was modified. Every number below was re-derived from committed files by
`reviewer_recompute.py` (output `reviewer_numbers.csv`) or read directly from them.

| ref | commit |
|---|---|
| `main` | `2810c346d40ceb3e011625f6fbf63db8833d9572` |
| `experiment/temporally-matched-observable-control` (A+) | `04e0abbd7a9a6a8c8d00052cd1b20c51e0a71d28` |
| `review/temporally-matched-observable-control` (A+ review) | `f1967b6a9d3801bf1a3c962def32fc3a08b30732` |
| `experiment/aplus-solver-convergence-audit` (A+S) | `ccb9a3d7e8fc1ced5707b5691de6b09a90f3736f` |
| `experiment/nonlinear-observable-control` (NL) | `0b00d6f97635f991c8f12c2e34be9b1073d7f33d` |
| `research/real-data-feasibility-audit` | `8f6ee870e1c8d0809d4d1352e8fde0fd450b56d5` |

Remote refs were verified against `github.com/kuo1234/xlstm_anomaly` on 2026-09-23 and match
the table exactly.

## Verdict

**PASS WITH REQUIRED FIXES.**

The scientific chain G1 → strong observable control → A+ → A+ review → A+S → NL is coherent,
provenance-clean, and statistically consistent. Nothing found changes a sign, an ordering that the
documents rely on, or a qualitative conclusion. There are two classes of required fix:

1. **Consolidation-blocking (history).** `f1967b6` (the independent A+ review) is **not** an
   ancestor of `0b00d6f`. Its three files are absent from the NL head, although the A+S
   protocol and red-team cite `f1967b6` by hash as review evidence. Fast-forwarding `main` to
   `0b00d6f` and then retiring `review/temporally-matched-observable-control` would leave
   `f1967b6` unreachable. It must be merged explicitly (§6).
2. **Documentation.** The NL-versus-linear comparison mixes estimands. The claim ladder has no
   rung for the nonlinear decoder, and it still calls L1c "backbone-heterogeneous", which the
   NL result no longer supports as a magnitude statement. `CURRENT_STATUS.md` has no forward
   decision or current branch map. The A+ `results.md` still presents the misspecified
   nested interval and does not point to its correction. This branch implements all
   documentation fixes (§7).

## 1. Nonlinear-control audit

### 1a. Protocol fixed before result generation — verified

- Seal commit `61e57ef` (parent `ccb9a3d`) adds `protocol.md`, `scripts/nonlinear_observable_control.py`,
  the test module and the label-blind preflight.
- `git diff 61e57ef 0b00d6f` is empty for the NL script, the NL protocol, the inherited A+
  feature script and `configs/`. The only later edits are the seal-string substitutions in
  `preflight.json`/`preflight.md` (`f5933a5`, `c0292e8`) and three added tests in `0b00d6f`,
  none of which changes code under test.
- The first run file was committed in `456fab5`, 14 min after the seal. All six run JSONs carry
  `protocol_seal = 61e57ef7894c8db7faaeb5efc2fd63fb5f58956e`, a value that cannot exist before
  that commit.
- Limitation: git cannot prove that no exploratory fit ran outside version control. The frozen
  grid has two values, so little post-hoc tuning freedom exists.

### 1b. Identical rows and the same HGB family in both arms — verified

- `_verify_row_contract` compares each fold's row count, row-key SHA256 and timestamp range with
  the committed A+ `row_meta` and raises on mismatch. `_fit_arm` re-checks the per-arm key hash.
- From the committed JSONs, for all six runs: `row_key_sha256` is identical between `H+O1r` and
  `H+O1r+I` and equal to the A+ `row_meta` hashes. Class counts are identical. Rows are
  697,430 / 348,715 / 697,430 and dimensions 1,678 / 1,912.
- All 24 candidate fits share one parameter dictionary that differs only in `max_iter`. There is
  no scaler, no internal validation split and no early stopping.
- `reports/` and `m0/` are byte-identical from `main` to `0b00d6f`. The A+ directory is
  unchanged from `04e0abb` and the A+S directory unchanged from `ccb9a3d`.

### 1c. Test data did not influence `max_iter` selection — verified

- `_fit_candidate` receives only the train and validation folds, and no candidate record
  contains a test metric. In all 12 arm fits, the selected `max_iter` equals the arg-max of
  validation AP (tie → 100). Test is predicted once, in `_fit_selected`, after selection.
- The selection path differs between arms in 2/6 runs (for example xLSTM seed 22 selects
  300 / 100). This does not drive the effect. The validation-fold increment at a *fixed* budget
  is +0.01743310 (100) versus +0.01610632 (300) for xLSTM, and +0.00951683 versus
  +0.00937298 for LSTM.
- HGB semantics: `early_stopping=False` makes `n_iter_ == max_iter` the fixed boosting budget
  by construction. It is **not** a convergence failure, and the LogisticRegression convergence
  reading from A+/A+S does not transfer. The NL documents describe this correctly as budget
  exhaustion.

### 1d. Crossed source×seed uncertainty — implemented consistently

`crossed_bootstrap()` in the NL script is identical to the A+S S0 implementation: rows and
columns are drawn independently once per replicate, with 10,000 draws at seed 901. Recomputing
from `source_seed_effects` reproduces both committed NL intervals to within 1e-12.

The one inconsistency is at the chain level, not in the code. A+S S1/S2 persisted **pooled**
per-seed test AP only, with no source-level APs. The S2 "linear references" +0.02596099 /
+0.01076562 are therefore means of pooled per-seed deltas, and they carry no crossed interval.
The NL documents set them against the NL **source-level** mean. See §2 for the like-for-like
numbers.

### 1e. Predictive utility versus information-theoretic sufficiency — correctly distinguished

The NL protocol, results, assessment and red-team consistently call the result bounded
predictive utility under one fixed decoder, and they disclaim sufficiency or insufficiency of
the observables. That is correct. It is also the only reading available *in principle*, as §3
explains.

## 2. What the ~42 % xLSTM attenuation does and does not support

### Like-for-like numbers

| quantity | xLSTM | matched LSTM |
|---|---:|---:|
| S2 linear, mean pooled Δ (the documented reference) | +0.02596099 | +0.01076562 |
| NL, mean pooled Δ (same estimand) | +0.01505744 | +0.01136827 |
| change, pooled like-for-like | **−0.01090355 (−42.0 %)** | +0.00060264 |
| change as documented (NL source-level − S2 pooled) | −0.01079596 (−41.6 %) | +0.00048641 |
| NL source-level − A+ linear source-level, same 30 cells | −0.01154542 | +0.00103188 |
| crossed 95 % interval of that paired change | [−0.01808989, −0.00439573] | [−0.00223226, +0.00382090] |
| cells attenuated | 27/30 | 11/30 |

The estimand mix changes the documented figure by only about 0.0001 AP. It is immaterial to the
conclusion, but it should be stated. The attenuation is specific to xLSTM, and its paired
interval excludes zero. For the matched LSTM the change is null.

### Where the attenuation comes from (pooled test AP, mean of three seeds)

| arm | xLSTM S2 linear | xLSTM HGB | gain | LSTM S2 linear | LSTM HGB | gain |
|---|---:|---:|---:|---:|---:|---:|
| `H+O1r` | 0.90779605 | 0.93697843 | **+0.02918238** | 0.93584318 | 0.94582957 | +0.00998640 |
| `H+O1r+I` | 0.93375704 | 0.95203587 | +0.01827883 | 0.94660880 | 0.95719784 | +0.01058904 |

For xLSTM, the nonlinear decoder raises the *observable-only* arm by more than the entire linear
internal increment. The attenuation equals the observable-arm gain minus the full-arm gain. For
the LSTM, the decoder raises both arms by about the same amount.

### Supported

1. About 0.011 AP of the linear xLSTM increment was information that O1r already contains but a
   linear probe cannot extract. The linear xLSTM `H+O1r` baseline was under-extracted
   (0.9078, against 0.9358 for the LSTM). The HGB baseline closes most of that gap.
2. The seed heterogeneity of the linear xLSTM increment depended on the probe. The per-seed
   pooled increments were +0.02812832 / +0.01629509 / +0.03345957 under linear S2, and they
   become +0.01520113 / +0.01476300 / +0.01520820 under HGB. The seed main-effect standard
   deviation of the source-level matrix falls from 0.00637722 (A+ linear) to 0.00054398.
3. The attenuation is concentrated in the strata that need cross-window context. For xLSTM,
   recurring moves +0.025478 → +0.010652 and gradual +0.022980 → +0.016571, while abrupt and
   correlation are unchanged. This is descriptive only.
4. A positive increment survives this decoder for both backbones in 30/30 source×seed cells:
   xLSTM +0.01516504 [+0.01248823, +0.01822553], LSTM +0.01125203 [+0.00895238, +0.01347492].
   The A+ increment is therefore not *solely* an artifact of linear accessibility.

### Not supported

1. **xLSTM superiority or a backbone-specific mechanism.** The xLSTM − LSTM increment gap
   shrinks from +0.01649030 (A+ linear) to +0.00391301 under HGB (reviewer crossed interval
   [+0.00036699, +0.00743939]). O1r is derived from each backbone's own residuals, so the
   baselines differ: the xLSTM HGB `H+O1r` baseline is 0.00885 AP lower. As a fraction of
   remaining headroom `1 − AP(H+O1r)`, the increments are 0.2391 (xLSTM) and 0.2100 (LSTM),
   a ratio of 1.14×, down from 1.66× under linear S2. Absolute ceilings favour the LSTM in
   every seed (HGB `H+O1r+I` 0.95204 versus 0.95720). The residual gap is what a weaker
   observable baseline would produce, and it is not evidence of a better representation.
2. **That the remaining +0.015 / +0.011 is irreducible.** It is specific to one decoder family
   at one budget. On validation, the xLSTM increment falls from budget 100 to budget 300 in
   3/3 seeds. This is descriptive and gives no basis for further decoders, but it means the
   attenuation is not shown to have saturated.
3. **Observable insufficiency** in any information-theoretic sense (§3).
4. **A practically large effect by the project's own reference.** 0/3 seed means reach the
   historical +0.02 descriptive reference for either backbone under HGB. The cell counts are
   4/30 (xLSTM) and 0/30 (LSTM).
5. **That the attenuated share was "spurious internal signal".** It is signal that O1r also
   carries.

## 3. Claim-ladder audit

**Structural boundary.** `internal234` at decision `t` is a deterministic function of the raw
window `x[t−94, t]` and frozen weights. O1r is a function of the same window and of that
detector's predictions. Hence `I(Y; internal234 | x[t−94,t]) = 0` exactly, by the
data-processing inequality. No experiment on this benchmark can show that internal state holds
information the observations lack. Every rung below is a statement that a frozen learned
representation is **more decodable** than a specified observable summary under a specified
bounded decoder. That is representation utility, not observability.

| rung | claim (recommended wording) | status |
|---|---|---|
| L1a | internal state adds predictive utility over score/history | **SUPPORTED** — confirmatory (G1 H2 GO, +0.142519); unchanged |
| L1b | the increment survives rich *within-window* residual controls (O1, O2; not temporally matched) | **PARTIALLY SUPPORTED**, exploratory; min over controls +0.03958 / +0.01527; span-confounded, superseded interpretively by L1c |
| L1c | the increment survives a temporally matched **residual-derived** control (O1r) under a fixed L2 logistic probe | **PARTIALLY SUPPORTED**, exploratory (A+/A+S): +0.026710 / +0.010220 source-level, 30/30 cells each; converged; grid-stable. The backbone asymmetry here is largely a linear-probe effect (see L1c-NL) |
| L1c-NL | the same O1r increment survives a fixed bounded nonlinear decoder (HGB) | **PARTIALLY SUPPORTED**, exploratory: +0.015165 / +0.011252, 30/30 cells each, both below the +0.02 reference; xLSTM attenuated about 42 %, LSTM unchanged |
| L1c-P | the increment survives a temporally matched **input-derived** control (P1r) | **NOT TESTED** |
| — | observables are information-insufficient | **OUT OF SCOPE IN PRINCIPLE** — never to be claimed |
| L1d / L5 | the measurement describes real systems | **NOT TESTED** |

The current `CURRENT_STATUS.md` L1c wording is defensible for A+/A+S but incomplete. It lacks
the NL rung. Its annotation "backbone-heterogeneous" is true only under the linear probe. It
does not show that P1r was not run in the rung itself. This branch corrects all three.

## 4. Remaining control gap: P1r versus real data

**Is P1r still necessary before publication?** Two cases:

- It is not needed for the narrowest claim ("beyond score/history and temporally matched
  *residual-derived* summaries").
- It is required for any wording that says "observable" without qualification. It is also the
  most predictable reviewer objection. The task is drift versus anomaly, and drift is defined
  as a change in the input distribution, yet no arm of the ladder contains the input
  trajectory.

P1r is also the only control that is **identical across backbones**. Every comparison so far has
been confounded by backbone-specific residual baselines, and P1r is the first common baseline.
It was predeclared as the conditional secondary arm before A+. Its cost is a deterministic
generator regeneration pass, with no detector inference and no training.

**Should real-data validation come before P1r? No.** The feasibility audit at `8f6ee87` is
careful and useful, but it establishes the following:

- **No acquired public multivariate dataset reproduces the drift-versus-anomaly estimand**
  (its recommended suite, part C, is N/A). Real data can test anomaly-versus-normal
  measurement (L1d, partial). It cannot test L1c, L1c-NL or the P1r question.
- Acquisition is incomplete: the NASA arrays return HTTP 403, the SMD 1-8 bytes are absent,
  HAI needs Git LFS, and SWaT/WADI/Yahoo need manual grants.
- Any real-data stage needs new detector training under a new sealed M0-compliant protocol. That
  is a larger and riskier investment than P1r.
- That protocol should carry the final control ladder, and it cannot be specified until P1r
  settles whether an input-derived control is part of that ladder.

The branch is ready as a data-provenance record, not as an experiment. Its acquired bytes are
git-ignored and local to a separate worktree. It touches only its own paths and merges cleanly
with `0b00d6f`. Keep it separate.

## 5. Single next scientific action

**P1r — one sealed, bounded experiment, then stop and write.**

Constraints for its protocol (to be reviewed and sealed before any fit):

- **Arms:** `H+P1r` versus `H+P1r+internal234`. P1r applies the O1 statistic family and the
  identical causal `[t−94, t]` rolling expansion to the detector's scaled input windows.
  Use the same rows, folds, seeds, backbones and row-key contract as A+.
- **Decoder:** the frozen HGB family from the NL audit, unchanged, as primary. This is the
  stronger decoder, and the linear probe is now known to overstate increments against lossy
  observable summaries. No new decoder.
- **Reproducibility preflight (label-blind):** the regenerated streams and the input scaler must
  reproduce the cached row keys and timestamps. Fail closed otherwise.
- **Estimand:** the source-level 10×3 mean with crossed and source-only bootstrap, as in NL.
  Pooled deltas are descriptive.
- **Pre-declared outcome → wording map**, and an explicit commitment that P1r is the **last**
  observable control before writing, whatever it shows. No further decoders, budgets or
  controls. This stops the ladder from regressing indefinitely.

Not recommended now: real-data validation (§4), W128+, mLSTM replication, adaptation, or any
further decoder sweep.

## 6. Branch consolidation review

**Ancestry (verified with `git merge-base --is-ancestor`):**

- `2810c34 ⊂ 04e0abb ⊂ ccb9a3d ⊂ 0b00d6f`. This is a linear chain of 21 commits, so
  `0b00d6f` contains the complete A+ and A+S ancestry, and `main` can be fast-forwarded to it.
- `f1967b6` = `04e0abb` + one commit that adds `independent_review.md`,
  `independent_review_numbers.csv` and `independent_review_recompute.py`. It is **not** an
  ancestor of `ccb9a3d` or `0b00d6f`.
- `git merge-tree --write-tree 0b00d6f f1967b6` is conflict-free (tree
  `e7a13a1ee9670da2dc659158606d292db4909b1c`).
- `8f6ee87` branches from `2810c34`, touches only `research/real_data_feasibility/` and
  `scripts/*real_data*`, and merges cleanly with `0b00d6f`. It is not part of this
  consolidation.

**Is `0b00d6f` safe to consolidate into `main`?** Yes, as an exploratory record, provided that
`f1967b6` is merged in the same consolidation. The proposed cleanup is safe only in that order.

Safe sequence (for the maintainer; not executed by this review):

```bash
git fetch origin
git switch main && git merge --ff-only origin/main                  # 2810c34
git merge --no-ff docs/control-line-consolidation-review \
  -m "Consolidate completed post-G1 observable-control line (A+, A+S, nonlinear) into main"
git merge --no-ff f1967b6 \
  -m "Preserve independent A+ review (f1967b6) in main history"
for c in 04e0abb f1967b6 ccb9a3d 0b00d6f docs/control-line-consolidation-review; do
  git merge-base --is-ancestor "$c" main && echo "ok $c" || echo "MISSING $c"
done
git diff --quiet 0b00d6f main -- reports/ m0/ scripts/ configs/ \
  research/temporally_matched_observable_control/results research/temporally_matched_observable_control/results.json \
  research/aplus_solver_convergence_audit research/nonlinear_observable_control/runs \
  research/nonlinear_observable_control/results.json research/nonlinear_observable_control/protocol.md \
  && echo "experimental artifacts unchanged"
git push origin main
```

`docs/control-line-consolidation-review` is based on `0b00d6f`, so merging it brings in the
whole control line. **Only after every ancestry check prints `ok`** do these branches become
redundant and safe to retire, locally and on `origin`:

- `experiment/temporally-matched-observable-control` (`04e0abb`)
- `experiment/aplus-solver-convergence-audit` (`ccb9a3d`)
- `experiment/nonlinear-observable-control` (`0b00d6f`)
- `review/temporally-matched-observable-control` (`f1967b6`)
- `docs/control-line-consolidation-review` (this branch)

Retain `research/framing-2026-09` and `research/real-data-feasibility-audit`. Local
housekeeping, all optional:

- `origin/research/framing-refresh-2026-09` and `https/*` are stale remote-tracking refs, with
  no branch on GitHub and no configured `https` remote.
- The real-data worktree is listed as `prunable`. Verify on the host that its directory is
  really gone before running `git worktree prune`, because it holds git-ignored acquired data.

## 7. Fixes implemented on this branch (docs only)

1. `research/consolidation_review_2026-09/` — this review, `reviewer_recompute.py`, and
   `reviewer_numbers.csv`.
2. `research/nonlinear_observable_control/post_review_addendum.md` — the like-for-like estimand
   statement, the decoder-gain decomposition and the backbone gap. The historical `results.md`
   is unchanged.
3. `research/temporally_matched_observable_control/post_review_addendum.md` — points to the
   crossed interval, the review commit `f1967b6`, A+S and the NL effect on the asymmetry
   reading. The historical `results.md` is unchanged.
4. `research/CURRENT_STATUS.md` — NL paragraph estimand, claim ladder (L1c narrowed, L1c-NL and
   L1c-P added, information-theoretic rung excluded), next action, branch map.

Remaining fix, which cannot be made on a docs branch based on `0b00d6f`: merge `f1967b6` during
consolidation (§6).
