"""Step 2a (issue #15 comment 5969872677): real-stream, non-oracle admission / quarantine / rollback pilot.

LABEL-BLIND STAGE.  This script reads SMD train and test *observations* only (p10_step2a_data.load_observations) and
writes per-run score traces plus a seal manifest.  It has no code path that opens a label file.

Detector (same role as Step 1a-1c): normal-reference memory with retrieval prediction
    key k_t = phi(z[t-8:t]) (fixed random ReLU features, d_k = 128, seeds 11/22/33), value v_t = z_t,
    anomaly score s_t = ||v_t - M(k_t)||_2, computed BEFORE any write that includes t (score-before-write).
    Operators: W1 append/kNN (K=5), W2 Hebbian+normalizer f=.995, W3 delta rule beta=.1.
Scaling: all 38 channels, z-score with train mean/sd, sd floor 0.02, |z| clipped at 20.
M0 = first 80% of the train split.  Threshold tau = q0.99 of M0 scores on the last 20% of the train split.
The test stream is processed in 16-step blocks; each block is scored with the memory at block start, then the
policy decides which of its points are written.  Only causal quantities (scores so far, tau) are used.

Policies
    A no_update      never write
    B always         write every point
    C threshold      write a block only if no point in it exceeds tau
    D quarantine     clean blocks are written; a block with an exceedance goes to a quarantine buffer.  A clean block
                     discards the buffer; if the suspicious run reaches 32 blocks (512 steps) the buffer is promoted
                     (written) -- sustained deviation is treated as a new normal
    E rollback       write every point immediately (optimistic).  An exceedance run (gaps <= 8 tolerated) that reaches
                     8 exceedances triggers: suspicious interval S = [run_start - 8, last exceedance]; every memory entry
                     whose value time OR key window [t-8, t-1] intersects S is rolled back, and while/after the run no
                     point whose value or key window touches S is written (causal approximation of "fault-touched
                     writes", Step 1c).  Runs shorter than the trigger are kept.
    E_value          as E but only value time is checked (rollback of the admitted points only; Step 1c ablation)
    rand_C/D/E       random block-level writes with the same written fraction as C / D / E (seeded) -- separates
                     "fewer updates" from "the right updates"
Rollback semantics: W1 deletes entries by time tag; W2 subtracts f^age v k^T (and n); W3 restores the latest block
checkpoint before the earliest affected write and replays the kept writes (replayed-write count is logged).
"""
from __future__ import annotations

import collections
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p10_step1a_oracle import Phi  # noqa: E402
from p10_step2a_data import MACHINES, load_observations, sha256  # noqa: E402

CFG2A = dict(machines=list(MACHINES), phi_seeds=[11, 22, 33], w=8, dk=128, knn_k=5, sd_floor=0.02, z_clip=20.0,
             fit_frac=0.8, calib_q=0.99, block=16, ops=["W1", "W2_f0995", "W3_b01"],
             quarantine_promote_blocks=32, trigger_n=8, margin=8, run_gap=8, random_seed=907, vus_window=100,
             policies=["A_no_update", "B_always", "C_threshold", "D_quarantine", "E_rollback", "E_value",
                       "rand_C", "rand_D", "rand_E"])


# ============================================================================ streaming memories
class W1S:
    def __init__(self, cap, dk, dv, k):
        self.K, self.V = np.zeros((cap, dk)), np.zeros((cap, dv))
        self.tv, self.alive, self.n, self.k = np.zeros(cap, np.int64), np.zeros(cap, bool), 0, k
        self.replayed = 0

    def write(self, K, V, t):
        m = len(K)
        self.K[self.n:self.n + m], self.V[self.n:self.n + m], self.tv[self.n:self.n + m] = K, V, t
        self.alive[self.n:self.n + m] = True
        self.n += m

    def read(self, Q):
        S = Q @ self.K[:self.n].T
        S[:, ~self.alive[:self.n]] = -np.inf
        idx = np.argpartition(-S, self.k, axis=1)[:, :self.k]
        return self.V[idx].mean(1)

    def rollback(self, hit):          # hit(tv_array) -> bool mask
        m = self.alive[:self.n] & hit(self.tv[:self.n]) & (self.tv[:self.n] >= 0)
        self.alive[:self.n] &= ~m
        return int(m.sum())

    def size(self):
        return int(self.alive[:self.n].sum())


