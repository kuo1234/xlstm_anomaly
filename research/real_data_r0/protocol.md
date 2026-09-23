# R0 — source-native real-data recurrent-state measurement validation (SMD)

Protocol `r0-v1`. Frozen before any R0 detector is trained, any probe is fitted or any R0 performance number exists.
Base: `main@b7ae44fafc4e9ea6671647c5cb73156ddaf26e5e` (post-P1r consolidation).
Machine-readable form: [`config.json`](config.json). If this document and the
config disagree, the config governs and the disagreement is a protocol defect that blocks execution.

## 1. Question and primary contrast

R0 asks an external-validity question: **does the recurrent internal-state measurement show additional
anomaly-predictive/decodable utility over causal score/history on source-native real multivariate telemetry?**

Primary contrast, per unit: `ΔAP_real = AP(H + internal234) − AP(H)`.

R0 is a real-data replication/transfer of the *measurement phenomenon* (claim rung L1d, see
[`claim_boundary.md`](claim_boundary.md)). It does not test, and cannot support, any of: internal state carrying
information absent from observations; internal state beating a complete observable representation; xLSTM
superiority; real benign-drift detection; safe online adaptation; deployment readiness. P1r (synthetic
observable-control ladder, terminal) and R0 answer different questions; a positive R0 result does not contradict P1r
and R0 does not attempt to rescue L1c-P.

No P1r/O1r feature family is ported to D=38 and no other observable baseline (PCA, raw-input HGB, MLP, …) is added.
The only arms are `H` and `H+I`.

## 2. Data (frozen)

Exactly three source-native SMD machines (OmniAnomaly `7fb0e0acf89ea49908896bcc9f9e80fcfff6baf4`), chosen before any
detector result and never replaced:

| machine | role | train_N | test_N | D |
|---|---|---:|---:|---:|
| machine-1-8 | historical strict Phase-A anchor | 23698 | 23699 | 38 |
| machine-2-1 | historical strict anchor; provenance independently rechecked | 23693 | 23694 | 38 |
| machine-1-4 | real-data feasibility work; prelisted M2N2-overlap analysis | 23706 | 23707 | 38 |

Raw bytes: original `train/`, `test/`, `test_label/` text files only; SHA256 identities are frozen in the config and in
[`dataset_manifest.json`](dataset_manifest.json); acquisition in [`data_acquisition.md`](data_acquisition.md). CANDI
preprocessed pickles and any transformed copy are forbidden inputs. Train splits are *documented* normal (upstream
has no train labels; not independently label-verified). Labels support anomaly-versus-nonanomaly evaluation only; no
drift, new-normal, transition or mixed labels are derived from SMD.

## 3. Streams, windows and labels

* Original train and test are **separate streams**. No window straddles the original train/test boundary, and no
  training/validation window straddles the fit/validation boundary.
* W64, stride 1, right-edge decision timestamp; every window is processed from fresh zero recurrent state.
* Test decision rows: right edges `t ∈ [63, test_N)`. `H` and `internal234` use causal rolling widths 4/8/16/32 over
  the chronological test row stream, so rows `63…93` are warm-up (non-finite) and are excluded everywhere; the first
  finite feature row is `t = 94`. The receptive field of a finite feature row is observations `[t−94, t]` (95).
* **Primary label: window-any-anomaly** `y(t) = max(label[t−63 … t])` on the original test split, matching the
  repository common causal track. No point adjustment. Endpoint point labels are not analysed in R0; point and window
  metrics are never mixed.

*Resolved convention conflict.* The Phase-A seal lists a `concatenated_test_interval` in concatenated
train+test coordinates. R0 does **not** concatenate: it keeps the original separation required by M0 L38. The only
consequence is that the first 94 test points are warm-up; this is label-independent and fixed now. The Phase-A
fit/calibration intervals are reproduced exactly (preflight check `phase_a_seal_agreement`).

## 4. Detector design (frozen; not yet trained)

* **Split of the original train split** (M0 L42 convention, identical to the Phase-A intervals):
  `fit_end = floor(0.8·train_N)`; fit `[0, fit_end)`, detector validation = calibration `[fit_end, train_N)`.
  `fit_end` = 18958 / 18954 / 18964 (1-8 / 2-1 / 1-4). Fit windows: right edges `[63, fit_end)`; validation windows:
  right edges `[fit_end+63, train_N)`.
* **Scaler**: per machine, fit interval only; float64 per-channel mean and population std; an exact-zero std becomes
  1 (sealed Phase-F convention); transform in float64 then cast to float32; applied unchanged to validation and test.
  No test value or label can move it (preflight `scaler_fit_only`). Near-constant fit channels are retained
  unchanged under this rule (see §12).
* **Backbones × seeds × machines**: xLSTM and capacity-matched LSTM; seeds 11, 22, 33; three machines →
  **18 detector fits**, each trained only on its own machine's fit windows.
