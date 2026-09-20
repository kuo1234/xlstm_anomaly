# Spark environment

Captured on the DGX Spark in the isolated `research/cuda-spark` worktree.

| Item | Observed value |
|---|---|
| GPU | NVIDIA GB10 |
| Compute capability | `(12, 1)` |
| Driver | `580.173.02` |
| Toolkit / nvcc | CUDA `13.0`, V13.0.88 |
| OS / architecture | Linux aarch64, kernel `6.17.0-1026-nvidia-aarch64` |
| Python | `3.12.3` |
| Host compiler | GCC/G++ `13.3.0` |
| PyTorch | `2.13.0+cu130` |
| `torch.version.cuda` | `13.0` |
| cuDNN | `92000` |
| xlstm | `2.0.5` |
| lightning | `2.6.1` |
| ninja | `1.13.2` |
| triton | `3.7.1` |

`torch.cuda.is_available()` was true. CUDA tensor allocation, matrix
multiplication, and a CUDA forward/backward autograd smoke test all passed.

The baseline shell had no `TORCH_CUDA_ARCH_LIST`, `CUDA_HOME`, `CUDA_PATH`,
`CUDA_VISIBLE_DEVICES`, `MAX_JOBS`, `CXX`, `CC`, or `CUDAFLAGS` set. The
diagnostic process used `MAX_JOBS=1`, an isolated Python-header include path,
and a separate `TORCH_EXTENSIONS_DIR`; it did not change system-wide settings.

`nvcc --list-gpu-arch` and `--list-gpu-code` both include `compute_121` and
`sm_121`. The diagnostic loader passed `-gencode arch=compute_121,code=sm_121`
explicitly. This matters because xLSTM 2.0.5's `cuda_init.py` supplies its own
`-gencode arch=compute_80,code=compute_80`, so setting
`TORCH_CUDA_ARCH_LIST` alone does not override that path.

The default environment reports `torch.backends.cudnn.allow_tf32=True`; the
benchmark scripts explicitly set it to `False`, together with
`torch.backends.cuda.matmul.allow_tf32=False` and matmul precision `highest`,
to keep the numerical comparison conservative. The custom sLSTM CUDA kernels
do not use cuDNN.

`nvidia-smi` reports GB10 memory fields as `[N/A]` on this unified-memory
system. PyTorch peak allocated memory is recorded in the benchmark JSON logs.
An external `nvidia-smi` sampler observed 110 samples with GPU utilization
0–95% (mean 70.9%) across the short vanilla/CUDA benchmark; this is an
aggregate process-level sample, not a scientific workload measurement.
