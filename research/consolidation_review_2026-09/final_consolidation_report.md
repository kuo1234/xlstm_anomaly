# Final consolidation report — `consolidation/observable-control-line`

Date 2026-09-23. Docs-only consolidation; no experiment, fit, inference or cache access.

**Verdict: PASS.** Every gate below passed. Merging into `main` is authorised.

## Exact HEAD

| item | commit |
|---|---|
| validated consolidation HEAD | `2d7740bd906715e76edf21571e8d87a826313f88` |
| this report commit | adds only this file and `consolidation_validation.json` (the machine-readable record of the validation of `2d7740b`) |
| `main` before consolidation | `2810c346d40ceb3e011625f6fbf63db8833d9572` |

First-parent history on top of `0b00d6f`:

| commit | parents | change |
|---|---|---|
| `aa0860c` | `0b00d6f` | consolidation review, reviewer re-aggregation, addenda, `CURRENT_STATUS.md` |
| `a9e6137` | `aa0860c`, `f1967b6` | merge of the independent A+ review (conflict-free, tree `8410a37`) |
| `d19efb3` | `a9e6137` | P1r / observable wording unified (§8 wording rule) |
| `b410cd8` | `d19efb3` | read-only `consolidation_validation.py` |
| `2d7740b` | `b410cd8` | validation: last-ulp float tolerance, git-ignored checkpoints separated |

## Ancestor map

All of the following are ancestors of `2d7740b` (`git merge-base --is-ancestor`):

| commit | role | ancestor |
|---|---|---|
| `2810c346` | `main` before consolidation | yes |
| `04e0abbd` | A+ temporally matched observable control | yes |
| `de76db7` | A+ pre-result seal | yes |
| `f1967b6a` | independent A+ review | yes (merged by `a9e6137`) |
| `ccb9a3d7` | A+S convergence and C-grid audit | yes |
| `61e57ef7` | nonlinear pre-result seal | yes |
| `0b00d6f9` | bounded nonlinear observable-control audit | yes |
| `aa0860cb` | consolidation review (docs) | yes |

The three independent-review files are present at HEAD and are byte-identical (same git blob) to
`f1967b6`:

- `research/temporally_matched_observable_control/independent_review.md`
- `research/temporally_matched_observable_control/independent_review_numbers.csv`
- `research/temporally_matched_observable_control/independent_review_recompute.py`

## Changed documents (relative to `0b00d6f`)

Only these files differ, and all are in the allowed docs list:

- `research/CURRENT_STATUS.md` (modified)
- `research/consolidation_review_2026-09/consolidation_review.md`
- `research/consolidation_review_2026-09/reviewer_recompute.py`
- `research/consolidation_review_2026-09/reviewer_numbers.csv`
- `research/consolidation_review_2026-09/consolidation_validation.py`
- `research/consolidation_review_2026-09/consolidation_validation.json` (this commit)
- `research/consolidation_review_2026-09/final_consolidation_report.md` (this commit)
- `research/nonlinear_observable_control/post_review_addendum.md`
- `research/temporally_matched_observable_control/post_review_addendum.md`
- the three independent-review files from `f1967b6`

## Unchanged experimental artifacts

**Git object identity.** The object at HEAD equals the object at the source commit for every
path below: tree ids for directories, blob ids for files.

| path | source | object |
|---|---|---|
| `reports/` (all M0 / phase / G1 artifacts) | `2810c34` | `69c1c6805006` |
| `m0/` | `2810c34` | `a76226c37ef7` |
| `data/` (tracked checkpoints) | `2810c34` | `721392fa686e` |
| `configs/` | `0b00d6f` | `4673061fe04f` |
| `scripts/` | `0b00d6f` | `98e392de3a06` |
| `tests/` | `0b00d6f` | `c47534b85986` |
| `research/strong_observable_control/` | `2810c34` | `641761e3ea0f` |
| `research/framing-refresh-2026-09/` | `2810c34` | `dc8fba82ee04` |
| A+ `protocol.md` | `04e0abb` | `df4e025cd648` |
| A+ `results.json` | `04e0abb` | `05a3b1f79964` |
| A+ `results/` (six run JSONs) | `04e0abb` | `7dcd6744e5dd` |
| A+ `results.md`, `execution.md`, `red_team.md`, `scientific_assessment.md` | `04e0abb` | identical |
| `research/aplus_solver_convergence_audit/` (S0/S1/S2, all JSON) | `ccb9a3d` | `344594be0edf` |
| NL `protocol.md` | `0b00d6f` | `519114af4170` |
| NL `preflight.json` / `preflight.md` | `0b00d6f` | identical |
| NL `runs/` (six run JSONs) | `0b00d6f` | `ab1a3469d538` |
| NL `results.json` | `0b00d6f` | `be23ef1aaea1` |
| NL `source_seed_effects.csv`, `results.md`, `statistical_assessment.md`, `scientific_assessment.md`, `red_team.md` | `0b00d6f` | identical |

**Phase seals.** All 16 `reports/*/SHA256SUMS` files were checked. 1,495 entries verify
byte-exactly. The remaining 10 entries are git-ignored `data/phase_f_v3/runs/*.pt` checkpoints
that live only on the training host. They are not part of the repository and cannot drift here.
There are 0 mismatches.

