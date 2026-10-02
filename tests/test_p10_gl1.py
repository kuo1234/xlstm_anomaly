"""Tests for the P10 G-L1 runner (torch required; no SMD data needed)."""
import copy
import json
import os
import sys

import numpy as np
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("yaml")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import p10_gl1_core as K  # noqa: E402
import p10_gl1_models as M  # noqa: E402
import p10_gl1_run as Rn  # noqa: E402

CFG_PATH = os.path.join(ROOT, "configs", "p10_gl1_config.yaml")
RECUR = ["mlstm", "gdeltanet", "titans", "lstm"]


def small_cfg():
    cfg = Rn.load_config(CFG_PATH)
    c = copy.deepcopy(cfg)
    for k, v in cfg["dry_run_overrides"].items():
        sec, key = k.split(".", 1)
        c[sec][key] = v
    return c


def _st(m, B, dtype):
    return tuple(s.to(dtype) if torch.is_tensor(s) else s for s in m.init_state(B, "cpu"))


# ---------------------------------------------------------------- parity (chunk-parallel == step recurrence)
@pytest.mark.parametrize("name", RECUR)
@pytest.mark.parametrize("dtype,tol", [(torch.float64, 1e-10), (torch.float32, 1e-4)])
def test_parity_chunk_vs_step(name, dtype, tol):
    torch.manual_seed(0)
    m = M.build(name, 7).to(dtype)
    z = torch.randn(3, 203, 7, dtype=dtype)
    p1, s1 = m.forward(z[:, :70], _st(m, 3, dtype))      # 70 = non-multiple of 16 and 64
    p2, s2 = m.forward(z[:, 70:], s1)                     # state carried across calls
    pc = torch.cat([p1, p2], 1)
    st, ps = _st(m, 3, dtype), []
    for t in range(z.shape[1]):
        p, st = m.step(z[:, t], st)
        ps.append(p)
    assert float((pc - torch.stack(ps, 1)).abs().max()) < tol
    for a, b in zip(s2, st):
        if torch.is_tensor(a):
            assert float((a - b).abs().max()) < tol * 10
        else:
            assert a == b


# ---------------------------------------------------------------- score-before-write / causality
@pytest.mark.parametrize("name", RECUR)
def test_score_before_write_causal(name):
    torch.manual_seed(1)
    m = M.build(name, 5).double()
    z = torch.randn(1, 120, 5, dtype=torch.float64)
    p, _ = m.forward(z, _st(m, 1, torch.float64))
    z2 = z.clone(); z2[:, 61:] += 5.0                     # change the future from t=61
    q, _ = m.forward(z2, _st(m, 1, torch.float64))
    # pred index 60 (forecast of z[61]) must not depend on z[61] or later
    assert torch.allclose(p[:, :61], q[:, :61], atol=1e-12)
    assert not torch.allclose(p[:, 61:], q[:, 61:])


# ---------------------------------------------------------------- reset alignment
@pytest.mark.parametrize("name", RECUR + ["window_only"])
def test_reset_window_alignment(name):
    torch.manual_seed(2)
    R = 100
    m = M.build(name, 5)
    z = torch.randn(400, 5)
    e = np.array([250])
    base = K.windowed_preds(m, z, e, R, 8)
    for t_bad in (e[0] - R, e[0] + 1, e[0] + 2):            # outside [e-R+1, e]
        z2 = z.clone(); z2[t_bad] += 10.0
        assert torch.allclose(base, K.windowed_preds(m, z2, e, R, 8))
    z3 = z.clone(); z3[e[0]] += 10.0                         # inside the window
    assert not torch.allclose(base, K.windowed_preds(m, z3, e, R, 8))


# ---------------------------------------------------------------- parameter budget
@pytest.mark.parametrize("C", list(range(20, 36)))
def test_param_budget(C):
    lo, hi = Rn.load_config(CFG_PATH)["models"]["param_budget"]
    for name in ["mlstm", "gdeltanet", "titans", "lstm", "window_only", "mlstm_std"]:
        n = M.n_params(M.build(name, C))
        assert lo <= n <= hi, (name, C, n)


