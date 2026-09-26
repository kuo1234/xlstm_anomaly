"""Isolated, label-blind xLSTMAD-R completion of the Stage-1A nine-machine screen.

The module is inert on import. ``run_stage1b_r`` fits only xLSTMAD-R, seals its
two raw score arrays and the full frozen calibration provenance, and never
imports or opens anomaly labels or computes metrics.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

try:
    from scripts import adaptive_normality_m1_data as data
    from scripts import adaptive_normality_m1_execute as execute
    from scripts import adaptive_normality_m1_models as models
    from scripts import adaptive_normality_m1_scores as scores
    from scripts import adaptive_normality_m1_stage1a as stage1a
except ImportError:  # direct script execution
    import adaptive_normality_m1_data as data
    import adaptive_normality_m1_execute as execute
    import adaptive_normality_m1_models as models
    import adaptive_normality_m1_scores as scores
    import adaptive_normality_m1_stage1a as stage1a

ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = Path("reports/adaptive_normality_m1_smd/stage1b_r")
RUN_DIR = BASE_DIR / "runs"
SCORE_DIR = BASE_DIR / "scores"
SCORE_MANIFEST = BASE_DIR / "score_manifest.json"
EXECUTION_MANIFEST = BASE_DIR / "execution_calibration_manifest.json"
EXECUTION_SUMMARY = BASE_DIR / "execution_summary.json"
SCHEMA = "adaptive-normality-m1-stage1b-r-execution-calibration-v1"
SCORE_SCHEMA = "adaptive-normality-m1-stage1b-r-score-inventory-v1"
MACHINES = (
    "machine-1-7", "machine-1-3", "machine-1-5",
    "machine-2-4", "machine-2-7", "machine-2-8",
    "machine-3-2", "machine-3-11", "machine-3-7",
)
R_SCORE_NAMES = ("r_native_window", "r_endpoint")
SEED = 11
PARAMETER_COUNT = 75_934
QUANTILE = {"q": 0.99, "method": "higher"}
ALL_RAW_NAMES = ("last_value", "moving_median", "var1", "r_native_window",
                 "r_endpoint", "xlstmad_f", "lstm_f")


class Stage1BError(RuntimeError):
    """Stage-1B-R provenance or execution contract failed."""


def _sha_bytes(value: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def _sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _git_head(repo: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise Stage1BError("cannot record source Git commit") from error


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite immutable Stage-1B-R artifact {path}")
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".partial")
    tmp = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True, indent=2, allow_nan=False)
            handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        os.link(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _write_npz(path: Path, arrays: Mapping[str, np.ndarray], *, repo: Path = ROOT) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite immutable Stage-1B-R artifact {path}")
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".partial")
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            np.savez_compressed(handle, **arrays)
            handle.flush(); os.fsync(handle.fileno())
        os.link(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)
    return {"path": path.resolve().relative_to(Path(repo).resolve()).as_posix(),
            "sha256": _sha_file(path), "bytes": path.stat().st_size}


def _make_fit_record_portable(fit_record: dict[str, Any], repo: Path) -> None:
    """Store only repository-relative checkpoint provenance in the run record."""
    checkpoint = fit_record.get("best_checkpoint")
    if not isinstance(checkpoint, Mapping) or not isinstance(checkpoint.get("path"), str):
        raise Stage1BError("xLSTMAD-R fit record lacks a selected checkpoint path")
    try:
        checkpoint_path = Path(checkpoint["path"]).resolve().relative_to(repo.resolve())
    except ValueError as error:
        raise Stage1BError("selected R checkpoint falls outside the repository") from error
    fit_record["best_checkpoint"] = {**checkpoint, "path": checkpoint_path.as_posix()}


def reconstruction_score_vectors(model: Any, stream: np.ndarray, timestamps: Sequence[int], *,
                                device: str = "cpu", batch_size: int = execute.BATCH_SIZE
                                ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Score exact trailing W×D windows and return native and endpoint errors at t."""
    z = np.asarray(stream)
    times = np.asarray(timestamps, dtype=np.int64)
    if z.ndim != 2 or z.shape[1] != data.D or times.ndim != 1 or int(batch_size) <= 0:
        raise ValueError("stream/timestamps must have [T,38] and [N] shapes")
    if len(times) and (times[0] < data.W - 1 or times[-1] >= len(z)):
        raise ValueError("reconstruction timestamps must lie in [W-1, stream_length)")
    if len(times) > 1 and np.any(times[1:] <= times[:-1]):
        raise ValueError("reconstruction timestamps must be strictly increasing")
    native_parts, endpoint_parts = [], []
    for start in range(0, len(times), int(batch_size)):
        batch_times = times[start:start + int(batch_size)]
        predictions = execute._inference_batches(model, z, batch_times,
                                                 arm="xlstmad_r", device=device)
        actual = np.stack([data.reconstruction_window(z, int(t), 0, len(z)) for t in batch_times])
        native, endpoint, returned = scores.reconstruction_scores(actual, predictions, batch_times)
        if not np.array_equal(returned, batch_times):
            raise Stage1BError("R score timestamps changed during reconstruction scoring")
        native_parts.append(native); endpoint_parts.append(endpoint)
    if not len(times):
        empty = np.empty(0, dtype=np.float64)
        return empty, empty, times
    return np.concatenate(native_parts), np.concatenate(endpoint_parts), times


