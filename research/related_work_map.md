# Related-work map

Scope: 78 retrieved records across 16 families, 61 read in full text. Per-paper attributes and
verbatim supporting quotes are in `literature_records.json`; the compressed per-paper view and the
novelty conclusions are in `positioning_table.md`. This file is the reading map: what each family
established, what it did **not** establish, where to enter it, and why it matters here.

Evidence discipline used throughout: a paper read only at abstract or metadata level is marked as
such, and no mechanism absence is asserted from an unread paper. Family coverage (records / of which
full text): F1 7/6, F2 6/4, F3 10/5, F4 9/4, F5 2/2, F6 10/6, F7 9/8, F8 8/7, F9 8/8, F10 6/5,
F11 6/6, F12 4/4, F13 5/5, F14 7/5, F15 7/6, F16 14/9.

---

## Theme I — Adaptation under normality shift in multivariate TSAD

### F1. Curated / selective test-time adaptation for TSAD

**Established.** Test-time adaptation of a frozen reconstruction detector is worth doing under
normality shift, and *which* windows are adapted on matters more than how many. CANDI
(`10.1609/aaai.v40i17.38524`, AAAI 2026) selects adaptation windows by two internal criteria — anomaly
score above a validation percentile, and small Mahalanobis distance in the frozen encoder's latent
space to a reference set of high-scoring *normal validation* windows — and updates a lightweight
residual module rather than the detector. COMET (`arXiv:2602.01635`) reaches the same admission idea
without a threshold, using which codebook entries were activated during normal-only training.

**Not established.** That curation prevents contamination. CANDI's own analysis states that
adaptation is sometimes performed on mislabelled anomalous data and argues only for robustness to
moderate contamination, listing failure recovery as future work.

**Entry points.** CANDI → COMET → TAFAS (`10.1609/aaai.v39i17.33965`, the gated-calibration module
design in forecasting).

**Relevance.** This is the project's baseline family, and its open edge — contamination acknowledged
but never costed — is exactly where the project's contamination accounting sits.

### F2. "New normal" adaptation

**Established.** The field's default contamination guard is the detector's own score: M2N2
(`arXiv:2312.11976`, AAAI 2024) detrends with an EMA trend estimator and masks the test-time
reconstruction loss by one minus its own predicted anomaly label, so updates are computed only over
windows it currently believes normal. MemStream (`arXiv:2106.03837`, WWW 2022) had already gated
memory updates by a discounted KNN score threshold and handled drift by memory replacement, with a
proposition relating memory size to drift speed.

**Not established.** That any of these guards is sufficient. None measures the causal cost of an
admitted anomaly, and none defers an admission decision.

**Entry points.** M2N2 → MemStream → COMET.

### F3. Continual / streaming / online TSAD

**Established.** Two structural answers to non-stationarity dominate: maintain a pool or ensemble and
route (ARCUS, `10.1145/3534678.3539348`, KDD 2022, which spawns or merges models when the pool is
judged inadequate "presumably due to a concept drift"; METER, `10.14778/3636218.3636233`, PVLDB 2023,
which routes by evidential concept uncertainty), or maintain a memory of normal patterns and replace.
ReCATS (`10.1145/3770855.3817985`, abstract only) is the replay-free continual MTSAD anchor with
multi-regime modelling and BWT/FWT evaluation. The industrial-service literature
(`arXiv:1906.03821`, KDD 2019) documents deployment constraints but describes no mechanism for
excluding real anomalies from its update path.

**Not established.** Admission. In the task-incremental framing, what enters each task's training set
is defined by the benchmark rather than decided by the method.

**Entry points.** ARCUS → METER → ReCATS.

### F5. xLSTM, and xLSTM for anomaly detection

**Established.** Very little, and the thinness is itself informative. xLSTM (`arXiv:2405.04517`,
NeurIPS 2024) introduces exponential gating and a matrix memory and makes no claim about anomaly
detection, drift, or the information content of its internal states. xLSTMAD (`arXiv:2506.22837`,
ICDM 2025) is the only retrieved xLSTM-based anomaly detector: offline, no adaptation, no drift
handling, no use of internal state as evidence.

**Not established.** Anything about xLSTM gates carrying drift-relevant information — in either
direction. There is no published claim to inherit and no published refutation to overcome.

**Relevance.** The project's H3a is unoccupied territory. That is an opportunity for the measurement
and a liability for external validity: a two-paper literature offers no independent replication.

---

## Theme II — Drift, deferral and reversibility

