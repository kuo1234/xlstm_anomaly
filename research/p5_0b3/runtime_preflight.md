# P5-0B3 runtime preflight

**Runtime gate:** `PASS`

**SOURCE operational/semantic access:** not started at this gate

This is the required synthetic-only runtime gate for P5-0B3. It does not
validate SOURCE support, detector folds, or model readiness, and it does not
authorize any TARGET access.

## Pinned environment

- CPython `3.12.3`
- NumPy `1.26.4`
- TensorFlow `2.18.1`; Keras `3.15.1`
- EnergyFaultDetector `0.7.1`, commit
  `ced470e1386066931bad32f3cb6e24bac9c5bb89`, clean Git tree
  `899d9ea5a891508bb6b447ca4cd7a9b825607209`
- Linux `6.17.0-1026-nvidia`, glibc `2.39`, ARM64; 20 logical CPUs across
  Cortex-X925 and Cortex-A725 cores
- CPU only, deterministic TensorFlow ops, intra-op/inter-op threads `1`, seed
  `17`
- Complete resolved dependency lock SHA-256:
  `5cc46d5a1b2dc63dd4ec1f879babd337a97481f1af8595603ea9ed97ecfad9a5`

The preflight checks the exact Python version, complete installed package
version set, dependency-lock hash, clean EFD commit/tree and imported module
paths, CPU-only device configuration, float32 model policy, and the frozen EFD
model/optimizer settings.

## Synthetic repeatability result

The script trained two independent EFD autoencoders on the same synthetic
`259 x 8` partial-NaN input. Each fit used the frozen 100-epoch configuration
with seed `17`. The preprocessing arrays were byte-identical; all `259` scores
were finite and identical across runs. Maximum absolute and relative score
deltas were both `0.0`, within the required `atol=1e-7`, `rtol=1e-7` gate.

The combined output is retained in `runtime_preflight.log`; the parsed result
is retained in `runtime_preflight_result.json` (SHA-256
`e5ea82ab60d69e1578d4cef835e815c83e1d0fdb63eaa17a645557cbac9cb939`). The log
SHA-256 is
`cd8867669f98f5087e65c2ee56e2d5745f74e593a4f6713b3e2e28e44d7cd121`. It
includes this TensorFlow
diagnostic, unchanged across both preflight invocations:

> `NodeDef mentions attribute use_unbounded_threadpool which is not in the op definition ... Unknown attributes will be ignored.`

The [TensorFlow 2.18.1 NodeDef validator](https://github.com/tensorflow/tensorflow/blob/v2.18.1/tensorflow/core/framework/node_def_util.cc)
describes this as an unknown NodeDef attribute that is ignored. The
[2.18.1 dataset op definitions](https://github.com/tensorflow/tensorflow/blob/v2.18.1/tensorflow/core/ops/dataset_ops.cc)
show `use_unbounded_threadpool` on `ParallelMapDatasetV2`, not `MapDataset`.
The diagnostic did not prevent either fit, and the required
repeatability check passed. This record makes no broader compatibility claim
outside the exact locked runtime and tested synthetic training path.

## Reproduction

```bash
CUDA_VISIBLE_DEVICES=-1 \
TF_DETERMINISTIC_OPS=1 \
TF_NUM_INTRAOP_THREADS=1 \
TF_NUM_INTEROP_THREADS=1 \
PYTHONHASHSEED=17 \
P5_EFD_SOURCE=/tmp/p5-efd-v071 \
/tmp/p5-0b3-venv/bin/python research/p5_0b3/scripts/runtime_preflight.py
```

The preflight and its tests use synthetic inputs only. No project manifest,
operational file, or semantic label was opened to produce this gate result.
