> **v0.4 更正說明（2026-09-30）**：本報告為 2026-09-29 的歷史紀錄。
> - MWAdp-JITL（Urhan & Alakent, Neurocomputing 392:23–37, 10.1016/j.neucom.2020.01.083）的**全文已讀**（使用者提供 PDF，未放入 repo）。它在查詢時，以相似度加上近期的實際預測誤差選擇歷史區段，因此 **G3b 的廣義版本降為 PARTIALLY_OCCUPIED**。
> - 它**沒有**逐筆的持續效用與淘汰、沒有 H 步延遲，也沒有篩選故障汙染。
> - correntropy JITL（10.3390/s17081830）與 LST-FEDA（10.1016/j.chemolab.2024.105246）使 G3c 的佔據程度更高。
> - Scopus／WoS 補查仍 **UNRESOLVED**；D3 **不升為核心新意**。見 `../proposal_v0.4.md` §8。

# Direction 3 Gap Audit — Retrieval / External Memory for Forecasting Under Drift on Machine Data

**Scope.** Candidate design: a memory bank of historical segments (long-term memory) queried with the recent window
(short-term memory); retrieved analogues fused into the forecast. Candidate contribution: the **memory management
policy under non-stationarity** — what to store, how to score utility (from delayed forecast errors), what to
evict/down-weight/decay, how to handle recurring regimes and stale memories, on **machine/industrial** data.

Search date: 2026-09-29. Sources: OpenAlex (via API key), arXiv, and full-text reads of the five closest competitors.
42 papers verified (11 full_text, 22 abstract, 1 metadata_only [paywalled, see caveat under G3c], titles/DOIs of all
others independently confirmed to exist via OpenAlex). See `d3_papers.json` for the full structured list.

---

## Gap verdicts

### G3a — RAG deep TS forecasting assumes a static retrieval database; online maintenance under drift is unstudied
**Verdict: OPEN_AT_SEARCH_DEPTH**

Every retrieval-augmented forecasting paper found — RAF, RATD, TimeRAF, TS-RAG, RATSF, ReTime, Cross-RAG, RAEF,
SpecReTF, SARAF — builds its retrieval corpus **once**, from the training split, before deployment. Full-text
reads confirm this explicitly:
- RATD's database is the entire training set, indexed once, with no online-update discussion (read pp.1–5 of the
  NeurIPS 2024 paper).
- TimeRAF explicitly deduplicates and "establishes" a knowledge base with no overlap, described as a one-time
  construction step (read pp.1–4).
- TS-RAG's Adaptive Retrieval Mixer adapts *fusion weights* per query but never touches the corpus itself (read
  full text).
- SARAF (2026) and SpecReTF (2026), the two most recent successors, add diversity-aware candidate selection and
  spectral/recency-weighted scoring respectively, but both operate over a **fixed candidate pool** at query time —
  neither grows, prunes, or evicts entries as new post-deployment data arrives.

No paper in this line evaluates performance as its own retrieval index ages years past its construction date, and
none proposes an update/eviction algorithm for the index. This is a genuine, currently open gap in the RAG-for-TS
literature.

**Queries run:** "retrieval augmented time series forecasting", "RAF retrieval augmented forecasting Chronos",
"RATD retrieval augmented time series diffusion", "TimeRAF retrieval augmented forecasting", "TS-RAG retrieval
augmented generation time series", "dynamic knowledge base update retrieval augmented time series", "retrieval
database update over time forecasting streaming", "time-varying retrieval database time series forecasting online".

---

### G3b — Utility-based retention/eviction of retrieval memory from delayed forecast-error feedback, for deep forecasters
**Verdict: OPEN_AT_SEARCH_DEPTH**

No paper was found that scores a stored memory's value by *how much it improved a deep forecaster's subsequent
forecast* (i.e., a delayed, outcome-based utility signal) and uses that score to decide retention/eviction. The
closest partial precedents are all in adjacent fields, not forecasting:
- **SAM-kNN** (Losing et al., 2016/2017) scores instance relevance by classification consistency with the current
  concept, not by a delayed downstream error signal, and is for kNN classification, not deep sequence forecasting.
- **Online Class-Incremental Continual Learning with Adversarial Shapley Value** (Shim et al., 2021) computes a
  Shapley-value utility score for replay-buffer retention/replacement — a genuinely utility-based mechanism — but
  for image classification, with no forecasting or TS analogue found.