class _Ledger:
    def __init__(self):
        self.K, self.V, self.t, self.alive = [], [], [], []

    def add(self, K, V, t):
        self.K.extend(K); self.V.extend(V); self.t.extend(t); self.alive.extend([True] * len(t))


class W2S:
    def __init__(self, dk, dv, f):
        self.f, self.C, self.nv, self.nw, self.L = f, np.zeros((dv, dk)), np.zeros(dk), 0, _Ledger()
        self.replayed = 0

    def write(self, K, V, t=None):
        L = len(K)
        wts = self.f ** np.arange(L - 1, -1, -1.0)
        self.C = self.f ** L * self.C + (V * wts[:, None]).T @ K
        self.nv = self.f ** L * self.nv + wts @ K
        if t is not None:
            self.L.add(K, V, t)
        self.nw += L

    def read(self, Q):
        return (Q @ self.C.T) / np.maximum(np.abs(Q @ self.nv), 1.0)[:, None]

    def rollback(self, hit):
        if not self.L.t:
            return 0
        tt = np.asarray(self.L.t); al = np.asarray(self.L.alive)
        m = al & hit(tt)
        if not m.any():
            return 0
        idx = np.where(m)[0]
        n_led = len(tt)
        age = (self.nw - (self.nw - n_led) - 1 - idx).astype(float)     # later writes after each ledger entry
        Kr, Vr = np.asarray(self.L.K)[idx], np.asarray(self.L.V)[idx]
        w = self.f ** age
        self.C = self.C - (Vr * w[:, None]).T @ Kr
        self.nv = self.nv - w @ Kr
        for i in idx:
            self.L.alive[i] = False
        return int(len(idx))

    def size(self):
        return int(sum(self.L.alive))


class W3S:
    def __init__(self, dk, dv, beta):
        self.b, self.C, self.L = beta, np.zeros((dv, dk)), _Ledger()
        self.ckpt = collections.deque(maxlen=128)   # (ledger_len, C copy) at block starts
        self.replayed = 0

    def _apply(self, K, V):
        C, b = self.C, self.b
        for k, v in zip(K, V):
            C += b * np.outer(v - C @ k, k)
        self.C = C

    def checkpoint(self):
        self.ckpt.append((len(self.L.t), self.C.copy()))

    def write(self, K, V, t=None):
        self._apply(K, V)
        if t is not None:
            self.L.add(K, V, t)

    def read(self, Q):
        return Q @ self.C.T

    def rollback(self, hit):
        if not self.L.t:
            return 0
        tt = np.asarray(self.L.t); al = np.asarray(self.L.alive)
        m = al & hit(tt)
        if not m.any():
            return 0
        i0 = int(np.where(m)[0][0])
        for i in np.where(m)[0]:
            self.L.alive[i] = False
        cands = [c for c in self.ckpt if c[0] <= i0]
        if not cands:
            raise RuntimeError("rollback older than checkpoint horizon")
        n0, C0 = cands[-1]
        self.C = C0.copy()
        keep = [i for i in range(n0, len(self.L.t)) if self.L.alive[i]]
        if keep:
            self._apply(np.asarray(self.L.K)[keep], np.asarray(self.L.V)[keep])
        self.replayed += len(keep)
        return int(m.sum())

    def size(self):
        return int(sum(self.L.alive))


def make_mem(op, cap, dk, dv, k):
    return {"W1": lambda: W1S(cap, dk, dv, k), "W2_f0995": lambda: W2S(dk, dv, 0.995),
            "W3_b01": lambda: W3S(dk, dv, 0.1)}[op]()


def scores(mem, Q, V):
    return np.linalg.norm(V - mem.read(Q), axis=1)


