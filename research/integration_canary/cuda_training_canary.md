# Canary B — real Phase-F seed-11 CUDA training

Status: **BLOCKED** for integration readiness.

This was a bounded engineering run, not a scientific experiment. It used the
sealed Phase-F train/validation windows and `orders_11.npy`, batch 128, W=64,
D=8, embedding 40, float32, Adam `lr=0.001`, no autocast, no TF32, and the
same source-ascending window cohort. No labels, test sources, observers,
checkpoints, or probe code were used. Vanilla and CUDA started from the same
mathematical initial parameters using the existing recurrent-layout adapter.

The predeclared engineering rule was symmetric validation-MSE difference at
most 1% for every executed epoch. The first epoch passed, so the run was
extended to the permitted three epochs. All values remained finite, all epochs
consumed 316 optimizer steps and 40,330 windows per backend, and both training
losses decreased. Nevertheless, CUDA validation diverged materially after the
first epoch, so the canary is not accepted.

| epoch | vanilla train MSE | CUDA train MSE | vanilla validation MSE | CUDA validation MSE | symmetric validation difference | vanilla wall (s) | CUDA wall (s) | speedup |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.0923043 | 0.0923043 | 0.00411453 | 0.00410668 | 0.191% | 54.153 | 10.431 | 5.19x |
| 2 | 0.00238113 | 0.00238774 | 0.00136732 | 0.00138236 | 1.088% | 54.530 | 10.227 | 5.33x |
| 3 | 0.00113965 | 0.00109865 | 0.000771477 | 0.000743329 | 3.649% | 55.309 | 10.266 | 5.39x |

The symmetric difference is `abs(vanilla-CUDA)/max(abs(vanilla),abs(CUDA))`.
The first three epoch-1 step losses were identical in the recorded precision;
the later validation divergence is therefore not an immediate non-finite or
data-order failure. Initial loss was `1.1532068253` for both backends. Peak
allocated memory was approximately 772.4 MB (vanilla) and 529.4 MB (CUDA).
Sealed data loading took 0.332 s; validation took approximately 6.25–6.37 s
per vanilla epoch and 1.06–1.07 s per CUDA epoch.

The machine-readable run is `cuda_training_canary.json`. An initial execution
was discarded for a JSON `numpy.bool_` serialization defect. A subsequent
diagnostic exposed and discarded an intermediate harness version that used
`np.array_split`; the final run uses the exact sealed contiguous partition
(315 batches of 128 plus a final batch of 10), recorded in the order manifest.
No scientific artifact was touched.
