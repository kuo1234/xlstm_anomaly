"""Unit checks for the Step 1a memory operators (role-matched: same keys, values, score)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from p10_step1a_oracle import W1, W2, W3, Phi  # noqa: E402

rng = np.random.default_rng(0)


def _kv(n=300, dk=32, dv=5):
    K = np.abs(rng.standard_normal((n, dk)))
    K /= np.linalg.norm(K, axis=1, keepdims=True)
    return K, rng.standard_normal((n, dv))


def test_w2_closed_form_equals_sequential():
    K, V = _kv()
    for f in (1.0, 0.995, 0.9):
        a = W2(32, 5, f)
        a.write(K[:100], V[:100]); a.write(K[100:], V[100:])
        C, n = np.zeros((5, 32)), np.zeros(32)
        for k, v in zip(K, V):
            C = f * C + np.outer(v, k); n = f * n + k
        assert np.abs(a.C - C).max() < 1e-9 and np.abs(a.n - n).max() < 1e-9


def test_w3_learns_linear_map_and_w1_exact_recall():
    K, _ = _kv(2000, 16, 3)
    A = rng.standard_normal((3, 16))
    m = W3(16, 3, 0.5)
    m.write(K, K @ A.T)
    assert np.abs(m.read(K[:50]) - K[:50] @ A.T).max() < 1e-2
    K2, V2 = _kv(50, 16, 3)
    w = W1(1); w.write(K2, V2)
    assert np.allclose(w.read(K2), V2)


def test_copy_isolation_and_phi_causal():
    K, V = _kv()
    for m in (W1(5), W2(32, 5, 0.99), W3(32, 5, 0.1)):
        m.write(K[:200], V[:200])
        before = m.read(K[:10]).copy()
        m2 = m.copy(); m2.write(K[200:], V[200:] + 10)
        assert np.allclose(m.read(K[:10]), before)
    z = rng.standard_normal((100, 4))
    phi = Phi(4, 8, 16, 11)
    k1 = phi(z, [50]); z2 = z.copy(); z2[50:] += 100
    assert np.allclose(phi(z2, [50]), k1)          # key at t uses only z[t-8 .. t-1]
    assert np.allclose(np.linalg.norm(phi(z, np.arange(10, 90)), axis=1), 1, atol=1e-4)
