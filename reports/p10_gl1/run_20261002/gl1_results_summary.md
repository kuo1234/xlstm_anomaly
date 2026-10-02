# P10 G-L1 結果：**FAIL-PERSIST → 依預宣告決策樹進 G-L2**（run_20261002）

- 執行：sealed `1dda8f1`，GB10，2026-10-02 07:29–09:15 UTC。6 primary 機台 × 3 seeds × 6 模型 + kNN。Completeness validator **通過**（沒有 TECHNICAL-INCOMPLETE）；24 個 job marker 共用同一個 seal digest；technical invalid：無。
- 原始輸出 tarball（保留在 GB10 `.worktrees/p10-gl1/reports/p10_gl1/run_20261002/`）SHA256 `0600c9f01a2e0de2b06394beffe09311121ffc10146f5e010765f06c4d8ae663`。本資料夾是彙整版：`decision.json`、`fits_all.csv`、`episodes_all.csv.gz`、`sentinel_all.csv.gz`、`g0_responses_all.npz`（含 raw null fork）、`job_markers.json`、`logs/`。
- 執行期間沒有修改任何 protocol、config、margin 或機台。

## 1. Gate 判定（primary = mLSTM）
| 條件 | mLSTM | GDeltaNet（rep.） | Titans（rep.） | LSTM（ref.） |
|---|---|---|---|---|
| P0 fit adequacy（達標機台數／6） | PASS（6） | PASS（6） | PASS（4） | PASS（6） |
| P1 h05 ≥ 400（通過機台數，需 ≥ 4） | **FAIL**（3） | **FAIL**（1） | **FAIL**（1） | **FAIL**（0） |
| P2 utility（通過的 family 數，需 ≥ 2） | FAIL（0） | FAIL（0） | FAIL（0） | FAIL（0） |
| P4 stability | PASS | PASS | FAIL（9 個 fit 發散或 NaN） | PASS |
| **Label** | **FAIL-PERSIST** | **FAIL-PERSIST** | **FAIL-PERSIST** | **FAIL-PERSIST** |

**判定的穩健性：** mLSTM 的 P1 差一台才達標（3／6）。但就算 P1 過了，P2 也會失敗：三個 drift family 沒有一個同時滿足「點估計 ≤ −0.02」與「CI 上界 < 0」。因此結論不取決於 P1 的邊界：**在標準長序列訓練下，持續記憶沒有達到預宣告的部署效益。**

### P1：各機台的 h05（中位數，單位為步）
|             |   mlstm |   gdeltanet |   titans |   lstm |
|:------------|--------:|------------:|---------:|-------:|
| machine-3-7 |   121   |       269.5 |      0   |   21.5 |
| machine-1-6 |   725   |       339.5 |      0   |   16   |
| machine-2-7 |   329   |       421.5 |      0   |   18   |
| machine-3-5 |   258.5 |       334.5 |   2007.5 |   16   |
| machine-2-9 |   468   |       324   |      0   |   15   |
| machine-1-3 |   451   |       215.5 |      0   |   14   |

### P2：ΔFPR = persistent − reset（hierarchical 95% CI）
- mlstm：level -0.021 [-0.046, +0.004] / ramp -0.018 [-0.034, -0.003] / gain +0.000 [-0.002, +0.002]
- gdeltanet：level -0.004 [-0.016, +0.008] / ramp +0.001 [-0.010, +0.017] / gain -0.001 [-0.005, +0.002]
- titans：level -0.082 [-0.278, +0.025] / ramp -0.062 [-0.260, +0.023] / gain +0.000 [-0.064, +0.054]
- lstm：level +0.000 [-0.001, +0.001] / ramp -0.000 [-0.001, +0.000] / gain +0.000 [-0.000, +0.000]

mLSTM 各機台的 ΔFPR：
|             |   level |   ramp |   gain |
|:------------|--------:|-------:|-------:|
| machine-3-7 |  -0.037 | -0.022 | -0.002 |
| machine-1-6 |   0.024 |  0.008 |  0.002 |
| machine-2-7 |  -0.013 | -0.037 | -0.001 |
| machine-3-5 |  -0.006 | -0.005 |  0.001 |
| machine-2-9 |  -0.067 | -0.035 |  0.001 |
| machine-1-3 |  -0.027 | -0.019 |  0.002 |

### P3 與 P4（mLSTM）
- P3 只評估 `none`（因為沒有任何 family 通過 P2）：Δrecall -0.0008 [-0.0154, +0.0162] → no-drift sentinel guardrail 本身 PASS；但 `decision.json` 的 formal `P3` flag 定義為「sentinel non-inferiority ∧ P2」，因為 P2 失敗而連帶標為 false。
- P4：無漂移時 ΔFPR -0.0006 [-0.0035, +0.0011]，沒有發散 → PASS。