### F4. Concept-drift detection and drift-aware anomaly detection

**Established.** A mature vocabulary (Gama et al., `10.1145/2523813`, bibliographic only) and a
critique of that vocabulary's inconsistency (Bayram et al., `10.1016/j.knosys.2022.108632`, which also
surveys *performance-aware* detectors that monitor model signals rather than input statistics). The
most relevant instance is STAD (`10.1016/j.datak.2024.102365`, abstract only): an autoencoder detector
that maps stream periods to discrete states and uses statistical tests, with a reported
sensitivity/power analysis, to decide transitions. Drift *attribution* is a separate line
(`arXiv:2310.15830`, permutation importance; DriftGuard `arXiv:2601.08928`, SHAP).

**Not established.** A public benchmark with per-timestamp drift-versus-anomaly ground truth. None was
found in this search — which is consistent with the project's own decision to answer the information
question synthetically.

**Entry points.** STAD → Bayram et al. → DriftGuard.

### F8. Quarantine, deferred decision, delayed commitment

**Established.** Deferral is more thoroughly explored than the project's framing implies, though
scattered across settings: METER accumulates concept uncertainty over a sliding window before an
offline update; the HTM+SPRT framework (`arXiv:2504.18599`, also `10.33889/IJMEMS.2025.10.3.039`)
binarises the detector's own likelihood output and runs a sequential probability ratio test over a
lagged window, restarting after each drift decision; Quilt (`arXiv:2312.09691`, AAAI 2024) waits for a
minimum number of post-drift samples before selecting training segments; a drift-aware online MTSAD
method (`arXiv:2604.09358`) excludes current-window samples from supervised updating and imposes a
detection cooldown; an RL-plus-human-feedback detector (`arXiv:2607.08373`) holds incomplete
transitions in a pending buffer until expert validation; and stream-based active learning has
formalised the delay itself as verification latency (`arXiv:2204.06822`).

**Not established.** What the deferral *bought*. None of these quantifies contamination avoided.

**Entry points.** HTM+SPRT → METER → Quilt.

**Relevance.** The project's "quarantine" is a construct with prior art. Its open edge is the
accounting, and — see `safe_adaptation_design_space.md` §1 — the requirement that the exit rule can
reject rather than merely delay.

### F9. Rollback, reset and restore in continual test-time adaptation

**Established.** Effectively solved for classification CTTA, and should be treated as prior art rather
than as an opportunity. CoTTA (`arXiv:2203.13591`) stochastically restores a fraction of trainable
weights to source values at every step; EATA (`arXiv:2204.02610`) combines entropy-based sample
exclusion with Fisher-weighted anti-forgetting regularisation; SAR (`arXiv:2302.12400`) resets
parameters when a moving average of entropy loss indicates collapse; PETAL (`arXiv:2212.09713`)
restores parameters selected by the diagonal Fisher information matrix; RDumb (`arXiv:2306.05401`)
shows a fixed periodic reset to pretrained weights beats most of the field on long streams; adaptive
selective reset (`arXiv:2603.03796`, ICLR 2026) makes both *when* and *where* to reset a function of
prediction concentration and its EMA; RDumb++ (`arXiv:2601.15544`) triggers full or soft resets from
entropy- and KL-based drift detectors.

**Not established.** Reset *semantics* under unsupervised normality change. Every one of these reverts
toward a **fixed source model**; none reverses a single normality commitment while preserving a
legitimately learned new normal.

**Entry points.** RDumb → adaptive selective reset → PETAL.

### F14. Distinguishing anomaly from benign distribution shift

**Established.** The conceptual separation is settled — the generalized OOD survey
(`arXiv:2110.11334`) separates covariate shift from semantic shift and notes that most
anomaly-detection settings assume a clean in-distribution training set. Operationally, SCALE
(`10.1145/3770855.3817912`, abstract only) is the most direct: online separation of domain drift from
true anomalies using two decoupled model-derived criteria with claimed theory. STAD does it with
statistical tests over reconstructions; HTM+SPRT with a sequential test over binarised likelihoods;
anytime-valid gating (`arXiv:2608.30502`) with a decision table over a conformal test martingale.
AnoShift (`arXiv:2206.15476`, NeurIPS 2022 D&B) supplies a distribution-shift benchmark for
unsupervised AD but evaluates degradation, not separation.

**Not established.** How much information any particular internal signal carries about the
distinction — because none of these measures the separation as a prediction problem against
timestamp-level truth.

