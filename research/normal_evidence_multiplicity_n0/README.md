# N0 — normal evidence multiplicity counterfactual

Direct user authorization: independently design the next experiment and advance the research goal. This new normal-only experiment does not reopen the killed E1 lifecycle route or paused P5 target efficacy. No external reviewer GO or new-method novelty is claimed.

Question: with a frozen detector and fixed unique healthy calibration observations, can replaying one source's identical records change an operating threshold and materially alter false alarms on previously unseen normal runs?

Freeze before new scores: [protocol](configs/protocol.json), [test identities](configs/test_manifest.json), [pinned raw sources](provenance/raw_sources.json). E1 calibration/outcomes were exposed; the three new tests were selected before score generation. Original E1 PCA/LSTM weights/scaler/features remain unchanged. Source keys are trace identity plus timestamp. No fault labels, recall, lifecycle metrics, model tuning or retraining.

Arms: pooled row-weighted quantile, equal-trace mixture, identity-deduplicated pooled quantile. All use the same inverse empirical-CDF q.995. Duplicate each calibration trace by factors1/4/16/64; unique information stays fixed. Equal-trace/dedup invariance is a mathematical control, not itself an empirical success or a novel algorithm. Material empirical gate needs>=1IQR threshold range plus>=1 percentage-point unseen-test FPR spread in>=2 test traces for each of two families. Freeze/push before any new detector inference; never increase doses or select a favorable test after exposure.

Acquisition-only process reads native timestamps/selected features, checks Git blob SHA and archive/CSV/canonical-array SHA. Split ZIP is losslessly merged with `zip -s0`; component hashes remain separate. Raw/score arrays remain ignored. Existing fault data are not evaluated.

## Prior-art boundary

Weighted quantiles for covariate shift are established: [Tibshirani et al., Conformal Prediction Under Covariate Shift](https://arxiv.org/abs/1904.06019). [Wen et al., GC-FCP2026](https://proceedings.mlr.press/v337/wen26a.html) explicitly studies target group mixtures and stratified score aggregation. [Gao et al.2026](https://arxiv.org/abs/2605.14260) studies pooled cross-group distortion and calibration tradeoffs. These opened primary-source abstracts limit novelty: generic group balancing is ALREADY_EXPLICIT; whether exact provenance-preserving record replay exposes an actionable industrial ingest mechanism is UNRESOLVED. This is a bounded search, not full-text/global novelty clearance.

A normal-only improvement cannot establish anomaly detection utility or certified coverage, and three runs are not three independent physical machines. Target mixture assumptions, context mismatch and temporal dependence remain explicit. The overall research goal stays active unless a useful, independently replicated mechanism and defensible research residual are established.

Completed external replication: [RESULTS](RESULTS.md), [verification](provenance/verification.json), [interventions](results/intervention.csv). Gate NO_MATERIAL_EXTERNAL_EFFECT; overall objective remains active.
