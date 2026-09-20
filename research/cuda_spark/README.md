# CUDA Spark investigation

This directory contains the isolated engineering investigation of the pinned
xlstm sLSTM CUDA path on DGX Spark/GB10. It is not part of the scientific G1
result and does not modify the main worktree's checkpoints, caches, or reports.

## Re-run fixtures

Use the existing project venv and the extracted Python headers. All extension
builds should use a fresh temporary `TORCH_EXTENSIONS_DIR`:

```bash
XLSTM_PY_HEADERS_ROOT=/home/p76141495/home/xlstm_anomaly/data/phase_e/python_headers/usr/include \
XLSTM_EXTRA_INCLUDE_PATHS=/home/p76141495/home/xlstm_anomaly/data/phase_e/python_headers/usr/include/python3.12:/home/p76141495/home/xlstm_anomaly/data/phase_e/python_headers/usr/include \
TORCH_EXTENSIONS_DIR=/tmp/xlstm_cuda_diag_native121_false MAX_JOBS=1 \
/home/p76141495/home/xlstm_anomaly/data/phase_e2/venv/bin/python \
research/cuda_spark/slstm_cuda_fixture.py \
  --arch 121 --code sm_121 --static-stub false \
  --extension-dir /tmp/xlstm_cuda_diag_native121_false
```

The full-model correctness and benchmark runner is
`xlstmad_cuda_bench.py`; it only creates random D=8/W=64 models. Raw compiler
and profiler logs are intentionally kept out of the consolidated branch; the
versioned summaries below record the relevant commands and outcomes.

## Read first

- [diagnosis.md](diagnosis.md): root cause and pass/fail matrix
- [environment.md](environment.md): Spark software/hardware inventory
- [compatibility_findings.md](compatibility_findings.md): source/upstream review
- [benchmark_results.md](benchmark_results.md): correctness and throughput
- [recommendation.md](recommendation.md): GO/NO-GO and bounded next step
