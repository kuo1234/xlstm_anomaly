# 研究計畫 v0.4：證據紀錄下的正常參考更新——故障誤吸收、撤銷範圍與回滾殘餘傷害

> **狀態：REFRAME（docs-only）。** 本文件依 #12 的 Active Handoff（comment 5904294585）改寫。**不授權任何訓練、GPU／CPU／toy 實驗、方法實作、標籤存取或資料下載。** 啟動任何實驗前，必須另有 Active Handoff 並封存 protocol；`reports/m0_protocol.md` 的 GO／STOP gates 仍然有效。
> 日期：2026-09-30。前一版 [proposal_v0.3.md](proposal_v0.3.md) 保留為歷史版本，其中的主張**以本文件為準**。
> 依據的審查：[Codex A1–C11](https://github.com/kuo1234/xlstm_anomaly/issues/12#issuecomment-5896220289)、[ChatGPT 獨立查核](https://github.com/kuo1234/xlstm_anomaly/issues/12#issuecomment-5896418052)。

---

## 0. 核心問題

> **在固定、而且有到達時序的證據紀錄（evidence ledger）下，部署後對正常參考的更新會造成多少故障誤吸收？cache（非參數記憶）與參數更新之間，傷害大小、撤銷範圍和回滾後的殘餘傷害有什麼差異？**

工作假說（待證，不是結論）：H1 非參數的 cache 條目可以逐筆追蹤與撤銷，因此在**相同證據**下，cache 式更新的誤吸收比較容易被偵測，回滾後的殘餘傷害也比參數更新小。H1 可能不成立，例如被汙染的條目已經影響了閾值、校準池和後續准入，或者 cache 本身的誤吸收率就比較高。

### 與 v0.3 的主要差異

| 項目 | v0.3（歷史） | v0.4（目前） |
|---|---|---|
| 核心 | 少樣本通用偵測器＋雙 cache，吸收老化並學習新故障 | 正常參考更新的**安全性**：故障誤吸收、撤銷、回滾後的殘餘傷害 |
| 升格證據 | 「持續且可被 context 解釋」即可升格 | 三層證據 E0／E1／E2；**E0 只能否決**；證據缺失、衝突或超出支撐範圍時一律 `unresolved`（§3） |
| 新意 | G4c、G4d、G4g 皆標為 OPEN | 三者都縮小；G4g 的廣義版本已被推翻（§5） |
| 資料 | SMD 接 CARE；CARE 用來做長期老化 | CARE **固定 v6**，只做 episode-level；刪除跨事件的時間順序假設（§6） |
| 回滾 | 刪除 cache 條目即為精確回滾 | 回滾必須依 **state lineage**；刪除條目不等於完整回滾（§7.4） |
| 保證 | anchor、conformal 被當成安全機制 | 撤回所有未經證明的保證（§3.4） |

---

## 1. 範圍與非目標

- **在範圍內**：
  - 部署後新增的觀測，能否改寫正常參考（normal reference）的准入決策。
  - 錯誤准入造成的傷害。
  - 撤銷與回滾的成本和殘餘影響。
  - L0、L1、L2 三種適應機制在相同證據下的比較。
- **第二研究軸（分開處理）**：確認過的故障記憶（fault memory），以及故障型態是否重複出現。不假設同一個資料集或同一個機制能同時回答兩軸（§4 RQ3）。
- **非目標**：
  - 宣稱通用偵測器。
  - 宣稱已經能辨識良性老化。
  - 宣稱完整的新故障型態持續學習。
  - 宣稱 coverage 或安全保證。

---

## 2. 架構（只描述研究對象，不是實作）

```
x_t ──► 凍結 source encoder f_θ（version v_e）──► z_t
          │ s_b                         ├─► 正常參考：anchor（K-shot，不可淘汰）＋ dynamic entries
          │                             └─► 故障記憶（第二軸；confirmed fault，型態可為 unknown）
          ▼
 score_before_update(t) 先寫入紀錄 ──► 准入決策（§3）──► 更新（L0／L1／L2）──► lineage 紀錄（§7.4）
```

- **L0**：只增減 cache 條目。
- **L1**：調整 threshold、fusion 權重（α、β、γ）與 cache key。threshold／fusion 和 key tuning 分開記錄。
- **L2**：小 adapter，會改變 embedding，因此必須處理 cache 的 embedding 版本（§7.4）。
- 對照組一律保留：**frozen**（完全不更新）與 **anchor-only**（只用 K-shot 錨點）。

---

## 3. 准入規則：三層證據（AC1）

### 3.1 證據層級

| 層級 | 來源 | 可以提供 | 使用條件 |
|---|---|---|---|
| **E0** 訊號本身與內部 context | 同一段 X 的函數：anomaly score、殘差、通道之間的關係 h(X) | **風險特徵、否決（veto）**。**不能單獨批准** normal admission | 依 #3 的可識別性邊界，h(X) 並未提供 X 以外的新證據 |
| **E1** 獨立 context 或物理關係 | 負載或設定點指令、風速與 power curve、環境溫度、質量與能量平衡等 | **有條件的正常證據** | 必須全部通過：(a) 來源與**獨立性**（不是受監測的 target 通道，也沒有共同感測鏈）；(b) **部署時可取得**（available-at ≤ 決策時間）；(c) **freshness**（延遲在上限內）；(d) **support**（落在訓練時看過的 context 範圍內，不外插）；(e) **conflict check**（多個 context 之間、或與 E2 之間不衝突） |
| **E2** peer、維修紀錄、操作員、服務報告 | 同型機台的同步變化、工單、確認或駁回、服務報告 | 較高可信度的證據，但**層級名稱本身不保證正確** | 必須記錄來源、可靠度、可取得時間與後續更正；peer 可能有共同原因的汙染，回饋也可能出錯，兩者都要建模 |

### 3.2 狀態與轉移

條目狀態：`suspect`、`transient_unresolved`、`unresolved`、`active_normal`、`confirmed_fault`（型態可為 `unknown`）、`reserve`、`revoked`。

| 情況 | 可支持的轉移 | 不可支持的轉移 |
|---|---|---|
| 只有 E0 顯示偏離，且很快消失 | `suspect → transient_unresolved` | 直接判為 anomaly（正常的啟停或設定點轉換也可能很短暫） |
| 只有 E0 顯示偏離，且持續 | `suspect → unresolved`，並升級警報 | 升格為 `active_normal` |
| E0 顯示通道關係一致 | 可作為**不否決**的條件 | 單獨批准升格 |
| E0 否決（例如違反物理範圍、卡值特徵） | `→ unresolved`，或維持 alarm | — |
| E1 通過 (a)–(e)，而且能解釋偏離 | `unresolved → active_normal`（**有條件**；保留撤銷能力） | 視為永久的正常 |
| E1 缺失、延遲、超出 support，或彼此衝突 | 維持 `unresolved` | 任何升格 |
| E2 駁回警報，且 E1 不衝突 | `→ active_normal` | — |
| E2 確認故障 | `→ confirmed_fault`（型態未確認時記為 `unknown`）；觸發 §7.4 的撤銷 | — |
| E2 與 E1 衝突 | `unresolved`，並記錄衝突 | 自動選一邊 |
| 後續更正（撤回或改判） | 在紀錄中 append 一筆更正事件，並觸發 lineage 撤銷 | 回寫歷史決策 |

### 3.3 已知失效情境（必須在評估中明確設計對應的注入或情境）

1. **緩慢劣化**：沿著 context manifold 平滑移動，每一步都「解釋得通」。toy 模擬中，S3 對這種情境的召回率只有 0.50。
2. **協同或共同模式故障**：多個通道一起偏移，關係仍一致，E0 會顯示「可解釋」。
3. **控制器補償**：控制器為了抵銷零件劣化而同步調整其他量，觀測關係反而看起來更合理。
4. **context 本身故障或延遲**：例如 context 感測器偏移、時間戳錯位，或與 target 有共同原因的汙染。
5. **超出 support 的外插**：新工況下，context 關係不再成立。
6. **E2 錯誤**：操作員誤判、peer 共同原因故障、維修紀錄延遲或遺漏。

### 3.4 撤回的主張

- 撤回「context 可解釋即為正常」。
- 撤回「anchor 不可淘汰即可保護」。被汙染的 dynamic entry 仍可能透過最近鄰距離壓低分數，因此必須獨立報告 anchor-only 對照組的結果與警報。
- 撤回「rolling 或 leave-one-out conformal 提供 nominal FPR 或 coverage 保證」。這些做法同時受到時間相依與適應性選樣的影響，在沒有對應的定理與校準條件之前，只能稱為**校準啟發式**。
- 撤回「刪除 cache 條目即為精確回滾」（見 §7.4）。

---

## 4. 研究問題（AC2：拆分）

| RQ | 問題 | 資料角色 | 狀態 |
|---|---|---|---|
| RQ1 | 用 K-shot 啟用新機台時的偵測能力，以及固定閾值下的誤報率（K 掃描；對照 frozen 與逐台訓練） | SMD leave-one-machine-out | 可在 SMD 上界定 |
| **RQ2（主軸）** | 在固定的證據紀錄下，各種准入規則與 L0／L1／L2 的 **false absorption**、錯誤更新代價、撤銷範圍與 rollback residual harm | SMD＋預先封存的注入；CARE v6 episode-level | 需要新的 protocol |
| RQ3（第二軸） | confirmed fault memory：同型故障再發生時的召回率 | **尚無合格資料**：SMD 的 `interpretation_label` 不是故障型態；CARE 的故障型態與重複次數為 `unknown` | 延後處理；binary fault 不能當作 fault type |
| RQ4 | 證據品質（延遲、錯誤率、缺失）對 RQ2 結論的影響 | 注入實驗的證據紀錄參數 | 需要新的 protocol |

---

## 5. 新意主張對照（AC2、AC3）

「未找到」只代表**在列出的查詢深度內未確認**，不代表「不存在」。

| 缺口 | v0.3 的主張 | v0.4 修訂後的主張 | 既有反例或近鄰 | 仍未確認的交集 | 標記 |
|---|---|---|---|---|---|
| G4c | L0／L1／L2 在相同預算下的正面比較 | 在**同一份證據紀錄、相同資訊到達時序**下，比較 L0／L1／L2 的 unsafe update、false absorption 與 rollback residual harm | 同 shot 數下 cache 與微調的比較：Tip-Adapter（arXiv:2207.09519）、CLAP-S（arXiv:2501.09877）。適應風險與尾端風險：Monitoring Risks in TTA（arXiv:2507.08721）、OGA（arXiv:2501.04352） | 共用證據紀錄＋三級機制＋故障誤吸收造成的因果傷害＋回滾殘餘傷害 | OPEN_AT_SEARCH_DEPTH（待證） |
| G4d | 同一機制吸收老化並學習新故障 | **以正常參考准入的安全性與錯誤更新代價為主**；fault memory 列為第二軸 | iADCPS（arXiv:2504.04374）、Axle Sensor Fusion（arXiv:2602.16101，模擬資料）、Wang et al. 2023（10.1109/TIM.2023.3265118） | 有證據的准入＋誤吸收量測＋可追溯撤銷 | OPEN_AT_SEARCH_DEPTH（待證） |
| G4g | 首次把 Tip／TDA cache 搬到時間序列 | 在 multivariate machine TSAD 中，**有證據把關、可追溯撤銷**的 normal-reference adaptation | CLAP-S（感測訊號上的 Tip 式 cache）、EEG 的 Tip-F（10.1088/2632-2153/ae15e5）、PuRF（arXiv:2608.25653，cache 汙染的清理與刷新） | 原生多變量機台 TSAD＋部署時的准入＋延遲證據＋回滾 | 廣義版本 **CONTRADICTED**；窄版本 OPEN_AT_SEARCH_DEPTH |
| §4.2 context 升格 | context 可解釋即可升格 | E1 只提供**有條件**的證據；主要差異在線上准入、`unresolved` 狀態、撤銷與 lineage | Wang et al. 2023（new-normal buffer＋continual update＋abnormal-data rules，真實風機 SCADA）、BP-MSET（10.1016/j.neucom.2024.128693）、Letzgus 2020 NBM（10.5194/wes-5-1375-2020） | 延遲證據下的線上准入＋`unresolved`＋誤吸收指標＋lineage | 寬泛版本已被佔據；窄版本待證 |
| D3 檢索記憶維護 | 以延遲誤差估計的效用來淘汰（G3b） | **不升為核心新意**（§8） | MWAdp-JITL（10.1016/j.neucom.2020.01.083，已讀全文）、correntropy JITL（10.3390/s17081830）、LST-FEDA（10.1016/j.chemolab.2024.105246） | 逐筆、持續累積的延遲效用＋汙染風險＋淘汰的可逆影響，而且以保護異常證據為目標 | UNRESOLVED（Scopus／WoS 未完成） |

**本論文不能宣稱**：
- cache 或 memory bank 本身。
- 同 shot 數下的 cache 與微調比較。
- 一般性的 adaptation harm 或 risk monitoring。
- cache 汙染的清理。
- 「正常模型要隨工況更新，並排除異常資料」。
- 只從 X 就能判斷良性或故障。
- 「首次把 cache 用在感測訊號」。

---

## 6. 資料計畫（AC4）

| 資料 | 可以支持 | 不可以支持 | 狀態 |
|---|---|---|---|
| **SMD** | RQ1 跨機台 K-shot 啟用；RQ2 預先封存的注入；RQ4 | 真實老化（每台 train／test 約 16.5 天）；語意 context（通道匿名）；語意故障型態（`interpretation_label` 只列出涉及的通道，不是故障型態） | 事實只檢查到本機兩台的特徵檔；標籤存取須遵守 repo 規定 |
| **CARE to Compare v6**（DOI [10.5281/zenodo.15846963](https://zenodo.org/records/15846963)） | **episode-level**：單一事件內的早期故障偵測、context-conditioned 分析、事件層級的正常／異常評估 | **跨事件的真實時間順序**：時間戳是逐檔匿名，無法重建同一台風機跨事件的先後，因此**不得**用匿名時間戳拼接多年的持續適應 replay，也不得用來對齊同時的 peer 訊號 | 只有 release metadata（v6：95 個事件、36 台、3 座風場、45 anomaly／50 normal）。檔案內容尚未驗證 |
| Kelmarsh v4（10.5281/zenodo.16807551）／Penmanshiel v3（10.5281/zenodo.16807304） | 候選：長期正常參考的穩定性分析（2016–2024） | event log 不等於故障型態真值；兩座風場機型不同（MM92 與 **MM82**），不能直接當成同一個機群 | **未通過資料 gate**，只列為可行性候選 |

CARE 的使用邊界：
- 89 turbine-years 是各事件窗口的加總，不是一條連續軌跡。
- 各風場真實的起訖日期：`unknown`。
- 完整的故障型態清單，以及每種型態的重複次數：`unknown`。
- `status_type_id = 0` 代表運轉狀態，**不等於**已確認健康。
- 部分 Min／Max／Std 欄位官方標示可能不可信，Farm B 建議優先使用 Avg。
- 授權為 CC BY-SA 4.0：重新發佈資料或改作資料內容時，需署名、附授權連結、標示修改，並依 ShareAlike 處理；單純用資料做分析，並不會讓整篇論文或獨立的程式碼自動適用同一授權（這不是法律意見）。

---

## 7. 評估規格（AC5，只寫規格，不實作）

### 7.1 Evidence ledger（append-only）

每一筆事件至少包含以下欄位：

| 欄位 | 說明 |
|---|---|
| `evidence_id` | 唯一識別碼 |
| `event_id`／`sample_id` | 對應的事件或樣本；重疊的視窗要記錄所屬的獨立事件 |
| `source_asset`／`segment` | 來源機台與區段 |
| `tier`／`source` | E0／E1／E2，以及具體來源 |
| `observation_time` | 被觀測的時間 |
| `available_at` | 方法可以使用這筆證據的最早時間 |
| `delay` | `available_at − observation_time` |
| `label_content` | normal／fault／unknown；fault type 或 `unknown` |
| `reliability` | 來源可靠度（若已知） |
| `supersedes`／`correction_of` | 更正或撤回的對象；**不修改原紀錄** |
| `ledger_version` | 紀錄版本 |
| `decision` | 准入決策，以及當時的狀態轉移 |
| `depends_on` | 這個決策所依賴的 evidence_id 清單 |

### 7.2 公平性

- 固定以下各項：source backbone 與來源機台的排除規則、K-shot 的**實際樣本 ID**、**獨立於 support set** 的 calibration set、可見資訊，以及回饋時序。
- 評估專用的標籤**不得**進入證據紀錄。
- 主比較：所有方法重播**同一份**封存的證據紀錄，並一律採 `score-before-update`（先記分數、後更新，歷史紀錄不得改寫）。
- active query 另列為研究範圍，比較時固定查詢成本、查詢種類與延遲。
- 算力、記憶體、原始樣本保留、checkpoint／optimizer 大小、重新編碼與回滾 replay 的成本**另外量測與報告**，不以「回饋次數相同」代替「證據相同」。

### 7.3 指標（計數單位、分母、去重規則）

| 指標 | 定義 | 單位與規則 |
|---|---|---|
| **Admission contamination rate** | faulty normal admissions ÷ all normal admissions | 單位：條目。分母為 0 時記 N/A。**不可單獨報告**（永不更新的方法會得到 N/A 或 0） |
| **Event false-promotion rate** | 至少有一筆條目被誤升格的獨立 fault event 數 ÷ 全部暴露給方法的 fault event 數 | 單位：獨立事件。重疊視窗依事件 ID 去重。**不可把條目數除以事件數當作事件比例** |
| **Missed-alarm duration** | 每次錯誤准入之後，到故障結束（或被撤銷）為止的漏報時長 | 單位：時間步；依事件彙總 |
| **Harm vs. frozen** | 方法與 frozen 對照組在相同事件母體上的偵測指標差（AP、事件 recall、固定閾值 FPR） | 以機台為單位做 paired 比較 |
| **Rollback residual harm** | 撤銷後，方法與「clean replay」（從未收到被汙染證據的同一方法）之間的偵測指標差 | 依 §7.4 的撤銷邊界定義；同時報告回滾成本 |
| **Benign adaptation latency** | 從良性變化開始，到正常段 FPR 回到基準範圍所需的時間 | **只在有外部良性真值時計算**（例如注入實驗）；否則記 N/A |

以上指標必須**同時報告**。另外必須附上 frozen 與 anchor-only 的結果，才能看出一個方法是真的安全，還是只因為從不更新而看起來安全。

### 7.4 Rollback lineage

- **需要追蹤的狀態**：
  - cache 條目；
  - scaler；
  - calibration pool 與 threshold；
  - 後續的 admission 決策（它們可能依賴被汙染的狀態）；
  - L1 的 cache key 與 fusion 參數；
  - L2 的 adapter 權重、optimizer state 與 checkpoint；
  - embedding version。L2 更新後，舊的 cache embedding 需要重新編碼，這個成本要計入。
- **汙染依賴**：一筆被撤回的證據會汙染所有 `depends_on` 包含它的決策，以及這些決策之後衍生的所有狀態，這是一種遞移關係。
- **撤銷邊界**：
  - L0：刪除條目，重新計算受影響的閾值，再重放後續的准入決策。
  - L1／L2：回到最近一個乾淨的 checkpoint，重放未受汙染的證據。
  - 兩者都要記錄 replay 的範圍與成本。
- **殘餘影響**：無法完整重放的部分，例如已經發出或壓掉的警報，列入 rollback residual harm。
- **宣稱限制**：刪除 cache 條目**不得**宣稱為完整回滾。anchor 沒被刪除，也不自動保證安全。

---

## 8. JITL 補查狀態（AC6）

| 子項 | 狀態 | 說明 |
|---|---|---|
| Neurocomputing 2020 全文與方法查核（Urhan & Alakent, *Neurocomputing* 392:23–37, DOI 10.1016/j.neucom.2020.01.083） | **已完成**（2026-09-30，使用者提供全文 PDF；PDF 未放入 repo） | 見下方摘要 |
| Scopus／WoS citation-chain 補查 | **UNRESOLVED** | 本代理、Codex、ChatGPT 都沒有訂閱資料庫的介面。建議查詢式：`("just-in-time" OR JITL) AND ("soft sensor" OR "soft-sensor") AND (database OR maintenance OR pruning OR forgetting OR "sample selection")`，並對 MWAdp-JITL、correntropy JITL、LST-FEDA 做 forward／backward citation tracing |

**MWAdp-JITL 全文查核摘要**（依 §2–§5 與 Algorithms 1–3）：

- **機制**：
  - 自適應移動視窗 MWAdp 有兩個調整機制。CheckM：當查詢點到視窗的 Mahalanobis 距離超出上界時擴大視窗，用來因應 virtual drift。Checks：以模型誤差變異數做 EWMA 管制圖，超出上界時縮小視窗，用來因應 real drift。
  - JITL 對每個查詢點：
    - 在歷史資料中，以歐氏距離閾值 `median − l·MAD` 找出相似的**連續區段**；
    - 用最近 m_p（= 3）筆已標註樣本的驗證誤差，選出誤差最小的區段；
    - 再以 BMA 權重（驗證誤差的倒數）與 MW 模型組合預測。
- **資料庫**：採 rolling-origin，每筆測試觀測在預測後都附加進資料庫。另有 `lim` 變體把資料庫大小固定為初始訓練集大小，但主文**沒有說明淘汰規則**（可能在補充材料中，本次未讀補充材料）。
- **對三個問題的回答**：
  1. **逐筆效用與保留／淘汰**：**否**。效用是在查詢時、以區段為單位的驗證誤差，不會持續累積到個別樣本上，也沒有依效用淘汰。
  2. **延遲真值回頭評估個別樣本的貢獻**：**部分**。論文用最近的實際預測誤差來選擇歷史區段與設定 ensemble 權重（這已部分佔據「用實際誤差選擇記憶」），但只在區段層級、只在查詢當下，而且假設標籤在下一步就到達，沒有 H 步延遲。
  3. **故障汙染資料庫**：**否**。所有觀測都未經篩選就附加進資料庫；Mahalanobis 檢查是用來擴大視窗，不是用來排除故障。論文結論只提到方法**可能**有助於故障偵測與診斷。
- **對 D3 的影響**：「依相似度與近期實際誤差，在查詢時選擇歷史區段」已被佔據。D3 剩下的可能差異是：**逐筆、持續累積**的延遲效用、H 步延遲、汙染風險，以及淘汰的可逆影響。在 Scopus／WoS 補查完成之前，D3 **不升為核心新意**。
- **適用範圍**：單輸出 soft-sensor 回歸（RVM）；資料集為 DC、SRU、MI、WWTP 與 CSTR 模擬；評估目標是預測誤差，不是保護異常證據。

本項未解決的部分**不阻止**本 docs-only v0.4 交付，但也**不構成**研究 GO。

---

## 9. 停損與下一個 gate

- 下一個 gate（需另有 Active Handoff）：以 docs-only 方式封存 RQ2 的 protocol。內容包括證據紀錄的 schema、注入型態清單（涵蓋 §3.3 的六種失效情境）、指標的分母與去重規則、margin、以及 frozen 和 anchor-only 對照組。
- 停損條件：
  - 若 RQ2 的注入實驗無法在 SMD 上設計出「E1 可能存在」的情境（SMD 沒有獨立 context），RQ2 在 SMD 上只測 E0 否決與 E2 回饋，E1 則等到有 context 的資料（CARE v6 episode-level）再測。
  - 若 H1 在 pilot 中方向相反，也就是 cache 的殘餘傷害不比參數更新小，就如實報告，論文轉為分析「哪些 lineage 狀態讓撤銷失效」。
  - 若有新文獻完整覆蓋 G4c 的窄版交集，則 REFRAME 或 STOP。
