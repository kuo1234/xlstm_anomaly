# Normal-only readiness feature contract

本文件界定 Track A 中可考慮的輸入契約，不授權計算 trajectories 或宣稱 READY 效果。Feature contract 假設 target prefix 已由一個另行核准、獨立記錄的 provenance step 證明為 reference-normal；本輪沒有核准該 label adjudication，所以目前不可計算 trajectories。Prefix labels 若未來獲准，只用來資格核對，絕不能送入 READY rule/features；若 prefix 不合格記為 `NOT_EVALUABLE`，不得換 target。

## Allowed at look `t`

- `s(x_1), …, s(x_t)`：凍結 detector 在目前已顯示 prefix 上的 scores。
- **Threshold trajectory:** 當前 prefix 的 predeclared calibration threshold `theta_t` 及與之前 look 的變化；exact estimator、prefix/block windows、min support 待 execution 前凍結。
- **Score distribution trajectory:** 已觀測 prefix scores 的 mean/std/tail summaries、固定分位數、predeclared block-to-block distance（如 Wasserstein/KS-style）。任何 normalization/reference 僅能來自 source fit/calibration 或目前可見 prefix。
- **Exceedance:** 目前已觀測、按 frozen threshold 計算的 prefix exceedance counts/rates；只作 empirical normal-side diagnostic，不是獨立 FPR guarantee。
- **Prefix-internal hold-forward calibration error:** 可將已觀測的較早 prefix block threshold 套到其後、目前已完整到達的 block，計算 exceedance/calibration error；這只可使用此時以前可見的 reference-normal prefix，不能借用 target suffix labels。若 normal status 僅能事後判定，須明確標作回溯模擬而非線上可知。
- **Marginal-gain plateau:** 只可根據兩個已到達 look 的 prefix-side量，例如 `|theta_t-theta_(t-k)|`、distribution-distance 的 prefix-only 改善、preprocessing validity 或當前 prefix exceedance stability。其 rule、`k`、容忍值須事先固定；本輪不填任意值。
- **Pipeline validity:** schema/dimension、numeric finite, missingness, zero/near-zero variance, scaler range、timestamps/order/cadence, duplicate entity/overlap checks。若 invalid，輸出 `NOT_EVALUABLE`，不能說成資料量不足。
- **Operational metadata:** 只限在 look 前實際可見且 manifest 列出的 static schema/config metadata；不得使用 hindsight report fields。

## Forbidden at look `t`

- 任意 suffix observations/scores/normal/anomaly labels、evaluator normal mask、fault/event IDs、event start/end/lead-time metadata。
- READY 後的 future FPR, event recall, delay, AP/AUROC 或其變化；不得以這些結果定義 plateau 或挑 `tau_i`。
- 用 suffix `normal_events.csv`/fault labels 來選 target、挑 prefix、決定 cut 或修整 missingness。Prefix-only normal annotation 只能在另行批准的 provenance adjudication 中、且 target/time role 已鎖定後核對資格；仍不得作 READY input。Suffix evaluator labels 只能在 trajectory/output seal 後開啟。
- Meta-RL、learned/neural stopper、post-hoc fusion、改模型 weights/score ranking。

## Required outputs at each target

只可輸出 `READY`, `NOT_READY`, `NOT_EVALUABLE` 與 timestamp/observed-sample index `tau_i`；never-READY target 保留在 denominator。READY rule 不能排除結果不利的 target。之後評估時不得以 suffix label 改 rule。

## Prefix provenance 與 marginal-gain 修正

「收更多資料已不再改善」若以 AP/AUROC/FPR/event recall 等 evaluator result 定義，即為 outcome leakage。Track A 的 margin 只能表示 prefix-observable calibration/score stability 已趨平；是否因此真的節省 acquisition 且保留 deployment outcome，是另一個 evaluator-only 問題。穩定本身不是 FPR certificate，亦不能消除序列相依/repeated-look風險。
