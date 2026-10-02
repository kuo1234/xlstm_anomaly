# P10 / T1 occupancy audit — memory side

Scope: has anyone studied contamination or absorption of test-time-learned / fast-weight memory by anomalous inputs, and has repeated-anomaly self-masking been quantified? Status: **provisional**. Search coverage was web search plus a limited arXiv keyword API; OpenAlex and Semantic Scholar were not queried. 35 table rows (36 papers) were screened. 17 full texts were downloaded and examined by keyword scan plus targeted passage reading, not cover-to-cover; Patched-DeltaNet was read in an earlier session. The remainder rest on search snippets or citations and are labelled as such in `p10_occupancy_memory.csv`. A negative result below means "not found in the sources examined", not "does not exist".

## Verdicts per attack point

### AP1 — contamination of test-time-learned / fast-weight memory by anomalous inputs: **PARTIAL**
- **Generic phenomenon is occupied, in other settings.** Online parameter/statistics updates absorb attacker-chosen inputs and the damage persists: TePA (arXiv 2308.08505; 10 poisoned samples take accuracy 76.2% to 41.8%), DIA (2301.12576), realistic test-time data poisoning (2410.04682, snippet only), MedBN (CVPR 2024, snippet only). All are vision TTA with adversarial samples and BN/parameter updates.
- **Closest recurrent-state result:** HiSPA (2601.01972) shows short trigger sequences irreversibly overwrite Mamba hidden state, measured as retrieval accuracy with trigger vs clean prompt (paired test, drops 5.0 to 8.1 points for 5 of 7 triggers). It is a selective SSM, adversarial, retroactive erasure, LLM domain.
- **LLM memory poisoning** (MemPoison 2605.29960, 2606.04329, ER-MIA 2602.15344, 2609.00523) concerns explicit external stores written through a pipeline. Conceptually "one write persists", but not parametric state.
- **Not found:** any study of Titans neural memory, TTT layers, (Gated) DeltaNet, or mLSTM matrix memory being contaminated by anomalous or surprising inputs, in TSAD or in LLMs. Titans (2501.00663) states the premise (surprising events are more memorable) and never examines the consequence. Patched-DeltaNet (2605.27992) uses a delta-rule memory for TSAD but resets state per window. Sparse Delta Memory lists adversarial key collisions only as open work (secondary summary).
- **TSAD side acknowledges the risk without measuring it.** COMET and M2N2 gate updates on predicted-normal and say contamination is a hazard. CANDI is the only one with a number: ~10% (SMD 1-8) and ~25% (SMD 2-1) of its curated adaptation samples are real anomalies, and it still improves AUROC.
- Net: the specific architecture class x TSAD x anomaly-as-write combination is open; the general idea "adaptive models absorb bad inputs" is not novel and a reviewer will say so.

### AP2 — repeated-anomaly attenuation / self-masking quantified, counterfactually or as masking-vs-similarity: **OPEN (provisional)**
- Keyword scan of the 17 full texts (patterns for repeated/recurring anomaly, masking, swamping, counterfactual, with/without update) found **no** measurement of recurrence attenuation in any recurrent, SSM, fast-weight or streaming-TTA detector. M2N2, COMET, METER, DyMETER, TimeRCD, TimeRep contain no relevant hit.
- **DAMP (Lu et al., KDD 2022) is the only place the effect is named.** The twin-freak problem is the batch-discord failure in which two occurrences of one pattern are each other's nearest neighbour. The left matrix profile is adopted so the first occurrence is flagged and later ones are explicitly set aside (to be found by similarity search). This treats the second-occurrence masking as a property of kNN-with-history, with qualitative ECG examples and accuracy comparisons, not as a measured function of time gap or similarity, and with no write/no-write contrast.
- MemStream Sec 5.4 and CANDI's with/without-TTA score plot are the nearest counterfactual-style designs, but they test (i) a single anomaly placed in memory at initialisation (AUC vs beta, gamma) and (ii) shift-driven false positives, respectively. Neither varies the gap to a recurrence nor the similarity of the recurrence.
- Net: counterfactual WIM_sub(Delta) with F-sub/F-skip/F-decay controls and a masking kernel are not found in the sources examined.

### AP3 — baseline map (what each measures vs WIM and the masking kernel)
| Baseline | Memory type | What it measures | Difference from WIM / masking kernel |
|---|---|---|---|
| DAMP / left-MP | Non-parametric: all past subsequences, no decay | Discord detection accuracy; twin-freak shown qualitatively on ECG | Masking is by construction (1-NN to history). It is the kNN-append reference for RQ2': a neural kernel no wider than this is "neural twin-freak". No Delta sweep, no similarity curve, no write/no-write branch. |
| MemStream | kNN latent memory, FIFO, beta write gate, gamma discounted kNN | Sec 5.4: AUC when one labelled anomaly sits in memory at init, across beta and gamma | Closest single-event poisoning ablation. One event, tabular, AUC (not rank-quantile of the later score), no recurrence, no Delta. |
| CANDI | Adapter weights on frozen backbone | Anomaly share (10%/25%) in adaptation set; AUROC/AUPRC with vs without TTA | Contamination counted, not traced to a specific later event. |
| M2N2 | Full-model online fine-tuning + EMA trend | Ablate update vs detrend | Assumes normal-only updates; contamination not measured. |
| COMET | VQ codebook + coreset | Benchmark F1/AUC | Gate by codebook activation; contamination avoided by design, no test. |
| METER / DyMETER | Hypernetwork-generated parameters / uncertainty-gated updates | Drift-adaptation accuracy | Persistence benefit under drift (RQ0-adjacent); no masking. |
| LLM memory poisoning | Explicit text stores | Attack success over write-retrieve-use | Adversarial, discrete retrieval, no counterfactual F-sub. |
| TTA poisoning (TePA/DIA) | BN stats / weights | Benign-sample accuracy after poison | Adversarial; no "same event twice". |
| HiSPA | Mamba state | Retrieval with vs without trigger | Retroactive erasure, not suppression of a later recurrence. |

## Strongest reviewer counterarguments
1. **"This is the known stability/plasticity or twin-freak effect re-measured."** Any adaptive model that learns from its stream will score a repeat lower; DAMP builds this in, MemStream gates against it, and COMET/CANDI/M2N2 motivate their update rules by it. Defence needed: show neural memory differs from kNN-append in kernel width, decay and dose-response (RQ2'); if it does not, this is a replication of DAMP's observation (the pre-registered STOP).
2. **"Nobody deploys Titans/TTT/mLSTM with persistent state for TSAD."** The only TSAD precedent (Patched-DeltaNet) resets per window. RQ0 (persistent state gives a benefit under benign drift) is the guard; without it the effect is irrelevant in practice.
3. **"Attack-framed work already covers state contamination"** (TePA, DIA, HiSPA). Defence: those are adversarial and not counterfactual on a specific recurrence; WIM is natural-anomaly, paired, and uses a normal-segment replacement of A1.

**Strongest single threat:** the combination of DAMP (masking acknowledged as design) and MemStream Sec 5.4 (anomaly-in-memory ablation), because together they let a reviewer call the existence result (RQ1) expected and confine novelty to RQ2' and RQ3. Unread items that could still occupy the space: FITNESS (ICML 2022), SPOT/DSPOT, HTM follow-ups, and newer unindexed arXiv (Sept 2026) papers.

## Caveats and flags
- arXiv:2509.12650 is *Leveraging Intermediate Representations of TSFMs for AD* (TimeRep); project memory calls it TTAMB. Please re-check the ID/name pairing.
- Venues marked "unverified" in the CSV were not confirmed against proceedings.
- No experiments were run.
