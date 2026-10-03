# Step 2b — delayed-evidence drift-vs-fault admission pilot (P7+P10, issue #15)

Authorized in #15 comment 5970197497. Development / exploratory pilot on the same three SMD machines as Step 2a
(machine-1-6 / 2-7 / 3-7). Their labels were exposure-visible before, and the designer knew the Step 2a failure
episodes, so **no number here is confirmatory**. No deep classifier, no bootstrap gate, no SOTA claim.

Question: for a quarantined sustained deviation, can *causal delayed evidence* tell a new normal regime (should be
promoted) from a long fault (should not be written)?

## 1. Protocol

| stage | commit | content |
|---|---|---|
| label-blind main run | `2c9e92b` | 297 traces (3 machines × φ seeds 11/22/33 × W1/W2/W3 × 11 policies), 1704 evidence checkpoints; seal `2c44143c…` (`labels_read: 0`) |
| gated dev evaluation | — | `load_test_labels(purpose="step2b_dev_evaluation")`, re-verifies seal + every sealed file; 3 reads |
| label-blind post-hoc run | `0d0c4f1` | one rule chosen **after** the dev evaluation (§5); 27 traces; seal `f9399a55…` (`posthoc: true`) |
| gated post-hoc evaluation | — | 3 reads, separate log |

- All rules and thresholds of the main run were fixed in `CFG2B` before any Step 2b label access.
  The evaluator was committed with the seal.
- One evaluator bug was found after label access: the feature named `level` overwrote the unit-level key of
  the identifiability row. It only affected that key, not any AUROC value. The table is recomputed from the
  labelled checkpoint CSV by `p10_step2b_aggregate.py`, with no new label read, and the evaluator is fixed.
- Interpretation boundaries (Step 2a review):
  - this is **16-step delayed causal admission**;
  - the detector architecture, M0, φ, τ calibration and scoring rule are fixed across policies, while the memory
    state differs by policy (that is the policy effect);
  - the 27 units are 3 machines × 3 seeds × 3 operators, not 27 independent datasets. Machine-level means are
    reported alongside unit counts.

## 2. Mechanism

Segment machinery, shared by all new policies:

- A block with an exceedance opens or extends a quarantine segment. Held blocks are not written.
- Clean blocks inside a segment are held too. The segment ends (DISCARD) after 2 consecutive clean blocks.
- A checkpoint fires at segment age 256 and then every 128 steps. Each checkpoint chooses
  **KEEP-QUARANTINED** or **PROMOTE**.
- PROMOTE writes only the trailing window T (the last 256 steps), not the whole buffer.

Delayed evidence at each checkpoint (all causal):

| feature | definition |
|---|---|
| `level` | median score(T)/τ — what the instantaneous gate sees |
| `cv`, `slope` | variability and trend of the score over T |
| `self0`, `self`, `learn` | q0.9 score of T2 before / after a **trial write of T1 into a copy of the operator's memory**, /τ; ratio |
| `stat` | plateau ratio ‖mean z(T2)−mean z(T1)‖ / ‖mean z(T)−mean z(pre-segment 256)‖ |
| `shift`, `nch`, `conc` | size of the change, number of affected channels, top-3 channel concentration |
| `novel` | key novelty vs. the initial normal memory |
| `dis`, `frozen` | W1/W2/W3 disagreement and mean level of frozen-M0 scores |

Policies:

- **A–D**: Step 2a policies, reproduced exactly (no update, always, threshold, quarantine age 512 with whole-buffer promotion).
- **H_hold**: segment machinery, never promotes. This is the reference run for identifiability.
- **D_trail512**: promote T at age ≥ 512 (age only).
- **DE_stab**: promote when `self ≤ 1` and `stat ≤ 0.5`.
- **DE_stab512**: DE_stab with age ≥ 512 (age-matched to D_trail512).
- **C_lb / DE_stab_lb**: delayed commit. Clean blocks wait 128 steps; an exceedance purges pending blocks with max score > q0.95.
- **rand_DE**: random writes at DE_stab's write fraction.

Evaluation adds two label-defined point sets, both inside the H_hold persistent segments:

- **PF**: persistent-fault points. Recall should be high (the long fault is not absorbed).
- **PN**: persistent-normal points (a new regime). FPR should be low (the memory adapted).

## 3. The persistent segments are few

`results/step2b_physical_segments.csv`: clustering segment starts across seeds and operators gives
**two long physical segments** that carry almost all checkpoints:

| machine | start | max age | fault ck | normal ck | structure |
|---|---|---|---|---|---|
| machine-1-6 | 18656 | 4992 | 206 | 40 | 3161-step labelled fault, short normal tail |
| machine-3-7 | 21152 | 7552 | 12 | 477 | short labelled fault, then a long post-fault regime labelled normal |
| machine-2-7 | 18576 | 384 | 18 | 0 | short fault segment |

There are also three 256-step segments (two normal, one mixed).

