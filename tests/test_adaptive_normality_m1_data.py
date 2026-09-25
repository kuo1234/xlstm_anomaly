import sys
import hashlib
import io
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import adaptive_normality_m1_data as m1


def test_forecast_indices_are_exclusive_and_cover_first_internal_final_targets():
    n, w = 1000, 256
    indices = m1.forecast_target_indices((0, n), window=w)
    assert indices[0] == w
    assert indices[11] == w + 11
    assert indices[-1] == n - 1
    x = np.arange(n * 2, dtype=np.int64).reshape(n, 2)
    for t in (indices[0], indices[11], indices[-1]):
        context, target = m1.forecast_sample(x, int(t), (0, n), window=w)
        assert np.array_equal(context, x[t - w:t])
        assert np.array_equal(target, x[t])
        assert context.tobytes() == x[t - w:t].tobytes()
        assert t not in np.arange(t - w, t)


def test_fit_validation_calibration_boundaries_do_not_cross():
    n = 2000
    blocks = m1.train_blocks(n)
    fit, val, cal = blocks["fit"], blocks["validation"], blocks["calibration"]
    assert fit == (0, 1400)
    assert val == (1400, 1700)
    assert cal == (1700, 2000)
    assert m1.forecast_target_indices(fit)[-1] == 1399
    assert m1.forecast_target_indices(val)[0] == 1656
    assert m1.forecast_target_indices(cal)[0] == 1956
    x = np.arange(n)
    with pytest.raises(m1.M1DataError):
        m1.forecast_sample(x, 1400, fit)
    with pytest.raises(m1.M1DataError):
        m1.forecast_sample(x, 1700, val)
    # The first target in each following block starts after its own warm-up.
    for bounds in (val, cal):
        target = bounds[0] + m1.W
        context, _ = m1.forecast_sample(x, target, bounds)
        assert context[0] == bounds[0]
        assert context[-1] == target - 1


def test_test_forecast_warmup_begins_exactly_at_256_without_padding():
    targets = m1.test_forecast_targets(300)
    assert targets[0] == 256
    assert targets[-1] == 299
    assert len(targets) == 44
    with pytest.raises(m1.M1DataError):
        m1.forecast_sample(np.zeros((300, 1)), 255, (0, 300))


def test_reconstruction_window_trails_and_ends_at_same_timestamp():
    x = np.arange(600 * 2).reshape(600, 2)
    for t in (m1.W - 1, 300, 599):
        window = m1.reconstruction_window_for_bounds(x, t, (0, 600))
        assert np.array_equal(window, x[t - m1.W + 1:t + 1])
        assert window.shape == (m1.W, 2)
    with pytest.raises(m1.M1DataError):
        m1.reconstruction_window_for_bounds(x, 1399, (1400, 1700))


def test_lazy_window_datasets_materialize_only_requested_samples():
    x = np.arange(800 * 3, dtype=np.float32).reshape(800, 3)
    forecast = m1.ForecastWindowDataset(x, (100, 500), window=32)
    assert len(forecast) == 368
    assert forecast.targets[0] == 132
    assert forecast.targets[-1] == 499
    assert not hasattr(forecast, "windows")
    for idx in (0, 87, len(forecast) - 1):
        context, target = forecast[idx]
        t = int(forecast.targets[idx])
        assert context.shape == (32, 3)
        assert np.array_equal(context, x[t - 32:t])
        assert np.array_equal(target, x[t])

    reconstruction = m1.ReconstructionWindowDataset(x, (100, 500), window=32)
    assert len(reconstruction) == 369
    assert reconstruction.timestamps[0] == 131
    assert reconstruction.timestamps[-1] == 499
    assert not hasattr(reconstruction, "windows")
    for idx in (0, 87, len(reconstruction) - 1):
        window, t = reconstruction[idx]
        assert window.shape == (32, 3)
        assert np.array_equal(window, x[t - 31:t + 1])


def test_robust_transform_exactness_repeatability_dtype_and_clip():
    rng = np.random.default_rng(19)
    x = rng.normal(size=(1000, m1.D)).astype(np.float64)
    x[:, 17] = 4.0
    fit_end = 700
    scaler = m1.RobustScaler().fit(x, fit_end)
    fit = x[:fit_end]
    center = np.median(fit, axis=0)
    mad = 1.4826 * np.median(np.abs(fit - center), axis=0)
    q05, q95 = np.quantile(fit, [0.05, 0.95], axis=0, method="linear")
    robust = np.maximum(mad, (q95 - q05) / 3.2897072539)
    expected_floor = 0.05 * np.median(robust[robust > 0])
    expected_scale = np.maximum(robust, expected_floor)
    assert np.array_equal(scaler.statistics.center, center)
    assert np.array_equal(scaler.statistics.raw_robust_scale, robust)
    assert np.array_equal(scaler.statistics.scale, expected_scale)
    assert scaler.statistics.scale_floor == expected_floor
    assert scaler.statistics.fit_rows == (0, fit_end)
    assert scaler.statistics.scale[17] == expected_floor
    transformed_a = scaler.transform(x)
    transformed_b = scaler.transform(x)
    assert transformed_a.dtype == np.float32
    assert np.array_equal(transformed_a, transformed_b)
    assert np.max(np.abs(transformed_a)) <= 50.0
    x_extreme = x.copy()
    x_extreme[-1, 0] = center[0] + expected_scale[0] * 1000
    assert scaler.transform(x_extreme)[-1, 0] == np.float32(50.0)


