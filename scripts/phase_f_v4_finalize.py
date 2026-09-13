"""Validate and seal the complete Phase F-v4 training set.

This validator reads only F4 clean-training artifacts and the reference-only
carry-forward manifests.  It never loads test observations or anomaly labels.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/phase_f_v4"
DATA = ROOT / "data/phase_f_v4"
CONFIG_PATH = ROOT / "configs/phase_f_v4.json"
FRESH = ["lstm_33", "lstm_44", "lstm_55", "xlstm_11", "xlstm_22", "xlstm_33", "xlstm_44", "xlstm_55"]
ALL = ["lstm_11", "lstm_22", *FRESH]
RAW_FIELDS = {"allclose", "bitwise", "max_abs", "mean_abs", "failed_element_count", "element_count", "shape", "other_shape", "finite", "shape_valid"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _assert_raw(raw: dict, expected_shape: list[int]) -> None:
    missing = RAW_FIELDS - set(raw)
    if missing:
        raise AssertionError(f"raw diagnostic missing fields: {sorted(missing)}")
    if raw["shape"] != expected_shape or raw["other_shape"] != expected_shape:
        raise AssertionError(f"raw diagnostic shape mismatch: {raw}")
    if raw["finite"] is not True or raw["shape_valid"] is not True:
        raise AssertionError("raw output finite/shape contract failed")


def _fresh_summary(name: str, config: dict) -> dict:
    run_report = REPORT / "runs" / name
    run_data = DATA / "runs" / name
    manifest = json.loads((run_report / "manifest.json").read_text())
    curves = json.loads((run_report / "curves.json").read_text())
    post = json.loads((run_report / "post_training_parity.json").read_text())
    if manifest.get("status") != "PASS" or post.get("status") != "PASS":
        raise AssertionError(f"{name}: manifest/post status is not PASS")
    if manifest.get("epochs") != 50 or len(curves) != 50 or [row.get("epoch") for row in curves] != list(range(1, 51)):
        raise AssertionError(f"{name}: incomplete epoch trace")
    if manifest.get("labels_used") or manifest.get("test_sources_used") or manifest.get("probe_fitting"):
        raise AssertionError(f"{name}: unauthorized data flag")
    if manifest.get("architecture") not in ("lstm", "xlstm"):
        raise AssertionError(f"{name}: unknown architecture")
    expected_parameter_count = config["parameters"][manifest["architecture"]]
    if manifest.get("parameter_count") != expected_parameter_count:
        raise AssertionError(f"{name}: parameter count mismatch")
    if not manifest.get("recurrent_changes") or not any(v.get("best_changed") for v in manifest["recurrent_changes"].values()):
        raise AssertionError(f"{name}: recurrent weights did not change")
    for checkpoint in ("initial.pt", "best.pt", "final.pt"):
        path = run_data / checkpoint
        if not path.is_file():
            raise AssertionError(f"{name}: missing checkpoint {checkpoint}")
        expected = manifest.get("checkpoint_sha256", {}).get(checkpoint)
        if expected != digest(path):
            raise AssertionError(f"{name}: checkpoint hash mismatch {checkpoint}")
    hard_failures = []
    raw_epoch_max = {"B128_vs_B1": 0.0, "B128_vs_B3": 0.0}
    raw_epoch_failed = {"B128_vs_B1": 0, "B128_vs_B3": 0}
    for row in curves:
        canary = row.get("canary", {})
        if not canary.get("pass_"):
            hard_failures.extend(name for name, value in canary.get("checks", {}).items() if value.get("hard") and not value.get("pass_"))
        for label, key in (("B128_vs_B1", "raw_output_B128_vs_B1"), ("B128_vs_B3", "raw_output_B128_vs_B3")):
            raw = canary.get("checks", {}).get(key)
            if raw is None:
                raise AssertionError(f"{name}: missing {key}")
            _assert_raw(raw, [128, 64, 8])
            raw_epoch_max[label] = max(raw_epoch_max[label], float(raw["max_abs"]))
            raw_epoch_failed[label] += int(raw["failed_element_count"])
    for key, check in post.get("checks", {}).items():
        if key in {"output_permutation", "partition_B128_output", "partition_B3_output", "partition_B1_output"}:
            raw = check.get("raw_diagnostic")
            if raw is None:
                raise AssertionError(f"{name}: missing post raw diagnostic {key}")
            _assert_raw(raw, [131, 64, 8])
    if hard_failures:
        raise AssertionError(f"{name}: hard canary failures {sorted(set(hard_failures))}")
    return {
        "run": name,
        "type": "fresh",
        "architecture": manifest["architecture"],
        "seed": manifest["seed"],
        "status": "PASS",
        "epochs": manifest["epochs"],
        "selected_epoch": manifest["selected_epoch"],
        "parameter_count": manifest["parameter_count"],
        "initial_model_hash": manifest["initial_model_hash"],
        "best_model_hash": manifest["best_model_hash"],
        "final_model_hash": manifest["final_model_hash"],
        "checkpoint_sha256": manifest["checkpoint_sha256"],
        "training_order_file_sha256": manifest["training_order_file_sha256"],
        "consumed_order_sha256": manifest["consumed_order_sha256"],
        "training_seconds": manifest["training_seconds"],
        "total_seconds": manifest["total_seconds"],
        "peak_allocated_bytes": manifest["peak_allocated_bytes"],
        "peak_reserved_bytes": manifest["peak_reserved_bytes"],
        "raw_epoch_max_abs": raw_epoch_max,
        "raw_epoch_failed_element_count_sum": raw_epoch_failed,
        "post_training_parity": "PASS",
        "native_predict_calls": manifest["native_predict_calls"],
        "labels_used": False,
        "test_sources_used": False,
        "probe_fitting": False,
    }


def _carry_summary(entry: dict) -> dict:
    manifest_path = ROOT / entry["source_manifest"]
    parity_path = ROOT / entry["source_post_training_parity"]
    checkpoint = ROOT / entry["source_checkpoint"]
    if not manifest_path.is_file() or not parity_path.is_file() or not checkpoint.is_file():
        raise AssertionError(f"{entry['run']}: missing carry-forward source")
    manifest = json.loads(manifest_path.read_text())
    parity = json.loads(parity_path.read_text())
    if manifest.get("status") != "PASS" or parity.get("status") != "PASS" or manifest.get("epochs") != 50:
        raise AssertionError(f"{entry['run']}: carry source not sealed PASS")
    if entry.get("checkpoint_copied") or entry.get("retrained") or entry.get("labels_used") or entry.get("test_sources_used"):
        raise AssertionError(f"{entry['run']}: carry-forward policy violation")
    return {
        "run": entry["run"],
        "type": "carry_forward_reference",
        "architecture": "lstm",
        "seed": entry["seed"],
        "status": "CARRIED_FORWARD",
        "epochs": manifest["epochs"],
        "selected_epoch": manifest["selected_epoch"],
        "best_model_hash": manifest["best_model_hash"],
        "checkpoint_sha256": {"best.pt": digest(checkpoint)},
        "source_checkpoint": entry["source_checkpoint"],
        "source_manifest": entry["source_manifest"],
        "source_post_training_parity": entry["source_post_training_parity"],
        "checkpoint_copied": False,
        "retrained": False,
        "labels_used": False,
        "test_sources_used": False,
        "probe_fitting": False,
    }


def _write_sha256sums() -> None:
    paths = []
    for root in (REPORT, DATA):
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.name != "SHA256SUMS":
                paths.append(path)
    output = REPORT / "SHA256SUMS"
    output.write_text("".join(f"{digest(path)}  {path.relative_to(ROOT)}\n" for path in paths))


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text())
    execution = json.loads((REPORT / "execution.json").read_text())
    if execution.get("status") != "PASS" or sorted(row["run"] for row in execution.get("completed", [])) != sorted(FRESH):
        raise AssertionError("fresh-run execution is not complete")
    carry_manifest = json.loads((REPORT / "carry_forward_manifest.json").read_text())
    if carry_manifest.get("status") != "REFERENCE_ONLY" or len(carry_manifest.get("runs", [])) != 2:
        raise AssertionError("carry-forward manifest is not sealed")

    rows = [_carry_summary(entry) for entry in carry_manifest["runs"]]
    rows.extend(_fresh_summary(name, config) for name in FRESH)
    if [row["run"] for row in rows] != ALL:
        raise AssertionError("final run order mismatch")
    if any("phase_f_v3" in json.dumps(row) for row in rows if row["type"] == "fresh"):
        raise AssertionError("fresh F4 summary references a forbidden F3 artifact")
    environments = [json.loads((REPORT / "runs" / name / "manifest.json").read_text())["environment"] for name in FRESH]
    fingerprints = {environment.get("backend_fingerprint") for environment in environments}
    if len(fingerprints) != 1:
        raise AssertionError(f"backend fingerprint mismatch: {fingerprints}")
    final = {
        "status": "PASS",
        "phase": "F-v4",
        "validity_contract": "raw_output_partition_diagnostic_only_finite_shape_hard",
        "amendment_config_sha256": digest(CONFIG_PATH),
        "implementation_commits": sorted({json.loads((REPORT / "runs" / name / "manifest.json").read_text())["implementation_commit"] for name in FRESH}),
        "backend_fingerprints": sorted(fingerprints),
        "runs": rows,
        "run_counts": {"total": len(rows), "fresh": len(FRESH), "carry_forward": 2, "pass": len(rows)},
        "labels_used": False,
        "test_sources_used": False,
        "probe_fitting": False,
        "anomaly_metrics_computed": False,
        "phase_g_locked": True,
        "forbidden_reuse": config["forbidden_reuse"],
        "execution": execution,
    }
    (REPORT / "final_manifest.json").write_text(json.dumps(final, indent=2, allow_nan=False) + "\n")
    environment = {
        "status": "PASS",
        "phase": "F-v4",
        "backend": environments[0],
        "fresh_run_count": len(FRESH),
        "fresh_training_seconds": {row["run"]: row["training_seconds"] for row in rows if row["type"] == "fresh"},
        "launcher_wall_seconds": execution.get("wall_seconds"),
        "gpu_training_ran": True,
        "labels_used": False,
        "test_sources_used": False,
        "probe_fitting": False,
    }
    (REPORT / "environment_runtime.json").write_text(json.dumps(environment, indent=2, allow_nan=False) + "\n")
    decision = """# Phase F-v4 decision\n\n**PASS — implementation/training validity only.**\n\nAll eight fresh runs completed the fixed 50 epochs and passed the hard score,\ncommon18, recurrent/reference, observer, reset, prefix-causality, finite/shape\nchecks. The two eligible LSTM runs are carried forward by reference only. Raw\nreconstruction partition allclose remains diagnostic as preregistered.\n\nNo anomaly labels, test sources, H2/H3 probes, H3b, H4, or anomaly metrics were\nused. Phase G remains locked pending external review.\n"""
    (REPORT / "decision.md").write_text(decision)
    _write_sha256sums()
    print(json.dumps({"status": final["status"], "runs": len(rows), "fresh": len(FRESH), "sha256sums": str((REPORT / "SHA256SUMS").relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
