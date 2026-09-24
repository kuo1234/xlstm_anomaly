# internal234 cross-model comparability audit (R0, mandatory)

Question (brief §9): does every one of the 18 base internal features — and hence every one of the 234 expanded
columns — have the same semantic meaning across independently trained, machine-specific detector instances? The
answer decides the probe design (A: machine-held-out; B: within-machine blocked). This audit was completed, and the
design frozen, before any R0 detector was trained. Empirical checks use random-initialisation D=38 models only
(no labels, no test observations); numbers are in [`preflight.json`](preflight.json) → `model.semantic_audit`.

## 1. What the implementation actually computes

Sources read: `scripts/phase_e2_schema.py` (`summarize`, `BASE_COLUMNS`, `SCALAR_CELLS`),
`scripts/phase_e2_fast_observer.py` (`summarize_fast`, `state_and_gate_traces`), `scripts/phase_e2_observer.py`
(`scalar_reference`), `scripts/phase_f_lstm_observer.py` (`replay`, `summarize`), `scripts/phase_g1_core.py`
(`expand_internal234`).

At the right-edge timestep `T−1` of each W64 window, for each recurrent layer and each trace
`hidden`, `input` gate, `retention` (forget) gate, `memory`:

| # | column | reduction over units (within head for xLSTM) |
|---|---|---|
| 0–3 | hidden_mean, hidden_std, hidden_rms, hidden_delta_rms | mean, population std, RMS, RMS of `h_T−1 − h_T−2` |
| 4–8 | input_mean, input_std, input_q10, input_q90, input_delta_mean | mean, std, 10/90% quantile, mean change |
| 9–13 | retention_* (same five) | as above |
| 14–17 | memory_mean, memory_std, memory_rms, memory_relative_delta_norm | mean, std, RMS, `‖m_T−1 − m_T−2‖/(‖m_T−2‖+1e-8)` |

Aggregation: xLSTM — per head, then equal mean over the 4 heads, then equal mean over the four sLSTM cells
(`encoder/decoder.blocks.{0,1}.xlstm.slstm_cell`, traces `[B,64,4,10]`); memory = normalised cell state `c/n`.
LSTM — per layer over its 38 units, then equal mean over the 6 layers (`encoder/decoder.{0,1,2}`, traces
`[B,64,38]`); memory = cell state `c`. `internal234` = for each of the 18 columns: the value plus causal
mean/std/slope over 4/8/16/32 successive decision rows (feature-major).

**No raw hidden coordinate, unit index or architecture-specific dimension enters any column.** Both backbones emit
the same 18 names with the same operational definitions, so the external schema is identical (14 + 234).

## 2. Invariance to the reparameterisation symmetries of the networks

| symmetry | LSTM (D=38, w=38) | xLSTM (sLSTM cells) | effect on common18 |
|---|---|---|---|
| hidden-unit permutation within a layer / head, heads permuted | exact network symmetry (verified) | reductions verified invariant to within-head unit and head permutations of the traces; a network-level symmetry is not needed for the verdict | all 18 invariant |
| per-unit sign flip of `(g-gate row, h, c)` | **exact** for every layer not followed by GELU (5 of 6) | not an exact symmetry: the cell output feeds `MultiHeadLayerNorm` (`F.group_norm`, mean-subtracting) in xlstm 2.0.5; the per-unit polarity is a learned convention with no constraint aligning it across instances | hidden_mean, hidden_std, memory_mean, memory_std change; the other 14 invariant |

Why the sign symmetry exists in the LSTM: negating the candidate-gate row of unit *j* negates `c_j` and therefore
`h_j = o_j·tanh(c_j)`; negating column *j* of `W_hh` (all gates) and of the next layer's `W_ih` restores every gate
and every downstream pre-activation exactly. Gates, RMS/norm statistics and delta RMS are unchanged; the mean and
across-unit standard deviation of `h` and `c` are not.

### Empirical verification (GB10, random-init D=38, seed 11, 128 fit-interval windows of machine-1-8)

| test | result |
|---|---|
| full-network LSTM unit permutation (all 6 layers, non-trivial permutations) | output max \|Δ\| 3.0e-8; common18 max \|Δ\| 1.2e-7 → invariant |
| full-network LSTM sign reparameterisation (21/18/25/16/16/0 units flipped per layer) | output and score **bitwise identical**; changed columns exactly {hidden_mean (Δ 0.0163), hidden_std (0.0028), memory_mean (0.0410), memory_std (0.0058)}; the 14 others Δ = 0 |
| xLSTM reduction on real traces: unit + head permutation | invariant (max \|Δ\| 1.2e-7) |
| xLSTM / LSTM reduction on real traces: sign flip of a unit subset in hidden & memory | exactly the same 4 columns change; the 14 others unchanged |

Unit tests (`tests/test_real_data_r0.py::SemanticAudit`) reproduce the reduction and CPU full-network checks.

## 3. Operating-point shift across instances

Even the 14 symmetry-invariant columns are not calibrated across instances: typical gate openness, state RMS and
their rolling statistics are set by each trained detector's weights and each machine's input distribution. A
machine-held-out probe would therefore confound (i) machine shift, (ii) detector-instance shift and (iii) the
polarity non-identifiability above. No label-free alignment step is part of the frozen feature definition, and
adding one would invent a new feature transformation (forbidden by brief §11).

## 4. Verdict

`INTERNAL234_NOT_FULLY_COMPARABLE_ACROSS_INDEPENDENT_DETECTORS`

* 14/18 base features (182/234 columns): permutation- and sign-invariant state/gate summaries with fixed semantics.
* 4/18 base features (52/234 columns: hidden_mean, hidden_std, memory_mean, memory_std with their rolling
  expansions): depend on learned per-unit polarity — an exact non-identifiability in the LSTM, an unconstrained
  learned convention in the xLSTM.
* All 18: instance-specific operating points.

Not every feature has the same semantic meaning across independently trained machine-specific detectors, so the
Design-A precondition fails. **Selected: Design B — within-machine blocked diagnostic**, where each probe is trained,
selected and tested on rows produced by one fixed detector, so polarity and operating point are constant within the
task and `internal234` is used exactly as defined.

Consequences recorded for interpretation: R0 measures within-machine decodability, not unseen-machine or
unseen-detector transfer; features are not dropped, re-signed or re-normalised; xLSTM and LSTM keep the same
schema.
