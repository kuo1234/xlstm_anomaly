# Full persistent inference state

Pinned source: PyPI `xlstm==2.0.5`, SHA-verified against the E2 source seal; see [provenance](provenance/code_sources.json). File/function references below refer to that wheel, not current main or xLSTM-Large. Actual shape enumeration is in [state_probe.json](provenance/state_probe.json).

## Model-state inventory

For each of **encoder and decoder**, maintain an independent dictionary returned by `xLSTMBlockStack.step`, with `block_0`, `block_1`, `block_2`. Do not share state between the two stacks or between streams.

| Layer | Persistent values | Actual E40 shape per layer, batch B |
|---|---|---|
| sLSTM blocks 0 and 1 | `slstm_state`: `(y,c,n,m)` (hidden, cell, normalizer, log stabilizer), returned by cell.forward | `[4,B,40]`; each component is concatenated 4 heads × 10 features. No separate external head axis. |
| sLSTM blocks 0 and 1 | `conv_state`: one-element tuple of normalized layer-input history | step buffer `[B,4,40]`, kernel width 4 |
| mLSTM block 2 | `mlstm_state`: tuple `(C,n,m)` | C `[B,4,20,20]`, n `[B,4,20,1]`, m `[B,4,1,1]` |
| mLSTM block 2 | `conv_state`: one-element tuple of up-projected x_mlstm history | step buffer `[B,8,80]`, kernel width 8 |

Thus per stream the six blocks carry 5,928 float32 values (23,712 tensor bytes, excluding object overhead): 4 scalar layers × (4×40 + 4×40) and 2 matrix layers × (4×20×20 + 4×20 + 4 + 8×80). Headwise q/k/v projections use 16 groups × 5 features; these are **not** the four memory heads × 20 dimensions.

In `blocks/mlstm/backends.py::recurrent_step_stabilized_simple`, C stores a stabilized **key-by-value** outer product `k_scaled @ v.T`; readout is `q.T @ C`. q,k,v, output h, output-gate branch z, normalized readout and residual activations are transient at a timestep. There is no extra h recurrence or persistent q/k/v cache in this path. sLSTM y, in contrast, feeds the recurrent projection and must be retained.

## Reset is a state transition, never reset_parameters

`state=None` at **both stacks**, or a fresh empty stack dictionary, invokes native initializers: all y/c/n/m or C/n/m zeros and all convolution buffers zeros. This includes stabilizers; substituting −infinity for m would change the pinned implementation. `reset_parameters()` changes weights and is explicitly the wrong API.

Native `sLSTMLayer.step` calls `slstm_cell.forward(..., state=slstm_state)` with S=1. Use that route through stack.step. The lower-level `sLSTMCell.step` at cell.py:486–494 returns the incoming `state` variable rather than `_get_final_state(all_states)`; its apparent signature is not enough to trust it as a carry primitive. This static hazard does not affect the tested layer route. The vanilla pointwise code also tests `torch.all(n == 0.0)` across the whole tensor when choosing initialization stabilization; heterogeneous per-row reset behavior needs a dedicated gate. Do not assume row masking is equivalent to independent streams.

Dropping y/c alone leaves n/m and convolution history; clearing all recurrent values but keeping conv history is also not a fresh reset. The latter is an explicit negative control in the prototype. A selected-layer reset must clear that layer's cell **and conv** state; untouched downstream layers can still encode the old regime. Label it a partial intervention, not full history erasure.

## Capture/restore contract and hidden mutable quantities

`components/conv.py::conv1d_step` uses `copy_` and assignment on the supplied buffer; `xlstm_block_stack.py::step` updates the supplied dictionary. A shallow copy aliases history. Capture recursively clones/detaches tensors and their containers. A restored snapshot must not share storage with a live branch. Serialization roundtrip plus suffix replay is tested. `state_dict()` captures weights and registered buffers, **not these external recurrence dictionaries**.

Convolution forward's returned tail is `[B,K−1,D]` as a tensor; convolution step uses a tuple containing `[B,K,D]`. These APIs are not interchangeable without an explicit conversion. The full mixed stack forward does not expose a complete final carry state. Do not forward an sLSTM tail into a step tuple or claim that `return_last_state=True` works uniformly through mixed residual blocks.

LayerNorm and MultiHeadLayerNorm (`components/ln.py`) operate independently per token/features (group_norm reshapes to B*S); no running mean/variance or positional counter. Projections, residual/skip weights and FFNs add no inference history. mLSTM causal masks are fixed nonpersistent registered buffers; retain config/device and verify them, but do not treat masks as regime memory. All dropout is disabled by eval. With deterministic eval no RNG state is consumed in the tested path; stochastic inference would additionally need RNG capture and is out of scope.

**Complete streaming-system snapshot** also includes stream ID and timestamp/ingest cursor, outstanding forecast and its issue/target times, warmup/reset age, residual aggregation ring, drift observer statistics and cooldown, frozen scaler/calibration identity, model/config/source hash and numerical backend/dtype. Missing values/gaps and padding masks need explicit rules. A model reset normally leaves already-emitted score records and frozen calibration intact; whether observer history resets must be separately specified to avoid repeated triggers. There is no optimizer in frozen inference. Any online normalizer update is an additional adaptation mechanism, not state-only evidence.

The wrapper in this audit has no observer, scaler, forecast queue or optimizer and does not pretend to validate them. Complete model state is deterministic on the tested CPU fixture; complete deployment-system capture is a design contract, not an implemented product claim.

## Why state *= rho is not forgetting

sLSTM stabilized recurrence updates c and n jointly and emits `o*c/n`; uniform c,n scaling can leave the immediate ratio unchanged while changing future effective gates. mLSTM readout divides `q.T C` by `max(abs(q.T n),exp(-m))+eps`; scaling C,n changes the two denominator branches differently. m is a log stabilizer, not an ordinary magnitude; multiplying it by rho has no consistent retention interpretation. Scaling y changes subsequent sLSTM gate logits. Scaling conv history changes feature preprocessing.

External forgetting, if ever pursued, must modify the retained contribution with log(rho) and recompute stabilization consistently, while specifying n, y and conv semantics. Even that is a new equation/controller and requires fresh parity/numerical analysis; it is **not implemented or authorized here**. Whole-state hard reset is the clean first diagnostic; fixed finite replay is the essential context control.
