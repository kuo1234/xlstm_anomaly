"""Causal M1 training/scoring primitives and future Stage-1 runner.

This file defines the experiment runner but does not execute it on import. The
only currently authorized invocation is the isolated engineering timing
canary. All data dependencies are observation-only; test-label access is
blocked by a process audit hook.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import random
import subprocess
import tempfile
import time
import copy
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import numpy as np

try:
    from scripts import adaptive_normality_m1_data as data
    from scripts import adaptive_normality_m1_models as models
    from scripts import adaptive_normality_m1_scores as scores
except ImportError:  # direct script execution
    import adaptive_normality_m1_data as data
    import adaptive_normality_m1_models as models
    import adaptive_normality_m1_scores as scores


SEED = 11
BATCH_SIZE = 128
MAX_EPOCHS = 50
LEARNING_RATE = 1e-3
STAGE1_EXECUTION_DIR = Path("reports/adaptive_normality_m1_smd/stage1_execution")
STAGE1_EXECUTION_MANIFEST_PATH = Path("reports/adaptive_normality_m1_smd/stage1_execution_manifest.json")
STAGE1_EXECUTION_SCHEMA = "adaptive-normality-m1-stage1-execution-calibration-v1"
ARMS = ("xlstmad_r", "xlstmad_f", "lstm_f")
ARM_NAMES = {
    "xlstmad_r": "xLSTMAD-R",
    "xlstmad_f": "xLSTMAD-F",
    "lstm_f": "LSTM-F",
}


class M1ExecutionError(RuntimeError):
    pass


def deterministic_order(length: int, seed: int, epoch_zero_based: int) -> np.ndarray:
    """Frozen per-epoch permutation; order is independent of global RNG state."""
    return np.random.default_rng(
        np.random.SeedSequence([int(seed), int(epoch_zero_based), 1701])
    ).permutation(int(length))


def _torch():
    return models.configure_runtime()["torch"]


def _materialize_batch(z: np.ndarray, arm: str, endpoints: np.ndarray,
                       target_start: int) -> tuple[np.ndarray, np.ndarray]:
    """Materialize one fit/validation batch; F contexts exclude target t."""
    if arm == "xlstmad_r":
        windows = np.stack([data.reconstruction_window(z, int(t), 0, len(z)) for t in endpoints])
        return windows, windows
    contexts = np.stack([np.array(z[int(t) - data.W:int(t)], copy=True) for t in endpoints])
    targets = np.stack([np.array(z[int(t)], copy=True) for t in endpoints])
    return contexts, targets


def _batch_loss(model, arm: str, x, y):
    prediction = model(x)
    if arm == "xlstmad_r":
        if prediction.shape != y.shape:
            raise M1ExecutionError("xLSTMAD-R reconstruction shape differs from its W×D target")
    elif prediction.shape != y.shape:
        raise M1ExecutionError("forecast prediction does not match the p=1 D-vector target")
    return (prediction - y).square().mean()


def _to_device(batch: tuple[np.ndarray, np.ndarray], device: str):
    torch = _torch()
    return tuple(torch.as_tensor(x, dtype=torch.float32, device=device) for x in batch)


def _fit_endpoints(arm: str, fit_bounds: tuple[int, int]) -> np.ndarray:
    a, b = fit_bounds
    if arm == "xlstmad_r":
        first = a + data.W - 1
    else:
        first = a + data.W
    if first >= b:
        raise M1ExecutionError("fit block contains no eligible W=256 windows")
    return np.arange(first, b, dtype=np.int64)


def _validation_endpoints(bounds: tuple[int, int]) -> np.ndarray:
    a, b = bounds
    if a >= b:
        raise M1ExecutionError("validation block is empty")
    # Validation targets occupy the validation partition. Their contexts may
    # use preceding fit observations, as they are already observed at time t.
    return np.arange(a, b, dtype=np.int64)


def run_epoch(model, optimizer, z: np.ndarray, arm: str, endpoints: np.ndarray,
              *, device: str, seed: int, epoch_zero_based: int,
              batch_size: int = BATCH_SIZE, max_batches: int | None = None,
              order: np.ndarray | None = None) -> dict[str, Any]:
    """Run one training epoch or a bounded deterministic prefix of its batches."""
    torch = _torch()
    permutation = deterministic_order(len(endpoints), seed, epoch_zero_based) if order is None else np.asarray(order)
    if permutation.shape != (len(endpoints),) or not np.array_equal(np.sort(permutation), np.arange(len(endpoints))):
        raise M1ExecutionError("training permutation must contain every endpoint exactly once")
    if max_batches is not None:
        permutation = permutation[:int(max_batches) * int(batch_size)]
    start = time.perf_counter()
    model.train()
    loss_sum = 0.0
    exposures = steps = 0
    for offset in range(0, len(permutation), batch_size):
        endpoint_batch = endpoints[permutation[offset:offset + batch_size]]
        x_np, y_np = _materialize_batch(z, arm, endpoint_batch, 0)
        x, y = _to_device((x_np, y_np), device)
        optimizer.zero_grad(set_to_none=True)
        loss = _batch_loss(model, arm, x, y)
        if not bool(torch.isfinite(loss)):
            raise M1ExecutionError(f"{arm} produced a non-finite fit loss")
        loss.backward()
        if not all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in model.parameters()):
            raise M1ExecutionError(f"{arm} produced a non-finite gradient")
        optimizer.step()
        count = len(endpoint_batch)
        loss_sum += float(loss.detach()) * count
        exposures += count
        steps += 1
    if str(device).startswith("cuda"):
        torch.cuda.synchronize(device)
    seconds = time.perf_counter() - start
    return {
        "loss": loss_sum / exposures if exposures else float("nan"),
        "windows": exposures,
        "optimizer_steps": steps,
        "seconds": seconds,
        "windows_per_second": exposures / seconds if seconds else float("inf"),
        "steps_per_second": steps / seconds if seconds else float("inf"),
        "order_sha256": hashlib.sha256(np.asarray(permutation, dtype=np.int64).tobytes()).hexdigest(),
        "complete_epoch": exposures == len(endpoints),
    }


def evaluate_loss(model, z: np.ndarray, arm: str, endpoints: np.ndarray, *,
                  device: str, batch_size: int = BATCH_SIZE,
                  max_batches: int | None = None) -> dict[str, float | int]:
    torch = _torch()
    model.eval()
    selected = endpoints if max_batches is None else endpoints[:int(max_batches) * int(batch_size)]
    total = 0.0
    count = steps = 0
    start = time.perf_counter()
    with torch.inference_mode():
        for offset in range(0, len(selected), batch_size):
            ts = selected[offset:offset + batch_size]
            pair = _to_device(_materialize_batch(z, arm, ts, 0), device)
            loss = _batch_loss(model, arm, *pair)
            if not bool(torch.isfinite(loss)):
                raise M1ExecutionError(f"{arm} produced a non-finite validation loss")
            total += float(loss) * len(ts)
            count += len(ts)
            steps += 1
    if str(device).startswith("cuda"):
        torch.cuda.synchronize(device)
    seconds = time.perf_counter() - start
    if count == 0:
        raise M1ExecutionError("validation has no eligible endpoints")
    return {"loss": total / count, "windows": count, "batches": steps,
            "seconds": seconds, "windows_per_second": count / seconds if seconds else float("inf")}


def _cpu_state(model) -> dict[str, Any]:
    return {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}


def _state_hash(state: Mapping[str, Any]) -> str:
    h = hashlib.sha256()
    for key in sorted(state):
        h.update(key.encode("utf-8"))
        h.update(state[key].detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def _save_checkpoint(path: Path, state: Mapping[str, Any]) -> tuple[str, int, float]:
    torch = _torch()
    path.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    fd, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".partial")
    os.close(fd)
    temporary = Path(temp_name)
    try:
        torch.save(state, temporary)
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return _sha256_file(path), path.stat().st_size, time.perf_counter() - started


def _immutable_npz_write(path: Path, **arrays: np.ndarray) -> dict[str, Any]:
    """Publish a numeric artifact with create-if-absent semantics."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".partial")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            np.savez_compressed(handle, **arrays)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
        temporary.unlink(missing_ok=True)
    return {"path": str(path), "sha256": _sha256_file(path), "bytes": path.stat().st_size}


