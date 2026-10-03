# Novelty threats

## Overall threat assessment

**High threat to broad framing; moderate and unresolved threat to the exact lifecycle framing.** Every major component has prior art, and adjacent systems cover most pairings. The inventory did not find one audited paper documenting all four of (a) persistent recurrent normal-state regimes, (b) selective state writes, (c) an explicit quarantined candidate regime with promotion criteria, and (d) controlled transition or recovery, in an unsupervised TSAD stream. This is a bounded search observation only. A claim of novelty cannot rest on the unlocated conjunction alone.

## Threats by component

### 1. Score or confidence gated write

MemStream scores against normal embeddings before an insertion and rejects points above threshold. M2N2 updates from predicted-normal points. CANDI selects likely false positives using score and latent distance to a normal validation bank. MemTTA reports gradient-gated memory writes. A new “write only when likely normal” rule is not novel by itself.

### 2. Protected reference knowledge

CANDI freezes its pretrained backbone and latent space, CoTTA restores source weights stochastically, and O-LoRA retains old category-specific normality banks. Protection against forgetting or contamination is established across TTA and continual AD. A protected normal bank needs a precise new property, such as immutable confirmed states plus explicitly bounded promotion and eviction semantics, rather than the generic word “protected.”

### 3. Defer, accumulate and update later

METER labels uncertain inputs unknown, accumulates uncertainty, then updates from a recent window. Smart-building AD buffers repeated drift predictions and updates only after a persistence criterion. Sequential HTM/SPRT work also accumulates evidence before classification. “Quarantine” must have operational semantics and a direct comparison against these defer/buffer systems.

### 4. Candidate concepts and recurring-regime reuse

AnDri is the strongest lifecycle threat: it has local candidate patterns, criteria for normal admission, inactive patterns, and reactivation. ARCUS maintains an adaptive model pool and can train new models, merge and reuse. A proposal that says it discovers recurring regimes and reuses old knowledge overlaps materially. The potential distinction is whether recurrent internal state itself is versioned, isolated, and transitioned under a normality lifecycle, and whether this is evaluated in time-series anomaly detection.

### 5. Recurrent representation

MD-RS establishes recurrent-reservoir state as an anomaly-scoring representation, while xLSTMAD applies xLSTM to TSAD. Markovian RNNs model regime-specific recurrent transition states. None makes xLSTM uniquely appropriate. The architecture is an implementation choice; the lifecycle and evidence standard carry the research contribution.

### 6. Semantic drift versus anomaly

No online unsupervised gate can guarantee semantic identification from observations alone without assumptions. Persistent attacks can form coherent repeated patterns; benign changes can be abrupt or irregular. If the algorithm promotes every persistent pattern, repeated faults poison memory; if it never promotes, benign drift causes persistent false alarms. This is a problem definition and observability limit, not a component novelty opportunity.

## Pairwise and combined overlap

| Proposed pairing | Closest evidence | What remains unestablished |
|---|---|---|
| Normality gate + online adaptation | M2N2, CANDI | Persistent recurrent regime isolation and lifecycle transitions |
| Normal memory + score-gated admission | MemStream; CANDI reference banks; MemTTA thesis | Candidate quarantine and temporal confirmation |
| Unknown/defer + delayed update | METER; smart-building drift buffer | Candidate bank whose state is explicitly separate from protected confirmed regimes |
| Candidate patterns + promotion + recurrence | AnDri | Recurrent neural state as the versioned normal representation; comparable contamination semantics |
| Protected old knowledge + new capacity | ARCUS, O-LoRA, CoTTA | A unified unsupervised TSAD state lifecycle with evidence-gated promotion and regression testing |
| Recurrent state anomaly scoring | MD-RS, xLSTMAD | Online state adaptation with normality confirmation |

## Falsifiers for the residual gap

The narrow framing should be withdrawn if a primary-source search finds a prior TSAD or streaming AD method with the same operational lifecycle, especially one that:

1. leaves confirmed recurrent normal states isolated from candidate writes;
2. stores uncertain observations or state transitions in a separate candidate;
3. promotes only after explicit time, evidence, and contamination controls;
4. keeps multiple confirmed regimes and reactivates a matched old regime; and
5. evaluates false promotion, adaptation delay, recovery and forgetting.

Even if no such paper is found, a method that differs only in naming or state container is not a meaningful contribution. The design must demonstrate a useful frontier shift or a capability unavailable to the closest baselines.
