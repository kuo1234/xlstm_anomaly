# P10 G-L1 Protocol v0.3（seal candidate）
狀態：**SEAL CANDIDATE**。尚未授權執行。
- 依據：issue #15 的 Active Handoff（comment 5946095046）。
- 前一版：v0.2（`gl1_protocol_v0.2.md`）。本文件只列出**相對 v0.2 的變更**，以及在實作中**固定下來的規格**。凡是本文件沒有改到的部分，以 v0.2 為準。
- **任何數值都以 `configs/p10_gl1_config.yaml` 為最終依據**；runner 啟動時會檢查 `models.arch` 與程式內的 `ARCH` 是否完全一致，不一致即 fail closed。

## A. 四個 blocker 的修正

### B1：Technical invalidity 與 scientific failure 分開處理（§8 改寫）
- **A 類（technical）**：manifest／SHA256 不符、資料損壞或缺檔、runner／parity 實作錯誤、硬體中斷。
  - 處理方式：寫入 `technical_invalid.json`。資料類問題只在這種情況下，才依序以 reserve 機台（2-6 → 3-9 → 2-2）遞補。
  - 實作錯誤要修正後重跑，這不算模型結果。
- **B 類（scientific）**：驗證 MSE 超過 1.5 倍 window-only、訓練出現 NaN／Inf、state 發散、P1–P4 任一 endpoint 失敗。
  - 處理方式：**一律計入 gate，不得排除，也不得以 reserve 遞補**。
- 新增 **P0 fit adequacy**：primary 的 6 台機台中，至少 4 台要有 ≥ 2 個 seed，同時滿足「訓練無 NaN」與「val_ratio ≤ 1.5」。不滿足時判 **FAIL-FIT**，進入 G-L2。
  - 判 P0 時，val_ratio 偏高的 fit **仍納入 P2–P4 的所有 endpoint**，不做事後挑選。
- P4 的定義擴大：primary 只要有**任何一個** fit 出現訓練 NaN 或串流 state 發散，P4 即判 FAIL。發散的判準是 state norm 超過訓練期最大值的 100 倍，或 forecast 出現非有限值。
- 實作位置：`p10_gl1_run.py: effective_machines / evaluate_model`。
- 對應測試：`test_reserve_only_for_technical_invalid`。

### B2：h05 的可量測門檻與聚合順序（§4 改寫）
- **Noise floor**：在每個 G0 位置做 null fork，也就是同一段 clean 序列複製兩份、各自獨立執行一次。
  - floor = max(該 fit 所有 null 差值的 0.999 分位數, parity_tol = 1e-4)。
  - floor 在 outcome 計算之前就由這個規則決定，不能事後調整。
- **可量測條件**：0.05 · R_ref > floor，其中 R_ref = lag 1 到 16 的 R(ℓ) 最大值。
  - 為什麼不用 R(1)：Titans 的 memory 只在 chunk（16 步）結束時才寫入，所以 R(1) 到 R(15) 在結構上就是 0。改用前 16 lag 的最大值，不會讓任何架構只因為 chunk 延遲就被判為「不可量測」。
- **h05 定義**：最小的 ℓ，使得 R(ℓ′) < 0.05 · R_ref 對所有 ℓ′ ∈ [ℓ, 2048] 都成立。若 R(2048) 仍 ≥ 0.05 · R_ref，記為 censored = 2048。
- **不穩定**：若 max_{ℓ>16} R(ℓ) > 2 · R_ref，該位置記為 `unstable`，**不得計為長記憶**。
- 判為 `not_measurable` 或 `unstable` 的位置，都不參與 h05 的中位數計算。
- **聚合順序**（position → seed → machine）：
  1. Position → seed：該 seed 至少要有 8／12 個可量測位置，才取這些位置 h05 的中位數；否則該 seed 的 h05 記為 0。
  2. Seed → machine：取 3 個 seed h05 的中位數，缺失的 seed 記為 0。
  3. Machine → P1：P1 PASS ⇔ 6 台中至少 4 台的 h05 ≥ 400。
