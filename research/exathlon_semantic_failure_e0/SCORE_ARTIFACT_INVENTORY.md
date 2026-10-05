# Official score-artifact inventory

Search scope: immutable untruncated default-branch trees, official release APIs, README links and original reproducibility notebook. Exathlon and DIVAD have no GitHub releases/assets at audit time. No native per-trace score arrays, thresholds, checkpoints or machine-readable AD1–AD4 output tables were found in these snapshots. This is a bounded public-artifact search, not a claim private/external outputs do not exist.

| repo | tree_entries | truncated | score_or_model_files | notebook_cells_with_output |
|---|---|---|---|---|
| exathlon | 242 | False | 0 | 0 |
| divad | 188 | False | 0 | 0 |

The Exathlon notebook computes trace_scores and reads locally generated evaluation CSVs/models; its code cells have no saved output. A reproducible generation recipe is not a released score bundle. Published PDF figures and aggregate/type F1 or peak-PR values cannot reconstruct event-level score continuity, normal trace scales, first alarm or RCI-vs-EEI contrast. Prior-art external repo searches also found no admissible native score manifest: see PRIOR_ART_OVERLAP.md and provenance.

Original [AE reconstruction readout](https://github.com/exathlonbenchmark/exathlon/blob/4101f6087f902fa150e392b65c957976faa84e40/src/scoring/reconstruction/reconstruction_scorers.py) averages scores of enclosing windows back onto each member record. Interior targets depend on later window ends. The inspected method is executed only against constant dummy window scores in scripts/readout_trace.py: W40,N100 gives future availability up to39 steps, and its actual tail division leaves the last constant-input readout at0.025 rather than1. This is a source-readout fixture, not a detector inference, a released score reproduction or a measured artifact contribution. The native 15s default could multiply step latency if that configuration generated the result; no manifest seals it.

Native LSTM prediction is statically implemented but has its own warmup/target alignment. DIVAD TranAD provides a right-edge window scorer but the base wrapper applies EWMA and masked warmup; its published peak F1 uses test labels. Neither is automatically admissible under E0 causal raw-score/normal-only threshold requirements. AE enclosing-window score and original future fills cannot be relabeled as zero-latency early alarms.

Missing required bundle: raw native identity/hash; original t and score target; available_at; complete unpadded raw scores; normal fit/validation/calibration/heldout-normal trace membership; preprocessing/source/checkpoint hashes; fixed architecture/window/training seed/budget; unsupervised threshold provenance; every event and separate RCI/EEI masks. Score arrays with only transformed TSB indices or union labels are insufficient.

A bounded rerun is scientifically required to answer the model-failure question when such a bundle cannot be recovered. Conditional candidate panel (maximum4): native Exathlon AE, native LSTM, DIVAD PCA, DIVAD TranAD. No baseline is selected by observed anomaly performance. Existing runtime is Python3.12 arm64 without TensorFlow/torch in the bundled analysis environment; native requirements differ and include unpinned dependencies. This probe is not a proof of impossibility and does not substitute for runtime parity.

This Commit-A protocol freezes the audit and measurement contract, **not a training execution manifest**. No bounded run executes from guessed preprocessing, unsupported native runtime or incomplete raw feature/split seal. Resolving those contracts needs a concrete execution amendment; arbitrary toy retraining or a private PyTorch imitation would not answer the requested native/representative failure comparison. Training remains NOT_RUN; the final evidence branch must retain this limitation.
