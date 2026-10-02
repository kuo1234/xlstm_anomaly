# Step 1a — role-matched oracle memory pilot (P7+P10, issue #15)

Authorized in #15 comment 5954497867. Exploratory: no protocol, no seal, no STOP gate, no bootstrap.
Code: `scripts/p10_step1a_oracle.py` (operators, M1a, M1b), `tests/test_p10_step1a.py` (3 unit checks).
Data: SMD train split only, machine-3-7 / machine-1-6 / machine-2-7; φ seeds 11 / 22 / 33 → 9 units
(machine × seed). CPU, about 2 min in total.

## Design (as run)

**Role matching.** Every operator gets the same key, value, stream, oracle segment and score:

- key: `k_t = φ(z[t-8:t])`, the 8 steps ending at t−1;
- value: `v_t = z_t`;
- score: `s_t = ||v_t − M(k_t)||₂`.

`φ` is a fixed random ReLU feature map: `k = normalize(relu(R·vec(window)/√(wC) + b))` with R and b Gaussian and
d_k = 128. Only R and b depend on the φ seed. I used ReLU features instead of a plain random projection for one
reason. With non-negative keys, every inner product `k_i·q` is ≥ 0, so the Hebbian read `C q / max(|n·q|, 1)` is a
proper kernel-weighted average. With signed projections, `n·q` crosses zero and the normalizer becomes degenerate.
The same keys are also unit-norm, which keeps the delta rule stable.

| operator | write | read |
|---|---|---|
| W1 append | append (k, v) | mean v of top-5 cosine neighbours |
| W2 f=1 | C ← fC + v kᵀ, n ← fn + k | C q / max(|n·q|, 1) |
| W2 f=0.995 | same, f = 0.995 per write | same |
| W3 β=0.1 / β=0.5 | C ← C + β(v − Ck)kᵀ | C q |

**Initial memory.** Every memory starts as M0, a sequential write of the fit-train region (9.5k–11.5k steps).
Outside the oracle segments, writes are deterministic and identical across arms. Within an admitted segment, W2/W3
apply their per-step increments in order; the segment is not compressed to a prototype.

**M1a (benign-write utility).** Uses the G-L1 plan: 24 onsets per family (level / ramp / gain / none), with 2σ drift
on 8 channels, 512-step ramp, ×1.5 gain.

- Threshold: q0.99 of M0 scores on [t0−1024, t0).
- Write arm: write the drifted segment [t0, t0+256); no-write arm: skip it.
- Then freeze the memory, skip a 16-step unwritten guard, and score the same path on [t0+272, t0+784).
- No-memory context baselines (no write): last-value `||z_t − z_{t−1}||`, and RevIN-kNN (window-mean-centred keys and
  values, train bank).

**M1b (contamination).** Clean stream, 16 positions per fault type.

- A1 is a 30-step fault at ta. The admission segment is [ta, ta+38): every step whose key or value touches the fault.
- Arms at the segment: B writes it from the faulty stream; D writes the same steps from the clean stream; C writes
  nothing.
- All arms then write the clean stream up to ta2−16 (identical), keep a 16-step guard, and score A2 at ta2 = ta+30+Δ
  on frozen memory.
- Endpoint: paired `lift = mean_30 [s(stream + A2) − s(stream)]`.
- Faults reuse the G-L1 injection semantics:
  - spike: sentinel spike, 5 channels, 2u; its variant keeps the channels and redraws the signs;
  - burst: level 2σ on 8 channels for 30 steps; its variant is the same pattern at ×0.6.
- Diagnostic arm B30/D30: write only [ta, ta+30), dropping the 8 trailing recovery steps whose keys contain the fault
  but whose values are clean.

Calibration-region mean score (no drift), as a measure of predictor quality: W1 3.19, W3 β=0.1 4.57, W2 f=1 4.92,
W2 f=0.995 5.37, W3 β=0.5 8.17; last-value 2.11, RevIN-kNN 1.63.

## Answers to the three questions

### 1. Benign write: yes for W1, W3 and decayed W2; no for undecayed W2

Mean ΔFPR (write − no write) over 9 units; brackets are unit min/max:

| family | W1 | W2 f=1 | W2 f=0.995 | W3 β=0.1 | W3 β=0.5 |
|---|---|---|---|---|---|
| level | −0.118 [−0.28, −0.03] | −0.008 | −0.032 | −0.087 | −0.089 |
| ramp | −0.104 | −0.008 | −0.058 | −0.091 | −0.113 |
| gain | −0.002 | −0.003 | −0.009 | −0.004 | +0.009 |
| none | −0.003 | −0.001 | +0.011 | −0.010 | −0.017 |

- **Level/ramp:** every unit is negative for every operator. In mean log score the delta rule moves most:
  W3 β=0.1 −0.67 (level), W1 −0.52, W2 f=0.995 −0.45, W2 f=1 −0.02.
