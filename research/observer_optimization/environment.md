# Execution environment

Captured on the DGX Spark in the isolated observer-optimization worktree.

| Item | Value |
|---|---|
| GPU | NVIDIA GB10 |
| Compute capability | `(12, 1)` |
| Driver | `580.173.02` |
| CUDA toolkit / nvcc | `13.0`, `V13.0.88` |
| OS architecture | Linux `aarch64` |
| Python | `3.12.3` |
| Host compiler | GCC/G++ `13.3.0` |
| PyTorch | `2.13.0+cu130` |
| `torch.version.cuda` | `13.0` |
| cuDNN | `92000` |
| xLSTM | `2.0.5` |
| Lightning | `2.6.1` |
| ninja | `1.13.2` |
| Triton | `3.7.1` |
| CUDA extension target | `compute_121,code=sm_121` |
| CUDA template flag | `--static-global-template-stub=false` |
| float32 matmul precision | `highest` |
| CUDA TF32 | disabled for benchmark |

The minimal CUDA checks used in the parent CUDA investigation passed: CUDA is
available, tensors allocate, matrix multiply runs, and the xLSTM forward /
backward fixture is finite. The observer benchmark itself is inference-only
and runs under `torch.no_grad()`.

`torch.cuda.get_arch_list()` reports `sm_80`, `sm_90`, `sm_100`, `sm_110`, and
`sm_120`; it does not list `sm_121`. The custom extension nevertheless builds
and runs a native `sm_121` target when that target is explicitly passed to the
isolated loader. `TORCH_CUDA_ARCH_LIST` was unset; the old pinned package's
hard-coded `compute_80` flag is bypassed only inside the engineering overlay.
