# P5-0B1 PreDist v2 structural preflight — STOP

**Final status: `LABEL_BOUNDARY_BREACH`**
**Branch:** `research/p5-0b1-predist-structural-preflight`
**Base SHA:** `209e1f55ee19bbaf71ee6e658938e4e14788ad46`

## Incident and stop decision

The official PreDist v2 archive was downloaded and its archive checksum matched Zenodo's published MD5. The ZIP central directory was inspected for member paths and byte sizes. Static configuration and feature-description metadata were opened as allowed.

During a broad read of the archive's root `README.md`, the complete README was printed. It includes a table of known, unlabelled anomaly time intervals. That is semantic anomaly-outcome metadata and may fall within the handoff's forbidden event/anomaly information boundary. We therefore conservatively record a **`LABEL_BOUNDARY_BREACH`** and stopped immediately. No label/event CSV payload was opened or parsed; no raw operational time-series payload was parsed; no split or horizon recommendation was produced.

This status supersedes the four normal P5-0B1 gate outcomes. It is not a structural GO or an efficacy authorization. The archive remains in `/tmp`, outside the repository.

## Work performed before the stop

- Verified official record 19496480, version v2, publication date 2026-04-10, CC BY 4.0, archive filename, expected size, and expected MD5 from Zenodo metadata.
- Downloaded `predist_dataset.zip` from the version-specific official content URL. The archive size is 266,814,500 bytes; SHA-256 is `bbd95677835110a953146441f2215ad4ebd207bf3aca70496ce799605cfc218e`; MD5 is `298b6425df12ee0d93c05bd67efa3b75`, matching Zenodo.
- Read only the ZIP central directory for paths and compressed/uncompressed sizes. Six obvious label/event tables were identified; their payloads and hashes were not accessed.
- Opened the first rows of `configuration_types.csv` and `feature_descriptions.csv` for each manufacturer.
- Printed the root README, including its known-anomaly interval table. This is the boundary incident described above.

## Not produced

No entity manifest, schema/horizon audit, candidate role split, parser scripts, or parser tests were produced. These require continuing the structural audit after the stop point and could turn the incident into unauthorized downstream analysis. Do not resume from this branch without a new explicit review/task defining the incident disposition and the safe source boundary.

No raw data archive, observation rows, or label-table payload was committed. No model, GPU, or efficacy run was performed. Tests were not run because no scripts were created after the mandatory stop.

## References

- [Official Zenodo v2 record](https://zenodo.org/records/19496480)
- [Version-specific official archive endpoint](https://zenodo.org/api/records/19496480/files/predist_dataset.zip/content)
- [P5-0B1 handoff comment](https://github.com/kuo1234/xlstm_anomaly/issues/9#issuecomment-5854357432)
