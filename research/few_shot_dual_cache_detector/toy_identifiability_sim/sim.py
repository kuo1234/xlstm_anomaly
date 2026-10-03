"""Toy identifiability simulation for the self-confirming cache rule.

CPU only, no real data, no labels. A ridge one-step forecaster stands in for a
forecasting detector such as xLSTMAD-F; the identifiability argument (scenario C
vs D produce bit-identical y) does not depend on the model, the magnitudes do.

Usage:  python sim.py  -> writes results.csv (both load settings)
"""
import numpy as np
import pandas as pd

T, T0, EV = 3000, 1000, 1500           # length, deployment start, event onset
PHI, SIG, GAIN = 0.7, 0.3, 2.0         # AR(1) noise, noise sd, load->signal gain
LAGS, THR, SPAN, DWELL, GAP, W = 16, 4.0, 20, 150, 10, 300
tt = np.arange(T)

NAMES = {"A": "transient spike fault (20 steps)",
         "B": "benign short test (setpoint +0.6 for 20 steps)",
         "C": "benign permanent setpoint change (+0.6)",
         "D": "sensor-bias fault (+1.2), y identical to C",
         "E": "slow degradation fault (linear ramp 0->1.5)",
         "F": "long fault (400 steps) then repaired"}
STRATEGIES = {"S1 signal-only + promote if persistent (user rule)": ("X", True),
              "S2 context model + promote if persistent": ("C", True),
              "S3 context model + never auto-promote unexplained": ("C", False)}


def base(seed=7):
    rng = np.random.default_rng(seed)
    e = np.zeros(T)
    eps = rng.normal(0, SIG, T)
    for t in range(1, T):
        e[t] = PHI * e[t - 1] + eps[t]
    return e, rng.normal(0, 0.02, T)


def scenario(name, load):
    e, cn = base()
    c = 1.0 + load + cn
    bias = np.zeros(T)
    truth = np.zeros(T, int)            # 1 = fault
    if name == "A": bias[EV:EV + 20] = 3.0; truth[EV:EV + 20] = 1
    if name == "B": c[EV:EV + 20] += 0.6
    if name == "C": c[EV:] += 0.6
    if name == "D": bias[EV:] = 1.2; truth[EV:] = 1
    if name == "E": bias[EV:] = np.linspace(0, 1.5, T - EV); truth[EV:] = 1
    if name == "F": bias[EV:EV + 400] = 1.2; truth[EV:EV + 400] = 1
    return GAIN * c + e + bias, c, truth


def design(y, c, idx, mode):
    if mode == "X":                     # one-step forecaster on its own lags
        return np.column_stack([np.ones(len(idx))] + [y[idx - k] for k in range(1, LAGS + 1)])
    return np.column_stack([np.ones(len(idx)), c[idx], c[idx - 1]])   # normal-behaviour model on context


def _ref_stats(y, c, idx, mode, beta):
    res = y[idx] - design(y, c, idx, mode) @ beta
    ew = pd.Series(res).ewm(span=SPAN).mean().values[SPAN:]
    return ew.mean(), max(ew.std(), 1e-6)


def run(y, c, mode, promote):
    idx = np.arange(LAGS, T0)
    beta = np.linalg.lstsq(design(y, c, idx, mode), y[idx], rcond=None)[0]
    mu0, sd0 = _ref_stats(y, c, idx, mode, beta)
    alarm = np.zeros(T, bool)
    ew, a = 0.0, 2 / (SPAN + 1)
    ep_start, last_flag, promos = None, None, []
    for t in range(T0, T):
        r = y[t] - (design(y, c, np.array([t]), mode) @ beta)[0]
        ew = (1 - a) * ew + a * r
        if abs(ew - mu0) / sd0 > THR:
            if ep_start is None or (t - last_flag) > GAP:
                ep_start = t
            last_flag = t
            alarm[t] = True
            if promote and t - ep_start >= DWELL:       # "persistent, so it must be the new normal"
                w = np.arange(t - W + 1, t + 1)
                beta = np.linalg.lstsq(design(y, c, w, mode), y[w], rcond=None)[0]
                mu0, sd0 = _ref_stats(y, c, w, mode, beta)
                ew = mu0
                promos.append(t)
                ep_start = None
    return alarm, promos


def run_all(load_amp):
    load = load_amp * np.sin(2 * np.pi * tt / 400)
    rows = []
    for s, desc in NAMES.items():
        y, c, truth = scenario(s, load)
        for sn, (mode, prom) in STRATEGIES.items():
            alarm, promos = run(y, c, mode, prom)
            dep = np.arange(T0, T)
            f = truth[dep] == 1
            rows.append(dict(config="constant load" if load_amp == 0 else "cyclic load",
                             scenario=s, scenario_desc=desc, strategy=sn,
                             fault_recall=alarm[dep][f].mean() if f.any() else np.nan,
                             normal_alarm_rate=alarm[dep][~f].mean(),
                             n_promotions=len(promos),
                             fault_absorbed_into_normal=any(truth[p] == 1 for p in promos),
                             first_promotion_t=promos[0] if promos else None))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    load = 0.3 * np.sin(2 * np.pi * tt / 400)
    yC, _, _ = scenario("C", load)
    yD, _, _ = scenario("D", load)
    print("max |y_C - y_D| =", np.abs(yC - yD).max())
    out = pd.concat([run_all(0.0), run_all(0.3)])
    out.to_csv("results.csv", index=False)
    print(out[["config", "scenario", "strategy", "fault_recall", "fault_absorbed_into_normal"]].round(3).to_string(index=False))
