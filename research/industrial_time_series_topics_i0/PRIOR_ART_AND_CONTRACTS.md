# Closest prior art and information contracts

| Primary source / depth | 已有研究 / 對候選的威脅 | 尚缺的證據 |
|---|---|---|
| [Honti2024](https://doi.org/10.1016/j.ijpharm.2024.124509)，publishedPDF，§2.1–2.3/evaluation read | Same1005dataset；挑20mg445batches，2018–19calibration、2020test，非純randomtest。將wholetrajectory轉0–100%completion並interpolate2000points，以LSTM/biLSTMpredictwaste與offset100pointsforecast。 | Completionnormalization取actualend，是retrospectivevalidpreprocessing，但prospectivedeadline用途需要可用progress/unknownend核對；100points不是跨batch固定30min。不能未跑reproduction便稱其paperbad/leakage。Target是controllerwaste，非六個獨立finalCQAs。 |
| [PharmaQAI2026](https://www.preprints.org/manuscript/202603.0225)，未peerreviewpreprint，webfull§2/eval read；directcache403 | Samebatchleveldata、summaryfeatures、sixCQAs、pipelinetrain-onlyzscore、80/20與kfold；含explorationapp。普通多模型benchmark / Streamlitdashboard不是newgap。 | 是否chronology/lotpurged、earlyprefix、availablelabinformation沒有在所讀method中明確完整支持；不能直接因未寫便宣告實際漏。 |
| [ASSLD2025](https://www.sciencedirect.com/science/article/abs/pii/S0019057825005129)，primarypublisherabstract/preview；全文403 | Adaptive label-delaysoftsensor直接存在，SRU/polyestercase。Genericdelay+reusehistory+unlabelledrecentdata不是新問題。 | Delaygeneration/nativearrival、method/fairness完整unknown；需授權公開copy或code，不能UNKNOWN=clearance。 |
| [Multi-rate softsensor2026](https://doi.org/10.1016/j.chemolab.2026.105768)，primarypreview | Time-awareimputation/quality-awaresemi-supervision已有SRU/gasturbinecase。 | Fullcontract、sameclock/labelavailability與wholecostunknown。 |
| [Calibratedsoftsensor2026](https://ssrn.com/abstract=7181724)，primarySSRNabstract，未peerreview/fullPDFunavailable | Already分開pointaccuracy與intervalvalidity，explicit delayedfeedback對issuedinterval而非lateradaptedinterval評分。只說issued-timecalibration不新。 | Fullproof/code/nativeclock未核對，與SECOMnegativecontrolsemantics不代作industrialCQAtruth。 |
| [OnlineDTW2011](https://doi.org/10.1016/j.chemolab.2011.01.003)，institutionalabstract；fullPDFmirrorretrievefailed | Unknownbatchduration與ongoingalignment已有成熟解法，relaxedgreedy及boundaries；genericonlinesynchronizationclaimSTOP。 | Fullmethodimplementation與比較qualityforecastdeadline需要讀全文，notcleared。 |
| [Harves-time2018](https://doi.org/10.1016/j.compchemeng.2018.05.019)，primarypublisherabstract/introduction/methodpreview | RealfermentationearlyharvesttimeLasso與DTWupdates；completiontimeprediction已是应用。 | Fullpaper/code/transferqualitycaseunknown。 |
| [ActiveJIT2026](https://www.sciencedirect.com/science/article/abs/pii/S0959152426000417)，primarypreview/full403 | Informativeactivesampling+lightweightdictionary已有；用activelearning挑lab測試不新。 | 真實measurementcost/nativequeue/assaydelay與currentdatasetavailabilityunknown。 |

## Pinned InduTS model-contract triage（不等end-to-end結果）

來源在[loader_source.json](provenance/loader_source.json)、[model_contract_sources.json](provenance/model_contract_sources.json)。Foreigncode沒有修改/執行；不少是independentreimplementations，不能把此code的問題歸到originalpapers。

- Dataset_Customforecasting把pasttarget加入input；對predictionnextrows可以合法，但qualitydelay需要as-ofmask。Softsensorregression某些modelbranches也把targethistory加入；labelrow正好是inputlastrow。僅這點不足以宣告全部模型targetleakage。
- TSLambdaGRUforward明確quality_history=x_enc[:, :-1, ...]、要求seq_len≥2；排除currenttarget。Olderqualityvalues是否已返回仍是另一問題。
- HSAM_dGRUstest/valid只以previousrowquality作query；train有use_true_y_in_trainbranch；trainingteacherforcing與test資訊要分開。STALSTM只用firstquality作initialseed，其後用predictions，並非lasttarget直接copy。
- GCTsoft_sensor先從整段y（含currentlasty）算mean，再用該mean覆寫lasty。若loader/run此path，已知currenttarget可影響derivedfeature，係數1/T。這是staticinformationdependency；尚未驗證runtimeconfig/runner、輸出實際依賴幅度或performanceinflation，不能宣稱originalmethod的全部publishedgains無效。
- MP `_get_feature_columns`僅排date/mode/selectedtarget，因而可能把另一個labquality作source。該值returntime/onlineavailabilityunknown，不能由欄位numeric就當即時sensor。

這些證據支持先做availability/clockaudit，不支持newnetwork。即使只是benchmarkimplementationbug，也應定位可重現evaluationreview，不把repair當methodnovelty。

## 射出首選的最近威脅（2026-10-06補查）

| Source / 深度 | 直接collision與可測邊界 |
|---|---|
| [Bogedale2023](https://doi.org/10.3390/polym15040978)，primaryindexedmethod/evaluation＋authorrepo，directPMCrecaptcha/MDPI403，非取得cache全文 | Scalar/curvequalityprediction與nestedrandomCV已有，weight/dimension自動量測給independenttarget。Data/runtime可重現，本輪不是原作者models reproduction。Futurecyclevalidity是不同evaluationestimand，非指控randombenchmark非法。 |
| [Uddin/Lofstrom2023](https://proceedings.mlr.press/v204/uddin23a.html)，19頁formalPDF，§3.2–3.4 read | Industrialweight intervals、RF+Crepes/MAPIE/EnbPI已有。文中未測change-point，並明示sharpness與usefuloperatingrange需要工廠experiment。AddingCP不是novelty；必須比已有update/normalizedmethods，不能只靠staticRidge失敗。 |
| [Wang2026](https://doi.org/10.36001/phmconf.2026.v18i1.4829)，15頁formalPDF，§2.1/model/split/evaluation read | CAE/qualityprediction/decoder-Jacobianattribution已有；70/15/15randomsplit與train-onlynormalization。本輪不把explainability當gap，也不指控scalerleakage。Futureproductionvalidity仍需不同qualification。 |
| [Stage-aware2026](https://doi.org/10.1016/j.engappai.2026.115823)，primarypublisherpreview，fullunknown | Stageheads/channelattention等直接存在；全部其baselines/split/uncertainty未取得fulltext，不能排除overlap。 |
| [PCRpart-masscontrol2026](https://doi.org/10.1016/j.jprocont.2026.103725)，primaryTU-Delftabstract+RWTHdatarecord | Learning-enabledNMPC/GPR與跨PCRmaterialmasscontrol已直接研究；genericclosed-loopadaptationSTOP。RawRWTHarchive本輪未取得，不稱已驗證效益。 |

Primaryfullsource hashes見provenance/injection_prior_sources.json，authorreleasepin/hash/schema/IDs見injection_inventory/assets/qualification。App-specificevaluationframing是proposal；沒有globalpriority或新方法clearance。
