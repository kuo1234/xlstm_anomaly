"""Aggregate + figures for the exploratory P10/T1 pilot (reads full/*.csv)."""
import pandas as pd, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
IN = 'full/'; MS = ['machine-1-4', 'machine-2-1']
MODELS = ['window_only', 'lstm', 'mlstm', 'gdeltanet', 'titans', 'knn_append']
COL = dict(window_only='#7f7f7f', lstm='#1f77b4', mlstm='#2ca02c', gdeltanet='#ff7f0e', titans='#d62728', knn_append='#9467bd')
rng = np.random.RandomState(0)
def boot(x, B=2000):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) == 0: return np.nan, np.nan, np.nan
    m = x[rng.randint(0, len(x), (B, len(x)))].mean(1)
    return x.mean(), np.quantile(m, .025), np.quantile(m, .975)
rd = lambda p: pd.concat([pd.read_csv(f'{IN}{p}_{m}.csv') for m in MS], ignore_index=True)
g0, rq0, rq1, ker = rd('g0'), rd('rq0'), rd('rq1'), rd('kernel')
for n, df in [('p10_g0.csv', g0), ('p10_rq0.csv', rq0), ('p10_rq1_wim_raw.csv', rq1), ('p10_kernel_raw.csv', ker)]: df.to_csv(n, index=False)

# ---- WIM summary
def unit_table(df, keys):
    p = df.pivot_table(index=keys + ['machine', 'pos'], columns='branch', values='q2').reset_index()
    ps = df.pivot_table(index=keys + ['machine', 'pos'], columns='branch', values='s2').reset_index()
    p['wim_sub'] = p.F_sub - p.W; p['null'] = p.F_sub - p.F_sub2
    p['wim_skip'] = p.F_skip - p.W if 'F_skip' in p else np.nan
    p['wim_decay'] = p.F_decay - p.W if 'F_decay' in p else np.nan
    p['content_vs_skip'] = (p.F_sub - p.F_skip) if 'F_skip' in p else np.nan
    p['logratio'] = np.log(ps.W) - np.log(ps.F_sub)
    return p
u1 = unit_table(rq1, ['model', 'fault', 'delta'])
rows = []
for (mo, fa, de), g in u1.groupby(['model', 'fault', 'delta']):
    r = dict(model=mo, fault=fa, delta=de, n_units=len(g), q_W=g.W.mean(), q_Fsub=g.F_sub.mean())
    for k in ['wim_sub', 'null', 'wim_skip', 'wim_decay', 'logratio']:
        m, lo, hi = boot(g[k]); r[k] = m; r[k + '_lo'] = lo; r[k + '_hi'] = hi
    r['null_sd_unit'] = g['null'].std(); r['frac_detect_W'] = (g.W > .95).mean(); r['frac_detect_Fsub'] = (g.F_sub > .95).mean()
    rows.append(r)
wim = pd.DataFrame(rows); wim.to_csv('p10_wim_summary.csv', index=False)

# paired difference to window-only (pooled over delta>=16, i.e. beyond window length K=8)
rows = []
for fa in u1.fault.unique():
    for dset, ds in [('d16', [16]), ('d64_1024', [64, 256, 1024]), ('d>=16', [16, 64, 256, 1024])]:
        w = u1[(u1.model == 'window_only') & (u1.fault == fa) & u1.delta.isin(ds)].set_index(['delta', 'machine', 'pos']).wim_sub
        for mo in MODELS[1:]:
            g = u1[(u1.model == mo) & (u1.fault == fa) & u1.delta.isin(ds)].set_index(['delta', 'machine', 'pos']).wim_sub
            dif = (g - w.reindex(g.index)).groupby(level=['machine', 'pos']).mean()
            m, lo, hi = boot(dif); rows.append(dict(fault=fa, deltas=dset, model=mo, wim_minus_window=m, lo=lo, hi=hi))
paired = pd.DataFrame(rows); paired.to_csv('p10_wim_vs_window.csv', index=False)

