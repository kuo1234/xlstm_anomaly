> **v0.4 更正說明（2026-09-30）**：本報告為 2026-09-29 的歷史紀錄。依 #12 的二次審查：
> - G4c 的廣義版本已被佔據（Tip-Adapter、CLAP-S）。
> - G4d 出現新威脅（iADCPS arXiv:2504.04374、Axle Sensor Fusion arXiv:2602.16101、Wang et al. 2023 10.1109/TIM.2023.3265118）。
> - CARE 改用 v6，而且不能用於跨事件的時間順序實驗。
> - 目前主張見 `../proposal_v0.4.md` §5，最接近的文獻見 `v0.4_closest_competitors.json`。

# Task A Gap Audit: Universal / Few-Shot Time-Series Anomaly Detectors for Machines

*Audit date: 2026-09-29. Coverage target: 2023-2026 including arXiv through September 2026.*
*Scope: this audit is additive to the prior CTAP-directions-2/3 audit already on record for this project
(memory search: "Thesis-topic audit 2026-09-29"). Prior art already mapped there (CANDI, COMET, M2N2, MemStream,
METER, AnDri, ADAPTS, SCALE, Du et al. CCS 2019, selective-TTA papers, COLDSTART, xLSTMAD) is cited here only
where it directly informs a Task-A gap verdict; it was not re-audited from scratch. CANDI, AnDri and MemStream
were re-verified with a fresh lookup in this session (see fs_detector_papers.json) because they bear directly on
gaps G4a/G4d; the others are cited as previously-mapped context per the task's own instruction.*

## 1. Method summary by sub-area (Task A items 1-5)

### 1.1 Universal / foundation / zero-shot TSAD (item 1)
DADA (ICLR 2025) is the clearest "general time series anomaly detector" candidate: a frozen backbone
(adaptive-bottleneck encoder + dual adversarial decoders) pretrained on ~400M points from a dozen-plus
heterogeneous series and applied **zero-shot** at test time on SMD/MSL/SMAP/SWaT/PSM/UCR, several of which
are genuine industrial/machine series (SMD = server-machine telemetry, SWaT = water-treatment process control).
MOMENT, UniTS, Timer and Timer-XL are general time-series foundation models (forecasting-first, multi-task,
or generative-pretrained) whose anomaly-detection use is a downstream head rather than the primary design
target. AnomalyBERT is a strong per-dataset self-supervised transformer trained with synthetic data degradation,
not a single reusable frozen model. LLM-prompting detectors (DSAA 2024 "Can LLMs be Anomaly Detectors for
Time Series?", and its Findings companion) show zero-shot LLM scoring is feasible but weaker than dedicated
models. TAB (VLDB 2025) is the most comprehensive current benchmark harness for comparing all of the above
plus classical/deep/LLM/pretrained methods on 29 multivariate + 1635 univariate series; it is useful as an
evaluation harness/baseline source, not a new detector. None of these ship a non-parametric cache or an explicit
few-shot commissioning protocol for a brand-new machine — they are all either fully zero-shot-frozen or
fully retrained per dataset.

### 1.2 Few-shot / cross-machine / cross-domain TSAD (item 2)
The DCASE Task 2 lineage (2021→2024) is the best-developed few-shot cross-machine benchmark in any modality:
2021-2022 establish domain-shift and domain-generalization requirements over MIMII/MIMII-DG/ToyADMOS2 machine
sounds; the 2023 domain-generalization baseline and the 2024 "first-shot" task description explicitly formalize
"one section of normal samples per new machine type, no per-machine hyperparameter tuning" — i.e., exactly the
few-shot-commissioning-without-tuning scenario the lead's design targets, just in the acoustic modality. Published
top DCASE systems are typically a shared frozen embedding extractor scored by cosine-similarity/kNN against the
few given reference embeddings per machine — a real-world, competition-validated instance of an "L0 cache-only"
detector. On the vibration/rotating-machinery side, meta-transfer learning (Knowledge-Based Systems 2023) and
early few-shot metric learning (IEEE Access 2019) give few-shot **fault classification** into a fixed, named
fault taxonomy via weight adaptation (meta-learning), not open-set anomaly detection with a frozen backbone.

### 1.3 Memory-bank / kNN detectors (item 3)
PatchCore (CVPR 2022) is the reference training-free coreset-memory detector, and "Optimizing PatchCore for
Few/many-shot Anomaly Detection" (2023) is the closest published precedent to the lead's cache: it studies
exactly how a single fixed nominal-only memory bank degrades as the shot budget shrinks (1-/5-/10-shot) and
proposes recovery tricks. FR-PatchCore improves the memory bank's feature robustness. All of this work is
in the **image** domain (MVTec/VisA), builds one static nominal memory once, and has no fault cache, no
operator-feedback loop, and no online eviction/maintenance policy — the whole "cache lifecycle after
deployment" question this project is aimed at is outside PatchCore's scope. MemStream (WWW 2022, already
mapped) is the closest streaming/time-series analogue: an online, self-updating normal memory for streaming
records, but the update is gated by the model's own classification, not by delayed confirmed operator
feedback, and it is not evaluated on machine condition monitoring.

