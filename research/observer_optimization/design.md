# Design decision

## V0 versus selected observer

`scripts/phase_e2_observer.py` remains the immutable reference observer. It
still performs the complete scalar replay and native/reference parity checks.
The new `scripts/phase_e2_fast_observer.py` is an engineering extraction
observer and is intentionally not a replacement for the audit path.

The selected design is **native-state capture plus vectorized gate recovery**:

1. Wrap each of the same four actual sLSTM cell instances at `_impl()` entry.
2. Let the official CUDA cell run unchanged.
3. Capture its returned `all_states` tensor, whose installed CUDA layout is
   `[4, T+1, B, H] = [h,c,n,m]` including the zero initial state.
4. Derive `hidden` directly from `h` and `memory` as `c/n`.
5. Reconstruct raw gates from the already available post-permutation input,
   the native previous `h` history, the unchanged recurrent kernel, and bias
   in one batched `einsum` over `(B,T)`; apply the exact existing
   `logsigmoid`, `maximum`, `exp`, and `minimum` equations.
6. Run a no-audit common18 reduction with exactly the same final/previous
   timestamp, per-head statistics, quantile, and equal-pooling formulas.

The temporal recurrence is not incorrectly parallelized. The official CUDA
kernel still owns the dependent recurrence; only gate reconstruction is
batched using the states that kernel has already produced.

## Why this is semantically valid

The direct state path is not a new cell or a changed model. It only observes
the output of the existing `_impl()` call. The four observed module names are
still checked against the frozen `SCALAR_CELLS` tuple. The state-derived
traces have exactly the same shapes (`B,T,heads,head_dim`) and the same
meaning as V0. The gate equations retain the 2.0.5 upper cap and the initial
`m_0 = i_0` branch.

The fast reduction is a semantic counterpart of `phase_e2_schema.summarize`;
validation and finite/parity checks are removed from the hot path, not from
the reference/canary path. A production use should run V0 on fixed canary
batches and fail closed on disagreement before accepting a checkpoint or
environment change.

## Direct gate-cache instrumentation was not required

The CUDA extension already returns all state history, but inference mode does
not expose gate caches. Exposing those caches from the custom extension would
require changing the installed CUDA/Python ABI and maintaining a fork. The
batched gate reconstruction uses only public results of the existing `_impl`
call plus immutable cell parameters and removes the expensive recurrent
replay without that invasive change.

## Alternatives considered

### Trace-only V0 / deferred replay

Capturing hook inputs first and replaying after the model forward would isolate
parity auditing, but profiling shows the replay itself is ~80% of V0 time. It
does not remove the 64-step Python loop and was therefore rejected as the
primary optimization.

### `torch.compile`

A bounded experiment compiled the vectorized per-cell recovery function in
`torch 2.13.0+cu130`. Compilation took about 2.4 seconds on first use and a
single-cell call averaged about 3.0 ms after compilation. The selected eager
batched path already gives 9.24 ms end-to-end for all four cells plus the model
at B=128, so compiling four independent cell calls adds startup/cache
complexity without a demonstrated end-to-end win. It remains a possible
follow-up if feature extraction becomes dominant again.

### CUDA graphs / streams / multiprocessing

The model forward and native state capture are already one dependent CUDA
execution. Multiple CUDA contexts would add memory and startup overhead, while
streams cannot overlap the state-dependent gate reconstruction with the cell
that produces its inputs. No evidence justified either change.

### Custom fused gate kernel

A fused kernel could reduce the remaining batched pointwise launches, but it
would duplicate CUDA equations and create a larger correctness/maintenance
surface. The selected observer already reaches 13.9k decisions/s at B=128 and
17.1k at B=256/512, so this is not warranted for the current target.

## Future mLSTM instrumentation

The wrapper boundary is cell-agnostic: a future adapter can capture an mLSTM
cell's native state/matrix-memory return without changing the model. The
current trace adapter is deliberately sLSTM-specific and will reject an
unexpected state shape rather than silently inventing mLSTM features. A future
mLSTM implementation should add a separate state adapter and schema binding;
it should not overload the common18 sLSTM gate equations.
