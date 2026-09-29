# Few-shot universal detector with dual cache（P7 研究構想紀錄）

**Issue**：[#12](https://github.com/kuo1234/xlstm_anomaly/issues/12)
**Branch**：`research/few-shot-dual-cache-detector`（只有文件；base `origin/main` 60fd1ce）
**日期**：2026-09-29
**狀態**：`RESEARCH_BACKLOG / AWAITING_SECOND_REVIEW`

本目錄記錄論文題目的探索過程與目前的構想。**不授權任何訓練、GPU 實驗或標籤存取**；也沒有修改 M1（#11）或 P5（#9）。

## 一句話

一個凍結的通用異常偵測器，給它 K 筆新機台的正常樣本就上線。之後靠正常 cache 和故障 cache 持續學習，以面對機台老化和新故障型態。持續偏離要升格為正常時，必須有**訊號歷史以外的證據**，例如 context、內部 context、peer 或操作員回饋。核心研究問題是：只動 cache 什麼時候就夠，什麼時候必須動權重？

## 檔案

| 檔案 | 內容 |
|---|---|
| [proposal_v0.3.md](proposal_v0.3.md) | **目前版本的研究計畫**：context 優先、回饋選配、SMD 加 CARE 兩階段 |
| [problems_and_feasibility.md](problems_and_feasibility.md) | 8 個主要問題、解法、SMD 的實測事實、可行性評估 |
| [second_review_request.md](second_review_request.md) | **給 ChatGPT 的二次調查清單**（A1–C11），附回覆格式 |
| [literature/gap_summary.md](literature/gap_summary.md) | 四輪文獻缺口審查的總表與限制 |
| literature/*_gap_audit.md、*_papers.json | 各輪的完整審查報告與論文清單（附 verification_level） |
| literature/datasets_audit.* | 19 個機台資料集的審查 |
| [toy_identifiability_sim/](toy_identifiability_sim/) | 自我確認 cache 規則的 toy 模擬：`sim.py` 可重現 `results.csv` 和 `figure.png` |
| history/proposal_v0.1_retrieval_forecasting.md | 備案：檢索式預測的記憶維護（D3） |
| history/proposal_v0.2_dual_cache_detector.md | 前一版：以操作員回饋為必要條件 |

## 演進

1. **v0.1**（預測方向）：用延遲誤差估計檢索記憶的效用，並據此維護記憶；Kelmarsh／Penmanshiel 為主資料。
2. **v0.2**（使用者釐清目標是 detector）：凍結通用偵測器＋雙 cache＋操作員回饋；CARE to Compare 為主資料。
3. **v0.3**（使用者提出「時間累積就能判定」的構想）：toy 模擬顯示只看時間的規則會吸收持續故障，因此改為 context 優先、回饋選配；加入 SMD 作為第一階段資料。

## 資料存取聲明

- 只讀取了本機 `xlstm_anomaly-realdata` 中 SMD machine-1-4 和 machine-2-1 的 train 與 test **特徵檔**，用來確認形狀和常數通道數量。
- **未開啟任何標籤檔。**
- toy 模擬只使用合成資料。