### 1.4 Continual / open-set fault diagnosis and continual AD with new classes (item 4)
UCAD (AAAI 2024) is architecturally the closest analogue to a maintained normal-cache-per-context design: a
small key-prompt-knowledge memory bank retrieved by nearest-key lookup, with SAM-guided contrastive learning
to keep per-task normal knowledge separated. But its "tasks" are discrete, experimenter-labeled object classes
introduced with an explicit training step each — there is no organic drift/new-fault discovery, no operator
feedback, and the domain is industrial **images**, not sensor time series. IUF (ECCV 2024), ReplayCAD
(IJCAI 2025) and ONER (2024) are further continual-AD variants (feature-conflict reduction, diffusion replay,
online experience replay respectively) — all vision-domain, all requiring some backprop/replay step per new
class rather than training-free retrieval. AnDri (already mapped) — activate/deactivate/add normal-pattern
pools under concept drift — is the single closest conceptual analogue to a *maintained normal cache with
lifecycle operations* found in this sweep, but it has no paired fault cache and no operator-feedback gating.
The 2026 continual-AD survey independently flags streaming/non-stationary-normality handling as an open
research direction, corroborating that this remains unsettled at the field level, not merely in this
project's prior narrower audit.

### 1.5 Few-shot operating-point / threshold calibration (item 5)
"From Zero to Hero: Cold-Start Anomaly Detection" (Findings of ACL 2024) is the most directly relevant
published framing beyond COLDSTART: it names exactly the "zero-shot-initialized detector receives a small
number of contaminated observations" setting and proposes ColdFusion plus an evaluation protocol/suite for it.
However the domains used are general OOD/AD benchmarks (not machine sensor time series), the adaptation is a
single step (not an ongoing multi-year deployment), and there is no fault-vs-normal cache split or explicit
FPR-operating-point reliability analysis of the kind COLDSTART already performs with conformal calibration on
voraus-AD/AURSAD. No other conformal-prediction-for-new-equipment-threshold paper surfaced at this search depth.

## 2. Gap verdicts

| id | statement | verdict |
|----|-----------|---------|
| G4a | frozen universal TS anomaly detector + training-free few-shot target cache (Tip-Adapter-style fusion) for commissioning a NEW machine | **PARTIALLY_OCCUPIED** |
| G4d | one mechanism that both absorbs benign machine aging into the normal reference AND learns emerging new fault types few-shot, evaluated for false absorption of faults | **OPEN_AT_SEARCH_DEPTH** |
| G4e | few-shot operating-point (FPR/threshold) reliability of a cache-based detector on a new machine | **PARTIALLY_OCCUPIED** |
| G4f | evaluation of such a system on real machine data over a long deployment horizon (months+) with aging and multiple fault types | **OPEN_AT_SEARCH_DEPTH** |

**G4a — evidence.** The individual halves exist and are each well validated separately, but not fused into one
system evaluated on machine sensor time series. DADA supplies a validated frozen universal TS backbone applied
zero-shot to machine series (SMD, SWaT). PatchCore + its few-shot variant, and DCASE's frozen-embedding +
kNN/cosine-scoring first-shot baselines, supply validated training-free few-shot memory/cache scoring on top of
a frozen backbone — DCASE's baseline is arguably a real-world, competition-tested existence proof of "L0
cache-only commissioning" for machines, just in the acoustic modality with a single fixed reference set and no
explicit Tip-Adapter-style learned fusion weight. No source in this sweep combines a frozen general multivariate
sensor-time-series backbone with an explicit two-cache (normal+fault) Tip-Adapter-style fused score, evaluated on
multivariate rotating-machinery / process-plant data. Blocking/most-overlapping papers: DADA (arXiv:2405.15273),
"Optimizing PatchCore for Few/many-shot AD" (arXiv:2307.10792), DCASE 2024 Task 2 description
(arXiv:2406.07250) and its 2023 domain-generalization baseline (EUSIPCO 2023).

