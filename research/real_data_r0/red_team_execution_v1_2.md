# R0 red-team — r0-v1.2 amendment and execution

Scope: the final implementation amendment r0-v1.2 ([`protocol_amendment_v1_2.md`](protocol_amendment_v1_2.md)) and
the completed R0 execution under it ([`execution.md`](execution.md), r0-v1.2 section). Every answer below cites a
committed record.

## 1. Amendment red-team (answered before execution, re-checked against the records afterwards)

| question | answer | evidence |
|---|---|---|
| 1. Had any execution-stage SMD label been read? | **No.** | Every v1/v1.1 training and extraction record has `labels_read: false` / `label_read_count: 0`; no probe or sanity record existed before `2842198`; the sealed manifest records `execution_stage_label_reads_before_seal: 0`. The r0-v1 protocol preflight's per-block label counts remain the only earlier label access. |
| 2. Had any detector AP/AUROC been observed? | **No.** | `detector_sanity.json` was first written in `6a1b5aa`, after `results.json`. |
| 3. Had any HGB probe been fitted? | **No.** | The first `runs/probe_*.json` appear in `b55eacc`. |
| 4. Had any ΔAP matrix been computed? | **No.** | `results.json` first appears in `4bb2b5b`. |
| 5. Was the amendment chosen from a scientific outcome? | **No.** | It responds to the r0-v1.1 implementation-parity stop (`57eb5d8`); only train-split reconstruction MSE and parity diagnostics existed. |
| 6. Does v1.2 change dataset, labels, H, internal234, probe, estimand or statistics? | **No.** | The sealed library / config SHA256 values were re-verified by the v1.2 preflight (`sealed_design_probe_statistics_unchanged: true`); only the matched-LSTM recurrence implementation and its nine fits changed. |
| 7. Were all nine xLSTM results frozen before the amendment? | **Yes.** | Checkpoint, model-hash, cache and record SHA256 values are pinned in `amendment_v1_2.json` (`2c1677c`), re-verified by the preflight and at sealing. |
| 8. Is the old LSTM seed-11 result excluded because the implementation changed, not because of its validation MSE? | **Yes.** | `runs/v1_1_native_lstm_invalidation.json` applies to the native checkpoint regardless of its values; all nine LSTMs were retrained under v1.2. |

**Verdict: `R0_V1_2_AMENDMENT_RESULT_BLIND_PASS`.**

## 2. Execution integrity

| check | result |
|---|---|
| Amendment, implementation, tests and preflight committed and pushed before any LSTM training | PASS — `2c1677c` → `776a1cf` → `1f6f4ab` → `5ba3218` → `cc3e69a`; the nine unit commits (`7d5e458` … `fe1afd0`) all follow `cc3e69a` |
| v1.2 preflight status | `R0_V1_2_READY_TO_RESUME`, 13 / 13 |
| Native LSTM absent from the scientific path | PASS — static AST test (no `LSTM` / `LSTMCell` / `replay` / `Observer` / `build_lstm` call in the runner or the auditable module) and runtime guard in every training/extraction process; `native_predict_calls: 0` in every v1.2 training record |
| Nine auditable LSTM units | 9 / 9 PASS (74,100 parameters; v1.2 gate bitwise; finite; gates in [0,1]; H 14 / internal234 234) |
| At most two concurrent detector processes | PASS (`schedule --workers 2`) |
| xLSTM identities at seal | 9 / 9 re-verified; backends `vanilla_reference` (xLSTM) / `auditable_manual_v1_2` (LSTM) |
| Manifest committed and pushed before the first label read | PASS — sealed 09:30:58Z (`2842198`, pushed in the same job); first probe label read 09:31:37Z in a later job; the probe refuses to run unless the manifest is committed clean and pushed |
| Label reads | 54 in the probe (18 fit/selection + 36 final evaluation, one per arm per cell); 3 in detector sanity (one per machine) after `results.json` was committed |
| Probe inputs equal the sealed caches | PASS — every probe record's `feature_cache_sha256` equals the manifest; `results.json` carries the manifest SHA256 |
| Aggregation reproducible | PASS — recomputing both matrices from the probe records and rerunning the sealed bootstraps (10,000 draws, seed 901) locally reproduces every mean, count and interval bound exactly |
| Stage ordering (probe → aggregate → commit → sanity → report) | PASS — `b55eacc` → `4bb2b5b` → `6a1b5aa` → `1c75c51`, each pushed |
| Gate failures, retries, substitutions, tolerance changes | none |

## 3. Adversarial reading of the result

* **Could the null be an implementation artefact?** The matched LSTM passed bitwise capture/repeat/forward gates and
  the float64 equation tests; the non-gating comparison shows the auditable recurrence reproduces native `nn.LSTM`
  to 1.49e-8 with identical parameters. The xLSTM caches passed the v1.1 reference-observer gates. Both backbones
  give the same classification.
* **Is `R0_NO_RESOLVED_INCREMENT` being read as "no effect"?** It must not be. Five of nine cells are positive in
  each backbone, the means are positive and the intervals are wide; the frozen rule requires both interval lower
  bounds > 0 and ≥ 7 / 9 positive cells.
* **Is the positive part real-data recurrent-state utility?** Not established. All six positive-only cells come from
  machine-1-4, whose scores are dominated by the disclosed near-constant channel 17 (identical recall / FPR at
  threshold across all six detectors). The increment there may reflect compensation for a degenerate score.
* **Would a different choice have changed the class?** Not examined and not permitted: the scaler, probe budget,
  blocks, embargo and wording map are frozen; no re-analysis, subset, alternative scaler or extra seed is authorised.
* **Backbone comparison?** None is made; the matrices are parallel measurements.
* **Relation to P1r / L1c-P?** None: different data, no observable control beyond score/history. P1r remains terminal.

## 4. Residual risks disclosed

* Three machines and three seeds: exploratory intervals only.
* Design B is within-machine; anomaly composition differs between blocks (window-positive rows per block are listed
  in `scientific_assessment.md`), which limits stability of any within-machine increment.
* The sealed scaler has no variance floor (near-constant channels on machine-1-4 and zero-variance channels on
  machine-1-8 shape the scores); this was disclosed before execution and is not repaired.
* The matched LSTM is an auditable reimplementation rather than native cuDNN/PyTorch `nn.LSTM`; it is reported under
  its methods label.

Execution verdict: **`SMD_R0_V1_2_COMPLETE`** — both backbones `R0_NO_RESOLVED_INCREMENT`. ZERO_SHOT_NOT_STARTED.
