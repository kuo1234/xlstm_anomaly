# Post-P2 research decision：先查 response support，再測 temporal evidence

**狀態：DESIGN COMPLETE / PROPOSED P3-A AUDIT / awaiting reviewer task。** 本輪是文獻與研究設計；沒有新 acquisition、模型訓練、feature extraction、policy evaluation 或 memory write。
Base：`26b4ffcc5bddcbc472116f54469302940b74f47c`；工作與來源檢查在 ssh kuo。

依據：[P2 review #15](https://github.com/kuo1234/xlstm_anomaly/issues/15#issuecomment-5980382672)、[#16 update](https://github.com/kuo1234/xlstm_anomaly/issues/16#issuecomment-5980382963)。Review 接受 protocol PASS / frozen pilot LEFT_POINT_EVIDENCE_NOT_SUPPORTED，STOP current LEFT pilot；建議下一個 research decision 比較 process-response、healthy-only temporal representation、tentative-write verification。這不是重開 LEFT 或任何新 experiment 的 GO。

## 結論與研究問題

**優先建議 P3-A：source-backed channel / command availability / healthy response-support audit。** 先回答能否合理測 response dynamics，再決定小型 healthy-only lagged-response falsification。LSTM 是後續非線性 representation comparator；xLSTM-specific claim 與 shadow Verify 都保持另行 review。

可測問題是：在相同 observable support 下，保留過去 measurement / manipulated-variable 的 response，是否能在獨立 physical interventions 上提供 R0 norm 之外的 source fault-versus-legitimate-transition 訊息？不能先把「更可預測、cross-channel一致、模型更大」當成安全證據。

已在pinned upstream再次核對：official PSM/SMD是20epochs、Adam1e-4、LR type2/type1與patience3；P2是30epochs constant LR與3000step checkpoint eligibility。P2 的 training recipe 不是 official training reproduction，兩個 anchors 在 cap 時 val loss仍下降。故 negative evidence 僅限制該 frozen adaptation；另開 LEFT adequacy study是可討論的獨立路線，但不是這輪延訓 rescue，也不是 review 優先方向。P2 weights/maps/config/code/results 全部封存。

## 已有 evidence 如何限制選擇

| 已驗收／已報告 evidence | 可以推論 | 不能推論 |
|---|---|---|
| Persistence / low CV / self-consistency 不能穩定分辨 source fault 與新 regime | 穩定性不足以決定 normal reference admission | 多等一段時間必然會產生 legitimacy evidence |
| P1 concentration 在 IDV3/5 反轉 | development 結構訊號有 family dependence | raw temporal channels 完全沒有資訊 |
| P2 weak-fault recall <1.1%；SP1 NORMAL_B FPR100% | 該 frozen point-score protocol 未解 coverage／new-regime alarm | LEFT / 所有 cross-view representations 一般性無效 |
| SMD cross-path 6/9 pairs 正確，PSM2/9 | 有局部 anchor-dependent signal；需保留 | 可挑 SMD 或翻轉 PSM 成為通用 Validate feature |
| Step1c oracle provenance rollback | 部分 operators 有可驗證的撤銷機制與成本 | 已存在可部署的錯誤-write detection trigger |

這些是 simulator、有限 physical realizations 的 evidence。Source disturbance、source legitimate operating change、operational unsafe 是三個不同 target。使用者已要求分開定義；unsafe-operation／safe-to-promote truth仍 NOT_EVALUABLE。

## 三條路的對照

| Route | 假設與新增資訊 | 必要 support／最小對照 | 可否證方式 | 主要 confound／成本 |
|---|---|---|---|---|
| **Process-response / lagged dynamics（優先，但先 audit）** | 加入被 norm 丟掉的 lag、measurement與actuator coordination；不同成因可能產生不同 response | source-verified channel roles、可用時間、healthy response support；先小型 regularized lagged predictor，對照 own-history / 無control-history、相同 train/scaler/history | adequate healthy support 下，fault與benign的 residual response仍重疊／family反轉，或不增於matched control | manipulated values是feedback內生量；noise能造成滿rank但不保證plant identification；steady Mode1→new regime可能OOD。Audit成本低，模型是否可做尚未驗證 |
| **Healthy-only LSTM / xLSTM representation** | 非線性／長lag可能保存 linear model未表達的時序資訊 | disjoint healthy physical runs；healthy validation選training；同context、support、prediction task、calibration；linear與普通LSTM對照 | trained mechanism adequate後，weak-family coverage／source fault-vs-benign increment仍不穩 | 不能創造未觀測的command／hazard資訊；capacity、history、support、未收斂training混淆。先LSTM feasibility，不先宣稱xLSTM優勢；GPU成本較高 |
| **Tentative write → future verification / rollback** | 額外未來 observations可能否證有害 candidate；shadow隔離降低reference exposure | protected reference、只寫past的candidate、預先固定future holdout、provenance/replay；需要可觀測且獨立於candidate-fit loss的驗證依據 | fault candidate也同樣降低future loss，或self-evaluation不能保留fault detectability | write只改演算法，不是physical plant intervention；stationary fault可自我預測。Step1c是oracle mechanics。Engineering最高，當前缺non-oracle safety trigger |

不能用 route 的 complexity 當 evidence quality。若linear probe失敗但healthy support足夠，不能推出nonlinear模型必然失敗；需新 decision 才能選 matched LSTM study。若support／可觀測性不足，直接升級model也不是合理補救。

## 兩個核心質疑

**1. 現在真的有 command-response 資料嗎？** 官方 source README說 processdata含原始measured／manipulated variables；inspection記錄53channels、Time另存。但目前沒有已審定的 time-valid online command stream，source `setpoint_init` / event schedule / `economic_data` 仍 evaluator-only。Manipulated action ≠ authorized setpoint command；兩者不可互換。Source attrs知道「這次是SP」不代表deployed model可以知道。這是現況缺口，不是宣稱資料永遠不存在。

P2 的50 healthy training runs只取各600-point pre-event Mode1 prefix，沒有任何source command-transition windows加入訓練。這個事實不證明數值不夠excited，但也不證明具有合法新regime response support。不能憑30,000points／full-rank covariance直接聲稱可identify整個plant/controller。

**2. 比較會預測 future 的candidate，真的比較健康嗎？** 若兩個語義類別在全部可觀測history上具有相同law，任何causal representation也具有相同law；這是條件式identifiability限制，未宣称本TEP cases完全相同。更長future只有在later observables確實不同時才有額外資訊。修改shadow memory並沒有對plant做intervention，不能自己產生辨別因果的excitation。Fault被controller補償是可能解釋，尚未在這些runs驗證；弱fault不能事後改標safe。

## 為什麼 audit 先於下一個神經網路

DPCA與正常資料訓練的temporal predictors早已有先例；2024 CNN-GAT原論文摘要更直接提出fault-free Granger map與正常control-adjustment辨識。新graph／lagged model本身不是novelty。近因假設也必須區別predictive dependence與physical causality。[文獻對照與access limits](LITERATURE.md)

目前最有資訊價值的下一步是釐清：哪些control/action channels可因果取得、3分鐘sampling是否足以觀測response、normal training到底cover哪些excitation與regime、哪種truth真的能支持研究target。這能使後續negative結果區分support mismatch、training adequacy與evidence failure，避免再把所有結果歸因scalar compression。

## Reviewable 下一個 task

建議 reviewer 授權 **P3-A audit-only**，完整驗收見 [P3A_AUDIT_SPEC.md](P3A_AUDIT_SPEC.md)。P3-A只做source/schema/availability/healthy-support inventory與manifest，任何新增來源只在ssh kuo；不產生detector scores，不看outcomes挑channel／lag／run，不把command/fault profiles變成input。

P3-A完成後：
- **AUDIT_READY_FOR_PROBE_DESIGN**：source mapping、因果可用時間、healthy support已具體且可驗證；再提出固定lagged baseline protocol、training adequacy與prospective evaluation seal，等待新experiment GO。
- **OBSERVATION_ONLY_LIMITED**：只有observed manipulated values，command／plant-causal guarantee缺；可另提closed-loop predictive probe，限定claim，不偷偷升格control-response causal model。
- **SUPPORT_INSUFFICIENT / SOURCE_BLOCKED**：記錄缺的資料與條件；不以fault/test training、額外metadata／model容量補洞。
- unsafe truth未建立時，任何結果仍不得解鎖safe admission claim。

不先填一組方便過關的lag／threshold，也不製造不存在的physical-run inventory。P3-B若获GO，必须先冻结input、模型／matched controls、lags/history、seeds、healthy validation與runtime/adequacy停止条件、physical-run/source-group selection、primary targets与qualitative verdict；score/checkpoint seal先commit+push再source-state evaluation。P1/P2 events僅development／history，不能重新叫confirmatory transfer。全部維持 no point-adjust、no source-ID input、no overlapping-window independent N。

## 本輪完成範圍

已讀最新review、既有protocol與archived evidence、官方source README／thesis既有bytes與新primary literature。沒有新數值experiment／下載raw／改舊scores或模型。README與P2報告僅更新review acceptance，sealed結果不動。[機器可讀來源紀錄](source_review.json)