# ============================================================================ data
def scale(train, test, cfg):
    mu, sd = train.mean(0), np.maximum(train.std(0), cfg["sd_floor"])
    f = lambda x: np.clip((x - mu) / sd, -cfg["z_clip"], cfg["z_clip"])
    return f(train), f(test)


# ============================================================================ one streaming run
def run_policy(policy, op, M0_builder, Kt, Vt, tau, cfg, p_write=None, rng=None):
    w, B, N = cfg["w"], cfg["block"], len(Kt)
    mem = M0_builder()
    s_all = np.zeros(N, np.float32)
    written = np.zeros(N, bool)
    events = dict(promotions=0, discards=0, quarantined_points=0, rollbacks=[], n_removed=0)
    buf = []                         # quarantine: list of (j0, j1)
    # rollback state
    run_start, last_exc, run_cnt, trig = None, None, 0, False
    S_list = []                      # suspicious intervals (start, end) in test time
    use_key = policy == "E_rollback"

    def touched(tt):
        if not S_list:
            return np.zeros(len(tt), bool)
        m = np.zeros(len(tt), bool)
        for a, b in S_list:
            m |= (tt >= a) & (tt <= b)
            if use_key:
                m |= (tt - w <= b) & (tt - 1 >= a)
        return m

    t0 = time.time()
    for j0 in range(0, N, B):
        j1 = min(j0 + B, N)
        if isinstance(mem, W3S):
            mem.checkpoint()
        s = scores(mem, Kt[j0:j1], Vt[j0:j1])
        s_all[j0:j1] = s
        exc = s > tau
        wmask = np.zeros(j1 - j0, bool)
        if policy == "B_always":
            wmask[:] = True
        elif policy == "C_threshold":
            wmask[:] = not exc.any()
        elif policy == "D_quarantine":
            if not exc.any():
                if buf:
                    events["discards"] += 1
                    buf = []
                wmask[:] = True
            else:
                buf.append((j0, j1))
                events["quarantined_points"] += j1 - j0
                if len(buf) >= cfg["quarantine_promote_blocks"]:
                    for a, b in buf:
                        mem.write(Kt[a:b], Vt[a:b], np.arange(a, b))
                        written[a:b] = True
                    events["promotions"] += 1
                    buf = []
        elif policy in ("E_rollback", "E_value"):
            extended = False
            for i, j in enumerate(range(j0, j1)):
                if exc[i]:
                    if run_start is None or j - last_exc > cfg["run_gap"]:
                        run_start, run_cnt, trig = j, 0, False
                    run_cnt += 1
                    last_exc = j
                    if not trig and run_cnt >= cfg["trigger_n"]:
                        trig = True
                        S_list.append([run_start - cfg["margin"], j])
                        events["rollbacks"].append(dict(t=j, start=run_start - cfg["margin"], n_removed=0))
                        extended = True
                    elif trig:
                        S_list[-1][1] = j
                        extended = True
            if extended:                              # roll back every stored write the (grown) interval touches
                n_rm = mem.rollback(touched)
                events["rollbacks"][-1]["n_removed"] += n_rm
                events["n_removed"] += n_rm
                written[:j0] &= ~touched(np.arange(j0))
            tt = np.arange(j0, j1)
            wmask[:] = ~touched(tt)
        elif policy.startswith("rand_"):
            wmask[:] = rng.random() < p_write
        if policy != "D_quarantine" or wmask.any():
            idx = np.where(wmask)[0] + j0
            if len(idx):
                mem.write(Kt[idx], Vt[idx], idx)
                written[idx] = True
    return dict(score=s_all, written=written, events=events, mem_size=mem.size(), replayed=mem.replayed,
                runtime_s=time.time() - t0)