## 2. 描述性結果（不參與判定）
各模型、各臂的平均 post-onset FPR（frozen pre-onset 99% threshold）：
|                              |   gain |   level |   none |   ramp |
|:-----------------------------|-------:|--------:|-------:|-------:|
| ('gdeltanet', 'persistent')  |  0.046 |   0.664 |  0.024 |  0.508 |
| ('gdeltanet', 'reset')       |  0.047 |   0.668 |  0.023 |  0.507 |
| ('knn_append', 'persistent') |  0.049 |   0.056 |  0.03  |  0.04  |
| ('knn_append', 'reset')      |  0.127 |   0.568 |  0.058 |  0.44  |
| ('lstm', 'persistent')       |  0.047 |   0.38  |  0.032 |  0.32  |
| ('lstm', 'reset')            |  0.047 |   0.38  |  0.032 |  0.32  |
| ('mlstm', 'persistent')      |  0.04  |   0.505 |  0.024 |  0.381 |
| ('mlstm', 'reset')           |  0.04  |   0.526 |  0.025 |  0.4   |
| ('mlstm_std', 'reset')       |  0.046 |   0.57  |  0.024 |  0.454 |
| ('titans', 'persistent')     |  0.101 |   0.685 |  0.023 |  0.53  |
| ('titans', 'reset')          |  0.106 |   0.779 |  0.023 |  0.609 |
| ('window_only', 'single')    |  0.041 |   0.19  |  0.029 |  0.138 |

Sentinel recall（frozen pre-onset event threshold）：
|                              |   gain |   level |   none |   ramp |
|:-----------------------------|-------:|--------:|-------:|-------:|
| ('gdeltanet', 'persistent')  |  0.324 |   0.659 |  0.295 |  0.587 |
| ('gdeltanet', 'reset')       |  0.323 |   0.654 |  0.301 |  0.592 |
| ('knn_append', 'persistent') |  0.266 |   0.322 |  0.188 |  0.287 |
| ('knn_append', 'reset')      |  0.296 |   0.606 |  0.19  |  0.569 |
| ('lstm', 'persistent')       |  0.286 |   0.431 |  0.233 |  0.427 |
| ('lstm', 'reset')            |  0.286 |   0.431 |  0.232 |  0.427 |
| ('mlstm', 'persistent')      |  0.31  |   0.567 |  0.272 |  0.527 |
| ('mlstm', 'reset')           |  0.302 |   0.55  |  0.272 |  0.531 |
| ('mlstm_std', 'reset')       |  0.321 |   0.61  |  0.293 |  0.59  |
| ('titans', 'persistent')     |  0.338 |   0.617 |  0.289 |  0.571 |
| ('titans', 'reset')          |  0.37  |   0.69  |  0.319 |  0.653 |
| ('window_only', 'single')    |  0.26  |   0.397 |  0.23  |  0.363 |

要點：
1. **神經記憶的持續狀態幾乎沒有作用。** mLSTM 的 level ΔFPR 為 −0.021、ramp 為 −0.018；GDeltaNet、LSTM 都約為 0（LSTM 的 h05 只有 15–22 步，持續與 reset 兩臂在數值上相同）。所有神經 forecaster 在 2σ level shift 下的 FPR 都在 0.38–0.78，**記憶並沒有幫它們適應漂移**。
2. **Titans 不穩定。** 9 個 fit 發散或訓練出 NaN（其中 5 個是訓練 NaN），可量測的 h05 只出現在 1 台機台上，P4 FAIL。
3. **顯式記憶（kNN-append，參考臂）的效應大得多。** level FPR 從 reset 的 0.568 降到 persistent 的 0.056，ramp 從 0.440 降到 0.040。也就是說，在相同的漂移與門檻設定下，**「把新常態寫進記憶」的效益只在顯式記憶上出現**。這與 P10 pilot 的觀察一致，也對應 P7 的前提。
4. **方法學註記（供下一版 protocol 使用，不影響本次判定）。** 在 drift 條件下，frozen pre-onset event threshold 的 sentinel recall 會被 drift 本身的告警墊高：reset 臂的 FPR 已經很高，事件窗的最大分數幾乎一定超過門檻。因此 drift 條件下兩臂的 recall 差（例如 kNN 的 0.322 vs 0.606）**不能解讀為遮蔽**。本次的 P3 只用到 `none`，不受此影響。若未來 G-L2 或 P7 要在 drift 條件下比較 sentinel，需要改用 paired lift，例如以同時刻、無 sentinel 的 fork 作為基準。

## 3. 依決策樹的下一步
- G-L1 = **FAIL-PERSIST**（P2 也未通過）→ 依預宣告的決策樹進入 **G-L2**（drift-augmented 訓練，held-out family 為 gain 加一個新 family）。
- 交審查者決定：
  - (a) 依樹執行 G-L2，作為 P10 的最終關線檢驗；
  - (b) 鑑於神經記憶效應極小，而顯式記憶效應大，直接 STOP P10，把本結果作為論文第 3 章的負面量測，轉回 P7。
- **執行者意見：** 傾向 (b)，但 G-L2 已有大綱，只需 1–2 小時 GPU，若審查者要求可以照樹跑完。