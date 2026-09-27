# P5-0B protocol 提案：僅回溯可行性

**狀態：** 僅供審查，尚未授權或執行。查核日 2026-09-27。此最小後續方案遵循 [Issue #9](https://github.com/kuo1234/xlstm_anomaly/issues/9)、[artifact 清冊](existing_artifact_inventory.md)及[主張邊界](claim_boundary.md)。

## 問題與 estimand

對已具備 qualification、且凍結的 detector，是否能讓只依目前 target reference-normal prefix 的規則，產生有用的回溯性 empirical per-target READY 時點 `tau_i`；並在 normal-side outcomes 未惡化的條件下，相較 fixed-N baseline 減少 acquisition？Future suffix outcomes 僅供 evaluator 使用。本 protocol 不研究 prospective verified-normal deployment。

## Gate 0：有效性與資格

計算 trajectory 前，先建立並提交、推送 artifact/data manifest。Manifest 至少須含來源與 target IDs、每個輸入檔案及資料/score artifacts 的 SHA256、upstream dataset version/commit、程式與 config revision、model/checkpoint 與 threshold provenance、split roles/時間戳、允許使用的 feature 欄位、label access boundary、missingness/schema checks 與排除條件。manifest 封存後才可計算 trajectory；不得事後依 outcomes 改變 manifest。必須先通過 pipeline validity：schema 相符、數值有限、missing channel、zero/near-zero variance、scaler explosion、嚴重 range shift 檢查。Pipeline 無效時標記 `NOT_EVALUABLE`，不可解釋為「commissioning data 還不夠」。

盡可能使用 disjoint source/development 與 target/evaluation entities；在查看 outcomes 前凍結 target membership。既有 M1 只能用作九條 streams 的 source-native exploratory feasibility，不能當 untouched confirmatory targets。看過 evaluator outcomes 後不可改 threshold 或 stopping rule。

只有當 provenance 支持回溯辨識時，prefix 才可稱為 `reference-normal`。缺少 prospective collection record 或獨立 attestation 時，不得稱作 prospective `verified-normal`。若沒有獲准的獨立 normal evaluator interval/mask，必須在 efficacy comparison 前停止；僅報計算層面的 feasibility。

## 資訊邊界與 trajectory

每個預先固定的 block look，規則只能使用截至該時點可見的 prefix score/observable statistics、凍結 calibration state 與允許 metadata。禁止使用 future observations、hidden suffix scores、anomaly labels、evaluator statistics。所有 targets 與方法使用同一 common maximum commissioning horizon `N_max`、block/look schedule 及其後完全相同的 sealed hidden evaluation suffix；suffix 必須嚴格晚於 `N_max`。規則在自己的 `tau_i` 後不得再看到或使用任何 commissioning observations，即使其他方法繼續到 `N_max`。輸出 `READY`、`NOT_READY` 或 `NOT_EVALUABLE` 及 `tau_i`；never-READY targets 不可靜默排除。

## 比較基線

至少比較：

1. zero-shot/source-only；
2. 對齊 horizon 的 fixed-N；
3. threshold stability；
4. score-distribution stability（mean/std/tails 或事先固定的距離）；
5. marginal-gain plateau；
6. 簡單且事先固定的 FPR/exceedance rule（除非 dependence 假設成立，否則僅作 empirical）；
7. always-READY；
8. never-early / maximum-horizon；
9. oracle evaluator upper bound，只供 evaluator 使用且明確標記為不可部署；
10. always-normal/no-alarm detector 負控制，與 always-READY rule 分開報告。

候選 readiness 使用透明 conjunction；不得把各自寬鬆的訊號用 naive max fusion。Detector qualification 與 readiness 分開；evaluator-only anomaly discrimination 另行報告，不可用來定義 READY。

## Outcomes 與分析

停止規則與 threshold 凍結後，evaluator 才能在每個方法共用、且嚴格晚於 `N_max` 的同一 sealed hidden suffix 上計算 future normal-side false-alarm/exceedance 與 anomaly discrimination。此 suffix、評估期間及必要 purge gap 必須在查看 outcomes 前封存。逐 target 報告及呈現 `tau_i` 分布、never-READY 比率、相較 matched fixed-N 的 acquisition 節省、相較事前 margin 的 normal-side risk，以及相較事前 reference 的 anomaly discrimination。研究層級的成功必須同時符合三項預先凍結條件：(1) 相較 matched fixed-N 有實質資料量或 elapsed-time 節省；(2) future normal-side risk 符合預先指定界限/非劣性 margin；(3) evaluator-only anomaly-detection quality 對預先指定 reference 非劣。第三項只能作 evaluator 判定，不得輸入 READY rule。always-normal/no-alarm 負控制應有最低 normal false-alarm，但預期無法通過 anomaly-quality 非劣門檻，以檢查「永不警報」是否被錯判 READY。使用 target-level uncertainty，呈現所有符合資格的 targets；不得將曾使用過的同一批 SMD streams 擴張成 population claim。

## Dependence 與 sequential validity

一般 per-look binomial interval 在 repeated adaptive looks 後不自動有效。不可把 IID binomial/Clopper–Pearson 加 Bonferroni，或 circular moving-block bootstrap，稱作 anytime-valid guarantee。Block bootstrap 是有限 horizon 的 sensitivity analysis；ESS/autocorrelation diagnostics 是描述性指標，對 constant binary sequence 可能無法識別。

必須分開：（a）pointwise marginal false-alarm rate；（b）long-run average/marginal rate；（c）整個 stream 至少出現一次 false alarm 的機率。對其中一項的 bound 不會自動給出其他項。若要聲稱 time-uniform stream-level control，需在明確且 dependence-valid 的 null 與假設下使用有效的 e-process/supermartingale 或其他 sequential construction；本提案沒有提供這種方法。Adaptive conformal 的 long-run average coverage 不代表 anytime false-alarm control。Issue #9 protocol 提及的 2026 ICLR adaptive-conformal TSAD 工作，須在後續專門核對其 estimand、假設與 repeated-look guarantee；本次未完成該 paper 的獨立定理審查，不據此宣稱 operational guarantee。

若未建立有效的 dependence/repeated-look 方法，結果只能是描述性回溯 feasibility；不可使用「certified」、guaranteed FPR 或 deployment safety 用語。

## 停止條件與授權

若 pipeline validity 失敗、資料 provenance 無法支持 prefix/evaluator split、必須讀取 protected labels 才能建 normal mask、outcomes 已影響 threshold/rule，或沒有合格的 normal evaluator，則停止。此提案不授權 training、Meta-RL、GPU run、存取其他資料集或超出此回溯分析的 implementation。執行前，root/reviewer 必須核准具體 data manifest 與 protocol。
