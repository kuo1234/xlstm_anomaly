"""Fast, audit-free xLSTM sLSTM observer for engineering benchmarks.

This module is deliberately separate from :mod:`phase_e2_observer`.  The
original observer remains the scientific reference implementation.  The fast
observer captures the ``all_states`` tensor already produced by the CUDA
sLSTM cell and reconstructs only the gate traces needed by the frozen
common18 schema in one batched operation.  It performs no parity checks or
label/evaluator access.
"""
from __future__ import annotations

from typing import Callable

import torch
import torch.nn.functional as F

from phase_e2_schema import SCALAR_CELLS


def _cell_parameters(cell) -> tuple[torch.Tensor, torch.Tensor]:
    kernel = cell._recurrent_kernel_int2ext(cell._recurrent_kernel).detach()
    bias = cell._bias_int2ext(cell._bias).detach().permute(1, 0, 2)
    return kernel, bias


def state_and_gate_traces(
    internal_input: torch.Tensor,
    all_states: torch.Tensor,
    kernel: torch.Tensor,
    bias: torch.Tensor,
) -> dict[str, torch.Tensor]:
    """Convert one CUDA cell's native state history into observer traces.

    ``all_states`` has native shape ``[4, T+1, B, H]`` and contains
    ``h,c,n,m``.  The input is the post-permutation ``[T,B,N*G*D]`` tensor
    (the installed CUDA backend uses ``SBNGH``).  Gate reconstruction uses
    native prior hidden states and therefore does not replay the recurrent
    update or its temporal Python loop.
    """
    if internal_input.ndim != 3 or all_states.ndim != 4:
        raise ValueError("unexpected sLSTM input/state rank")
    _, T_plus_one, B, H = all_states.shape
    T = T_plus_one - 1
    N, _, G, D = kernel.shape
    if G != 4 or H != N * D:
        raise ValueError("unexpected sLSTM dimensions")
    if internal_input.shape != (T, B, N * G * D):
        raise ValueError(
            f"unexpected internal input shape {tuple(internal_input.shape)}"
        )

    # Native SBNGH layout -> the scalar_reference B,T,G,N,D layout.
    x = internal_input.reshape(T, B, N, G, D).permute(1, 0, 3, 2, 4)
    h_prev = all_states[0, :-1].permute(1, 0, 2).reshape(B, T, N, D)
    m_prev = all_states[3, :-1].permute(1, 0, 2).reshape(B, T, N, D)
    raw_recurrent = torch.einsum("btni,nigo->btngo", h_prev, kernel)
    raw = x + raw_recurrent.permute(0, 1, 3, 2, 4) + bias
    ir, fr, _zr, _orr = raw.unbind(2)
    fm = m_prev + F.logsigmoid(fr)
    if T:
        m = torch.cat((ir[:, :1], torch.maximum(ir[:, 1:], fm[:, 1:])), dim=1)
    else:
        m = ir
    one = torch.ones_like(ir)
    i = torch.minimum(torch.exp(ir - m), one)
    f = torch.minimum(torch.exp(fm - m), one)

    h = all_states[0, 1:].permute(1, 0, 2).reshape(B, T, N, D)
    c = all_states[1, 1:].permute(1, 0, 2).reshape(B, T, N, D)
    n = all_states[2, 1:].permute(1, 0, 2).reshape(B, T, N, D)
    u = c / n
    return {"hidden": h, "input": i, "retention": f, "memory": u}


def summarize_fast(traces: dict[str, dict[str, torch.Tensor]]) -> torch.Tensor:
    """The frozen common18 reduction without audit-only synchronization.

    This is intentionally a line-for-line semantic counterpart of
    ``phase_e2_schema.summarize``.  Shape/finiteness/schema checks belong to
    the reference/canary observer, not the hot extraction path.
    """
    layers = []
    for cell in SCALAR_CELLS:
        layer = traces[cell]
        shape = layer["hidden"].shape
        cols = []
        for name in ("hidden", "input", "retention", "memory"):
            sequence = layer[name]
            value = sequence[:, -1]
            previous = sequence[:, -2] if shape[1] > 1 else torch.zeros_like(value)
            cols.extend([value.mean(-1), value.std(-1, correction=0)])
            if name in ("input", "retention"):
                cols.extend(
                    [
                        torch.quantile(value, 0.1, dim=-1),
                        torch.quantile(value, 0.9, dim=-1),
                        (value - previous).mean(-1),
                    ]
                )
            else:
                cols.append(value.square().mean(-1).sqrt())
                cols.append(
                    (value - previous).square().mean(-1).sqrt()
                    if name == "hidden"
                    else torch.linalg.vector_norm(value - previous, dim=-1)
                    / (torch.linalg.vector_norm(previous, dim=-1) + 1e-8)
                )
        layers.append(torch.stack(cols, -1).mean(1))
    return torch.stack(layers).mean(0)


class FastStateObserver:
    """Capture native CUDA states and build exact common18 traces."""

    def __init__(self, model: torch.nn.Module):
        self.model = model
        self.handles: list[tuple[object, Callable]] = []
        self.latest: dict[str, dict[str, torch.Tensor]] = {}

    def __enter__(self):
        cells = {n: m for n, m in self.model.named_modules() if n.endswith("slstm_cell")}
        if set(cells) != set(SCALAR_CELLS):
            raise ValueError("Unexpected actual scalar-cell schema")
        for name, cell in cells.items():
            if getattr(getattr(cell, "config", None), "backend", None) != "cuda" or getattr(
                cell, "internal_input_shape", None
            ) != "SBNGH":
                raise ValueError("fast observer requires the validated CUDA SBNGH sLSTM backend")
            original = cell._impl

            def wrapped(training, internal_input, state, _original=original, _name=name, _cell=cell):
                all_states = _original(training, internal_input, state)
                # Only state history and immutable native inputs are retained;
                # no values are copied to CPU and no parity check is performed.
                kernel, bias = _cell_parameters(_cell)
                self.latest[_name] = state_and_gate_traces(
                    internal_input, all_states, kernel, bias
                )
                return all_states

            cell._impl = wrapped
            self.handles.append((cell, original))
        return self

    def __exit__(self, *exc):
        for cell, original in self.handles:
            cell._impl = original
        self.handles.clear()

    def summary(self) -> torch.Tensor:
        return summarize_fast(self.latest)


def extract_fast(model: torch.nn.Module, x: torch.Tensor):
    """Return score/common18 using native states and vectorized gate recovery."""
    with torch.no_grad(), FastStateObserver(model) as observer:
        output = model(x)
        features = observer.summary()
    return (output - x).square().mean((1, 2)), features