- 實作位置：`p10_gl1_core.py: h05_from_response`；`p10_gl1_run.py: p1_table`。
- 對應測試：`test_h05_rules`（涵蓋 not_measurable、unstable、censored，以及 Titans 式的延遲起始）。

### B3：P1 不得作為納入條件
- P1 的機台別結果，只用來判斷 aggregate 的 P1 是否成立。
- P2–P4 一律使用**全部 effective primary 機台**，也就是 ex-ante 的 6 台，扣除 A 類失敗並經 reserve 遞補後的機台。
- 實作位置：`evaluate_model`。
- 對應測試：`test_p1_is_not_an_inclusion_filter`。

### B4：架構與時間語意完全固定
完整規格見 `configs/p10_gl1_config.yaml` 的 `models.arch`（等同 `p10_gl1_models.ARCH`）。

**共同外殼**
- 運算順序：z_t → Linear(C, d) → core → LayerNorm(x + W_o · o) → Linear(d, C)。
- 預測：ŷ_{t+1} = z_t + head(·)。

**mLSTM（primary）**
- 維度：d = 128，4 個 head，dk = dv = 32。
- Gate：forget 與 input gate 都是 **sigmoid**，不使用 exp gate。forget bias 初始化為 linspace(3, 6)，input bias 初始化為 0。
- k 除以 √dk。
- 輸出正規化：h = C·q / max(|n·q|, 1)。
- 以 chunk-parallel 計算，chunk 長度 64，結果與逐步遞迴完全相同（float64 誤差 < 1e-10）。

**Gated DeltaNet**
- 更新式：S_t = α_t S_{t−1}(I − β_t k_t k_tᵀ) + β_t v_t k_tᵀ。
- q 與 k 做 L2 normalize；α 與 β 都是 sigmoid；α bias 初始化為 linspace(3, 6)。
- Chunk 計算以 triangular solve 實作（UT 形式，長度 64）。

**Titans-LMM**
- Memory：M(k) = W2 · silu(W1 · k)，dm = 64，hidden = 192；W1、W2 的初值為可學習參數。
- Chunk 長度 b = 16。整個 chunk 內，retrieval 與 per-token gradient 都使用 chunk 起點的 memory（gradient 以解析式計算）。
- 更新：S_t = η_t S_{t−1} − θ_t g_t，M_t = (1 − α_t) M_{t−1} + S_t。chunk 結束時，下一個 chunk 改用 M_b。
- 參數：η = sigmoid（bias 初始化為 +2）；θ = 0.1 · sigmoid（bias 初始化為 0）；α = sigmoid（bias 初始化為 −5）。

**LSTM**
- 結構：Linear(C, 64) → LSTM(64, 96) → LayerNorm → head；forget bias 總和初始化為 1。

**window-only**
- 結構：MLP(K · C → h → C)，K = 100，h = ⌊(70000 − C) / (K · C + 1 + C)⌋。

**參數量**
- 對 C = 20–35，上述各模型都落在 60k–80k 參數（`test_param_budget`）。

**時間語意**
- 「t 時刻的 state」是指已讀入 z[:t] 之後的 state。
- 讀入 z[t] 時產生的 forecast，是對 z[t+1] 的預測。觀測值 z[τ] 用讀入 τ−1 時的預測評分，也就是 score-before-write。

**時間格點**
- 所有 fork 時點都落在 16 步格點上：G0 位置、drift onset，以及 sentinel 起點（onset 加 256、512、768）。
- fit_end 與 tr_end 也取 16 的倍數，因此 Titans 在每個 fork 點的 chunk 位置都是 0（`test_plan_grid_and_titans_fork_alignment`）。

