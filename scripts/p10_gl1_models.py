"""P10 G-L1 model zoo (sealed-candidate architectures).

Every recurrent forecaster exposes the same interface:
    init_state(B, device) -> state (tuple)
    forward(z, state) -> (pred, state)   # chunk-parallel where available
    step(z_t, state)  -> (pred_t, state) # exact reference recurrence
    state_norm(state) -> (B,) tensor
pred[:, t] is the one-step forecast of z[:, t+1] and depends only on z[:, :t+1]
(score-before-write: the observation z[:, t+1] is scored before it is written).

Architectures are fixed by ARCH below; do not change after seal.
"""
from __future__ import annotations

import math
import torch
import torch.nn as nn
import torch.nn.functional as F

ARCH = {
    "mlstm": dict(d=128, heads=4, dk=32, dv=32, chunk=64,
                  forget_gate="sigmoid", input_gate="sigmoid",
                  forget_bias_init=[3.0, 6.0], input_bias_init=0.0,
                  normalizer="max(|n.q|,1)", qk_norm="k scaled by 1/sqrt(dk)"),
    "gdeltanet": dict(d=128, heads=4, dk=32, dv=32, chunk=64,
                      alpha_gate="sigmoid", beta_gate="sigmoid",
                      alpha_bias_init=[3.0, 6.0], beta_bias_init=0.0, qk_norm="L2"),
    "titans": dict(d=128, dm=64, mem_hidden=192, chunk=16,
                   retrieval="memory at chunk start", grad="analytic, w.r.t. memory at chunk start",
                   eta_bias_init=2.0, theta_scale=0.1, theta_bias_init=0.0, alpha_bias_init=-5.0,
                   key_norm="L2", loss="mean squared ||M(k)-v||^2"),
    "lstm": dict(d=64, hidden=96, forget_bias_init=1.0),
    "window_only": dict(K=100, hidden_rule="floor((70000-C)/(K*C+1+C))"),
}


def _bias_linspace(n, lo, hi):
    return torch.linspace(lo, hi, n) if n > 1 else torch.tensor([lo])


class _Shell(nn.Module):
    """emb -> core -> residual+LayerNorm -> head; pred = z + head(h)."""

    def __init__(self, C, d, dout):
        super().__init__()
        self.C, self.d = C, d
        self.emb = nn.Linear(C, d)
        self.wo = nn.Linear(dout, d)
        self.ln = nn.LayerNorm(d)
        self.head = nn.Linear(d, C)

    def readout(self, z, x, o):
        return z + self.head(self.ln(x + self.wo(o)))


