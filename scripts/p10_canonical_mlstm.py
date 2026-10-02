"""Step 0 (P7+P10, issue #15): canonical mLSTM repair -- wrapper + state carry + parity.

Three explicitly named arms (do NOT conflate them in reports):

  mLSTMexp     canonical xLSTM mLSTM layer.  All parameters/sub-modules are the
               OFFICIAL ``xlstm.blocks.mlstm.layer.mLSTMLayer`` (xlstm 2.0.5):
               proj_up (factor 2) -> CausalConv1d(k=4)+SiLU -> headwise q/k
               (from conv branch) and v (from non-conv branch) -> cell
               (igate/fgate = Linear(3*inner, NH) on concat(q,k,v), exp input
               gate, sigmoid forget gate, normalizer + max-stabilizer) ->
               MultiHeadLayerNorm outnorm -> learnable_skip -> h * SiLU(z) ->
               proj_down.  The cell core runs through mlstm_kernels 2.0.5:
                 chunk  : mlstm_kernels.torch.chunkwise.native.mlstm_chunkwise__native_autograd
                 step   : mlstm_kernels.torch.recurrent.native_step.mlstm_recurrent_step__native
               Reference for parity: the official ``mLSTMLayer.step`` loop
               (xlstm backend ``recurrent_step_stabilized_simple``).

  mLSTMsig     TFLA sigmoid-input-gate mLSTM (Beck et al. 2025, arXiv:2503.14376):
               same official layer modules, cell core replaced by the official
               siging kernels of mlstm_kernels 2.0.5:
                 zero-state parallel (CPU/GPU): ...parallel.native_siging.mlstm_siging_parallel__native_autograd
                 stateful chunk (GPU/triton):   ...chunkwise.triton_xl_chunk_siging.mlstm_siging_chunkwise__xl_chunk
               plus a recurrent step written here (no official native siging
               step exists in 2.0.5) and verified against both kernels.
               ``normalize=False`` (default here) = paper definition (no n state,
               no m state; output NORM + output gate retained).  The library's own
               default is ``normalize=True`` (denominator max(|n.q|,1)).
               NOTE: the triton kernel's tl.dot runs fp32 inputs at TF32 precision
               (~1e-3 relative vs an fp64 recurrence); CPU/native paths are exact.

  mLSTM-sig+n  the historical G-L1 class ``p10_gl1_models.MLSTM`` (unchanged; it
               is not built here).  Its cell core equals the siging core with
               normalize=True, but it has no up-projection / conv / skip / output
               gate / head-norm / block -- kept only as a historical ablation.

State (continuable across calls; mlstm_kernels convention, k unscaled / q scaled), dict of tensors:
    conv : (B, KS-1, D_inner)   last KS-1 pre-conv inputs of the mLSTM branch
    C    : (B, NH, DH, DH)      mlstm_kernels convention (k v^T)
    n    : (B, NH, DH)
    m    : (B, NH, 1)           (zeros and unused for mLSTMsig)
"""
from __future__ import annotations

import importlib.metadata as _md
import math

import torch
import torch.nn as nn
from xlstm.blocks.mlstm.layer import mLSTMLayer, mLSTMLayerConfig
from xlstm.components.ln import LayerNorm as XLSTMLayerNorm
from mlstm_kernels.torch.chunkwise.native import mlstm_chunkwise__native_autograd
from mlstm_kernels.torch.recurrent.native_step import mlstm_recurrent_step__native
from mlstm_kernels.torch.parallel.native_siging import mlstm_siging_parallel__native_autograd

VERSIONS = {"xlstm": _md.version("xlstm"), "mlstm_kernels": _md.version("mlstm_kernels"),
            "torch": torch.__version__}
KERNELS = {
    "mLSTMexp": {"chunk": "mlstm_kernels.torch.chunkwise.native.mlstm_chunkwise__native_autograd",
                 "step": "mlstm_kernels.torch.recurrent.native_step.mlstm_recurrent_step__native",
                 "reference": "xlstm.blocks.mlstm.layer.mLSTMLayer.step (backend recurrent_step_stabilized_simple)"},
    "mLSTMsig": {"chunk_gpu": "mlstm_kernels.torch.chunkwise.triton_xl_chunk_siging.mlstm_siging_chunkwise__xl_chunk",
                 "parallel_zero_state": "mlstm_kernels.torch.parallel.native_siging.mlstm_siging_parallel__native_autograd",
                 "step": "p10_canonical_mlstm.siging_step (local; verified against both official kernels)"},
}


