# Phase A — STOP (2026-09-12)

Protocol: `5acc64aee055d3c223efc89510c53a92ec319bbc`. No selection-rule amendment. This is a sealed **audit**, not a successful dataset manifest. Phase B and Phase C were not started.

## Exact blocker

All 75 CD=1 candidate CSVs were obtained from the official multivariate archive and numerically audited. 65 pass numeric/prefix checks. Fifteen SMD traces have content-verified native machine identities; fourteen pass the prefix rule. The remaining 60 candidates lack verified native trace/crop mappings in this audit and are excluded fail-closed. This is an unresolved provenance blocker, **not proof that those sources cannot ever be resolved**.

Eligible distinct-source counts in bucket order are 5 / 12 / 3 / 3. Although every bucket individually has at least three, the periodic and random_walk eligible pools are the **same three sources**. The frozen global assignment returns no solution. Selecting twelve with the currently verified evidence is impossible. No final twelve-file manifest is emitted.

| Periodic candidate | Finding |
|---|---|
| 059_SMD_id_3_Facility_tr_757_1st_857.csv | Eligible; original machine-2-3 |
| 065_SMD_id_9_Facility_tr_737_1st_837.csv | Eligible; original machine-1-7 |
| 075_SMD_id_19_Facility_tr_564_1st_664.csv | Eligible; original machine-2-7 |
| 078_SMD_id_22_Facility_tr_500_1st_326.csv | Original machine-3-10; 3 anomalous observations in original prefix |
| 080_LTDB_id_2_Medical_tr_500_1st_266.csv | 107 anomalous observations in original prefix; native mapping also unresolved |
| 138_CATSv2_id_1_Sensor_tr_16568_1st_16668.csv | Simulated source; excluded by frozen protocol |
| 139_CATSv2_id_2_Sensor_tr_5592_1st_5692.csv | Simulated source; excluded by frozen protocol |
| 142_CATSv2_id_5_Sensor_tr_30704_1st_30804.csv | Simulated source; excluded by frozen protocol |

CATSv2 is explicitly simulated in both the pinned TSB source catalog and [the original dataset record](https://zenodo.org/records/8338435). Five CATSv2 candidates overall are excluded as synthetic, not only the three periodic entries. Ten prefixes are contaminated: SMD 078, LTDB 080 and all eight TAO candidates. All 75 have D≥2, finite numeric observations, binary labels and sufficient prefix/test lengths. No boundary was moved and no test anomaly requirement was added.

## Provenance, grouping and limitations

`candidate_inventory.json` records every filename, tag, exclusion, SHA256, D/N/cutoff and half-open fit/calibration/test intervals. The cutoff is the **original TSB-released cutoff**, not a claim that TSB preserved each native dataset's original training partition. The pinned naming README documents it. The archived upstream author comment explains that benchmark prefixes can contain anomalies; labels were therefore checked directly rather than trusting the filename's first-anomaly field.

All 28 original SMD test traces were compared using exact full-row numeric containment. All 15 candidate SMD traces resolve to machines, with offsets and raw native SHA256. None maps to fixed machine-1-8 or machine-2-1. This is an exact native-content test, not an approximate similarity heuristic.

All 2,775 candidate pairs were checked for exact equality/contiguous containment where dimensionality permits. Six duplicate pairs form one four-member feature-trace group: Exathlon 188 / 190 / 198 / 199. No additional exact containment pair was detected. This does not rule out nonidentical overlapping crops, transforms, or shared physical origins. Unknown groups are not assumed independent. The Exathlon group remains provenance-ineligible regardless of duplicate detection.

Unresolved mappings by dataset: GHL 23, TAO 8, OPPORTUNITY 7, CATSv2 5, SMAP 5, Exathlon 5, SWaT 2, MSL 1, Daphnet 1, LTDB 1, CreditCard 1, GECCO 1. Dataset-level catalog URLs are recorded where available, but they are not native file mappings. The official archive contains only the 200 CSV files and its directory, not a native mapping table. GHL's catalog endpoint did not provide usable access during this audit; SWaT requires a source access request. The catalog's CreditCard entry links to CICIDS2017 despite the finance filename, a provenance contradiction. TAO lacks a dataset-level source link in the inspected catalog. No unsupported original filenames were invented.

Thus the request to resolve **every** candidate's native origin is not completed. Additional source-file/offset/transformation documentation, especially for non-synthetic random_walk candidates, is needed before the unchanged rule can be retried. Do not interpret this STOP as evidence against the modeling hypotheses. A different selection rule requires a new pre-outcome amendment.

## Integrity and SMD seal

- StrAD metadata commit: `7078876bbd9398481a65c22b7689702ce9e0d558`.
- TSB documentation commit: `6beac72e11d1155ade40870492c00d0d1cfdcaaf`.
- OmniAnomaly raw-source commit: `7fb0e0acf89ea49908896bcc9f9e80fcfff6baf4`.
- CANDI preprocessing commit: `28c9679e503832f59e351208cde63657fcb51cad`.
- Metadata SHA256: `e109da612a90ce3d7b2fcdf51f1a0982358b889ad38f49e85d5049ba0d2eef5c`.
- Official archive SHA256: `7de86ac27f30eeb48d833bb061055670e3f3de07defd995cf2bd5db10ccc9a0d`.

`downloads.json` seals 46 downloaded assets with exact URLs, commits when applicable, bytes and hashes. The archive itself has no immutable upstream commit: the hash seals the downloaded snapshot, not proof it is identical to the archive used by the StrAD authors. `smd_seal.json` records twelve raw/CANDI-preprocessed files for the fixed two machines. Their raw numeric/label checks passed. Normality of native SMD training is documented, not independently verified from unavailable training labels. CANDI pickles were byte-hashed, not executed or modified; normalization auditing remains future work. Large raw data stays local under ignored `data/phase_a/`, reproducibly addressable from the download inventory.

`SHA256SUMS` seals committed audit artifacts. `source_groups.json` records grouping evidence and its limits. No detector was run. No model-result file was inspected or used for selection. A provenance-oriented broad issue search incidentally returned unrelated performance numbers; these were not used, and no model outputs were downloaded or opened. Only the pinned drift metadata was read from StrAD's results directory.

## Tests and reproducibility

Run from repository root (Python 3.12, numpy 1.26.4, pandas 3.0.3; exact observed versions in `environment.json`):

```sh
rtk python3 scripts/phase_a_fetch.py
rtk python3 scripts/phase_a_audit.py
rtk python3 scripts/phase_a_seal_smd.py
rtk python3 -m unittest discover -s scripts -p test_phase_a.py -v
rtk python3 scripts/phase_a_finalize.py
rtk sha256sum -c reports/phase_a/SHA256SUMS
```

Five Phase A tests PASS: numeric/prefix split boundaries, invalid-value/minimum-size rejection, exact crop/signed-zero hashing, non-greedy global assignment, shared-source infeasibility. All 75 dataset numeric checks were executed; ten failed the normal-prefix invariant as reported above. Source trace comparisons and fixed-SMD checks also ran on CPU. There was no GPU training.

Phase B tests: **NOT RUN**, including Lyapunov residual, stationary moments, correlation difference, transition variance, non-identifiability, metric, label-isolation and score-before-update tests. No Phase B scaffolding was built because A did not pass. Protocol deviations: none; incomplete provenance is reported as a blocker, not waived.

Next step: return this STOP for review. Resolve missing native provenance under the unchanged rule, or obtain explicit approval for a pre-outcome amendment. Phase B stays locked until a feasible dataset manifest is sealed; Phase C is not authorized.
