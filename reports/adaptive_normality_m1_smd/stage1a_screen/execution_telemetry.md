# Stage 1A execution telemetry

This engineering record was written before Stage-1A labels were opened.

- GPU: NVIDIA GB10.
- Runtime: Python 3.12.3, PyTorch 2.13.0+cu130, CUDA 13.0, xlstm 2.0.5.
- The per-arm `nvidia-smi` sampler in the run records failed to parse its output (`ValueError`, zero samples). The execution summary marks the automated GPU telemetry unavailable.
- During periodic live monitoring, `nvidia-smi` utilization samples ranged from 49% to 86%, with observed temperatures from 59°C to 67°C. These are intermittent observations, not a continuous utilization trace or measured run maximum.
- One early live process listing reported 2,822 MiB GPU memory for the Python process. Later `nvidia-smi` outputs reported GPU memory as unsupported, so this is not a peak or a reliable free-memory measurement.
- Per-fit PyTorch peak-memory records: xLSTMAD-F peak allocated 2,592,951,808 bytes and peak reserved 2,720,006,144 bytes; LSTM-F peak allocated 314,249,216 bytes and peak reserved 2,720,006,144 bytes. These are allocator readings from individual sequential fits.
- No concurrent fit was started. No training setting was changed.
- Stage-1A test-label reads and anomaly metrics remained false/zero at the end of training.
