# P3-A source/channel and healthy response support audit

**Audit complete, pending review.** Scope: [Issue #15 GO5981480803](https://github.com/kuo1234/xlstm_anomaly/issues/15#issuecomment-5981480803), [#16 GO5981482755](https://github.com/kuo1234/xlstm_anomaly/issues/16#issuecomment-5981482755). Everything executed on ssh kuo; no raw download to local, no detector, predictor, new score, feature selection or controller.

## Source and chronology

Source is official [Extended TEP v1](https://doi.org/10.11583/DTU.13385936.v1), TEP_Mode1.h5. Whole HDF5 not acquired/hash-verified; existing exact official ranges total 46,202,880 bytes (44.0625 MiB), with every block hash in source_inventory.json. Previously extracted healthy arrays are hash-verified individually; their hashes do not imply a whole-file hash.

The [author's thesis](https://backend.orbit.dtu.dk/ws/portalfiles/portal/262630763/Thesis_Christopher_Clarc_Reinartz.pdf), Appendix A.3.2–A.3.4, directly gives the sampling/normal-prefix convention and Tables A.4–A.6 define channels, units and measurement/internal distinctions. PDF SHA256: 5d4e73b7d676ae77517e509d2f6653a75d151f256d2507bd65746b6d78723d67. README, thesis text, API snapshot and prior inspection hashes are in source_evidence.json.

Only two small official reference archives were acquired remotely: Ricker's tables.zip and temexd_mod.zip, linked by the [author archive](https://depts.washington.edu/control/LARRY/TE/download.html). They corroborate original ordinal roles and analyzer code; they are not a substituted2021 generator. Exact hashes are recorded; no simulator executed. Python cannot decode tables.zip legacy compression, so unzip -p inspected the same official bytes, without a mirror.

Config/diagnostic code/source schema were committed and pushed as 075b4fc1d13da84eb875c77943f4831dda4ef776 before numerical healthy access. Remote HEAD was verified identical at execution. All58 existing healthy arrays were subsequently read once for numerical support diagnostics; source profiles/attrs were re-read from the cached HDF5 for provenance only. No fault/event observation array was numerically loaded or analyzed by P3-A. Protected P2 integrity verification does hash old raw event/score/checkpoint bytes; this separate byte-only access is listed explicitly in the access log and does not interpret outcomes. Source profiles and historical metadata ARE exposed; this audit does not claim new global label blindness. audit_access_log.json records both kinds of access, actual hashes, UTCs and the earlier document-inspection timestamp limitation. The old P2 score/checkpoint seal was re-verified unchanged.

## Original channel contract

channel_manifest.json has all54 raw columns and keeps duplicate display names distinguished by zero-based raw index. raw0=Time(h), excluded from old P2 numerical inputs; raw1–41=41 measurements; raw42–53=12 manipulated variables. Roles/order/units are verified directly against author Table A.4 p78, not inferred from names. Observation index=raw index−1. Table A.5 p79 establishes32 additional measurement points with units; Table A.6 p80 instead marks idv_monitoring as noise-free internal simulator values.

The existing53 columns are recorded simulation values. No inspected evidence establishes deployed instrument availability, same-tick ordering, telemetry latency or operator authorization. A logged manipulated value is not a verified authorized exogenous command; its relation to physical actuator feedback vs demanded value is UNKNOWN. Past logged histories could support a future explicitly delayed observation contract, but P3-A enables no inputs.

Observed manipulated value ≠ authorized setpoint/command ≠ simulator event profile. setpoint_init, idv_init, event ID/path/time_info/run attrs remain evaluator/source-curator metadata. A3x12 before/after/time profile contains future schedule information and is not a runtime command log.

## Additional inventory and alignment

- additional_meas exists in previously inspected official runs and has32 labels, none Time. Its sampling grid/alignment cannot be established by name or matching row count. The58 healthy groups' extra dataset headers are outside current range cache: 116 cache-only metadata requests were denied, zero network bytes. source_inventory.json marks these schemas UNKNOWN_CACHE_MISS; no silent range acquisition or fallback occurred.
- economic_data has five variables in the README: operating cost, production setpoint, actual production, quality setpoint, actual quality. Stored column-to-name order, units, computation semantics and online availability are UNKNOWN. Listed ordinal order is provisional, never activated as input. Existing SP/mode examples have2000 process/additional rows but2001 economic rows. No timestamp join was verified.
- Alarm, operator authorization, true command and controller-update streams: UNKNOWN in the current source inspection, not a claim of global absence. The old simulator archive having a controller is not evidence that this dataset logs its online context.
- idv_monitoring is documented for random-disturbance families, not numerically inspected in P3-A; evaluator-only internal values.
- No new source above is an enabled model input. Any future use requires protocol amendment and independent alignment/runtime/provenance verification. Matching lengths or reconstructing a future profile cannot replace those checks.

## Healthy source coverage

All58 physical source runs are healthy100–157, native seeds all distinct: train100–149(50), validation150–153(4), calibration154–157(4). All saved arrays600×53, t=0...29.95h, nominal eligibility[0,30), source event not active before30h. That is30h nominal record coverage,29.95h elapsed span per run; train30,000 rows/1,500 nominal run-hours, all roles34,800 rows/1,740 run-hours. Run-hours and rows are not independent N.

Cached source profile checks confirm Mode1 and one identical initial setpoint vector across all58, with no setpoint change inside these runs. No different normal operating level or legitimate command-transition training window exists in the cohort. **healthy response support insufficient for transition modelling**.

There are58 unique full-array hashes, no exact full duplicate, no duplicate native seed, no common exact8/128/600-row prefix. All58 share exactly the first53-vector at t0; all1,653 pairs' longest exact prefix is one row, including cross-role pairs. This common initialized point must be disclosed for future splitting. Unique seed/byte checks do not prove stochastic independence or unseen operating-condition diversity.

## Variation: local closed-loop histories, not commanded-transition evidence

Every run has the same exact constant observation indices45,49,52 (raw46 Recycle,50 Steam,53 Agitator). The frozen numerical near-constant flag std/max(abs(mean),1)<1e−6 identifies those same three. It is an explicitly unit-dependent numerical convention, not physical importance, and no column was removed. Train scale floor0.02 affects indices [0, 8, 9, 20, 36, 37, 38, 45, 48, 49, 52]; it is separately an inherited scaling convention, with no clipping or feature selection.

Nine manipulated columns vary. Across the50 train runs their median within-run standard deviations range0.01956–1.62901 percentage points. Such variation can describe closed-loop adjustment/noise response; its source is not proven exogenous or persistently exciting. It cannot establish the effect of an authorized command.

| Raw / observation index | Source name | Pooled train SD (%) | Median run SD (%) | Median run max−min (%) |
|---|---|---:|---:|---:|
| 42 / 41 | D feed | 0.103456 | 0.092697 | 0.529698 |
| 43 / 42 | E Feed | 0.110657 | 0.102605 | 0.588058 |
| 44 / 43 | A Feed | 0.544965 | 0.521848 | 3.112954 |
| 45 / 44 | A and C Feed | 0.096411 | 0.096449 | 0.572872 |
| 46 / 45 | Recycle | 0.000000 | 0.000000 | 0.000000 |
| 47 / 46 | Purge | 1.215297 | 1.176255 | 6.226432 |
| 48 / 47 | Separator | 0.030754 | 0.029041 | 0.168816 |
| 49 / 48 | Stripper | 0.019722 | 0.019563 | 0.120368 |
| 50 / 49 | Steam | 0.000000 | 0.000000 | 0.000000 |
| 51 / 50 | Reactor Coolant | 0.092326 | 0.091689 | 0.551868 |
| 52 / 51 | Condenser Coolant | 1.622917 | 1.629012 | 9.627802 |
| 53 / 52 | Agitator | 0.000000 | 0.000000 | 0.000000 |

All41 measurement columns vary within each healthy run; per-channel means/min/max/std/step-RMS/autocorrelations are stored for every run in healthy_support_manifest.json. Units differ, so a pooled cross-channel SD is not a physical excitation scale. These measurements alone do not distinguish measurement noise, plant variation, feedback correction and unlogged commands.

## Lagged spectrum and sampling

All53 channels kept. Fixed histories1/8/16 steps were recorded before diagnostic, covering3/24/48 minutes. Each row is[x(t−1),...,x(t−p)] and stays within a physical run; no target, coefficient, forecast or anomaly statistic was computed. Scales fit only train50; validation/calibration never fit scaling or pooled spectrum. Per-run history1 spectra use the same train scale but center each run for a descriptive within-run spectrum.

| History steps / span | Train regressor shape | Entropy effective rank | Stable rank | Eigen ratio>1e−6 count | Eigen ratio>1e−4 count |
|---|---:|---:|---:|---:|---:|
| 1 / 3 min | 29950 × 53 | 37.177 | 11.409 | 50 | 50 |
| 8 / 24 min | 29600 × 424 | 163.878 | 13.048 | 398 | 386 |
| 16 / 48 min | 29200 × 848 | 284.105 | 14.282 | 791 | 739 |

Full singular/eigen spectra and frozen sensitivity counts are stored. Gram eig squares conditioning; near-null estimates are limited by the explicit float64 roundoff bound. Constants stay in the regressor, with centered constant columns explicitly zeroed. History1 effective rank per train run ranges32.098–37.239. High spectral rank is not a plant-identification certificate: measurement noise and closed-loop fluctuations can populate many directions without transitions or independent command excitation.

Saved interval3min has an ideal uniform-sampling Nyquist lower period6min. This is an aliasing bound, not an empirical identified plant timescale or guaranteed recoverable6min response. Faster effects, same-tick direction/order and unknown latency cannot be resolved; holding/interpolation does not invent missing information. Reference2015 analyzer code advances gas every0.1h and product every0.25h with a previous-value delay;2021 generator equivalence remains UNKNOWN. Actual saved healthy gas composition raw23–36 has unchanged adjacent-value fraction0.500835 and product raw37–41 has0.801336 for every train run, consistent with slower held analyzer updates. Continuous measurement raw1–22 has zero exact unchanged-step fraction; this does not prove latency-free dynamics.

Author A.3.2 discusses24–48h responses to legitimate setpoint changes and its40h transition convention. These descriptive source timescales are outside the current48min audit history spans and, more critically, wholly absent from the healthy30h pre-event training intervals. The lags were not selected to capture those responses; no best-lag search was done.

## Physical run ledger

Each entry below is a physical simulator realization/native seed, not a model seed or sliding window. Source path, SHA256, modes, per-column stats and exact prefix relationships are in the machine-readable manifest. No significance test treats rows or lags as independent N.

| Run | Role | Native seed | Points / elapsed duration | History1 effective rank |
|---|---|---:|---:|---:|
| healthy100 | train | 4378 | 600 / 29.95 h | 32.639 |
| healthy101 | train | 22198 | 600 / 29.95 h | 34.388 |
| healthy102 | train | 35229 | 600 / 29.95 h | 35.237 |
| healthy103 | train | 49091 | 600 / 29.95 h | 36.296 |
| healthy104 | train | 17906 | 600 / 29.95 h | 35.367 |
| healthy105 | train | 5766 | 600 / 29.95 h | 34.498 |
| healthy106 | train | 60045 | 600 / 29.95 h | 35.923 |
| healthy107 | train | 49764 | 600 / 29.95 h | 35.485 |
| healthy108 | train | 41875 | 600 / 29.95 h | 37.000 |
| healthy109 | train | 37504 | 600 / 29.95 h | 36.865 |
| healthy110 | train | 38228 | 600 / 29.95 h | 34.399 |
| healthy111 | train | 48786 | 600 / 29.95 h | 36.838 |
| healthy112 | train | 44179 | 600 / 29.95 h | 36.169 |
| healthy113 | train | 32046 | 600 / 29.95 h | 32.644 |
| healthy114 | train | 45230 | 600 / 29.95 h | 36.917 |
| healthy115 | train | 40537 | 600 / 29.95 h | 35.816 |
| healthy116 | train | 30302 | 600 / 29.95 h | 35.214 |
| healthy117 | train | 42868 | 600 / 29.95 h | 36.277 |
| healthy118 | train | 7845 | 600 / 29.95 h | 34.058 |
| healthy119 | train | 16171 | 600 / 29.95 h | 37.239 |
| healthy120 | train | 25324 | 600 / 29.95 h | 34.404 |
| healthy121 | train | 19664 | 600 / 29.95 h | 35.239 |
| healthy122 | train | 14036 | 600 / 29.95 h | 36.666 |
| healthy123 | train | 44424 | 600 / 29.95 h | 37.044 |
| healthy124 | train | 15297 | 600 / 29.95 h | 36.260 |
| healthy125 | train | 41354 | 600 / 29.95 h | 36.300 |
| healthy126 | train | 9156 | 600 / 29.95 h | 35.646 |
| healthy127 | train | 42553 | 600 / 29.95 h | 35.422 |
| healthy128 | train | 14804 | 600 / 29.95 h | 33.460 |
| healthy129 | train | 1559 | 600 / 29.95 h | 33.506 |
| healthy130 | train | 18550 | 600 / 29.95 h | 36.596 |
| healthy131 | train | 19259 | 600 / 29.95 h | 36.646 |
| healthy132 | train | 42826 | 600 / 29.95 h | 32.152 |
| healthy133 | train | 46127 | 600 / 29.95 h | 36.528 |
| healthy134 | train | 12838 | 600 / 29.95 h | 35.549 |
| healthy135 | train | 28915 | 600 / 29.95 h | 34.520 |
| healthy136 | train | 16364 | 600 / 29.95 h | 35.216 |
| healthy137 | train | 23730 | 600 / 29.95 h | 37.202 |
| healthy138 | train | 37155 | 600 / 29.95 h | 35.528 |
| healthy139 | train | 33542 | 600 / 29.95 h | 35.827 |
| healthy140 | train | 3195 | 600 / 29.95 h | 36.034 |
| healthy141 | train | 45092 | 600 / 29.95 h | 35.343 |
| healthy142 | train | 36047 | 600 / 29.95 h | 36.070 |
| healthy143 | train | 22165 | 600 / 29.95 h | 32.098 |
| healthy144 | train | 8618 | 600 / 29.95 h | 35.791 |
| healthy145 | train | 20797 | 600 / 29.95 h | 35.649 |
| healthy146 | train | 36 | 600 / 29.95 h | 35.400 |
| healthy147 | train | 60047 | 600 / 29.95 h | 33.955 |
| healthy148 | train | 28216 | 600 / 29.95 h | 36.756 |
| healthy149 | train | 3254 | 600 / 29.95 h | 34.890 |
| healthy150 | validation | 19335 | 600 / 29.95 h | 35.783 |
| healthy151 | validation | 25249 | 600 / 29.95 h | 36.445 |
| healthy152 | validation | 43429 | 600 / 29.95 h | 36.288 |
| healthy153 | validation | 60048 | 600 / 29.95 h | 35.893 |
| healthy154 | calibration | 37286 | 600 / 29.95 h | 35.200 |
| healthy155 | calibration | 42397 | 600 / 29.95 h | 36.327 |
| healthy156 | calibration | 11855 | 600 / 29.95 h | 32.053 |
| healthy157 | calibration | 16877 | 600 / 29.95 h | 36.041 |

Truth boundaries and a conditional future eligibility contract are in target_semantics.md and PROBE_READINESS.md. All original input data/arrays/code sealed by P2 remain unchanged.
