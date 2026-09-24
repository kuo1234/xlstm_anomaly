# R0 v1.1 result-blind preflight

**Status: `R0_V1_1_READY_TO_RESUME`** — 7/7 checks ([`preflight_v1_1.json`](preflight_v1_1.json)). No SMD test label
was read, no metric function was called and the CUDA overlay was never invoked (it was replaced by a raising stub
for the whole run).

Executed on GB10 (`ssh:kuo`, NVIDIA GB10, Python 3.12.3, torch 2.13.0+cu130, xlstm 2.0.5, lightning 2.6.1, official
xLSTMAD `e8b56ba`) in `.worktrees/real-data-r0-execution` at the amendment commit
`ed9f7a2d27eae33bd7165e08cfc70911f294abf5`; record committed as `00f1d58`.

## Gates re-run first

Raw hashes 9/9; `tests/test_real_data_r0.py` 26/26; `tests/test_real_data_r0_execute.py` 7/7;
`tests/test_real_data_r0_v1_1.py` 7/7 (0 skipped). No other research process was running.

## v1 CUDA caches

`runs/v1_cuda_cache_invalidation.json` (commit `2e80ea9`): the five v1 caches (machine-1-8 seeds 11/22/33,
machine-2-1 seeds 11/33) were hash-checked against their v1 records and retired to
`features_v1_cuda_invalidated.npz` with status `INVALIDATED_BY_R0_V1_1_EXTRACTION_AMENDMENT`; machine-2-1 seed 22
had no v1 cache (`NO_V1_CACHE`, v1 stop). None was ever sealed or read by a probe.

## Six reused xLSTM checkpoints (vanilla backend + scalar reference observer)

| unit | best.pt = train record = amendment | model hash | parameters | eval | observer on/off (canary, fit) | repeat inference (canary, fit) | finite output/score/common18 | causality | H / I dims | warm-up |
|---|---|---|---:|---|---|---|---|---|---|---|
| machine-1-8 xLSTM 11 | yes | yes | 75,934 | yes | bitwise, bitwise | bitwise, bitwise | yes | pass | 14 / 234 | 31 rows, first finite t=94 |
| machine-1-8 xLSTM 22 | yes | yes | 75,934 | yes | bitwise, bitwise | bitwise, bitwise | yes | pass | 14 / 234 | 31, 94 |
| machine-1-8 xLSTM 33 | yes | yes | 75,934 | yes | bitwise, bitwise | bitwise, bitwise | yes | pass | 14 / 234 | 31, 94 |
| machine-2-1 xLSTM 11 | yes | yes | 75,934 | yes | bitwise, bitwise | bitwise, bitwise | yes | pass | 14 / 234 | 31, 94 |
| machine-2-1 xLSTM 22 | yes | yes | 75,934 | yes | bitwise, bitwise | bitwise, bitwise | yes | pass | 14 / 234 | 31, 94 |
| machine-2-1 xLSTM 33 | yes | yes | 75,934 | yes | bitwise, bitwise | bitwise, bitwise | yes | pass | 14 / 234 | 31, 94 |

Inputs: N(0,1) canary `[128,64,38]` (CPU generator seed 710) and the first/last 64 fit-interval windows of the
unit's machine; common18 shape `[128,18]` on both. The scalar reference observer's internal hidden/state parity
passed on every batch (it raises otherwise). Causality: perturbing a 400-row fit stream at index ≥ 250 left every
earlier row's score, common18, H and internal234 bitwise identical and changed later rows.

## Invariants

The sealed library and config (`real_data_r0_{data,models,probe,preflight}.py`, `config.json`,
`tests/test_real_data_r0.py`) have the SHA256 values recorded in the v1 `preflight.json`; Design B, embargo 96, HGB
{100, 300}, bootstraps and classification rules are therefore unchanged.
