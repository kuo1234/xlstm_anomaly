# Three-seed exploratory replication

Frozen vanilla-trained checkpoints 11, 22, and 33 were used without
retraining.  The same observation-only extraction, deterministic timestamp
cohort, four shifted scenarios, five conditions, pooled train/validation C
selection, train-only StandardScaler, and L2 logistic probe were used for all
three seeds.  This remains exploratory; no confirmatory p-value or H3b claim
is produced.

## Pooled test AP and increments

| seed | H | H+S | H+M | H+S+M | M|H | M|H+S |
|---:|---:|---:|---:|---:|---:|---:|
| 11 | 0.830556 | 0.947755 | 0.981010 | 0.973903 | +0.150454 | +0.026148 |
| 22 | 0.826253 | 0.948373 | 0.978841 | 0.971482 | +0.152587 | +0.023110 |
| 33 | 0.814998 | 0.954666 | 0.971151 | 0.959742 | +0.156153 | +0.005076 |
| mean | 0.823936 | 0.950265 | 0.977001 | 0.968376 | +0.153065 | +0.018111 |
| sample SD | 0.0080 | 0.0037 | 0.0051 | 0.0077 | 0.0029 | 0.0114 |

M|H is positive for all three seeds and all four scenarios.  M|H+S is
positive for all three pooled seeds; it is positive in abrupt, gradual, and
recurring for each seed, while correlation is positive only for seed 11 and
negative for seeds 22 and 33.  The scenario means for M|H+S are abrupt
`+0.0065`, gradual `+0.0210`, recurring `+0.0736`, and correlation `-0.0044`.

The duration/severity breakdown is heterogeneous for M|H+S, especially for
seed 33; these strata are descriptive and do not rescue or create a
confirmatory claim.  The machine-readable per-seed files contain every
scenario, duration, severity, selected C, class count, and validation-candidate
value.
