# Closest competitors

This ranking reflects overlap with the proposed lifecycle, not overall paper quality. “Direct” means a time-series or streaming anomaly-detection problem; “cross-domain” papers can still defeat broad component claims.

## Tier 1: direct or near-direct threats

### 1. AnDri — candidate normal patterns and recurrence

AnDri is the strongest challenge to claims about normal-pattern promotion, persistence filtering, and recovery of recurring behavior. The 2025 extended report describes temporally clustered patterns, active/inactive status, candidate local windows, coherence and minimum-size conditions for normal admission, and reactivation of old patterns. It therefore occupies much of “candidate regime → promotion → reactivation” at the pattern level.

The remaining distinction is representation and scope: AnDri is not a recurrent neural hidden-state bank with isolated online state writes. A credible proposal must explain why a hidden-state lifecycle offers a measurable benefit over pattern clustering, and compare directly to AnDri-like admission/reactivation. The source also recognizes that a persistent anomaly can be coherent and become a pattern; it does not solve semantic identifiability.

### 2. METER — unknown cases accumulated before update

METER's evidential classifier can label a case unknown. Uncertainty accumulates over a sliding window, and crossing a threshold triggers an update using the current window. This is a close precedent for deferred adaptation rather than an immediate update on each observation.

The audited description does not establish that the accumulated window is a separate candidate normal regime, that a candidate is later promoted into a protected bank, or that old recurrent regimes are restored. The proposal must compare against METER's uncertainty threshold/window update and show what temporal candidate state adds.

### 3. CANDI — normal-reference filtering and selective adaptation

CANDI's false-positive mining uses anomaly scores and latent Mahalanobis similarity against normal-validation reference banks to select likely normal target samples; its residual adaptation leaves the pretrained backbone and latent representation frozen. This is a close challenge to “protected normality” and “update only from likely normal inputs.”

The inspected method does not document a separate candidate lifecycle with time-based quarantine, regime promotion, multiple recurrent state versions, or old-regime reactivation. A proposal should distinguish state-level normality transitions from CANDI's sample curation and residual-parameter update, and should measure contamination.

### 4. M2N2 — predicted-normal online parameter adaptation

M2N2 masks online adaptation loss to time points the detector predicts normal. It directly defeats novelty claims around scoring an observation before updating or using an online normality gate. Its test-time trend estimate also uses the incoming stream, including anomalous points; the paper acknowledges ambiguity between normality, anomaly and drift and assumes normal observations dominate.

It does not document a quarantine/promotion lifecycle or multiple protected recurrent normal states. The proposed distinction, if retained, must be explicit state isolation and delayed regime transition, not simply a stricter pseudo-normal mask.

### 5. Smart-building drift-aware online AD — persistent drift buffer

This system freezes a TCN-VAE, uses input-gradient profiles to classify normal, normal drift, and attack, buffers batches predicted as drift, and updates drift centroids only after five drift batches. Its process is close to buffer + persistence criterion + selective update.

It bootstraps the gradient classifier with 100 labeled target examples per class, including drift and attack. That dependency is material: its result does not establish unsupervised semantic drift identification. It has no recurrent hidden-state regime bank or documented old-regime recovery.

### 6. MemStream and MemTTA — gated memory writes

MemStream scores an embedding against the accepted normal memory and inserts only if it is below a threshold. This is direct score-before-write precedent. MemTTA's thesis describes a neural normal-pattern memory and a gradient-based gate intended to prevent anomalous writes. The thesis is not peer-reviewed evidence, and detailed update ordering was not confirmed.

Neither inspected source establishes the entire candidate/quarantine, promotion, multi-regime retention and recovery lifecycle.

## Tier 2: strong component threats

### ARCUS

ARCUS keeps an adaptive autoencoder pool, weights models by reliability, updates a contributing model when fit is good, or trains a new model and merges/consolidates when it is not. This is strong precedent for multiple concepts, retention and reuse. It operates at model-pool level, not through semantic normality confirmation of recurrent hidden-state writes.

### MD-RS and xLSTMAD

MD-RS demonstrates recurrent-reservoir state trajectories as anomaly statistics. xLSTMAD establishes an xLSTM TSAD baseline. Neither supplies online promotion. They rule out claims that recurrent-state anomaly scoring or xLSTM-for-TSAD are themselves new.

### PADRE and COMET

PADRE uses an online regime-conditioned residual pattern bank and an evidence-consistency update gate in forecasting. COMET's 2026 preprint uses normal codebook/memory-distance signals and pseudo-label online adaptation for TSAD. Both are recency-sensitive threats to broad “regime memory plus gated update” phrasing. Their boundaries and evidence status are described in the inventory.

## Tier 3: cross-domain protection or lifecycle threats

- Orthogonal LoRA Banks preserve old normality banks and create a new one after a novelty threshold in continual industrial image AD.
- CoTTA protects source knowledge by stochastic restoration during continual test-time adaptation.
- Validation-gated satellite telemetry AD evaluates an updated candidate model before deployment.
- MemMambaAD combines memory with an SSM in image AD; PAMA uses normal and pseudo-anomaly memories at training time.

These systems do not reproduce the proposed TSAD semantics, but they invalidate generic claims about protected memories, novelty-triggered growth, model candidate validation, or memory plus recurrent/state-space architecture.

## Comparator set required for a future study

At minimum, compare an explicit lifecycle implementation to:

1. no adaptation;
2. score-gated memory write (MemStream-style);
3. immediate pseudo-normal TTA (M2N2-style);
4. reference-bank filtering with frozen representation (CANDI-style);
5. uncertainty/window update (METER-style);
6. candidate pattern admission and reactivation (AnDri-style);
7. model/concept pool reuse (ARCUS-style); and
8. a simple fixed-window or residual baseline.

The exact baselines, data and protocol require a later approved experiment plan. This report does not authorize running them.
