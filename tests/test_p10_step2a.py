"""Step 2a checks: label gating, rollback semantics of the streaming memories, causality of the score trace."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import p10_step2a_data as D  # noqa: E402
from p10_step2a_stream import CFG2A, W1S, W2S, W3S, run_policy  # noqa: E402

rng = np.random.default_rng(5)


def _kv(n, dk=16, dv=3):
    K = np.abs(rng.standard_normal((n, dk)))
    return K / np.linalg.norm(K, axis=1, keepdims=True), rng.standard_normal((n, dv))


def test_label_gate_refuses_without_seal(tmp_path):
    with pytest.raises(D.ProtocolViolation):
        D.load_test_labels("machine-1-6", purpose="step2a_final_evaluation", seal_path=tmp_path / "seal.json",
                           label_root=tmp_path, expected_seal_sha="0" * 64)
    with pytest.raises(D.ProtocolViolation):
        D.load_test_labels("machine-1-6", purpose="peek", seal_path=tmp_path / "seal.json", label_root=tmp_path,
                           expected_seal_sha="0" * 64)
    with pytest.raises(D.ProtocolViolation):
        D.load_observations("machine-1-6", "test_label", tmp_path)


def test_stream_runner_has_no_label_path():
    src = (Path(__file__).resolve().parents[1] / "scripts" / "p10_step2a_stream.py").read_text()
    assert "load_test_labels" not in src and "test_label" not in src


def test_rollbacks_equal_never_written_or_decay_kept():
    K0, V0 = _kv(300); K, V = _kv(64); t = np.arange(64)
    hit = lambda tt: (tt >= 20) & (tt < 40)
    keep = ~hit(t)
    # W1: deletion == never written
    a = W1S(400, 16, 3, 5); a.write(K0, V0, -np.ones(300, np.int64)); a.write(K, V, t); a.rollback(hit)
    b = W1S(400, 16, 3, 5); b.write(K0, V0, -np.ones(300, np.int64)); b.write(K[keep], V[keep], t[keep])
    Q = _kv(30)[0]
    assert np.allclose(a.read(Q), b.read(Q))
    # W3: checkpoint + replay == never written
    a = W3S(16, 3, 0.1); a.write(K0, V0)
    for j in range(0, 64, 16):
        a.checkpoint(); a.write(K[j:j + 16], V[j:j + 16], t[j:j + 16])
    a.rollback(hit)
    b = W3S(16, 3, 0.1); b.write(K0, V0); b.write(K[keep], V[keep])
    assert np.allclose(a.C, b.C)
    # W2: subtraction == replay with removed writes as decay-only steps
    a = W2S(16, 3, 0.99); a.write(K0, V0); a.write(K, V, t); a.rollback(hit)
    b = W2S(16, 3, 0.99); b.write(K0, V0)
    for j in range(64):
        if keep[j]:
            b.write(K[j:j + 1], V[j:j + 1])
        else:
            b.C *= b.f; b.nv *= b.f
    assert np.allclose(a.C, b.C) and np.allclose(a.nv, b.nv)


def test_score_before_write_causality():
    K0, V0 = _kv(200); K, V = _kv(96)
    def builder():
        m = W1S(400, 16, 3, 5); m.write(K0, V0, -np.ones(200, np.int64)); return m
    r1 = run_policy("B_always", "W1", builder, K, V, 1.0, CFG2A)
    V2 = V.copy(); V2[60:] += 50.0                      # change the future only
    r2 = run_policy("B_always", "W1", builder, K, V2, 1.0, CFG2A)
    assert np.allclose(r1["score"][:48], r2["score"][:48])   # blocks fully before t=60 unchanged
