# 文獻缺口審查總表（2026-09-29）

判定用語：OCCUPIED／PARTIALLY_OCCUPIED／OPEN_AT_SEARCH_DEPTH（在列出的查詢範圍內未見前例，**不是**證明不存在）／UNRESOLVED。
各輪的完整證據、查詢語句和最接近的競爭者，請見同目錄下的 `*_gap_audit.md`；論文清單在 `*_papers.json`，每筆都標註了 verification_level。

| 輪次 | 主題 | JSON 筆數 | 檔案 |
|---|---|---|---|
| D2 | 預測模型的線上適應（慢模型＋快 adapter、延遲標籤、gate） | 35 | d2_online_adaptation_* |
| D3 | 檢索式預測記憶與部署後的維護 | 42 | d3_retrieval_memory_* |
| D4a | 通用或少樣本 TSAD、跨機台、新故障型態 | 29 | fs_detector_* |
| D4b | cache 式適應與回饋驅動的偵測器更新 | 20 | cache_feedback_* |
| DS | 機台資料集（19 個） | — | datasets_audit.* |

## 與本構想最相關的判定（D4）

| 缺口 | 判定 | 最接近的工作 |
|---|---|---|
| G4a 凍結通用 TS 偵測器＋新機台 few-shot cache | PARTIALLY_OCCUPIED | DADA（ICLR 2025, arXiv:2405.15273）；PatchCore few-shot（arXiv:2307.10792）；DCASE 2023–2024 Task 2 first-shot（arXiv:2406.07250） |
| G4b 以延遲操作員回饋更新雙 cache，並有 quarantine | PARTIALLY_OCCUPIED（各元件分散在不同文獻） | TDA（arXiv:2403.18293）、DMN（arXiv:2403.17589），兩者用偽標籤；AAD（10.1109/icdm.2016.0102）；Siddiqui KDD 2018（10.1145/3219819.3220083）；DeepLog（10.1145/3133956.3134015）；DRA（arXiv:2203.14506） |
| G4c 相同預算下 L0／L1／L2 的正面比較，附 false-absorption 指標 | **OPEN_AT_SEARCH_DEPTH** | 只有同一篇論文內的比較，例如 Tip-Adapter vs. -F；PromptAD（CVPR 2024） |
| G4d 同一機制既吸收老化又學新故障，並量測誤吸收 | **OPEN_AT_SEARCH_DEPTH** | AnDri（arXiv:2506.15831）；UCAD（AAAI 2024）；IUF（ECCV 2024） |
| G4e few-shot 閾值與 FPR 可靠度 | PARTIALLY_OCCUPIED | ColdFusion（ACL Findings 2024, 10.18653/v1/2024.findings-acl.453）；COLDSTART |
| G4f 真實機台、長期部署、多種故障型態的評估 | **OPEN_AT_SEARCH_DEPTH** | — |
| G4g Tip-Adapter／TDA 式 cache 轉移到時間序列 | **OPEN_AT_SEARCH_DEPTH** | — |

## D2／D3 的主要判定（備案方向）

- G2a 延遲標籤協定、G2b gate、G2c 慢加快結構：PARTIALLY_OCCUPIED。主要威脅是 Proceed（arXiv:2412.08435）與 PADRE（IJCAI 2026, 10.24963/ijcai.2026/503）。
- G2d 線上更新不學入故障（機台資料）、G2e 基礎模型 vs. 線上適應在多年期資料上比較：OPEN_AT_SEARCH_DEPTH。
- G3a 檢索資料庫部署後的維護、G3b 以延遲誤差估計記憶效用：OPEN_AT_SEARCH_DEPTH。主要威脅是 SARAF（KDD 2026, 10.1145/3770855.3817813）、JITL 軟感測器文獻、SAM-kNN。

## 已經由人工另行查核存在的論文（Crossref／arXiv API）

PADRE（IJCAI 2026）、SARAF（KDD 2026）、LEAF（IJCAI 2025）、arXiv:2605.17250、TiRex-2（arXiv:2607.01204）、Proceed（arXiv:2412.08435）、PETSA（arXiv:2506.23424）。

## 審查限制（二次調查請優先處理）

1. arXiv 與 Semantic Scholar 在 D4 輪遇到 HTTP 429，部分查詢改走 OpenAlex，2026 年的預印本可能漏掉。
2. 只驗證到 metadata 的論文：Tip-Adapter、AAD、RevIN、ICLR 2025 Lau/Shao/Yeung，以及 JITL 關鍵論文「Integrating adaptive moving window and just-in-time learning paradigms for soft-sensor design」（Neurocomputing 2020，付費牆）。
3. 只讀了摘要：IUF、DCASE 2024 Task 2 說明論文、SARAF。
4. 製程控制與化學計量學的 JITL 文獻，用 OpenAlex 搜尋雜訊很大，建議用 Scopus 或 Web of Science 補查。
5. 所有資料集只驗證到 landing page 或 API metadata，沒有下載完整檔案。
6. D2 的 JSON 有 35 筆，子代理的報告寫「33 篇已驗證」，差異的 2 筆應為 metadata_only，需要核對。
