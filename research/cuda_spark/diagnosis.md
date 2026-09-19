# Spark/GB10 xLSTM sLSTM CUDA diagnosis

This is an engineering-only investigation on a separate `research/cuda-spark`
worktree. It uses random inputs and fresh random weights. It does not load,
modify, or regenerate any Phase-F/G checkpoint, cache, label, or scientific
result.

## Scope and disposition

The pinned environment is `xlstm==2.0.5`, CUDA 13.0, PyTorch 2.13.0+cu130,
Python 3.12.3 on an aarch64 DGX Spark with an NVIDIA GB10 (CC 12.1).

The old CUDA path is reproducibly broken with the package's default build:

1. the package hard-codes `-gencode arch=compute_80,code=compute_80`;
2. CUDA 13 emits warning #20280-D for the cross-translation-unit
   `SLSTMPointwiseForward<true/false>` templates; and
3. the host link fails with undefined references to both specializations.

With an isolated loader overlay (the installed package is not edited), explicit
`sm_121` compilation plus
`--static-global-template-stub=false` builds and runs the same source. A full
improved xLSTMAD D=8/W=64/embedding=40 model then completes finite forward and
backward passes.

## Reproduction matrix

| Fixture | Architecture | Static template stub | Result |
|---|---:|---:|---|
| historical source, default flags | compute_80 / compute_80 | CUDA 13 default (`true`) | linker failure |
| same source, controlled flag | compute_80 / compute_80 | `false` | forward/backward PASS |
| native GB10 | compute_121 / sm_121 | `false` | forward/backward PASS |
| native GB10 | compute_121 / sm_121 | CUDA 13 default (`true`) | same linker failure |
| native GB10 | compute_121 / sm_121 | `-rdc=true` only | import failure (`__cudaRegisterLinkedBinary...`) |

The `-rdc=true` result is not a valid drop-in workaround because the current
PyTorch extension link command uses the host linker without the CUDA device-link
step. It would require a separate build-system change.

## Correctness evidence

The full improved official xLSTMAD model (random weights, B=8, W=64, D=8) has
finite output and gradients on `sm_121` CUDA. A vanilla/CUDA comparison with
the same mathematical weights required the documented recurrent-layout adapter
(vanilla and CUDA store the recurrent matrix differently). Results:

- output max absolute difference: `5.3644180e-7`;
- reconstruction losses: both `1.1567840576` (absolute difference 0);
- input-gradient max absolute difference: `2.6775524e-9`;
- maximum parameter-gradient difference: `5.2154064e-8`;
- repeated CUDA output: bitwise identical;
- all outputs and gradients finite.

The direct sLSTM cell and the complete model both pass this comparison. A
100-step B=128 reconstruction run decreases loss from `0.8785525` to
`0.0403346` on both backends.

## Conclusion

The historical failure is established as a CUDA 13 whole-program template-stub
linkage incompatibility in the pinned xLSTM sLSTM build, with hard-coded
compute_80 as a separate portability/optimization defect. It is not an ARM64
CUDA availability failure and not a GB10 execution failure after the isolated
build correction.

CUDA is therefore benchmarkable and potentially usable through a narrowly
scoped build overlay. The scientific environment remains unchanged; no
existing result is reinterpreted.
