# Proposed P3-A：source-backed response support / observability audit

**DESIGN ONLY — NOT AN EXPERIMENT GO。** 建議作下一個Issue task；此檔沒有授權acquisition、training、new detector score、new policy或controller。最新review是STOP current LEFT pilot，P3-A須另有task comment。所有後續bytes／inspection在ssh kuo；main與舊sealed artifacts不變。

本audit不重做Step2d/2e的source-state驗證；它查尚未建立的runtime channel/command contract與healthy response support，優先重用既有official manifests。

## 目標

給出一個可重現的回答：现有source-backed measurements是否足以設計因果可取得的response-dynamics probe？將「schema可讀」「deployment可用」「healthy model有support」「source disturbance可標」「operational unsafe可標」分別驗收，不用其中一項替代另一項。

## Source / channel contract

每個column產生channel_manifest：raw index、original name、measurement／manipulated／command／internal-state角色、unit、sample/hold convention、time availability／latency、證據URL／pinned version／頁碼或code位置、證據status。重複display names以raw index區分，不依名字猜角色。

現有可證：official processdata labels有Time＋53variables，原始source README說measured/manipulated；3分鐘sampling与order由既有adapter驗證。缺的deployment證據標UNKNOWN。53channel之外只建立inventory，不直接啟用input：
- `setpoint_init` / `idv_init` / `time_info` / source attrs：event/profile/evaluator資訊，非online command stream。
- `additional_meas`：判明instrumentable measurement或simulator internal value、units／timestamp alignment／sampling；不能拿row index就直接對齊。
- `economic_data`：區分actual measured production/quality、setpoint與aggregate metadata；沒有獨立危險envelope不能造unsafe label。
- 真command/alarm/context：必須是runtime本來能取得、time-valid且有provenance的stream；curator知道event ID不符合此條件。

既有inspection只提供原label列表，尚不構成上述availability驗收。以metadata／文件確認channel role可以；不依fault outcomes挑有利channels。若control update與measurement在同tick的先後不明，prospective模型只允許已知past inputs；不能以未知零lag因果claim代替。

## Healthy support / training eligibility

先列source-verified healthy groups及可用型態，不憑model scores認定healthy：
- P2 50/4/4 disjoint pre-event Mode1 runs：600points／run，可作既有support參考；**尚無**healthy command-transition training windows。
- 如需source legitimate command-response／不同operating levels作training，必須另定健康來源、合法training區間、role／native-seed／shared-prefix disjointness；這是新的training eligibility contract，不能沿用P2禁止TRANSITION/NORMAL_B training的規則又偷偷餵入同test段。
- prospective test不參與scaler、lag、feature或training-hyperparameter選擇。P1/P2 outcomes與source families已exposed，不能作新的confirmatory test。
- literal paths、native seeds、duplicates／shared healthy-prefix groups、raw hashes與role manifest在新score前seal；不存在的source不替換成近似release／unknown derivative。

source文件若無healthy excitation説明，不把數值variation說成identified plant support。獲audit GO後可做healthy-only observation diagnostics：available excitation span、lag-regressor singular spectrum／effective rank、collinearity、constant channels、realization-wise coverage與sampling限制；方法及使用區間先記錄。它們只是support diagnostics，不是依rank定safety threshold、不是決定哪fault好檢測。沒有足夠source證據時，強control-response claim仍SUPPORT_INSUFFICIENT；可另提限定closed-loop prediction的baseline。

## Truth / claim contract

| Target | 本輪已知 | 缺的條件 |
|---|---|---|
| Source disturbance detection | Restricted TEP event provenance／source state convention已在Step2e/P2驗證 | 新test realizations的prospective selection與manifest；不能外推全部fault可觀測 |
| Source legitimate regime vs disturbance evidence | Source SP scenario可作受限合法operating variation對照 | 多independent commands／families、support匹配；高score／低error不等於causalhealth |
| Operational unsafe detection | **NOT_EVALUABLE** | 獨立物理envelope／hazard或有provenance的operating-risk annotations、時間尺度與availability |
| Safe normal-reference admission | **NOT_ESTABLISHED** | admissibility定義、reference／candidate寫入後後果、獨立可觀測verification依據 |

不以simulation完成、正常生產量、沒有fault ID、command authorized或prediction loss低，單獨創造safe-to-promote truth。Command與fault可能同時發生，command-aware對照不能假設二者互斥。可能的controller compensation是待證假設，不能事後把弱fault改safe。

## Audit artifacts / acceptance

建議交付SOURCE_CHANNEL_AUDIT.md、channel_manifest.json、healthy_support_manifest.json、target_semantics.md、audit_access_log.json、PROBE_READINESS.md。每個claimed fact須對應source與hash；無證據用UNKNOWN。

Acceptance逐項：
1. 完整column inventory，角色／unit／availability分別标verified或unknown；原order與constants保留。
2. Command profiles與runtime observed actuator values分清，source IDs／event schedules仍evaluator-only。
3. Healthy支援按physical/source group分離；未驗證不存在／duplicate／共有prefix不能假設獨立。
4. 3分鐘sampling／alignment／latency限制明列；沒有resampling補出未觀測response。
5. 四種target按上表分開；unsafe未有獨立truth就保持NOT_EVALUABLE。
6. 若acquisition另被授權，official pinned source＋remote raw hashes／pointer及range checks；來源失敗BLOCKED，不silent fallback。
7. 無detector output／new model／test-informedchannel-lag selection；audit只回答下一個probe是否可合理設計。
8. commit＋push＋remoteSHA核對，再中文回報#15/#16。

## 後續 experiment design（條件式，未執行）

如果audit足夠，**P3-B small lagged-response falsification**可先測一個regularized linear predictor及matched own-history對照，保留channel innovation maps，兩者same healthy support/scaler/history、healthy-only calibration。需保存innovation vectors／channel maps與response關係，不只以另一個norm的AP選winner。Control-history ablation若改變regressor數量，必須揭露capacity差異；要宣稱control-specific增量，還需另外預先設計equal-capacity negative control，不能把更多參數的gain全部稱control evidence。Prediction在t-1完成，t觀測只算residual；不讀actualfuture／eventstart label。先把這叫closed-loop predictive response，不把lag regression稱identified causal plant。

輸出source FAULT coverage／delay與NORMAL_A/NORMAL_B FPR，以及physical-run response ordering；onset/transition/settled對照由evaluator按source semantics附上，模型score全stream才避免知道onset。Late fault與late NORMAL_B用相同age windows比較，不以early fault對late normal製造分離。N為physical/source groups，不是seed或windows。

若另做LSTM：同support/context/task/calibration，普通LSTM先作representation feasibility／linear comparator；xLSTM為另行匹配capacity與backend audit，不與P10 fast-weight/admission混同。Healthy-training adequate與evidence failed分開，training cap仍下降時保持適用範圍。

若另做shadow Verify：candidate在t只用過去，protected reference不改；future evaluation到t+H才可用，完整H與選擇cohort須先freeze，不能從futurelabels挑能成功的candidate。Lower future loss只是adaptation endpoint，必須另報fault masking／normal benefit的evaluator結果；未證獨立observable verification，不能deploy COMMIT/ROLLBACK。

以上實驗的config／lags／runtime／training adequacy criteria、literal cohorts與qualitative verdict必須在新outcome前commit，checkpoint／trace seal先push，再label evaluator。Audit結論不足時停，不在同輪循序加模型把結果救成positive。