# ---- kernel summary
uk = unit_table(ker, ['model', 'delta', 'variant'])
uk['rho'] = ker[ker.branch == 'W'].groupby(['model', 'delta', 'variant', 'machine', 'pos']).rho.first().reindex(
    pd.MultiIndex.from_frame(uk[['model', 'delta', 'variant', 'machine', 'pos']])).values
rows = []
for (mo, de, va), g in uk.groupby(['model', 'delta', 'variant']):
    m, lo, hi = boot(g.wim_sub); nm, nlo, nhi = boot(g['null'])
    rows.append(dict(model=mo, delta=de, variant=va, rho=g.rho.mean(), wim_sub=m, lo=lo, hi=hi, null=nm, q_W=g.W.mean(), q_Fsub=g.F_sub.mean()))
ks = pd.DataFrame(rows); ks.to_csv('p10_kernel_summary.csv', index=False)

# ---- RQ0 summary
rows = []
for (mo, mode, dr), g in rq0.groupby(['model', 'mode', 'drift']):
    m, lo, hi = boot(g.fpr_post); rows.append(dict(model=mo, mode=mode, drift=dr, fpr_post=m, lo=lo, hi=hi, fpr_pre=g.fpr_pre.mean(), logratio=g.logratio.mean()))
r0 = pd.DataFrame(rows)
# paired persistent - reset
pr = rq0.pivot_table(index=['model', 'drift', 'machine', 'pos'], columns='mode', values='fpr_post').reset_index(); pr['d'] = pr.persistent - pr.reset
rows = []
for (mo, dr), g in pr.groupby(['model', 'drift']):
    m, lo, hi = boot(g.d); rows.append(dict(model=mo, drift=dr, persistent_minus_reset=m, lo=lo, hi=hi))
r0d = pd.DataFrame(rows); r0.to_csv('p10_rq0_summary.csv', index=False); r0d.to_csv('p10_rq0_paired.csv', index=False)

# ---- figures
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False})
# G0
fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
lags = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]
for mo in MODELS:
    R = np.array([[g0[(g0.model == mo) & (g0.machine == m)][f'R_lag{k}'].iloc[0] for k in lags] for m in MS])
    R = R / R[:, :1]; y = np.maximum(R.mean(0), 1e-6)
    ax[0].plot(lags, y, '-o', ms=3, color=COL[mo], label=mo)
ax[0].axhline(.5, ls=':', c='k', lw=.8); ax[0].set_xscale('log'); ax[0].set_yscale('log'); ax[0].set_ylim(1e-5, 20)
ax[0].set_xlabel('lag after single-step impulse (update steps)'); ax[0].set_ylabel('R(lag)/R(1)  (|Δ forecast| or |Δ score|)')
ax[0].set_title('G0 impulse response (mean of 2 machines; floor 1e-6)'); ax[0].legend(fontsize=7)
w = .38
for i, m in enumerate(MS):
    h = [min(g0[(g0.model == mo) & (g0.machine == m)].h50.iloc[0], 2048) for mo in MODELS]
    ax[1].bar(np.arange(6) + (i - .5) * w, h, w, color=[COL[mo] for mo in MODELS], alpha=.55 + .4 * i, label=m)
ax[1].set_yscale('log'); ax[1].set_xticks(range(6)); ax[1].set_xticklabels(MODELS, rotation=30, ha='right')
ax[1].set_ylabel('half-life h50 (update steps)'); ax[1].set_title('h50 per machine (light=1-4, dark=2-1)')
fig.tight_layout(); fig.savefig('fig_g0_halflife.png', dpi=160); plt.close(fig)
# RQ0
fig, axs = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
for ax, dr in zip(axs, ['none', 'level', 'ramp']):
    for j, mode in enumerate(['persistent', 'reset']):
        s = r0[(r0.drift == dr) & (r0['mode'] == mode)].set_index('model').loc[MODELS]
        ax.bar(np.arange(6) + (j - .5) * .38, s.fpr_post, .38, yerr=[s.fpr_post - s.lo, s.hi - s.fpr_post], color=[COL[m] for m in MODELS], alpha=1 if j == 0 else .4, capsize=2)
    ax.axhline(.01, ls=':', c='k'); ax.set_xticks(range(6)); ax.set_xticklabels(MODELS, rotation=40, ha='right'); ax.set_title(f'drift = {dr}')
