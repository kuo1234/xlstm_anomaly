# M0 adversarial review — safe normality adaptation

日期：2026-09-12。狀態：**STOP 原版 protocol；先修正再啟動 M0。這不是 hypothesis 的實驗性 STOP。**

本輪只做文獻、官方程式與資料 metadata review，未安裝模型、訓練、產生模型結果、挑選最佳資料或實作 adaptation。工作目錄原先為空。以下區分已核對事實、review 推論與待驗證事項；不宣稱已完成 reproduction。未建立 `m0_decision.md`，因 H1–H5 尚無本專案實驗證據。

## 1. 判定與七個問題的直接回答

| 問題 | 判定 |
|---|---|
| M0 是否科學合理？ | 問題值得研究，分離 H1–H5 與接受負結果合理；原版不足以產生可信的 H2/H3/H4 結論，需先修正可識別性、標籤、時間與延遲語義。 |
| Confound / leakage / unfair comparison？ | 有重大風險：事件長度捷徑、overlapping windows 洩漏、跨資料來源重複、事後 threshold、training-prefix 污染、不同 scoring 時間、delay 降低更新量，以及混淆 state evolution 與 parameter adaptation。詳見下文。 |
| xLSTM gates/state 能可靠 instrument？ | 原理及官方 reference code 支持；尚未 runtime 驗證。sLSTM 有 gates 與四項 state；mLSTM 有 recurrent state 實作。不能只靠高層 forward hook 取得所有內部量，也不能將 parallel attention-like matrix 當成 recurrent memory。 |
| xLSTMAD 官方實作足以起步？ | 足以做 reproduction 起點；不足以開箱完成 causal streaming / instrumentation。必須區分原投稿版與改良主線。 |
| CANDI 能 reproduce / 接 delayed commit？ | 有官方 code、指定 SMD scripts 與資料，工程可行性高；必須保留 FPM/SANA、既有 batching，並審核 code/paper 差異。delay 是新增 wrapper，不能稱官方既有機制。 |
| TSB-drift 適合？ | 適合外部 non-stationary 壓力測試；不能直接提供每個 timestamp 的 legitimate-drift 真值。多標籤分類及可能污染的初始 batch 使原選樣規則不完整。 |
| 已有 gate-informed safe adaptation 直接重複？ | 本次有界搜尋未確認完全相同工作；不是新穎性證明。safe adaptation / normality shift 本身已有直接 prior art，ReCATS 全文仍待核對。 |

## 2. Prior art 核對及證據範圍

### xLSTM 原論文

