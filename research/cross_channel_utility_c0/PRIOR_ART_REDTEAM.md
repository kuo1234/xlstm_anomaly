# Phase A red-team：為什麼整條 C0 應 STOP

本次最强stop論證是**題目重複**，不是「cross-channel信息完全無用」。六個全文與publisher/code evidence見 [NOVELTY_MATRIX.md](NOVELTY_MATRIX.md)。我們沒有本地predictive outcomes。

1. 動態Top-K/budget communication：MS-FLOW already；soft clustering/structure：DUET/DyTimeNet；lag：LIFT；patch-adaptation：TimeFilter。加xLSTM、gate或regime字樣不能跳過collision。
2. Related/useful/used、horizon-dependentutility、controlled→strongmodel transfer、same-checkpoint functional reliance：Rethinking already。照做Ridge+intervention會是replication，不是未解scientific question。
3. CI穩定route+bounded cross-channel補充：Rethinking的posthoc support與CLOC的zero-communication endpoint already。疊到另一backbone不足novelty。
4. 高維accuracy/costtradeoff：U-Cast/Time-HD與CLOC already。MS-FLOW sparseedges仍densekernel是可量測implementation concern，尚未證明unique frontier；不能從O(D²)批評直接跳到new methodGO。
5. Data-firstutility benchmark：MixBench already。它按positive gain選資料；在已知正release找更多正結果有selection bias，不能作新source-family discovery。
6. Papertruth仍可被反駁：partial-layerablation有earlier-layerpaths、donorjointOOD、finitecapacity與budget混淆都可能留下實證限制。但「既有研究有limitations」不等C0有獨立paper-worthy gap，且其作者已做相當robustness checks。
7. Leakage不能亂指控：forecast target只在split內、train-onlysource/scaler、input-onlyInstanceNorm都是合理設計。Temporalquery/horizon-conditionedtraining本身不是偷看testfuture。未核對code不可宣告有leakage以救novelty。
8. 以相同benchmark追加兩seeds/Ridge或測另一architecture只會加強replication，不能清除problem-levelcollision。效率需samehardware/alloverhead；weakmodelgain≥3%仍不滿足strongexisting residual。

**結論：PRIOR_ART_COLLISION；genericC0 paper主線STOP。** PhaseB沒有通過prior-art gate，NOT_RUN_GATED；不進行scorer/modelsmoke test來偷開outcomes。

## 可考慮不同研究方向（非下一步自動授權）

- **As-of cross-source forecasting**：有publicationdelay、revisionvintages、missingrelease或clockuncertainty時，原來「有用」sources是否真的在decisiontime可用？新問題不是dynamicrouter。先搜real-time/vintageforecasting、mixed-frequency/nowcasting與laggedcovariates；多數已有成熟經濟計量工作，仍可能STOP。需要release/arrivalmetadata，不可從同步CSV猜。
- **Cross-site operational utility under intervention/cost**：採樣頻率或sensoracquisition有可記錄真實cost時，sourceutility是否在更換站點/部署後仍成立？需可辨識acquisitionmechanism與siteheldout，另查activefeatureacquisition/transferpriorart。與N2合併不是授權。
- **Measurement validity / reproducibility audit**：jointOOD intervention與denseimplementation可能改寫已發表claim。但先鎖定具體paperclaim、可取得code與faircounterfactual；若只是profilingbug，不包成新forecastingarchitecture。

以上只推薦新的auditproblem。没有完成它們的文獻/data gates，未給ACTIONABLE_UNRESOLVED_GAP，也未給newnetworkGO。