**State carry 與 detach**
- 訓練時，同一 epoch 內的相鄰 chunk 攜帶 detached state。每個 epoch 各 stream 的起點 offset 都在 [0, L) 內隨機抽取，並從零 state 開始。

**Reset 臂**
- t 時刻的 state 由零 state 開始，只讀入 z[t−99 … t] 後算出，用來預測 z[t+1]（`test_reset_window_alignment`）。
- 使用**與 persistent 臂完全相同的權重**。evaluate 前後 state_dict 逐 byte 相同（`test_calibration_isolation_and_weight_identity`）。

## B. 其他在實作中固定的細節
- **Persistent 臂的起點**：串流開始時的 state，是從零 state 讀完整個 fit 區（train 加 val）後得到的 state。
- **σ**：每個 fit、每個臂，各自以驗證區殘差的逐通道標準差計算（下限 1e-3）。score = mean_c(r/σ)²。
- **Sentinel**：每個 episode 有三個 sentinel，在 onset 之後固定偏移：spike +256、stuck +512、corr_break +768（各 30 步）。
  - 每個 sentinel 都在 fork 出的副本中評分，評分後丟棄，主串流的 state 不受影響（`test_sentinel_fork_does_not_write_main_state`）。
  - 背景分佈：同一臂、同一 drift 分支（不含 sentinel），評估窗內所有 30 步滑動窗的最大值。
- **Corr_break 的 donor**：在距離 sentinel 起點 ≥ 2048 步的 16 格點上，由 seed 抽一段真實資料。
- **抽樣 seed**：所有位置與通道都由 seed（onset 902、sentinel 903）加上機台名稱的 hash 決定，與模型、臂、seed 無關。
- **kNN-append**（只報告，不參與判定）：窗口 w = 8，排除最近 8 步，bank 為 fit-train 區以 stride 4 取的窗口。
- **Calibration isolation**：threshold 只由 [t0 − 1024, t0) 的分數決定。測試會改變 onset 之後的 drift 幅度，確認 threshold 完全不變（`test_calibration_isolation_and_weight_identity`）。
- **執行防護**：`fit`、`knn`、`finalize` 都需要環境變數 `P10_GL1_AUTHORIZED=1`，並且要通過 `configs/p10_gl1_SHA256SUMS` 的逐檔驗證（`test_execution_requires_authorization`）。`dry-run` 只使用合成資料。
- **Machine-level 報告**：`decision.json` 中的 `P2_machine_effects` 逐機台列出 paired ΔFPR；`P3_large_degradation_flags` 標記任一 sentinel 類型的 recall 下降超過 0.10 的情況（只標記，不影響判定）。

## C. 判定順序（只看 primary mLSTM；其他模型的結果全部照常報告）
依序檢查，第一個失敗的條件決定標籤：
1. 有效機台不足（A 類失敗後 reserve 也不夠補足 6 台） → TECHNICAL-INCOMPLETE（必須重跑，不構成結果）
2. P0 → FAIL-FIT
3. P1 → FAIL-PERSIST
4. P2 → FAIL-UTILITY
5. P3 → FAIL-COLLAPSE
6. P4 → FAIL-STABILITY
7. 以上皆通過 → PASS

- PASS → 撰寫 WIM protocol v0.3。
- 任何 FAIL → 進入 G-L2。
- 「Family 層級」的主張需要 primary PASS，**而且**至少一個 replication（GDeltaNet 或 Titans）也 PASS。

## D. 成本（以合成資料的 CPU micro-benchmark 估計，不是實測結果）
- 每次訓練 iteration（batch 8、L = 2048、C = 30）：mLSTM 0.18 秒、GDeltaNet 0.27 秒、Titans 0.54 秒、LSTM 0.22 秒。
- 若跑滿 4000 iterations：每個（機台, seed）大約 1–1.5 CPU 小時（early stopping 可能縮短），18 組合計約 18–27 CPU 小時。在 GB10 上應更短。
