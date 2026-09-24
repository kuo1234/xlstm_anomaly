# Source and reconstruction chains

## M2N2 exact set

[Kim, Park and Choo, AAAI 2024](https://ojs.aaai.org/index.php/AAAI/article/view/29210/30283) selects SMD `machine-1-4` and `machine-2-1`, MSL `P-15`, SMAP `T-3`, Yahoo A1 `R20`/`R55`, SWaT, WADI and CreditCard. Its [official README](https://github.com/carrtesy/M2N2) specifies the SMD [OmniAnomaly upstream](https://github.com/NetManAIOps/OmniAnomaly), NASA [Telemanom](https://github.com/khundman/telemanom), restricted [iTrust](https://itrust.sutd.edu.sg/itrust-labs_datasets/), [Yahoo Webscope](https://webscope.sandbox.yahoo.com/), and [Kaggle CreditCard](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) routes. The paper's new-normal rationale is observed train/test distribution differences, *not* a ground-truth drift onset. It explicitly treats CreditCard as comparatively low shift. Normal-only training is an experimental assumption and does not prove every historical prefix is label-verified.

SMD chain: OmniAnomaly `7fb0e0ac` original train/test/test_label TXT → unchanged local bytes → per-test-row anomaly labels. `machine-2-1`'s three SHA256 values equal the historical Phase A seal; M2N2 names the same upstream series, but its private local run files cannot be byte compared. `machine-1-8` is the existing strict anchor, not an M2N2 replacement. NASA chain: mission telemetry and [Hundman et al. KDD 2018](https://arxiv.org/abs/1802.04431) → Telemanom per-series `.npy` train/test and `labeled_anomalies.csv` → expert anomaly intervals in test index coordinates. Only labels downloaded; source ZIP returned 403. The paper's 55 SMAP and 27 MSL *series* counts must not be substituted for each array's feature dimension.

SWaT/WADI chain: iTrust physical testbed normal run + staged physical attacks → release-specific normal/attack files → attack flags. M2N2 uses SWaT Dec 2015 Physical v0 and WADI Nov 2019 A2. These are *attack* annotations, not independently labeled benign operating changes. Yahoo A1 is real traffic, while A2–A4 are synthetic. CreditCard is chronological irregular transactions with `Class` fraud, not a fixed-frequency sensor stream. For both, M2N2's exact per-series chronological train cutoff is not established from the main paper; freeze it separately before analysis.

## AnDri paper version versus current repository

This is an actual inventory/version discrepancy, not alternative names for the same files:

| Artifact | Inventory | What may be inferred |
|---|---|---|
| [AnDri arXiv **v2**, 29 June 2025](https://arxiv.org/pdf/2506.15831v2), evaluation pp. 9–10 | ECG, IOPS, Elec, Weather | ECG/IOPS retain source anomalies but **CanGene/MOA injects** abrupt/gradual drift via segment concatenation and sigmoid transitions. Elec/Weather have natural temporal variation and **injected** scaled sequential anomalies (1.5–3). No exact injection artifacts or per-point four-class labels were found in the current tree. |
| [Current extended manuscript](https://www.cas.mcmaster.ca/~fchiang/pubs/andri.pdf), Table II/evaluation pp. 13–14 | Climate, Sensor, Traffic, SMD, SWaT | This updated paper asserts expert-labeled Sensor drift/anomaly points; Traffic labels are augmented by an EWMA/calendar rule; Climate's heavy-precipitation labels are threshold-derived. It is *not* proof the v2 generated series are in current Git. |
| [`mac-dsl/AnDri` commit `df27f8e`](https://github.com/mac-dsl/AnDri/tree/df27f8eee3244c431c55519ebc84957d46924a44/data/processed) | Directories `climate`, `sensor`, `traffic`, `SMD`, `SWaT` | README still describes older folder names `2021_2025_precip_selected`, `PeMS`, `real iot`; actual tree renames/grouping differ. `test_andri.py` enumerates these five current names. No ECG/IOPS/Elec/Weather processed directories at this commit. |

Specific chains and reconstruction status:

| Current processed family | Upstream → transformation → file/label | Reconstruction confidence |
|---|---|---|
| `climate` (README's precipitation directory) | [Environment and Climate Change Canada hourly stations and climate normals](https://climate-change.canada.ca/climate-data/#/hourly-climate-data) → AnDri precipitation accumulation, station/month thresholds (`util_data.py`) → `AB_..._processed.csv` etc. with raw columns, `heavy`, `heavy_0..5` → threshold-based event labels. Seasonal change is natural but no audited drift-active label. | Partial: station IDs and many derived columns present, but exact source snapshots, normal tables, threshold choices, and export script not sealed. Not NASA MERRA2 Weather. |
| `sensor` (README's `real iot`) | [kimhungGCZ/anomaly_dataset](https://github.com/kimhungGCZ/anomaly_dataset/tree/73a8a89517aa93d4f85cac6200f3d4168f5fd8d0/real%20iot) → **byte-identical copies**, no numerical injection found → `real iot 1.csv`, `real iot 2.csv`, each `anomaly_pattern,anomaly_point,change_point,timestamp,value` → source flags. `util_exp.get_data('INN_Sensor')` ORs the two anomaly flags and discards `change_point` for its binary target. | File exactly reconstructible by copying upstream; labeling *procedure* not independently documented in that Git source. The current paper attributes expert labels; verify this attribution with original authors/ICDE source before calling it independently verified expert ground truth. Actual timestamps are irregular, not uniformly hourly. |
| `traffic` (README's `PeMS`) | [Caltrans PeMS](https://pems.dot.ca.gov/) (login) → station filtering, lag/calendar/holiday/weather indicators and paper Appendix A's EWMA rule → `traffic/101_N/drifts/rev_..._DST.csv`, `total_flow`, `Occupancy_avg`, `Speed_avg`, respective `_label` columns plus `is_event`. | Partial: representative CSV schema and selection code inspected; login, raw snapshot, missing-station selection and rule parameters must be reconstructed. `_label` columns are derived, not expert benign-drift truth. |
| `SMD` | [OmniAnomaly SMD](https://github.com/NetManAIOps/OmniAnomaly) → anomaly test subsets and dimension reduction (paper VIF threshold) → `machine-*_subset.csv`; labels remain anomalies. | Partial: original upstream available, but processed crop/feature-selection identity has not been byte-reconstructed. No drift labels. |
| `SWaT` | [iTrust SWaT July 2019](https://itrust.sutd.edu.sg/itrust-labs_datasets/) → AnDri subset/dimension reduction → `SWaT_processed.csv`, attack labels. | Restricted original; no access-bypassing use of its public derivative. Different release from M2N2's Dec 2015 files. No benign-drift labels. |

The v2 source chains are TSB-UAD ECG/IOPS → CanGene/MOA transition injection → *unlocated* generated series → anomaly labels plus generated drift schedule; NSW Elec / NASA MERRA2 Weather → anomaly scaling injection → *unlocated* generated series → injected anomaly labels, natural but unlocalized drift. None can be independently reconstructed **exactly** from current repository because generation seeds, original samples and export hashes were not traced. Do not map any of them to Climate/Sensor/Traffic by name similarity.

## HAI 22.04

[Official `icsdataset/hai` at `2a814ceb`](https://github.com/icsdataset/hai) → six normal CSVs (`train1`–`train6`) and four attack CSVs (`test1`–`test4`) under `hai-22.04` via Git LFS → 86 process variables + `timestamp` + `Attack` (88 columns **according to release-specific summary files**). Its official small `summary/summary(testN.csv).txt` reports start/end, durations and 7/17/10/24 attack episodes; the [README](https://github.com/icsdataset/hai#hai-dataset) reports 1 Hz, 279 normal hours/534.4 MB and 100 attack-test hours/195.6 MB. The [official technical manual](https://github.com/icsdataset/hai/blob/master/hai_dataset_technical_details.pdf), HAI 22.04 section, describes 58 attacks as **32 primitives plus 26 simultaneous combinations**, with a timetable of scenario/target controller/target point/start/duration. It also says normal set-point command sequences are generated by an HMM. Its prose anomalously claims 89 columns/87 tags/four labels for 22.04, contradicting both the repository's 22.04-specific README (process labels dropped) and all ten official 22.04 summary files (88 columns, 86 tags, `Attack`); treat that paragraph as stale and verify actual CSV header after LFS acquisition. The summary files are metadata, not additional benign-regime labels. Timestamps are formatted wall-clock strings with no verified timezone; do not infer UTC. License: [CC BY-SA 4.0](https://github.com/icsdataset/hai#license). A continuous `Attack` run yields an attack interval; whether a particular attack causes an observable process deviation at every second is a different question. No legitimate-drift class is supplied.

Published per-file uncompressed decimal MB and duration, **not locally measured sizes** (Git LFS unavailable):

| Normal file | Hours / MB | Attack test file | Hours / MB / episodes |
|---|---:|---|---:|
| train1 | 26 / 50.7 | test1 | 24 / 48.2 / 7 |
| train2 | 56 / 108.9 | test2 | 23 / 44.5 / 17 |
| train3 | 35 / 66.7 | test3 | 17 / 33.4 / 10 |
| train4 | 24 / 45.7 | test4 | 36 / 69.5 / 24 |
| train5 | 66 / 125.6 | — | — |
| train6 | 72 / 136.8 | — | — |

The per-file published hours sum to 279 train and 100 test; the README table prints 100.3 h for the test total, reflecting rounded file durations. No CSV was acquired or silently read as LFS pointer text.

## Existing repository constraints

[Phase A README](../../reports/phase_a/README.md), [SMD seal](../../reports/phase_a/smd_seal.json) and [download list](../../reports/phase_a/downloads.json) document the strict SMD 1-8/2-1 anchor and the TSB-AD-M/CD=1 candidate inventory. The TSB "drift" tag is series-level metadata, not per-timestamp drift truth; many native identities remain unresolved and the historical STOP is preserved. `data/phase_a/` is absent locally. No existing SMAP/MSL/SWaT/WADI raw acquisition script or file was found at the base commit; historical reports mention them as candidates or context, not available assets.
