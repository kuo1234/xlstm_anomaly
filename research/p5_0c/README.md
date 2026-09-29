# P5-0C：資料集切換與 target-unit gate

**查核日期：** 2026-09-29

**Issue 任務：** [#9 — P5-0C Dataset Switch](https://github.com/kuo1234/xlstm_anomaly/issues/9#issuecomment-5884662287)

**起始 commit：** `7576bef5c09a19b2093ee0497d9aa01a9b5f5061`

**最終 gate：** `P5_0C_TARGET_UNIT_BLOCKED`

## 結論

已下載並固定官方 voraus-AD 100 Hz Parquet；AURSAD v1.1 使用 COLDSTART 固定版既有的完整資料雜湊與結構稽核作為 pin，本輪沒有把未完成的暫存下載當成資料證據。沒有提交 raw dataset。

在本次限定查核的 COLDSTART 程式中，找到固定 N commissioning、固定 calibration/evaluation cohorts，以及事後由 Recall/FPR 估計 N*；沒有找到只根據當前 target healthy prefix 決定 READY 時點的 per-target online stopping。這表示窄義 stopping 想法在該版尚未被此程式查核否決；這不是廣泛 novelty 證明。

兩個資料集各記錄一套實體 robot/task setup；這本身不排除同一 robot 下有可重複的獨立 execution contexts。voraus-AD 的 `setting`、`action`、`category` 及其交叉欄位不能當此類 context；AURSAD plate-pin registers 是候選，但目前只有欄位邊際統計，未證明 per-execution pin context 的重複支持及 chronology。故現有證據尚未建立足夠的獨立 target streams，不能進入 P5 efficacy run；這不是證明資料中永遠不存在可用 contexts。

## 產物

- [dataset_pins.json](dataset_pins.json)：版本、授權、檔案大小與雜湊來源。
- [coldstart_overlap.md](coldstart_overlap.md)：按程式與協定逐項比對 COLDSTART/P5。
- [voraus_structure.md](voraus_structure.md)：本輪下載的 Parquet 結構稽核。
- [voraus_structure_aggregate.json](voraus_structure_aggregate.json)：不含 sample IDs 或 signal values 的聚合輸出。
- [aursad_structure.md](aursad_structure.md)：AURSAD v1.1 的既有固定版稽核及本輪結構判讀。
- [target_unit_analysis.md](target_unit_analysis.md)：候選 unit 支持度與選擇結果。
- [claim_boundary.md](claim_boundary.md)：允許及禁止的論述。
- [proposed_p5_0d_protocol.md](proposed_p5_0d_protocol.md)：若要重開工作，先做的資料資格協定。
- [final_gate.md](final_gate.md)：最終狀態與可解除條件。
- [scripts/audit_voraus_structure.py](scripts/audit_voraus_structure.py)：可重現 aggregate-only Parquet audit。

本輪只讀 COLDSTART 程式/協定與資料 metadata；沒有訓練模型、計算 target performance、調校 AURSAD、救援 PreDist，或執行 formal efficacy run。
