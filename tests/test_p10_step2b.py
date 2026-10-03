"""Step 2b checks: label gating, trial-write copy semantics, causality of the segment / delayed-commit policies."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import p10_step2b_data as D  # noqa: E402
from p10_step2a_stream import W1S, W2S, W3S  # noqa: E402
from p10_step2b_stream import CFG2B, run_seg_policy, trial_scores  # noqa: E402

rng = np.random.default_rng(7)


def _kv(n, dk=16, dv=3):
    K = np.abs(rng.standard_normal((n, dk)))
    return K / np.linalg.norm(K, axis=1, keepdims=True), rng.standard_normal((n, dv))


def test_label_gate_requires_step2b_seal(tmp_path):
    with pytest.raises(D.ProtocolViolation):
        D.load_test_labels("machine-1-6", purpose="step2b_dev_evaluation", seal_path=tmp_path / "seal.json",
                           label_root=tmp_path, expected_seal_sha="0" * 64)
    with pytest.raises(D.ProtocolViolation):
        D.load_test_labels("machine-1-6", purpose="step2a_final_evaluation", seal_path=tmp_path / "seal.json",
                           label_root=tmp_path, expected_seal_sha="0" * 64)


def test_stream_runner_has_no_label_path():
    src = (Path(__file__).resolve().parents[1] / "scripts" / "p10_step2b_stream.py").read_text()
    assert "load_test_labels" not in src and "test_label" not in src


@pytest.mark.parametrize("kind", ["W1", "W2", "W3"])
def test_trial_write_leaves_memory_unchanged(kind):
    K0, V0 = _kv(200); Kw, Vw = _kv(40); Kq, Vq = _kv(30)
    m = {"W1": lambda: W1S(400, 16, 3, 5), "W2": lambda: W2S(16, 3, 0.995), "W3": lambda: W3S(16, 3, 0.1)}[kind]()
    m.write(K0, V0, -np.ones(200, np.int64)) if kind == "W1" else m.write(K0, V0)
    before = m.read(Kq).copy()
    s = trial_scores(m, Kw, Vw, Kq, Vq)
    assert np.allclose(m.read(Kq), before)
    # the trial really used the written entries
    m2 = {"W1": lambda: W1S(400, 16, 3, 5), "W2": lambda: W2S(16, 3, 0.995), "W3": lambda: W3S(16, 3, 0.1)}[kind]()
    m2.write(K0, V0, -np.ones(200, np.int64)) if kind == "W1" else m2.write(K0, V0)
    m2.write(Kw, Vw, -2 * np.ones(40, np.int64)) if kind == "W1" else m2.write(Kw, Vw)
    assert np.allclose(s, np.linalg.norm(Vq - m2.read(Kq), axis=1))


@pytest.mark.parametrize("pol", ["H_hold", "DE_stab", "DE_stab_lb", "C_lb"])
def test_segment_policies_are_causal(pol):
    K0, V0 = _kv(300); K, V = _kv(900)
    V = V * 0.2

    def builder():
        m = W1S(1400, 16, 3, 5); m.write(K0, V0, -np.ones(300, np.int64)); return m

    def ctx_for(Vx):
        frozen = {op: np.linalg.norm(Vx - builder().read(K), axis=1) for op in CFG2B["ops"]}
        return dict(cfg=CFG2B, tau=1.5, tau_low=1.2, Kt=K, Vt=Vx, K0=K0, frozen=frozen,
                    taus={op: 1.5 for op in CFG2B["ops"]},
                    zbase=lambda st: np.concatenate([np.zeros((256, 3)), Vx])[st:st + 256])
    V1 = V.copy(); V1[300:700] += 3.0                                  # sustained deviation
    V2 = V1.copy(); V2[800:] += 50.0                                   # change only the future
    r1, r2 = run_seg_policy(pol, builder, ctx_for(V1)), run_seg_policy(pol, builder, ctx_for(V2))
    assert np.allclose(r1["score"][:784], r2["score"][:784])
    c1 = [c for c in r1["checks"] if c["t"] <= 784]
    c2 = [c for c in r2["checks"] if c["t"] <= 784]
    assert [c["decision"] for c in c1] == [c["decision"] for c in c2]
