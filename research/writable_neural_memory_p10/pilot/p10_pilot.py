"""P10/T1 exploratory, label-blind CPU scale pilot (NOT a sealed gate).
Uses ONLY SMD *_train.txt.  Never opens *_test.txt / *_test_label.txt.
Usage: python p10_pilot.py <machine-1-4|machine-2-1> <outdir> [quick]
"""
import sys, time, json, os
import numpy as np, pandas as pd, torch, torch.nn as nn, torch.nn.functional as F

import os as _os
D = _os.environ.get('SMD_DIR', 'data/external_real/smd/')  # was a local absolute path in the exploratory run (xlstm_anomaly-realdata worktree)
HID, DK, DV, DM, KW = 64, 16, 16, 16, 8
PRE, L, POST = 300, 30, 10
DELTAS = [1, 4, 16, 64, 256, 1024]
SKIP, WRITE, DECAY = 0, 1, 2
MODELS = ['window_only', 'lstm', 'mlstm', 'gdeltanet', 'titans', 'knn_append']
NO_DECAY = {'window_only', 'lstm', 'knn_append'}   # F-decay not defined

# ---------------------------------------------------------------- data
def load(machine):
    assert machine in ('machine-1-4', 'machine-2-1')
    X = np.loadtxt(D + machine + '_train.txt', delimiter=',')     # TRAIN ONLY
    n = len(X); nfit = n // 2
    fit = X[:nfit]
    keep = fit.std(0) >= 1e-3
    mu = fit[:, keep].mean(0); sd = np.maximum(fit[:, keep].std(0), 0.02)
    Z = ((X[:, keep] - mu) / sd).astype(np.float32)
    Zfit, Zs = Z[:nfit], Z[nfit:]
    u = np.maximum(np.diff(Zfit, axis=0).std(0), 0.05).astype(np.float32)   # one-step innovation scale
    return Zfit, Zs, u, int(keep.sum()), n

# ---------------------------------------------------------------- models
class Head(nn.Module):
    def __init__(s, d, r):
        super().__init__(); s.f = nn.Sequential(nn.Linear(d + r, HID), nn.GELU(), nn.Linear(HID, d))
    def forward(s, z, r): return z + s.f(torch.cat([z, r], -1))

def l2n(x): return x / (x.norm(dim=-1, keepdim=True) + 1e-6)

class WindowOnly(nn.Module):
    name = 'window_only'
    def __init__(s, d):
        super().__init__(); s.d = d
        s.f = nn.Sequential(nn.Linear(KW * d, 128), nn.GELU(), nn.Linear(128, d))
    def init_state(s, B): return [torch.zeros(B, KW, s.d)]
    def step(s, st, zp, z, g):
        buf = torch.cat([st[0][:, 1:], z[:, None]], 1)
        return [buf], z + s.f(buf.flatten(1))

class LSTM(nn.Module):
    name = 'lstm'
    def __init__(s, d):
        super().__init__(); s.cell = nn.LSTMCell(d, HID); s.head = Head(d, HID)
    def init_state(s, B): return [torch.zeros(B, HID), torch.zeros(B, HID)]
    def step(s, st, zp, z, g):
        h, c = s.cell(z, (st[0], st[1])); return [h, c], s.head(z, h)

class MLSTM(nn.Module):
    name = 'mlstm'
    def __init__(s, d):
        super().__init__()
        s.k = nn.Linear(d, DK); s.v = nn.Linear(d, DV); s.q = nn.Linear(d, DK)
        s.gf = nn.Linear(d, 1); s.gi = nn.Linear(d, 1); s.og = nn.Linear(d, DV)
        nn.init.constant_(s.gf.bias, 3.0); nn.init.constant_(s.gi.bias, 0.0)
        s.head = Head(d, DV)
    def init_state(s, B): return [torch.zeros(B, DV, DK), torch.zeros(B, DK)]
    def step(s, st, zp, z, g):
        C, n = st
        k = l2n(s.k(zp)); v = s.v(z); q = l2n(s.q(z))
        f = torch.sigmoid(s.gf(z)); i = torch.sigmoid(s.gi(z)) * g[:, None]
        C = f[:, :, None] * C + i[:, :, None] * v[:, :, None] * k[:, None, :]
        n = f * n + i * k
        den = torch.clamp((n * q).sum(-1, keepdim=True).abs(), min=1.0)
        r = torch.sigmoid(s.og(z)) * (C @ q[:, :, None]).squeeze(-1) / den
        return [C, n], s.head(z, r)

