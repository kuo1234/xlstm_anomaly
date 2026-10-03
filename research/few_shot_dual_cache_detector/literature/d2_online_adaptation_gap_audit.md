# Gap Audit — Direction 2: Safe Long/Short-Memory Online Adaptation for Multivariate Forecasting on Machine Data

**Date:** 2026-09-29. **Scope:** verified literature search (arXiv API, OpenAlex API with stored key, Crossref via OpenAlex, IJCAI/OpenReview direct fetch) across the 8 sub-areas named in the task, with full text read for the 9 closest competitors. All papers listed in `d2_papers.json` were confirmed via at least one live lookup; `verification_level` records how far that confirmation went (`full_text` / `abstract` / `metadata_only`). Two placeholder "search_gap_marker" records in `d2_papers.json` document negative-result query sets — they are not papers.

## 1. Candidate design under audit

Frozen "slow" forecaster (long-term memory) + small "fast" state/adapter updated online from ground truth that arrives **H steps late**; a **gate** decides when the fast memory may override the slow one; **transient faults/anomalies must not be learned**; an evaluation protocol with **no information leakage**, on **machine/industrial multivariate data**.

## 2. Gap verdicts

### G2a — Realistic H-step label delay in online-TSF evaluation
**Verdict: PARTIALLY_OCCUPIED**

This is no longer an unrecognized problem — it is the explicit subject of an active, recent sub-line. FSNet (2022) and OneNet (2023) — the two canonical "fast-and-slow" / online-ensembling forecasters — "used (X_{t-1}, Y_{t-1}) in their official implementations, while the practical strategy is to use (X_{t-H}, Y_{t-H}) without information leakage", per Proceed's direct analysis of both codebases. Proceed (KDD-track, arXiv:2412.08435) states the problem directly: online forecasters "overlook a critical issue: obtaining ground-truth future values of each sample should be delayed until after the forecast horizon... This delay creates a temporal gap between the training samples and the test sample", and Proceed's own ablation shows using the leaky (X_{t-1},Y_{t-1}) update roughly **halves** measured error relative to the correct (X_{t-H},Y_{t-H}) update — i.e. the leakage is not a minor artifact, it materially inflates reported gains. A concurrent ICLR 2025 paper (Lau, Shao & Yeung, "Fast and Slow Streams for Online Time Series Forecasting Without Information Leakage") independently made the same fix via pseudo-labelling the unobserved horizon. PADRE (IJCAI 2026) then explicitly builds on the corrected protocol: "Beyond Uniform Updates: Drift Pattern Aware Online Time Series Forecasting under Delayed Feedback", stating it "strictly adhere[s] to the practical online forecasting protocol defined in proceed".

What remains open: (i) FSNet/OneNet's leaky numbers are still the reference baselines cited by much of the wider online-TSF literature, so the correction has not fully propagated; (ii) every paper that fixes the leakage (Proceed, the ICLR'25 paper, PADRE) evaluates exclusively on generic multivariate benchmarks (ETT, Electricity, Traffic, Weather) — none extends the corrected protocol to industrial/machine multivariate streams, and none couples the delay-correctness question to an anomaly-vs-drift distinction. The general streaming-ML literature has an older, non-forecasting-specific treatment of the same idea (Grzenda, Gomes & Bifet, "Delayed labelling evaluation for data streams," DMKD 2019), which the TSF-specific line does not appear to cite or build on directly — a possible missed cross-community link.

**Blocking/anchor papers:** FSNet (arXiv:2202.11672), OneNet (arXiv:2309.12659), Proceed (arXiv:2412.08435), Fast-and-Slow-Streams (ICLR 2025, OpenReview I0n3EyogMi), PADRE / "Beyond Uniform Updates" (IJCAI 2026).

**Queries run:** "online time series forecasting label delay leakage evaluation"; "concept drift online time series forecasting benchmark evaluation protocol 2025"; "delayed feedback online learning forecasting drift pattern aware"; "information leakage online time series forecasting evaluation critique"; "fast and slow learning online time series forecasting without information leakage".

---

### G2b — Learned/statistical GATE for adapt/freeze/rollback, evaluated via "adaptation harm"
**Verdict: PARTIALLY_OCCUPIED**

