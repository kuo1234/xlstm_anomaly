# P10 回應：對 ChatGPT 第一輪審查的意見與修正（2026-10-01）

## A. 接受的部分
| 項目 | 處理 |
|---|---|
| P10 只審 T1；T2b 改為 P11 候選；T2a 關閉；T3 擱置 | 接受。DyMETER（TPAMI 2026，10.1109/tpami.2026.3682661）已確認存在，T2a 與它的差異只剩條件輸入不同 |
| 「重複故障分數下降」本身不是新發現（twin-freak／DAMP、MemStream β-gate、CANDI） | 接受 |
| 主要估計量由 m(Δ)=s₂/s₁ 改為反事實的 write-induced masking（WIM） | 接受，但 branch 的定義要修正（見 B2） |
| G0：Memory Persistence Audit | 接受，並加上半衰期量測（見 B4） |
| Δ 以 memory-update 步數為單位 | 接受 |
| 移除 20% 的 STOP 門檻；先做 label-blind 的尺度 pilot，再封存門檻 | 接受 |
| 修正方法（雙時間尺度記憶）不放進主要主張 | 接受 |
| T2b 的「可撤銷」不是貢獻 | 接受，撤回原先的說法 |

## B. 補充與修正
### B1. Patched-DeltaNet 全文已讀（arXiv:2605.27992v1，PDF 存於 paper/）
- 設定：sliding window L=100、P=10，每個窗口只有 N=10 個 token。L 擴到 512k 只用於延遲與 VRAM 測試。
- 從論文描述看，state 的範圍是窗口內；文中沒有任何跨窗口保留 state 的串流推論，也沒有研究重複事件。
- 指標是 PA-F1 與 ROC-AUC。PA-F1 在本 repo 禁用。
- 「Δ≠0 時才更新」是數學上的誇大：Δ 幾乎不會恰好為 0。實際上每步都在寫入，只是寫入量隨 Δ 變化。
- 判定：屬於 G0 分類中的 within-window，不進主要實驗，只列為一級相關工作。對 T1 的威脅降低，但它的 event-driven framing 必須引用。

### B2. 反事實 branch 必須分開三種
對 gated 模型（mLSTM、Gated DeltaNet），「在 A₁ 凍結寫入」有歧義：跳過更新也會一併跳過遺忘衰減，使 F branch 保留更多舊記憶。Titans 還有 momentum S_t，若沒有一起凍結，surprise 會延續到後面。
| Branch | A₁ 期間的操作 | 回答的問題 |
|---|---|---|
| W | 正常寫入 | — |
| F-skip | state 不變（包含 momentum） | 寫入加上時間流逝的總效應 |
| F-decay | 只套用 forget／decay，不寫入 | 純寫入效應 |
| **F-sub（主要）** | A₁ 換成長度相同的正常段，正常寫入 | 寫入異常相對於寫入正常的效應；步數與衰減完全相同 |

主要估計量：WIM_sub(Δ) = q(s₂^{F-sub}) − q(s₂^{W})。
- q(·) 是該 branch 以 A₁ 之前的正常分數分佈計算的分位數（rank）。不用 |s₂^F| 正規化，因為 s₂^F 接近 0 時數值不穩。
- 部署層面的指標：event recall 差異。threshold 在 A₁ 之前校準後即凍結，固定 FPR。
- 所有 branch 都必須 score-before-write。

### B3. 與 twin-freak 的真正分界：masking kernel
- kNN 或明確記憶只會遮蔽近似重複的片段，也就是 twin-freak。分散式寫入可能遮蔽變體：不同振幅、不同通道、同一族的不同形狀。
- 新的 RQ2'：WIM 作為 sim(A₁, A₂) 的函數。sim 由同類型、振幅、通道、形狀分層控制。
- 附帶效應：A₁ 的寫入對之後正常段分數的影響（FPR 漂移），以及對其他故障類型的影響。
- STOP 規則：若所有 neural memory 的 masking kernel 寬度與 kNN-append baseline 在誤差內相同，就判定為 neural twin-freak，P10 停止。

### B4. 缺少的 RQ0：持續記憶的效益
- 如果持續的串流記憶沒有帶來任何好處，簡單的解法就是每個窗口 reset state，現象本身也就無關緊要（審稿人會說沒有人這樣部署）。
- RQ0：在 benign drift（setpoint 改變、緩慢老化、注入的正常模式變化）下，persistent 相對於 reset 是否降低 FPR、提升適應？
- P10 的主張因此是一個取捨：適應效益 vs WIM 成本。這也接回原始動機：部署後退化，但不想重新訓練。
- RQ0 若顯示無效益，可在封存前就 STOP。
- G0 另外量測每個機制的 state 脈衝響應半衰期 h。Δ 同時以步數與 Δ/h 報告。

### B5. 修正後的 RQ
- RQ0 Utility：persistent 相對於 reset 在 benign drift 下的效益。
- RQ1 Existence：WIM_sub(Δ) > 0？
- RQ2 Mechanism：WIM 與 ‖ΔM_{A₁}‖、decay、Δ/h 的關係。
- RQ2' Masking kernel：WIM 與 sim(A₁, A₂) 的關係，以及 kNN-append 對照。
- RQ3 Architecture：fixed-weight LSTM／xLSTM sLSTM、fast-weight（mLSTM、Gated DeltaNet）、test-time learned（Titans LMM、TTT）、explicit kNN-append、window-only。

### B6. 資料與治理
- 主資料是 SMD train split 加故障注入。A₁ 與 A₂ 都由注入產生，ground truth 不需要開啟 SMD label，符合 label-access 規則。
- train split 中可能存在未標記的既有異常，視為噪聲，並以多個注入位置平均。
- CARE v6 只做 episode 層級的 sanity check。

### B7. 佔位審查第五個攻擊點（新增）
在原本四個攻擊點之外加一項：
- 5. TSAD 實務上是否有人用持續 state 部署 linear-RNN／TTT／Titans？例如 streaming SSM detector、TTT-for-TS、Reverso 類 TSFM 的串流模式。
- 若沒有：RQ0 是必要的。
- 若有：他們是否報告過遮蔽現象？

## C. 建議下一步
1. P10 的 P7 等級佔位審查，涵蓋五個攻擊點，至少 40 篇。
2. 開 GitHub issue P10 與 docs-only 分支（proposal v0.1 包含上述 RQ0–RQ3、G0、三種 branch、masking kernel 的 STOP 規則），交給 ChatGPT／Codex 做二次審查。
3. 在審查完成之前，不跑 GB10 gate。
