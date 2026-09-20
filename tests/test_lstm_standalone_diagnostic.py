import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lstm_standalone_diagnostic import analyze_payload, reconstruct_lstm_effects  # noqa: E402


def _payload(h2, h3a_b):
    return {
        "verdict": "PASS_SCIENTIFIC_AUDIT",
        "recomputed_primary_effects": {
            "h2": np.asarray(h2, dtype=float).tolist(),
            "h3a_b": np.asarray(h3a_b, dtype=float).tolist(),
        },
    }


def test_elementwise_identity_delta_l_equals_h2_minus_h3a_b(tmp_path):
    h2 = np.full((10, 5), 0.14)
    h3a_b = np.full((10, 5), -0.002)
    result = reconstruct_lstm_effects(_payload(h2, h3a_b))
    np.testing.assert_array_equal(result["delta_l_own"], h2 - h3a_b)
    assert np.isclose(result["delta_l_own"].mean(), 0.142)


def test_aggregate_reconstruction_is_not_hard_coded(tmp_path):
    h2 = np.arange(50, dtype=float).reshape(10, 5) / 100.0
    h3a_b = np.linspace(-0.01, 0.01, 50).reshape(10, 5)
    audit = tmp_path / "audit.json"
    audit.write_text(json.dumps(_payload(h2, h3a_b)))
    result = analyze_payload(json.loads(audit.read_text()), audit)
    expected = float(np.mean(h2 - h3a_b))
    assert result["delta_l_own"]["mean"] == expected
    assert result["identity"]["aggregate_delta_l_own"] == expected


def test_authoritative_artifact_is_read_only(tmp_path):
    h2 = np.full((10, 5), 0.14)
    h3a_b = np.full((10, 5), -0.002)
    audit = tmp_path / "audit.json"
    audit.write_text(json.dumps(_payload(h2, h3a_b)))
    before = hashlib.sha256(audit.read_bytes()).digest()
    analyze_payload(json.loads(audit.read_text()), audit)
    assert hashlib.sha256(audit.read_bytes()).digest() == before
