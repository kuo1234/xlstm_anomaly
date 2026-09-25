"""Result-blind score construction and sealing for adaptive-normality M1.

This module deliberately has no dependency on the SMD label files. Score
arrays are indexed by original timestamps and all fusion functions require
identical timestamp vectors.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

CONTROL_ARMS = ("R-native-window", "R-endpoint", "last-value", "moving-median", "ridge-var1")
FORECAST_ARM = "xLSTMAD-F"
STAGE1_SCORE_NAMES = ("last_value", "moving_median", "var1", "r_native_window", "r_endpoint",
                      "xlstmad_f", "lstm_f", "control_fusion", "forecast_control_fusion")
STAGE1_MACHINES = tuple([f"machine-1-{i}" for i in range(1, 9)] +
                        [f"machine-2-{i}" for i in range(1, 10)] +
                        [f"machine-3-{i}" for i in range(1, 12)])
STAGE1_SCORE_DIR = Path("reports/adaptive_normality_m1_smd/stage1_scores")
STAGE1_MANIFEST_PATH = Path("reports/adaptive_normality_m1_smd/stage1_score_manifest.json")


def _scores(x: np.ndarray) -> np.ndarray:
    a = np.asarray(x, dtype=np.float64)
    if not np.isfinite(a).all():
        raise ValueError("scores must be finite")
    return a


def _check_times(times: Sequence[int], n: int) -> np.ndarray:
    t = np.asarray(times)
    if t.ndim != 1 or len(t) != n:
        raise ValueError("timestamps must be a one-dimensional vector matching scores")
    if len(t) > 1 and np.any(t[1:] <= t[:-1]):
        raise ValueError("timestamps must be strictly increasing")
    return t


def reconstruction_scores(y: np.ndarray, yhat: np.ndarray, timestamps: Sequence[int]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return native W×D mean error and endpoint D mean error, both for t.

    The final position in each input window is the reconstruction aligned with
    its associated timestamp. Input shapes are [N,W,D].
    """
    actual, pred = np.asarray(y), np.asarray(yhat)
    if actual.ndim != 3 or actual.shape != pred.shape:
        raise ValueError("reconstruction arrays must have the same [N,W,D] shape")
    if actual.shape[0] == 0 or actual.shape[1] == 0 or actual.shape[2] == 0:
        raise ValueError("reconstruction arrays must be non-empty")
    t = _check_times(timestamps, actual.shape[0])
    residual2 = np.square(actual.astype(np.float64) - pred.astype(np.float64))
    return residual2.mean(axis=(1, 2)), residual2[:, -1, :].mean(axis=1), t


def forecast_score(target: np.ndarray, prediction: np.ndarray, timestamps: Sequence[int]) -> tuple[np.ndarray, np.ndarray]:
    """Point residual score for target t; caller must materialize prediction first."""
    y, p = np.asarray(target), np.asarray(prediction)
    if y.shape != p.shape or y.ndim != 2:
        raise ValueError("forecast target and prediction must share [N,D] shape")
    t = _check_times(timestamps, len(y))
    return np.square(y.astype(np.float64) - p.astype(np.float64)).mean(axis=1), t