class GDeltaNet(nn.Module):
    name = 'gdeltanet'
    def __init__(s, d):
        super().__init__()
        s.k = nn.Linear(d, DK); s.v = nn.Linear(d, DV); s.q = nn.Linear(d, DK)
        s.ga = nn.Linear(d, 1); s.gb = nn.Linear(d, 1)
        nn.init.constant_(s.ga.bias, 4.0); nn.init.constant_(s.gb.bias, -1.0)
        s.head = Head(d, DV)
    def init_state(s, B): return [torch.zeros(B, DV, DK)]
    def step(s, st, zp, z, g):
        S = st[0]
        k = l2n(s.k(zp)); v = s.v(z); q = l2n(s.q(z))
        a = torch.sigmoid(s.ga(z))[:, :, None]; b = (torch.sigmoid(s.gb(z)) * g[:, None])[:, :, None]
        Sk = (S @ k[:, :, None])                                   # (B,DV,1)
        S = a * (S - b * Sk @ k[:, None, :]) + b * v[:, :, None] * k[:, None, :]
        r = (S @ q[:, :, None]).squeeze(-1)
        return [S], s.head(z, r)

class Titans(nn.Module):
    """Neural memory M(k)=W2 tanh(W1 k); test-time update by grad of ||M(k)-v||^2 with momentum eta, decay alpha."""
    name = 'titans'
    def __init__(s, d):
        super().__init__()
        s.k = nn.Linear(d, DK); s.v = nn.Linear(d, DV); s.q = nn.Linear(d, DK)
        s.W1 = nn.Parameter(torch.randn(DM, DK) * 0.3); s.W2 = nn.Parameter(torch.randn(DV, DM) * 0.2)
        s.gth = nn.Linear(d, 1); s.get = nn.Linear(d, 1); s.gal = nn.Linear(d, 1)
        nn.init.constant_(s.gth.bias, -1.0); nn.init.constant_(s.get.bias, 1.5); nn.init.constant_(s.gal.bias, -2.0)
        s.head = Head(d, DV)
    def init_state(s, B):
        return [s.W1.detach()[None].repeat(B, 1, 1) if not s.training else s.W1[None].expand(B, -1, -1),
                s.W2.detach()[None].repeat(B, 1, 1) if not s.training else s.W2[None].expand(B, -1, -1),
                torch.zeros(B, DM, DK), torch.zeros(B, DV, DM)]
    def step(s, st, zp, z, g):
        W1, W2, m1, m2 = st
        k = l2n(s.k(zp)); v = s.v(z); q = l2n(s.q(z))
        h = torch.tanh((W1 @ k[:, :, None]).squeeze(-1))           # (B,DM)
        err = (W2 @ h[:, :, None]).squeeze(-1) - v                 # (B,DV)
        gW2 = 2 * err[:, :, None] * h[:, None, :] / DM
        dh = (W2.transpose(1, 2) @ (2 * err)[:, :, None]).squeeze(-1) * (1 - h * h) / DM
        gW1 = dh[:, :, None] * k[:, None, :]
        th = 0.3 * torch.sigmoid(s.gth(z))[:, :, None] * g[:, None, None]
        et = torch.sigmoid(s.get(z))[:, :, None]; al = 0.1 * torch.sigmoid(s.gal(z))[:, :, None]
        m1 = et * m1 - th * gW1; m2 = et * m2 - th * gW2
        W1 = (1 - al) * W1 + m1; W2 = (1 - al) * W2 + m2
        hq = torch.tanh((W1 @ q[:, :, None]).squeeze(-1))
        r = (W2 @ hq[:, :, None]).squeeze(-1)
        return [W1, W2, m1, m2], s.head(z, r)

