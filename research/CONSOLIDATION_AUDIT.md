# Research consolidation audit

This consolidation is selective. The source branches remain available in Git
history while `main` receives only maintainable implementation, tests, and
compact evidence summaries.

## Imported

- CUDA Spark diagnosis, compatibility, environment, benchmark, recommendation,
  and small fixture scripts.
- FastObserver implementation, design/correctness/profile summaries, and
  bounded benchmark utilities.
- Integration-canary scripts and compact reports, including the distinction
  between frozen-checkpoint inference parity and non-identical CUDA training
  trajectories.
- Read-only mLSTM observer/probe/canary code, configuration, architecture and
  state-semantics notes, and compact seed-11/three-seed exploratory summaries.
- Dense stride-1 attribution code/tests and compact stride-32/stride-1,
  ablation, and decision summaries.

## Intentionally excluded

- CUDA compiler/profiler logs and raw utilization/throughput dumps.
- Observer profiler/correctness JSON dumps where the Markdown summaries retain
  the relevant measurements.
- mLSTM and dense-attribution prediction `.npz` files.
- The approximately 1.6 GB dense observation cache and its large manifest.
- Checkpoints, Phase-F/G caches, labels, and generated per-stream artifacts.

The excluded artifacts are reproducibility aids or historical evidence, not
source code required for the consolidated tests. They remain on the original
research branches or external artifact storage where applicable.

## Scientific boundary

No G1 report, checkpoint, feature definition, or decision was edited. The
post-G1 mLSTM summaries are explicitly exploratory and are not promoted to the
frozen H3a/H3b claim.
