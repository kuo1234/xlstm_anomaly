# P5-0C claim boundary

## 本輪可以記錄

- 官方 voraus-AD 100 Hz blob、AURSAD v1.1 release 與稽核來源已固定；本輪結構輸出不含 raw dataset 或 sample identifiers。
- 在 COLDSTART commit `9454d21f1f0ee4924868ce171607e19a3648f1ec` 已查的 runner/builders 中，確認 fixed-N commissioning cohorts 與 retrospective N*；沒有看到 per-target online READY acquisition stop。
- voraus-AD 有一套 Yu-Cobot cell 的 retrospective normal/anomaly episodes；AURSAD `sample_nr` 表示 execution，無法依目前證據建立跨 execution acquisition order。
- 現有 dataset 候選沒有足夠獨立 target units 支持 P5 adaptive-stopping feasibility comparison。

## 不可主張

- 不宣稱已普遍證明或成功建立 novelty。
- 不把固定-N/N* 改名為 sequential stopping 貢獻，也不宣稱勝過 COLDSTART N*。
- 不宣稱跨 robot/machine recommissioning、跨機器泛化、deployment guarantee 或 safety certification。
- 不將 setting/action/category/sample number 當作物理 target 身分。
- 不把 COLDSTART 的固定隨機 cohorts 描述成 chronological online acquisition。
- 不將 AURSAD supplementary label 5 當 healthy commissioning；不在 AURSAD 上調參。
- 不報告任何 target performance、模型比較或 efficacy 結果；本輪沒有執行這些工作。

## 可能的窄義問題

若未來找到足夠的獨立 target streams，才可研究「在一個已鎖定 target 上，只依當下 healthy-only prefix 證據輸出候選 READY 時點」；該問題仍不等同 anytime-valid false-alarm guarantee、production release decision 或安全認證。資料與 protocol gate 通過前，它只是待審研究假設。
