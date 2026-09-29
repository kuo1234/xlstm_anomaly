# 研究計畫大綱 v0.2：少樣本通用機台異常偵測器的雙快取持續適應（2026-09-29）

## 題目（暫定）

**中文**：以操作員回饋維護之雙快取少樣本機台異常偵測——兼顧機台老化與新型故障

**English**: *Feedback-Maintained Dual-Cache Adaptation for Few-Shot Machine Anomaly Detection under Aging and Emerging Faults*

---

## 0. 一句話定位

一個凍結的通用偵測器，給它 K 筆新機台的正常樣本就能上線。之後靠兩個 cache 持續學習：
- **正常 cache**：吸收機台老化，也就是良性的漂移。
- **故障 cache**：記住操作員確認過的新型故障。

**cache 的更新由操作員回饋驅動**，包括確認故障、駁回誤報，以及對尚未確認的資料先做隔離。本研究要回答的核心問題是：**什麼時候只動 cache 就夠，什麼時候必須動權重？**

---

## 1. 為什麼需要操作員回饋

repo #3 已經確立：**只看訊號本身，無法區分良性新工況和持續故障**。這代表只靠自身的偽標籤就吸收漂移（TDA 就是這樣做），在機台上一定會碰到「把故障學成正常」的問題。

機台現場本來就有一個真實的回饋通道：**警報會被技師確認或駁回**。這個回饋有三個特性：稀疏、延遲、偶爾出錯。把這個通道正式納入設計，問題才定義得清楚，這也是本研究和 TDA、DPE 一類「用自己的預測來更新 cache」的方法最根本的差別。

---

## 2. 文獻缺口審查摘要（本輪驗證 49 篇，另有前兩輪的 75 篇）

| 缺口 | 判定 | 最接近的工作 | 還沒被做的部分 |
|---|---|---|---|
| G4a 凍結通用偵測器＋新機台 few-shot cache | PARTIALLY_OCCUPIED | DADA（ICLR 2025，零樣本通用 TSAD）；PatchCore few-shot；**DCASE 2023–2024 Task 2 first-shot**（聲音模態，凍結 embedding＋kNN） | 多變量感測器時間序列，而且沒有「正常＋故障」雙 cache 的融合分數 |
| G4b 以延遲操作員回饋更新雙 cache，並隔離未確認資料 | PARTIALLY_OCCUPIED（各元件分散在三條文獻） | 雙 cache：TDA、DMN（CVPR 2024，但用的是偽標籤）；回饋：AAD（ICDM 2016）、Siddiqui（KDD 2018）、DeepLog（CCS 2017，用誤報重訓）；已知與未知異常：DRA（CVPR 2022） | 三者沒有被組合起來，也沒有隔離機制，更沒有用在時間序列上 |
| G4c cache-only（L0）、輕量微調（L1）、adapter（L2）在相同回饋預算下的正面比較，並附適應傷害指標 | **OPEN_AT_SEARCH_DEPTH** | 只有同一篇論文內的 ablation（Tip-Adapter vs. Tip-Adapter-F）；PromptAD 指出只用 cache 在 one-class 設定下不夠 | 跨方法、相同預算、有 false-absorption 指標的比較，在任何領域都沒找到 |
| G4d 同一機制既吸收老化又學新故障，並量測是否誤吸收故障 | **OPEN_AT_SEARCH_DEPTH** | AnDri（正常 pattern 池）；UCAD、IUF（新類別由實驗者依序給定，而且要重新訓練） | — |
| G4e few-shot 下的閾值與 FPR 可靠度 | PARTIALLY_OCCUPIED | ColdFusion（ACL Findings 2024）、COLDSTART | 閾值可靠度與「持續演化的雙 cache」之間的耦合 |
| G4f 在真實機台、長期部署、多種故障型態下評估 | **OPEN_AT_SEARCH_DEPTH** | DCASE 只有單次評估；MIMII-DG 的 shift 是實驗誘發的 | — |
| G4g Tip-Adapter／TDA 式 cache 轉移到時間序列 | **OPEN_AT_SEARCH_DEPTH** | 整條 cache-adapter 文獻都只做 CLIP 影像分類 | — |

**主要威脅**：
1. DCASE first-shot 已經證明「凍結 embedding＋kNN、不調參」在機台聲音上很強。所以本研究不能只證明 cache 有用，而要證明 **cache 在長期、回饋有噪音的情況下哪裡會壞掉，以及該怎麼修**。
2. TAB（PVLDB 2025）的基準測試顯示，基礎模型或預訓練 TSAD 在多變量工業序列上**還不是最強**。「凍結的通用骨幹夠好」這個前提必須先用 pilot 驗證（見 §7 的 M2 查核點）。
3. 這一輪 arXiv 和 Semantic Scholar 有 rate limit，較新的預印本可能漏掉。Tip-Adapter、AAD 只驗證到書目資料。

---

## 3. 研究問題

