# D0 data composition and provenance — 2026-10-06

Primary snapshot: [StrAD commit 7078876](https://github.com/magaliparrino/StrAD/blob/7078876bbd9398481a65c22b7689702ce9e0d558/README.md). All result/metadata inputs have180 unique matching file keys; archive source checksums and per-file SHA256 are in provenance. The paper-linked Zenodo concept record20310651 resolves to version20310652 (6,988,090-byte source ZIP); fifteen audited data/code entries match pinned main byte-for-byte. The archive root identifies d2c66c1; no model-score vectors were found in either inventory. These are publication artifacts, not run manifests.

The independently pinned official TSB file lists reconcile the paper’s200 total with20 tuning and180 evaluation files. The release matches the evaluation list exactly, the lists are disjoint and their union is the200-file list. Family totals for the paper’s whole pool should not be copied into this evaluation-only atlas. Paper Table2 drift-family counts also differ for MSL (paper0, release1) and SWaT (paper1, release2); the released CD.csv defines this audit subset, and the discrepancy is not silently repaired.

| origin | CD | series |
|---|---|---|
| MEASURED_FAMILY_DOCUMENTED | 0 | 105 |
| MEASURED_FAMILY_DOCUMENTED | 1 | 46 |
| SIMULATED_SOURCE | 1 | 28 |
| UNKNOWN_SOURCE | 1 | 1 |

MEASURED_SOURCE_ONLY means **documented measured family**, not individually verified native origin. The official TSB catalog describes ECG, telemetry, servers, human sensors and physical testbeds; current family grouping preserves that broad provenance only. CreditCard remains UNKNOWN_SOURCE because its catalog entry points to network-intrusion data, conflicting with its family identity. No nearby dataset is substituted. GHL and CATSv2 are simulation-origin even though some benchmark descriptions call all series real-world.

[GHL creator paper](https://arxiv.org/abs/1612.06676v2) describes a Modelica gasoil-plant simulation; [CATS v2 creator record](https://zenodo.org/records/8338435) describes a simulated dynamical system. The historical [TSB catalog evidence](../../reports/phase_a/TSB_source_catalog.html) and source URLs are retained; source-family measurement status does not establish legitimate drift or native fault semantics.

All28 simulation-origin rows are in CD=1. Removing them and the one unknown CreditCard row leaves151 measured-family rows,46 drift and105 non-drift. Thus unconditioned drift/non-drift comparisons change composition. There are17 released families overall and13 in drift; family means are an audit aggregation, not proof of iid independence.

| family | n | origin | portfolio_gap | oracle_streaming_wins | portfolio_streaming_wins |
|---|---|---|---|---|---|
| CATSv2 | 5 | SIMULATED_SOURCE | -0.08191 | 0 | 0 |
| CreditCard | 1 | UNKNOWN_SOURCE | -0.00764 | 0 | 0 |
| Daphnet | 1 | MEASURED_FAMILY_DOCUMENTED | -0.07242 | 0 | 0 |
| Exathlon | 5 | MEASURED_FAMILY_DOCUMENTED | -0.02934 | 1 | 2 |
| GECCO | 1 | MEASURED_FAMILY_DOCUMENTED | -0.11961 | 0 | 0 |
| GHL | 23 | SIMULATED_SOURCE | -0.00304 | 5 | 17 |
| LTDB | 1 | MEASURED_FAMILY_DOCUMENTED | -0.00527 | 0 | 0 |
| MSL | 1 | MEASURED_FAMILY_DOCUMENTED | 0.13246 | 1 | 1 |
| OPPORTUNITY | 7 | MEASURED_FAMILY_DOCUMENTED | 0.03171 | 4 | 5 |
| SMAP | 5 | MEASURED_FAMILY_DOCUMENTED | -0.00160 | 3 | 2 |
| SMD | 15 | MEASURED_FAMILY_DOCUMENTED | -0.04664 | 4 | 7 |
| SWaT | 2 | MEASURED_FAMILY_DOCUMENTED | -0.25569 | 0 | 0 |
| TAO | 8 | MEASURED_FAMILY_DOCUMENTED | -0.16217 | 0 | 1 |

The historical Phase A v4 audit covers75 drift files. Their dimensions, lengths and first-anomaly indices exactly match current released metadata. Historical raw/feature/label hashes, finite/binary checks and contamination counts are not renewed byte inspections here. Among those75,15 native SMD mappings were verified and60 unresolved. The other105 raw traces are not inspected. Do not claim180 verified native identities.

One known exact-feature duplicate group contains Exathlon188/190/198/199; no more than one may enter sentinels. Collapsing known duplicate groups is a sensitivity check; treating all remaining files as different does not certify physical independence. Source catalog family labels can include multiple sensors, crops or related source sessions.

Train cutoffs and first-anomaly indices are parsed only under the documented **TSB released filename convention** and checked against the historical75-file audit, not interpreted as native source training boundaries. This is metadata-derived context. Ten historically audited drift training prefixes contain anomalies; the StrAD task is unsupervised and permits initial-batch contamination. Do not impose an undocumented clean-prefix claim.

All180 metadata rows satisfy anomaly_ratio=anomaly_len/ts_len and avg_anomaly_len=anomaly_len/num_anomaly. Counts describe released label runs; anomaly physics, severity and event semantics are not established. CD/type are series-level, four nonexclusive tags, and cannot be converted into exact onset/recovery truth. High feature count also does not establish effective independent dimensionality (command/constant channels are possible).

Current raw acquisition is out of scope. No bulk benchmark data download, restricted-source bypass, raw-label experiment or model run occurred. The small paper-linked source archive was inspected only for source/evidence availability.
