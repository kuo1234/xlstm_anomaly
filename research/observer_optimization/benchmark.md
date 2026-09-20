# Benchmark results

All numbers below are metric-free engineering measurements. The model has
fresh random weights; no scientific checkpoint or label is involved.

## Microbenchmark protocol

* xLSTMAD improved official implementation, two sLSTM blocks in encoder and
  decoder, embedding 40, `D=8`, `W=64`, float32.
* CUDA overlay: native `compute_121, code=sm_121`, CUDA 13.0, and
  `--static-global-template-stub=false`.
* Each batch was warmed up four times and timed for 12 CUDA-event repetitions.
* V0 is `phase_e2_observer.extract`; optimized is
  `phase_e2_fast_observer.extract_fast`.
* The optimized observer uses the exact same score output and common18
  reduction; it only changes how the internal traces are obtained.

The raw benchmark JSON is intentionally excluded from the consolidated branch;
the measurements below are the preserved summary.

| Batch | V0 decisions/s | Optimized decisions/s | Speedup | V0 peak memory | Optimized peak memory |
|---:|---:|---:|---:|---:|---:|
| 128 | 2,958 | 13,856 | 4.68x | 188 MB | 188 MB |
| 256 | 5,145 | 17,198 | 3.34x | 348 MB | 348 MB |
| 512 | 7,655 | 17,146 | 2.24x | 653 MB | 653 MB |

At B=128 the optimized observer reaches 84% of the separately measured
score-only throughput (16,479 decisions/s). At B=256/512 it is close to the
score-only plateau, while V0 remains dominated by replay launch overhead.

An external `nvidia-smi` sampler at 100 ms during the B=128/B=256/B=512 run
reported 30 nonzero samples with GPU utilization 12--76% (mean 51.3% over
nonzero samples). This is consistent with the profiler's launch-bound result;
it is not evidence of saturation. Spark reports memory as `[N/A]` through this
query, so peak allocator memory above comes from `torch.cuda`.

## End-to-end bounded extraction

`bounded_pipeline.py` uses only observations from fixed source/scenario pairs
`(3000, abrupt, mixture)` and `(3001, correlation, mixture)`. It does not read
labels or evaluator metadata. It creates 1,024 causal W64 windows per stream,
processes 2,048 decisions in 16 B=128 chunks, copies score/common18 to CPU,
and writes one `.npy` cache file per chunk.

| Pipeline | Wall seconds | Decisions/s |
|---|---:|---:|
| V0 current observer | 0.7021 | 2,917 |
| optimized state capture | 0.1488 | 13,767 |

End-to-end speedup is 4.72x, including window batches, device transfer, and
cache-style writes. Packed score+common18 arrays are allclose under the frozen
`atol=1e-5, rtol=1e-4` contract (`max_abs=3.58e-7`, zero failures).

## GPU-only score baseline

The initial bounded profile measured score-only model forward at 0.00777 s per
B=128 batch (16,479 decisions/s). The observer therefore remains about 16%
of score-only throughput with V0, but the selected observer raises this to
about 84% without changing the model or features.
