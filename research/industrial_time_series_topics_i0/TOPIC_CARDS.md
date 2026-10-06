# Provisional topic cards：題目不是已通過novelty的claim

## Q1. 未知完成時間下的批次品質預測：有效提前量與誤差

**問題**：在固定實際deadline，process prefixes能否對最終laboratoryquality提供有用增量？若以事後完成百分比對齊，當前看似「提前30分鐘」的結果是否仍能在停機／速度變化／未知結束時間下成立？

**應用**：讓工程師在生產尚未完成前知道continuousquality偏移及uncertainty，不聲稱自動放行、不需anomaly、不必xLSTM。

**近鄰**：Honti2024已用完成百分比/2000pointsforecastwaste；onlineDTW2011與harvest-time2018處理unknownlength/progress；一般earlyquality已不是白地。剩餘候選是**共同physicaltime与availableinformation下，quality-error×trueleadtime的可重現benchmark**，不是另一個warpingnetwork。

**實際可行性**：已讀Process/1.csv共106878rows、95batches，95/95可join最終Lab，timestamps与12processsignals存在；fixed15/30/60min prefixes可建立，pausedspeed与emptycells保留。完整Lab1005batches、6continuousendpoints；Rawarchive與MD5/SHA可重現。

**尚缺**：全25productcodes的clock/labels audit，fixedtimecutoffs裡哪些batch真的尚未結束，planvsactualsize、量測返回time缺失，closestonlinealignment全文與matchedstrongbaselines。公開allwithin-specification資料不能驗證out-of-spec interception。

**最小否證**：固定historycutoffs+train-onlyscaler，對比preprocessknownmaterials/recipe-only、processprefix、retrospectivefullprocess（oracle diagnostic），在futurebatches與predeclaredpause/lengthstrata檢查incrementalquality及actualtimelead。若material-only足夠，或gain只由completion/targetproxy洩漏提供，STOP。不能用test結果重選cutoff/target。

**當前判斷**：DATA_FEASIBILITY_SUPPORTED_FOR_ONE_PRODUCT_CODE / NOVELTY_UNRESOLVED / PILOT_NOT_RUN。最優先深入，還不能給newmethodGO。

## Q2. 實驗室延遲下軟感測的資訊可用性審查

**問題**：softsensor比較是否讓部分方法使用尚未返回的qualityhistory/另一個labquality，或讓rowstep冒充固定physicalhorizon？在相同availableinformation下，文獻排名與實際可用task會如何變？

