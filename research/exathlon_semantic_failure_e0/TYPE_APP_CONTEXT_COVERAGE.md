# Type × app × context coverage

Unit: annotation events nested in native traces, applications and shared cluster executions. Repeated events within one run and concurrent apps are not independent scientific replications. Shared-start candidates are preserved in results/shared_start_candidates.csv; unequal starts can still share a batch. Source families from D0 do not substitute for native identity here.

| anomaly_type | app | events | traces | rci_median_seconds | rci_min_seconds | rci_max_seconds | eei_count | eei_median_seconds | point_rci_events | context_count | small_event_stratum |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bursty_input | 2 | 3 | 1 | 919.000 | 919 | 929 | 3 | 61.000 | 0 | 1 | False |
| bursty_input | 4 | 9 | 1 | 1869.000 | 869 | 1884 | 9 | 62.000 | 0 | 1 | False |
| bursty_input | 5 | 12 | 3 | 899.000 | 894 | 1789 | 11 | 67.000 | 0 | 2 | False |
| bursty_input | 6 | 5 | 1 | 904.000 | 904 | 904 | 5 | 68.000 | 0 | 1 | False |
| bursty_input_crash | 1 | 1 | 1 | 2321.000 | 2321 | 2321 | 0 | N/A / unknown | 0 | 1 | True |
| bursty_input_crash | 2 | 1 | 1 | 1660.000 | 1660 | 1660 | 0 | N/A / unknown | 0 | 1 | True |
| bursty_input_crash | 3 | 2 | 2 | 626.500 | 454 | 799 | 0 | N/A / unknown | 0 | 2 | True |
| bursty_input_crash | 5 | 1 | 1 | 958.000 | 958 | 958 | 0 | N/A / unknown | 0 | 1 | True |
| bursty_input_crash | 9 | 1 | 1 | 3455.000 | 3455 | 3455 | 0 | N/A / unknown | 0 | 1 | True |
| bursty_input_crash | 10 | 1 | 1 | 5247.000 | 5247 | 5247 | 0 | N/A / unknown | 0 | 1 | True |
| cpu_contention | 1 | 6 | 1 | 800.000 | 400 | 1500 | 5 | 59.000 | 0 | 1 | False |
| cpu_contention | 3 | 1 | 1 | 600.000 | 600 | 600 | 1 | 74.000 | 0 | 1 | True |
| cpu_contention | 5 | 1 | 1 | 600.000 | 600 | 600 | 1 | 347.000 | 0 | 1 | True |
| cpu_contention | 8 | 6 | 1 | 800.000 | 400 | 1500 | 4 | 67.500 | 0 | 1 | False |
| cpu_contention | 9 | 6 | 1 | 800.000 | 400 | 1500 | 5 | 82.000 | 0 | 1 | False |
| cpu_contention | 10 | 6 | 1 | 800.000 | 400 | 1500 | 5 | 65.000 | 0 | 1 | False |
| driver_failure | 2 | 2 | 1 | 0.000 | 0 | 0 | 2 | 63.000 | 2 | 1 | True |
| driver_failure | 3 | 1 | 1 | 0.000 | 0 | 0 | 1 | 63.000 | 1 | 1 | True |
| driver_failure | 5 | 2 | 2 | 0.000 | 0 | 0 | 2 | 63.500 | 2 | 2 | True |
| driver_failure | 6 | 1 | 1 | 0.000 | 0 | 0 | 1 | 63.000 | 1 | 1 | True |
| driver_failure | 8 | 1 | 1 | 0.000 | 0 | 0 | 1 | 69.000 | 1 | 1 | True |
| driver_failure | 9 | 1 | 1 | 0.000 | 0 | 0 | 1 | 68.000 | 1 | 1 | True |
| driver_failure | 10 | 1 | 1 | 0.000 | 0 | 0 | 1 | 63.000 | 1 | 1 | True |
| executor_failure | 1 | 1 | 1 | 0.000 | 0 | 0 | 1 | 182.000 | 1 | 1 | True |
| executor_failure | 2 | 3 | 2 | 0.000 | 0 | 0 | 3 | 1612.000 | 3 | 2 | False |
| executor_failure | 3 | 1 | 1 | 0.000 | 0 | 0 | 1 | 163.000 | 1 | 1 | True |
| executor_failure | 4 | 1 | 1 | 0.000 | 0 | 0 | 1 | 95.000 | 1 | 1 | True |
| executor_failure | 5 | 2 | 1 | 0.000 | 0 | 0 | 2 | 454.500 | 2 | 1 | True |
| executor_failure | 8 | 1 | 1 | 0.000 | 0 | 0 | 1 | 150.000 | 1 | 1 | True |
| executor_failure | 9 | 1 | 1 | 0.000 | 0 | 0 | 1 | 327.000 | 1 | 1 | True |
| stalled_input | 6 | 4 | 1 | 899.000 | 857 | 900 | 3 | 64.000 | 0 | 1 | False |
| stalled_input | 8 | 4 | 1 | 899.000 | 866 | 900 | 3 | 77.000 | 0 | 1 | False |
| stalled_input | 9 | 4 | 1 | 899.000 | 899 | 900 | 4 | 75.500 | 0 | 1 | False |
| stalled_input | 10 | 4 | 1 | 899.000 | 887 | 900 | 3 | 73.000 | 0 | 1 | False |
| unknown | 1 | 1 | 1 | 478.000 | 478 | 478 | 0 | N/A / unknown | 0 | 1 | True |
| unknown | 2 | 1 | 1 | 491.000 | 491 | 491 | 0 | N/A / unknown | 0 | 1 | True |
| unknown | 3 | 2 | 2 | 139.500 | 139 | 140 | 0 | N/A / unknown | 0 | 2 | True |
| unknown | 4 | 1 | 1 | 534.000 | 534 | 534 | 0 | N/A / unknown | 0 | 1 | True |
| unknown | 5 | 3 | 2 | 224.000 | 154 | 583 | 0 | N/A / unknown | 0 | 2 | False |
| unknown | 6 | 1 | 1 | 643.000 | 643 | 643 | 0 | N/A / unknown | 0 | 1 | True |
| unknown | 8 | 1 | 1 | 59.000 | 59 | 59 | 0 | N/A / unknown | 0 | 1 | True |
| unknown | 9 | 1 | 1 | 115.000 | 115 | 115 | 0 | N/A / unknown | 0 | 1 | True |
| unknown | 10 | 1 | 1 | 108.000 | 108 | 108 | 0 | N/A / unknown | 0 | 1 | True |

