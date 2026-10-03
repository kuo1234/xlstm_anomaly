# P7：部署後正常參考更新的安全性（研究構想紀錄）

**Issue**：[#12](https://github.com/kuo1234/xlstm_anomaly/issues/12)
**Branch**：`research/few-shot-dual-cache-detector`（只有文件）
**狀態**：`REFRAME / docs-only v0.4 delivered / awaiting review`（2026-09-30）

本目錄記錄論文題目的探索過程與目前的構想。**不授權任何訓練、GPU／CPU／toy 實驗、方法實作、標籤存取或資料下載**；也沒有修改 M1（#11）、P5（#9）或 main。

## 目前的主張（v0.4）

> 在固定、而且有到達時序的證據紀錄下，部署後對正常參考的更新會造成多少故障誤吸收？cache 與參數更新之間，傷害大小、撤銷範圍和回滾後的殘餘傷害有什麼差異？

- **主文件**：[proposal_v0.4.md](proposal_v0.4.md)。包含三層證據的准入規則、縮小後的新意主張、資料邊界、證據紀錄與指標規格、rollback lineage，以及 JITL 補查狀態。
- 工作假說 H1（**待證**）：在相同證據下，cache 式更新的誤吸收比較容易被偵測與撤銷。
- 以下主張**都不能**宣稱：通用偵測器、已能辨識良性老化、完整的新故障型態持續學習、「首次把 cache 用在感測訊號」、coverage 或安全保證。

## 歷史主張與目前主張

| 版本 | 主張 | 狀態 |
|---|---|---|
| [history/proposal_v0.1_retrieval_forecasting.md](history/proposal_v0.1_retrieval_forecasting.md) | 檢索式預測記憶，以延遲誤差估計效用並據此維護 | 歷史；D3 **不升為核心**（見 v0.4 §8） |
| [history/proposal_v0.2_dual_cache_detector.md](history/proposal_v0.2_dual_cache_detector.md) | 通用偵測器＋雙 cache＋以操作員回饋為必要條件 | 歷史 |
| [proposal_v0.3.md](proposal_v0.3.md) | context 優先；「持續且可被解釋」即可升格；SMD 接 CARE 做長期老化 | 歷史；**被 v0.4 取代**。其中「context 可解釋即正常」、G4g 廣義版本、CARE 跨事件老化、anchor／conformal 保證都已撤回 |
| **[proposal_v0.4.md](proposal_v0.4.md)** | 證據紀錄下的准入安全性、誤吸收、撤銷與殘餘傷害 | **目前版本** |

## 檔案

| 檔案 | 內容 |
|---|---|
| [proposal_v0.4.md](proposal_v0.4.md) | 目前的研究計畫 |
| [problems_and_feasibility.md](problems_and_feasibility.md) | 問題、解法與可行性評估（已更新到 v0.4） |
| [literature/gap_summary.md](literature/gap_summary.md) | 缺口判定的變化、最接近的文獻、未解決項目 |
| [literature/v0.4_closest_competitors.json](literature/v0.4_closest_competitors.json) | 14 筆最接近的文獻，附查核層級 |
| literature/*_gap_audit.md、*_papers.json、datasets_audit.* | 各輪的原始審查（開頭附 v0.4 更正說明） |
| [second_review_request.md](second_review_request.md) | 給二次審查的清單（已完成，結論為 REFRAME） |
| [toy_identifiability_sim/](toy_identifiability_sim/) | toy 模擬（本次未更動，也未重跑） |

## 資料存取聲明

- v0.3：只讀取了本機 SMD machine-1-4 和 machine-2-1 的 train 與 test **特徵檔**，沒有開啟任何標籤檔。
- v0.4：沒有存取任何資料或標籤，也沒有執行任何實驗。MWAdp-JITL 的全文由使用者提供 PDF 供閱讀，**PDF 沒有放入 repo**。
