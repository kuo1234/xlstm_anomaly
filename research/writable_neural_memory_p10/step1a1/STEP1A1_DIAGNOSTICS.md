# Step 1a.1 — mechanism diagnostics (P7+P10, issue #15)

Authorized in #15 comment 5955307476. Exploratory: no protocol, seal, bootstrap, W4, six machines or dose-response.

- **Code:** `scripts/p10_step1a1_diag.py` (imports the Step 1a operators unchanged); `tests/test_p10_step1a1.py`
  (3 checks; with the Step 1a tests, 6 pass).
- **Units:** φ1 = Step 1a random-ReLU features (3 machines × seeds 11/22/33 = 9 units). φ2 = PCA-whitened windows
  (deterministic, 3 units).
- **Regression check:** for φ1, the Step 1a arms (B, C, D, B30, D30 and M1a write / no-write) reproduce the Step 1a
  raw rows exactly (max abs diff 0.0 over 43,200 M1b and 4,320 M1a rows).

## A. W2 decay-matched no-write

W2 gets `decay(L)` (apply f^L, add nothing). The M1a arms are write, decay_only and skip; M1b adds `Cdec` (block the
input write, keep the decay).

**Result: decay-only is identical to skip in M1a** (max |decay_only − skip| = 0.0 over all units, families and W2
variants).

- **Why:** both W2 reads are ratios, `C q / max(|n·q|, 1)` and `d_k C q / c`. A uniform decay scales numerator and
  denominator together, so it is a no-op by itself (as long as `n·q` stays above the floor of 1, which it does with
  roughly 10k M0 writes).
- **Consequence:** `write − decay_only = write − skip`, so the Step 1a M1a W2 utility stands as reported. W2 f=0.995
  under φ1: level −0.032 (9/9 units negative), ramp −0.058 (9/9).
- **Interpretation:** forgetting acts only *relative to new writes*. The f=0.995 benefit is "new data plus a relative
  down-weighting of M0", and both are consequences of the write. There is no separable decay-only component.

**M1b:** for W2 f=0.995, burst, identical A2, Δ=64:

| | C−D | Cdec−D |
|---|---|---|
| φ1 W2 | −0.254 | −0.202 |
| φ2 W2 split map | −0.272 | −0.214 |
| φ2 W2 elu map | −0.237 | −0.189 |

- Here decay does matter, because clean gap writes follow it: about 20% of the original C−D gap is the skipped decay.
- The remaining −0.20 is a real effect of *writing* the 38 clean A1-window steps.
- **B−D is unaffected,** since B and D have the same number of write/decay steps.

## B. W1 neighbour provenance (burst, identical A2, B arm)

| Δ | A1 share of top-5 (φ1) | same, gap blocked (φ1) | best A1 similarity (φ1) | 5th-best non-A1 (φ1) | A1 share (φ2) | best A1 sim (φ2) | 5th-best non-A1 (φ2) |
|---|---|---|---|---|---|---|---|
| 64 | 0.83 | 0.86 | 0.94 | 0.85 | 0.89 | 0.87 | 0.56 |
| 256 | 0.62 | 0.65 | 0.86 | 0.85 | 0.84 | 0.83 | 0.57 |
| 1024 | 0.38 | 0.42 | 0.79 | 0.85 | 0.82 | 0.82 | 0.59 |

Masking ratio B/D with the gap written vs blocked (Bng/Dng):

- φ1: 0.30 / 0.61 / 0.82 vs 0.07 / 0.46 / 0.75
- φ2: 0.19 / 0.68 / 0.84 vs −0.14 / 0.27 / 0.77

**The recovery from 0.30 to 0.81 is not displacement by clean gap entries.** With the gap blocked, the A1 share
falls almost the same way (0.86 → 0.42) and the masking ratio recovers to 0.75. The competitor bar (the 5th-best
non-A1 similarity) is flat at about 0.85 under φ1.

What changes is the A1 entries' relevance to the A2 window:

- **Key side:** under φ1, similarity of the A2 query to the best A1 entry drops from 0.94 to 0.79.
- **Value side:** under φ2, A1 entries are still 82% of the top-5 at Δ=1k, yet masking fades. The retrieved A1 values
  carry A1's background, which no longer matches A2's.

**Measured directly:** the per-episode W1 masking ratio rises with the A1→A2 background distance
`mean_j ||z[ta2+j] − z[ta+j]||`:

| | Spearman, all Δ | within Δ=64 / 256 / 1024 | ratio by distance quartile (q1→q4) |
|---|---|---|---|
| φ1 | 0.88 | 0.63 / 0.89 / 0.89 | 0.21 → 0.44 → 0.71 → 0.97 |
| φ2 | 0.86 | 0.60 / 0.90 / 0.89 | — |

