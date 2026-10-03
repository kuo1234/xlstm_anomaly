# Step 1c — oracle rollback-granularity pilot (P7+P10, issue #15)

Authorized in #15 comment 5965829950. Exploratory: no learned rollback policy, automatic segmentation, admission
classifier, W4, six machines, bootstrap or contamination-ratio matrix.

- **Code:** `scripts/p10_step1c_rollback.py`, `scripts/p10_step1c_aggregate.py`.
- **Tests:** `tests/test_p10_step1c.py`, 3 checks. They verify that W2 ledger subtraction equals a replay with the
  removed writes as decay-only steps (to 1e-9), that W1 tag deletion equals replay, that W3 replay is exact, and the
  category masks.
- **Data:** machine-3-7 / 1-6 / 2-7, train split only (files SHA-matched to the G-L1 manifest).
- **Units:** φ1 = 9 units (3 machines × seeds 11/22/33), φ2 = 3 units. Ramp is primary, level a cross-check.
- **Stream:** the same as Step 1b, with the same burst draws.

## Design

- **History written after M0, in order:**
  1. the admitted segment [ta, ta+L) from the actual stream, with L ∈ {30, 38, 46} (composition 0/30/0, 0/30/8,
     8/30/8);
  2. a delay: the next d ∈ {0, 64} steps of the actual stream, written as normal;
  3. an oracle rollback;
  4. freeze and evaluate.
- **Step categories:** fault-value [ta, ta+30); recovery-key [ta+30, ta+38) (value clean, key contains A1); benign.
  - With L=30, the 8 recovery-key steps fall into the *delay*, not the segment.
- **Rollback targets:**
  - R0: none;
  - R_fault: fault-value steps;
  - R_all: the admitted segment (delay writes stay);
  - R_fault_rec: fault-value + recovery-key steps, wherever they were written.
- **Rollback semantics:**
  - **W1:** delete the target entries by provenance tag (equal to replay).
  - **W2 f=.995:** analytical ledger subtraction, `C −= f^age v kᵀ`, `n −= f^age k`. The φ2 read uses the split
    positive map.
  - **W3 β=.1 / .5:** checkpoint at M0 plus replay of the kept writes (exact oracle rollback).
- **References:**
  - T = the clean counterfactual (the same segment and delay steps from the stream without the fault).
  - **T_R = the same rollback applied to the clean history.** This separates two effects:
    `lift_R/lift_T = (lift_R/lift_TR) × (lift_TR/lift_T)`, i.e. contamination left behind × information removed.
- **Endpoints:**
  - **Residual (functional):** Σ_ep mean_q‖M_R(q) − M_TR(q)‖ / Σ_ep mean_q‖M_R0(q) − M_T(q)‖. Probe keys are the eval
    window plus the A2 windows. 1 = contamination untouched, 0 = none left.
  - **A2:** paired lift at Δ=128 (A2 after the latest write plus a 16-step guard). Ratio = lift_R / lift_TR.
  - **Adaptation:** FPR on [ta+126, ta+638). Lost adaptation = FPR(T_R) − FPR(T).

## Results (ramp, φ1; cross-checks below)

### 1. Removing only fault-value steps is not enough for W1 and W3; it nearly is for W2

Contamination left after R_fault:

| | W1 | W2 f=.995 | W3 β=.1 | W3 β=.5 |
|---|---|---|---|---|
| L=38, immediate | 0.51 | 0.03 | 0.21 | **0.92** |
| L=46, immediate | 0.41 | 0.02 | 0.23 | **1.03** |
| any L, after 64 writes | 0.32 | 0.02 | 0.37 | **1.09** |

A2 ratio vs T_R after R_fault:

| | W1 | W2 f=.995 | W3 β=.1 | W3 β=.5 |
|---|---|---|---|---|
| L=38, immediate | 0.86 | 0.99 | 0.91 | 0.78 |
| L=46, immediate | 0.97 | 0.99 | 0.95 | 0.93 |
| after 64 writes | 1.03 | 1.00 | 0.99 | 0.94–0.95 |

- **What is left:** the recovery-key writes, whose keys contain the fault and whose values are clean. For W3 β=.5
  (recency) they are as large a functional change as the whole contamination (residual ≈ 1). Behaviourally they
  leave residual masking (0.78) rather than inversion.
- **R_fault_rec recovers the clean T_R exactly** for every operator, segment and delay: residual 0 and A2 ratio 1.00,
  because every kept step is then identical in the actual and clean streams.
- **The no-rollback state for reference:** with L=30 immediate, R0 is inverted (W1 −0.14, W3 β=.1 −0.69, W3 β=.5
  −1.12), and any rollback that removes the fault steps restores it.