**G4d — evidence.** No paper in this sweep, nor in the prior direction-2/3 audit on record, presents a single
mechanism that is evaluated on *both* (i) correctly folding benign slow drift into the normal reference over
time and (ii) few-shot-learning a genuinely new fault type from sparse confirmations, with an explicit metric
for *false absorption* of a real fault into the normal cache. AnDri's activate/deactivate/add normal-pattern
pool is the closest structural analogue but is not paired with a fault-side cache or feedback-gated fault
recall test. UCAD/IUF/ReplayCAD/ONER handle sequential *new normal classes* but as experimenter-labeled tasks
with a training step, not organically-arriving drift, and do not report a false-absorption-of-faults metric.
The 2026 continual-AD survey names this combination as an open direction at the field level, independent of
this project's own audit, which strengthens the OPEN verdict beyond "we didn't find it" to "the field agrees
it isn't solved yet." Queries run (this session, beyond the item-specific ones logged in section 3): "benign
drift versus fault distinguish anomaly detection sensor", "sensor drift adaptation online anomaly detection
industrial", "DNE anomaly detection dynamic normal expansion continual" (no relevant, non-duplicate hit).

**G4e — evidence.** ColdFusion (Findings ACL 2024) and COLDSTART (already mapped; conformal calibration on
voraus-AD/AURSAD) both directly study few-shot/zero-shot-initialized operating-point reliability, and DCASE's
first-shot task explicitly forbids per-machine hyperparameter tuning, implicitly forcing a few-shot-robust
operating point. This sub-gap is therefore better covered than G4a suggests at the *concept* level; what
remains open is machine-sensor-time-series-specific coverage combined with a maintained two-cache design — no
paper couples few-shot threshold reliability to an explicitly evolving normal+fault cache pair, which is why it
is still listed as an open combination in the framing below even though the isolated threshold-calibration
problem is PARTIALLY_OCCUPIED.

**G4f — evidence.** No paper found evaluates a commissioning-then-cache-adaptation TSAD system on real machine
data over a genuine months-to-years deployment horizon with both aging and multiple distinct fault types
realized in the data. DCASE's protocol is a single train/eval snapshot per machine (no longitudinal
re-evaluation); MIMII-DG's domain shifts are induced experimentally (speed/load changes), not naturally
elapsed time; UCAD/IUF/ReplayCAD's "increments" are experimenter-sequenced object classes, not calendar time.
This matches and reinforces G2e from the prior audit (zero-shot TSFM vs. online-adapted models over multi-year
machine drift) and is consistent with CARE-to-Compare / Kelmarsh-Penmanshiel wind SCADA being flagged in the
prior audit as the rare real, multi-year, multi-fault-type machine dataset capable of testing this.

## 3. Closest competitors (method + evaluation, read in full)

See `closest_competitors` in the structured output and the `verification_level: full_text` rows of
`fs_detector_papers.json` for: DADA, TAB benchmark, "Optimizing PatchCore for Few/many-shot AD", UCAD,
"From Zero to Hero: Cold-Start Anomaly Detection". IUF and DCASE 2024 Task 2 PDFs were also downloaded to the
workspace (`articles/IUF_2312.08917.pdf`, `articles/DCASE2024Task2_2406.07250.pdf`) but characterized here from
their OpenAlex/arXiv abstracts (verification_level: abstract) rather than a full read, given the time budget for
this pass — noted as a deviation below.

## 4. Candidate machine datasets for evaluation