Both long cases have the same shape: **the "new normal" is the tail of a segment that began as a fault.** The
decision is therefore temporal (has the deviation *settled*?), not a property of the segment as a whole. All
identifiability evidence below rests on these 2 physical regimes.

## 4. Results with the pre-registered rules

Means over 9 units (3 machines × 3 seeds).

| op | policy | AP | VUS-PR | PF recall | PN FPR | anomaly written |
|---|---|---|---|---|---|---|
| W1 | threshold | 0.681 | 0.681 | 0.922 | 0.512 | 0.115 |
| W1 | quarantine (2a) | 0.659 | 0.669 | 0.715 | 0.200 | 0.482 |
| W1 | trailing, age 512 | 0.702 | 0.721 | 0.726 | 0.201 | 0.257 |
| W1 | DE_stab | 0.717 | 0.748 | 0.740 | 0.206 | 0.482 |
| W1 | DE_stab512 | 0.722 | 0.738 | 0.782 | 0.201 | 0.203 |
| W1 | DE_stab_lb | 0.726 | 0.752 | 0.778 | 0.208 | 0.417 |
| W2 | threshold / DE_stab | 0.657 / 0.676 | 0.647 / 0.684 | 0.961 / 0.765 | 0.496 / 0.242 | 0.146 / 0.364 |
| W3 | threshold / DE_stab | 0.667 / 0.691 | 0.671 / 0.714 | 0.960 / 0.742 | 0.641 / 0.323 | 0.138 / 0.481 |

Full table: `results/step2b_summary.csv`.

Paired AP contrasts (`results/step2b_contrasts_AP.csv`):

| contrast | unit wins | mean ΔAP | ΔAP 1-6 / 2-7 / 3-7 |
|---|---|---|---|
| DE_stab − threshold | 9/27 | +0.026 | −0.145 / −0.087 / **+0.311** |
| DE_stab − quarantine (2a) | 17/27 | +0.043 | +0.059 / −0.087 / +0.156 |
| trailing512 − quarantine (2a) | 15/27 | +0.017 | +0.016 / −0.001 / +0.036 |
| DE_stab512 − trailing512 | 7/27 (15 ties) | +0.004 | +0.041 / 0.000 / −0.029 |
| DE_stab − random matched | 27/27 | +0.284 | all three positive |
| C_lb − threshold | 3/27 | −0.012 | — |
| DE_stab_lb − DE_stab | 2/27 | −0.021 | — |

Reading:

1. **The pre-registered rule does not break the trade-off.**
   - Every promoting policy sits at PF recall ≈ 0.72–0.81 and PN FPR ≈ 0.20–0.33.
   - Every non-promoting policy sits at PF ≈ 0.92–0.99 and PN ≈ 0.50–0.79 (`fig_step2b_frontier.png`).
   - Evidence policies dominate the Step 2a quarantine on this plane: same PN, more PF. The long fault on
     machine-1-6 is written 26–36% (DE_stab512 / DE_stab) instead of 63–65% (quarantine) or 45–49% (trailing512).
   - It is still far from the threshold gate (3–5%).
2. **The machines conflict.**
   - On machine-3-7 promotion is required: the threshold gate's PN FPR there is ≈ 1.0.
   - On machine-1-6 and 2-7 any fault promotion costs AP.
   - So the pooled AP gain of DE_stab (+0.026 vs threshold) is one machine winning large and two losing.
3. **Why the rule fails.** `results/step2b_rule_pass_rates.csv`: `self ≤ 1 ∧ stat ≤ 0.5` passes 20% / 39% / 25%
   of fault checkpoints (1-6 / 2-7 / 3-7) and 93–97% of normal ones. A segment is promoted at its first passing
   checkpoint, so a long fault with ~25 checkpoints is almost surely promoted at some point. Trial-write
   self-consistency (`self`) and the plateau ratio are too permissive: a fault has locally stationary sub-plateaus.
4. **Promote only the trailing window, not the whole buffer.** trailing512 > quarantine (2a) on 15/27, and it
   halves the anomalous points written (0.26 vs 0.48 for W1). This part needs no evidence at all.
5. **Delayed commit (slow-onset fix) does not pay.**
   - It does recover the machine-1-6 slow-onset episode for W1: written 0.68 → 0.00, score ratio vs no-update
     0.41 → 0.99.
   - But it purges so many benign blocks that adaptation suffers (W1 written fraction 0.79 → 0.50; machine-1-6 W1
     normal FPR 0.006 → 0.42).
   - Net AP is lower: C_lb loses on 24/27 units and DE_stab_lb on 25/27. The τ_low = q0.95 purge is too aggressive.

## 5. Identifiability: which delayed signals carry information the instantaneous gate lacks

AUROC fault vs. normal on H_hold checkpoints (`results/step2b_identifiability_auroc.csv`):

