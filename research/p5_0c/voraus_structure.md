# voraus-AD 100 Hz 結構稽核

## Pin 與稽核範圍

下載來源為官方 Parquet URL，檔案大小 `1,115,942,833` bytes，SHA-256 為 `c90ab1c78af52651b954d41787f7e89d750f0a128b57600b0e5ceec22621f704`。資料授權為 CC BY-NC-SA 4.0；官方 repository code 固定在 `a91a86a642d23df58833b792a53de01edfd81abe`。見 [dataset pin](dataset_pins.json)。官方 README 未提供 immutable data release 或密碼學檔案 checksum；本次下載 hash 用來識別實際讀取的 blob，ETag 僅記作 HTTP metadata。

`scripts/audit_voraus_structure.py` 讀取七個 episode/metadata columns，從 Parquet metadata 讀取完整欄位 schema。沒有讀取 sensor feature values，亦沒有訓練、打分或查看模型結果。完整 aggregate 輸出在 [voraus_structure_aggregate.json](voraus_structure_aggregate.json)，不包含 sample IDs 或 raw rows。

## 結構摘要

| 項目 | 稽核結果 |
|---|---:|
| Parquet row groups | 1 |
| rows | 2,321,690 |
| fields | 137：7 個 metadata + 130 個 signal fields |
| schema signature SHA-256 | `56f1f4ca6f10be8bb2b1750b48899f3b175898da8ce8443da86d4540c90c0f20` |
| samples / 操作 episode | 2,122 |
| metadata nulls | 讀取的 7 欄為 0 |
| 每 episode label/category/setting 穩定 | 2,122/2,122 |
| episode rows 在檔案中連續 | 是；重新出現的 sample 數為 0 |
| within-sample `time` | 2,319,568 個相鄰 pair 全部嚴格遞增，無下降 |

樣本長度（rows）為 min 986、p05 1,055、p25 1,082、中位數 1,096、p75 1,110、p95 1,137、max 1,164。

資料集含 1,367 個 normal episodes 及 755 個 anomaly episodes。normal setting 支持為 PRE_A 948、PRE_B 319、BETWEEN_A 37、BETWEEN_B 44、BETWEEN_C 19；合計 1,367。category 0–11 對應 anomaly 類別，category 12 為 normal。官方 paper 描述先收集 948 個初始 normal samples，再交替收集 755 個 anomaly 與 419 個後續 normal samples。這是單一 Yu-Cobot cell 的歷史資料設計；資料中的 `time` 是操作 episode 內的時間，不能拿來計算 episode 之間的經過時間。

## Candidate 欄位判讀

- `setting` 對應官方 Variant enum，包括 PRE_A、PRE_B、BETWEEN_A/B/C 和各種故障/場景變體。它不是機器或獨立 target ID。這批資料中正常 setting 與 anomaly setting 也按類別分開。
- `action` 是每個 pick-and-place operation 內的動作階段。每個 sample 含 14–15 個 action codes；14 個 codes 出現在全部 2,122 個 samples，最後一個出現在 558 個 samples。它是 episode 內 metadata，不是重複 commissioning context。
- `setting × action` 有 1,152 個觀測 strata：75 個只含 normal、1,077 個只含 anomaly，沒有跨 normal/anomaly 的 strata。其樣本支持中位數 10、範圍 1–948。這些 strata 不代表 1,152 個獨立實體 target。
- `category` 表示正常/故障類別，不是物理身分；每個 sample 只有一類。
- `sample` 是一次 pick-and-place operation 的 episode ID。它給出重複 operations，但沒有多台 Yu-Cobot 或多個獨立 cell 可做 target-level 比較。

官方 paper 的資料切分描述提供單一 cell 內的 retrospective sequence：前段 948 個 normal episodes，後段含 normal/anomaly episodes。這可支援有限的單 cell historical replay 問題，不能供跨 target 適應效果估計。官方 `time` 欄位不能補足跨 episode timestamp。

## 來源

- [官方 dataset README 與授權](https://github.com/vorausrobotik/voraus-ad-dataset/blob/a91a86a642d23df58833b792a53de01edfd81abe/README.md)
- [官方 metadata/Variant/Action/Category enum](https://github.com/vorausrobotik/voraus-ad-dataset/blob/a91a86a642d23df58833b792a53de01edfd81abe/voraus_ad.py)
- [官方 paper：樣本數與歷史資料順序](https://arxiv.org/html/2311.04765#S3)
- [pin 與完整 schema fingerprint](dataset_pins.json)
