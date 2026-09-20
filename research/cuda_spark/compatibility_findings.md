# Compatibility findings

## Pinned xLSTM 2.0.5 build

The installed `xlstm/blocks/slstm/src/cuda_init.py` hard-codes:

```text
-gencode arch=compute_80,code=compute_80
```

It also passes `--use_fast_math`, `-O3`, and related optimization flags. The
custom loader does not consult `TORCH_CUDA_ARCH_LIST` for this explicit flag.
The package asks for extra include paths through `XLSTM_EXTRA_INCLUDE_PATHS`;
the first isolated attempt failed only because the host Python headers were not
on the include path. Supplying the existing extracted headers resolved that
environment-only error and exposed the linker failure.

The source layout is:

- `slstm_pointwise.cuh`: declaration of templated `__global__`
  `SLSTMPointwiseForward`;
- `slstm_forward.cu`: calls both `SLSTMPointwiseForward<true>` and
  `<false>`;
- `slstm_pointwise.cu`: definitions and explicit instantiations.

CUDA 13's default whole-program `--static-global-template-stub=true` warns
that a `__global__` template specialization must be defined in the current
translation unit. The warning is followed by the exact undefined references
seen in the historical report. Passing
`--static-global-template-stub=false` makes the link succeed without changing
the kernel source or equations. This controlled default-vs-false experiment is
the evidence for the root cause, rather than a conjecture from the warning.

## GB10 native target

CUDA 13 on this machine accepts `compute_121`/`sm_121`. The native target plus
`--static-global-template-stub=false` compiles all seven translation units and
executes forward/backward on GB10. The default-stub native build fails at the
same linker references, so the issue is independent of whether the old
compute_80 target is used.

The current package's compute_80 flag is consequently both non-native and
insufficiently portable. The engineering overlay uses `compute_121,sm_121`.
It is intentionally not installed into the scientific environment.

## Alternative `-rdc=true`

Adding `-rdc=true` lets nvcc compile the objects, but importing the resulting
extension fails with an unresolved `__cudaRegisterLinkedBinary_*` symbol. A
proper relocatable-device-code solution would need nvcc device linking (or an
equivalent `CUDAExtension` build), not just an extra compile flag. The safer
minimal compatibility path for this source is the explicit
`--static-global-template-stub=false` flag.

## Upstream review

The current official README documents sLSTM CUDA for compute capability >=8.0,
suggests `TORCH_CUDA_ARCH_LIST="8.0;8.6;9.0"`, and recommends matching CUDA /
PyTorch versions. It does not document GB10, SM121, CUDA 13, or aarch64. See
<https://github.com/NX-AI/xlstm/blob/main/README.md>.

Release `v2.0.6` (commit `a5f07ea`) includes packaging changes and a prototype
binary sLSTM distribution, but the release/PR materials do not establish a
tested aarch64 + CUDA 13 + SM121 matrix or this template-stub fix. See
<https://github.com/NX-AI/xlstm/releases/tag/v2.0.6> and
<https://github.com/NX-AI/xlstm/pull/118>. The current upstream CUDA source
still has the same declaration/reference/definition split:

- <https://raw.githubusercontent.com/NX-AI/xlstm/main/xlstm/blocks/slstm/src/cuda/slstm_pointwise.cuh>
- <https://raw.githubusercontent.com/NX-AI/xlstm/main/xlstm/blocks/slstm/src/cuda/slstm_forward.cu>
- <https://raw.githubusercontent.com/NX-AI/xlstm/main/xlstm/blocks/slstm/src/cuda/slstm_pointwise.cu>

Therefore an upgrade is not evidence of a Spark fix. Test it as a separate
compatibility project if desired; do not alter the pinned scientific install.

FlashRNN is presented upstream as an optional faster sLSTM kernel, but its
README does not establish this GB10/CUDA13/aarch64 configuration. It should be
benchmarked independently rather than substituted in this study:
<https://github.com/NX-AI/flashrnn>.

The CUDA 13 compiler behavior is documented by NVIDIA in the `nvcc` compiler
driver guide: <https://docs.nvidia.com/cuda/archive/13.0.2/pdf/CUDA_Compiler_Driver_NVCC.pdf>.
