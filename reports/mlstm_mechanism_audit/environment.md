# Environment and commands

The runs used `/home/p76141495/home/xlstm_anomaly/data/phase_e2/venv/bin/python`
with Python 3.12, PyTorch 2.13.0+cu130, `xlstm==2.0.5`,
`lightning==2.6.1`, CUDA 13.0, and the DGX Spark GB10 (compute capability
12.1).  The xLSTM CUDA extension was the already validated overlay at
`research/cuda-spark` commit `dd5ad9d1d1580be2e39313bc6cb7befa0f9cdf61`, using
SM121 and `static-global-template-stub=false`.

The backend flags were deterministic=True, benchmark=False, float32 matmul
precision `highest`, CUDA matmul TF32=False, cuDNN TF32=False, no autocast.

Representative commands were:

```text
python scripts/mlstm_inference_canary.py --mode parity --output reports/mlstm_mechanism_audit/inference_parity.json
python scripts/mlstm_inference_canary.py --mode benchmark --output reports/mlstm_mechanism_audit/observer_benchmark.json
python scripts/mlstm_probe.py --seed 11 --output reports/mlstm_mechanism_audit/seed11_results.json
python scripts/mlstm_probe.py --seed 22 --output reports/mlstm_mechanism_audit/seed22_results.json
python scripts/mlstm_probe.py --seed 33 --output reports/mlstm_mechanism_audit/seed33_results.json
```

All commands used the existing sealed checkpoint paths and did not create an
optimizer or write model weights.
