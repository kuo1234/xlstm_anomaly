# R0 v1.2 result-blind preflight

Machine-readable record: [`preflight_v1_2.json`](preflight_v1_2.json) (GB10, torch 2.13.0+cu130, NVIDIA GB10;
execution commit `1f6f4abe36465b1e66843c38d47bd62d8bd56671`, finished 2026-09-24T06:38:19Z; amendment commit
`2c1677c5c739deac7e31c91099a658779a8a532c`). No training, no execution-stage label read, no metric call.

**Status: `R0_V1_2_READY_TO_RESUME`** (13 / 13 checks, `failed: []`).

| check | result |
|---|---|
| raw SMD hashes 9 / 9 | PASS |
| carried xLSTM identities 9 / 9 (best.pt SHA256, model hash via vanilla build, feature-cache SHA256, v1.1 extraction and training record SHA256) | PASS |
| auditable LSTM trainable parameters = 74,100 (seeds 11 / 22 / 33) | PASS |
| seed determinism (two builds per seed bitwise equal; seeds differ) | PASS |
| equation tests (float64 handcrafted one-step: max abs i 0, f 0, g 1.1e-16, o 0, c 5.6e-17, h 2.8e-17; multi-step bitwise; capture on/off bitwise) | PASS |
| v1.2 gate, 3 seeds × 3 machines (canary + fit windows: capture on/off, repeat, extract = forward all bitwise, max abs 0.0; finite; gates in [0,1]; common18 [128, 18]; six layers) | PASS (9 / 9) |
| common18 / H / internal234 schema and causality on the machine-1-8 fit stream (past rows bitwise equal after a future perturbation; future rows change; 18 / 14 / 234; first finite edge 94; 31 warm-up rows) | PASS (3 seeds) |
| no label access (`label_access_log: []`) | PASS |
| no metric calls (`metric_calls: []`) | PASS |
| no native LSTM scientific call (runtime guard active) | PASS |
| sealed design / probe / statistics code unchanged (SHA256 vs `preflight.json`) | PASS |
| native LSTM invalidation recorded ([`runs/v1_1_native_lstm_invalidation.json`](runs/v1_1_native_lstm_invalidation.json)) | PASS |
| amendment protocol version `r0-v1.2` | PASS |

Test suites on GB10 before the preflight: `test_real_data_r0` 26 / 26, `test_real_data_r0_execute` 7 / 7,
`test_real_data_r0_v1_1` 8 / 8, `test_real_data_r0_v1_2` 11 / 11 (0 skipped); `data verify` PASS.

Non-gating engineering diagnostic ([`runs/engineering_native_lstm_comparison_v1_2.json`](runs/engineering_native_lstm_comparison_v1_2.json)):
at seed 11 random initialisation the auditable LSTM's initial parameters are identical to the r0-v1 native
builder's, and with the same parameters the reconstruction on the N(0,1) canary differs from native `nn.LSTM` by at
most 1.49e-8 (output max abs 0.173). This documents mathematical equivalence only; it is not an acceptance criterion
and was not used for tuning.
