# Matrix-memory family attribution

The frozen base families were expanded independently with the same causal
rolling transform. No matrix was flattened into probe inputs and no new family
was invented.

The overall dense APs show that most of the mLSTM gain is carried by the
non-C families:

* `H+M_noC = 0.936035`, slightly above `H+M_full = 0.935443`;
* `H+Mn+Mm = 0.925963`, `H+Mh = 0.878984`, and `H+MC = 0.905477`;
* after sLSTM, `H+S+M_noC = 0.943456` and `H+S+M_full = 0.950065`.

The required matrix-specific contrasts are:

* `ΔC_history = AP(H+M_full)-AP(H+M_noC) = -0.000592`;
* `ΔC_given_sLSTM = AP(H+S+M_full)-AP(H+S+M_noC) = +0.006610`.

The second contrast is a small positive conditional increment, but the first
is null/slightly negative and the broad mLSTM increment is already present
without C. Therefore this screen does not support calling the previous result
matrix-memory-specific. The C-only arm is descriptive and is not a causal
mechanism proof.

Scenario C contrasts are included in `stride1_results_strata.json`:

| scenario | C|H | C|H+S |
|---|---:|---:|
| abrupt | -0.005254 | +0.001289 |
| gradual | -0.015217 | +0.005119 |
| recurring | +0.000230 | +0.009939 |
| correlation | +0.010504 | +0.004928 |

The recurring conditional C increment is the largest, but it is still small
and one detector seed is not confirmatory evidence.
