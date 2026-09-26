import numpy as np
import pytest

from scripts.adaptive_normality_m1_scores import (
    CONTROL_ARMS,
    FORECAST_ARM,
    STAGE1_SCORE_NAMES,
)
from scripts.adaptive_normality_m1_stage1b_r_metrics import (
    RESULT_SCHEMA,
    build_xlstm_lstm_diagnostic,
    compose_stage1b_r_score_arrays,
    run_after_committed_r_seal,
    stage1b_r_result_document,
    write_stage1b_r_result_artifacts,
    _validate_frozen_calibration_extension,
)
from scripts.adaptive_normality_m1_stage1b_r import _canonical_calibration


MACHINES = (
    "machine-1-7", "machine-1-3", "machine-1-5",
    "machine-2-4", "machine-2-7", "machine-2-8",
    "machine-3-2", "machine-3-11", "machine-3-7",
)


def _rows():
    rows = []
    for i, machine in enumerate(MACHINES):
        score_rows = {
            name: {
                "AP": 0.1 + i / 100,
                "AUROC": 0.7,
                "AP_over_prevalence": 0.5 + i / 100,
                "event_detection_rate": 0.6,
                "onset_delay": 2.0,
                "miss_fraction": 0.1,
                "normal_point_FPR": 0.01,
                "false_alarm_points_per_10000_normal": 100.0,
                "false_alarm_runs_per_10000_normal": 10.0,
                "score_recovery_delay": 12.0,
                "score_recovery_censored_count": 1,
            }
            for name in STAGE1_SCORE_NAMES
        }
        score_rows["xlstmad_f"].update({"AP": 0.3 + i / 100, "normal_point_FPR": 0.01 + i / 1000})
        score_rows["lstm_f"].update({"AP": 0.25 + i / 100, "normal_point_FPR": 0.02 + i / 1000})
        rows.append({
            "machine": machine, "prevalence": 0.2, "scores": score_rows,
            "delta_AP_forecast_control_fusion": (
                score_rows["forecast_control_fusion"]["AP"] -
                score_rows["control_fusion"]["AP"]
            ),
        })
    return rows


def _calibration_extension_fixture():
    calibration_times = np.arange(10, 20, dtype=np.int64)
    stage1a = {"timestamps": np.arange(15, 20, dtype=np.int64)}
    for offset, name in enumerate(("last_value", "moving_median", "var1", "xlstmad_f")):
        stage1a[f"tail_reference__{name}"] = np.arange(1 + offset, 5 + offset, dtype=np.float64)
    stage1a_thresholds = {}
    for offset, name in enumerate(("last_value", "moving_median", "var1", "xlstmad_f", "lstm_f")):
        stage1a[f"threshold_scores__{name}"] = np.linspace(offset + 1, offset + 3, 5)
        stage1a_thresholds[name] = float(offset + 10)
    r_raw = {"r_native_window": np.linspace(2, 8, len(calibration_times)),
             "r_endpoint": np.linspace(3, 9, len(calibration_times))}
    full_calibration, sealed = _canonical_calibration(
        stage1a, r_raw, calibration_times, stage1a_thresholds=stage1a_thresholds)
    return stage1a, stage1a_thresholds, sealed, full_calibration["thresholds"]


def test_full_score_composition_uses_frozen_five_controls_plus_xlstm_f():
    timestamps = np.arange(256, 263, dtype=np.int64)
    old = {
        "last_value": np.arange(7.0),
        "moving_median": np.arange(7.0) + 1,
        "var1": np.arange(7.0) + 2,
        "xlstmad_f": np.arange(7.0) + 3,
        "lstm_f": np.arange(7.0) + 4,
    }
    r = {"r_native_window": np.arange(7.0) + 5, "r_endpoint": np.arange(7.0) + 6}
    references = {name: np.arange(1.0, 5.0) for name in
                  ("last_value", "moving_median", "var1", "r_native_window", "r_endpoint", "xlstmad_f")}
    arrays, returned_times = compose_stage1b_r_score_arrays(old, r, timestamps, references)
    assert set(arrays) == set(STAGE1_SCORE_NAMES)
    assert np.array_equal(returned_times, timestamps)
    assert all(value.shape == timestamps.shape and np.isfinite(value).all() for value in arrays.values())


