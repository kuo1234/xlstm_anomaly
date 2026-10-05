# Parity, reset and causal feasibility

## What was actually executed

[Executable fixture](optional_minimal_prototypes/state_probe.py), [machine-readable result](provenance/state_probe.json), [dependency environment](provenance/probe_environment.txt). One CPU random-input audit: seed22, B2/T23/D8, E40, context capacity64, both native encoder/decoder stacks, vanilla float32, eval, deterministic algorithms enabled, no optimizer, no gradients, no labels, no scientific checkpoint. Four scalar recurrent matrices were initialized to nonzero random values in the fixture to avoid a trivial all-zero recurrence test. This is not training or a changed upstream implementation.

The source pin and float32 configuration match E2; runtime is Python3.14/PyTorch2.9.0 on macOS CPU, **not** the old Linux/PyTorch2.13/CUDA environment. The initial attempt to install torch2.8.0 had no wheel for this Python; torch2.9.0 was chosen for runtime compatibility before running outcomes. The independent audit venv resides outside the repository. Full dependency versions are recorded; broad optional dependencies were installed by xlstm's distribution but optimized kernels were not invoked.

19/19 checks passed at fixed `atol=1e-5, rtol=1e-4` (the historical E2 tolerances, not relaxed after results). Execution after imports/setup took about 0.22 seconds; that is not an end-to-end throughput benchmark.

| Evidence | Observed result |
|---|---|
| Native full-sequence reconstruction vs stack.step reconstruction | max absolute output difference 3.129243850708008e-7; numerical, not bitwise parity |
| Same stream delivered in chunks `[3,1,7,12]` with complete state capture at boundaries | output and final full state bitwise identical to uninterrupted recurrent execution |
| Serialized deep snapshot after 9 points, restore, replay suffix | output and final full state bitwise identical |
| Deep snapshot stays immutable while live state advances | pass; live-state mutation negative control detected |
| Full reset before suffix vs native fresh full forward on suffix | max absolute difference 4.172325134277344e-7 |
| Clear cells but retain conv buffers | differs from fresh by 0.10981784760951996; detects incomplete reset |
| Change every future observation after prefix | prefix outputs bitwise unchanged in both paths |
| Batch permutation / separate B1 processing | permutation bitwise; partition max difference 3.2782554626464844e-7 |
| New stream fresh state | agrees with independent native fresh forward within 2.905726432800293e-7 |
| Reconstruction score before KEEP/RESET fork | current score bitwise equal, later output differs |
| State finiteness; parameters and all registered buffers; RNG | finite, unchanged, unchanged |

No anomaly/drift series were generated. All positives are API feasibility evidence only; no learned observer or scientific effect is tested.

## Three different parity claims

1. **Native full forward vs recurrent-step output:** measured on a small fresh-state fixture. Full forward's mLSTM uses `parallel_stabilized_simple`; step uses `recurrent_step_stabilized_simple`. They implement related stabilized algebra with potentially different floating-point summation/scale and epsilon effects. Native forward does not return full mixed-stack state; final-state equality with it was **not** measured.
2. **Uninterrupted recurrent vs chunk-delivered recurrent:** exact here for outputs **and** returned full state. The chunk wrapper loops native S=1 steps, preserving all state; it is not an optimized vectorized chunk kernel. Changing chunk boundaries alone changes no observation or reset schedule.
3. **Optimized parallel chunk-with-initial-state kernel:** **NOT VERIFIED**. `chunkwise_simple` exists in backends.py but is not the selected `mLSTMCell.forward` backend; it has shape/chunk-size constraints and a distinct interface. The layer.forward path does not consume/export all state. Do not equate its mere presence to end-to-end supported carry. No patch or optimized kernel prototype is included.

Thus C1 has a credible, measured **step-wrapper** route. A full architecture-preserving vectorized state-carry implementation is not being claimed. Kernel-scale performance and long-horizon numerical equivalence remain open.

## Gate coverage and remaining tests

| Concern | Current resolution | Before any later scientific inference |
|---|---|---|
| Convolution/state completeness | all 6 layers' cell and conv states enumerated/captured | verify all actual trained-config states and schema; fail on missing/extra keys |
| Layer norm / projections / residuals | token-local static inspection and native full/step output parity | repeat on any changed objective/head/config |
| Encoder / decoder histories | separate complete dictionaries; no bottleneck/forecast rollout in improved path | forecast wrapper needs its own timeline and tests |
| Overlapping windows | native stride1 verified; prototype consumes disjoint successive tokens | instrument ingest IDs; prohibit replay except named finite-context comparator |
| Backend / precision | vanilla CPU float32 only | independently gate target hardware, trained checkpoint and long streams; do not transfer this PASS to CUDA/half |
| Padding / masks / short chunks | no padding; a size1 chunk tested | specify missingness, variable lengths, batch padding and masked no-op semantics; reject silent padding updates |
| Batching / stream boundaries | homogeneous B2, partition/permutation and fresh independent stream tested | asynchronous per-row reset/stream permutation, checkpoint restart, empty stream, gaps and reorder checks outstanding |
| Dropout / eval | disabled, RNG unchanged | reject training mode/stochastic inference unless snapshot includes its RNG |
| Sequence capacity | T23 below configured64 | native parallel mask beyond64 is not covered; extend/configure before comparison, never truncate/pad silently |
| Reset C2 | discard all external model state; compare native fresh suffix; parameters/buffers unchanged | drift observer, scaler and prediction queue absent here; their reset policy needs separate tests |
| Score ordering C3 | tested reconstruction score then KEEP/RESET, no retroactive rescore | one-step forecast must have prediction issued before x_t; future-prefix invariance must include observer and score log |

A frozen scaler is configuration, not something silently refitted at reset. No optimizer exists in the prototype. Batchwise model buffers include causal masks; the fixture checks named_buffers as well as parameters, including nonpersistent masks omitted by state_dict.

## Reproduction

Use a disposable virtual environment with the recorded dependencies and fetch the pinned upstream module (the script verifies its SHA256 before import). Example from repository root, replacing the Python path if necessary:

```sh
curl -L --fail https://raw.githubusercontent.com/Nyderx/xlstmad/e8b56ba27352733bb83729e85b1d6196dca70c99/xlstmad.py -o /tmp/xlstmad.py
python research/drift_aware_xlstm_m0e/optional_minimal_prototypes/state_probe.py --upstream-dir /tmp --output /tmp/state_probe.json
```

Compare script/source hashes and named checks, not elapsed time or cross-platform bitwise equality. Preserve any failed result; do not loosen tolerance or substitute a kernel to obtain PASS. The fixture validates API mechanics, not a performance protocol or deployable detector.
