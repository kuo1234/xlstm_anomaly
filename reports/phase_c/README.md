# Phase C — C1 INVESTIGATE; reproduction expansion stopped

Official commit: `28c9679e503832f59e351208cde63657fcb51cad`. A1/A2/B remain accepted. This delivery does NOT claim full C1/C2 completion or authorize Phase D.

## Official native reproduction

Untouched official Python modules executed through main.py with each author script's exact arguments, seed0, released pretrained checkpoint, native preprocessing, W=10/stride1, batches256, both hard/moderate FPM, MIN_SAMPLES16, native SANA/SGD and counters. TRAIN.ENABLE=False is the author's default when the supplied checkpoint directory exists. No backbone retraining occurred; SANA test-time gradient updates DID run on GPU. No xLSTM/LSTM/probe/H4/Phase D run occurred.

The working directory is a separate fresh run directory with data/checkpoint symlinks; official checkout receives no outputs or bytecode. A wrapper observes Predictor after completion to save metrics/state/memory; it does not alter its control flow or calculations. Native configuration before Predictor's documented loader overrides is saved in each run's config.txt; resolved Predictor config is in runs/*.json. Official repository status and source hashes are reverified. Checkpoint hashes and all output hashes are recorded. Large checkpoints/arrays stay under ignored data/phase_c/runs; logs/configs/hashes are committed.

Native metrics use window-any anomaly truth, sklearn roc_auc_score and **trapezoidal PR-AUC**, not average precision, no point adjustment. Published values below are Table1 of [the paper](https://arxiv.org/html/2604.01845v1). Thresholds use validation percentile 100-alpha; no test-best threshold.

| Machine | alpha | Published AUROC / PR-AUC | Observed AUROC / PR-AUC | Absolute discrepancy |
|---|---|---|---|---|
| 1-8 | 0.5 | .872 / .432 | .852404 / .438389 | .019596 / .006389 |
| 1-8 | 1 | .872 / .434 | .853212 / .438938 | .018788 / .004938 |
| 1-8 | 5 | .867 / .423 | .868101 / .449996 | .001101 / **.026996** |
| 2-1 | 0.5 | .725 / .319 | N/A | NOT RUN: stop gate |
| 2-1 | 1 | .711 / .314 | N/A | NOT RUN: stop gate |
| 2-1 | 5 | .780 / .348 | N/A | NOT RUN: stop gate |

The alpha5 discrepancy exceeds .02, so native expansion stopped immediately. Five-seed replication was NOT allowed. Remaining machine/alpha combinations must not be presented as reproduced using upstream cached arrays.

## Investigation — paper and released artifacts disagree

Read-only investigation recomputed native metrics on the **author-committed cached** outputs, explicitly separate from our observed runs. Their 1-8 alpha5 PR-AUC is also about .4500, not paper .423; their static PR-AUC is .367750 versus paper .332. Local alpha1/5 closely match those caches, but alpha0.5 differs from its cached result. Checkpoint epoch29/config and upstream output hashes are in upstream_cache_investigation.json and logs/*checkpoint_config.txt. Cached run configs include TRAIN.ENABLE=True; the default supplied-checkpoint rerun uses False, so author training-time RNG history may differ. This is a plausible contributor, not proven root cause. No RNG/config adjustment, retraining or test tuning was attempted.

Evidence supports a paper-versus-release lineage mismatch; it does not establish which checkpoint, training run, or environment produced the paper table. Exact original dependency environment is not published in a root requirements/lockfile. Resolving that provenance requires author artifact clarification or a separately reviewed investigation, not quietly changing the .02 gate.

## Independent audit — bounded to 1-8 alpha5 seed0

The official adapter accepts test_labels for diagnostic counts. The independent label-isolation overlay deletes ONLY those diagnostic reads/increments and strips the argument before adapter construction. Full exact diff and generated overlay are under overlays/. FPM, masks, queues, MIN_SAMPLES, losses, update steps and official ordering remain unchanged. This is an audit variant, not a compatibility patch or replacement baseline. Native code still receives labels for its unchanged counters and does not satisfy a literal label-free API contract.

Stable window ID is the zero-based native test window start. Whole-batch scores precede adapt; availability is the last window's endpoint. Latency is commit-batch last-window ID minus selected-window ID, including batch waiting. Observers record selection and queue admission separately (identical in this implementation), commits at actual loss entry, optimizer exposures/steps, hashes after every step and batch, pending tails, and hard/moderate queues. Raw anomaly coverage uses evaluator-only raw labels. Full IDs/buffers/timing in logs/*audit_events.json; no oracle affects adaptation.

| Queue | Candidate anomalies / windows | Committed anomalies / windows | Gradient anomalies / exposures |
|---|---|---|---|
| Hard | 237 / 1275 (18.5882%) | 237 / 1275 (18.5882%) | 237 / 1275 (18.5882%) |
| Moderate | 199 / 9747 (2.04165%) | 199 / 9746 (2.04186%) | 199 / 9746 (2.04186%) |
| Total | 436 / 11022 (3.95572%) | 436 / 11021 (3.95608%) | 436 / 11021 (3.95608%) |

101 updates and 101 optimizer steps; no repeated exposures (native STEPS=1 here); one moderate window pending. Unique raw anomaly coverage531 timestamps. Zero-exposure rates are null, never decontamination evidence. This confirms natural admission in one run, NOT five-seed H1-admission and NOT causal H1-harm.

Runtime bookkeeping discrepancy: last batch length138, actual offset23552; native iter*len(scores) gives12696. One selected moderate window23629 is counted using label12773. Both happen normal here, so the total anomaly count is unchanged despite the incorrect ID. Official moderate admission counter9747 also differs from actual committed9746; it counts queue admissions, not optimizer use.

Other risks: Q1-Q3 moderate test mask is overwritten by scores<threshold (validation moderate reference remains Q1-Q3). USE_FPM=False returns before iter increment (static inspection only; alternate algorithm not run). Representation path applies current sana_in before frozen encoder and L2 normalization; query representation is not adaptation-invariant. Scaler is fitted on initial80% of native training, transforms val/test; no online refit. TRAIN_RATIO>=1 test-as-validation fallback exists but is inactive. Configured gradient-clip flag is not called by adapt loop. None was fixed.

## Label isolation / parity

Unpermuted and independently evaluator-permuted audit replays use identical observations/model/RNG. Exact comparisons cover scores, candidate/commit IDs, timing, every optimizer-step model hash, every batch model hash, final state and all recorded events. Evaluator contamination changes as expected. Permutation occurs only evaluator-side after stream execution by construction; no true or permuted label enters the isolated adaptation API.

Native versus isolated audit has bitwise-equal scores and final model-state hash. Native intermediate trajectories were not instrumented; no claim of complete native intermediate-state comparison. Diagnostic anomaly counters intentionally differ in the overlay. The result establishes invariance for the label-isolated audit path, not that the official API itself is label-free. No label-permutation behavior failure was observed.

## Environment, runtime and scope

NVIDIA GB10, driver580.173.02, CUDA13.0, PyTorch2.13.0+cu130, Python3.12.3. Separate system-site-packages venv added yacs/wandb/reformer-pytorch to satisfy imports; full resolved versions in environment.json. W&B disabled; no external telemetry. No algorithm compatibility patch was needed. Do not call this an exact recreation of the unpublished author dependency environment.

Native three-run measured spans: 11.0372s,10.8471s,11.1751s (~33.06s total). Audit and permutation add ~30.40s; total measured execution ~63.46s, excluding process startup and later serialization. Peak torch GPU allocation2,709,062,656 bytes (~2.52GiB), reserved3,586,129,920 bytes (~3.34GiB) across all runs. CUDA event spans include host gaps, not summed kernel-active time. GB10 nvidia-smi reports memory usage unsupported, so allocator measurements are explicitly labeled. Per-process wall time, stdout/stderr and launch commands are preserved separately.

Run `rtk data/phase_c/venv/bin/python scripts/phase_c_finalize.py` for fresh parity/count/source verification, then `rtk sha256sum -c reports/phase_c/SHA256SUMS`. Existing run directories/logs are protected against overwrite. Native launch expansion is guarded by recorded status; do not remove evidence to bypass it.

**Phase D is not scientifically ready:** C1 tolerance gate unresolved, second-machine native/C2 work incomplete, five-seed replication locked. Return this INVESTIGATE report for external review; no contamination intervention or later branch is started.
