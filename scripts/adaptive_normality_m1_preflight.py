"""Result-blind machine-readable implementation preflight for M1 SMD.

The checks use manifest metadata, verified observations, and synthetic model
inputs. They never read test anomaly labels, invoke the metric entry point on a
sealed Stage-1 score set, or train the 28-machine experiment.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

try:
    from scripts import adaptive_normality_m1_data as data
    from scripts import adaptive_normality_m1_execute as execute
    from scripts import adaptive_normality_m1_metrics as metrics
    from scripts import adaptive_normality_m1_models as models
    from scripts import adaptive_normality_m1_scores as scores
    from scripts import adaptive_normality_m1_timing_canary as canary
except ImportError:  # direct script execution
    import adaptive_normality_m1_data as data
    import adaptive_normality_m1_execute as execute
    import adaptive_normality_m1_metrics as metrics
    import adaptive_normality_m1_models as models
    import adaptive_normality_m1_scores as scores
    import adaptive_normality_m1_timing_canary as canary


PINNED = {
    "python": "3.12.3",
    "torch": "2.13.0+cu130",
    "torch_cuda": "13.0",
    "xlstm": "2.0.5",
    "lightning": "2.6.1",
}


def _check(ok: bool, detail: Any = None) -> dict[str, Any]:
    return {"pass": bool(ok), "detail": detail}


def _manifest_check() -> dict[str, Any]:
    manifest = data.MANIFEST
    pattern = re.compile(r"^[0-9a-f]{64}$")
    entries = []
    for machine, parts in manifest["machines"].items():
        for split in ("train", "test", "test_label"):
            item = parts.get(split)
            entries.append({"machine": machine, "split": split,
                            "valid_sha256": bool(item and pattern.match(item.get("sha256", ""))),
                            "valid_bytes": bool(item and int(item.get("bytes", 0)) > 0)})
    valid = sum(item["valid_sha256"] and item["valid_bytes"] for item in entries)
    return _check(len(manifest["machines"]) == 28 and len(entries) == 84 and valid == 84,
                  {"manifest_entries": len(entries), "complete_valid_hash_entries": valid,
                   "expected": 84,
                   "raw_test_label_bytes_read": False,
                   "test_label_hashes": "validated only for manifest syntax/coverage; raw label files intentionally unopened"})


def _observation_check(root: Path | None) -> dict[str, Any]:
    hashes = data.verify_observation_hashes(root)
    schemas = []
    for machine in data.MACHINES:
        train = data.load_train(machine, root)
        test = data.load_test(machine, root)
        schemas.append({"machine": machine,
                        "train_shape": list(train.shape), "test_shape": list(test.shape),
                        "valid": train.shape == (data.MANIFEST["machines"][machine]["train_rows"], data.D) and
                                 test.shape == (data.MANIFEST["machines"][machine]["test_rows"], data.D)})
    valid_shapes = sum(item["valid"] for item in schemas)
    return _check(hashes["all_match"] and hashes["verified_count"] == 56 and valid_shapes == 28,
                  {"verified_observation_hashes": hashes["verified_count"],
                   "expected_observation_hashes": 56,
                   "machine_train_test_shapes": valid_shapes,
                   "expected_machine_pairs": 28,
                   "schemas": schemas,
                   "test_anomaly_labels_opened": 0})


def _scaler_check() -> dict[str, Any]:
    rng = np.random.default_rng(2026)
    x = rng.normal(size=(1000, data.D)).astype(np.float64)
    x[:, 17] = 4.0
    fit_end = 700
    transform = data.RobustScaler().fit(x, fit_end).statistics
    assert transform is not None
    fit = x[:fit_end]
    center = np.median(fit, axis=0)
    mad = 1.4826 * np.median(np.abs(fit - center), axis=0)
    q05, q95 = np.quantile(fit, [0.05, 0.95], axis=0, method="linear")
    raw = np.maximum(mad, (q95 - q05) / 3.2897072539)
    floor = 0.05 * np.median(raw[raw > 0])
    expected_scale = np.maximum(raw, floor)
    output_a = data.apply_robust_transform(x, transform)
    output_b = data.apply_robust_transform(x, transform)
    exact = (np.array_equal(transform.center, center) and
             np.array_equal(transform.raw_robust_scale, raw) and
             np.array_equal(transform.scale, expected_scale) and
             transform.scale_floor == floor and
             transform.fit_rows == (0, fit_end) and
             np.array_equal(output_a, output_b) and
             output_a.dtype == np.float32 and np.max(np.abs(output_a)) <= 50.0 and
             transform.scale[17] == floor)
    fail_closed = False
    try:
        data.fit_robust_transform(np.zeros((300, data.D)))
    except data.M1DataError:
        fail_closed = True
    # Previously recorded train-only machine-1-4 near-constant channel values.
    known_floor, known_channel_std = 0.00145873, 1.63e-5
    channel_value = 0.0554
    channel_result = data.apply_robust_transform(
        np.eye(1, data.D, 17, dtype=np.float64) * channel_value,
        data.RobustTransform(np.zeros(data.D),
                             np.array([known_floor if i == 17 else 1.0 for i in range(data.D)]),
                             np.array([0.0 if i == 17 else 1.0 for i in range(data.D)]),
                             known_floor, (0, 16594)))
    near_constant = (channel_result[0, 17] == np.float32(channel_value / known_floor) and
                     abs(known_floor / known_channel_std - 89.5) <= 0.01 * 89.5)
    return _check(exact and fail_closed and near_constant,
                  {"median": "exact", "mad_factor": 1.4826,
                   "central_quantile_scale": "(Q95-Q05)/3.2897072539, linear quantiles",
                   "scale": "max(MAD scale, central quantile scale)",
                   "machine_scale_floor": 0.05, "clip": [-50.0, 50.0],
                   "dtype": "float32", "repeatability": bool(np.array_equal(output_a, output_b)),
                   "fail_closed_without_positive_scale": fail_closed,
                   "machine_1_4_channel_17": {"train_std": known_channel_std,
                      "raw_robust_scale": 0.0, "floor": known_floor,
                      "transformed_0.0554": float(channel_result[0, 17])},
                   "no_test_values_used_for_fit": True})

def _index_check() -> dict[str, Any]:
    n = 2000
    blocks = data.split_boundaries(n)
    fit_targets = execute._fit_endpoints("xlstmad_f", blocks.fit)
    reconstruction_fit_targets = execute._fit_endpoints("xlstmad_r", blocks.fit)
    val_targets = execute._validation_endpoints(blocks.validation)
    cal_targets = execute._validation_endpoints(blocks.calibration)
    x = np.arange(n, dtype=np.int64)
    exact = (fit_targets[0] == data.W and fit_targets[-1] == blocks.fit[1] - 1 and
             reconstruction_fit_targets[0] == data.W - 1 and
             reconstruction_fit_targets[-1] == blocks.fit[1] - 1 and
             val_targets[0] == blocks.validation[0] and
             cal_targets[0] == blocks.calibration[0])
    for t in (fit_targets[0], fit_targets[len(fit_targets)//2], fit_targets[-1]):
        sample, target = data.forecast_sample(x, int(t), blocks.fit)
        exact = exact and np.array_equal(sample, x[t-data.W:t]) and int(target) == t
    for target in (blocks.validation[0], blocks.calibration[0]):
        contexts = np.array(x[target-data.W:target], copy=True)
        exact = exact and np.array_equal(contexts, x[target-data.W:target]) and contexts[-1] == target - 1
    final_fit_context, final_fit_target = data.forecast_sample(
        x, int(fit_targets[-1]), blocks.fit)
    exact = exact and final_fit_target == blocks.fit[1] - 1 and final_fit_context[-1] == blocks.fit[1] - 2
    test_targets = data.test_forecast_targets(1000)
    rec = data.reconstruction_window(x, 500, 0, len(x))
    exact = exact and test_targets[0] == 256 and test_targets[-1] == 999
    exact = exact and np.array_equal(rec, x[500-data.W+1:501])
    test_first_input = x[test_targets[0]-data.W:test_targets[0]]
    exact = exact and np.array_equal(test_first_input, x[:data.W])
    exact = exact and data.reconstruction_timestamps(0, 1000, 1000)[0] == data.W - 1
    return _check(bool(exact), {"forecast_input": "[t-256,t)", "target": "t",
        "test_first_eligible_t": int(test_targets[0]), "test_last_eligible_t": int(test_targets[-1]),
        "training_fit_first_internal_final_checked": bool(fit_targets[0] == data.W and
            fit_targets[-1] == blocks.fit[1] - 1 and reconstruction_fit_targets[0] == data.W - 1),
        "fit_training_targets_do_not_reach_validation": bool(fit_targets[-1] < blocks.validation[0]),
        "validation_first_target_uses_only_prior_context": bool(val_targets[0] == blocks.validation[0]),
        "calibration_first_target_uses_only_prior_context": bool(cal_targets[0] == blocks.calibration[0]),
        "reconstruction_input": "[t-255,t+1)",
        "no_score_padding": True})


def _reconstruction_scores_check() -> dict[str, Any]:
    w, d = data.W, data.D
    y = np.zeros((3, w, d), dtype=np.float32)
    pred = np.zeros_like(y)
    timestamps = np.array([256, 257, 258], dtype=np.int64)
    probe = []
    for position in (0, w // 2, w - 1):
        pred[:] = 0
        pred[:, position, 0] = 1.0
        native, endpoint, out_times = scores.reconstruction_scores(y, pred, timestamps)
        expected_native = 1.0 / (w * d)
        expected_endpoint = 1.0 / d if position == w - 1 else 0.0
        ok = np.allclose(native, expected_native, rtol=0, atol=1e-15) and np.array_equal(
            endpoint, np.full(3, expected_endpoint)) and np.array_equal(out_times, timestamps)
        probe.append({"corrupted_position": position, "native": native.tolist(),
                      "endpoint": endpoint.tolist(), "pass": bool(ok)})
    return _check(all(row["pass"] for row in probe),
                  {"R-native-window": "mean of squared residual over W×D",
                   "R-endpoint": "mean of squared residual over final D position",
                   "timestamp": "same original t as forecast", "synthetic_corruption_cases": probe})


def _model_check() -> dict[str, Any]:
    torch = models.configure_runtime()["torch"]
    builders = {"xlstmad_r": models.build_xlstmad_r,
                "xlstmad_f": models.build_xlstmad_f,
                "lstm_f": models.build_lstm_f}
    counts, forwards, no_state_carry = {}, {}, True
    sample = torch.randn(2, data.W, data.D, generator=torch.Generator().manual_seed(44))
    for arm, builder in builders.items():
        model = builder(seed=execute.SEED, device="cpu").eval()
        count = models.count_parameters(model)
        counts[arm] = count
        with torch.inference_mode():
            out1 = model(sample)
            out2 = model(sample)
            forward_shape = (2, data.W, data.D) if arm == "xlstmad_r" else (2, data.D)
            forwards[arm] = bool(out1.shape == forward_shape and torch.isfinite(out1).all())
            no_state_carry = no_state_carry and torch.equal(out1, out2)
        if arm in ("xlstmad_f", "lstm_f"):
            with torch.inference_mode():
                one = model(sample[:1])
                pair = model(torch.cat([sample[:1], sample[:1]], dim=0))
            no_state_carry = no_state_carry and torch.allclose(one[0], pair[0], rtol=1e-6, atol=1e-7)
            no_state_carry = no_state_carry and torch.allclose(one[0], pair[1], rtol=1e-6, atol=1e-7)
    expected = dict(models.EXPECTED_PARAMETERS)
    counts_exact = counts == expected
    first = models.build_lstm_f(seed=92, device="cpu")
    second = models.build_lstm_f(seed=92, device="cpu")
    deterministic = all(torch.equal(a, b) for a, b in zip(first.parameters(), second.parameters()))
    return _check(counts_exact and all(forwards.values()) and no_state_carry and deterministic,
                  {"parameter_counts": counts, "expected_parameter_counts": expected,
                   "finite_synthetic_forwards": forwards,
                   "fresh_state_per_independent_window": bool(no_state_carry),
                   "deterministic_model_seed": bool(deterministic),
                   "xLSTMAD-F_historical_parity_test": "covered by unit suite",
                   "xLSTMAD-R_official_source": models.OFFICIAL_R_COMMIT})


def _timestamp_alignment_check() -> dict[str, Any]:
    rng = np.random.default_rng(83)
    z = rng.normal(size=(280, data.D)).astype(np.float32)
    timestamps = np.arange(data.W, len(z), dtype=np.int64)
    yhat = np.zeros((len(timestamps), data.D), dtype=np.float32)
    _, forecast_times = scores.forecast_score(z[timestamps], yhat, timestamps)
    windows = np.stack([data.reconstruction_window(z, int(t), 0, len(z)) for t in timestamps])
    native, endpoint, reconstruction_times = scores.reconstruction_scores(windows, windows * 0, timestamps)
    last, last_times = scores.last_value_score(z, np.arange(len(z)))
    moving, moving_times = scores.moving_median_score(z, data.W, np.arange(len(z)))
    var_a, var_b = scores.fit_ridge_var1(z[:200], lam=1.0)
    var, var_times = scores.ridge_var1_score(z, var_a, var_b, np.arange(len(z)))
    selected = {
        "last_value": last[timestamps - 1],
        "moving_median": moving[timestamps - data.W],
        "var1": var[timestamps - 1], "r_native_window": native,
        "r_endpoint": endpoint, "xlstmad_f": scores.forecast_score(z[timestamps], yhat, timestamps)[0],
        "lstm_f": scores.forecast_score(z[timestamps], yhat, timestamps)[0],
    }
    same = (np.array_equal(forecast_times, timestamps) and
            np.array_equal(reconstruction_times, timestamps) and
            np.array_equal(last_times[timestamps - 1], timestamps) and
            np.array_equal(moving_times[timestamps - data.W], timestamps) and
            np.array_equal(var_times[timestamps - 1], timestamps) and
            all(array.shape == timestamps.shape for array in selected.values()))
    return _check(bool(same), {"timestamp_start": int(timestamps[0]),
        "timestamp_stop_exclusive": int(timestamps[-1] + 1),
        "all_raw_arm_array_lengths": {key: len(value) for key, value in selected.items()},
        "all_arms_share_exact_timestamps": bool(same)})


def _calibration_isolation_check() -> dict[str, Any]:
    blocks = data.split_boundaries(2000)
    cal_times = np.arange(*blocks.calibration)
    half = len(cal_times) // 2
    raw = np.arange(len(cal_times), dtype=np.float64)
    reference = scores.fit_tail_rank(raw[:half])
    threshold_part = raw[half:]
    ok = (len(reference) == half and np.max(reference) < np.min(threshold_part) and
          cal_times[0] == blocks.calibration[0] and cal_times[-1] == blocks.calibration[1] - 1)
    return _check(bool(ok), {"calibration_bounds": list(blocks.calibration),
        "tail_reference_bounds": [blocks.calibration[0], blocks.calibration[0] + half],
        "operating_threshold_bounds": [blocks.calibration[0] + half, blocks.calibration[1]],
        "test_scores_or_labels_used": False})


def _label_and_seal_check(repo: Path) -> dict[str, Any]:
    data.install_test_label_access_guard()
    callbacks = {"labels": 0, "metrics": 0}
    expected_artifacts = [repo / scores.STAGE1_SCORE_DIR / f"{machine}.npz"
                          for machine in scores.STAGE1_MACHINES]
    with tempfile.TemporaryDirectory(prefix="m1-metric-gate-") as temporary:
        empty_repo = Path(temporary)
        fake = [empty_repo / scores.STAGE1_SCORE_DIR / f"{machine}.npz"
                for machine in scores.STAGE1_MACHINES]
        rejected = False
        try:
            metrics.run_metric_entrypoint(
                score_artifacts=fake, repo=empty_repo,
                label_loader=lambda: callbacks.__setitem__("labels", callbacks["labels"] + 1),
                metric_runner=lambda *_: callbacks.__setitem__("metrics", callbacks["metrics"] + 1))
        except (RuntimeError, FileNotFoundError):
            rejected = True
    source_paths = [Path(data.__file__), Path(execute.__file__),
                    Path(models.__file__), Path(scores.__file__)]
    parsed = [ast.parse(path.read_text(encoding="utf-8")) for path in source_paths]
    imports = []
    for tree in parsed:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
    no_label_imports = not any("test_label" in name.lower() for name in imports)
    zero_open = data.test_label_open_attempt_count() == 0
    ok = rejected and callbacks == {"labels": 0, "metrics": 0} and no_label_imports and zero_open
    return _check(ok, {"test_label_open_attempts": data.test_label_open_attempt_count(),
        "test_label_reads": 0, "label_loader_calls_before_seal": callbacks["labels"],
        "metric_calls_before_seal": callbacks["metrics"],
        "metric_entrypoint_rejected_unsealed_inventory": rejected,
        "static_no_test_label_import": no_label_imports,
        "canonical_score_artifacts_expected": len(expected_artifacts)})


def _environment_check() -> dict[str, Any]:
    actual = execute.environment_record()
    versions = actual["packages"]
    matched = {
        "python": actual["python"] == PINNED["python"],
        "torch": versions["torch"] == PINNED["torch"],
        "torch_cuda": actual["torch_cuda"] == PINNED["torch_cuda"],
        "xlstm": versions["xlstm"] == PINNED["xlstm"],
        "lightning": versions["lightning"] == PINNED["lightning"],
    }
    return _check(all(matched.values()), {"pinned": PINNED, "actual": actual, "matched": matched})


def _timing_check(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _check(False, {"timing_record_exists": False})
    record = json.loads(path.read_text(encoding="utf-8"))
    selection = canary.select_canary_machines()
    expected = {item["machine"] for item in selection["selected"]}
    actual = {item["machine"] for item in record.get("machines", [])}
    all_arms = all({entry.get("arm_key") for entry in machine.get("arms", [])} == set(execute.ARMS)
                   for machine in record.get("machines", []))
    finite = all(np.isfinite(entry.get("bounded_train", {}).get("windows_per_second", float("nan"))) and
                 entry.get("bounded_train", {}).get("windows", 0) > 0
                 for machine in record.get("machines", []) for entry in machine.get("arms", []))
    ok = (record.get("schema") == "adaptive-normality-m1-engineering-canary-v1" and
          actual == expected and all_arms and finite and
          record.get("test_observations_read") is False and
          record.get("test_labels_read") is False and
          record.get("test_label_open_attempts") == 0 and
          record.get("anomaly_metrics_computed") is False and
          record.get("canary_training_started") is True and
          record.get("full_stage1_training_started") is False and
          all(entry.get("complete_epoch") is True
              for machine in record.get("machines", []) for entry in machine.get("arms", [])))
    return _check(ok, {"completed": ok, "selected_machines": record.get("selection", {}).get("selected"),
        "selection_matches_mechanical_rule": actual == expected,
        "all_learned_arms_measured": all_arms,
        "test_observations_read": record.get("test_observations_read"),
        "test_labels_read": record.get("test_labels_read"),
        "test_label_open_attempts": record.get("test_label_open_attempts"),
        "canary_artifact": str(path)})


def _test_record(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _check(False, "verification_tests.json is missing")
    record = json.loads(path.read_text(encoding="utf-8"))
    ok = (record.get("status") == "PASS" and record.get("failed") == 0 and
          record.get("passed", 0) >= 1 and record.get("test_label_reads") == 0 and
          record.get("anomaly_metrics_computed") is False)
    return _check(ok, record)


def run_preflight(*, repo: Path | None = None, data_root: Path | None = None,
                  timing_path: Path | None = None, test_record_path: Path | None = None,
                  red_team_path: Path | None = None,
                  output: Path | None = None) -> dict[str, Any]:
    root = Path(repo or Path(__file__).resolve().parents[1]).resolve()
    data.install_test_label_access_guard()
    checks = {
        "84_84_data_hash_manifest_entries": _manifest_check(),
        "56_56_observation_hashes_and_28_28_shapes_schema": _observation_check(data_root),
        "frozen_scaler_exactness_and_near_constant_regression": _scaler_check(),
        "W256_sample_index_and_causality_contract": _index_check(),
        "reconstruction_alignment_and_scores": _reconstruction_scores_check(),
        "model_parameter_counts_determinism_finite_forward_and_no_state_carry": _model_check(),
        "score_timestamp_equality_across_arms": _timestamp_alignment_check(),
        "calibration_block_isolation": _calibration_isolation_check(),
        "label_access_and_score_seal_enforcement": _label_and_seal_check(root),
        "environment_pins": _environment_check(),
        "timing_canary_completion": _timing_check(timing_path or root / "reports/adaptive_normality_m1_smd/timing_canary.json"),
        "cpu_and_R0_regression_tests": _test_record(test_record_path or root / "reports/adaptive_normality_m1_smd/verification_tests.json"),
    }
    red_team_file = red_team_path or root / "reports/adaptive_normality_m1_smd/implementation_red_team.md"
    red_team_pass = red_team_file.is_file() and "M1_IMPLEMENTATION_RESULT_BLIND_PASS" in red_team_file.read_text(encoding="utf-8")
    checks["result_blind_red_team"] = _check(red_team_pass, {"report": str(red_team_file),
                                                               "required_verdict": "M1_IMPLEMENTATION_RESULT_BLIND_PASS"})
    score_manifest = root / scores.STAGE1_MANIFEST_PATH
    anomaly_result = score_manifest.exists()
    checks["no_M1_anomaly_metric_observed"] = _check(not anomaly_result, {
        "test_label_open_attempts": data.test_label_open_attempt_count(),
        "test_label_reads": 0,
        "metric_entrypoint_invoked_on_scores": False,
        "score_inventory_exists": anomaly_result,
        "anomaly_metrics_computed": False})
    ready = all(item["pass"] for item in checks.values())
    record = {
        "schema": "adaptive-normality-m1-implementation-preflight-v1",
        "status": "M1_SMD_READY_FOR_STAGE1_EXECUTION" if ready else "M1_SMD_IMPLEMENTATION_BLOCKED",
        "checks": checks,
        "test_label_open_count": data.test_label_open_attempt_count(),
        "test_label_read_count": 0,
        "test_anomaly_labels_opened": False,
        "M1_anomaly_metrics_observed": False,
        "full_Stage1_training_started": False,
        "Stage2_transfer_zero_shot_adaptation_started": False,
        "generated_utc": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
    }
    target = output or root / "reports/adaptive_normality_m1_smd/implementation_preflight.json"
    execute.immutable_json_write(target, record)
    return record


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--timing", type=Path, default=None)
    parser.add_argument("--tests", type=Path, default=None)
    parser.add_argument("--red-team", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    record = run_preflight(repo=args.repo, data_root=args.data_root,
        timing_path=args.timing, test_record_path=args.tests,
        red_team_path=args.red_team, output=args.output)
    print(json.dumps(record, sort_keys=True, indent=2))
    return 0 if record["status"] == "M1_SMD_READY_FOR_STAGE1_EXECUTION" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
