# P5-0B 終態 gate

**本輪終態：`P5_0B_BLOCKED_BY_EVALUATOR`**
**Track：** Track A — frozen-score calibration readiness（概念方向選定；不構成 execution GO）
**Closest candidate:** PreDist v2 for a retrospective study; no P5-0C dataset/evaluator pair admitted.

## Gate result

Issue #9 要求先指出哪個候選能在 label boundary 內建立合法、獨立的 future-normal evaluator。答案是：**本輪目前沒有一個候選被證明完成了所需 evaluator construction。** PreDist 的公開文件顯示有 `normal_events.csv`、chronological substation series 與 fault/maintenance reports；這使它成為可供未來審查的 retrospective candidate，但不代表一個預先固定 target 的正常 prefix 已有獲准的資格核對步驟，亦不代表 common `N_max` 後有足夠、可分離的 normal/fault evaluator exposure。CARE v6 的事件檔不證明同一 target 的共同未來 suffix；voraus-AD 沒有 held-out physical target entity。

**Retrospective label-derived provenance 本身不是 blocker。** Blocker 是目前無法同時滿足：(1) READY trajectory 前合法證明 reference-normal prefix；(2) target/time split 不受 future labels 影響；(3) trajectories seal 後才用固定 suffix labels 做 evaluator；(4) 不足時不換 entity/cut。label-blind time/missingness metadata不能證明 label masks 的存在與覆蓋；本輪亦未獲准開 labels，故不可假稱已通過。

## Track A disposition

概念上選 Track A，因 source score function frozen、只校準 target threshold，研究邊界較清楚；純 threshold-only 不改 score ranking，所以 AP/AUROC 僅作 detector qualification/background。post-READY anomaly outcome 候選應使用 event recall/TPR、delay 等 threshold-dependent metrics。但目前沒有可執行的 dataset-bound estimand，這項選擇不會讓資料 gate 自動通過。

## 停止範圍

- 不發 P5-0C protocol skeleton；[同名文件](proposed_p5_0c_protocol.md)僅列阻塞與 reopen requirements。
- 不下載 raw archive、不開 row-level labels、不計算 prefix trajectory、不訓練模型、不跑 GPU/Meta-RL。
- 不用 source-native M1/SMD outputs冒充held-out target recommissioning，不改 M1 結論。

## 下一步 gate

需由下一個 Issue comment 核准一套 label boundary：先凍結 target/time roles；如何單獨 adjudicate prefix-only normal status；如何 seal READY outputs；何時僅對固定 common suffix 解鎖 normal/fault masks；不足時如何保留 `NOT_EVALUABLE` 且不得替換 target。沒有這些先決條件以前，不繼續到 P5-0C。
