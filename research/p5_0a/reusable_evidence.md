# 可重用證據分類

**查核日期：** 2026-09-27。分類描述哪些內容可帶入「未來且另行授權」的 P5-0B，不等同於確認性證據。另見[清冊](existing_artifact_inventory.md)與[主張邊界](claim_boundary.md)。

| 證據 | 分類 | 可允許用途 | 不允許的推論 |
|---|---|---|---|
| M1 Stage1A/Stage1B-R frozen public score arrays、manifests、train calibration references/thresholds，九台 machines | `REUSABLE_DIRECTLY` | 依事先固定規則計算 score-only retrospective prefix features 與 READY trajectories；不依 test outcomes 選規則 | 不代表 readiness efficacy、future normal FPR 或 verified-normal commissioning。Stage1A train-normal 是 benchmark assumption，不是逐列獨立驗證。 |
| M1 結果表/diagnostics 與 Issue #11 closeout | `MOTIVATION_ONLY` | 保留凍結結論；說明 ranking 與 operating-point reliability 須分開 | 不得重開/挽救 M1；不得推論 cross-entity transfer failure 或普遍 xLSTM/forecasting failure。 |
| M1 hold-forward normal FPR evidence | `MUST_REVALIDATE` | 僅在取得可獨立許可的 normal mask 或 attested interval、並記錄有效性後使用 | 本審查不可透過開啟 protected labels 建立 normal set。現有 scores 不能證明 normal status。 |
| P1r observable control | `MOTIVATION_ONLY` | 選擇透明 observable baselines；承認相對 temporally matched observables 沒有 resolved added value | 不代表真實 commissioning 效果或 READY 預測價值。 |
| R0 within-machine internal-vs-score/history diagnostic | `MOTIVATION_ONLY` | 支持 target heterogeneity 的動機與 observable-first 設計 | 不代表 target-specific commissioning/readiness 成功或 transfer proof。 |
| PreDist v2 與 CARE v6 公開 labels/normal-event 文件 | 回溯 feasibility 線索為 `MOTIVATION_ONLY`；用於 readiness outcome 為 `MUST_REVALIDATE` | 完成資料與 provenance 資格審查後，僅可研究 retrospective `reference-normal` feasibility | 無 provenance/collection 記錄時，不能稱為 `verified-normal`、prospective commissioning 或 confirmatory deployment evidence。 |
| COLDSTART fixed-size curves、N*、E0、E8 | 比較用途 `MOTIVATION_ONLY`；同時是 prior-art 限制 | 限縮 novelty 用語並納入 fixed-N/certification/dependence baselines | 不得稱 commissioning sample complexity、conformal calibration 或一般 N* 為新穎；不得稱 E8 bootstrap 是 time-uniform certification。 |

本審查沒有為新增證據開啟任何 labels。任何 `MUST_REVALIDATE` 轉換都需要 protocol 修訂及明確資料授權。
