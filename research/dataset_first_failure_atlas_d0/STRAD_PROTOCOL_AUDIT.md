# D0 benchmark semantics audit

Static is retrospective full-series availability. Online fits an initial batch and performs sequential sliding-window inference with fixed learned parameters. Streaming may change execution memory/model/statistics. **Static→Online delta is not adaptation gain.** The [paper definitions](https://arxiv.org/html/2609.39215v1#S2.SS3) and actual wrappers must be distinguished.

Pinned [Static driver](https://github.com/magaliparrino/StrAD/blob/7078876bbd9398481a65c22b7689702ce9e0d558/exp/Run_Static_Detector_M.py) calls full-data fit for eight shared unsupervised methods (IForest, LOF, PCA, HBOS, KNN, KMeansAD, CBLOF, RobustPCA), while [Online wrapper](https://github.com/magaliparrino/StrAD/blob/7078876bbd9398481a65c22b7689702ce9e0d558/exp/online_model_wrapper.py) fits their initial prefix. Those comparisons change fit information, not merely how the same model is invoked. Other prefix-trained methods still can differ in context/readout; AutoEncoder additionally has ACF-derived Online window versus a fixed/default Static window. The results field fit_scope_comparable covers fit scope alone, not complete score parity.

The [Online driver](https://github.com/magaliparrino/StrAD/blob/7078876bbd9398481a65c22b7689702ce9e0d558/exp/Run_Online_Detector.py) uses stride1 Window3D, takes output[-1], and fills positions0..W−2 from output at W (the second available window-end target, not the first at W−1). [Streaming driver](https://github.com/magaliparrino/StrAD/blob/7078876bbd9398481a65c22b7689702ce9e0d558/exp/Run_Streaming_Detector_M.py) repeats this padding and separately backfills xStream window256. The full data are streamed after fitting the prefix and metrics receive the full label vector, including the initial region. This is not a strictly causal deployment score log.

| method | window_candidate | max_prefix_fraction | mean_prefix_fraction | declared_first_inside | historical_first_inside_75 |
|---|---|---|---|---|---|
| AnomalyTransformer | 50.00000 | 0.04471 | 0.00341 | 12 | 7 |
| AutoEncoder | unknown / unsupported | unknown / unsupported | unknown / unsupported | 0 | 0 |
| CBLOF | unknown / unsupported | unknown / unsupported | unknown / unsupported | 0 | 0 |
| CNN | 51.00000 | 0.04562 | 0.00348 | 12 | 7 |
| FITS | 100.00000 | 0.09033 | 0.00689 | 13 | 8 |
| HBOS | 1.00000 | 0.00000 | 0.00000 | 0 | 0 |
| IForest | 100.00000 | 0.09033 | 0.00689 | 13 | 8 |
| KMeansAD | 40.00000 | 0.03558 | 0.00271 | 12 | 7 |
| KNN | 1.00000 | 0.00000 | 0.00000 | 0 | 0 |
| LOF | 1.00000 | 0.00000 | 0.00000 | 0 | 0 |
| LSTMAD | 151.00000 | 0.13686 | 0.01044 | 14 | 8 |
| MCD | 1.00000 | 0.00000 | 0.00000 | 0 | 0 |
| OCSVM | 1.00000 | 0.00000 | 0.00000 | 0 | 0 |
| OmniAnomaly | 100.00000 | 0.09033 | 0.00689 | 13 | 8 |
| PCA | 100.00000 | 0.09033 | 0.00689 | 13 | 8 |
| RobustPCA | unknown / unsupported | unknown / unsupported | unknown / unsupported | 0 | 0 |
| TimesNet | 96.00000 | 0.08668 | 0.00661 | 13 | 8 |
| TranAD | 10.00000 | 0.00821 | 0.00063 | 7 | 4 |
| USAD | 100.00000 | 0.09033 | 0.00689 | 13 | 8 |

Window values are candidates from the independently pinned TSB HP dictionary6beac72 and inspected driver logic. The StrAD requirements leave TSB_AD unversioned, so no published environment proves those exact values generated each release row. AutoEncoder/CBLOF/RobustPCA use a training-ACF window: exact value unknown here, inspected function bound6..303. Missing windows stay unknown rather than guessed125. Report fractions as candidates, not exact historical run facts.

For candidate USAD W100,13 declared first anomalies lie in warm-up (TAO11,LTDB1,SVDB1);8 are confirmed by historical first-label evidence in the75 audited drift series. Candidate maximum padding fraction is9.03%; LSTMAD W151 reaches13.69%. Absence of positive labels in a prefix does not eliminate its influence on PR rankings: backfilled normal scores can change false-positive rank. Drop/N-A/first-available-score AUC-PR sensitivity is NOT_AVAILABLE without score vectors; no artificial metric values are invented.

[AdapterDSalmon](https://github.com/magaliparrino/StrAD/blob/7078876bbd9398481a65c22b7689702ce9e0d558/models/streaming/base_model_adapter.py) forwards the whole matrix to fit_predict. SWKNN receives overlapping64-row windows, and the no-model index trace passes each middle observation to the backend64 times. Last-point outputs could nevertheless equal a strict64-point window under some backend semantics; this trace proves replay/work count, **not an accuracy difference**. Internal timestamps/window semantics and real score parity remain unresolved.

[LEAP](https://github.com/magaliparrino/StrAD/blob/7078876bbd9398481a65c22b7689702ce9e0d558/models/streaming/LEAP.py) extracts the newest point and emits32 scores after a chunk fills. The index trace verifies score-index alignment, availability lag0..31 and an unscored tail remainder left at initialized zero. It does not prove that Java uses future points for each score, but delayed availability must be reported rather than called zero-latency scoring. Raw timing aggregation and batch/point equivalence are not published.

[PySAD adapter](https://github.com/magaliparrino/StrAD/blob/7078876bbd9398481a65c22b7689702ce9e0d558/models/streaming/base_model_adapter.py) uses fit_score_partial; PostProcessedModel explicitly fits the current point before scoring. [MemStream](https://github.com/magaliparrino/StrAD/blob/7078876bbd9398481a65c22b7689702ce9e0d558/models/streaming/MemStream.py) scores before admitted memory/statistics updates. MCOD invokes Java point-scoring routines; complete internal update order is not established from Python alone. There is no single verified score-before-update contract across all Streaming methods.

Primary numbers retain the official AUC-PR column. Audited TSB reference basic_metricor.metric_PR returns sklearn.average_precision_score, consistent with README examples. D0 does not substitute trapezoidal PR-AUC, VUS-PR or adjusted/event F1 for the released column; the reference calculation is AP, while the precise release dependency is unsealed. The dependency version and release score vectors remain unsealed, so we do not claim bitwise metric reproduction. Online TranAD has13 zeros and Static-only Donut7; source exceptions can substitute zeros. Those entries are unresolved data-quality flags, retained rather than silently recoded, and neither method is in the fixed portfolio.

All three archived/pinned drivers iterate only file_list[153]. They cannot as checked-in produce the180-row release without a launch/source change. Metric/time tables match the published archive, but no score/run manifest binds them to a complete execution. Score sensitivity and causal/padding attribution are therefore unresolved. We do not patch or rerun upstream models. See results/semantics_trace.json for the model-free fixture.
