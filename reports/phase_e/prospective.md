# Phase E bounded instrumentation pilot

Reporting-only H1 amendment `839cc08` precedes this phase. Preserve all D-v2
evidence. No harm experiment, feature-label extraction, probe or matched LSTM fit.

Immutable detector: Nyderx/xlstmad at 3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6,
models/xlstmad_rec_ad.py reconstruction MSE. Dependency xlstm==2.0.3 as required
by that checkout; download wheels and hash their contents. Native run_custom.py
uses W50, embedding40, batch128, lr0.005 (class defaults W100/embedding20 differ).
Common diagnostic changes only W to64 and input D8; retain embedding40, all
six blocks and original readout. No architecture search or carry between windows.

Attempt original CUDA backend separately. Original sLSTM defaults bfloat16
internally despite float32 input/parameters. For the preregistered float32
reference comparison, explicitly set all sLSTM dtype fields to float32 in an
external config overlay, keeping equations/weights/layout/readout unchanged.
The wheel's vanilla backend is a numerical reference, NOT an automatic replacement
for the native detector. Native CUDA compilation/execution failure remains blocked
native parity, even if the reference runs. No silent version/backend substitution.

Observe sLSTM cell states (hidden y, c,n,m) and stabilized effective i/f from the
same scalar cells. Do not identify gate roles from projection attribute names:
the pinned layer feeds fgate projection to the input slot and igate to forget slot.
Common scalar readout is c/n. Matrix-only states are audit-only and excluded.
Freeze 18-column executable schema in scripts/phase_e_schema.py: population
std, linear quantiles, zero previous state at each cell-call start, right-edge
summaries; equal per-head then per-scalar-layer pooling. Encoder uses its last
input timestep; decoder uses its last singleton invocation, whose previous state
is zero because native decoder restarts recurrence on every call. Never chain
decoder recurrent states to invent history. External rolling stats remain causal
4/8/16/32 decision means/std/OLS slopes; incomplete history is warmup, not padding.

Pilot only uses pseudorandom Gaussian observations from a separate torch generator
seed710; random model seed11, no dataset labels or benchmark scoring. W50 and W64,
D8, embedding40; parity B4 plus final-batch B3/B1 checks, throughput B128 (native
batch size), 2 warmups/5 timed forwards where feasible, 1 warmup/3 timed
forward-backward batches without optimizer steps. No trained checkpoint or probe.
Watchdog total process budget1800s; stop early on parity failure. After a failure,
only bounded diagnostic tests/timing, no scientific expansion or changed tolerance.

Float32 atol1e-5/rtol1e-4 frozen; observer OFF/ON bitwise same-backend outputs.
Check states finite, independent-window reset, batch permutation of model output
AND native flattened score path, encoder prefix causality, reference recurrence,
and mLSTM parallel/recurrent agreement where available. Missing scalar features
block H3a. Readout/scoring failure remains an E blocker; do not silently transpose
native outputs or rewrite the detector to pass.

Report measured versus unavailable throughput, memory, overhead and explicit
E/F/G extrapolation assumptions using sealed manifest lengths. >5x reference
overhead or >160 GPU hours requires review; no matched LSTM timing/training is
authorized. Unmeasured F runtime remains N/A, not claimed empirical throughput.
