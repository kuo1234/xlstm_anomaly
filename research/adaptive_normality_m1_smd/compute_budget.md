# M1-A compute budget

## Previous planning estimate

The earlier approximately 190 GB10-hour figure was an extrapolation from R0 W=64 fits, scaled to W=256. It was not a measured M1 runtime and did not use the historical xLSTMAD-F one-step implementation's throughput.

## Result-blind GB10 canary

After all CPU/unit and R0 regression tests passed, an engineering-only canary ran on NVIDIA GB10. It used four bounded batches per arm before applying a predeclared affordability rule; the throughput projection was below 600 seconds per case and 1,800 seconds in total, so one complete epoch was measured for all nine arm/machine cases. The canary trained only on fit rows and evaluated only on validation rows. It did not load test observations or labels, generate anomaly scores, or compute metrics.

Machines were selected mechanically from train lengths after sorting `(train_rows, machine_name)`: shortest `machine-3-4` (23,687 rows), lower median rank `machine-1-3` (23,702 rows), and longest `machine-2-6` (28,743 rows). The lower median rank is `floor((28-1)/2)=13`; ties use machine name.

Environment: Python 3.12.3, PyTorch 2.13.0+cu130, CUDA 13.0, xlstm 2.0.5, Lightning 2.6.1, 20 Torch threads, NVIDIA GB10. All canary fits used W=256, D=38, batch 128, seed 11, float32, Adam at 1e-3.

| Arm | Complete-epoch fit windows/s (range) | Optimizer steps/s (range) | Forward windows/s (range) | Measured epoch duration (range) | Peak allocated / reserved GPU memory |
|---|---:|---:|---:|---:|---:|
| xLSTMAD-R | 150.0–152.5 | 1.178–1.196 | 683–698 | 112.3–138.8 s | 3.78 / 3.85 GB |
| xLSTMAD-F | 429.2–431.3 | 3.36–3.38 | 1,729–1,745 | 39.9–48.8 s | 2.59 / 3.85 GB |
| LSTM-F | 14,694–15,766 | 115.1–123.8 | 58,143–61,315 | 1.16–1.34 s | 0.315 / 3.85 GB |

Checkpoint writes took 0.008–0.019 seconds per measured best checkpoint, under 0.02% of the xLSTMAD-R epoch and below 2% of the shortest LSTM-F epoch. Timing records, per-machine values, and the affordability decision are in [timing_canary.json](../../reports/adaptive_normality_m1_smd/timing_canary.json).

## Re-estimated Stage 1

The estimate uses the actual frozen 28-machine train-window and validation-window counts. For each machine it assigns measured throughput from the nearest canary train length; ties use the selection order. It projects the frozen 50 epochs, validation passes, checkpoint writes, normal calibration forwards, and test forwards from t=256. It does not use test labels or detector behavior.

| Learned arm | Fit training | Validation | Calibration/test forwards and checkpoint I/O | Estimated serial GB10-hours |
|---|---:|---:|---:|---:|
| xLSTMAD-R | 44.89 h | 2.14 h | 0.33 h | **47.36 h** |
| xLSTMAD-F | 15.79 h | 0.85 h | 0.13 h | **16.78 h** |
| LSTM-F | 0.45 h | 0.02 h | 0.01 h | **0.48 h** |
| Total | 61.12 h | 3.02 h | 0.49 h | **64.62 GB10-h** |

The Stage-1 estimate is **64.62 serial GB10-hours**. A 25% engineering schedule allowance gives **80.78 hours**. This replaces the older 190-hour R0 W=64 extrapolation in the engineering budget only; no scientific gate or frozen setting changed. Detailed counts and the per-machine extrapolation are in [compute_estimate.json](../../reports/adaptive_normality_m1_smd/compute_estimate.json).

Peak allocated memory was 3.78 GB and peak reserved memory was 3.85 GB. The device reports 130.66 GB total memory; available memory after the canary was 7.21 GB. Two fits would require about 7.71 GB reserved before a 15% headroom allowance, so two concurrent fits are **not currently budgeted**. The expected wall time therefore equals the 64.62-hour serial estimate (or 80.78 hours with the schedule allowance). Concurrent-throughput contention was not measured.

The conservative disk estimate is **0.672 GiB**, including the 56 pinned train/test feature files, uncompressed nine-score arrays and timestamps, calibration score/reference arrays, scaler artifacts, best checkpoints, 50-epoch run-record allowance, and 25% staging margin. The observed filesystem had substantially more available space.

These are engineering estimates, not observed 28-machine runtimes. Stage 1 has not started. Cheap control CPU time and unrelated filesystem staging overhead are excluded. The estimate does not change the 28-machine cohort, W=256, seed, batch size, epochs, dimensions, or detector arms.

## Stage 2

Stage 2 remains gated by the frozen scientific criteria and is not authorized or started here. Its previous planning estimate is not revised by this Stage-1 canary.

## Compute-aware handoff

Before a later Stage-1 start, confirm the approximately 81-hour engineering allocation, the completed implementation preflight, all observation manifest checks, and the no-label score-sealing order. Do not reduce the frozen cohort, context, epoch cap, seed, or arms to fit an allocation.
