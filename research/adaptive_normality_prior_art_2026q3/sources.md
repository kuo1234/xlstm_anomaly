# Sources and evidence register

**Cutoff:** 2026-09-26. The primary link is preferred. DOI, proceedings, official repository, and institutional records are included where available. Evidence wording is deliberately conservative where the full text or implementation could not be inspected.

| ID | Source | Evidence class | Links | Audit note |
|---|---|---|---|---|
| S01 | M2N2 | AAAI 2024 paper; official code | [AAAI proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/29210), [arXiv](https://arxiv.org/abs/2312.11976), [code](https://github.com/carrtesy/M2N2) | Supports predicted-normal-masked online gradient adaptation and trend estimation. |
| S02 | CANDI | AAAI 2026 paper; official code | [AAAI paper](https://ojs.aaai.org/index.php/AAAI/article/view/38524), [PDF](https://ojs.aaai.org/index.php/AAAI/article/download/38524/42486), [code](https://github.com/kimanki/CANDI) | FPM reference-bank filtering and SANA residual adaptation; backbone/latent space frozen. |
| S03 | MemTTA for TSAD | Master’s thesis catalog and PDF | [Korea University record](https://dcollection.korea.ac.kr/srch/srchDetail/000000308007), [PDF](https://dcollection.korea.ac.kr/public_resource/pdf/000000308007_20260621234921.pdf) | Thesis evidence only. Memory and gradient gate described; exact write ordering and lifecycle not verified. |
| S04 | MemStream | WWW 2022 paper; official code | [arXiv](https://arxiv.org/abs/2106.03837), [code](https://github.com/Stream-AD/MemStream), DOI 10.1145/3485447.3512221 | Score-before-write threshold and FIFO normal embedding memory. |
| S05 | METER | PVLDB 2024 paper; code | [PVLDB PDF](https://www.vldb.org/pvldb/vol17/p794-zhu.pdf), [code](https://github.com/zjiaqi725/METER), DOI 10.14778/3636218.3636233 | Unknown output, uncertainty accumulation and window-triggered offline update; paper text inspected. |
| S06 | AnDri | 2025 extended report; CIKM system demo; official code | [arXiv](https://arxiv.org/abs/2506.15831), [author PDF](https://www.cas.mcmaster.ca/~fchiang/pubs/andri.pdf), [code](https://github.com/mac-dsl/AnDri), CIKM DOI 10.1145/3746252.3761481 | Pattern candidates, normal admission, active/inactive patterns and reactivation. Extended report is preprint evidence; demo is peer-reviewed system evidence. |
| S07 | ARCUS | KDD 2022 paper; official code | [author paper](https://bslee.w3.uvm.edu/papers/ARCUS_KDD2022.pdf), [code](https://github.com/kaist-dmlab/ARCUS), DOI 10.1145/3534678.3539348 | Adaptive autoencoder pool and concept model reuse. |
| S08 | Drift-aware online AD for smart buildings | ACM e-Energy 2026 paper; code | [DOI/paper](https://doi.org/10.1145/3744255.3811742), [code](https://github.com/illinois-arcs/Drift-Aware_AD) | TCN-VAE, gradient classifier, labeled bootstrap, buffered persistent drift updates. |
| S09 | MD-RS | npj Artificial Intelligence 2026 paper; code | [Nature article](https://www.nature.com/articles/s44387-026-00090-6), [code](https://github.com/hiroto0324/MD-RS), DOI 10.1038/s44387-026-00090-6 | Recurrent reservoir state trajectory scored against normal Gaussian fit; no adaptive lifecycle. |
| S10 | xLSTM | NeurIPS 2024 paper; official code | [NeurIPS paper PDF](https://papers.neurips.cc/paper_files/paper/2024/file/c2ce2f2701c10a2b2f2ea0bfa43cfaa3-Paper-Conference.pdf), [code](https://github.com/NX-AI/xlstm) | Architecture source, not an anomaly regime method. |
| S11 | xLSTMAD | ICDM 2025 paper; official code | [arXiv](https://arxiv.org/abs/2506.22837), [code](https://github.com/Nyderx/xlstmad), DOI 10.1109/ICDM65498.2025.00032 | xLSTM TSAD forecasting/reconstruction. Inference reset statement is limited to the audited official reconstruction path. |
| S12 | MEMTO | NeurIPS 2023 paper; code | [OpenReview PDF](https://openreview.net/pdf?id=UFW67uduJd), [code](https://github.com/gunny97/MEMTO) | Offline learned normal prototypes guide reconstruction. |
| S13 | MemMambaAD | Engineering Applications of AI 2025 | [ScienceDirect DOI](https://doi.org/10.1016/j.engappai.2025.111308) | Memory-augmented SSM for image anomaly detection; code not verified. |
| S14 | PAMA | SSRN 2026 preprint / under-review manuscript | [SSRN abstract](https://papers.ssrn.com/sol3/abstract/6486773), DOI 10.2139/ssrn.6486773 | Posted 2026-03-28. Any journal item dated 2026-10-25 is future relative to this cutoff and excluded. |
| S15 | PADRE | IJCAI 2026 paper | [IJCAI proceedings](https://www.ijcai.org/proceedings/2026/503), DOI 10.24963/ijcai.2026/503 | Online forecasting, regime-conditioned residual Pattern Bank and evidence-consistency update gate. |
| S16 | Orthogonal LoRA Banks for continual industrial AD | Neurocomputing 2026 journal record; arXiv preprint | [arXiv](https://arxiv.org/abs/2606.02042), DOI 10.1016/j.neucom.2026.135021 | Journal available online 2026-09-03; image categories and task structure. Code not found. |
| S17 | CoTTA | CVPR 2022 paper; official code | [CVF paper](https://openaccess.thecvf.com/content/CVPR2022/html/Wang_Continual_Test-Time_Domain_Adaptation_CVPR_2022_paper.html), [code](https://github.com/qinenergy/cotta) | Source-weight stochastic restoration during TTA. |
| S18 | Markovian RNN | 2020 arXiv preprint | [arXiv](https://arxiv.org/abs/2006.10119) | Regime-specific recurrent cells selected by Markovian regime model; not AD. |
| S19 | COMET for TSAD | 2026 arXiv preprint | [arXiv](https://arxiv.org/abs/2602.01635) | Normal codebook/memory distance and pseudo-label online codebook adaptation; code not verified. |
| S20 | Validation-gated continual learning for satellite telemetry AD | Acta Astronautica 2026 journal record | DOI 10.1016/j.actaastro.2026.07.065 | Model candidate validation before deployment; exact public repository URL not recovered. |
| S21 | Safety-Gated CL for Drift-Aware AD in CPS | ICAISET 2026 proceedings metadata/abstract | DOI 10.1109/icaiset66439.2026.11541767 | Only abstract-level mechanism verified; other matrix cells intentionally unknown. |
| S22 | HTM + SPRT | 2025 arXiv preprint | [arXiv](https://arxiv.org/abs/2504.18599) | Sequential drift/anomaly decisions; adjacent, not a recurrent normal-regime bank. |
| S23 | SCALE, online latent-domain MTSAD | ACM 2026 metadata/abstract lead, unresolved | DOI 10.1145/3770855.3817912 | The exact ACM source and full text were not retrieved. Existing project notes mention sparse likelihood regret, counterfactual residuals and expert pool; treat only as a high-priority lead. |
| S24 | EATA | ICLR 2022 paper; code | [OpenReview](https://openreview.net/forum?id=A9g_BgNTE4), [code](https://github.com/mr-eggplant/EATA) | Entropy/diversity sample selection and forgetting regularization for TTA; general, not TSAD. |

## Repository and protocol sources

- Project issue #1: [adaptive-normality prior-art audit](https://github.com/kuo1234/xlstm_anomaly/issues/1).
- Project research constraint: [reports/m0_protocol.md](../../reports/m0_protocol.md).
- Issue-branch base at start: origin/main commit 537fc7d4a15ae603f285c3511b80ce0c0eba3e99.

## Search and access caveats

This is not an exhaustive systematic review. It prioritizes the papers named in the issue, citation-near methods, and records relevant to online TSAD, memory gating, concept drift, recurrent-state AD, and continual normality protection. The SCALE full-text lead, Safety-Gated CL paper details, and MemTTA update ordering require follow-up. Exact claims tied to those records are therefore qualified in the matrix and inventory.
