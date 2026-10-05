# D0 conditional sentinel list

Selection ran after atlas computation using the previously recorded analysis_rules:3 robust Streaming-win,3 robust Online-win,2 near-tie,2 high-D,2 sequence-morphology candidates. Robust means **released fixed-panel numeric gap**,>=.05,>=.75 cross-pair votes and every method leave-one-out margin>=.02; it does not prove runtime/model failure validity. No per-series winning method is selected. Tie=.02 absolute gap, high-D>80, sequence average length>=100.

Selection status: {'candidate_counts': {'robust_streaming_win': 4, 'robust_online_win': 69, 'near_tie': 46, 'high_dim': 7, 'sequence_candidate': 132}, 'shortfall': {'robust_streaming_win': 0, 'robust_online_win': 0, 'near_tie': 0, 'high_dim': 0, 'sequence_candidate': 0}, 'selected_count': 12, 'family_counts': {'MSL': 1, 'SMD': 2, 'Exathlon': 1, 'SMAP': 1, 'SWaT': 1, 'SVDB': 1, 'LTDB': 1, 'OPPORTUNITY': 2, 'MITDB': 1, 'Daphnet': 1}, 'family_target_met': True, 'rules_relaxed': False, 'D1_executed': False}. All12 are documented measured-family candidates spanning10 families; known duplicate groups are unique. Diversity target>=4 is met without threshold relaxation. Robust Streaming candidates in the entire release number4 and occur only in two families (MSL/SMD).

| category | file | family | CD | features | avg_anomaly_len | portfolio_gap | historical_training_anomaly_count |
|---|---|---|---|---|---|---|---|
| robust_streaming_win | 012_MSL_id_11_Sensor_tr_539_1st_940.csv | MSL | 0 | 55 | 101.00000 | 0.26529 | unknown / unsupported |
| robust_streaming_win | 078_SMD_id_22_Facility_tr_500_1st_326.csv | SMD | 1 | 38 | 80.53846 | 0.19909 | 3.00000 |
| robust_streaming_win | 059_SMD_id_3_Facility_tr_757_1st_857.csv | SMD | 1 | 38 | 26.90000 | 0.15961 | 0.00000 |
| robust_online_win | 175_Exathlon_id_2_Facility_tr_10684_1st_10784.csv | Exathlon | 0 | 8 | 946.75000 | -0.45353 | unknown / unsupported |
| robust_online_win | 150_SMAP_id_7_Sensor_tr_2077_1st_5394.csv | SMAP | 0 | 25 | 281.00000 | -0.37974 | unknown / unsupported |
| robust_online_win | 172_SWaT_id_2_Sensor_tr_23700_1st_23800.csv | SWaT | 1 | 51 | 1856.22222 | -0.32516 | 0.00000 |
| near_tie | 114_SVDB_id_31_Medical_tr_25000_1st_63090.csv | SVDB | 0 | 2 | 497.00000 | -0.00121 | unknown / unsupported |
| near_tie | 080_LTDB_id_2_Medical_tr_500_1st_266.csv | LTDB | 1 | 3 | 108.44526 | -0.00527 | 107.00000 |
| high_dim | 129_OPPORTUNITY_id_1_HumanActivity_tr_1801_1st_1901.csv | OPPORTUNITY | 1 | 248 | 360.50000 | 0.08135 | 0.00000 |
| high_dim | 130_OPPORTUNITY_id_2_HumanActivity_tr_1045_1st_1145.csv | OPPORTUNITY | 1 | 248 | 469.00000 | 0.09793 | 0.00000 |
| sequence_candidate | 019_MITDB_id_1_Medical_tr_37500_1st_103211.csv | MITDB | 0 | 2 | 18610.00000 | -0.07017 | unknown / unsupported |
| sequence_candidate | 018_Daphnet_id_1_HumanActivity_tr_9693_1st_20732.csv | Daphnet | 1 | 9 | 384.33333 | -0.07242 | 0.00000 |

Names/cutoffs are released metadata, not independently reverified native identities. SMD078 and LTDB080 have historically verified contaminated initial prefixes (3 and107 anomaly points respectively); current raw bytes are not re-inspected here. These are explicit trace/initial-batch diagnostics, not clean-training assurances. Prior raw hashes exist only where the historical75-file audit applies. Missing current acquisition/native mapping stays unresolved.

No known Exathlon duplicate group is repeated. Unverified_unique IDs mean no duplicate is known, not a proof of distinct native source. The two high-D candidates are necessarily OPPORTUNITY and cannot resolve dimension-versus-family causation.

**D1_GO=false.** This is a saved conditional list only. No detector or trace experiment ran. Before any separately authorized D1, reviewer must establish an actionable mechanism, acquire/verify exact bytes and label/cutoff semantics, settle complete score and availability timestamps, and keep strict causal warm-up/test-region metrics. Sentinel listing does not authorize D1 or new method development.
