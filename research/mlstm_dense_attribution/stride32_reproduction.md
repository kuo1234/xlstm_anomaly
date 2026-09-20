# Stride-32 reproduction gate

The dense cache was subsampled **before** any rolling features were built, at
timestamps `63, 95, 127, ...`. The same train-only source scaling, causal
history/rolling schema, L2 logistic regression, C grid, pooled validation AP
selection, and primary anomaly-vs-drift cohort were then applied as in the
previous seed-11 screen.

| arm | previous AP | reconstructed AP |
|---|---:|---:|
| H | 0.830556 | 0.830556 |
| H+S | 0.947755 | 0.947763 |
| H+M_full | 0.981010 | 0.981069 |
| H+S+M_full | 0.973903 | 0.973899 |

The reconstructed increments are `M|H=+0.150513` and
`M|H+S=+0.026136`, versus the prior `+0.150454` and `+0.026148`. This is a
pass for the pipeline gate; no dense interpretation was made until this check
completed. A few lbfgs fits reached the existing 300-iteration ceiling; the
classifier, solver, C grid, and tie rule were not changed to chase the result.

Machine-readable output: `stride32_results.json` and
`stride32_results_strata.json`.
