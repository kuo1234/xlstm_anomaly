# P10 G-L1 Protocol v0.2：Standard long-horizon persistence utility gate
狀態：**DRAFT，未 seal，未執行。** 審查通過並取得 Active Handoff 之後，才實作 runner／tests 並 seal。
來源：issue #15 第二次審查（comment 5945068125）的 10 點修正；本文件只處理 G-L1，G-L2 只列大綱（§10）。

## 0. G-L1 要回答的一句話
> 在**不做任何為 gate 量身打造的 drift augmentation** 的標準長序列訓練下，可寫神經記憶（primary：mLSTM 矩陣記憶）跨窗口持續保留 state，相對於同一組權重的 per-window reset，是否在未見過的良性漂移下帶來部署效益，**而且這個效益不是靠整體分數塌陷換來的**？

G-L1 不量測 WIM。它是 P10 的前置條件：持續記憶若沒有效益，recurrence masking 就沒有研究價值。

## 1. 資料（label-blind；只用 train split）
- 主要機台（6 台；以 seed 20261002 從合格集合中隨機抽出，見 `gl1_data_manifest.csv`）：machine-3-7、1-6、2-7、3-5、2-9、1-3。
- 備用機台（依序遞補，只在 §8 的 validity 失敗時使用）：2-6、3-9、2-2。
- 排除：1-4、2-1（P10 pilot 用過）、1-8（R0 用過）。這三台只能作 secondary replication，不進 primary 推論。
- 來源：OmniAnomaly `ServerMachineDataset/train/<machine>.txt`。**test 與 test_label 不下載、不開啟。** 不使用 point-adjust。
- 切分（每台）：前 50% 為 fit 區，其中前 80% 訓練、後 20% 驗證；後 50% 為 stream 區（11.8k–14.4k 步）。fit 區 sd < 1e-3 的通道整條刪除。z-score 參數只從 fit 區估計（sd 下限 0.02）。
- 宣告的假設：train split 視為常態，但可能含未標記異常。ground truth 只來自注入事件。

## 2. 模型
| 角色 | 模型 | 狀態 |
|---|---|---|
| **Primary** | mLSTM（矩陣記憶 C_t = f_t C_{t−1} + i_t v_t k_tᵀ，exp 或 sigmoid gate 依實作宣告） | persistent 與 reset |
| Replication | Gated DeltaNet（S_t = α_t S_{t−1}(I − β_t k_t k_tᵀ) + β_t v_t k_tᵀ） | persistent 與 reset |
| Replication | Titans-style LMM（MLP 記憶；test-time 以 ‖M(k) − v‖² 的梯度、momentum η、decay α 更新） | persistent 與 reset |
| 參考：固定權重 recurrence | LSTM | persistent 與 reset |
| 參考：無跨窗 state | window-only MLP，lookback K = R = 100 | — |
| 參考：顯式記憶 | kNN-append（persistent：每個評分窗之後 append；reset：bank 固定為 fit 區） | 只報告 |
| Secondary 實務基線 | mLSTM-std：以 L = 100、零初始 state 訓練，windowed 推論 | 只報告 |

- 所有神經模型都是 one-step forecaster：ŷ_{t+1} = z_t + head(state)。score = 以驗證區殘差 σ 標準化的均方誤差。**一律 score-before-write**。
- 參數量對齊：各模型 60k–80k 可訓練參數，互差在 ±10% 以內，實際數字寫進 config。
- reset 臂定義：使用**同一組權重**，在 t 時刻的 state 由零 state 起，只看 x[t−R+1, t] 計算（R = 100，與 SMD 常見窗口長度及 Patched-DeltaNet 的 L 相同）。這就是業界標準的 within-window 推論。primary 對照因此是在相同權重下「持續 state」與「窗口內 state」的因果差異。