Mean background distance grows with Δ (3.6 / 5.5 / 6.8 for Δ = 64 / 256 / 1024). So W1's Δ-dependence is
background non-stationarity of the stream, now measured rather than assumed. It acts through both the keys (φ1) and
the retrieved values (φ2).

## C. Second φ (PCA-whitened, signed, untrained)

**φ2 definition:** 8-step window, PCA fitted on the M0 windows, top 64 components whitened, then L2 normalisation.
It explains 0.973 / 0.980 / 0.996 of window variance on machine-1-6 / 2-7 / 3-7 (`pca_explained` in the raw files). W1 (cosine kNN) and W3 (delta
rule) are unchanged.

W2 read semantics under φ2 (documented variants):

- **W2s (count-normalised signed Hebbian, `M(q) = d_k C q / c`): not a valid normal reference.** Its calibration
  score is 46 for f=0.995 (other operators 3–6). Even with f=1, writing 256 *normal* steps raises FPR from 0.019 to
  0.144. Temporally correlated writes are far from isotropic, so the Hebbian cross-covariance estimate gets large
  crosstalk. Its masking numbers are not interpretable.
- **W2p (positive feature map inside W2, keeping the mLSTM normalizer read).** Two maps: split `[relu(k), relu(−k)]`,
  and elu `elu(√d·k)+1` (the linear-attention map). Calibration score is 5.2–5.7, and it behaves like φ1 W2:
  - benign utility only with decay (f=0.995: level −0.024 / −0.027, ramp −0.060 / −0.065; f=1 ≈ 0);
  - masking at Δ=64 of 0.64 / 0.78 (B/D), fading to 1.00 by Δ=1k.

Masking (1 − B/D) and relative masking of the ×0.6 variant ÷ identical, burst, Δ=64 (unit mean, [min, max]):

| operator | φ1 masking | φ2 masking | φ1 variant/identical | φ2 variant/identical |
|---|---|---|---|---|
| W1 append | 0.70 | 0.81 | 0.56 [0.46, 0.64] | 0.63 [0.59, 0.65] |
| W2 f=0.995 (φ2: split map) | 0.23 | 0.36 | 1.70 [1.68, 1.72] | 1.63 [1.61, 1.65] |
| W2 f=0.995 (φ2: elu map) | — | 0.22 | — | 1.78 [1.74, 1.81] |
| W3 β=0.1 | 0.14 | 0.49 | 1.24 [1.16, 1.32] | 1.29 [1.23, 1.33] |
| W3 β=0.5 (B30) | 0.16 | 0.60 | 1.18 [1.10, 1.25] | 1.15 [1.11, 1.18] |

**The broader-masking result survives the change of φ.**

- **What carries over:** append stays local (0.56 → 0.63); Hebbian and delta writes mask the scaled variant as much as
  or more than the identical copy (1.15–1.78), with nearly identical ratios across φ.
- **What depends on φ:** the masking *magnitude*. The delta rule masks 3–4× more under φ2 (0.49–0.60 vs 0.14–0.16).
  So the size of the contamination effect is a joint property of write operator × representation kernel, while the
  shape of its generalisation (local vs along the fault direction) follows the operator.

Further observations under φ2:

- **Recovery boundary for W3 β=0.5:** full-segment B/D is 0.91 / 1.03 / 1.02 (Δ = 64 / 256 / 1k) vs B30 0.40 / 0.65 /
  0.81. The recovery steps again remove most of the masking. The ratio crosses above 1 only from Δ=256.
- **W1 × variant:** B/D exceeds 1 at Δ≥256 (1.24 / 1.37). Full-amplitude A1 neighbours are still retrieved for the
  ×0.6 variant and over-predict the fault (over-retrieval).
- **W1 benign write on no-drift data:** it raises FPR slightly (+0.031, 0/3 units negative). Not investigated.

## Status against the reviewer's criteria for moving on

1. *Decay-matched W2 still has real write utility:* **yes**. Decay-only is exactly zero for both W2 reads, so the whole
   effect is the write.
2. *W1 provenance explained:* **yes**. A1 entries remain and are not displaced; masking fades with A1→A2 background
   distance (Spearman 0.86–0.88).
3. *Broader distributed-write masking survives a second φ:* **yes** for W3 and for W2 with a positive feature map. The
   signed count-normalised Hebbian read is not a valid memory under φ2.

## Files

- **Figures:** `fig_w1_provenance.png`, `fig_phi2_generalisation.png`.
- **Summaries:** `m1a_decaymatched_summary.csv`, `m1b_diag_summary.csv`, `generalisation_summary.csv`.
- **Units / episodes:** `m1a_decaymatched_units.csv`, `m1b_diag_units.csv`, `generalisation_units.csv`,
  `w1_provenance_units.csv`, `w1_bgdist_episodes.csv`.
- **Raw:** `m1a_diag_raw.csv.gz`, `m1b_diag_raw.csv.gz`, `w1_provenance_raw.csv.gz`, `*_w2p.csv.gz`.
