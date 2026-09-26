# Sources and evidence map

Sources were checked 2026-09-26. Primary sources are preferred. The description below states what each link supports; no source alone proves complete M6 suitability.

## Direct semantic candidates

- [Drift-Aware Online Anomaly Detection in Smart Buildings, ACM E-Energy 2026](https://doi.org/10.1145/3744255.3811742) — paper describing three semantic row classes, collection periods, sample counts, train/evaluation setup, and normal-drift versus attack examples.
- [Official Drift-Aware_AD GitHub repository](https://github.com/illinois-arcs/Drift-Aware_AD) — CSV links/schema, row counts, public repository metadata; the repository currently has no explicit license field or LICENSE file. Branch head recorded for provenance: `f13b7699bfb9bd86f44a37c2d42882476128ae52` on 2026-09-26.
- [PreDist current Zenodo record v2](https://zenodo.org/records/19496480) and [original record](https://zenodo.org/records/17522255) — release/version, files, public availability and storage metadata.
- [PreDist README in Zenodo](https://zenodo.org/records/17522255/files/README.md?download=1) — substation populations, cadence/features, normal events, fault records, approximate labels, gaps, unknown/unreported faults and training intervals.
- [PreDist paper, Energy 2026](https://doi.org/10.1016/j.energy.2026.141178) and [arXiv record](https://arxiv.org/abs/2511.14791) — dataset description and CC BY 4.0 publication/data statement.
- [Tennessee Eastman Reference Data for Fault-Detection and Decision Support Systems, DTU Data](https://data.dtu.dk/articles/dataset/Tennessee_Eastman_Reference_Data_for_Fault-Detection_and_Decision_Support_Systems/13385936/1) and [DOI](https://doi.org/10.11583/DTU.13385936.v1) — six modes, 28 process faults, repetitions, 3-minute cadence, duration, file counts/size and CC0 listing.
- [Extended TEP paper](https://doi.org/10.1016/j.compchemeng.2021.107281) — simulator/reference dataset methodology.

## Transfer and fault benchmark candidates

- [NoBOOM NeurIPS 2025 Datasets and Benchmarks paper](https://papers.nips.cc/paper_files/paper/2025/hash/96f8c5e879c339dae55e6c2188b02a33-Abstract-Datasets_and_Benchmarks_Track.html), [paper/OpenReview](https://openreview.net/forum?id=qiLboR0ocm), [dataset DOI](https://doi.org/10.26204/data/13), [official code](https://github.com/wagner-d/noboom), [dataset page](https://tulaut.github.io/ds_NoBoom) — per-process dimensions, sequences, anomaly phase definitions and dataset license. Code license is separate from data license.
- [Batch Distillation anomaly dataset, Scientific Data 2026](https://www.nature.com/articles/s41597-026-07124-3), [current Zenodo release](https://zenodo.org/records/21535243), [earlier DOI](https://doi.org/10.5281/zenodo.17395543), [companion repository](https://github.com/Jarweile/batch-distillation-anomaly-detection-data) — run counts, recipe/metadata, sampling, modalities, storage and CC BY 4.0 terms.
- [NASA C-MAPSS Data.gov record](https://catalog.data.gov/dataset/cmapss-jet-engine-simulated-data) and [NASA Open Data page](https://data.nasa.gov/dataset/groups/c-mapss-aircraft-engine-simulator-data) — entity/column counts, operating conditions, fault modes, RUL protocol and conflicting access/license status.
- [PATH benchmark paper, arXiv HTML](https://arxiv.org/html/2411.13951v6) and [Zenodo record](https://zenodo.org/records/13255121) — 16 channels, 10 Hz, nominal test sequences, drive-cycle context, anomaly types, simulation, storage and dataset card license.
- [Official iTrust SWaT dataset page](https://itrust.sutd.edu.sg/itrust-labs/datasets/dataset-characteristics/swat/) — release description and request-controlled access.
- [Official iTrust WADI dataset page](https://itrust.sutd.edu.sg/itrust-labs/datasets/dataset-characteristics/wadi/) and [iTrust newsletter issue 12](https://itrust.sutd.edu.sg/wp-content/uploads/2018/03/iTrust-newsletter-Issue-12-Jan-Mar_final.pdf) — normal/attack periods, cadence and attack counts for cited WADI version.
- [Official iTrust BATADAL dataset page](https://www.sutd.edu.sg/itrust/itrust-labs/datasets/dataset-characteristics/batadal/) and [BATADAL challenge design](https://www.batadal.net/challenge.html) — C-Town simulated normal/attack challenge setup; page license does not automatically establish data package terms.
- [Google ClusterData 2019 official README](https://github.com/google/cluster-data/blob/master/ClusterData2019.md) — Borg cells, workload schema/cadence and repository license.
- [UCI Electricity Load Diagrams 2011–2014, official UCI dataset page](https://archive.ics.uci.edu/dataset/321/electricityloaddiagrams20112014) and [dataset DOI](https://doi.org/10.24432/C58C86) — 370 clients, 140,256 timestamps, 15-minute interval, principal text-file and download-bundle sizes, and CC BY 4.0 license.
- [DAYPSCI article, Data in Brief 2026](https://doi.org/10.1016/j.dib.2026.113146) and [PubMed record](https://pubmed.ncbi.nlm.nih.gov/42644104/) — event-based PLC testbed, sensor/actuator injection types, external state/context and data-description claims; data repository/license still unresolved here.

## Project protocol sources

- [ReCATS paper DOI](https://doi.org/10.1145/3770855.3817985), [project README](../../README.md), and [M0 review](../../reports/m0_review.md) — ReCATS task-incremental setting with known task partitions and per-task normal-only training. It is included as protocol context, not as a newly audited dataset source. The M0 review records that the full text was independently checked by the user; this audit does not repeat that paper review.

- [Revised M0 protocol](../../reports/m0_protocol.md) — eligibility, authorization boundaries, synthetic/real semantic safeguards and prohibition on inventing real drift labels.
- [M1 experiment plan](../../research/adaptive_normality_xlstm/experiment_plan.md) — M4 same-D leave-one-machine-out SMD definition and M6 data contract. The current active M1 worktree observed separately is recorded in this audit's README.

## Evidence notes

Publisher pages, paper text/metadata, official dataset README files, and official source repositories were used for claims. Third-party dataset mirrors were not used to substantiate licensing. Source pages that disagreed (C-MAPSS availability/license) are explicitly marked unresolved. A listed storage size is a publisher or repository statement unless identified as a request probe; it should be rechecked before acquisition.
