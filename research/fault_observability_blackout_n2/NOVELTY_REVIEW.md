# Issue #29：novelty 與 problem framing 反證審查

日期：2026-10-06。執行依據：[review task comment](https://github.com/kuo1234/xlstm_anomaly/issues/29#issuecomment-6008999873)。同一 branch `codex/fault-observability-blackout-n2`；審查基準 commit `497a4f73eee4aef72fbaf395c61703e89d127156`。本文是獨立判斷，未把 reviewer 的排序當作研究結論。原 N2 seal、結果、程式與既有 STOP 保持不變。

**Primary verdict：CROSS_DATASET_REPLICATION_REQUIRED。** Secondary：**PRIOR_ART_COLLISION、TRIVIAL_CONTRACT_EFFECT、INSUFFICIENT_GENERALITY**。目前不給 METHOD_NOVELTY_PLAUSIBLE。Evaluation 的殘餘題目值得做小範圍可行性審查，但還未達 paper-level novelty GO；systems 題目需要不同的資料與效用證據。

完成範圍：五篇最近相關工作的完整 methodology/evaluation 閱讀、指定威脅的分級檢查、三條不同貢獻路線各十問、D1–D11 攻擊、第二資料來源的 bounded data-only inspection、下一步 protocol draft。沒有訓練、推論、模型分數、模型修改或 cross-dataset experiment。

## 0. N2 到底支持什麼

[RESULTS.md](RESULTS.md) 與 [RESEARCH_DECISION.md](RESEARCH_DECISION.md)：五個新 Spark traces、六個 driver-labelled events；五個有固定合法 controls 的事件跨四個 applications，strict finite-history W32 相對 current-vector 多損失 39.06–50.00pp 機會。十五個固定 annotation-clean pre-controls 的額外 history loss 全為零，current-vector availability 最低 98.44%。一個沒有合法 controls 的事件保留 unsupported；其 50.79pp 不放進 controlled effect range。

這是 **Exathlon-internal prospective holdout replication**。共享 Spark 環境、相同故障家族、跨 applications，不能升格成獨立工業場域或 cross-dataset replication。「external replication」若被理解成第二資料來源，應收窄為上述範圍。Annotation-clean 也不等於經物理驗證的 healthy。

效果依賴固定 19-feature causal recipe、5s bounded forward fill、observed target 與 strict all-finite history eligibility。這是被驗證的部署 contract，沒有證明所有 LSTM/xLSTM、partial-observation 方法都必須停止。六個 recovery episodes 的 32s 是 feature-vector recovery 到 first W32-eligible target 的差，並非實際 alarm delay；其中一個越過 annotation end。舊 E1/N0/N1 STOP 不因 N2 解鎖。

最重要的缺口：N2 只有 mask/opportunity，沒有 conditional detector accuracy、alarm recall、false-alarm cost、deadline utility。它**未證明 conditional accuracy 一定樂觀**。被移除的樣本可以更難或更容易，AP 還受 prevalence 影響，偏差方向須實測。

## A. 四個候選主張的拆解

### A1：fault-conditioned scoring availability

可描述 `C_y = P(A=1 | Y=y)`、fault 與 normal 的 coverage gap，但 class association 不自動等於統計上的 MNAR；missingness 在可觀測 covariates 條件下可能是 MAR。Informative missingness 已被 GRU-D 系統研究。更直接的 GST-Pro 已明說異常期間觀測不可取得，且設計不需要當前 target 的 scorer（B 表）。因此「故障時資料缺失」與「仍能打分」不是新問題。

可能的殘餘 gap 是：在具 provenance、共同 time denominator、自然 observation-process failure 的真實資料中，現有 detector/evaluator 是否系統性刪掉故障機會，進而改變方法比較或運作判斷。這是待驗證的 benchmark/evaluation 問題，不能只靠 `C_fault < C_normal` 宣告 novelty。N2 提供一個 contract-specific 實例，尚無第二來源或 ranking/utility evidence。

### A2：quality × availability

Selective prediction 已聯合討論 covered risk 與 coverage；group selective disparities 也已指出 aggregate 改善可以隱藏群組退化。定義 `A` 為 input/scorer feasibility、`R` 為 voluntary acceptance，實際接受 `g=A·R`；標準 selection function 可以包含 mask/support，並不在數學上排除被迫缺輸出。分開記錄原因有工程價值，但不是新的 risk–coverage 原理。

必須分清四件事：score production `P(A=1)`、selective acceptance `E[g]`、conformal set coverage `P(Y∈Γ)`、故障事件在 deadline 前是否有可行且正確的 action。不得把前三者都叫 coverage 再混合比较。Unavailable 也不自動等於 FN；合理 abstention/escalation 可能較安全。單一 quality×coverage product 沒有決策成本根據，目前為 **PRIOR_ART_COLLISION**。

### A3：full-history amplification

在固定 1Hz、history 位於 target 之前且須連續 W32 finite 的 contract 下，恢復後再等 32s 是 eligibility predicate 的直接算術。換 indexing convention 結果可以是 W−1，並非新定理。W8/W16/W32 掃描不能把結構性結果变成方法貢獻。

值得研究的是 observation failure 與既有 causal predictor/scorer contracts 的交互作用是否真的失去 deadline 前的事件偵測機會。Prediction、current residual、distribution-of-predictions score 的支持需求不同；GST-Pro 已提供後者。Variable-length、partial-window、mask-aware continuous-time 方法不能被 strict-full-history predicate 一起判成 unavailable。N2 recovery lag 不等於這些方法的 alarm latency。**TRIVIAL_CONTRACT_EFFECT** 為現在 A3 的主判斷。

### A4：adaptive context / fallback / calibration

候選可以是 contexts `{1,8,16,32}` 的因果 fallback；但切換由 missingness/support 決定，score distribution 的可比性與 policy-level normal FPR 是核心，不是附加校正。Per-context quantile 並不自動保證切換後、serial-dependent、shifted-support stream 的 overall FPR。Mask-conditional calibration 已有文獻；GST-Pro、SFAFormer、RC-WMRAD 是重要 baseline/threat。

目前只有 proposal：先獨立證明現成 partial-observation scorer 的 operational frontier 存在缺口，再問是否有新的 calibration/decision 保證。N2 沒有證明 repair benefit，也沒有證明 short context 不漏長期異常。**STOP 新方法實作**；xLSTM 並非必要成分。

## B. Prior-art evidence matrix

下表只從 primary sources 推論。`未見` 是 inspected sections 未明確報告；`unknown` 是未取得/未驗證，不能拿來排除 collision。Retrieval depth 與 hashes 在 [sources.json](provenance/novelty_review/sources.json)、[additional_sources.json](provenance/novelty_review/additional_sources.json)。原四篇來源也見 [PRIOR_ART.md](PRIOR_ART.md)。搜尋涵蓋 informative missingness/MNAR/observation process、prediction availability、selective/risk–coverage、partial history、industrial sparse/imputation consistency、mask calibration；非 systematic-review 全文覆蓋保證。

### 完整 methodology / evaluation 閱讀的五個最近威脅

| 工作與定位 | Missingness、score/output 與 denominator | Fallback / joint objective / 對 N2 的威脅 |
|---|---|---|
| [GST-Pro / Graph Spatiotemporal Process (2024)](https://arxiv.org/html/2401.05800v1)：Intro Fig1(B1)、§3–4 Eq9、§5.1–5.2.2 | 明說 anomalous period 的 values may be inaccessible；scorer 以 forecasts 的分布評分，不要求 current target。SWaT/WADI 實驗以人工各 channel 隨機 drop；主要 ROC/PR AUC。未見 fault-conditional score production 分母；完全空 history 的行為 unknown。 | NCDE 路徑與 masked learning，不是 strict finite-history eligibility；沒有 inspected evidence 證明它聯合最佳化自然故障的 availability/utility。**比「generic imputation」更直接的 A1/A4 collision**；不能主張所有 predictor 都需要 observed target。 |
| [LSD / latent SDE (2026 preprint)](https://arxiv.org/html/2606.18898v1)：§3.2–3.3、§4/4.2、AppB | Sparse/irregular latent dynamics；likelihood score。人工 per-feature geometric burst masks 套在全 stream，train/val/test 同規則，未以 fault label 生成。Baselines interpolation 可用前後值；AUC/AP/F1，F1 使用 test max-F1。完全 unobserved target 的 scorer/code denominator unknown。 | 處理 sparse history 已是現有方法；不能把 imputed input 等同 unavailable prediction，也不能把離線 interpolation benchmark直接當 causal service。未見自然 fault-conditioned availability/accuracy 聯合報告。 |
| [SelectiveNet (2019)](https://proceedings.mlr.press/v97/geifman19a/geifman19a.pdf)：§2–3、§5–7 | `φ=E[g]`、selective risk=`E[loss·g]/φ`；分類/回歸，非自然工業 TSAD outage。Coverage-constrained objective，另有 validation coverage calibration。 | **Quality/availability tradeoff 已佔據**。Mask/input feasibility 可以进入 g；forced vs voluntary 是因果/操作來源的分類，不足以產生新 mathematical formulation。沒有直接提供 temporal fault/deadline semantics。 |
| [GRU-D (2018)](https://www.nature.com/articles/s41598-018-24271-9)：Methods mask/time/decay、Results synthetic missingness-label correlation 與 clinical data | 學習 masks、elapsed times、input/hidden decay；同 missing-rate 不同 label-correlation 的實驗。Informative missingness 已明確研究；任務主要 clinical classification。 | **A1 的一般觀念已有先例**。沒有在 inspected results 中直接定義 industrial score-unavailability/deadline denominator；這個不同不足以單獨建立 novelty。 |
| [Mask-conditional weighted conformal prediction (2025 preprint)](https://arxiv.org/html/2512.14221v1)：§2、§3.1–3.5、§4.1–4.4 | Mask-aware imputation/calibration、density-ratio/shift correction；MAR/MNAR、tabular examples。其 coverage 是 label 落在 prediction set，非 scorer 產出率。 | **Mask-conditioned calibration 已有工作**；positivity/support、estimated weights 等假設不能直接移植到 serial TSAD。未見 fault-deadline utility；不同任務不是隨意 quantile fallback 新意的證明。 |

### 其他指定與新增威脅：深度限制不可消失

| 工作 | 本次核對與 claim boundary |
|---|---|
| [SFAFormer, Information Sciences 2026](https://www.sciencedirect.com/science/article/pii/S0020025526000253)，DOI 10.1016/j.ins.2026.123094 | Primary indexed abstract/introduction：sampling-frequency-aware embedding、patch/variable Transformer、免 interpolation，含 sparse/irregular benchmarks。Direct full-page 403。Exact mask generation、fully missing output、denominator、causal/readout 與 calibration **unknown**，仍是 A4 強威脅。 |
| [M2SC2-AD, 2026](https://doi.org/10.1016/j.ipm.2026.104948)，PII S0306457326003390 | DOI→publisher redirect verified；取得的 2736-byte HTML **不是 full text**，ScienceDirect 403。不能以第三方摘要完成 method/evaluation clearance；細節 **unknown**。編排的 December 2026 issue 不當成當前已出版日期；online-first date unknown。 |
| [RC-WMRAD, 2026](https://www.mdpi.com/1424-8220/26/18/5751) | 先前 primary indexed §3.3–3.5/4.3、Eq18/21 支持 observation-conditioned fusion、observed-target handling；本次仍 403。Exact overlap **unknown**，不是「沒有解決」。Mask-aware scoring 已明確，不准用 strict-full-history 淘汰它。 |
| [MoPIN, 2025](https://ieeexplore.ieee.org/abstract/document/11008721) | 已查 primary publisher abstract：industrial sparse observations / imputation consistency。Direct 418、full methodology/evaluation unavailable，denominator/fallback/joint objective **unknown**。 |
| [Dietterich & Zemicheal, 2018](https://arxiv.org/html/1809.01605v1)，§3/5 full text | Missing-feature point-query anomaly detection、MCAR 比較已有；無法由 generic missing handling 未測 N2 判定 novelty。 |
| [ImAD, 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/f99f7b22ad47fa6ce151730cf8d17911-Paper-Conference.pdf)，§4.1/5、AppK full PDF | Imputation bias、joint imputation/detection、11 tabular datasets；incomplete time series 不在該評估範圍。N2 不是新的 imputation objective。 |
| [Selective classification disparities](https://arxiv.org/html/2010.14134v1) | Group-specific risk/coverage 與 aggregate improvement 掩盖群組差異已有；不能以 class-conditional coverage formula 當成新原理。 |
| [Industrial wind-turbine masked autoencoder, 2026](https://wes.copernicus.org/articles/11/1163/2026/index.html)，sensor-error robustness evaluation / data availability | 区分 sensor errors 與 component failure，masked/unmasked error 比較用同 inter-failure window；這個工業問題已有實例。資料受 NDA、非公開，不能當作可直接 replication 的第二資料集。 |
| [Google SRE: Service Level Objectives](https://sre.google/sre-book/service-level-objectives/) | Usable service fraction、success/latency SLI/SLO 已成熟。把 score availability 改叫 uptime 沒有 systems novelty；需提供故障 deadline、支持狀態與安全 action 的實際新結果。 |

補充 A4 的搜尋邊界：[DATECT (2023)](https://www.sciencedirect.com/science/article/pii/S0306457323001206) 的 primary publisher preview 已有 adaptive window normalization / score-shift 問題；這不等於 support-triggered fallback。[STMoE (2026)](https://www.sciencedirect.com/science/article/pii/S095741742601050X) 的 primary preview 以 missing-pattern-aware gating 整合 short/long temporal 等 experts，但任務是 imputation。[Graph-MoE](https://arxiv.org/abs/2412.19108) 已使用 experts 做 TSAD；其 router 不據此推定解決 unavailable outputs。[Karaahmetoglu / Ilhan / Kozat](https://fatih-ilhan.github.io/publications/UOAD) 的 author abstract 明確處理 variable-length / irregular / missing-value sequences、time-gated LSTM + SVDD。這四項是 **abstract/preview depth**，未納入五篇 full-methodology clearance；fault-conditioned availability、fully empty support、joint objective 的細節仍 unknown。它們進一步削弱「多 context + router」或「LSTM 加 masks 就新」的先驗，沒有證明特定新方法被完全解決。Multi-resolution / fallback 關鍵字檢索沒有帶來已讀且可直接排除全部 overlap 的來源，這是 corpus limit。

未取得全文的四個威脅不能用「unknown」替自己取得 novelty GO。即使五個全文來源尚未逐字使用 N2 的 metric，問題、selection 機制、partial-observation 方法已有相當覆蓋。全文 method/evaluation 是本文的證據；未執行其 code、未驗證 all-missing corner cases 或所有 benchmark denominator。

## C. 三條獨立 paper 候選：各十個問題

### C1：Evaluation / benchmark——共同 clock 上的 scoring-support 與 selection audit

1. **Scientific question**：自然 observation failure 下，conditional-only TSAD 指標是否改變方法排名、故障事件判讀或 deadline 結論？
2. **最近三篇**：GST-Pro、LSD、SelectiveNet（B）；GRU-D 補足 informative missingness 威脅。
3. **真正 gap**：不是新 coverage 公式；是 provenance-backed common-clock ledger，區分 raw unavailable / feature transform / contract / runtime / voluntary abstention，驗證現有評估結論是否受 selection 改寫。Gap 尚未證實。
4. **N2 支持**：一個固定 legacy contract 的 class-associated opportunity loss；不支持 bias direction、rank reversal 或新 metric 原理。
5. **缺資料/實驗**：第二自然來源、fault-independent observer evidence、各現成 scorer 的原生 output contract、可比因果 clock、實際 quality/FPR/event utility。輸出缺口不得用任意 zero-score 補成已觀測。
6. **Reviewer kill**：只是刪除 NaN 的已知 evaluation bug；modern partial-observation baseline 根本沒缺輸出；availability 低仍能即時抓到每個事件。
7. **最小 falsification**：先 data/denominator audit；下一個獨立 scope 若允許 scorer replay，固定 common target clock、至少一個原生 mask-aware competitor，逐項比較原 evaluator 與 ledger interpretation。若差只存在人为 strict rule、沒有事件/排名/效用影響，STOP claim。
8. **Novelty type**：有條件的 empirical evaluation/benchmark；不是方法、理論或 class-coverage metric novelty。
9. **xLSTM 必要嗎**：不必要。xLSTM/LSTM 至多是受相同 preprocessing/contract 影響的例子。
10. **值得 paper line 嗎**：目前僅值得小型 feasibility gate。跨來源及現成方法下仍有 materially different operational interpretation 才可能成立。

### C2：Method——endogenous support selection 後的 calibrated context/fallback

1. **Scientific question**：在 support-dependent context switching 下，能否同時控制 normal FPR 與提高 deadline 前有支持的偵測效用？
2. **最近三篇**：GST-Pro、SFAFormer、mask-conditional weighted CP；RC-WMRAD/MoPIN 的 full overlap 仍 unknown。
3. **真正 gap**：若有，應是受時序/選擇影響的 calibration 或決策保證，而非 masks、variable history、多 context 或 quantile 本身。尚無證明現成方法無法達成。
4. **N2 支持**：legacy full-history contract 會失去機會；不支持新 fallback 更準、FPR 安全、資訊足夠或 superiority。
5. **缺資料/實驗**：可用 normal-only calibration/support strata、serial dependence 設定、長期故障、benign dropouts、強 mask-aware baseline、shift 及 positivity 診斷。
6. **Reviewer kill**：既有 partial-observation scorer 已取代需要修補的 predicate；{1,8,16,32}+calibration 是拼裝，沒有新結果。
7. **最小 falsification**：先鎖定 calibration/utility protocol；未來獨立授權下比較現成方法 frontier 與簡單固定 short-context baseline。若已達到相同 FPR/事件效用，STOP 新 learner；不得因 mask availability 較高便宣布贏。
8. **Novelty type**：可能的 statistical/method contribution，但目前 PRIOR_ART_COLLISION，不給 METHOD_NOVELTY_PLAUSIBLE。
9. **xLSTM 必要嗎**：不必要，且選 architecture 不能替代 novelty 證明。
10. **值得 paper line 嗎**：目前 STOP implementation。C1 有實際未解決缺口與已知理論不適用的精確理由後再考慮。

### C3：Systems——fault-time decision continuity 與安全 escalation

1. **Scientific question**：physical fault 與 observer/communication failure 交互出現時，service 能否在指定 deadline 交付具支持的 action 或安全 escalation？
2. **最近三篇**：wind-turbine masked-autoencoder study、RC-WMRAD（完整 overlap unknown）、GST-Pro。分別涵蓋 measurement-vs-component fault、supported residual/event evaluation、缺 current observation 仍評分。Google SRE SLO 是額外的 systems 基準書，service availability 原理也不是新貢獻。
3. **真正 gap**：只有實際 observation→arrival→score→action 的可追蹤機制、deadline/cost 與 fault attribution 才可能超越既有 uptime；非把 coverage 改名。
4. **N2 支持**：source-time contract feasibility counterexample；沒有 arrival timestamps、service failures、執行時間或 operator outcome。
5. **缺資料/實驗**：quality/arrival flags、独立 shadow observer、physical-vs-sensor/transport labels、service logs、alarm/escalation 成本與 deadline、保護層接口。
6. **Reviewer kill**：純 monitoring SLA engineering；故障本來會讓 logger 掛掉；guessing continuous scores 反而更危險。
7. **最小 falsification**：先驗證一個有 provenance 的實際系統是否能區分兩種故障與 action 時鐘。若所有可用資料只有 retrospective interpolated arrays，STOP service-continuity claim；若既有 health monitoring已保留相同deadline效用，STOP新系統claim。
8. **Novelty type**：可能的 systems measurement/design study；不是目前已實證的 method。SYSTEMS_FRAMING_PLAUSIBLE 只能作未來假說，非本次 primary verdict。
9. **xLSTM 必要嗎**：不必要；deterministic protection/interlocks 獨立於 detector/LLM，不能以模型 fallback 代替。
10. **值得 paper line 嗎**：資料門檻比 C1 更高。目前無 service-clock evidence，不投入新系統實作。

## D. Reviewer-style attacks：不保護第一個正結果

| Attack | 判斷、尚缺的反證與 stop condition |
|---|---|
| D1：obvious dataset-specific telemetry failure | 成立為重大威脅。Driver fault 影響 logger/collector 不出人意料；新 holdout 增加 repeatability，沒有建立新物理機制。第二來源與觀测过程证據缺失。 |
| D2：trivial 32s arithmetic | 成立。W32 recovery lag 不當 novelty；保留為實證影響量。若唯一結果就是 W 的延遲，STOP A3 paper。 |
| D3：mask-aware methods already solve | 部分成立，GST-Pro 是直接反例。不能以另加 all-finite predicate 製造對手不可用。完全空支持是否能產生可信分數仍 unknown；需 native contracts，而非假定修好/失敗。 |
| D4：coverage/risk already known | 成立。A2 new-metric claim STOP；故障条件、輸入原因與 deadline 的實證結果仍須獨立证明。 |
| D5：evaluation bug, not method | 成立的可能性高。若原 evaluator 改成共同分母即可，應誠實定位 audit/benchmark；沒有 ranking/utility impact 時連獨立 paper 也可能不足。 |
| D6：driver-only generalization weak | 成立。共享 Spark、同家族、少量 controlled events；其他 fault/unknown overlap 不得事後挑掉。不能推論工廠全部異常。 |
| D7：penalizing legitimate abstention | 成立。將 UNAVAILABLE、ABSTAIN、ESCALATE 分開；未觀測 label 不補 normal；不把任何拒答直接當 FN。事前 action cost/deadline 決定何謂 failure。 |
| D8：guessing more is less safe | 成立。填零/無限 forward fill 可以讓 availability=1，但不證明支持或正確。有效 score、supported action 與 safe escalation 均要評估。 |
| D9：fallback FP / long-anomaly misses | 未測，不能反駁。Normal FPR 需 policy-level、benign missingness 與 support shift 檢驗；short contexts 可能漏慢變/長期故障。N2 mask gain 不能解鎖修補。 |
| D10：我們可能人為製造 unavailability | 比 reviewer 排序更優先。19-feature fixed bundle + ffill5 + strict all-finite 是特定政策；改 scoring functional/current-target requirement 即可消除大部分 gap。先做 native-policy/denominator audit；若只是弱 contract，不建新 learner。 |
| D11：collection semantics / clock / utility 不可辨識 | 更深威脅：change-only reporting、未安裝 channel、actual packet loss、sensor invalid 不能混成同一 NaN。Lossless sparse encoding 可有完全相同資訊但不同 tensor masks；timestamp 不等 arrival/deadline。低 timestamp coverage 仍可能捕捉所有事件。若這些不可識別，STOP MNAR/real-time/utility claims。 |

可加一個不涉及模型的 negative-control protocol：同一 fully observed signal 做**資訊等價**的 dense vs lossless change-only representation，檢查 coverage 結論是否只因 encoding 而翻轉。這是檢查度量有效性，不當成新的 dropout experiment，也不在本次執行。

## E. 第二真實來源的 feasibility evidence

### E1. 3W：取得 bytes，但沒有 replication

Primary [3W 2.0 paper](https://arxiv.org/html/2507.01048v1)、[official repository pinned commit](https://github.com/petrobras/3W/tree/d57c058af6baf65f1b285f3e56f46e4f018a07d9)。官方說明 native acquisition 已經含 1Hz linear interpolation，並保留 missing/frozen variables；WELL real、SIMULATED、DRAWN 必須分開。不是「untouched real-time arrivals」。Class、operational state 與 unknown 各有不同語義，不能互換。

固定抽樣規則：在 pinned 完整 tree 中，class directory 0/2/3 各取 lexicographically first `WELL-*.parquet`；先固定再讀 null/labels。它是 bounded feasibility convenience sample，**不是 inferential sample、沒有檢驗全資料集**。Tree 2585 entries、不 truncated；blob identity + SHA256 存於 [3w_sources.json](provenance/novelty_review/3w_sources.json)，schema/counts 存於 [3w_sample_inspection.json](provenance/novelty_review/3w_sample_inspection.json)。DuckDB 1.4.3 只讀欄位/labels/nulls，沒有模型。

| Pinned file | rows | released class counts | 整欄缺失 / 間歇缺失 channels |
|---|---:|---|---:|
| `dataset/0/WELL-00001_20170201010207.parquet` | 21474 | 0:17874；unknown:3600 | 9 / 0 |
| `dataset/2/WELL-00002_20131104004101.parquet` | 12721 | 0:3755；2:217；102:5149；unknown:3600 | 23 / 0 |
| `dataset/3/WELL-00001_20170320120025.parquet` | 21576 | 3:17976；unknown:3600 | 9 / 0 |

Class2 是 DHSV spurious closure、102 是 transient2，class3 severe slugging，0 normal；released null 保留 unknown。三檔都有 state0/unknown，不能據此把 fault class 改 healthy。All-null 不表示 fault dropout，可能是未安裝/未發布 sensors；**installed bundle semantics unknown**，不能看標籤/效果後删欄救活availability。

這三檔沒有 intermittently missing channel，不能正向重現 N2，也不能宣告整個 3W 沒有這個現象。較大但仍 data-only、result-blind 的固定 coverage scan 與 sensor/collection semantics audit 才是下一個可行性問題。沒有原生 arrival/quality flags 時，最多審查 released-observation coverage，不能聲稱 service outage。

### E2. QAPPD：release identity 不一致

[Official Zenodo version1.0](https://zenodo.org/records/20287835)（2026-05-23、DOI 10.5281/zenodo.20287835）是 10 train/test/label pairs、14 channels、100Hz 的 physical Quanser Aero2 cyclic testbed，binary test labels。Pinned [author repository](https://github.com/JRC-ISIA/industrial-federated-learning/tree/7936f683ccc222c216ccfcc00bd56bd8eeb5ed76) 指向這個 release。

但 LSD 的 Table4 / AppB 描述 QAPPD **16 traces / 15 variates**。這個 release/preprocessing bridge **unknown**，不能默認兩者等價。未下載或 unpickle 其 arrays；native missingness、故障造成 observation loss、timestamp/arrival semantics 也 unknown。人工 burst masks 的 benchmark 可作 corruption control，不能當自然 fault-conditioned replication。公開 metadata 的「independent series」不等於獨立 physical fleets。

### E3. 其他來源的 scope

Wind study NDA 無 public data，保留 access blocker，不繞過。GECCO official [Zenodo3884398](https://zenodo.org/records/3884398) 可做後續 raw/schema/rules audit，但本次未下載，event labels 是否為 physical faults、native missingness 語義 unknown。Processed finite-array SMD/SMAP/MSL 或人工 masking 不能提供自然 observer outage 證據；HAI/SWaT/WADI attack label 也不自動等於自然故障與 arrival loss。不能從附近 release、檔名或 attack 代猜 missingness mechanism。

## F. 下一個最小 task 的 draft（不是自動擴張授權）

獨立排序為：**先 audit collection semantics / native output contract / denominator，再第二來源 feasibility，再才考慮 quality evaluation；新 architecture 最後且目前 STOP。** 這比先保護 A1、再做多 context 更可能推翻現有 framing。

1. 固定一個來源 release/SHA、result-blind sample budget（建議 3W real WELL metadata + 至多30檔，依固定 tree order 與 class strata）；完整記錄沒有合格事件、全欄缺失、unknown labels，不替換不挑 favorable traces。下載前記選取規則；raw 全 ignored。
2. 固定 sensor-installation / value-validity / collection-semantics 證據標準。沒有證據便寫 unknown；保持 static absent 與 within-channel outages 分離。Paper interpolation、發布層缺失與 real-time acquisition loss 不可合併。
3. 只做 schema、timestamp cadence、原生 missingness run/label alignment、來源 hash 與 native support/denominator 的閱讀核對；不算 anomaly scores、不訓練、不重新定義 N2 recipe。原生 scorer 是否可打分須從其 contract/code 讀取，fully empty history unknown 就保留。
4. **Data feasibility GO** 需至少一個不同物理來源有同一 source-supported sensor bundle 的自然 within-channel observation gaps，fault/control labels 與 source time 可對齊、靜態不安裝與未知標籤不混入。這只允許 protocol review；不是跨資料集效應、MNAR 因果或 method GO。
5. 若沒有 qualifying data、資料已插值到無法還原 observation process、gap 只來自 static channels，則 STOP cross-dataset availability study 或 REFRAME 至 released-data audit；不得用人工 masks 補成 natural replication。
6. 未來若再有獨立 reviewer task 允許實際 scorer evaluation，須先鎖共同 clock、native partial-observation competitor、causal preprocessing、normal FPR calibration 與 ALARM/NORMAL/ABSTAIN/UNAVAILABLE/ESCALATE 的 deadline/cost。Conditional quality、availability 與 event outcomes 分別報告；缺輸出相關品質只能 bounds/unknown，不能補造真實 performance。

## G. Research decision 與完成邊界

**CROSS_DATASET_REPLICATION_REQUIRED** 是 primary research verdict，並不表示已找到合格第二來源。A2 formulation collision、A3 contract arithmetic、A4 method collision、A1 generality/bias 尚缺。最可辯護的 current claim 仍是「一個被鎖定且可 replay 的 Exathlon contract，在 driver-labelled holdout 失去 scoring opportunities」。不能升格成 xLSTM novelty、universal detector blindspot、real alarm delay 或 paper-ready conclusion。

本次 review task 完成；**bounded provenance/data/denominator audit 的下一個 reviewer scope 可以繼續，method development/large experiments STOP**。全文 access blockers、QAPPD bridge、3W bundle/arrival semantics 未解除。本文不修改既有 M0 protocol/research gates，也不由 commit/push 授權推導研究 GO。Verification 記錄見 [verification.json](provenance/novelty_review/verification.json)。
