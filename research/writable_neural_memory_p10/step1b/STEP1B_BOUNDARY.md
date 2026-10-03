# Step 1b — mixed-segment / boundary pilot (P7+P10, issue #15)

Authorized in #15 comment 5965080510. Exploratory, oracle segments. No W4, learn-to-write, automatic
segmentation, learned admission, six machines, bootstrap or seal.

- **Code:** `scripts/p10_step1b_boundary.py`; `tests/test_p10_step1b.py` (2 composition checks).
- **Data:** machine-3-7 / 1-6 / 2-7, train split only. The three files were re-fetched from the OmniAnomaly
  repository because the local realdata folder was no longer present; the SHA-256 of all three matches the G-L1
  manifest.
- **Units:** φ1 = 9 units (3 machines × seeds 11/22/33); φ2 = 3 units. Both were run on every boundary because the
  cost is small.
- **Runtime:** about 2.5 min on CPU.

## Design

- **Regime:** the benign new-normal regime starts at the G-L1 plan onset t0 (ramp is primary, level a cross-check;
  2σ on 8 channels; 24 onsets per family).
- **Fault:** A1 is a 30-step, 2σ burst on 8 other channels at ta = t0+128, i.e. *inside* the new regime.
- **Writes:** memory = M0 + one oracle admission segment [ta+o, ta+o+L); nothing else is written.
- **Sweeps:**
  - Sweep A: L = 38, o ∈ {−16, −8, 0, +8, +16, +30}.
  - Sweep B: o = 0, L ∈ {16, 30, 38, 46, 62}.
- **Arms:** B writes the segment from the actual stream (regime + fault); D writes the same steps from the matched
  stream without the fault (regime only); C writes nothing.
- **Segment composition:** each step is benign (key and value untouched by A1), fault-value (value inside A1), or
  recovery-key (value clean, key window contains A1).
- **Read-outs:**
  - adaptation: FPR on [ta+84, ta+596) of the A2-free stream (fixed for all boundaries; the latest segment end is
    ta+68, followed by a 16-step guard). Threshold = q0.99 of M0 on [t0−1024, t0).
  - contamination: paired A2 lift (identical burst, plus a ×0.6 variant) at Δ = 64 and 256.
  - ratio = lift_B / lift_D.
- **Operators:** W1 append, W2 f=.995 (φ1 normalizer read; φ2 split positive feature map), W3 β=.1, W3 β=.5.

## Main result: the segment *end* relative to the fault's recovery transition controls the sign

Ramp, φ1. Tick label = benign / fault-value / recovery-key steps.

| segment | composition | W1 | W2 f=.995 | W3 β=.1 | W3 β=.5 |
|---|---|---|---|---|---|
| L=16 | 0/16/0 | −0.19 | 0.80 | −0.47 | −1.12 |
| L=30 | 0/30/0 | −0.25 | 0.63 | −0.74 | −1.14 |
| L=38 | 0/30/8 | −0.09 | 0.65 | 0.10 | 0.83 |
| L=46 | 8/30/8 | 0.16 | 0.67 | 0.57 | **1.09** |
| L=62 | 24/30/8 | 0.24 | 0.71 | 0.82 | **1.09** |
| o=−16, L=38 | 16/22/0 | 0.06 | 0.74 | −0.63 | −1.12 |
| o=+8, L=38 | 8/22/8 | 0.21 | 0.74 | 0.56 | 0.91 |
| o=+30, L=38 | 30/0/8 | 1.01 | 0.99 | 0.98 | 0.96 |

Values are the A2 lift ratio B/D at Δ=64. Across the 9 units, the min–max range at a point has median 0.08 and maximum 0.29.

There are three regimes, ordered by where the segment ends.

1. **Segment ends inside the fault (no recovery keys): inversion, "the fault becomes the expectation."** This holds for
   W1 and W3, and ratios go below 0.
   - Decomposition (W3 β=.5, L=30): on the A2-free stream at the A2 positions, the score under B is 9.5 vs 5.3 under D.
     With A2 present it is 5.1 vs 9.1.
   - So the memory now predicts the burst from the regime context. Its *absence* becomes the anomaly, and its presence
     is scored as normal.
   - Adaptation is lost at the same time. FPR reduction under B is 0.032 vs 0.096 under D for W3 β=.5, and 0.015 vs
     0.068 for W3 β=.1. Under φ2, W3 β=.5 is worse than writing nothing (−0.06 to −0.09).
