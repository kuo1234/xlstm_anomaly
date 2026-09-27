# 候選資料集可採性稽核

**範圍：** 依 Issue #9 的候選清單及最新 handoff，只讀公開 primary-source docs、papers、repo code/config/manifests、dataset metadata 和本 repo 已提交報告。不下載 raw archives，不開 row-level/future labels，不計算資料統計。

## 分類定義

- `ADMISSIBLE_FOR_P5_FEASIBILITY`：文件足以支持 held-out physical target entity、chronological reference-normal prefix、預先凍結的共同 `N_max`、其後 temporally disjoint normal/anomaly evaluator，且有明確 label-open sequence。本分類仍不代表 execution GO；retrospective labels 可接受，但 prefix provenance 與 future evaluator 必須以合法、分離的步驟建立。
- `ADMISSIBLE_FOR_RETROSPECTIVE_ONLY`：公開 metadata 顯示有歷史序列/事件和回溯 labels，可能可做歷史 replay；但此輪未證明指定 P5 target 的 prefix label adjudication 和 common-horizon future evaluator 可以在 boundary 內分離建立。回溯資料本身不是拒絕原因；未鎖定的 prefix/evaluator provenance 才是本輪 gate。需精確限制 estimand。
- `MECHANICS_ONLY`：可檢查固定 N 的 split、feature/replay/evaluator code path 或報表，但沒有合格的 per-target sequential data/evaluator identity。
- `NOT_ADMISSIBLE`：基本來源、授權或資料定義不足，無法安全用於所提分析。

| 候選 | 實體／source-target | 時間與 normal prefix | future evaluator / horizon | 類別與角色 |
|---|---|---|---|---|
| PreDist v2 | 93 個 substations；可依 substation ID 切 entity-disjoint source/target；單一 utility、兩個廠牌 | 10-minute chronological records；`normal_events.csv` 為回溯策展 normal windows，沒有 prospective commissioning attestation | Fault reports + normal events 是可能的 evaluator label source；label-blind manifest 可固定時間結構但不能證明 common `N_max` 後 target 級 normal/fault label coverage；report-based faults 不完整 | `ADMISSIBLE_FOR_RETROSPECTIVE_ONLY`；最佳回溯候選，不是 full P5 feasibility |
| CARE to Compare v6 | 36 turbines / 3 farms；asset IDs 可支援同 farm 的 turbine-disjoint split | 10-minute、95 個 event-centered sequences；同一檔案內排序，跨 event 檔案時間對齊有限；normal labels/status 為回溯形成 | 有正常與 fault windows，但共同未來 suffix、逐 target normal exposure、跨事件 chronology 尚未證明 | `ADMISSIBLE_FOR_RETROSPECTIVE_ONLY`；限 event-level/歷史 replay |
| WindADBench | 新資料集不存在；它使用 CARE to Compare | README 提供 held-out turbine/cross-farm benchmark track；資料仍為 CARE event files | Normal-operation track 是既有固定 normal sequences，沒有 P5 sequential acquisition / sealed suffix | `MECHANICS_ONLY`；可參考 entity split 和 evaluator code |
| COLDSTART framework | voraus-AD/AURSAD 的 benchmark code；PRE_A/PRE_B 是設定值，不是不同 robot | commissioning samples 隨機抽樣；固定 grid `N`，不是 chronological prefix | 固定 normal calibration/eval 與 anomaly eval cohort；無 per-target future suffix | `MECHANICS_ONLY`；不把 fixed-N/N* 重命名為 sequential readiness |
| voraus-AD 原始資料 | 一個 Yu-Cobot pick-and-place cell；沒有多個獨立 robot IDs 可切 source/target | 論文記載先 948 normal cycles、再交錯收集正常與 fault cycles；可作單一實體的 retrospective chronology replay | 後期 419 normal / 755 anomaly cycles 可作歷史 evaluator；不是 held-out physical target、無 operator live-attestation | `ADMISSIBLE_FOR_RETROSPECTIVE_ONLY` 僅限單一實體 time replay；不符合 P5 source→held-out-target identity |
| AURSAD | 一個 UR3e + screwdriver；`sample_nr` 是 execution，不是機器 entity | 100 Hz 週期內有時間，跨 execution 的 acquisition chronology 未成立；COLDSTART 以 randomized label-stratified episode split | 固定 disjoint normal/fault cohorts，沒有 chronological suffix | `MECHANICS_ONLY` |
| SMD / repo M1 | 28 machine IDs；名義可分實體，但 cross-machine channel semantics 未文件化，無現成 source→target detector | 僅 sample index，無真實 timestamp；train-normal 是 benchmark assumption/source-native | test anomaly labels 已屬 protected evaluator；無獨立 hold-forward verified-normal mask 或 event IDs | `MECHANICS_ONLY`；限 code mechanics，不能當 P5 feasibility |

