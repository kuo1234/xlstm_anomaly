# P5 與 COLDSTART 組成比較

**查核日期：** 2026-09-27。來源及範圍限制見 [COLDSTART prior-art 審查](prior_art_coldstart.md)。

| 組成項目 | COLDSTART 已查版本 | P5 預計項目 | 審查判讀 |
|---|---|---|---|
| Frozen detector / normal commissioning | 有 | 有 | 重疊，不是 novelty。 |
| 固定 commissioning sizes 與多 seeds | 有：`{10,25,50,100}` | 作為比較基線 | 直接重疊。 |
| 固定 calibration/evaluation partitions | 有，從既有資料選取 | Hold-forward reference-normal blocks | 都是回溯評估；只有真正在線上 per-target 決定是否再取得資料，才是可能差異。 |
| Threshold calibration | 有，含 conformal-style | 既有固定 threshold / 透明重校候選 | Calibration 本身不是 novelty。 |
| Recall/FPR/success 評估 | 有，使用回溯 outcome | Evaluator-only hidden suffix outcomes | 評估指標重疊；P5 必須隔離規則輸入與 evaluator outcome。 |
| Aggregate sample requirement `N*` | 有，回溯推導 | Per-target `tau_i` / READY 時點 | estimand 有差別，但超出已查版本的 novelty 未證立。 |
| 只用當下 normal prefix、未看 future labels 的 per-target online stop | 已查流程未找到 | 核心候選 gap | 可能差異；不能說已普遍證明新穎。 |
| 固定 replicates certification | E0：binomial/Clopper–Pearson 加 Bonferroni | feasibility 階段不作 certificate | 不等價於 anytime-valid per-target stopping。 |
| Dependence sensitivity | E8：autocorrelation/ESS 與 circular moving-block bootstrap | 必須報告 sensitivity/限制 | 不提供 time-uniform repeated-look guarantee。 |
| Cross-entity transfer / universal detector claims | 非 COLDSTART 比較核心 | 明確排除於 P5-0A 主張 | 不可由 M1/R0 推論。 |

## 解讀

P5 應重新聚焦於：只看 normal-only observations，能否產生回溯性的 per-target readiness trajectory；與 fixed-N 相比是否節省 acquisition。不得將此包裝成已認證的 stopping rule、部署保證或新的一般 calibration 方法。