Gating exists, but nowhere in the form specified (discrete adapt/freeze/rollback decision, evaluated by a headline "adaptation harm" metric — cases where adapting made things worse than not adapting). PADRE's Prompt-Guided Update Policy "queries P online and outputs a continuous update gate γt ∈ (0, 1) to modulate the online gradient step" — this is a soft, continuously-valued brake on the SAME backbone's gradient step, not a discrete choice among "adopt fast state / stay on slow state / roll back to a previous checkpoint," and PADRE reports only aggregate MSE plus a component-ablation table, not an adaptation-harm metric. TAFAS (AAAI 2025) also gates an aggregation of adaptation candidates but again optimizes and reports only aggregate accuracy. The clearest evidence that "adaptation can actively hurt" is diagnosed, not gated: "Towards Principled Test-Time Adaptation for Time Series Forecasting" (arXiv:2605.17250) shows empirically that "the adjusted prediction of the first sample is generally inferior to the direct prediction of the last sample... across multiple datasets, forecasting horizons and frozen source forecasters" — i.e., naive TTA calibration is shown to sometimes be actively worse than simply not adapting — but the paper's own fix (Frequency-Aware Calibration) is a fixed lightweight correction module, not a learned gate that can choose to freeze or roll back. The adjacent vision-domain TTA literature (e.g. "When Test-Time Adaptation Helps, Harms, or Becomes Inactive," arXiv:2608.22233; "To Adapt or Not to Adapt?", arXiv:2609.08367 — both already mapped in the user's prior-art survey) does frame a three-way helps/harms/inactive outcome space, but for image classification, not forecasting, and not with rollback semantics.

**Blocking/anchor papers:** PADRE/"Beyond Uniform Updates" (IJCAI 2026), TAFAS (arXiv:2501.04970), "Towards Principled Test-Time Adaptation for Time Series Forecasting" (arXiv:2605.17250).

**Queries run:** "adaptation harm test-time adaptation when not to adapt"; "selective update online learning forecaster reject rollback"; "gated online adaptation forecasting safety".

---

### G2c — Explicit slow(frozen)/fast(adapter) split with principled arbitration for forecasting
**Verdict: PARTIALLY_OCCUPIED**

Components exist separately but not combined. PETSA (arXiv:2506.23424) is architecturally the closest: it keeps the pretrained forecaster frozen and learns small, parameter-efficient correction modules updated online — an explicit slow/fast split — but has no arbitration rule beyond "always apply the learned correction," no notion of H-step delay, and no anomaly-robustness treatment. LEAF (IJCAI 2025, "Learning to Extrapolate and Adjust") is the closest *conceptual* macro/micro-drift split — "an extrapolation stage to address stable, long-term macro-drifts... and an adjustment stage that responds to unpredictable, short-term" drift — but this operates on a compressed latent embedding of the model's own parameters via meta-learning, not a literal frozen backbone plus a separate small state module, has zero occurrences of "delay" in the text (does not address H-step label delay), and is evaluated only on ETT/Electricity. Titans (arXiv:2501.00663) has the cleanest neuroscience-inspired long-term/short-term memory framing and a genuine test-time-updated memory module, but it is a general sequence-modeling architecture (language, genomics, a minor generic time-series benchmark) — not built or evaluated for industrial forecasting under delayed feedback, and its "surprise"-based update rule is not shown to reject transient anomalies specifically.

**Blocking/anchor papers:** PETSA (arXiv:2506.23424), LEAF/"Learning to Extrapolate and Adjust" (IJCAI 2025), Titans (arXiv:2501.00663), FSNet (arXiv:2202.11672, the original "fast and slow" framing).

**Queries run:** "Titans learning to memorize at test time"; "test-time training layers sequence modeling"; "fast weight memory neural network sequence"; "Learning to Extrapolate and Adjust concept drift online forecasting".

---

### G2d — Protection of online forecaster updates against transient faults/anomalies, on machine data
**Verdict: OPEN_AT_SEARCH_DEPTH**

No paper was found that (a) is an online/continually-updated multivariate forecaster, (b) explicitly protects its parameter updates from being corrupted by transient anomalous/faulty points in the incoming stream (as opposed to genuine drift), and (c) evaluates this on machine/industrial sensor data. PADRE's tri-view consistency score is conceptually adjacent — it is designed so that "errors stemming from measurement noise, outliers, or unseen drift mechanisms yield inconsistent multi-view signals", which lowers its update gate — but this is demonstrated only on generic energy/traffic/weather benchmarks, with no labeled anomaly/fault ground truth to actually measure whether the gate correctly rejects faults versus genuine drift. Adjacent literature found: generic time-series anomaly-detection surveys, and adaptive soft-sensor work (see G2c/soft-sensor discussion below) that discusses robust/trimmed windowing but not a learned gate distinguishing fault from drift for a modern online neural forecaster.