* **Training contract** (Phase F-v4 contract with D=38): MSE reconstruction over aligned B×W×D; Adam
  (lr 1e-3, betas 0.9/0.999, eps 1e-8, no weight decay); batch 128; 50 epochs; every epoch uses
  `default_rng(SeedSequence([seed, epoch, 1701])).permutation(n_fit_windows)` over all fit windows including the
  final partial batch; no early stopping, scheduler, clipping, autocast or accumulation; checkpoint = lowest
  whole-validation MSE, earliest epoch on exact tie. Seeds set (python/numpy/torch/cuda) immediately before model
  construction. Backend state = F-v3 (`cudnn.deterministic`, no benchmark, highest matmul precision, TF32 off,
  4 torch threads); the matched LSTM runs with cuDNN disabled inside its LSTM stack.
* **xLSTM (D=38)**: official xLSTMAD pin `e8b56ba27352733bb83729e85b1d6196dca70c99`, xlstm 2.0.5, lightning 2.6.1,
  `xLSTMAD(embedding_dim=40, features_no=38, window_size=64)`, sLSTM dtypes float32, vanilla backend for training.
  **Trainable parameters: 75,934** (D=8 was 73,504; only `input_projection.weight`, `output_projection.weight/bias`
  depend on D). Extraction uses the validated native CUDA sLSTM overlay with weights mapped from the vanilla
  checkpoint (`map_vanilla_weights`), built in a dedicated JIT directory.
* **Matched LSTM (D=38)**: `Linear(38,w) → 3 encoder + 3 decoder nn.LSTM(w,w) → GELU → Linear(w,38)` with the F-v3
  module names. Repository rule: width with parameter count nearest to the xLSTM count, required within ±10%, exact
  tie → smaller width. Resolved **w = 38, 74,100 parameters (−2.415%)**; neighbours w=37: 70,375, w=39: 77,921.
  w = 38 is also the only width the sealed LSTM observer replays, so the observer binds unchanged.
* **Calibration threshold** (diagnostic only): `numpy.quantile(validation-window scores, 0.95)`; used only for the
  detector-sanity recall/FPR; it never enters the probe.
* Builders: `scripts/real_data_r0_models.py` (the audited D-parameterised counterparts of the sealed D=8 builders).
  No online adaptation, no test-informed architecture, budget or threshold choice.

## 5. Features (unchanged definitions)

Per trained detector, on the test stream:

* `H = history14` (`phase_g1_core.history14`): current score, first difference, and causal mean/std/slope over
  widths 4/8/16/32 of the scalar window reconstruction MSE.
* `common18` at the right-edge timestep: xLSTM via `phase_e2_fast_observer.summarize_fast` (reference
  `phase_e2_schema.summarize`); LSTM via `phase_f_lstm_observer.summarize`.
* `internal234 = phase_g1_core.expand_internal234(common18)` (feature-major: value + mean/std/slope at 4/8/16/32).
* xLSTM and LSTM expose the identical 14 + 234 external schema. Labels never enter any extraction API.

## 6. Probe design — Design B (within-machine blocked diagnostic)

**Selected from the representation-comparability audit alone** ([`internal_feature_transfer_audit.md`](internal_feature_transfer_audit.md)):
`common18` contains no raw hidden coordinates and is invariant to hidden-unit permutations, but 4 of the 18 base
statistics (hidden mean, hidden std, memory mean, memory std → 52 of 234 columns) depend on learned per-unit
polarity, which is an exact non-identifiability of the LSTM (demonstrated on the D=38 network) and is not fixed by any
constraint in the xLSTM; in addition every statistic's operating point is instance-specific. Not every feature has
the same semantic meaning across independently trained machine-specific detectors, so the precondition for
Design A fails. Design B keeps detector identity fixed within each probe task.

**Design B is an offline, within-machine, supervised measurement diagnostic. It is not unseen-machine transfer.**

For every machine and every trained detector, over eligible test rows `t ∈ [94, test_N)`, with
`L = test_N − 94`, `c1 = 94 + ⌊L/3⌋`, `c2 = 94 + ⌊2L/3⌋`:

| block | right edges |
|---|---|
| probe-train | `[94, c1)` |
| embargo | `[c1, c1+96)` |
| probe-validation | `[c1+96, c2)` |
| embargo | `[c2, c2+96)` |
| probe-test | `[c2+96, test_N)` |

The embargo (96 = repository `PURGE`) exceeds the complete feature receptive field (95), so no observation, W64
window, rolling-history row or window-any label window is shared between blocks. Equal thirds were fixed without
inspecting label positions (maximin block size). Label counts were inspected only to confirm AP is defined in every
block (see [`preflight.md`](preflight.md)); boundaries are never moved.

**Decoder** — exactly the frozen bounded HGB family of the nonlinear/P1r line
(`HistGradientBoostingClassifier`: log_loss, lr 0.1, max_leaf_nodes 31, max_depth 6, min_samples_leaf 100,
l2 1.0, max_bins 255, no early stopping, random_state 901, no class weight), `max_iter ∈ {100, 300}`. For each arm
independently: fit both candidates on probe-train only; select by probe-validation AP only; exact tie → 100;
compute probe-test predictions, freeze the selection record, then request probe-test labels exactly once and
compute probe-test AP once. No refit. No feature scaler (HGB is invariant to per-feature monotone transforms within
one detector; no statistic of any block transforms features). No other decoder or budget.
3 machines × 3 seeds × 2 backbones × 2 arms × 2 candidates = 72 HGB fits.

