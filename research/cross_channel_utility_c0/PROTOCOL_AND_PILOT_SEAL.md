# C0 Phase A decision seal / Phase B status

**Pilot status：NOT_RUN_GATED。Executable pilot seal：NOT_CREATED。** 沒有synthetic、probe、neuraltraining/inference或baseline可執行性跑分。Prior-art gate返回PRIOR_ART_COLLISION，issue明確允許在PhaseA停；不要製造一份沒有qualifieddata/未解題目的假seal。

Data-onlypre-acquisitionrecord為 [SAMPLING_RULE.md](provenance/SAMPLING_RULE.md)。它在download/nullinspection之前寫入，但不是pilotseal；未宣稱有modeloutcomeexposure。本次已讀publishedresults，不能稱完全blind於literature。

## Pre-result門檻草案：只能未來reviewer scope再seal，現在不执行

以下數字是砍線用engineering門檻，不是理論/literature保证，不能在結果後下修。

- Literature gate：一句話的residualquestion必須與Rethinking/MixBench/CLOC等可辨識不同；新dataset/backbone不算。
- Data gate：2獨立real-sourcefamilies，exactfiles/hashes、samplingsync/arrivalcutoff、splits、preprocessing qualified；同ETT4files/同PeMS分區不當4N。Synthetic僅measurementvalidation。
- Materiality：matchedOOSrelativeMSEgain至少3%，至少2個predeclaredfamily×horizonconditions，兩families各至少一個；每條件3固定neural seeds如需neural，同方向且minimumseedgain≥1%；pairedmovingblockuncertainty不以overlappingwindows作N。3%下限還須大於train/validationnoise envelope（只用pretestrollingcalibration）；無足够independentfamilies只作feasibility。
- Residual gate：收益必須相對strongexistingmatchedfrontier，非只CI/Ridge。未執行closestofficialmethods時methodgap=UNKNOWN，不能ACTIONABLE_UNRESOLVED_GAP。
- Efficiency claim另需alloverheadfixeddevice error×real latency/memory，建議≥10%endtoend改善且MSE非劣margin≤1%；結果前確定測量noise floor/interval。不以Kedgecounts替代。
- Controls：matchedtarget/history/info cutoff、training-onlyselection/scaler/lag；sameKrandomsubset、history-onlylag/time-misalignment、correlated-noincrementalutility；capacity/searchbudgetunequal時downgrade。每controlexpectedbehavior事前寫明。

若真有新residual：至多3families×2horizons×4primaryvariants，不以控制變體偷偷擴大primarymodelbudget；控制每個run也記入總fitcount/runtimecap。可執行性失敗不在結果後換有利baseline。需要currentruntime、officialweights、datahashes才可定CI/CD/strongmodelnames。此草案**不固定不存在的runtime、channel lists、splits或hyperparams**，也不授權執行。

未來PhaseB順序必須：取得reviewerscope→完成prior-art/data qualification→填全具體executablemanifest/metric/seeds/cost/control/stop→commit+pushseal→才跑低成本固定existingmethods→另commitresults→停等reviewer。新architecture仍NOTAUTHORIZED。
