# Frozen compact mLSTM feature schema

The schema was frozen in `configs/mlstm_mechanism_audit.json` before the
seed-11 labeled screen.  It uses only the final within-window state and the
immediately preceding state, with equal pooling across heads and then equal
pooling across the encoder and decoder mLSTM cells.

Base dimension: 18

1. Raw hidden/readout: mean, standard deviation, RMS, delta-RMS (4).
2. Matrix memory `C`: mean, standard deviation, Frobenius norm, relative
   update norm, leading-singular-value ratio, normalized spectral entropy (6).
3. Normalizer `n`: mean, standard deviation, RMS, delta-RMS (4).
4. Stabilizer `m`: mean, standard deviation, RMS, delta-mean (4).

The rolling expansion is the same causal feature-major mean/std/OLS-slope
expansion used by the existing internal track at widths 4, 8, 16, and 32.
It produces 234 columns (`18 * (1 + 4*3)`).  The exploratory arms are:

* `H`: score/history control, 14 columns;
* `H+S`: score/history plus existing sLSTM common internal features, 248;
* `H+M`: score/history plus mLSTM 234, 248;
* `H+S+M`: score/history plus both internal summaries, 482.

The matrix statistics deliberately remain compact and interpretable.  They
retain scale sensitivity through the Frobenius and relative-update terms but
avoid unstable inverses or a flattened 4x20x20 representation.
