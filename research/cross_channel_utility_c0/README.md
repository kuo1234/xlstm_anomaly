# C0 — Cross-channel predictive utility：Phase A

2026-10-06；[Issue #31](https://github.com/kuo1234/xlstm_anomaly/issues/31)。獨立 forecasting topic audit；不延續 anomaly/adaptation/N2 scientific claims。基準 `53e00cd460e9b4196fdd2a95f3cacbd224caa876`，branch `codex/cross-channel-utility-c0`。

**Primary verdict：PRIOR_ART_COLLISION。Secondary：NO_PAPER_WORTHY_GAP。Phase B：NOT_RUN_GATED。** 沒有訓練、推論、utility probe、correlation/graph fitting、合成資料生成或新 architecture。Literature STOP 已足以禁止 pilot；data audit 的 unknown 不能當作 novelty clearance。

關鍵發現：related/useful/used、horizon utility→neural transfer gap 已被 Rethinking Cross-Channel Importance 直接研究；budgeted sparse dynamic interactions、CI 殘差補充、high-dimensional efficiency 又被 MS-FLOW、DUET、U-Cast、CLOC 等覆蓋。現有問題尚未被全部解決，但本次沒有提出可區分既有研究的新 residual question。

| Deliverable | 範圍 |
|---|---|
| [PRIOR_ART_REDTEAM.md](PRIOR_ART_REDTEAM.md) | 如何砍掉整條線、alternative directions |
| [NOVELTY_MATRIX.md](NOVELTY_MATRIX.md) | 七個指定 sources、CLOC 與近鄰；method/eval/ablation 深度、cost、controls、collision |
| [DATASET_QUALIFICATION.md](DATASET_QUALIFICATION.md) | 固定候選、source families、read-only samples、缺失資格 |
| [RELATED_USEFUL_USED.md](RELATED_USEFUL_USED.md) | 三個 measurement objects 與 identifiability |
| [PROTOCOL_AND_PILOT_SEAL.md](PROTOCOL_AND_PILOT_SEAL.md) | STOP record，非虛構 executable seal；若未來重開的 pre-result 門檻草案 |
| [EFFICIENCY_COST_AUDIT.md](EFFICIENCY_COST_AUDIT.md) | sparse semantics 與實際 dense kernel、成本不能省略 |
| [FINAL_GATE.md](FINAL_GATE.md) | H1–H5、decision、限制、next decision |
| [provenance/verification.json](provenance/verification.json) | source hash、read-only replay、baseline preservation |

全文/資料 bytes 留在 ignored `data/cross_channel_utility_c0/`。Provenance ledgers 保存 exact URLs/revisions/hashes；publisher/indexed previews 與 frontend HTML 不當全文/資料。停止等 reviewer，不自動轉換成另一條研究線。