def _git_head(repo: Path | None = None) -> str:
    """Return the source commit used to produce a future run record."""
    root = (repo or Path(__file__).resolve().parents[1]).resolve()
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise M1ExecutionError("cannot record the source Git commit") from error


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fit_arm(z: np.ndarray, bounds: Mapping[str, tuple[int, int]], arm: str, *,
            device: str, seed: int = SEED, max_epochs: int = MAX_EPOCHS,
            max_batches_per_epoch: int | None = None,
            validation_max_batches: int | None = None,
            checkpoint_path: Path | None = None) -> tuple[Any, dict[str, Any]]:
    """Fit one arm with frozen optimizer/checkpoint selection, without labels."""
    if arm not in ARMS:
        raise M1ExecutionError(f"unknown M1 learned arm: {arm}")
    if not 1 <= int(max_epochs) <= MAX_EPOCHS:
        raise M1ExecutionError("max_epochs must be between 1 and the frozen 50-epoch cap")
    data.install_test_label_access_guard()
    torch = _torch()
    builders = {"xlstmad_r": models.build_xlstmad_r, "xlstmad_f": models.build_xlstmad_f,
                "lstm_f": models.build_lstm_f}
    model = builders[arm](seed=seed, device=device)
    if models.count_parameters(model) != models.EXPECTED_PARAMETERS[arm]:
        raise M1ExecutionError(f"{arm} parameter count changed after construction")
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    fit_endpoints = _fit_endpoints(arm, bounds["fit"])
    val_endpoints = _validation_endpoints(bounds["validation"])
    history: list[dict[str, Any]] = []
    best_loss, best_epoch, best_state = float("inf"), None, None
    best_checkpoint = None
    checkpoint_io = []
    if str(device).startswith("cuda"):
        torch.cuda.reset_peak_memory_stats(device)
    start = time.perf_counter()
    for epoch in range(int(max_epochs)):
        train = run_epoch(model, optimizer, z, arm, fit_endpoints, device=device,
                          seed=seed, epoch_zero_based=epoch,
                          max_batches=max_batches_per_epoch)
        validation = evaluate_loss(model, z, arm, val_endpoints, device=device,
                                   max_batches=validation_max_batches)
        if validation["loss"] < best_loss:  # strict comparison keeps earliest exact tie
            best_loss, best_epoch = float(validation["loss"]), epoch + 1
            best_state = _cpu_state(model)
            if checkpoint_path is not None:
                digest, size, duration = _save_checkpoint(checkpoint_path, {"model": best_state,
                    "epoch": best_epoch, "validation_loss": best_loss})
                best_checkpoint = {"path": str(checkpoint_path), "sha256": digest, "bytes": size}
                checkpoint_io.append(duration)
        history.append({"epoch": epoch + 1, "train": train, "validation": validation})
        if max_batches_per_epoch is not None and not train["complete_epoch"]:
            # A bounded engineering sample is not a protocol epoch and must not
            # be repeated as if it were a complete epoch.
            break
    if best_state is None:
        raise M1ExecutionError("no finite validation checkpoint was selected")
    model.load_state_dict(best_state, strict=True)
    if str(device).startswith("cuda"):
        torch.cuda.synchronize(device)
        peak_allocated = int(torch.cuda.max_memory_allocated(device))
        peak_reserved = int(torch.cuda.max_memory_reserved(device))
    else:
        peak_allocated = peak_reserved = 0
    record = {
        "arm": ARM_NAMES[arm], "arm_key": arm, "seed": int(seed),
        "parameter_count": models.count_parameters(model), "expected_parameters": models.EXPECTED_PARAMETERS[arm],
        "batch_size": BATCH_SIZE, "max_epochs": int(max_epochs), "epochs_run": len(history),
        "fit_windows_per_epoch": int(len(fit_endpoints)), "validation_windows": int(len(val_endpoints)),
        "optimizer": {"name": "Adam", "learning_rate": LEARNING_RATE},
        "best_epoch": best_epoch, "best_validation_loss": best_loss,
        "best_model_sha256": _state_hash(best_state), "best_checkpoint": best_checkpoint,
        "checkpoint_io_seconds": checkpoint_io, "history": history,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_allocated_bytes": peak_allocated, "peak_reserved_bytes": peak_reserved,
        "training_order": "SeedSequence([seed, zero_based_epoch, 1701]).permutation",
        "labels_read": False, "test_observations_read": False,
    }
    return model, record