- **Undecayed Hebbian:** its 256 writes are diluted into roughly 10k prior writes, so it barely adapts.
- **Gain:** ×1.5 is hardly visible to any memory (no-write FPR 0.04–0.07), so there is nothing to absorb.
- **Context check:** last-value and RevIN-kNN have post-onset FPR 0.012–0.016 for *all* families, the same as the
  no-drift control. These drifts are invisible to normalization-based scores. M1a therefore shows that the writes
  work; it does not show that a memory write is needed to handle this drift.

### 2. Anomaly write: yes, causal masking, strongly operator- and fault-dependent

Burst A1 with identical A2 gives the lift ratio B/D (1 = no masking). Counts are units with B−D < 0:

| Δ | W1 | W2 f=1 | W2 f=0.995 | W3 β=0.1 | W3 β=0.5 (B) | W3 β=0.5 (B30) |
|---|---|---|---|---|---|---|
| 64 | 0.30 (9/9) | 0.99 | 0.77 (9/9) | 0.86 (9/9) | 1.09 (0/9) | 0.84 |
| 256 | 0.61 | 0.99 | 0.94 | 0.90 | 1.10 | 0.88 |
| 1024 | 0.81 | 0.99 | 1.00 | 0.91 | 1.06 | 0.91 |

- **Machine consistency:** the per-machine values at Δ=64 agree; for example, W1 is 0.29 / 0.23 / 0.39.
- **Spike (2u, random signs):** masking is weak: W1 0.84 at Δ=64, W3 β=0.5 0.93, all others ≥ 0.98. A spike with
  fresh signs is masked by nothing (≥ 0.97).
- **C−D** is ≈ 0 except for W2 f=0.995 (−0.25 at Δ=64, burst). That is a decay artefact: skipping 38 writes means
  less forgetting of M0.
- **Sensitization in W3 β=0.5.** With the full admission segment, forced write *raises* A2 lift (ratio > 1). Removing
  the 8 recovery steps (B30) turns this into ordinary masking (0.84). A high-β delta rule is dominated by its last
  writes, which here map "fault-in-context" keys to clean values. The memory learns the recovery transition, not the
  fault. **For P7 this means the admission-segment boundary changes the sign of the contamination effect.**

### 3. Distributed writes show different similarity behaviour, but only along a scaled direction

Burst at Δ=64:

| | W1 | W2 f=0.995 | W3 β=0.1 | W3 β=0.5 (B30) |
|---|---|---|---|---|
| B−D, identical A2 | −2.73 | −0.76 | −0.60 | — |
| B−D, ×0.6 variant | −0.76 | −0.58 | −0.38 | — |
| relative masking, variant ÷ identical | 0.56 | 1.70 | 1.24 | 1.18 |

- **Append is local.** The ×0.6 variant keeps 28% of W1's absolute masking and about half of its relative masking.
- **Hebbian and delta writes generalize.** They mask the scaled variant as much as or more than the identical copy, in
  relative terms. This is consistent with a linear read: the stored fault shifts predictions along the fault
  direction, whatever the amplitude.
- **Where it stops.** It does not reach a fresh-sign spike: no operator masks that.
- **Time profiles differ too.** W2 f=0.995 decays to 1.00 by Δ=1k (forgetting). W3 β=0.1 stays flat at about 0.9
  (persistent). W1 decays from 0.30 to 0.81 even though append never forgets. My hypothesis is background
  non-stationarity: A1 neighbours become less similar to later A2 queries. This is **not verified**; checking it needs
  a neighbour-provenance count.

## Caveats and failure modes

- One φ family (random ReLU features, d_k=128, w=8). The breadth of the Hebbian kernel is a property of this φ.
- Predictor quality differs a lot (W3 β=0.5 has the worst calibration score). Thresholds are per operator, so FPR is
  comparable but absolute scores are not.
- No-write FPR under drift is modest (0.08–0.20), and normalization alone removes it.
- Masking is large only for the burst fault (lift ≈ 4). Spike lift is ≈ 1.3, and its masking is small for every
  operator.
- 3 machines × 3 φ seeds; per-unit spread is shown in the figures. There is no inferential statistics.

## Figures and tables

- `fig_m1a_benign_write.png`: (a) post-onset FPR without write, (b) ΔFPR from the benign write, per family.
- `fig_m1b_masking.png`: B/D lift ratio vs Δ for burst/spike × identical/variant A2; dashed line = W3 β=0.5 B30/D30.
- `fig_tradeoff_generalisation.png`: (a) benign-write utility vs masking, (b) variant-vs-identical relative masking.
- `m1a_summary.csv`, `m1b_summary.csv`, `m1a_units.csv`, `m1b_units.csv`, raw `m1a_raw.csv.gz`, `m1b_raw.csv.gz`,
  `run_config.json`.
