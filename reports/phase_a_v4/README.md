# Final A2 PASS — released-series external stress-test manifest

The v4 rule was committed and pushed as `6852e7ccec0dce0ff81d3fca77df925b25e6a473` before manifest generation. A1 raw/preprocessed seals remain valid. Historical strict/v3 audits remain unchanged, including their prior STOPs and ambiguous legacy field; no unresolved native mapping has been reclassified as verified independence.

The final exact solver objectives are: **9** global families (maximum), **9** sum of within-bucket unique-family counts (maximum conditional on primary), **20** sum of squared global family counts (minimum conditional on both). Lexicographic filename tie-breaking selects the following twelve. Synthetic GHL/CATSv2 and contaminated prefixes remain excluded. Original multi-tags are retained in JSON, not replaced by the assigned bucket.

| Bucket | Released filename | source_family | native_provenance_unresolved |
|---|---|---|---|
| continuous | 154_SMAP_id_11_Sensor_tr_2117_1st_4770.csv | SMAP | true |
| continuous | 171_SWaT_id_1_Sensor_tr_3749_1st_9522.csv | SWaT | true |
| continuous | 173_GECCO_id_1_Sensor_tr_16165_1st_16265.csv | GECCO | true |
| change_point | 009_MSL_id_8_Sensor_tr_714_1st_1390.csv | MSL | true |
| change_point | 018_Daphnet_id_1_HumanActivity_tr_9693_1st_20732.csv | Daphnet | true |
| change_point | 137_CreditCard_id_1_Finance_tr_500_1st_541.csv | CreditCard | true |
| periodic | 059_SMD_id_3_Facility_tr_757_1st_857.csv | SMD | false |
| periodic | 065_SMD_id_9_Facility_tr_737_1st_837.csv | SMD | false |
| periodic | 075_SMD_id_19_Facility_tr_564_1st_664.csv | SMD | false |
| random_walk | 129_OPPORTUNITY_id_1_HumanActivity_tr_1801_1st_1901.csv | OPPORTUNITY | true |
| random_walk | 132_OPPORTUNITY_id_4_HumanActivity_tr_895_1st_995.csv | OPPORTUNITY | true |
| random_walk | 188_Exathlon_id_15_Facility_tr_12538_1st_12638.csv | Exathlon | true |

Global family counts: SMD=3, OPPORTUNITY=2; SMAP/SWaT/GECCO/MSL/Daphnet/CreditCard/Exathlon=1 each. Per bucket: continuous has 1+1+1; change_point has 1+1+1; periodic has SMD=3; random_walk has OPPORTUNITY=2 and Exathlon=1. Periodic is **single-family descriptive evidence only**. All TSB statistics cluster at source_family first; none are causal H2/H3/H4a evidence.

Explicit provenance denominators in `selection_summary.json`: inventory_count=75; eligible_count=37; inventory_native_provenance_unresolved=60; eligible_inventory_native_provenance_unresolved=23; selected_count=12; selected_native_provenance_unresolved=9. Only three selected SMD traces have verified native identities. Unresolved released-family provenance, including CreditCard's conflicting catalog link, is preserved verbatim in the inventory. Source-family grouping is a conservative inference unit, not proof of native independence.

`manifest.json` records released-file SHA256, official metadata commit/hash, archive URL/member, source-family and native trace evidence where available, D/N/cutoff and fit/calibration/test intervals. All 75 raw candidate byte hashes and all twelve A1 raw/preprocessed hashes were rechecked before assignment. Known duplicate/same-origin constraints remain enforced: only Exathlon 188 is selected from the known four-member exact duplicate group; no released file is reused; selected SMD machines do not overlap fixed 1-8/2-1.

Three v4 regression tests cover the real manifest, explicit denominators, exact agreement with exhaustive four-level optimization on a small fixture, reversed-input determinism, known duplicate exclusion and mathematical infeasibility handling. No heuristic or random tie-breaking was used.

Reproduce with `rtk python3 scripts/phase_a_v4.py`. Verify with `rtk sha256sum -c reports/phase_a_v4/SHA256SUMS`. The seal includes this report and JSON artifacts after `scripts/seal_v4.py` runs. No model-result inspection or GPU/model training occurred. Phase C remains locked pending external review.