# ----------------------------------------------------------------------------- mLSTM
class MLSTM(_Shell):
    name = "mlstm"

    def __init__(self, C):
        a = ARCH["mlstm"]
        H, dk, dv, d = a["heads"], a["dk"], a["dv"], a["d"]
        super().__init__(C, d, H * dv)
        self.H, self.dk, self.dv, self.cs = H, dk, dv, a["chunk"]
        self.q = nn.Linear(d, H * dk)
        self.k = nn.Linear(d, H * dk)
        self.v = nn.Linear(d, H * dv)
        self.fg = nn.Linear(d, H)
        self.ig = nn.Linear(d, H)
        with torch.no_grad():
            self.fg.bias.copy_(_bias_linspace(H, *a["forget_bias_init"]))
            self.ig.bias.fill_(a["input_bias_init"])

    def init_state(self, B, device):
        return (torch.zeros(B, self.H, self.dv, self.dk, device=device),
                torch.zeros(B, self.H, self.dk, device=device))

    def _proj(self, x):
        B, T, _ = x.shape
        sh = lambda t, dd: t.view(B, T, self.H, dd).transpose(1, 2)  # B,H,T,dd
        q = sh(self.q(x), self.dk)
        k = sh(self.k(x), self.dk) / math.sqrt(self.dk)
        v = sh(self.v(x), self.dv)
        logf = F.logsigmoid(self.fg(x)).transpose(1, 2)  # B,H,T
        i = torch.sigmoid(self.ig(x)).transpose(1, 2)
        return q, k, v, logf, i

    @staticmethod
    def _chunk(q, k, v, logf, i, C0, n0):
        L = q.shape[2]
        cum = torch.cumsum(logf, -1)  # B,H,L
        diff = cum[..., :, None] - cum[..., None, :]
        mask = torch.ones(L, L, dtype=torch.bool, device=q.device).tril()
        G = torch.where(mask, torch.exp(diff.masked_fill(~mask, 0.0)), torch.zeros((), device=q.device))
        A = (q @ k.transpose(-1, -2)) * G * i[..., None, :]
        Fc = torch.exp(cum)[..., None]
        num = Fc * (q @ C0.transpose(-1, -2)) + A @ v
        den = Fc[..., 0] * (q * n0[..., None, :]).sum(-1) + A.sum(-1)
        h = num / torch.clamp(den.abs(), min=1.0)[..., None]
        w = torch.exp(cum[..., -1:] - cum) * i  # B,H,L
        C1 = torch.exp(cum[..., -1])[..., None, None] * C0 + torch.einsum("bhjv,bhjk->bhvk", v * w[..., None], k)
        n1 = torch.exp(cum[..., -1])[..., None] * n0 + (k * w[..., None]).sum(2)
        return h, C1, n1

    def forward(self, z, state):
        x = self.emb(z)
        q, k, v, logf, i = self._proj(x)
        C0, n0 = state
        outs = []
        for s in range(0, z.shape[1], self.cs):
            e = slice(s, s + self.cs)
            h, C0, n0 = self._chunk(q[:, :, e], k[:, :, e], v[:, :, e], logf[:, :, e], i[:, :, e], C0, n0)
            outs.append(h)
        h = torch.cat(outs, 2).transpose(1, 2).reshape(z.shape[0], z.shape[1], -1)
        return self.readout(z, x, h), (C0, n0)

    def step(self, z_t, state):
        x = self.emb(z_t[:, None])
        q, k, v, logf, i = self._proj(x)
        q, k, v, f, i = q[:, :, 0], k[:, :, 0], v[:, :, 0], torch.exp(logf[:, :, 0]), i[:, :, 0]
        C0, n0 = state
        C1 = f[..., None, None] * C0 + i[..., None, None] * v[..., :, None] * k[..., None, :]
        n1 = f[..., None] * n0 + i[..., None] * k
        num = (C1 @ q[..., None])[..., 0]
        den = (n1 * q).sum(-1)
        h = num / torch.clamp(den.abs(), min=1.0)[..., None]
        h = h.reshape(z_t.shape[0], 1, -1)
        return self.readout(z_t[:, None], x, h)[:, 0], (C1, n1)

    @staticmethod
    def state_norm(state):
        return state[0].flatten(1).norm(dim=1) + state[1].flatten(1).norm(dim=1)


