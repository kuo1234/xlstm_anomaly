# Direct prior art — refreshed 2026-09

## Refresh method and coverage

This is a **targeted top-up**, not a new sweep. The base is the pre-G1 sweep in
`research/framing-2026-09/literature_records.json` (78 records, 61 full texts, 16 families); that
file remains authoritative for anything not restated here.

The refresh ran OpenAlex and arXiv queries against the families the pre-G1 package named as
unresolved or unsearched, plus every method the current review brief named by acronym:

| target | outcome |
|---|---|
| SCALE (`10.1145/3770855.3817912`) — flagged as "must read before any novelty claim" | **abstract obtained** (upgraded from metadata-level). Full text not open: Unpaywall reports no OA location; DOI landing page requires HTML scraping. Mechanism attributes below are from the abstract. |
| Safety-gated CPS (`10.1109/icaiset66439.2026.11541767`) — flagged as "the single largest unquantified novelty risk" | **abstract obtained** (upgraded from metadata-only). Full text closed (no OA location, no TDM link). |
| M2N2, CANDI, COMET, MemStream, METER, HTM+SPRT, martingale gating, iADCPS, reset family | already full-text in the base sweep; carried forward |
| AnDri | **new**: `arXiv:2506.15831` (extended report) + demo `10.1145/3746252.3761481`. Not in the base sweep. |
| STAD | already in base at abstract level (`10.1016/j.datak.2024.102365`); unchanged |
| ADA-ADF | **resolved**: `10.1016/j.asoc.2025.113903`, *Applied Soft Computing* 2025. Not in the base sweep. |
| DDADE | **not resolved.** No OpenAlex or arXiv record matches the acronym in this domain. Reported as unresolved rather than guessed. |
| ADAPTS | **not resolved.** arXiv `ti:"ADAPTS"` returns only unrelated work (`2605.03212`, symptom tracking). Reported as unresolved. |
| recurrent-state / reservoir-state anomaly methods | **new and important**: MD-RS (`10.36227/techrxiv.22678774`), IncFed MD-RS (`arXiv:2502.05679` / `10.1109/ijcnn64981.2025.11228565`), FedKO (`arXiv:2503.11255`), SR-RC (`arXiv:2510.14287`) |
| TTA for anomaly detection, 2025-06 onward | **new**: RTTAD (`arXiv:2605.10242`), EPHAD (`arXiv:2510.21296`), TUNE (`arXiv:2511.07023`) |
| xLSTM for anomaly detection | **unchanged**: still exactly two works (`arXiv:2405.04517`, `arXiv:2506.22837`/`10.1109/ICDM65498.2025.00032`), neither using internal state |

**Limits.** Two of the highest-threat works (SCALE, safety-gated CPS) are assessed at abstract level
because neither is open access; their mechanism columns below carry `?` where the abstract is
silent, and `?` means "not retrievable", never "no". The refresh did not re-search the two families
the pre-G1 package left unsearched (adversarial anomaly poisoning; cross-entity/fleet drift), so
nothing here licenses a novelty claim on either.

Columns. **Drift handling**: how legitimate change is separated from fault. **Internal state?**: is a
model-internal quantity used as the evidence. **Selective adapt?**: is adaptation restricted to
chosen samples/windows. **Contam?**: is contamination of the update path explicitly handled.
`Y` yes / `~` partial / `n` no / `?` not retrievable.

---

## OUTPUT 2 — the 20 closest works

