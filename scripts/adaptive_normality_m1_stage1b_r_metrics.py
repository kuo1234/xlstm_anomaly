"""Metric-only Stage-1B-R diagnostic gate for the frozen nine machines.

This module never trains a model. Real labels are opened only after the exact
Stage-1B-R score/execution inventory is committed and its commit is verified
on the configured remote branch.
"""
from __future__ import annotations

import hashlib
import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

try:
    from scripts import adaptive_normality_m1_data as m1_data
    from scripts import adaptive_normality_m1_metrics as metric_core
    from scripts import adaptive_normality_m1_stage1a as stage1a
    from scripts.adaptive_normality_m1_scores import (
        STAGE1_MACHINES,
        STAGE1_SCORE_NAMES,
        fixed_control_fusion,
        fixed_forecast_control_fusion,
        git_committed,
        higher_empirical_quantile,
        normal_tail_severity,
    )
except ImportError:  # pragma: no cover - direct script execution
    import adaptive_normality_m1_data as m1_data
    import adaptive_normality_m1_metrics as metric_core
    import adaptive_normality_m1_stage1a as stage1a
    from adaptive_normality_m1_scores import (
        STAGE1_MACHINES,
        STAGE1_SCORE_NAMES,
        fixed_control_fusion,
        fixed_forecast_control_fusion,
        git_committed,
        higher_empirical_quantile,
        normal_tail_severity,
    )


ROOT = Path(__file__).resolve().parents[1]
MACHINES = (
    "machine-1-7", "machine-1-3", "machine-1-5",
    "machine-2-4", "machine-2-7", "machine-2-8",
    "machine-3-2", "machine-3-11", "machine-3-7",
)
BASE_DIR = Path("reports/adaptive_normality_m1_smd/stage1b_r")
SCORE_DIR = BASE_DIR / "scores"
SCORE_MANIFEST = BASE_DIR / "score_manifest.json"
EXECUTION_MANIFEST = BASE_DIR / "execution_calibration_manifest.json"
EXECUTION_SUMMARY = BASE_DIR / "execution_summary.json"
RESULTS_JSON = BASE_DIR / "stage1b_r_results.json"
RESULTS_MD = BASE_DIR / "stage1b_r_results.md"
LABEL_LOG = BASE_DIR / "stage1b_r_label_access_log.json"
FEASIBILITY_JSON = BASE_DIR / "stage1b_r_feasibility.json"
R_SCORE_NAMES = ("r_native_window", "r_endpoint")
RESULT_SCHEMA = "adaptive-normality-m1-stage1b-r-diagnostic-v1"
SCORE_SCHEMA = "adaptive-normality-m1-stage1b-r-score-inventory-v1"
EXECUTION_SCHEMA = "adaptive-normality-m1-stage1b-r-execution-calibration-v1"
THRESHOLD_QUANTILE = {"q": 0.99, "method": "higher"}
BRANCH = "research/adaptive-normality-m1-smd"
STAGE1B_SOURCE_FILES = (
    "scripts/adaptive_normality_m1_stage1b_r.py",
    "scripts/adaptive_normality_m1_stage1b_r_metrics.py",
    "scripts/adaptive_normality_m1_stage1b_r_feasibility.py",
    "research/adaptive_normality_m1_smd/stage1b_gate_feasibility.md",
    "scripts/adaptive_normality_m1_stage1a.py",
    "scripts/adaptive_normality_m1_metrics.py",
    "scripts/adaptive_normality_m1_data.py",
    "scripts/adaptive_normality_m1_execute.py",
    "scripts/adaptive_normality_m1_models.py",
    "scripts/adaptive_normality_m1_scores.py",
)


