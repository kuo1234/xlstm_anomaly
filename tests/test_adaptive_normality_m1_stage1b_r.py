import numpy as np
import pytest

from scripts import adaptive_normality_m1_scores as scores
from scripts.adaptive_normality_m1_stage1b_r import (
    MACHINES,
    R_SCORE_NAMES,
    Stage1BError,
    _make_fit_record_portable,
    _load_stage1a_inputs,
    _sha_file,
    _write_npz,
    build_full_test_scores,
    calibrate_full_stage1_fusions,
    reconstruction_score_vectors,
)


def _stage1a_calibration(times):
    n = len(times)
    out = {"timestamps": np.asarray(times, dtype=np.int64)}
    for offset, name in enumerate(("last_value", "moving_median", "var1", "xlstmad_f")):
        out[f"tail_reference__{name}"] = np.arange(1 + offset, 5 + offset, dtype=np.float64)
    for offset, name in enumerate(("last_value", "moving_median", "var1", "xlstmad_f", "lstm_f")):
        out[f"threshold_scores__{name}"] = np.linspace(1 + offset, 5 + offset, n)
    return out


def test_stage1b_r_machine_and_score_inventories_are_frozen():
    assert MACHINES == (
        "machine-1-7", "machine-1-3", "machine-1-5",
        "machine-2-4", "machine-2-7", "machine-2-8",
        "machine-3-2", "machine-3-11", "machine-3-7",
    )
    assert R_SCORE_NAMES == ("r_native_window", "r_endpoint")


def test_sealed_artifact_and_checkpoint_paths_are_repository_relative(tmp_path):
    artifact = tmp_path / "reports" / "adaptive_normality_m1_smd" / "stage1b_r" / "scores" / "m.npz"
    record = _write_npz(artifact, {"timestamps": np.arange(3)}, repo=tmp_path)
    assert record["path"] == "reports/adaptive_normality_m1_smd/stage1b_r/scores/m.npz"
    checkpoint = tmp_path / "reports" / "adaptive_normality_m1_smd" / "stage1b_r" / "runs" / "m.pt"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_bytes(b"checkpoint")
    fit = {"best_checkpoint": {"path": str(checkpoint), "sha256": "a" * 64}}
    _make_fit_record_portable(fit, tmp_path)
    assert fit["best_checkpoint"]["path"] == "reports/adaptive_normality_m1_smd/stage1b_r/runs/m.pt"
    fit["best_checkpoint"]["path"] = str(tmp_path.parent / "outside.pt")
    with pytest.raises(Stage1BError, match="outside"):
        _make_fit_record_portable(fit, tmp_path)


def test_stage1a_reuse_loads_scores_and_calibration_from_explicit_repo_root(tmp_path, monkeypatch):
    from scripts import adaptive_normality_m1_stage1a as stage1a

    machine = MACHINES[0]
    run_dir = tmp_path / stage1a.RUN_DIR / machine
    score_path = tmp_path / stage1a.SCORE_DIR / f"{machine}.npz"
    calibration_path = run_dir / "calibration.npz"
    run_dir.mkdir(parents=True)
    score_path.parent.mkdir(parents=True)
    timestamps = np.arange(256, 260, dtype=np.int64)
    np.savez_compressed(score_path, timestamps=timestamps,
                        **{name: np.full(len(timestamps), i, dtype=np.float64)
                           for i, name in enumerate(stage1a.SCORE_NAMES)})
    np.savez_compressed(calibration_path, timestamps=np.arange(10, dtype=np.int64))
    record = {
        "machine": machine,
        "source_commit": "a" * 40,
        "test_labels_read": False,
        "anomaly_metrics_computed": False,
        "scores": {"path": score_path.relative_to(tmp_path).as_posix(), "sha256": _sha_file(score_path)},
        "calibration": {"path": calibration_path.relative_to(tmp_path).as_posix(),
                        "sha256": _sha_file(calibration_path)},
    }
    (run_dir / "machine_run.json").write_text(__import__("json").dumps(record))
    monkeypatch.setattr(stage1a, "validate_run_record", lambda *args, **kwargs: None)

    loaded_record, calibration, score_arrays = _load_stage1a_inputs(machine, tmp_path)
    assert loaded_record["machine"] == machine
    assert np.array_equal(calibration["timestamps"], np.arange(10))
    assert np.array_equal(score_arrays["timestamps"], timestamps)


