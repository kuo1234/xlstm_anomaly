# Canary A — trained-checkpoint observer equivalence

Status: **PASS**.

This engineering canary used the frozen Phase-F xLSTM seed-11 checkpoint:

* path: `data/phase_f_v4/runs/xlstm_11/best.pt`
* checkpoint SHA256: `4729a3ba385b285078aa987fce176e61fd382715c5357fc92f2635a929a0ae41`
* selected epoch: 50
* vanilla model hash: `49cf7982872c53280d315fb529133aaca3ac34609d9a34c7382bccbed0773f15`

The checkpoint was loaded into the CUDA model through the existing recurrent
layout adapter (`int2ext` → `ext2int`). V0 and FastObserver then ran on the
same CUDA model and identical `[B,64,8]` tensors. The CUDA extension was the
validated GB10 `sm_121`, `static-global-template-stub=false` build. No labels,
evaluator truth, anomaly metrics, or test-result selection entered extraction.

The fixed fixture included stationary, abrupt, gradual, recurring,
correlation-only, and anomaly-containing observations. The extractor saw only
the selected observation windows. Batch sizes were 1, 8, and 128. The frozen
contract was `atol=1e-5`, `rtol=1e-4`; failed elements mean `torch.isclose`
failure under both tolerances.

| batch | output max abs | score max abs | common18 max abs | hidden max abs | input-gate max abs | retention max abs | memory max abs | status |
|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| 1 | 0 | 0 | 5.96e-8 | 2.38e-7 | 2.38e-7 | 4.17e-7 | 2.98e-7 | PASS |
| 8 | 0 | 0 | 5.96e-8 | 2.98e-7 | 2.98e-7 | 4.17e-7 | 3.58e-7 | PASS |
| 128 | 0 | 0 | 1.19e-7 | 3.58e-7 | 5.96e-7 | 7.15e-7 | 4.17e-7 | PASS |

All feature families were finite, shape-identical, and had zero failed
elements. The complete machine-readable details are in
`observer_checkpoint_canary.json`.
