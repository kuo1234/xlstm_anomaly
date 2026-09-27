# 既有 artifacts 清冊

**查核日期：** 2026-09-27。僅審閱 metadata/source；未讀取受保護標籤、未重算指標。分類定義見[可重用證據](reusable_evidence.md)。

| Artifact 家族 | 凍結位置 / revision | 可用證據 | P5-0B 用途與限制 |
|---|---|---|---|
| M1 Stage1A | `reports/adaptive_normality_m1_smd/stage1a_screen/`；score seal `bcdd348`；results `2792b1e`；M1 frozen base `f7dd019f3ddb206221cb6bfb79e6b3a543b832d4` | 九個 machine streams 的 time-aligned public score arrays、score manifest、train calibration references/thresholds、checkpoints | 僅可在相同九條 streams 建立 score-only retrospective prefix features/READY trajectories；這些 artifacts 沒有可用的獨立 hold-forward normal evaluation mask。 |
| M1 Stage1B-R | `reports/adaptive_normality_m1_smd/stage1b_r/`；score seal `f791ec7`；final diagnostic `f7dd019` | 相同九個 machine scope 的 frozen score artifacts 與診斷輸出 | 可作同樣受限的 trajectory feasibility。診斷輸出不能作 efficacy 證據；M1 FPR gate failure 排除將其當 readiness 成功證據。 |
| M1 closeout | Issue #11 final status `FINAL_STAGE1_GATE_ALREADY_IMPOSSIBLE` | 九個已評估 machines 已令 frozen FPR gate 在數學上不可達；本輪未評估其餘 19 台 | 凍結結論，不救援、不更改。只支持狹義 source-native claim；不支持 cross-entity transfer failure 或普遍 xLSTM/forecasting 無效。 |
| P1r observable-control | `origin/experiment/input-derived-observable-control`，`1f4296f62fe3f0a514171a94afe3ce8bc1686986`；`research/temporally_matched_observable_control/` | Synthetic/O1r 情境中的 temporally matched、nonlinear 強 observable controls；沒有真實 commissioning trajectories | 只作研究動機與基線設計。相對 temporally matched observables 沒有 resolved incremental utility。 |
| R0 execution | `ffae1da6e37b48076e2610390c249318acfbea2e`；`scripts/real_data_r0_execute.py` 與 R0 reports | 真實 SMD within-machine internal-vs-score/history diagnostic；無 resolved increment | 只作動機/機制參考；不是 target-specific calibration/readiness trajectories 或 transfer proof。 |
| PreDist v2 | [Zenodo record 19496480](https://zenodo.org/records/19496480) 與其 primary docs | 事後 incident/maintenance reports 與 curated normal events；fault reporting 可能不完整 | 可作 retrospective reference-normal feasibility 線索；沒有文件證明 prospective verified-normal prefix。 |
| CARE v6 | [Zenodo record 15846963](https://zenodo.org/records/15846963) 與其 primary docs | 依 operator/report/manual inputs 建立 event/status labels；farm-A 使用回溯 fault-logbook windows | 可作 retrospective reference-normal feasibility 線索；沒有文件證明 prospective verified-normal prefix。 |

## 可用性總結

目前最佳候選是用 frozen M1 scores 在九條 source-native streams 做小型 score-only retrospective trajectories。若要比較 outcome，必須另有經許可且獨立有效的 normal mask/interval；目前 M1 score arrays 本身不能證明 normal status。P1r 與 R0 可協助挑選簡單 baselines，但無法補足缺少的 hold-forward normal evidence。
