"""Frozen Stage-1 evaluator, label loader, and fail-closed provenance gates.

This module is metric-only: it has no execution/training imports, and real SMD
labels are opened only inside ``run_metric_entrypoint`` after both committed
score and execution/calibration manifests validate.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import subprocess
import tempfile
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Callable, Iterable, Mapping, TypeVar

import numpy as np

try:
    from scripts import adaptive_normality_m1_data as m1_data
    from scripts.adaptive_normality_m1_scores import (
        STAGE1_MACHINES, STAGE1_MANIFEST_PATH, STAGE1_SCORE_DIR,
        STAGE1_SCORE_NAMES, _check_times, _scores, _sha256, git_committed,
        verify_score_seal,
    )
except ImportError:  # pragma: no cover
    import adaptive_normality_m1_data as m1_data
    from adaptive_normality_m1_scores import (
        STAGE1_MACHINES, STAGE1_MANIFEST_PATH, STAGE1_SCORE_DIR,
        STAGE1_SCORE_NAMES, _check_times, _scores, _sha256, git_committed,
        verify_score_seal,
    )

T = TypeVar("T")
_PRODUCTION_LABEL_ACCESS: ContextVar[bool] = ContextVar("m1_production_label_access", default=False)
EXECUTION_MANIFEST_PATH = Path("reports/adaptive_normality_m1_smd/stage1_execution_manifest.json")
EXECUTION_SCHEMA = "adaptive-normality-m1-stage1-execution-calibration-v1"
LABEL_ACCESS_LOG_PATH = Path("reports/adaptive_normality_m1_smd/stage1_label_access_log.json")
RESULTS_JSON_PATH = Path("reports/adaptive_normality_m1_smd/stage1_results.json")
RESULTS_MD_PATH = Path("reports/adaptive_normality_m1_smd/stage1_results.md")
GATE_PATH = Path("reports/adaptive_normality_m1_smd/stage1_gate.json")
BOOTSTRAP_SAMPLES = 10_000
BOOTSTRAP_SEED = 901
CONTROL_SCORE_NAMES = ("last_value", "moving_median", "var1", "r_native_window", "r_endpoint")
LEARNED_ARMS = ("xlstmad_f", "lstm_f")
FUSION_ARMS = ("control_fusion", "forecast_control_fusion")
TAIL_REFERENCE_NAMES = (*CONTROL_SCORE_NAMES, "xlstmad_f")


@contextmanager
def _sealed_metric_label_access():
    """Authorize the guard contexts for every import alias of the M1 data module.

    R0 compatibility tests can load the same source once as a package module
    and once as a top-level module. Each copy installs its own audit hook, so
    the metric-only window must set all matching contexts together.
    """
    source = Path(m1_data.__file__).resolve()
    modules = []
    for module in tuple(sys.modules.values()):
        if module is None or not callable(getattr(module, "sealed_metric_label_access", None)):
            continue
        module_file = getattr(module, "__file__", None)
        if module_file and Path(module_file).resolve() == source:
            modules.append(module)
    if m1_data not in modules:
        modules.append(m1_data)
    with ExitStack() as stack:
        for module in modules:
            stack.enter_context(module.sealed_metric_label_access())
        yield


@contextmanager
def _authorized_production_label_access():
    """Open the real-label window only after both committed seals validated."""
    token = _PRODUCTION_LABEL_ACCESS.set(True)
    try:
        with _sealed_metric_label_access():
            yield
    finally:
        _PRODUCTION_LABEL_ACCESS.reset(token)


def _require_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"invalid SHA-256 for {label}")
    return value


def verify_single_score_artifact_seal(path: str | Path, repo: str | Path) -> dict:
    """Verify one committed numeric artifact and its committed sidecar seal."""
    root, artifact = Path(repo).resolve(), Path(path).resolve()
    if not artifact.is_file():
        raise FileNotFoundError(f"required Stage-1 score artifact missing: {artifact}")
    manifest = artifact.with_suffix(artifact.suffix + ".manifest.json")
    if not manifest.is_file():
        raise RuntimeError(f"score artifact is not sealed: {artifact}")
    doc = verify_score_seal(manifest)
    if doc.get("artifact") != artifact.name:
        raise RuntimeError(f"seal points to a different artifact: {manifest}")
    if not git_committed(artifact, root) or not git_committed(manifest, root):
        raise RuntimeError(f"score artifact and seal must both be committed: {artifact}")
    return doc


def require_all_stage1_scores_sealed_and_committed(score_artifacts: Iterable[str | Path], repo: str | Path) -> list[dict]:
    """Backward-compatible explicit single-artifact seal collection check."""
    artifacts = [Path(p).resolve() for p in score_artifacts]
    if not artifacts or len(set(artifacts)) != len(artifacts):
        raise ValueError("required Stage-1 score artifact list must be nonempty and unique")
    return [verify_single_score_artifact_seal(path, repo) for path in artifacts]


def verify_complete_stage1_score_inventory(repo: str | Path) -> dict:
    """Require the exact committed 28-machine/nine-score inventory."""
    root = Path(repo).resolve()
    manifest = root / STAGE1_MANIFEST_PATH
    if not manifest.is_file():
        raise RuntimeError("canonical Stage-1 score inventory seal is missing")
    doc = json.loads(manifest.read_text(encoding="utf-8"))
    if doc.get("schema") != "adaptive-normality-m1-stage1-score-inventory-v1":
        raise RuntimeError("unknown Stage-1 inventory seal schema")
    if doc.get("score_names") != list(STAGE1_SCORE_NAMES):
        raise RuntimeError("Stage-1 inventory does not declare the exact nine score arrays")
    entries = doc.get("machines")
    if not isinstance(entries, list) or [e.get("machine") for e in entries] != list(STAGE1_MACHINES):
        raise RuntimeError("Stage-1 inventory must enumerate the exact ordered frozen 28-machine set")
    if not git_committed(manifest, root):
        raise RuntimeError("Stage-1 inventory manifest must be committed")
    for entry in entries:
        machine = entry["machine"]
        rel = (STAGE1_SCORE_DIR / f"{machine}.npz").as_posix()
        if entry.get("artifact") != rel or entry.get("arrays") != list(STAGE1_SCORE_NAMES):
            raise RuntimeError(f"{machine}: noncanonical artifact path or score array set")
        artifact = root / rel
        if not artifact.is_file() or not git_committed(artifact, root):
            raise RuntimeError(f"{machine}: score artifact must exist and be committed")
        if _sha256(artifact) != entry.get("sha256"):
            raise RuntimeError(f"{machine}: score artifact hash differs from inventory seal")
        with np.load(artifact, allow_pickle=False) as arrays:
            if set(arrays.files) != {"timestamps", *STAGE1_SCORE_NAMES}:
                raise RuntimeError(f"{machine}: artifact does not contain the exact required arrays")
            times = _check_times(arrays["timestamps"], len(arrays["timestamps"]))
            if hashlib.sha256(times.tobytes()).hexdigest() != entry.get("timestamp_sha256"):
                raise RuntimeError(f"{machine}: timestamp hash differs from inventory seal")
            if len(times) != entry.get("count"):
                raise RuntimeError(f"{machine}: timestamp count differs from inventory seal")
            for name in STAGE1_SCORE_NAMES:
                values = _scores(arrays[name])
                if values.ndim != 1 or len(values) != len(times):
                    raise RuntimeError(f"{machine}: invalid score vector {name}")
    return doc


def require_stage1_inventory(repo: str | Path) -> dict:
    """Compatibility wrapper; prefer ``verify_complete_stage1_score_inventory``."""
    return verify_complete_stage1_score_inventory(repo)


def _committed_json(root: Path, rel: object, expected_hash: object, field: str) -> tuple[dict, Path]:
    if not isinstance(rel, str) or Path(rel).is_absolute() or ".." in Path(rel).parts:
        raise ValueError(f"{field} path must be safe and repository-relative")
    path = root / rel
    digest = _require_sha(expected_hash, field)
    if not path.is_file() or _sha256(path) != digest or not git_committed(path, root):
        raise RuntimeError(f"{field} must exist, match its committed hash, and be committed")
    return json.loads(path.read_text(encoding="utf-8")), path


def _file_record(root: Path, rel: object, digest: object, field: str) -> Path:
    if not isinstance(rel, str) or Path(rel).is_absolute() or ".." in Path(rel).parts:
        raise ValueError(f"{field} path must be safe and repository-relative")
    path = root / rel
    if not path.is_file() or _sha256(path) != _require_sha(digest, field) or not git_committed(path, root):
        raise RuntimeError(f"{field} must exist, match its committed hash, and be committed")
    return path


def _array_sha256(values: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()


def verify_complete_execution_calibration_provenance(repo: str | Path, score_inventory: Mapping | None = None) -> dict:
    """Verify the committed execution/calibration seal before any label read."""
    root = Path(repo).resolve()
    path = root / EXECUTION_MANIFEST_PATH
    if not path.is_file():
        raise RuntimeError("canonical Stage-1 execution/calibration manifest is missing")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema") != EXECUTION_SCHEMA or not git_committed(path, root):
        raise RuntimeError("execution/calibration manifest must have the frozen schema and be committed")
    entries = doc.get("machines")
    if not isinstance(entries, list) or [e.get("machine") for e in entries] != list(STAGE1_MACHINES):
        raise RuntimeError("execution/calibration manifest must enumerate the exact ordered 28 machines")
    score_by_machine = ({e["machine"]: e for e in score_inventory["machines"]}
                        if score_inventory is not None else {})
    required_thresholds = set(STAGE1_SCORE_NAMES)
    expected_refs = set(TAIL_REFERENCE_NAMES)
    for entry in entries:
        machine = entry["machine"]
        train_rows = int(m1_data.MANIFEST["machines"][machine]["train_rows"])
        test_rows = int(m1_data.MANIFEST["machines"][machine]["test_rows"])
        blocks = m1_data.split_boundaries(train_rows)
        cal_start, cal_stop = blocks.calibration
        half = max(1, (cal_stop - cal_start) // 2)
        expected_first_bounds = [cal_start, cal_start + half]
        expected_second_bounds = [cal_start + half, cal_stop]
        expected_calibration_timestamps = np.arange(cal_start + half, cal_stop, dtype=np.int64)
        source = entry.get("source_commit")
        if not isinstance(source, str) or len(source) != 40 or any(c not in "0123456789abcdef" for c in source):
            raise ValueError(f"{machine}: source Git commit is missing or malformed")
        try:
            subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", source, "HEAD"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError) as error:
            raise RuntimeError(f"{machine}: source commit is not an ancestor of the committed evaluator") from error
        model_hashes = entry.get("model_state_sha256")
        if not isinstance(model_hashes, dict) or set(model_hashes) != {"xlstmad_r", "xlstmad_f", "lstm_f"}:
            raise RuntimeError(f"{machine}: exact learned-arm model hashes are required")
        for arm, value in model_hashes.items():
            _require_sha(value, f"{machine}/{arm} model state")
        scaler_path = _file_record(root, entry.get("scaler_artifact"), entry.get("scaler_sha256"), f"{machine} scaler")
        cal_path = _file_record(root, entry.get("calibration_artifact"), entry.get("calibration_artifact_sha256"), f"{machine} calibration artifact")
        run_record, _ = _committed_json(root, entry.get("run_record"), entry.get("run_record_sha256"), f"{machine} run record")
        thresholds = entry.get("thresholds")
        quantile = entry.get("threshold_quantile")
        if not isinstance(thresholds, dict) or set(thresholds) != required_thresholds:
            raise RuntimeError(f"{machine}: execution seal must contain exactly nine thresholds")
        if quantile != {"q": 0.99, "method": "higher"}:
            raise RuntimeError(f"{machine}: threshold quantile differs from frozen q=.99 higher rule")
        if any(not isinstance(v, (int, float)) or not np.isfinite(v) for v in thresholds.values()):
            raise ValueError(f"{machine}: thresholds must be finite numbers")
        ref_hashes, ref_counts = entry.get("tail_reference_hashes"), entry.get("tail_reference_counts")
        if not isinstance(ref_hashes, dict) or set(ref_hashes) != expected_refs:
            raise RuntimeError(f"{machine}: tail-reference hashes differ from the six frozen fused inputs")
        if not isinstance(ref_counts, dict) or set(ref_counts) != expected_refs:
            raise RuntimeError(f"{machine}: tail-reference counts differ from the six frozen fused inputs")
        for ref in expected_refs:
            _require_sha(ref_hashes[ref], f"{machine}/{ref} tail reference")
            if not isinstance(ref_counts[ref], int) or ref_counts[ref] != half:
                raise RuntimeError(f"{machine}: tail-reference count differs from frozen first-half calibration boundary: {ref}")
        # Numeric calibration samples independently verify thresholds and refs.
        with np.load(cal_path, allow_pickle=False) as cal_arrays:
            needed = {f"tail_reference__{ref}" for ref in expected_refs}
            needed |= {f"threshold_scores__{name}" for name in STAGE1_SCORE_NAMES}
            needed.add("timestamps")
            if not needed.issubset(set(cal_arrays.files)):
                raise RuntimeError(f"{machine}: calibration artifact is missing frozen arrays")
            cal_timestamps = _check_times(cal_arrays["timestamps"], len(expected_calibration_timestamps))
            if not np.array_equal(cal_timestamps, expected_calibration_timestamps):
                raise RuntimeError(f"{machine}: calibration timestamps differ from frozen second-half boundary")
            for ref in expected_refs:
                values = _scores(cal_arrays[f"tail_reference__{ref}"]).reshape(-1)
                if len(values) != half:
                    raise RuntimeError(f"{machine}: tail-reference array length differs from frozen first-half boundary: {ref}")
                if _array_sha256(values) != ref_hashes[ref]:
                    raise RuntimeError(f"{machine}: tail-reference bytes/count differ from execution seal")
            for name in STAGE1_SCORE_NAMES:
                samples = _scores(cal_arrays[f"threshold_scores__{name}"]).reshape(-1)
                if len(samples) != len(expected_calibration_timestamps):
                    raise RuntimeError(f"{machine}: threshold calibration count differs from frozen timestamps: {name}")
                actual = float(np.quantile(samples, 0.99, method="higher"))
                if actual != float(thresholds[name]):
                    raise RuntimeError(f"{machine}: threshold differs from committed higher-quantile samples: {name}")
        if (run_record.get("schema") != "adaptive-normality-m1-machine-run-v1" or
                run_record.get("machine") != machine or run_record.get("source_commit") != source):
            raise RuntimeError(f"{machine}: run-record identity/source commit differs from execution seal")
        if run_record.get("test_labels_read") is not False or run_record.get("anomaly_metrics_computed") is not False:
            raise RuntimeError(f"{machine}: execution run record is not result-blind")
        calibration = run_record.get("calibration", {})
        if calibration.get("thresholds") != thresholds or calibration.get("threshold_quantile") != quantile:
            raise RuntimeError(f"{machine}: run-record threshold values differ from execution seal")
        if calibration.get("artifact", {}).get("path") != entry["calibration_artifact"] or calibration.get("artifact", {}).get("sha256") != _sha256(cal_path):
            raise RuntimeError(f"{machine}: run-record calibration artifact differs from execution seal")
        scaler = run_record.get("scaler", {})
        if scaler.get("artifact", {}).get("path") != entry["scaler_artifact"] or scaler.get("artifact", {}).get("sha256") != _sha256(scaler_path):
            raise RuntimeError(f"{machine}: run-record scaler artifact differs from execution seal")
        if calibration.get("tail_reference_counts") != ref_counts:
            raise RuntimeError(f"{machine}: run-record tail-reference counts differ from execution seal")
        if (calibration.get("first_half_bounds") != expected_first_bounds or
                calibration.get("second_half_bounds") != expected_second_bounds or
                calibration.get("threshold_calibration_count") != len(expected_calibration_timestamps) or
                calibration.get("threshold_score_names") != list(STAGE1_SCORE_NAMES)):
            raise RuntimeError(f"{machine}: calibration bounds/counts differ from frozen train calibration partition")
        arm_records = run_record.get("arms", {})
        if set(arm_records) != set(model_hashes):
            raise RuntimeError(f"{machine}: run record does not contain exactly three learned arms")
        for arm, digest in model_hashes.items():
            fit_record = arm_records[arm].get("fit", {})
            if fit_record.get("best_model_sha256") != digest:
                raise RuntimeError(f"{machine}: model state hash differs from generating run record")
            if fit_record.get("labels_read") is not False or fit_record.get("test_observations_read") is not False:
                raise RuntimeError(f"{machine}/{arm}: fit run record is not label-isolated")
        checkpoints = entry.get("model_checkpoints")
        if not isinstance(checkpoints, dict) or set(checkpoints) != set(model_hashes):
            raise RuntimeError(f"{machine}: checkpoint provenance is missing an arm")
        for arm, checkpoint in checkpoints.items():
            if not isinstance(checkpoint, dict) or not isinstance(checkpoint.get("path"), str):
                raise ValueError(f"{machine}: malformed {arm} checkpoint provenance")
            _require_sha(checkpoint.get("sha256"), f"{machine}/{arm} checkpoint")
            if not isinstance(checkpoint.get("bytes"), int) or checkpoint["bytes"] <= 0:
                raise ValueError(f"{machine}: malformed {arm} checkpoint byte count")
            fit_checkpoint = arm_records[arm].get("fit", {}).get("best_checkpoint") or {}
            if (fit_checkpoint.get("sha256") != checkpoint["sha256"] or
                    fit_checkpoint.get("bytes") != checkpoint["bytes"] or
                    fit_checkpoint.get("path") != checkpoint["path"]):
                raise RuntimeError(f"{machine}: checkpoint differs from generating run record")
            checkpoint_path = Path(checkpoint["path"])
            if not checkpoint_path.is_absolute():
                checkpoint_path = root / checkpoint_path
            if (not checkpoint_path.is_file() or checkpoint_path.stat().st_size != checkpoint["bytes"] or
                    _sha256(checkpoint_path) != checkpoint["sha256"]):
                raise RuntimeError(f"{machine}: model checkpoint bytes differ from execution seal")
        score_rel = (STAGE1_SCORE_DIR / f"{machine}.npz").as_posix()
        score_hash = _require_sha(entry.get("score_artifact_sha256"), f"{machine} score artifact")
        timestamp_hash = _require_sha(entry.get("timestamp_sha256"), f"{machine} timestamps")
        if entry.get("score_artifact") != score_rel:
            raise RuntimeError(f"{machine}: score artifact path is not canonical")
        score_file = _file_record(root, score_rel, score_hash, f"{machine} score artifact")
        if run_record.get("score_timestamp_sha256") != timestamp_hash:
            raise RuntimeError(f"{machine}: run-record timestamp hash differs from execution seal")
        score_entry = score_by_machine.get(machine)
        if score_inventory is not None and (score_entry is None or score_entry.get("sha256") != score_hash or score_entry.get("timestamp_sha256") != timestamp_hash):
            raise RuntimeError(f"{machine}: execution provenance differs from canonical score inventory")
        with np.load(score_file, allow_pickle=False) as score_arrays:
            timestamps = _check_times(score_arrays["timestamps"], test_rows - 256)
            expected_timestamps = np.arange(256, test_rows, dtype=np.int64)
            if not np.array_equal(timestamps, expected_timestamps):
                raise RuntimeError(f"{machine}: score timestamps are not exactly [256,test_rows)")
            if _array_sha256(timestamps) != timestamp_hash:
                raise RuntimeError(f"{machine}: score timestamp vector differs from execution seal")
    return doc

def load_pinned_test_labels(machine: str, label_path: str | Path, *, manifest: Mapping | None = None,
                            expected_test_rows: int | None = None, warmup: int = 256) -> dict[str, np.ndarray]:
    """Load one manifest-pinned binary label vector and align it at t>=W.

    ``manifest``/``expected_test_rows`` are injection points for isolated
    synthetic tests. Production defaults always use the frozen SMD manifest.
    """
    # Check authorization before Path(label_path), resolve, stat, or open.
    # Custom manifests can exercise parser tests only for non-pinned IDs.
    if manifest is None and not _PRODUCTION_LABEL_ACCESS.get():
        raise RuntimeError("real pinned labels require verified score and execution seals")
    if manifest is not None and machine in m1_data.MANIFEST["machines"]:
        raise RuntimeError("custom label manifests are restricted to synthetic machine IDs")
    m1_data.install_test_label_access_guard()
    if manifest is None and (warmup != 256 or expected_test_rows is not None):
        raise ValueError("production label loading fixes test row count from manifest and warm-up at t=256")
    doc = m1_data.MANIFEST if manifest is None else manifest
    machines = doc.get("machines", {})
    if machine not in machines:
        raise ValueError(f"machine is absent from pinned manifest: {machine}")
    spec = machines[machine].get("test_label")
    if not isinstance(spec, Mapping) or spec.get("evaluator_only") is not True:
        raise ValueError("manifest does not authorize an evaluator-only pinned label file")
    path = Path(label_path)
    if path.name != f"{machine}_test_label.txt":
        raise ValueError("test-label filename must be the exact registered machine label filename")
    if manifest is None and path.resolve().parent != m1_data.data_root().resolve():
        raise ValueError("production test-label path must be under the configured pinned SMD data root")
    if manifest is not None:
        synthetic_path = path.resolve()
        real_root = m1_data.data_root().resolve()
        if synthetic_path == real_root or real_root in synthetic_path.parents:
            raise ValueError("synthetic label fixtures must be outside the configured pinned SMD data root")
    if path.stat().st_size != int(spec["bytes"]):
        raise ValueError("test-label byte count differs from pinned manifest")
    if _sha256(path) != spec["sha256"]:
        raise ValueError("test-label SHA-256 differs from pinned manifest")
    n = expected_test_rows
    if n is None:
        n = int(machines[machine]["test_rows"])
    raw = path.read_text(encoding="ascii")
    lines = raw.splitlines()
    if len(lines) != int(n) or any(line.strip() not in {"0", "1"} for line in lines):
        raise ValueError("test labels must contain exactly one binary value per test row")
    labels = np.asarray([int(line.strip()) for line in lines], dtype=np.uint8)
    if warmup < 0 or warmup > len(labels):
        raise ValueError("invalid warm-up boundary")
    timestamps = np.arange(warmup, len(labels), dtype=np.int64)
    return {"timestamps": timestamps, "labels": labels[warmup:]}


def _binary_labels(labels: np.ndarray) -> np.ndarray:
    a = np.asarray(labels)
    if a.ndim != 1 or not np.isin(a, (0, 1)).all():
        raise ValueError("labels must be a one-dimensional binary vector")
    if len(a) == 0:
        raise ValueError("labels cannot be empty")
    return a.astype(np.uint8)


def average_precision(labels: np.ndarray, scores: np.ndarray) -> float:
    y, s = _binary_labels(labels), _scores(scores).reshape(-1)
    if len(y) != len(s) or not np.any(y):
        raise ValueError("AP requires aligned labels/scores and at least one positive")
    order = np.argsort(-s, kind="mergesort")
    ys = y[order]
    tp = np.cumsum(ys, dtype=np.int64)
    # Evaluate only after complete tie groups, matching average_precision_score.
    ends = np.r_[np.flatnonzero(s[order][1:] != s[order][:-1]), len(y)-1]
    recall = tp[ends] / int(y.sum())
    precision = tp[ends] / (ends + 1)
    return float(np.sum(np.diff(np.r_[0.0, recall]) * precision))


def area_under_roc(labels: np.ndarray, scores: np.ndarray) -> float:
    y, s = _binary_labels(labels), _scores(scores).reshape(-1)
    if len(y) != len(s) or not y.any() or y.all():
        raise ValueError("AUROC requires aligned labels containing both classes")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), dtype=np.float64)
    sorted_scores = s[order]
    i = 0
    while i < len(s):
        j = i + 1
        while j < len(s) and sorted_scores[j] == sorted_scores[i]:
            j += 1
        ranks[order[i:j]] = (i + 1 + j) / 2.0
        i = j
    pos, neg = int(y.sum()), int((1-y).sum())
    return float((ranks[y == 1].sum() - pos * (pos + 1) / 2) / (pos * neg))


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    padded = np.r_[False, np.asarray(mask, dtype=bool), False].astype(np.int8)
    starts = np.flatnonzero(np.diff(padded) == 1)
    ends = np.flatnonzero(np.diff(padded) == -1)
    return list(zip(starts.tolist(), ends.tolist()))


def event_metrics(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict:
    """Pointwise-threshold event metrics, with frozen censoring edge rules."""
    y, s = _binary_labels(labels), _scores(scores).reshape(-1)
    if len(y) != len(s) or not np.isfinite(threshold):
        raise ValueError("event labels/scores must align and threshold must be finite")
    alarm = s >= float(threshold)
    events = _runs(y == 1)
    delays, misses, detected = [], 0, 0
    recovery_delays, recovery_censored, recovery_censor_reasons = [], [], []
    for i, (start, stop) in enumerate(events):
        hits = np.flatnonzero(alarm[start:stop])
        if len(hits):
            detected += 1
            delays.append(int(hits[0]))
        else:
            misses += 1
            delays.append(int(stop-start))  # censored-at-event-length descriptive delay
        boundary = events[i+1][0] if i+1 < len(events) else len(y)
        cursor, streak, recovered = stop, 0, False
        while cursor < boundary:
            if y[cursor] == 0 and not alarm[cursor]:
                streak += 1
                if streak == 10:
                    recovered = True
                    cursor += 1
                    break
            else:
                streak = 0
            cursor += 1
        recovery_delays.append(int(cursor-stop))
        recovery_censored.append(not recovered)
        recovery_censor_reasons.append(None if recovered else ("next_event" if i + 1 < len(events) else "test_end"))
    normal = y == 0
    fpr = float(np.mean(alarm[normal])) if normal.any() else float("nan")
    # Count contiguous alarm runs whose first alarm lies on a normal point.
    false_runs = len(_runs(alarm & normal))
    normal_count = int(normal.sum())
    false_points = int(alarm[normal].sum())
    return {
        "event_count": len(events), "event_detection_rate": detected / len(events) if events else 0.0,
        "detected_event_count": int(detected), "missed_event_count": int(misses),
        "onset_delay": float(np.mean(delays)) if delays else 0.0,
        "miss_fraction": misses / len(events) if events else 0.0,
        "normal_point_FPR": fpr,
        "normal_point_count": normal_count, "false_alarm_point_count": false_points,
        "false_alarm_run_count": int(false_runs),
        "false_alarm_points_per_10000_normal": float(false_points * 10000 / normal_count) if normal_count else float("nan"),
        "false_alarm_runs_per_10000_normal": float(false_runs * 10000 / normal_count) if normal_count else float("nan"),
        "score_recovery_delay": float(np.mean(recovery_delays)) if recovery_delays else 0.0,
        "score_recovery_censored_count": int(sum(recovery_censored)),
        "score_recovery_censoring": recovery_censored,
        "score_recovery_censor_reason_by_event": recovery_censor_reasons,
        "onset_delay_by_event": delays,
        "score_recovery_delay_by_event": recovery_delays,
    }


def evaluate_machine(machine: str, score_arrays: Mapping[str, np.ndarray], labels: np.ndarray,
                     thresholds: Mapping[str, float], timestamps: np.ndarray | None = None,
                     label_timestamps: np.ndarray | None = None) -> dict:
    """Compute all nine per-machine point, event, and comparator metrics."""
    if set(score_arrays) != set(STAGE1_SCORE_NAMES) or set(thresholds) != set(STAGE1_SCORE_NAMES):
        raise ValueError("exact frozen nine-score arrays and thresholds are required")
    y = _binary_labels(labels)
    if timestamps is not None and label_timestamps is not None and not np.array_equal(timestamps, label_timestamps):
        raise ValueError("score and aligned test-label timestamps differ")
    scores = {name: _scores(score_arrays[name]).reshape(-1) for name in STAGE1_SCORE_NAMES}
    if any(len(v) != len(y) for v in scores.values()):
        raise ValueError("all nine score arrays must align exactly with labels")
    prevalence = float(y.mean())
    result = {"machine": machine, "prevalence": prevalence, "scores": {}}
    for name in STAGE1_SCORE_NAMES:
        ap = average_precision(y, scores[name])
        roc = area_under_roc(y, scores[name])
        events = event_metrics(y, scores[name], float(thresholds[name]))
        result["scores"][name] = {"AP": ap, "AUROC": roc, "AP_over_prevalence": ap / prevalence,
                                  "threshold": float(thresholds[name]), **events}
    winner = max(CONTROL_SCORE_NAMES, key=lambda name: result["scores"][name]["AP"])
    result["oracle_control_AP"] = result["scores"][winner]["AP"]
    result["oracle_control_winner"] = winner
    result["delta_AP_xlstmad_f"] = result["scores"]["xlstmad_f"]["AP"] - result["oracle_control_AP"]
    result["delta_AP_forecast_control_fusion"] = (result["scores"]["forecast_control_fusion"]["AP"] -
                                                    result["scores"]["control_fusion"]["AP"])
    result["delta_AP_lstm_f"] = result["scores"]["lstm_f"]["AP"] - result["oracle_control_AP"]
    return result


def _distribution_summary(values: Iterable[float]) -> dict[str, float]:
    array = np.asarray(list(values), dtype=np.float64)
    if not len(array) or not np.isfinite(array).all():
        raise ValueError("aggregate metrics require nonempty finite per-machine values")
    return {"macro_mean": float(array.mean()), "median": float(np.median(array)),
            "minimum": float(array.min()), "maximum": float(array.max())}


def summarize_stage1_metrics(machine_metrics: list[dict]) -> dict:
    """Equal-machine and descriptive micro summaries, without changing gates."""
    if len(machine_metrics) != 28 or [row.get("machine") for row in machine_metrics] != list(STAGE1_MACHINES):
        raise ValueError("Stage-1 summaries require ordered metrics for exactly the frozen 28 machines")
    summary = {
        "machine_count": len(machine_metrics),
        "prevalence": _distribution_summary(row["prevalence"] for row in machine_metrics),
        "oracle_control_AP": _distribution_summary(row["oracle_control_AP"] for row in machine_metrics),
        "per_score": {},
        "delta_AP_xlstmad_f": _distribution_summary(row["delta_AP_xlstmad_f"] for row in machine_metrics),
        "delta_AP_forecast_control_fusion": _distribution_summary(
            row["delta_AP_forecast_control_fusion"] for row in machine_metrics),
        "delta_AP_lstm_f": _distribution_summary(row["delta_AP_lstm_f"] for row in machine_metrics),
    }
    fields = ("AP", "AUROC", "AP_over_prevalence", "event_detection_rate", "onset_delay",
              "miss_fraction", "normal_point_FPR", "false_alarm_points_per_10000_normal",
              "false_alarm_runs_per_10000_normal", "score_recovery_delay")
    for name in STAGE1_SCORE_NAMES:
        per_machine = [row["scores"][name] for row in machine_metrics]
        score_summary = {field: _distribution_summary(row[field] for row in per_machine)
                         for field in fields}
        score_summary["AP_above_prevalence_machines"] = int(sum(
            row["scores"][name]["AP"] > row["prevalence"] for row in machine_metrics))
        total_events = sum(row["event_count"] for row in per_machine)
        total_normals = sum(row["normal_point_count"] for row in per_machine)
        total_false_points = sum(row["false_alarm_point_count"] for row in per_machine)
        total_false_runs = sum(row["false_alarm_run_count"] for row in per_machine)
        all_onset_delays = [delay for row in per_machine for delay in row["onset_delay_by_event"]]
        all_recovery_delays = [delay for row in per_machine for delay in row["score_recovery_delay_by_event"]]
        score_summary["micro_event_count"] = int(total_events)
        score_summary["micro_event_detection_rate"] = (
            float(sum(row["detected_event_count"] for row in per_machine) / total_events)
            if total_events else 0.0)
        score_summary["micro_miss_fraction"] = (
            float(sum(row["missed_event_count"] for row in per_machine) / total_events)
            if total_events else 0.0)
        score_summary["micro_onset_delay"] = float(np.mean(all_onset_delays)) if all_onset_delays else 0.0
        score_summary["micro_score_recovery_delay"] = (
            float(np.mean(all_recovery_delays)) if all_recovery_delays else 0.0)
        score_summary["micro_score_recovery_censored_events"] = int(
            sum(row["score_recovery_censored_count"] for row in per_machine))
        score_summary["micro_normal_point_FPR"] = (
            float(total_false_points / total_normals) if total_normals else 0.0)
        score_summary["micro_false_alarm_points_per_10000_normal"] = (
            float(total_false_points * 10000 / total_normals) if total_normals else 0.0)
        score_summary["micro_false_alarm_runs_per_10000_normal"] = (
            float(total_false_runs * 10000 / total_normals) if total_normals else 0.0)
        summary["per_score"][name] = score_summary
    return summary


def paired_machine_bootstrap(differences: np.ndarray, *, samples: int = BOOTSTRAP_SAMPLES,
                             seed: int = BOOTSTRAP_SEED) -> dict:
    """Paired whole-machine percentile interval; fixed 10,000/901 contract."""
    values = np.asarray(differences, dtype=np.float64)
    if values.shape != (28,) or not np.isfinite(values).all():
        raise ValueError("paired machine bootstrap requires 28 finite machine effects")
    if samples != BOOTSTRAP_SAMPLES or seed != BOOTSTRAP_SEED:
        raise ValueError("Stage-1 bootstrap is frozen at 10,000 resamples and seed 901")
    indices = np.random.default_rng(seed).integers(0, len(values), size=(samples, len(values)))
    means = values[indices].mean(axis=1)
    lower, upper = np.percentile(means, [2.5, 97.5])
    return {"mean": float(values.mean()), "lower_95": float(lower), "upper_95": float(upper),
            "samples": samples, "seed": seed, "resampling_unit": "paired machine", "bootstrap_means": means}


def _route_gate(machine_metrics: list[dict], delta_key: str, candidate: str) -> dict:
    if len(machine_metrics) != 28 or [m.get("machine") for m in machine_metrics] != list(STAGE1_MACHINES):
        raise ValueError("mechanical Stage-1 gate requires ordered metrics for exactly 28 machines")
    deltas = np.asarray([m[delta_key] for m in machine_metrics], dtype=np.float64)
    boot = paired_machine_bootstrap(deltas)
    aps = np.asarray([m["scores"][candidate]["AP"] for m in machine_metrics])
    prevalence = np.asarray([m["prevalence"] for m in machine_metrics])
    ap_ratio = aps / prevalence
    event = np.asarray([m["scores"][candidate]["event_detection_rate"] for m in machine_metrics])
    fpr = np.asarray([m["scores"][candidate]["normal_point_FPR"] for m in machine_metrics])
    catastrophic = [m["machine"] for m, ap, prev, ev in zip(machine_metrics, aps, prevalence, event)
                    if ap <= prev and ev <= 0.10]
    high_fpr = [m["machine"] for m, value in zip(machine_metrics, fpr) if value > 0.05]
    components = {
        "macro_delta_ap_ge_0_02": float(deltas.mean()) >= 0.02,
        "bootstrap_lower_95_gt_0": boot["lower_95"] > 0.0,
        "positive_delta_on_at_least_20": int(np.sum(deltas > 0)) >= 20,
        "ap_above_prevalence_on_at_least_20": int(np.sum(aps > prevalence)) >= 20,
        "median_ap_over_prevalence_ge_1_5": float(np.median(ap_ratio)) >= 1.5,
        "macro_event_detection_ge_0_50": float(event.mean()) >= 0.50,
        "macro_normal_point_fpr_le_0_02": float(fpr.mean()) <= 0.02,
        "no_more_than_two_fpr_over_0_05": len(high_fpr) <= 2,
        "no_more_than_two_catastrophic": len(catastrophic) <= 2,
    }
    return {"candidate": candidate, "delta_ap": boot["mean"], "bootstrap": {k: v for k, v in boot.items() if k != "bootstrap_means"},
            "positive_delta_machines": int(np.sum(deltas > 0)), "ap_above_prevalence_machines": int(np.sum(aps > prevalence)),
            "median_ap_over_prevalence": float(np.median(ap_ratio)), "macro_event_detection_rate": float(event.mean()),
            "macro_normal_point_FPR": float(fpr.mean()), "high_fpr_machines": high_fpr,
            "catastrophic_machines": catastrophic, "gate_components": components,
            "failed_gate_components": [k for k, passed in components.items() if not passed],
            "passed": all(components.values())}


def _validate_complete_machine_metrics(machine_metrics: list[dict]) -> None:
    """Reject partial or internally inconsistent inputs to the final decision."""
    if len(machine_metrics) != 28 or [m.get("machine") for m in machine_metrics] != list(STAGE1_MACHINES):
        raise ValueError("mechanical Stage-1 decision requires ordered metrics for exactly 28 machines")
    required_score_fields = {
        "AP", "AUROC", "AP_over_prevalence", "threshold", "event_count",
        "event_detection_rate", "detected_event_count", "missed_event_count",
        "onset_delay", "onset_delay_by_event", "miss_fraction", "normal_point_FPR",
        "normal_point_count", "false_alarm_point_count", "false_alarm_run_count",
        "false_alarm_points_per_10000_normal", "false_alarm_runs_per_10000_normal",
        "score_recovery_delay", "score_recovery_censored_count", "score_recovery_censoring",
        "score_recovery_delay_by_event",
        "score_recovery_censor_reason_by_event",
    }
    for row in machine_metrics:
        prevalence = row.get("prevalence")
        if not isinstance(prevalence, (int, float)) or not np.isfinite(prevalence) or not 0 < prevalence < 1:
            raise ValueError(f"{row.get('machine')}: complete decision metrics require both label classes")
        by_score = row.get("scores")
        if not isinstance(by_score, Mapping) or set(by_score) != set(STAGE1_SCORE_NAMES):
            raise ValueError(f"{row['machine']}: decision requires exactly the frozen nine score records")
        for name in STAGE1_SCORE_NAMES:
            values = by_score[name]
            if not isinstance(values, Mapping) or not required_score_fields.issubset(values):
                raise ValueError(f"{row['machine']}/{name}: incomplete frozen per-score metrics")
            numeric = ("AP", "AUROC", "AP_over_prevalence", "threshold", "event_detection_rate",
                       "onset_delay", "miss_fraction", "normal_point_FPR",
                       "false_alarm_points_per_10000_normal", "false_alarm_runs_per_10000_normal",
                       "score_recovery_delay")
            if any(not isinstance(values[key], (int, float)) or not np.isfinite(values[key]) for key in numeric):
                raise ValueError(f"{row['machine']}/{name}: non-finite per-score metric")
            if not (0 <= values["AP"] <= 1 and 0 <= values["AUROC"] <= 1 and
                    0 <= values["event_detection_rate"] <= 1 and 0 <= values["miss_fraction"] <= 1 and
                    0 <= values["normal_point_FPR"] <= 1):
                raise ValueError(f"{row['machine']}/{name}: per-score rate is outside [0,1]")
            if not np.isclose(values["AP_over_prevalence"], values["AP"] / prevalence, rtol=0, atol=1e-12):
                raise ValueError(f"{row['machine']}/{name}: AP/prevalence ratio is inconsistent")
            event_count = values["event_count"]
            detected, missed = values["detected_event_count"], values["missed_event_count"]
            if not isinstance(event_count, int) or event_count < 0 or detected + missed != event_count:
                raise ValueError(f"{row['machine']}/{name}: event counts are inconsistent")
            if len(values["onset_delay_by_event"]) != event_count or len(values["score_recovery_delay_by_event"]) != event_count:
                raise ValueError(f"{row['machine']}/{name}: event delays do not cover every event")
            censoring = values["score_recovery_censoring"]
            if len(censoring) != event_count or int(sum(censoring)) != values["score_recovery_censored_count"]:
                raise ValueError(f"{row['machine']}/{name}: recovery censoring records are inconsistent")
            reasons = values["score_recovery_censor_reason_by_event"]
            if len(reasons) != event_count or any(
                    (reason not in {"next_event", "test_end"}) != (not censored)
                    for reason, censored in zip(reasons, censoring)):
                raise ValueError(f"{row['machine']}/{name}: recovery censor reasons are inconsistent")
            if event_count and (not np.isclose(values["event_detection_rate"], detected / event_count, atol=1e-12) or
                                not np.isclose(values["miss_fraction"], missed / event_count, atol=1e-12)):
                raise ValueError(f"{row['machine']}/{name}: event rates do not match event counts")
            normal_count, false_points, false_runs = (
                values["normal_point_count"], values["false_alarm_point_count"], values["false_alarm_run_count"])
            if not all(isinstance(v, int) and v >= 0 for v in (normal_count, false_points, false_runs)):
                raise ValueError(f"{row['machine']}/{name}: invalid normal-point false-alarm counts")
            if normal_count == 0 or false_points > normal_count:
                raise ValueError(f"{row['machine']}/{name}: invalid normal-point denominator/count")
            if not np.isclose(values["normal_point_FPR"], false_points / normal_count, rtol=0, atol=1e-12):
                raise ValueError(f"{row['machine']}/{name}: normal-point FPR does not match counts")
        expected_oracle = max(CONTROL_SCORE_NAMES, key=lambda name: by_score[name]["AP"])
        if row.get("oracle_control_winner") != expected_oracle or not np.isclose(
                row.get("oracle_control_AP", float("nan")), by_score[expected_oracle]["AP"], rtol=0, atol=1e-12):
            raise ValueError(f"{row['machine']}: oracle control envelope does not match its five controls")
        expected_deltas = {
            "delta_AP_xlstmad_f": by_score["xlstmad_f"]["AP"] - by_score[expected_oracle]["AP"],
            "delta_AP_forecast_control_fusion": by_score["forecast_control_fusion"]["AP"] - by_score["control_fusion"]["AP"],
            "delta_AP_lstm_f": by_score["lstm_f"]["AP"] - by_score[expected_oracle]["AP"],
        }
        for key, expected in expected_deltas.items():
            if not np.isclose(row.get(key, float("nan")), expected, rtol=0, atol=1e-12):
                raise ValueError(f"{row['machine']}: {key} is inconsistent with complete score metrics")


def decide_stage1(machine_metrics: list[dict]) -> dict:
    """Return the sole frozen Stage-1 outcome plus diagnostic routes."""
    _validate_complete_machine_metrics(machine_metrics)
    standalone = _route_gate(machine_metrics, "delta_AP_xlstmad_f", "xlstmad_f")
    complement = _route_gate(machine_metrics, "delta_AP_forecast_control_fusion", "forecast_control_fusion")
    lstm = _route_gate(machine_metrics, "delta_AP_lstm_f", "lstm_f")
    return {"decision": "M1_STAGE1_PASS" if standalone["passed"] or complement["passed"] else "FORECASTING_NOT_JUSTIFIED",
            "standalone_route": standalone, "complement_route": complement,
            "lstm_viability": "LSTM_FORECAST_VIABLE" if lstm["passed"] else "LSTM_FORECAST_NOT_VIABLE",
            "lstm_diagnostic_route": lstm,
            "interpretation": "ARCHITECTURE_AGNOSTIC_REFRAME_CANDIDATE"
            if lstm["passed"] and not standalone["passed"] and not complement["passed"] else None}


def result_artifact_documents(machine_metrics: list[dict], gate: Mapping, *, label_access_log: Mapping) -> dict[str, dict]:
    """Build deterministic machine-readable result documents without writing."""
    return {
        RESULTS_JSON_PATH.as_posix(): {"schema": "adaptive-normality-m1-stage1-results-v1",
                                      "summary": summarize_stage1_metrics(machine_metrics),
                                      "machines": machine_metrics},
        GATE_PATH.as_posix(): {"schema": "adaptive-normality-m1-stage1-gate-v1", **dict(gate)},
        LABEL_ACCESS_LOG_PATH.as_posix(): {"schema": "adaptive-normality-m1-label-access-v1", **dict(label_access_log)},
    }


def write_result_artifacts(repo: str | Path, machine_metrics: list[dict], gate: Mapping,
                           label_access_log: Mapping) -> dict[str, Path]:
    """Publish deterministic UTF-8 artifacts once, with exclusive lock and links."""
    root = Path(repo).resolve()
    docs = result_artifact_documents(machine_metrics, gate, label_access_log=label_access_log)
    expected_outputs = [root / rel for rel in (*docs.keys(), RESULTS_MD_PATH.as_posix())]
    summary = {"decision": gate["decision"], "machines": len(machine_metrics),
               "real_SMD_test_label_reads": label_access_log.get("real_SMD_test_label_reads", 0)}
    machine_summary = summarize_stage1_metrics(machine_metrics)
    columns = ("Score", "Macro AP", "Median AP", "AP range", "Macro AUROC",
               "Macro AP/prevalence", "Macro event detection", "Macro normal FPR")
    lines = ["# M1 Stage-1 results", "", *[f"- {k}: {v}" for k, v in summary.items()], "",
             "| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for name in STAGE1_SCORE_NAMES:
        values = machine_summary["per_score"][name]
        row = (name, values["AP"]["macro_mean"], values["AP"]["median"],
               f'{values["AP"]["minimum"]}–{values["AP"]["maximum"]}',
               values["AUROC"]["macro_mean"], values["AP_over_prevalence"]["macro_mean"],
               values["event_detection_rate"]["macro_mean"],
               values["normal_point_FPR"]["macro_mean"])
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    rendered = {root / rel: json.dumps(document, sort_keys=True, indent=2, allow_nan=False) + "\n"
                for rel, document in docs.items()}
    rendered[root / RESULTS_MD_PATH] = "\n".join(lines) + "\n"
    for destination in expected_outputs:
        destination.parent.mkdir(parents=True, exist_ok=True)
    lock_path = root / "reports/adaptive_normality_m1_smd/.stage1_results.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise FileExistsError("Stage-1 result publication is already in progress or was interrupted") from error
    staged: list[Path] = []
    published: list[Path] = []
    try:
        if any(path.exists() for path in expected_outputs):
            raise FileExistsError("Stage-1 result artifacts are immutable and already exist")
        for destination, content in rendered.items():
            fd, temp_name = tempfile.mkstemp(prefix=".stage1-result-", dir=destination.parent)
            temp_path = Path(temp_name)
            staged.append(temp_path)
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        for source, destination in zip(staged, rendered):
            os.link(source, destination)  # atomic no-replace publication
            published.append(destination)
        return {rel: root / rel for rel in (*docs.keys(), RESULTS_MD_PATH.as_posix())}
    except BaseException:
        for path in published:
            path.unlink(missing_ok=True)
        raise
    finally:
        for path in staged:
            path.unlink(missing_ok=True)
        os.close(lock_fd)
        lock_path.unlink(missing_ok=True)


def evaluate_committed_stage1(repo: str | Path) -> dict:
    """Production metric-only evaluator over the committed canonical inventory.

    Call only after Stage-1 execution artifacts have been committed. This
    verifies all provenance first, then opens each pinned label file, computes
    the frozen per-machine metrics and mechanical decision, and writes the
    four predeclared result artifacts exactly once.
    """
    root = Path(repo).resolve()
    inventory = verify_complete_stage1_score_inventory(root)
    execution = verify_complete_execution_calibration_provenance(root, inventory)
    execution_by_machine = {entry["machine"]: entry for entry in execution["machines"]}
    metrics = []
    labels_root = m1_data.data_root().resolve()
    m1_data.install_test_label_access_guard()
    with _authorized_production_label_access():
        for machine in STAGE1_MACHINES:
            score_path = root / STAGE1_SCORE_DIR / f"{machine}.npz"
            with np.load(score_path, allow_pickle=False) as packed:
                timestamps = packed["timestamps"]
                arrays = {name: packed[name] for name in STAGE1_SCORE_NAMES}
            labels_doc = load_pinned_test_labels(machine, labels_root / f"{machine}_test_label.txt")
            row = evaluate_machine(machine, arrays, labels_doc["labels"],
                                   execution_by_machine[machine]["thresholds"],
                                   timestamps=timestamps, label_timestamps=labels_doc["timestamps"])
            metrics.append(row)
    gate = decide_stage1(metrics)
    access_log = {"real_SMD_test_label_reads": len(STAGE1_MACHINES),
                  "real_M1_anomaly_metrics_computed": True,
                  "label_source": "manifest-pinned SMD test_label files",
                  "warmup_excluded_timestamps": "t < 256",
                  "score_inventory_manifest_sha256": _sha256(root / STAGE1_MANIFEST_PATH),
                  "execution_manifest_sha256": _sha256(root / EXECUTION_MANIFEST_PATH)}
    artifacts = write_result_artifacts(root, metrics, gate, access_log)
    return {"decision": gate["decision"], "gate": gate, "machines": metrics,
            "label_access_log": access_log, "artifacts": {k: str(v) for k, v in artifacts.items()}}


def run_metric_entrypoint(*, score_artifacts: Iterable[str | Path], repo: str | Path,
                          label_loader: Callable[[], T], metric_runner: Callable[[list[dict], T], object]) -> object:
    """Open labels only after canonical score and execution/calibration seals pass."""
    m1_data.install_test_label_access_guard()
    root = Path(repo).resolve()
    expected = [root / STAGE1_SCORE_DIR / f"{m}.npz" for m in STAGE1_MACHINES]
    supplied = [Path(p).resolve() for p in score_artifacts]
    if supplied != expected:
        raise RuntimeError("metric entry point requires the exact canonical 28-machine score inventory")
    inventory = verify_complete_stage1_score_inventory(root)
    execution = verify_complete_execution_calibration_provenance(root, inventory)
    with _authorized_production_label_access():
        labels = label_loader()
    return metric_runner([inventory, execution], labels)


def main(argv: list[str] | None = None) -> int:
    """CLI for the future metric-only stage; deliberately not run in preflight."""
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate committed M1 Stage-1 scores")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    result = evaluate_committed_stage1(args.repo)
    print(json.dumps({"decision": result["decision"], "artifacts": result["artifacts"]},
                     sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover - metric-only CLI
    raise SystemExit(main())