CLS = {'window_only': WindowOnly, 'lstm': LSTM, 'mlstm': MLSTM, 'gdeltanet': GDeltaNet, 'titans': Titans}

def train_model(name, Ztr, u, d, iters, seed=0, log=print):
    torch.manual_seed(seed); np.random.seed(seed)
    m = CLS[name](d); m.train()
    opt = torch.optim.Adam(m.parameters(), lr=2e-3)
    w = torch.tensor((1 / u ** 2) / np.mean(1 / u ** 2))
    Zt = torch.tensor(Ztr); T = 128; Bn = 32
    t0 = time.time()
    for it in range(iters):
        idx = np.random.randint(0, len(Zt) - T - 2, Bn)
        zs = torch.stack([Zt[i:i + T + 1] for i in idx])
        st = m.init_state(Bn); loss = 0.0; zp = zs[:, 0]
        for t in range(T):
            st, yh = m.step(st, zp, zs[:, t], torch.ones(Bn)); zp = zs[:, t]
            if t >= 8: loss = loss + (((yh - zs[:, t + 1]) ** 2) * w).mean()
        loss = loss / (T - 8)
        opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(m.parameters(), 1.0); opt.step()
        if it % 50 == 0 or it == iters - 1: log(f'  train {name} it{it} loss={loss.item():.4f} t={time.time()-t0:.0f}s')
    m.eval(); return m

class KNN:
    name = 'knn_append'
    def __init__(s, Zfit, stride=2):
        n = len(Zfit)
        W = np.stack([Zfit[i:i + KW].reshape(-1) for i in range(0, n - KW + 1, stride)])
        s.bank = torch.tensor(W); s.bn = (s.bank ** 2).sum(1); s.F = W.shape[1]
        s.sigma = None
    @torch.no_grad()
    def run(s, Z, mode, return_pred=False):
        B, T, d = Z.shape
        app = torch.zeros(B, T, s.F); valid = torch.zeros(B, T, dtype=torch.bool)
        appn = torch.zeros(B, T)
        sc = torch.full((B, T), float('nan'))
        for t in range(KW - 1, T):
            w = Z[:, t - KW + 1:t + 1].reshape(B, -1); wn = (w ** 2).sum(1)
            d0 = (wn[:, None] + s.bn[None] - 2 * w @ s.bank.T).min(1).values
            best = d0
            hi = t - KW + 1                                     # exclusion zone: windows appended within last KW steps
            if hi > 0:
                dd = appn[:, :hi] + wn[:, None] - 2 * torch.einsum('bf,btf->bt', w, app[:, :hi, :])
                dd = torch.where(valid[:, :hi], dd, torch.full_like(dd, float('inf')))
                best = torch.minimum(d0, dd.min(1).values)
            sc[:, t] = best.clamp(min=0) / s.F
            wr = mode[:, t] == WRITE
            if wr.any():
                app[wr, t] = w[wr]; appn[wr, t] = wn[wr]; valid[wr, t] = True
        return sc

