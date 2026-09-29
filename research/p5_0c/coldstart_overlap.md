# COLDSTART 與 P5 元件重疊查核

**查核 pin：** [COLDSTART `9454d21f1f0ee4924868ce171607e19a3648f1ec`](https://github.com/priestly-ops/COLDSTART/tree/9454d21f1f0ee4924868ce171607e19a3648f1ec)

查核直接檢查 P0.5 voraus runner、source/target split builder、AURSAD protocol builder，以及固定 N 的 AURSAD runner/N* estimator；不是只依賴 README。未讀取 anomaly performance output。

| 元件 | COLDSTART 實作 | 與 P5 的關係 |
|---|---|---|
| voraus source/target | `split_generator.py` 將 setting PRE_A=72 當 source、PRE_B=73 當 target；兩者是同一 Yu-Cobot dataset 的 Variant code，不是不同 robot。 | 跨實體 source→held-out target 的獨立身份不成立。 |
| voraus commissioning | P0.5 固定 N `{10,25,50,100}`、20 seeds；從 target healthy episodes 隨機排列後選 commissioning prefix。 | 固定 N 曲線直接重疊；sample index prefix 是隨機抽樣 cohort，不是歷史 acquisition order。 |
| calibration / healthy evaluation | 100 筆 calibration 和 100 筆 healthy evaluation 由固定 evaluation seed 選出，所有 N/seed 共用；anomaly evaluation 使用固定 cohort。 | Retrospective fixed partition，沒有線上 READY 決策。 |
| voraus `N*` | 在 seeds 結果上 bootstrap Recall/FPR CI；取最小測試 N，使 Recall lower CI ≥ 0.90 且 FPR upper CI ≤ 0.01，否則在最大 N 右設限。 | `N*` 是觀察結果後的 aggregate estimator，不是每個 target 的 online acquisition stop。 |
| AURSAD cohort | `sample_nr` execution 按 label 分組；固定 normal calibration/evaluation 和 fault evaluation cohort；每個 seed 內 commissioning reservoir 隨機化且 N nested。 | 固定-N benchmark mechanics；不建立 chronology 或 target context stream。 |
| AURSAD N grid | 官方 protocol builder 預設 `{10,25,50,100,250,500}`；runner 同樣對各固定 N 評估並估計事後 N*。 | 樣本複雜度與 N* 非 P5 novelty。 |
| Online READY rule | 上述 inspected paths 未見「僅用該 target 當下累積 healthy commissioning evidence，在未開啟後續 outcome 前，決定是否停止收集」的 per-target stop。 | 仍是候選方法差異；此狹窄 code review 不構成廣泛 novelty 證明。 |

## 判定

廣義健康樣本需求、固定 commissioning-N 曲線、threshold calibration、Recall/FPR evaluation、retrospective `N*` 均已有直接重疊，不列為創新主張。P5 原先的差異候選只能是 per-target online stopping，但資料 target-unit gate 沒通過。因此本輪不把「COLDSTART 沒寫該 stop」升格成 P5 已有可驗證貢獻。

## 固定版 primary sources

- [P0.5 runner：固定 grid、metrics 與 N* 定義](https://github.com/priestly-ops/COLDSTART/blob/9454d21f1f0ee4924868ce171607e19a3648f1ec/experiments/run_p05_anomaly_commissioning.py)
- [voraus source/target and frozen evaluation split](https://github.com/priestly-ops/COLDSTART/blob/9454d21f1f0ee4924868ce171607e19a3648f1ec/src/split_generator.py)
- [AURSAD fixed episode protocol](https://github.com/priestly-ops/COLDSTART/blob/9454d21f1f0ee4924868ce171607e19a3648f1ec/experiments/build_aursad_protocol.py)
- [AURSAD target-only runner and fixed N/N*](https://github.com/priestly-ops/COLDSTART/blob/9454d21f1f0ee4924868ce171607e19a3648f1ec/experiments/run_targetonly_aursad.py)
