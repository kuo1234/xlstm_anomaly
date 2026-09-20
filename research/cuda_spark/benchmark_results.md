# CUDA benchmark results

All measurements use fresh random weights and random D=8/W=64 float32 inputs;
no scientific checkpoint, label, or Phase-F/G data was read. Each run has five
warmup steps and twenty timed Adam reconstruction steps unless stated
otherwise. CUDA uses native `sm_121` and the isolated
`--static-global-template-stub=false` overlay. TF32 is disabled for the
comparison process.

## Correctness

The full improved official xLSTMAD architecture (two stacks, three blocks,
embedding 40, D=8) passed forward/backward on CUDA. Vanilla and CUDA with the
same mathematical weights produced:

| Quantity | Result |
|---|---:|
| output max abs difference | `5.3644180e-7` |
| reconstruction loss (both) | `1.1567840576` |
| input-gradient max abs difference | `2.6775524e-9` |
| max parameter-gradient difference | `5.2154064e-8` |
| repeated CUDA output | exact match |
| finite output/gradients | PASS |

The short 100-step B=128 reconstruction check decreased loss from
`0.8785525` to `0.0403346` on both backends.

## Training throughput

`samples/sec` is windows processed per timed optimizer step. Peak memory is
PyTorch allocated bytes.

| Backend | B | forward s/step | backward s/step | step s | samples/s | peak MiB |
|---|---:|---:|---:|---:|---:|---:|
| vanilla | 128 | 0.05545 | 0.11016 | 0.16714 | 765.8 | 638.0 |
| CUDA | 128 | 0.00748 | 0.01804 | 0.02646 | 4836.9 | 384.9 |
| vanilla | 256 | 0.05940 | 0.11683 | 0.17772 | 1440.5 | 1223.5 |
| CUDA | 256 | 0.01191 | 0.03461 | 0.04668 | 5484.7 | 699.9 |
| vanilla | 512 | 0.07094 | 0.18471 | 0.25586 | 2001.1 | 2356.5 |
| CUDA | 512 | 0.02397 | 0.07181 | 0.09595 | 5336.2 | 1313.5 |
| vanilla | 1024 | 0.09921 | 0.32199 | 0.42137 | 2430.1 | 4605.7 |
| CUDA | 1024 | 0.04853 | 0.15137 | 0.20007 | 5118.2 | 2554.4 |

Approximate CUDA speedups in full optimizer steps are 6.31x, 3.81x, 2.67x,
and 2.11x for B=128/256/512/1024. B=1024 was still finite and below the
available-memory pressure observed in this run; no larger batch was attempted.

## Inference and feature-observer path

For B=128 and twenty no-grad iterations:

| Path | Backend | batches/s | decisions/s | peak MiB |
|---|---|---:|---:|---:|
| score only | vanilla | 22.77 | 2914 | 146.1 |
| score only | CUDA | 147.84 | 18924 | 146.1 |
| score + existing scalar observer | vanilla | 12.51 | 1601 | 165.0 |
| score + existing scalar observer | CUDA | 23.28 | 2980 | 165.0 |

The observer uses the existing Python reference replay and checks CUDA states;
it is CPU-bound enough that the end-to-end feature path improves only about
1.86x, even though score-only inference improves about 6.49x. This does not
certify a future production feature extractor; it shows that the same observer
can execute and pass on CUDA.

An external `nvidia-smi` sampler covering a short B=128/B=1024 mixed benchmark
recorded 110 samples, GPU utilization 0–95% (mean 70.9%). GB10 memory fields
were unavailable through `nvidia-smi`; PyTorch allocation is reported above.

Raw JSON/log evidence remains on the historical branch; especially:

- `native121_static_false.log`, `native121_default.log`, `native121_rdc.log`;
- `vanilla_cuda_compare_v5.jsonl`;
- `throughput_benchmark_v2.jsonl`;
- `traincheck_100_b128.jsonl`;
- `inference_score_b128.jsonl`, `inference_observer_b128.jsonl`;
- `nvidia_smi_benchmark.csv`.
