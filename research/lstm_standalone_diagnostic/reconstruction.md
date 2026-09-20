# Standalone LSTM diagnostic reconstruction

This is a post-hoc exploratory diagnostic, not a new H2 test and not a new
member of the frozen four-comparison Holm family. It uses only the committed
and independently audited G1 summary:

`reports/phase_g1/g1_self_review_postrun_recovered_v2_pass.json`

No checkpoint, label, cache, feature extractor, or probe-fitting path is
opened.

The audit's primary arrays are `[test source, detector seed] = [10, 5]`:

```text
Delta_X  = h2
H3a-B    = (Delta_X) - (Delta_L_own)
```

Thus the standalone matched-LSTM increment is reconstructed elementwise as:

```text
Delta_L_own = h2 - h3a_b
```

The script computes this subtraction from the loaded arrays; it does not use
the expected aggregate as a constant. The exact maximum elementwise identity
error is zero in the saved result.

The original source and detector axes are preserved: sources `3000..3009` and
detector seeds `(11, 22, 33, 44, 55)`. Uncertainty reuses the existing source-
first/detector-second bootstrap implementation with 10,000 draws and seed
901, plus the existing source-cluster sign-flip implementation with seed 902.
All new uncertainty is labelled **POST-HOC / EXPLORATORY**.