def _canonical_calibration(stage1a_calibration: Mapping[str, Any],
                            r_calibration: Mapping[str, np.ndarray],
                            calibration_timestamps: Sequence[int], *,
                            stage1a_thresholds: Mapping[str, float]) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    times = np.asarray(calibration_timestamps, dtype=np.int64)
    if times.ndim != 1 or len(times) < 2 or (len(times) > 1 and np.any(np.diff(times) != 1)):
        raise ValueError("calibration timestamps must be a contiguous vector")
    half = len(times) // 2
    second_times = times[half:]
    frozen_times = np.asarray(stage1a_calibration["timestamps"], dtype=np.int64)
    if not np.array_equal(frozen_times, second_times):
        raise ValueError("Stage-1A calibration threshold timestamps are misaligned")
    if set(stage1a_thresholds) != {"last_value", "moving_median", "var1", "xlstmad_f", "lstm_f"}:
        raise ValueError("Stage-1A frozen thresholds must contain the exact five existing scores")
    raw_cal = {}
    for name in ("last_value", "moving_median", "var1", "xlstmad_f", "lstm_f"):
        value = np.asarray(stage1a_calibration[f"threshold_scores__{name}"], dtype=np.float64)
        if value.shape != second_times.shape or not np.isfinite(value).all():
            raise ValueError(f"Stage-1A calibration threshold samples invalid for {name}")
        raw_cal[name] = value
    tails: dict[str, np.ndarray] = {}
    for name in ("last_value", "moving_median", "var1", "xlstmad_f"):
        ref = np.asarray(stage1a_calibration[f"tail_reference__{name}"], dtype=np.float64).reshape(-1)
        if not len(ref) or not np.isfinite(ref).all() or np.any(ref[1:] < ref[:-1]):
            raise ValueError(f"Stage-1A tail reference invalid for {name}")
        tails[name] = ref.copy()
    for name in R_SCORE_NAMES:
        values = np.asarray(r_calibration[name], dtype=np.float64)
        if values.shape != times.shape or not np.isfinite(values).all():
            raise ValueError(f"R calibration scores invalid for {name}")
        ref = np.sort(values[:half], kind="mergesort")
        tails[name] = ref
        raw_cal[name] = values[half:]
    controls = {
        "R-native-window": (scores.normal_tail_severity(raw_cal["r_native_window"], tails["r_native_window"]), second_times),
        "R-endpoint": (scores.normal_tail_severity(raw_cal["r_endpoint"], tails["r_endpoint"]), second_times),
        "last-value": (scores.normal_tail_severity(raw_cal["last_value"], tails["last_value"]), second_times),
        "moving-median": (scores.normal_tail_severity(raw_cal["moving_median"], tails["moving_median"]), second_times),
        "ridge-var1": (scores.normal_tail_severity(raw_cal["var1"], tails["var1"]), second_times),
    }
    control, control_times = scores.fixed_control_fusion(controls)
    forecast = (scores.normal_tail_severity(raw_cal["xlstmad_f"], tails["xlstmad_f"]), second_times)
    forecast_control, forecast_times = scores.fixed_forecast_control_fusion(forecast, controls)
    if not np.array_equal(control_times, second_times) or not np.array_equal(forecast_times, second_times):
        raise Stage1BError("full calibration fusions changed timestamps")
    threshold_samples = dict(raw_cal)
    threshold_samples["control_fusion"] = control
    threshold_samples["forecast_control_fusion"] = forecast_control
    thresholds = {name: float(stage1a_thresholds[name]) for name in stage1a_thresholds}
    thresholds.update({name: scores.higher_empirical_quantile(raw_cal[name], .99) for name in R_SCORE_NAMES})
    thresholds["control_fusion"] = scores.higher_empirical_quantile(control, .99)
    thresholds["forecast_control_fusion"] = scores.higher_empirical_quantile(forecast_control, .99)
    if set(thresholds) != set(scores.STAGE1_SCORE_NAMES):
        raise Stage1BError("full Stage-1 calibration threshold inventory drift")
    calibration = {
        "tail_references": tails,
        "threshold_calibration_scores": threshold_samples,
        "thresholds": thresholds,
        "threshold_quantile": dict(QUANTILE),
        "threshold_timestamps": second_times,
        "first_half_bounds": [int(times[0]), int(times[half])],
        "second_half_bounds": [int(times[half]), int(times[-1] + 1)],
    }
    arrays = {"timestamps": second_times}
    arrays.update({f"tail_reference__{name}": np.asarray(ref) for name, ref in tails.items()})
    arrays.update({f"threshold_scores__{name}": np.asarray(values) for name, values in threshold_samples.items()})
    return calibration, arrays


