# 二次調查請求（給 ChatGPT）

請依 AGENTS.md 的 GitHub Issue workflow，在對應的 Issue 回覆審查結果。本請求**只涵蓋文獻、資料與設計的審查**，不授權任何訓練、GPU 實驗或標籤存取。

## A. 新意查核（最優先）

1. **G4c**：有沒有任何論文在相同的標籤或回饋預算下，正面比較 cache-only、cache 加輕量微調、adapter 或權重更新，而且報告 adaptation harm 或 false absorption？任何模態都算，但特別注意時間序列和異常偵測。
2. **G4g**：有沒有論文把 Tip-Adapter、TDA、DMN、DPE 式的 key-value cache 用在時間序列或機台訊號上？請特別搜尋 2025–2026 年的 arXiv（本輪遇到 rate limit）。
3. **G4d**：有沒有論文在同一機制下，同時處理良性漂移的吸收和新故障型態的 few-shot 學習，並報告故障被誤吸收的比例？
4. **以 context 作為升格證據**：在 normal behaviour model 文獻中（風機 SCADA、製程），是否已經有人用 context 可解釋性來決定是否更新正常參考？若有，請列出，並說明與 §4.2 的差異。
5. **JITL**：請補讀 Neurocomputing 2020 那篇「Integrating adaptive moving window and just-in-time learning paradigms for soft-sensor design」，並用 Scopus 或 WoS 補查 JITL 資料庫維護的文獻。這會影響備案方向 D3 的新意。

## B. 設計審查

6. §4.2 的升格規則（無法解釋的持續偏離不自動升格）是否有明顯漏洞？特別是：緩慢劣化（toy 模擬中 S3 也只有 0.50）、協同型故障、context 本身出錯。
7. SMD 的內部 context（通道之間的關係）作為升格證據是否合理？有沒有文獻在 SMD 上分析過通道關係的穩定性？
8. L0／L1／L2 的「相同預算」應該如何定義才公平？（回饋次數、可用樣本數、算力？）

## C. 資料查核

9. SMD：OmniAnomaly 的 `interpretation_label` 是否每台都有？是否能用來定義異常型態，以及異常是否在同一台機台內重複出現？**請只查文件和 repo 說明，不要開啟 repo 規定尚未開放的標籤。**
10. CARE to Compare：確認最新版本、欄位、故障型態清單、各風場的時間範圍，以及 CC-BY-SA 對論文使用的影響。
11. 還有沒有其他同時具備多台同型機台、多種故障標註、長期老化，並提供 context 變數的公開機台資料集？

## D. 建議的回覆格式

```
Issue:
Reviewed branch / SHA:
Sources checked (with DOI / arXiv id):
Findings per item A1–C11: SUPPORTED / CONTRADICTED / NEW_THREAT / UNRESOLVED
New closest competitors:
Recommended changes to proposal_v0.3:
GO / REFRAME / STOP recommendation for the idea:
```