## 3. 訓練（標準長序列，**沒有 drift augmentation**）
- 目標：fit 區上的 one-step MSE。
- 序列長度 L = 2048，batch 8。使用 stateful TBPTT：同一輪內的相鄰 chunk 攜帶 detached state；每輪的起點 offset 隨機；每輪第一個 chunk 從零 state 開始。
- 優化：Adam，lr 1e-3，grad clip 1.0，最多 4000 iterations。早停依據驗證區的串流 one-step MSE（攜帶 state），patience 5 次評估、每 200 iterations 評估一次。
- 訓練 seed：11、22、33（沿用 repo 慣例）。
- Titans 的 inner-loop 超參數（η、α、inner lr）在 config 中固定，**不依任何 gate 結果調整**。
- 必要的實作測試：parity test 要求逐步 recurrent 推論與訓練時 forward 的最大差 < 1e-4；state-norm 監控在出現 NaN 或 Inf 時 fail closed。

## 4. 前置條件 P1：Persistence
- G0 脈衝響應：在 stream 區 12 個位置，對 8 個通道注入 3u 的單步脈衝；以 forecast 差的絕對值計算 h50 與 h05（lag 1 為基準）。
- P1 PASS：primary 模型在 ≥ 4／6 台機台上，跨 seed 的 h05 中位數 ≥ 4R = 400 步。

## 5. 主要終點 P2：Benign utility（三個 drift family 都未出現在訓練中）
- Drift family：
  - F1 level shift：+2σ，8 個隨機的非常數通道，正負號隨機，持續到 episode 結束。
  - F2 ramp：在 512 步內由 0 線性增加到 2σ，之後維持。
  - F3 gain：把偏離 fit 區通道平均的部分放大 ×1.5，同樣 8 個通道。
- Episode：每台機台、每個 family 24 個 onset t0。onset 以 seed 902 在 [stream_start + 2048, stream_end − 1024] 內均勻抽樣。
  - persistent 臂從 stream 起點連續執行到 t0（中間不注入），在 t0 fork 出注入分支。
  - calibration 窗為 [t0 − 1024, t0)，threshold 取該臂自己在此窗內分數的 99th percentile。
  - 評估窗為 [t0, t0 + 1024)。
- 終點：ΔFPR = FPR_persist − FPR_reset。secondary 另報後半窗 [t0 + 512, t0 + 1024) 與時間曲線。
- P2 PASS：F1／F2／F3 中**至少 2 個** family 同時滿足點估計 ≤ −0.02，以及 hierarchical 95% CI 上界 < 0。

## 6. Guardrail P3：No score collapse（用 sentinel 檢查敏感度）
- Sentinel fault：S1 spike burst（2u、5 通道、30 步）、S2 stuck（6 通道、30 步）、S3 correlation break（6 通道換成遠處真實片段，30 步）。
- 注入方式：在每個 drift episode 的評估窗內，以及在無漂移 stream 中，另外 fork 一份副本注入 sentinel。sentinel 只用於評分，**副本在評分後丟棄，記憶永遠看不到 sentinel**。
- 偵測定義（避免 drift 本身墊高的分數混入 recall）：sentinel 事件窗的最大分數，在**同一臂、同一時段、未注入 sentinel 的 30 步窗最大分數分佈**中的分位數 q > 0.95 時，算作偵測到。
- P3 PASS：對 P2 中通過的每個 family，以及無漂移條件，Recall_persist − Recall_reset 的 hierarchical 95% CI 下界 > −0.02（non-inferiority margin 0.02），三種 sentinel 合併計算；各類型分開列出。
- 若 P2 通過但 P3 失敗，判為 **FAIL-COLLAPSE**，不能稱為 utility PASS。

## 7. Guardrail P4：長串流穩定性
- 無漂移 stream 的 24 個 episode 中，FPR_persist − FPR_reset 的 95% CI 上界 ≤ +0.01。
- 整段 stream 不得出現 state norm 發散（超過訓練期最大值的 100 倍即視為發散）。

