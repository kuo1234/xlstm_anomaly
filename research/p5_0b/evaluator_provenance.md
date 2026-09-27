# Evaluator provenance 與 label boundary

## 本輪結論

所有候選的論文/README 顯示存在歷史 normal/anomaly annotations，但本輪沒有打開 row-level labels。文件本身不能證明某個預先固定 target 的 common `N_max` 後有足夠的 normal/fault evaluator exposure。更早一步，若所有 `normal_events.csv` 一律封存到 READY 輸出之後，就沒有方法在計算 readiness trajectory 前確認 target prefix 真的是 reference-normal。這個流程循環沒有獲准的分離步驟，因此終態為 `P5_0B_BLOCKED_BY_EVALUATOR`。

Retrospective label-derived provenance 本身不是禁用原因。需要另行核准並分開記錄兩種用途：prefix-only normal-status adjudication，與 suffix-only future-outcome evaluation。不能用 suffix labels 決定誰的 prefix 合格、切點、`N_max`、source/target membership 或 READY rule。

## 資訊順序與限制

| 階段 | 允許資訊 / 動作 | 禁止事項 |
|---|---|---|
| Label-blind manifest | Dataset version, entity IDs, schema, raw file hashes, timestamps/row counts/missingness；預先定義每個候選的 source/target、prefix、suffix time ranges | 讀 future normal/fault masks 後挑 entity、改 cut、找足夠 labels、調 `N_max` |
| Prefix provenance adjudication | **本輪未授權。** 後續若獲獨立授權，只能核對已鎖定 prefix 的 normal status；target 若不合格記 `NOT_EVALUABLE`，不得看 suffix 或換成有利 target | 將 prefix labels 當 READY feature、用 prefix outcome調 threshold/rule、根據結果替換 target |
| Source detector / prefix scoring | 只有 prefix provenance gate 合格後，使用 frozen source detector、允許的 raw prefix observations 計算 scores/features | suffix rows/scores/labels、fault/event IDs、任何 evaluator metrics |
| READY/rule/output seal | Freeze rule, threshold, READY/NOT_READY, `tau_i`, trajectory hashes and manifest | 開 future evaluator labels 或更改之前的 selection/rules |
| Suffix evaluator unlock | 僅在上一步 seal 後，獨立 evaluator 對**已凍結 common suffix**讀 normal/fault labels；不足則 `NOT_EVALUABLE`，不替換 target/cut | 用 suffix labels回頭改 eligibility、cut、prefix、`N_max`、margin 或 READY rule |

本輪未下載 archive、未讀 raw samples/row labels，也未做上述 prefix adjudication 或 suffix evaluation。公開 labels 即使可下載，對本研究仍按 evaluator-only boundary 處理。

## 候選資料的 evaluator limits

### PreDist v2

公開資料說明列出 `normal_events.csv` 歷史 normal intervals，以及 fault/maintenance reports。它是最合理的 retrospective evaluator 候選；來源證據不等同已有足量 evaluator。公開 metadata 未證明每個 label-blind 預先指定的 held-out substation，在 common horizon 後同時含足量已標記 normal exposure 和 fault episodes，也未提供一個本輪已核准的 prefix-only label adjudication 流程。fault reports 不完整，故 anomaly metric 只能代表已報告/已標記事件。不得稱為獨立 operational attestation。

### CARE v6 / WindADBench

v6 release 有 normal behavior 和 fault event sequences；WindADBench 執行 label-based evaluation。公開 docs 未證明各 event file 可拼接成同一 held-out turbine 的連續 `N_max` 後正常 suffix；跨檔 chronology、overlap 和 target 級 normal exposure 未知。本輪不讀 archive/event labels。

### voraus-AD / AURSAD / COLDSTART

voraus-AD 的 paper 描述單一 robot cell 的早期正常與後期 normal/fault recording，可用於歷史同實體 replay，但不能建立 P5 要求的 source→held-out-target identity。COLDSTART 現行 split 是隨機 cohorts；AURSAD 跨 execution 時間不可作 acquisition order。固定正常/異常 evaluator cohorts不能替代 common future suffix。

### SMD / M1

SMD 的 M1 test labels 為 protected evaluator data；沒有獨立 hold-forward normal mask/event IDs，且 nine-machine M1 result 已披露，不是 untouched confirmatory suffix。本輪未開 label files。

## Reopen 條件

之後若有一個獲准任務能：(1) 在不讀 suffix labels 下凍結全部 entity/time roles；(2) 以明確且單獨記錄的 prefix-only normal-status adjudication 解除 READY replay 的循環；(3) prefix status 不輸入 readiness features；(4) seal 所有 trajectories 後才解鎖 suffix-only labels；(5) 即使沒有足夠 suffix evaluator 也不替換 target/cut，則可重新評估 PreDist 是否 admissible for a bounded retrospective P5-0C. 未完成前仍是 blocked。
