# C0 data qualification：沒有看本地forecast結果才選資料

選取規則先寫 [SAMPLING_RULE.md](provenance/SAMPLING_RULE.md)，才取得raw/prefix。Standard兩個候選ETTh1/Weather；MixBench兩個候選AQShunyi/HouseholdPower按可解釋systemidentity與modestD選，而非按論文gain排序；Time-HD選Meter（Londonsmartmeterenergy）。所有forecast/correlation/sourceprobe均NOTRUN。Publishedpaperresults已可見，不宣稱literature-blind。

## 候選資格與來源家族

| Candidate / family | D,T,cadence / channel identity / lineage | Split, quality, feasibility與publishedCI/CD evidence |
|---|---|---|
| ETTh1 / ETT transformer family | OfficialETDataset `1d16c8f4f943005d613b5bc962e9eeb06058cf07`、ETT-small/ETTh1.csv；完整17420rows、D7，loadfeaturesHUFL/HULL/MUFL/MULL/LUFL/LULL與OT，hourlytimestamps。SHA256 f18de3ad269cef59bb07b5438d79bb3042d3be49bdeecf01c1cd6d29695ee066。 | Rawemptyfields0，cadence3600s完整核對；沒有fit/correlations。AuthorrepoMITmetadata不代替所有底層資料rights查核。常用12/4/4月=14400 benchmarkregion不是rawfull17420；不能把DUET表長度當rawidentity。MixBenchTSMixer-familynegative、Rethinkinghorizonutilitypositive等不同protocol不矛盾。ETA/multiplegranularity不新增familyN。 |
| Weather / Jena monitoring family | StandardpaperD21/10min，同weatherstationphysicalindicators；本次Time-HD官方HFreleasemirrorprefixD21、256rows，非原Jenaacquisition復原。FullT **unknown from inspectedbytes**；paperbenchmark常長度不能代作本地fullcount。 | HF `b2042c9eb22afc153c079ab13d3b8ced648f46c9` pinnedweather.csv。Prefixhash與rawbytesledger，UTF-8replacement出現在unitheader，encoding未資格化。完整missingness/resampling/upstreamrelease/arrival未知；train70/10/20是候選protocol，不稱已seal。MixBenchstandard negative只對該matchedTSMixer；Rethinking各horizonmixed。 |
| AQShunyi / Beijingairquality family | MixBenchTable4D11,T35064,hourly、oneTFBstation；與AirQuality132channelmulti-station可能sourceoverlap，不作2families。 | Papertrain70/10/20、forecasttargetinsideboundary、trainstatistics；officialanonymousrelease只取得SPAfrontend，exactdatafiles/commit/hash/encoding及interpolation未解析。DataqualificationUNKNOWN，不能拿另一TFB/UCIpreprocessed檔悄悄替代；paperCDgainpositive為benchmarkselection，不是本地utility。 |
| HouseholdPower / UCIhousehold family | MixBenchTable4D7,T138352,15min；同householdpower/sensorpanel，不是七個獨立systems。 | PaperpositiveCDgain但CI DLinear仍強；cross-model不穩定，不當universalbenefit。OfficialMixBenchexactasset未解析，rawsource→15minaggregation、missing策略與timeavailablemetadataunknown。Nativecadence不得從released15min猜。 |
| Meter / Londonsmartmeter family | Time-HDpaperD2898,T28512,30min；HFpublicnongatedApache2metadata，pinnedsmart_meters_in_london.csv。PrefixheaderD2898，僅59完整rows；末尾partialrow排除。Distinctcustomerspanel，非singlephysicalplant。 | 底層Londonmeterstartdates/installation與同步/彙整policiesunknown；arrivalvsobservationtimes不明。官方genericloadertrain70/10/20及train-onlyStandardScaler已readcode，未execute；paperCI/CDarchitecturecomparisons非matchedcapacity。D²estimation有效N無法由T或windowcount推斷；Prefix不sealfullhash/T/nullcoverage。 |

Weather長度保留unknown，只信prefix實際rows。Data-levelclaim與paperdescription分層。

## 已取得什麼

[additional_evidence.json](provenance/additional_evidence.json)保存ETTh1fullhash、schema/cadence，CPiRifullPDF及官方codebytes；[hf_prefix_inspection.json](provenance/hf_prefix_inspection.json)保存兩個至多1MiBprefix的hash、actualheader/rowcount。Prefixhash**不是整檔hash**，read最多256rows；未調整sample以尋找漂亮missingness。Originalbytes全ignored。

[code_inventory.json](provenance/code_inventory.json)：八個官方GitHubrepo pins、READMEhash及tree完整性；[sources.json](provenance/sources.json)：論文versions/retrieval。MixBenchHTTP200是frontend，非資料可取得確認；Time-HDHFrevision是releasepin，非驗證其originalsensorlineage。沒有外部受限來源繞過。

## 八項資格仍需甚麼

1. D/T/nativecadence：ETTh1raw有完整核對；其他release/paper分開，nativearrivalcadenceunknown。
2. Splits/source-family：沒有pilot；相同station/plant的多granularity與衍生datasets合併family，testtargets不得跨split；priorhistory可合法來自precedingsplit。
3. Channelidentity/system：ETT同transformer、Weather同station、AQ單station、household同house、Meter多customerspanel；相關panel不必具physicalinteraction。
4. Targetavailable/leadlag：只有releasedtimestamps不足证明同步值在當時可用；noactualutilityprobe，release/arrivallack則as-of不可識別。
5. Missing/resampling/scaledrift/futurecovariates：noimputation/fullseriesnormalization；prefixnullcount不推全資料；unknown欄不補值，futurecalendar與futuremeasuredcovariate分清。
6. Legal/reproducible：officiallinks與revision/prefix/fullhash有ledger；HFdeclaredlicense不等upstreamrights全審完；MixBenchasset未解析，不做manualdeanonymization或任意替代。
7. EffectiveN：看nonoverlappingtimeblocks、autocorrelation/sourcefamilies，不看stride1windows。MeterD2898與prefix59row不能估dependency；完整T也不等independentN。
8. Publishedgain：已查MixBenchmatchedTSMixer與Rethinkingcontrolled/intervention、Time-HDarchitecturecomparisons。各是paperclaims，不能以leaderboard把本地H1/H3當通過。

**Data/protocol gate未通過；primary literature gate已STOP，因此不擴張下載，不進pilot，不生成synthetic去補realN。** 這是PhaseA的有界可行性audit，沒有cross-family實驗完成之宣稱。