def test_config_arch_is_sealed(tmp_path):
    cfg = Rn.load_config(CFG_PATH)
    assert cfg["models"]["primary"] == "mlstm"
    assert cfg["training"]["drift_augmentation"] is False
    assert cfg["data"]["open_test_or_labels"] is False
    import yaml
    bad = copy.deepcopy(cfg); bad["models"]["arch"]["mlstm"]["forget_gate"] = "exp"
    p = tmp_path / "c.yaml"; p.write_text(yaml.safe_dump(bad))
    with pytest.raises(K.TechnicalInvalid):
        Rn.load_config(str(p))


# ---------------------------------------------------------------- label-blind data guard
def test_label_blind_loader(tmp_path):
    for nm in ("machine-1-1_test.txt", "machine-1-1_test_label.txt", "machine-1-1.txt"):
        f = tmp_path / nm; f.write_text("0,1\n1,2\n")
        with pytest.raises(K.TechnicalInvalid):
            K.load_train_split(str(f))
    f = tmp_path / "machine-1-1_train.txt"; f.write_text("0,1\n1,2\n")
    assert K.load_train_split(str(f)).shape == (2, 2)
    with pytest.raises(K.TechnicalInvalid):
        K.load_train_split(str(f), expected_sha="0" * 64)


def test_execution_requires_authorization(monkeypatch):
    monkeypatch.delenv("P10_GL1_AUTHORIZED", raising=False)
    with pytest.raises(SystemExit):
        Rn.require_authorization(Rn.load_config(CFG_PATH))


# ---------------------------------------------------------------- h05 measurement rules (blocker 2)
def test_h05_rules():
    lags = np.arange(1, 2049)
    R = np.exp(-lags / 200.0)
    h, st = K.h05_from_response(R, floor=1e-4, ref_lags=16, unstable_factor=2.0)
    assert st == "ok" and abs(h - int(np.ceil(-200 * np.log(0.05 * R[:16].max())))) <= 2
    h, st = K.h05_from_response(np.full(2048, 1e-6), floor=1e-4, ref_lags=16, unstable_factor=2.0)
    assert st == "not_measurable" and h == 0
    Ru = R.copy(); Ru[1500] = 5.0
    assert K.h05_from_response(Ru, 1e-4, 16, 2.0)[1] == "unstable"
    h, st = K.h05_from_response(np.ones(2048), 1e-4, 16, 2.0)
    assert st == "censored" and h == 2048
    # Titans-style delayed onset: first 15 lags zero, response from lag 16
    Rd = np.zeros(2048); Rd[15:] = np.exp(-(lags[15:] - 16) / 50.0)
    assert K.h05_from_response(Rd, 1e-4, 16, 2.0)[1] == "ok"


# ---------------------------------------------------------------- hierarchical bootstrap
def test_hier_boot_equal_weight_and_constant():
    D = np.zeros((4, 3, 10)); D[0] = 1.0                   # one machine of four
    pt, lo, hi = Rn.hier_boot(D, 500, 901)
    assert abs(pt - 0.25) < 1e-12 and lo <= pt <= hi
    pt, lo, hi = Rn.hier_boot(np.full((4, 3, 10), -0.03), 200, 901)
    assert pt == lo == hi == pytest.approx(-0.03)


# ---------------------------------------------------------------- plan / grid / Titans alignment
def test_plan_grid_and_titans_fork_alignment():
    c = small_cfg()
    P = K.prepare(K.synthetic_series(N=4000, C=5, seed=3), c)
    plan = K.make_plan(P, c, "synthetic-A")
    pts = list(plan.g0_pos) + [t for v in plan.onsets.values() for t in v]
    pts += [t + o for v in plan.onsets.values() for t in v for o in c["sentinel"]["offsets"].values()]
    assert all(int(p) % K.GRID == 0 for p in pts)
    assert P.fit_end % K.GRID == 0 and P.tr_end % K.GRID == 0
    m = M.build("titans", P.z.shape[1]).eval()
    _, caps, _ = K.run_capture(m, K.to_t(P.z, "cpu"), m.init_state(1, "cpu"), 0, P.z.shape[0] - 1, pts[:5])
    assert all(st[6] == 0 for st in caps.values())
    # plan is identical across calls (same for all models/arms)
    plan2 = K.make_plan(P, c, "synthetic-A")
    assert all((plan.onsets[f] == plan2.onsets[f]).all() for f in plan.onsets)