**Queries run:** "robust online learning forecaster anomaly contaminated updates"; "anomaly resilient online time series forecasting outlier robust update"; "robust test-time adaptation forecasting outliers corruption"; "soft sensor concept drift industrial process monitoring 2024 2025".

---

### G2e — Systematic zero-shot TSFM vs. online-adapted small models on long-horizon (months–years) machine-data drift
**Verdict: OPEN_AT_SEARCH_DEPTH**

Time-series foundation models (TimesFM, Chronos/Chronos-2, Moirai, TiRex/TiRex-2) are an active area with many application-specific benchmarking papers (electricity price, load forecasting, wildfire PM2.5, financial returns, etc. — see `d2_papers.json` "foundation_model" category, all located via search), and TiRex-2 (arXiv:2607.01204) explicitly targets "streaming" settings, which is the closest hit. However, no paper was found that runs a controlled, long-horizon (multi-month-to-multi-year) degradation comparison between (i) a zero-shot/in-context foundation-model forecaster and (ii) a small online-adapted model (e.g. FSNet/OneNet/Proceed/PADRE-style), specifically on industrial/machine sensor data with a real deployment-length time axis. Existing TSFM-vs-industrial-data papers benchmark short-horizon accuracy snapshots (e.g. short-term household/grid load), not the multi-year drift-degradation regime the thesis is motivated by.

**Queries run:** "time series foundation model degradation drift industrial"; "TiRex time series foundation model xLSTM"; "Chronos-2 time series foundation model"; "Moirai universal time series forecasting foundation model"; "in-context fine-tuning time series foundation model forecasting".

---

## 3. Closest competitors (full text read)

| # | Paper | Venue/Year | What it does | What it leaves open |
|---|---|---|---|---|
| 1 | **Proceed** — Proactive Model Adaptation Against Concept Drift (arXiv:2412.08435) | KDD-track 2024/25 | Names and fixes the FSNet/OneNet label-delay leakage; proactively adapts parameters from the last fully-observed (X_{t-H},Y_{t-H}) pair via a hypernetwork | No gate (always adapts), no anomaly-robustness, no machine data |
| 2 | **PADRE / "Beyond Uniform Updates"** (IJCAI 2026) | 2026 | Tri-view drift consistency score + continuous update gate γ_t∈(0,1) modulating the gradient step under H-step delay | Gate is a soft scalar on the whole backbone, not adapt/freeze/rollback; no machine data; no labeled anomaly ground truth |
| 3 | **LEAF** — Learning to Extrapolate and Adjust (IJCAI 2025) | 2025 | Two-stage meta-learning: macro-drift extrapolation + micro-drift adjustment in a latent parameter-embedding space | No H-step delay handling at all; no literal frozen-backbone+adapter split; no machine data |
| 4 | **PETSA** — Accurate Parameter-Efficient TTA for TSF (arXiv:2506.23424) | 2025 | Frozen forecaster + small online-updated low-rank/spectral correction modules | No delay analysis, no gate/arbitration, no anomaly-robustness, no machine data |
| 5 | **TAFAS** — Battling Non-stationarity via TTA (AAAI 2025, arXiv:2501.04970) | 2025 | Gated aggregation of multiple test-time adaptation candidates for a frozen forecaster | Gate optimizes only for accuracy; standard benchmarks only |
| 6 | **"Towards Principled TTA for TSF"** (arXiv:2605.17250) | 2026 | Empirically shows TTA calibration can be worse than no adaptation; proposes frequency-domain fixed correction | No learned gate/rollback; no adaptation-harm metric as such; no machine data |
| 7 | **FSNet** — Learning Fast and Slow (arXiv:2202.11672) | ICLR 2023 | Original neural "fast" (memory-driven per-layer adapter) + "slow" (backbone) online forecaster | Its official protocol leaks future ground truth (X_{t-1},Y_{t-1}); no gate; no machine data |
| 8 | **OneNet** — Online Ensembling under Concept Drift (arXiv:2309.12659) | NeurIPS 2023 | Online convex ensembling of cross-time/cross-variable predictors with bandit-style weight updates | Same leakage issue as FSNet; ensembling ≠ a slow/fast memory split; no machine data |
| 9 | **Titans** — Learning to Memorize at Test Time (arXiv:2501.00663) | 2024/25 | Neural long-term memory trained online via a surprise-gated update rule + short-term attention memory | Built for general sequence modeling; minor generic TS benchmark only; no delay/anomaly/machine-data treatment |