**Entry points.** SCALE → generalized OOD survey → AnoShift.

**Relevance.** This family contains the project's closest framing prior art, and the gap it leaves is
precisely the project's measurement question.

### F15. Uncertainty-guided and conformal / sequential-test-guided adaptation

**Established.** The statistical machinery for "wait for more evidence" is available off the shelf and
is already wired into adaptation loops: a conformal uncertainty indicator for CTTA
(`arXiv:2502.02998`); anytime-valid gating (`arXiv:2608.30502`) which uses a filter's own standardised
innovation as the nonconformity score of a conformal test martingale and maps the martingale state
onto a four-way action table with reset-on-fire; segmented confidence sequences (`arXiv:2508.06638`)
giving time-uniform thresholds under arbitrary stopping; METER's evidential (Dirichlet) routing.

**Not established.** That any of these gates improves *anomaly-detection* outcomes under
contamination. The martingale paper in particular reports no detection-quality evaluation.

**Entry points.** Anytime-valid gating → segmented confidence sequences → conformal uncertainty
indicator.

**Relevance.** This is the family the project should borrow its operating point from rather than
inventing a threshold; see design-space F1/F3.

---

## Theme III — Selection, memory and continual anomaly detection

### F7. Selective adaptation, selective update, sample selection

**Established.** Selection by model-internal confidence is the dominant pattern: entropy-based sample
exclusion plus Fisher regularisation (EATA), reliability filtering with sharpness-aware updates (SAR),
instance-wise BN statistics with a prediction-balanced reservoir against temporal correlation
(NOTE, `arXiv:2208.05117`), high/low-quality sample partitioning with positive/negative learning
(DSS, `arXiv:2310.03335`), and the finding that entropy alone is insufficient under
spurious-correlation shift, motivating disentangled-factor criteria (DeYO, `arXiv:2403.07366`) and
entropy-plus-gradient-norm combinations (ETAGE, `arXiv:2409.09251`).

**Not established.** Anything about *unsupervised anomaly* admission, where the error mode is not a
wrong pseudo-label but a true fault being written into normality.

**Entry points.** EATA → DeYO → NOTE.

### F10. Replay-based and replay-free continual anomaly detection

**Established.** Forgetting mitigation under known task boundaries: ReplayCAD (`arXiv:2505.06603`,
IJCAI 2025) synthesises old-task samples with a diffusion model; ONER (`arXiv:2412.03907`) replays
image- and pixel-level prototypes; CADIC (`arXiv:2511.08634`) maintains a shared incremental coreset;
DeCoFlow (`arXiv:2606.26687`) decomposes normalizing flows with prototype routing and no replay;
ReCATS is the MTSAD instance.

**Not established.** Admission — the data entering each task's training set is given by the benchmark.

### F11. Normality-preserving / anti-forgetting continual AD

**Established.** Normality preservation as a *parameter-space* problem: orthogonal LoRA banks
(`arXiv:2606.02042`) project layer activations onto the orthogonal complement of previously used
subspaces so new-task updates do not overwrite old normality; UCAD (`arXiv:2401.01010`, AAAI 2024)
uses a contrastively learned key-prompt-knowledge memory; neural-collapse-guided task-free continual
AD (`arXiv:2609.03406`) uses fixed ETF prototypes to avoid task boundaries; a systematic framework and
benchmark (`arXiv:2607.18289`) formalises inter-task change as a shift in the *normal* distribution.

**Not established, and important.** These share an assumption the project does not: per-task normal
data is *given as clean*, taken directly from ground-truth labels. That is precisely the assumption
the admission question is about.

### F12. Novelty detection and open-set / open-world AD

**Established.** The taxonomy the project must use when it says "legitimate new normal" — a covariate
shift within the normal class (`arXiv:2110.11334`). Open-Set MTSAD (`arXiv:2310.12294`, ECAI 2024)
assumes labelled disjoint normal and anomaly sets, a different supervision regime; AD under
distribution shift (`arXiv:2303.13845`, ICCV 2023) adapts via teacher-student feature agreement.

**Not established.** Any timestamp-level drift truth for time series.

### F13. Continual-learning memory mechanisms

**Established.** Stable/plastic separation as an architecture: DualNet (`arXiv:2110.00175`) pairs a
slow representation learner with a fast learner; CLS-ER (`arXiv:2201.12604`, ICLR 2022) maintains
plastic and stable EMA copies of the working model. Inside AD, memory appears as prototypes, coresets
and codebooks (UCAD, CADIC, COMET).