Beck et al., *xLSTM: Extended Long Short-Term Memory*, NeurIPS 2024。核對原論文架構與官方 reference kernels：exponential input gating、normalization/stabilization、sLSTM scalar memory mixing 與 mLSTM matrix memory。原論文沒有證明 recurrent gates 能辨識 legitimate normality shift，也沒有提供本題所需的 adaptation 安全保證。[論文](https://arxiv.org/html/2405.04517v1)、[官方 code](https://github.com/NX-AI/xlstm)。

本 review 推論：gates 是模型對歷史資料的函數，可以提供有用的壓縮歷史特徵，但不會憑空創造判定「合法」所需的語義資訊。不能從語言模型能力推導本研究 H2/H3。

### xLSTMAD

Faber et al., ICDM 2025，DOI `10.1109/ICDM65498.2025.00032`。論文包含 reconstruction / forecasting 變體；官方目前主線明說是改良版，僅保留 reconstruction + MSE，並指向 `v1-submission-version`。因此目前主線跑出的結果不能直接冠名為原論文全套 reproduction。[論文](https://arxiv.org/pdf/2506.22837)、[官方版本說明](https://github.com/Nyderx/xlstmad)。

核對到原投稿版 commit：`3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6`。此版本日期早於最終論文，仍需核對最終表格是否对应同版本，不能僅憑 tag 名認定一致。

主線 `xlstmad.py` 使用 encoder/decoder block stacks；forward 沒有傳入跨 window state，test score 是整個 window、所有 channel 的平均 MSE。這是 window-local detector，不能直接聲稱保留跨 window 的持續 recurrent memory。[程式](https://github.com/Nyderx/xlstmad/blob/main/xlstmad.py)。

### M2N2

Kim et al., AAAI 2024，*When Model Meets New Normals*。核對方法為 EMA detrending 與依模型 pseudo-normal prediction 選擇更新；normalizer 和梯度更新是不同污染通道。原論文測試採 non-overlapping windows，並報告 F1-PA 等指標；本專案主要結論不能依賴 PA 或 test-best threshold。[論文](https://arxiv.org/html/2312.11976v2)。

官方 repo 存在，但 README 說精確環境已遺失，提供 Python 3.8.18、GPU 與 requirements 線索。CANDI repo 也含 M2N2 adapter；那是 CANDI 設定下的比較版本，必須與原作者 reproduction 分開標示。[官方 repo](https://github.com/carrtesy/M2N2)。成本判定：可先做 CANDI comparison track，再用固定 machine-2-1 做原 M2N2 相容性核對；不為重現全表增加未授權資料集。

### CANDI — 首要 baseline

Kim et al., AAAI 2026，DOI `10.1609/aaai.v40i17.38524`。FPM 用正常 validation reference、score 與 latent distance 篩選，SANA 執行受限 adaptation。Appendix 指出 hard/moderate 分別累積至少 16 個樣本才更新。[論文，Table 3 與 Additional Implementation Details](https://arxiv.org/html/2604.01845v1)。

Table 3 的 Hard+Moderate 設定：machine-1-8 hard anomaly 為 497/4,332（約 11.47%），machine-2-1 為 76/310（約 24.52%）。hard-only 設定則是 527/5,437 與 78/353；不可混用分母。這已支持「admission contamination 存在」，但原表整體效能仍改善，不能據此宣稱 CANDI adaptation 已造成失敗。

已讀官方 `predictor.py`、`tta/candi/adapter_candi.py`、MLP model、loader、指定 script；查核 snapshot commit `28c9679e503832f59e351208cde63657fcb51cad`。[官方 repo](https://github.com/kimanki/CANDI)。具體 code-level 發現：

- Predictor 先記 score/prediction 再呼叫 adapt；這個順序應保留。批次內 score 的可用時間仍要明確記錄。
- Hard/moderate 各自排隊，達 `MIN_SAMPLES` 後更新並清空；同次呼叫可能連續做兩種更新。官方 admission counters 在入候選 queue 時增加，不代表樣本已實際用於梯度更新。
- Moderate 的 Q1–Q3 mask 被下一行 `scores < threshold` 覆蓋；不能照註解另寫一版卻稱官方 reproduction。
- `test_labels` 傳進 adapter，在讀到的 selection path 只用於統計，未見用於 mask/loss。這不是已證實 decision leakage；新 harness 應把 labels 完全移到 evaluator，並做 label-permutation invariance check。
- `offset = self.iter * len(scores)` 對最後變長 batch 可能錯配統計；`USE_FPM=False` 的 early return 也繞過 `iter += 1`。因此污染計數需用穩定 window IDs 另行核對，不把官方計数當 ground truth。
- MLP `get_representations` 會先經 `sana_in`；即使 backbone 凍結，candidate representation 仍可能隨 adapter 改變。新分析不能假設 reference/query representation 全程不變。

以上是靜態 code inspection，尚未用執行結果判定影響量。重現時保留原碼；計數修正、causal wrapper 與任何演算法改動各有明確 diff。

### StrAD / TSB-drift

Parrino et al., KDD 2026，DOI `10.1145/3770855.3817495`。HAL 遭阻擋後，取得作者網站 12 頁全文。研究限 multivariate，採 initial batch + sequential evaluation，初始 batch 允許含 anomaly；static/online 常勝 streaming，不能推論所有 adaptation 都無效。[作者全文](https://pierre.senellart.com/publications/parrino2026streaming.pdf)。

官方 TSB-drift 有 75 條，依每 channel 的 batch distribution divergence 再 max-pool 選取；C/CP/P/RW 是形態分類。查核 repo snapshot `7078876bbd9398481a65c22b7689702ce9e0d558`。`results/benchmark_eval_results/CD.csv` 有 `file,jsd,jsd_mean,CD,type,CD_rate`，其中 type 可多標籤，不是互斥四類。[官方 metadata](https://github.com/magaliparrino/StrAD/blob/7078876bbd9398481a65c22b7689702ce9e0d558/results/benchmark_eval_results/CD.csv)。本輪只讀這份 drift metadata，未使用模型效能表選樣。

repo 中 TSB-drift/Datasets 只見一條真實示例及 synthetic 示例；完整 12 條需從對應 TSB-AD-M 來源取得並驗 checksum/schema。不能把示例 synthetic 當成 12 條真實資料，也不能宣稱完整資料已就緒。

### ReCATS

Li et al., *ReCATS: Replay-Free Continual Anomaly Detection for Non-Stationary Multivariate Time Series*, KDD 2026。作者網站可核對題名、作者與 venue；ACM DOI `10.1145/3770855.3817985` 的全文/PDF 存取失敗，作者列表的 PDF 文字沒有可用連結。[作者出版列表](https://tianyili.site/)、[ACM 原文入口](https://doi.org/10.1145/3770855.3817985)。

**未完成全文方法核對。**「預切 task，每 task 有 normal-only training」在此明確記作使用者提供的 protocol 資訊。依此資訊，ReCATS 屬有 task 邊界及乾淨增量訓練的 continual learning，不能直接當 boundary-free unlabeled TTA baseline。需要取得正文確認 task construction、可見資訊與 replay-free 定義；本輪不冒充已讀過。

## 3. 必須先修正的推論障礙

### 3.1 無標籤串流不存在一般性的 drift/anomaly 可識別保證

考慮兩個世界在時間 t 以前有完全相同的 x[1:t]：一個是合法新 regime，另一個是持續 fault。固定模型與相同初始 state 所產生 gates、hidden、memory 都相同；任何只讀這些資料的判別器也無法區分。等待只有在後續分布提供差異時才可能有幫助。persistent 不等於 normal；transient 也不必然 anomaly。

**最小修正**：H2 限定為「在預註冊且可辨識的資料生成條件下，internal dynamics 是否有可泛化的額外預測資訊」，不宣稱辨識合法性。保留完全相同觀測、不同語義的不可辨識對照，預期不可優於 chance；再加入 long collective anomaly / short legitimate regime，使 duration 不成為答案。這是事前 falsification control，不是在負結果後換 hypothesis。

### 3.2 Real datasets 沒有足夠的 drift-vs-anomaly timestamp 真值

SMD 的 anomaly labels 不能推出每段正常資料何時發生 legitimate drift；TSB-drift 的 series-level、多標籤形態也不能直接當每窗 drift class。drift 與 anomaly 可同時存在。若把所有 post-shift window 標 drift，會把其中 anomaly 標错；若只在 stationary 段放 anomaly，probe 可用 regime identity 作弊。

**最小修正**：generator 分別儲存 `regime`, `drift_active`, `anomaly_active`, `event_id`, `anomaly_type`。probe 主分析比較 dry/clean drift-event windows 與 anomaly-event windows；stationary clean 為 specificity control，overlap/mixed windows 另報，不偷偷刪除。正常穩定新 regime 與 drift transition 分開定義。real data 沒有獨立 drift event annotation 時，H2/H3 的 cross-dataset validation 記 N/A/未證實，不能用模型 score 或 JSD pseudo-label 宣稱真值。

### 3.3 原 M0-3 沒有定義 delay 如何拒絕污染

對固定候選序列，若 K 步後每個候選都仍提交，最終提交集合不變。有限測試尾端少提交一些是 censoring，不是淨化。endogenous FPM 因更新時機而改變後續候選，所以純 delay 仍可能改善線上效能；但那不能自動歸因於「累積歷史證據」。

**最小修正**：主比較明確為 official CANDI「無額外 delay，K=0」對額外 FIFO delay K∈{4,8,16,32}；保留官方最少樣本數及 hard/moderate 順序。K 定義成 stream decision windows，另換算 raw samples/時間，不能定義為選中候選數。純 delay 測 schedule 效應，完整報 pending queue 與成熟 cohort。

若要測 rejection，須另預註冊一個固定、只看目前及歷史的新證據條件，命名為 delay+revalidation，而不是默默附加到 delay。對凍結模型重算同一旧候選，可能完全沒有新資訊；重新評分也不能保證清除 anomaly。本輪不設計新的 gate classifier、rollback 或 dual memory。純 delay frontier 無改善時，依使用者 stop rule 停止此支線。

## 4. 最小 protocol 修正規格

### 4.1 固定資料與選樣

- 保持 SMD machine-1-8 / machine-2-1，不加挑其他機器。兩條本來就是已知困難案例，只支持 failure case study，不能估計所有 SMD 的失敗盛行率。
- TSB-drift 保持總數 12、每類 3、只 multivariate。先固定 selection rule，再下載/核對候選資料；禁止看 detector 結果後換檔。
- 建議 rule：在固定 CD.csv commit 中取 CD=1，type 以 whitespace token 化，保留全部官方標籤。依固定類別順序 Continuous、Change Point、Periodic、Random Walk，從每類按完整 filename 字典序排列；找可滿足每类 3 條、全球 12 條 distinct series 的字典序最小可行指派。使用 deterministic feasible assignment，避免 greedy 提前耗盡稀有類別。指派桶不表示此序列只有該 drift。
- 事前 eligibility：D≥2，合法原始 train cutoff，有足够 initial training + chronological calibration prefix；normal-only 主研究要求該 initial prefix 經 evaluator 審計為正常。不得為拿到乾淨資料而用 test labels 挖出分散 normal windows 訓練。完整保留排除原因及候補順序。
- 若上述條件不能滿足每類 3 條，STOP 資料支線並提出修改，不能補 synthetic、偷偷改分類或合成跨序列 channels。原 StrAD 允許污染初始 batch 的 track 可另報，但不能稱同一 normal-only CANDI 設定。
- 避免 SMD 原版與 TSB-AD-M 裁切片段重複進入不同 probe folds；以原始 machine/source trace 分組，不能只用 filename 判斷獨立。

本輪未產生最終 12-ID manifest，因資料 eligibility 尚未核對且原 protocol 已 STOP；以上規則在任何模型結果前提出。

### 4.2 Synthetic 生成條件

保留 D=8 及五種指定 scenario、三種指定 anomaly。可用穩定 multivariate VAR process（非對角 transition matrix，spectral radius <1）加 correlated innovations；regime-specific mean、scale、transition/covariance 控制不同 shift。相關性變化須盡可能保持 marginal mean/variance，否則變成容易的 scale 分類。

每個 anomaly type 交叉出現在各 regime/shift 條件；duration、amplitude、onset 與 channel masks 不能由 class 決定。為 drift/anomaly 製作 matched-duration/amplitude 子集；加 stationary-no-anomaly 負對照及 shift+anomaly overlap。跨 split 使用不同 process matrix/innovation seed，不能讓相同 underlying trajectory 出現在 train/test probe。

generator metadata 只交 evaluator。adaptation API 僅有 x、time、先前 algorithm state；不傳 drift boundaries、regime、anomaly labels 或 event IDs。

### 4.3 兩條評估軌道與共同 baseline

1. **文獻 reproduction track**：各自保留原資料處理、window、stride、score alignment、threshold、seed、config、commit、套件與硬體；只比較同設定可對照的文獻數字。固定兩條 SMD 的 CANDI reproduction 是優先目標。12 條子集不能冒充全 benchmark 論文數字重現。
2. **共同 causal track**：相同 initial data、normalization、window、stride、warmup、可用資訊與輸出時間。至少包括 CANDI 同 backbone 的 frozen detector、official CANDI、xLSTMAD static、matched LSTM；可加便宜的固定 VAR residual detector 做 temporal/cross-channel sanity control。M2N2 要標示原版或 CANDI adapter 版。

每個窗口只在右端資料到齊後發出 score，且先 score 再 update。整窗重建 error 可以當「窗末 decision score」，不能回填成早期點的零延遲 prediction。若使用 point-level score，統一採可 causal 對齊的 endpoint rule，並承認與官方整窗 score 的差別。

Scaler、threshold/reference set 只用 initial training/calibration；不得 fit 整段 test。StrAD offline drift-curation code 使用全序列統計可以是資料描述，但不能移植成 online preprocessor。排除 training/warmup 與 padded scores 於 test metrics；凍結模型也要遵守同樣可用資訊。

### 4.4 Instrumentation 與 matched LSTM

官方 sLSTM `slstm_forward_pointwise` 明確回傳 y,c,n,m 及 stabilized input/forget/output gates；同時保存 raw logits，不能把 stabilized gate 當 raw exp gate。官方目前 forget 實作使用 log-sigmoid，不能假設每一種 xLSTM gate 都是 exponential。[sLSTM kernel](https://github.com/NX-AI/xlstm/blob/main/xlstm/blocks/slstm/src/vanilla/slstm.py)。

mLSTM `recurrent_step_stabilized_simple` 提供 C,n,m，parallel path 提供等價 hidden 計算但不直接輸出完整 state 軌跡。用同一權重、同一 window reset、同一 scaling/stabilization 的 reference recurrence 觀測；先核對 outputs 再接受 memory summaries。[mLSTM backends](https://github.com/NX-AI/xlstm/blob/main/xlstm/blocks/mlstm/backends.py)。

必要驗收：instrument on/off 輸出相等（預註冊 float32 tolerance）；parallel/reference hidden 對齊；finite checks；batch permutation 不改 per-window 結果；window reset 正確；同 prefix 接不同 future 的 prefix feature 不變。若不相符，STOP instrument 結論，不調 architecture 讓測試過關。

只存每 layer/head 的固定低維 moments/norms、hidden/memory delta 與 causal rolling persistence。對 C/state 的 rescaling 需標注；優先 normalized/readout-related summaries，避免 stabilizer 數值變化被誤當語義證據。完整 matrix flatten 後接 logistic 仍可能有極高容量，禁止以「線性」掩飾 feature 數暴增。

xLSTMAD 主 track 保持 window reset；不能偷偷改成跨窗 state carry。跨窗 rolling summaries 可以加，但這是外部歷史統計，LSTM 與簡單 control 必須享有相同 history budget。

LSTM 對齊 objective、資料、window、depth/readout、訓練步數與 tuning budget，盡量匹配參數（建議差距≤10%，實際列出）；不能只把 hidden width 設一樣。殘差、convolution、normalization 等未能匹配的差別須披露，因此 H3 最多是這兩種 backbone 在指定配置的比較，不能完全歸因於 gates。

### 4.5 Probe 與統計

probe 是**離線有監督診斷**，不是 unlabeled adaptation 的一部分。主 probe 僅 internal features，L2 logistic regression，固定 feature 維度/標準化/regularization 搜尋範圍；scaler 與模型只 fit probe-train。

H2 的「額外 signal」需比較額外 control：同容量 score-history / simple persistence probe，以及 history-control 加 internal summary 的線性增益分析。這些 controls 不取代 internal-only 主結果。另分 hidden-only、gate-only、memory-only 與預先指定組合；不事後挑最好 layer。

Split 依完整 series/source/event，禁止 random window split；時間分割須 purge 至少 window+rolling horizon，完整事件不跨 split。先固定正類（建議 anomaly）及 prevalence，per-drift-type AUPRC 報 prevalence baseline。macro per-series/event 結果優先於將長序列全部 pool。

固定多個 training seeds；95% paired hierarchical/bootstrap CI 以獨立 source/series/event 為 resampling unit，保留時間相關，不 bootstrap 單點。四類各三條的 CI 會很寬；SMD 只有兩機，不能以數千 window 製造虛假的跨資料證據。H2/H3 應分成支持、反駁、資料不足三種 evidence status；未顯著不等於證明無 signal。

### 4.6 Contamination、metrics 與 latency

必須同時記錄 candidate-selected、committed-for-update、pending、rejected 的唯一 window IDs、涵蓋 raw timestamps、更新次數與 loss exposure。定義：

- committed contamination = 含 anomaly 的已提交 windows / 全部已提交 windows。
- anomaly admission recall = 被提交的 anomaly windows / 全部 eligible anomaly windows；另報 unique raw anomaly timestamp coverage。
- candidate contamination 使用 candidate 分母，不能與 committed contamination 混用；零提交分母記 N/A 並列 counts，不能畫成完美 0% 安全。
- post-shift FPR = 預註冊 post-shift horizon 內 false positives / 真 normal points；threshold 用 initial calibration 固定。real data 缺 shift 真值時標 N/A 或明確標 proxy，不由 detector peaks 定邊界。

c∈{0,5,10,20,30}% 建議明確定義為固定大小 adaptation buffer 的 anomaly-window 比例，與 stream-level anomaly rate 分別記錄。各 anomaly type 單獨做、再用固定 mixture；window overlap 造成的實際污染另外算。c=0 只能在 clean controlled track 用 oracle 實驗建構，不能把 SMD 原污染算成 0%。oracle 控制 buffer 的試驗是因果診斷，不是可部署 selector；另保留完全 unlabeled 的自然串流試驗。

H1 除了 admission 存在，還需配對污染/乾淨更新 intervention：同 initial model、後續 stream、buffer 大小與 update budget，測 anomaly recall/AUPRC 或其他預註冊效能損失，分離「入選」與「造成有害 learning」。同時保留 no-update baseline。

AUROC、AUPRC 全部以不可回填的 causal scores 評估。CANDI code 用 trapezoidal PR-AUC；StrAD README 示例用 average precision，兩者不能當同一數字。建議兩者皆存，報表明確命名。VUS-PR 固定 implementation/version 與 buffer range，只作補充；不得用 test labels 調 range。不用 point adjustment 決定 GO。

Latency 至少分：candidate-to-commit、drift-to-first-update、drift-to-sustained-FPR-recovery、anomaly alarm latency；未更新/未恢復為 censored，不能刪除。K 之外還有 batch/window/min-samples 的固有等待。

Pareto axes 用 latency、committed contamination/error、post-shift performance；保留 K=0、全部 K 與 static（static 的 commit latency=N/A，不偽造為 0）。固定 eligible cohorts，報測試尾端 pending，另做 fixed-update-budget diagnostic 以排除「只是少訓練」。frontier 用 paired uncertainty 與預註冊 practical margins 判斷，不能只靠一個 seed 的極值或最高 F1。未改善則按原要求停止更複雜 delayed/rollback 支線。

## 5. 新穎性搜尋與不得過度推論之處

查詢包括指定六篇的 title/repo，以及 `gate-informed safe adaptation`、`LSTM gates concept drift anomaly`、`gate safe adaptation anomaly detection`，並檢查 CANDI related work。未找到可核實的「直接讀 recurrent internal gate/state，據此在 boundary-free unlabeled multivariate TSAD 延遲提交 adaptation」完全重複工作；但檢索覆蓋有限，ReCATS 全文缺口尚在。

額外相關工作 OWAD（NDSS 2023）已處理 normality shift detection/explanation/adaptation，涉及降低人工標註成本；所以不能把 normality shift / safe adaptation 本身當首創。[OWAD 原文](https://www.ndss-symposium.org/wp-content/uploads/2023-830-paper.pdf)。CANDI 的 SANA 也有 learnable gating，但那是 adapter residual 控制，不等於讀取 pretrained recurrent gate history 作為安全提交證據。

原 xLSTMAD 對 memory revision 的動機不是「安全撤銷已污染 gradient update」的證明。即使 H2/H3 成立，也只證明 signal source；即使 H4 成立，也只證明延遲策略的指定收益。都不足以直接支持 reversible adaptation 的有效性或理論安全。

## 6. 修正後的最小工作清單與停止條件

目前不執行以下模型工作；這是 review 後可採用的最小順序。

1. 補齊 ReCATS 正文查核，固定 protocol/metric/latency/selection 定義；下載 metadata 對應資料、檢查 initial prefix、來源重複與 12 條 eligibility，存 manifest/checksum。若固定 12 條規則不成立，先回報，不換資料湊數。
2. 只建立 causal stream/evaluator 與 D=8 generator，labels 在 evaluator 隔離。先驗證窗口時間、score-before-update、counter IDs 與 metrics 一致性；不寫完整論文框架。
3. 固定 SMD 兩機，重現官方 CANDI 與同 backbone static，保留 script/config/environment；同時評估 M2N2 成本。先確認 natural candidate contamination，再做 controlled type-specific causal failure test。
4. xLSTMAD 原版/主線差異盤點，選定並固定一個 architecture；通過 instrumentation parity 後才訓練 matched LSTM 與 linear probes。失敗則 STOP xLSTM-specific interpretation。
5. 保留 CANDI 原更新機制，只加額外 FIFO K；做 latency/contamination/performance frontier 及少更新量 control。無改善則 STOP，不建 rollback、dual memory 或新 cell。
6. 只有 M0 實驗完成才寫 `reports/m0_decision.md`，每個 H 分開列 effect size、CI、資料涵蓋、反例與 GO/STOP 決策理由。未驗證/資料不足要明示，不能捏造成支持或實驗負結果。

H1 目前僅有文獻支持 admission 存在，沒有本專案的 harmful-effect 證據。H2/H3/H4 尚未測；H5 不予 GO。原 protocol 的阻碍是可修正的推論與協定問題，不構成繼續開發複雜模型的理由。
