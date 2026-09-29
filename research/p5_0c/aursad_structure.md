# AURSAD v1.1 結構稽核

## Pin 與證據來源

AURSAD 固定至 [Zenodo v1.1](https://zenodo.org/records/4559556)，DOI `10.5281/zenodo.4559556`，檔案 `AURSAD.h5` 大小 `6,417,816,949` bytes，官方 MD5 `08e4706cf15144761a12cb86bd071d72`。既有 COLDSTART 固定版稽核記錄同一檔案大小及 SHA-256 `40ae5ce055a7f9cf399f4485bc667c81171013b3742799ed3f28f1e7243c7aea`；其大小與 Zenodo 相符，但本輪沒有重新下載全檔來核對 MD5 與 SHA-256 是否對應同一 bytes。partial temp file 不作為證據。授權依 Zenodo API metadata 為 CC BY 4.0。雜湊來源詳見 [dataset_pins.json](dataset_pins.json)。

本報告引用 COLDSTART commit `9454d21f1f0ee4924868ce171607e19a3648f1ec` 已產生的 aggregate-only audit，不複製 execution IDs 或 raw rows。主要來源是 [episode audit](https://github.com/priestly-ops/COLDSTART/blob/9454d21f1f0ee4924868ce171607e19a3648f1ec/reports/aursad/aursad_episode_audit.json)、[dataframe schema audit](https://github.com/priestly-ops/COLDSTART/blob/9454d21f1f0ee4924868ce171607e19a3648f1ec/reports/aursad/aursad_dataframe_audit.json) 及 [episode length summary](https://github.com/priestly-ops/COLDSTART/blob/9454d21f1f0ee4924868ce171607e19a3648f1ec/reports/aursad/aursad_episode_length_summary.csv)。

## 結構摘要

- 固定 audit 檢查 6,249,074 rows、6,417,816,949-byte HDF5，整理後 dataframe 有 134 fields；原論文報告 125 signal dimensions，欄位總數採計口徑不同。
- 4,094 個 `sample_nr` executions，編號 1–4,094；每個 execution 一個 label，資料 rows 依 execution 連續，沒有 mixed-label 或 noncontiguous execution。
- 100 Hz。episode timestamp 在 4 個 execution 內有非單調 pair。COLDSTART 的 P0.8a script 將跨 execution timestamp decrease 視為候選 recording-block boundary，並明確將 `sample_nr` 視為 stored-file index、不是 global physical clock；該 session audit 的輸出未包含在固定版，所以本輪不據此主張已建立全域時間順序。
- label counts：normal tightening 1,420；damaged screw 221；extra component 183；missing screw 218；damaged thread 3；supplementary loosening/screw-picking operation 2,049。後者不自動併入 normal commissioning。
- execution length：normal 中位數 1,544.5 rows（min 914、max 3,100）；damaged screw 1,543（1,127–2,567）；extra component 1,532（1,052–2,224）；missing screw 1,397.5（852–1,976）；damaged thread 3 筆，中位數 1,362（1,284–1,362）。Supplementary label 5 長度中位數 1,581，範圍 13–3,795。

## Identity、chronology 與 candidate context

官方資料及 paper 描述一套 UR3e + OnRobot screwdriver screwdriving setup。`sample_nr` 是一次 execution 的 identity，不是機器/target identity；100 Hz timestamp 是 execution 內時間，stored `sample_nr` 次序不能證明實際 acquisition chronology。COLDSTART AURSAD protocol builder 按 label 組成 fixed healthy commissioning/calibration/evaluation 及 anomaly-evaluation cohorts，沒有把它們作為同一 target 的時間 prefix/suffix。

論文記載兩片各有 92 個孔的 screwdriving plates；HDF5 schema 也列有 from/to plate pin register fields。固定版 column-statistics audit 記錄 register 25 有 93 個整體 distinct values（範圍 0–92），register 26 有 103 個（範圍 0–102）；這只是逐欄、全 row 的邊際統計，沒有檢查每個 execution 的 pin pair 是否穩定，也沒有聯合 pair、label 或時間順序支持度。register 26 超出 paper 所述 plate hole index 範圍的值也需先釐清。因此 pin/pin-pair 是仍待 label-blind 驗證的 dataset-native context 候選；目前沒有證據證明它們可形成多個具 chronology、反覆 healthy commissioning、未來 normal/fault exposure 的獨立 streams。

這項未知不等於「同一 robot 不能有多個 target」；阻塞原因是可重現的獨立 context stream 尚未由現有 audit 證據建立。下一步若要檢查 pin contexts，應只做 metadata-level per-execution consistency/support/recording-block audit，並遵守 AURSAD external lock，不用它挑 method 或調參。

## 來源

- [Zenodo v1.1 pin](https://zenodo.org/records/4559556)
- [AURSAD paper：setup、資料頻率及各 plate hole](https://arxiv.org/html/2102.01409)
- [AURSAD package README](https://github.com/CptPirx/AURSAD)
- [COLDSTART 固定版 AURSAD protocol builder](https://github.com/priestly-ops/COLDSTART/blob/9454d21f1f0ee4924868ce171607e19a3648f1ec/experiments/build_aursad_protocol.py)
- [COLDSTART 固定版 acquisition-session audit implementation](https://github.com/priestly-ops/COLDSTART/blob/9454d21f1f0ee4924868ce171607e19a3648f1ec/experiments/run_p08a_aursad_session_audit.py)
- [COLDSTART 固定版 per-column aggregate statistics](https://github.com/priestly-ops/COLDSTART/blob/9454d21f1f0ee4924868ce171607e19a3648f1ec/reports/aursad/aursad_column_statistics.csv)