**Not established.** A *gating policy* for what enters the plastic store under unsupervised,
possibly-contaminated streaming input — the version the project would need.

---

## Theme IV — Internal state as evidence

### F6. Recurrent hidden / gating / memory state as confidence, uncertainty or shift evidence

**The thinnest family on-target, and the most important one for the current probe.** Targeted searches
for recurrent gate or cell-state dynamics used as drift or shift evidence in TSAD returned
essentially nothing; several deliberately phrased queries returned zero arXiv records. What exists is
adjacent: gate activation signals correlate with phoneme boundaries in speech (`arXiv:1703.07588`,
abstract only); a modified forget gate / self-contained cell state is used for video anomaly
estimation (`arXiv:2104.01478`, abstract only); LoRA gate activations are read out as a diagnostic of
when adaptation engages (`arXiv:2605.19028`); a state-space detector's learned latent dynamics drive
incremental adaptation (iADCPS, `arXiv:2504.04374`); a Kalman-style filter's standardised innovation
serves as a nonconformity score (`arXiv:2608.30502`); MemStream's memory contents serve as both
scoring and update-gating signal.

**Two caveats that must travel with this gap.** First, the two closest on-target items were read at
abstract level only. Second, "internal state" is used very broadly in the wider TTA literature —
entropy, logits, Fisher information, BN statistics, prototypes and latent distances are all internal
quantities, and those are thoroughly mined (F7, F9, F15). The gap is specific: **recurrent gate and
memory dynamics, in TSAD, evaluated for incremental information about drift versus anomaly.**

**Entry points.** Anytime-valid gating (`arXiv:2608.30502`) for the closest construct; iADCPS
(`arXiv:2504.04374`) for learned latent dynamics driving adaptation; MemStream for memory-as-evidence.

---

## Theme V — Evaluation and deployment practice

### F16. Industrial streaming deployment and evaluation-methodology critiques

**Established, and constraining.** Point adjustment inflates scores to the point where random scores
can beat trained detectors (`10.1609/aaai.v36i7.20680`, AAAI 2022); the broader methodology critique
covers dataset triviality and protocol leakage (`arXiv:2308.13068`, TPCTC 2023); the metric space has
been taxonomised (`10.1007/s10618-023-00988-8`, DMKD 2023); range-based precision/recall
(`arXiv:1803.03639`, NeurIPS 2018) and VUS-family measures (`arXiv:2502.13318`) are the recommended
replacements; and a 2026 adversarial stress test asks whether the post-point-adjustment fixes actually
fixed it (`arXiv:2607.11969`). Benchmarks named by later work include TSB-AD
(`10.52202/079017-3437`, metadata only), TAB (`10.14778/3746405.3746407`, abstract withheld), MSAD
(`arXiv:2510.26643`) on model selection and StreamAD (`10.1016/j.tbench.2023.100121`, abstract only)
on online cloud-metric benchmarking.

**Relevance.** The project is already aligned with this family — AP as the primary metric, no point
adjustment, trapezoidal PR-AUC named separately for reproduction only, no test-best thresholds — and
should say so explicitly, because it is a defensible position that most of the compared literature
does not hold.

**Entry points.** Kim et al. 2022 → Wagner et al. 2023 → Sørbø & Ruocco 2023.

---

## How this repositions the project

1. **The framing is not the contribution.** "Learn the new normal without learning the anomaly" is
   anticipated, most directly by SCALE. What remains is a measurement claim and an accounting claim.
2. **Four papers must move from Related Work to Baselines**: CANDI, COMET, M2N2, MemStream. They
   already perform internal-quantity admission control on a normality buffer.
3. **Reset is prior art; reset *semantics* is not.** The F9 family solves when and where to reset
   toward a fixed source model. Nothing reverses one normality commitment while keeping another.
4. **The clean-normal-data assumption is the field's blind spot** (F10, F11) and the project's entry
   point: those benchmarks hand the method clean per-task normal data, which is the assumption the
   admission question interrogates.
5. **Borrow the statistics rather than inventing them.** F15 supplies anytime-valid machinery with
   error control; a learned gate would have to beat a conformal test martingale that already exists
   and already includes a skip action.
6. **Two retrieval gaps bound this assessment**: SCALE was read at abstract level, and a 2026
   safety-gated continual-learning paper for drift-aware anomaly detection
   (`10.1109/icaiset66439.2026.11541767`) was retrieved as metadata only. Both must be read before a
   novelty claim is written.
