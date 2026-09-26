# License audit

Status checked 2026-09-26. This is a source-document audit, not legal advice. A public URL or accessible archive does not grant reuse rights. Code license, article license, and data license are separate.

| Dataset | Data license evidence | Status for research reuse |
|---|---|---|
| E-Energy smart buildings | Official GitHub API metadata returned no repository license; repository contains no LICENSE file. The paper and public CSV links do not supply an explicit data license in the reviewed sources. | **Unresolved; blocking.** Obtain written/explicit dataset terms before downloading for reuse or redistribution. |
| PreDist | 2026 paper and current Zenodo record state CC BY 4.0. | **Clear with attribution and license terms**, subject to checking the exact record/file license at acquisition. |
| Extended TEP | DTU publisher record lists CC0 1.0. | **Clear on the publisher listing**, retain attribution/provenance and verify file-level terms. |
| NoBOOM | Dataset paper identifies CC BY-SA 4.0 for the dataset. Official code repository has a separate MIT license. | **Clear with share-alike obligations** for the data; do not substitute the code license. Confirm the selected mirror is the same release. |
| Batch Distillation | Paper/current record and companion data repository identify CC BY 4.0. | **Clear with attribution**, but verify the chosen subset and any third-party modalities' notices. |
| C-MAPSS | Data.gov public catalog record offers a resource; NASA Open Data page says license unspecified and resource unavailable. | **Unresolved/conflicting portal metadata.** Do not assume a general US government public-domain rule resolves the data's reuse conditions. |
| PATH | Dataset card/paper repository identifies MIT for the dataset release; arXiv paper links to a Zenodo archive. | **Appears clear under MIT**; verify that current Zenodo files correspond to the card/release and retain notices. |
| SWaT | iTrust page uses request-controlled access; terms govern access. A public open-data license was not established in the reviewed page. | **Restricted/unresolved for reuse.** Obtain and follow current access agreement; do not redistribute. |
| WADI | iTrust request-controlled access; a dataset-specific open license was not established by reviewed source. | **Restricted/unresolved for reuse.** Obtain current terms and version-specific authorization. |
| BATADAL | Challenge page content is CC BY 4.0; reviewed source did not conclusively establish that the underlying data package has the same license. | **Data license unverified.** Confirm package-specific terms before acquisition/reuse. |
| Google Borg ClusterData 2019 | Official repository describes the trace release under CC BY. | **Appears clear with attribution**, subject to current repository terms and privacy/use conditions. |
| UCI Electricity Load Diagrams | Current official UCI dataset page identifies CC BY 4.0. | **Clear with attribution**; verify the downloaded archive/version and retain citation. |
| DAYPSCI | Article metadata identifies the paper, but this audit did not locate/verify the data repository license or access conditions. | **Unresolved.** Locate publisher-linked data record and verify license before download or use. |
| SMD | Existing project protocol governs this audit; no new source/license review or data access was done. | **Out of scope for this issue audit.** Follow existing project restrictions and do not inspect unopened labels. |

## Decision impact

The strongest direct real-data semantic candidate, E-Energy, is not cleared for reuse by the sources reviewed. PreDist and Batch Distillation have clear CC BY terms, NoBOOM is share-alike, and TEP/PATH are listed as CC0/MIT respectively, but licensing alone does not remedy missing M6 semantics. For any release, cite upstream papers and records, preserve the data license, and separately review derived annotations and preprocessing code terms.