Every known type spans multiple apps, so type is not a deterministic function of app. Many type×app cells have only one or two events and cannot be independent scientific strata. Resource configuration is more severely tied to trace type: documented memory is usually 30GB for normal versus 9/15GB for disturbed runs; executor counts and input-rate corrections also change. The context inventory uses actual DIVAD declarations, preserves the one executor conflict and distinguishes nominal filenames from corrected rates. It is documentation, not independently reverified cluster settings.

| app | undisturbed_runs | disturbed_runs | documented_normal_contexts | documented_test_contexts | disturbed_traces_with_exact_normal_context | disturbed_traces_with_unknown_context | disturbed_traces_with_matching_input_rate_only |
|---|---|---|---|---|---|---|---|
| 1 | 6 | 3 | 4 | 3 | 0 | 0 | 1 |
| 2 | 3 | 4 | 2 | 4 | 0 | 0 | 1 |
| 3 | 4 | 4 | 2 | 4 | 0 | 0 | 0 |
| 4 | 6 | 2 | 2 | 2 | 0 | 0 | 1 |
| 5 | 8 | 7 | 2 | 6 | 0 | 1 | 2 |
| 6 | 12 | 3 | 5 | 3 | 0 | 0 | 0 |
| 7 | 7 | 0 | 2 | 0 | 0 | 0 | 0 |
| 8 | 0 | 3 | 0 | 3 | 0 | 0 | 0 |
| 9 | 6 | 4 | 4 | 3 | 0 | 0 | 0 |
| 10 | 7 | 4 | 3 | 3 | 0 | 0 | 0 |

No one of the 33 disturbed traces with known full context has an exact same-app normal tuple (corrected input rate,batch interval,executors,memory); the remaining disturbed trace has uncertain executor context. A failed exact joint match is not proof that the application lacks all useful normal support: input-rate-only matches exist. Application8 has no undisturbed runs; app7 has no disturbed runs. Original all-app experiments exclude both and cover eight apps, not all ten.

Original dataset split puts whole undisturbed runs in train and disturbed runs in test; its modeling split subsequently uses stratified windows with seed21 and normal validation/modeling-test proportions .15/.15. DIVAD has unsupervised/generalization/weakly setups and different time/random validation policies; the YAML alone is not a run manifest. E0 performs no train/validation/test split and no threshold fitting.

Bounded native normal examples have observed raw-channel location/scale differences, shown below for diagnostic context only. These are raw telemetry, **not detector scores** and not evidence of calibration dominance. The three selected normal runs do not establish the distribution across all 59 normal runs; −1 sentinel values are counted and excluded from these descriptive nonnegative raw statistics.

| trace | metric | finite_nonnegative_count | minus_one_sentinel_count | median | q25 | q75 |
|---|---|---|---|---|---|---|
| 5_0_100000_37 | StreamingMetrics_streaming_lastCompletedBatch_processingDelay_value | 3568 | 13 | 1073 | 829 | 1287 |
| 5_0_100000_37 | StreamingMetrics_streaming_lastCompletedBatch_schedulingDelay_value | 3568 | 13 | 0 | 0 | 1 |
| 5_0_100000_37 | node5_CPU001_Idle% | 3572 | 9 | 100 | 100 | 100 |
| 5_0_50000_39 | StreamingMetrics_streaming_lastCompletedBatch_processingDelay_value | 2709 | 12 | 518 | 473 | 719 |
| 5_0_50000_39 | StreamingMetrics_streaming_lastCompletedBatch_schedulingDelay_value | 2709 | 12 | 0 | 0 | 1 |
| 5_0_50000_39 | node5_CPU001_Idle% | 2712 | 9 | 98 | 91 | 100 |
| 9_0_100000_3 | StreamingMetrics_streaming_lastCompletedBatch_processingDelay_value | 3321 | 17 | 700 | 644 | 770 |
| 9_0_100000_3 | StreamingMetrics_streaming_lastCompletedBatch_schedulingDelay_value | 3321 | 17 | 0 | 0 | 0 |
| 9_0_100000_3 | node5_CPU001_Idle% | 3329 | 9 | 96 | 95 | 97 |

Type footprint hypotheses are documented interventions, not empirical modern-detector failures: burst/stall change input supply; CPU contention changes host resource availability and sometimes has no application impact; driver/executor injections are instantaneous and consequences persist; unknown has no known intervention. F4 needs score/feature attribution with context and crash controls before calling any footprint observed.
