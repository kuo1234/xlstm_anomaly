# D0 fixed method / family analysis

[AD_multi.csv](https://github.com/magaliparrino/StrAD/blob/7078876bbd9398481a65c22b7689702ce9e0d558/AD_multi.csv) supplies29 method property rows:19 Online/static and10 Streaming. Static metric CSV has an additional Donut column absent from Online/AD_multi; it remains static-only and is excluded from paired deltas. MCOD type CLustering is retained as published (case differences are not a new model class). GPU/tuning flags are descriptors, not proof of resources used or equally strong optimization budgets.

Fixed-method drift table, equal source-family AUC-PR:

| mode | method | family_mean_auc_pr | class | type | GPU | tuning | released_zero_count |
|---|---|---|---|---|---|---|---|
| online | CNN | 0.34796 | Prediction | Forecasting | 1.00000 | 0.00000 | 0 |
| online | TimesNet | 0.34143 | Prediction | Reconstruction | 1.00000 | 0.00000 | 0 |
| online | MCD | 0.32581 | Density | Distribution | 0.00000 | 0.00000 | 0 |
| online | CBLOF | 0.31746 | Distance | Proximity | 0.00000 | 0.00000 | 0 |
| online | KNN | 0.31651 | Distance | Proximity | 0.00000 | 0.00000 | 0 |
| online | LSTMAD | 0.30961 | Prediction | Forecasting | 1.00000 | 0.00000 | 0 |
| online | FITS | 0.29392 | Prediction | Reconstruction | 1.00000 | 0.00000 | 0 |
| online | AutoEncoder | 0.26707 | Prediction | Reconstruction | 1.00000 | 0.00000 | 0 |
| online | TranAD | 0.26020 | Prediction | Reconstruction | 1.00000 | 0.00000 | 12 |
| online | OCSVM | 0.25803 | Density | Distribution | 0.00000 | 0.00000 | 0 |
| online | RobustPCA | 0.25409 | Density | Encoding | 0.00000 | 0.00000 | 0 |
| online | KMeansAD | 0.25408 | Distance | Clustering | 0.00000 | 0.00000 | 0 |
| online | PCA | 0.24318 | Density | Encoding | 0.00000 | 0.00000 | 0 |
| online | HBOS | 0.23980 | Density | Distribution | 0.00000 | 0.00000 | 0 |
| online | LOF | 0.23847 | Distance | Proximity | 0.00000 | 0.00000 | 0 |
| online | USAD | 0.22982 | Prediction | Reconstruction | 1.00000 | 0.00000 | 0 |
| online | OmniAnomaly | 0.22906 | Prediction | Reconstruction | 1.00000 | 0.00000 | 0 |
| online | IForest | 0.20027 | Density | Tree | 0.00000 | 0.00000 | 0 |
| online | AnomalyTransformer | 0.05838 | Prediction | Reconstruction | 1.00000 | 0.00000 | 0 |
| streaming | SWKNN | 0.35126 | Distance | Proximity | 0.00000 | 1.00000 | 0 |
| streaming | MemStream | 0.28245 | Density | Encoding | 1.00000 | 1.00000 | 0 |
| streaming | MCOD | 0.23088 | Distance | CLustering | 0.00000 | 1.00000 | 0 |
| streaming | LEAP | 0.19684 | Distance | Proximity | 0.00000 | 1.00000 | 0 |
| streaming | RSHash | 0.19394 | Density | Distribution | 0.00000 | 1.00000 | 0 |
| streaming | SDOstream | 0.17999 | Distance | Proximity | 0.00000 | 1.00000 | 0 |
| streaming | HSTree | 0.15426 | Density | Tree | 0.00000 | 1.00000 | 0 |
| streaming | LODA | 0.09004 | Density | Distribution | 0.00000 | 0.00000 | 0 |
| streaming | RRCF | 0.08417 | Density | Tree | 0.00000 | 1.00000 | 0 |
| streaming | xStream | 0.06025 | Density | Encoding | 0.00000 | 1.00000 | 0 |

Property-group summaries, averaging fixed method means within each property:

| mode | property | value | methods | family_balanced_method_mean_auc_pr |
|---|---|---|---|---|
| online | class | Density | 6 | 0.25353 |
| online | class | Distance | 4 | 0.28163 |
| online | class | Prediction | 9 | 0.25971 |
| online | GPU | 0.0 | 10 | 0.26477 |
| online | GPU | 1.0 | 9 | 0.25971 |
| online | tuning | 0.0 | 19 | 0.26237 |
| streaming | class | Density | 6 | 0.14418 |
| streaming | class | Distance | 4 | 0.23975 |
| streaming | GPU | 0.0 | 9 | 0.17129 |
| streaming | GPU | 1.0 | 1 | 0.28245 |
| streaming | tuning | 0.0 | 1 | 0.09004 |
| streaming | tuning | 1.0 | 9 | 0.19267 |

GPU, method capacity, class, normalizer policy, backend and tuning are strongly confounded. Nine Streaming methods carry tuning=1 while all19 Online rows have tuning=0; the latter means reuse of TSB hyperparameters, not “never tuned.” The source paper describes separate TSB tuning-set selection, not per-series test-label tuning. No independently published environment/run manifest seals the optimization history.

The fixed portfolio is an explicitly chosen analysis panel, not a fitted ensemble. Per-pair support and family values are fully emitted; method class means cannot certify that a whole algorithm class is intrinsically better. Streaming methods can update memory/counts/statistics while keeping encoder weights frozen; Online means fixed learned parameters in this task, not low-latency adaptation.

## Static→Online paired deltas

| method | online_minus_static_family_mean | fit_scope_comparable |
|---|---|---|
| IForest | -0.05637 | False |
| HBOS | -0.03982 | False |
| PCA | -0.03309 | False |
| LSTMAD | -0.02640 | True |
| OmniAnomaly | -0.02608 | True |
| AnomalyTransformer | -0.02299 | True |
| USAD | -0.01914 | True |
| KMeansAD | -0.01276 | False |
| AutoEncoder | -0.00132 | True |
| MCD | 0.00000 | True |
| OCSVM | 0.00000 | True |
| CNN | 0.00295 | True |
| CBLOF | 0.00332 | False |
| RobustPCA | 0.03057 | False |
| TranAD | 0.05236 | True |
| KNN | 0.09425 | False |
| FITS | 0.11197 | True |
| TimesNet | 0.12503 | True |
| LOF | 0.14056 | False |

LOF/KNN large positive deltas must be interpreted alongside full-series versus prefix-only fit. IForest/HBOS/PCA negative deltas have the same training-information asymmetry. TimesNet/FITS improvements cannot simply be assigned to drift adaptation; context/readout and batching change with no parameter update. AutoEncoder’s window configuration also differs. A zero MCD/OCSVM delta is preserved; no artificial effect is inferred.

Published TranAD Online13 zeros and Donut Static7 zeros are unresolved evaluation-quality flags. A finite AP with positive labels is ordinarily nonzero, and driver exception paths can insert zeros; exact failure cause is unavailable. We retain native scalar values, count flags, and keep them outside the primary fixed portfolio rather than silently treating zero as missing or declaring a model failure.

Neither fixed-method heterogeneity nor test-label oracle winner variation establishes a new model-selector/router contribution. No method is trained, rerun, tuned or selected for deployment.
