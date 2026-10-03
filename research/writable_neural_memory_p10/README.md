# P10：Writable / Distributed Memory Mechanisms

**Issue**：#15  
**Current branch**：`research/p7-p10-segment-memory`  
**Status**：`REFRAME / ACTIVE`

P10 已不再單獨研究「persistent mLSTM state 是否比 reset 好」。

目前定位：

> **在 role-matched normal-reference setting 下，不同 write operator 對 adaptation、contamination masking、generalisation、forgetting 與 reversibility 造成什麼行為差異？**

P10 與 P7 已整合：

- P7：Should this segment be written?
- P10：What happens after this segment is written?

---

## Progression

### G-L1

結果：`FAIL-PERSIST`

- standard forecasting training 下，mLSTM persistent utility 很弱
- GDeltaNet persistent/reset 近零
- LSTM memory 很短
- Titans 不穩定
- explicit kNN memory 的 benign-drift adaptation 明顯較強

這只否證當時的 architecture + objective 組合，不代表 segment-level writable memory 無效。

### Step 0 — canonical mLSTM：PASS

補上 canonical `mLSTMexp` / `mLSTMsig` 與 state-carry parity。

見：

`step0/STEP0_CANONICAL_MLSTM.md`

### Step 1a — role-matched oracle memory：PASS

統一 memory role，只改 write operator：

- W1 append / kNN
- W2 Hebbian + normalizer
- W3 delta rule

結果：

- benign write 有 adaptation effect
- forced anomaly write 會造成 recurring-fault masking
- distributed write 對同方向 variant 有較寬的 contamination generalisation
- recovery transition 可讓 high-β delta rule 從 masking 轉為 sensitization

見：

`step1a/STEP1A_REPORT.md`

### Step 1a.1 — diagnostics：PASS

釐清：

- W2 utility 不是 decay-only artifact
- W1 masking 隨 Δ 消退主要來自 A1→A2 background mismatch
- broader distributed-write masking 在 PCA-whitened φ2 下仍存在
- masking magnitude 受 operator × representation kernel 共同影響

見：

`step1a1/STEP1A1_DIAGNOSTICS.md`

---

### Step 1b — mixed-segment / boundary pilot：pending review

一個 oracle admission segment 同時含 new-normal（ramp / level）、burst fault 與 recovery evidence：
Sweep A 固定 L=38 滑動 boundary，Sweep B 從 fault onset 起改長度 L=16–62。

結果（φ1 + φ2、ramp + level 一致）：

- 決定 contamination 正負號的是 **segment 結尾相對於 fault recovery transition 的位置**，不是 fault 步數比例
- 結尾在 fault 內（無 recovery keys）：W1 / W3 出現 inversion（memory 把 fault 當成預期），同時失去 adaptation
- 包含 recovery keys：一般 masking；再加入 post-recovery benign steps：W3 β=.5 轉為 sensitization（B/D ≈ 1.1）
- W2 f=.995（normalised Hebbian）對 boundary 幾乎不敏感

見：

`step1b/STEP1B_BOUNDARY.md`

---

## Next question

待 review 決定：mixed contamination dose、admission policy，或 rollback / reversible write。

目前仍採 oracle boundary / oracle semantics。

尚未宣稱：

- admission 已解決
- segment boundary 可自動找到
- neural memory 優於 explicit cache
- deployment safety 已建立

---

## Directory map

- `p10_decision_memo.md`：早期 P10 framing / decision history
- `review_response_v0.md`：初期 review response
- `audit/`：prior-art / occupancy audit
- `pilot/`：最早 P10 exploratory pilot
- `gl1/`：G-L1 protocol history
- `step0/`：canonical mLSTM repair / parity
- `step1a/`：role-matched oracle memory pilot
- `step1a1/`：mechanism diagnostics
- `step1b/`：mixed-segment / boundary pilot

舊的 `docs-only` / `no research GO` 狀態已不再適用。
