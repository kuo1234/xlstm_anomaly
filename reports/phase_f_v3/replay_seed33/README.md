# F3-R seed33 epoch-29 deterministic replay

This directory is an implementation diagnostic only.  It replays the exact
sealed F-v3 matched-LSTM seed33 run from initialization through epoch 29 using
the same train/validation prefixes, per-source scalers, epoch orders, Adam
state, W64/B128 cohort, float32 backend, and scoped cuDNN-disabled `nn.LSTM`
calls.  No anomaly labels, test sources, probes, or Phase G data were read.

Replay fidelity for epochs 1--28 is `PASS`: train MSE, validation MSE,
training-order hashes, canary pass flags, canary shapes, and canary max-abs
values reproduce the sealed F-v3 trace (28/28 rows).  This replay is not
scientific evidence; it only validates the failure localization setup.

The model state was saved immediately after the epoch-29 optimizer updates and
before the non-raising epoch-29 canary.  The canary then used the fixed
random-unlabeled seed710 B128 fixture and the unchanged `atol=1e-5,
rtol=1e-4` allclose rule.

## Localization result

| stage | allclose | max abs | mean abs | failed elements |
|---|---:|---:|---:|---:|
| input projection | PASS | 0 | 0 | 0 / 311296 |
| encoder0 | PASS | 9.220093488693237e-07 | 1.4221847699502632e-08 | 0 / 311296 |
| encoder1 | PASS | 2.4437904357910156e-06 | 1.9409345242138442e-08 | 0 / 311296 |
| encoder2 | PASS | 1.296401023864746e-06 | 2.471476712173626e-08 | 0 / 311296 |
| decoder0 | PASS | 1.5497207641601562e-06 | 3.431634709727405e-08 | 0 / 311296 |
| decoder1 | PASS | 2.9206275939941406e-06 | 6.05998522473783e-08 | 0 / 311296 |
| decoder2 | PASS | 6.496906280517578e-06 | 1.0002703021427802e-07 | 0 / 311296 |
| GELU | PASS | 5.662441253662109e-06 | 7.479651031871981e-08 | 0 / 311296 |
| output projection | **FAIL** | **1.800060272216797e-05** | **6.533035730171832e-07** | **1 / 65536** |

The first failed stage is the final non-recurrent output projection.  Every
recurrent stage and GELU remains within the frozen allclose rule; no recurrent
stage is a failing layer.

The epoch-29 canary fields were:

* raw output: FAIL, max abs `1.800060272216797e-05`, mean abs
  `6.533035730171832e-07`, 1 failed element / 65536;
* reconstruction score: PASS, max abs `2.1606683731079102e-07`, 0 failed
  elements / 128;
* common18: PASS, max abs `3.5762786865234375e-07`, 0 failed elements / 2304;
* full/partition finite and shape checks: PASS;
* six-layer manual/native sequence h, final h, final c, finite-state, and
  input/forget gate-range checks: PASS for the full call and all 768 partition
  layer calls;
* observer on/off output and score: bitwise PASS, RNG unchanged;
* reset and prefix-causality checks: PASS.

## Decision

This localizes the seed33 failure to the non-recurrent output-projection path
after recurrent and observer/reference checks pass.  Per protocol, stop after
diagnosis and return for external review.  Do not create F-v4 automatically,
change CUDA/cuDNN/backend, relax tolerance, alter architecture/batch size, or
reuse the diagnostic state.

H2/H3 remain `NOT_TESTED`; Phase G remains `LOCKED`.

