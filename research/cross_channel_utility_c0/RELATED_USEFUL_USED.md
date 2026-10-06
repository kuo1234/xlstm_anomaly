# Related / Useful / Used：measurement objects

這個三分法已有 [Rethinking](https://arxiv.org/html/2609.32187v1) 直接研究，不能當 C0 新 contribution。本次未計算以下任何數值。

- **RELATED_ONLY**：history-only dependence statistic 顯示關係，但沒有matched OOS增益。Common trend/season、hidden driver、cadence mismatch、overlapping windows都可能造成關聯；MI/Granger/graph不等因果。Utility未測時也不能武斷判RELATED_ONLY，應UNIDENTIFIABLE。
- **PREDICTIVELY_USEFUL**：對指定predictor、target/history/info cutoff/searchbudget，加入source降低新時間段risk。`ΔR=R(CI)−R(CD)`是mechanism/protocol-specific；source與target自身歷史的redundancy、joint synergy、samplevariance均重要。Probe能獲益不等neural模型會獲益。
- **USED_BY_MODEL**：固定checkpoint，保持target歷史、只干預source，輸出或loss改变；是functional reliance。Attention/router weights無法替代；joint OOD造成的loss增大不是unambiguous informative use。Retrain-without-source回答可替代性，不能與posthoc干預混稱。
- **UNIDENTIFIABLE**：data cutoff/target identity未追蹤、source干預破壞同步/分布、未matched budgets、沒實際probe或模型。C0本地全部資料目前在utility/use這一層都是此狀態。

若未來獨立scope重開，需三套隔離record：dependency僅train；source utility僅train rolling selection + untouched OOS；functional reliance在鎖定model/test protocol之下評估，不能依test loss重選sources。保留target identity與selfhistory；donor/lag-misalignment要由past-only時移、season-matched donors與negativecontrols評估OOD。Conditional incremental gain無法證明physical causal edge；沒有timestamps/availability證據便unknown。

新的問題不能只問「三者相同嗎」，因prior art已有直接答案。可能更窄的疑問是release-time available source的utility能否在publication delays/revisions下兌現；这需要不同資料與as-of protocol，仍未完成novelty審查。