def run_unit(machine, seed, op, train_root, test_root, out, cfg=CFG2A):
    tr = load_observations(machine, "train", train_root)
    te = load_observations(machine, "test", test_root)
    ztr, zte = scale(tr, te, cfg)
    C, w = ztr.shape[1], cfg["w"]
    phi = Phi(C, w, cfg["dk"], seed)
    fit_end = int(len(ztr) * cfg["fit_frac"])
    t_fit = np.arange(w, fit_end)
    K0, V0 = phi(ztr, t_fit), ztr[t_fit]
    t_cal = np.arange(fit_end, len(ztr))
    Kc, Vc = phi(ztr, t_cal), ztr[t_cal]
    zext = np.concatenate([ztr[-w:], zte])
    Kt, Vt = phi(zext, np.arange(w, len(zext))), zte
    cap = len(K0) + len(Kt) + 16

    def builder():
        m = make_mem(op, cap, cfg["dk"], C, cfg["knn_k"])
        if isinstance(m, W1S):
            m.write(K0, V0, -np.ones(len(K0), np.int64))       # M0 entries carry no test time
        else:
            m.write(K0, V0)
        return m
    m0 = builder()
    tau = float(np.quantile(scores(m0, Kc, Vc), cfg["calib_q"]))
    res, metas = {}, []
    for pol in ["A_no_update", "B_always", "C_threshold", "D_quarantine", "E_rollback", "E_value"]:
        res[pol] = run_policy(pol, op, builder, Kt, Vt, tau, cfg)
    for base in ("C", "D", "E"):
        src = {"C": "C_threshold", "D": "D_quarantine", "E": "E_rollback"}[base]
        p = float(res[src]["written"].mean())
        rng = np.random.default_rng([cfg["random_seed"], seed, MACHINES.index(machine), ord(base)])
        res[f"rand_{base}"] = run_policy(f"rand_{base}", op, builder, Kt, Vt, tau, cfg, p_write=p, rng=rng)
    out = Path(out)
    (out / "traces").mkdir(parents=True, exist_ok=True)
    for pol, r in res.items():
        name = f"traces/{machine}__s{seed}__{op}__{pol}.npz"
        np.savez_compressed(out / name, score=r["score"], written=r["written"])
        ev = r["events"]
        metas.append(dict(machine=machine, phi_seed=seed, op=op, policy=pol, tau=tau, file=name,
                          n_test=len(Kt), written_frac=float(r["written"].mean()), mem_size_end=r["mem_size"],
                          promotions=ev["promotions"], discards=ev["discards"],
                          quarantined_points=ev["quarantined_points"], n_rollbacks=len(ev["rollbacks"]),
                          n_removed=ev["n_removed"],
                          mean_rollback_span=float(np.mean([e["t"] - e["start"] for e in ev["rollbacks"]]))
                          if ev["rollbacks"] else 0.0,
                          replayed_writes=r["replayed"], runtime_s=r["runtime_s"],
                          rollback_events=ev["rollbacks"]))
    print(f"{machine} s{seed} {op} tau={tau:.3f} done", flush=True)
    return metas


def _job(a):
    return run_unit(*a)


if __name__ == "__main__":
    import argparse
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-root", required=True)
    ap.add_argument("--test-root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--procs", type=int, default=12)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(m, s, op, a.train_root, a.test_root, str(out)) for m in CFG2A["machines"] for s in CFG2A["phi_seeds"]
            for op in CFG2A["ops"]]
    with Pool(a.procs) as pool:
        metas = [x for r in pool.map(_job, jobs) for x in r]
    (out / "runs.json").write_text(json.dumps(metas, indent=1))
    (out / "policy_config.json").write_text(json.dumps(CFG2A, indent=1))
    here = Path(__file__).resolve().parent
    files = {m["file"]: sha256(out / m["file"]) for m in metas}
    files["runs.json"] = sha256(out / "runs.json")
    files["policy_config.json"] = sha256(out / "policy_config.json")
    seal = dict(stage="step2a_label_blind_scores", machines=CFG2A["machines"], files=files,
                code={p: sha256(here / p) for p in ("p10_step2a_stream.py", "p10_step2a_data.py",
                                                    "p10_step1a_oracle.py")},
                observations={f"{m}_{s}": sha256(Path(a.train_root if s == "train" else a.test_root) / f"{m}_{s}.txt")
                              for m in CFG2A["machines"] for s in ("train", "test")},
                labels_read=0, utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    (out / "seal.json").write_text(json.dumps(seal, indent=1, sort_keys=True))
    print("seal.json", sha256(out / "seal.json"))