# ----------------------------------------------------------------------------- Gated DeltaNet
class GDeltaNet(_Shell):
    name = "gdeltanet"

    def __init__(self, C):
        a = ARCH["gdeltanet"]
        H, dk, dv, d = a["heads"], a["dk"], a["dv"], a["d"]
        super().__init__(C, d, H * dv)
        self.H, self.dk, self.dv, self.cs = H, dk, dv, a["chunk"]
        self.q = nn.Linear(d, H * dk)
        self.k = nn.Linear(d, H * dk)
        self.v = nn.Linear(d, H * dv)
        self.ag = nn.Linear(d, H)
        self.bg = nn.Linear(d, H)
        with torch.no_grad():
            self.ag.bias.copy_(_bias_linspace(H, *a["alpha_bias_init"]))
            self.bg.bias.fill_(a["beta_bias_init"])

    def init_state(self, B, device):
        return (torch.zeros(B, self.H, self.dv, self.dk, device=device),)

    def _proj(self, x):
        B, T, _ = x.shape
        sh = lambda t, dd: t.view(B, T, self.H, dd).transpose(1, 2)
        q = F.normalize(sh(self.q(x), self.dk), dim=-1)
        k = F.normalize(sh(self.k(x), self.dk), dim=-1)
        v = sh(self.v(x), self.dv)
        loga = F.logsigmoid(self.ag(x)).transpose(1, 2)
        beta = torch.sigmoid(self.bg(x)).transpose(1, 2)
        return q, k, v, loga, beta

    @staticmethod
    def _chunk(q, k, v, loga, beta, S0):
        L = q.shape[2]
        dev = q.device
        cum = torch.cumsum(loga, -1)
        diff = cum[..., :, None] - cum[..., None, :]
        incl = torch.ones(L, L, dtype=torch.bool, device=dev).tril()
        G = torch.where(incl, torch.exp(diff.masked_fill(~incl, 0.0)), torch.zeros((), device=dev))
        gam = torch.exp(cum)  # B,H,L
        KK = k @ k.transpose(-1, -2)
        strict = torch.ones(L, L, dtype=torch.bool, device=dev).tril(-1)
        Lm = torch.where(strict, beta[..., :, None] * KK * G, torch.zeros((), device=dev))
        eye = torch.eye(L, device=dev)
        rhs = beta[..., None] * (v - gam[..., None] * (k @ S0.transpose(-1, -2)))
        U = torch.linalg.solve_triangular(eye + Lm, rhs, upper=False, unitriangular=True)
        O = gam[..., None] * (q @ S0.transpose(-1, -2)) + ((q @ k.transpose(-1, -2)) * G) @ U
        w = torch.exp(cum[..., -1:] - cum)
        S1 = torch.exp(cum[..., -1])[..., None, None] * S0 + torch.einsum("bhiv,bhik->bhvk", U * w[..., None], k)
        return O, S1

    def forward(self, z, state):
        x = self.emb(z)
        q, k, v, loga, beta = self._proj(x)
        (S0,) = state
        outs = []
        for s in range(0, z.shape[1], self.cs):
            e = slice(s, s + self.cs)
            o, S0 = self._chunk(q[:, :, e], k[:, :, e], v[:, :, e], loga[:, :, e], beta[:, :, e], S0)
            outs.append(o)
        o = torch.cat(outs, 2).transpose(1, 2).reshape(z.shape[0], z.shape[1], -1)
        return self.readout(z, x, o), (S0,)

    def step(self, z_t, state):
        x = self.emb(z_t[:, None])
        q, k, v, loga, beta = self._proj(x)
        q, k, v, a, b = q[:, :, 0], k[:, :, 0], v[:, :, 0], torch.exp(loga[:, :, 0]), beta[:, :, 0]
        (S0,) = state
        Sk = (S0 @ k[..., None])[..., 0]
        S1 = a[..., None, None] * (S0 - b[..., None, None] * Sk[..., :, None] * k[..., None, :]) \
            + b[..., None, None] * v[..., :, None] * k[..., None, :]
        o = (S1 @ q[..., None])[..., 0].reshape(z_t.shape[0], 1, -1)
        return self.readout(z_t[:, None], x, o)[:, 0], (S1,)

    @staticmethod
    def state_norm(state):
        return state[0].flatten(1).norm(dim=1)


