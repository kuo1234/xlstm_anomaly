# TSB-drift qualification audit

Final protocol gate: **ADMISSION_BENCHMARK_READY**. This is dataset/protocol readiness, not safe-admission performance.

All 75 upstream CD=1 entries retained in tsb_candidate_inventory.json. Source correction excludes 23 simulated GHL and five simulated CATSv2; all remaining 47 assessed with frozen rules, no favorable-series selection. Primary physical units are all 15 source-mapped SMD machines. Other families have unresolved native crop/group identity; four Exathlon entries are one exact feature-duplicate group, not four independent confirmations.

## Method and exposure

Commit e07b0b19093ce90b98c3d8f265e43867a054322a was pushed and verified before the first new qualification label read at 2026-10-04T17:31:08.022144+00:00. Access log completed 2026-10-04T17:31:22.404164+00:00. All labels were historically read during M0; prior exposure metadata was also read in this task before new calculations. This is frozen-method exploratory qualification, not strict confirmatory.

The result JSON utc field inherits freeze-check start time (dictionary merge); the access-log timestamp is the completion authority. No timestamps were used to select data.

Upstream full-observation scaler, FD auto bins (10–30) and .001/.999 edge quantiles reproduce an offline diagnostic only. Filename train cutoff defines original batch boundaries; incomplete tail excluded. Mask Label==0 in place using identical edges/scaler; never compact time or impute empty batches. Support requires max(32,ceil(.5*batch length)) retained points. Anchor batch0 and two consecutive supported post-batches required. Masked max-feature JS divergence >=.10 nats for two adjacent post-batches, and common-support mean-strength retention >=.5, define descriptive persistent drift. These engineering cutoffs were committed prospectively and never tuned; no inferential significance claim.

## Results

| Qualification | Series count |
|---|---:|
| REAL_DRIFT_SUPPORTED | 46 |
| DRIFT_ANOMALY_CONFOUNDED | 0 |
| DRIFT_CAUSE_UNRESOLVED | 1 |
| INSUFFICIENT_SERIES_LENGTH / SUPPORT | 0 |

Raw-versus-masked common-support strength Spearman rho=0.966563 (47 series; descriptive, no iid p-value). Max raw JSD reproduction absolute error against published metadata: 5.8491937e-06; full-matrix mean error max 0.0027972842. This is close approximate reproduction, not exact certification of original 75-series selection; selection script/full HAL paper remains unverified.

Max-feature persistence: 14/15 SMD; mean-feature sensitivity with the same predeclared .10-nat consecutive criterion: 7/15 SMD and 31/47 overall. Max aggregation may be driven by a single channel and tends to saturate near ln2. Histograms do not establish finite settled time, temporal dynamics, causal mechanism or change-point accuracy. Full max and mean anchor curves remain in JSON, matrices are ignored remote artifacts with SHA256.

Masked/raw strength ratios can exceed1: removing labelled anomalies may sharpen differences, not repair or improve detector performance. None of the assessed files loses the primary persistence criterion through masking under sufficient support, except 076 which never meets anchor persistence (raw and masked). This does not exclude unlabelled faults, annotation bias or missing-not-at-random sampling. A CD=1 label can reflect post-to-post differences that our fixed batch0 persistence criterion does not capture; 076 remains unresolved, no anchor rescue.

Ten files have labelled anomalies inside their released train prefix (078,080,116,118,119,122,123,124,125,127). They stay in this distribution audit but are ineligible for a future healthy-only prefix fit as released. No split moved to make them eligible.

## All SMD physical units

