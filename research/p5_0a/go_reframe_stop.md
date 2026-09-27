# P5-0A 終態處置

**查核日期：** 2026-09-27
**本輪終態：`P5_0A_REFRAME`。**

## 理由

1. COLDSTART 對健康 commissioning sample complexity、fixed-N curves、`N*` 與 conformal calibration 的廣義 novelty 形成實質限制。
2. 在指定公開版本中，沒有確認已存在只依累積 normal evidence、且先於 future outcome labels 的等價 per-target online stop。因此對窄化 gap，尚未建立 `NOVELTY_THREAT_BLOCKING`；這是有限範圍的審查結論，不能聲稱已證明普遍不存在。
3. M1 score artifacts 可支持九條 source-native streams 上有限的 score-only retrospective READY trajectories，但沒有獨立且獲准的 normal evaluator mask。M1 凍結 FPR gate failure 排除將其當 readiness efficacy evidence，不得挽救 M1。
4. P1r 與 R0 可作動機和 baseline mechanics，不提供 readiness outcome evidence。資料集線索的 labels/intervals 均屬回溯資訊，不能證明 prospective verified-normal prefixes。
5. 完成 manifest/provenance 審查後，或可考慮小型回溯分析。P5-0B protocol 提案限 no-new-training，尚未授權執行。

## 選項

- **P5_0A_GO：** 目前不建議。僅當 reviewer 接受窄化問題，且執行前能確認合格、獨立可辯護的 normal-side evaluator，才考慮。
- **P5_0A_REFRAME：** 建議。限制為 per-target score-only trajectories 的回溯 empirical feasibility；不主張廣義 novelty、prospective deployment 或 certification。
- **P5_0A_STOP：** 若無法建立合格的 normal-side evaluation、沒有 certification 就不具研究價值，或 prior-art recheck 找到等價 sequential acquisition 方法，則停止。

P5-0A 未授權或執行任何實驗。Gate 與邊界詳見 [P5-0B protocol 提案](proposed_p5_0b_protocol.md) 及[主張邊界](claim_boundary.md)。