# ---------------------------------------------------------------- calibration isolation, sentinel no-write, weight identity
def _tiny_eval(c, name="mlstm", mag=None):
    c = copy.deepcopy(c)
    if mag is not None:
        c["utility"]["families"]["level"]["magnitude_sigma"] = mag
    P = K.prepare(K.synthetic_series(N=4000, C=5, seed=4), c)
    torch.manual_seed(0)
    m = M.build(name, P.z.shape[1]).eval()
    plan = K.make_plan(P, c, "synthetic-A")
    sig, _ = K.sigmas(m, name, P, c, "cpu", 1.0)
    before = {k: v.clone() for k, v in m.state_dict().items()}
    res = K.evaluate_fit(m, name, P, plan, c, "cpu", sig)
    after = m.state_dict()
    assert all(torch.equal(before[k], after[k]) for k in before)    # same weights both arms, unchanged
    return res


def test_calibration_isolation_and_weight_identity():
    c = small_cfg()
    a = _tiny_eval(c, mag=2.0)
    b = _tiny_eval(c, mag=5.0)                                         # changes only post-onset data
    ta = {(r["family"], r["ep"], r["arm"]): r["thr"] for r in a["episodes"]}
    tb = {(r["family"], r["ep"], r["arm"]): r["thr"] for r in b["episodes"]}
    assert ta == tb
    fa = {(r["family"], r["ep"], r["arm"]): r["fpr"] for r in a["episodes"] if r["family"] == "level"}
    assert {"persistent", "reset"} <= {k[2] for k in fa}


def test_sentinel_fork_does_not_write_main_state():
    torch.manual_seed(5)
    m = M.build("mlstm", 5).eval()
    z = torch.randn(1, 300, 5)
    _, st, _ = K.run(m, z[:, :128], m.init_state(1, "cpu"))
    snap = tuple(s.clone() for s in st)
    zs = z.clone(); zs[:, 128:158] += 4.0
    K._state_after(m, st, zs[:, 128:200])
    K.run(m, zs[:, 128:200], st)
    assert all(torch.equal(a, b) for a, b in zip(snap, st))


# ---------------------------------------------------------------- technical vs scientific failure (blocker 1)
def test_reserve_only_for_technical_invalid(tmp_path):
    c = Rn.load_config(CFG_PATH)
    (tmp_path / "technical_invalid.json").write_text(json.dumps({"machine-1-6": "SHA256 mismatch"}))
    eff, tech = Rn.effective_machines(c, str(tmp_path))
    assert "machine-1-6" not in eff and eff[-1] == "machine-2-6" and len(eff) == 6
    # scientific failure (nan training, poor fit) is never replaced and counts against P0
    os.remove(tmp_path / "technical_invalid.json")
    eff, _ = Rn.effective_machines(c, str(tmp_path))
    assert eff == c["data"]["primary_machines"]
    fits = [dict(model="mlstm", machine=m, seed=str(s), nan_train="True" if m in eff[:3] else "False",
                 val_ratio="1.0", diverged="False") for m in eff for s in (11, 22, 33)]
    res = Rn.evaluate_model(c, str(tmp_path), eff, "mlstm", [], [], fits)
    assert res["P0"] is False and res["label"] == "FAIL-FIT"
    assert len(res["P4_diverged_fits"]) == 9 and res["P4"] is False


def test_p1_is_not_an_inclusion_filter():
    """P2-P4 use all effective machines regardless of machine-level P1 (blocker 3)."""
    import inspect
    src = inspect.getsource(Rn.evaluate_model)
    assert "endpoint_arrays(cfg, eps, sents, machines," in src
    assert "mach_lvl" not in src.split("# P2 utility")[1]


# ---------------------------------------------------------------- end-to-end synthetic dry-run
@pytest.mark.slow
def test_dry_run_end_to_end(tmp_path):
    cfg = Rn.load_config(CFG_PATH)
    dec = Rn.dry_run(cfg, str(tmp_path), torch.device("cpu"))
    assert dec["decision"] in {"PASS", "FAIL-FIT", "FAIL-PERSIST", "FAIL-UTILITY", "FAIL-COLLAPSE", "FAIL-STABILITY"}
    r = dec["results"]["mlstm"]
    for k in ("P0", "P1", "P2", "P3", "P4", "P2_machine_effects", "P3_large_degradation_flags"):
        assert k in r
