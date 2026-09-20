"""Read-only mLSTM state replay and compact feature summaries.

The pinned xlstm 2.0.5 parallel mLSTM backend returns only normalized hidden
output; it does not expose C/n/m histories.  This module captures q/k/v at the
two actual mLSTM cells and replays the documented recurrent update from zero
state.  It never receives labels or evaluator metadata and never mutates model
parameters or outputs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import torch
import torch.nn.functional as F


MLSTM_CELLS = (
    "encoder.blocks.2.xlstm.mlstm_cell",
    "decoder.blocks.2.xlstm.mlstm_cell",
)
ATOL = 1e-5
RTOL = 1e-4
EPS = 1e-6


def _cell_replay(cell: torch.nn.Module, q: torch.Tensor, k: torch.Tensor, v: torch.Tensor) -> dict[str, torch.Tensor]:
    """Replay the pinned recurrent equations over one independent window."""
    if q.ndim != 3 or k.shape != q.shape or v.shape != q.shape:
        raise ValueError("mLSTM q/k/v must be B,T,H tensors")
    B, T, H = q.shape
    N = int(cell.config.num_heads)
    DH = H // N
    if H != N * DH or DH != 20:
        raise ValueError(f"unexpected mLSTM dimensions H={H}, heads={N}, DH={DH}")
    gate_input = torch.cat((q, k, v), dim=-1)
    igate = cell.igate(gate_input).transpose(-1, -2).unsqueeze(-1)
    fgate = cell.fgate(gate_input).transpose(-1, -2).unsqueeze(-1)
    qh = q.reshape(B, T, N, DH).transpose(1, 2)
    kh = k.reshape(B, T, N, DH).transpose(1, 2)
    vh = v.reshape(B, T, N, DH).transpose(1, 2)
    c = q.new_zeros((B, N, DH, DH))
    n = q.new_zeros((B, N, DH, 1))
    m = q.new_zeros((B, N, 1, 1))
    c_hist: list[torch.Tensor] = []
    n_hist: list[torch.Tensor] = []
    m_hist: list[torch.Tensor] = []
    h_hist: list[torch.Tensor] = []
    for t in range(T):
        log_f = F.logsigmoid(fgate[:, :, t]).unsqueeze(-1)
        i_pre = igate[:, :, t].unsqueeze(-1)
        m_new = torch.maximum(log_f + m, i_pre)
        f = torch.exp(log_f + m - m_new)
        i = torch.exp(i_pre - m_new)
        k_scaled = kh[:, :, t].unsqueeze(-1) / (DH**0.5)
        v_row = vh[:, :, t].unsqueeze(-2)
        c = f * c + i * (k_scaled @ v_row)
        n = f * n + i * k_scaled
        q_row = qh[:, :, t].unsqueeze(-2)
        h_num = q_row @ c
        qn = q_row @ n
        denom = torch.maximum(qn.abs(), torch.exp(-m_new)) + EPS
        h = h_num / denom
        c_hist.append(c)
        n_hist.append(n)
        m_hist.append(m_new)
        h_hist.append(h.squeeze(-2))
        m = m_new
    return {
        "c": torch.stack(c_hist, dim=2),  # B,N,T,DH,DH
        "n": torch.stack(n_hist, dim=2),  # B,N,T,DH,1
        "m": torch.stack(m_hist, dim=2),  # B,N,T,1,1
        "hidden": torch.stack(h_hist, dim=2),  # B,N,T,DH
    }


def _matrix_entropy(c: torch.Tensor) -> torch.Tensor:
    singular = torch.linalg.svdvals(c)
    total = singular.sum(-1)
    p = singular / (total.unsqueeze(-1) + 1e-8)
    return -(p * torch.log(p + 1e-8)).sum(-1) / torch.log(c.new_tensor(float(c.shape[-1])))


def _summarize_cell(trace: dict[str, torch.Tensor]) -> torch.Tensor:
    c = trace["c"][:, :, -1]
    c_prev = trace["c"][:, :, -2] if trace["c"].shape[2] > 1 else torch.zeros_like(c)
    n = trace["n"][:, :, -1, :, 0]
    n_prev = trace["n"][:, :, -2, :, 0] if trace["n"].shape[2] > 1 else torch.zeros_like(n)
    m = trace["m"][:, :, -1, :, :].squeeze(-1).squeeze(-1)
    m_prev = trace["m"][:, :, -2, :, :].squeeze(-1).squeeze(-1) if trace["m"].shape[2] > 1 else torch.zeros_like(m)
    h = trace["hidden"][:, :, -1]
    h_prev = trace["hidden"][:, :, -2] if trace["hidden"].shape[2] > 1 else torch.zeros_like(h)

    h_cols = (
        h.mean(-1), h.std(-1, correction=0), h.square().mean(-1).sqrt(),
        (h - h_prev).square().mean(-1).sqrt(),
    )
    c_flat = c.flatten(-2)
    c_prev_flat = c_prev.flatten(-2)
    c_frob = torch.linalg.vector_norm(c_flat, dim=-1)
    c_rel = torch.linalg.vector_norm(c_flat - c_prev_flat, dim=-1) / (torch.linalg.vector_norm(c_prev_flat, dim=-1) + 1e-8)
    singular = torch.linalg.svdvals(c)
    c_sum = singular.sum(-1)
    c_cols = (
        c.mean((-1, -2)), c.std((-1, -2), correction=0), c_frob, c_rel,
        singular[..., 0] / (c_sum + 1e-8), _matrix_entropy(c),
    )
    n_cols = (
        n.mean(-1), n.std(-1, correction=0), n.square().mean(-1).sqrt(),
        (n - n_prev).square().mean(-1).sqrt(),
    )
    # m is already scalar per head.  Its four summaries are explicitly
    # computed across the four heads (there is no within-head width axis).
    m_cols = (
        m.mean(1), m.std(1, correction=0), m.square().mean(1).sqrt(),
        (m - m_prev).mean(1),
    )
    # All other tuples are [B,heads]; equal head pooling is explicit and fixed.
    pooled = [value.mean(1) for value in (*h_cols, *c_cols, *n_cols)]
    return torch.stack((*pooled, *m_cols), dim=-1)


def summarize_mlstm(traces: dict[str, dict[str, torch.Tensor]]) -> torch.Tensor:
    if set(traces) != set(MLSTM_CELLS):
        raise ValueError("both actual encoder/decoder mLSTM cells are required")
    cells = [_summarize_cell(traces[name]) for name in MLSTM_CELLS]
    result = torch.stack(cells, dim=0).mean(0)
    if result.shape[1] != 18 or not bool(torch.isfinite(result).all()):
        raise RuntimeError("invalid mLSTM base feature summary")
    return result


def expand_mlstm_history(base: torch.Tensor, widths: tuple[int, ...] = (4, 8, 16, 32)) -> torch.Tensor:
    """Feature-major causal mean/std/slope expansion, returning B,T,234."""
    if base.ndim != 3 or base.shape[-1] != 18:
        raise ValueError("expected B,T,18 mLSTM base")
    B, T, Fdim = base.shape
    columns = []
    for j in range(Fdim):
        value = base[:, :, j]
        columns.append(value)
        for width in widths:
            if T < width:
                columns.extend([value.new_full((B, T), float("nan"))] * 3)
                continue
            unfolded = value.unfold(1, width, 1)
            t = torch.arange(width, device=value.device, dtype=value.dtype)
            t = t - t.mean()
            pad = value.new_full((B, width - 1), float("nan"))
            mean = unfolded.mean(-1)
            std = unfolded.std(-1, correction=0)
            slope = (unfolded * t).sum(-1) / t.square().sum()
            columns.extend([torch.cat((pad, item), dim=1) for item in (mean, std, slope)])
    return torch.stack(columns, dim=-1)


@dataclass
class Capture:
    model: torch.nn.Module
    latest: dict[str, dict[str, torch.Tensor]] = field(default_factory=dict)
    native_outputs: dict[str, torch.Tensor] = field(default_factory=dict)
    handles: list[Any] = field(default_factory=list)

    def __enter__(self):
        cells = dict(self.model.named_modules())
        if set(name for name in cells if name in MLSTM_CELLS) != set(MLSTM_CELLS):
            raise ValueError("model does not contain exactly the pinned mLSTM cells")
        for name in MLSTM_CELLS:
            cell = cells[name]

            def hook(module, args, kwargs, output, _name=name, _cell=cell):
                q, k, v = kwargs["q"], kwargs["k"], kwargs["v"]
                trace = _cell_replay(_cell, q.detach(), k.detach(), v.detach())
                self.latest[_name] = {key: value.detach() for key, value in trace.items()}
                self.native_outputs[_name] = output.detach()

            self.handles.append(cell.register_forward_hook(hook, with_kwargs=True))
        return self

    def __exit__(self, *exc):
        for handle in self.handles:
            handle.remove()
        self.handles.clear()

    def summary(self) -> torch.Tensor:
        return summarize_mlstm(self.latest)


def extract(model: torch.nn.Module, observations: torch.Tensor, check_mutation: bool = True) -> dict[str, Any]:
    """Observation-only output, state traces, and compact mLSTM features."""
    if observations.ndim != 3 or observations.shape[-1] != 8:
        raise ValueError("expected B,W,8 observation windows")
    before = {name: value.detach().clone() for name, value in model.state_dict().items()} if check_mutation else None
    with torch.no_grad(), Capture(model) as observer:
        output = model(observations)
        summary = observer.summary()
        traces = {
            cell: {name: value.clone() for name, value in layer.items()}
            for cell, layer in observer.latest.items()
        }
        native_outputs = {cell: value.clone() for cell, value in observer.native_outputs.items()}
    if check_mutation:
        after = {name: value.detach() for name, value in model.state_dict().items()}
        if any(not torch.equal(before[name], after[name]) for name in before):
            raise RuntimeError("mLSTM observer mutated model parameters/state")
    replay_outputs = {}
    for cell in MLSTM_CELLS:
        replay_h = traces[cell]["hidden"].permute(0, 2, 1, 3).reshape(observations.shape[0], observations.shape[1], -1)
        # outnorm is applied by the native cell after its parallel backend.
        replay_outputs[cell] = dict(replay_h=replay_h)
    return {
        "output": output.detach().clone(),
        "score": (output - observations).square().mean((1, 2)).detach().clone(),
        "base": summary.detach().clone(),
        "traces": traces,
        "native_outputs": native_outputs,
        "replay_outputs": replay_outputs,
    }