# ----------------------------------------------------------------------------- Titans-style LMM
class Titans(_Shell):
    """Neural long-term memory M(k)=W2 silu(W1 k), updated at test time.

    Chunked semantics (fixed): tokens are grouped in chunks of b steps aligned to the
    start of each processed stream/window. Retrieval for every token of a chunk uses
    the memory at chunk start M0; per-token gradients g_t are taken w.r.t. M0;
    S_t = eta_t S_{t-1} - theta_t g_t ; M_t = (1-alpha_t) M_{t-1} + S_t ; at chunk end M0 <- M_b.
    State = (W1_0, W2_0, W1_run, W2_run, S1, S2, pos) with pos = position within chunk.
    """
    name = "titans"

    def __init__(self, C):
        a = ARCH["titans"]
        d, dm, hm = a["d"], a["dm"], a["mem_hidden"]
        super().__init__(C, d, dm)
        self.dm, self.hm, self.b = dm, hm, a["chunk"]
        self.q = nn.Linear(d, dm)
        self.k = nn.Linear(d, dm)
        self.v = nn.Linear(d, dm)
        self.eta = nn.Linear(d, 1)
        self.theta = nn.Linear(d, 1)
        self.alpha = nn.Linear(d, 1)
        self.theta_scale = a["theta_scale"]
        self.W1init = nn.Parameter(torch.randn(hm, dm) / math.sqrt(dm))
        self.W2init = nn.Parameter(torch.randn(dm, hm) / math.sqrt(hm))
        with torch.no_grad():
            self.eta.bias.fill_(a["eta_bias_init"])
            self.theta.bias.fill_(a["theta_bias_init"])
            self.alpha.bias.fill_(a["alpha_bias_init"])

    def init_state(self, B, device):
        W1 = self.W1init[None].expand(B, -1, -1).to(device)
        W2 = self.W2init[None].expand(B, -1, -1).to(device)
        z1 = torch.zeros(B, self.hm, self.dm, device=device)
        z2 = torch.zeros(B, self.dm, self.hm, device=device)
        return (W1, W2, W1, W2, z1, z2, 0)

    def _proj(self, x):
        q = F.normalize(self.q(x), dim=-1)
        k = F.normalize(self.k(x), dim=-1)
        v = self.v(x)
        eta = torch.sigmoid(self.eta(x))[..., 0]
        theta = self.theta_scale * torch.sigmoid(self.theta(x))[..., 0]
        alpha = torch.sigmoid(self.alpha(x))[..., 0]
        return q, k, v, eta, theta, alpha

    @staticmethod
    def _mem(W1, W2, u):  # u: B,T,dm
        a = torch.einsum("bhm,btm->bth", W1, u)
        return torch.einsum("bmh,bth->btm", W2, F.silu(a)), a

    def _grad_terms(self, W1, W2, k, v):
        out, a = self._mem(W1, W2, k)
        e = (out - v) * (2.0 / self.dm)  # B,T,dm
        s = F.silu(a)
        sig = torch.sigmoid(a)
        dsilu = sig * (1 + a * (1 - sig))
        r = torch.einsum("bmh,btm->bth", W2, e) * dsilu  # B,T,hm
        return e, s, r  # gW2_t = e_t s_t^T ; gW1_t = r_t k_t^T

    def _full_chunk(self, q, k, v, eta, theta, alpha, st):
        W1_0, W2_0, W1r, W2r, S1, S2, pos = st
        assert pos == 0
        y, _ = self._mem(W1_0, W2_0, q)
        e, s, r = self._grad_terms(W1_0, W2_0, k, v)
        b = q.shape[1]
        le, la = torch.log(eta), torch.log1p(-alpha)
        ce, ca = torch.cumsum(le, 1), torch.cumsum(la, 1)  # B,b
        Hb, Db = torch.exp(ce[:, -1]), torch.exp(ca[:, -1])
        # S_b = H_b S0 - sum_i (H_b/H_i) theta_i g_i
        wS = torch.exp(ce[:, -1:] - ce) * theta
        # M_b = D_b M0 + (sum_t D_b/D_t H_t) S0 - sum_i c_i theta_i g_i, c_i = sum_{t>=i} (D_b/D_t)(H_t/H_i)
        logDt = ca[:, -1:] - ca  # log D_b/D_t, B,b(t)
        mask = torch.ones(b, b, dtype=torch.bool, device=q.device).triu()  # i<=t
        expo = (logDt[:, None, :] + ce[:, None, :] - ce[:, :, None])  # B,i,t
        cmat = torch.where(mask, torch.exp(expo.masked_fill(~mask, 0.0)), torch.zeros((), device=q.device))
        c = cmat.sum(-1) * theta  # B,i
        s0coef = torch.exp(logDt + ce).sum(-1)  # B
        gw2 = lambda w: torch.einsum("bt,btm,bth->bmh", w, e, s)
        gw1 = lambda w: torch.einsum("bt,bth,btm->bhm", w, r, k)
        S1n = Hb[:, None, None] * S1 - gw1(wS)
        S2n = Hb[:, None, None] * S2 - gw2(wS)
        W1n = Db[:, None, None] * W1r + s0coef[:, None, None] * S1 - gw1(c)
        W2n = Db[:, None, None] * W2r + s0coef[:, None, None] * S2 - gw2(c)
        return y, (W1n, W2n, W1n, W2n, S1n, S2n, 0)

    def _step_core(self, q, k, v, eta, theta, alpha, st):
        W1_0, W2_0, W1r, W2r, S1, S2, pos = st
        y, _ = self._mem(W1_0, W2_0, q[:, None])
        e, s, r = self._grad_terms(W1_0, W2_0, k[:, None], v[:, None])
        g1 = r[:, 0, :, None] * k[:, None, :]
        g2 = e[:, 0, :, None] * s[:, 0, None, :]
        S1 = eta[:, None, None] * S1 - theta[:, None, None] * g1
        S2 = eta[:, None, None] * S2 - theta[:, None, None] * g2
        W1r = (1 - alpha)[:, None, None] * W1r + S1
        W2r = (1 - alpha)[:, None, None] * W2r + S2
        pos += 1
        if pos == self.b:
            W1_0, W2_0, pos = W1r, W2r, 0
        return y[:, 0], (W1_0, W2_0, W1r, W2r, S1, S2, pos)

    def forward(self, z, state):
        x = self.emb(z)
        q, k, v, eta, theta, alpha = self._proj(x)
        T = z.shape[1]
        ys, t, st = [], 0, state
        while t < T and st[6] != 0:  # finish a partial chunk step by step
            y, st = self._step_core(q[:, t], k[:, t], v[:, t], eta[:, t], theta[:, t], alpha[:, t], st)
            ys.append(y[:, None]); t += 1
        while t + self.b <= T:
            e = slice(t, t + self.b)
            y, st = self._full_chunk(q[:, e], k[:, e], v[:, e], eta[:, e], theta[:, e], alpha[:, e], st)
            ys.append(y); t += self.b
        while t < T:
            y, st = self._step_core(q[:, t], k[:, t], v[:, t], eta[:, t], theta[:, t], alpha[:, t], st)
            ys.append(y[:, None]); t += 1
        y = torch.cat(ys, 1)
        return self.readout(z, x, y), st

    def step(self, z_t, state):
        x = self.emb(z_t[:, None])
        q, k, v, eta, theta, alpha = self._proj(x)
        y, st = self._step_core(q[:, 0], k[:, 0], v[:, 0], eta[:, 0], theta[:, 0], alpha[:, 0], state)
        return self.readout(z_t[:, None], x, y[:, None])[:, 0], st

    @staticmethod
    def state_norm(state):
        return sum(state[i].flatten(1).norm(dim=1) for i in (2, 3, 4, 5))


