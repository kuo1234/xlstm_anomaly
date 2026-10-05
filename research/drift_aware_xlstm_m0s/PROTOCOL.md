# M0-S v1 — pre-result protocol freeze

Authority: [Issue #23](https://github.com/kuo1234/xlstm_anomaly/issues/23), **GO for controlled mechanism falsification only**, and the user's instruction to complete experiments. This is a separately authorized encoder-only predictive track. It does not reinterpret old H3b, revive Safe Admission, or alter historical M0 outcomes. Commit A must contain this protocol, all executable generator/model/training/evaluation/gate code and tests; push and verify its remote SHA before any optimizer update or scientific outcome inspection. Commit B records outcomes. No post-outcome change to difficulty, architecture, seeds, L, metrics, amplitude, thresholds or excluded groups.

## Fixed scope

D=8. Three primary mechanisms (mean, dynamics, correlation), each with five physical process groups and three model seeds 11/22/33. Each `(mechanism,group)` gets its own xLSTM and matched LSTM trained on equal stationary A/B support: **90 full-budget training runs**. Group transformations are reused across mechanisms; scientific N=5 within each mechanism, not 15 pooled independent sources, 90 models, or overlapping windows. There is no GRU, periodic reset, learned trigger, parameter TTA, real data, controller or novelty experiment.

The authoritative machine-readable choices are in [configs/protocol.json](configs/protocol.json). The generator group seeds and every sample address are deterministic; no rejection/resampling by observed moments or performance. Formal stationarity/finite covariance and disjoint addresses are checked before results. The variable group spectral radii, dynamics-B coefficients and mean magnitudes make groups different processes, rather than only relabeled copies. Correlation-only construction retains identical marginal means/variances and transition operator. [GENERATOR.md](GENERATOR.md) states the exact equations and splice limits.

## Training / support contract

Encoder-only xLSTM E16, two blocks `[sLSTM,mLSTM]`, four heads, causal kernel4, no extra FFN; input D→E, stack, linear E→D one-step head. Scalar backend vanilla float32, automatic mixed precision disabled. Matched LSTM has two layers H20, same D→E projection, H→E linear readout and E→D head. Counts 6,832 and 7,016, difference 2.69%. Both use identical balanced normal sample tensors, objective, horizon, batch order seeds, 30 epochs, 120 Adam updates, lr0.002, no weight decay, global gradient clipping1.0. Matching capacity does not equate inductive bias or wall time.

Per regime: 64 training sequences ×128, 16 validation sequences ×128, 16 independent calibration sequences ×256. No state crosses a training or validation sequence boundary. Train-input position t predicts x[t+1], valid output positions t=7..126 (120 targets/sequence after 8 observed points). Every epoch is run; select lowest balanced stationary validation forecasting MSE, earliest exact tie. Test/anomaly labels cannot affect checkpoint selection. Frozen channel scaler is fit once to all balanced training observations only. Every held-out model uses its own train-fitted scaler; within its comparison the scaler/checkpoint/threshold are identical across arms. Data hashes and checkpoint raw-byte hashes are retained.

**B-support gate precedes incompatible-history inference.** On compatible B-prefix→B-suffix, calculate mean standardized one-step MSE over all 256 suffix points, paired with last-value, trailing32 moving mean, and ridge0.001 linear VAR(1) trained on normal B training segments only (including an unpenalized intercept). B-trained AR is an evaluator diagnostic, not a regime oracle given to the recurrent model. A seed passes if recurrent MSE ≤0.98×min(last-value,moving-mean) **and** ≤1.25×B-AR MSE. A group requires ≥2/3 seeds. A mechanism requires ≥4/5 support groups in **both** backbones; otherwise `MODEL_SUPPORT_INSUFFICIENT` for that mechanism and no incompatible-history/AD interpretation. All groups/seeds, including failures, remain reported. Other predeclared mechanisms may finish independently; failure does not authorize easier data or more training.

These adequate-fit margins are prospective engineering choices. They avoid declaring state staleness when a same-weight compatible forecast is inadequate; passing is only operational task adequacy, not complete model identification. [MODEL_CONTRACT.md](MODEL_CONTRACT.md) specifies full state and exact forecast timestamps.

## Paired histories and interventions

Eight test realizations per group. Equal prefixes128; common suffix256. Independently sampled A-prefix and B-prefix both connect to the **same exact** B suffix. This prevents a privileged stochastic correlation between compatible prefix and the suffix. The primary suffix is a controlled stationary splice, not a claim of a physically continuous switching VAR. Also retain A-prefix→common A-suffix and separately sampled physically continuous A/A and B/B controls. Never feed generator IDs, labels or boundary truth to the forecaster.

KEEP carries complete state, COMPATIBLE_B_HISTORY carries the B prefix, and ORACLE_BOUNDARY_RESET discards complete state before ingesting suffix x0. The x0 forecast was already issued from the old prefix and is scored identically to KEEP; RESET affects x1 onward. Boundary information belongs to the evaluator arm schedule, not a deployable method. No backdating or rescore.

FIXED-L={8,32}: reconstruct each forecast from fresh state with exactly the last L observations **strictly before** its target. Replay may intentionally consume past inputs repeatedly, unlike persistent arms. Count/charge that extra context compute; data availability is identical, compute is not. At suffix k≥L, compatible/incompatible replay predictions must be bitwise identical on the same backend because their complete input windows are identical. Full replay uses native forward and must pass full/step parity; neither state nor parameters are optimized at test.

## Fixed quantities / gates

Definitions and per-point units are in [METRICS.md](METRICS.md). Primary offset interval is **[32,64)**; both L controls and actual recent suffix values are identical there, and the native conv horizon4 has been exceeded. Early bins [0,8),[8,16),[16,32) and late bins [64,128),[128,256) remain descriptive. No peak/bin selection for GO.

For each seed, normalize paired loss differences by the compatible B KEEP mean MSE in [32,64). `H` = incompatible KEEP−compatible KEEP; `R` = incompatible KEEP−oracle RESET. Material harm H≥0.05; oracle recovery R/H≥0.50 (undefined if H≤0). Physically continuous stationary A/A **and** B/B deterioration KEEP−RESET must each be ≤0.05 of that regime's compatible KEEP primary MSE. Long-context benefit over [32,256) is (FIXED-L−compatible KEEP)/compatible KEEP≥0.02 for **each** L. Same seed must jointly pass support/harm/recovery/stationary; ≥2/3 jointly passing seeds per group and ≥4/5 qualifying groups are required. Separate seed witnesses may not be combined.

Context truncation suffices if some predeclared L achieves replay-minus-reset≤0.02 (primary MSE-normalized) **and** compatible replay-minus-KEEP≤0.02 in ≥2/3 seeds of ≥4/5 groups. The claim of unique reset value is withheld when short context matches these effects. Without that control match or a verified long-context advantage, the explicit conservative category is `STATE_STALENESS_INCONCLUSIVE_CONTEXT_CONTROL`, not positive evidence.

xLSTM-specific signal additionally requires xLSTM-minus-LSTM group-mean H≥0.03 in ≥4/5 groups. Architecture-neutral category requires LSTM pre-AD signal in ≥4/5 groups and absolute paired harm gap<0.03 in ≥4/5 groups. These operational equivalence/difference bands do not prove statistical equivalence or novelty. No iid p-values or bootstrap is planned; report physical-group median/range/signs, each model-seed result and every offset curve/censoring result.

## AD extension and kill hierarchy

AD runs only for mechanisms with ≥4/5 xLSTM groups passing the **joint pre-AD gate** (support, harm, oracle recovery, stationary controls). It runs all five groups, both backbones and all three seeds; no deletion of difficult groups. If no mechanism qualifies, write `NOT_RUN_GATED`, not fabricated anomaly outcomes.

Independent observation-only injections: spike1, short collective8, long collective32; onset0/32/96, two fixed-seed-selected channels, signed magnitude4×train channel std. The same design applies to both A and B target suffixes so event attributes are not bound to the regime class; no anomaly enters latent process, training, validation or calibration. Eighteen fixed conditions per run, all retained. Paired history/intervention arms share the exact contaminated suffix. Frozen alarm threshold is calibration-only 95th percentile of normal residuals after warmup; the same threshold across all arms. Report point AP (not trapezoidal PR-AUC), event recall, normal FPR/alarms per1000, missed anomalous points after reset and mean anomaly-score attenuation.

Any one prespecified AD condition with RESET−KEEP AP<−0.02, event recall<−0.10, or missed anomaly-point rate>+0.10 in ≥2/3 seeds of ≥4/5 groups triggers `RESET_HARMS_ANOMALY_DETECTION`. All conditions are reported; this is a conservative descriptive kill gate, not an uncorrected inferential significance claim. Current score before reset is immutable.

Per-mechanism precedence: insufficient support → `MODEL_SUPPORT_INSUFFICIENT`; fewer than4 joint pre-AD xLSTM groups → `NO_STATE_STALENESS_SIGNAL`; replicated AD harm → `RESET_HARMS_ANOMALY_DETECTION`; matching context control → `CONTEXT_TRUNCATION_SUFFICES`; incomplete long-context gate → `STATE_STALENESS_INCONCLUSIVE_CONTEXT_CONTROL`; neutral/specific comparisons as above → `ARCHITECTURE_NEUTRAL_STALENESS` / `XLSTM_SPECIFIC_SIGNAL`; otherwise complete gates → `STATE_STALENESS_SUPPORTED`. Overall headline uses prespecified priority in summarize.py, while always retaining every per-mechanism verdict. Any broken state, suffix, causal, provenance or label-isolation invariant instead yields `PROTOCOL_FAIL` and STOP; no scientific interpretation, repair or automatic rerun after outcomes.

## Execution and costs

Pre-result random/no-label checks: deterministic covariance/stability, disjoint split addresses, parameter counts, full/step and chunk carry parity, snapshot serialization, conv reset negative control, future-prefix invariance, batch partition/permutation, exact recent replay equality, predicted-before-ingestion timestamps, event/metric unit checks and frozen parameters/buffers. Repeat random state audit on each selected trained checkpoint before held-out support evaluation. Existing source paths remain unmodified.

Chosen execution environment: existing `kuo` host, Linux GB10 machine, but **CPU float32**, one thread per worker, three workers for independent training/support/AD runs; mechanism evaluation serialized. Existing Python3.12 environment has torch2.13.0+cu130, xlstm2.0.5, numpy1.26.4. CUDA availability does not mean CUDA use. Local CPU preflight uses Python3.14/torch2.9 and records its different environment. Required xlstm source hash pin is checked on execution host. No dependency upgrade is required.

Hard caps: 180 seconds per training run, 14,400 seconds total compute process wall time. Exceeding a cap stops with evidence; never change budget after seeing held-out outcomes. Full training is 90×120 optimizer steps, 128 normal sequences/run; estimated premeasurement envelope <2 CPU hours, **not a measured throughput claim**. The existing historical ≤160 GPU-hour envelope is not approached; this CPU controlled track is separately authorized by #23. No scientific training/pilot before Commit A remote confirmation.

Exact commands after pushing Commit A and verifying `git ls-remote`:

```sh
# On the clean isolated remote checkout at Commit A, with seal stored outside it:
export M0S_FREEZE_SEAL=/tmp/m0s-issue23-remote-freeze.json
M0S_PY=/home/p76141495/home/xlstm_anomaly/data/phase_e2/venv/bin/python
$M0S_PY -m unittest discover -s research/drift_aware_xlstm_m0s/tests -v
$M0S_PY research/drift_aware_xlstm_m0s/scripts/run.py --artifacts data/m0s-v1 --output research/drift_aware_xlstm_m0s/results
$M0S_PY research/drift_aware_xlstm_m0s/scripts/summarize.py --results research/drift_aware_xlstm_m0s/results --report research/drift_aware_xlstm_m0s/RESULTS.md
```

The external seal records Commit A plus every frozen file hash and verified remote ref SHA. `verify_freeze()` checks that SHA, all code/config hashes and installed upstream hashes before every worker stage. Ignored data stores raw checkpoints; tracked JSON stores full selection/update logs, input/checkpoint hashes and full per-offset quantities. Preserve failures in provenance; do not run another directory to hide failure. Commit B adds results/figures/report, source provenance and terminal logs. Push/verify, reply to Issue, then **STOP for reviewer** regardless of outcome.