def _inference_batches(model, z: np.ndarray, timestamps: np.ndarray, *,
                       arm: str, device: str, batch_size: int = BATCH_SIZE,
                       validate_order: Callable[[], None] | None = None) -> np.ndarray:
    """Predict only from past windows; target rows are fetched after forward."""
    torch = _torch()
    predictions = []
    model.eval()
    with torch.inference_mode():
        for offset in range(0, len(timestamps), batch_size):
            ts = timestamps[offset:offset + batch_size]
            if arm == "xlstmad_r":
                contexts = np.stack([data.reconstruction_window(z, int(t), 0, len(z)) for t in ts])
            else:
                contexts = np.stack([np.array(z[int(t) - data.W:int(t)], copy=True) for t in ts])
            x = torch.as_tensor(contexts, dtype=torch.float32, device=device)
            output = model(x)
            if not bool(torch.isfinite(output).all()):
                raise M1ExecutionError(f"{arm} emitted non-finite inference values")
            # An optional assertion callback is used by the causal sample-index test.
            if validate_order is not None:
                validate_order()
            predictions.append(output.detach().cpu().numpy())
    if not predictions:
        return np.empty((0, data.W, data.D) if arm == "xlstmad_r" else (0, data.D), dtype=np.float32)
    return np.concatenate(predictions, axis=0)


def forecast_predictions_then_score(model, stream, timestamps: Iterable[int], *,
                                    device: str = "cpu", batch_size: int = BATCH_SIZE) -> tuple[np.ndarray, np.ndarray]:
    """Access z_t only after the model has materialized its prediction for t."""
    times = np.asarray(list(timestamps), dtype=np.int64)
    if times.ndim != 1 or (len(times) and (times[0] < data.W or times[-1] >= len(stream))):
        raise M1ExecutionError("forecast timestamps must lie in [W, stream_length)")
    if len(times) > 1 and np.any(times[1:] <= times[:-1]):
        raise M1ExecutionError("forecast timestamps must be strictly increasing")
    torch = _torch()
    preds, targets = [], []
    model.eval()
    with torch.inference_mode():
        for offset in range(0, len(times), batch_size):
            ts = times[offset:offset + batch_size]
            contexts = np.stack([np.array(stream[int(t) - data.W:int(t)], copy=True) for t in ts])
            x = torch.as_tensor(contexts, dtype=torch.float32, device=device)
            batch_prediction = model(x).detach().cpu().numpy()
            # z_t enters score construction only after this batch prediction exists.
            batch_targets = np.stack([np.array(stream[int(t)], copy=True) for t in ts])
            preds.append(batch_prediction)
            targets.append(batch_targets)
    if not len(times):
        empty = np.empty((0, data.D), dtype=np.float32)
        return empty, empty
    prediction = np.concatenate(preds)
    target = np.concatenate(targets)
    if not np.isfinite(prediction).all() or not np.isfinite(target).all():
        raise M1ExecutionError("non-finite forecast target or prediction")
    return prediction, target


def score_forecaster(model, z: np.ndarray, timestamps: np.ndarray, *,
                     device: str) -> tuple[np.ndarray, np.ndarray]:
    predictions, targets = forecast_predictions_then_score(model, z, timestamps, device=device)
    return scores.forecast_score(targets, predictions, timestamps)