# ----------------------------------------------------------------------------- LSTM
class LSTMF(nn.Module):
    name = "lstm"

    def __init__(self, C):
        super().__init__()
        a = ARCH["lstm"]
        self.C, self.hd = C, a["hidden"]
        self.emb = nn.Linear(C, a["d"])
        self.rnn = nn.LSTM(a["d"], a["hidden"], batch_first=True)
        self.ln = nn.LayerNorm(a["hidden"])
        self.head = nn.Linear(a["hidden"], C)
        with torch.no_grad():
            H = a["hidden"]
            for nm in ("bias_ih_l0", "bias_hh_l0"):
                b = getattr(self.rnn, nm); b.zero_(); b[H:2 * H].fill_(a["forget_bias_init"] / 2)

    def init_state(self, B, device):
        return (torch.zeros(1, B, self.hd, device=device), torch.zeros(1, B, self.hd, device=device))

    def forward(self, z, state):
        o, (h, c) = self.rnn(self.emb(z), state)
        return z + self.head(self.ln(o)), (h, c)

    def step(self, z_t, state):
        p, st = self.forward(z_t[:, None], state)
        return p[:, 0], st

    @staticmethod
    def state_norm(state):
        return state[0][0].norm(dim=1) + state[1][0].norm(dim=1)


# ----------------------------------------------------------------------------- window-only
class WindowOnly(nn.Module):
    name = "window_only"

    def __init__(self, C):
        super().__init__()
        K = ARCH["window_only"]["K"]
        h = (70000 - C) // (K * C + 1 + C)
        self.C, self.K, self.h = C, K, h
        self.net = nn.Sequential(nn.Linear(K * C, h), nn.ReLU(), nn.Linear(h, C))

    def forward_windows(self, W):  # W: N,K,C (last row = z_t) -> forecast of z_{t+1}
        return W[:, -1] + self.net(W.flatten(1))


MODELS = {"mlstm": MLSTM, "gdeltanet": GDeltaNet, "titans": Titans, "lstm": LSTMF,
          "window_only": WindowOnly, "mlstm_std": MLSTM}
RECURRENT = ("mlstm", "gdeltanet", "titans", "lstm", "mlstm_std")


def build(name, C):
    return MODELS[name](C)


def n_params(m):
    return sum(p.numel() for p in m.parameters() if p.requires_grad)


def state_detach(state):
    return tuple(s.detach() if torch.is_tensor(s) else s for s in state)


def state_select(model, state, idx):
    """Select batch rows idx (LSTM keeps its (1,B,H) layout; Titans pos int passes through)."""
    if isinstance(model, LSTMF):
        return tuple(s[:, idx] for s in state)
    return tuple(s[idx] if torch.is_tensor(s) else s for s in state)


def state_repeat(model, state, n):
    """Repeat a batch-1 state n times along batch."""
    if isinstance(model, LSTMF):
        return tuple(s.expand(-1, n, -1).contiguous() for s in state)
    return tuple(s.expand(n, *s.shape[1:]).contiguous() if torch.is_tensor(s) else s for s in state)


def state_cat(model, states):
    if isinstance(model, LSTMF):
        return tuple(torch.cat([st[j] for st in states], 1) for j in range(2))
    out = []
    for j in range(len(states[0])):
        if torch.is_tensor(states[0][j]):
            out.append(torch.cat([st[j] for st in states], 0))
        else:
            vals = {st[j] for st in states}
            assert len(vals) == 1, "cannot batch Titans states with different chunk positions"
            out.append(states[0][j])
    return tuple(out)
