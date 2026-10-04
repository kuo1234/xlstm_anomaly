# P7 + P10：安全的 Segment Memory for Streaming TSAD

目前唯一 active research line：

`research/p7-p10-segment-memory`

研究核心：

> **在 non-stationary multivariate time-series anomaly detection 中，什麼 temporal segment 應該被寫入 normal memory，以及不同 write operator 會如何改變後續 adaptation、fault masking 與 reversibility？**

目前將問題拆成兩層：

- **P7 — Admission / safety**：Should this segment be written?
- **P10 — Write mechanism / consequence**：What happens after this segment is written?

兩者已整合成同一條研究主線。

---

## Branch structure

目前 remote 長期只保留：

| Branch | 用途 |
|---|---|
| `main` | 穩定基線與已合併歷史 |
| `research/p7-p10-segment-memory` | **目前唯一 active research line** |
| `research/p5-consolidated` | P5 歷史研究 archive |
| `research/adaptive-normality-consolidated` | Adaptive Normality / M1 SMD 歷史研究 archive |

後續 experiment branch 僅作短期開發；完成與驗收後 merge 回 active research branch，再刪 temporary branch。

---

## Current research model

```text
stream
  ↓
temporal segment
  ↓
admission / quarantine        ← P7
  ↓
write operator                ← P10
  ↓
memory
  ↓
future prediction / retrieval
  ↓
adaptation benefit / masking / sensitization / rollback cost
```

### P7：是否允許這個 segment 寫入？

P7 關注：

- normal / suspect / fault admission
- false absorption
- evidence delay
- quarantine
- attribution
- rollback / residual harm
- segment boundary / purity

歷史與設計文件：

`research/few_shot_dual_cache_detector/`

### P10：寫入後會發生什麼？

P10 關注：

- explicit append memory
- Hebbian / mLSTM-style matrix memory
- delta-rule / fast-weight memory
- representation kernel
- decay / retention
- recurring-fault masking
- contamination generalisation
- reversibility cost

主要實驗與報告：

`research/writable_neural_memory_p10/`

---

## Current evidence

### G-L1：persistent recurrent state 沒有形成足夠 deployment utility

在標準 one-step forecasting、長序列訓練下：

- mLSTM 只有 3/6 machines 的 measured memory length ≥ 400 steps
- benign-drift deployment utility 沒有通過原先 P2 gate
- GDeltaNet persistent/reset effect 接近 0
- LSTM memory 很短
- Titans training 不穩定
- explicit kNN memory 對 level/ramp drift 的 adaptation effect 明顯更大

這個結果只否證：

> **standard forecasting objective 下，當時的 point-wise recurrent state 不會自然形成足夠的 drift-adaptation utility。**

它不否證 canonical mLSTM、segment-level write、learn-to-write 或 contamination masking。

結果：

`reports/p10_gl1/run_20261002/`

---

## Step 0 — canonical mLSTM repair：PASS

補上：

- canonical `mLSTMexp`
- `mLSTMsig`
- historical `mLSTM-sig+n` ablation
- recurrent / chunkwise parity
- full state carry
- causal-conv state carry
- non-integer chunk handling
- time-series forecasting wrapper

主要檔案：

- `scripts/p10_canonical_mlstm.py`
- `scripts/p10_step0_parity.py`
- `research/writable_neural_memory_p10/step0/`

Step 0 的目的不是重跑 G-L1，而是建立可信的 canonical state semantics。

---

## Step 1a — role-matched oracle memory pilot：PASS

為避免「kNN normal-reference memory」對「forecaster hidden state」的角色不對稱，Step 1a 固定相同 key/value/score，只改 write operator：

- **W1**：append / top-k kNN
- **W2**：Hebbian + normalizer
- **W3**：delta rule

結果：

1. benign segment write 對 level/ramp 有 measurable adaptation effect
2. forced anomaly write 會造成 recurring-fault masking
3. append 與 distributed write 的 similarity behaviour 不同
4. high-β delta rule 對 recovery transition 很敏感，segment boundary 甚至會讓 masking 轉為 sensitization

報告：

`research/writable_neural_memory_p10/step1a/STEP1A_REPORT.md`

---

## Step 1a.1 — mechanism diagnostics：PASS

這一步釐清：

1. **W2 utility 不是 decay-only artifact**  
   在 M1a 中 `decay-only == skip`，原本 benign-write utility 仍成立。

2. **W1 masking 的時間衰退已有直接解釋**  
   A1 entries 沒有單純被 clean-gap entries 擠掉；masking 會隨 A1→A2 background distance 增大而消退。

3. **broader distributed-write masking 在第二個 representation 仍存在**  
   PCA-whitened φ2 下仍看到：
   - append contamination 較 local
   - W2 / W3 對同方向縮放 variant 有較寬的 masking
   - contamination magnitude 受 write operator × representation kernel 共同影響
   - generalisation shape 仍明顯跟 write operator 有關

報告：

`research/writable_neural_memory_p10/step1a1/STEP1A1_DIAGNOSTICS.md`

---

## Next — Step 1b：mixed-segment / boundary pilot

下一步暫定研究：

> **當同一個 variable-length temporal segment 同時包含 new-normal、fault 與 recovery evidence 時，segment boundary / length 是否系統性控制 adaptation benefit、masking 與 sensitization？**

目前只做 oracle mechanism pilot，不做 learned segmentation / learned admission。

### Sweep A：固定長度，滑動 boundary

固定 segment length，改變 segment 相對 A1 onset 的位置，觀察：

- benign-only steps
- fault-overlap steps
- recovery-key steps

如何改變 memory behaviour。

### Sweep B：固定起點，改 segment length

