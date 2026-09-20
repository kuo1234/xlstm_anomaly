# Correctness evidence

## Reference and contract

The original `scripts/phase_e2_observer.py` is the reference. Its complete
Python scalar replay was run on the same model/input fixture as the optimized
observer. The comparison uses the existing frozen `atol=1e-5, rtol=1e-4`
allclose rule and checks finite status, shape, and failed element counts.

No downstream anomaly metric was used to choose or validate the optimization.

## Fixtures

`correctness.py` uses fresh random CUDA models and independent random inputs at
batch sizes 1, 8, and 128. For every one of the four frozen scalar cells it
compares:

* full `hidden` trace;
* full `input` effective-gate trace;
* full `retention` effective-gate trace;
* full `memory` (`c/n`) trace;
* model output and common18 summary.

All three fixtures pass. The largest observed differences across the complete
test is below:

| Quantity | Maximum absolute error | allclose failures |
|---|---:|---:|
| model output / score | 0 | 0 |
| hidden | `1.79e-7` | 0 |
| input gate | `1.61e-6` | 0 |
| retention gate | `1.73e-6` | 0 |
| memory | `2.53e-7` | 0 |
| common18 (B=128 fixture) | `2.38e-7` | 0 |

The largest values are comfortably below the absolute tolerance and every
element passes the combined absolute/relative check. Full machine-readable
the historical branch contains the raw diagnostic JSON; the consolidated
branch preserves the tested contract and summary below.

## Invariants checked by the implementation

* The four observed module names must equal the frozen `SCALAR_CELLS` set.
* Native state shape must be `[4,T+1,B,H]`, with four states and the expected
  four heads; otherwise the fast adapter fails closed.
* The installed CUDA input layout must be the known `SBNGH` layout and is
  explicitly reshaped before gate reconstruction.
* Initial state is excluded from features exactly as in V0; final and
  previous timestamps are selected identically.
* Gate cap (`minimum(exp(...), 1)`) and initial `m` branch are unchanged.
* The observer context restores every cell's original `_impl` method even if
  the model exits through an exception.
* No optimizer, labels, evaluator metadata, scaler, or test result enters the
  observer API.

## Audit separation

The optimized path intentionally omits parity/finiteness checks from the hot
loop. Those checks remain in V0 and should be run on bounded canary batches
when the environment, CUDA extension, model, or checkpoint changes. The fast
path's no-audit reduction is not permission to weaken the scientific validity
contract; it is a separation of production extraction from implementation
auditing.

## Remaining risks

The `_impl` wrapper is an integration seam into xLSTM 2.0.5 rather than a
public observer API. An upstream change to the state layout or input layout
will trigger a shape error, but may require a new adapter. A future direct
gate-cache CUDA extension could reduce the remaining batched gate
reconstruction work, but it would need a new independent equivalence audit.
