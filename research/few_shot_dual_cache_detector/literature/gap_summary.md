# 文獻缺口審查總表（v0.4，2026-09-30）

判定用語：OCCUPIED／PARTIALLY_OCCUPIED／OPEN_AT_SEARCH_DEPTH（在列出的查詢深度內未確認，**不是**證明不存在）／CONTRADICTED／UNRESOLVED。
本表整合了 2026-09-29 的四輪審查，以及 #12 的兩份二次審查：[Codex](https://github.com/kuo1234/xlstm_anomaly/issues/12#issuecomment-5896220289)、[ChatGPT](https://github.com/kuo1234/xlstm_anomaly/issues/12#issuecomment-5896418052)。**目前主張以 [../proposal_v0.4.md](../proposal_v0.4.md) §5 為準**；各輪的 `*_gap_audit.md` 是歷史紀錄，檔案開頭都加了 v0.4 更正說明。

## 1. 檔案

| 檔案 | 內容 | 筆數 |
|---|---|---|
| [v0.4_closest_competitors.json](v0.4_closest_competitors.json) | **v0.4 新增的最接近文獻**：識別碼、發現來源、審查者的閱讀層級、本代理的查核層級、已佔據的貢獻、尚未確認的交集 | 14 |
| d2_online_adaptation_* | 預測模型的線上適應（備案方向） | 35 |
| d3_retrieval_memory_* | 檢索記憶與維護（備案方向；MWAdp-JITL 已讀全文，另新增 2 筆 JITL） | 44 |
| fs_detector_* | 通用或少樣本 TSAD | 29 |
| cache_feedback_* | cache 式適應與回饋 | 20 |
| datasets_audit.* | 19 個資料集；CARE、Kelmarsh、Penmanshiel 已更正 | — |

## 2. 判定變化（原始 → v0.4）

| 缺口 | 2026-09-29 判定 | v0.4 判定 | 變化原因 |
|---|---|---|---|
| G4a 凍結通用偵測器＋few-shot cache | PARTIALLY_OCCUPIED | PARTIALLY_OCCUPIED（不再作為主張） | 論文主軸改為准入安全 |
| G4b 雙 cache＋延遲操作員回饋 | PARTIALLY_OCCUPIED | 併入 RQ2（E2 證據） | — |
| G4c cache vs. 權重 | OPEN_AT_SEARCH_DEPTH | 廣義版本 **OCCUPIED**；窄版本 OPEN_AT_SEARCH_DEPTH（待證） | Tip-Adapter、CLAP-S 已做同 shot 數比較；Monitoring Risks、OGA 已做適應風險。窄版本限定為：同一份證據紀錄下的 false absorption 與 rollback residual harm |
| G4d 吸收老化＋學新故障 | OPEN_AT_SEARCH_DEPTH | NEW_THREAT；窄版本 OPEN_AT_SEARCH_DEPTH | iADCPS、Axle Sensor Fusion、Wang 2023。改為以准入安全為主軸，fault memory 另列第二軸 |
| G4e few-shot 閾值 | PARTIALLY_OCCUPIED | 不變；另外撤回 conformal 保證 | — |
| G4f 真實長期多故障評估 | OPEN_AT_SEARCH_DEPTH | 找不到滿足條件的資料 | CARE 的時間戳是逐檔匿名 |
| G4g cache 轉移到時間序列 | OPEN_AT_SEARCH_DEPTH | 廣義版本 **CONTRADICTED**；窄版本 OPEN_AT_SEARCH_DEPTH | CLAP-S（感測訊號）、EEG Tip-F、PuRF（cache 汙染清理） |
| §4.2 以 context 作為升格證據 | 設計新意 | 寬泛版本 **OCCUPIED** | Wang 2023（new-normal buffer＋continual update＋abnormal-data rules）、BP-MSET、Letzgus 2020 |
| G3b 以延遲誤差估計記憶效用 | OPEN_AT_SEARCH_DEPTH | 廣義版本 **PARTIALLY_OCCUPIED**；整體 UNRESOLVED | MWAdp-JITL 在查詢時用近期實際誤差選擇區段（全文已讀）；Scopus／WoS 補查未完成 |
| G3c JITL 資料庫維護 | PARTIALLY_OCCUPIED | PARTIALLY_OCCUPIED（證據更強） | correntropy JITL 在新標籤到達時補充並重新清理資料庫；LST-FEDA 用最新樣本更新 |

## 3. v0.4 最接近的文獻（摘要；完整內容見 JSON）

| ID | 文獻 | 識別碼 | 本代理的查核層級 | 已佔據的貢獻 |
|---|---|---|---|---|
| C01 | Wang et al. 2023（MSET＋continual learning） | 10.1109/TIM.2023.3265118 | metadata | **正常參考更新的直接近鄰**：new-normal buffer、continual update、abnormal-data rules |
| C02 | BP-MSET 2025 | 10.1016/j.neucom.2024.128693 | metadata | 小樣本與不連續樣本下的動態更新 |
| C03 | Letzgus 2020 NBM | 10.5194/wes-5-1375-2020 | metadata | context-conditioned NBM，並清理出乾淨的參考資料 |
| C04 | iADCPS | arXiv:2504.04374 | metadata | 用有限的新正常樣本持續適應演化中的 CPS |
| C05 | CLAP-S | arXiv:2501.09877 | metadata | 感測訊號上的 Tip 式 cache；同 shot 數比較 cache 與 adapter |
| C06 | EEG Tip-F 2025 | 10.1088/2632-2153/ae15e5 | metadata | 跨模態的 cache 先例 |
| C07 | PuRF | arXiv:2608.25653 | metadata | cache 汙染的清理與刷新 |
| C08 | Monitoring Risks in TTA | arXiv:2507.08721 | metadata | 適應風險監測 |
| C09 | OGA | arXiv:2501.04352 | metadata | 串流設定下的尾端風險 |
| C10 | Axle Sensor Fusion | arXiv:2602.16101 | metadata | 工況變動下的持續故障學習（模擬資料） |
| C11 | MWAdp-JITL | 10.1016/j.neucom.2020.01.083 | **full_text** | 查詢時依相似度與近期誤差選擇歷史區段 |
| C12 | correntropy JITL | 10.3390/s17081830 | metadata | 資料庫的清理與補充 |
| C13 | LST-FEDA | 10.1016/j.chemolab.2024.105246 | metadata | 用最新樣本更新 |
| C14 | MSDG | 10.3390/s24227218 | metadata | SMD 的通道關係會隨時間變動，支持「E0 只能否決」 |

「metadata」代表本代理只以 Crossref 或 arXiv API 確認文獻存在；機制描述來自審查者的閱讀，審查者的閱讀層級記錄在 JSON 中。**未取得全文的文獻，本文件不推定其具體機制。**

## 4. 仍未解決（阻止研究 GO，但不阻止 docs-only 交付）

1. **Scopus／WoS citation-chain 補查**（JITL 資料庫維護）：UNRESOLVED，因為沒有訂閱資料庫的介面。
2. 2025–2026 年的 arXiv 預印本：兩輪審查都補搜過，但仍可能有遺漏。
3. CARE v6 的檔案內容（欄位、故障型態清單、每型重複次數）：未驗證。
4. SMD `interpretation_label` 的內容與一致性（參見 OmniAnomaly issue #66）：未驗證，也不得在沒有授權的情況下開啟。