| ID / native machine | Original tags | Classification | Mask/raw ratio | Supported batches | Mean-feature persistent | Healthy prefix |
|---|---|---|---:|---:|---|---|
| 057 / SMD/machine-1-2 | change_point | REAL_DRIFT_SUPPORTED | 0.9967 | 5/5 | False | True |
| 059 / SMD/machine-2-3 | change_point, periodic, random_walk | REAL_DRIFT_SUPPORTED | 1.0039 | 31/31 | True | True |
| 060 / SMD/machine-3-7 | change_point | REAL_DRIFT_SUPPORTED | 1.0007 | 4/4 | False | True |
| 061 / SMD/machine-3-8 | continuous | REAL_DRIFT_SUPPORTED | 1.0126 | 4/4 | False | True |
| 064 / SMD/machine-1-3 | continuous, change_point | REAL_DRIFT_SUPPORTED | 0.9996 | 9/9 | False | True |
| 065 / SMD/machine-1-7 | periodic, change_point, random_walk | REAL_DRIFT_SUPPORTED | 1.0024 | 29/32 | True | True |
| 066 / SMD/machine-3-4 | change_point | REAL_DRIFT_SUPPORTED | 0.9950 | 8/8 | False | True |
| 067 / SMD/machine-3-2 | continuous, change_point | REAL_DRIFT_SUPPORTED | 1.0036 | 11/11 | True | True |
| 068 / SMD/machine-3-9 | change_point | REAL_DRIFT_SUPPORTED | 0.9994 | 26/26 | True | True |
| 071 / SMD/machine-3-1 | continuous | REAL_DRIFT_SUPPORTED | 0.9993 | 25/25 | True | True |
| 074 / SMD/machine-3-11 | change_point | REAL_DRIFT_SUPPORTED | 0.9996 | 4/4 | False | True |
| 075 / SMD/machine-2-7 | change_point, periodic, random_walk | REAL_DRIFT_SUPPORTED | 1.0000 | 41/42 | True | True |
| 076 / SMD/machine-2-8 | change_point | DRIFT_CAUSE_UNRESOLVED | 0.9941 | 4/4 | False | True |
| 077 / SMD/machine-1-4 | continuous, change_point | REAL_DRIFT_SUPPORTED | 1.0016 | 7/7 | False | True |
| 078 / SMD/machine-3-10 | change_point, periodic | REAL_DRIFT_SUPPORTED | 1.0001 | 45/47 | True | False |

059 machine-2-3, 065 machine-1-7 and 075 machine-2-7 are source-mapped, healthy-prefix, periodic/change-point tagged examples that retain masked max and mean persistence; all 15 outcomes remain primary, not a post-hoc best-three experiment. 078 machine-3-10 retains drift but has contaminated prefix. Tags alone do not verify a recurrence or benign operating context.

## Every non-simulated candidate (no omitted failures)

