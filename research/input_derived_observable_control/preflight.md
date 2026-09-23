# P1r label-blind preflight

Protocol seal: `90b2470b45b1f8e52aa95ee8677b855b2e3c4e4d` (protocol, implementation and tests).
Both preflight stages ran the byte-identical sealed files; the SHA256 values recorded on the host
equal the blobs at the seal commit. **No model was fitted, no metric was computed, no scikit-learn
module was imported, and no experiment result was produced.**

## Authoritative run — cache host (GB10)

Host: Linux aarch64 (`Linux-6.17.0-1026-nvidia-aarch64-with-glibc2.39`), Python 3.12.3,
NumPy 1.26.4, SciPy 1.17.1. Eight-worker process pool; job
`f0d2800a-caa0-4574-a266-4658c79eec1b`.

**Stage 1 — repository preflight (`preflight.json`): PASS**

| gate | result |
|---|---|
| G1 code identity | sealed-file hashes recorded; `m0/synthetic.py`, `m0/correlation.py` and `configs/synthetic_v1.json` equal `reports/generator_validation_v4` |
| G2 generator identity | 500/500 streams and 25/25 scaler streams equal the sealed cache-host observation hashes |
| G3 determinism | detector input, scaled input, P1 base and P1r bit-identical across two independent computations (0 mismatching streams); scalers deterministic |
| G4 row-key contract | regenerated rows equal A+ `row_meta` exactly: train 697,430 / validation 348,715 / test 697,430 rows, timestamps 5632–21054, keys `71191e06…`, `77ab6914…`, `fb907824…` |
| G5 truth independence | feature signature `(observations, scaler)`; no label/event/regime/semantic name in the feature path; anomaly/legitimate semantic variants give identical observations in 500/500 streams |
| G6 backbone invariance | no backbone, seed, cache or model argument in any feature function |
| G7 temporal support | perturbing input sample 5000 changes exactly decisions 5000–5094, and sample 12345 exactly 12345–12439 (95 rows = `[t−94, t]`); no backward change; boundary samples 0 and 21503 give only in-support changes; first fully finite decision index 31 (`t = 94`) in every stream |
| G8 dimensions | P1 base 128, P1r 1,664, `H+P1r` 1,678, `H+P1r+internal234` 1,912 |
| G9 selection | candidates see train and validation only; test predicted once after selection; frozen HGB family and `max_iter ∈ {100, 300}`; scikit-learn not imported |

**Stage 2 — cache-host preflight (`host_preflight.json`): PASS**

| gate | result |
|---|---|
| H1 | stage 1 PASS under the same seal |
| H2 | sealed code unchanged |
| H3 | inputs bit-identical to stage 1 |
| H4 | P1r bit-identical to stage 1 in 500/500 streams (max relative deviation 0.0) |
| H5 | all six A+ cache manifests complete; all 3,000 cached timestamp arrays equal the regenerated right-edge timestamps |
| H6 | no fit (scikit-learn not imported) |

## Non-admissible host (recorded for completeness)

`preflight_local_host_nonadmissible.json` is the same stage-1 preflight on the review
workstation: macOS arm64, NumPy 1.26.4, sequential. It **FAILS closed at G2**:

- 420/500 streams and 21/25 scaler streams reproduce the sealed cache-host observations.
- All streams of sources 1002, 1009, 2002 and 3005 differ at the bit level.
- The truth arrays match everywhere.

Every other gate passes on that host. Where the observations agree (420 streams), the scaled
input, P1 base and P1r fingerprints are bit-identical across the two hosts. The platform-sensitive
component is the generator's floating-point output, not the P1r feature code.

P1r must therefore be computed on the cache host. The sealed `fit-one` command enforces this: it
refuses to run without both PASS records, and it checks every stream's P1r bit-exactly against
the stage-2 fingerprint before fitting. On the review workstation, a NumPy 2.5.3 environment
reproduced none of the 625 sealed generator observation hashes.

## Status

The preflight is complete. The experiment has **not** been run. Running it requires executing
`fit-one` for the six backbone × seed runs on the cache host, followed by `aggregate`, under the
sealed protocol and the frozen outcome wording in `protocol.md`.