def test_full_fusion_calibration_reuses_frozen_stage1a_tail_references():
    stage1a = _stage1a_calibration(np.arange(15, 20))
    cal_times = np.arange(10, 20)
    native = np.arange(1, 11, dtype=np.float64)
    endpoint = native * 3.0
    result = calibrate_full_stage1_fusions(
        stage1a,
        {"r_native_window": native, "r_endpoint": endpoint},
        cal_times,
        stage1a_thresholds={
            "last_value": 11.0, "moving_median": 12.0, "var1": 13.0,
            "xlstmad_f": 14.0, "lstm_f": 15.0,
        },
    )

    expected_native_ref = np.sort(native[:5])
    expected_endpoint_ref = np.sort(endpoint[:5])
    assert np.array_equal(result["tail_references"]["r_native_window"], expected_native_ref)
    assert np.array_equal(result["tail_references"]["r_endpoint"], expected_endpoint_ref)
    assert np.array_equal(result["tail_references"]["last_value"], stage1a["tail_reference__last_value"])
    assert result["threshold_quantile"] == {"q": 0.99, "method": "higher"}
    assert set(result["thresholds"]) == set(scores.STAGE1_SCORE_NAMES)
    assert result["thresholds"]["last_value"] == 11.0
    assert result["thresholds"]["lstm_f"] == 15.0

    second = slice(5, None)
    control_severities = [
        scores.normal_tail_severity(stage1a[f"threshold_scores__{name}"],
                                   stage1a[f"tail_reference__{name}"])
        for name in ("last_value", "moving_median", "var1")
    ]
    control_severities += [
        scores.normal_tail_severity(native[second], expected_native_ref),
        scores.normal_tail_severity(endpoint[second], expected_endpoint_ref),
    ]
    control_fusion = np.maximum.reduce(control_severities)
    forecast_fusion = np.maximum(control_fusion, scores.normal_tail_severity(
        stage1a["threshold_scores__xlstmad_f"], stage1a["tail_reference__xlstmad_f"]))
    assert result["thresholds"]["control_fusion"] == scores.higher_empirical_quantile(control_fusion, .99)
    assert result["thresholds"]["forecast_control_fusion"] == scores.higher_empirical_quantile(forecast_fusion, .99)


def test_full_fusion_calibration_rejects_misaligned_stage1a_half():
    stage1a = _stage1a_calibration(np.arange(15, 20))
    with pytest.raises(ValueError, match="timestamp"):
        calibrate_full_stage1_fusions(
            stage1a,
            {"r_native_window": np.arange(10.0), "r_endpoint": np.arange(10.0)},
            np.arange(9, 19),
            stage1a_thresholds={"last_value": 1., "moving_median": 1., "var1": 1.,
                                "xlstmad_f": 1., "lstm_f": 1.},
        )


def test_full_test_score_construction_keeps_exact_nine_arrays_and_timestamps():
    timestamps = np.arange(256, 262, dtype=np.int64)
    raw = {
        "last_value": np.arange(6.0), "moving_median": np.arange(6.0) + 1,
        "var1": np.arange(6.0) + 2, "r_native_window": np.arange(6.0) + 3,
        "r_endpoint": np.arange(6.0) + 4, "xlstmad_f": np.arange(6.0) + 5,
        "lstm_f": np.arange(6.0) + 6,
    }
    references = {name: np.arange(1.0, 5.0) for name in scores.CONTROL_ARMS}
    references["xlstmad_f"] = np.arange(1.0, 5.0)
    arrays, actual_times = build_full_test_scores(raw, timestamps, references)
    assert set(arrays) == set(scores.STAGE1_SCORE_NAMES)
    assert np.array_equal(actual_times, timestamps)
    assert all(np.asarray(value).shape == timestamps.shape for value in arrays.values())
    assert all(np.isfinite(value).all() for value in arrays.values())


def test_reconstruction_score_vectors_use_trailing_windows_and_shared_timestamp(monkeypatch):
    from scripts import adaptive_normality_m1_execute as execute

    stream = np.arange(258 * 38, dtype=np.float32).reshape(258, 38)
    times = np.array([256, 257], dtype=np.int64)
    expected = []
    for t in times:
        window = stream[t - 255:t + 1]
        expected.append(window)
    predictions = np.stack(expected)
    predictions[:, -1, :] -= 2.0

    def fake_inference(model, z, got_times, **kwargs):
        assert np.array_equal(got_times, times)
        return predictions

    monkeypatch.setattr(execute, "_inference_batches", fake_inference)
    native, endpoint, returned_times = reconstruction_score_vectors(
        object(), stream, times, device="cpu"
    )
    assert np.array_equal(returned_times, times)
    assert np.all(native > 0)
    assert np.all(endpoint == 4.0)
