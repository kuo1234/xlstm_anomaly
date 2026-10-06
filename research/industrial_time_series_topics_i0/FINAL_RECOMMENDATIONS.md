# 工業時序選題建議與可行性結論

2026-10-06；優先製程品質與軟感測，已擴查批次製造、射出／組裝、機加工、維護與能源決策。這是選題與可行性審查的交付，**不是新方法已獲准或已證明論文 novelty**。

**首選：射出成型品質軟感測的前瞻可信度——從隨機周期驗證到未來周期的誤差、涵蓋率與精度。** 可取得獨立品質量測、有確切周期 join，已跑通有界測量 prototype，並出現值得進一步查驗的前瞻失效。建議先做應用／evaluation 研究資格驗證；不先選網路架構。

## 1. 首選題目的問題與證據

工廠使用模型預估重量、尺寸等難以持續實測的品質。實際問題不是只有平均誤差，而是：模型在先前資料上的良好成績、以及標稱區間涵蓋率，是否對**之後生產的零件**仍可信？在需要實測確認時，應如何判定預測精度已不足？

[原始射出研究](https://doi.org/10.3390/polym15040978)已研究高解析時序與 scalar 的品質預測；[工業 conformal 研究](https://proceedings.mlr.press/v204/uddin23a.html)也已做重量區間；[2026 temporal attribution](https://doi.org/10.36001/phmconf.2026.v18i1.4829)已做時序品質解釋。因此，下列都不能當新意：加 LSTM/Mamba、stage-aware head、SHAP 或直接套 conformal。剩餘可測的是**有獨立實物量測、共同可用資訊與前瞻測試的有效性邊界**，以及已有強方法是否已處理這個邊界。

已驗證的資料：作者連結的 scatimdata commit `7bd35941d75c97a3f276439377dc430ab47402be`，dataset1.zip，CC BY4.0；1,167 有品質標籤的周期全部對應壓力與流量曲線。品質來自秤重與幾何量測，不是控制器 OK/NOK。兩種曲線各2,048個點；另7個曲線缺品質標籤，保留紀錄。這是實體實驗 cell 的 controlled settings 資料，不能稱獨立工廠或自然漂移樣本。

### 封存後的四個 Ridge / split-conformal fit

Seal commit `7000cc9eb24bc4e6e7daa88200a641137bebb2e0` push、核對遠端後才執行。固定重量 target、alpha10、60/20/20% 切分、90% 名目區間；無 tuning、神經網路或結果後替換。

| 固定 protocol / inputs | Test n | RMSE（g） | R² | 90% 區間實際涵蓋率 | 區間寬度（g） |
|---|---:|---:|---:|---:|---:|
| Future cycles / scalar | 234 | 0.05769 | −0.2430 | 74.79% | 0.15700 |
| Future cycles / scalar + curves | 234 | 0.05906 | −0.3028 | 73.93% | 0.15768 |
| Random diagnostic / scalar | 234 | 0.04619 | −0.1990 | 88.46% | 0.09229 |
| Random diagnostic / scalar + curves | 234 | 0.03186 | 0.4295 | 88.89% | 0.09212 |

**可行性結論**：資料／對齊／程式與測量問題可執行；隨機診斷有初步訊號，前瞻測試揭露可信度問題。**沒有證明強模型都有同一殘餘 gap，也沒有證明新方法 superiority。** Random 與 future 的 test populations 不同，差異是描述性的，不能估計 split 的因果影響。Cycle 關聯與 shift 不符合一般 exchangeability，90% 是名目設定，沒有被宣稱為前瞻理論保證。

現有方法須先比：原研究的 RF/SVR/非線性方法、EnbPI／rolling calibration／normalized或Mondrian CP、簡單訓練均值與時間基線。沒有正確比較前，不建立新網路。資料沒有完整 day／DoE setting IDs、實測返回時間、原圖面公差與量測成本；因此不能直接聲稱 unseen-condition 泛化、品質合格判定、減少實測成本或可部署控制。

**最小下一階段**：固定 cycle-level future blocks；強點預測基線＋已有 interval 方法；報告誤差、涵蓋率、寬度與缺失量測。須向資料來源核對工況／時鐘 metadata，才進行工況層 inference。若已有方法恢復精度與可信度，記 `EXISTING_METHOD_SUFFICIENT`，停止新方法主張；若只有弱 Ridge 失敗，也不建新模型題。這個建議是下一個研究 task，不是本輪自動開大型實驗。

## 2. 備選：延遲品質回饋下的資訊契約與公平 soft-sensor 比較

題目可寫成：「當品質量測尚未返回時，不同軟感測方法到底使用了哪些合法資訊？」先區分 process sensors、另一個品質分析值、歷史 quality 與 current target。

InduTS-SS MP 檔案及 loader 可核對；3,614 rows 並非完整 hourly grid，最大間隔13.29天，row horizon不能當固定小時。五個 model branches 的 static source 已讀；部分方法排掉 current target，GCT 的 mean-before-overwrite path 則仍有 current-target 資訊依賴。尚未證明全部 runtime 或原 GCT 論文有同一問題，不能由重實作缺陷推翻原方法。

**可行性**：公開資料足以做 clock／input contract 工程審查。**原生延遲效益驗證仍 HOLD**，因沒有 sample/result-return ledger。ASSLD2025、multi-rate2026、calibrated soft-sensor2026 已直接研究 delay／validity；generic delayed-label learner 不是新意。

若有企業 LIMS／MES 資料，最少需要 sample ID、採樣時間、結果返回／修訂時間、process time、批次／設備與品質單位，才能做 matched available-information 比較。沒有這些，只可做明示假設的延遲敏感度，不稱原生工業 replication。此備選有具體 acquisition contract，但目前不推薦當已可投入的方法論文主線。

## 3. 目前不推薦的題目與原因

| 題目 | 已驗證的結果 | 決定 |
|---|---|---|
| 製藥早期軌跡「必然」增加品質預測價值 | 95個固定批次，20次封存 Ridge fit；15/60min prefix 相對材料 baseline MSE高32.40%/65.71%，整批 oracle 亦未改善 | STOP 該初始線性訊號主張；不以換 target／模型救本輪結果；不否定所有非線性資訊 |
| 所有原料 lot 完全獨立的品質泛化 | 1,005個批次在明確 typed-lot 假設下形成單一 connected component | 此資料上的 all-lot-disjoint claim 不可行；不得改成只 API 分組却沿用原主張 |
| 控制器 OK/NOK 當獨立裝配品質 | PyScrew s01：5,000操作／100工件；未核對 joint-strength / pull-out ground truth | 物理品質版本 HOLD；分類控制器結果是另一個已研究的任務 |
| 泛用工具 wear／RUL + 新 backbone | 公開資料與2025–2026強近鄰存在，但新 backbone 不定義剩餘 application gap | 不優先；需 failure／replacement／censoring及equipment-disjoint資格 |
| Energy forecasting即可宣稱節能排程 | decision-focused / chance-constrained scheduling已有直接研究；signals缺 action／cost／counterfactual | 沒有可重放決策契約便 HOLD 效益聲稱 |

## 交付的邊界與投入建議

本輪完成的是「提出候選、查目前同題研究、取得並驗證資料、用小型既有方法驗證能否測量、給出排序與阻止條件」。已完成24個 Ridge fit（製藥20＋射出4），0 neural，不做實體控制／放行。

推薦順序是：**先做射出品質預測的前瞻有效性研究資格验证；有原生 sample/result-return 資料時再做延遲資訊契約；暫停無證據的 architecture／節能／全原料泛化主張。** 方法 novelty 與跨工廠效益仍未核准。本研究選題審查的完成，不代表下一階段實驗或新方法已完成。