| feature | pooled (236 F / 521 N) | machine-1-6 | machine-3-7 |
|---|---|---|---|
| `level` (instantaneous) | **0.32** | 0.96 | 0.83 |
| `frozen` (M0 score level) | 0.77 | 1.00 | 0.74 |
| `self` (trial-write residual) | 0.95 | 1.00 | 0.70 |
| `learn` | 0.92 | 0.79 | 0.68 |
| `stat` | 0.81 | 0.76 | 1.00 |
| `cv` (score variability) | **0.99** | 0.93 | **1.00** |
| `nch` | 0.77 | 0.25 | 0.90 |
| `novel`, `dis`, `conc` | ≤ 0.10 | inconsistent sign | inconsistent sign |

- The level a gate sees **reverses across machines**: machine-3-7's new regime scores higher than machine-1-6's
  fault. No single τ can separate them, which is the Step 2a wall.
- The variability of the score over the trailing window (`cv`) does separate them. Settled regimes have
  cv ≈ 0.02–0.05; fault phases have cv ≈ 0.17–0.36 (`fig_step2b_evidence.png`).
  A *persistent* deviation is not evidence of a new normal. A *stabilised* one is, on these two regimes.
- Channel-structure, novelty and operator-disagreement features change sign between the machines and carry no
  usable signal here.
- Segment-level AUROC at the first checkpoint (age 256) is not informative: only 4 normal segments, and the
  post-fault regimes are not yet reached at age 256.
- A label-trained leave-one-machine-out linear probe reaches AUROC 1.0 on both held-out machines. With 2
  regimes this only says the information exists in-sample. It is a diagnostic, not a policy.

### Post-hoc headroom run (dev-tuned, not confirmatory)

One rule was added after seeing §5: **DEph_cv** = DE_stab ∧ `cv ≤ 0.10`. The threshold lies between the dev class
medians. It passes 0/236 fault and 93–97% of normal checkpoints. Run label-blind and sealed (`0d0c4f1`), it gives:

| op | AP (thr / DE_stab / **DEph_cv**) | PF recall | PN FPR | long fault 1-6 written |
|---|---|---|---|---|
| W1 | 0.681 / 0.717 / **0.756** | 0.916 | 0.201 | 0.03 |
| W2 | 0.657 / 0.676 / **0.755** | 0.960 | 0.235 | 0.02 |
| W3 | 0.667 / 0.691 / **0.780** | 0.966 | 0.246 | 0.03 |

- It has the threshold gate's PF recall together with quarantine's PN FPR, i.e. the trade-off breaks on the dev set.
- Machine-level ΔAP vs threshold: 1-6 +0.000, 2-7 −0.001, 3-7 +0.287. vs no-update: 27/27 units.
- It promoted zero fault windows (9 mixed, 4 normal).

Caveats on this result:

- It is tuned on 2 physical regimes.
- The margin is thin. On machine-1-6, 4 of 206 fault checkpoints already have cv ≤ 0.10 (minimum 0.088); only the
  conjunction with `self`/`stat` blocks them. The seed-11 W1 trace stays at cv ≈ 0.12–0.24 (`fig_step2b_evidence.png` b).
- It must be re-tested with a sealed config on machines whose labels have not been seen before anything is claimed.

## 6. Answer to the Step 2b question

- **Pre-registered rules: no.** Trial-write self-consistency and plateau ratio, as pre-registered, do not break the
  drift-vs-long-fault wall. They shift the frontier relative to the Step 2a quarantine (less fault written at the
  same adaptation) but not to the threshold gate's fault recall.
- **Signal exists in-sample.** Delayed score-variability (`cv`) carries information that the instantaneous level
  does not (pooled AUROC 0.99 vs 0.32), and a dev-tuned rule using it removes the trade-off on these three machines.
- **The supported mechanism claim is modest.** On these two regimes, sustained deviations that stabilise (low
  score variability during the hold) are the ones that became labelled-normal regimes. Persistence alone
  is not evidence.
- **Two design facts hold without evidence:** promote only the trailing stabilised window, not the whole buffer;
  and a delayed-commit purge at q0.95 costs more adaptation than it saves.

## 7. Next step (proposal)

A confirmatory Step 2c with sealed config (DE_stab, DEph_cv, trailing512, threshold, quarantine; cv ≤ 0.10 frozen)
on SMD machines not yet label-inspected, or another labelled dataset, with machine as the unit of inference.
If cv does not transfer, the honest conclusion is an observation-only identifiability wall, and external evidence
would be needed (operator confirmation, cross-sensor checks).

## Files

- `scripts/p10_step2b_stream.py`, `p10_step2b_data.py`, `p10_step2b_eval.py` — main run, label gate, evaluator
- `scripts/p10_step2b_posthoc.py`, `p10_step2b_posthoc_eval.py` — post-hoc headroom run
- `scripts/p10_step2b_aggregate.py` — tables (no label access)
- `tests/test_p10_step2b.py` — label gate, trial-write copy semantics, causality of segment / delayed-commit policies
- `run/`, `posthoc_run/` — sealed traces, checkpoints, configs, seals
- `results/` — unit metrics, summaries, contrasts, identifiability, rule pass rates, promotion quality, episodes, label access logs
- `fig_step2b_frontier.png`, `fig_step2b_evidence.png`, `fig_step2b_ap_by_machine.png`
