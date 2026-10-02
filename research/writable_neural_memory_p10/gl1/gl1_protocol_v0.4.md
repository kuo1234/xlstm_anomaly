# P10 G-L1 Protocol v0.4（seal candidate 2）
**狀態：** SEAL CANDIDATE，尚未授權執行。
**依據：** issue #15 的 seal-readiness review（comment 5947040807）。
**範圍：** 本文件只列出相對 v0.3 的變更；其餘內容沿用 v0.3（`gl1_protocol_v0.3.md`），v0.3 又以 v0.2 為基礎。**不新增 endpoint 或研究條件。**
`R_ref = max_{ℓ≤16} R(ℓ)` 已在該 review 中獲接受，維持不變。

## 1. Execution completeness：在計算任何 endpoint 之前 fail closed（seal blocker 1）
`finalize` 會先呼叫 `validate_execution_completeness`。只要發現任何問題，就輸出 **TECHNICAL-INCOMPLETE**，並列出問題清單，**不進入 P0–P4**。檢查內容如下：

- **Job 完成標記。** 每個 effective machine 需要 3 個 seed 的 fit job 加上 1 個 knn job，每個 job 都必須有 `job_done.json`。
  - 標記中的 `config_digest`（config 的 SHA256）與 `seal_digest`（`configs/p10_gl1_SHA256SUMS` 的 SHA256）必須與 finalize 當下一致；不一致即視為 stale output。
  - 標記中的 machine 與 seed 必須正確。
  - 同一台機台的所有 job，`plan_hash` 必須相同。
- **原子輸出。** job 一律先寫到 `<dir>.tmp-<pid>`，寫完 `job_done.json` 後才 `os.replace` 成最終目錄。
  - 最終目錄若已存在，job 拒絕執行（stale-run guard）。
  - 只要殘留任何 `.tmp-` 目錄，就判定為 partial output。
- **Fit rows。** 每個 (machine, seed, model) 必須恰好 1 筆。trained models 為 window_only、mlstm、gdeltanet、titans、lstm、mlstm_std。
- **G0。** 對每個 (machine, seed, model ∈ {mlstm, gdeltanet, titans, lstm})，位置集合必須等於 job 標記中的 12 個 sealed 位置，不可重複，且每個位置都有對應的 npz。
- **Episode rows。** 每個 (machine, seed, model, family ∈ {level, ramp, gain, none}, ep 0–23, arm) 必須恰好 1 筆。arm 依模型而定：recurrent 模型是 persistent 與 reset；mlstm_std 只有 reset；window_only 只有 single。
- **Sentinel rows。** episode key 加上 kind ∈ {spike, stuck, corr_break}，每個組合必須恰好 1 筆。
- **kNN。** 每台機台的 (family, ep, arm ∈ {persistent, reset}) 與對應的 sentinel key 必須完整，且不可重複。
- **訓練出現 NaN 的 fit。** 這類 fit 會有一筆 fit row（`nan_train=True`），但依設計沒有 G0、episode、sentinel 輸出。validator 只對這類 fit 免除後三項檢查。它們仍屬 B 類 scientific failure，照常計入 P0 與 P4。

測試：`test_completeness_complete_run_passes`，以及 `test_completeness_fail_closed[...]` 的 8 種破壞情境：缺 seed、缺 episode、重複 sentinel、缺 G0、stale digest、殘留 tmp、缺 fit、缺 kNN row。每種情境都必須讓 finalize 輸出 TECHNICAL-INCOMPLETE。另有 `test_stale_output_guard`。

## 2. P3 改用 pre-onset frozen event threshold 作為主要判定（seal blocker 2）
仍然是同一個 P3，不新增 gate。

**主要判定方式：**
- 對每個 episode 的每個 arm，取 calibration 窗 [t0 − 1024, t0) 內的 clean score，計算 30 步 sliding-window max。
- `event_thr` 取這些 max 的 **0.95 分位數**（`sentinel.event_threshold_quantile`），在 onset 之前即凍結。
- 只有在 30 步 sentinel 事件內的最大 score > `event_thr` 時，才算偵測到。
- P3 PASS 的條件不變：Recall_persist − Recall_reset 的 hierarchical 95% CI 下界 > −0.02。

**Local rank q 降為次要診斷：**
- `q_local`、`detected_local`（q > 0.95）只報告，不參與判定。

**為什麼要改：**
- 若 persistent 分支在 onset 之後讓所有 score 等比例縮小，local rank q 不會改變，但在凍結門檻下 recall 會下降。舊的 q 判定因此抓不到 score collapse，新的判定可以。
- 測試：`test_sentinel_collapse_regression`。

**Config 變更：**
- `sentinel.detect_quantile` 改為 `sentinel.local_q_quantile`（0.95）。
- 新增 `sentinel.event_window`（30）與 `sentinel.event_threshold_quantile`（0.95）。

## 3. 非 blocker 修正
- `decision.json` 一律保留以下欄位，避免只看最上層 label 而誤讀失敗原因：
  - 最上層的 `scientific_failure_flags`：所有模型中出現 NaN、發散或 poor fit 的 fit。
  - `P4_diverged_fits_primary`。
  - 各模型的 `P4_diverged_fits`。
- Null fork 的原始分佈保存在每個 G0 位置的 npz（`null` 陣列）中，判定規則不變。
