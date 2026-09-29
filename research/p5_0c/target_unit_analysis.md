# P5 target-unit 判定

Issue 要求 target unit 同時具備多個 healthy commissioning episodes、未來 held-out healthy 與 anomaly episodes，以及足以比較 adaptive stopping 的獨立 units。sample 數量不能替代 target/context 身分數量。

| 候選 unit | 可觀察支持 | 判定 |
|---|---|---|
| voraus physical robot/cell | paper 描述一套 Yu-Cobot pick-and-place setup；同一 cell 有 2,122 operations，其中 948 個初期 normal，後續有 419 normal 與 755 anomaly。 | 這是候選實體層級；單一 setup 不排除另有可識別的 context units，需依其他 dataset-native grouping 判斷。 |
| voraus `setting` | 77 個數值 variants；PRE_A/PRE_B/BETWEEN_A/B/C 是 split/variant 代碼，其餘為 anomaly condition variants。Normal/anomaly 支持按 settings 分開。 | 不是實體 target；某一 setting 也不構成含兩種 outcome 的完整 target stream。 |
| voraus `action` | 15 個 action IDs；14 個出現在全部 2,122 個 sample，action 14 出現在 558 個 sample；每 episode 內含 14–15 個 phases。 | 是 cycle 內的行為階段，不能把同一 episode 的 phase 當獨立重複 target。 |
| voraus `setting × action` | 1,152 個 strata；75 個只有 normal、1,077 個只有 anomaly，無 mixed-label stratum。 | 由實驗 variant 與 phase 組成，非獨立實體 context；缺少 within-unit 正常與未來故障 sequence。 |
| voraus `category` | 12 種 anomaly categories，category 12 是 normal；每個 sample 一個 category。 | 是 outcome/故障類別，不是 target identity。 |
| voraus `sample` / execution | 2,122 個完整 pick-and-place operations，每個 operation 長 986–1,164 rows。 | 是 episode/acquisition ID，但本身不指出跨 execution 重複的物理或操作 context；還需獨立 grouping key。 |
| AURSAD `sample_nr` | 4,094 個 contiguous executions：1,420 normal、625 fault tightening executions、2,049 supplementary operations。 | 是 execution ID，不是 context key；需查 pin registers 等其他官方欄位來識別跨 execution context。 |
| AURSAD pin/from-to plate fields | paper schema 定義 register 25/26 為 to/from plate pin numbers、plate 各有 92 holes；既有全資料逐欄統計分別有 93 個及 103 個 distinct values（含 0），但沒有 execution-level joint support。 | **未解候選**：還未驗證每個 execution 的 pin-pair 穩定性、跨 execution chronology、重複 healthy commissioning 與 future evaluator。不能據欄位名稱/邊際 counts 直接建立 target。 |

## 選擇

**Chosen target unit：目前無已驗證合格 unit。**

`voraus-AD` 中 `setting`、`action`、`category` 及 `setting×action` 的 metadata 已不足以定義合格 context；未見另有 label-blind target/context key。`AURSAD` 的 `sample_nr` 是 execution ID，不是 context；pin/from-to fields 仍可提供下一輪候選，但目前 aggregate 只有 marginal value counts，還無 per-execution pair consistency/support/order。故結論限定為：**在目前檢查的 metadata 與 fixed-version audit 中，尚未建立足夠獨立、具可確認 chronology 的 target streams。**

不以「一個 physical robot 必然只有一個 target」作推論；同一 robot 上科學上有效的重複 task/context 只要有穩定 ID、完整 healthy prefix、future evaluators 及足夠獨立 contexts，也可重新評估。AURSAD 是 external-validation lock，不得用來開發或調參，也不得把與 primary 不同 task 的 setup 硬併成同質 replicate。
