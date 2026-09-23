# R0 execution handoff

Status at handoff: **`R0_READY_FOR_EXECUTION`**. Nothing has been trained, fitted or scored. The executing agent
implements a thin runner over the sealed library functions, runs it on GB10, and must not change any frozen choice
in [`config.json`](config.json) / [`protocol.md`](protocol.md). Any deviation is written to `execution.md` before
results are read; a deviation that alters the contract stops R0.

## 0. Environment (GB10, `ssh:kuo`)

```
cd ~/home/xlstm_anomaly
git fetch origin research/real-data-r0-protocol
git worktree add -b experiment/real-data-r0-execution .worktrees/real-data-r0-execution origin/research/real-data-r0-protocol   # or reuse .worktrees/real-data-r0-protocol
cd .worktrees/real-data-r0-execution
mkdir -p data
ln -s ~/home/xlstm_anomaly/data/external_real data/external_real   # R0 raw bytes (git-ignored)
ln -s ~/home/xlstm_anomaly/data/phase_e2      data/phase_e2        # pinned official xLSTMAD e8b56ba
ln -s ~/home/xlstm_anomaly/data/phase_e       data/phase_e         # Python headers for the sLSTM JIT build
export PATH=$HOME/.local/bin:$PATH                                  # system /usr/bin/python3 3.12.3
```

