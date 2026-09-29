# 提議的 P5-0D：資料資格先行協定

## 執行狀態

這是條件式提案，**不是 GO，也未核准 model/effectiveness run**。目前還沒有從已查的 metadata/audit 建立合格的獨立 target streams。不能因為 robot 數量只有一套就先排除同機器內可重複的 contexts；應先檢查有官方語義且可追溯的 dataset-native IDs。P5-0D 先完成這個資料資格 gate，再由 reviewer 決定是否解鎖後續方法研究。

## 資料准入與角色

1. 用 label-blind raw metadata 檢查現有 AURSAD `sample_nr` 與 from/to pin fields：先驗證 pin-pair 在 execution 內是否穩定、不同 executions 的 context 支持度，以及 timestamp-reset recording blocks。這是結構資格查核，不得用來選模型或調參；AURSAD 維持 external lock。若無穩定可用 context，再尋找/取得其他有多個可識別、相互獨立 target contexts 的 dataset。每個 target 必須有依真實 acquisition order 記錄的多筆 healthy commissioning episodes、晚於候選停止範圍的 healthy episodes，以及 fault episodes。目標數需按預定 estimand/power/不確定性要求另行 justified；本輪不虛構最低數字。
2. 只用 label-blind metadata 驗證 ID、時間、episode 長度、schema、missingness、context 重複及跨 target 的 channel semantics。先固定 dataset hash、source/development/target IDs、split 與時間 cut；不得看 outcome label 後換 target 或 cut。
3. Source role 用於凍結 detector/feature pipeline；development targets 用於選擇適配規則與候選 looks；held-out targets 只用於單次評估。每個 role 都按物理 target/context 分組，episode 不能跨 split。
4. Prefix 的 normal provenance 若需 labels adjudication，應由獨立 adjudicator 在 target/time roles 鎖定後只看 prefix；僅能決定 `ELIGIBLE`/`NOT_EVALUABLE`，不能把 label 輸入 READY rule 或替換 target。若無可信 prefix-normal evidence，停止。

## Acquisition 與方法輸出

- 同一 target 的 commissioning episode 按 frozen chronological order 到達；look candidates 只能在 label-blind structure audit 後從可用 prefix 容量推導並送 reviewer 核准，不直接沿用 COLDSTART grid。
- Adaptive rule 的輸入僅限截至當前 look 的 target healthy commissioning observations 與預先凍結的 detector/reference parameters。它輸出 `READY`、`NOT_READY` 或 `NOT_EVALUABLE` 以及 episode index `tau_i`。Never-READY target 保留於 denominator。
- 固定-N baselines 使用相同 target、相同 detector、相同 episode sequence、相同後續 evaluator；比較各預先鎖定 N 及全 `N_max`。使用 acquisition cost = `tau_i`/healthy episodes；只有時間戳和 cadence 可跨 context 比較時才解讀 elapsed time。
- 在 prefix-only rule outputs、READY decisions、scores 和 manifests 封存前，不開啟 future evaluator labels。封存後由獨立 evaluator 解鎖固定 suffix labels；不得用 suffix 結果改 rule、look schedule、target membership 或 margin。

## Outcome definitions（待 reviewer 鎖定）

- **共同 future evaluator：** 每個方法（adaptive 與固定-N）都在完全相同、開始時間嚴格晚於共同 frozen `N_max` 的 held-out suffix 上評估；不以 method-specific `tau_i` 換不同 suffix。
- **Future-normal FPR：** 在此共同 suffix 中，預先指定且 evaluator-confirmed normal 的 episodes，被凍結 detector 判為 alarm 的 episodes / normal episodes。若改以 row/window FPR 或 false alarms per elapsed time 為主指標，須在開 label 前另行鎖定 episodeization、exposure denominator 與 purge。
- **Fault episode recall：** 在相同共同 suffix 中，被偵測的預標 fault episodes / suffix fault episodes。若一 fault 有多段 labels，event merging/window latency 規則及 delay metric 必須預先定義。
- **Success/noninferiority margins、信賴區間方法及 serial-dependence 處理：** 全部待 reviewer/domain justification，不能按結果選。
- 這些是 feasibility estimands；不宣稱 anytime-valid FPR certification 或 safety guarantee。

## AURSAD external-validation lock

AURSAD v1.1 維持 external-only。開發期不得用它選 detector、features、threshold、look schedule、stopping margins 或 eligibility。只有 primary protocol、code、READY outputs 與分析計畫都封存後，才可依相同事前規則作一次外部結構/結果驗證；若資料沒有合格 chronological target units，記 `NOT_EVALUABLE` 並停止，不能換成隨機 sample split。

## 解鎖條件

P5-0D 若確認沒有合格 dataset，記錄 `DATASET_BLOCKED` 並停止 P5 feasibility。只有資料資格表、target-unit manifest、label-open sequence 與 evaluator denominator 都由 reviewer 核准後，才建立下一個明確允許的 protocol task。
