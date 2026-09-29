# P5-0C final gate

## Status

`P5_0C_TARGET_UNIT_BLOCKED`

## 證據

1. voraus-AD 已下載並重算 SHA-256；metadata aggregate audit 得到 2,122 episodes、1,367 normal、755 anomaly。setting/action/category 是 variant、phase 或 outcome metadata；在已讀欄位中沒有合格的其他 context key。這不假設同一 robot 必然只有一個 target。
2. AURSAD v1.1 以固定版完整資料稽核中的 SHA-256/size pin；Zenodo 官方 MD5 單獨記錄，未在本輪完成 bytes-level 交叉核對。4,094 `sample_nr` executions 來自 UR3e screwdriving dataset。execution ID 不等同 context target；pin registers 是 plausible candidate，但 per-execution pair support/order 未查核，sample 間 chronology 尚未建立。
3. COLDSTART 固定版直接涵蓋 fixed-N commissioning、fixed cohorts、Recall/FPR-based retrospective N*；查核 paths 未找到 per-target online READY stop。這不消除 dataset target-unit blocker。
4. setting×action 不是替代的獨立 target：voraus-AD 的 1,152 個 strata 全部單一 label class，action IDs 是 episode 內 phase。AURSAD pin registers 有欄位邊際支持，但尚未形成有 per-execution context stability、chronology、及足夠重複單位的 stream protocol。

## Decision

不啟動 formal efficacy run，不訓練大型模型、不做 target performance experiment、不調校 AURSAD、不救援 PreDist。`proposed_p5_0d_protocol.md` 只提議下一步找/取得並先資格審查具備多個獨立 chronological target streams 的資料。

**Recommended P5-0D：** 先做不調參的 AURSAD pin-context metadata qualification，確認每次 execution 的 from/to context、context 支持度與 recording-block order；不開 model outcomes、不改 external-validation lock。若此候選不成立，再找/取得有足夠獨立 contexts、healthy prefix 及共同未來 normal/fault evaluator 的資料。目標單位可位於同一 robot，只要 context independence 和 chronology 有科學依據。若最後只剩單一 Yu-Cobot historical stream，須由 reviewer 改寫 estimand 為描述性 n=1 replay，不能宣稱跨-target adaptive-stopping 效果。