| RQ | 問題 | 缺口 |
|---|---|---|
| RQ1 啟用 | 新機台只有 K 筆正常樣本（K = 1 天、3 天、7 天、14 天）時，凍結骨幹＋正常 cache 的偵測能力與**固定閾值下的 FPR**，和逐台訓練的偵測器、DADA 零樣本相比如何？K 需要多大才夠？ | G4a、G4e |
| RQ2 老化 | 長期部署中，正常 cache 採用哪種更新策略，能在「FPR 不隨時間上升」和「不誤吸收故障」之間取得最好的平衡？ | G4d |
| RQ3 新故障 | 某種新故障被確認 k 次（k = 1、3、5）後，故障 cache 對同型故障再發生的召回率如何？對從沒見過的故障型態是否仍有泛化能力？ | G4b、G4d |
| RQ4 cache vs. 權重 | 在相同回饋預算下，L0（只動 cache）、L1（調融合權重 α、閾值、cache key）、L2（小 adapter）的偵測能力、適應傷害、回滾能力與算力如何取捨？ | **G4c（核心貢獻）** |
| RQ5 回饋品質 | 操作員延遲 D、漏答率、誤判率 e 對各策略的影響為何？什麼程度以上方法會失效？ | G4b |

---

## 4. 方法設計

### 4.1 架構

```
輸入視窗 x_t ──► 凍結通用 encoder f_θ ──► embedding z_t
                    │                       │
                    │ 骨幹分數 s_b          ├──► 正常 cache N：kNN 距離 d_N
                    │                       └──► 故障 cache F：相似度 sim_F（附故障型態標籤）
                    ▼
       最終分數 s = α·s_b + β·d_N + γ·sim_F   → 閾值 τ → 警報
       警報 → 操作員（延遲 D，誤判率 e）→ 確認或駁回 → 更新 cache
```

- **骨幹**：先以 fleet 內的來源機台自監督預訓練（leave-one-farm-out），再與 DADA、MOMENT 等公開通用模型比較。novelty 不綁骨幹。
- **正常 cache**：初始為 K-shot 樣本，做 coreset 取樣（PatchCore 式）。
- **故障 cache**：初始為空，或放來源機台已知的故障樣本。

### 4.2 cache 生命週期（本研究的方法核心）

每筆 cache 條目的狀態：`quarantine → active → reserve → evicted`

| 事件 | 動作 |
|---|---|
| 未觸發警報的新資料 | 在正常 cache 的 quarantine 停留 dwell 時間 T；期間沒有被確認為故障，才轉為 active（吸收老化） |
| 警報被**駁回**（誤報） | 直接寫入正常 cache，這是最強的「新正常」證據 |
| 警報被**確認**為故障 | 寫入故障 cache，附上型態標籤；同時把同一時段、還在 quarantine 的正常條目**撤回**（精確回滾） |
| 容量已滿 | 依效用、涵蓋率、時間衰減淘汰；每個工況保留最少數量（延續 v0.1 的效用淘汰概念） |
| 閾值 τ | 依正常 cache 近期的分數分布做滾動校準（conformal 式）；只用已經 active 的條目，避免汙染 |

### 4.3 三級適應（RQ4）

- **L0**：只做上表的 cache 操作，不做任何反向傳播。
- **L1**：用累積的確認和駁回樣本，微調 α、β、γ、τ 與 cache key（Tip-Adapter-F 式）。
- **L2**：在凍結骨幹上加一個小 adapter，用同一批回饋樣本訓練。
- 所有層級使用**相同的回饋預算**，例如每月最多 B 次確認。

### 4.4 Baselines

- 靜態系列：DADA 零樣本；PatchCore 式靜態 cache；逐台訓練的 AE 或 LSTM 偵測器（可沿用 repo 的程式）。
- 自我更新系列：TDA 式偽標籤雙 cache；MemStream；M2N2 或 CANDI 類的正常參考更新。
- 回饋系列：AAD 式回饋重新加權；DeepLog 式用誤報重訓。
- 上界參考：定期全量重訓。

---

## 5. 資料集

| 角色 | 資料集 | 理由 | 注意事項 |
|---|---|---|---|
| **主資料** | CARE to Compare（Zenodo 14006163） | 36 台風機、3 座風場、89 turbine-years、44 個標註的故障事件（含故障型態）。可以做 leave-one-farm／turbine-out 的新機台啟用，也有長期老化和多種故障 | CC-BY-SA 授權；5.5 GB；需使用最新版本 |
| 次要：老化 | MetroPT-3（UCI 791） | 真實空壓機，有維修紀錄的真實故障 | 單一機台，時間跨度 6 個月 |
| 次要：跨機台 few-shot | MIMII-DG／DCASE Task 2 | 與 first-shot 文獻直接對齊 | 聲音模態 |
| 受控實驗：新故障型態 | Tennessee Eastman（20 種故障） | 可以精確控制「新故障型態第一次出現」的時間點 | 模擬資料；官方頁面這次無法連線 |
| 真值建構 | 在 CARE 的正常段注入半合成老化（漸進增益、偏移）與故障 | 取得逐時間點的真值，用於量測 false absorption | 注入的型態要事先封存 |

**模擬操作員**：以資料的真實標籤為基礎，加上延遲 D、漏答率與誤判率 e（例如 D ∈ {1 天, 7 天}、e ∈ {0, 5%, 15%}）。這是 RQ5 的實驗軸。

