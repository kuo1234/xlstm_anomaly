"""R0-v1.2 capacity-matched auditable LSTM — the single matched-LSTM implementation.

One explicit recurrence is used for training, validation/test reconstruction, the
anomaly score and every internal trace.  There is no second LSTM implementation:
``torch.nn.LSTM``, ``torch.nn.LSTMCell`` and ``phase_f_lstm_observer.replay`` are
never called.  Trace capture retains tensors the recurrence has already computed;
it never recomputes them, so ``forward(x, capture=False)`` and
``forward(x, capture=True)`` execute identical arithmetic.

Per layer and timestep (PyTorch gate order input, forget, candidate, output)::

    raw = linear(x_t, weight_ih, bias_ih) + linear(h_{t-1}, weight_hh, bias_hh)
    i, f, g, o = raw.chunk(4)
    i, f, g, o = sigmoid(i), sigmoid(f), tanh(g), sigmoid(o)
    c_t = f * c_{t-1} + i * g
    h_t = o * tanh(c_t)

Initialisation (frozen, identical semantics and RNG order to the native
matched LSTM): every recurrent tensor ``weight_ih, weight_hh, bias_ih, bias_hh``
is ``U(-1/sqrt(38), 1/sqrt(38))`` drawn in that order per layer (the
``nn.LSTM.reset_parameters`` rule); the input/output projections are default
``torch.nn.Linear`` (weight kaiming-uniform with a=sqrt(5), bias
``U(-1/sqrt(fan_in), 1/sqrt(fan_in))``).  Modules are constructed on CPU in the
order input projection, encoder 0-2, decoder 0-2, output projection immediately
after seeding with the detector seed.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import real_data_r0_data as r0data  # noqa: E402

D = r0data.D
W = r0data.W
WIDTH = 38
EXPECTED_PARAMETERS = 74_100
BACKEND = "auditable_manual_v1_2"
LAYERS = tuple(f"{stack}.{i}" for stack in ("encoder", "decoder") for i in range(3))
TRACE_KEYS = ("hidden", "input", "retention", "memory")


class AuditableLSTMLayer(torch.nn.Module):
    """Single-layer LSTM with explicit parameters; batch-first sequences."""

    def __init__(self, input_size: int, hidden_size: int):
        super().__init__()
        self.input_size, self.hidden_size = int(input_size), int(hidden_size)
        self.weight_ih = torch.nn.Parameter(torch.empty(4 * hidden_size, input_size))
        self.weight_hh = torch.nn.Parameter(torch.empty(4 * hidden_size, hidden_size))
        self.bias_ih = torch.nn.Parameter(torch.empty(4 * hidden_size))
        self.bias_hh = torch.nn.Parameter(torch.empty(4 * hidden_size))
        self.reset_parameters()

    def reset_parameters(self) -> None:
        bound = 1.0 / math.sqrt(self.hidden_size)
        for parameter in (self.weight_ih, self.weight_hh, self.bias_ih, self.bias_hh):
            torch.nn.init.uniform_(parameter, -bound, bound)

    def step(self, x_t: torch.Tensor, h: torch.Tensor, c: torch.Tensor):
        """One timestep; returns (h_t, c_t, gates) with gates after activation."""
        raw = F.linear(x_t, self.weight_ih, self.bias_ih) + F.linear(h, self.weight_hh, self.bias_hh)
        i, f, g, o = raw.chunk(4, dim=-1)
        i, f, g, o = torch.sigmoid(i), torch.sigmoid(f), torch.tanh(g), torch.sigmoid(o)
        c_t = f * c + i * g
        h_t = o * torch.tanh(c_t)
        return h_t, c_t, {"i": i, "f": f, "g": g, "o": o}

    def forward(self, x: torch.Tensor, capture: bool = False):
        batch, steps, _ = x.shape
        h = x.new_zeros(batch, self.hidden_size)  # fresh zero state per window
        c = x.new_zeros(batch, self.hidden_size)
        hidden, inputs, forgets, memories = [], [], [], []
        for t in range(steps):
            h, c, gates = self.step(x[:, t], h, c)
            hidden.append(h)
            if capture:  # keep already-computed tensors only
                inputs.append(gates["i"])
                forgets.append(gates["f"])
                memories.append(c)
        sequence = torch.stack(hidden, dim=1)
        if not capture:
            return sequence
        return sequence, {"hidden": sequence, "input": torch.stack(inputs, dim=1),
                          "retention": torch.stack(forgets, dim=1), "memory": torch.stack(memories, dim=1)}


class AuditableMatchedLSTM(torch.nn.Module):
    """Linear(38,38) -> 3 encoder + 3 decoder auditable LSTM layers -> GELU -> Linear(38,38)."""

    def __init__(self, d: int = D, width: int = WIDTH):
        super().__init__()
        self.input_projection = torch.nn.Linear(d, width)
        self.encoder = torch.nn.ModuleList([AuditableLSTMLayer(width, width) for _ in range(3)])
        self.decoder = torch.nn.ModuleList([AuditableLSTMLayer(width, width) for _ in range(3)])
        self.gelu = torch.nn.GELU()
        self.output_projection = torch.nn.Linear(width, d)

    def forward(self, x: torch.Tensor, capture: bool = False):
        x = self.input_projection(x)
        traces: dict[str, dict[str, torch.Tensor]] = {}
        for name, layer in zip(LAYERS, (*self.encoder, *self.decoder)):
            if capture:
                x, traces[name] = layer(x, capture=True)
            else:
                x = layer(x)
        output = self.output_projection(self.gelu(x))
        return (output, traces) if capture else output


def build(seed: int, device: str = "cuda") -> AuditableMatchedLSTM:
    import real_data_r0_models as models

    models.seed_all(seed)
    model = AuditableMatchedLSTM(D, WIDTH)
    count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    if count != EXPECTED_PARAMETERS:
        raise r0data.ProtocolViolation(f"R0_V1_2_BLOCKED: auditable LSTM has {count} parameters, expected 74,100")
    return model.float().to(device)


def summarize(traces: dict[str, dict[str, torch.Tensor]]) -> torch.Tensor:
    """The frozen matched-LSTM common18 reduction (phase_f_lstm_observer.summarize, unchanged)."""
    from phase_f_lstm_observer import summarize as sealed_summarize

    return sealed_summarize(traces)


def extract_batch(model: AuditableMatchedLSTM, x: torch.Tensor):
    """One recurrence execution -> (reconstruction, score, common18); checks finiteness and gate range."""
    with torch.no_grad():
        output, traces = model(x, capture=True)
    for layer in traces.values():
        for key in TRACE_KEYS:
            if not bool(torch.isfinite(layer[key]).all()):
                raise r0data.ProtocolViolation("non-finite auditable LSTM trace")
        for key in ("input", "retention"):
            if not bool(((layer[key] >= 0) & (layer[key] <= 1)).all()):
                raise r0data.ProtocolViolation("auditable LSTM gate outside [0, 1]")
    score = (output - x).square().mean((1, 2))
    common18 = summarize(traces)
    if common18.shape != (x.shape[0], 18) or not bool(torch.isfinite(common18).all()) or not bool(torch.isfinite(score).all()):
        raise r0data.ProtocolViolation("invalid auditable LSTM score/common18")
    return output, score, common18


def extract_windows(model: AuditableMatchedLSTM, windows: np.ndarray, batch_size: int = 128) -> dict[str, np.ndarray]:
    """Observation-only extraction over independent W64 windows (no labels in the signature)."""
    import real_data_r0_models as models

    x = np.asarray(windows, dtype=np.float32)
    if x.ndim != 3 or x.shape[1:] != (W, D):
        raise r0data.ProtocolViolation("windows must be [n, 64, 38] float32")
    before = models.model_hash(model)
    device = next(model.parameters()).device
    scores, bases = [], []
    for left in range(0, len(x), batch_size):
        batch = torch.from_numpy(np.ascontiguousarray(x[left:left + batch_size])).to(device)
        _output, score, common18 = extract_batch(model, batch)
        scores.append(score.detach().cpu().numpy().astype(np.float64))
        bases.append(common18.detach().cpu().numpy().astype(np.float64))
    if models.model_hash(model) != before:
        raise r0data.ProtocolViolation("model mutated during extraction")
    return {"score": np.concatenate(scores), "internal_base18": np.concatenate(bases)}


class _ForbiddenNative:
    def __init__(self, *args: Any, **kwargs: Any):
        raise r0data.ProtocolViolation("native LSTM implementation forbidden in the r0-v1.2 scientific path")


def forbid_native_lstm() -> None:
    """Process-wide guard: any native LSTM construction or observer replay raises."""
    torch.nn.LSTM = _ForbiddenNative
    torch.nn.LSTMCell = _ForbiddenNative
    torch.nn.modules.rnn.LSTM = _ForbiddenNative
    torch.nn.modules.rnn.LSTMCell = _ForbiddenNative
    import phase_f_lstm_observer

    def replay(*args: Any, **kwargs: Any):
        raise r0data.ProtocolViolation("phase_f_lstm_observer.replay forbidden in the r0-v1.2 scientific path")

    phase_f_lstm_observer.replay = replay
