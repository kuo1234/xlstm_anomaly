# R0 protocol amendment r0-v1.1 — single-backend xLSTM scientific extraction

Machine-readable form: [`amendment_v1_1.json`](amendment_v1_1.json). The r0-v1 protocol
(`research/real-data-r0-protocol@d7708586`, [`protocol.md`](protocol.md), [`config.json`](config.json)) is unchanged
and remains authoritative for everything this amendment does not name. The v1 execution stop
([`execution.md`](execution.md), `runs/extract_machine-2-1_xlstm_22.json`,
`runs/diagnostic_parity_machine-2-1_xlstm_22.json`) is permanent history: **R0-v1 EXECUTION_BLOCKED occurred before
any label read by an execution stage and before any scientific result.**

Authorised by the owner's selection of Option 2 in the v1 stop record. Blocked v1 execution HEAD:
`4e743610e1a27b5c9ac5a894c77a629aa3f7a75f`.

## 1. Rationale (recorded before any further detector execution)

The v1 gate that failed compared two numerical implementations of the same trained xLSTM: the vanilla backend used
for training and the native CUDA sLSTM backend (built with `--use_fast_math`) used only for extraction. The failure
was one N(0,1)-canary reconstruction element outside the frozen tolerance. The result-blind diagnostic found
1 / 311,296 violating canary elements, 0 / 311,296 violating fit-window elements, bitwise observer on/off parity,
score agreement ≈ 3.6e-7 and common18 agreement ≈ 1.2e-7, using no labels and no test observations.

No R0 anomaly metric, probe metric, ΔAP or classification has been observed. v1.1 therefore is a result-blind
implementation amendment. It **removes the second numerical implementation** instead of redefining the failed
tolerance: training and scientific extraction now use one implementation, so cross-backend equivalence is no longer
part of the measurement.

## 2. New frozen xLSTM extraction rule

| | r0-v1 | r0-v1.1 |
|---|---|---|
| training backend | vanilla | vanilla (unchanged) |
| scientific extraction backend | native CUDA sLSTM overlay | **vanilla** |
| observer | `FastStateObserver` | **scalar reference observer** (`phase_e2_observer`, via `real_data_r0_models.extract_batch(model, "xlstm_reference", x)` / `extract_windows(model, "xlstm_reference", …)`) |
| backend label in records | — | `vanilla_reference` |

Reconstruction output, score, common18, history14, internal234, validation scores/threshold and detector-sanity
inputs all come from the vanilla/reference path. The CUDA overlay remains documented engineering history only; it
may not contribute any value to v1.1 caches, probe inputs or detector-sanity metrics. The runner replaces
`cuda_overlay_from_vanilla` / `build_xlstm_cuda` with raising stubs in every extraction process.

## 3. v1.1 xLSTM extraction gate (fail-closed)

On the N(0,1) canary (`[128,64,38]`, CPU generator seed 710) and on the first/last 64 fit-interval windows:
best.pt SHA256 = training record; model hash = training record; 75,934 parameters; eval mode; observer-off vs
observer-on reconstruction output **bitwise**; repeated vanilla inference **bitwise**; scalar reference observer
internal parity (hidden/state) passes; output, score and common18 finite; common18 shape `[N,18]`. On the test
stream: H = 14, internal234 = 234, 31 warm-up rows, first finite edge 94. Per-checkpoint causality is verified in
the v1.1 preflight. No label access, no metric call. The vanilla-vs-CUDA comparison is removed from the gating path
(its v1 result is preserved); any new CUDA comparison would be `NON_GATING_ENGINEERING_DIAGNOSTIC` (none is planned).

## 4. Checkpoints, caches and records

* **Reuse authorised, no retraining**: the six v1 xLSTM checkpoints (machine-1-8 and machine-2-1, seeds 11/22/33)
  with the best.pt SHA256 and model hashes listed in `amendment_v1_1.json`, including machine-2-1 / seed 22 (the
  failure concerned extraction only; training used the vanilla backend). No other checkpoint may be selected.
* **v1 CUDA caches invalidated**: the five v1 caches are retired by hash-checked rename to
  `features_v1_cuda_invalidated.npz` and recorded as `INVALIDATED_BY_R0_V1_1_EXTRACTION_AMENDMENT`
  (`runs/v1_cuda_cache_invalidation.json`). All six reused checkpoints are re-extracted from scratch.
* **v1.1 files**: `runs/extract_v1_1_<unit>.json`, git-ignored `data/r0_runs/<machine>/<backbone>_<seed>/features_v1_1.npz`,
  `feature_cache_manifest_v1_1.json`. Cache validation accepts only `protocol_version = r0-v1.1`, the registered
  backend (`vanilla_reference` for xLSTM, `lstm_manual_replay` for LSTM), the v1.1 file name, dimensions 14/234 and
  zero label reads; every v1 record fails it.
* **Matched LSTM**: training, extraction path (manual replay observer) and gate (observer on/off bitwise + replay
  parity) unchanged from r0-v1.

## 5. Unchanged

Datasets, machines, raw hashes, D=38, architectures and parameter counts, seeds, fit/validation split, W64, epochs,
optimizer, shuffling, checkpoint selection, scaler (no variance floor), Design-B blocks, 96-row embargo, H and
internal234 definitions, HGB family and {100, 300} budget, validation-only selection, probe label rules, both
bootstraps (10,000 draws, seed 901), classification thresholds, wording, claim boundary, detector-sanity metrics and
the DETECTOR_WEAK rule. The estimand is the same R0 estimand; v1.1 is not a new hypothesis.

Remaining training: machine-1-4 xLSTM seeds 11/22/33 and all nine matched-LSTM units (12); final total 18; at most
two concurrent detector processes. Sealing requires 18 passing training and v1.1 extraction records, nine
`vanilla_reference` xLSTM caches and nine LSTM caches, with the SHA256 manifest committed **and pushed** before any
label is read.

## 6. Red-team: is v1.1 an outcome-driven rescue?

| statement | evidence | true? |
|---|---|---|
| No SMD test label had been read before the amendment | No execution stage read a label: all 6 training and 6 v1 extraction records have `labels_read: false`; no probe or sanity record exists. The only label access in R0 history is the sealed r0-v1 protocol preflight, which read label *counts* per Design-B block (purpose `preflight_counts`) to confirm AP is defined; it used no model output, is disclosed in `preflight.md`, and carries no information about the extraction backend. | yes (with the disclosed protocol-stage count check) |
| No probe was fitted | 0 of 72 HGB fits; no `probe_*.json` | yes |
| No R0 AP/AUROC/ΔAP/classification observed | no `results.json`, `detector_sanity.json`; nothing computed | yes |
| Only training-validation MSE was available | run records contain train/validation reconstruction MSE on the original train split, and parity/diagnostic numbers | yes |
| The amendment changes implementation parity only | extraction backend/observer and the gate that compared backends; no estimand, feature, probe or statistic change | yes |
| Detector checkpoints are unchanged | reused best.pt SHA256/model hashes pinned in `amendment_v1_1.json` and re-checked by preflight and sealing | yes |
| Datasets/features/estimand/probe/statistics/claim boundary unchanged | sealed library and config SHA256 re-verified against `preflight.json` by the v1.1 preflight and tests | yes |

Classification: **`R0_V1_1_AMENDMENT_RESULT_BLIND_PASS`**.