def test_calibration_extension_preserves_stage1a_and_recomputes_fusions():
    old, old_thresholds, sealed, thresholds = _calibration_extension_fixture()
    _validate_frozen_calibration_extension(sealed, old, old_thresholds, thresholds, "machine-1-7")

    tampered = {name: value.copy() for name, value in sealed.items()}
    tampered["tail_reference__var1"][0] += 1
    with pytest.raises(RuntimeError, match="tail reference changed"):
        _validate_frozen_calibration_extension(tampered, old, old_thresholds, thresholds, "machine-1-7")

    with pytest.raises(RuntimeError, match="threshold changed"):
        _validate_frozen_calibration_extension(
            sealed, old, old_thresholds, {**thresholds, "xlstmad_f": thresholds["xlstmad_f"] + 1}, "machine-1-7")

    tampered = {name: value.copy() for name, value in sealed.items()}
    tampered["threshold_scores__control_fusion"][0] += 1
    with pytest.raises(RuntimeError, match="fusion calibration"):
        _validate_frozen_calibration_extension(tampered, old, old_thresholds, thresholds, "machine-1-7")


def test_xlstm_lstm_diagnostic_is_paired_and_descriptive_only():
    diagnostic = build_xlstm_lstm_diagnostic(_rows())
    assert diagnostic["mean_ap_difference_xlstm_minus_lstm"] == pytest.approx(0.05)
    assert diagnostic["positive_ap_difference_machines"] == 9
    assert diagnostic["machines"][0]["ap_difference"] == pytest.approx(0.05)
    assert diagnostic["machines"][0]["fpr_difference_xlstm_minus_lstm"] == pytest.approx(-0.01)
    assert diagnostic["claim_permitted"] is False


def test_result_document_cannot_return_stage1_pass():
    feasibility = {"decision": "FINAL_COMPLEMENT_ROUTE_STILL_FEASIBLE", "bounds": {}}
    result = stage1b_r_result_document(_rows(), feasibility, seal_sha="a" * 40)
    assert result["schema"] == RESULT_SCHEMA
    assert result["decision"] == "FINAL_STAGE1_GATE_STILL_FEASIBLE"
    assert result["stage1_pass_permitted"] is False
    assert "M1_STAGE1_PASS" not in repr(result)

    feasibility["decision"] = "FINAL_COMPLEMENT_ROUTE_IMPOSSIBLE"
    result = stage1b_r_result_document(_rows(), feasibility, seal_sha="a" * 40)
    assert result["decision"] == "FINAL_STAGE1_GATE_ALREADY_IMPOSSIBLE"


def test_metric_entrypoint_verifies_seal_before_invoking_label_loader():
    events = []
    result = run_after_committed_r_seal(
        seal_verifier=lambda: events.append("seal") or {"seal_sha": "b" * 40},
        score_loader=lambda seal: events.append(("scores", seal["seal_sha"])) or "score-data",
        label_loader=lambda seal: events.append(("labels", seal["seal_sha"])) or [1, 0],
        metric_runner=lambda seal, scores, labels: events.append(("metrics", scores, labels)) or "ok",
    )
    assert result == "ok"
    assert events == ["seal", ("scores", "b" * 40), ("labels", "b" * 40), ("metrics", "score-data", [1, 0])]

    events.clear()
    with pytest.raises(RuntimeError, match="seal unavailable"):
        run_after_committed_r_seal(
            seal_verifier=lambda: (_ for _ in ()).throw(RuntimeError("seal unavailable")),
            score_loader=lambda seal: events.append("scores"),
            label_loader=lambda seal: events.append("labels"),
            metric_runner=lambda seal, scores, labels: None,
        )
    assert events == []


def test_result_writers_are_deterministic_and_immutable(tmp_path):
    result = stage1b_r_result_document(
        _rows(), {"decision": "FINAL_COMPLEMENT_ROUTE_STILL_FEASIBLE", "bounds": {}}, seal_sha="c" * 40
    )
    paths = write_stage1b_r_result_artifacts(tmp_path, result)
    assert set(paths) == {"json", "markdown"}
    assert paths["json"].is_file()
    before = paths["json"].read_bytes()
    with pytest.raises(FileExistsError):
        write_stage1b_r_result_artifacts(tmp_path, result)
    assert paths["json"].read_bytes() == before
