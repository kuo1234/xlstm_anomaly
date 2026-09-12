# A1 PASS; A2 STOP — v3 released-series audit

The original strict audit at `ad97c4a` remains unchanged. The evidence-tier and exact selection rule were committed/pushed as `06b0684` **before** revised manifest generation. Correlation tests/synthetic configuration were independently committed as `b0a79fe` before observation generation. A source-evidence correction was committed/pushed as `5b5ea9d` before corrected assignment.

## A1

All twelve fixed SMD raw/preprocessed assets match the original seal; all fifteen original audit-artifact checksums also match. Reproduction splits and CANDI preprocessing are unchanged. This remains the strict real-data reproduction/natural-H1 anchor. No CANDI run occurred.

## A2: why no valid twelve-file manifest exists yet

The original 75-file audit supplied all released-file hashes, official metadata, D/N/cutoff, intervals and numeric/label/prefix checks. Every released file was byte-verified again. Native provenance is now explicitly nullable and is NOT an eligibility blocker; all rows have source_family and native_provenance_unresolved fields. TSB inference must cluster by family first, and cannot establish H2/H3/H4a causal claims.

There are 37 eligible released rows after excluding 10 contaminated prefixes and 28 simulated-source rows (5 CATSv2 plus 23 GHL). These two exclusion sets do not overlap. Numeric/prefix audits were not relaxed. Exact duplicates and known original groups remain constrained to one selection each; known SMD overlap remains excluded. Native provenance remains unresolved for 60 of the 75 inventory rows, including already-excluded rows; the flag is preserved rather than interpreted as independent identity.

The first provisional assignment had twelve files, ten families, and repeated SMD three times. Subsequent source-type verification established that GHL is also simulated. The original dataset authors describe generating data with a Modelica model of a gasoil plant in [their abstract](https://arxiv.org/abs/1612.06676). This is not an experimental outcome and is not a change to the no-synthetic rule. The correction and primary-source snapshot are preserved. The original strict report is not rewritten.

The provisional files are retained under `rejected_provisional/` for transparency and MUST NOT be used. After excluding GHL, the unchanged global integer solver reports infeasibility. `manifest.json` is consequently an empty array and `selection_summary.json` reports STOP_A2, not PASS. No valid selected twelve-series set or valid repeated-family counts can be reported.

Exact conflicting requirements:

- periodic has exactly three eligible files, all SMD: 059_SMD_id_3_Facility_tr_757_1st_857.csv (machine-2-3), 065_SMD_id_9_Facility_tr_737_1st_837.csv (machine-1-7), 075_SMD_id_19_Facility_tr_564_1st_664.csv (machine-2-7).
- random_walk has SMD, OPPORTUNITY and Exathlon available before allocation. The committed hard rule requires three families, one each.
- Its SMD choices are exactly those three periodic files, and released files cannot be reused. All three are consumed by periodic. Therefore no solution exists.

This STOP is caused by the hard standalone bucket-diversity constraint plus the corrected synthetic exclusion, not by unresolved native provenance. A feasible-direction proposal for later review is to maximize within-bucket diversity subject to **global** feasibility, allowing a 2+1 split when all candidates of a third family are necessarily consumed by another bucket. That change is NOT implemented; no silent exception was made after freezing the rule.

## Rejected provisional list — NOT SELECTED / NOT FOR EXPERIMENTS

| Bucket | Released filename | Family | Native unresolved |
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
| random_walk | 032_GHL_id_1_Sensor_tr_50000_1st_65001.csv | GHL — simulated, excluded | true |
| random_walk | 129_OPPORTUNITY_id_1_HumanActivity_tr_1801_1st_1901.csv | OPPORTUNITY | true |
| random_walk | 188_Exathlon_id_15_Facility_tr_12538_1st_12638.csv | Exathlon | true |

All original multi-tags and provenance caveats, including the catalog CreditCard contradiction and Exathlon duplicate group, are retained in the JSON inventory. No original mapping was invented. `SHA256SUMS` seals current A2 artifacts, including the explicitly rejected provisional record.

Phase B CPU work is separately authorized by v3 and completed as scaffolding; see `../phase_b/README.md`. No model-result files were inspected and no GPU training ran. Provenance web searches exposed unrelated published performance snippets, not local model-result files; no such numbers were used in selection. Only primary-source dataset-origin information supports the correction.