**近鄰**：ASSLD2025、multi-rate softsensor2026、[calibratedsoftsensor2026preprint](https://ssrn.com/abstract=7181724)均直接研究delay/validity；indirectqualitymeasurement從早期chemometrics就成熟。**Genericdelaycalibration方法STOP**；只考慮可追溯benchmarkcontract與conditionalclaim。

**實際可行性**：InduTS-SS官方pinnedMP3614rows/24columns、有date與2qualitycolumns；loader与5個模型實作已staticread。Hourgrid不連續、labresultreturn欄缺失。Loader有targethistorypaths，TSLambdaGRU明確去掉currenttarget，HSAMvalidation/testquery前一row，不能只看loader就指控全部模型currenttargetleakage。

**獨立較強的contract問題**：GCTsoftsensor先mean整段y，再覆寫最後y，mean仍含currenty；若此loader/modeltaskpath被runtime實際選中，currenttarget的資訊仍可流進模型。這是benchmark獨立重實作的staticcode問題，不能直接歸咎originalGCTpaper，尚未做end-to-endruntime或qualityscoreexperiment。

**尚缺**：originalrawMP→curatedtransformation、timestamp代表aggregationstart/end、native sample/resultreturn、完整runner/config/data_aug/downstreammask。只有「至少一小時delay」不足以證明y[t−1]已返回。Noresultreturn時最多controlledsensitivity，不宣稱nativeas-ofreplication。

**最小否證**：先trace一個pinnedrun的inputchannel/time支持，再鎖對比sensor-only與legitimateavailablequalityhistory；原pipeline的oracleinputs只作diagnostic。若strictavailabilitychecks不改變問題或只是單一implementationbug，不包成newmethodpaper。

**當前判斷**：STATIC_CONTRACT_AUDIT_FEASIBLE / NATIVE_DELAY_UNVERIFIED / GENERIC_METHOD_COLLISION。工程與evaluation候選，publication主線未通過。

## Q3. 原料批號變更時，早期製程軌跡還剩多少品質預測價值？

**問題**：在recipe/materialcertificate已知的條件下，processprefix的額外品質訊號是否能轉移到futureAPI lots？Predictivegain究竟来自物理trajectory還是material/productidentity記憶？

**近鄰**：PharmaQAI2026、Honti2024、[rawmaterial+processPLS2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3225512/)與[commercialtabletML2021](https://www.sciencedirect.com/science/article/pii/S0378517321009522)已處理material/process品質關係。新「material+time series」model不是contribution；可測的是被宣稱generalization的適用邊界。

**可行性**：1005 Labrows有25productcodes、typedAPI lots260、excipients各18/22/17lots；資料可join95sampledtrajectories。無法用allrawgenealogydisjoint來做independentsplit：1005個batch形成單一shared-lotcomponent，**此claim目前STOP**。

**剩餘可測protocol**：明確只問futuretime／newAPIlot，而非「所有原料新lot」。缺失/匿名lotnamespace仍須對照來源；不能按觀測gain選purge規則。新APIlot是否有足夠futureinstances與matchedpre-controls尚未核對。

**否證**：預先選定continuouslabendpoint与chronological/particularlotestimand，material/recipe-only vs同capacityprefixmodel。若data不支持新APIlot時間切分或utility不穩定，STOP。不要靠放寬all-lotdisjoint救同一claim。

**當前判斷**：DATA_PARTIALLY_SUPPORTED / FULL_GENEALOGY_DISJOINT_INFEASIBLE / NOVELTY_UNRESOLVED。Q1的必要generalizationcheck，可能不足以獨立paper。

## Q4. 機台拒料預測能否轉成独立最終品質的軟感測？

**問題**：機台依compressionforce等規則產生wastecounter；高準確度controllerrejectforecast是否真的預測dissolution/impurity等独立實驗室品質？

**近鄰**：Honti2024以wasteforecast為target、PharmaQAI2026有6CQAtargets、quality-relevantmultiblockPLS已研究。候選是proxy-to-qualityutility可否轉移的實證，不是genericauxiliarylearning新意。

**可行性**：同batch有processwastecounter及independentlabendpoints，95sampledjoins成立；不需要新device/acquisition。Lab後製程欄不可在早期作inputs，controllerOK/within-spec不當物理failuretruth。

**否證**：同informationcutoff/容量下比較prefixprocess-only、waste-derivedprefixfeatures、recipe/materialcontrols，僅測independentlabtargets；若gain只在predictcounter本身、品質effect不穩定或已由材料baseline解釋，STOP。

**當前判斷**：DATA_FEASIBLE_FOR_SCOPED_COMPARISON / PREDICTIVE_UTILITY_UNTESTED / NOVELTY_UNRESOLVED。可併入Q1，尚不強推獨立methodpaper。

## 非首選／暫停題目

- Active lab sampling：2026activeJIT已直接存在；原生samplingcost/selection與resultreturn未取得，不用假想cost宣稱工廠savings。
- PyScrewearlyphysicalquality：5000metadata操作有100workpieces，OK/NOK是controller outcome；rawtraces和pullout/jointstrength未核對。可研究terminalcontrollerclassification，但不能假裝已驗證獨立assembly品質。物理品質版本HOLD。
- Toolwear+uncertainty、RUL+foundationmodel：強prior且notqualitygroundtruth等價，先不投入newnetwork。
- Forecast→energy/scheduling：必須有完整optimization/actions/constraints與counterfactualevaluation；signalsalone不能驗證savings，prioritylower。
