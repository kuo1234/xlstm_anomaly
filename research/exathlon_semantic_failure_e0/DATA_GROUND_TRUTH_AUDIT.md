# Exathlon ground-truth reality check — 2026-10-06

Official [ground_truth.zip](https://github.com/exathlonbenchmark/exathlon/blob/4101f6087f902fa150e392b65c957976faa84e40/data/raw/ground_truth.zip) contains one CSV, seven fields and 109 unique rows. The original trace archive inventory contains 93 native traces: 59 undisturbed and 34 disturbed. The bytes and Git blob/SHA256 are saved in provenance; CSV SHA256 is `9ddb86e96efb029b2530d4ef620fff5fa44a5d678ed1f8db955677f727e9453d`. These are measured Spark-cluster telemetry with deliberately injected events, not naturally occurring faults or a dynamical simulation. No label is inferred from TSB filenames.

| Field | Meaning / audited rule |
|---|---|
| trace_name | Original native filename without extension; joins all 109 events to released archives |
| trace_type | One of five disturbed trace categories; process_failure contains driver/executor/unknown events |
| anomaly_type | Six known types plus unknown, kept separately |
| anomaly_details | CPU impact descriptor; 18 increased_processing_time, 5 no_application_impact, 3 application_crash |
| root_cause_start/end | Unix seconds, closed interval; 19 process-failure point intervals have equal endpoints |
| extended_effect_end | Best-effort consequence endpoint, not physical propagation truth; 28 missing values |
| application id | Documented native trace naming convention, not a separate CSV column |

| anomaly_type | events | traces | apps | point_rci | missing_eei |
|---|---|---|---|---|---|
| bursty_input | 29 | 6 | 4 | 0 | 1 |
| bursty_input_crash | 7 | 7 | 6 | 0 | 7 |
| cpu_contention | 26 | 6 | 6 | 0 | 5 |
| driver_failure | 9 | 8 | 7 | 9 | 0 |
| executor_failure | 10 | 8 | 7 | 10 | 0 |
| stalled_input | 16 | 4 | 4 | 0 | 3 |
| unknown | 12 | 11 | 9 | 0 | 12 |

The 28 absent EEIs comprise 7 burst-until-crash, 12 unknown, 5 CPU no-application-impact, 3 stalled-input and 1 bursty-input events. Absence is not a measured zero effect: crash truncation, no reported application effect and uncertain annotation are distinct. There are no reversed intervals or duplicate ground-truth rows. Durations are elapsed seconds; a zero duration RCI can still contain one native observation.

Two closed-interval overlap pairs touch at a single boundary; none overlap for positive elapsed time. The event-wise audit retains both rows and marks shared times ineligible for unique phase attribution. Original scalar label assignment can overwrite the earlier type at these shared instants.

| trace | event_a | event_b | type_a | type_b | boundary_only |
|---|---|---|---|---|---|
| 2_5_1000000_87 | gt_row_067 | gt_row_075 | driver_failure | executor_failure | True |
| 8_5_1000000_83 | gt_row_063 | gt_row_098 | driver_failure | unknown | True |

Seven metadata-selected native archives (43,256,084 compressed bytes) were inspected for CSV hashes/schema/timestamps and three diagnostic raw channels. They contain 2,283 features. All seven have timestamp gaps; 9_5_1000000_84 also contains one duplicate timestamp. This audit counts observed unique times without imputing detector input. Only 7/93 traces and 9/109 events have renewed raw inspection; remaining raw files and complete feature finiteness are unknown.

| trace | rows | unique_timestamps | duplicate_timestamp_rows | non_1s_steps | max_step |
|---|---|---|---|---|---|
| 1_2_100000_68 | 2936 | 2936 | 0 | 10 | 2 |
| 4_5_1000000_90 | 3621 | 3621 | 0 | 12 | 2 |
| 9_5_1000000_84 | 5918 | 5917 | 1 | 20 | 4 |
| 5_4_1000000_82 | 4218 | 4218 | 0 | 15 | 2 |
| 5_0_100000_37 | 3581 | 3581 | 0 | 10 | 2 |
| 5_0_50000_39 | 2721 | 2721 | 0 | 7 | 2 |
| 9_0_100000_3 | 3338 | 3338 | 0 | 8 | 2 |

All three checked process-failure RCIs have exactly one observed native timestamp. The checked burst-until-crash trace ends exactly at its RCI end, has no EEI and no observed recovery; an unknown event in the CPU trace also ends at the recording boundary. Right-censoring is retained.

| event_id | trace | anomaly_type | rci_observations | eei_observations | rci_point | missing_eei | combined_end_minus_trace_end | recovery_300s_right_censored |
|---|---|---|---|---|---|---|---|---|
| gt_row_032 | 1_2_100000_68 | bursty_input_crash | 2314 | 0 | False | True | 0 | True |
| gt_row_079 | 4_5_1000000_90 | executor_failure | 1 | 94 | True | False | -1821 | False |
| gt_row_105 | 4_5_1000000_90 | unknown | 533 | 0 | False | True | -2584 | False |
| gt_row_064 | 9_5_1000000_84 | driver_failure | 1 | 64 | True | False | -3338 | False |
| gt_row_073 | 9_5_1000000_84 | executor_failure | 1 | 326 | True | False | -4997 | False |
| gt_row_099 | 9_5_1000000_84 | unknown | 116 | 0 | False | True | -2919 | False |
| gt_row_062 | 5_4_1000000_82 | cpu_contention | 598 | 346 | False | False | -1505 | False |
| gt_row_106 | 5_4_1000000_82 | unknown | 155 | 0 | False | True | -3976 | False |
| gt_row_107 | 5_4_1000000_82 | unknown | 224 | 0 | False | True | 0 | True |

Original [SparkManager](https://github.com/exathlonbenchmark/exathlon/blob/4101f6087f902fa150e392b65c957976faa84e40/src/data/spark_manager.py) labels the closed union from RCI start through EEI end (or RCI end when absent), ignoring no_application_impact when os.only is requested. [Source defaults](https://github.com/exathlonbenchmark/exathlon/blob/4101f6087f902fa150e392b65c957976faa84e40/src/utils/spark.py) and the reproduction notebook use 15s pre/data/label sampling and trace_scaling. Labels use categorical max in each bin and features use aggregated values plus fills; bin timestamp and type id do not preserve phase identity. The higher enum is not anomaly severity.

| event_id | anomaly_type | native_rci_observations | rci_occupied_bins | mixed_rci_eei_bins |
|---|---|---|---|---|
| gt_row_032 | bursty_input_crash | 2314 | 156 | 0 |
| gt_row_079 | executor_failure | 1 | 1 | 1 |
| gt_row_105 | unknown | 533 | 36 | 0 |
| gt_row_064 | driver_failure | 1 | 1 | 1 |
| gt_row_073 | executor_failure | 1 | 1 | 1 |
| gt_row_099 | unknown | 116 | 9 | 0 |
| gt_row_062 | cpu_contention | 598 | 41 | 1 |
| gt_row_106 | unknown | 155 | 11 | 0 |
| gt_row_107 | unknown | 224 | 16 | 0 |

[DIVAD loader](https://github.com/exathlonbenchmark/divad/blob/47a0893eff719863e96e1156ea9ed1b4a9b92209/exathlon/data/managers/spark_manager.py) explicitly resolves duplicate/missing times with 1s max aggregation and ffill/bfill. Missing executor/OS handling and original trace scaling can use later observations. These transformations must have causal availability timestamps before any early-detection claim. DIVAD additionally supports include_extended_effect=False and different os_only relabeling, which are different ground-truth targets.

Source discrepancies remain visible: live official Dataset wiki says 6 stalled-input instances, while raw GT contains 16. The downloaded wiki is unversioned, hashed and not allowed to replace GT. DIVAD metadata contains an executor exception under renamed 5_5_1500000_92, conflicting with its raw-name mapping; executors for 5_5_1000000_92 stay unknown. The default YAML removal comment disagrees with actual REMOVAL_OPTIONS (source code removes 1_0_10000_17). No silent source correction is performed.