固定從 A1 onset 開始，改變 segment 長度，直接測 variable-length write。

主要 endpoints：

- post-write same-regime FPR / score
- A2 paired lift
- B−D contamination contrast
- B/D masking ratio
- utility–harm trade-off

---

## Interpretation boundary

目前 Step 1a / 1a.1 都屬於 **oracle mechanism evidence**。

可以支持：

- memory write 對未來 detection 有 causal effect
- write operator 與 representation 會改變 contamination behaviour
- segment boundary 可能是一級變數

不能直接支持：

- 無標籤情境已能判斷 normal / fault
- 已能自動找出 segment boundary
- deployment-safe adaptation
- universal detector
- P7 admission 已解決

---

## Repository layout

```text
configs/                                  experiment configs / frozen settings
scripts/                                  runners, diagnostics, model wrappers
tests/                                    unit / parity / regression tests
reports/                                  historical execution evidence and results

research/
  few_shot_dual_cache_detector/           P7 history: admission / rollback / identifiability
  writable_neural_memory_p10/             P10 + current P7/P10 mechanism experiments
    pilot/
    gl1/
    step0/
    step1a/
    step1a1/
```

歷史研究線：

- P5 → `research/p5-consolidated`
- Adaptive Normality / M1 SMD → `research/adaptive-normality-consolidated`

---

## Working rule

目前採 **exploration-first**：

```text
idea
  ↓
small mechanism pilot
  ↓
is there a real signal?
  ↓
yes → expand / formalize
no  → diagnose failure mode first
```

在 signal 尚未建立前，不先擴張成大型 protocol、seal、bootstrap 或完整 deployment experiment。

若某個機制要進正式 thesis claim，再補：

- fixed protocol
- broader machines / seeds
- statistical uncertainty
- provenance / reproducibility
- real-data validity
- admission identifiability

---

## Environment

目前 canonical xLSTM Step 0 使用：

```text
xlstm           2.0.5
mlstm_kernels   2.0.5
PyTorch         2.13.0 / 2.13.0+cu130
```

主要 GPU execution environment：NVIDIA GB10。

---

## Reading order

建議依序閱讀：

1. `research/few_shot_dual_cache_detector/proposal_v0.4.md`
2. `research/writable_neural_memory_p10/p10_decision_memo.md`
3. `reports/p10_gl1/run_20261002/gl1_results_summary.md`
4. `research/writable_neural_memory_p10/step0/STEP0_CANONICAL_MLSTM.md`
5. `research/writable_neural_memory_p10/step1a/STEP1A_REPORT.md`
6. `research/writable_neural_memory_p10/step1a1/STEP1A1_DIAGNOSTICS.md`

目前 active research state 以 `research/p7-p10-segment-memory` 與 issue #15 最新紀錄為準。

## P7/P10 Step 2c — protocol PASS / PARTIAL_TRANSFER

Step 2a：PASS；Step 2b：**exploratory PASS / pre-registered method FAIL**（Issue #15 review 5975468315）。
[Step 2c frozen transfer protocol](research/writable_neural_memory_p10/step2c/PROTOCOL.md) 與 [exposure audit](research/writable_neural_memory_p10/step2c/STEP2C_DATA_AUDIT.md)：9 台新 SMD machines，frozen exploratory machine-transfer，非 strict confirmatory；`cv<=0.10` 不調參。New-normal promotion 無 source ground truth，NOT EVALUABLE；HAI / SWaT acquisition BLOCKED。Step 2c 已經 Issue #15 review 驗收為 protocol PASS / PARTIAL_TRANSFER；Step3 / RL 未授權。

Step 2c 結果：[Frozen transfer report](research/writable_neural_memory_p10/step2c/STEP2C_TRANSFER.md) — **PARTIAL_TRANSFER / protocol PASS**。9 machines，8/9 ΔAP 正向，macro ΔAP +0.0157 / ΔVUS-PR +0.0181；21 次 replicate-trajectory promotions 中 0 次碰到 labelled anomaly。但 primary CV direction 僅 2/9 台具兩個 class，operator robustness 在 2-2 反轉；沒有 benign-regime truth，new-normal adaptation NOT EVALUABLE。Point recall 約 .278，部分低於 τ 的長 anomaly 仍大量寫入；零 fault promotion 不代表全面 memory safety。未調整 frozen rule；Step3 / RL 未執行（Issue #15 review 5977728169，暫不 GO FOR RL）。

## P7/P10 Step 2d — audit PASS / full TEP PARTIAL

[Extended TEP audit](research/writable_neural_memory_p10/step2d/STEP2D_TEP_AUDIT.md)：**TEP_PROTOCOL_PARTIAL / pending review**。在 `ssh kuo` 完成官方 DTU v1 range acquisition、固定 Mode1 subset 與兩條 observation parser smoke；raw data 全在遠端，未下載完整 HDF5。已確認 fault / mode-transition / setpoint hierarchy，但 activation profile row、warm-up 與 settled-normal/PROMOTE-safe endpoint 尚未由來源證實；預選 Mode1→3 的 10 h completed case 缺失（只有 emergency-stopped counterpart），不補挑。9 tests PASS；沒有 benchmark、CV tuning 或 RL。

## P7/P10 Step 2e — pending review

[Restricted TEP protocol](research/writable_neural_memory_p10/step2e/PROTOCOL.md)：Issue #15 review 5978181304 授權 SP variation vs fault pilot。作者 thesis Appendix A.3.2 支持前30h nominal、SP 30–70h transition / 70h後 settled normal；fixed 3 SP + 2 fault cases，七 policies，`cv<=0.10` / point counts 不調整。所有 acquisition / experiment 留在 `ssh kuo`；Step3 / RL 仍未授權。
