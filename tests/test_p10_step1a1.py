"""Unit checks for Step 1a.1 diagnostics operators."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from p10_step1a1_diag import W1P, W2D, W2S, PhiPCA  # noqa: E402

rng = np.random.default_rng(1)


def test_decay_only_equals_write_of_zero_values():
    K = rng.standard_normal((50, 16)); K /= np.linalg.norm(K, axis=1, keepdims=True)
    V = rng.standard_normal((50, 3))
    for M in (lambda: W2D(16, 3, 0.99), lambda: W2S(16, 3, 0.99)):
        a, b = M(), M()
        a.write(K, V); b.write(K, V)
        a.decay(20)
        b.write(K[:20], np.zeros((20, 3)))     # decay with zero value == decay-only for C
        assert np.allclose(a.C, b.C)


def test_w2s_sequential_and_regression():
    d = 32
    Q, _ = np.linalg.qr(rng.standard_normal((d, d)))
    K = rng.standard_normal((20000, d)) @ Q; K /= np.linalg.norm(K, axis=1, keepdims=True)
    A = rng.standard_normal((2, d))
    m = W2S(d, 2, 1.0); m.write(K[:7000], K[:7000] @ A.T); m.write(K[7000:], K[7000:] @ A.T)
    assert abs(m.c - 20000) < 1e-6
    q = K[:200]
    err = np.abs(m.read(q) - q @ A.T).mean() / np.abs(q @ A.T).mean()
    assert err < 0.1                            # isotropic keys: Hebbian read ~ regression


def test_pca_phi_whitened_and_w1p_provenance():
    z = rng.standard_normal((3000, 5))
    phi = PhiPCA(z, np.arange(8, 2000), 8, 10)
    F = phi(z, np.arange(8, 2000))
    assert np.allclose(np.linalg.norm(F, axis=1), 1, atol=1e-6) and (F < 0).any()
    m = W1P(3); m.write(F[:100], z[8:108], src=0, t=np.arange(100)); m.write(F[100:110], z[108:118], src=1, t=np.arange(100, 110))
    p = m.provenance(F[100:110], np.arange(100, 110))
    assert p["top1_A1"] == 1.0 and p["top1_dt_median"] == 0