def test_robust_transform_fails_closed_without_any_positive_scale():
    with pytest.raises(m1.M1DataError, match="no positive robust"):
        m1.fit_robust_transform(np.zeros((100, m1.D), dtype=np.float64))


def test_machine_1_4_channel_17_recorded_train_only_scale_regression():
    # Audit record: channel 17 fit std=1.63e-5; both raw robust scales are zero;
    # frozen machine-relative scale floor=0.00145873, with no channel removal.
    center = np.zeros(m1.D, dtype=np.float64)
    scale = np.full(m1.D, 1.0, dtype=np.float64)
    scale[17] = 0.00145873
    robust = np.ones(m1.D, dtype=np.float64)
    robust[17] = 0.0
    transform = m1.RobustTransform(center, scale, robust, 0.00145873, (0, 16594))
    sample = np.zeros((1, m1.D), dtype=np.float64)
    sample[0, 17] = 0.0554
    result = m1.apply_robust_transform(sample, transform)
    assert result[0, 17] == np.float32(0.0554 / 0.00145873)
    assert result[0, 17] < 50.0
    assert 0.00145873 / 1.63e-5 == pytest.approx(89.5, rel=0.01)


def test_manifest_and_loader_contract_excludes_label_api():
    assert len(m1.MACHINES) == 28
    assert sum(len({key for key in parts if key in {"train", "test", "test_label"}})
               for parts in m1.MANIFEST["machines"].values()) == 84
    assert all({"train", "test", "test_label"}.issubset(parts)
               for parts in m1.MANIFEST["machines"].values())
    assert not hasattr(m1, "load_test_labels")
    assert not hasattr(m1, "test_label_path")
    with pytest.raises(m1.M1DataError):
        m1.raw_path(m1.MACHINES[0], "test_label")


def test_acquisition_rejects_bad_download_without_installing_or_label_requests(tmp_path, monkeypatch):
    machine = m1.MACHINES[0]
    monkeypatch.setattr(m1, "MACHINES", (machine,))
    called = []
    monkeypatch.setattr(m1.urllib.request, "urlopen",
                        lambda url, timeout: (called.append(url) or io.BytesIO(b"wrong bytes")))
    report = m1.acquire_observations(tmp_path)
    assert report["status"] == "DATA_PROVENANCE_BLOCKED"
    assert report["files"][0]["status"] == "DATA_PROVENANCE_BLOCKED_DOWNLOAD_MISMATCH"
    assert len(called) == 2
    assert all("/train/" in url or "/test/" in url for url in called)
    assert not any("test_label" in url for url in called)
    assert not list(tmp_path.glob("*.txt"))
    assert not list(tmp_path.glob("*.partial"))


def test_acquisition_preserves_differing_existing_file(tmp_path, monkeypatch):
    machine = m1.MACHINES[0]
    monkeypatch.setattr(m1, "MACHINES", (machine,))
    target = tmp_path / f"{machine}_train.txt"
    target.write_bytes(b"preexisting untrusted bytes")
    monkeypatch.setattr(m1.urllib.request, "urlopen",
                        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must not download over existing file")))
    report = m1.acquire_observations(tmp_path)
    assert report["files"][0]["status"] == "DATA_PROVENANCE_BLOCKED_EXISTING_MISMATCH"
    assert target.read_bytes() == b"preexisting untrusted bytes"


def test_loader_rejects_manifest_row_count_mismatch(tmp_path, monkeypatch):
    machine = m1.MACHINES[0]
    path = tmp_path / f"{machine}_train.txt"
    payload = b"1,2\n3,4\n"
    path.write_bytes(payload)
    entry = m1.MANIFEST["machines"][machine]
    monkeypatch.setitem(entry["train"], "bytes", len(payload))
    monkeypatch.setitem(entry["train"], "sha256", hashlib.sha256(payload).hexdigest())
    monkeypatch.setitem(entry, "train_rows", 3)
    with pytest.raises(m1.M1DataError, match="invalid observation schema"):
        m1.load_observations(machine, "train", tmp_path)