def calibrate_full_stage1_fusions(stage1a_calibration: Mapping[str, Any],
                                  r_calibration_scores: Mapping[str, np.ndarray],
                                  calibration_timestamps: Sequence[int], *,
                                  stage1a_thresholds: Mapping[str, float]) -> dict[str, Any]:
    """Freeze R thresholds and both full Stage-1 fusion thresholds from train normals."""
    result, _ = _canonical_calibration(stage1a_calibration, r_calibration_scores,
                                       calibration_timestamps, stage1a_thresholds=stage1a_thresholds)
    return result


def _reference_keys(references: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    aliases = {"R-native-window": "r_native_window", "R-endpoint": "r_endpoint",
               "last-value": "last_value", "moving-median": "moving_median",
               "ridge-var1": "var1"}
    refs = {aliases.get(name, name): np.asarray(value, dtype=np.float64) for name, value in references.items()}
    required = {"last_value", "moving_median", "var1", "r_native_window", "r_endpoint", "xlstmad_f"}
    if not required.issubset(refs):
        raise ValueError("tail references lack a full Stage-1 control/forecast set")
    return refs


def build_full_test_scores(raw_scores: Mapping[str, np.ndarray], timestamps: Sequence[int],
                           tail_references: Mapping[str, np.ndarray]) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Build the exact nine Stage-1 scores from aligned raw scores and frozen tails."""
    times = np.asarray(timestamps, dtype=np.int64)
    if times.ndim != 1 or (len(times) > 1 and np.any(times[1:] <= times[:-1])):
        raise ValueError("test timestamps must be a strictly increasing vector")
    if set(raw_scores) != set(ALL_RAW_NAMES):
        raise ValueError("raw score inventory must contain exactly the seven frozen raw arrays")
    raw = {name: np.asarray(raw_scores[name], dtype=np.float64) for name in ALL_RAW_NAMES}
    if any(value.shape != times.shape or not np.isfinite(value).all() for value in raw.values()):
        raise ValueError("all raw scores must be finite and timestamp aligned")
    refs = _reference_keys(tail_references)
    controls = {
        "R-native-window": (scores.normal_tail_severity(raw["r_native_window"], refs["r_native_window"]), times),
        "R-endpoint": (scores.normal_tail_severity(raw["r_endpoint"], refs["r_endpoint"]), times),
        "last-value": (scores.normal_tail_severity(raw["last_value"], refs["last_value"]), times),
        "moving-median": (scores.normal_tail_severity(raw["moving_median"], refs["moving_median"]), times),
        "ridge-var1": (scores.normal_tail_severity(raw["var1"], refs["var1"]), times),
    }
    cf, cf_times = scores.fixed_control_fusion(controls)
    fcf, fcf_times = scores.fixed_forecast_control_fusion(
        (scores.normal_tail_severity(raw["xlstmad_f"], refs["xlstmad_f"]), times), controls)
    if not np.array_equal(cf_times, times) or not np.array_equal(fcf_times, times):
        raise Stage1BError("full test fusions changed timestamps")
    result = {**raw, "control_fusion": cf, "forecast_control_fusion": fcf}
    if set(result) != set(scores.STAGE1_SCORE_NAMES) or any(v.shape != times.shape for v in result.values()):
        raise Stage1BError("full test score inventory or alignment changed")
    return result, times


def _load_stage1a_inputs(machine: str, repo: Path) -> tuple[dict[str, Any], dict[str, np.ndarray], dict[str, np.ndarray]]:
    run_path = repo / stage1a.RUN_DIR / machine / "machine_run.json"
    if not run_path.is_file():
        raise Stage1BError(f"missing Stage-1A run for {machine}")
    record = json.loads(run_path.read_text())
    stage1a.validate_run_record(machine, record, source_commit=record.get("source_commit"), repo=repo)
    if record.get("test_labels_read") or record.get("anomaly_metrics_computed"):
        raise Stage1BError(f"Stage-1A machine {machine} is not label-blind")
    calibration_path = repo / record["calibration"]["path"]
    score_path = repo / record["scores"]["path"]
    if not calibration_path.is_file() or _sha_file(calibration_path) != record["calibration"].get("sha256"):
        raise Stage1BError(f"{machine}: Stage-1A calibration artifact is missing or changed")
    if not score_path.is_file() or _sha_file(score_path) != record["scores"].get("sha256"):
        raise Stage1BError(f"{machine}: Stage-1A score artifact is missing or changed")
    with np.load(calibration_path, allow_pickle=False) as archive:
        calibration = {key: np.asarray(archive[key]) for key in archive.files}
    with np.load(score_path, allow_pickle=False) as archive:
        test_scores = {key: np.asarray(archive[key]) for key in archive.files}
    return record, calibration, test_scores


def _load_transform(record: Mapping[str, Any], repo: Path) -> data.RobustTransform:
    path = repo / record["scaler"]["path"]
    if not path.is_file() or _sha_file(path) != record["scaler"].get("sha256"):
        raise Stage1BError("shared Stage-1A scaler is missing or changed")
    with np.load(path, allow_pickle=False) as archive:
        return data.RobustTransform(np.asarray(archive["center"]), np.asarray(archive["scale"]),
            np.asarray(archive["raw_robust_scale"]), float(archive["scale_floor"]),
            tuple(map(int, archive["fit_rows"])))


def _load_existing(machine: str, repo: Path, source_commit: str) -> dict[str, Any] | None:
    folder = repo / RUN_DIR / machine
    run_path = folder / "machine_run.json"
    if not folder.exists():
        return None
    if not folder.is_dir() or not run_path.is_file():
        raise Stage1BError(f"{machine}: incomplete Stage-1B-R output exists; refusing overwrite")
    run = json.loads(run_path.read_text())
    if run.get("machine") != machine or run.get("source_commit") != source_commit or run.get("status") != "complete":
        raise Stage1BError(f"{machine}: existing Stage-1B-R provenance differs")
    if run.get("seed") != SEED or run.get("W") != data.W or run.get("parameter_count") != PARAMETER_COUNT:
        raise Stage1BError(f"{machine}: existing Stage-1B-R frozen settings differ")
    if run.get("test_labels_read") is not False or run.get("anomaly_metrics_computed") is not False:
        raise Stage1BError(f"{machine}: existing Stage-1B-R label flags are invalid")
    for key in ("checkpoint", "run_record", "scaler", "calibration", "scores"):
        item = run.get(key, {})
        artifact = repo / item.get("path", "")
        if not artifact.is_file() or _sha_file(artifact) != item.get("sha256"):
            raise Stage1BError(f"{machine}: existing {key} artifact missing or changed")
    checkpoint = run["checkpoint"]
    if (checkpoint.get("bytes") != (repo / checkpoint["path"]).stat().st_size or
            run["fit_record"].get("best_model_sha256") != run.get("model_state_sha256") or
            run["fit_record"].get("parameter_count") != PARAMETER_COUNT):
        raise Stage1BError(f"{machine}: existing model/checkpoint provenance differs")
    old_run, _, _ = _load_stage1a_inputs(machine, repo)
    if run.get("stage1a", {}).get("run_record_sha256") != _sha_file(repo / stage1a.RUN_DIR / machine / "machine_run.json"):
        raise Stage1BError(f"{machine}: linked Stage-1A run record has changed")
    if run.get("scaler") != old_run.get("scaler"):
        raise Stage1BError(f"{machine}: shared Stage-1A scaler provenance differs")
    with np.load(repo / run["scores"]["path"], allow_pickle=False) as a:
        if set(a.files) != {"timestamps", *R_SCORE_NAMES}:
            raise Stage1BError(f"{machine}: existing R score inventory differs")
        times = np.asarray(a["timestamps"])
        expected = np.arange(data.W, int(data.MANIFEST["machines"][machine]["test_rows"]))
        if not np.array_equal(times, expected) or _sha_bytes(times) != run["scores"].get("timestamp_sha256"):
            raise Stage1BError(f"{machine}: existing R score timestamps changed")
        if any(a[name].shape != times.shape or not np.isfinite(a[name]).all() for name in R_SCORE_NAMES):
            raise Stage1BError(f"{machine}: existing R score data invalid")
    run["resumed"] = True
    return run


def _run_machine(machine: str, *, source_commit: str, repo: Path, device: str,
                 data_root: Path | None) -> dict[str, Any]:
    existing = _load_existing(machine, repo, source_commit)
    if existing is not None:
        return existing
    old_run, old_cal, _old_test = _load_stage1a_inputs(machine, repo)
    train = data.load_train(machine, data_root)
    test = data.load_test(machine, data_root)
    transform = _load_transform(old_run, repo)
    bounds = data.split_boundaries(len(train))
    z_train = data.apply_robust_transform(train, transform)
    run_dir = repo / RUN_DIR / machine
    run_dir.mkdir(parents=True, exist_ok=False)
    checkpoint = run_dir / "xlstmad_r.best.pt"
    model, fit_record = execute.fit_arm(z_train,
        {"fit": bounds.fit, "validation": bounds.validation, "calibration": bounds.calibration},
        "xlstmad_r", device=device, seed=SEED, max_epochs=50, checkpoint_path=checkpoint)
    if models.count_parameters(model) != PARAMETER_COUNT:
        raise Stage1BError("xLSTMAD-R parameter count differs from frozen architecture")
    scaler_info = old_run["scaler"]
    cal_start, cal_stop = bounds.calibration
    cal_times = np.arange(cal_start, cal_stop, dtype=np.int64)
    z_all = data.apply_robust_transform(train, transform)
    cal_native, cal_endpoint, _ = reconstruction_score_vectors(model, z_all, cal_times, device=device)
    stage1a_thresholds = {key: float(value) for key, value in old_run["thresholds"].items()
                          if key in {"last_value", "moving_median", "var1", "xlstmad_f", "lstm_f"}}
    calibration, cal_arrays = _canonical_calibration(old_cal,
        {"r_native_window": cal_native, "r_endpoint": cal_endpoint}, cal_times,
        stage1a_thresholds=stage1a_thresholds)
    cal_info = _write_npz(run_dir / "calibration.npz", cal_arrays, repo=repo)
    z_test = data.apply_robust_transform(test, transform)
    test_times = np.arange(data.W, len(z_test), dtype=np.int64)
    native, endpoint, returned = reconstruction_score_vectors(model, z_test, test_times, device=device)
    if not np.array_equal(returned, test_times):
        raise Stage1BError("R test timestamps differ from [256,test_rows)")
    score_path = repo / SCORE_DIR / f"{machine}.npz"
    score_info = _write_npz(score_path, {"timestamps": test_times,
        "r_native_window": native, "r_endpoint": endpoint}, repo=repo)
    # Persist the exact fit record before creating the final immutable machine record.
    _make_fit_record_portable(fit_record, repo)
    execute.immutable_json_write(run_dir / "xlstmad_r_run.json", fit_record)
    arm_run_info = {"path": str((run_dir / "xlstmad_r_run.json").relative_to(repo)),
                    "sha256": _sha_file(run_dir / "xlstmad_r_run.json")}
    tail_hashes = {name: _sha_bytes(np.asarray(value))
                   for name, value in calibration["tail_references"].items()}
    tail_counts = {name: int(len(value)) for name, value in calibration["tail_references"].items()}
    record = {
        "schema": "adaptive-normality-m1-stage1b-r-machine-run-v1", "status": "complete",
        "machine": machine, "source_commit": source_commit, "seed": SEED, "W": data.W,
        "batch_size": execute.BATCH_SIZE, "parameter_count": PARAMETER_COUNT,
        "model_state_sha256": fit_record["best_model_sha256"], "selected_epoch": fit_record["best_epoch"],
        "elapsed_seconds": fit_record["elapsed_seconds"],
        "peak_allocated_bytes": fit_record["peak_allocated_bytes"],
        "peak_reserved_bytes": fit_record["peak_reserved_bytes"],
        "checkpoint": {"path": str(checkpoint.relative_to(repo)), "sha256": _sha_file(checkpoint),
                       "bytes": checkpoint.stat().st_size},
        "run_record": arm_run_info, "fit_record": fit_record,
        "scaler": {"path": scaler_info["path"], "sha256": scaler_info["sha256"]},
        "stage1a": {"run_record": str((stage1a.RUN_DIR / machine / "machine_run.json").as_posix()),
            "run_record_sha256": _sha_file(repo / stage1a.RUN_DIR / machine / "machine_run.json"),
            "source_commit": old_run["source_commit"],
            "score_artifact": old_run["scores"]["path"], "score_sha256": old_run["scores"]["sha256"],
            "calibration_artifact": old_run["calibration"]["path"],
            "calibration_sha256": old_run["calibration"]["sha256"],
            "scaler": old_run["scaler"],
            "score_manifest": {"path": stage1a.SCORE_MANIFEST.as_posix(),
                               "sha256": _sha_file(repo / stage1a.SCORE_MANIFEST)},
            "execution_manifest": {"path": stage1a.EXECUTION_MANIFEST.as_posix(),
                                    "sha256": _sha_file(repo / stage1a.EXECUTION_MANIFEST)},
            "label_access_log": {"path": stage1a.LABEL_LOG.as_posix(),
                                  "sha256": _sha_file(repo / stage1a.LABEL_LOG)},
            "forecast_arms": {name: old_run["arms"][name] for name in ("xlstmad_f", "lstm_f")}},
        "feature_data": old_run["feature_data"],
        "calibration": {"path": cal_info["path"], "sha256": cal_info["sha256"],
                        "bytes": cal_info["bytes"]},
        "scores": {**score_info, "timestamp_sha256": _sha_bytes(test_times),
                   "timestamp_count": len(test_times), "score_names": list(R_SCORE_NAMES)},
        "tail_references": {name: {"sha256": tail_hashes[name], "count": tail_counts[name]}
                            for name in calibration["tail_references"]},
        "tail_reference_hashes": tail_hashes, "tail_reference_counts": tail_counts,
        "thresholds": calibration["thresholds"], "threshold_quantile": dict(QUANTILE),
        "test_labels_read": False, "anomaly_metrics_computed": False,
    }
    _atomic_json(run_dir / "machine_run.json", record)
    return record


def seal_stage1b_r(*, repo: Path = ROOT) -> tuple[Path, Path]:
    root = Path(repo).resolve()
    if (root / SCORE_MANIFEST).exists() or (root / EXECUTION_MANIFEST).exists() or (root / EXECUTION_SUMMARY).exists():
        raise Stage1BError("Stage-1B-R seal already exists; refusing overwrite")
    score_rows, execution_rows = [], []
    for machine in MACHINES:
        path = root / RUN_DIR / machine / "machine_run.json"
        if not path.is_file():
            raise Stage1BError(f"missing completed R run: {machine}")
        run = json.loads(path.read_text())
        if run.get("status") != "complete" or run.get("test_labels_read") is not False or run.get("anomaly_metrics_computed") is not False:
            raise Stage1BError(f"invalid Stage-1B-R result-blind run: {machine}")
        score_path = root / run["scores"]["path"]
        if _sha_file(score_path) != run["scores"]["sha256"]:
            raise Stage1BError(f"R score artifact changed: {machine}")
        old_run, _, _ = _load_stage1a_inputs(machine, root)
        if (run.get("stage1a", {}).get("run_record_sha256") !=
                _sha_file(root / stage1a.RUN_DIR / machine / "machine_run.json") or
                run.get("scaler") != old_run.get("scaler") or
                run.get("feature_data") != old_run.get("feature_data")):
            raise Stage1BError(f"Stage-1A provenance link changed: {machine}")
        calibration_path = root / run["calibration"]["path"]
        if _sha_file(calibration_path) != run["calibration"]["sha256"]:
            raise Stage1BError(f"R calibration artifact changed: {machine}")
        expected_calibration = {"timestamps",
            *(f"tail_reference__{name}" for name in
              ("last_value", "moving_median", "var1", "r_native_window", "r_endpoint", "xlstmad_f")),
            *(f"threshold_scores__{name}" for name in scores.STAGE1_SCORE_NAMES)}
        with np.load(calibration_path, allow_pickle=False) as cal:
            if set(cal.files) != expected_calibration:
                raise Stage1BError(f"full calibration inventory differs: {machine}")
            cal_times = np.asarray(cal["timestamps"])
            blocks = data.split_boundaries(int(data.MANIFEST["machines"][machine]["train_rows"]))
            c0, c1 = blocks.calibration
            half = (c1-c0)//2
            expected_cal_times = np.arange(c0+half, c1, dtype=np.int64)
            if not np.array_equal(cal_times, expected_cal_times):
                raise Stage1BError(f"full calibration timestamps differ: {machine}")
            expected_thresholds = {}
            for name in scores.STAGE1_SCORE_NAMES:
                values = np.asarray(cal[f"threshold_scores__{name}"])
                if values.shape != cal_times.shape or not np.isfinite(values).all():
                    raise Stage1BError(f"calibration scores invalid for {machine}/{name}")
                expected_thresholds[name] = scores.higher_empirical_quantile(values, .99)
            if expected_thresholds != run.get("thresholds") or run.get("threshold_quantile") != QUANTILE:
                raise Stage1BError(f"frozen thresholds differ from calibration for {machine}")
            for name in ("last_value", "moving_median", "var1", "r_native_window", "r_endpoint", "xlstmad_f"):
                ref = np.asarray(cal[f"tail_reference__{name}"])
                if (not len(ref) or not np.isfinite(ref).all() or np.any(ref[1:] < ref[:-1]) or
                        run.get("tail_references", {}).get(name) !=
                        {"sha256": _sha_bytes(ref), "count": len(ref)} or
                        run.get("tail_reference_hashes", {}).get(name) != _sha_bytes(ref) or
                        run.get("tail_reference_counts", {}).get(name) != len(ref)):
                    raise Stage1BError(f"tail reference provenance differs for {machine}/{name}")
        with np.load(score_path, allow_pickle=False) as archive:
            if set(archive.files) != {"timestamps", *R_SCORE_NAMES}:
                raise Stage1BError(f"R score set differs for {machine}")
            times = np.asarray(archive["timestamps"])
            expected = np.arange(data.W, int(data.MANIFEST["machines"][machine]["test_rows"]))
            if not np.array_equal(times, expected):
                raise Stage1BError(f"R timestamps are not exactly [256,test_rows): {machine}")
            if any(not np.isfinite(archive[name]).all() or archive[name].shape != times.shape for name in R_SCORE_NAMES):
                raise Stage1BError(f"nonfinite/misaligned R score for {machine}")
        timestamp_sha = _sha_bytes(times)
        score_rows.append({"machine": machine, "artifact": run["scores"]["path"],
            "sha256": run["scores"]["sha256"], "bytes": run["scores"]["bytes"],
            "score_names": list(R_SCORE_NAMES), "timestamp_sha256": timestamp_sha, "count": len(times)})
        execution_rows.append({"machine": machine,
            "run_record": path.relative_to(root).as_posix(), "run_record_sha256": _sha_file(path),
            "source_commit": run["source_commit"], "seed": run["seed"], "W": run["W"],
            "batch_size": run["batch_size"], "parameter_count": run["parameter_count"],
            "model_state_sha256": run["model_state_sha256"],
            "checkpoint": run["checkpoint"], "run_record_artifact": run["run_record"],
            "scaler": run["scaler"], "feature_data": run["feature_data"],
            "stage1a": run["stage1a"],
            "calibration": run["calibration"], "thresholds": run["thresholds"],
            "threshold_quantile": run["threshold_quantile"], "tail_references": run["tail_references"],
            "tail_reference_hashes": run["tail_reference_hashes"],
            "tail_reference_counts": run["tail_reference_counts"],
            "score_artifact": run["scores"]["path"], "score_sha256": run["scores"]["sha256"],
            "score_bytes": run["scores"]["bytes"], "score_timestamp_count": len(times),
            "score_timestamp_sha256": timestamp_sha, "test_labels_read": False,
            "anomaly_metrics_computed": False})
    sm, em = root / SCORE_MANIFEST, root / EXECUTION_MANIFEST
    _atomic_json(sm, {"schema": SCORE_SCHEMA, "machines": score_rows, "score_names": list(R_SCORE_NAMES)})
    _atomic_json(em, {"schema": SCHEMA, "machines": execution_rows, "threshold_quantile": dict(QUANTILE),
                      "test_labels_read": False, "anomaly_metrics_computed": False})
    return sm, em


def run_stage1b_r(*, repo: Path = ROOT, device: str = "cuda:0",
                  data_root: Path | None = None) -> dict[str, Any]:
    """Fit/reuse only xLSTMAD-R on the frozen nine, then create R-only seals."""
    root = Path(repo).resolve()
    source_commit = _git_head(root)
    source_files = ("scripts/adaptive_normality_m1_stage1b_r.py",
                    "scripts/adaptive_normality_m1_stage1b_r_metrics.py",
                    "scripts/adaptive_normality_m1_stage1b_r_feasibility.py",
                    "research/adaptive_normality_m1_smd/stage1b_gate_feasibility.md",
                    "scripts/adaptive_normality_m1_stage1a.py",
                    "scripts/adaptive_normality_m1_metrics.py",
                    "scripts/adaptive_normality_m1_data.py",
                    "scripts/adaptive_normality_m1_execute.py",
                    "scripts/adaptive_normality_m1_models.py",
                    "scripts/adaptive_normality_m1_scores.py")
    uncommitted = [path for path in source_files if not scores.git_committed(root / path, root)]
    if uncommitted:
        raise Stage1BError(f"Stage-1B-R execution source must be committed before execution: {uncommitted}")
    if tuple(stage1a.selected_machines()) != MACHINES:
        raise Stage1BError("Stage-1B-R machine list differs from frozen Stage-1A subset")
    started = time.perf_counter()
    records = [_run_machine(machine, source_commit=source_commit, repo=root,
                            device=device, data_root=data_root) for machine in MACHINES]
    score_manifest, execution_manifest = seal_stage1b_r(repo=root)
    summary = {"schema": "adaptive-normality-m1-stage1b-r-execution-summary-v1",
        "source_commit": source_commit, "machines": list(MACHINES),
        "score_manifest": score_manifest.relative_to(root).as_posix(),
        "execution_manifest": execution_manifest.relative_to(root).as_posix(),
        "wall_time_seconds": time.perf_counter() - started,
        "training_seconds": float(sum(run["elapsed_seconds"] for run in records)),
        "selected_epochs": {run["machine"]: run["selected_epoch"] for run in records},
        "peak_allocated_bytes": {run["machine"]: run["peak_allocated_bytes"] for run in records},
        "peak_reserved_bytes": {run["machine"]: run["peak_reserved_bytes"] for run in records},
        "resumed_machines": [run["machine"] for run in records if run.get("resumed")],
        "test_labels_read": False, "anomaly_metrics_computed": False}
    _atomic_json(root / EXECUTION_SUMMARY, summary)
    return summary


if __name__ == "__main__":
    run_stage1b_r()
