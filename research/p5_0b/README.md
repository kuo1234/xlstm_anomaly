# P5-0B 資料／評估器可採性與 estimand 鎖定

**查核日：** 2026-09-27
**分支：** `research/p5-0b-data-estimand-gate`
**起始 SHA：** `13fdf8f7b6910708b363bbec3b624c5067d687b6`（P5-0A 結案）
**本輪終態：** `P5_0B_BLOCKED_BY_EVALUATOR`

## 裁定

鎖定 **Track A：frozen-score calibration readiness** 為第一個候選 formal estimand：source detector 的 score function 固定，target prefix 只可影響 threshold/calibration 與 READY 決策，不更新 model weights。這只鎖定研究方向，不授權 P5-0C 執行。

PreDist v2 是目前最合適的**回溯式**候選：有 93 個實體 substation、具時間順序的資料、歷史 normal-event 區間及 fault/maintenance 記錄；source/target entity split 在資料結構上可行。它沒有證明 commissioning prefix 在當時由 operator 獨立確認為 normal，亦未在本輪證明每個合格 target 都有共同 `N_max` 之後可用的 sealed normal/anomaly evaluator。CARE v6 同樣可做部分回溯分析，但以 event-centered files 為主；跨檔案時間關係和共同 suffix 尚未成立。兩者都不得稱為 prospective 或 independently verified-normal。

因此目前沒有一個候選通過完整的 `ADMISSIBLE_FOR_P5_FEASIBILITY`；PreDist、CARE、voraus-AD 只列為歷史回溯候選。標籤盲 manifest 只能鎖定實體、時間範圍、檔案與缺失結構，不能證明 reference-normal prefix 或 suffix normal/fault label coverage。本輪已是 `P5_0B_BLOCKED_BY_EVALUATOR`：prefix-only provenance adjudication 未獲准，且固定 common `N_max` 後的 evaluator exposure 未獲證明。`proposed_p5_0c_protocol.md` 是阻塞通知，不是 skeleton；須有另行授權且分離的 prefix-status 與 sealed suffix-evaluator 流程後，才能重開 gate。

## 核心判定

- **正常評估器：** PreDist 的 curated `normal_events.csv` 是可能的 evaluator label source，但尚未證明能在預先固定 target 的共同 `N_max` 後提供足量 normal exposure。只有另行核准 prefix-only provenance adjudication、先封存 READY outputs、再解鎖固定 suffix labels 的程序，才可評估其回溯 FPR；目前不能宣稱已有合格 evaluator。
- **異常評估器：** PreDist fault/maintenance reports 可供已報告事件的 evaluator；fault ascertainment 不完整，不能支持對所有未來故障的泛化品質主張。
- **來源／目標：** PreDist、CARE 有不同實體 ID，可在不看 labels 下預先切 source/target；目前沒有 repo 內凍結的跨實體 source detector。M1/SMD 現有 scores 是 source-native，同一 machine 的 outputs，只能作機制檢查。
- **停止規則：** 選 Track A。純 threshold-only calibration 不改變固定 score ranking，因此 AP/AUROC 只作 detector qualification/background；post-READY anomaly outcome 應用 threshold-dependent 的 event recall/TPR，detection delay 作次要指標。無資料支持的 margin、block/look schedule、`N_max`、purge gap 均標 `TO_BE_FROZEN_BEFORE_EXECUTION`。
- **資訊邊界：** 本輪未下載 dataset archives、未讀取 raw observations/row-level labels、未讀 M1 protected test labels，亦未跑模型/GPU/實驗。所有候選結果來自公開資料集文件、論文、repo metadata、已提交 protocol/manifests/reports。

## 文件

- [逐資料集可採性稽核](dataset_admissibility.md)
- [normal / anomaly evaluator 與 label boundary](evaluator_provenance.md)
- [source-to-target 身分檢查](source_target_identity.md)
- [Track A estimand 決定](estimand_decision.md)
- [normal-only readiness feature contract](readiness_feature_contract.md)
- [P5-0C 未發 protocol／評估器阻塞](proposed_p5_0c_protocol.md)
- [終態 gate](final_gate.md)

## 工作流來源

依據 [Issue #9 handoff](https://github.com/kuo1234/xlstm_anomaly/issues/9#issuecomment-5853972010)、[P5-0A reviewer decision](https://github.com/kuo1234/xlstm_anomaly/issues/9#issuecomment-5853967832)、[P5-0A report at `13fdf8f`](https://github.com/kuo1234/xlstm_anomaly/tree/13fdf8f7b6910708b363bbec3b624c5067d687b6/research/p5_0a) 與專案 `reports/m0_protocol.md` 的資料 manifest／先封存後評估原則。M1 的凍結結論不變。
