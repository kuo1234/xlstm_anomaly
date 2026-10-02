# P10 決策備忘錄：Writable Neural Memory in Streaming TSAD（T1）
日期：2026-10-02｜狀態：**CONDITIONAL（REFRAME）**，非 GO。需先通過一個決定性 gate（G-L），否則 STOP。

## 1. 一句話結論
- 「寫入造成的遮蔽」這個**估計量**沒有被佔：在 75 篇篩選中，沒有任何反事實的 write vs no-write 量測，也沒有 masking-kernel 量測。
- 但這個**現象**對目前部署的偵測器不重要。業界標準是每個窗口 reset state（deployment 審查的 39 篇中有 24 篇是 within-window）。在探索性 pilot 中，持續狀態對神經記憶**沒有效益，甚至有害**；WIM 只在 Δ≈16 對 mLSTM 出現，Δ≥64 就消失。
- 唯一能翻案的條件：記憶在長序列上訓練後，持續狀態確實帶來效益。這要用 G-L 一次判定。

## 2. 證據
### 2.1 佔位審查（audit/；兩個 track，共篩選 75 篇，40 篇有全文，全文以關鍵字或段落定點閱讀；OpenAlex／Semantic Scholar 未完成，所有「不存在」的判定都是 provisional）
| 攻擊點 | 判定 | 要點 |
|---|---|---|
| AP1 test-time／fast-weight 記憶被異常污染 | PARTIAL | 「線上適應會吸收壞輸入」是已知概念：vision TTA poisoning（TePA、DIA）、Mamba hidden-state 覆寫（HiSPA 2601.01972）、LLM memory poisoning（MemPoison 2605.29960）、MemStream §5.4、CANDI。但沒有人研究 Titans／TTT／DeltaNet／mLSTM 的 state 在 TSAD 中被異常污染後，如何影響之後的事件 |
| AP2 重複異常衰減的反事實或 kernel 量測 | **OPEN** | DAMP 把 twin-freak 列為設計前提，但沒有對 Δ 或相似度量化；MemStream 只在初始化時放入一個異常 |
| AP3 baseline 對照 | PARTIAL | 每篇量的東西都不同；kNN-append（DAMP、TTAMB）是 RQ2' 的必要對照 |
| AP5a 跨窗口持續 state 的 linear-RNN／SSM 偵測器 | OPEN（provisional） | 只有 2503.22743（合成資料、無 ablation） |
| AP5b TSFM 的 in-context 污染 | 在 recurrence 層面 OPEN；在窗口內吸收層面 PARTIAL | TimeRCD 自承窗口內的 outlier 可能被吸收進局部參考 |
| AP3/4 是否只是 neural twin-freak 或 memory poisoning | PARTIAL threat | 概念層面已被 kNN／AE 記憶佔據，估計量仍 OPEN |
| AP6 每窗口 reset 是否為標準 | **是 → RQ0 必要** | — |

最強的審稿反論（deployment 審查）：T1 只是把已知的 adaptation-vs-absorption trade-off（MemStream 2022、Saurav 2018、HTM）套到新架構上；對 delta-rule 記憶而言，遮蔽可以從 closed form 預測，而 kernel 不過是 learned-metric 的 kNN-append（TTAMB 已在 TSFM AD 中部署帶 novelty gate 的版本）。要推翻這個反論，必須**同時**做到：(1) 實測 WIM 偏離 closed form；(2) 神經 kernel 與 matched kNN-append 的 CI 不重疊；(3) MemStream 式的 write gate 會付出可量測的 benign-drift utility；(4) RQ0 持續狀態以預宣告的 margin 勝過 reset。

### 2.2 探索性 pilot（pilot/；label-blind、CPU、SMD 1-4／2-1 只用 train split、48 個注入 unit、單一訓練 seed；**不是 sealed gate**）
- G0：除了 Titans（machine 2-1 不可靠）之外，所有參數化記憶的 h05 ≤ 54 步、h50 ≤ 5 步。記憶範圍被 128 步的訓練序列限制住。
- RQ0（漂移後 FPR，持續 − reset）：
  - mLSTM +0.040 [0.016, 0.071]、Titans +0.048 [0.012, 0.094]：持續狀態**有害**。
  - LSTM ≈ 0；GDeltaNet −0.009：可忽略。
  - **只有 kNN-append −0.065 [−0.108, −0.028] 有益**。
