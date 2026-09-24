# R0 v1.1 red-team (amendment and execution)

## A. Is r0-v1.1 an outcome-driven rescue?

| statement | evidence | true? |
|---|---|---|
| No SMD test label had been read before the amendment | No execution stage read a label (all v1 training/extraction records `labels_read: false`; no probe or sanity record). The only label access in R0 history is the sealed r0-v1 protocol preflight's per-block label *count* check (purpose `preflight_counts`), disclosed in `preflight.md`, which used no model output. | yes (protocol-stage count check disclosed) |
| No probe was fitted | 0 / 72 HGB fits; no `probe_*.json` | yes |
| No R0 AP/AUROC/ΔAP/classification observed | none computed then or since | yes |
| Only training-validation MSE was available | plus parity/diagnostic numbers; all train-split or canary quantities | yes |
| Amendment changes implementation parity only | xLSTM extraction backend/observer and the backend-comparison gate | yes |
| Detector checkpoints unchanged | six reused best.pt SHA256/model hashes pinned in `amendment_v1_1.json`, re-verified by preflight and every v1.1 extraction | yes |
| Datasets/features/estimand/probe/statistics/claim boundary unchanged | sealed library/config SHA256 equal the v1 `preflight.json` values (v1.1 preflight check, v1.1 test 6) | yes |

Classification: **`R0_V1_1_AMENDMENT_RESULT_BLIND_PASS`**.

## B. Execution under v1.1

| check | finding | status |
|---|---|---|
| Protocol HEAD unchanged | `research/real-data-r0-protocol` = `d7708586`; v1 protocol, config, library and preflight byte-identical | OK |
| v1 history preserved | v1 stop record, failed parity record, v1 diagnostic, six v1 training records and v1 extraction records unchanged; `execution.md` only gained a top note and appended sections | OK |
| All three machines retained | yes; nothing dropped | OK |
| No retraining of reused checkpoints | six reused units have no new training record; v1.1 extractions cite their original best.pt SHA256 | OK |
| All v1 CUDA caches invalidated, none mixed | five retired by hash-checked rename; all nine v1.1 xLSTM records name `features_v1_1.npz` and `vanilla_reference`; validation rejects every v1 record | OK |
| CUDA overlay never contributed | raising stubs in every extraction process; preflight recorded 0 overlay calls | OK |
| No labels before sealing | no label-reading stage ran; every v1.1 extraction record `label_read_count = 0` | OK |
| Checkpoint gate for every extracted detector | 9/9 xLSTM PASS; 1 LSTM gate PASS but test-stream observer parity FAIL → stop | OK (stop applied) |
| Engineering incident | CLI status line used a retired key after two successful extractions; fixed in `12b14e6` (status line only) before resuming; records untouched | disclosed |
| No weak detector removed / no scaler repair | not reached / sealed scaler unchanged (machine-1-4 channel 17 visible in validation MSE ≈ 260) | OK |
| Probe, bootstrap, wording | not reached | n/a |
| No zero-shot / TTA / HAI | none added | OK |

No result-affecting violation (`R0_PROTOCOL_VIOLATION` does not apply). Status: **`R0_V1_1_EXECUTION_BLOCKED`** at the
sealed matched-LSTM observer parity check (machine-1-8 / LSTM / seed 11, test stream, 1 of 185 batches,
`decoder.2` `sequence_h`, max |Δ| 3.08e-5). Owner decision required.