## 各候選欄位與證據

### PreDist v2 — closest retrospective candidate

- **Physical entities / disjoint split:** 93 district-heating substations（35 M1、58 M2）屬同一 utility；以 substation ID 切分 source/target 在結構上可行。未鎖具體 IDs。來源：[Zenodo v2](https://zenodo.org/records/19496480)、[dataset paper](https://arxiv.org/abs/2511.14791)。
- **Chronology / cadence / `N_max`:** 各 substation 有 timestamped chronological series，論文報告 10-minute sampling；歷史長度與 completeness 不同，M1/M2 平均 completeness 約 82%/97%，僅 49 個 substations 至少一年。相同 elapsed-time `N_max` 或同一有效樣本數不能依目前 metadata 直接斷言可用；須在不開 labels 的情況下查 row counts、missingness、timestamp gaps 後封存。
- **Normal prefix:** `normal_events.csv` / paper 定義的是事後選定的 normal intervals；選樣依 seasons、reports、maintenance/fault records 和其他無 fault report 的 substations。未找到 prospective commissioning record 或 prefix 時 operator attestation。只能稱 historical/reference-normal，不能稱 prospective verified-normal。
- **Future normal evaluator:** 另一個 `normal_events.csv` interval 若在固定 cut 之後，可能提供 evaluator-only 的回溯 false-positive mask；但須在另行核准的流程中先凍結 target ID、時間 cut、`N_max`、purge、features/rules，完成 prefix-only normal-status adjudication 並封存 READY outputs，再由獨立 evaluator 開啟固定 suffix labels。公開文件和 label-blind metadata 均未證明每個預先指定 target 在 common `N_max` 後有足量 normal intervals，因此目前不是已驗證 evaluator。
- **Anomaly evaluator:** fault/maintenance reports、fault IDs/metadata 及起訖時間可以標記已報告 fault；report-based ascertainment 不完整，未報告 fault 不可當正常。評估只可稱已標註 fault episodes 的 event recall/delay。
- **Prefix/suffix disjointness / events:** timestamps 及 substation IDs 讓 label-blind chronological cutoff 在結構上可行；`normal_events`/fault events 有 interval metadata。精確相交、重疊、purge 與 common suffix 尚未驗證。
- **Version / license / acquisition:** Zenodo record v2，2026-04-10 發布，加入 configuration types；開放下載約 267 MB，CC BY 4.0。license 與版本可追查；本輪未下載 archive。來源同上。
- **Protected-label boundary:** 本輪只讀 record/paper/docs，未讀 `normal_events.csv`、fault tables 或 raw series。若後續另行核准，prefix-only normal status 只能在已鎖定 target/time roles 後做獨立資格 adjudication，不得成為 READY input 或用來替換 target；future suffix labels 則只能由獨立 evaluator 在 READY/rule outputs 封存後讀取。不能用 suffix labels 建 eligibility、挑 target、選 cutoff、調 margin。
- **分類：** `ADMISSIBLE_FOR_RETROSPECTIVE_ONLY`，意指它是歷史回溯候選；label-blind manifest 只能固定 target/time roles，不能驗證 label coverage。目前 prefix-only status access sequence 未獲准，suffix evaluator exposure 未證明，故不符合 full `ADMISSIBLE_FOR_P5_FEASIBILITY`。

### CARE to Compare v6

- **Physical entities / split:** 36 turbines、Farms A/B/C 分別 5/9/22；`asset_id` 可用於同一 farm 內的 turbine-disjoint split。跨 farm 會同時改變 entity、farm 與 feature schema，不宜作首個 Track A。來源：[Zenodo v6](https://zenodo.org/records/15846963)、[paper](https://arxiv.org/abs/2404.10320)。
- **Chronology / cadence / horizon:** 10-minute SCADA；release v6 有 95 event datasets（45 anomaly、50 normal），每個 prediction period 長度依 event 約 4–98 days。單一 file 內有 row order/time，但 timestamps 經匿名化；跨 event datasets 的順序/絕對時間不能直接拼成連續 target acquisition stream。`N_max`、完整 exposure、purge 需 raw manifest 才能定。
- **Normal prefix status:** paper/v6 labels 結合 operator feedback、manual inspection、expert knowledge、operating status 與 service reports。Farm A 的 fault windows 依 EDP logbook 回溯；B/C status labels 有 status 只在改變時紀錄等 caveats。這是 retrospective labels，並非 deployment 時的 independent normal-prefix attestation。
- **Normal/anomaly evaluator:** 50 normal-behavior sequences和已標註 fault-event sequences可做固定的歷史 evaluator，但不是同一 target 上已證明連續、`N_max` 之後的共同 suffix。Farm A 與 B/C label source 不同；v6 有過去 label corrections，label completeness 不等同完整自然異常 ground truth。
- **IDs / disjointness / events:** event IDs、asset IDs、event start/end、row/status IDs 可作 manifest 線索；跨 event 的 overlap/chronology 要逐檔驗證，不能由摘要推論。
- **Version / license / acquisition:** Zenodo v6，2025-07-09，open，CC BY-SA 4.0，archive 約 5.5 GB。v6 record 為 45 anomaly / 50 normal；paper 摘要的 44/51 是舊計數，後續使用必須依 frozen v6 manifest。
- **Protected-label boundary:** 本輪未下載資料或讀 row labels；WindADBench 明確以 CARE label/event metadata 執行 labeled evaluation。將來 labels 只可於所有 splits/rules outputs sealed 後由 evaluator 讀取。
- **分類：** `ADMISSIBLE_FOR_RETROSPECTIVE_ONLY`；限 event-level/turbine-held-out replay，不代表 prospective chronological acquisition readiness。

### WindADBench

- **Identity / entities:** benchmark implementation，要求另行下載 CARE v6，並非獨立 release。README 有 36 turbines / 95 event sequences，列 cross-turbine held-out 和 cross-farm tracks。來源：[README at audited commit](https://github.com/ZJU-DAILY/WindADBench/blob/14946a9e4b2b2198e40aa0d5bab112139319859c/README.md)。
- **Chronology / normal / evaluators:** 10-minute event-centered sequences、normal-operation FPR track、labeled evaluator code。沒有 per-target sequential acquisition, prospective-normal collection 或 sealed post-`N_max` suffix。
- **IDs / `N_max` / completeness:** inherits CARE file/event/asset metadata and all CARE alignment/length issues; benchmark itself does not make a new chronology or common horizon.
- **Version/license/acquisition:** code pinned to commit `14946a9e4b2b2198e40aa0d5bab112139319859c`; README instructs obtaining raw data from CARE Zenodo. At the inspected GitHub tree no code license was declared; CARE data remain CC BY-SA 4.0. This audit used README/code metadata only.
- **Classification:** `MECHANICS_ONLY`; CARE is the data candidate, so WindADBench cannot count as a second independent dataset.

### COLDSTART framework and voraus-AD

- **COLDSTART version/method:** main `9454d21f1f0ee4924868ce171607e19a3648f1ec`; its existing P0.5 experiment fixes commissioning sizes and separate calibration/normal/fault evaluation cohorts. The split builder randomizes normal sample IDs; its target settings PRE_A/PRE_B do not denote distinct robot entities. These support fixed-N and split-mechanics only, not sequential acquisition stopping. Sources: [split generator](https://github.com/priestly-ops/COLDSTART/blob/9454d21f1f0ee4924868ce171607e19a3648f1ec/src/split_generator.py), [P0.5 experiment](https://github.com/priestly-ops/COLDSTART/blob/9454d21f1f0ee4924868ce171607e19a3648f1ec/experiments/run_p05_anomaly_commissioning.py).
- **voraus-AD physical unit/chronology:** one Yu-Cobot pick/place cell, 2,122 cycles in paper; 948 normal cycles are from the initial period, followed by 755 anomaly and 419 normal test cycles. This supports a retrospective single-unit chronological replay, not source→held-out-target identity. The cycle sample IDs do not define elapsed time between cycles; 100/500 Hz denote within-cycle sampling. Source: [official paper](https://arxiv.org/html/2311.04765#S3), [official dataset README](https://github.com/vorausrobotik/voraus-ad-dataset/blob/a91a86a642d23df58833b792a53de01edfd81abe/README.md).
- **Prefix/evaluators:** initial normal cycles and later normal/fault cycles are a documented retrospective chronological design. No live/operator commissioning attestation was found; anomaly labels are test/evaluator metadata and must be kept out of READY. Exact executable mapping and common `N_max` would need pre-label sample-ID manifest.
- **Versions/rights:** 100 Hz and 500 Hz variants; dataset CC BY-NC-SA 4.0. The COLDSTART README mentions a future MIT code release; no separate COLDSTART license file was relied on.
- **Classification:** COLDSTART protocol `MECHANICS_ONLY`; voraus-AD dataset `ADMISSIBLE_FOR_RETROSPECTIVE_ONLY` for same-unit time replay only. It cannot answer source-detector/held-out-target P5.

### AURSAD

- **Entities / chronology:** one UR3e screwdriver setup; `sample_nr` identifies individual process executions, not distinct machines. 100 Hz within-cycle sampling does not document order/time between executions. Source: [AURSAD paper](https://arxiv.org/html/2102.01409#S2), [Zenodo v1.1](https://zenodo.org/records/4559556).
- **Prefix/evaluators:** COLDSTART builds randomized label-stratified episode cohorts; normal commissioning/calibration/normal evaluation and fault evaluation are fixed disjoint sample sets, not chronological prefix/suffix. A 500-execution `N_max` capacity is a static reservoir fact, not a future acquisition horizon. Source: [pinned AURSAD protocol builder](https://github.com/priestly-ops/COLDSTART/blob/9454d21f1f0ee4924868ce171607e19a3648f1ec/experiments/build_aursad_protocol.py), [protocol manifest](https://github.com/priestly-ops/COLDSTART/blob/9454d21f1f0ee4924868ce171607e19a3648f1ec/reports/aursad/protocol/protocol_manifest.json).
- **Events/labels/version/license:** sample/event labels and categories exist; dataset paper documents 2,045 process samples plus supplemental motion; Zenodo v1.1 is CC BY 4.0/open, with files about 6.4 GB. No archive/labels accessed.
- **Classification:** `MECHANICS_ONLY`; no source-target unit split or verified acquisition chronology.

### SMD / repo M1

- **Physical identities:** 28 machine IDs can nominally be separated, but feature-position semantics across machines are undocumented. Existing M1 trained and scored each machine independently; it is source-native, not a source-trained detector evaluated after held-out-target recommissioning. Sources: [M1 dataset manifest at frozen SHA](https://github.com/kuo1234/xlstm_anomaly/blob/f7dd019f3ddb206221cb6bfb79e6b3a543b832d4/research/adaptive_normality_m1_smd/dataset_manifest.md#L7-L11), [M1 protocol](https://github.com/kuo1234/xlstm_anomaly/blob/f7dd019f3ddb206221cb6bfb79e6b3a543b832d4/research/adaptive_normality_m1_smd/protocol.md#L9-L24).
- **Time / normal / evaluator:** row order only; timestamps unavailable and 1-minute cadence nominal. Train-normal is a benchmark assumption; separate independent hold-forward normal masks and event IDs do not exist. Existing test labels are protected and M1 results already exposed.
- **Version/license/access:** upstream OmniAnomaly pinned in manifest; source-data terms need verification before redistribution. This audit did not inspect ignored raw files or protected label files.
- **Classification:** `MECHANICS_ONLY`, superseding P5-0A’s broad “REUSABLE_DIRECTLY” for this P5 identity. Use M1 artifacts only for deterministic score-prefix/threshold/replay implementation sanity, never P5 efficacy or source→target evidence. See [reviewer narrowing](https://github.com/kuo1234/xlstm_anomaly/issues/9#issuecomment-5853967832).

## Gate conclusion

No candidate is currently `ADMISSIBLE_FOR_P5_FEASIBILITY` for the requested evaluator contract. This does not require prospective/operator attestation for a retrospective feasibility study. The present blockers are specific: prefix-only normal-status adjudication for the already-frozen target/time roles has not been separately authorized, and public docs or label-blind metadata cannot prove adequate normal and reported-fault label exposure in each preselected target's common post-`N_max` suffix. A future approved sequence must separate this prefix provenance check from suffix-only outcome evaluation after READY/rule outputs are sealed. Do not open suffix labels to solve selection/eligibility. PreDist remains the best source for a future bounded retrospective design, but the current terminal state is `P5_0B_BLOCKED_BY_EVALUATOR` and no P5-0C protocol is issued.