- **Adaptive Gaussian Mixture Model-Based Relevant Sample Selection for JITL** (Chen et al., 2014) scores samples
  by a GMM-based similarity/relevance criterion at *selection* time, not by observed forecast-error feedback after
  the fact.

Combining (a) deep sequence forecasters, (b) an explicit external memory bank, and (c) retention/eviction driven by
*delayed, realized forecast-error* utility was not found anywhere in the searched literature. This is the clearest
candidate for the thesis's central contribution.

**Queries run:** "utility of retrieved sample forecast error feedback", "memory maintenance policy retrieval time
series drift", "forgetting mechanism retrieval augmented forecasting", "gradient based sample selection continual
learning" (Aljundi et al. found), "online class-incremental adversarial shapley value" (found), "reservoir sampling
replay buffer streaming data".

---

### G3c — Does JITL/soft-sensor literature already solve database maintenance under drift?
**Verdict: PARTIALLY_OCCUPIED**

Yes, substantially, but for a narrower model/task class than the thesis targets. Just-in-Time Learning (JITL) /
lazy-learning soft-sensor literature has, since at least 2010, treated "which historical samples to keep in the
database and how to weight them" as a first-class problem:
- **"Integrating adaptive moving window and just-in-time learning paradigms for soft-sensor design"** (Neurocomputing,
  2020) combines an adaptive moving-window (time-decay/eviction) database with JITL retrieval — i.e., essentially the
  exact "database maintenance under drift" mechanism the thesis would need, but for a shallow/kernel regression
  soft-sensor, not deep multivariate multi-horizon forecasting. *(Caveat: full text of this paper was not accessible
  — no open-access copy found via Unpaywall, and OpenAlex returned no abstract; the description above rests on the
  title, journal, and its position in the citation network from later JITL surveys, so this finding is provisional
  metadata-only and should be re-verified via institutional access before being cited as a blocking precedent.)*
- **Adaptive GMM-based relevant sample selection** (Chen et al., 2014) and the comparative JITL survey (Fujiwara
  et al., 2010) establish similarity-criterion design as a mature sub-topic.
- **A deep learning just-in-time modeling approach for soft sensor based on variational autoencoder** (2020)
  extends JITL to a learned (deep) embedding space for similarity — the closest thing found to "deep retrieval
  embeddings" in this literature.
- **Online-Dynamic-Clustering-Based Soft Sensor for Industrial Semi-Supervised Data Streams** (2023) shows the
  line remains active for streaming/dynamic database maintenance as recently as 2023.

**What remains open**, per this search: (1) all JITL database-maintenance work found targets **single-output,
single/short-horizon regression** (a scalar soft-sensor value), never deep **multivariate, multi-horizon**
forecasting; (2) JITL's moving-window and similarity-based selection mechanisms are inherently **recency-biased**
(old, dissimilar-to-recent samples drop out of the window) — no JITL paper found explicitly retains rare-but-valuable
old-regime samples for future reuse (contrast with SAM-kNN under G3e, which is not itself a JITL paper); (3) no JITL
paper found explicitly protects the database from **fault/anomaly contamination** as a distinct concern from missing
data (the "Probabilistic JITL... With Missing Data" paper handles missingness, not anomalous-but-present values).

---

### G3d — Protecting the memory bank from contamination by faults/anomalies
**Verdict: PARTIALLY_OCCUPIED**

**MemStream** (Bhatia et al., WWW 2022) is the closest precedent: it maintains a fixed-size memory of encoded
"normal" records for streaming anomaly detection and explicitly **gates memory updates by the incoming record's
anomaly score**, so anomalous records are not admitted into the normal-reference memory. This is conceptually
identical to the contamination-protection mechanism G3d asks about. However, MemStream's memory exists to define
*normality for detection*, not to serve as a bank of retrievable analogues for *forecasting*; no paper was found
that applies this fault-exclusion-gated-admission idea to a forecast-analogue retrieval memory specifically.
JITL literature's handling of "missing data" (Probabilistic JITL, 2016) is a related but distinct data-quality
problem (absent values vs. present-but-faulty/anomalous values). No paper combining (a) a forecasting retrieval
memory and (b) explicit fault/anomaly screening before admission was found.