2. **Segment includes the 8 recovery-key steps:** ordinary masking (W1 −0.09, W3 β=.1 0.10, W3 β=.5 0.83), and
   adaptation is mostly restored (B ≈ D).
3. **Recovery plus post-recovery benign steps:** masking weakens for W1 and W3 β=.1. **W3 β=.5 flips to
   sensitization** (1.09 at L=46 and 62); the A2 score under B exceeds D, 9.3 vs 9.0.

Fixed-length sliding (Sweep A) shows the same thing.

- Offsets −16 and −8 end inside or exactly at the end of the fault and invert.
- Offset 0 is the first segment that contains the recovery keys, and it masks.
- Offset +30 contains no fault values and has no effect.
- **The number of fault-value steps does not predict the sign.** o=+8 has 22 fault steps and masks mildly (W3 β=.1
  0.56). L=16 has only 16 fault steps and inverts (−0.47).

**W2 f=.995 has no regime boundaries.** Its masking is smooth (0.63–0.80), it never inverts or sensitizes, and its
adaptation grows monotonically with L (0.025 → 0.051). Its distributed write averages the segment into one
normalised kernel estimate, so the ordering of fault and recovery inside the segment matters little. W1 and W3 learn
the last transitions they saw (W1 by key locality, W3 by recency).

**Cross-checks** (`fig_boundary_tradeoff_crosscheck.png` b): the same profile holds for φ1/φ2 × ramp/level.
- Inversion at L ≤ 30 for W1 and W3.
- The jump at the recovery keys.
- W3 β=.5 sensitization: 1.10 (φ1 level), 1.14 (φ2 level), 1.00 (φ2 ramp).
- Magnitudes differ. W1 inverts more under φ2 and under level (down to −0.94).

**Δ=256:** W3 inversion persists (β=.5 −0.96; β=.1 −0.25 to −0.49), but W1's fades (0.06–0.30). This matches the
Step 1a.1 finding that append contamination needs background match.

**×0.6 variant at Δ=64:** same pattern, stronger for W3 (β=.5 −1.8 at L ≤ 30, 1.11 at L ≥ 46).

## Utility–harm trade-off

`fig_boundary_tradeoff_crosscheck.png` a shows ramp, φ1, Sweep B.

- **W1 and W3 move along a common direction:** a longer segment past the recovery edge brings both more adaptation
  and less masking. There is no interior trade-off point.
- **The bad corner is "short segment ending inside the fault":** low adaptation and inversion together.
- **W3 β=.5 reaches the highest adaptation (≈0.10)** together with sensitization.
- **W2 f=.995 sits apart:** modest adaptation (0.03–0.05), steady masking of about 0.65–0.8.

## Answer to the Step 1b question

Yes. With an oracle segment that contains new-normal and fault evidence, the boundary systematically controls
adaptation, masking and sensitization. The controlling variable is not the contamination fraction but **whether, and
by how much, the segment extends past the fault's recovery transition.** How strongly this matters is set by the
write operator:

- W3 (strong recency) has the sharpest transitions and the only sign flip to sensitization.
- W1 (local) has inversion and masking; its inversion fades with background change.
- W2 (normalised Hebbian) is nearly boundary-insensitive.

## Caveats

- Oracle labels for segment composition; one fault type (burst); Δ ≤ 256; ramp and level only.
- The adaptation effect of a ≤62-step segment is small in absolute terms (FPR reduction ≤ 0.10).
- The "inversion" reading relies on the B-vs-D decomposition of baseline and A2 scores (`base64_B`, `base64_D` in
  `step1b_summary.csv`). It has not been tested for faults whose shape differs from A1.
- Implication for P7, not tested here: an admission rule that cuts a segment at the fault's end, or a rollback that
  removes only the fault-value steps, could leave the memory in the inverted regime. The recovery steps are not just
  "more contamination".

## Files

- `fig_boundary_sweeps.png` — (a, c) adaptation and (b, d) masking for both sweeps.
- `fig_boundary_tradeoff_crosscheck.png` — (a) trade-off plane, (b) φ × family cross-check.
- `step1b_summary.csv`, `step1b_units.csv`, `step1b_raw.csv.gz`, `run_config.json`.
