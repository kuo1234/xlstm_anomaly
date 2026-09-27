# Prior-art 審查：COLDSTART 與既有文獻線索

**查核日期：** 2026-09-27。COLDSTART 公開來源：[priestly-ops/COLDSTART](https://github.com/priestly-ops/COLDSTART)。本文件只審查明列版本與路徑，不代表已窮盡所有已發表或未發表方法。

## COLDSTART 發現

在 main commit [`9454d21f1f0ee4924868ce171607e19a3648f1ec`](https://github.com/priestly-ops/COLDSTART/commit/9454d21f1f0ee4924868ce171607e19a3648f1ec)，`experiments/run_p05_anomaly_commissioning.py`（L1-L24、L68-L83、L162-L200、L203-L237）以 `{10, 25, 50, 100}` 固定 commissioning sizes 和多個 seeds 執行；對固定集合做 calibration/evaluation，再回溯彙總 `N*`。`src/split_generator.py`（L153-L185）從現有資料選出固定 commissioning/calibration/evaluation 集合。anomaly labels 不用於 fitting/calibration，但會用於評估 recall、FPR、success 與回溯計算 `N*`。

因此，健康 commissioning sample complexity、fixed-N 曲線、conformal calibration 與 population-level `N*` 等廣義說法和 COLDSTART 有實質重疊，不可列為 P5 novelty。

在本次檢視的公開版本中，**未找到每個 target 僅依當下累積 normal-only evidence、且在未看到未來 anomaly labels/outcomes 前線上停止取得 commissioning 資料的等價實作**。這是有範圍限制的審查結果，不是證明所有方法皆不存在。這個較窄的 gap 仍只是候選方向，不能說 novelty 已成立。

E0 branch [`9b2f96547c2e6824f2a582f863d3a4425cd63d70`](https://github.com/priestly-ops/COLDSTART/commit/9b2f96547c2e6824f2a582f863d3a4425cd63d70) 加入固定 replicates 的 binomial certification（`experiments/run_e0_certification_backbone.py` L146-L198；`src/certification.py` L88-L155），不是 per-target sequential acquisition stop。E8 branch [`f6da03453cb56ceff3bc2a8c6f8ce7a0f36d92ae`](https://github.com/priestly-ops/COLDSTART/commit/f6da03453cb56ceff3bc2a8c6f8ce7a0f36d92ae) 的 [`docs/E8_TEMPORAL_DEPENDENCE_PROTOCOL.md`](https://github.com/priestly-ops/COLDSTART/blob/f6da03453cb56ceff3bc2a8c6f8ce7a0f36d92ae/docs/E8_TEMPORAL_DEPENDENCE_PROTOCOL.md#L1-L15) 討論 autocorrelation/ESS 與 circular moving-block bootstrap sensitivity，並未提供 anytime-valid repeated-look stopping。另見統計附錄 [`a610056335a9542959fcfb063e059d9a211a8706`](https://github.com/priestly-ops/COLDSTART/blob/a610056335a9542959fcfb063e059d9a211a8706/docs/manuscript/COLDSTART_STATISTICAL_CERTIFICATION_APPENDIX.md#L93-L100)。

## Issue #9 既有審查所列文獻線索

下列線索承襲 Issue #9 comment 所引用的 [`P5_commissioning.md`](https://github.com/kuo1234/xlstm_anomaly/blob/5726732/research/adaptive_normality_issue_review_2026q3/P5_commissioning.md)（`xlstm_anomaly` repo branch/revision `research/adaptive-normality-issues-2026q3@5726732`）。本次 P5-0A **未重新審查每篇論文或 benchmark**；應視為 novelty 邊界線索，後續主張前需再核對。

- Few-shot one-class learning 與 normal-only domain adaptation 已使「少量 normal samples 就能 adaptation」不足以作貢獻：[Holly et al. 2025](https://arxiv.org/abs/2501.13052)、[Frikha et al. 2021](https://arxiv.org/abs/2007.04146)。
- 風機 target-data scarcity、transfer 與 threshold-only transfer 已有研究：[Roelofs et al. 2024](https://doi.org/10.1016/j.egyai.2024.100373)、[Jonas & Meyer 2025](https://doi.org/10.1016/j.egyai.2025.100626)。
- 最接近的 signal-level 線索是 Jonas & Meyer 2026 的 anomaly-free score proxy，可選 source mapping 並停止對固定 target sample 的 model training/optimization；其停止目標是**固定樣本上的最佳化**，不同於**停止取得更多 target-normal observations**。需納入 baseline/ablation 並精確區分：[arXiv:2608.30323](https://arxiv.org/abs/2608.30323)。
- DADA/TimeRCD 提醒需納入 frozen zero-shot detector 比較：[DADA](https://arxiv.org/abs/2405.15273)、[TimeRCD](https://arxiv.org/abs/2509.21190)。
- Cheap observable one-liners 也可能有競爭力；不應假設 neural detector 必要：[Zhu et al. 2026](https://openreview.net/forum?id=H27kvyG4qf)。
- Adaptive conformal TSAD 與 online FDR control 是相鄰統計文獻，但 estimand 不可混用；long-run coverage/FDR 不等於 anytime stream-wide FPR control：[Adaptive Conformal Inference](https://papers.nips.cc/paper/2021/file/0d441de75945e5acbc865406fc9a2559-Paper.pdf)、[Online FDR control for TSAD](https://arxiv.org/abs/2112.03196)。本次未完整重新審查這些方法或 Issue #9 protocol 所指的 2026 ICLR paper。
- WindADBench 是 held-out turbine/farm benchmark 的新線索；既有審查未獨立確認其論文/venue，需在任何廣義 benchmark novelty claim 前核對：[repository](https://github.com/ZJU-DAILY/WindADBench)。
- 公開資料前綴的 normal provenance 仍不足以支持 prospective verified-normal 說法：PreDist [Zenodo](https://zenodo.org/records/19496480)；CARE v6 [Zenodo](https://zenodo.org/records/15846963)。

## Novelty 判定

- 廣義「需要多少 normal samples 才能部署」、fixed commissioning-size curve、`N*`、conformal calibration novelty：**已有實質重疊，不能主張**。
- 較窄的 per-target、online、normal-only acquisition stopping：在指定 COLDSTART 版本中**未確認 `NOVELTY_THREAT_BLOCKING`**；但須保持限定表述，且後續應重查近期文獻與 WindADBench。
- 經 serial dependence 與 repeated looks 驗證的 stream-wide FPR certification：**本審查來源不支持**。

## COLDSTART primary source links

- [主流程 `run_p05_anomaly_commissioning.py`](https://github.com/priestly-ops/COLDSTART/blob/9454d21f1f0ee4924868ce171607e19a3648f1ec/experiments/run_p05_anomaly_commissioning.py#L1-L24)
- [固定資料切分 `split_generator.py`](https://github.com/priestly-ops/COLDSTART/blob/9454d21f1f0ee4924868ce171607e19a3648f1ec/src/split_generator.py#L153-L185)
- [E0 runner](https://github.com/priestly-ops/COLDSTART/blob/9b2f96547c2e6824f2a582f863d3a4425cd63d70/experiments/run_e0_certification_backbone.py#L146-L198)、[certification implementation](https://github.com/priestly-ops/COLDSTART/blob/9b2f96547c2e6824f2a582f863d3a4425cd63d70/src/certification.py#L88-L155)
- [E8 dependence protocol](https://github.com/priestly-ops/COLDSTART/blob/f6da03453cb56ceff3bc2a8c6f8ce7a0f36d92ae/docs/E8_TEMPORAL_DEPENDENCE_PROTOCOL.md#L1-L15)
- [Statistical certification appendix](https://github.com/priestly-ops/COLDSTART/blob/a610056335a9542959fcfb063e059d9a211a8706/docs/manuscript/COLDSTART_STATISTICAL_CERTIFICATION_APPENDIX.md#L93-L100)