**Queries run:** "memory bank contamination anomaly detection retrieval", "fault sample contamination soft sensor
database exclusion", "database update deletion soft sensor drift", plus reuse of MemStream/METER results already
known to the user from the anomaly-detection side of this project.

---

### G3e — Recurring regimes: retaining rarely-used but valuable old-regime memories vs. recency-biased eviction
**Verdict: PARTIALLY_OCCUPIED**

This exact idea — an explicit **long-term memory that retains and can reuse old concepts** distinct from a
recency-biased short-term memory — is already a named research topic, but in stream **classification**, not
forecasting:
- **SAM-kNN** (Losing, Hammer & Wersing, ICDM 2016 / KAIS 2017 / IJCAI 2017) is the closest match found anywhere in
  this search to the thesis's long-term/short-term memory framing: it maintains a short-term memory of only
  currently-relevant instances and a compressed long-term memory of past concepts, with an explicit
  consistency-based cleaning procedure so that old, valid regime-knowledge is not simply aged out. This directly
  operationalizes "old regime returns" reuse — for kNN classification, not sequence forecasting.
- **"A survey on machine learning for recurring concept drifting data streams"** (Suárez-Cetrulo et al., Expert
  Systems with Applications, 2022) confirms recurring-concept handling (concept repositories, model pools,
  meta-learning-based regime reuse) is an established sub-field, again centered on classification/ensemble model
  selection rather than retention of raw historical time-series segments as forecast analogues.
- **"Handling concept drift via model reuse"** (Yu, Zhao & Zhou, Machine Learning, 2019) operationalizes regime
  reuse at the level of whole trained models, not fine-grained memory entries.

**What remains open:** transplanting the SAM-kNN-style explicit short-/long-term split — with a principled
retain-for-reuse mechanism for rare-but-recurring regimes — into a deep, multivariate, multi-horizon forecasting
retrieval memory, and demonstrating it specifically on machine data with genuine seasonal/mode-switching operating
regimes (e.g., HVAC seasonal cycles, batch-process recipe changes, compressor load modes) was not found anywhere in
the searched literature.

**Queries run:** "SAM-kNN self adjusting memory concept drift", "recurring concepts drift model pool ensemble",
"concept history repository drift reuse", "recurring operating mode soft sensor model reuse".

---

## Closest competitors (full-text or near-full-text reviewed)

1. **RATD** (Retrieval-Augmented Diffusion Models for Time Series Forecasting, NeurIPS 2024) — embedding-retrieval
   + reference-guided diffusion; database = full training set, built once. Leaves open: any post-deployment
   database update, drift-awareness, or machine-data evaluation.
2. **TimeRAF** (2024/2025, IEEE TKDE) — learnable end-to-end retriever + Channel Prompting fusion over a
   domain-specific knowledge base built once with explicit de-duplication. Leaves open: online knowledge-base
   maintenance; evaluated on general zero-shot TS domains, not industrial machine data specifically.
3. **TS-RAG** (2025) — pretrained encoder retrieval + Adaptive Retrieval Mixer fusion, code available. Leaves open:
   the retrieval corpus itself is never updated, pruned, or evicted; no forecast-error-driven utility scoring.
4. **RAF** (Retrieval Augmented Forecasting, 2024) — first principled RAG framework built on TS foundation models
   (Chronos). Leaves open: static database, no drift-adaptive maintenance, no machine-data evaluation.
5. **MemDA** (Forecasting Urban Time Series with Memory-based Drift Adaptation, CIKM 2023) — a *parametric*
   Pattern Memory (not an explicit growable instance bank) queried via attention, updated end-to-end with a
   meta-dynamic network to absorb drift without retraining. Leaves open: memory is not an inspectable,
   individually-evictable segment database; no utility-based retention or fault-contamination handling; domain is
   urban mobility, not industrial machinery.
6. **Stationarity-Aware Retrieval-Augmented Time Series Forecasting (SARAF, 2026)** — the most topically adjacent
   2026 paper: explicitly targets non-stationarity by diversifying retrieved candidates in proportion to
   dataset-level stationarity, with code released. Leaves open: still selects from a fixed candidate pool per
   query; no mechanism for the pool itself to grow/evict as new post-deployment data arrives, and no delayed-error
   utility signal.