## 8. Validity（fail-closed）
- 一個 fit（模型 × 機台 × seed）有效的條件：驗證區串流 one-step MSE ≤ 1.5 × 同機台、同 seed 的 window-only 驗證 MSE，parity test 通過，且 P4 沒有發散。
- 無效的 fit 要排除並列出。primary（mLSTM）若有效機台少於 4 台（「有效機台」指至少 2 個有效 seed），依序用備用機台遞補一次；遞補後仍少於 4 台，判為 **INCONCLUSIVE**，並視同 FAIL 進入 G-L2。

## 9. 統計
- Hierarchical paired bootstrap：外層重抽 machine，中層在 machine 內重抽 seed，內層在 seed 內重抽 episode。B = 10,000，bootstrap seed 901。
- 每台機台的 paired effect 另外列表。
- primary 判定**只看 mLSTM**（避免只挑贏家）。GDeltaNet 與 Titans 用同一套準則報告；「writable memory family」層級的主張需要包含 primary 在內至少 2 種機制都 PASS。
- LSTM、kNN-append、mLSTM-std 只報告，不參與判定。

## 10. 決策樹
| 結果 | 判定 | 下一步 |
|---|---|---|
| mLSTM 的 P1、P2、P3、P4 都通過，且 validity 成立 | **G-L1 PASS** | 撰寫並 seal WIM protocol v0.3：主要估計量 WIM_write，次要 WIM_sub；Δ/h05 ∈ {0.25, 0.5, 1, 2, 4}，h05 取自本 gate 的 mLSTM |
| P1 失敗 | FAIL-PERSIST | 進入 G-L2 |
| P1 通過、P2 失敗 | FAIL-UTILITY | 進入 G-L2 |
| P2 通過、P3 失敗 | FAIL-COLLAPSE | 進入 G-L2，並記錄「效益來自分數塌陷」 |
| INCONCLUSIVE | 視同 FAIL | 進入 G-L2 |

G-L2 大綱（另外 seal）：
- 以 F1 + F2 + setpoint 做 drift-augmented 訓練；**F3 gain 與一個新的 family（例如 variance 改變）保留為 held-out**。
- PASS 必須在 held-out family 上成立，且 P3、P4 同樣要通過。
- G-L1 FAIL 但 G-L2 PASS：改題為「adaptation-trained writable memory 的 utility–masking trade-off」，不得宣稱可寫記憶天生具有部署效益。
- 兩者都 FAIL：**STOP P10**。改寫成論文第 3 章的負面量測結果，主線回到 P7。

## 11. Seal 與執行流程（沿用 repo 的 phase-gated 慣例）
1. 本文件與 `gl1_config_draft.yaml` 交給審查者。
2. 取得 Active Handoff。
3. 實作 `scripts/p10_gl1_*.py`、tests（parity、label-blind 檢查、score-before-write）。
4. seal commit：protocol、config、runner、tests 的 SHA256SUMS。
5. 在 GB10 的 worktree 執行。
6. 結果另開 commit，附 decision file。

## 12. 預估成本
- 訓練：primary 與 replication 共 4 個模型（mLSTM、GDeltaNet、Titans、LSTM），加上 window-only 與 mLSTM-std，合計 6 機台 × 3 seed × 6 = 108 個 fit。
- 每個 fit 的時間取決於實作。chunkwise 平行實作在 GB10 上估計每個 10–20 分鐘，合計約 20–35 GPU 小時（未實測）。
- reset 臂的 windowed 推論，必須以「每個 t 一個長度 R 的窗」做 batched／平行計算，否則 O(T·R) 的逐步計算會成為瓶頸。
- 評估：fork 式 episode 每機台約 (3 drift + 1 無漂移) × 24 × 2 臂，加上 sentinel fork，主要成本是串流推論。

## 13. 本 gate 不宣稱的事
- 不宣稱任何 WIM 或遮蔽相關結論。
- 不宣稱可分辨 benign 與 fault（受 #3 可識別性邊界限制）。
- 不把 kNN-append 結果用於判定。