### 2. The admitted-segment boundary does not bound the contamination once writing continues

With L=30 and a 64-step delay, the recovery-key steps are written *after* the segment, as normal writes. R_all then
leaves exactly the same residual as R_fault:

| | W1 | W2 | W3 β=.1 | W3 β=.5 |
|---|---|---|---|---|
| residual after R_all | 0.32 | 0.02 | 0.36 | 1.09 |

So rollback has to be defined by **provenance of fault-touched writes**: any write whose key window or value overlaps
the fault. Defining it by the admission decision that was later found wrong is not sufficient. A P7 rollback that
only reverts "the segment that was admitted" misses the spill-over in the keys of later writes.

### 3. Delayed vs immediate rollback

- **Contamination does not decay away by itself.** After 64 clean writes and no rollback (R0), the A2 ratio vs T is
  0.42–0.46 for W1 (append never forgets), 0.86–0.87 for W3 β=.1, 0.78–0.80 for W2, and 1.08–1.09 for W3 β=.5
  (sensitization, because recovery and benign steps followed).
- **Lost adaptation depends on timing.**
  - Immediate R_all / R_fault_rec discard information the clean counterfactual keeps: FPR(T_R) − FPR(T) = 0.06–0.10
    for W1/W3 and 0.03–0.04 for W2 when the whole segment goes.
  - After 64 clean writes this cost is ≈ 0 (≤ 0.004), since the delay supplies the regime information.
  - So delayed rollback is *cheaper in utility* in this setting. It is not harder in accuracy for exact methods.
- **Compute cost grows with delay for W3.** Exact delta-rule rollback must replay every kept write since the
  checkpoint. At L=46 that is 16 / 0 / 8 writes immediately vs 80 / 64 / 72 after the delay (R_fault / R_all /
  R_fault_rec).
  - W1 deletion and W2 subtraction touch only the removed entries, independent of the delay.
  - This is the reversibility cost of the nonlinear distributed write.

### 4. W2 ledger subtraction is exact only under "decay kept" semantics

Analytical subtraction equals a replay in which the removed steps become decay-only steps (verified to 1e-9). That is
not the same as "never written":

- When the removed block is the last write (immediate R_all), the difference is 0, because the ratio read is
  invariant to uniform decay.
- When writes follow the removed block, the subtracted state differs from never-written by 0.30–0.71 of the original
  contamination distance (largest with more later writes and longer L). Older content stays decayed by the removed
  slots, so the later writes are relatively over-weighted.
- Reaching the never-written state also needs re-weighting the writes that follow the removed block. That is still
  linear, but it costs O(later writes), like W3 replay. The cheap O(removed) inverse exists only for the
  decay-kept semantics.

## Cross-checks (φ2, level)

`step1c_summary.csv`:

- **Residual after R_fault (L=38, immediate):** W1 0.24–0.51, W2 0.03–0.07, W3 β=.1 0.21–0.27, W3 β=.5 0.73–0.98.
- **After the delay:** W3 β=.5 0.82–1.40.
- **R_all spill-over** at L=30 with delay holds in all four φ × family cells.
- **R_fault_rec residual = 0** in every cell.
- **A2 ratio after R_fault (L=38, immediate):** W3 β=.5 0.73–0.89, W1 0.86–0.96.

## Answer to the Step 1c question

Yes: rollback granularity × write operator decides whether the clean counterfactual is recovered.

- **Removing only the fault-value steps** is nearly sufficient for normalised Hebbian (W2), partly insufficient for
  append (W1, 30–50% of the contamination left), and insufficient for a high-β delta rule (W3 β=.5, ~100% left).
- **The admitted-segment boundary is the wrong rollback unit** once writing continues, because fault-touched keys
  spill into later writes.
- **Removing every fault-touched write (value or key)** restores the clean counterfactual exactly for all operators.
  Its cost is lost adaptation if done immediately, and replay cost growing with delay for the delta rule.

## Caveats

- Oracle step categories; one fault type (burst); delays 0 / 64 only; Δ = 128 (Δ = 256 in the CSV).
- The exactness of R_fault_rec is partly by construction: the kept benign steps are identical in both streams. The
  informative contrasts are R_fault vs R_fault_rec, R_all under delay, and the cost side.
- Not a production rollback design; the replay cost is reported, not optimised.

## Files

- `fig_rollback_residual.png`, `fig_rollback_A2.png`, `fig_rollback_costs.png`
- `step1c_summary.csv`, `step1c_units.csv`, `step1c_raw.csv.gz`, `run_config.json`
