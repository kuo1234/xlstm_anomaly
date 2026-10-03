# Step 2a — real-stream, non-oracle admission / quarantine / rollback pilot (P7+P10, issue #15)

Authorized in #15 comment 5969872677. Exploratory feasibility pilot: no seal of a protocol, no bootstrap, no SOTA
claim.

## Label handling (non-oracle)

The repo pattern of `scripts/real_data_r0_data.py` was followed.

1. **Label-blind stage** (`scripts/p10_step2a_stream.py`): reads only SMD train/test *observations* through
   `p10_step2a_data.load_observations`. A test asserts that the script contains no label path.
   - Output: 243 score traces (3 machines × φ seeds 11/22/33 × 3 operators × 9 policies), plus `runs.json` and
     `policy_config.json`.
   - All of these are listed with SHA-256 in `run/seal.json` (SHA-256 `9f7f271a87df52ec4d24c8c6775b30d023d219a01c9708ed980301092dbd988c`,
     `labels_read: 0`).
   - The seal, the traces and the evaluator were committed and pushed as `0f04812` **before any label was read**.
2. **Evaluation stage** (`scripts/p10_step2a_eval.py`): the only label-consuming code.
   - Labels come through `load_test_labels(purpose="step2a_final_evaluation")`, which re-verifies the seal SHA and every
     sealed trace before opening the label file.
   - The label files were downloaded at this point, not before.
   - Access log: `results/label_access_log.json`. There were 3 reads, one per machine, all after the seal.
3. **What the policies see:** only the causal anomaly score of the current and past steps, and the per-unit
   threshold τ (q0.99 of train-holdout scores). They never see labels, fault onsets/ends, recovery boundaries or episode
   identities.
4. **Exposure disclosure:** these three machines were already exposure-visible (an earlier committed data audit
   parsed all 28 SMD labels; see `research/m1_reproducibility_redteam_2026q3`). This pilot is exploratory and makes no
   label-blind confirmatory claim.

## Detector

The detector is the same role-matched normal-reference memory as in Step 1a–1c:

- key k_t = φ(z[t−8:t]) (random ReLU features, d_k = 128); value v_t = z_t;
- score s_t = ‖v_t − M(k_t)‖, computed before any write that includes t.

Data and calibration:

- All 38 channels, z-scored with train mean/sd (sd floor 0.02, |z| ≤ 20).
- M0 = the first 80% of the train split; τ = q0.99 of M0 scores on the last 20%.
- The test stream is processed in 16-step blocks: each block is scored with the memory at block start, then written
  according to the policy.

Operators: W1 append/kNN (K = 5), W2 Hebbian + normalizer f = .995, W3 delta rule β = .1.

**Detector vs policy:** the detector is fixed per unit. Every policy runs the same detector and differs only in which
points are written, so all differences between policies are policy effects.

## Policies (fixed before label access; `run/policy_config.json`)

| policy | rule |
|---|---|
| A no_update | never write |
| B always | write every point |
| C threshold | write a 16-step block only if no point exceeds τ |
| D quarantine | clean blocks written; a suspicious block is buffered; a clean block discards the buffer; a suspicious run of 32 blocks (512 steps) is promoted (sustained deviation treated as new normal) |
| E rollback | write optimistically; an exceedance run (gaps ≤ 8) reaching 8 exceedances triggers S = [run start − 8, last exceedance]; every stored write whose **value time or key window** intersects S is rolled back, and nothing touching S is written while the run lasts or afterwards |
| E_value | as E, but only value time is checked (Step 1c "admitted points only" ablation) |
| rand_C / D / E | random block writes at the same written fraction as C / D / E |

Rollback semantics: W1 deletes entries by time tag; W2 subtracts the write ledger; W3 restores the latest block
checkpoint and replays the kept writes.

## Results

Mean over 9 units (3 machines × 3 seeds); full table in `results/step2a_summary.csv`:

| operator | metric | no update | always | threshold | quarantine | rollback | rollback (value) | random (≙ threshold) |
|---|---|---|---|---|---|---|---|---|
| W1 | AP | 0.645 | 0.350 | **0.681** | 0.659 | 0.675 | 0.669 | 0.361 |
| W1 | VUS-PR | 0.636 | 0.388 | **0.681** | 0.669 | 0.675 | 0.670 | 0.398 |
| W2 f=.995 | AP | 0.610 | 0.481 | **0.657** | 0.635 | 0.655 | 0.654 | 0.501 |
| W2 f=.995 | VUS-PR | 0.581 | 0.508 | **0.647** | 0.636 | 0.646 | 0.646 | 0.534 |
| W3 β=.1 | AP | 0.627 | 0.381 | **0.667** | 0.662 | 0.604 | 0.553 | 0.391 |
| W3 β=.1 | VUS-PR | 0.623 | 0.429 | 0.671 | **0.675** | 0.609 | 0.565 | 0.439 |

W1 normal FPR at τ: no update 0.233, always 0.006, threshold 0.091, quarantine 0.010, rollback 0.090.
W1 point recall at τ: 0.770 / 0.187 / 0.745 / 0.580 / 0.733 in the same order.

Paired over the 27 units (AP; VUS-PR in brackets):

| comparison | units better | mean Δ |
|---|---|---|
| threshold > always | 24/27 | +0.264 (+0.225) |
| quarantine > always | 27/27 | +0.248 (+0.218) |
| rollback > always | 24/27 | +0.240 (+0.202) |
| threshold > no update | 27/27 | +0.041 (+0.053) |
| quarantine > no update | 18/27 | +0.024 (+0.047) |
| rollback > no update | 25/27 | +0.017 (+0.030) |
| threshold > random at the same write fraction | 23/27 | +0.251 (+0.210) |
| **rollback > threshold** | **4/27** | **−0.024 (−0.023)** |
| rollback (key+value) > rollback (value only) | 12/27 | +0.019 (+0.017); the gain is mostly W3 (+0.05) |

