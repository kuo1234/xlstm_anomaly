from pathlib import Path

import numpy as np
import pytest

from scripts.adaptive_normality_m1_scores import (
    CONTROL_ARMS, fixed_control_fusion, fit_normal_calibration,
    fit_ridge_var1, fixed_forecast_control_fusion, forecast_score,
    last_value_score, moving_median_score, normal_tail_severity,
    reconstruction_scores, ridge_var1_score, seal_score_artifact,
    verify_score_seal,
    higher_empirical_quantile,
    STAGE1_MACHINES, STAGE1_SCORE_DIR, STAGE1_SCORE_NAMES,
    seal_stage1_machine_scores,
)


def test_reconstruction_scores_share_endpoint_timestamp_and_residual_rules():
    y = np.zeros((3, 4, 2)); pred = y.copy(); times = np.array([256, 257, 258])
    for pos in (0, 2, 3):
        pred[:] = 0
        pred[:, pos, 0] = 2
        native, endpoint, out_times = reconstruction_scores(y, pred, times)
        assert np.array_equal(out_times, times)
        assert native == pytest.approx(4 / 8)
        assert endpoint.tolist() == ([2, 2, 2] if pos == 3 else [0, 0, 0])


def test_last_value_is_exact_squared_first_difference():
    z = np.array([[1, 2], [4, 6], [5, 7]], dtype=np.float32)
    values, times = last_value_score(z, [10, 11, 12])
    expected = np.square(z[1:] - z[:-1]).mean(axis=1).astype(np.float64)
    np.testing.assert_array_equal(values, expected)
    np.testing.assert_array_equal(times, [11, 12])


def test_moving_median_uses_only_preceding_window():
    z = np.array([[0.], [0.], [100.], [0.], [100.]])
    values, times = moving_median_score(z, 2)
    assert values[0] == 10000  # median(z[0:2]); current 100 is excluded
    assert values[1] == 2500  # median(z[1:3]); current row is excluded
    np.testing.assert_array_equal(times, [2, 3, 4])


def test_ridge_var1_dimensions_penalty_and_scoring_alignment():
    rng = np.random.default_rng(4)
    train = rng.normal(size=(40, 3))
    intercept, coef = fit_ridge_var1(train)
    assert intercept.shape == (3,)
    assert coef.shape == (3, 3)
    scores, times = ridge_var1_score(train, intercept, coef)
    assert scores.shape == (39,)
    np.testing.assert_array_equal(times, np.arange(1, 40))
    with pytest.raises(ValueError):
        fit_ridge_var1(train, lam=0.5)


def test_calibration_tail_severity_and_fixed_fusions_require_exact_timestamps():
    ref = fit_normal_calibration(np.array([1., 2., 3.]))
    np.testing.assert_allclose(normal_tail_severity(np.array([0., 2., 4.]), ref), -np.log10([1., 3/4, 1/4]))
    times = np.array([256, 257])
    controls = {name: (np.full(2, i, dtype=float), times) for i, name in enumerate(CONTROL_ARMS)}
    fused, out_times = fixed_control_fusion(controls)
    np.testing.assert_array_equal(fused, np.full(2, 4.))
    forecast, out_times2 = fixed_forecast_control_fusion((np.full(2, 5.), times), controls)
    np.testing.assert_array_equal(forecast, np.full(2, 5.))
    np.testing.assert_array_equal(out_times, out_times2)
    controls[CONTROL_ARMS[0]] = (np.ones(2), np.array([255, 257]))
    with pytest.raises(ValueError, match="same timestamps"):
        fixed_control_fusion(controls)


def test_higher_empirical_quantile_uses_frozen_higher_method():
    values = np.arange(1, 101, dtype=np.float64)
    assert higher_empirical_quantile(values, 0.99) == 100.0
    assert higher_empirical_quantile(values, 0.0) == 1.0


def test_forecast_score_is_pointwise():
    score, times = forecast_score(np.array([[1., 2.], [3., 4.]]), np.zeros((2, 2)), [256, 257])
    np.testing.assert_array_equal(score, [2.5, 12.5])
    np.testing.assert_array_equal(times, [256, 257])


def test_score_seal_is_numeric_verifiable_and_immutable(tmp_path):
    path = tmp_path / "arm.npz"
    manifest = seal_score_artifact(path, np.array([1., 2.]), [256, 257], arm="arm", machine="machine-1-1")
    assert verify_score_seal(manifest)["count"] == 2
    with np.load(path, allow_pickle=False) as data:
        assert data["scores"].dtype.kind == "f"
        assert data["timestamps"].tolist() == [256, 257]
    with pytest.raises(FileExistsError):
        seal_score_artifact(path, np.array([3.]), [258], arm="arm", machine="machine-1-1")


def test_racing_manifest_collision_does_not_delete_published_score(tmp_path, monkeypatch):
    import os

    path = tmp_path / "arm.npz"
    manifest = path.with_suffix(path.suffix + ".manifest.json")
    original_link = os.link

    def racing_link(source, target):
        if Path(target) == manifest:
            manifest.write_text("racing writer seal\n")
            raise FileExistsError("simulated racing manifest publication")
        return original_link(source, target)

    monkeypatch.setattr(os, "link", racing_link)
    with pytest.raises(FileExistsError, match="immutable"):
        seal_score_artifact(path, np.array([1.]), [256], arm="arm", machine="machine-1-1")
    assert path.is_file()
    assert manifest.read_text() == "racing writer seal\n"


def test_racing_stage1_artifact_collision_does_not_overwrite_or_seal_partial_inventory(tmp_path, monkeypatch):
    import os

    records = {machine: {"timestamps": np.array([256]),
                         **{name: np.array([1.]) for name in STAGE1_SCORE_NAMES}}
               for machine in STAGE1_MACHINES}
    target = tmp_path / STAGE1_SCORE_DIR / f"{STAGE1_MACHINES[0]}.npz"
    original_link = os.link

    def racing_link(source, destination):
        if Path(destination) == target:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"racing writer artifact")
            raise FileExistsError("simulated racing score publication")
        return original_link(source, destination)

    monkeypatch.setattr(os, "link", racing_link)
    with pytest.raises(FileExistsError):
        seal_stage1_machine_scores(tmp_path, records)
    assert target.read_bytes() == b"racing writer artifact"
    assert not (tmp_path / "reports/adaptive_normality_m1_smd/stage1_score_manifest.json").exists()