@torch.no_grad()
def run(model, Z, mode, return_pred=False):
    """Z (B,T,d) tensor, mode (B,T) long: 0 skip(freeze state) 1 write 2 decay-only. score[t] for z_t uses state written through z_{t-1}."""
    if isinstance(model, KNN): return model.run(Z, mode)
    B, T, d = Z.shape
    st = model.init_state(B); zl = Z[:, 0].clone()
    sc = torch.full((B, T), float('nan')); yh = None
    P = torch.zeros(B, T, d) if return_pred else None
    for t in range(T):
        z = Z[:, t]
        if yh is not None:
            sc[:, t] = (((z - yh) / model.sigma) ** 2).mean(-1)
            if return_pred: P[:, t] = yh
        m = mode[:, t]
        stn, yh = model.step(st, zl, z, (m == WRITE).float())
        hold = (m == SKIP)
        st = [torch.where(hold.view(-1, *[1] * (a.dim() - 1)), a, b) for a, b in zip(st, stn)]
        zl = torch.where(hold[:, None], zl, z)
    return (sc, P) if return_pred else sc

@torch.no_grad()
def run_reset(model, Z, Wn=64):
    """Per-window reset: fresh state every Wn steps (kNN: static bank, no appends)."""
    B, T, d = Z.shape
    if isinstance(model, KNN):
        return model.run(Z, torch.zeros(B, T, dtype=torch.long))
    Zw = Z.reshape(B * T // Wn, Wn, d)
    sc = run(model, Zw, torch.ones(Zw.shape[:2], dtype=torch.long))
    return sc.reshape(B, T)

def calibrate(model, Zfit):
    n = len(Zfit); Zc = torch.tensor(Zfit[int(.8 * n):]); nch = len(Zc) // 590
    Zb = torch.stack([Zc[i * 590:(i + 1) * 590] for i in range(nch)])
    d = Zb.shape[-1]
    model.sigma = torch.ones(d)
    with torch.no_grad():
        st = model.init_state(nch); zl = Zb[:, 0]; res = []; yh = None
        for t in range(590):
            if yh is not None and t >= 64: res.append(Zb[:, t] - yh)
            st, yh = model.step(st, zl, Zb[:, t], torch.ones(nch)); zl = Zb[:, t]
    r = torch.cat(res)
    model.sigma = r.std(0).clamp(min=0.05)

# ---------------------------------------------------------------- injection
def make_spec(kind, amp, p, d, nch=5, seed_off=0):
    rng = np.random.RandomState(1000 * p + seed_off + 7)
    ch = rng.choice(d, nch if kind == 'spike' else 6, replace=False)
    sp = dict(kind=kind, ch=ch, amp=amp, tau=int(rng.randint(3000, 6000)))
    if kind == 'spike': sp['pat'] = (rng.rand(L, nch) < 0.5) * rng.choice([-1., 1.], (L, nch))
    return sp

def inject(z, start, sp, sabs, Zs, u):
    """modify z (T,d) in place; return injected delta (L,d)."""
    d0 = z[start:start + L].copy()
    ch = sp['ch']
    if sp['kind'] == 'spike':
        z[start:start + L][:, ch] += sp['amp'] * u[ch] * sp['pat']
    elif sp['kind'] == 'corr':
        idx = (sabs + start + np.arange(L) + sp['tau']) % len(Zs)
        z[start:start + L][:, ch] = Zs[idx][:, ch]
    elif sp['kind'] == 'stuck':
        z[start:start + L][:, ch] = z[start - 1][ch]
    return z[start:start + L] - d0

def sim_variant(sp1, variant, d, rng):
    """A2 spec derived from A1 spec (spike family)."""
    sp = dict(sp1); n = len(sp1['ch'])
    if variant.startswith('amp'): sp['amp'] = sp1['amp'] * float(variant[3:])
    elif variant == 'ch_overlap0':
        pool = np.setdiff1d(np.arange(d), sp1['ch']); sp['ch'] = rng.choice(pool, n, replace=False)
    elif variant == 'ch_overlap50':
        pool = np.setdiff1d(np.arange(d), sp1['ch'])
        sp['ch'] = np.concatenate([sp1['ch'][:n // 2], rng.choice(pool, n - n // 2, replace=False)])
    elif variant == 'pat_random':
        sp['pat'] = (rng.rand(L, n) < 0.5) * rng.choice([-1., 1.], (L, n))
    elif variant == 'pat_square':
        sp['pat'] = np.tile(np.array([1., -1.])[:, None], (L // 2, n)) * rng.choice([-1., 1.], n)[None]
    elif variant == 'pat_ramp':
        sp['pat'] = sp1['pat'] * np.linspace(0.3, 1.7, L)[:, None]
    return sp

def build(Zs, u, starts, delta, make_specs, branches, rng_seed=0):
    """Return Z (B,T,d) tensor, mode (B,T), meta list. make_specs(p)->(sp1, [(name, sp2)])"""
    T = PRE + L + delta + L + POST; d = Zs.shape[1]
    Zl, Ml, meta = [], [], []
    for p, s in enumerate(starts):
        sp1, a2list = make_specs(p)
        for a2name, sp2 in a2list:
            for br in branches:
                rng = np.random.RandomState(rng_seed + 31 * p + (1 if br == 'F_sub' else 2 if br == 'F_sub2' else 0))
                z = Zs[s:s + T].copy(); mode = np.ones(T, dtype=np.int64)
                a1, a2 = PRE, PRE + L + delta
                if br in ('F_sub', 'F_sub2'):
                    r = rng.randint(0, len(Zs) - L); z[a1:a1 + L] = Zs[r:r + L]; d1 = np.zeros((L, d), np.float32)
                else:
                    d1 = inject(z, a1, sp1, s, Zs, u)
                    if br == 'F_skip': mode[a1:a1 + L] = SKIP
                    if br == 'F_decay': mode[a1:a1 + L] = DECAY
                dA = np.zeros((L, d), np.float32)
                d2 = inject(z, a2, sp2, s, Zs, u)
                Zl.append(z); Ml.append(mode)
                meta.append(dict(pos=p, branch=br, a2=a2name, delta=delta, rho=np.nan))
                if br == 'W':   # dissimilarity between injected deltas
                    d1w = inject(Zs[s:s + T].copy(), a1, sp1, s, Zs, u)
                    meta[-1]['rho'] = float(np.linalg.norm(d2 - d1w) / (np.linalg.norm(d1w) + 1e-9))
    return torch.tensor(np.stack(Zl)), torch.tensor(np.stack(Ml)), meta

def qstats(sc, delta):
    """per-episode: s2=max score on A2 window; q2 = rank vs sliding window-max (len L) of pre-A1 normal scores."""
    B, T = sc.shape; a2 = PRE + L + delta
    out = []
    for b in range(B):
        pre = sc[b, 60:PRE].numpy()
        nw = np.lib.stride_tricks.sliding_window_view(pre, L).max(1)
        s2 = float(np.nanmax(sc[b, a2:a2 + L].numpy()))
        q = float((nw < s2).mean() + 0.5 * (nw == s2).mean())
        out.append((s2, q, float(np.median(nw)), float(np.quantile(nw, .95))))
    return out

# ---------------------------------------------------------------- experiments
def main(machine, outdir, quick=False):
    os.makedirs(outdir, exist_ok=True)
    logf = open(f'{outdir}/log_{machine}.txt', 'a')
    def log(*a):
        s = ' '.join(str(x) for x in a); print(s, flush=True); logf.write(s + '\n'); logf.flush()
    torch.set_num_threads(6)
    Zfit, Zs, u, d, n = load(machine)
    log(f'[{machine}] rows={n} channels_kept={d} fit={len(Zfit)} stream={len(Zs)}')
    iters = 20 if quick else 600
    P = 3 if quick else 24
    dlist = [4, 64] if quick else DELTAS
    ntr = int(.8 * len(Zfit))
    models = {}
    for nm in MODELS:
        if nm == 'knn_append': models[nm] = KNN(Zfit)
        else:
            models[nm] = train_model(nm, Zfit[:ntr], u, d, iters, log=log); calibrate(models[nm], Zfit)
            log(f'  calibrated {nm} sigma median={models[nm].sigma.median():.3f}')
    rng = np.random.RandomState(123)
    Tmax = PRE + L + max(dlist) + L + POST
    starts = rng.randint(0, len(Zs) - Tmax - 1, P)

    # ---- G0 impulse response
    log('G0'); t0 = time.time()
    g0rows = []; lags = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]
    LAG = 2048 if not quick else 256; PG = 12 if not quick else 3
    TG = 200 + 1 + LAG + 4
    gst = rng.randint(0, len(Zs) - TG - 1, PG)
    Zc = np.stack([Zs[s:s + TG] for s in gst]); Zp = Zc.copy()
    for b in range(PG):
        r = np.random.RandomState(b); ch = r.choice(d, 8, replace=False)
        Zp[b, 200, ch] += 3.0 * u[ch] * r.choice([-1., 1.], 8)
    Zg = torch.tensor(np.concatenate([Zc, Zp])); Mg = torch.ones(Zg.shape[:2], dtype=torch.long)
    for nm, m in models.items():
        if nm == 'knn_append':
            sc = run(m, Zg, Mg); diff = (sc[PG:] - sc[:PG]).abs().numpy(); base = np.nanmedian(sc[:PG].numpy())
            R = np.nanmean(diff, 0) / base
        else:
            _, Pr = run(m, Zg, Mg, return_pred=True)
            R = (Pr[PG:] - Pr[:PG]).norm(dim=-1).mean(0).numpy()
        tt = 200                                      # R[tt+lag]: lag 0 = prediction of z_{t0+1}... index t is pred for z_t
        # pred for z_{t0+1} (lag 0) stored at index t0+1
        Rl = lambda k: R[200 + 1 + k]
        r1 = Rl(1) if Rl(1) > 0 else np.nan
        h50 = next((k for k in range(1, LAG) if Rl(k) <= 0.5 * Rl(1)), np.inf) if r1 == r1 else np.nan
        h5 = next((k for k in range(1, LAG) if Rl(k) <= 0.05 * Rl(1)), np.inf) if r1 == r1 else np.nan
        row = dict(machine=machine, model=nm, h50=h50, h05=h5, R1=float(Rl(1)) if r1 == r1 else 0.0)
        for k in lags:
            if k <= LAG: row[f'R_lag{k}'] = float(Rl(k)) if k + 202 < R.shape[0] else np.nan
        row['carry_frac_lag64'] = float(Rl(64) / Rl(1)) if r1 == r1 else 0.0
        g0rows.append(row); log(f'  {nm}: h50={h50} h05={h5} R1={row["R1"]:.4g} frac64={row["carry_frac_lag64"]:.3g}')
    pd.DataFrame(g0rows).to_csv(f'{outdir}/g0_{machine}.csv', index=False)
    log(f'G0 done {time.time()-t0:.0f}s')

    # ---- RQ0 persistent vs reset under benign drift
    log('RQ0'); t0 = time.time()
    PR = 4 if quick else 24; TR = 960; PRE0 = 320
    r0starts = rng.randint(0, len(Zs) - TR - 1, PR)
    Zl, meta = [], []
    for drift in ['none', 'level', 'ramp']:
        for p, s in enumerate(r0starts):
            z = Zs[s:s + TR].copy(); r = np.random.RandomState(p + 500); ch = r.choice(d, 8, replace=False)
            if drift == 'level': z[PRE0:, ch] += 2.0
            if drift == 'ramp': z[PRE0:, ch] += 2.0 * np.clip((np.arange(PRE0, TR) - PRE0) / 500., 0, 1)[:, None]
            Zl.append(z); meta.append((drift, p))
    Zr = torch.tensor(np.stack(Zl)); Mr = torch.ones(Zr.shape[:2], dtype=torch.long)
    idx = np.arange(TR); okmask = (idx % 64) >= KW
    rq0 = []
    for nm, m in models.items():
        for mode_name in ['persistent', 'reset']:
            sc = (run(m, Zr, Mr) if mode_name == 'persistent' else run_reset(m, Zr)).numpy()
            pre_ok = okmask & (idx >= 64) & (idx < PRE0); post_ok = okmask & (idx >= PRE0)
            thr = np.nanquantile(sc[:, pre_ok], 0.99)            # frozen pre-drift threshold, pooled
            for b, (drift, p) in enumerate(meta):
                rq0.append(dict(machine=machine, model=nm, mode=mode_name, drift=drift, pos=p,
                                fpr_pre=float((sc[b, pre_ok] > thr).mean()), fpr_post=float((sc[b, post_ok] > thr).mean()),
                                logratio=float(np.log(np.nanmedian(sc[b, post_ok]) / np.nanmedian(sc[b, pre_ok])))))
        log(f'  {nm} done t={time.time()-t0:.0f}s')
    pd.DataFrame(rq0).to_csv(f'{outdir}/rq0_{machine}.csv', index=False)

    # ---- RQ1 WIM
    log('RQ1'); t0 = time.time(); rows = []
    faults = [('spike', 1.0), ('spike', 2.0), ('spike', 4.0), ('corr', 0), ('stuck', 0)]
    if quick: faults = faults[1:2] + faults[3:4]
    BR = ['W', 'F_sub', 'F_sub2', 'F_skip', 'F_decay']
    for kind, amp in faults:
        fname = f'{kind}_a{amp:g}' if kind == 'spike' else kind
        for delta in dlist:
            def ms(p):
                sp = make_spec(kind, amp, p, d); return sp, [('identical', sp)]
            Zb, Mb, meta = build(Zs, u, starts, delta, ms, BR)
            for nm, m in models.items():
                sc = run(m, Zb, Mb); qs = qstats(sc, delta)
                for mt, (s2, q, nmed, n95) in zip(meta, qs):
                    if nm in NO_DECAY and mt['branch'] == 'F_decay': continue
                    rows.append(dict(machine=machine, model=nm, fault=fname, delta=delta, pos=mt['pos'], branch=mt['branch'], s2=s2, q2=q, null_med=nmed, null_p95=n95))
            log(f'  {fname} delta={delta} done t={time.time()-t0:.0f}s')
        pd.DataFrame(rows).to_csv(f'{outdir}/rq1_{machine}.csv', index=False)

    # ---- RQ2' masking kernel
    log('RQ2p'); t0 = time.time(); krows = []
    variants = ['amp0.5', 'amp0.75', 'amp1', 'amp1.5', 'amp2', 'ch_overlap50', 'ch_overlap0', 'pat_random', 'pat_square', 'pat_ramp']
    kdeltas = [4, 64] if quick else [16, 256]
    for delta in kdeltas:
        def ms(p):
            sp1 = make_spec('spike', 2.0, p, d); r = np.random.RandomState(900 + p)
            return sp1, [(v, sim_variant(sp1, v, d, r)) for v in variants]
        Zb, Mb, meta = build(Zs, u, starts, delta, ms, ['W', 'F_sub', 'F_sub2'])
        for nm, m in models.items():
            sc = run(m, Zb, Mb); qs = qstats(sc, delta)
            for mt, (s2, q, nmed, n95) in zip(meta, qs):
                krows.append(dict(machine=machine, model=nm, delta=delta, pos=mt['pos'], branch=mt['branch'], variant=mt['a2'], rho=mt['rho'], s2=s2, q2=q))
        log(f'  kernel delta={delta} done t={time.time()-t0:.0f}s')
    pd.DataFrame(krows).to_csv(f'{outdir}/kernel_{machine}.csv', index=False)
    json.dump(dict(machine=machine, d=d, starts=[int(x) for x in starts], iters=iters, P=P, deltas=dlist), open(f'{outdir}/meta_{machine}.json', 'w'))
    log('ALL DONE')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], quick=(len(sys.argv) > 3 and sys.argv[3] == 'quick'))
