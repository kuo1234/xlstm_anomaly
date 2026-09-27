# 主張邊界

**查核日期：** 2026-09-27。請搭配 [prior-art 發現](prior_art_coldstart.md)、[可重用證據](reusable_evidence.md)及[protocol 提案](proposed_p5_0b_protocol.md)閱讀。

## 本次審查支持的主張

- 已查的 COLDSTART workflows 與一般 commissioning sample complexity、fixed-N curves、回溯 aggregate `N*`、conformal calibration 有實質重疊。
- 在本次檢視的公開版本中，未找到完全等價的 per-target online stop，該 stop 只使用累積 normal evidence 且先於 future outcome labels。此結論只適用於明列版本，不證明全球不存在此方法。
- M1 凍結結案狀態是 `FINAL_STAGE1_GATE_ALREADY_IMPOSSIBLE`：九台已評估 machines 令 frozen FPR gate 在數學上不可達，其餘 19 台本輪未評估。M1 僅支持狹義 source-native claim。
- Frozen M1 scores 可在相同九條 streams 建立 score-only retrospective feature/trajectory，但須遵守另行 protocol、不得依 test outcomes 選 rule。

## 本次審查不支持的主張

- M1 證明 cross-entity transfer calibration failure、普遍 xLSTM 無效或普遍 forecasting 無效。
- Empirical score-only trajectory 等同 prospective deployment-readiness certificate。
- 由 test labels 事後推定的 normal interval 等同 prospective verified-normal commissioning evidence。
- Threshold stability、nominal quantile、IID binomial bounds 或 block-bootstrap sensitivity，在 serial dependence/repeated looks 下保證 future pointwise、long-run 或 stream-wide false-alarm rate。
- COLDSTART 已查版本證明任何地方皆不存在 sequential acquisition 方法。

## 必須採用的用語

只有在存在有效的 normal-side evaluator 時，才使用**回溯性 empirical normal-side readiness feasibility**。在 provenance 尚未證明前稱作 `reference-normal`，不可稱為 `verified-normal`。Detector qualification（anomaly discrimination）和 target commissioning readiness 必須分開。P5-0B 可用 evaluator-only suffix labels 評估 anomaly discrimination，但不能用該 labels 選 stopping rule 或 threshold。