| # | paper | year | task | drift / new-normal handling | internal state? | selective adapt? | contam? | closest overlap | key difference | threat |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **MD-RS** — Mahalanobis Distance of Reservoir States (`10.36227/techrxiv.22678774`) | 2023 | online univariate TSAD | none (stationary normal assumed) | **Y — the detection statistic IS the recurrent state** | n | n | The core construct: recurrent internal state used *instead of* prediction error, and shown superior **on the same reservoir**. This is the head-to-head "state beats residual" result. | Anomaly-vs-normal, not anomaly-vs-drift. Untrained random reservoir, not learned recurrent dynamics. No residual-trajectory control arm; no incremental-information estimand; no drift truth. | **HIGH** |
| 2 | **SCALE** (`10.1145/3770855.3817912`) *abstract only* | 2026 | online latent-domain MTSAD | Y — unobserved shift times, growing domain count, expandable style-expert pool | Y — two decoupled model-derived criteria (Sparse Likelihood Regret; Counterfactual Prediction Residual) | Y — SLR routes experts | ? | The exact framing: separate domain drift from true anomalies online, from model-derived quantities, with claimed theory and a purpose-built multi-domain benchmark. | Evidence is likelihood-regret / counterfactual-residual, i.e. score-like model outputs, not recurrent state dynamics. Validated by detection performance, not as an incremental-information measurement against a residual control. | **HIGH** |
| 3 | **AnDri** (`arXiv:2506.15831`; demo `10.1145/3746252.3761481`) | 2025 | TSAD under concept drift | Y — dynamic normal model: normal patterns **activated, deactivated, newly added**; Adjacent Hierarchical Clustering for temporally local patterns | n (subsequence/cluster level) | Y — pattern admission | ~ | Co-detection of anomaly and drift, and — decisively — pattern-level deactivation, which is the operation the pre-G1 map listed as the one genuinely unoccupied mechanism slot. | Not a deep detector; no internal-state evidence; no contamination-harm accounting; no per-timestamp drift/anomaly information measurement. | **HIGH** |
| 4 | **Safety-Gated Continual Learning for Drift-Aware AD in Real-Time CPS** (`10.1109/icaiset66439.2026.11541767`) *abstract only* | 2026 | CPS MTSAD, HAI 22.04 | Y — persistent drift detection | ~ — updates confined to a "high-confidence adaptation region" | **Y** | ~ ("reducing unsafe model update") | The whole mechanism family in one title, on a **recurrent (GRU) autoencoder**: drift-aware, safety-gated, controlled online adaptation. This is the closest thing published to the project's L4 target. | Reports detection metrics only (window F1 0.2201 → 0.2560 → 0.4860; event F1 0.7418, delay 20.05 windows, 35.74 FA/10k). No internal-state evidence, no contamination-harm accounting, no measurement of what the gate buys. Low absolute performance. | **HIGH** |
| 5 | **CANDI** (`arXiv:2604.01845` / `10.1609/aaai.v40i17.38524`) | 2026 | MTSAD TTA under distribution shift | Y — adapts to "potential false positives" | Y — anomaly score + **latent Mahalanobis similarity** in the frozen encoder space | Y — False Positive Mining | ~ (acknowledged, argued robust; failure recovery future work) | Admission control on a normality buffer using a model-internal quantity. The project's own anchor and the direct answer to "what is different here?" | A selection heuristic validated by downstream AUROC (up to +14%). Never measures the information content of the latent criterion, never controls against a residual trajectory, has no per-timestamp drift/anomaly truth. | **HIGH** |
| 6 | **Anytime-valid gating on real forecast streams** (`arXiv:2608.30502`) | 2026 | monitoring/gating online updates | Y — conformal test martingale over a filter's standardized innovation; four-way action table incl. skip and huberize | Y — filter innovation | Y | ~ | Internal evidence + deferral + drift-vs-anomaly action + reset, all four, on a simple detector. Also the **negative result** the project must now answer: 135/135 clean-stream fires at α = 0.05 on real data vs ≤1/60 on exchangeable synthetic. | Linear Kalman adapter, not a learned deep detector; forecasting streams; no anomaly-detection quality evaluation. | **HIGH** |
| 7 | **M2N2** (`arXiv:2312.11976`) | 2024 | unsupervised TSAD, "new normal problem" | Y — EMA trend estimation | Y — masks the test-time loss by one minus its own predicted anomaly label | Y | **Y** | Score-masked updating: the field's default contamination guard, and the origin of the "new normal" vocabulary the project uses. | The guard is the detector's own score; no deferral, no rollback, no measurement of what the mask prevents. | HIGH |
| 8 | **HTM + SPRT hybrid** (`arXiv:2504.18599`) | 2025 | real-time drift and anomaly identification | Y — SPRT over binarized likelihood, restart after each drift decision | Y | Y | n | Second full instantiation of the four-part shape (internal evidence, deferral, drift-vs-anomaly, reset) with explicit sequential error probabilities. | Univariate HTM; no learned deep detector; no contamination accounting; no information measurement. | HIGH |
| 9 | **COMET** (`arXiv:2602.01635`) | 2026 | TSAD with online adaptation | ~ — distribution shift at inference | Y — codebook activation from normal-only training; dual score (quantization error + memory distance) | Y — threshold-free admission via codebook pseudo-labels | ~ | Threshold-free internal-evidence admission; a baseline the project cannot omit. | Codebook/VQ evidence, not recurrent state; no drift-vs-anomaly separation; contamination not costed. | MEDIUM |
| 10 | **METER** (`arXiv:2312.16831` / `10.14778/3636218.3636233`) | 2023 | online AD, dynamic concept adaptation | Y — evidential (Dirichlet) concept uncertainty routing | Y | Y | n | Accumulate-then-commit: the canonical deferred-commitment instance. | Non-recurrent MLP-based; tabular/streaming setting; no contamination accounting. | MEDIUM |
| 11 | **MemStream** (`arXiv:2106.03837`) | 2022 | streaming AD | Y — memory replacement under drift, with a memory-size/drift-speed proposition | Y — memory contents both score and gate updates | Y | **Y** — discounted KNN score threshold gates memory writes | Score-gated memory: admission control, four years old. | Shallow denoising-autoencoder embedding; no drift-vs-anomaly distinction as a prediction problem. | MEDIUM |
| 12 | **iADCPS** (`arXiv:2504.04374`) | 2025 | evolving CPS TSAD | Y | Y — a state-space model's **learned latent dynamics** drive incremental adaptation | Y | n | Learned latent recurrent dynamics as the adaptation signal — the nearest published thing to the project's evidence source on a *trained* model. | Dynamics drive adaptation directly; no measurement of their incremental information, no residual control, no evaluator drift truth. | MEDIUM |
| 13 | **ADA-ADF** (`10.1016/j.asoc.2025.113903`) | 2025 | unsupervised drift-aware streaming TSAD | Y — hybrid statistical + performance-based drift detection; distinguishes sudden vs incremental drift | n — **reconstruction error** selects representative historical data | Y — drift-type-conditioned replay ratios | ~ | Drift-type-conditioned adaptation with reconstruction-error-based sample selection: the observable-evidence counterpart of the project's internal-evidence proposal. | Evidence is the residual, which is exactly the control the project is trying to beat — so it is the natural baseline, not a competitor for the measurement. | MEDIUM |
| 14 | **RTTAD** (`arXiv:2605.10242`) | 2026 | unsupervised **tabular** AD under normality shift | Y — "normality shifts" framing | Y — high-confidence pseudo-normal selection; kNN contrastive objective | Y | **Y** — explicitly "adaptation risk", constrains anomalous samples | Risk-aware selective test-time adaptation under normality shift: the closest recent statement of the project's L4 intent. | Tabular, not time series; no temporal drift; no internal recurrent state; risk is heuristic, not costed. | MEDIUM |
| 15 | **STAD** (`10.1016/j.datak.2024.102365`) *abstract only* | 2024 | AD under concept drift | Y — stream periods mapped to discrete states; statistical tests decide transitions, incl. revisiting a seen state | Y — autoencoder reconstructions | ~ | ? | Regime-switching normality with recurrence — the A→B→A case. | Statistical tests over reconstructions; no internal recurrent state; abstract-level only. | MEDIUM |
| 16 | **IncFed MD-RS** (`arXiv:2502.05679`) | 2025 | federated online TSAD | n | Y — incremental updating of the reservoir-state distribution | n | n | Shows the reservoir-state statistic is maintainable **online and incrementally** — i.e. the operational objection to state-based evidence is already answered elsewhere. | Federated/efficiency contribution; no drift-vs-anomaly separation. | MEDIUM |
| 17 | **Drift-aware online dynamic learning** (`arXiv:2604.09358`) | 2026 | nonstationary MTSAD | Y | Y | Y — excludes current-window samples; detection cooldown | n | Deferral plus exclusion on a deep multivariate detector. | MS-BCNN backbone; no internal-state measurement; no contamination accounting. | MEDIUM |
| 18 | **Adaptive selective reset** (`arXiv:2603.03796`) + RDumb++ (`arXiv:2601.15544`) | 2026 | continual test-time adaptation (classification) | Y — entropy/KL drift triggers | Y — prediction concentration and its EMA decide *when* and *where* | Y | n | The reset-timing problem, solved. | Classification CTTA; reverts toward a **fixed source model**; no normality semantics. | LOW |
| 19 | **EPHAD** (`arXiv:2510.21296`) | 2025 | AD under training-data contamination | n | n | n — post-hoc output adjustment | **Y** — the contamination is the subject | The only retrieved work whose subject is contaminated normality, from the other end: correcting a detector already trained on contaminated data. | Post-hoc score adjustment using external evidence (CLIP, LOF); no update path, no drift, no time-series drift truth. | LOW |
| 20 | **xLSTMAD** (`arXiv:2506.22837` / `10.1109/ICDM65498.2025.00032`) and **xLSTM** (`arXiv:2405.04517`) | 2025 / 2024 | offline MTSAD; architecture | n | n | n | n | The entire xLSTM-anomaly-detection literature. | Neither examines internal state, drift, or adaptation. There is no published claim to inherit and none to refute. | LOW |

