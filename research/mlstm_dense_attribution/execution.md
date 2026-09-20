# Execution record

* branch: `research/mlstm-dense-attribution`
* base: `b9a1a80e09aa4fe061878d4d66d67bc6ba22f490`
* checkpoint: `data/phase_f_v4/runs/xlstm_11/best.pt`
* implementation: pinned improved xLSTMAD `e8b56ba27352733bb83729e85b1d6196dca70c99`, `xlstm==2.0.5`
* backend: validated CUDA SM121 overlay, float32, inference-only
* cache command: `python scripts/mlstm_dense_attribution.py extract --cache-dir research/mlstm_dense_attribution/cache --batch-size 256`
* analysis commands: `... analyze --mode stride32` followed by `... analyze --mode stride1`
* probe: train-only scaling, L2 lbfgs logistic regression, C `{0.01,0.1,1,10}`, pooled validation AP selection
* no model retraining, no detector seeds 22/33/44/55, no G1/H3b execution

The cache is a local 1.6 GB observation artifact and is ignored by Git; its
manifest and validation report are committed with the result files.