def siging_step(C, n, q, k, v, i, f, normalize=False, eps=1e-6):
    """One recurrent step of the sigmoid-input-gate mLSTM (TFLA mLSTMsig).

    C (B,NH,DK,DV), n (B,NH,DK), q/k (B,NH,DK), v (B,NH,DV), i/f (B,NH,1) pre-activations.
    C_t = sig(f) C + sig(i) k v^T ;  h = C_t^T q / sqrt(DK)  [/ (max(|n_t.q|/sqrt(DK), 1) + eps)]
    Matches mlstm_siging_parallel_fw / mlstm_siging_chunkwise__xl_chunk exactly.
    """
    DK = q.shape[-1]
    fa, ia = torch.sigmoid(f), torch.sigmoid(i)
    C = fa[..., None] * C + ia[..., None] * (k[..., :, None] * v[..., None, :])
    n = fa * n + ia * k if normalize else n      # n is not maintained when normalize=False
    qs = q * DK ** -0.5
    h = torch.einsum("bhk,bhkv->bhv", qs, C)
    if normalize:
        den = torch.maximum((n * qs).sum(-1, keepdim=True).abs(), torch.ones_like(fa))
        h = h / (den + eps)
    return h, C, n


class CanonicalMLSTMLayer(nn.Module):
    """Stateful, chunk-parallel wrapper around the official xlstm mLSTMLayer modules."""

    def __init__(self, d_model=128, num_heads=4, conv_kernel=4, qkv_blocksize=4, proj_factor=2.0,
                 context_length=512, variant="exp", sig_normalize=False, chunk_size=64,
                 sig_chunk_backend="auto", eps=1e-6):
        super().__init__()
        assert variant in ("exp", "sig")
        cfg = mLSTMLayerConfig(embedding_dim=d_model, num_heads=num_heads, conv1d_kernel_size=conv_kernel,
                               qkv_proj_blocksize=qkv_blocksize, proj_factor=proj_factor,
                               context_length=context_length)
        self.layer = mLSTMLayer(cfg)          # official modules + official init
        self.variant, self.sig_normalize, self.chunk_size, self.eps = variant, sig_normalize, chunk_size, eps
        self.sig_chunk_backend = sig_chunk_backend
        self.NH = num_heads
        self.D = cfg._inner_embedding_dim
        self.DH = self.D // num_heads
        self.KS = conv_kernel

    @property
    def arm(self):
        return "mLSTMexp" if self.variant == "exp" else "mLSTMsig"

    def init_state(self, B, device=None, dtype=torch.float32):
        z = lambda *s: torch.zeros(*s, device=device, dtype=dtype)
        return {"conv": z(B, self.KS - 1, self.D), "C": z(B, self.NH, self.DH, self.DH),
                "n": z(B, self.NH, self.DH), "m": z(B, self.NH, 1)}

    # ---------------------------------------------------------------- cell cores
    def _core_exp(self, q, k, v, i, f, st):
        S, L = q.shape[2], self.chunk_size
        C, n, m = st["C"], st["n"], st["m"]
        outs, Sf = [], (S // L) * L
        if Sf > 0:
            h, (C, n, m) = mlstm_chunkwise__native_autograd(
                q[:, :, :Sf], k[:, :, :Sf], v[:, :, :Sf], i[:, :, :Sf], f[:, :, :Sf],
                c_initial=C, n_initial=n, m_initial=m, return_last_states=True,
                eps=self.eps, chunk_size=L)
            outs.append(h)
        for t in range(Sf, S):   # remainder (S not a multiple of chunk_size): official native step
            h, (C, n, m) = mlstm_recurrent_step__native(
                q[:, :, t], k[:, :, t], v[:, :, t], i[:, :, t, None], f[:, :, t, None],
                C, n, m, eps=self.eps, dtype_state=torch.promote_types(q.dtype, torch.float32))
            outs.append(h[:, :, None])
        return torch.cat(outs, 2), {"C": C, "n": n, "m": m}

    def _core_sig(self, q, k, v, i, f, st):
        S = q.shape[2]
        C, n = st["C"], st["n"]
        use_triton = q.is_cuda and self.sig_chunk_backend in ("auto", "triton")
        outs, s0 = [], 0
        if use_triton:
            from mlstm_kernels.torch.chunkwise.triton_xl_chunk_siging import mlstm_siging_chunkwise__xl_chunk
            L = self.chunk_size
            Sf = (S // L) * L
            if Sf > 0:
                h, (C, n) = mlstm_siging_chunkwise__xl_chunk(
                    q[:, :, :Sf].contiguous(), k[:, :, :Sf].contiguous(), v[:, :, :Sf].contiguous(),
                    i[:, :, :Sf].contiguous(), f[:, :, :Sf].contiguous(),
                    c_initial=C.contiguous(), n_initial=n.contiguous(), return_last_states=True,
                    eps=self.eps, normalize=self.sig_normalize, chunk_size=L,
                    autocast_kernel_dtype=torch.float32)
                if not self.sig_normalize:
                    n = st["n"]               # kernel does not maintain n without normalizer; keep it inert
                outs.append(h)
                s0 = Sf
        for t in range(s0, S):   # CPU path / remainder: recurrent siging step
            h, C, n = siging_step(C, n, q[:, :, t], k[:, :, t], v[:, :, t], i[:, :, t, None],
                                  f[:, :, t, None], normalize=self.sig_normalize, eps=self.eps)
            outs.append(h[:, :, None])
        return torch.cat(outs, 2), {"C": C, "n": n, "m": st["m"]}

    # ---------------------------------------------------------------- layer
    def _qkv_gates(self, x, conv_state):
        L = self.layer
        B, S, _ = x.shape
        x_inner = L.proj_up(x)
        x_mlstm, z = torch.split(x_inner, self.D, dim=-1)
        x_conv = L.conv1d(x_mlstm, conv_state=conv_state)                  # official CausalConv1d
        new_conv = torch.cat([conv_state, x_mlstm], 1)[:, -(self.KS - 1):]
        x_act = L.conv_act_fn(x_conv)
        q, k, v = L.q_proj(x_act), L.k_proj(x_act), L.v_proj(x_mlstm)
        cell = L.mlstm_cell
        g = torch.cat([q, k, v], -1)
        i = cell.igate(g).transpose(1, 2)                                    # (B,NH,S)
        f = cell.fgate(g).transpose(1, 2)
        hv = lambda t: t.view(B, S, self.NH, self.DH).transpose(1, 2)        # (B,NH,S,DH)
        return hv(q), hv(k), hv(v), i, f, x_act, z, new_conv

    def _readout(self, h, x_act, z):
        L = self.layer
        B, NH, S, DH = h.shape
        h = L.mlstm_cell.outnorm(h).transpose(1, 2).reshape(B, S, -1)       # official head norm
        h = h + L.learnable_skip * x_act
        return L.dropout(L.proj_down(h * L.ogate_act_fn(z)))

    def forward(self, x, state=None):
        """x (B,S,d_model) -> y (B,S,d_model), new_state.  Exact continuation of `state`."""
        if state is None:
            state = self.init_state(x.shape[0], x.device, x.dtype)
        q, k, v, i, f, x_act, z, new_conv = self._qkv_gates(x, state["conv"])
        core = self._core_exp if self.variant == "exp" else self._core_sig
        h, st = core(q, k, v, i, f, state)
        st["conv"] = new_conv
        return self._readout(h, x_act, z), st

    # ---------------------------------------------------------------- state format bridges
    def to_official(self, st):
        """-> (mlstm_state, conv_state (B,KS,D)) for xlstm mLSTMLayer.step (which takes conv_state as a 1-tuple)."""
        # Convention difference: xlstm's backend scales k by 1/sqrt(DH) before writing,
        # mlstm_kernels scales q instead -> C_xlstm = C_kernels / sqrt(DH), n likewise.
        B, r = st["C"].shape[0], self.DH ** -0.5
        conv = torch.cat([st["conv"].new_zeros(B, 1, self.D), st["conv"]], 1)   # (B,KS,D); row 0 is rolled out
        return (st["C"] * r, st["n"][..., None] * r, st["m"][..., None]), conv

    def from_official(self, mlstm_state, conv_state):
        c, n, m = mlstm_state
        conv_state = conv_state[0] if isinstance(conv_state, tuple) else conv_state
        r = self.DH ** 0.5
        return {"conv": conv_state[:, 1:].clone(), "C": c * r, "n": n[..., 0] * r, "m": m[..., 0]}

    def official_step(self, x_t, st):
        """Reference: official xlstm mLSTMLayer.step (exp variant)."""
        assert self.variant == "exp"
        ms, cs = self.to_official(st)
        y, d = self.layer.step(x_t, mlstm_state=ms, conv_state=(cs.clone(),))   # official conv state is a 1-tuple
        return y, self.from_official(d["mlstm_state"], d["conv_state"])


class CanonicalMLSTMForecaster(nn.Module):
    """Time-series wrapper: z (B,T,C) -> one-step forecast (B,T,C) + continuable state.

    emb Linear(C,d) -> official-style pre-LN residual block x + mLSTMLayer(LN(x))
    -> LayerNorm -> head Linear(d,C);  pred = z + head(.)  (same shell convention as
    G-L1: pred[:, t] forecasts z[:, t+1] and depends only on z[:, :t+1]).
    """

    def __init__(self, C, d_model=128, variant="exp", **layer_kw):
        super().__init__()
        self.C, self.d = C, d_model
        self.emb = nn.Linear(C, d_model)
        self.ln_in = XLSTMLayerNorm(d_model, bias=False)   # official xlstm block norm
        self.core = CanonicalMLSTMLayer(d_model=d_model, variant=variant, **layer_kw)
        self.ln_out = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, C)
        self.name = self.core.arm

    def init_state(self, B, device=None):
        return self.core.init_state(B, device)

    def forward(self, z, state=None):
        x = self.emb(z)
        y, st = self.core(self.ln_in(x), state)
        return z + self.head(self.ln_out(x + y)), st

    def step(self, z_t, state):
        """z_t (B,C).  exp: official layer.step; sig: wrapper with S=1 (recurrent siging step)."""
        x = self.emb(z_t[:, None])
        if self.core.variant == "exp":
            y, st = self.core.official_step(self.ln_in(x), state)
        else:
            y, st = self.core(self.ln_in(x), state)
        return (z_t[:, None] + self.head(self.ln_out(x + y)))[:, 0], st

    @staticmethod
    def state_norm(st):
        return st["C"].flatten(1).norm(dim=1) + st["n"].flatten(1).norm(dim=1)
