# Dataset Audit: Machine-Data Forecasting Under Long-Horizon Drift

_Audit date: 2026-09-29. Prepared for thesis scoping — online/test-time adaptation of multivariate forecasters under real drift (Direction 2), and retrieval-memory forecasting across recurring operating regimes (Direction 3)._

## Method

Reachability and licence metadata were checked with lightweight HTTP HEAD/GET requests and, where available, the host's own REST metadata API (Zenodo `/api/records/<id>`, UCI `/api/dataset?id=<id>`). No file over ~20 MB was downloaded. The default network sandbox blocks most external hosts; the following domains were individually requested and granted for this audit: `zenodo.org`, `archive.ics.uci.edu`, `www.nasa.gov`, `data.dtu.dk`, `edp.com`, `opendata-renewables.engie.com`. `kaggle.com`, `dataverse.harvard.edu`, and the NASA PHM S3 bucket were **not** requested (a deviation, declared below) — any dataset that could only be checked through those hosts is marked PROVISIONAL / NOT VERIFIED rather than confirmed.

## Ranked recommendations (top 5 for a master's thesis)

- 1. CARE to Compare / EDP-derived Wind Turbine SCADA (Zenodo 14006163) — 36 turbines across 3 real farms, 89 turbine-years, the most detailed public fault labeling of any open wind dataset; best combined fit for both long-horizon drift (direction 2) and fleet retrieval-memory (direction 3). Caveat: CC-BY-SA share-alike licence and 5.5GB size (subsample for a thesis).
- 2. Kelmarsh + Penmanshiel SCADA pair (Zenodo 7212475 / 8253010) — 6 + 14 turbines, 2016-2021+ continuous 10-min SCADA, CC-BY-4.0, small enough (~2GB combined) to be fully tractable on a laptop; widely used in the wind-forecasting literature so baselines are easy to find. Weaker fault labeling than CARE to Compare (status/event codes only, needs manual curation).
- 3. UCI Gas Turbine CO/NOx Emission Data Set (UCI 551) — small, tractable, single real gas turbine, and the original benchmark paper already reports and documents systematic multi-year drift in the pollutant outputs across the 2011-2015 span, which is rare, citable evidence of exactly the phenomenon this thesis targets. Caveat: no true datetime index, no fault labels, single unit only.
- 4. MetroPT-3 (UCI 791) plus its 2022 companion MetroPT2 (Zenodo 7766691) — a single real industrial machine (metro air-compressor) at 1Hz with documented real failure events and maintenance-report timestamps; very tractable size. Caveat: single unit, no fleet, so direction-3 (retrieval across regimes/entities) would need the two MetroPT releases to be treated as two time-separated 'eras' of the same machine rather than a true fleet.
- 5. ETT — Electricity Transformer Temperature (GitHub zhouhaoyi/ETDataset) — real physical grid transformers, clean 2-year continuous span, CC-BY-4.0, tiny size, and already the standard long-sequence-forecasting benchmark, so an online-adaptation/memory extension is easy to compare against strong published baselines. Caveat: only 2 units, and no curated drift/fault events — the 'drift' is implicit seasonal/load non-stationarity, not a labeled incident.

## Full candidate table

