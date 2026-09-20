# Interpretation

Classification: **DENSE_MLSTM_SIGNAL_NOT_MATRIX_SPECIFIC**.

The prior stride-32 result is reproducible from one dense observation cache.
Under the true stride-1 protocol, mLSTM summaries retain a large increment over
score/history (`+0.145661`) and a smaller but positive increment after sLSTM
(`+0.016657`). This rules out the claim that the earlier result was solely an
artifact of sparse decision sampling.

The family ablation does not isolate matrix memory C as the source: removing C
does not reduce H-only performance (`+0.000592` in favor of M_noC), while the
conditional C increment after sLSTM is only `+0.006610`. Hidden/normalizer/
stabilizer summaries therefore account for most of the observed mLSTM-layer
information under this screen. The small positive C|H+S result is worth noting,
not upgrading into a causal claim.

Scenario effects are heterogeneous: recurring and gradual have the strongest
conditional mLSTM increments, while abrupt and correlation remain positive but
small. The stride-1 conditional result did not change sign or collapse to a
near-zero value, so the preregistered temporal-span diagnostic (97/225/481/993
rolling widths) was not run.

This is one seed and exploratory. It does not reopen H3b, establish a global
xLSTM advantage, establish safe adaptation, or test persistent cross-window
memory.