def _machine_score_vectors(machine: str, train: np.ndarray, test: np.ndarray,
                           transform: data.RobustTransform, models_by_arm: Mapping[str, Any],
                           *, device: str) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Result-blind score generation for a future full run; never accepts labels."""
    data.install_test_label_access_guard()
    blocks = data.split_boundaries(len(train))
    z_train = data.apply_robust_transform(train, transform)
    z_test = data.apply_robust_transform(test, transform)
    timestamps = data.test_forecast_targets(len(z_test), data.W)
    if not np.array_equal(timestamps, np.arange(data.W, len(z_test))):
        raise M1ExecutionError("test score endpoints must start at t=256 without padding")

    raw: dict[str, np.ndarray] = {}
    for arm in ("xlstmad_f", "lstm_f"):
        raw[arm] = score_forecaster(models_by_arm[arm], z_test, timestamps, device=device)[0]

    recon_predictions = _inference_batches(models_by_arm["xlstmad_r"], z_test, timestamps,
                                            arm="xlstmad_r", device=device)
    recon_windows = np.stack([data.reconstruction_window(z_test, int(t), 0, len(z_test)) for t in timestamps])
    r_native, r_endpoint, recon_times = scores.reconstruction_scores(recon_windows, recon_predictions, timestamps)
    if not np.array_equal(recon_times, timestamps):
        raise M1ExecutionError("reconstruction and forecast timestamps differ")
    raw["r_native_window"], raw["r_endpoint"] = r_native, r_endpoint

    # The five non-forecast controls use a single shared test endpoint vector.
    last, last_times = scores.last_value_score(z_test, np.arange(len(z_test)))
    raw["last_value"] = np.asarray(last)[timestamps - 1]
    if not np.array_equal(np.asarray(last_times)[timestamps - 1], timestamps):
        raise M1ExecutionError("last-value timestamps differ from forecast timestamps")
    moving, moving_times = scores.moving_median_score(z_test, data.W, np.arange(len(z_test)))
    raw["moving_median"] = np.asarray(moving)[timestamps - data.W]
    if not np.array_equal(np.asarray(moving_times)[timestamps - data.W], timestamps):
        raise M1ExecutionError("moving-median timestamps differ from forecast timestamps")

    a, b = blocks.fit
    var_intercept, var_coef = scores.fit_ridge_var1(z_train[a:b], lam=1.0)
    var_all, var_times = scores.ridge_var1_score(z_test, var_intercept, var_coef, np.arange(len(z_test)))
    raw["var1"] = np.asarray(var_all)[timestamps - 1]
    if not np.array_equal(np.asarray(var_times)[timestamps - 1], timestamps):
        raise M1ExecutionError("VAR(1) timestamps differ from forecast timestamps")
    if any(values.shape != timestamps.shape or not np.isfinite(values).all() for values in raw.values()):
        raise M1ExecutionError("all arms must produce finite scores on the shared endpoint vector")
    return raw, timestamps


def calibration_fusions(train: np.ndarray, transform: data.RobustTransform,
                        models_by_arm: Mapping[str, Any], *, device: str) -> dict[str, Any]:
    """Fit tail references and all nine thresholds from their frozen train blocks."""
    data.install_test_label_access_guard()
    blocks = data.split_boundaries(len(train))
    z = data.apply_robust_transform(train, transform)
    cal_start, cal_stop = blocks.calibration
    # Point forecast targets and reconstruction right endpoints share t from
    # the beginning of calibration; their causal windows may use earlier rows.
    timestamps = np.arange(cal_start, cal_stop, dtype=np.int64)
    forecast_refs = {}
    for arm in ("xlstmad_f", "lstm_f"):
        prediction, target = forecast_predictions_then_score(models_by_arm[arm], z, timestamps, device=device)
        forecast_refs[arm] = scores.forecast_score(target, prediction, timestamps)[0]
    recon_predictions = _inference_batches(models_by_arm["xlstmad_r"], z, timestamps,
                                            arm="xlstmad_r", device=device)
    recon_windows = np.stack([data.reconstruction_window(z, int(t), 0, len(z)) for t in timestamps])
    native, endpoint, _ = scores.reconstruction_scores(recon_windows, recon_predictions, timestamps)
    last, _ = scores.last_value_score(z, np.arange(len(z)))
    moving, _ = scores.moving_median_score(z, data.W, np.arange(len(z)))
    a, b = blocks.fit
    var_intercept, var_coef = scores.fit_ridge_var1(z[a:b], lam=1.0)
    var, _ = scores.ridge_var1_score(z, var_intercept, var_coef, np.arange(len(z)))
    raw = {
        "last_value": last[timestamps - 1],
        "moving_median": moving[timestamps - data.W],
        "var1": var[timestamps - 1],
        "r_native_window": native,
        "r_endpoint": endpoint,
        "xlstmad_f": forecast_refs["xlstmad_f"],
        "lstm_f": forecast_refs["lstm_f"],
    }
    if any(value.shape != timestamps.shape for value in raw.values()):
        raise M1ExecutionError("calibration score arrays do not share timestamps")
    half = max(1, len(timestamps) // 2)
    # LSTM-F is retained as a raw comparison and receives its own threshold,
    # while only xLSTMAD-F participates in the frozen forecast fusion.
    references = {name: scores.fit_tail_rank(value[:half]) for name, value in raw.items()
                  if name != "lstm_f"}
    second_half_raw = {name: value[half:] for name, value in raw.items()}
    controls = {
        "R-native-window": (scores.normal_tail_severity(second_half_raw["r_native_window"], references["r_native_window"]), timestamps[half:]),
        "R-endpoint": (scores.normal_tail_severity(second_half_raw["r_endpoint"], references["r_endpoint"]), timestamps[half:]),
        "last-value": (scores.normal_tail_severity(second_half_raw["last_value"], references["last_value"]), timestamps[half:]),
        "moving-median": (scores.normal_tail_severity(second_half_raw["moving_median"], references["moving_median"]), timestamps[half:]),
        "ridge-var1": (scores.normal_tail_severity(second_half_raw["var1"], references["var1"]), timestamps[half:]),
    }
    control, _ = scores.fixed_control_fusion(controls)
    forecast = (scores.normal_tail_severity(second_half_raw["xlstmad_f"], references["xlstmad_f"]), timestamps[half:])
    forecast_control, _ = scores.fixed_forecast_control_fusion(forecast, controls)
    threshold_scores = {**second_half_raw,
                        "control_fusion": control,
                        "forecast_control_fusion": forecast_control}
    thresholds = {name: scores.higher_empirical_quantile(value, 0.99)
                  for name, value in threshold_scores.items()}
    if set(thresholds) != set(scores.STAGE1_SCORE_NAMES):
        raise M1ExecutionError("normal calibration must produce all nine frozen thresholds")
    return {"tail_references": references,
            "threshold_calibration_scores": threshold_scores,
            "thresholds": thresholds,
            "threshold_quantile": {"q": 0.99, "method": "higher"},
            "threshold_timestamps": timestamps[half:],
            "first_half_bounds": [cal_start, cal_start + half],
            "second_half_bounds": [cal_start + half, cal_stop]}


def fuse_raw_scores(raw: Mapping[str, np.ndarray], timestamps: np.ndarray,
                    references: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Create the fixed control-only and forecast-plus-control fusion arrays."""
    controls = {
        "R-native-window": (scores.normal_tail_severity(raw["r_native_window"], references["r_native_window"]), timestamps),
        "R-endpoint": (scores.normal_tail_severity(raw["r_endpoint"], references["r_endpoint"]), timestamps),
        "last-value": (scores.normal_tail_severity(raw["last_value"], references["last_value"]), timestamps),
        "moving-median": (scores.normal_tail_severity(raw["moving_median"], references["moving_median"]), timestamps),
        "ridge-var1": (scores.normal_tail_severity(raw["var1"], references["var1"]), timestamps),
    }
    control, control_times = scores.fixed_control_fusion(controls)
    forecast = (scores.normal_tail_severity(raw["xlstmad_f"], references["xlstmad_f"]), timestamps)
    forecast_control, forecast_times = scores.fixed_forecast_control_fusion(forecast, controls)
    if not np.array_equal(control_times, timestamps) or not np.array_equal(forecast_times, timestamps):
        raise M1ExecutionError("fixed fusions changed shared score timestamps")
    return {"control_fusion": control, "forecast_control_fusion": forecast_control}


