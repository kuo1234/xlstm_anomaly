import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mlstm_dense_attribution import expand_base, history14, select_stride  # noqa: E402
from mlstm_probe import expand234, history14 as old_history14  # noqa: E402


def test_dense_history_and_expansion_match_existing_schema():
    rng = np.random.default_rng(11)
    for length in (3, 4, 32, 64):
        values = rng.normal(size=length)
        np.testing.assert_allclose(history14(values), old_history14(values), equal_nan=True)
    base = rng.normal(size=(64, 18))
    np.testing.assert_allclose(expand_base(base), expand234(base), equal_nan=True)


def test_stride_selection_precedes_downstream_rolling():
    arrays = {
        "timestamp": np.arange(63, 63 + 10 * 32, dtype=np.int64),
        "score": np.arange(10 * 32, dtype=np.float32),
    }
    sparse = select_stride(arrays, 32)
    np.testing.assert_array_equal(sparse["timestamp"], np.array([63, 95, 127, 159, 191, 223, 255, 287, 319, 351]))


def test_expected_family_dimensions():
    rng = np.random.default_rng(0)
    n = 40
    h = history14(rng.normal(size=n))
    assert h.shape == (n, 14)
    assert expand_base(rng.normal(size=(n, 4))).shape == (n, 52)
    assert expand_base(rng.normal(size=(n, 6))).shape == (n, 78)
    assert expand_base(rng.normal(size=(n, 18))).shape == (n, 234)
