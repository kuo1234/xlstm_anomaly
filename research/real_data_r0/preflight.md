# R0 result-blind preflight

**Result: PASS — 32/32 checks** ([`preflight.json`](preflight.json)). No detector was trained, no probe was fitted,
and no AP/AUROC/recall/FPR was computed.

Executed on GB10 (`ssh:kuo`, NVIDIA GB10, Python 3.12.3, torch 2.13.0+cu130, xlstm 2.0.5, lightning 2.6.1, official
xLSTMAD `e8b56ba`) in the dedicated worktree `.worktrees/real-data-r0-protocol` at commit
`0f75d089f33e58c37c5d1d9ca5c2413457a1b270` (worktree clean before and after). Code/config SHA256 of that commit are
recorded in `preflight.json → code_sha256` and are unchanged in the sealing commit.
Reproduce: `python3 scripts/real_data_r0_preflight.py data|model --out …`, then `assemble`.

## Data and provenance (`data` stage; numpy only; sklearn never imported)

| check | machine-1-8 | machine-2-1 | machine-1-4 |
|---|---|---|---|
| raw SHA256 + bytes (train/test/label) | 3/3 | 3/3 | 3/3 |
| D | 38 | 38 | 38 |
| train_N / test_N / label_N | 23698 / 23699 / 23699 | 23693 / 23694 / 23694 | 23706 / 23707 / 23707 |
| finite observations; binary labels | yes; yes | yes; yes | yes; yes |
| fit_end = ⌊0.8·train_N⌋ | 18958 | 18954 | 18964 |
| Phase-A seal intervals reproduced | yes (5/5) | yes (5/5) | n/a (not in Phase A) |
| fit / validation / test windows | 18895 / 4677 / 23636 | 18891 / 4676 / 23631 | 18901 / 4679 / 23644 |
| straddling windows | 0 | 0 | 0 |
| zero-std fit channels (→ scale 1) | 4,7,16,17,26,28,36,37 | 7,26,28,36,37 | 7,16,26,28,36,37 |
| smallest non-zero fit std | 5.08e-3 | 1.52e-3 | 1.69e-5 |
| max \|scaled\| fit / validation / test | 81 / 28 / 196 | 122 / 48 / 656 | 70 / 3280 / 59333 |
| scaler unchanged when all non-fit rows are replaced | yes | yes | yes |
| point positives (prevalence) | 763 (3.22%) | 1170 (4.94%) | 720 (3.04%) |
| window-any positives, t ≥ 63 (prevalence) | 2007 (8.49%) | 1989 (8.42%) | 1476 (6.24%) |
| window-any labels equal brute force | yes | yes | yes |

### Design-B blocks (frozen before any model; label counts inspected only for AP definability)

| machine | probe-train | probe-validation | probe-test |
|---|---|---|---|
| machine-1-8 | [94, 7962): 7868 rows, 968 pos, 8 runs | [8058, 15830): 7772 rows, 523 pos, 6 runs | [15926, 23699): 7773 rows, 516 pos, 5 runs |
| machine-2-1 | [94, 7960): 7866 rows, 138 pos, 2 runs | [8056, 15827): 7771 rows, 269 pos, 3 runs | [15923, 23694): 7771 rows, 1518 pos, 8 runs |
| machine-1-4 | [94, 7965): 7871 rows, 211 pos, 2 runs | [8061, 15836): 7775 rows, 468 pos, 3 runs | [15932, 23707): 7775 rows, 797 pos, 7 runs |

Every block has both classes, so AP is defined for all 27 machine × block cells. Embargo 96 ≥ receptive field 95;
no point-anomaly run spans either embargo on any machine. Boundaries were not and will not be moved.

Label access log (data stage): exactly one purpose-gated read per machine (`preflight_counts`).

## Model and observer (`model` stage; random-init D=38; no labels, no test observations)

Metric trap installed before any model import (the official xLSTMAD/lightning stack imports sklearn transitively;
every sklearn metric entry point was replaced by a raising trap): **0 metric calls**. Label access: **none**.

| check | result |
|---|---|
| xLSTM trainable parameters (vanilla and CUDA overlay, seeds 11/22/33) | 75,934 each |
| D-dependent xLSTM tensors | `input_projection.weight` [40,38], `output_projection.weight` [38,40], `output_projection.bias` [38] |
| LSTM trainable parameters (w = 38) | 74,100 each; width rule reproduces 38 (−2.415%) |
| observer on/off output parity (xLSTM reference, xLSTM CUDA fast, LSTM; 3 seeds × 4 inputs) | bitwise identical, 36/36 |
| vanilla vs CUDA overlay output | max \|Δ\| 1.63e-6 (atol 1e-5, rtol 1e-4) |
| reference vs fast score / common18 | max \|Δ\| 4.77e-7 / 3.58e-7 |
| internal observer parity (scalar reference hidden/state; LSTM manual replay) | pass on every batch |
| common18 shape and finiteness | [128, 18], finite, both backbones |
| H / internal234 dimensions | 14 / 234 for both backbones |
| end-to-end causality (perturb observations ≥ index 250 of a 400-row fit stream) | rows with right edge < 250 bitwise identical (score, common18, H, internal234); later rows change |
| warm-up | first finite row t = 94; exactly 31 warm-up rows; all later rows finite |
| inputs used | N(0,1) canary [128,64,38] (seed 710) and the first/last 64 fit-interval windows of each machine |

Semantic audit — see [`internal_feature_transfer_audit.md`](internal_feature_transfer_audit.md):
LSTM full-network unit permutation invariant (output 3.0e-8, common18 1.2e-7); LSTM sign reparameterisation is
function-preserving (output bitwise identical) and changes exactly hidden_mean, hidden_std, memory_mean,
memory_std; xLSTM and LSTM reductions are permutation invariant on real traces and show the same four
polarity-sensitive columns.

API audit: no model-facing entry point (`extract_batch`, `extract_windows`, builders, `load_observations`,
`fit_scaler`, `apply_scaler`, `window_matrix`) has a label/target parameter.

## HGB selection isolation (unit tests)

`select_and_evaluate` fits both candidates on probe-train, selects on probe-validation AP (tie → 100), computes
probe-test predictions and only then calls the probe-test label loader, exactly once. Tests verify: the tie rule;
a single post-selection label read; selection and validation AP invariant to arbitrary changes of the probe-test
labels; a real HGB run on synthetic data. The HGB parameters equal `nonlinear_observable_control.estimator_parameters`
for both budgets.

## Test suites

* GB10, `python3 tests/test_real_data_r0.py` (unittest, torch available): **26/26 passed**, 0 skipped.
* Local (NumPy 1.26.4, torch-free): `PYTHONPATH=. pytest tests` excluding four torch-only historical modules —
  **155 passed, 3 skipped** (the three R0 torch tests, which ran on GB10). The P1r historical-artifact guard
  (`configs/`, `reports/`, … unchanged since `855c34d`) stays green; this is why the R0 config lives under
  `research/real_data_r0/config.json`.
* P1r consolidation validator (`p1r_consolidation_validation.py --ref b7ae44f…`, current working-tree wording):
  **PASS**; `research/CURRENT_STATUS.md` has no prohibited-wording hit. The validator's chronology walk assumes
  HEAD is the P1r consolidation merge, so it is run against `b7ae44f`; `git diff b7ae44f` shows no change under
  `research/input_derived_observable_control`, `reports`, `m0`, `configs`, `data` or the earlier control lines.
  The older `consolidation_review_2026-09/consolidation_validation.py` already reports FAIL on `b7ae44f` itself
  (its changed-file allow-list predates the P1r consolidation); R0 does not change that result.
