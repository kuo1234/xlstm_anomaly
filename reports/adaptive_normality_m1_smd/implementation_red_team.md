# M1 result-blind implementation red-team

## Verdict

`M1_IMPLEMENTATION_RESULT_BLIND_PASS`

The independent review found no material implementation blockers after the
documented fixes. It reviewed the isolated implementation, tests, result-blind
artifacts, and current branch ancestry. This is an implementation review, not
a detector evaluation.

## Required review points

1. **Historical xLSTMAD-F fidelity — PASS.** The port follows the pinned
   historical forecasting implementation at
   `3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6`; the CPU parity test loads the
   historical class and confirms exact synthetic p=1 output parity with shared
   state. The three-block encoder/decoder, E=40, `slstm_at=[1]`, last-latent
   one-token decoder, GELU and projection are preserved. Window normalization
   and score padding are absent; each independent window uses fresh state.
2. **Reconstruction comparison — PASS.** `R-native-window` remains the mean
   squared residual over W×D. `R-endpoint` is the mean over the final D
   residuals. Both use the same unchanged reconstruction model/output and
   original timestamp; synthetic first/middle/final-position corruptions are
   tested.
3. **Forecast causality — PASS.** Input is `[t−256,t)`, target is `t`, and
   prediction is materialized before target access in the score path. Fit
   targets stay in fit rows; validation/calibration use only preceding observed
   context. Test score endpoints begin exactly at 256 with no padding.
4. **Label isolation — PASS.** M1 loader APIs expose only train/test
   observations. Runtime guards block test-label file opens during
   preprocessing, training, validation, calibration, and scoring. The future
   metric entry point requires the committed complete score inventory before
   entering its label-loader scope. This implementation/preflight recorded
   zero test-label opens/reads and computed no anomaly metric.
5. **Oracle terminology — PASS.** The per-machine max-AP comparator is named
   the test-label-dependent oracle control envelope and described only as a
   conservative scientific gate. The fixed label-free fusion is separately
   retained as the operational complement diagnostic.
6. **Canary selection — PASS.** Shortest, lower-median-rank and longest
   machines were selected mechanically from train lengths and machine-name
   tie-breaking, independent of detector behavior.
7. **Frozen choices — PASS.** The code keeps 28 machines, W=256, seed 11,
   existing epoch/batch/model dimensions, the official R architecture and
   objective, the historical F one-step contract, and the declared scientific
   gates. No R0 scientific source or output was changed.
8. **Timestamp parity — PASS.** Raw learned arms and controls are checked
   against one exact endpoint vector before the nine-score machine record is
   sealed.
9. **Main/R0 ancestry — PASS.** The original M1 scientific commit remains an
   ancestor, and latest main was merged normally. R0 history and outputs remain
   unchanged.
10. **Engineering scope — PASS.** The canary used train fit/validation only;
    no 28-machine Stage-1 run or metric path was invoked. The report discloses
    that concurrent-fit throughput was not measured and that two fits fail the
    measured free-memory/headroom check.

## Evidence and limitations

The combined pinned-environment suite passed 103 tests: 51 M1 and 52 R0
regression tests. One pre-existing R0 tensor-to-scalar warning remains. The
implementation, test, canary and dry-run preflight records report zero
test-label opens/reads and no anomaly metrics. The reviewer did not use an
independent OS-level file-open trace, so the zero-read evidence is based on
module guards and execution records. No scientific detector result was
observed.
