# Resolved mLSTM state semantics

The installed xLSTM 2.0.5 implementation uses the stabilized mLSTM update.
For head width `DH=20` and four heads, the state tensors are:

| state | shape per timestamp | meaning |
|---|---:|---|
| `C`/`c_state` | `[B,4,20,20]` | matrix key/value memory |
| `n`/`n_state` | `[B,4,20,1]` | key normalizer accumulator |
| `m`/`m_state` | `[B,4,1,1]` | log-scale stabilization state |
| `h` | `[B,4,20]` | raw normalized readout before the cell output normalization |

The recurrence is stabilized with

```text
m_t = max(logsigmoid(fgate_t) + m_{t-1}, igate_t)
f_t = exp(logsigmoid(fgate_t) + m_{t-1} - m_t)
i_t = exp(igate_t - m_t)
C_t = f_t C_{t-1} + i_t (k_t/sqrt(DH)) v_t^T
n_t = f_t n_{t-1} + i_t (k_t/sqrt(DH))
h_t = q_t^T C_t / (max(|q_t^T n_t|, exp(-m_t)) + eps)
```

The official parallel implementation does not provide a history of these
states.  `scripts/mlstm_observer.py` captures q/k/v and performs exactly this
read-only recurrence from zero state for each independent window.  The replay
hidden is passed through the cell's existing `outnorm` only for a diagnostic
comparison with the native cell output; model output always comes from the
untouched native execution.

No matrix inverse, condition number, labels, event metadata, or future
observations enter the observer.