Do not edit the primary checkout (`~/home/xlstm_anomaly`, on `main@caa9b3c` with the owner's uncommitted work).
Do not run `git worktree prune`. The sLSTM CUDA JIT directory is `/tmp/xlstm_cuda_r0_sm121_false`
(`R0_SLSTM_EXTENSION_DIR`); the first load compiles it (~1–2 min).

## 1. Gates before any training

```
python3 scripts/real_data_r0_data.py verify                          # 9/9 hashes, else DATA_PROVENANCE_BLOCKED
python3 tests/test_real_data_r0.py --json /tmp/r0_tests.json         # 26/26
python3 scripts/real_data_r0_preflight.py model --out /tmp/r0_model_preflight.json   # must pass (random init)
```

## 2. Runner to implement: `scripts/real_data_r0_execute.py`

Use only `real_data_r0_data` (loading, scaler, windows, labels, blocks), `real_data_r0_models` (configure, builders,
`cuda_overlay_from_vanilla`, `extract_batch`, `extract_windows`, `model_hash`), `real_data_r0_probe`
(`arm_matrix`, `select_and_evaluate`, `summarize_matrix`, `two_way_bootstrap`, `machine_only_bootstrap`,
`classify`, `calibration_threshold`, `detector_sanity`) and `phase_g1_core.history14` / `expand_internal234`.
Template for the training loop: `scripts/phase_f_v3_train.py` (same contract, D=8).

### `train --machine M --backbone {xlstm,lstm} --seed S` (18 runs)

1. `models.configure()`; `x = load_observations(M, "train")`; `scaler = fit_scaler(x)`; `z = apply_scaler(x, scaler)`.
2. `fit = window_matrix(z, fit_window_edges(len(x)))`; `val = window_matrix(z, validation_window_edges(len(x)))`.
   Never open the test file or labels.
3. Model: `build_xlstm_vanilla(S)` or `build_lstm(S)` (seeding happens inside). Adam with the config optimizer
   block. For epoch `e = 0…49`: `order = default_rng(SeedSequence([S, e, 1701])).permutation(len(fit))`; batches of
   128 in that order (final partial batch kept); loss `((model(xb) − xb)**2).mean()`; `model.train()` while
   optimising. After each epoch, `model.eval()`, whole-validation MSE under `no_grad` (mean over all validation
   elements); keep the checkpoint when strictly lower than the best so far (earliest epoch wins ties).
4. Save git-ignored `data/r0_runs/{M}/{backbone}_{S}/best.pt` (`{model, epoch, validation_mse}`) and `final.pt`;
   commit `research/real_data_r0/runs/{M}_{backbone}_{S}.json` with curves, selected epoch, order SHA256s, initial/
   best/final model hashes, checkpoint SHA256, parameter count, scaler (mean/scale/zero-std channels), environment.

### `extract --machine M --backbone B --seed S` (18 runs; still no labels)

1. Load `best.pt` into `build_xlstm_vanilla(S)` / `build_lstm(S)`; freeze parameters; `eval()`.
   xLSTM extraction model = `cuda_overlay_from_vanilla(vanilla)`.
2. **Checkpoint parity gate**: on the N(0,1) canary (seed 710, [128,64,38]) and on the first/last 64 fit windows:
   observer on/off bitwise for each path; vanilla+`xlstm_reference` vs CUDA+`xlstm` score/common18/output within
   atol 1e-5, rtol 1e-4; LSTM replay parity. Any failure stops R0.
3. Validation windows → scores → `threshold = calibration_threshold(scores)`.
4. Test stream: `zt = apply_scaler(load_observations(M, "test"), scaler)`; `edges = test_window_edges(test_N)`;
   `extract_windows(model, arch, window_matrix(zt, edges))` → `score`, `internal_base18`;
   `H = history14(score)`, `I = expand_internal234(internal_base18)`.
5. Save git-ignored `data/r0_runs/{M}/{B}_{S}/features.npz` (edges, score, internal_base18, H, I) and commit its
   SHA256, the threshold and the parity record in `research/real_data_r0/runs/{M}_{B}_{S}_extract.json`.
6. Commit and push the 18 feature-cache hashes **before** step 3 below reads any label.

### `probe` (after all 18 caches are sealed)

For each (M, B, S): `blocks = design_b_blocks(test_N)`; rows `r = t − 63` for `t` in each block;
`y = window_any_labels(load_test_labels(M, purpose="probe_fit_selection"), edges)` for probe-train/validation;
the probe-test loader is a closure calling `load_test_labels(M, purpose="probe_final_evaluation")` and slicing the
probe-test block. For each arm in (`H`, `H+I`): `arm_matrix(H[r], I[r], arm)` and `select_and_evaluate(...)`.
Cell `ΔAP = test_ap(H+I) − test_ap(H)`. Save per-cell records (selected max_iter, validation APs, test AP, rows,
positives) to `research/real_data_r0/runs/probe_{M}_{B}_{S}.json`.

### `aggregate`

Per backbone: 3×3 matrix (rows machine-1-8, machine-2-1, machine-1-4; columns seeds 11, 22, 33) →
`summarize_matrix`, `two_way_bootstrap(draws=10000, seed=901)`, `machine_only_bootstrap(draws=10000, seed=901)`,
`classify` → `research/real_data_r0/results.json` and `results.md` using only the §8 wording. Then the detector-sanity
table (`purpose="detector_sanity"`; all test rows t ≥ 63; window-any label; `detector_sanity(score, y, threshold)`),
with the §12 near-constant-channel note beside machine-1-4. Then `scientific_assessment.md`, `red_team.md`
(execution), `execution.md`.

## 3. Budget and scheduling

18 detector fits (3 machines × 2 backbones × 3 seeds), 50 epochs each on ~18.9k fit windows; 72 HGB fits (CPU).
Check `ps -eo pid=,args= | grep python3` first; at most two concurrent training processes (F-v4 convention).
No seed, machine, backbone or epoch budget may be changed after any curve is seen.

## 4. Stop conditions (no substitution, no rescue)

Hash mismatch; parameter-count drift; non-finite observation/score/feature after warm-up; any parity-gate failure;
a label read before the feature caches are committed; a probe block without both classes. A nearly non-functional
detector is **not** a stop condition (retain, flag `DETECTOR_WEAK`).

## 5. Deliverables

`runs/*.json` (18 train, 18 extract, 18 probe), `results.json`, `results.md`, detector-sanity table,
`scientific_assessment.md`, `red_team_execution.md`, `execution.md`, updated `research/CURRENT_STATUS.md`;
push the execution branch. Do not merge to `main` without a consolidation review.
