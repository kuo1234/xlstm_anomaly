# Next experiment — ranking and decision

## The candidate the brief did not list

The brief's option **A** (`H+O1+O2` vs `H+O1+O2+I`) unions the two observable arms but leaves the
defect that actually threatens the result untouched: `O1` and `O2` enter the probe raw while `I`
carries a 13x causal rolling expansion at widths 4/8/16/32 (`evidence_red_team.md` §1a). Unioning
two temporally-unmatched controls produces a third temporally-unmatched control.

**A+** is option A with the asymmetry removed:

- `O1r` = the identical causal rolling expansion (`current, mean, std, slope` at widths 4, 8, 16,
  32) applied to each of the 128 `O1` columns → `128 x 13 = 1664` columns. Same transform, same
  widths, same warmup mask, same source-disjoint folds, same train-only scaler, same L2 probe, same
  four-value `C` grid, same pooled-validation selection, same single test evaluation.
- Arms: `H`, `H+O1r`, `H+O1r+I`, and the existing `H+O2`, `H+O2+I` as the unchanged reference.
- **Primary contrast:** `AP(H+O1r+I) − AP(H+O1r)`, both backbones, seeds 11/22/33, reported per
  source×seed unit as in the existing study.
- **Secondary arm (only if observation regeneration is allowed):** `P1r`, the same O1 statistic
  family and rolling expansion computed on the scaled **input** window `X` rather than on `R`. The
  existing cache stores `timestamp, score, internal_base18, residual, o1` and no model output, so
  `X` is not recoverable from it; the streams are deterministic from the generator, so this costs a
  regeneration pass but **no model inference**. This closes the second gap: no arm currently
  contains the observations.

Everything else about the frozen protocol is unchanged. This creates no new confirmatory family and
no GO/STOP rule; the `+0.02` margin remains a reference.

---

## Ranking by information value

| rank | experiment | uncertainty resolved | expected cost | result that would change direction | premature? |
|---|---|---|---|---|---|
| **1** | **A+** temporally matched observable control (`H+O1r+I` vs `H+O1r`), both backbones, 3 seeds | Whether the entire residual-controlled internal increment is a temporal-span artifact. This is the load-bearing question for the only viable paper spine. | **Lowest of all seven.** No training, no model inference. Probe refits on the six existing observation caches; 1,664 columns × ≈697k train rows ≈ 15 GiB peak versus the 9.24 GiB already benchmarked at 1,024 columns on a 117 GiB host. Add one generator pass if the `P1r` arm is included. | If the primary increment falls below `+0.02` for **both** backbones, spine A's title claim is dead and the project's headline becomes a negative result. If it holds at ≥ `+0.02` in ≥ 2/3 seeds for both, spine A is on solid ground and E2 becomes the next question. | No |
| **2** | **B** bounded nonlinear observable-only stress test | Whether the increment is about *information* or about *linear accessibility*. Partly pre-answered: engineered O1 already beats raw O2 by ≈0.035 AP under the same linear probe. | Moderate. One model class, two arms, validation-only selection. See the specification below. | If a fixed-capacity nonlinear model on the matched observable set closes the gap, the claim collapses to "the recurrent cell is a convenient nonlinear feature map", which is a much weaker paper. | No — but it is **uninterpretable before A+**. Run second. |
| 3 | **C** mLSTM dense replication, seeds 22/33 | Whether the one-seed `M_full\|H+S = +0.016657` reproduces. | Moderate — requires the dense observation cache and the replay observer for two more seeds. | A null stops the xLSTM-specific mechanism line permanently (decision D on the architecture question instead of B). A positive result still would not license a claim without the two missing controls. | Partly. As specified it would reproduce an uninterpretable number three times. Only worth running **with** a dimension-matched random-feature arm and the O1 residual control attached. |
| 4 | **D** online L2 decision rule | Whether internal evidence supports a label-free operating point. | High — requires a calibration protocol, a cost asymmetry, and paired baselines (always-adapt, never-adapt) that do not exist. | Would open L2. | **Yes, premature.** L1c is unresolved, so the rule would be built on evidence of unknown provenance. `arXiv:2608.30502` additionally documents the canonical calibration route failing on real streams (135/135 clean-stream fires). |
| 5 | **E** safe-adaptation contamination experiment | Whether gated adaptation reduces contamination harm. | Very high. | Would open L4. | **Yes, premature, and blocked upstream.** H1 natural harm is `NOT_RUN` and D-v2's single controlled step is below margin, so there is no demonstrated harm to improve on. An intervention without a harm baseline cannot produce a safety claim. |
| 6 | **F** W128 / W256 | Whether the effect is window-scale dependent. | High — re-training the matched pair at new window sizes. | Would broaden L1's scope. | **Yes.** Scaling an effect whose control is not yet matched multiplies the confound rather than testing it. |
| 7 | **G** persistent state | Whether carried state adds information over per-window resets. | High, and H3b is LOCKED under the frozen protocol. | Would open C1/H3b. | **Yes.** Also structurally blocked for the mLSTM arm: the observer replays the recurrence from zero state per window, so there is no persistent-state content to carry. |

