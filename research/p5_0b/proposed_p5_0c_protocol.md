# P5-0C protocol 未發出：evaluator gate 未通過

## 狀態

本檔是依 Issue #9 最低文件清單保留的**阻塞通知**，不是 protocol skeleton。P5-0C 不會在本輪啟動，亦沒有 source/target IDs、prefix/suffix cut、`N_max`、purge、metric margin 或 label-open schedule 被核准。

本輪分類中，PreDist v2 是較佳的 historical retrospective candidate，但 public metadata 只能證明資料集有 normal-event annotations、fault/maintenance records 和多個 chronological substation streams；不能證明某個預先固定 held-out target 的指定 prefix/suffix pair 已符合下列 evaluator contract。CARE v6 是 event-centered data，voraus-AD 僅一個 robot unit；其餘候選不能補足該 identity。故 final status 為 `P5_0B_BLOCKED_BY_EVALUATOR`。

## 尚未解決的兩個必要構造

1. **Reference-normal prefix adjudication**：raw observations 本身不能證明某段是 normal。若 label tables 完全封存到 READY 之後，就形成「無法證明 prefix normal」的循環。未來需有獨立、獲准且可稽核的 prefix-only status adjudication；它必須在 source/target IDs 與時間切點已先凍結後執行，只能把不合格 target 標為 `NOT_EVALUABLE`，不能改選 target，也不能把 labels 當 readiness inputs。本輪未授權此步驟。
2. **Common future evaluator**：時間戳/row counts/missingness 不表示 suffix 含有已標記 normal 和 fault exposure。要避免 outcome-based target/cut selection，需預先固定 target/time roles，再按被批准的 sequence 開啟 suffix labels；若 coverage 不足，必須停止且不可替換。公開摘要未證明 PreDist/CARE 每個 target 在共同 `N_max` 後都有該 evaluator。本輪不得讀 labels 來補這個證據。

回溯 label-derived provenance 本身不是 blocker，也不要求所有資料都 prospective/operator-attested。Blocker 是目前沒有合法分離的 prefix qualification 與 future-suffix evaluator sequence，也未證明固定 suffix coverage。

## 不得提前填入的 protocol fields

| P5-0C field | 狀態 |
|---|---|
| source/target entities；實體層 disjointness | 未鎖；需在 label-blind metadata 上先預註冊 |
| chronological prefix and suffix bounds | 未鎖；不得用 future labels挑 cut |
| prefix-normal adjudication source/access order | 未核准 |
| common `N_max`, look schedule, acquisition unit, purge gap | `TO_BE_FROZEN_BEFORE_EXECUTION`，需 domain/data justification |
| normal-risk evaluator mask and exposure | 未證明；suffix labels不得現在開啟 |
| anomaly evaluator episodes / event completeness | 未證明 target-level post-horizon coverage |
| threshold rule, baseline variants, no-alarm control | Track A 概念見 [estimand](estimand_decision.md)，尚未形成 executable lock |
| success/noninferiority margins | `TO_BE_FROZEN_BEFORE_EXECUTION`，不得任意設定或看結果選擇 |
| artifact/label-open sequence | 未核准，須解決上面兩項後另立任務 |

## Reopen gate

只有下一個獲准 review/task 明確定義：(a) prefix-only normal-status adjudication 如何在不洩漏到 READY inputs 的前提下完成；(b) source/target/time roles 如何先凍結；(c) future normal/fault labels 如何在 score/output seal 後對固定 suffix 解鎖；(d) 無足夠 suffix evaluator 時如何保留 `NOT_EVALUABLE` 且不替換 targets，才可重開 P5-0B/P5-0C。除此之外不執行資料下載、label inspection、trajectory computation、model/GPU work。
