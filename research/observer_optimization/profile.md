# Observer bottleneck profile

## Scope

This is an engineering-only investigation in the separate
`research/observer-optimization` worktree, based on the working CUDA overlay
from `research/cuda-spark` (`dd5ad9d1d1580be2e39313bc6cb7befa0f9cdf61`).
All measurements use fresh random xLSTMAD weights and random `D=8, W=64`
observations. No Phase-F/G checkpoint, label, probe, AP, or scientific result
was read or changed.

Environment: NVIDIA GB10 (CC 12.1), CUDA 13.0, PyTorch 2.13.0+cu130,
`xlstm==2.0.5`, float32, native `sm_121`, and the already validated
`--static-global-template-stub=false` loader overlay.

The reproducible command was:

```bash
XLSTM_PROJECT_ROOT=/home/p76141495/home/xlstm_anomaly \
XLSTM_PY_HEADERS_ROOT=/home/p76141495/home/xlstm_anomaly/data/phase_e/python_headers/usr/include \
XLSTM_EXTRA_INCLUDE_PATHS=/home/p76141495/home/xlstm_anomaly/data/phase_e/python_headers/usr/include/python3.12:/home/p76141495/home/xlstm_anomaly/data/phase_e/python_headers/usr/include \
TORCH_EXTENSIONS_DIR=/tmp/xlstm_cuda_full121_false MAX_JOBS=1 \
/home/p76141495/home/xlstm_anomaly/data/phase_e2/venv/bin/python \
research/observer_optimization/profile_observer.py \
  --extension-dir /tmp/xlstm_cuda_full121_false \
  --profiler-out research/observer_optimization/logs/profile.json
```

## Timing decomposition, B=128

CUDA-event timing used 12 repetitions after five warmups:

| Region | Mean seconds/batch | Decisions/s |
|---|---:|---:|
| score-only model forward | 0.00777 | 16,479 |
| current observer end-to-end | 0.04321 | 2,962 |
| current scalar replay after captured model input | 0.03466 | 3,693 |
| current common18 summary only | 0.00209 | 61,305 |

The summary reduction is not the dominant cost. Capturing the model input and
then timing replay separately shows that the replay itself accounts for about
80% of V0 wall time (`0.03466 / 0.04321`). The remaining time includes the
native forward, hooks, parity checks, and reductions.

## Profiler evidence

The bounded `torch.profiler` run covered two V0 and two score-only iterations.
The raw profiler tables are retained only on the historical research branch;
the most diagnostic counters are summarized here:

| Counter over two observer iterations | V0 | score-only |
|---|---:|---:|
| `cudaLaunchKernel` calls | 16,236 | 1,426 (approximately) |
| `cudaStreamSynchronize` calls | 616 | not material |
| `aten::all` calls | 600 | not material |
| `cudaLaunchKernel` self CPU time | 41.494 ms | 3.856 ms |

The V0 replay launches many tiny `einsum`, pointwise, `exp`, `minimum`, and
stack operations for each timestep of each of the four cells. The per-step
`bool(torch.all(n == 0))` and the observer's `allclose`, `max`, and
`isfinite().all()` checks add host/device synchronization. This establishes a
mixed bottleneck: duplicate recurrent compute expressed as Python-level
dispatch and kernel-launch overhead, with synchronization as a secondary
cost. It is not primarily limited by model FLOPs or the final quantile
summary.

The optimized profile reduces the two-
iteration counters to 2,308 `cudaLaunchKernel` calls and no `aten::all` calls
from the hot observer path. The remaining `cudaDeviceSynchronize` events are
the profiler/timing boundaries, not per-timestep parity checks.

## What the profile rules out

* Moving the existing Python replay after the model forward would improve
  separation of concerns but would not remove its 64-step recurrence or its
  launch count; it is not sufficient by itself.
* Quantile/statistics work is measurable but small relative to replay.
* Adding CUDA processes or streams is not justified by this profile; the
  dominant work is on one dependent stream and the optimized path already
  approaches score-only throughput at larger batches.