---

## What changed in the novelty boundary

**Lost since the pre-G1 assessment:**

1. *Reset semantics.* The pre-G1 map's single clean gap — "every retrieved reset reverts toward a
   fixed source model; none reverses one normality commitment while preserving others" — is
   occupied by AnDri's activate/deactivate/add dynamic normal model. Withdraw the claim.
2. *"Recurrent state carries evidence the residual does not."* MD-RS published the head-to-head
   comparison in 2023 on a reservoir. The project's version is better controlled and targets a
   different distinction (drift vs anomaly rather than normal vs anomaly), but the construct is not
   unoccupied and must be cited as the precedent.
3. *Safety-gated adaptation on a recurrent detector under drift.* Published, on a CPS benchmark,
   with numbers. Weak numbers, but published.

**Held:**

4. *The measurement.* Nothing retrieved estimates the incremental information of internal state for
   the drift-vs-anomaly distinction against a residual control at a fixed backbone with
   evaluator-side truth. This remains the contribution.
5. *Contamination-harm accounting.* Still zero retrieved records measuring the causal cost of
   admitting a true anomaly into a normality buffer against a pre-specified margin. EPHAD is the
   nearest and works from the opposite direction.
6. *xLSTM internal state.* Still empty — two papers, neither on internals.

**Gained (an argument, not a gap):**

7. `arXiv:2608.30502` supplies a measured failure of the off-the-shelf anytime-valid route on real
   streams. That is a reason the project's "measure before you gate" stance is *correct*, and it is
   citable support for deferring L2 rather than an embarrassment about not having reached it.
