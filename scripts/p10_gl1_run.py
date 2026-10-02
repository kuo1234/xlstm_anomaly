"""P10 G-L1 runner: fit/evaluate per (machine, seed), then finalize statistics and decision.

Usage
  # label-blind synthetic dry-run (allowed before seal; uses no SMD data)
  python scripts/p10_gl1_run.py dry-run --config configs/p10_gl1_config.yaml --out /tmp/gl1_dry
  # sealed execution (NOT authorized until seal-readiness review): per machine, then finalize
  P10_GL1_AUTHORIZED=1 python scripts/p10_gl1_run.py fit --config configs/p10_gl1_config.yaml \
      --machine machine-3-7 --seed 11 --out reports/p10_gl1/run_<id> --smd-dir $SMD_DIR
  P10_GL1_AUTHORIZED=1 python scripts/p10_gl1_run.py finalize --config ... --out reports/p10_gl1/run_<id>
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import os
import sys
import time

import numpy as np
import torch
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p10_gl1_core as K  # noqa: E402
import p10_gl1_models as M  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ============================================================================ config / seal
def load_config(path):
    with open(path) as f:
        cfg = yaml.safe_load(f)
    arch = cfg["models"]["arch"]
    if json.loads(json.dumps(arch)) != json.loads(json.dumps(M.ARCH)):
        raise K.TechnicalInvalid("config models.arch differs from p10_gl1_models.ARCH")
    return cfg


def verify_seal(cfg):
    sums = os.path.join(REPO, cfg["seal"]["sha256sums"])
    if not os.path.exists(sums):
        raise K.TechnicalInvalid("SHA256SUMS missing: protocol not sealed")
    bad = []
    for line in open(sums):
        if not line.strip():
            continue
        h, p = line.split(None, 1)
        p = p.strip()
        if K.sha256_file(os.path.join(REPO, p)) != h:
            bad.append(p)
    if bad:
        raise K.TechnicalInvalid(f"sealed files changed: {bad}")


def require_authorization(cfg):
    if os.environ.get("P10_GL1_AUTHORIZED") != "1":
        raise SystemExit("G-L1 execution is not authorized (set P10_GL1_AUTHORIZED=1 only after the "
                         "seal-readiness review grants execution).")
    verify_seal(cfg)


def manifest(cfg):
    rows = list(csv.DictReader(open(os.path.join(REPO, cfg["data"]["manifest"]))))
    return {r["machine"]: r for r in rows}



def config_digest(cfg):
    return hashlib.sha256(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()


def seal_digest(cfg):
    p = os.path.join(REPO, cfg["seal"]["sha256sums"])
    return K.sha256_file(p) if os.path.exists(p) else "unsealed"


def trained_models(cfg):
    m = cfg["models"]
    return list(dict.fromkeys(["window_only", m["primary"]] + m["replications"] + m["references_trained"]))


def arms_for(name):
    if name == "window_only":
        return ["single"]
    if name == "mlstm_std":
        return ["reset"]
    return ["persistent", "reset"]


G0_MODELS = ("mlstm", "gdeltanet", "titans", "lstm")


def _finish_job(cfg, tmp, final, meta):
    meta = dict(meta, config_digest=config_digest(cfg), seal_digest=seal_digest(cfg), finished=time.time())
    with open(os.path.join(tmp, "job_done.json"), "w") as f:
        json.dump(meta, f, indent=1)
    os.replace(tmp, final)


def _start_job(final):
    if os.path.exists(final):
        raise K.TechnicalInvalid(f"output {final} already exists; refusing to overwrite (stale-run guard)")
    tmp = f"{final}.tmp-{os.getpid()}"
    os.makedirs(tmp, exist_ok=False)
    return tmp


# ============================================================================ per-(machine, seed) job
def write_csv(path, rows):
    if not rows:
        open(path, "w").close(); return
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, restval=""); w.writeheader(); w.writerows(rows)


def fit_machine_seed(cfg, P, machine, seed, final, dev, models=None, log=print):
    os.makedirs(os.path.dirname(final), exist_ok=True)
    out = _start_job(final)
    plan = K.make_plan(P, cfg, machine)
    names = models or trained_models(cfg)
    fits, g0rows, eprows, srows = [], [], [], []
    trained = {}
    for name in ["window_only"] + [n for n in names if n != "window_only"]:
        t = time.time()
        model, info = K.train_model(name, P, cfg, seed, dev, log)
        row = dict(machine=machine, **info, C=P.z.shape[1])
        if info["nan_train"]:
            row.update(diverged=True, val_mse=float("nan"), val_ratio=float("nan"), stream_state_norm_max=float("nan"))
            fits.append(row); continue
        sig, mse = K.sigmas(model, name, P, cfg, dev, info["train_state_norm_max"])
        main_arm = "persistent" if "persistent" in mse else ("single" if name == "window_only" else "reset")
        row["val_mse"] = mse[main_arm]
        for a, v in mse.items():
            row[f"val_mse_{a}"] = v
        if name == "window_only":
            trained["window_only_val"] = mse["single"]
        row["val_ratio"] = row["val_mse"] / trained.get("window_only_val", float("nan"))
        res = K.evaluate_fit(model, name, P, plan, cfg, dev, sig, log)
        row["diverged"] = bool(res["diverged"])
        row["stream_state_norm_max"] = res["stream_state_norm_max"]
        row["seconds"] = round(time.time() - t, 1)
        fits.append(row)
        for g in res["g0"]:
            g0rows.append(dict(machine=machine, seed=seed, model=name, pos=g["pos"]))
            np.savez_compressed(os.path.join(out, f"g0_{name}_{g['pos']}.npz"), R=g["R"], null=g["null"])
        for e in res["episodes"]:
            eprows.append(dict(machine=machine, seed=seed, model=name, **e))
        for s in res["sentinel"]:
            srows.append(dict(machine=machine, seed=seed, model=name, **s))
        log(f"[{machine} s{seed}] {name}: iters={info['iters']} val_ratio={row['val_ratio']:.3f} "
            f"diverged={row['diverged']} {row['seconds']}s")
    write_csv(os.path.join(out, "fits.csv"), fits)
    write_csv(os.path.join(out, "g0_index.csv"), g0rows)
    write_csv(os.path.join(out, "episodes.csv"), eprows)
    write_csv(os.path.join(out, "sentinel.csv"), srows)
    _finish_job(cfg, out, final, dict(job="fit", machine=machine, seed=seed, plan_hash=K.plan_hash(plan),
                                     g0_positions=[int(p) for p in plan.g0_pos]))


def knn_machine(cfg, P, machine, final, dev):
    os.makedirs(os.path.dirname(final), exist_ok=True)
    out = _start_job(final)
    plan = K.make_plan(P, cfg, machine)
    rows, srows = K.knn_evaluate(P, plan, cfg, dev)
    write_csv(os.path.join(out, "episodes_knn.csv"), [dict(machine=machine, seed=0, model="knn_append", **r) for r in rows])
    write_csv(os.path.join(out, "sentinel_knn.csv"), [dict(machine=machine, seed=0, model="knn_append", **r) for r in srows])
    _finish_job(cfg, out, final, dict(job="knn", machine=machine, seed=0, plan_hash=K.plan_hash(plan)))


# ============================================================================ statistics
def hier_boot(D, B, seed):
    """D: array [machine, seed, episode] (NaN allowed for missing). Equal weight per level.
    Returns point, (lo, hi) 95% percentile CI from a machine->seed->episode paired bootstrap."""
    D = np.asarray(D, dtype=float)
    Mn, S, E = D.shape
    point = np.nanmean(np.nanmean(np.nanmean(D, 2), 1))
    rng = np.random.default_rng(seed)
    mi = rng.integers(Mn, size=(B, Mn))
    si = rng.integers(S, size=(B, Mn, S))
    ei = rng.integers(E, size=(B, Mn, S, E))
    X = D[mi[:, :, None, None], si[:, :, :, None], ei]
    with np.errstate(all="ignore"):
        bs = np.nanmean(np.nanmean(np.nanmean(X, 3), 2), 1)
    lo, hi = np.nanpercentile(bs, [2.5, 97.5])
    return float(point), float(lo), float(hi)


def read_all(out, fname):
    rows = []
    for root, _, files in os.walk(out):
        if fname in files:
            p = os.path.join(root, fname)
            if os.path.getsize(p):
                rows += list(csv.DictReader(open(p)))
    return rows


def effective_machines(cfg, out):
    tech = {}
    p = os.path.join(out, "technical_invalid.json")
    if os.path.exists(p):
        tech = json.load(open(p))
    prim = [m for m in cfg["data"]["primary_machines"] if m not in tech]
    for r in cfg["data"]["reserve_machines"]:
        if len(prim) >= len(cfg["data"]["primary_machines"]):
            break
        if r not in tech:
            prim.append(r)
    return prim, tech


def p1_table(cfg, out, machines, model):
    g0 = cfg["g0"]
    rows = []
    for m in machines:
        for s in cfg["training"]["seeds"]:
            d = os.path.join(out, m, f"seed{s}")
            files = [f for f in os.listdir(d)] if os.path.isdir(d) else []
            fl = [f for f in files if f.startswith(f"g0_{model}_") and f[len(f"g0_{model}_"):-4].isdigit()]
            if not fl:
                rows.append(dict(machine=m, seed=s, pos=None, h05=0, status="missing")); continue
            arrs = [np.load(os.path.join(d, f)) for f in fl]
            nulls = np.concatenate([a["null"] for a in arrs])
            floor = max(float(np.quantile(nulls, g0["null_quantile"])), cfg["validity"]["parity_tol"])
            for f, a in zip(fl, arrs):
                h, st = K.h05_from_response(a["R"], floor, g0["ref_lags"], g0["unstable_factor"])
                rows.append(dict(machine=m, seed=s, pos=int(f.split("_")[-1][:-4]), h05=h, status=st, floor=floor))
    seed_lvl, mach_lvl = {}, {}
    for m in machines:
        hs = []
        for s in cfg["training"]["seeds"]:
            r = [x for x in rows if x["machine"] == m and x["seed"] == s and x["status"] in ("ok", "censored")]
            hs.append(float(np.median([x["h05"] for x in r])) if len(r) >= g0["min_measurable_positions"] else 0.0)
            seed_lvl[(m, s)] = hs[-1]
        mach_lvl[m] = float(np.median(hs))
    npass = sum(v >= g0["pass_h05_min"] for v in mach_lvl.values())
    return rows, seed_lvl, mach_lvl, npass >= g0["pass_min_machines"], npass


def endpoint_arrays(cfg, eps, sents, machines, model, family):
    seeds = cfg["training"]["seeds"] if model != "knn_append" else [0]
    E = cfg["utility"]["episodes_per_family"]
    Dfpr = np.full((len(machines), len(seeds), E), np.nan)
    Ddet = np.full((len(machines), len(seeds), E), np.nan)
    Dkind = {k: np.full((len(machines), len(seeds), E), np.nan) for k in cfg["sentinel"]["types"]}
    idx = {}
    for r in eps:
        if r["model"] != model or r["family"] != family:
            continue
        idx.setdefault((r["machine"], int(r["seed"]), int(r["ep"])), {})[r["arm"]] = float(r["fpr"])
    sidx = {}
    for r in sents:
        if r["model"] != model or r["family"] != family:
            continue
        sidx.setdefault((r["machine"], int(r["seed"]), int(r["ep"]), r["kind"]), {})[r["arm"]] = float(r["detected"] == "True")
    for a, m in enumerate(machines):
        for b, s in enumerate(seeds):
            for e in range(E):
                v = idx.get((m, s, e))
                if v and "persistent" in v and "reset" in v:
                    Dfpr[a, b, e] = v["persistent"] - v["reset"]
                ks = []
                for k in cfg["sentinel"]["types"]:
                    w = sidx.get((m, s, e, k))
                    if w and "persistent" in w and "reset" in w:
                        Dkind[k][a, b, e] = w["persistent"] - w["reset"]; ks.append(Dkind[k][a, b, e])
                if ks:
                    Ddet[a, b, e] = np.mean(ks)
    return Dfpr, Ddet, Dkind


def evaluate_model(cfg, out, machines, model, eps, sents, fits):
    st = cfg["stats"]
    res = dict(model=model)
    ff = [f for f in fits if f["model"] == model and f["machine"] in machines]
    # P0 fit adequacy (scientific; no reserve substitution)
    ok_m = 0
    for m in machines:
        n_ok = sum(1 for f in ff if f["machine"] == m and f["nan_train"] == "False"
                   and float(f["val_ratio"]) <= cfg["validity"]["val_mse_max_ratio_vs_window_only"])
        ok_m += n_ok >= cfg["validity"]["min_valid_seeds_per_machine"]
    res["P0_machines_adequate"] = ok_m
    res["P0"] = ok_m >= cfg["validity"]["min_valid_machines"]
    # P1 persistence
    rows, seed_lvl, mach_lvl, p1, npass = p1_table(cfg, out, machines, model)
    res.update(P1=p1, P1_machines_pass=npass, P1_machine_h05=mach_lvl)
    # P2 utility
    fam = list(cfg["utility"]["families"])
    res["P2_family"] = {}
    passing = []
    per_machine = {}
    for f in fam:
        Dfpr, _, _ = endpoint_arrays(cfg, eps, sents, machines, model, f)
        pt, lo, hi = hier_boot(Dfpr, st["B"], st["bootstrap_seed"])
        ok = pt <= cfg["utility"]["pass_delta_fpr_max"] and hi < 0
        res["P2_family"][f] = dict(point=pt, lo=lo, hi=hi, pass_=ok)
        per_machine[f] = {m: float(np.nanmean(Dfpr[i])) for i, m in enumerate(machines)}
        if ok:
            passing.append(f)
    res["P2"] = len(passing) >= cfg["utility"]["pass_min_families"]
    res["P2_machine_effects"] = per_machine
    # P3 no score collapse (families passing P2 + none)
    res["P3_family"], flags = {}, []
    p3 = True
    for f in passing + ["none"]:
        _, Ddet, Dk = endpoint_arrays(cfg, eps, sents, machines, model, f)
        pt, lo, hi = hier_boot(Ddet, st["B"], st["bootstrap_seed"])
        kinds = {k: float(np.nanmean(v)) for k, v in Dk.items()}
        okf = lo > -cfg["sentinel"]["noninferiority_margin"]
        p3 &= okf
        res["P3_family"][f] = dict(point=pt, lo=lo, hi=hi, pass_=okf, per_kind=kinds)
        flags += [f"{f}:{k}" for k, v in kinds.items() if v < -cfg["sentinel"]["large_degradation_flag"]]
    res["P3"] = p3 and res["P2"]
    res["P3_large_degradation_flags"] = flags
    # P4 stability
    Dn, _, _ = endpoint_arrays(cfg, eps, sents, machines, model, "none")
    pt, lo, hi = hier_boot(Dn, st["B"], st["bootstrap_seed"])
    div = [f"{f['machine']}/s{f['seed']}" for f in ff if f.get("diverged") == "True" or f["nan_train"] == "True"]
    res["P4_nodrift"] = dict(point=pt, lo=lo, hi=hi)
    res["P4_diverged_fits"] = div
    res["P4"] = (hi <= cfg["stability"]["nodrift_delta_fpr_upper_max"]) and not div
    order = [("P0", "FAIL-FIT"), ("P1", "FAIL-PERSIST"), ("P2", "FAIL-UTILITY"), ("P3", "FAIL-COLLAPSE"), ("P4", "FAIL-STABILITY")]
    res["label"] = next((lab for k, lab in order if not res[k]), "PASS")
    return res


def validate_execution_completeness(cfg, out, machines):
    """Fail-closed audit of the sealed plan BEFORE any endpoint is computed.
    Returns list of problems (empty = complete). Any problem => TECHNICAL-INCOMPLETE."""
    probs = []
    seeds = cfg["training"]["seeds"]
    fams = list(cfg["utility"]["families"]) + ["none"]
    E = cfg["utility"]["episodes_per_family"]
    kinds = list(cfg["sentinel"]["types"])
    npos = cfg["g0"]["positions_per_machine"]
    cd, sd = config_digest(cfg), seal_digest(cfg)
    for root, dirs, _ in os.walk(out):
        for d in dirs:
            if ".tmp-" in d:
                probs.append(f"partial job directory {os.path.join(root, d)}")
    for m in machines:
        plan_hashes = set()
        jobs = [(s, os.path.join(out, m, f"seed{s}")) for s in seeds] + [("knn", os.path.join(out, m, "knn"))]
        for s, d in jobs:
            mk = os.path.join(d, "job_done.json")
            if not os.path.exists(mk):
                probs.append(f"missing or unfinished job {m}/{s}"); continue
            meta = json.load(open(mk))
            if meta.get("config_digest") != cd:
                probs.append(f"stale job {m}/{s}: config digest differs")
            if meta.get("seal_digest") != sd:
                probs.append(f"stale job {m}/{s}: seal digest differs")
            if str(meta.get("machine")) != m or str(meta.get("seed")) != str(0 if s == "knn" else s):
                probs.append(f"job marker mismatch in {m}/{s}")
            plan_hashes.add(meta.get("plan_hash"))
        if len(plan_hashes) > 1:
            probs.append(f"{m}: jobs disagree on the sealed plan")
        for s in seeds:
            d = os.path.join(out, m, f"seed{s}")
            if not os.path.exists(os.path.join(d, "job_done.json")):
                continue
            fits = list(csv.DictReader(open(os.path.join(d, "fits.csv")))) if os.path.getsize(os.path.join(d, "fits.csv")) else []
            fk = [(r["machine"], str(r["seed"]), r["model"]) for r in fits]
            exp_f = [(m, str(s), n) for n in trained_models(cfg)]
            if sorted(fk) != sorted(exp_f):
                probs.append(f"{m}/seed{s}: fit rows {sorted(set(fk) ^ set(exp_f))} missing/extra or duplicated" if set(fk) != set(exp_f) else f"{m}/seed{s}: duplicate fit rows")
            nan_models = {r["model"] for r in fits if r.get("nan_train") == "True"}
            meta = json.load(open(os.path.join(d, "job_done.json")))
            g0pos = meta.get("g0_positions", [])
            if len(g0pos) != npos or len(set(g0pos)) != npos:
                probs.append(f"{m}/seed{s}: G0 plan has {len(g0pos)} positions (expected {npos})")
            gidx = list(csv.DictReader(open(os.path.join(d, "g0_index.csv")))) if os.path.getsize(os.path.join(d, "g0_index.csv")) else []
            for n in G0_MODELS:
                if n not in trained_models(cfg) or n in nan_models:
                    continue
                got = [int(r["pos"]) for r in gidx if r["model"] == n]
                if sorted(got) != sorted(g0pos):
                    probs.append(f"{m}/seed{s}/{n}: G0 rows incomplete or duplicated")
                for p in g0pos:
                    if not os.path.exists(os.path.join(d, f"g0_{n}_{p}.npz")):
                        probs.append(f"{m}/seed{s}/{n}: missing G0 npz at {p}")
            eps = list(csv.DictReader(open(os.path.join(d, "episodes.csv")))) if os.path.getsize(os.path.join(d, "episodes.csv")) else []
            sen = list(csv.DictReader(open(os.path.join(d, "sentinel.csv")))) if os.path.getsize(os.path.join(d, "sentinel.csv")) else []
            ek = [(r["model"], r["family"], int(r["ep"]), r["arm"]) for r in eps]
            sk = [(r["model"], r["family"], int(r["ep"]), r["arm"], r["kind"]) for r in sen]
            exp_e = [(n, f, e, a) for n in trained_models(cfg) if n not in nan_models
                     for f in fams for e in range(E) for a in arms_for(n)]
            exp_s = [x + (k,) for x in exp_e for k in kinds]
            if sorted(ek) != sorted(exp_e):
                probs.append(f"{m}/seed{s}: episode rows incomplete/duplicated ({len(ek)} vs {len(exp_e)})")
            if sorted(sk) != sorted(exp_s):
                probs.append(f"{m}/seed{s}: sentinel rows incomplete/duplicated ({len(sk)} vs {len(exp_s)})")
        d = os.path.join(out, m, "knn")
        if os.path.exists(os.path.join(d, "job_done.json")):
            eps = list(csv.DictReader(open(os.path.join(d, "episodes_knn.csv"))))
            sen = list(csv.DictReader(open(os.path.join(d, "sentinel_knn.csv"))))
            exp_e = [(f, e, a) for f in fams for e in range(E) for a in ("persistent", "reset")]
            if sorted((r["family"], int(r["ep"]), r["arm"]) for r in eps) != sorted(exp_e):
                probs.append(f"{m}/knn: episode rows incomplete/duplicated")
            if sorted((r["family"], int(r["ep"]), r["arm"], r["kind"]) for r in sen) != sorted(x + (k,) for x in exp_e for k in kinds):
                probs.append(f"{m}/knn: sentinel rows incomplete/duplicated")
    return probs


def finalize(cfg, out):
    machines, tech = effective_machines(cfg, out)
    if len(machines) < len(cfg["data"]["primary_machines"]):
        dec = dict(decision="TECHNICAL-INCOMPLETE", machines=machines, technical_invalid=tech)
        json.dump(dec, open(os.path.join(out, "decision.json"), "w"), indent=1)
        return dec
    probs = validate_execution_completeness(cfg, out, machines)
    if probs:
        dec = dict(decision="TECHNICAL-INCOMPLETE", machines=machines, technical_invalid=tech, problems=probs)
        json.dump(dec, open(os.path.join(out, "decision.json"), "w"), indent=1)
        return dec
    fits = [f for f in read_all(out, "fits.csv") if f["machine"] in machines]
    eps = read_all(out, "episodes.csv") + read_all(out, "episodes_knn.csv")
    sents = read_all(out, "sentinel.csv") + read_all(out, "sentinel_knn.csv")
    prim = cfg["models"]["primary"]
    results = {prim: evaluate_model(cfg, out, machines, prim, eps, sents, fits)}
    for r in cfg["models"]["replications"]:
        results[r] = evaluate_model(cfg, out, machines, r, eps, sents, fits)
    for r in ("lstm",):
        if any(f["model"] == r for f in fits):
            results[r] = evaluate_model(cfg, out, machines, r, eps, sents, fits)
    gl1 = results[prim]["label"]
    family_claim = gl1 == "PASS" and sum(results[r]["label"] == "PASS" for r in cfg["models"]["replications"]) >= 1
    sci = [dict(model=f["model"], machine=f["machine"], seed=f["seed"],
                nan_train=f["nan_train"] == "True", diverged=f.get("diverged") == "True",
                poor_fit=(f["nan_train"] != "True" and float(f["val_ratio"]) > cfg["validity"]["val_mse_max_ratio_vs_window_only"]))
           for f in fits]
    sci = [x for x in sci if x["nan_train"] or x["diverged"] or x["poor_fit"]]
    dec = dict(gate="P10-GL1", decision=gl1, primary=prim, machines=machines, technical_invalid=tech,
               family_claim_supported=family_claim, scientific_failure_flags=sci,
               P4_diverged_fits_primary=results[prim]["P4_diverged_fits"], results=results,
               next=("WIM protocol v0.3" if gl1 == "PASS" else "G-L2"))
    json.dump(dec, open(os.path.join(out, "decision.json"), "w"), indent=1, default=str)
    return dec


# ============================================================================ dry-run (synthetic only)
def dry_run(cfg, out, dev):
    c = copy.deepcopy(cfg)
    for k, v in cfg["dry_run_overrides"].items():
        sec, key = k.split(".", 1)
        node = c[sec]
        *path, last = key.split(".")
        for p in path:
            node = node[p]
        node[last] = v
    names = c["data"]["primary_machines"] = ["synthetic-A", "synthetic-B"]
    c["data"]["reserve_machines"] = []
    c["g0"]["pass_min_machines"] = 2
    c["validity"]["min_valid_machines"] = 2
    for i, m in enumerate(names):
        x = K.synthetic_series(N=c["dry_run"]["N"], C=c["dry_run"]["C"], seed=100 + i)
        P = K.prepare(x, c)
        for s in c["training"]["seeds"]:
            fit_machine_seed(c, P, m, s, os.path.join(out, m, f"seed{s}"), dev)
        knn_machine(c, P, m, os.path.join(out, m, "knn"), dev)
    return finalize(c, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["dry-run", "fit", "knn", "finalize"])
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--machine")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--smd-dir", default=os.environ.get("SMD_DIR", "data/external_real/smd"))
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    a = ap.parse_args()
    cfg = load_config(a.config)
    dev = torch.device(a.device)
    if a.cmd == "dry-run":
        dec = dry_run(cfg, a.out, dev)
        print(json.dumps({k: dec[k] for k in ("decision",) if k in dec}))
        return
    require_authorization(cfg)
    if a.cmd == "finalize":
        print(json.dumps(finalize(cfg, a.out)["decision"]))
        return
    man = manifest(cfg)
    m = a.machine
    allowed = cfg["data"]["primary_machines"] + cfg["data"]["reserve_machines"]
    if m not in allowed:
        raise SystemExit(f"{m} is not a G-L1 machine")
    try:
        x = K.load_train_split(os.path.join(a.smd_dir, f"{m}_train.txt"), man[m]["sha256"])
    except K.TechnicalInvalid as e:
        p = os.path.join(a.out, "technical_invalid.json")
        os.makedirs(a.out, exist_ok=True)
        d = json.load(open(p)) if os.path.exists(p) else {}
        d[m] = str(e); json.dump(d, open(p, "w"), indent=1)
        raise
    P = K.prepare(x, cfg)
    if a.cmd == "knn":
        knn_machine(cfg, P, m, os.path.join(a.out, m, "knn"), dev)
    else:
        fit_machine_seed(cfg, P, m, a.seed, os.path.join(a.out, m, f"seed{a.seed}"), dev)


if __name__ == "__main__":
    main()
