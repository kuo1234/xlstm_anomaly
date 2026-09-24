# R0 protocol amendment r0-v1.2 — single-implementation auditable matched LSTM

Machine-readable form: [`amendment_v1_2.json`](amendment_v1_2.json). This is the **final implementation amendment
for R0**. r0-v1 ([`protocol.md`](protocol.md), [`config.json`](config.json)) and r0-v1.1
([`protocol_amendment_v1_1.md`](protocol_amendment_v1_1.md)) remain authoritative for everything not named here, and
their history is preserved unchanged.

Chronology: R0-v1 → xLSTM cross-backend stop → v1.1 single-backend xLSTM amendment → nine valid xLSTM caches →
matched-LSTM native/manual parity stop (blocked HEAD `57eb5d8055f2ecebe448190f1ded07d2b3948e8e`) → owner decision
→ **R0-v1.2**.

## 1. Rationale (recorded before any v1.2 run)

The r0-v1.1 matched-LSTM stop compared two implementations of one nominal recurrence: native PyTorch `nn.LSTM`
(training and output) and the `phase_f_lstm_observer` manual recurrence (gate traces). For the stopped checkpoint
(machine-1-8 / seed 11): validation 0 / 37 batches failing, test 1 / 185, only `decoder.2 sequence_h`, max |Δ|
3.08e-5, no non-finite value, no extreme input, no gate-range violation, no test label read. No R0 detector AP/AUROC,
probe AP, ΔAP, bootstrap or classification has been observed.

v1.2 does not declare that difference acceptable. It removes the duplicated LSTM implementation: one explicit
recurrence is used for training, validation and test reconstruction, the anomaly score, hidden/cell states,
input/forget gates, common18 and internal234. No second LSTM implementation, and therefore no runtime parity
between implementations, remains.

## 2. The v1.2 matched LSTM

`scripts/real_data_r0_lstm_v1_2.py::AuditableMatchedLSTM`:
`Linear(38,38) → 3 encoder + 3 decoder AuditableLSTMLayer(38) → GELU → Linear(38,38)`, 74,100 trainable parameters
(exactly the r0-v1 count). Each layer holds `weight_ih [152,38]`, `weight_hh [152,38]`, `bias_ih [152]`,
`bias_hh [152]` and runs, per timestep with zero initial state per window,

```text
raw = linear(x_t, weight_ih, bias_ih) + linear(h_{t-1}, weight_hh, bias_hh)
i, f, g, o = raw.chunk(4)          # PyTorch order: input, forget, candidate, output
i, f, o = sigmoid(i), sigmoid(f), sigmoid(o);  g = tanh(g)
c_t = f * c_{t-1} + i * g
h_t = o * tanh(c_t)
```

* The forward is the same for training and extraction. `torch.nn.LSTM`, `torch.nn.LSTMCell`,
  `phase_f_lstm_observer.replay` and its `Observer` are never called in the scientific path; every v1.2 training and
  extraction process installs a guard that makes them raise.
* **Trace capture** (`forward(x, capture=True)`) retains the `h`, `i`, `f`, `c` tensors the single recurrence already
  computed; it never recomputes. Reconstruction with capture off vs on must be bitwise identical.
* **common18** = the sealed reduction `phase_f_lstm_observer.summarize` over layers `encoder.0-2, decoder.0-2`
  (unchanged names, order, quantiles); history14 and internal234 unchanged; dimensions 18 / 14 / 234.
* **Initialisation (frozen)**: `weight_ih, weight_hh, bias_ih, bias_hh` each `U(−1/√38, 1/√38)`, drawn in that order
  per layer (the `nn.LSTM.reset_parameters` rule and order); input/output projections are default `torch.nn.Linear`
  (weight kaiming-uniform a=√5, bias `U(−1/√38, 1/√38)`). Built on CPU immediately after `seed_all(seed)` in module
  order input projection, encoder 0-2, decoder 0-2, output projection, then float32 on the GPU. Deterministic for
  seeds 11/22/33. Never initialised from the native checkpoint; all nine matched LSTMs are retrained from scratch.
* Methods label: **capacity-matched auditable LSTM implementation (R0-v1.2)**.

## 3. v1.2 extraction gate (fail-closed)

