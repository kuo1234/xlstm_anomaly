# 問題、解法與可行性評估（v0.4，2026-09-30）

> 對應 [proposal_v0.4.md](proposal_v0.4.md)。v0.3 版本的表格見 git 歷史（commit 302ef006）；本版依 #12 的兩份二次審查修訂。

## 1. 問題與處置

| # | 問題 | 來源 | v0.4 處置 | 狀態 |
|---|---|---|---|---|
| 1 | 持續的故障被吸收成正常 | toy：S1 對偏移、緩慢劣化、長故障的召回率只有 0.00–0.09 | 只有 E0 時不升格；維持 `unresolved` 並升級警報（§3.2） | 規格已定 |
| 2 | 「可以被 context 解釋」不等於正常 | 二次審查 B6 | E1 必須通過獨立性、可取得性、freshness、support、conflict 五項檢查；E0 只能否決；列出六種失效情境（§3.3） | 規格已定；有效性待實驗驗證 |
| 3 | SMD 沒有獨立 context | 通道匿名 | 內部 context 屬於 E0，**不能**當作正向證據；SMD 上的 RQ2 只測 E0 否決與 E2 回饋 | 限制已記錄 |
| 4 | 自我確認造成的回饋迴圈 | 設計 | 一律 score-before-update；證據紀錄 append-only；對照 frozen 與 anchor-only | 規格已定 |
| 5 | 回滾不完整 | 二次審查 B6 | rollback lineage 涵蓋 cache、scaler、閾值、後續准入、L1、L2、embedding version（§7.4） | 規格已定；成本待量測 |
| 6 | 少樣本下閾值不可靠 | M1：AP 0.96，但 FPR 57% | 報告固定閾值下的 FPR；撤回 conformal 保證，只稱為啟發式 | 規格已定 |
| 7 | 指標可能獎勵「永不更新」 | 二次審查 B8 | 同時報告准入汙染率、事件誤升格率、漏報時長、相對 frozen 的傷害、回滾殘餘傷害；分母為 0 時記 N/A（§7.3） | 規格已定 |
| 8 | 新意不足 | Wang 2023、CLAP-S、iADCPS、PuRF 等 | 縮小為 G4c、G4d、G4g 的窄版本（§5） | 窄版本 OPEN_AT_SEARCH_DEPTH（待證） |
| 9 | CARE 無法支撐長期老化 | CARE FAQ：時間戳逐檔匿名 | CARE 固定 v6，只做 episode-level（§6） | 限制已記錄 |
| 10 | 沒有合格資料可以做故障型態重複出現的研究 | SMD 的 `interpretation_label` 不是故障型態；CARE 的故障型態清單為 `unknown` | RQ3 延後處理 | 阻塞 |
| 11 | JITL 補查 | A5 | 全文已讀；Scopus／WoS 仍 UNRESOLVED；D3 不升為核心 | 部分阻塞 |

## 2. SMD 事實（v0.3 時的檢查；v0.4 沒有再存取任何資料）

| 機台 | train 形狀 | test 形狀 | train 中幾乎不變的通道數（sd < 1e-3） |
|---|---|---|---|
| machine-2-1 | 23693 × 38 | 23694 × 38 | 5 |
| machine-1-4 | 23706 × 38 | 23707 × 38 | 6 |

- 每分鐘一筆，train 和 test 各約 16.5 天。數值已正規化到 [0, 1]；通道匿名；沒有時間戳。
- `interpretation_label`：官方 repo 中有 28 個機台檔名（依二次審查的目錄 metadata）；內容只是涉及的通道，**不是故障型態**。

## 3. 可行性（v0.4）

| 部分 | 可行性 | 說明 |
|---|---|---|
| RQ1 K-shot 啟用（SMD） | 高 | 資料與程式現成；需要新的 protocol |
| RQ2 證據紀錄下的准入安全性 | 中高 | 核心；SMD 上 E1 無法測試，需要 CARE v6 episode-level 補充 |
| H1 cache 的回滾殘餘傷害較小 | 未知 | 方向可能相反；如實報告 |
| RQ3 fault memory 與重複出現 | 低（目前沒有合格資料） | 延後 |
| 長期老化 | 低 | CARE 無法支撐；Kelmarsh／Penmanshiel 未通過資料 gate |