## 7. Estimand and exploratory uncertainty

Cell = one (machine, detector seed, backbone): `ΔAP = AP_test(H+I) − AP_test(H)`. Per backbone a 3 machines × 3 seeds
matrix. Report all 9 cells, the mean, machine means, seed means and the positive-cell count.

* **Two-way bootstrap**: 10,000 replicates, `default_rng(901)`; per replicate draw 3 machine rows then 3 seed columns
  with replacement; statistic = mean of the resampled 3×3 matrix; interval = 2.5/97.5 percentiles.
* **Machine-only bootstrap** (conditional on observed seeds): fresh `default_rng(901)`, 10,000 replicates, resample 3
  machine rows; interval = 2.5/97.5 percentiles.

With three machines and three seeds both intervals are coarse and exploratory; neither may be called a calibrated
population 95% CI. xLSTM and LSTM are reported side by side; their difference is not an estimand.

## 8. Predeclared wording map (per backbone)

| class | rule | permitted wording |
|---|---|---|
| `R0_POSITIVE_INCREMENT` | two-way lower > 0 AND machine-only lower > 0 AND ≥ 7/9 positive cells | "Recurrent internal-state features retain additional anomaly predictive/decodable utility over causal score/history in the tested source-native SMD within-machine diagnostic." |
| `R0_NO_RESOLVED_INCREMENT` | every other outcome | "R0 does not resolve additional real-data predictive utility of internal state beyond score/history under the frozen diagnostic." |
| `R0_NEGATIVE_INCREMENT` | two-way upper < 0 AND machine-only upper < 0 AND ≤ 2/9 positive cells | reported directly as a negative increment |

Every statement carries "Design B, exploratory uncertainty, not unseen-machine transfer". Never claim from R0:
information unavailable in raw input; contradiction of P1r; xLSTM superiority; benign-drift discrimination;
cross-domain generality; deployment validity; online-adaptation value.

## 9. Detector-sanity report (diagnostic context only)

Per machine × backbone × seed on all test rows `t ∈ [63, test_N)` with the window-any label: AP and AUROC of the raw
score, unadjusted recall and FPR at `score > threshold`, window-any prevalence. A detector with AUROC ≤ 0.55 is
flagged `DETECTOR_WEAK`; its cells are retained. These numbers never select seeds, backbones, machines or cells.

## 10. Execution order and fail-closed rules

1. `real_data_r0_data.py verify` must pass (9/9 hashes) — else `DATA_PROVENANCE_BLOCKED`.
2. Train 18 detectors (train split only; no label file opened). Record per-run manifest, curves, selected epoch,
   checkpoint and model hashes.
3. Per checkpoint: re-run the observer parity canary (vanilla reference vs CUDA fast observer, observer on/off
   bitwise) on a fixed N(0,1) batch and on fit-interval windows; any failure stops execution.
4. Extract score + common18 on validation windows (threshold) and on the full test stream; seal feature caches with
   SHA256 **before any label is loaded**.
5. Probe stage: build blocks, load labels (purpose-gated), run §6 selection/evaluation, §7 estimand, §8 wording.
6. Detector-sanity report (§9) after the probe matrix is sealed.

Stop (no substitution, no rescue) on: any hash mismatch; non-finite observation, score or feature after warm-up;
observer parity failure; parameter-count drift; a block without both classes; any label access before step 5.
A nearly non-functional detector is not a stop condition.

## 11. Recorded prospectively: R1

R1 = HAI 22.04 distinct-domain (ICS/SCADA) replication with source-native attack labels. R1 is not part of R0. Its
execution depends only on successful acquisition, provenance and schema/model compatibility — never on the R0
outcome.

## 12. Known, disclosed properties (not rescue levers)

* **Near-constant fit channels.** Channels with exact-zero fit std are left unscaled (1-8: 8 channels, 2-1: 5, 1-4: 6).
  Some non-zero-std channels are almost constant in the fit interval (machine-1-4 channel 17: std 1.69e-5 from 11
  deviating rows; machine-2-1 channel 17: std 1.52e-3). Under the sealed rule their scaled test values reach
  |x| ≈ 5.9e4 (1-4), 6.6e2 (2-1) and 2.0e2 (1-8), so reconstruction scores on those machines may be dominated by one
  channel. This is a train-split property observed before any model result; R0 keeps the sealed convention rather
  than introducing a new variance-floor parameter. It affects `H` and `H+I` of the same detector identically at the
  input and is reported alongside the detector-sanity table.
* **Few positive events per block.** Window-any positive rows per block range 138–1,518 but come from 2–8 anomaly runs,
  so each probe-test AP rests on few events; this is why uncertainty is exploratory.
* **Same-machine supervision.** Design B probes learn and are tested on one machine's anomaly repertoire; results
  are within-machine measurements only.