class Stage1BRMetricError(RuntimeError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _array_sha256(values: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()


def compose_stage1b_r_score_arrays(
    stage1a_raw_scores: Mapping[str, np.ndarray],
    r_raw_scores: Mapping[str, np.ndarray],
    timestamps: np.ndarray,
    tail_references: Mapping[str, np.ndarray],
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Build the frozen full nine-score inventory from sealed raw scores."""
    raw_names = ("last_value", "moving_median", "var1", "xlstmad_f", "lstm_f")
    if set(stage1a_raw_scores) != set(raw_names):
        raise ValueError("Stage-1A reuse requires exactly its five raw score arrays")
    if set(r_raw_scores) != set(R_SCORE_NAMES):
        raise ValueError("Stage-1B-R requires exactly R-native-window and R-endpoint arrays")
    times = np.asarray(timestamps, dtype=np.int64)
    if times.ndim != 1 or not len(times) or np.any(np.diff(times) <= 0):
        raise ValueError("timestamps must be a nonempty, strictly increasing vector")
    raw = {**{name: np.asarray(stage1a_raw_scores[name], dtype=np.float64) for name in raw_names},
           **{name: np.asarray(r_raw_scores[name], dtype=np.float64) for name in R_SCORE_NAMES}}
    if any(value.shape != times.shape or not np.isfinite(value).all() for value in raw.values()):
        raise ValueError("all raw arms must be finite and aligned to the shared timestamps")
    expected_refs = {"last_value", "moving_median", "var1", "r_native_window", "r_endpoint", "xlstmad_f"}
    if set(tail_references) != expected_refs:
        raise ValueError("frozen full fusion requires exactly six normal tail references")
    controls = {
        "R-native-window": (normal_tail_severity(raw["r_native_window"], tail_references["r_native_window"]), times),
        "R-endpoint": (normal_tail_severity(raw["r_endpoint"], tail_references["r_endpoint"]), times),
        "last-value": (normal_tail_severity(raw["last_value"], tail_references["last_value"]), times),
        "moving-median": (normal_tail_severity(raw["moving_median"], tail_references["moving_median"]), times),
        "ridge-var1": (normal_tail_severity(raw["var1"], tail_references["var1"]), times),
    }
    control_fusion, control_times = fixed_control_fusion(controls)
    forecast = (normal_tail_severity(raw["xlstmad_f"], tail_references["xlstmad_f"]), times)
    forecast_fusion, forecast_times = fixed_forecast_control_fusion(forecast, controls)
    if not np.array_equal(control_times, times) or not np.array_equal(forecast_times, times):
        raise ValueError("fixed fusion changed the shared timestamp vector")
    result = {**raw, "control_fusion": control_fusion,
              "forecast_control_fusion": forecast_fusion}
    if set(result) != set(STAGE1_SCORE_NAMES):
        raise ValueError("full Stage-1 score inventory differs from the frozen nine")
    return result, times


def build_xlstm_lstm_diagnostic(machine_metrics: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Paired descriptive xLSTM-F/LSTM-F comparison; makes no superiority claim."""
    if len(machine_metrics) != len(MACHINES) or [row.get("machine") for row in machine_metrics] != list(MACHINES):
        raise ValueError("xLSTM/LSTM diagnostic requires ordered metrics for the exact frozen nine")
    paired = []
    for row in machine_metrics:
        forecast = row["scores"]["xlstmad_f"]
        lstm = row["scores"]["lstm_f"]
        paired.append({
            "machine": row["machine"],
            "xlstmad_f_AP": float(forecast["AP"]),
            "lstm_f_AP": float(lstm["AP"]),
            "ap_difference": float(forecast["AP"] - lstm["AP"]),
            "xlstmad_f_normal_point_FPR": float(forecast["normal_point_FPR"]),
            "lstm_f_normal_point_FPR": float(lstm["normal_point_FPR"]),
            "fpr_difference_xlstm_minus_lstm": float(
                forecast["normal_point_FPR"] - lstm["normal_point_FPR"]),
        })
    differences = np.asarray([row["ap_difference"] for row in paired], dtype=np.float64)
    return {
        "mean_ap_difference_xlstm_minus_lstm": float(differences.mean()),
        "positive_ap_difference_machines": int(np.sum(differences > 0.0)),
        "negative_ap_difference_machines": int(np.sum(differences < 0.0)),
        "zero_ap_difference_machines": int(np.sum(differences == 0.0)),
        "mean_fpr_difference_xlstm_minus_lstm": float(np.mean(
            [row["fpr_difference_xlstm_minus_lstm"] for row in paired])),
        "machines": paired,
        "interpretation": "descriptive paired diagnostics only; no xLSTM-specific superiority claim",
        "claim_permitted": False,
    }


def stage1b_r_result_document(
    machine_metrics: list[Mapping[str, Any]],
    feasibility: Mapping[str, Any],
    *,
    seal_sha: str,
    label_access: Mapping[str, Any] | None = None,
    execution_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if len(machine_metrics) != len(MACHINES) or [row.get("machine") for row in machine_metrics] != list(MACHINES):
        raise ValueError("Stage-1B-R results require exactly the ordered frozen nine-machine metric rows")
    if len(seal_sha) != 40 or any(char not in "0123456789abcdef" for char in seal_sha):
        raise ValueError("Stage1B-R score seal SHA must be a full Git commit ID")
    feasibility_decision = feasibility.get("decision")
    if feasibility_decision == "FINAL_COMPLEMENT_ROUTE_STILL_FEASIBLE":
        decision = "FINAL_STAGE1_GATE_STILL_FEASIBLE"
    elif feasibility_decision == "FINAL_COMPLEMENT_ROUTE_IMPOSSIBLE":
        decision = "FINAL_STAGE1_GATE_ALREADY_IMPOSSIBLE"
    else:
        raise ValueError("unknown original complement-route feasibility result")
    fprs = np.asarray([row["scores"]["xlstmad_f"]["normal_point_FPR"] for row in machine_metrics], dtype=np.float64)
    high_fpr = [row["machine"] for row in machine_metrics
                if float(row["scores"]["xlstmad_f"]["normal_point_FPR"]) > 0.05]
    standalone_best_macro = float(fprs.sum() / len(STAGE1_MACHINES))
    standalone_impossible = len(high_fpr) > 2 or standalone_best_macro > 0.02
    delta_values = np.asarray([row["delta_AP_forecast_control_fusion"] for row in machine_metrics], dtype=np.float64)
    documented_rows = []
    for source in machine_metrics:
        row = dict(source)
        row["scores"] = {
            name: {**values, "catastrophic": bool(
                float(values["AP"]) <= float(source["prevalence"]) and
                float(values["event_detection_rate"]) <= 0.10)}
            for name, values in source["scores"].items()
        }
        documented_rows.append(row)
    return {
        "schema": RESULT_SCHEMA,
        "decision": decision,
        "stage1_pass_permitted": False,
        "diagnostic_only": True,
        "STAGE1B_R_SCORE_SEAL_SHA": seal_sha,
        "machine_count": len(MACHINES),
        "machines": documented_rows,
        "complement_delta_AP": {
            "mean": float(delta_values.mean()),
            "positive_machines": int(np.sum(delta_values > 0.0)),
            "per_machine": {row["machine"]: float(row["delta_AP_forecast_control_fusion"])
                            for row in machine_metrics},
        },
        "standalone_xlstmad_f": {
            "status": "FINAL_STANDALONE_ROUTE_IMPOSSIBLE" if standalone_impossible else "FINAL_STANDALONE_ROUTE_STILL_FEASIBLE",
            "observed_high_fpr_machines": high_fpr,
            "observed_high_fpr_count": len(high_fpr),
            "maximum_permitted_high_fpr_count": 2,
            "observed_fpr_sum": float(fprs.sum()),
            "best_case_28_machine_macro_fpr_if_unopened_are_zero": standalone_best_macro,
            "maximum_permitted_macro_fpr": 0.02,
            "reason": "deterministic consequence of the original frozen standalone gate",
        },
        "complement_route_feasibility": dict(feasibility),
        "xlstm_lstm_diagnostic": build_xlstm_lstm_diagnostic(list(machine_metrics)),
        "label_access": dict(label_access or {}),
        "execution_summary": dict(execution_summary or {}),
        "full_28_machine_evaluation_started": False,
        "remaining_19_machines_opened": False,
        "stage1_pass": False,
    }


def _markdown_result(document: Mapping[str, Any]) -> str:
    lines = [
        "# M1 Stage-1B-R diagnostic and feasibility audit",
        "",
        f"Decision: `{document['decision']}`",
        "",
        "This nine-machine result is diagnostic only. It cannot establish Stage-1 success.",
        "The remaining 19 machines were not opened or evaluated.",
        "",
        f"R score seal: `{document['STAGE1B_R_SCORE_SEAL_SHA']}`",
        "",
        "## Per-machine metrics",
        "",
        "| Machine | Prevalence | Score | AP | AUROC | AP/prevalence | Event detection | Onset delay | Miss fraction | Normal FPR | False alarm points/10k | False alarm runs/10k | Recovery delay | Recovery censored | Catastrophic |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    names = ("r_native_window", "r_endpoint", "control_fusion", "forecast_control_fusion",
             "xlstmad_f", "lstm_f", "last_value", "moving_median", "var1")
    for machine in document["machines"]:
        for name in names:
            score = machine["scores"][name]
            lines.append(
                f"| {machine['machine']} | {machine['prevalence']:.8g} | {name} | {score['AP']:.8g} | {score['AUROC']:.8g} | "
                f"{score['AP_over_prevalence']:.8g} | {score['event_detection_rate']:.8g} | "
                f"{score['onset_delay']:.8g} | {score['miss_fraction']:.8g} | {score['normal_point_FPR']:.8g} | "
                f"{score['false_alarm_points_per_10000_normal']:.8g} | "
                f"{score['false_alarm_runs_per_10000_normal']:.8g} | {score['score_recovery_delay']:.8g} | "
                f"{score['score_recovery_censored_count']} | {score['catastrophic']} |"
            )
    lines.extend(["", "## Standalone xLSTMAD-F route", "",
                  f"Status: `{document['standalone_xlstmad_f']['status']}`",
                  f"High-FPR machines: {document['standalone_xlstmad_f']['observed_high_fpr_machines']}",
                  f"Best-case 28-machine macro FPR: {document['standalone_xlstmad_f']['best_case_28_machine_macro_fpr_if_unopened_are_zero']:.8g}",
                  "", "## Complement-route feasibility bounds", "",
                  "```json", json.dumps(document["complement_route_feasibility"], sort_keys=True, indent=2), "```",
                  "", "## xLSTM-F versus LSTM-F diagnostic", "",
                  f"Mean paired AP difference: {document['xlstm_lstm_diagnostic']['mean_ap_difference_xlstm_minus_lstm']:.8g}",
                  f"Machines with positive xLSTM-F minus LSTM-F AP: {document['xlstm_lstm_diagnostic']['positive_ap_difference_machines']}/9",
                  "This comparison is descriptive and does not support an xLSTM-specific superiority claim.",
                  "", "## Execution accounting", "",
                  "```json", json.dumps(document["execution_summary"], sort_keys=True, indent=2), "```", ""])
    return "\n".join(lines)


def write_stage1b_r_result_artifacts(repo: str | Path, document: Mapping[str, Any]) -> dict[str, Path]:
    root = Path(repo).resolve()
    paths = {"json": root / RESULTS_JSON, "markdown": root / RESULTS_MD}
    docs = {paths["json"]: json.dumps(document, sort_keys=True, indent=2, allow_nan=False) + "\n",
            paths["markdown"]: _markdown_result(document)}
    _publish_immutable_documents(docs)
    return paths


def _publish_immutable_documents(documents: Mapping[Path, str]) -> None:
    if any(path.exists() for path in documents):
        raise FileExistsError("Stage-1B-R result artifacts are immutable")
    written = []
    try:
        for path, content in documents.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".partial")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.link(temp_name, path)
                written.append(path)
            finally:
                Path(temp_name).unlink(missing_ok=True)
    except BaseException:
        for path in written:
            path.unlink(missing_ok=True)
        raise


def _write_label_access_log(path: Path, document: Mapping[str, Any]) -> None:
    """Durably update the one-shot access log before/after each label read."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".partial")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(document, handle, sort_keys=True, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        Path(temp_name).unlink(missing_ok=True)


def _remote_sha(repo: Path, remote: str, branch: str) -> str:
    output = subprocess.check_output(
        ["git", "-C", str(repo), "ls-remote", remote, f"refs/heads/{branch}"], text=True
    )
    rows = [line.split() for line in output.splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) < 2:
        raise Stage1BRMetricError("cannot resolve unique remote branch for Stage-1B-R seal gate")
    return rows[0][0]


def _require_remote_r_seal(repo: Path, seal_sha: str, *, remote: str, branch: str) -> str:
    if len(seal_sha) != 40 or any(char not in "0123456789abcdef" for char in seal_sha):
        raise Stage1BRMetricError("Stage-1B-R score seal SHA must be a full Git commit ID")
    remote_sha = _remote_sha(repo, remote, branch)
    try:
        subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", seal_sha, remote_sha],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError) as error:
        raise Stage1BRMetricError("Stage-1B-R score seal is not an ancestor of the remote branch") from error
    try:
        subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", seal_sha, "HEAD"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError) as error:
        raise Stage1BRMetricError("Stage-1B-R score seal is not an ancestor of local HEAD") from error
    return remote_sha


def _git_blob(repo: Path, commit: str, relative: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), "show", f"{commit}:{relative}"])


def _bound_commit_file(repo: Path, seal_sha: str, relative: str, expected_sha: str | None = None) -> Path:
    rel_path = Path(relative)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        raise Stage1BRMetricError(f"sealed artifact path must stay inside the repository: {relative}")
    path = repo / relative
    if not path.is_file() or not git_committed(path, repo):
        raise Stage1BRMetricError(f"required Stage-1B-R artifact is missing or uncommitted: {relative}")
    blob = _git_blob(repo, seal_sha, relative)
    if blob != path.read_bytes():
        raise Stage1BRMetricError(f"Stage-1B-R artifact differs from its pre-label seal commit: {relative}")
    if expected_sha is not None and hashlib.sha256(blob).hexdigest() != expected_sha:
        raise Stage1BRMetricError(f"Stage-1B-R artifact hash differs from its seal: {relative}")
    return path


def _verify_stage1a_reuse(repo: Path, source_commit: str,
                          machine: str, r_run: Mapping[str, Any]) -> dict[str, Any]:
    """Verify all reused Stage-1A artifacts against the R run's source commit."""
    binding = r_run.get("stage1a")
    if not isinstance(binding, Mapping):
        raise Stage1BRMetricError(f"{machine}: Stage-1A reuse provenance is missing")
    expected_global = {
        "score_manifest": stage1a.SCORE_MANIFEST.as_posix(),
        "execution_manifest": stage1a.EXECUTION_MANIFEST.as_posix(),
        "label_access_log": stage1a.LABEL_LOG.as_posix(),
    }
    for key, expected_path in expected_global.items():
        item = binding.get(key)
        if not isinstance(item, Mapping) or item.get("path") != expected_path:
            raise Stage1BRMetricError(f"{machine}: Stage-1A {key} binding differs")
        _bound_commit_file(repo, source_commit, expected_path, item.get("sha256"))

    score_manifest = json.loads(_git_blob(repo, source_commit, stage1a.SCORE_MANIFEST.as_posix()))
    execution_manifest = json.loads(_git_blob(repo, source_commit, stage1a.EXECUTION_MANIFEST.as_posix()))
    if (score_manifest.get("schema") != stage1a.SCORE_SCHEMA or
            score_manifest.get("score_names") != list(stage1a.SCORE_NAMES) or
            [row.get("machine") for row in score_manifest.get("machines", [])] != list(MACHINES) or
            execution_manifest.get("schema") != stage1a.SCHEMA or
            [row.get("machine") for row in execution_manifest.get("machines", [])] != list(MACHINES)):
        raise Stage1BRMetricError("Stage-1A source-commit inventories are not the exact frozen nine")
    score_entry = next(row for row in score_manifest["machines"] if row["machine"] == machine)
    execution_entry = next(row for row in execution_manifest["machines"] if row["machine"] == machine)
    run_rel = stage1a.RUN_DIR.joinpath(machine, "machine_run.json").as_posix()
    if binding.get("run_record") != run_rel:
        raise Stage1BRMetricError(f"{machine}: Stage-1A run-record path differs")
    old_run_path = _bound_commit_file(repo, source_commit, run_rel, binding.get("run_record_sha256"))
    old_run = json.loads(old_run_path.read_text())
    if (old_run.get("machine") != machine or old_run.get("source_commit") != binding.get("source_commit") or
            old_run.get("source_commit") != execution_entry.get("source_commit") or
            execution_entry.get("run_record") != run_rel or
            execution_entry.get("run_record_sha256") != binding.get("run_record_sha256") or
            binding.get("score_artifact") != score_entry.get("artifact") or
            binding.get("score_sha256") != score_entry.get("sha256") or
            execution_entry.get("score_artifact") != score_entry.get("artifact") or
            execution_entry.get("score_sha256") != score_entry.get("sha256") or
            old_run.get("scores", {}).get("path") != score_entry.get("artifact") or
            old_run.get("scores", {}).get("sha256") != score_entry.get("sha256") or
            binding.get("calibration_artifact") != old_run.get("calibration", {}).get("path") or
            binding.get("calibration_sha256") != old_run.get("calibration", {}).get("sha256") or
            binding.get("scaler") != old_run.get("scaler") or
            execution_entry.get("scaler") != old_run.get("scaler") or
            execution_entry.get("arms") != old_run.get("arms") or
            execution_entry.get("thresholds") != old_run.get("thresholds") or
            execution_entry.get("calibration", {}).get("path") != old_run.get("calibration", {}).get("path") or
            execution_entry.get("calibration", {}).get("sha256") != old_run.get("calibration", {}).get("sha256") or
            r_run.get("feature_data") != old_run.get("feature_data")):
        raise Stage1BRMetricError(f"{machine}: Stage-1A run and manifest provenance disagree")
    if binding.get("forecast_arms") != {name: old_run.get("arms", {}).get(name)
                                         for name in ("xlstmad_f", "lstm_f")}:
        raise Stage1BRMetricError(f"{machine}: Stage-1A forecasting checkpoints/run records changed")

    artifact_records = [
        (score_entry["artifact"], score_entry["sha256"]),
        (old_run["calibration"]["path"], old_run["calibration"]["sha256"]),
        (old_run["scaler"]["path"], old_run["scaler"]["sha256"]),
    ]
    for arm in ("xlstmad_f", "lstm_f"):
        arm_record = old_run["arms"][arm]
        artifact_records.extend([
            (arm_record["checkpoint_path"], arm_record["checkpoint_sha256"]),
            (arm_record["run_record_path"], arm_record["run_record_sha256"]),
        ])
    for rel, digest in artifact_records:
        _bound_commit_file(repo, source_commit, rel, digest)
    try:
        stage1a.validate_run_record(machine, old_run, source_commit=old_run["source_commit"], repo=repo)
    except Exception as error:
        raise Stage1BRMetricError(f"{machine}: frozen Stage-1A artifact chain failed revalidation") from error
    label_log = json.loads(_git_blob(repo, source_commit, stage1a.LABEL_LOG.as_posix()))
    if (label_log.get("machines_opened") != list(MACHINES) or
            label_log.get("other_19_unopened") is not True or
            label_log.get("labels_read_before_prelabel_sha") != 0):
        raise Stage1BRMetricError("Stage-1A label log differs from its frozen nine-machine boundary")
    return old_run


def _validate_frozen_calibration_extension(
    stage1b_calibration: Mapping[str, np.ndarray],
    stage1a_calibration: Mapping[str, np.ndarray],
    stage1a_thresholds: Mapping[str, float],
    thresholds: Mapping[str, float],
    machine: str,
) -> None:
    """Ensure R did not rewrite inherited Stage-1A normal references/samples."""
    times = np.asarray(stage1b_calibration["timestamps"], dtype=np.int64)
    if not np.array_equal(times, np.asarray(stage1a_calibration["timestamps"], dtype=np.int64)):
        raise Stage1BRMetricError(f"{machine}: R threshold timestamps differ from Stage-1A")
    for name in ("last_value", "moving_median", "var1", "xlstmad_f", "lstm_f"):
        key = f"threshold_scores__{name}"
        if not np.array_equal(np.asarray(stage1b_calibration[key]), np.asarray(stage1a_calibration[key])):
            raise Stage1BRMetricError(f"{machine}: inherited Stage-1A calibration samples changed for {name}")
        if float(thresholds[name]) != float(stage1a_thresholds[name]):
            raise Stage1BRMetricError(f"{machine}: inherited Stage-1A threshold changed for {name}")
    for name in ("last_value", "moving_median", "var1", "xlstmad_f"):
        key = f"tail_reference__{name}"
        if not np.array_equal(np.asarray(stage1b_calibration[key]), np.asarray(stage1a_calibration[key])):
            raise Stage1BRMetricError(f"{machine}: inherited Stage-1A tail reference changed for {name}")

    references = {
        name: np.asarray(stage1b_calibration[f"tail_reference__{name}"], dtype=np.float64)
        for name in ("last_value", "moving_median", "var1", "r_native_window", "r_endpoint", "xlstmad_f")
    }
    values = {
        name: np.asarray(stage1b_calibration[f"threshold_scores__{name}"], dtype=np.float64)
        for name in STAGE1_SCORE_NAMES
    }
    controls = {
        "R-native-window": (normal_tail_severity(values["r_native_window"], references["r_native_window"]), times),
        "R-endpoint": (normal_tail_severity(values["r_endpoint"], references["r_endpoint"]), times),
        "last-value": (normal_tail_severity(values["last_value"], references["last_value"]), times),
        "moving-median": (normal_tail_severity(values["moving_median"], references["moving_median"]), times),
        "ridge-var1": (normal_tail_severity(values["var1"], references["var1"]), times),
    }
    expected_control, control_times = fixed_control_fusion(controls)
    expected_forecast, forecast_times = fixed_forecast_control_fusion(
        (normal_tail_severity(values["xlstmad_f"], references["xlstmad_f"]), times), controls
    )
    if (not np.array_equal(control_times, times) or not np.array_equal(forecast_times, times) or
            not np.array_equal(values["control_fusion"], expected_control) or
            not np.array_equal(values["forecast_control_fusion"], expected_forecast)):
        raise Stage1BRMetricError(f"{machine}: full fusion calibration samples differ from frozen max-tail rules")


def verify_stage1b_r_score_seal(repo: str | Path, seal_sha: str, *, remote: str = "origin",
                                branch: str = BRANCH) -> dict[str, Any]:
    """Verify remote ancestry and every committed R/calibration score artifact."""
    root = Path(repo).resolve()
    remote_sha = _require_remote_r_seal(root, seal_sha, remote=remote, branch=branch)
    score_manifest_path = root / SCORE_MANIFEST
    execution_manifest_path = root / EXECUTION_MANIFEST
    score_doc = json.loads(_bound_commit_file(root, seal_sha, SCORE_MANIFEST.as_posix()).read_text())
    execution_doc = json.loads(_bound_commit_file(root, seal_sha, EXECUTION_MANIFEST.as_posix()).read_text())
    summary_path = _bound_commit_file(root, seal_sha, EXECUTION_SUMMARY.as_posix())
    summary = json.loads(summary_path.read_text())
    if score_doc.get("schema") != SCORE_SCHEMA or score_doc.get("score_names") != list(R_SCORE_NAMES):
        raise Stage1BRMetricError("Stage-1B-R score seal does not declare the exact two R score arrays")
    if execution_doc.get("schema") != EXECUTION_SCHEMA or execution_doc.get("threshold_quantile") != THRESHOLD_QUANTILE:
        raise Stage1BRMetricError("Stage-1B-R execution/calibration seal has wrong schema or quantile")
    score_entries = score_doc.get("machines")
    execution_entries = execution_doc.get("machines")
    if not isinstance(score_entries, list) or [item.get("machine") for item in score_entries] != list(MACHINES):
        raise Stage1BRMetricError("Stage-1B-R score inventory must contain exactly the frozen ordered nine")
    if not isinstance(execution_entries, list) or [item.get("machine") for item in execution_entries] != list(MACHINES):
        raise Stage1BRMetricError("Stage-1B-R execution inventory must contain exactly the frozen ordered nine")
    if execution_doc.get("test_labels_read") is not False or execution_doc.get("anomaly_metrics_computed") is not False:
        raise Stage1BRMetricError("R execution manifest must certify no labels or anomaly metrics")
    if (summary.get("schema") != "adaptive-normality-m1-stage1b-r-execution-summary-v1" or
            summary.get("machines") != list(MACHINES) or
            summary.get("test_labels_read") is not False or
            summary.get("anomaly_metrics_computed") is not False or
            not isinstance(summary.get("source_commit"), str) or len(summary["source_commit"]) != 40 or
            not np.isfinite(float(summary.get("wall_time_seconds", float("nan")))) or
            not np.isfinite(float(summary.get("training_seconds", float("nan"))))):
        raise Stage1BRMetricError("R execution summary has invalid machine/time/label provenance")
    source_commit = summary["source_commit"]
    for rel in STAGE1B_SOURCE_FILES:
        _bound_commit_file(root, source_commit, rel)
    if not git_committed(score_manifest_path, root) or not git_committed(execution_manifest_path, root):
        raise Stage1BRMetricError("Stage-1B-R top-level manifests must be committed")

    from scripts.adaptive_normality_m1_metrics import STAGE1_SCORE_NAMES as FROZEN_SCORE_NAMES

    score_by_machine = {entry["machine"]: entry for entry in score_entries}
    execution_by_machine = {entry["machine"]: entry for entry in execution_entries}
    for machine in MACHINES:
        score_entry = score_by_machine[machine]
        execution = execution_by_machine[machine]
        if score_entry.get("score_names") != list(R_SCORE_NAMES):
            raise Stage1BRMetricError(f"{machine}: R score array inventory differs")
        score_rel = score_entry.get("artifact")
        if not isinstance(score_rel, str) or not score_rel.startswith(SCORE_DIR.as_posix() + "/"):
            raise Stage1BRMetricError(f"{machine}: R score artifact escapes the isolated directory")
        score_path = _bound_commit_file(root, seal_sha, score_rel, score_entry.get("sha256"))
        if score_path.stat().st_size != int(score_entry.get("bytes", -1)):
            raise Stage1BRMetricError(f"{machine}: R score artifact byte count differs")
        test_rows = int(m1_data.MANIFEST["machines"][machine]["test_rows"])
        with np.load(score_path, allow_pickle=False) as arrays:
            if set(arrays.files) != {"timestamps", *R_SCORE_NAMES}:
                raise Stage1BRMetricError(f"{machine}: R score archive contains unexpected arrays")
            timestamps = np.asarray(arrays["timestamps"])
            expected_times = np.arange(m1_data.W, test_rows, dtype=np.int64)
            if not np.array_equal(timestamps, expected_times):
                raise Stage1BRMetricError(f"{machine}: R scores are not exactly indexed at t in [256,test_rows)")
            if _array_sha256(timestamps) != score_entry.get("timestamp_sha256"):
                raise Stage1BRMetricError(f"{machine}: R timestamp hash differs")
            if (execution.get("score_timestamp_count") != len(timestamps) or
                    run.get("scores", {}).get("timestamp_count") != len(timestamps) or
                    run.get("scores", {}).get("timestamp_sha256") != score_entry.get("timestamp_sha256") or
                    run.get("scores", {}).get("score_names") != list(R_SCORE_NAMES)):
                raise Stage1BRMetricError(f"{machine}: R run timestamp inventory differs")
            if len(timestamps) != int(score_entry.get("count", -1)):
                raise Stage1BRMetricError(f"{machine}: R score timestamp count differs")
            if any(np.asarray(arrays[name]).shape != timestamps.shape or not np.isfinite(arrays[name]).all()
                   for name in R_SCORE_NAMES):
                raise Stage1BRMetricError(f"{machine}: R scores are not finite and aligned")

        run_rel = execution.get("run_record")
        run_sha = execution.get("run_record_sha256")
        if not isinstance(run_rel, str) or not run_rel.startswith((BASE_DIR / "runs").as_posix() + "/"):
            raise Stage1BRMetricError(f"{machine}: run record escapes the isolated directory")
        run_path = _bound_commit_file(root, seal_sha, run_rel, run_sha)
        run = json.loads(run_path.read_text())
        if (run.get("machine") != machine or run.get("source_commit") != execution.get("source_commit") or
                run.get("test_labels_read") is not False or run.get("anomaly_metrics_computed") is not False or
                run.get("status") != "complete"):
            raise Stage1BRMetricError(f"{machine}: R run record identity/flags differ")
        if not isinstance(execution.get("source_commit"), str) or len(execution["source_commit"]) != 40:
            raise Stage1BRMetricError(f"{machine}: source commit missing from R execution seal")
        if execution.get("source_commit") != summary.get("source_commit"):
            raise Stage1BRMetricError(f"{machine}: execution summary and run source commits differ")
        try:
            subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor",
                            execution["source_commit"], seal_sha], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError) as error:
            raise Stage1BRMetricError(f"{machine}: source commit is not an ancestor of R seal") from error

        score_ref = execution.get("score_artifact")
        if (score_ref != score_rel or execution.get("score_sha256") != score_entry.get("sha256") or
                execution.get("score_bytes") != score_entry.get("bytes") or
                run.get("scores", {}).get("path") != score_rel or
                run.get("scores", {}).get("sha256") != score_entry.get("sha256") or
                run.get("scores", {}).get("bytes") != score_entry.get("bytes")):
            raise Stage1BRMetricError(f"{machine}: R score provenance cross-reference differs")
        if execution.get("score_timestamp_sha256") != score_entry.get("timestamp_sha256"):
            raise Stage1BRMetricError(f"{machine}: R score timestamp provenance differs")
        thresholds = execution.get("thresholds")
        if not isinstance(thresholds, Mapping) or set(thresholds) != set(FROZEN_SCORE_NAMES):
            raise Stage1BRMetricError(f"{machine}: exact nine frozen thresholds are required")
        if run.get("thresholds") != thresholds or run.get("threshold_quantile") != THRESHOLD_QUANTILE:
            raise Stage1BRMetricError(f"{machine}: run and seal thresholds/quantile differ")
        if (run.get("seed") != 11 or run.get("W") != m1_data.W or run.get("batch_size") != 128 or
                run.get("parameter_count") != 75_934 or execution.get("seed") != run.get("seed") or
                execution.get("W") != run.get("W") or
                execution.get("parameter_count") != run.get("parameter_count") or
                execution.get("model_state_sha256") != run.get("model_state_sha256")):
            raise Stage1BRMetricError(f"{machine}: frozen R model settings differ")

        checkpoint = execution.get("checkpoint")
        fit_record_ref = execution.get("run_record_artifact")
        scaler = execution.get("scaler")
        if not isinstance(checkpoint, Mapping) or not isinstance(fit_record_ref, Mapping) or not isinstance(scaler, Mapping):
            raise Stage1BRMetricError(f"{machine}: checkpoint, fit record, or scaler seal is missing")
        for artifact, directory in (
            (checkpoint, (BASE_DIR / "runs").as_posix() + "/"),
            (fit_record_ref, (BASE_DIR / "runs").as_posix() + "/"),
            (scaler, stage1a.RUN_DIR.as_posix() + "/"),
        ):
            rel, digest = artifact.get("path"), artifact.get("sha256")
            if not isinstance(rel, str) or not rel.startswith(directory):
                raise Stage1BRMetricError(f"{machine}: sealed artifact path is outside its run directory")
            artifact_path = _bound_commit_file(root, seal_sha, rel, digest)
            if artifact.get("bytes") is not None and artifact_path.stat().st_size != int(artifact["bytes"]):
                raise Stage1BRMetricError(f"{machine}: sealed artifact byte count differs")
        checkpoint_path = root / checkpoint["path"]
        fit_record_path = root / fit_record_ref["path"]
        fit_record = json.loads(fit_record_path.read_text())
        if (run.get("checkpoint") != checkpoint or run.get("run_record") != fit_record_ref or
                run.get("scaler") != scaler or
                fit_record != run.get("fit_record") or fit_record.get("arm_key") != "xlstmad_r" or
                fit_record.get("seed") != 11 or fit_record.get("parameter_count") != 75_934 or
                fit_record.get("best_model_sha256") != run.get("model_state_sha256") or
                fit_record.get("best_model_sha256") != execution.get("model_state_sha256") or
                fit_record.get("best_checkpoint", {}).get("sha256") != checkpoint.get("sha256") or
                fit_record.get("best_checkpoint", {}).get("path") != checkpoint.get("path") or
                checkpoint_path.stat().st_size != int(checkpoint.get("bytes", -1))):
            raise Stage1BRMetricError(f"{machine}: xLSTMAD-R checkpoint/run-record hashes disagree")
        stage1a_run = _verify_stage1a_reuse(root, execution["source_commit"], machine, run)

        calibration = execution.get("calibration")
        if not isinstance(calibration, Mapping):
            raise Stage1BRMetricError(f"{machine}: calibration provenance is missing")
        cal_rel, cal_sha = calibration.get("path"), calibration.get("sha256")
        if not isinstance(cal_rel, str) or not cal_rel.startswith((BASE_DIR / "runs").as_posix() + "/"):
            raise Stage1BRMetricError(f"{machine}: calibration artifact escapes the isolated directory")
        cal_path = _bound_commit_file(root, seal_sha, cal_rel, cal_sha)
        if cal_path.stat().st_size != int(calibration.get("bytes", -1)):
            raise Stage1BRMetricError(f"{machine}: calibration byte count differs")
        with np.load(cal_path, allow_pickle=False) as arrays:
            expected_cal = {"timestamps", *(f"tail_reference__{name}" for name in
                ("last_value", "moving_median", "var1", "r_native_window", "r_endpoint", "xlstmad_f")),
                *(f"threshold_scores__{name}" for name in FROZEN_SCORE_NAMES)}
            if set(arrays.files) != expected_cal:
                raise Stage1BRMetricError(f"{machine}: calibration array inventory differs")
            cal_times = np.asarray(arrays["timestamps"])
            bounds = m1_data.split_boundaries(int(m1_data.MANIFEST["machines"][machine]["train_rows"]))
            cal_start, cal_stop = bounds.calibration
            first_half = (cal_stop - cal_start) // 2
            expected_cal_times = np.arange(cal_start + first_half, cal_stop, dtype=np.int64)
            if not np.array_equal(cal_times, expected_cal_times):
                raise Stage1BRMetricError(f"{machine}: calibration timestamps differ from frozen normal split")
            tail_hashes, tail_counts = {}, {}
            for name in ("last_value", "moving_median", "var1", "r_native_window", "r_endpoint", "xlstmad_f"):
                ref = np.asarray(arrays[f"tail_reference__{name}"])
                if (ref.ndim != 1 or len(ref) != first_half or not len(ref) or
                        not np.isfinite(ref).all() or np.any(ref[1:] < ref[:-1])):
                    raise Stage1BRMetricError(f"{machine}: invalid tail reference for {name}")
                tail_hashes[name] = _array_sha256(ref)
                tail_counts[name] = int(len(ref))
            expected_tail_hashes = execution.get("tail_reference_hashes")
            expected_tail_counts = execution.get("tail_reference_counts")
            if tail_hashes != expected_tail_hashes or tail_counts != expected_tail_counts:
                raise Stage1BRMetricError(f"{machine}: tail reference hashes/counts differ")
            for name in FROZEN_SCORE_NAMES:
                sample = np.asarray(arrays[f"threshold_scores__{name}"])
                if sample.shape != cal_times.shape or not np.isfinite(sample).all():
                    raise Stage1BRMetricError(f"{machine}: invalid threshold calibration scores for {name}")
                expected_threshold = higher_empirical_quantile(sample, 0.99)
                if float(thresholds[name]) != expected_threshold:
                    raise Stage1BRMetricError(f"{machine}: threshold differs from q=.99 higher calibration for {name}")
            old_cal_path = _bound_commit_file(root, execution["source_commit"],
                stage1a_run["calibration"]["path"], stage1a_run["calibration"]["sha256"])
            with np.load(old_cal_path, allow_pickle=False) as old_cal_archive:
                old_calibration = {key: np.asarray(old_cal_archive[key]) for key in old_cal_archive.files}
            _validate_frozen_calibration_extension(
                {key: np.asarray(arrays[key]) for key in arrays.files},
                old_calibration, stage1a_run["thresholds"], thresholds, machine,
            )
        if run.get("calibration", {}).get("path") != cal_rel or run.get("calibration", {}).get("sha256") != cal_sha:
            raise Stage1BRMetricError(f"{machine}: run record does not bind the calibration artifact")
        if execution.get("test_labels_read") is not False or execution.get("anomaly_metrics_computed") is not False:
            raise Stage1BRMetricError(f"{machine}: execution seal flags must remain false")

    return {"score_manifest": score_doc, "execution_manifest": execution_doc,
            "score_entries": score_by_machine, "execution_entries": execution_by_machine,
            "execution_summary": summary,
            "remote_branch_sha": remote_sha, "seal_sha": seal_sha}


def run_after_committed_r_seal(
    *,
    seal_verifier: Callable[[], Any],
    score_loader: Callable[[Any], Any],
    label_loader: Callable[[Any], Any],
    metric_runner: Callable[[Any, Any, Any], Any],
) -> Any:
    """Enforce seal -> score assembly -> authorized-label callback -> metrics."""
    seal = seal_verifier()
    score_data = score_loader(seal)
    labels = label_loader(seal)
    return metric_runner(seal, score_data, labels)


def _verify_stage1a_label_authorization(repo: Path) -> dict[str, Any]:
    path = repo / "reports/adaptive_normality_m1_smd/stage1a_screen/label_access_log.json"
    if not path.is_file() or not git_committed(path, repo):
        raise Stage1BRMetricError("committed Stage-1A label authorization log is required")
    access = json.loads(path.read_text())
    if (access.get("anomaly_metrics_computed") is not True or
            access.get("machines_opened") != list(MACHINES) or
            access.get("other_19_unopened") is not True or
            access.get("labels_read_before_prelabel_sha") != 0):
        raise Stage1BRMetricError("Stage-1A label authorization does not match the frozen nine-machine boundary")
    return access


def _load_sealed_scores(repo: Path, seal: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    stage1a_base = repo / "reports/adaptive_normality_m1_smd/stage1a_screen"
    stage1a_score_doc = json.loads((stage1a_base / "score_manifest.json").read_text())
    stage1a_execution_doc = json.loads((stage1a_base / "execution_calibration_manifest.json").read_text())
    if (stage1a_score_doc.get("score_names") != ["last_value", "moving_median", "var1", "xlstmad_f", "lstm_f",
                                                   "cheap_control_fusion", "forecast_cheap_control_fusion"] or
            [row.get("machine") for row in stage1a_score_doc.get("machines", [])] != list(MACHINES) or
            [row.get("machine") for row in stage1a_execution_doc.get("machines", [])] != list(MACHINES)):
        raise Stage1BRMetricError("committed Stage-1A score/provenance inventory is not the exact frozen nine")
    stage1a_scores_by_machine = {row["machine"]: row for row in stage1a_score_doc["machines"]}
    stage1a_execution_by_machine = {row["machine"]: row for row in stage1a_execution_doc["machines"]}
    result = {}
    raw_stage1a_names = ("last_value", "moving_median", "var1", "xlstmad_f", "lstm_f")
    refs_names = ("last_value", "moving_median", "var1", "r_native_window", "r_endpoint", "xlstmad_f")
    for machine in MACHINES:
        old_score_entry = stage1a_scores_by_machine[machine]
        old_execution = stage1a_execution_by_machine[machine]
        r_execution = seal["execution_entries"][machine]
        expected_stage1a_binding = r_execution.get("stage1a")
        if not isinstance(expected_stage1a_binding, Mapping):
            raise Stage1BRMetricError(f"{machine}: R seal is missing Stage-1A reuse provenance")
        old_score_path = repo / old_score_entry["artifact"]
        if (not old_score_path.is_file() or
                _sha256_file(old_score_path) != old_score_entry.get("sha256") or
                expected_stage1a_binding.get("score_sha256") != old_score_entry.get("sha256")):
            raise Stage1BRMetricError(f"{machine}: committed Stage-1A scores are missing or changed")
        stage1a_run_path = repo / old_execution["run_record"]
        if (not stage1a_run_path.is_file() or
                _sha256_file(stage1a_run_path) != old_execution.get("run_record_sha256") or
                expected_stage1a_binding.get("run_record_sha256") != old_execution.get("run_record_sha256")):
            raise Stage1BRMetricError(f"{machine}: committed Stage-1A run record is missing or changed")
        old_run = json.loads(stage1a_run_path.read_text())
        if (expected_stage1a_binding.get("score_artifact") != old_score_entry.get("artifact") or
                expected_stage1a_binding.get("calibration_artifact") != old_run.get("calibration", {}).get("path") or
                expected_stage1a_binding.get("calibration_sha256") != old_run.get("calibration", {}).get("sha256") or
                expected_stage1a_binding.get("scaler") != old_run.get("scaler") or
                expected_stage1a_binding.get("forecast_arms") !=
                {name: old_run.get("arms", {}).get(name) for name in ("xlstmad_f", "lstm_f")}):
            raise Stage1BRMetricError(f"{machine}: R seal binds different Stage-1A artifacts")
        with np.load(old_score_path, allow_pickle=False) as old_arrays:
            times = np.asarray(old_arrays["timestamps"])
            if set(old_arrays.files) != {"timestamps", *old_score_entry["score_names"]}:
                raise Stage1BRMetricError(f"{machine}: Stage-1A score archive contains unexpected arrays")
            old_raw = {name: np.asarray(old_arrays[name]) for name in raw_stage1a_names}
        r_score_entry = seal["score_entries"][machine]
        r_score_path = repo / r_score_entry["artifact"]
        with np.load(r_score_path, allow_pickle=False) as r_arrays:
            r_times = np.asarray(r_arrays["timestamps"])
            if not np.array_equal(times, r_times):
                raise Stage1BRMetricError(f"{machine}: Stage-1A and R score timestamps differ")
            raw_r = {name: np.asarray(r_arrays[name]) for name in R_SCORE_NAMES}
        calibration_path = repo / r_execution["calibration"]["path"]
        with np.load(calibration_path, allow_pickle=False) as cal_arrays:
            references = {name: np.asarray(cal_arrays[f"tail_reference__{name}"])
                          for name in refs_names}
        result[machine] = {
            "timestamps": times,
            "raw_stage1a": old_raw,
            "raw_r": raw_r,
            "references": references,
            "thresholds": r_execution["thresholds"],
        }
    return result


def _load_nine_labels(repo: Path) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    log = {
        "schema": "adaptive-normality-m1-stage1b-r-label-access-v1",
        "stage1b_r_score_seal_verified": True,
        "new_real_test_label_file_reads": 0,
        "unique_machines_opened": [],
        "open_attempt_in_progress": None,
        "other_19_unopened": True,
        "anomaly_metrics_computed": False,
        "stage1b_r_only_execution_before_seal_was_label_free": True,
        "status": "in_progress",
    }
    log_path = repo / LABEL_LOG
    if log_path.exists():
        raise Stage1BRMetricError("Stage-1B-R label access log already exists; refusing another label read")
    _write_label_access_log(log_path, log)
    loaded = {}
    for machine in MACHINES:
        log["open_attempt_in_progress"] = machine
        log["new_real_test_label_file_reads"] = len(log["unique_machines_opened"]) + 1
        log["unique_machines_opened"] = [*log["unique_machines_opened"], machine]
        _write_label_access_log(log_path, log)
        path = m1_data.data_root() / f"{machine}_test_label.txt"
        try:
            loaded[machine] = metric_core.load_pinned_test_labels(machine, path)
        except BaseException as error:
            log["status"] = "failed_during_label_access"
            log["failure_type"] = type(error).__name__
            log["open_attempt_in_progress"] = None
            _write_label_access_log(log_path, log)
            raise
        log["open_attempt_in_progress"] = None
        _write_label_access_log(log_path, log)
    return loaded, log


def _compute_rows(score_data: Mapping[str, Mapping[str, Any]], labels_by_machine: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for machine in MACHINES:
        item = score_data[machine]
        arrays, timestamps = compose_stage1b_r_score_arrays(
            item["raw_stage1a"], item["raw_r"], item["timestamps"], item["references"])
        labels = labels_by_machine[machine]
        if not np.array_equal(timestamps, labels["timestamps"]):
            raise Stage1BRMetricError(f"{machine}: score timestamps differ from pinned label alignment")
        rows.append(metric_core.evaluate_machine(machine, arrays, labels["labels"], item["thresholds"],
                                                timestamps=timestamps, label_timestamps=labels["timestamps"]))
    return rows


def evaluate_stage1b_r(repo: str | Path, seal_sha: str, *, remote: str = "origin",
                        branch: str = BRANCH) -> dict[str, Any]:
    """Evaluate the full nine-machine complement only after remote R score seal."""
    root = Path(repo).resolve()

    def verify() -> dict[str, Any]:
        destinations = (root / RESULTS_JSON, root / RESULTS_MD, root / LABEL_LOG, root / FEASIBILITY_JSON)
        if any(path.exists() for path in destinations):
            raise Stage1BRMetricError("Stage-1B-R result artifacts already exist; refusing label reaccess or overwrite")
        seal = verify_stage1b_r_score_seal(root, seal_sha, remote=remote, branch=branch)
        _verify_stage1a_label_authorization(root)
        return seal

    def load_scores(seal: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
        return _load_sealed_scores(root, seal)

    def load_labels(seal: Mapping[str, Any]) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
        with metric_core._authorized_production_label_access():
            return _load_nine_labels(root)

    def run_metrics(seal: Mapping[str, Any], scores_by_machine: Mapping[str, Any], label_result: Any) -> dict[str, Any]:
        labels, label_log = label_result
        rows = _compute_rows(scores_by_machine, labels)
        from scripts.adaptive_normality_m1_stage1b_r_feasibility import decide_complement_feasibility

        remaining_lengths = {
            machine: int(m1_data.MANIFEST["machines"][machine]["test_rows"]) - m1_data.W
            for machine in STAGE1_MACHINES if machine not in MACHINES
        }
        feasibility = decide_complement_feasibility(rows, remaining_lengths)
        label_log["anomaly_metrics_computed"] = True
        label_log["status"] = "complete"
        _write_label_access_log(root / LABEL_LOG, label_log)
        result = stage1b_r_result_document(rows, feasibility, seal_sha=seal_sha,
                                          label_access=label_log,
                                          execution_summary=seal["execution_summary"])
        # The result directory is created only after score-seal verification and metric completion.
        docs = {
            root / RESULTS_JSON: json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n",
            root / RESULTS_MD: _markdown_result(result),
            root / FEASIBILITY_JSON: json.dumps(feasibility, sort_keys=True, indent=2, allow_nan=False) + "\n",
        }
        _publish_immutable_documents(docs)
        return result

    return run_after_committed_r_seal(seal_verifier=verify, score_loader=load_scores,
                                      label_loader=load_labels, metric_runner=run_metrics)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate Stage-1B-R diagnostic metrics only after the remote score seal passes."
    )
    parser.add_argument("--seal-sha", required=True, help="full commit ID containing pushed R score/provenance seal")
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default=BRANCH)
    args = parser.parse_args(argv)
    result = evaluate_stage1b_r(args.repo, args.seal_sha, remote=args.remote, branch=args.branch)
    print(json.dumps({
        "decision": result["decision"],
        "score_seal_sha": result["STAGE1B_R_SCORE_SEAL_SHA"],
        "complement_route_status": result["complement_route_feasibility"]["decision"],
        "opened_machines": result["label_access"]["unique_machines_opened"],
        "other_19_unopened": result["label_access"]["other_19_unopened"],
        "stage1_pass_permitted": result["stage1_pass_permitted"],
    }, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
