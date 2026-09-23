# P1r results — input-derived observable control

## Scope

Six sealed runs were executed on the GB10 cache host (`spark-3994`, Linux aarch64, Python
3.12.3, NumPy 1.26.4, SciPy 1.17.1, scikit-learn 1.9.0): xLSTM and matched LSTM, detector
seeds `11, 22, 33`. They ran in the worktree
`~/home/xlstm_anomaly/.worktrees/input-derived-observable-control` under protocol seal
`90b2470b45b1f8e52aa95ee8677b855b2e3c4e4d`. The sealed aggregate followed.

- No detector inference, retraining or cache write took place.
- No code changed after the seal.
- Both preflights passed before any fit.

Execution details are in `execution.md`.

- The decoder is the frozen `HistGradientBoostingClassifier` family from the nonlinear audit,
  with `max_iter ∈ {100, 300}`. Candidates were fitted on train only and selected by pooled
  validation AP. Test was evaluated once, after selection.
- P1r is the frozen 128-column O1 statistic family on the scaled `[64,8]` input window,
  followed by the identical causal 4/8/16/32 expansion: 1,664 columns with raw support
  `[t−94, t]`.
- Arm dimensions are 1,678 and 1,912.

## Primary result

Primary estimand: the source-level mean of the 10 × 3 source × seed matrix of
`AP(H+P1r+internal234) − AP(H+P1r)`.

| backbone | source-level mean ΔAP | crossed 95 % interval (exploratory) | source-only 95 % interval (exploratory) | positive cells | outcome |
|---|---:|---:|---:|---:|---|
| xLSTM | −0.00023259 | [−0.00076128, +0.00029149] | [−0.00047119, +0.00002557] | 14/30 | `NO_RESOLVED_ADDITIONAL_UTILITY` |
| matched LSTM | +0.00028937 | [−0.00041494, +0.00095887] | [−0.00006616, +0.00063865] | 17/30 | `NO_RESOLVED_ADDITIONAL_UTILITY` |

The full matrices are in `source_seed_effects.csv` and `results.json`. The cells range from
−0.00311858 to +0.00190768 for xLSTM and from −0.00212528 to +0.00268517 for LSTM. No cell
reaches the historical +0.02 descriptive reference.

## Per-seed and per-source summaries (descriptive)

| backbone | seed | seed mean of source effects | pooled test ΔAP | AP(H+P1r) | AP(H+P1r+I) |
|---|---:|---:|---:|---:|---:|
| xLSTM | 11 | −0.00041730 | −0.00040826 | 0.97700518 | 0.97659691 |
| xLSTM | 22 | +0.00019222 | +0.00012880 | 0.97670471 | 0.97683351 |
| xLSTM | 33 | −0.00047268 | −0.00042654 | 0.97711351 | 0.97668697 |
| matched LSTM | 11 | +0.00018156 | +0.00020858 | 0.97630728 | 0.97651586 |
| matched LSTM | 22 | +0.00084303 | +0.00083476 | 0.97646758 | 0.97730234 |
| matched LSTM | 33 | −0.00015647 | −0.00016743 | 0.97658239 | 0.97641496 |

Per-source means over seeds:

| source | xLSTM | matched LSTM |
|---:|---:|---:|
| 3000 | −0.000699 | −0.000080 |
| 3001 | +0.000390 | +0.000184 |
| 3002 | −0.000765 | +0.000814 |
| 3003 | −0.000240 | +0.000646 |
| 3004 | +0.000301 | −0.000814 |
| 3005 | −0.000342 | +0.000095 |
| 3006 | −0.000575 | +0.000917 |
| 3007 | −0.000496 | −0.000184 |
| 3008 | +0.000274 | +0.000113 |
| 3009 | −0.000175 | +0.001202 |

Scenario means of pooled-within-scenario ΔAP (descriptive strata, not tests):

| scenario | xLSTM | matched LSTM |
|---|---:|---:|
| abrupt | −0.00044326 | +0.00029026 |
| gradual | −0.00023957 | −0.00027349 |
| recurring | −0.00042503 | +0.00044490 |
| correlation | +0.00003551 | +0.00096784 |

## Selection path

All 12 arm fits (2 arms × 6 runs) selected `max_iter = 300` by validation AP. Every candidate
and selected fit recorded `n_iter_ == max_iter`, which is the fixed boosting budget with
`early_stopping=False`, and no candidate carries a test metric. The validation APs are in
`descriptive_summary.json`.

## Descriptive comparison with the nonlinear O1r audit (protocol: descriptive only)

This comparison uses the same rows, decoder family and detector runs; only the observable
summary differs.

| backbone | seed | AP(H+O1r) | AP(H+O1r+I) | AP(H+P1r) | AP(H+P1r+I) |
|---|---:|---:|---:|---:|---:|
| xLSTM | 11 | 0.93448083 | 0.94968195 | 0.97700518 | 0.97659691 |
| xLSTM | 22 | 0.93838540 | 0.95314840 | 0.97670471 | 0.97683351 |
| xLSTM | 33 | 0.93806905 | 0.95327725 | 0.97711351 | 0.97668697 |
| matched LSTM | 11 | 0.94411540 | 0.95536643 | 0.97630728 | 0.97651586 |
| matched LSTM | 22 | 0.94655021 | 0.95818695 | 0.97646758 | 0.97730234 |
| matched LSTM | 33 | 0.94682311 | 0.95804012 | 0.97658239 | 0.97641496 |

Under the frozen decoder, `H+P1r` has higher test AP than `H+O1r+internal234` in every run.
This is a descriptive observation and is not tested.