## Baselines with public code
- TS-RAG — https://github.com/UConn-DSIS/TS-RAG
- Cross-RAG — https://github.com/seunghan96/cross-rag/
- SARAF — https://github.com/ShiqiaoZhou/SARAF

(RAF, RATD, TimeRAF, RAEF, SpecReTF, ReTime, RATSF and the JITL papers did not have a confirmed public code link
located during this search; absence of a found link is not proof no code exists — not exhaustively checked beyond
the paper page / abstract.)

## Recommended thesis framing

Frame the contribution **not** as "retrieval-augmented forecasting" (occupied, G3a shows 10+ 2024-2026 papers
already do query-time retrieval-and-fuse) but as **the memory-lifecycle/maintenance policy that sits underneath
any such retriever**: given an already-competent retrieve-and-fuse forecaster (e.g., a re-implementation of
RAF/RATD/TimeRAF-style fusion as the fixed "front end"), study what happens to accuracy over a multi-year deployment
simulation on machine data (rotating machinery / process-plant / industrial-IoT streams) under four concrete memory
policies: (i) never update (today's default, per G3a), (ii) pure recency window (today's JITL default, per G3c),
(iii) utility-scored retention from delayed forecast-error feedback (the open gap, G3b), and (iv) a SAM-kNN-style
explicit short-/long-term split that additionally protects against admitting fault-contaminated segments (G3d) and
preserves rare recurring regimes (G3e). This directly targets the two gaps with no found prior art (G3b, G3d as
applied to forecasting memories) while explicitly building on and citing the two literatures that most nearly
overlap it (RAG-for-TS forecasting, and JITL/SAM-kNN-style drift-aware instance memory) rather than claiming
novelty merely because no single existing paper combines every component.

## Main threats to this framing

1. **SARAF and SpecReTF (both 2026)** are moving in exactly this direction — SARAF's stationarity-modulated
   diversity selection and SpecReTF's recency-weighted spectral scoring are both primitive forms of drift-aware
   retrieval scoring. A thesis contribution must clearly go beyond query-time re-weighting of a static pool to
   genuine online admission/eviction with a persistent, evolving memory state, and should benchmark against both.
2. **The G3c caveat is load-bearing**: the single most on-point JITL paper ("Integrating adaptive moving window
   and JITL", Neurocomputing 2020) could not be read in full text (paywalled, no OA copy, no abstract via OpenAlex)
   during this search. If its moving-window mechanism turns out, on manual inspection, to already implement a
   utility- or regime-aware policy (not just simple recency), G3b/G3e would need to be downgraded from
   OPEN_AT_SEARCH_DEPTH/PARTIALLY_OCCUPIED toward OCCUPIED for the shallow-model case, and the novelty claim would
   need to rest more heavily on "deep multivariate multi-horizon" + "machine data" as the differentiator rather
   than the maintenance policy itself.
3. **MemStream's anomaly-gated memory update** (already known to the user from the anomaly-detection side of this
   project) is a working, published fault-contamination-avoidance mechanism; a reviewer familiar with the streaming
   anomaly-detection literature may ask why its gating idea cannot simply be transplanted into a forecasting
   retrieval memory with modest adaptation — the thesis should explain concretely why forecasting analogue-memory
   contamination is a harder or different problem (e.g., partial/gradual faults that don't trigger a detector
   threshold, mislabeled "normal" segments that are actually early-fault precursors).
4. **SAM-kNN's long-term/short-term split** is 2016-2017 vintage, well-cited, and already solves the recurring-regime
   retention problem for kNN; a thesis re-deriving the same idea for deep forecasters must show the extension is
   non-trivial (different memory representation — raw/embedded TS segments vs. labeled feature vectors; different
   utility signal — regression/forecast error vs. classification consistency; different consolidation mechanism for
   high-dimensional multivariate windows) rather than a relabeling.
5. **Search-depth limits**: OpenAlex free-text search on shallow-model process-control literature (JITL, soft
   sensors) returned many irrelevant generic-deep-learning hits alongside the true positives, meaning highly
   specific niche JITL variants (e.g., non-English-language venues, some IEEE Trans. Industrial Electronics/
   Informatics papers) may not have surfaced; a dedicated Scopus/Web-of-Science pass restricted to chemometrics
   and process-control venues is recommended before finalizing novelty claims for G3c.