By machine (W1 AP):

| machine | no update | always | threshold | quarantine | rollback |
|---|---|---|---|---|---|
| machine-1-6 | 0.878 | 0.580 | **0.897** | 0.707 | 0.891 |
| machine-2-7 | 0.856 | 0.337 | **0.869** | **0.869** | 0.860 |
| machine-3-7 | 0.202 | 0.132 | 0.276 | **0.400** | 0.274 |

## Diagnostics

1. **Episodes absorbed under always-update** (mean score of B ÷ no-update < 0.7): 53 of 165 W1 episode-units
   (machine-1-6: 42, machine-2-7: 5, machine-3-7: 6).
   - Long episodes are hit hardest: >300 steps gives a median ratio of 0.29.
   - Example: machine-3-7, t = 21201 (`fig_step2a_episodes.png` b). The memory learns the anomaly within the episode,
     and its score falls below τ while the label is still 1.
2. **Did threshold / quarantine avoid it?** Mostly. For absorbed episodes the median ratio vs no-update is 0.73
   (threshold), 0.72 (quarantine) and 0.67 (rollback), against 0.29–0.40 for always-update on the long ones.
   Two failure modes:
   - **Slow-onset anomaly below τ** (machine-1-6, t = 4647, 398 steps): its early points never exceed τ, so threshold
     writes 70% of them and rollback writes 100% (no trigger). Every gating policy is absorbed as much as always-update
     (ratio 0.40).
   - **Quarantine promotes long anomalies** (machine-1-6, t = 18600, 3161 steps): after 512 suspicious steps the
     buffer is promoted, 68% of the episode is written, and the ratio drops to 0.41. This is why quarantine loses on
     machine-1-6.
3. **Did rollback actually repair?** When it triggered on an episode, yes: it wrote only 3% of that episode's points,
   and the episode score equals no-update (median ratio 1.00).
   - But it triggers on exactly the evidence the threshold gate already uses (exceedances of τ), so it rarely catches
     anything the gate misses.
   - Its optimism (writing short runs and the first steps of a run) does not pay off in AP: rollback beat threshold on
     only 4/27 units.
   - Rollback cost per stream (mean): rollback 2.6–2.9 rollbacks removing 13–22 entries; value-only 3.0–4.0 rollbacks
     removing 17–52 entries; W3 replay 13 writes (rollback) and 24 writes (value-only).
4. **Too conservative?** Yes, on machine-3-7. After the labelled anomaly the stream stays in a shifted regime that the
   labels call normal (`fig_step2a_episodes.png` b).
   - Threshold and rollback never write it, so their normal FPR stays at 0.26, the same as no-update.
   - Only quarantine's promotion (and always-update) adapts to it, which is why quarantine is best there (AP 0.40 vs
     0.28).
   - This is the drift-vs-fault identifiability trade-off showing up on real data.
5. **Where does the gain come from?**
   - Not from fewer updates: random writes at the same rate stay at always-update level (+0.00–0.05 AP).
   - Not from rollback: rollback ≤ threshold.
   - The gain comes from **preventing contamination at write time**.
   - Against no-update, the gating policies also gain modestly in AP (+0.02–0.04) and strongly in normal FPR
     (0.23 → 0.01–0.09), because they still absorb benign drift. They do not collapse to no-update.

## Answer to the Step 2a question

**Yes, there is measurable detection value, but it is the admission gate, not provenance rollback.**

- On the real SMD test stream, always-update memory absorbs anomalies (AP −0.30 vs no-update for W1, and point recall
  0.77 → 0.19).
- Causal, label-free admission control recovers all of it and slightly improves on no-update while keeping the
  adaptation benefit (AP +0.04, FPR 0.23 → 0.09; 27/27 units vs no-update).
- Provenance-aware rollback, using the same instantaneous evidence, adds nothing over the simple threshold gate here.
  Key-window provenance (vs value only) helps only for the delta-rule memory (W3).

**Why rollback adds nothing here:**

- Rollback can only add value when its trigger sees evidence the write-time gate did not have. Here it uses the same
  score, so it cannot.
- The two observed failure modes are exactly where a *different* delayed signal would be needed:
  - slow-onset anomalies below τ;
  - a post-fault regime that is a new normal vs a long fault that is not.

## Caveats

- 3 machines (machine-3-7 has only 5 episodes; machine-1-6 has 15.6% anomalous points); one φ family; fixed policy
  parameters (τ = q0.99, trigger 8, promotion 512) chosen before label access and not tuned.
- The detector is a simple memory-based scorer, not a strong SMD detector (W1 AP ranges 0.20–0.90 by machine).
- Labels of these machines were already exposure-visible (see above); no confirmatory claim.

## Files

- `run/`: sealed label-blind stage (`seal.json`, `runs.json`, `policy_config.json`, 243 traces)
- `results/`:
  - `step2a_summary.csv`, `step2a_summary_by_machine.csv`, `step2a_metrics_units.csv`;
  - per-episode trace `step2a_episode_trace.csv.gz` and `step2a_episode_ratios.csv`;
  - `label_access_log.json`
- Figures: `fig_step2a_policies.png`, `fig_step2a_episodes.png`
- Code: `scripts/p10_step2a_data.py`, `scripts/p10_step2a_stream.py`, `scripts/p10_step2a_eval.py`,
  `tests/test_p10_step2a.py` (4 passed)
