# C0 efficiency：paper sparse graph 不等實際 sparse computation

本地 **没有** training time、inference latency、MAC/FLOP、memorymeasurements；全為NOT_RUN_GATED。不能以paper數字、BigO、少edges或CPUstaticcode審查宣告EFFICIENCY_FRONTIER_OCCUPIED或新的Pareto gap。

最具體code evidence：pinnedMS-FLOW `models/MS-FLOW.py` DynamicGraphLearner，建QK dense[B,D,D] logits、zeros_like/masked_fill/topk、softmax，propagation仍torch.matmul完整adj。Eq9/11/12與官方code一致。TopK限制informationpaths，沒有把此kernel的all-paircost變O(DK)。同樣budget不能只數nonzeroedges。

| 工作 | 必須算入的成本 / comparison limitation |
|---|---|
| MS-FLOW | Windowembedding/patchcompression、allpairscore/TopK、densemaskedpropagation、predictionhead；Ksearch與fit。 |
| DUET | FFT/frequencymetric、router/experts、D²mask與fusion；randommask/CIablation需核對保留sharedcapacity。 |
| U-Cast | Latentquerydown/upsampling首層D×floor(D/r)、regularizertraininglogdet；降低常數不等linearD。 |
| CPiRi | Pretrainedencoder/decoderweights與cache、D²spatialattention；externalpretrainingexposure/cost單列，不當零成本fromscratchcomparison。 |
| CLOC | Backbone、group/prototypemessages、selection/validationsearch、profilingwarmup/device同步；zeroresidualstrength不保證branch不執行。 |
| Ridge/sourceprobes | Pair/lag/horizoncandidateconstruction、selectionfit、scaler、CV、storage与matrixtemps；cost不止最终OLS解。 |
| LIFT | Precomputedleader/lagcache的CPU/IO/time及online更新；可以amortize，但須公布reusefactor與break-even。 |

若未來獨立scope授權efficiencypilot：固定hardware/software、batch1與fixedbatch報告、warmup/同步、p50/p95latency、peakallocated/reserved/hostmemory、端到端data→selection→forecast、preprocesscold/warm與amortization；MAC=一次multiply-accumulate，FLOP是否=2MAC說清楚，TopK/FFT/logdet不能只靠matrixMACcounter。Counttrainable/totalparams；search/epochs/seeds與foundationpretrain分開。不同L/H/D或輸出targetlists不能畫同一Paretofrontier。

Cost audit 的發現是「必須量測」，不是本地已有有效率gap。Currentmethodproposal無新scientifictarget，即使此implementationslow也不自動解鎖。