def stage1_score_record(raw: Mapping[str, np.ndarray], timestamps: np.ndarray,
                        references: Mapping[str, np.ndarray], lstm_f_scores: np.ndarray) -> dict[str, Any]:
    """Assemble the canonical nine score arrays for one machine, in memory."""
    packed = dict(raw)
    packed["lstm_f"] = np.asarray(lstm_f_scores, dtype=np.float64)
    fused = fuse_raw_scores(raw, timestamps, references)
    record = {
        "timestamps": np.asarray(timestamps, dtype=np.int64),
        "last_value": packed["last_value"], "moving_median": packed["moving_median"],
        "var1": packed["var1"], "r_native_window": packed["r_native_window"],
        "r_endpoint": packed["r_endpoint"], "xlstmad_f": packed["xlstmad_f"],
        "lstm_f": packed["lstm_f"], "control_fusion": fused["control_fusion"],
        "forecast_control_fusion": fused["forecast_control_fusion"],
    }
    if set(record) != {"timestamps", *scores.STAGE1_SCORE_NAMES}:
        raise M1ExecutionError("canonical nine-score inventory drift")
    if any(np.asarray(record[name]).shape != timestamps.shape for name in scores.STAGE1_SCORE_NAMES):
        raise M1ExecutionError("Stage-1 scores do not share endpoint indexing")
    return record


def environment_record() -> dict[str, Any]:
    versions = {}
    for distribution in ("torch", "xlstm", "lightning", "numpy"):
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[distribution] = None
    torch = _torch()
    versions["torch_metadata"] = versions.get("torch")
    versions["torch"] = torch.__version__
    return {"python": platform.python_version(), "platform": platform.platform(),
            "packages": versions, "torch_cuda": torch.version.cuda,
            "cuda_available": bool(torch.cuda.is_available()),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "torch_threads": torch.get_num_threads()}


def immutable_json_write(path: str | Path, record: Mapping[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"immutable run record already exists: {target}")
    encoded = json.dumps(record, sort_keys=True, indent=2, default=_json_default).encode("utf-8") + b"\n"
    fd, temporary_name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".partial")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
        os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def _immutable_copy(source: str | Path, target: str | Path) -> dict[str, Any]:
    """Copy a frozen numeric artifact into the canonical repo inventory once."""
    source_path, target_path = Path(source), Path(target)
    if not source_path.is_file():
        raise M1ExecutionError(f"required execution artifact is missing: {source_path}")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists():
        raise FileExistsError(f"immutable execution artifact already exists: {target_path}")
    fd, temporary_name = tempfile.mkstemp(
        dir=target_path.parent, prefix=f".{target_path.name}.", suffix=".partial")
    temporary = Path(temporary_name)
    try:
        with source_path.open("rb") as source_handle, os.fdopen(fd, "wb") as target_handle:
            while True:
                block = source_handle.read(1 << 20)
                if not block:
                    break
                target_handle.write(block)
            target_handle.flush()
            os.fsync(target_handle.fileno())
        os.link(temporary, target_path)
    finally:
        temporary.unlink(missing_ok=True)
    digest = _sha256_file(target_path)
    if digest != _sha256_file(source_path):
        target_path.unlink(missing_ok=True)
        raise M1ExecutionError(f"copied execution artifact changed bytes: {source_path}")
    return {"path": target_path.as_posix(), "sha256": digest,
            "bytes": target_path.stat().st_size}


