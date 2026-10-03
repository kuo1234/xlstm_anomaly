"""Rollback-semantics checks for Step 1c."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from p10_step1a_oracle import W1, W3  # noqa: E402
from p10_step1a1_diag import W2D, FeatW2, W1P  # noqa: E402
from p10_step1c_rollback import CFG1C, category, keep_mask, replay, w2_decay_replay, w2_subtract  # noqa: E402

rng = np.random.default_rng(3)


def _kv(n, d=16, dv=3, signed=False):
    K = rng.standard_normal((n, d)) if signed else np.abs(rng.standard_normal((n, d)))
    return K / np.linalg.norm(K, axis=1, keepdims=True), rng.standard_normal((n, dv))


def test_w2_subtract_equals_decay_only_replay():
    K0, V0 = _kv(500)
    K, V = _kv(80)
    keep = np.ones(80, bool); keep[10:40] = False; keep[50:55] = False
    for m0 in (W2D(16, 3, 0.995), FeatW2(16, 3, 0.995, "split")):
        if isinstance(m0, FeatW2):
            K0s, Ks = _kv(500, signed=True)[0], _kv(80, signed=True)[0]
        else:
            K0s, Ks = K0, K
        m0.write(K0s, V0)
        full = replay(m0, Ks, V, np.ones(80, bool))
        a = w2_subtract(full, Ks, V, keep)
        b = w2_decay_replay(m0, Ks, V, keep)
        assert np.abs(a.C - b.C).max() < 1e-9 and np.abs(a.n - b.n).max() < 1e-9


def test_w1_tag_delete_equals_replay_and_w3_replay_exact():
    K0, V0 = _kv(300)
    K, V = _kv(60)
    keep = np.ones(60, bool); keep[5:35] = False
    p = W1P(5); p.write(K0, V0, src=0, t=np.arange(300)); p.write(K, V, src=1, t=300 + np.arange(60))
    deleted = p.tt >= 0
    deleted[:300] = False
    deleted[300:] = ~keep
    w = W1(5); w.write(K0, V0)
    r = replay(w, K, V, keep)
    Q = _kv(40)[0]
    pk = W1(5); pk.write(p.K[~deleted], p.V[~deleted])
    assert np.allclose(pk.read(Q), r.read(Q))
    m3 = W3(16, 3, 0.5); m3.write(K0, V0)
    a = replay(m3, K, V, keep)
    b = W3(16, 3, 0.5); b.write(K0, V0); b.write(K[keep], V[keep])
    assert np.allclose(a.C, b.C)


def test_categories_and_masks():
    cat = category(np.arange(0, 46 + 64), 30, 8)
    assert (cat == "fault").sum() == 30 and (cat == "recovery").sum() == 8
    in_seg = np.arange(110) < 46
    assert keep_mask("R_all", cat, in_seg).sum() == 64
    assert keep_mask("R_fault_rec", cat, in_seg).sum() == 72
    assert CFG1C["eval_start"] >= max(CFG1C["seg_L"]) + max(CFG1C["delays"]) + 16
    assert min(CFG1C["deltas"]) + 30 >= CFG1C["eval_start"]
