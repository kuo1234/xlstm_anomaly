# Step 0 — canonical mLSTM repair (P7+P10, issue #15)

Scope (authorized in #15 comment 5953762106): wrapper + state carry + parity only. Not done here: G-L1 rerun, drift
augmentation, oracle segment experiment, W1–W4, changes to P1–P4, protocol/seal.

## Files

- `scripts/p10_canonical_mlstm.py` — `CanonicalMLSTMLayer` (stateful wrapper around the official layer),
  `CanonicalMLSTMForecaster` (time-series wrapper `[B,T,C] -> (pred, state)`), `siging_step`.
- `scripts/p10_step0_parity.py` — all parity checks; writes JSON.
- `tests/test_p10_canonical_mlstm.py` — 17 tests (16 CPU + 1 CUDA-only). Local CPU: 16 passed, 1 skipped; GB10: 17 passed.
- `research/writable_neural_memory_p10/step0/parity_cpu_fp64.json`, `parity_gb10_gpu.json` — raw numbers.

Versions: xlstm 2.0.5, mlstm_kernels 2.0.5; torch 2.13.0 (local CPU, macOS) and 2.13.0+cu130 (GB10, NVIDIA GB10).

## Arm → implementation

| arm | modules | cell core (chunk) | cell core (step) |
|---|---|---|---|
| **mLSTMexp** (canonical) | official `xlstm.blocks.mlstm.layer.mLSTMLayer` (proj_up ×2, CausalConv1d k=4 + SiLU, block-diag q/k/v bs=4, igate/fgate on concat(q,k,v), MultiHeadLayerNorm, learnable_skip, h·SiLU(z), proj_down; official init) | `mlstm_kernels.torch.chunkwise.native.mlstm_chunkwise__native_autograd` with `c/n/m_initial`, `return_last_states=True` | `mlstm_kernels.torch.recurrent.native_step.mlstm_recurrent_step__native`; reference = official `mLSTMLayer.step` |
| **mLSTMsig** (TFLA) | same official modules | GPU: `mlstm_kernels.torch.chunkwise.triton_xl_chunk_siging.mlstm_siging_chunkwise__xl_chunk` (with `c/n_initial`, `return_last_states`) | `siging_step` (local; no native siging step exists in 2.0.5), verified against `parallel.native_siging.mlstm_siging_parallel__native_autograd` and the triton chunk kernel |
| **mLSTM-sig+n** | historical G-L1 `p10_gl1_models.MLSTM`, unchanged | own chunk code | own step |

`mLSTMsig` default `normalize=False` = paper definition (no n/m state). The library default is `normalize=True`
(denominator max(|n·q|,1)); the G-L1 cell core is exactly that `normalize=True` core, but without any of the official
layer structure (no up-projection, conv, skip, output gate, head norm, block).

Forecaster shell (both canonical arms): `emb Linear(C,d)` → `x + mLSTMLayer(LN(x))` (xlstm LayerNorm, no bias) →
`LayerNorm` → `Linear(d,C)`; `pred = z + head(.)` (same convention as G-L1). Parameter count at C=38:
d=64 35k, d=96 71k, d=128 120k (G-L1 mLSTM-sig+n: 77k), so d≈96 is roughly parameter-matched.

## Parity (CPU float64 unless noted)

| check | max abs error |
|---|---|
| kernel: chunkwise with nonzero initial C/n/m vs native step loop (S=150/128/50, chunk 64) | ≤ 1.1e-13 (H); state ≤ 6e-16 rel |
| kernel: same vs xlstm backend `recurrent_step_stabilized_simple` loop | ≤ 1.1e-13 (H); state ≤ 6e-16 rel |
| full layer: wrapper (single call / split 70 / split 1; S=150, 129) vs official `mLSTMLayer.step` loop | ≤ 3.1e-15 (y, scale ≈ 6); state ≤ 6e-16 rel; conv state exact |
| state bridge: wrapper→official step and official step→wrapper at t=70 | ≤ 2.4e-15 |
| wrapper (zero state) vs official `mLSTMLayer.forward` (parallel_stabilized_simple) | 4.0e-8 (stabilizer/eps-level difference of the official parallel form) |
| conv state: split vs single call (exp / sig) | 3.6e-15 / 3.3e-16; carried state = last KS−1 pre-conv inputs exactly; zeroing it changes output by 1.6 / 1.2 |
| mLSTMsig `siging_step` vs official parallel siging (normalize False / True) | 5.3e-15 / 8.9e-15 |
| forecaster: split vs full, step loop vs forward (exp, sig) | ≤ 2.2e-15; causal leak before the perturbed t = 0 exactly |
| GB10 GPU fp32: exp wrapper split vs official step | 1.9e-6 |
| GB10 GPU fp32: triton siging chunk (with initial C/n) vs fp64 recurrence | H 1.4e-2 (scale 8.6, ≈1.7e-3 rel), C 1.1e-3 rel, n 2e-7 rel; layer 2.6e-3 (scale 4.7) |

Smoke: 60 Adam steps on a 7-channel sine reduce MSE 0.34 → 0.0016 for both exp and sig.

## Differences from the API described in the review

1. **C/n scale convention.** xlstm's backend scales k by 1/√DH before writing; mlstm_kernels scales q instead, so
   the same trajectory has `C_xlstm = C_kernels/√DH` (likewise n). The wrapper keeps the mlstm_kernels convention and
   converts in `to_official`/`from_official`. Without the conversion outputs still match from a zero state, but a state
   handed between the two libraries would be wrong by a factor √DH.
2. **Official conv state.** `mLSTMLayer.step` takes `conv_state` as a 1-tuple `(B, KS, D)` holding the last KS inputs
   incl. the current one; `CausalConv1d.forward(x, conv_state)` takes the last KS−1 inputs. The wrapper stores KS−1.
3. **Chunkwise needs S % chunk_size == 0** (`mlstm_chunkwise__native_autograd` asserts it). The wrapper runs the
   multiple-of-64 prefix chunkwise and the remainder with the official native step (S=50, 129, 150 tested).
4. **`mlstm_recurrent_step__native` defaults `dtype_state=float32`.** The wrapper promotes to the input dtype
   (fp64 parity was 7e-7 before this fix, 3e-15 after).
5. **mLSTMsig on CPU has no official stateful kernel.** Official stateful siging exists only as triton (GPU); on CPU the
   wrapper uses the local `siging_step`, checked against the official parallel kernel. With `normalize=False` the triton
   kernel does not maintain n, so the wrapper keeps n inert.
6. **Triton precision.** The triton siging kernel's `tl.dot` runs fp32 inputs at TF32, so it differs from an fp64
   recurrence by about 1e-3 relative; the native exp path on GPU is about 1e-6.
7. **GB10 environment.** Triton's JIT needs Python headers the system lacks; the `libpython3.12-dev` .deb was extracted
   to `~/.local/pyhdr` (no sudo) and passed via `CPATH`. pytest was installed with `--user`.