axs[0].set_ylabel('post-drift FPR @ pre-drift 99th pct threshold\n(solid=persistent, faded=per-window reset)')
fig.tight_layout(); fig.savefig('fig_rq0_fpr.png', dpi=160); plt.close(fig)
# WIM vs delta
faults = ['spike_a1', 'spike_a2', 'spike_a4', 'corr', 'stuck']
fig, axs = plt.subplots(1, 5, figsize=(17, 3.6), sharey=True)
for ax, fa in zip(axs, faults):
    for mo in MODELS:
        s = wim[(wim.model == mo) & (wim.fault == fa)].sort_values('delta')
        ax.errorbar(s.delta * (1 + .04 * MODELS.index(mo)), s.wim_sub, yerr=[s.wim_sub - s.wim_sub_lo, s.wim_sub_hi - s.wim_sub], color=COL[mo], marker='o', ms=3, lw=1, capsize=1.5, label=mo)
    nl = wim[(wim.fault == fa)].groupby('delta').null.mean()
    ax.axhline(0, c='k', lw=.6); ax.axvline(8, ls=':', c='gray'); ax.set_xscale('log'); ax.set_title(fa); ax.set_xlabel('Δ (update steps)')
axs[0].set_ylabel('WIM_sub = q(F_sub) − q(W)'); axs[0].legend(fontsize=6); axs[0].text(8.5, axs[0].get_ylim()[1] * .9, 'window\nK=8', fontsize=6, color='gray')
fig.tight_layout(); fig.savefig('fig_wim_vs_delta.png', dpi=160); plt.close(fig)
# kernel
fig, axs = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
for ax, de in zip(axs, [16, 256]):
    for mo in MODELS:
        s = ks[(ks.model == mo) & (ks.delta == de)].sort_values('rho')
        ax.errorbar(s.rho, s.wim_sub, yerr=[s.wim_sub - s.lo, s.hi - s.wim_sub], color=COL[mo], marker='o', ms=3, lw=1, capsize=1.5, label=mo, alpha=.9)
    ax.axhline(0, c='k', lw=.6); ax.set_xlabel('dissimilarity ρ = ||δ2 − δ1|| / ||δ1||  (injected deltas)'); ax.set_title(f'masking kernel, Δ={de} (spike family, A1 amp=2u)')
axs[0].set_ylabel('WIM_sub'); axs[0].legend(fontsize=7)
fig.tight_layout(); fig.savefig('fig_kernel.png', dpi=160); plt.close(fig)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
print(wim[wim.delta >= 16].pivot_table(index=['fault', 'model'], columns='delta', values='wim_sub').round(3))
print(wim[wim.delta >= 16][['fault', 'model', 'delta', 'wim_sub', 'wim_sub_lo', 'wim_sub_hi', 'null', 'null_sd_unit']].query('wim_sub_lo>0').round(3))
print(paired.round(3).query("deltas=='d>=16'"))
print(wim[wim.delta <= 4].pivot_table(index=['fault', 'model'], columns='delta', values='wim_sub').round(3).head(12))
print(wim.groupby('delta')['null'].agg(['mean', 'std']).round(4)); print(wim.null_sd_unit.describe().round(3))
print(r0d.round(3)); print(wim[(wim.delta >= 16)].pivot_table(index=['fault', 'model'], columns='delta', values='logratio').round(3))
print(ks.pivot_table(index=['model', 'delta'], columns='variant', values='wim_sub').round(3)); print(ks[ks.model=='mlstm'][['delta','variant','rho']].drop_duplicates().round(2).T)
