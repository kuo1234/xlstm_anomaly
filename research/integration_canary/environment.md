# Environment and provenance

* worktree/branch: `research/integration-canary`
* base observer commit: `4c04b6a602838b0348eee644e5bbcbaff40997b6`
* CUDA overlay commit: `dd5ad9d1d1580be2e39313bc6cb7befa0f9cdf61`
* device: NVIDIA GB10, compute capability 12.1
* torch: `2.13.0+cu130`; CUDA runtime/toolkit: 13.0
* xLSTM package: 2.0.5; improved official xLSTMAD commit: `e8b56ba27352733bb83729e85b1d6196dca70c99`
* backend: CUDA sLSTM, native `sm_121`, `--static-global-template-stub=false`, float32
* `cudnn.deterministic=True`, `cudnn.benchmark=False`, cuDNN TF32=False,
  CUDA matmul TF32=False, float32 matmul precision `highest`, deterministic
  algorithms=False
* Phase-F checkpoint SHA256:
  `4729a3ba385b285078aa987fce176e61fd382715c5357fc92f2635a929a0ae41`
* sealed epoch-order SHA256:
  `83620f8707e9f8c9f563eb017b1b93063eafa566d5d010bff7f334dcef8d54a6`

The ignored `data/phase_e2` and `data/phase_f` directories were read from the
existing sealed repository data location through worktree-local symlinks; no
data were regenerated or modified.
