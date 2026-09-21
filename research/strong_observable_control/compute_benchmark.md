# O2 compute-safety benchmark

This dry-run was performed before any residual-cache label join or AP result.
It used a deterministic synthetic matrix with the estimated train primary-row
count (697,430 rows) and 1,024 float32 columns; its dummy binary labels were
not evaluator labels.

| measurement | result |
|---|---:|
| matrix size | 2,856,673,280 bytes (2.660 GiB) |
| train-only StandardScaler wall | 2.22 s |
| one L2 `lbfgs`, C=0.1, 20-iteration cap | 0.44 s |
| iterations used | 3 (converged before cap) |
| maximum RSS | 9.24 GiB |
| host available memory at test | approximately 117 GiB |

The benchmark does not claim that real AP fitting takes 0.44 seconds: the
dummy matrix is easier to optimize than the detector cohort and excludes the
four-C validation loop.  It does establish that a full 1,024-column matrix at
the expected row scale is operationally feasible without downsampling.  The
scientific script therefore retains the frozen `lbfgs` solver and all rows.

A bounded inference canary on one xLSTM seed-11 stream found B256 reduced
launch overhead relative to B128 without changing the window cohort; the
committed extraction batch is 256.  No test labels were read for either
benchmark.
