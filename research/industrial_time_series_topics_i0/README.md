# I0 — 工業時序应用缺口與選題可行性審查

2026-10-06。原始目標：不再限定 anomaly，查詢工業時序相關應用缺口、提出題目並驗證可行性。使用者已指定**製程品質／軟感測優先**，保留設備、組裝、能源與決策的 broader screening；不把這個偏好改成只研究一個資料集。

Branch `codex/industrial-timeseries-topic-audit`；基準 `08cec9b402990831790c2e1be8849f4d531be8cf`。#31/C0 的 STOP 保留。I0 是另一個由使用者直接提出的研究 audit，未解鎖任何舊 anomaly / adaptation gates。

**選題與有界可行性審查：完成；method novelty / deployment GO：未給予。** 第一輪已從題目搜尋推進到 exact data bytes、批次 join、原料 genealogy、時間間隔與原生 model input contract 核對。已依兩個pushedseals完成24次既有Ridge fit、0neural、沒有新architecture；單一產品的quality可行性檢查是負向。最終排序與投入建議見 [FINAL_RECOMMENDATIONS.md](FINAL_RECOMMENDATIONS.md)，沒有 paper novelty GO。

首選已改為「**射出成型品質軟感測的前瞻可信度**」，因已取得独立實物品質量測與有界prototype的證據。原批次候選的負結果完整保留。Data feasibility 有實際支持，但固定15/60minprefix的初始Ridge增量訊號未通過；generic online alignment / early quality modeling 已有成熟 prior art，剩餘貢獻需限定於可追溯的 operational evaluation，不得宣稱首次處理不等長批次。

| 文件 | 本輪已完成的證據 / 尚缺 |
|---|---|
| [FINAL_RECOMMENDATIONS.md](FINAL_RECOMMENDATIONS.md) | 最終首選／備選／STOP排序、射出4-fit證據、方法新意與部署界線 |
| [COMPLETION_AUDIT.md](COMPLETION_AUDIT.md) | 原始goal逐項驗證與完成範圍 |
| [LANDSCAPE.md](LANDSCAPE.md) | 跨應用初篩與近鄰；部分 source 仍 abstract/preview depth |
| [TOPIC_CARDS.md](TOPIC_CARDS.md) | 四個品質候選及其他方向，明確 data/method/utility gates |
| [DATA_FEASIBILITY.md](DATA_FEASIBILITY.md) | exact bytes、CSV/archive/label/clock/genealogy 檢查 |
| [PRIOR_ART_AND_CONTRACTS.md](PRIOR_ART_AND_CONTRACTS.md) | Honti2024 full methods、PharmaQAI2026 methods、延遲/對齊強威脅及 static code |
| [TASK_STATE.md](TASK_STATE.md) | 原始scope、完成要求、未完成工作與下一步 |
| [LINEAR_FEASIBILITY_RESULTS.md](LINEAR_FEASIBILITY_RESULTS.md) | 預封存線性pilot的完整負結果與不外推範圍 |
| [provenance/qualification_checks.json](provenance/qualification_checks.json) | 來源定義下的數據核對，非 forecast performance |

兩個已足以改變選題的反證：

1. 製藥1005批次以「共享任一原料lot」相連時形成單一component。不能聲稱可以在這份資料上做全原料 genealogy-disjoint train/test；需改成明確的時間／特定原料lot問題，不能悄悄把 split放寬當同一claim。
2. Mining Process 雖發布 hourly rows，並非連續小時grid。3614 rows有多種時間間隔，最大相鄰間隔1148400s；row horizon不等physical-hour horizon。現有loader以row建立windows，須在forecasting前釐清clock。

Raw資料、全文及foreign code snapshots全在ignored `data/industrial_time_series_topics_i0/`，沒有執行foreign模型，也沒有寄信/請作者提供資料。每个candidate的GO只指下一層可行性審查，不指automatic控制或newmethodGO。
