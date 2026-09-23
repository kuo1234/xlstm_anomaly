# R0 execution record

**Status: `R0_EXECUTION_BLOCKED` — fail-closed at the checkpoint parity gate of `machine-2-1 / xLSTM / seed 22`.**
R0 was stopped exactly as the sealed protocol requires (protocol §10 step 3; `execution_handoff.md` §2 extract step 2:
"Any failure stops R0"). No checkpoint was substituted, no tolerance was changed and no step was repeated. No test
label has been read by any stage. No R0 result exists: this is **not** a null result.

## Integrity

| item | value |
|---|---|
| protocol branch / sealed HEAD | `research/real-data-r0-protocol` @ `d7708586fe3264fcd6e5567504cccd97104c2a2e` (unchanged) |
| base main | `b7ae44fafc4e9ea6671647c5cb73156ddaf26e5e` (unchanged) |
| execution branch | `experiment/real-data-r0-execution` (worktree `~/home/xlstm_anomaly/.worktrees/real-data-r0-execution`, created from `origin/research/real-data-r0-protocol`) |
| runner commit | `271eb81fbee51b8cdd01f68f0e537d7d4d709d7b` — pushed before any detector was trained; runner, library, tests, config and protocol unchanged at every later commit (only run records were added) |
| data links | `data/external_real`, `data/phase_e2`, `data/phase_e` → primary checkout `data/` (git-ignored); primary checkout untouched (`main@caa9b3c`, identical `git status` before and after) |
| compute | GB10 (`ssh:kuo`), Python 3.12.3, torch 2.13.0+cu130, xlstm 2.0.5, lightning 2.6.1, official xLSTMAD `e8b56ba`; sLSTM JIT dir `/tmp/xlstm_cuda_r0_sm121_false` |

## Gates before training (all PASS)

* `real_data_r0_data.py verify`: 9/9 raw SHA256 and byte counts.
* `tests/test_real_data_r0.py`: 26/26 (0 skipped). Runner orchestration tests `tests/test_real_data_r0_execute.py`: 7/7 on GB10.
* `real_data_r0_preflight.py model`: PASS; xLSTM 75,934 and matched LSTM 74,100 parameters for seeds 11/22/33; observer
  on/off bitwise and reference-vs-fast parity on random-init models; no label access; 0 metric calls.
* `ps` before training: no other research Python process (only an unrelated long-running service helper).

## Detector execution (train split only; at most two concurrent processes)

Schedule order (longest first): xLSTM machine-1-8 s11/s22/s33, machine-2-1 s11/s22/s33, machine-1-4 s11/s22/s33, then
the nine LSTM units. Each unit = `train` then `extract`; each finished unit was committed and pushed immediately.

| unit | train | params | selected epoch | best validation MSE | train s | extract / checkpoint parity |
|---|---|---:|---:|---:|---:|---|
| machine-1-8 xLSTM 11 | PASS | 75,934 | 47 | 0.00147915 | 2234 | PASS (cache `e321c469…`) |
| machine-1-8 xLSTM 22 | PASS | 75,934 | 50 | 0.00156007 | 2236 | PASS (cache `d3ee6d3c…`) |
| machine-1-8 xLSTM 33 | PASS | 75,934 | 49 | 0.00156225 | 2247 | PASS (cache `bb7ed791…`) |
| machine-2-1 xLSTM 11 | PASS | 75,934 | 50 | 0.0102585 | 2247 | PASS (cache `d14b2ef7…`) |
| machine-2-1 xLSTM 22 | PASS | 75,934 | 50 | 0.0103989 | 2252 | **STOP_CHECKPOINT_PARITY** (no cache) |
| machine-2-1 xLSTM 33 | PASS | 75,934 | 50 | 0.0119099 | 2253 | PASS (cache `9b316994…`; already running when the stop occurred) |

Every training record: 7,400 optimizer steps (50 × 148), `labels_read: false`, `test_split_read: false`,
0 native `predict_step` calls, full curve, scaler metadata, checkpoint and model hashes, environment. Validation MSE is
a train-split quantity; no test performance was computed or inspected.

**Not executed (stopped):** machine-1-4 xLSTM 11/22/33 and all nine matched-LSTM units (12 of 18 detector fits);
`seal-features`, `probe` (0 of 72 HGB fits), `aggregate`, `sanity`, `report`. Five feature caches exist git-ignored
under `data/r0_runs/`; they are **not sealed** (no feature-cache manifest was written) and no label was read.

## The stop event

Gate for `machine-2-1_xlstm_22` (record `runs/extract_machine-2-1_xlstm_22.json`):

| input | observer on/off (reference, fast) | vanilla vs CUDA output | reference vs fast score | reference vs fast common18 |
|---|---|---|---|---|
| N(0,1) canary [128,64,38], seed 710 | bitwise, bitwise | **fail**: max \|Δ\| 2.63e-5 | pass (3.6e-7) | pass (1.2e-7) |
| first/last 64 fit windows | bitwise, bitwise | pass (max \|Δ\| 1.72e-5) | pass (1.1e-8) | pass (1.2e-7) |

Result-blind diagnostic of the same checkpoint (`runs/diagnostic_parity_machine-2-1_xlstm_22.json`; canary and fit
windows only; no labels; no test observations; run after the stop and not part of any R0 decision): exactly **1 of
311,296** canary output elements exceeds `atol 1e-5 + rtol 1e-4·|ref|` (by a factor of 2.07); 0 of 311,296 on the fit
windows. The discrepancy is between the vanilla training backend and the native CUDA sLSTM overlay (compiled with
`--use_fast_math`) on the raw reconstruction output for an out-of-distribution random input. The score and common18
that `H` and `internal234` are built from agree to ≤ 3.6e-7 on both inputs. The other five xLSTM checkpoints passed
the same gate (largest canary output |Δ| 1.53e-5, within tolerance through the relative term).

Interpretation for the owner (no action taken): the failing criterion is the output-parity component of the
sealed gate, not the observer mechanism itself; the frozen rule nonetheless makes it a stop, and the executing
agent may not reinterpret it.

## Owner decision required (not taken)

The trained checkpoints are unaffected (training used the vanilla backend). Continuing R0 requires an explicit,
result-blind protocol amendment committed before any label is read. Options:

1. **Keep R0 stopped.**
2. **r0-v1.1 extraction-backend amendment** — extract all nine xLSTM units with the vanilla (training) backend and
   the parity-checked scalar reference observer (`extract_batch(..., "xlstm_reference")`), re-extracting the five
   existing xLSTM caches, so no fast-math CUDA kernel enters any feature; keep every other rule. Same checkpoints, no
   substitution.
3. **r0-v1.1 gate amendment** — require bitwise observer on/off plus score/common18 parity (the feature inputs) and
   fit-window output parity; record OOD-canary output parity as a diagnostic.

Either amendment is decidable now because no probe, label or test metric has been observed. Option 2 removes the
backend difference entirely and is the cleaner choice; option 3 keeps the validated extraction path.

## Files

`runs/train_*.json` (6), `runs/extract_*.json` (6, one `STOP_CHECKPOINT_PARITY`),
`runs/diagnostic_parity_machine-2-1_xlstm_22.json`, `red_team_execution.md`, `scientific_assessment.md`.
Not produced (stage not reached): `feature_cache_manifest.json`, `runs/probe_*.json`, `results.json`, `results.md`,
`detector_sanity.json`.
