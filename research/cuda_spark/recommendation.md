# Recommendation

## Engineering verdict: GO, with an isolated compatibility overlay

The CUDA backend meets the requested engineering gates on this Spark:

1. reproducible build on GB10 using native `sm_121`;
2. finite forward and backward;
3. stable repeated execution;
4. vanilla/CUDA numerical agreement at roughly `1e-6` output and `1e-8`
   gradient scale for the deterministic fixture;
5. a 100-step reconstruction loss decrease;
6. material training throughput improvement (about 6.3x at B=128 and 2.1x at
   B=1024 in this short benchmark).

The GO is for engineering follow-up, not authorization to alter Phase F/G.
The pinned package's default loader remains broken on CUDA 13 and still emits
the non-native compute_80 target. The fix must remain process-local or in a
separately reviewed overlay that adds:

```text
-gencode arch=compute_121,code=sm_121
--static-global-template-stub=false
```

Do not silently patch site-packages, upgrade the scientific environment, or
replace any sealed checkpoint.

## Estimated project impact

Historical vanilla Phase-F-like runs were approximately 1.1–1.9 hours per
seed, about 8.5 GPU-hours for five seeds. Applying the measured B=128 training
speedup gives a rough engineering estimate of 10–18 minutes per seed and
0.9–1.5 hours for five seeds (about 1.3 hours if the historical 8.5-hour total
is used). This is an extrapolation, not a new Phase-F result; dataloading,
checkpoint I/O, compilation, and observer work can reduce the realized gain.

The measured score-only inference path is about 6.5x faster at B=128. The
existing scalar feature observer is only about 1.86x faster end-to-end because
its reference replay is Python/Torch work. Thus CUDA can help later feature
extraction, but it does not turn the current observer into a fully fused CUDA
instrumentation path and does not justify claiming a 6.5x G1 speedup.

## Recommended next experiment (separate authorization required)

Run a single prospective, unlabeled CUDA-vs-vanilla parity canary using the
same random fixture and isolated overlay, then benchmark the exact feature
observer at the intended production batch shape. If that canary remains
finite and numerically stable, a new CUDA-backed detector training study can
be proposed with new checkpoints and a new provenance record. Do not rerun G1,
overwrite Phase-F/G artifacts, or interpret this engineering benchmark as
scientific evidence.