def write_execution_calibration_seal(
        *, repo: str | Path, run_root: str | Path,
        machine_records: Mapping[str, Mapping[str, Any]],
        score_inventory: Mapping[str, Any]) -> Path:
    """Publish the immutable execution/calibration provenance for future metrics.

    This writer runs only after all frozen machine scores have been produced.
    Its output must be committed before the metric-only evaluator is allowed
    to open any test labels.
    """
    root, runs = Path(repo).resolve(), Path(run_root).resolve()
    if list(machine_records) != list(scores.STAGE1_MACHINES):
        raise M1ExecutionError("execution seal requires the exact ordered 28-machine set")
    if score_inventory.get("score_names") != list(scores.STAGE1_SCORE_NAMES):
        raise M1ExecutionError("execution seal requires the exact frozen nine-score inventory")
    inventory_entries = score_inventory.get("machines")
    if not isinstance(inventory_entries, list) or [item.get("machine") for item in inventory_entries] != list(scores.STAGE1_MACHINES):
        raise M1ExecutionError("execution seal score inventory has a noncanonical machine set")
    score_by_machine = {item["machine"]: item for item in inventory_entries}
    manifest_path = root / STAGE1_EXECUTION_MANIFEST_PATH
    execution_root = root / STAGE1_EXECUTION_DIR
    if manifest_path.exists() or execution_root.exists():
        raise FileExistsError("execution/calibration seal is immutable")

    entries = []
    for machine in scores.STAGE1_MACHINES:
        original = copy.deepcopy(dict(machine_records[machine]))
        if original.get("machine") != machine or original.get("schema") != "adaptive-normality-m1-machine-run-v1":
            raise M1ExecutionError(f"{machine}: malformed machine run record")
        run_source = runs / machine / "machine_run.json"
        if not run_source.is_file():
            raise M1ExecutionError(f"{machine}: generating machine run record is missing")
        stored_run = json.loads(run_source.read_text(encoding="utf-8"))
        if stored_run != original:
            raise M1ExecutionError(f"{machine}: in-memory machine record differs from persisted run record")

        canonical_machine_dir = execution_root / machine
        scaler = _immutable_copy(original["scaler"]["artifact"]["path"],
                                 canonical_machine_dir / "scaler.npz")
        calibration = _immutable_copy(original["calibration"]["artifact"]["path"],
                                      canonical_machine_dir / "calibration_scores.npz")
        scaler["path"] = (STAGE1_EXECUTION_DIR / machine / "scaler.npz").as_posix()
        calibration["path"] = (STAGE1_EXECUTION_DIR / machine / "calibration_scores.npz").as_posix()

        original["scaler"]["artifact"] = scaler
        for arm in ARMS:
            if arm not in original["arms"]:
                raise M1ExecutionError(f"{machine}: missing frozen learned arm {arm}")
            original["arms"][arm]["transform"]["artifact"] = scaler
        original["calibration"]["artifact"] = calibration
        run_record_rel = (STAGE1_EXECUTION_DIR / machine / "run_record.json").as_posix()
        run_record_path = root / run_record_rel
        immutable_json_write(run_record_path, original)

        with np.load(root / calibration["path"], allow_pickle=False) as saved:
            reference_names = sorted(name.removeprefix("tail_reference__")
                                     for name in saved.files if name.startswith("tail_reference__"))
            tail_reference_hashes = {}
            tail_reference_counts = {}
            for reference_name in reference_names:
                values = np.ascontiguousarray(saved[f"tail_reference__{reference_name}"])
                tail_reference_hashes[reference_name] = hashlib.sha256(values.tobytes()).hexdigest()
                tail_reference_counts[reference_name] = int(values.size)
            expected_references = {"last_value", "moving_median", "var1", "r_native_window",
                                   "r_endpoint", "xlstmad_f"}
            if set(reference_names) != expected_references or any(v <= 0 for v in tail_reference_counts.values()):
                raise M1ExecutionError(f"{machine}: calibration tail-reference inventory is incomplete")
            recorded_counts = original["calibration"].get("tail_reference_counts")
            if recorded_counts != tail_reference_counts:
                raise M1ExecutionError(f"{machine}: run-record tail-reference counts differ from calibration bytes")
            for name in scores.STAGE1_SCORE_NAMES:
                key = f"threshold_scores__{name}"
                if key not in saved.files:
                    raise M1ExecutionError(f"{machine}: missing threshold samples for {name}")
                expected_threshold = scores.higher_empirical_quantile(saved[key], 0.99)
                if float(original["calibration"]["thresholds"].get(name, float("nan"))) != expected_threshold:
                    raise M1ExecutionError(f"{machine}: {name} threshold differs from its q=.99 higher samples")

        fit_records = {arm: original["arms"][arm]["fit"] for arm in ARMS}
        model_state_hashes = {arm: fit_records[arm]["best_model_sha256"] for arm in ARMS}
        model_checkpoints = {}
        for arm in ARMS:
            checkpoint = fit_records[arm].get("best_checkpoint")
            if not isinstance(checkpoint, Mapping) or not checkpoint.get("path"):
                raise M1ExecutionError(f"{machine}/{arm}: exact best checkpoint provenance is missing")
            checkpoint_path = Path(checkpoint["path"])
            if (not checkpoint_path.is_file()
                    or _sha256_file(checkpoint_path) != checkpoint.get("sha256")
                    or checkpoint_path.stat().st_size != checkpoint.get("bytes")):
                raise M1ExecutionError(f"{machine}/{arm}: best checkpoint differs from its recorded hash/size")
            model_checkpoints[arm] = {"path": str(checkpoint_path.resolve()),
                                      "sha256": checkpoint["sha256"],
                                      "bytes": int(checkpoint["bytes"])}

        score_entry = score_by_machine[machine]
        score_artifact = root / score_entry["artifact"]
        if not score_artifact.is_file() or _sha256_file(score_artifact) != score_entry.get("sha256"):
            raise M1ExecutionError(f"{machine}: score bytes differ from the score inventory")
        calibration_summary = original["calibration"]
        thresholds = calibration_summary.get("thresholds")
        if not isinstance(thresholds, Mapping) or list(thresholds) != list(scores.STAGE1_SCORE_NAMES):
            # Serialize in canonical order irrespective of the mapping's input order.
            if not isinstance(thresholds, Mapping) or set(thresholds) != set(scores.STAGE1_SCORE_NAMES):
                raise M1ExecutionError(f"{machine}: calibration thresholds differ from the frozen nine-score set")
            thresholds = {name: thresholds[name] for name in scores.STAGE1_SCORE_NAMES}
            calibration_summary["thresholds"] = thresholds
        threshold_quantile = calibration_summary.get("threshold_quantile")
        if threshold_quantile != {"q": 0.99, "method": "higher"}:
            raise M1ExecutionError(f"{machine}: calibration threshold rule changed")
        if list(calibration_summary.get("threshold_score_names", [])) != list(scores.STAGE1_SCORE_NAMES):
            raise M1ExecutionError(f"{machine}: calibration record does not enumerate the frozen scores")

        run_record_digest = _sha256_file(run_record_path)
        entries.append({
            "machine": machine,
            "source_commit": original["source_commit"],
            "scaler_artifact": scaler["path"],
            "scaler_sha256": scaler["sha256"],
            "model_state_sha256": model_state_hashes,
            "model_checkpoints": model_checkpoints,
            "calibration_artifact": calibration["path"],
            "calibration_artifact_sha256": calibration["sha256"],
            "thresholds": {name: thresholds[name] for name in scores.STAGE1_SCORE_NAMES},
            "threshold_quantile": {"q": 0.99, "method": "higher"},
            "tail_reference_hashes": tail_reference_hashes,
            "tail_reference_counts": tail_reference_counts,
            "score_artifact": score_entry["artifact"],
            "score_artifact_sha256": score_entry["sha256"],
            "timestamp_sha256": score_entry["timestamp_sha256"],
            "run_record": run_record_rel,
            "run_record_sha256": run_record_digest,
        })

    seal = {"schema": STAGE1_EXECUTION_SCHEMA,
            "score_manifest": scores.STAGE1_MANIFEST_PATH.as_posix(),
            "machines": entries}
    immutable_json_write(manifest_path, seal)
    return manifest_path