| dataset | multiple units? | multiple labeled fault types? | aging / long horizon? | fit for this thesis |
|---|---|---|---|---|
| **DCASE/MIMII(-DG) + ToyADMOS2** | Yes — several machine types (fan, pump, valve, slider, gearbox, bearing) x several individual units per type | Partial — "anomalous" is often a single coarse label per recording rather than multiple named fault classes, though some releases distinguish fault mechanisms | No — snapshots per domain condition, not longitudinal | Best fit for validating the **cross-machine few-shot commissioning** axis (G4a/G4e) at low engineering cost; weakest for the aging/G4d/G4f axis. |
| **CARE-to-Compare wind SCADA (Zenodo 14006163)** | Yes — many turbines across multiple wind farms | Yes — multiple documented fault/event categories with expert labels | Yes — multi-year SCADA logs per turbine | Best overall fit for the **same-machine aging + new-fault-type + long-horizon** axis (G4d/G4f); already the backbone of the prior direction-2/3 proposal, and reachable in this session (Zenodo API responded 200). |
| **Tennessee Eastman Process (TEP)** | Partial — one plant simulator, but many independent simulation runs/seeds can stand in for "units" | Yes — the classic TEP benchmark ships ~20 distinct programmed fault types | No — simulated runs are short episodes, not calendar-time aging | Good complementary benchmark for **new-fault-type few-shot recall** (many clean, named fault classes) but not for real sensor drift or true units; simulated, not physically measured. |
| **PRONOSTIA / XJTU-SY bearing run-to-failure** | Yes — multiple bearings run under different operating conditions (XJTU-SY: 15 bearings x 3 conditions) | Limited — labels are mostly "degrading toward failure," not distinct fault-type categories | Yes — each unit's run-to-failure trace is itself a long degradation/aging horizon | Good fit for **within-unit aging/degradation absorption**, weak for the multi-fault-type recall side; good stress test of "don't let real degradation get labeled a false alarm forever." |
| **MetroPT-3** | No — one metro-train compressor's air-production-unit sensors | Partial — failures are logged but not finely typed | Yes — continuous real operational logs over an extended period | Useful single-unit long-horizon real deployment sanity check; too small alone to test cross-machine few-shot commissioning. |
| **CWRU bearing dataset** | Yes — multiple bearings, multiple fault locations/severities, multiple load conditions | Yes — inner-race/outer-race/ball fault at several severities is the standard taxonomy | No — short controlled-lab recordings, no real aging | The most standardized few-shot **fault-diagnosis** baseline for reviewers to recognize, but a lab dataset with no genuine long-horizon aging; best used as a sanity-check/reviewer-familiar baseline, not the main evaluation. |

Dataset availability was checked with light HTTP requests only (Zenodo API record lookups, a GitHub mirror
listing, and search-engine confirmation for CWRU/TEP hosting pages that were not directly reachable from this
sandbox's network allowlist) — no bulk data was downloaded.

## 5. Recommended framing (given the audit)

The strongest, least-occupied thesis framing coming out of this Task-A sweep is **not** "build the frozen
backbone + two-cache commissioning system" in isolation — DADA-style frozen backbones and PatchCore/DCASE-style
few-shot cache scoring are each already validated, so a system that just concatenates them would mostly be
demonstrating known pieces on a new (machine-sensor) domain. The open contribution is the **cache lifecycle
under real deployment dynamics**: a normal+fault cache pair maintained by delayed, partially-confirmed operator
feedback, evaluated explicitly for (i) false absorption of real faults into the normal reference, (ii) recall of
genuinely new fault types after k confirmations, and (iii) stability of the operating point (FPR) as both caches
evolve — on real multi-unit machine data with an actual long horizon (CARE-to-Compare / MIMII-DG combination, or
CARE-to-Compare alone if cross-machine few-shot commissioning is de-scoped to a secondary experiment). This is
consistent with, and sharpens, the G4d/G4f open gaps identified above and the G3a/G3b gaps already on record from
the prior retrieval-augmented-forecasting audit.

## 6. Main threats to this framing

- **Non-identifiability without feedback** (already observed in the user's own repo): benign new-normal vs.
  persistent fault is not separable from the raw signal alone, so any false-absorption evaluation must build in
  a believable operator-feedback delay/noise model — get that model wrong and the results won't generalize.
- **DCASE's first-shot baselines already show that "frozen backbone + kNN cache, no tuning" is a strong, cheap
  solution for cross-machine commissioning** in the acoustic modality; the thesis needs to show its problem
  (lifecycle maintenance) is where a naive cache-only baseline breaks, not re-litigate whether cache-only
  commissioning works at all.
- **Real long-horizon multi-fault-type machine datasets are scarce** — CARE-to-Compare is close to a "gold"
  fit but is a single domain (wind turbines); generalization claims across "rotating machinery" broadly will
  need at least one second real dataset (e.g., MetroPT-3 or a CWRU/XJTU-SY bearing degradation trace) to avoid
  over-fitting the narrative to wind SCADA idiosyncrasies.
- **Benchmarks like TAB show foundation/pretrained TS methods are not yet dominant on multivariate industrial
  series**, so claims that hinge on "the frozen backbone is strong enough that only the cache needs research"
  should be empirically checked on the chosen dataset before committing the thesis to that framing.
