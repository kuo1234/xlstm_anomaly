# Frozen feature schema

The mLSTM base18 is split without modification:

* `Mh` hidden/readout: mean, std, RMS, immediate within-window delta RMS (4);
* `MC` matrix C: mean, std, Frobenius norm, relative update norm, leading
  singular-value ratio, normalized spectral entropy (6);
* `Mn` normalizer n: mean, std, RMS, immediate delta RMS (4);
* `Mm` stabilizer m: mean, std, RMS, immediate delta mean (4).

For every family, the same causal expansion is current value plus mean/std/OLS
slope over widths 4, 8, 16, and 32. Thus dimensions are 13 columns per base
feature. The tested arms have dimensions H=14, H+Mh=66, H+MC=92,
H+Mn+Mm=118, H+M_noC=170, H+M_full=248, H+S=248,
H+S+M_noC=404, and H+S+M_full=482.

Rows are source-disjoint train/validation/test folds (1000..1009,
2000..2004, 3000..3009), four shifted scenarios, and the existing five
conditions. Logistic regression is L2 with C in `{0.01,0.1,1,10}`, selected by
pooled validation AP after train-only scaling. Mixed rows are excluded from
the primary anomaly-vs-drift cohort. No test-informed feature, C, or rolling
choice was made.