## 4. Recommended thesis framing

The label-delay-leakage problem (G2a) is real but is being actively closed by a 2024–2026 line (Proceed → concurrent ICLR'25 fix → PADRE) — a thesis cannot claim novelty for "handling H-step delay" alone. What is consistently and jointly absent across every closest competitor found is: **(1) a literal frozen-slow-backbone + small-fast-adapter/state architecture** (PETSA has the frozen+adapter shape but no delay-correct protocol or gate; PADRE has the delay-correct protocol and a gate but modulates the whole backbone, not a separate small state), **(2) a discrete, evaluable gate (adapt / freeze / roll back)** whose quality is measured by an explicit "adaptation harm" metric (fraction/magnitude of cases where adapting made forecasts worse than freezing) rather than aggregate MSE alone, **(3) any evaluation on labeled machine/industrial multivariate data where transient sensor faults can be distinguished from genuine regime drift**, and **(4) a long-horizon (multi-month/year) comparison against zero-shot foundation-model forecasters** to justify that the added complexity of an online-adapted small model earns its keep over just deploying a frozen TSFM. Recommended framing: position the thesis explicitly as filling this specific intersection — cite Proceed/PADRE for the delay-correct protocol (adopt it, don't re-derive it), cite PETSA/LEAF/Titans for the architectural precedents (adopt/adapt their slow/fast split), and contribute the gated-with-rollback arbitration mechanism plus an industrial-fault-aware, leakage-free, long-horizon evaluation protocol as the delta. The soft-sensor / just-in-time-learning process-industry literature (Perera et al. 2023 review; Urhan & Alakent 2020; Bakirov et al. 2016) should be explicitly engaged as related prior art for "when to update" triggers — reviewers from a process-control background will otherwise flag this as unacknowledged prior art on the "gate" idea, even though that literature does not use deep slow/fast neural architectures or label-delay-correct protocols.

## 5. Baselines with public code

- FSNet — https://github.com/salesforce/fsnet
- OneNet — https://github.com/yfzhang114/OneNet
- Proceed — https://github.com/SJTU-DMTai/OnlineTSF
- TimesFM — https://github.com/google-research/timesfm
- Chronos — https://github.com/amazon-science/chronos-forecasting
- Moirai — https://github.com/SalesforceAIResearch/uni2ts

(PADRE, LEAF, PETSA, TAFAS, "Towards Principled TTA," and Titans did not expose a code URL in the fetched text/metadata at time of search — check for camera-ready/author-page releases before committing to them as baselines.)

## 6. Main threats to the proposed thesis direction

1. **Fast-moving overlap window.** PADRE (IJCAI 2026) was published within the last search cycle and already combines delay-correct protocol + drift/outlier-aware consistency gating; a thesis committee will expect explicit differentiation from it, not just citation.
2. **Baseline correctness risk.** Any comparison that re-uses FSNet/OneNet's official code inherits their label-delay leakage; results must be regenerated under the corrected (X_{t-H},Y_{t-H}) protocol or they will not be defensible against Proceed/PADRE's critique.
3. **Cross-community prior art.** The process-industry adaptive soft-sensor / just-in-time-learning literature has practiced "when to update" gating for over a decade (pre-dating deep learning); failing to cite it invites a "this already exists" objection even though the mechanisms differ (classical JITL/PLS vs. deep slow/fast memory).
4. **Machine-data availability for the anomaly-vs-drift distinction.** Per the project's own real-data feasibility audit, no acquired public multivariate dataset currently carries a labeled drift-vs-anomaly estimand — the exact evaluation axis G2d/G2e require may need to be constructed (semi-synthetic fault injection on top of a real machine dataset) rather than found off-the-shelf.
5. **Foundation-model moving target.** TSFMs (Chronos-2, TiRex-2) are being updated every few months with explicit streaming/multivariate extensions; a "zero-shot vs. online-adapted" comparison risks being outdated by the time of thesis defense unless the comparison protocol (not a specific model snapshot) is the contribution.
