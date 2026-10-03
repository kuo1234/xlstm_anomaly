# P7：Safe Admission / Rollback for Segment Memory

**Issue**：#12  
**Current branch**：`research/p7-p10-segment-memory`  
**Status**：`REFRAME / ACTIVE WITH P10`

P7 最初從 dual-cache / adaptive-normality safety 問題出發，目前已與 P10 合併成同一條 segment-memory 研究線。

目前 P7 的核心問題：

> **Should this temporal segment be written into normal memory?**

也就是研究：

- admission
- quarantine
- evidence delay
- false absorption
- attribution
- rollback
- residual harm
- segment purity / boundary

P10 則回答：

> **What happens after an admitted segment is written?**

共同結構：

```text
segment
  ↓
admission / quarantine        ← P7
  ↓
write operator                ← P10
  ↓
future behaviour
  ↓
adaptation / masking / sensitization / rollback cost
```

---

## Why P7 still matters

目前 Step 1a / Step 1a.1 已看到：

- 寫入 benign new-normal evidence 可以降低後續 error / FPR
- 強制寫入 fault evidence 可以降低 recurring-fault detectability
- 不同 write operator 的 contamination generalisation 不同
- recovery transition 甚至可能讓 masking 轉為 sensitization

因此 P7 現在真正要處理的是：

> **segment 的內容與邊界會如何決定一筆 write 最終是 adaptation benefit 還是 contamination harm？**

這也是 mixed-segment / boundary pilot 的直接動機。

---

## Proposal history

| 版本 | 主張 | 狀態 |
|---|---|---|
| `history/proposal_v0.1_retrieval_forecasting.md` | retrieval forecasting memory | 歷史 |
| `history/proposal_v0.2_dual_cache_detector.md` | dual-cache + operator feedback | 歷史 |
| `proposal_v0.3.md` | context-first adaptation | 歷史；被 v0.4 取代 |
| `proposal_v0.4.md` | admission safety / false absorption / rollback | **目前 P7 設計基礎** |

`proposal_v0.4.md` 保留原樣作為最後一版完整 P7 proposal；新的 P7+P10 mechanism evidence 尚未正式整理成 v0.5。

目前 active framing 以：

- root `README.md`
- 本 README
- P10 Step 1a / 1a.1 報告
- issue #15 最新紀錄

為準。

---

## Current evidence from merged P7 + P10

### Step 1a

- explicit append 與 distributed write 都會產生 contamination effect
- append contamination 比較 local
- W2/W3 對同方向 variant 有較寬的 masking

### Step 1a.1

- explicit append 的 masking 會受到 A1→A2 background mismatch 影響
- distributed contamination magnitude 依 representation kernel 改變
- high-β delta update 對 recovery boundary 特別敏感

因此 **segment boundary / composition 已成為 P7 的一級變數**。

---

## What P7 has not solved

目前仍是 oracle mechanism stage，尚未證明：

- 無標籤 stream 能可靠辨識 benign drift vs fault
- segment boundary 可自動找到
- admission confidence 可校準
- rollback 在 nonlinear neural memory 中一定可精確完成
- deployment safety / coverage guarantee

這些問題只有在 oracle mechanism 先證明值得研究後，才會逐步加入。

---

## Files

- `proposal_v0.4.md`：P7 最新完整 proposal
- `problems_and_feasibility.md`：問題與可行性整理
- `literature/`：prior-art / gap audit
- `second_review_request.md`：第二次審查紀錄
- `toy_identifiability_sim/`：早期 identifiability toy study
- `history/`：v0.1 / v0.2 等歷史版本

舊 branch `research/few-shot-dual-cache-detector` 已整合並刪除；後續 P7/P10 均以
`research/p7-p10-segment-memory` 為唯一 active research line。