def last_value_score(z: np.ndarray, timestamps: Sequence[int] | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Squared first difference per target timestamp, averaged over channels."""
    a = np.asarray(z)
    if a.ndim != 2 or len(a) < 2:
        raise ValueError("z must be [T,D] with T >= 2")
    values = np.square(a[1:].astype(np.float64) - a[:-1].astype(np.float64)).mean(axis=1)
    ts = np.arange(1, len(a)) if timestamps is None else np.asarray(timestamps)
    if len(ts) == len(a):
        ts = ts[1:]
    ts = _check_times(ts, len(values))
    return values, ts


def moving_median_score(z: np.ndarray, window: int, timestamps: Sequence[int] | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Squared point residual against channel-wise median of preceding W rows."""
    a = np.asarray(z)
    if a.ndim != 2 or window < 1 or len(a) <= window:
        raise ValueError("need [T,D] data with T > positive window")
    vals = np.empty(len(a) - window, dtype=np.float64)
    for j, t in enumerate(range(window, len(a))):
        vals[j] = np.square(a[t].astype(np.float64) - np.median(a[t-window:t], axis=0)).mean()
    ts = np.arange(window, len(a)) if timestamps is None else np.asarray(timestamps)
    if len(ts) == len(a):
        ts = ts[window:]
    return vals, _check_times(ts, len(vals))


def fit_ridge_var1(train: np.ndarray, lam: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Fit VAR(1) with unpenalized intercept; coefficients have [D+1,D] shape."""
    x = np.asarray(train, dtype=np.float64)
    if x.ndim != 2 or len(x) < 2 or lam != 1.0:
        raise ValueError("VAR(1) requires [T,D], T>=2, and frozen lambda=1")
    design = np.column_stack((np.ones(len(x)-1), x[:-1]))
    target = x[1:]
    penalty = np.eye(design.shape[1], dtype=np.float64) * lam
    penalty[0, 0] = 0.0
    coef = np.linalg.solve(design.T @ design + penalty, design.T @ target)
    return coef[0], coef[1:]


def ridge_var1_score(z: np.ndarray, intercept: np.ndarray, coefficients: np.ndarray,
                     timestamps: Sequence[int] | None = None) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(z, dtype=np.float64)
    b, a = np.asarray(intercept), np.asarray(coefficients)
    if x.ndim != 2 or b.shape != (x.shape[1],) or a.shape != (x.shape[1], x.shape[1]):
        raise ValueError("VAR parameters must have intercept [D], coefficients [D,D]")
    residual = x[1:] - (x[:-1] @ a + b)
    ts = np.arange(1, len(x)) if timestamps is None else np.asarray(timestamps)
    if len(ts) == len(x):
        ts = ts[1:]
    return np.square(residual).mean(axis=1), _check_times(ts, len(residual))


score_var1 = ridge_var1_score


def fit_normal_calibration(calibration_scores: np.ndarray) -> np.ndarray:
    """Freeze finite empirical normal-score reference values."""
    a = _scores(calibration_scores).reshape(-1)
    if not len(a):
        raise ValueError("normal calibration block is empty")
    return np.sort(a, kind="mergesort")


def higher_empirical_quantile(calibration_scores: np.ndarray, q: float = 0.99) -> float:
    """Frozen higher empirical quantile for normal-calibration thresholds."""
    values = _scores(calibration_scores).reshape(-1)
    if not len(values) or not 0.0 <= float(q) <= 1.0:
        raise ValueError("higher empirical quantile requires data and q in [0,1]")
    return float(np.quantile(values, float(q), method="higher"))


def normal_tail_severity(scores: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Empirical upper-tail severity: -log10((#cal >= score + 1)/(n + 1))."""
    x, ref = _scores(scores), _scores(reference).reshape(-1)
    if not len(ref):
        raise ValueError("normal calibration reference is empty")
    # searchsorted on the sorted frozen reference avoids any fitted test state.
    n_ge = len(ref) - np.searchsorted(ref, x, side="left")
    return -np.log10((n_ge + 1.0) / (len(ref) + 1.0))


def fit_tail_rank(calibration_scores: np.ndarray) -> np.ndarray:
    return fit_normal_calibration(calibration_scores)


def tail_rank(scores: np.ndarray, fitted_reference: np.ndarray) -> np.ndarray:
    return normal_tail_severity(scores, fitted_reference)


def _aligned(series: Mapping[str, tuple[np.ndarray, Sequence[int]]], names: Sequence[str]) -> tuple[dict[str, np.ndarray], np.ndarray]:
    if tuple(names) != tuple(series.keys()):
        raise ValueError("fusion arms/order do not match the fixed declared set")
    aligned: dict[str, np.ndarray] = {}
    canonical = None
    for name in names:
        s, ts = series[name]
        v = _scores(s).reshape(-1)
        t = _check_times(ts, len(v))
        if canonical is None:
            canonical = t
        elif not np.array_equal(canonical, t):
            raise ValueError("all fusion arms must score exactly the same timestamps")
        aligned[name] = v
    assert canonical is not None
    return aligned, canonical


def fixed_control_fusion(series: Mapping[str, tuple[np.ndarray, Sequence[int]]]) -> tuple[np.ndarray, np.ndarray]:
    """Operational per-time maximum severity across the five fixed controls."""
    values, times = _aligned(series, CONTROL_ARMS)
    return np.maximum.reduce([values[n] for n in CONTROL_ARMS]), times


def fixed_forecast_control_fusion(forecast: tuple[np.ndarray, Sequence[int]],
                                  controls: Mapping[str, tuple[np.ndarray, Sequence[int]]]) -> tuple[np.ndarray, np.ndarray]:
    """Fixed max fusion of xLSTMAD-F and the five control severities."""
    all_series = {FORECAST_ARM: forecast, **controls}
    names = (FORECAST_ARM, *CONTROL_ARMS)
    values, times = _aligned(all_series, names)
    return np.maximum.reduce([values[n] for n in names]), times


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def seal_score_artifact(path: str | Path, scores: np.ndarray, timestamps: Sequence[int], *, arm: str, machine: str) -> Path:
    """Atomically write a numeric NPZ plus immutable JSON seal manifest."""
    target = Path(path)
    if target.suffix != ".npz":
        raise ValueError("score artifact path must end in .npz")
    values = _scores(scores).reshape(-1)
    t = _check_times(timestamps, len(values))
    target.parent.mkdir(parents=True, exist_ok=True)
    manifest = target.with_suffix(target.suffix + ".manifest.json")
    if target.exists() or manifest.exists():
        raise FileExistsError("sealed score artifacts are immutable")
    with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".npz", delete=False) as f:
        tmp = Path(f.name)
    try:
        np.savez_compressed(tmp, scores=values.astype(np.float64), timestamps=t)
        # Hard-link publishes only if absent; a racing writer cannot replace
        # the immutable bytes after the initial precheck.
        os.link(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()
    doc = {
        "schema": "adaptive-normality-m1-score-seal-v1", "arm": arm, "machine": machine,
        "count": int(len(values)), "timestamp_sha256": hashlib.sha256(np.asarray(t).tobytes()).hexdigest(),
        "scores_sha256": hashlib.sha256(values.astype(np.float64).tobytes()).hexdigest(),
        "artifact": target.name, "artifact_sha256": _sha256(target),
    }
    fd, temp_name = tempfile.mkstemp(dir=target.parent, prefix=".seal-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(doc, f, sort_keys=True, indent=2); f.write("\n"); f.flush(); os.fsync(f.fileno())
        # Hard-link gives create-if-absent semantics so a concurrent seal cannot overwrite.
        os.link(temp_name, manifest)
    except FileExistsError:
        # Leave any artifact already published by us or another writer alone.
        # An orphan without its manifest is fail-closed at the metric gate.
        raise FileExistsError("sealed score artifacts are immutable")
    finally:
        Path(temp_name).unlink(missing_ok=True)
    return manifest


def seal_score_artifacts(artifacts: Sequence[dict]) -> list[Path]:
    """Seal a declared set of independent artifacts, refusing partial overwrite."""
    paths = [Path(item["path"]) for item in artifacts]
    if len(set(paths)) != len(paths) or any(p.exists() or p.with_suffix(p.suffix + ".manifest.json").exists() for p in paths):
        raise FileExistsError("score artifact batch contains duplicate or already sealed paths")
    return [seal_score_artifact(item["path"], item["scores"], item["timestamps"], arm=item["arm"], machine=item["machine"])
            for item in artifacts]


def verify_score_seal(manifest_path: str | Path) -> dict:
    mp = Path(manifest_path)
    doc = json.loads(mp.read_text(encoding="utf-8"))
    if doc.get("schema") != "adaptive-normality-m1-score-seal-v1":
        raise ValueError("unknown score seal schema")
    artifact = mp.parent / doc["artifact"]
    if _sha256(artifact) != doc["artifact_sha256"]:
        raise ValueError("score artifact hash does not match seal")
    with np.load(artifact, allow_pickle=False) as z:
        scores = _scores(z["scores"]); times = _check_times(z["timestamps"], len(scores))
    if len(scores) != doc["count"] or hashlib.sha256(times.tobytes()).hexdigest() != doc["timestamp_sha256"] or hashlib.sha256(scores.astype(np.float64).tobytes()).hexdigest() != doc["scores_sha256"]:
        raise ValueError("sealed score content does not match manifest")
    return doc


def git_committed(path: str | Path, repo: str | Path) -> bool:
    """True only if the exact working-tree file matches its HEAD blob."""
    root, p = Path(repo).resolve(), Path(path).resolve()
    rel = p.relative_to(root).as_posix()
    try:
        head = subprocess.check_output(["git", "-C", str(root), "show", f"HEAD:{rel}"], stderr=subprocess.DEVNULL)
        return head == p.read_bytes()
    except (subprocess.CalledProcessError, OSError, ValueError):
        return False


def seal_stage1_machine_scores(repo: str | Path, machine_scores: Mapping[str, Mapping[str, object]]) -> Path:
    """Write the canonical 28 machine score files and their root inventory seal.

    Each machine record has ``timestamps`` and exactly the nine score arrays
    named by ``STAGE1_SCORE_NAMES``. The top-level manifest is published last,
    so an interrupted write cannot pass the metric gate.
    """
    root = Path(repo).resolve()
    if set(machine_scores) != set(STAGE1_MACHINES):
        raise ValueError("Stage-1 score inventory must contain exactly the frozen 28 machines")
    outdir = root / STAGE1_SCORE_DIR
    manifest = root / STAGE1_MANIFEST_PATH
    paths = [outdir / f"{m}.npz" for m in STAGE1_MACHINES]
    if manifest.exists() or any(p.exists() for p in paths):
        raise FileExistsError("Stage-1 score inventory is immutable")
    entries = []
    # Validate all arrays and common indexing before writing any artifact.
    packed = {}
    for machine in STAGE1_MACHINES:
        record = machine_scores[machine]
        if set(record) != {"timestamps", *STAGE1_SCORE_NAMES}:
            raise ValueError(f"{machine}: score names must exactly match the frozen nine-arm set")
        times = np.asarray(record["timestamps"])
        timestamps = _check_times(times, len(times))
        arrays = {name: _scores(np.asarray(record[name])).reshape(-1) for name in STAGE1_SCORE_NAMES}
        if any(len(values) != len(times) for values in arrays.values()):
            raise ValueError(f"{machine}: score arrays do not share timestamp length")
        packed[machine] = {"timestamps": timestamps, **arrays}
    outdir.mkdir(parents=True, exist_ok=True)
    for machine in STAGE1_MACHINES:
        target = outdir / f"{machine}.npz"
        with tempfile.NamedTemporaryFile(dir=outdir, suffix=".npz", delete=False) as f:
            tmp = Path(f.name)
        try:
            np.savez_compressed(tmp, **packed[machine])
            os.link(tmp, target)
        finally:
            tmp.unlink(missing_ok=True)
        entries.append({"machine": machine, "artifact": target.relative_to(root).as_posix(),
                        "sha256": _sha256(target), "count": len(packed[machine]["timestamps"]),
                        "timestamp_sha256": hashlib.sha256(packed[machine]["timestamps"].tobytes()).hexdigest(),
                        "arrays": list(STAGE1_SCORE_NAMES)})
    doc = {"schema": "adaptive-normality-m1-stage1-score-inventory-v1",
           "machines": entries, "score_names": list(STAGE1_SCORE_NAMES)}
    fd, temp_name = tempfile.mkstemp(dir=manifest.parent, prefix=".stage1-seal-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(doc, f, sort_keys=True, indent=2); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.link(temp_name, manifest)
    finally:
        Path(temp_name).unlink(missing_ok=True)
    return manifest
