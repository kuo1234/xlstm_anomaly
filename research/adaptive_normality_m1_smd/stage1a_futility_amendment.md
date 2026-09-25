# Prospective M1 Stage-1A futility screen amendment

**Frozen prospectively before any formal M1 anomaly outcome.** At the time this amendment was prepared, the committed full Stage-1 result, gate, and label-access artifacts were absent and no real M1 anomaly metric had been computed or inspected. This amendment cannot establish scientific success and cannot return `M1_STAGE1_PASS`. Its only outcomes are `STOP_FOR_FUTILITY` and `CONTINUE_TO_STAGE1B`; Stage 1B is never launched automatically.

The complete 28-machine Stage-1 protocol and gate remain authoritative. Stage 1A is a one-sided expenditure screen only. A stop means only that the frozen screen showed sufficiently weak evidence to justify ending M1 forecasting expenditure; continuation means only that the screen did not establish futility. Neither outcome alone supports a paper claim.

## Machine selection

Select three machines within each SMD group using only the frozen manifest's train-row counts. Sort by `(train_rows, machine_name)`. For group size `n`, select zero-based rank `floor(q*(n-1)+0.5)` at q=.25, .50, and .75. If ranks collide, move to the nearest unused rank, preferring the higher rank on equal distance. No test labels, prevalence, anomaly properties, R0 or M1 detector behavior, or score outcomes enter selection. The exact ordered list and ranks are frozen in `stage1a_machines.json`.

Frozen ordered selection: `machine-1-7` (n=8, q=.25, rank 2, 23,697 train rows), `machine-1-3` (n=8, q=.50, rank 4, 23,702), `machine-1-5` (n=8, q=.75, rank 5, 23,705); `machine-2-4` (n=9, q=.25, rank 2, 23,689), `machine-2-7` (n=9, q=.50, rank 4, 23,696), `machine-2-8` (n=9, q=.75, rank 6, 23,702); `machine-3-2` (n=11, q=.25, rank 3, 23,702), `machine-3-11` (n=11, q=.50, rank 5, 28,695), `machine-3-7` (n=11, q=.75, rank 8, 28,705). No duplicate-rank correction was needed.

## Frozen execution

The detector set is last-value, moving median, ridge VAR(1), xLSTMAD-F, and capacity-matched LSTM-F, plus fixed label-free `cheap_control_fusion` and `forecast_cheap_control_fusion`. xLSTMAD-R is not run. All existing M1 data splits, robust scaling, W=256, D=38, seed 11, batch 128, Adam at 1e-3, maximum 50 epochs, validation checkpoint selection, and normal-calibration procedure remain unchanged. Calibration thresholds are q=.99 with method `higher`. Each Stage-1A file is isolated below `reports/adaptive_normality_m1_smd/stage1a_screen/`; none is a member of the final 28-machine inventory.

## Futility rule

For each machine, `cheap_oracle_AP=max(AP(last_value), AP(moving_median), AP(var1))`. This is test-label-dependent and exists only for this screen; it is not deployable. Let standalone delta be xLSTMAD-F AP minus that oracle, and complement delta be forecast-plus-cheap-control fusion AP minus cheap-control-fusion AP. A route is futile only when its nine-machine mean delta is <=0 and no more than 3/9 deltas are positive. Return `STOP_FOR_FUTILITY` only when both routes are futile. In every other case return `CONTINUE_TO_STAGE1B`. There is no significance test, efficacy gate, bootstrap, or early-success rule. LSTM-F is diagnostic only.

After labels are opened, these nine machines may remain in the final confirmatory 28 only if no scientific configuration is changed based on their outcomes. Any result-driven change to method, W, scaler, threshold, fusion, machine subset, seed, or model size makes these nine development machines and removes their untouched-confirmatory status.