def _json_default(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def make_run_record(*, machine: str, arm: str, fit_record: Mapping[str, Any],
                    transform: data.RobustTransform, source_commit: str,
                    data_blocks: Mapping[str, tuple[int, int]],
                    scaler_artifact: Mapping[str, Any] | None = None,
                    environment: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Create an auditable immutable run record for a future authorized fit."""
    return {"schema": "adaptive-normality-m1-run-v1", "machine": machine,
            "arm": ARM_NAMES[arm], "arm_key": arm, "source_commit": source_commit,
            "model_sources": {"xLSTMAD-R": models.OFFICIAL_R_COMMIT,
                              "xLSTMAD-F": models.HISTORICAL_F_COMMIT},
            "protocol": {"W": data.W, "D": data.D, "seed": SEED,
                         "batch_size": BATCH_SIZE, "max_epochs": MAX_EPOCHS,
                         "optimizer": "Adam", "learning_rate": LEARNING_RATE,
                         "precision": "float32", "target": "p=1" if arm != "xlstmad_r" else "native W×D reconstruction"},
            "data_partitions": {name: list(bounds) for name, bounds in data_blocks.items()},
            "environment": dict(environment or environment_record()),
            "transform": {"fit_rows": list(transform.fit_rows),
                          "center": transform.center.tolist(), "scale": transform.scale.tolist(),
                          "raw_robust_scale": transform.raw_robust_scale.tolist(),
                          "center_sha256": hashlib.sha256(transform.center.tobytes()).hexdigest(),
                          "scale_sha256": hashlib.sha256(transform.scale.tobytes()).hexdigest(),
                          "raw_robust_scale_sha256": hashlib.sha256(transform.raw_robust_scale.tobytes()).hexdigest(),
                          "scale_floor": transform.scale_floor,
                          "artifact": dict(scaler_artifact or {})},
            "fit": dict(fit_record), "test_labels_read": False,
            "anomaly_metrics_computed": False}


def run_stage1_machine(machine: str, *, device: str = "cuda:0",
                       train_root: Path | None = None, test_root: Path | None = None,
                       run_root: Path | None = None,
                       source_commit: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Future full Stage-1 machine unit. Not called in implementation preflight."""
    if run_root is None:
        raise M1ExecutionError("future Stage-1 fits require a persistent run_root")
    data.install_test_label_access_guard()
    train = data.load_train(machine, train_root)
    blocks = data.split_boundaries(len(train))
    transform = data.RobustScaler().fit(train, blocks.fit[1]).statistics
    assert transform is not None
    z_train = data.apply_robust_transform(train, transform)
    bounds = {"fit": blocks.fit, "validation": blocks.validation, "calibration": blocks.calibration}
    machine_dir = Path(run_root) / machine
    machine_dir.mkdir(parents=True, exist_ok=False)
    scaler_artifact = _immutable_npz_write(
        machine_dir / "scaler.npz", center=transform.center,
        scale=transform.scale, raw_robust_scale=transform.raw_robust_scale,
        scale_floor=np.asarray(transform.scale_floor, dtype=np.float64),
        fit_rows=np.asarray(transform.fit_rows, dtype=np.int64),
    )
    source_commit = source_commit or _git_head()
    environment = environment_record()
    trained = {}
    records = {}
    for arm in ARMS:
        checkpoint_path = machine_dir / f"{arm}.best.pt"
        model, fit_record = fit_arm(z_train, bounds, arm, device=device, seed=SEED,
                                    checkpoint_path=checkpoint_path)
        trained[arm] = model
        records[arm] = make_run_record(machine=machine, arm=arm, fit_record=fit_record,
                                       transform=transform, source_commit=source_commit,
                                       data_blocks=bounds,
                                       scaler_artifact=scaler_artifact, environment=environment)
        immutable_json_write(machine_dir / f"{arm}_run.json", records[arm])
    # calibration_fusions performs the transform internally; it must receive raw
    # train observations exactly once, not the already transformed z_train.
    calibration = calibration_fusions(train, transform, trained, device=device)
    calibration_arrays: dict[str, np.ndarray] = {
        "timestamps": np.asarray(calibration["threshold_timestamps"], dtype=np.int64),
    }
    calibration_arrays.update({f"tail_reference__{name}": np.asarray(value)
                               for name, value in calibration["tail_references"].items()})
    calibration_arrays.update({f"threshold_scores__{name}": np.asarray(value)
                               for name, value in calibration["threshold_calibration_scores"].items()})
    calibration_artifact = _immutable_npz_write(machine_dir / "calibration_scores.npz", **calibration_arrays)
    calibration_summary = {key: calibration[key] for key in (
        "thresholds", "threshold_quantile", "first_half_bounds", "second_half_bounds")}
    calibration_summary.update({
        "tail_reference_counts": {name: int(len(value)) for name, value in calibration["tail_references"].items()},
        "threshold_calibration_count": int(len(calibration["threshold_timestamps"])),
        "threshold_score_names": list(scores.STAGE1_SCORE_NAMES),
        "artifact": calibration_artifact,
    })
    # Test observations are acquired/read only after every model and calibration
    # quantity is frozen; the test-label guard remains active throughout.
    test = data.load_test(machine, test_root)
    raw, timestamps = _machine_score_vectors(machine, train, test, transform, trained, device=device)
    machine_scores = stage1_score_record(raw, timestamps, calibration["tail_references"], raw["lstm_f"])
    record = {"schema": "adaptive-normality-m1-machine-run-v1", "machine": machine,
              "source_commit": source_commit, "arms": records,
              "scaler": {"fit_rows": list(transform.fit_rows), "center": transform.center.tolist(),
                         "scale": transform.scale.tolist(), "raw_robust_scale": transform.raw_robust_scale.tolist(),
                         "scale_floor": transform.scale_floor, "artifact": scaler_artifact},
              "calibration": calibration_summary,
              "score_timestamp_bounds": [int(timestamps[0]), int(timestamps[-1] + 1)],
              "score_timestamp_count": int(len(timestamps)),
              "score_timestamp_sha256": hashlib.sha256(np.asarray(timestamps, dtype=np.int64).tobytes()).hexdigest(),
              "test_observations_read": True, "test_labels_read": False,
              "anomaly_metrics_computed": False}
    immutable_json_write(machine_dir / "machine_run.json", record)
    return machine_scores, record


def run_stage1_all(*, repo: Path | None = None, data_root: Path | None = None,
                   run_root: Path, device: str = "cuda:0") -> dict[str, Any]:
    """Future complete Stage-1 runner; execution is deliberately not automatic."""
    root = Path(repo or Path(__file__).resolve().parents[1]).resolve()
    run_root = Path(run_root).resolve()
    if not run_root.is_dir():
        run_root.mkdir(parents=True, exist_ok=False)
    if ((root / scores.STAGE1_MANIFEST_PATH).exists()
            or (root / scores.STAGE1_SCORE_DIR).exists()
            or (root / STAGE1_EXECUTION_MANIFEST_PATH).exists()
            or (root / STAGE1_EXECUTION_DIR).exists()):
        raise M1ExecutionError("canonical Stage-1 score/provenance destination already exists; refusing to overwrite")
    source_commit = _git_head(root)
    inventory: dict[str, dict[str, Any]] = {}
    records_by_machine: dict[str, dict[str, Any]] = {}
    machine_records = []
    for machine in scores.STAGE1_MACHINES:
        machine_scores, record = run_stage1_machine(
            machine, device=device, train_root=data_root, test_root=data_root,
            run_root=run_root, source_commit=source_commit,
        )
        inventory[machine] = machine_scores
        records_by_machine[machine] = record
        machine_records.append({"machine": machine, "run_record": str(run_root / machine / "machine_run.json"),
                                "run_record_sha256": _sha256_file(run_root / machine / "machine_run.json"),
                                "source_commit": record["source_commit"],
                                "test_labels_read": False, "anomaly_metrics_computed": False})
    manifest = scores.seal_stage1_machine_scores(root, inventory)
    score_inventory = json.loads(manifest.read_text(encoding="utf-8"))
    if _git_head(root) != source_commit:
        raise M1ExecutionError("source Git HEAD changed during Stage-1 execution")
    execution_manifest = write_execution_calibration_seal(
        repo=root, run_root=run_root, machine_records=records_by_machine,
        score_inventory=score_inventory)
    result = {"schema": "adaptive-normality-m1-stage1-run-inventory-v1",
              "source_commit": source_commit, "score_manifest": str(manifest),
              "score_manifest_sha256": _sha256_file(manifest), "machines": machine_records,
              "execution_manifest": str(execution_manifest),
              "execution_manifest_sha256": _sha256_file(execution_manifest),
              "test_labels_read": False, "anomaly_metrics_computed": False}
    immutable_json_write(run_root / "stage1_run_inventory.json", result)
    return result
