# Dense cache artifact

The observation-only dense cache is intentionally not part of the consolidated
Git history. It is a large local artifact (about 1.6 GB) containing no labels
or event metadata. The committed extraction script and
`dense_cache_design.md` describe how to regenerate it from the frozen seed-11
checkpoint; the compact JSON/Markdown summaries in this directory preserve the
reported analyses.

Prediction arrays and the large cache manifest are also excluded from `main`.
They remain available on the historical research branch or external artifact
storage when byte-level replay is required.