On the N(0,1) canary and the first/last 64 fit-interval windows: checkpoint SHA256 and model hash equal the v1.2
training record; 74,100 parameters; eval mode; capture off vs on reconstruction **bitwise**; repeated forward
**bitwise**; extraction output equals the plain forward bitwise; finite reconstruction, score and all traces;
gates in [0,1]; common18 `[N,18]`. On the test stream: H 14, internal234 234, 31 warm-up rows, first finite edge 94;
zero label reads. Backend label `auditable_manual_v1_2`. No replay and no comparison against `nn.LSTM`.
A non-gating engineering comparison with a native `nn.LSTM` carrying the same random-init parameters
(`scripts/real_data_r0_engineering_lstm_compare.py`) may document mathematical equivalence; it is marked
`NON_GATING_ENGINEERING_DIAGNOSTIC` and is never an acceptance criterion or tuning target.

## 4. Carried forward, invalidated, retrained

* **xLSTM (carried forward, authorised)**: the nine r0-v1.1 checkpoints and `vanilla_reference` caches are reused
  without retraining or re-extraction; their checkpoint SHA256, model hashes, cache SHA256 and extraction/training
  record SHA256 are pinned in `amendment_v1_2.json` and re-verified by the v1.2 preflight and at sealing.
* **Native LSTM (invalidated)**: the machine-1-8 / seed-11 native checkpoint and its v1.1 records are preserved as
  history with status `INVALIDATED_BY_R0_V1_2_SINGLE_IMPLEMENTATION_LSTM_AMENDMENT` — because the implementation
  changed, not because of its validation MSE or any result. No v1/v1.1 LSTM cache exists or may enter the manifest.
* **Matched LSTM (retrained)**: machine-1-8, machine-2-1, machine-1-4 × seeds 11/22/33 = 9 new fits under the
  unchanged training contract (W64, 80/20 train split, 50 epochs, batch 128, Adam settings, SeedSequence shuffle,
  lowest validation MSE with earliest tie; no early stopping, scheduler, clipping, test data or labels); at most two
  concurrent processes. Records `runs/train_v1_2_*.json`, `runs/extract_v1_2_*.json`; caches
  `data/r0_runs/<machine>/lstm_v1_2_<seed>/features_v1_2.npz`.
* **Final manifest** `feature_cache_manifest_v1_2.json`: xLSTM = 9 × `vanilla_reference` carried from r0-v1.1;
  LSTM = 9 × `auditable_manual_v1_2`; committed and pushed before any execution-stage label read.

## 5. Unchanged

Datasets, machines, raw hashes, D=38, xLSTM, matched-LSTM graph/width/parameter count, seeds, split, W64, training
contract, scaler (no variance floor), common18/H/internal234, Design-B blocks, 96-row embargo, label semantics, HGB
family and {100, 300}, validation-only selection, single probe-test evaluation, estimand, both bootstraps (10,000
draws, seed 901), classification rules and wording, claim boundary, detector-sanity metrics and DETECTOR_WEAK rule.
xLSTM vs LSTM remains a parallel measurement, not an inferential comparison.

**No further implementation amendment.** If the auditable LSTM itself fails determinism, finiteness, causality,
schema or checkpoint integrity, R0 ends as `R0_V1_2_EXECUTION_BLOCKED`; there is no v1.3.

## 6. Amendment red-team

| question | answer |
|---|---|
| 1. Had any execution-stage SMD label been read? | No — 0 execution-stage label reads (all training/extraction records `labels_read: false`, `label_read_count: 0`; no probe or sanity record). The sealed r0-v1 protocol preflight's per-block label-count check remains the only label access in R0 history. |
| 2. Had any detector AP/AUROC been observed? | No. |
| 3. Had any HGB probe been fitted? | No (0 / 72). |
| 4. Had any ΔAP matrix been computed? | No. |
| 5. Was the amendment chosen from a scientific outcome? | No — from an implementation-parity stop; the only available quantities were train-split reconstruction MSE and parity/diagnostic numbers. |
| 6. Does v1.2 change dataset, labels, H, internal234, probe, estimand or statistics? | No — only the matched-LSTM recurrent implementation (and hence the nine LSTM fits); sealed library/config hashes are re-verified. |
| 7. Are all nine xLSTM results frozen before the amendment? | Yes — produced under v1.1 and pinned by hash in `amendment_v1_2.json` before any v1.2 run. |
| 8. Is the old LSTM seed-11 result excluded because the implementation changed, not because of its validation MSE? | Yes — the exclusion applies to every native-LSTM artefact regardless of its values; all nine LSTMs are retrained under v1.2. |

Verdict: **`R0_V1_2_AMENDMENT_RESULT_BLIND_PASS`**.
