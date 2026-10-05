# E1 execution seal — prospective

**GO only for the fixed PCA/SPE and CAUSAL_LSTM_REFERENCE panel after this seal is committed, pushed and remote-verified. No detector training/inference has run during seal construction.**

[Issue #26](https://github.com/kuo1234/xlstm_anomaly/issues/26) authorizes E1 independently of stopped M0/D0/E0 hypotheses. Historical results remain unchanged. This is causal score generation/lifecycle falsification, not method design.

19 raw traces across apps6/9/10:12 whole normal traces,6 primary-type disturbed traces,1 crash control. Selected strata: {'excluded': 79, 'primary': 24, 'secondary_crash': 2, 'negative_no_impact': 2, 'secondary_no_EEI': 2}. All109 GT events remain in [event manifest](configs/event_manifest.json), with selected/excluded reasons. Ground-truth SHA256: `9ddb86e96efb029b2530d4ef620fff5fa44a5d678ed1f8db955677f727e9453d`. Exact archive/blob/CSV/selected-column identities and prepared-array hashes are [raw audit](provenance/raw_audit.json). No anomaly score was used in selection.

Native1s, official19-feature definitions through a separately documented causal variant; no15s phase mixing. Global fit-only scaler. First duplicate row; integer timestamps retained; bounded forward fill only for histories/features; missing targets never receive primary scores. Initial missing values are unavailable. Same-time active executor averaging precedes fill.

Fixed seed21; PCA8 components; one-layer LSTM hidden32/history32, Adam1e-3,10epochs,128batch, norm-clip1; fit stride8/max8192 windows. Final epoch only, validation is diagnostic. No early stopping, sweep or anomaly model selection. C is excluded prospectively for unsealed native runtime compatibility; no replacement. [Complete protocol](configs/protocol.json).

Material effect: trace-macro median Delta_effect >=1 normal-calibration IQR in both families; each eligible type/app median positive; stationary event-balanced ramp<0.5IQR, excess-normal contrast>=1IQR, effect-only excess>=0.1 and>=50% complete RCI alarm events. Raw eligibility>=95% native phase score coverage, RCI>=30/EEI>=10/pre>=30 observations; at least50% selected events,2types/3apps, and>=5 matched normal controls for a majority. These are prospective engineering margins, not statistical guarantees.

Protocol bugs require STOP, pushed amendment and exposure disclosure before changed execution. Negative gates cannot authorize type/model/threshold/polarity changes. After results, commit/push/reply Issue and STOP.