**Seals in result files.** All six NL run files carry
`protocol_seal = 61e57ef7894c8db7faaeb5efc2fd63fb5f58956e`, as does NL `preflight.json`.

**Row-key contract.** For all six backbone × seed runs, the A+ `row_meta`, NL `row_meta`, and
A+S S1/S2 `row_key_sha256` are identical:

| fold | rows | timestamp range | ordered row-key SHA256 |
|---|---:|---|---|
| train | 697,430 | 5632–21054 | `71191e06ef47a9843ae1cc1e141d01fbbb541238514bce7b9d5e0a0683415fdd` |
| validation | 348,715 | 5632–21054 | `77ab6914c34b16262fe9afc80780a8fec079325ca88083b0bbd52751027f697c` |
| test | 697,430 | 5632–21054 | `fb90782494e416d25563f666a4b79a2a24a1968f90821bb36c57287228b4ac6d` |

**Result numbers re-derived.** Each committed aggregate was regenerated from its committed run
files into a temporary directory with the original repository functions, then compared with
the committed file. No fitting was involved.

| aggregate | function | match |
|---|---|---|
| A+ `results.json` | `temporally_matched_observable_control.aggregate` | exact |
| A+S `s0_results.json` | `aplus_solver_convergence_audit.run_s0` | exact (NumPy 1.26.4); ≤1.7e-16 relative on 2 floats (NumPy 2.5.3) |
| A+S `s1_summary.json`, `s2_summary.json` | `summarize_stage` | exact |
| NL `results.json` | `nonlinear_observable_control.aggregate` | exact (excluding the `sklearn_version` string under 2.5.3) |

Headline numbers are unchanged:

- A+ source-level: +0.02671045 (xLSTM), +0.01022015 (LSTM).
- A+S S0 crossed: [+0.01950949, +0.03258161] (xLSTM), [+0.00780522, +0.01281719] (LSTM).
- NL source-level: +0.01516504 [+0.01248823, +0.01822553] (xLSTM), +0.01125203
  [+0.00895238, +0.01347492] (LSTM).

## Test results

| environment | suite | result |
|---|---|---|
| Python 3.12.14, NumPy 1.26.4, SciPy 1.17.1, scikit-learn 1.9.0 (matches the GB10 generator-validation stack) | `tests/` excluding four torch-dependent modules | **117 passed**, 0 failed |
| same | control-line suites (strong, A+, A+S, NL) and `test_phase_b` | 44 passed |
| Python 3.12.14, NumPy 2.5.3, scikit-learn 1.9.1 | `tests/` excluding four torch-dependent modules | 114 passed, 3 failed |
| same | control-line suites (strong, A+, A+S, NL) | 28 passed |

- Under NumPy 2.5.3, the 3 failures are in `test_phase_b.py`. They come from the pre-existing
  `np.trapz` call in protocol-frozen `m0/metrics.py`, which NumPy 2 removed. The same 3 tests
  fail identically on `main@2810c34` under NumPy 2.5.3. They are unrelated to this
  consolidation and pass under NumPy 1.26.4.
- The four modules `test_mlstm_dense_attribution`, `test_phase_d_v2`, `test_phase_e_schema`
  and `test_phase_e2_schema` import torch at module level. They cannot be collected on this
  CPU-only host, and none of their inputs changed (`scripts/`, `tests/` and `data/` are
  object-identical).

## Reviewer recompute

`research/consolidation_review_2026-09/reviewer_recompute.py` was re-run under both NumPy 1.26.4
and 2.5.3. Each run regenerated `reviewer_numbers.csv` byte-identically. Its internal assertion
reproduces the committed NL crossed intervals to within 1e-12. The A+S S0 crossed and
source-only intervals are reproduced by the S0 re-aggregation above.

## Wording gate

`CURRENT_STATUS.md`, `consolidation_review.md` (outside §8, the wording rule itself) and both
post-review addenda contain no prohibited wording. Specifically, none of them contains:

- a claim that internal state holds information the observations lack;
- any insufficiency claim about observables;
- a claim that P1r closes every observable alternative;
- "beyond observables" without a qualifier.

P1r is described only as "the last bounded input-derived control" and an "input-derived
observable summary". Its admissible conclusion is "additional predictive/decodable utility under
the fixed decoder". The structural statement is retained: `internal234` is a deterministic
function of the causal input window, so information-theoretic superiority over the full
observation is out of scope in principle.

## Merge authorisation

All gates passed: ancestry, review files, object identity, allowed-change set, SHA256SUMS,
re-aggregation, row keys, seals, tests, reviewer recompute, and wording. The consolidation
branch may be merged into `main` with `--no-ff`. After the merge, these branches are redundant:

- `experiment/temporally-matched-observable-control`
- `experiment/aplus-solver-convergence-audit`
- `experiment/nonlinear-observable-control`
- `review/temporally-matched-observable-control`
- `docs/control-line-consolidation-review`
- `consolidation/observable-control-line`

Branch retirement is a separate, explicitly authorised step.
