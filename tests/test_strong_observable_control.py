import inspect

import numpy as np

from scripts.strong_observable_control import _arm_matrix, _fit_arm, _rolling, array_sha, dense_windows, extract_stream, residual_o1, residual_o2


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


def test_arm_row_keys_are_identical_across_observable_arms():
    records = [
        {
            "H": np.zeros((2, 14)), "I": np.zeros((2, 234)),
            "O1": np.zeros((2, 128)), "O2": np.zeros((2, 1024)),
            "y": np.array([0, 1]), "source": np.array([3000, 3000]),
            "scenario": np.array(["abrupt", "abrupt"]), "condition": np.array(["none", "spike"]),
            "timestamp": np.array([63, 64]),
        },
        {
            "H": np.ones((1, 14)), "I": np.ones((1, 234)),
            "O1": np.ones((1, 128)), "O2": np.ones((1, 1024)),
            "y": np.array([1]), "source": np.array([3001]),
            "scenario": np.array(["gradual"]), "condition": np.array(["collective"]),
            "timestamp": np.array([63]),
        },
    ]
    h = _arm_matrix(records, "H")
    o2 = _arm_matrix(records, "H+O2")
    for key in ("y", "source", "scenario", "condition", "timestamp"):
        assert np.array_equal(h[key], o2[key])


def test_scaler_hash_is_fit_from_training_rows_only():
    train = {"X": np.array([[0.0, 1.0], [1.0, 2.0], [0.0, 2.0], [1.0, 1.0]]), "y": np.array([0, 1, 0, 1])}
    validation = {"X": np.array([[10.0, 10.0], [11.0, 11.0]]), "y": np.array([0, 1])}
    test = {"X": np.array([[12.0, 12.0], [13.0, 13.0]]), "y": np.array([0, 1])}
    info, _ = _fit_arm(train, validation, test, "H", 11)
    from sklearn.preprocessing import StandardScaler

    expected = StandardScaler().fit(train["X"])
    assert info["scaler_mean_sha256"] == array_sha(expected.mean_.astype(np.float64))
    assert info["scaler_scale_sha256"] == array_sha(expected.scale_.astype(np.float64))
