# Timing summary

Measured real wall-clock timings, including the bounded training loop and
validation. CUDA-event-only microbenchmarks are not substituted for epoch
wall time.

| backend | epoch 1 (s) | epoch 2 (s) | epoch 3 (s) | mean (s) | mean throughput (windows/s) |
|:---|---:|---:|---:|---:|---:|
| vanilla | 54.153 | 54.530 | 55.309 | 54.664 | 738 |
| CUDA sm_121 | 10.431 | 10.227 | 10.266 | 10.308 | 3,912 |

Real epoch speedups were 5.19x, 5.33x, and 5.39x. CUDA forward, backward,
optimizer, and validation components were all faster; the engineering block is
from validation-trajectory divergence, not from speed or numerical finiteness.

The bounded run is not a 50-epoch replacement estimate. If the CUDA trajectory
were later made equivalent, the measured training-only epoch times would imply
about 43.0 minutes for five seeds at 50 epochs (5 × 50 × 10.31 s), versus
about 3.80 hours for vanilla at the measured 54.66 s/epoch. These are bounded
training-loop extrapolations and omit the heavier scientific parity/reporting
work in the historical 50-epoch runner. This extrapolation is
engineering-only and is not authorization to retrain.
