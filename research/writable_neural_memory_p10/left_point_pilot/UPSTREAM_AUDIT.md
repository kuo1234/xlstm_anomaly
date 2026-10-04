# Pinned upstream audit

Official repo DezhengWang/Left, commit3fadb4811797075e233076b9faceb0d8ec59b697. Hashes in upstream_manifest.json. Read full models/Left/LEFT.py and scoring Tools; anchors PSM/SMD changed enc_in only. Import package on remote, no vendored alternate LEFT loss.

Forward returns official alpha_cycle_l*loss_cycle+alpha_ms_l*loss_ms+alpha_cons_l*loss_cons. Inference combines smoothed weighted time/frequency/gate/cross-path cycle map with aggregated multi-scale reconstruction map. Instrumentation appends a component dictionary before original return, keeping original arithmetic/order intact; parity required.

Moving average uses symmetric replicate padding WITHIN input192window. Endpoint has no real sample aftert: rightpadding replicates endpoint, including SMD smooth51. STFT reflective centering/MS spectral processing uses whole pastwindow, no outsidefuture. Endpoint wrapper discards all earlier timestamp outputs; no cross-window future averaging. Official noncausal fullwindow earlier outputs never primary.

Prototype EMA only when training=True; eval returns lambda_max regardless training step. Warmup1000/ramp2000 is therefore a real support concern. Pre-register minimum3000optimizer steps before choosing checkpoint; otherwise an eval full-mixing model may not have trained the intended mixing mechanism. This changes training/checkpoint scheduling only, not official loss/model/score. CUDA float32 random-tensor forward/backward/infer smoke passed both anchors; torch2.13 differs pinned requirements1.10, so feasibility rather than exact published reproduction.

LEFT prototype buffers remain frozen during event inference, never treated as P10 normal-reference memory. Check state_dict before/after inference and future modifications.

Primary PSM seq192 nFFT64/win32/hop16, smooth3, alpha_cycle_s/ms_s=.5/.5. Sensitivity SMD seq192 nFFT128/win128/hop16, smooth51, cycle/ms=.2/.8. Preserve all values. No alpha/layer/frequency tuning.

[Paper v2](https://arxiv.org/html/2602.08638v2) motivates timestamp multiview scoring (Section3.7); it does not demonstrate safe benign adaptation. Mapping paper terms to exact pinned implementation takes precedence over assumed terminology.