- RQ1（WIM_sub）：
  - Δ ≤ 8 時 window-only 本身也有大 WIM，那是窗口內污染。
  - Δ = 16：只有 mLSTM 出現效應，A2 分數降低 13–25%（log ratio −0.15 至 −0.29，五種故障的 CI 都排除 0），但換成 q 單位只有 ≤ 0.085。
  - Δ ≥ 64：所有神經記憶的 WIM ≈ 0。
  - kNN-append 只在高振幅 spike 上有不隨 Δ 衰減的小幅遮蔽（Δ = 1024 時 log ratio −0.136）。
- RQ2'：神經 kernel 平坦且雜訊大，**沒有證據顯示比 kNN-append 更寬**（統計檢定力不足）。

### 2.3 附帶發現（對 P7 有利）
在 pilot 中，同時具有「持續有益」（漂移下 FPR 0.092 → 0.027）與「持續遮蔽」（Δ = 1024 仍存在）的，只有**顯式 kNN-append 記憶**。這正是 P7 研究的 adaptation-vs-absorption trade-off，所以 P10 的 pilot 反而為 P7 提供了實證動機。

## 3. 決定性 gate G-L（Long-horizon persistence utility）：要預先封存後才執行
- 目的：排除「null 是訓練設定造成的」這個解釋。
- 設定：mLSTM、Gated DeltaNet、Titans-LMM。
  - 以 ≥ 2048 步的序列訓練。
  - 加入 benign drift 增強（level／ramp／setpoint，隨機起點），讓記憶被訓練去承載適應。
  - 至少 3 個訓練 seed × 2 台機器（建議再加 SMD machine-1-x／3-x 的 train split 擴到 ≥ 4 台）。
  - 對照：reset、window-only、kNN-append。
- PASS 條件：至少一個神經記憶在 G0 達到 h05 ≥ 256，**且**在 level 與 ramp 兩種漂移下，持續 − reset 的 FPR 差 ≤ −0.02，95% CI 上界 < 0。
- FAIL → **STOP T1**，寫成一頁負面紀錄，主線回到 P7。
- PASS → 執行 sealed 的 WIM 與 kernel 測試（§4）。
- 成本估計：CPU 或 GB10，1–3 天。

## 4. Proposal v0.1（僅在 G-L PASS 後啟用）
- RQ0 utility；RQ1 existence：WIM_sub(Δ)，Δ ∈ [2K, 4·h05]；RQ2 mechanism：‖ΔM_A1‖、decay、Δ/h；RQ2' kernel vs matched kNN-append；RQ3 architecture。
- Branch：W／F-sub（主要）／F-sub2（null）／F-skip／F-decay；score-before-write；q = 該 branch pre-A1 正常分數的分位數，另報 log(s2_W / s2_Fsub)。
- 主要終點草案（來自 pilot 尺度）：相對 window-only 的成對 WIM 差 ≥ 0.05（q 單位），95% CI 下界 > 0；≥ 48 unit × ≥ 3 seed。次要終點：log ratio ≤ −0.18（約降低 16% 以上）。振幅限 1u–2u，避免 q 飽和。
- STOP 規則：
  - 神經 kernel 與 kNN-append 在 CI 內相同 → neural twin-freak，STOP。
  - WIM 與 delta-rule 的 closed-form 預測在誤差內一致 → 只剩工程結論，降為 workshop 級。
- 修正方法（surprise clipping／score-gated write／episodic checkpoint）不放進主要主張。

## 5. 建議時程
- 本週封存 G-L，1–3 天跑完。
- FAIL：立即回到 P7 v0.4 收斂論文主題，並把本 pilot 的 kNN-append 結果當作 P7 的動機實驗。
- PASS：P10 成為主線，P7 降為 related work 或第二章。
