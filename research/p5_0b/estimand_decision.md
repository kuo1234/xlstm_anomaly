# Estimand 決定：Track A

## 選擇

第一個 formal-study candidate 選 **Track A — Frozen-score calibration readiness**，不選 Track B。這符合 Issue #9 reviewer 的預設，也把第一個問題限於 threshold/calibration 是否可透過 target-normal evidence 適時就緒。

- Score function `s(x)`、feature transformation、model weights 與 source detector 全部 frozen。
- Target prefix 可影響的只有 predeclared threshold/calibration state `theta_t` 和 READY/NOT_READY 決策。
- 不以 target prefix 更新 weights、representation 或 ranking score function。
- Exact source/target entities、threshold algorithm、quantile/coverage target、block/look schedule、`N_max`、purge、margins 均 `TO_BE_FROZEN_BEFORE_EXECUTION`；沒有從候選資料證據支持的數值，不填任意常數。

## 實質 outcome

對符合資格的 held-out target entity `i`，比較 normal-only readiness rule 首次 READY 的觀測/時間 `tau_i` 與預先對齊的 fixed-N baselines：

1. **Acquisition cost:** primary 以 usable reference-normal observations 數量計；elapsed time 作共同 timestamp/cadence 可驗證時的 co-primary/secondary，具體選擇須在資料 manifest 前鎖定。不得以不同資料密度把 row savings 解讀成時間 savings。
2. **Future normal risk:** 在 `tau_i` 後、且嚴格晚於共同 `N_max` 的相同 sealed suffix 上，以 evaluator-confirmed normal exposure 的 pointwise FPR 作候選主指標；若要報 false alarms/time，須另鎖 alarm episodeization。多次 look 的 pointwise FPR 不等於 stream-wide anytime bound。
3. **Anomaly-side quality:** 純 threshold-only 改動保持 `s(x)` ranking 不變，因此 AP/AUROC 理論上不受 threshold 影響，不能當 post-READY noninferiority gate。候選主指標為預先標記 fault episode 的 event recall/TPR；detection delay/lead time 作次要。確切 metric 的 event semantics 和 margin 待資料/專業依據鎖定。

成功必須同時符合預先凍結的 acquisition saving、future normal-risk margin 和 event-recall noninferiority。所有 margins 均 `TO_BE_FROZEN_BEFORE_EXECUTION`，不得看結果後設定。No-alarm detector 是負控制：應有極低 normal FPR 但不能通過 event-recall gate。

## 不在此 estimand 內

- 未經批准的模型權重/representation adaptation；若將來做 Track B，AP/AUROC 才可能成為 adaptation quality outcome，但它是不同、更複雜的實驗。
- Prospective verified-normal 或 operator deployment safety claim。當前候選最多歷史 reference-normal replay。
- Anytime-valid / certified false-alarm guarantee。序列相依與 repeated-look 方法若未另證明，只能做 empirical analysis。
- 使用 M1/SMD source-native scores 充當 cross-entity target recommissioning。

## 本輪鎖定級別

**Track A conceptual estimand：已選。** **Executable data-bound estimand：未鎖定**，因 prefix normal-status adjudication 的獨立 access step 尚未核准，且目前 public metadata 無法證明預定 common `N_max` 後 evaluator masks 的逐 target exposure。這些是未解的 gate，不是待執行期間可臨時處理的步驟；本輪終態 `P5_0B_BLOCKED_BY_EVALUATOR`。