| # | Dataset | Domain | Entities | Span & sampling | Fault/event labels | Fleet? (dir. 3) | Real drift over months–years? (dir. 2) | Licence | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | CARE to Compare (EDP-derived Wind Turbine SCADA dataset for Early Fault Detection) | wind turbine SCADA / fleet fault detection | 36 wind turbines across 3 different real wind farms (fleet, cross-farm) | 10-minute resolution; 89 turbine-years aggregate across all units (per paper abstract) | Yes — most detailed public fault labeling of any open wind-t... | Yes | Strong | CC-BY-SA-4.0 (Zenodo record metadata) | Reachable and verified via Zenodo REST API (HTTP 2 |
| 2 | Kelmarsh Wind Farm SCADA data | wind turbine SCADA | 6 turbines (Senvion MM92), single wind farm (Kelmarsh, UK) | 10-minute SCADA, 2016-2021 (subsequent Zenodo deposits extend coverage further; check latest record version for updated end date) | Partial — status/event codes and downtime periods are logged... | Yes | Good | CC-BY-4.0 (Zenodo record metadata) | Reachable, verified via Zenodo REST API (HTTP 200) |
| 3 | Penmanshiel Wind Farm SCADA data | wind turbine SCADA | 14 turbines (Senvion MM92), single wind farm (Penmanshiel, UK) | 10-minute SCADA, 2016-2021 (extended in later record versions) | Partial — status/event codes only, no curated fault catalogu... | Yes | Good, same rationale as Kelmarsh | CC-BY-4.0 (Zenodo record metadata) | Reachable, verified via Zenodo REST API (HTTP 200) |
| 4 | ENGIE 'La Haute Borne' open wind farm SCADA data | wind turbine SCADA | 4 turbines, single farm (Meuse, France) | Historically ~2013-2020, 10-minute SCADA, 4 turbines | Not verifiable (portal down) | No/weak | Cannot recommend — dataset itself may still exist in third-party GitHub mirrors, but the source portal could not be verified reachable at this time | Unknown/unverified (portal unreachable) | UNAVAILABLE — direct connection attempt to opendat |
| 5 | MetroPT-3 (Porto Metro Air Production Unit) | rail compressor / industrial IoT | Single Air Production Unit on a single metro train (no fleet in this specific release) | 1 Hz sampling, February-August 2020 continuous (~1.52M rows per UCI API metadata) | Yes — several documented real failure events (e.g. air-leak,... | No/weak | Good | UCI ML Repository site license (CC BY 4. | Reachable, verified via UCI dataset API and page G |
| 6 | UCI Gas Turbine CO and NOx Emission Data Set | gas turbine / power generation emissions | Single gas turbine unit | Hourly-averaged readings, one file per year, 2011-2015 (5 years); 36,733 instances total (UCI API) | None — no fault/failure labels, only continuous process and ... | No/weak | Good | UCI ML Repository site license (CC BY 4. | Reachable, verified via UCI dataset API and page G |
| 7 | UCI Condition Monitoring of Hydraulic Systems | hydraulic test rig / rotating machinery | Single hydraulic test rig with deliberately varied component condition (cooler, valve, pump, accumulator) across cycles | 2,205 sixty-second measurement cycles under constant load conditions; not a continuous calendar-time series | Yes, but as discrete per-cycle condition labels (multi-class... | No/weak | Weak-to-moderate | UCI ML Repository site license (CC BY 4. | Reachable, verified via UCI dataset API and page G |
| 8 | NASA C-MAPSS Turbofan Engine Degradation Simulation | aircraft turbofan engine (simulated) | 100-260+ simulated turbofan units depending on sub-dataset (a synthetic 'fleet') | Simulated run-to-failure trajectories indexed by engine operating cycle, not calendar time; hundreds of engine units across 4 sub-datasets (FD001-FD004) | Yes — run-to-failure with known remaining-useful-life ground... | Yes | Weak for THIS thesis | NASA open data (public domain / NASA dat | NASA PCoE repository page reachable (HTTP 200) |
| 9 | N-CMAPSS (New C-MAPSS, with flight-condition time histories) | aircraft turbofan engine (simulated, higher fidelity) | ~128 simulated engine units across several sub-datasets (DS01-DS08) | Continuous flight-by-flight simulated histories (seconds resolution within each flight) until failure, across multiple flight classes | Yes, run-to-failure with RUL ground truth and health-state (... | Yes | Weak for calendar-scale drift (still simulated, no real months/years deployment gap), but the flight-condition time histories give richer within-unit non-stationarity than classic C-MAPSS | NASA open data | Landing page reachable (HTTP 200) |
| 10 | XJTU-SY Bearing Datasets / PRONOSTIA (FEMTO) / IMS Bearing Dataset | rolling-element bearings (accelerated run-to-failure test rigs) | Multiple bearings per rig (XJTU-SY: 15 bearings across 3 operating conditions; IMS: 4 bearings/test; PRONOSTIA: 17 bearings across 3 conditions) | Each individual run-to-failure test lasts minutes to at most a few days (accelerated ageing); not months/years | Yes — run-to-failure with known failure mode/time | No/weak | Poor | Research use, redistribution terms vary  | XJTU-SY GitHub mirror reachable (HTTP 200) |
| 11 | SKAB (Skoltech Anomaly Benchmark) | water-circulation test rig (industrial IoT) | Single test rig, multiple short experiment runs (some labeled as anomalous, some normal) plus an 'other' extended benchmark subset | Individual experiments last minutes to ~1 hour each; tens of separate short experiments total, not a continuous multi-month log | Yes — anomaly start/end intervals are labeled per experiment | No/weak | Poor | Permissive (repository states an open li | Reachable, verified via GitHub GET (HTTP 200) |
| 12 | Extended Tennessee Eastman Process (Reinartz/Kulahci/Ravn / Rieth simulation datasets) | chemical process plant (simulated) | Single simulated chemical plant, replicated across many independent stochastic simulation runs (not a real fleet) | Simulated continuous process runs, several hundred simulated hours per run, hundreds of independent simulation runs per fault type (Reinartz et al. extended set) or ~500 runs (Rieth et al.) | Yes, extensively — this is the standard fault-detection/diag... | No/weak | Weak for calendar-scale drift (simulated, no real deployment-time gap) but useful for controlled ablation of a proposed online-adaptation mechanism under known, labeled fault onsets | DTU Data: CC-BY-4.0-style open repositor | DTU Data page reachable (HTTP 202, dynamic content |
| 13 | Debutanizer Column / Sulfur Recovery Unit soft-sensor datasets (Fortuna et al.) | petrochemical distillation / gas-treatment soft sensing | Single unit each | Static single-run sample sequences (2,394 and ~10,081 samples respectively); no timestamps, sample index only | None | No/weak | Poor | Varies by mirror; original book dataset  | Not independently re-verified in this pass beyond  |
| 14 | ETT (Electricity Transformer Temperature) Dataset | power transformer (grid equipment) | 2 physical electricity transformers (a small 'fleet' of 2 units) | 2 years continuous, July 2016-July 2018, fixed hourly or 15-minute sampling | None | No/weak | Good | CC BY 4.0 (per repository) | Reachable, verified via GitHub GET (HTTP 200) |
| 15 | Server Machine Dataset (SMD) | compute-cluster server telemetry (not physical industrial machinery) | 28 machines (compute servers) grouped into 3 clusters | ~5 weeks of data per machine (train+test combined), fixed sampling interval | Yes — anomaly interval labels per machine | No/weak | Poor | MIT (repository code licence; data relea | Reachable, verified via GitHub GET (HTTP 200) |
| 16 | HAI (HIL-based Augmented ICS) Security Dataset | industrial control system testbed (boiler/turbine/water-treatment emulator) | Single integrated testbed combining 3 physical process emulators (boiler, turbine, water treatment) | Each released version spans on the order of days to a few weeks of continuous operation with injected attacks; not months/years | Yes — labeled attack intervals | No/weak | Poor | Available for research use per USENIX CS | Reachable, verified via GitHub GET (HTTP 200) |
| 17 | Microsoft Azure Predictive Maintenance dataset | industrial machine telemetry (vendor-stated as simulated) | 100 machines, 4 machine models (a synthetic fleet) | 1 year of hourly telemetry (per widely-cited dataset documentation) | Yes — failure and maintenance event logs | Yes | Weak | Unclear/unverified — Kaggle domain not i | NOT VERIFIED — kaggle.com was not requested/allowl |
| 18 | Alibaba Cluster Trace (2017/2018/v2022) | compute-cluster workload traces (not physical industrial machinery) | Thousands of physical machines in a data-centre cluster | 8 days (2017 trace) to ~2 months (2018 trace); newer traces exist but none span multiple years | None (workload/scheduling events only, not failures) | No/weak | Poor | Repository states usage terms for resear | Reachable, verified via GitHub GET (HTTP 200) |
| 19 | Building Data Genome Project 2 (BDG2) | building energy / HVAC (non-residential buildings) | 3,053 energy meters across 1,636 non-residential buildings across multiple climate zones (a very large fleet) | 2 full years (2016-2017), hourly sampling | None | Yes | Moderate | CC-BY-4.0 (Zenodo record metadata) | Reachable, verified via Zenodo REST API (HTTP 200) |

## Detailed profiles

### 1. CARE to Compare (EDP-derived Wind Turbine SCADA dataset for Early Fault Detection)

- **Domain:** wind turbine SCADA / fleet fault detection
- **URL:** https://zenodo.org/records/14006163 (also mirrored at https://zenodo.org/records/10958775); paper https://arxiv.org/abs/2404.10320 (published Data 2024, 9(12):138)
- **Licence:** CC-BY-SA-4.0 (Zenodo record metadata)
- **Download status:** Reachable and verified via Zenodo REST API (HTTP 200); single zip, 5.48 GB total, direct-download links resolve without login
- **Channels:** 10-minute SCADA aggregates: wind speed, power, pitch, rotor/generator speed, temperatures (gearbox/bearing/generator/nacelle), ambient conditions, plus turbine-status codes; exact channel count varies by farm/turbine (SCADA vendor differences)
- **Duration & sampling:** 10-minute resolution; 89 turbine-years aggregate across all units (per paper abstract)
- **Entities:** 36 wind turbines across 3 different real wind farms (fleet, cross-farm)
- **Documented drift / regime changes:** Turbine-status-based labels for every sample (documents operating-mode changes); 44 labeled anomalous time frames leading to faults plus 51 normal-behavior series, i.e. explicit before/after-fault regime segmentation
- **Fault/event labels:** Yes — most detailed public fault labeling of any open wind-turbine dataset per the authors: fault type, onset and normal/anomalous time windows
- **Context variables:** Ambient wind speed/direction, ambient temperature; turbine status/alarm codes
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Strong: real multi-year fleet operation with labeled fault onsets is close to a natural long-horizon drift + concept-shift testbed; original CARE score already evaluates detection reliability over time
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Strong: 36 turbines across 3 farms with comparable SCADA schema gives natural recurring-regime / cross-unit retrieval-memory setup (same turbine model across seasons, or across sister turbines)
- **Size:** 5.48 GB single archive (do not bulk-download for audit; verified via Zenodo API only)
- **Caveats:** CC-BY-SA (share-alike) is more restrictive than CC-BY — check clash with advisor's IP policy before use; per-turbine exact channel set and true calendar timestamps need to be confirmed after download (not verified here beyond metadata); large size for a laptop-scale thesis (subsampling likely needed); a companion/earlier version lives at record 10958775, use latest version 14006163 to avoid a documented labeling issue in v<6

### 2. Kelmarsh Wind Farm SCADA data

- **Domain:** wind turbine SCADA
- **URL:** https://zenodo.org/records/7212475
- **Licence:** CC-BY-4.0 (Zenodo record metadata)
- **Download status:** Reachable, verified via Zenodo REST API (HTTP 200); 13 files, sizes from 38 KB (docs) up to ~175 MB per year-file
- **Channels:** ~10-min SCADA: active power, wind speed/direction, pitch angle, rotor/generator speed, nacelle/ambient temperature, yaw, plus turbine event/status log
- **Duration & sampling:** 10-minute SCADA, 2016-2021 (subsequent Zenodo deposits extend coverage further; check latest record version for updated end date)
- **Entities:** 6 turbines (Senvion MM92), single wind farm (Kelmarsh, UK)
- **Documented drift / regime changes:** Turbine status/event log documents downtime, curtailment and alarm states across the multi-year span; seasonal wind-resource variation gives natural covariate shift
- **Fault/event labels:** Partial — status/event codes and downtime periods are logged, but there is no curated 'these are the faults' label file comparable to CARE to Compare
- **Context variables:** Ambient wind speed/direction, temperature
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Good: multi-year continuous SCADA from the same physical units, ideal for testing an online/TTA forecaster against real seasonal and long-term drift
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Moderate: only 6 turbines, but paired with Penmanshiel (same format, same maintainer) gives a small fleet across two sites for regime-retrieval experiments
- **Size:** ~350-450 MB total across year files (per-file sizes 1.5 MB-175 MB observed via API)
- **Caveats:** Same publisher/format as Penmanshiel so the two are natural companions; event/status log is not a clean fault-catalogue like CARE to Compare — extracting 'drift events' will take manual curation

### 3. Penmanshiel Wind Farm SCADA data

- **Domain:** wind turbine SCADA
- **URL:** https://zenodo.org/records/8253010
- **Licence:** CC-BY-4.0 (Zenodo record metadata)
- **Download status:** Reachable, verified via Zenodo REST API (HTTP 200); 19 files, largest ~475 MB
- **Channels:** Same schema family as Kelmarsh: 10-min active power, wind speed/direction, pitch, rotor/generator speed, temperatures, status/event log
- **Duration & sampling:** 10-minute SCADA, 2016-2021 (extended in later record versions)
- **Entities:** 14 turbines (Senvion MM92), single wind farm (Penmanshiel, UK)
- **Documented drift / regime changes:** Status/event log across multi-year span; seasonal and long-term wind-resource drift
- **Fault/event labels:** Partial — status/event codes only, no curated fault catalogue
- **Context variables:** Ambient wind speed/direction, temperature
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Good, same rationale as Kelmarsh
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Good: 14 comparable turbines at one site is a reasonable fleet size for retrieval-memory experiments across recurring regimes (e.g. wind-direction sectors, seasons)
- **Size:** ~1.5-2 GB total across year files (per-file sizes up to 475 MB observed via API)
- **Caveats:** Same caveats as Kelmarsh (manual fault curation needed); larger fleet than Kelmarsh makes it the stronger of the pair for direction 3

### 4. ENGIE 'La Haute Borne' open wind farm SCADA data

- **Domain:** wind turbine SCADA
- **URL:** https://opendata-renewables.engie.com (portal)
- **Licence:** Unknown/unverified (portal unreachable)
- **Download status:** UNAVAILABLE — direct connection attempt to opendata-renewables.engie.com failed (proxy 502/tunnel failure) and independent community sources (curated open-SCADA lists found via search) mark this portal as no longer available as of 2025-2026
- **Channels:** Historically: 10-min SCADA similar to Kelmarsh/Penmanshiel (per third-party summaries)
- **Duration & sampling:** Historically ~2013-2020, 10-minute SCADA, 4 turbines
- **Entities:** 4 turbines, single farm (Meuse, France)
- **Documented drift / regime changes:** Not verifiable (portal down)
- **Fault/event labels:** Not verifiable (portal down)
- **Context variables:** Not verifiable (portal down)
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Cannot recommend — dataset itself may still exist in third-party GitHub mirrors, but the source portal could not be verified reachable at this time
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Cannot recommend — same reason
- **Size:** Unknown
- **Caveats:** PROVISIONAL: only checked via a direct connection attempt to the vendor portal (failed) plus web-search snippets describing third-party mirrors; did not verify any GitHub mirror's licence or completeness. Treat as currently unavailable at the original source; do not rely on it without independently confirming a mirror.

### 5. MetroPT-3 (Porto Metro Air Production Unit)

- **Domain:** rail compressor / industrial IoT
- **URL:** https://archive.ics.uci.edu/dataset/791/metropt+3+dataset
- **Licence:** UCI ML Repository site license (CC BY 4.0 per current UCI Repository terms; no dataset-specific override found)
- **Download status:** Reachable, verified via UCI dataset API and page GET (HTTP 200)
- **Channels:** 8 analogue signals (pressures TP2/TP3/H1/DV_pressure/Reservoirs, oil temperature, flowmeter, motor current) + 8 digital signals + GPS lat/long/speed = 16-17 columns
- **Duration & sampling:** 1 Hz sampling, February-August 2020 continuous (~1.52M rows per UCI API metadata)
- **Entities:** Single Air Production Unit on a single metro train (no fleet in this specific release)
- **Documented drift / regime changes:** Continuous operational data with seasonal/operational variation but no explicit regime labels beyond failure windows
- **Fault/event labels:** Yes — several documented real failure events (e.g. air-leak, oil-leak incidents) with maintenance-report start/end timestamps, described in the companion Scientific Data paper
- **Context variables:** GPS location/speed (proxy for duty-cycle/operating context)
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Good: single real machine, dense 1 Hz data, several months, genuine documented failures suitable for online-adaptation/drift experiments at a tractable size
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Weak: single unit only in this release — no fleet for cross-entity retrieval memory (see MetroPT2 below for a later multi-month release, still single APU)
- **Size:** Moderate (~1.5M rows x 16 cols, well under 1 GB as CSV)
- **Caveats:** Only 1 unit; if fleet comparison is required this dataset alone will not suffice. Companion MetroPT2 (Zenodo 7766691, 2022 data, ~7.1M rows) extends duration but is reportedly still a single APU — was not separately downloaded/verified beyond its Zenodo metadata page.

### 6. UCI Gas Turbine CO and NOx Emission Data Set

- **Domain:** gas turbine / power generation emissions
- **URL:** https://archive.ics.uci.edu/dataset/551/gas+turbine+co+and+nox+emission+data+set
- **Licence:** UCI ML Repository site license (CC BY 4.0 per current UCI Repository terms)
- **Download status:** Reachable, verified via UCI dataset API and page GET (HTTP 200)
- **Channels:** 11 sensor/process variables (ambient temperature/pressure/humidity, compressor discharge pressure/temperature, turbine inlet/exhaust temperature, fuel flow, turbine energy yield) + CO and NOx targets
- **Duration & sampling:** Hourly-averaged readings, one file per year, 2011-2015 (5 years); 36,733 instances total (UCI API)
- **Entities:** Single gas turbine unit
- **Documented drift / regime changes:** The original benchmark paper (Kaya et al.) explicitly reports systematic multi-year shifts in pollutant-emission magnitudes across the 2011-2015 span — i.e. real, published evidence of concept drift in this exact dataset
- **Fault/event labels:** None — no fault/failure labels, only continuous process and emission readings
- **Context variables:** Ambient temperature, pressure, humidity
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Good: one of few public sources with a peer-reviewed, explicit claim of multi-year drift in a real machine's output variables; hourly cadence and 5-year span are appropriate for testing long-horizon forecast degradation and online adaptation
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Weak: single unit, no recurring-regime metadata beyond year-of-record; not suited to a fleet/retrieval-memory design without heavy augmentation
- **Size:** Small (36.7K rows x 11 cols, a few MB as CSV)
- **Caveats:** No true datetime column — only year-segmented files in chronological order, so any calendar-scale drift analysis must assume roughly uniform intra-year sampling; single unit limits direction-3 use

### 7. UCI Condition Monitoring of Hydraulic Systems

- **Domain:** hydraulic test rig / rotating machinery
- **URL:** https://archive.ics.uci.edu/dataset/447/condition+monitoring+of+hydraulic+systems
- **Licence:** UCI ML Repository site license (CC BY 4.0 per current UCI Repository terms)
- **Download status:** Reachable, verified via UCI dataset API and page GET (HTTP 200)
- **Channels:** 17 sensors (pressure, volume flow, temperature, vibration, cooling efficiency/power, efficiency factor) recorded at 100 Hz/10 Hz/1 Hz depending on channel, 43,680 raw features per cycle
- **Duration & sampling:** 2,205 sixty-second measurement cycles under constant load conditions; not a continuous calendar-time series
- **Entities:** Single hydraulic test rig with deliberately varied component condition (cooler, valve, pump, accumulator) across cycles
- **Documented drift / regime changes:** Component degradation levels are deliberately varied and labeled per cycle (e.g. cooler efficiency %, valve condition %) — a controlled, labeled proxy for gradual degradation rather than real deployment-time drift
- **Fault/event labels:** Yes, but as discrete per-cycle condition labels (multi-class), not timestamped real-world failure events
- **Context variables:** None beyond the rig's own load cycle
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Weak-to-moderate: cycles are not spaced over real calendar months/years (a lab test-rig protocol, not a deployed asset), so it does not directly exercise 'a model trained today loses accuracy a year later'; useful mainly as a controlled degradation-severity benchmark
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Weak: single rig, no fleet
- **Size:** Moderate (~2,205 x 43,680 raw sensor matrix, but often used via engineered aggregate features)
- **Caveats:** Frequently mis-cited as a 'long-term monitoring' dataset — it is a lab rig with cycle-indexed condition levels, not a real multi-year deployment; treat any 'drift' claim about it as provisional

### 8. NASA C-MAPSS Turbofan Engine Degradation Simulation

- **Domain:** aircraft turbofan engine (simulated)
- **URL:** https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/ (also mirrored on Kaggle)
- **Licence:** NASA open data (public domain / NASA data usage policy)
- **Download status:** NASA PCoE repository page reachable (HTTP 200); actual data files are hosted on a separate S3-backed PHM-datasets bucket not verified in this audit (network scope not requested)
- **Channels:** 21 sensor channels + 3 operating-condition settings per engine unit
- **Duration & sampling:** Simulated run-to-failure trajectories indexed by engine operating cycle, not calendar time; hundreds of engine units across 4 sub-datasets (FD001-FD004)
- **Entities:** 100-260+ simulated turbofan units depending on sub-dataset (a synthetic 'fleet')
- **Documented drift / regime changes:** Explicit multiple operating conditions/regimes in FD002/FD004 by design, but these are simulator settings, not real deployment drift
- **Fault/event labels:** Yes — run-to-failure with known remaining-useful-life ground truth (this is the standard RUL benchmark)
- **Context variables:** 3 operating-condition settings (altitude/Mach/throttle-resolver angle analogues)
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Weak for THIS thesis: fully simulated, no calendar-time drift, extremely well-trodden RUL benchmark (any 'novelty' here is already occupied by hundreds of papers)
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Moderate: large synthetic fleet with labeled regimes is a clean sandbox for prototyping a retrieval-memory mechanism before moving to real data, but reviewers will discount novelty claims resting only on C-MAPSS
- **Size:** Small-moderate (a few hundred MB across sub-datasets)
- **Caveats:** Simulated, not real; extremely widely used (hundreds of RUL papers) — good for a sanity-check baseline, weak as a primary evaluation dataset for a novelty claim

### 9. N-CMAPSS (New C-MAPSS, with flight-condition time histories)

- **Domain:** aircraft turbofan engine (simulated, higher fidelity)
- **URL:** https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/
- **Licence:** NASA open data
- **Download status:** Landing page reachable (HTTP 200); actual .h5 data files not directly probed in this audit
- **Channels:** ~20 sensor readings + auxiliary/virtual sensors + full flight-condition (altitude, Mach, throttle-resolver-angle, temperature) time histories
- **Duration & sampling:** Continuous flight-by-flight simulated histories (seconds resolution within each flight) until failure, across multiple flight classes
- **Entities:** ~128 simulated engine units across several sub-datasets (DS01-DS08)
- **Documented drift / regime changes:** Realistic flight-condition variability by design (different flight classes/durations), still simulated
- **Fault/event labels:** Yes, run-to-failure with RUL ground truth and health-state (healthy/faulty) labels
- **Context variables:** Full flight-condition trajectory
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Weak for calendar-scale drift (still simulated, no real months/years deployment gap), but the flight-condition time histories give richer within-unit non-stationarity than classic C-MAPSS
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Moderate, same rationale as C-MAPSS but higher fidelity
- **Size:** Large (multi-GB HDF5 files per sub-dataset)
- **Caveats:** Simulated; not verified beyond the landing page in this audit (large individual files, avoided per the ~20MB probing limit)

### 10. XJTU-SY Bearing Datasets / PRONOSTIA (FEMTO) / IMS Bearing Dataset

- **Domain:** rolling-element bearings (accelerated run-to-failure test rigs)
- **URL:** https://github.com/WangBiaoXJTU/xjtu-sy-bearing-datasets (XJTU-SY mirror); IMS/PRONOSTIA hosted on NASA PCoE
- **Licence:** Research use, redistribution terms vary by mirror (GitHub mirror reachable, HTTP 200)
- **Download status:** XJTU-SY GitHub mirror reachable (HTTP 200); IMS/PRONOSTIA original hosts not separately re-verified beyond prior general knowledge of these well-established benchmarks
- **Channels:** Vibration (accelerometer, horizontal/vertical) at high frequency (12.8-25.6 kHz), some with additional channels
- **Duration & sampling:** Each individual run-to-failure test lasts minutes to at most a few days (accelerated ageing); not months/years
- **Entities:** Multiple bearings per rig (XJTU-SY: 15 bearings across 3 operating conditions; IMS: 4 bearings/test; PRONOSTIA: 17 bearings across 3 conditions)
- **Documented drift / regime changes:** Distinct pre-set operating conditions (speed/load) across sub-tests, but each individual trajectory is a short accelerated-ageing run, not a long deployment history
- **Fault/event labels:** Yes — run-to-failure with known failure mode/time
- **Context variables:** Fixed speed/load setting per sub-test
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Poor: durations are minutes-to-days, the opposite of the 'a year or two later' deployment-drift scenario this thesis targets
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Weak-moderate: multiple comparable bearings/conditions exist, but the short horizon limits usefulness for a memory mechanism meant to bridge long time gaps
- **Size:** Moderate (GBs of raw vibration waveforms)
- **Caveats:** Classic, heavily used RUL/PHM benchmarks — good baselines for a related-work table, poor fit for THIS thesis's core long-horizon-drift requirement

### 11. SKAB (Skoltech Anomaly Benchmark)

- **Domain:** water-circulation test rig (industrial IoT)
- **URL:** https://github.com/waico/SKAB
- **Licence:** Permissive (repository states an open license; verify exact SPDX tag on the repo before use)
- **Download status:** Reachable, verified via GitHub GET (HTTP 200)
- **Channels:** ~8 sensors (pressure, flow rate, temperature, current) plus a few derived/vibration channels depending on version
- **Duration & sampling:** Individual experiments last minutes to ~1 hour each; tens of separate short experiments total, not a continuous multi-month log
- **Entities:** Single test rig, multiple short experiment runs (some labeled as anomalous, some normal) plus an 'other' extended benchmark subset
- **Documented drift / regime changes:** None at the calendar-time scale; different experiments correspond to different induced-fault types
- **Fault/event labels:** Yes — anomaly start/end intervals are labeled per experiment
- **Context variables:** None beyond controlled rig settings
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Poor: individual runs are far too short (minutes) to represent a deployment drifting over months/years
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Poor: single rig, no fleet
- **Size:** Small (tens of MB)
- **Caveats:** Good as an anomaly-detection sanity-check dataset, not appropriate as the primary long-horizon-drift dataset for this thesis

### 12. Extended Tennessee Eastman Process (Reinartz/Kulahci/Ravn / Rieth simulation datasets)

- **Domain:** chemical process plant (simulated)
- **URL:** https://data.dtu.dk/articles/dataset/Tennessee_Eastman_Reference_Data_for_Fault-Detection_and_Decision_Support_Systems/13385936 ; https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/6C3JR1
- **Licence:** DTU Data: CC-BY-4.0-style open repository (page reachable, HTTP 202 dynamic-render response, consistent with a live Figshare-for-institutions page); Harvard Dataverse version not independently re-verified in this pass
- **Download status:** DTU Data page reachable (HTTP 202, dynamic content); actual CSV bundle not downloaded (size and exact license text not independently confirmed beyond the landing page)
- **Channels:** 52 process variables (41 measured + 11 manipulated) per the standard TEP variable set
- **Duration & sampling:** Simulated continuous process runs, several hundred simulated hours per run, hundreds of independent simulation runs per fault type (Reinartz et al. extended set) or ~500 runs (Rieth et al.)
- **Entities:** Single simulated chemical plant, replicated across many independent stochastic simulation runs (not a real fleet)
- **Documented drift / regime changes:** 20 known fault types with documented onset times per run; no real calendar-time drift (simulation clock only)
- **Fault/event labels:** Yes, extensively — this is the standard fault-detection/diagnosis benchmark process
- **Context variables:** None beyond the simulator's own state
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Weak for calendar-scale drift (simulated, no real deployment-time gap) but useful for controlled ablation of a proposed online-adaptation mechanism under known, labeled fault onsets
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Weak: single simulated plant, no fleet, though many independent runs allow a 'library of regimes' retrieval design as a methodological testbed
- **Size:** Moderate-large depending on version (100s of MB to low GBs)
- **Caveats:** One of the most heavily used FDD benchmarks in the process-control literature — reviewers will expect it to be explicitly extended rather than used as-is; simulated, not real drift

### 13. Debutanizer Column / Sulfur Recovery Unit soft-sensor datasets (Fortuna et al.)

- **Domain:** petrochemical distillation / gas-treatment soft sensing
- **URL:** Distributed as supplementary material with Fortuna et al., 'Soft Sensors for Monitoring and Control of Industrial Processes' (Springer); mirrored in various GitHub research repos
- **Licence:** Varies by mirror; original book dataset has no explicit open licence statement found
- **Download status:** Not independently re-verified in this pass beyond prior search snippets (small static files typically <1 MB, well under probing threshold, but no canonical stable URL was confirmed reachable)
- **Channels:** Debutanizer: 7 process variables; SRU: 5 input variables x 2 quality targets
- **Duration & sampling:** Static single-run sample sequences (2,394 and ~10,081 samples respectively); no timestamps, sample index only
- **Entities:** Single unit each
- **Documented drift / regime changes:** None documented
- **Fault/event labels:** None
- **Context variables:** None
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Poor: no calendar time, single short static run, no drift documentation
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Poor: single unit, no recurring regimes documented
- **Size:** Very small (<1 MB)
- **Caveats:** PROVISIONAL — could not confirm a single canonical, currently-reachable download URL in this pass; widely cited in soft-sensor papers via supplementary files rather than a persistent repository. Not recommended given the poor fit regardless.

### 14. ETT (Electricity Transformer Temperature) Dataset

- **Domain:** power transformer (grid equipment)
- **URL:** https://github.com/zhouhaoyi/ETDataset
- **Licence:** CC BY 4.0 (per repository)
- **Download status:** Reachable, verified via GitHub GET (HTTP 200)
- **Channels:** 6 power-load features (high/medium/low useful load and useless load) + oil temperature target, x2 transformers x2 granularities (ETTh1/h2 hourly, ETTm1/m2 15-min)
- **Duration & sampling:** 2 years continuous, July 2016-July 2018, fixed hourly or 15-minute sampling
- **Entities:** 2 physical electricity transformers (a small 'fleet' of 2 units)
- **Documented drift / regime changes:** No curated drift/event labels; seasonal load variation is present implicitly in the raw series and is well known in the long-sequence-forecasting literature as exhibiting distributional shift across the 2-year span
- **Fault/event labels:** None
- **Context variables:** None beyond the load features themselves
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Good: real physical equipment (grid transformer), genuine 2-year continuous span, fixed sampling, already the standard benchmark for long-sequence/long-horizon forecasting (Informer, Autoformer, etc.) — a natural base for adding an online-adaptation/memory layer and comparing to established long-horizon forecasting baselines
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Weak: only 2 units, and they are not documented as having comparable recurring regimes beyond generic seasonality
- **Size:** Small (a few MB as CSV)
- **Caveats:** No documented faults/regime-change events — 'drift' here means routine seasonal/load non-stationarity, not a labeled deployment incident; classified by the user's advisor domain preference as borderline machine-like (grid power equipment) rather than core rotating machinery

### 15. Server Machine Dataset (SMD)

- **Domain:** compute-cluster server telemetry (not physical industrial machinery)
- **URL:** https://github.com/NetManAIOps/OmniAnomaly
- **Licence:** MIT (repository code licence; data released with the paper)
- **Download status:** Reachable, verified via GitHub GET (HTTP 200)
- **Channels:** 38 metrics per machine (CPU, memory, network, etc.)
- **Duration & sampling:** ~5 weeks of data per machine (train+test combined), fixed sampling interval
- **Entities:** 28 machines (compute servers) grouped into 3 clusters
- **Documented drift / regime changes:** None documented beyond generic anomaly segments
- **Fault/event labels:** Yes — anomaly interval labels per machine
- **Context variables:** None
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Poor: duration (~5 weeks) is far short of the 'a year or two later' deployment gap this thesis targets, and the domain (compute servers) is explicitly outside the user's target application area
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Weak: 28 comparable entities is nice for retrieval-across-units in principle, but domain mismatch and short duration make this a poor primary choice
- **Size:** Small (tens of MB)
- **Caveats:** Domain mismatch with the advisor's preferred machine/industrial-sensor application area; included for completeness only, not recommended

### 16. HAI (HIL-based Augmented ICS) Security Dataset

- **Domain:** industrial control system testbed (boiler/turbine/water-treatment emulator)
- **URL:** https://github.com/icsdataset/hai
- **Licence:** Available for research use per USENIX CSET/AsiaCCS publications (exact SPDX licence on the GitHub repo not confirmed beyond reachability)
- **Download status:** Reachable, verified via GitHub GET (HTTP 200)
- **Channels:** ~50-80 process variables depending on HAI version (20.07/21.03/22.04), spanning boiler, turbine and water-treatment emulator subsystems
- **Duration & sampling:** Each released version spans on the order of days to a few weeks of continuous operation with injected attacks; not months/years
- **Entities:** Single integrated testbed combining 3 physical process emulators (boiler, turbine, water treatment)
- **Documented drift / regime changes:** None at calendar scale; documented attack/anomaly intervals only
- **Fault/event labels:** Yes — labeled attack intervals
- **Context variables:** None beyond testbed setpoints
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Poor: short duration (days-weeks), no long-horizon drift
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Poor: single testbed, no fleet
- **Size:** Small-moderate (tens to low hundreds of MB per version)
- **Caveats:** Genuinely machine-like domain (turbine/boiler emulator) but duration is far too short for this thesis's long-horizon-drift focus; better suited to intrusion-detection research

### 17. Microsoft Azure Predictive Maintenance dataset

- **Domain:** industrial machine telemetry (vendor-stated as simulated)
- **URL:** https://www.kaggle.com/datasets/arnabbiswas1/microsoft-azure-predictive-maintenance (originally Azure AI Gallery, now retired)
- **Licence:** Unclear/unverified — Kaggle domain not in this audit's allowlisted scope; original Azure AI Gallery source has been retired by Microsoft
- **Download status:** NOT VERIFIED — kaggle.com was not requested/allowlisted for this audit; original Azure AI Gallery hosting page is reported retired in search results
- **Channels:** Telemetry (voltage, rotation, pressure, vibration), error logs, maintenance/replacement logs, failure logs, machine metadata (age, model) for 100 machines
- **Duration & sampling:** 1 year of hourly telemetry (per widely-cited dataset documentation)
- **Entities:** 100 machines, 4 machine models (a synthetic fleet)
- **Documented drift / regime changes:** Not documented as real drift
- **Fault/event labels:** Yes — failure and maintenance event logs
- **Context variables:** Machine age, model
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Weak: Microsoft's own documentation describes this telemetry as simulated/generated to demonstrate the modeling approach, not measured from real machines, and only 1 year span
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Moderate in principle (100-unit fleet) but undermined by the synthetic nature of the telemetry
- **Size:** Small (tens of MB)
- **Caveats:** PROVISIONAL — not reachability-checked in this pass (Kaggle not allowlisted); widely reported to be simulated data, not real sensor telemetry, which conflicts with the user's stated preference for real machine data

### 18. Alibaba Cluster Trace (2017/2018/v2022)

- **Domain:** compute-cluster workload traces (not physical industrial machinery)
- **URL:** https://github.com/alibaba/clusterdata
- **Licence:** Repository states usage terms for research (verify exact terms on repo before use)
- **Download status:** Reachable, verified via GitHub GET (HTTP 200)
- **Channels:** Machine-level CPU/memory/disk utilization, container/job scheduling events
- **Duration & sampling:** 8 days (2017 trace) to ~2 months (2018 trace); newer traces exist but none span multiple years
- **Entities:** Thousands of physical machines in a data-centre cluster
- **Documented drift / regime changes:** None documented as calendar-scale drift
- **Fault/event labels:** None (workload/scheduling events only, not failures)
- **Context variables:** None
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Poor: durations (days-to-months) fall far short of the 'a year or two later' scenario, and domain (data-centre compute) is outside the advisor's preferred industrial/rotating-machinery focus
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Poor for the same domain-mismatch and duration reasons
- **Size:** Large (many GB for full traces)
- **Caveats:** Domain and duration mismatch with the thesis's stated target application area; not recommended

### 19. Building Data Genome Project 2 (BDG2)

- **Domain:** building energy / HVAC (non-residential buildings)
- **URL:** https://zenodo.org/records/3887306 (also https://github.com/buds-lab/building-data-genome-project-2)
- **Licence:** CC-BY-4.0 (Zenodo record metadata)
- **Download status:** Reachable, verified via Zenodo REST API (HTTP 200); single archive, 595 MB
- **Channels:** Hourly electricity, chilled-water, steam, hot-water, gas, water and irrigation meters where available; building metadata (type, floor area, location) and matched weather data
- **Duration & sampling:** 2 full years (2016-2017), hourly sampling
- **Entities:** 3,053 energy meters across 1,636 non-residential buildings across multiple climate zones (a very large fleet)
- **Documented drift / regime changes:** No explicit fault/regime labels, but real multi-year, multi-building operation naturally contains occupancy, seasonal and retrofit-driven regime shifts across such a large building fleet
- **Fault/event labels:** None
- **Context variables:** Matched local weather (temperature, humidity, etc.) per building site
- **Fit for Direction 2 (online/TTA under long-horizon drift):** Moderate: real 2-year span and huge scale support long-horizon forecasting/adaptation experiments, but no documented failure/regime-change events to anchor evaluation
- **Fit for Direction 3 (retrieval-memory across recurring regimes):** Moderate-good: very large number of comparable meters/buildings gives strong statistical power for a retrieval-memory-across-entities design, though the domain (whole-building energy) is HVAC-adjacent rather than core rotating machinery
- **Size:** 595 MB archive
- **Caveats:** Domain is building energy rather than the advisor's preferred rotating-machinery/compressor/turbine focus; include only if the advisor accepts HVAC/building energy as within scope

## Blocked / unavailable / not independently verified

- ENGIE 'La Haute Borne' open data portal (opendata-renewables.engie.com): connection attempt failed (proxy 502/tunnel failure); independent web-search snippets from curated open-SCADA-dataset lists also flag it as no longer available. Could not verify licence, schema, or completeness of any third-party mirror.
- Microsoft Azure Predictive Maintenance dataset: kaggle.com was not requested/allowlisted for this audit pass, so reachability/licence was not directly verified; in addition, Microsoft's own documentation (found via search) describes the telemetry as simulated rather than measured from real machines, which conflicts with the user's stated preference for real sensor data — recommend deprioritizing regardless of reachability.
- Debutanizer / Sulfur Recovery Unit soft-sensor datasets (Fortuna et al.): no single canonical, currently-reachable download URL could be confirmed in this pass (they circulate as book supplementary files via various research mirrors); not recommended on fit grounds in any case (static single run, no calendar time).
- N-CMAPSS and C-MAPSS actual data files: the NASA PCoE landing page was confirmed reachable, but the underlying large data archives (hosted on a separate S3 bucket / NASA data portal) were not individually probed in this pass to stay within the audit's light-touch, no-large-download scope.

## Discussion: why the ranking

The task's requirements (real machines, multivariate, long chronological span of several months to years, fixed sampling, documented operating-mode/maintenance/failure changes, multiple comparable units, permissive licence, currently downloadable) are jointly satisfied best by the **CARE to Compare / EDP wind-turbine SCADA** release: it is real, multi-year in aggregate (89 turbine-years), spans 36 turbines across 3 farms (a genuine fleet), and — unusually for a public dataset — ships with the most detailed fault-onset labeling of any open wind dataset. Its only real drawback is the CC-BY-SA share-alike licence (more restrictive than CC-BY) and its 5.5 GB size, which a thesis would need to subsample.

**Kelmarsh + Penmanshiel** trade some of that fault-label richness for a smaller, more tractable, CC-BY-4.0 footprint and a track record as a standard benchmark pair in the wind-forecasting literature — a safer default if the CARE to Compare licence or size is a blocker.

For a *single-unit, very tractable* option, **UCI Gas Turbine CO/NOx** is notable because the source paper itself documents multi-year drift in the target variables — a citable, pre-existing claim of exactly the phenomenon the thesis is about — though it lacks a real datetime index and any fault labels. **MetroPT-3** is the closest thing to a real single-machine 'trained today, degrades over months' story with genuine failure events, but is a single unit. **ETT** offers the cleanest 2-year continuous real-equipment span and is already the standard long-sequence-forecasting benchmark, making it easy to position a new method against strong published baselines, at the cost of having no curated drift/fault events.

Datasets excluded from the top 5 either fail the calendar-time-span requirement outright (XJTU-SY/PRONOSTIA/IMS bearings: minutes-to-days per run; SKAB: minutes-per-experiment; HAI: days-to-weeks per release; Alibaba cluster traces: days-to-2-months; SMD: ~5 weeks), are fully simulated with no calendar clock (C-MAPSS, N-CMAPSS, Tennessee Eastman), are domain-mismatched to the advisor's stated industrial/rotating-machinery focus (SMD, Alibaba traces — compute clusters; BDG2 — building energy, included only as a borderline HVAC-adjacent option), or could not be confirmed reachable/real in this pass (La Haute Borne portal is down; Azure PdM telemetry is vendor-documented as simulated; debutanizer/SRU has no confirmed canonical URL).

## Threats to this audit

- **Coverage limited by network allowlist.** kaggle.com, dataverse.harvard.edu, and the NASA PHM S3 bucket were not requested for this pass; anything gated behind them (Azure PdM, one TEP mirror, the actual C-MAPSS/N-CMAPSS data files) is reachability-**unverified**, not confirmed available or unavailable.
- **Metadata-only verification.** For every dataset, 'reachable' means the landing page or REST metadata endpoint responded, not that the full file set downloads correctly or matches the documented schema — actual column names, exact date ranges, and file integrity should be re-checked once a specific dataset is chosen and downloaded in full.
- **Licence text was read from repository metadata fields, not full licence documents**, for the Zenodo- and UCI-hosted sets; for GitHub-hosted sets (SKAB, HAI, ETT, SMD, Alibaba) the exact SPDX tag on the repository should be re-confirmed before redistribution or publication.
- **'Documented drift' is a matter of degree.** Only CARE to Compare and UCI Gas Turbine CO/NOx have an explicit, citable claim of drift/labeled regime change; for Kelmarsh/Penmanshiel/MetroPT/ETT, 'drift' has to be operationalised by the thesis (e.g. via a rolling-window forecast-error metric) rather than read off a pre-existing label.
- **La Haute Borne status is provisional** — based on one failed connection attempt plus secondary web-search evidence, not an exhaustive check of every mirror.