---

## 6. 評估指標

1. **偵測**：AP、AUROC、事件層級 F1、偵測延遲。
2. **部署可靠度**：固定閾值下正常資料的 FPR，以及 FPR 隨部署月份的變化曲線（延續 M1 的教訓：AP 高不代表可以部署）。
3. **適應安全**：
   - false absorption：故障被寫入正常 cache 的比例，以及之後漏報的時長。
   - 良性老化的適應延遲。
   - 回滾之後的殘留影響。
4. **學習新故障**：recall@k 次確認；對未見過故障型態的召回率。
5. **成本**：需要的回饋次數、cache 容量、每步延遲、L1／L2 的訓練時間。
6. **統計**：以機台或風場為單位做 paired bootstrap。margin 和比較家族在看結果前先寫好，沿用 repo 的 seal 流程，但做輕量版。

---

## 7. 時程（約 10 個月）

| 月 | 工作 | 查核點 |
|---|---|---|
| 1 | 用 Scopus 補搜尋（重點查 streaming few-shot TSAD 與工業期刊）；下載 CARE to Compare；寫操作員模擬器和不洩漏資訊的評估框架 | 單元測試：cache 更新只能用到已經到達的回饋 |
| 2 | **Pilot**：凍結骨幹＋K-shot 靜態 cache vs. 逐台訓練偵測器 vs. DADA | **Go／no-go**：凍結骨幹至少要接近逐台訓練的水準。如果不行，就改用 fleet 自監督預訓練的骨幹 |
| 3 | RQ1：K 掃描與閾值可靠度 | |
| 4–5 | RQ2：正常 cache 生命週期（隔離、駁回寫入、回滾）；半合成老化注入 | false absorption 曲線 |
| 6 | RQ3：故障 cache 與新型態故障 | recall@k |
| 7 | RQ4：比較 L0、L1、L2 | **核心結果** |
| 8 | RQ5：回饋噪音掃描；MetroPT、MIMII 外部驗證 | |
| 9–10 | 撰寫論文、投稿（例如 IEEE TII、PHM Society、KDD／CIKM applied track） | |

---

## 8. 風險與停損

| 風險 | 應對 |
|---|---|
| 凍結通用骨幹在 CARE 上表現太差（TAB 的警訊） | 骨幹改為 fleet 內預訓練。研究重點本來就在 cache 生命週期，不受影響 |
| L0 在所有情況都和 L1、L2 一樣好 | 這本身就是有價值的結論：training-free 就夠。論文重點轉為「cache 在哪些條件下會壞」 |
| L0 在所有情況都比 L2 差很多 | 報告 cache 失效的機制（例如老化方向與故障方向重疊），轉為分析型貢獻 |
| CARE 的故障事件太少（44 個），統計檢定力不足 | 用半合成注入擴充，TEP 做受控補充；報告信賴區間，不誇大結論 |
| 有新論文搶先 | 核心貢獻放在 G4c 的比較協定與 false-absorption 評估，這部分最難被完全取代 |

---

## 9. 與 repo 及 v0.1 的關係

- 本計畫實際上把 repo 的幾個 backlog 整合成一篇論文：#9／#10（P5／P6，新機台啟用與就緒）→ RQ1；#6（P2，隔離、延遲確認、回滾）→ §4.2；#5（P1，汙染指標）→ §6 第 3 點；#8（P4，機群）→ 用 fleet 預訓練骨幹。
- 延續 M1 的結論：novelty 不綁 xLSTM；ranking 與 operating point 要分開評估。
- v0.1 的檢索式**預測**計畫保留為備案。它的效用淘汰機制已經併入 §4.2 的容量管理。

---

## 附：審查輸出檔

- few-shot TSAD 缺口審查：[fs_detector_gap_audit.md]({{artifact:7056e445-cd0e-404f-8b65-961a275605a8}})；[fs_detector_papers.json]({{artifact:7b2f8b56-dc85-4241-9cb3-9dc5d464a6f1}})（29 篇）
- cache 與回饋缺口審查：[cache_feedback_gap_audit.md]({{artifact:786e7f1c-0862-4b8f-a9fd-6ed85f48ab8e}})；[cache_feedback_papers.json]({{artifact:84d62eab-9222-4db6-bd37-91ba56648b9e}})（20 篇）
- 資料集審查（前一輪）：[datasets_audit.md]({{artifact:aaf41d9f-a481-4204-9fde-89349a3d2ed3}})
- v0.1 預測版計畫：[thesis_proposal_outline.md]({{artifact:8cf9313b-23fd-4f99-b80f-ca17193e4e78}})

**審查限制**：OPEN_AT_SEARCH_DEPTH 只代表在本次查詢範圍內沒找到。這一輪 arXiv 和 Semantic Scholar 有 rate limit，部分查詢改走 OpenAlex，最新的預印本可能有遺漏。Tip-Adapter、AAD 只驗證到書目資料；IUF 和 DCASE 2024 的說明論文只讀了摘要；CWRU 和 TEP 的官方頁面無法連線，只透過次要來源確認。
