import inspect

import numpy as np

from scripts.strong_observable_control import _rolling, dense_windows, extract_stream, residual_o1, residual_o2


def test_o1_o2_dimensions_and_finite_zero_variance_rule():
    residual = np.zeros((2, 64, 8), dtype=np.float32)
    residual[0, :, 0] = np.arange(64, dtype=np.float32)
    o1 = residual_o1(residual)
    o2 = residual_o2(residual)
    assert o1.shape == (2, 128)
    assert o2.shape == (2, 1024)
    assert np.isfinite(o1).all()
    assert np.isfinite(o2).all()
    # A zero-variance channel has deterministic zero autocorrelation and
    # zero correlation entries, including its diagonal.
    assert np.all(o1[:, 8 + 7] == 0.0)
    assert np.all(o1[:, 64 + 8] == 0.0)


def test_o2_chronological_channel_flatten_order():
    residual = np.arange(64 * 8, dtype=np.float32).reshape(1, 64, 8)
    o2 = residual_o2(residual)
    assert np.array_equal(o2[0, :512], residual.reshape(-1))
    assert np.array_equal(o2[0, 512:], (residual * residual).reshape(-1))


def test_dense_windows_are_right_edge_causal():
    observations = np.arange(80 * 8, dtype=np.float32).reshape(80, 8)
    windows, timestamps = dense_windows(observations)
    assert timestamps[0] == 63
    assert timestamps[-1] == 79
    assert np.array_equal(windows[0], observations[:64])
    assert np.array_equal(windows[-1], observations[16:80])


def test_vectorized_rolling_matches_direct_window_formula():
    values = np.arange(20, dtype=np.float64)[:, None] ** 2
    got = _rolling(values, 4)
    expected = np.full_like(got, np.nan)
    t = np.arange(4, dtype=np.float64) - 1.5
    for end in range(3, len(values)):
        window = values[end - 3 : end + 1]
        expected[end] = np.concatenate((window.mean(0), window.std(0), (window * t[:, None]).sum(0) / np.square(t).sum()))
    assert np.allclose(got, expected, equal_nan=True)


def test_extractor_signature_is_observation_only():
    names = set(inspect.signature(extract_stream).parameters)
    assert not names.intersection({"labels", "truth", "metadata", "event", "scenario", "condition"})
