# Upstream / backend compatibility review

## Pinned 2.0.5 versus upstream 2.0.6

The official `NX-AI/xlstm` tag `v2.0.6` (commit
`c302766da72e96cdf924b7c3743500b9da39521e`) adds an automatic
`--static-global-template-stub=false` nvcc flag for CUDA versions `>=12.8`.
That is the same compatibility flag used by the already validated Spark
overlay and directly addresses the CUDA 13 cross-translation-unit template
stub/linker failure. It also improves extension cache-key handling. The
installed scientific environment remains pinned to 2.0.5; no upgrade was
performed here.

The upstream README's generic CUDA guidance still documents compute capability
`>=8.0` and example architectures `8.0;8.6;9.0`; it does not document a GB10
/ CC12.1 validation path. PyTorch 2.13 on this Spark reports up to `sm_120`
in its built-in arch list, so the explicit `sm_121` extension target remains
an overlay-specific engineering choice, not an upstream-supported scientific
configuration.

## FlashRNN

The official `NX-AI/flashrnn` v1.0.8 source offers CUDA, fused CUDA, Triton,
and vanilla sLSTM backends and advertises possible 2--5x kernel speedups in
appropriate configurations. It likewise documents CC8.0+ and example
architectures through 9.0, but provides no GB10/CC12.1 or aarch64 validation
in the reviewed material. `flashrnn` is not installed in the Phase-E2
environment and was not substituted into xLSTMAD. A FlashRNN port would alter
the backend and require a separate forward/backward/state-layout correctness
study, so it is not a justified prerequisite for this observer optimization.

## CUDA template-linkage conclusion

The parent CUDA investigation independently reproduced the old undefined
`SLSTMPointwiseForward<false/true>` references with the pinned default
`compute_80` build and CUDA 13's default static template stubs. Supplying
`--static-global-template-stub=false` removes that linker failure. Compiling
the same source for native `sm_121` also works. Thus the historical CUDA issue
was a real build/linkage plus architecture-target problem; it is separate from
the observer bottleneck addressed here.

References reviewed:

* https://github.com/NX-AI/xlstm
* https://github.com/NX-AI/xlstm/releases/tag/v2.0.6
* https://github.com/NX-AI/flashrnn
