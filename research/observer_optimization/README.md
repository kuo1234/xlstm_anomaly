# xLSTM observer optimization

Engineering-only benchmark of the DGX Spark/GB10 CUDA internal-feature
observer. It is based on the isolated CUDA overlay in
`research/cuda-spark`; it does not rerun G1 or modify Phase-F/G artifacts.

The selected implementation is in
[`scripts/phase_e2_fast_observer.py`](../../scripts/phase_e2_fast_observer.py):
it captures the native sLSTM state history already emitted by the CUDA cell,
reconstructs the four gate traces in batched operations, and applies the same
common18 semantics without hot-path parity synchronization.

Start with [`profile.md`](profile.md), then read [`design.md`](design.md),
[`correctness.md`](correctness.md), and [`benchmark.md`](benchmark.md).
`recommendation.md` records the engineering disposition and remaining risks.