| File | Family | Qualification | Mask/raw | Supported batches | Mean sensitivity | Prefix anomaly points |
|---|---|---|---:|---:|---|---:|
| 009_MSL_id_8_Sensor_tr_714_1st_1390.csv | MSL | REAL_DRIFT_SUPPORTED | 0.9954 | 4/4 | False | 0 |
| 018_Daphnet_id_1_HumanActivity_tr_9693_1st_20732.csv | Daphnet | REAL_DRIFT_SUPPORTED | 1.0178 | 4/4 | True | 0 |
| 057_SMD_id_1_Facility_tr_4529_1st_4629.csv | SMD | REAL_DRIFT_SUPPORTED | 0.9967 | 5/5 | False | 0 |
| 059_SMD_id_3_Facility_tr_757_1st_857.csv | SMD | REAL_DRIFT_SUPPORTED | 1.0039 | 31/31 | True | 0 |
| 060_SMD_id_4_Facility_tr_7176_1st_10609.csv | SMD | REAL_DRIFT_SUPPORTED | 1.0007 | 4/4 | False | 0 |
| 061_SMD_id_5_Facility_tr_7176_1st_15144.csv | SMD | REAL_DRIFT_SUPPORTED | 1.0126 | 4/4 | False | 0 |
| 064_SMD_id_8_Facility_tr_2272_1st_2372.csv | SMD | REAL_DRIFT_SUPPORTED | 0.9996 | 9/9 | False | 0 |
| 065_SMD_id_9_Facility_tr_737_1st_837.csv | SMD | REAL_DRIFT_SUPPORTED | 1.0024 | 29/32 | True | 0 |
| 066_SMD_id_10_Facility_tr_2634_1st_2734.csv | SMD | REAL_DRIFT_SUPPORTED | 0.9950 | 8/8 | False | 0 |
| 067_SMD_id_11_Facility_tr_1980_1st_2080.csv | SMD | REAL_DRIFT_SUPPORTED | 1.0036 | 11/11 | True | 0 |
| 068_SMD_id_12_Facility_tr_1099_1st_1199.csv | SMD | REAL_DRIFT_SUPPORTED | 0.9994 | 26/26 | True | 0 |
| 071_SMD_id_15_Facility_tr_1109_1st_1209.csv | SMD | REAL_DRIFT_SUPPORTED | 0.9993 | 25/25 | True | 0 |
| 074_SMD_id_18_Facility_tr_7174_1st_21230.csv | SMD | REAL_DRIFT_SUPPORTED | 0.9996 | 4/4 | False | 0 |
| 075_SMD_id_19_Facility_tr_564_1st_664.csv | SMD | REAL_DRIFT_SUPPORTED | 1.0000 | 41/42 | True | 0 |
| 076_SMD_id_20_Facility_tr_5925_1st_17580.csv | SMD | DRIFT_CAUSE_UNRESOLVED | 0.9941 | 4/4 | False | 0 |
| 077_SMD_id_21_Facility_tr_3026_1st_3126.csv | SMD | REAL_DRIFT_SUPPORTED | 1.0016 | 7/7 | False | 0 |
| 078_SMD_id_22_Facility_tr_500_1st_326.csv | SMD | REAL_DRIFT_SUPPORTED | 1.0001 | 45/47 | True | 3 |
| 080_LTDB_id_2_Medical_tr_500_1st_266.csv | LTDB | REAL_DRIFT_SUPPORTED | 1.0087 | 199/200 | True | 107 |
| 116_TAO_id_1_Environment_tr_500_1st_3.csv | TAO | REAL_DRIFT_SUPPORTED | 1.0542 | 20/20 | True | 26 |
| 118_TAO_id_3_Environment_tr_500_1st_7.csv | TAO | REAL_DRIFT_SUPPORTED | 1.0453 | 20/20 | True | 19 |
| 119_TAO_id_4_Environment_tr_500_1st_1.csv | TAO | REAL_DRIFT_SUPPORTED | 1.1149 | 20/20 | True | 56 |
| 122_TAO_id_7_Environment_tr_500_1st_19.csv | TAO | REAL_DRIFT_SUPPORTED | 1.0983 | 20/20 | True | 42 |
| 123_TAO_id_8_Environment_tr_500_1st_62.csv | TAO | REAL_DRIFT_SUPPORTED | 1.0453 | 20/20 | True | 19 |
| 124_TAO_id_9_Environment_tr_500_1st_1.csv | TAO | REAL_DRIFT_SUPPORTED | 1.0596 | 20/20 | True | 33 |
| 125_TAO_id_10_Environment_tr_500_1st_9.csv | TAO | REAL_DRIFT_SUPPORTED | 1.1088 | 20/20 | True | 51 |
| 127_TAO_id_12_Environment_tr_500_1st_24.csv | TAO | REAL_DRIFT_SUPPORTED | 1.0544 | 20/20 | True | 27 |
| 129_OPPORTUNITY_id_1_HumanActivity_tr_1801_1st_1901.csv | OPPORTUNITY | REAL_DRIFT_SUPPORTED | 1.0009 | 13/13 | True | 0 |
| 130_OPPORTUNITY_id_2_HumanActivity_tr_1045_1st_1145.csv | OPPORTUNITY | REAL_DRIFT_SUPPORTED | 0.9989 | 4/4 | True | 0 |
| 132_OPPORTUNITY_id_4_HumanActivity_tr_895_1st_995.csv | OPPORTUNITY | REAL_DRIFT_SUPPORTED | 0.9958 | 10/10 | True | 0 |
| 133_OPPORTUNITY_id_5_HumanActivity_tr_1745_1st_6500.csv | OPPORTUNITY | REAL_DRIFT_SUPPORTED | 1.0009 | 4/4 | True | 0 |
| 134_OPPORTUNITY_id_6_HumanActivity_tr_1477_1st_1577.csv | OPPORTUNITY | REAL_DRIFT_SUPPORTED | 0.9987 | 11/11 | True | 0 |
| 135_OPPORTUNITY_id_7_HumanActivity_tr_2085_1st_2185.csv | OPPORTUNITY | REAL_DRIFT_SUPPORTED | 1.0000 | 10/10 | True | 0 |
| 136_OPPORTUNITY_id_8_HumanActivity_tr_1495_1st_1595.csv | OPPORTUNITY | REAL_DRIFT_SUPPORTED | 1.0002 | 18/18 | True | 0 |
| 137_CreditCard_id_1_Finance_tr_500_1st_541.csv | CreditCard | REAL_DRIFT_SUPPORTED | 0.9996 | 569/569 | True | 0 |
| 148_SMAP_id_5_Sensor_tr_2011_1st_5060.csv | SMAP | REAL_DRIFT_SUPPORTED | 0.9940 | 4/4 | False | 0 |
| 154_SMAP_id_11_Sensor_tr_2117_1st_4770.csv | SMAP | REAL_DRIFT_SUPPORTED | 0.9997 | 4/4 | False | 0 |
| 156_SMAP_id_13_Sensor_tr_1173_1st_2750.csv | SMAP | REAL_DRIFT_SUPPORTED | 0.9942 | 4/4 | False | 0 |
| 166_SMAP_id_23_Sensor_tr_1113_1st_1890.csv | SMAP | REAL_DRIFT_SUPPORTED | 0.9941 | 4/4 | False | 0 |
| 167_SMAP_id_24_Sensor_tr_2094_1st_5600.csv | SMAP | REAL_DRIFT_SUPPORTED | 1.0000 | 4/4 | False | 0 |
| 171_SWaT_id_1_Sensor_tr_3749_1st_9522.csv | SWaT | REAL_DRIFT_SUPPORTED | 1.0000 | 4/4 | False | 0 |
| 172_SWaT_id_2_Sensor_tr_23700_1st_23800.csv | SWaT | REAL_DRIFT_SUPPORTED | 1.0014 | 15/16 | True | 0 |
| 173_GECCO_id_1_Sensor_tr_16165_1st_16265.csv | GECCO | REAL_DRIFT_SUPPORTED | 1.0007 | 8/8 | True | 0 |
| 179_Exathlon_id_6_Facility_tr_11665_1st_13484.csv | Exathlon | REAL_DRIFT_SUPPORTED | 0.9983 | 4/4 | False | 0 |
| 188_Exathlon_id_15_Facility_tr_12538_1st_12638.csv | Exathlon | REAL_DRIFT_SUPPORTED | 0.9971 | 10/10 | True | 0 |
| 190_Exathlon_id_17_Facility_tr_12538_1st_12638.csv | Exathlon | REAL_DRIFT_SUPPORTED | 0.9971 | 10/10 | True | 0 |
| 198_Exathlon_id_25_Facility_tr_12538_1st_12638.csv | Exathlon | REAL_DRIFT_SUPPORTED | 0.9971 | 10/10 | True | 0 |
| 199_Exathlon_id_26_Facility_tr_12538_1st_12638.csv | Exathlon | REAL_DRIFT_SUPPORTED | 0.9971 | 10/10 | True | 0 |

Original tags are preserved in full inventory/results; they are source-level descriptions, not point/interval legitimate-settled truth. Random-walk tags never imply an available settled regime.

Real distribution drift has a small physically mapped qualifying group. All REAL_DRIFT_SUPPORTED entries still have drift cause UNKNOWN, legitimate new normal UNKNOWN, operational unsafe NOT_EVALUABLE and PROMOTE timing NOT_EVALUABLE. No real admission benchmark or policy benefit was measured.

Sources: [StrAD pinned audit code](https://github.com/magaliparrino/StrAD/blob/7078876bbd9398481a65c22b7689702ce9e0d558/TSB-drift/jsd_drift.py); [released drift metadata](https://github.com/magaliparrino/StrAD/blob/7078876bbd9398481a65c22b7689702ce9e0d558/results/benchmark_eval_results/CD.csv); [official archive](https://www.thedatum.org/datasets/TSB-AD-M.zip). Existing primary-backed source corrections and hashes: reports/m0_v3_source_correction.md, reports/phase_a/downloads.json, source_groups.json and trace_relations.json. All raw data remain remote.
