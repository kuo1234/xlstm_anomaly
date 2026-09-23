# P1r consolidation report

**Verdict: PASS.** The P1r line may be merged into `main` (`--no-ff`, chronology preserved).

| item | commit |
|---|---|
| pre-P1r `main` | `855c34d29920cc9aa85fa26d438784d150ac0d79` |
| validated P1r HEAD | `e7ab753bc61b0e4a43ece7c2fee92d4f0155e036` |
| this report commit | adds only this file and `p1r_consolidation_validation.json` (the record of the `e7ab753` validation) |

## Chronology (first parent, in order)

| step | commit | subject |
|---|---|---|
| seal | `90b2470` | Seal input-derived observable control (P1r) protocol |
| preflight | `4c22e52` | Record label-blind P1r preflight (stage 1 and stage 2 PASS on cache host) |
| run | `4745f32` | Record P1r xLSTM seed-11 run |
| run | `08f34f9` | Record P1r xLSTM seed-22 run |
| run | `a683ab4` | Record P1r xLSTM seed-33 run |
| run | `e383dcb` | Record P1r LSTM seed-11 run |
| run | `b5533cb` | Record P1r LSTM seed-22 run |
| run | `32ee597` | Record P1r LSTM seed-33 run |
| aggregate | `af6cc47` | Aggregate P1r input-derived observable control |
| assessment | `bb070fc` | Add P1r results, statistical and scientific assessment |
| red-team | `5f78e8b` | Add P1r red-team review and execution record |
| status | `d8335b6` | Update current status after P1r: L1c-P outcome and R0 as next stage |
| validation | `e7ab753` | Add read-only P1r consolidation validation script |

## Checks (`p1r_consolidation_validation.py`, all PASS)

- **Ancestry.** `855c34d`, the seal, the preflight, all six run commits and the aggregate are
  ancestors of HEAD, and the chronology above is the exact first-parent order.
- **Sealed files.** `scripts/`, `tests/` and `protocol.md` are object-identical to seal
  `90b2470`.
- **Preflight records.** `preflight.json`, `host_preflight.json`,
  `preflight_local_host_nonadmissible.json` and `preflight.md` are identical to `4c22e52`.
- **Run files.** Each of the 12 files (`runs/results_*.json`, `runs/execution_*.json`) is
  identical to its run commit. `results.json` is identical to `af6cc47`.
- **Historical artifacts.** The following are object-identical to pre-P1r `main@855c34d`:
  `reports/` (M0/G1), `m0/`, `configs/`, `data/`, and the directories
  `strong_observable_control`, `framing-refresh-2026-09`,
  `temporally_matched_observable_control`, `aplus_solver_convergence_audit`,
  `nonlinear_observable_control` and `consolidation_review_2026-09` under `research/`.
- **Row-key contract.** Both arms of all six runs equal the A+ train/validation/test keys.
  Dimensions are 1,678 / 1,912, and every run carries seal `90b2470`.
- **Execution sidecars.** All six runs record host `spark-3994`, an unchanged A+ cache listing,
  and a result SHA256 that matches the committed file.
- **Re-aggregation.** Running the sealed `aggregate` from the committed runs reproduces
  `results.json` exactly. An independent bootstrap recomputation reproduces both intervals
  exactly (`red_team.md`).
- **Wording.** `results.md`, `statistical_assessment.md`, `scientific_assessment.md` and
  `CURRENT_STATUS.md` contain no prohibited wording.

## Tests

The environment was Python 3.12.14, NumPy 1.26.4, SciPy 1.17.1 and scikit-learn 1.9.0, matching
the GB10 stack.

- Torch-free suite: **132 passed**. Four torch-dependent modules are not collectable on the
  CPU-only review host, and none of their inputs changed.
- P1r and control-line suites: 43 passed.
- `research/consolidation_review_2026-09/reviewer_recompute.py` regenerated
  `reviewer_numbers.csv` byte-identically.

## Result being consolidated

| backbone | mean ΔAP | crossed interval | source-only interval | positive | outcome |
|---|---:|---:|---:|---:|---|
| xLSTM | −0.00023259 | [−0.00076128, +0.00029149] | [−0.00047119, +0.00002557] | 14/30 | `NO_RESOLVED_ADDITIONAL_UTILITY` |
| matched LSTM | +0.00028937 | [−0.00041494, +0.00095887] | [−0.00006616, +0.00063865] | 17/30 | `NO_RESOLVED_ADDITIONAL_UTILITY` |

P1r closes the predeclared synthetic input-derived-control stage, not every possible observable
representation. The next scientific stage is R0: real-data recurrent-state measurement
validation. It is not started.