**The three to run, in order: A+, then B, then C-with-controls** — and C only if A+ survives.

---

## Nonlinear control decision

**Does a serious reviewer reasonably require a modest nonlinear observable-only stress test before
accepting the internal-state representation claim?**

**Yes — unambiguously.** The claim "internal state carries evidence the observables do not" is a
claim about information; a linear probe measures linear accessibility. The repository's own
`interpretation.md` concedes this, and the O1-versus-O2 result makes it concrete: hand-built
nonlinear statistics of the residual beat the raw residual by ≈0.035 AP (xLSTM) and ≈0.038 AP
(LSTM) under the identical probe, which is direct evidence that the probe class is load-bearing.
The paper will not survive review without this test.

But it is the **second** question. Run it on the matched observable set from A+, not on the current
unmatched one.

### Specification (one model, no zoo)

**Model: gradient-boosted trees on the matched engineered observable set.** Chosen over a shallow
MLP because the evidence already says engineered nonlinear residual statistics are the strongest
observable competitor, because trees need no architecture search, and because they are
scale-invariant and so require no new preprocessing decisions. A small temporal CNN on raw `R` and a
random-Fourier-feature model are explicitly **not** run.

| element | frozen value |
|---|---|
| implementation | `sklearn.ensemble.HistGradientBoostingClassifier` |
| fixed architecture | `max_leaf_nodes=31`, `max_depth=6`, `min_samples_leaf=100`, `l2_regularization=1.0`, `learning_rate=0.1` |
| fixed capacity | `max_iter ∈ {100, 300}` — the **only** tuned hyperparameter |
| selection | pooled **validation** AP on sources `2000..2004`; exact ties resolve to the smaller `max_iter`; one test evaluation on `3000..3009` |
| test discipline | no test result may select a feature, an arm, a seed, or a hyperparameter |
| randomness | `random_state = 901` (the existing bootstrap seed), fixed before any arm is fit |
| **arms — both required** | `H+O1r` (observable-only) and `H+O1r+I`. The **same** model class is fit to both. A nonlinear observable arm compared against a linear internal arm measures the probe, not the features. |
| estimand | `AP(H+O1r+I) − AP(H+O1r)` under the nonlinear class, reported alongside the linear-class value from A+ |
| status | exploratory; no new p-value family, no GO/STOP rule, `+0.02` remains a reference |

Optional second model, only if the first is ambiguous: a single-hidden-layer MLP (256 units, ReLU,
`alpha ∈ {1e-4, 1e-3}` selected on pooled validation AP, fixed 50 epochs, no early stopping on
test). Do not add a third.

---

## OUTPUT 4

```
DO_NEXT: A+ — temporally matched observable control. Re-fit the frozen L2 probe with the
identical causal rolling expansion (current, mean, std, slope at widths 4/8/16/32) applied to
the 128 O1 residual-summary columns, giving arms H, H+O1r, H+O1r+I for both xLSTM and the
matched LSTM at detector seeds 11/22/33, with primary contrast AP(H+O1r+I) - AP(H+O1r) reported
per source-by-seed unit. No training, no model inference, no change to any other frozen element.
```

```
IF the primary increment is below +0.02 for both backbones (or positive in fewer than 2 of 3
   seeds for each):
   THEN stop the internal-state representation line and write the negative result — "an assumed
        internal-state advantage for anomaly-vs-drift evidence disappears once the observable
        control is matched on temporal span" — using the already-frozen protocol; do not run the
        nonlinear probe, the mLSTM replication, W128/W256, persistent state, or any adaptation
        experiment.
```

```
IF the primary increment holds at >= +0.02 in >= 2 of 3 seeds for both backbones:
   THEN run the bounded nonlinear observable stress test exactly as specified above
        (HistGradientBoostingClassifier, both arms, validation-only selection), and only after
        that schedule the three-seed dense mLSTM replication with its two missing controls
        attached.
```
