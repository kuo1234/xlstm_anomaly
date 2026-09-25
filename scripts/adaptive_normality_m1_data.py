"""Isolated, label-free data and timestamp contracts for M1 SMD.

This module intentionally has no label API. It opens only pinned ``train`` and
``test`` observation files and verifies their byte seals before parsing.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import urllib.request
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "research" / "adaptive_normality_m1_smd" / "smd_28_manifest.json"
MANIFEST = json.loads(MANIFEST_PATH.read_text())
MACHINES = tuple(MANIFEST["machines"])
D = 38
W = 256
CLIP = 50.0
MAD_FACTOR = 1.4826
CENTRAL_RANGE_DENOMINATOR = 3.2897072539
SCALE_FLOOR_FRACTION = 0.05


class M1DataError(RuntimeError):
    """An M1 data provenance or index contract was violated."""


_LABEL_GUARD_INSTALLED = False
_LABEL_OPEN_ATTEMPTS = 0
_SEALED_METRIC_LABEL_ACCESS: ContextVar[bool] = ContextVar("m1_sealed_metric_label_access", default=False)


def _is_test_label_path(value: object) -> bool:
    """Recognize local and upstream SMD test-label path spellings."""
    try:
        name = os.fsdecode(os.fspath(value)).replace("\\", "/").lower()
    except (TypeError, ValueError):
        return False
    return ("test_label" in name or "test-label" in name or
            ("/labels/" in name and ("/test/" in name or name.endswith("test.txt"))))


def install_test_label_access_guard() -> None:
    """Fail closed if this process tries to open an SMD test-label path.

    Python's audit hook observes normal file opens including NumPy loaders.
    M1 score/training/preflight code never calls a label API; this process-wide
    backstop protects against accidental future imports or path construction.
    """
    global _LABEL_GUARD_INSTALLED
    if _LABEL_GUARD_INSTALLED:
        return

    def reject(event: str, args: tuple[object, ...]) -> None:
        global _LABEL_OPEN_ATTEMPTS
        if (event == "open" and args and _is_test_label_path(args[0]) and
                not _SEALED_METRIC_LABEL_ACCESS.get()):
            _LABEL_OPEN_ATTEMPTS += 1
            raise M1DataError("test anomaly-label access is forbidden before sealed metrics")

    sys.addaudithook(reject)
    _LABEL_GUARD_INSTALLED = True


def test_label_open_attempt_count() -> int:
    return _LABEL_OPEN_ATTEMPTS


@contextmanager
def sealed_metric_label_access():
    """Permit label reads only around a caller already past the score-seal gate."""
    token = _SEALED_METRIC_LABEL_ACCESS.set(True)
    try:
        yield
    finally:
        _SEALED_METRIC_LABEL_ACCESS.reset(token)


def data_root() -> Path:
    """Directory containing ``{machine}_{train|test}.txt`` pinned files."""
    return Path(os.environ.get("M1_SMD_DATA_ROOT", ROOT / "data" / "external_real" / "m1_smd")).expanduser()


def raw_path(machine: str, split: str, root: Path | None = None) -> Path:
    if machine not in MACHINES or split not in ("train", "test"):
        raise M1DataError("only registered machines and train/test observations are available")
    return (root or data_root()) / f"{machine}_{split}.txt"


def source_url(machine: str, split: str) -> str:
    """Commit-addressed upstream URL for an observation split only."""
    raw_path(machine, split, Path("."))  # centralized allow-list validation
    return ("https://raw.githubusercontent.com/NetManAIOps/OmniAnomaly/"
            f"{MANIFEST['upstream_commit']}/ServerMachineDataset/{split}/{machine}.txt")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_observation(machine: str, split: str, root: Path | None = None) -> dict[str, object]:
    path = raw_path(machine, split, root)
    expected = MANIFEST["machines"][machine][split]
    if not path.is_file():
        return {"path": str(path), "exists": False, "match": False}
    size = path.stat().st_size
    digest = sha256_file(path)
    return {"path": str(path), "exists": True, "bytes": size, "sha256": digest,
            "match": size == expected["bytes"] and digest == expected["sha256"]}


def load_observations(machine: str, split: str, root: Path | None = None) -> np.ndarray:
    """Load a verified finite [N,38] train or test observation matrix."""
    install_test_label_access_guard()
    path = raw_path(machine, split, root)
    check = verify_observation(machine, split, root)
    if not check["match"]:
        raise M1DataError(f"pinned observation hash/size mismatch: {machine}/{split}")
    matrix = np.loadtxt(path, delimiter=",", dtype=np.float64, ndmin=2)
    expected_rows = int(MANIFEST["machines"][machine][f"{split}_rows"])
    if matrix.shape != (expected_rows, D) or not np.isfinite(matrix).all():
        raise M1DataError(f"invalid observation schema or non-finite values: {machine}/{split}")
    return matrix


def acquire_observations(root: Path | None = None) -> dict[str, object]:
    """Atomically acquire and verify all pinned train/test observations.

    The acquisition keyspace is exactly 28 machines × {train,test}; test-label
    paths and URLs are not generated or requested. A differing installed file
    is preserved and reported as blocked.
    """
    dest = root or data_root()
    dest.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    for machine in MACHINES:
        for split in ("train", "test"):
            target = raw_path(machine, split, dest)
            expected = MANIFEST["machines"][machine][split]
            row: dict[str, object] = {"machine": machine, "split": split,
                                      "url": source_url(machine, split),
                                      "expected_bytes": expected["bytes"],
                                      "expected_sha256": expected["sha256"]}
            if target.exists():
                check = verify_observation(machine, split, dest)
                row["installed"] = check
                row["status"] = "already_present_verified" if check["match"] else "DATA_PROVENANCE_BLOCKED_EXISTING_MISMATCH"
                results.append(row)
                continue

            temporary: Path | None = None
            try:
                with urllib.request.urlopen(source_url(machine, split), timeout=120) as response:
                    with tempfile.NamedTemporaryFile(prefix=f".{machine}_{split}_", suffix=".partial",
                                                     dir=dest, delete=False) as handle:
                        temporary = Path(handle.name)
                        shutil.copyfileobj(response, handle)
                size = temporary.stat().st_size
                digest = sha256_file(temporary)
                row["download_bytes"] = size
                row["download_sha256"] = digest
                if size != expected["bytes"] or digest != expected["sha256"]:
                    row["status"] = "DATA_PROVENANCE_BLOCKED_DOWNLOAD_MISMATCH"
                else:
                    # Recheck just before install to avoid replacing a file created
                    # by another process while the network request was in flight.
                    if target.exists():
                        check = verify_observation(machine, split, dest)
                        row["installed"] = check
                        row["status"] = ("already_present_verified" if check["match"] else
                                         "DATA_PROVENANCE_BLOCKED_EXISTING_MISMATCH")
                    else:
                        os.replace(temporary, target)
                        temporary = None
                        row["installed"] = verify_observation(machine, split, dest)
                        row["status"] = "installed_verified" if row["installed"]["match"] else "DATA_PROVENANCE_BLOCKED_POSTINSTALL"
            except Exception as error:
                row["status"] = "DATA_ACQUISITION_BLOCKED"
                row["error"] = f"{type(error).__name__}: {error}"
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            results.append(row)
    blocked = [f"{row['machine']}/{row['split']}" for row in results
               if str(row["status"]).startswith(("DATA_PROVENANCE_BLOCKED", "DATA_ACQUISITION_BLOCKED"))]
    return {"status": "DATA_PROVENANCE_BLOCKED" if blocked else "ACQUIRED_AND_VERIFIED",
            "expected_count": 56,
            "verified_count": sum(row.get("status") in {"installed_verified", "already_present_verified"}
                                  for row in results),
            "blocked": blocked, "files": results}


def load_train(machine: str, root: Path | None = None) -> np.ndarray:
    return load_observations(machine, "train", root)


def load_test(machine: str, root: Path | None = None) -> np.ndarray:
    return load_observations(machine, "test", root)


def verify_observation_hashes(root: Path | None = None) -> dict[str, object]:
    """Verify only the 56 train/test observation files; never probes label paths."""
    files = {f"{machine}/{split}": verify_observation(machine, split, root)
             for machine in MACHINES for split in ("train", "test")}
    return {"files": files, "verified_count": sum(bool(row["match"]) for row in files.values()),
            "expected_count": 56, "all_match": all(row["match"] for row in files.values())}


@dataclass(frozen=True)
class Blocks:
    """Half-open train-relative fit, validation, and calibration partitions."""
    fit: tuple[int, int]
    validation: tuple[int, int]
    calibration: tuple[int, int]
    train_n: int


def split_boundaries(train_n: int) -> Blocks:
    n = int(train_n)
    if n <= 0:
        raise M1DataError("train stream must be nonempty")
    a, b = (7 * n) // 10, (85 * n) // 100
    return Blocks((0, a), (a, b), (b, n), n)


def train_blocks(n: int) -> dict[str, tuple[int, int]]:
    b = split_boundaries(n)
    return {"fit": b.fit, "validation": b.validation, "calibration": b.calibration}


@dataclass(frozen=True)
class RobustTransform:
    center: np.ndarray
    scale: np.ndarray
    raw_robust_scale: np.ndarray
    scale_floor: float
    fit_rows: tuple[int, int]


def fit_robust_transform(train: np.ndarray) -> RobustTransform:
    """Fit the frozen M1 robust transform on the first 70% of train only."""
    install_test_label_access_guard()
    x = np.asarray(train, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != D or not np.isfinite(x).all():
        raise M1DataError("transform requires a finite [N,38] train matrix")
    end = split_boundaries(len(x)).fit[1]
    return _fit_robust_transform(x, end)


def _fit_robust_transform(x: np.ndarray, end: int) -> RobustTransform:
    if end <= 0 or end > len(x):
        raise M1DataError("fit_end must define a nonempty prefix of the train matrix")
    fit = x[:end]
    center = np.median(fit, axis=0)
    mad = MAD_FACTOR * np.median(np.abs(fit - center), axis=0)
    q05, q95 = np.quantile(fit, [0.05, 0.95], axis=0, method="linear")
    central = (q95 - q05) / CENTRAL_RANGE_DENOMINATOR
    robust = np.maximum(mad, central)
    positive = robust[robust > 0]
    if positive.size == 0:
        raise M1DataError("no positive robust channel scale; refusing zero-scale fit")
    floor = SCALE_FLOOR_FRACTION * float(np.median(positive))
    scale = np.maximum(robust, floor)
    return RobustTransform(center, scale, robust, floor, (0, end))


class RobustScaler:
    """Small stateful facade used by the M1 runner; fit statistics are train-only."""
    def __init__(self) -> None:
        self.statistics: RobustTransform | None = None

    def fit(self, train: np.ndarray, fit_end: int) -> "RobustScaler":
        install_test_label_access_guard()
        x = np.asarray(train, dtype=np.float64)
        if x.ndim != 2 or x.shape[1] != D or not np.isfinite(x).all():
            raise M1DataError("scaler fit requires finite [N,38] train observations")
        self.statistics = _fit_robust_transform(x, int(fit_end))
        return self

    def transform(self, observations: np.ndarray) -> np.ndarray:
        if self.statistics is None:
            raise M1DataError("scaler must be fit before transform")
        return apply_robust_transform(observations, self.statistics)


def apply_robust_transform(observations: np.ndarray, transform: RobustTransform) -> np.ndarray:
    install_test_label_access_guard()
    x = np.asarray(observations, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != D or not np.isfinite(x).all():
        raise M1DataError("transform input must be finite [N,38]")
    if transform.center.shape != (D,) or transform.scale.shape != (D,) or np.any(transform.scale <= 0):
        raise M1DataError("invalid frozen transform")
    z = np.clip((x - transform.center) / transform.scale, -CLIP, CLIP).astype(np.float32)
    if not np.isfinite(z).all():
        raise M1DataError("transformed observations are non-finite")
    return z


def _check_interval(start: int, stop: int, n: int) -> tuple[int, int]:
    a, b = int(start), int(stop)
    if a < 0 or b > int(n) or b <= a:
        raise M1DataError(f"invalid half-open block [{a},{b}) for stream length {n}")
    return a, b


def forecast_targets(start: int, stop: int, n: int, window: int = W) -> np.ndarray:
    """Targets whose [t-W,t) input and target t stay within [start,stop)."""
    a, b = _check_interval(start, stop, n)
    if window <= 0:
        raise M1DataError("window must be positive")
    first = a + int(window)
    return np.arange(first, b, dtype=np.int64)


def forecast_target_indices(bounds: tuple[int, int], first_eligible: int | None = None,
                            window: int = W) -> np.ndarray:
    """Indices t with [t-W,t) wholly in bounds; optional lower-bound warm-up."""
    a, b = int(bounds[0]), int(bounds[1])
    lower = a + int(window)
    if first_eligible is not None:
        lower = max(lower, int(first_eligible))
    if a < 0 or b <= a or window <= 0:
        raise M1DataError("invalid forecast block or window")
    return np.arange(lower, b, dtype=np.int64)


def forecast_example(stream: np.ndarray, target: int, start: int = 0, stop: int | None = None,
                     window: int = W) -> tuple[np.ndarray, int]:
    """Materialize input indices [t-W,t) without touching target observation."""
    x = np.asarray(stream)
    end = len(x) if stop is None else int(stop)
    a, b = _check_interval(start, end, len(x))
    t = int(target)
    if t - int(window) < a or t >= b:
        raise M1DataError("forecast window/target crosses or falls outside its block")
    return x[t - int(window):t], t


def forecast_sample(stream: np.ndarray, t: int, bounds: tuple[int, int], window: int = W) -> tuple[np.ndarray, np.ndarray]:
    """Return a copied input window and target value; window excludes position t."""
    x = np.asarray(stream)
    a, b = int(bounds[0]), int(bounds[1])
    if x.ndim < 1 or int(t) - window < a or int(t) >= b:
        raise M1DataError("forecast sample crosses or falls outside its block")
    # Materialize independently before returning the target, preserving the strict
    # [t-W,t) input contract for callers that immediately run model inference.
    inputs = np.array(x[int(t) - window:int(t)], copy=True)
    target = np.array(x[int(t)], copy=True)
    return inputs, target


def reconstruction_timestamps(start: int, stop: int, n: int, window: int = W) -> np.ndarray:
    """Right endpoints t for trailing windows [t-W+1,t+1) inside a block."""
    a, b = _check_interval(start, stop, n)
    if window <= 0:
        raise M1DataError("window must be positive")
    return np.arange(a + int(window) - 1, b, dtype=np.int64)


def reconstruction_window(stream: np.ndarray, timestamp: int,
                          start: int | tuple[int, int] = 0,
                          stop: int | None = None, window: int = W) -> np.ndarray:
    x = np.asarray(stream)
    if isinstance(start, tuple):
        if stop is not None:
            raise M1DataError("pass either a bounds tuple or separate start/stop values")
        start, stop = start
    end = len(x) if stop is None else int(stop)
    a, b = _check_interval(start, end, len(x))
    t = int(timestamp)
    lo = t - int(window) + 1
    if lo < a or t >= b:
        raise M1DataError("reconstruction window crosses or falls outside its block")
    return x[lo:t + 1]


def reconstruction_window_for_bounds(stream: np.ndarray, t: int,
                                     bounds: tuple[int, int], window: int = W) -> np.ndarray:
    return reconstruction_window(stream, t, bounds, window=window)


class ForecastWindowDataset:
    """Lazy block-local forecast samples; never allocates a windows tensor."""
    def __init__(self, stream: np.ndarray, bounds: tuple[int, int], window: int = W,
                 first_eligible: int | None = None) -> None:
        self.stream = np.asarray(stream)
        self.bounds = (int(bounds[0]), int(bounds[1]))
        self.window = int(window)
        self.targets = forecast_target_indices(self.bounds, first_eligible, self.window)
        # Validate once, then retain only source + endpoint indices. Each window
        # is sliced/copied on demand by __getitem__.
        _check_interval(*self.bounds, len(self.stream))

    def __len__(self) -> int:
        return len(self.targets)

    def __getitem__(self, index: int) -> tuple[np.ndarray, np.ndarray]:
        t = int(self.targets[index])
        return forecast_sample(self.stream, t, self.bounds, self.window)


class ReconstructionWindowDataset:
    """Lazy trailing-window reconstruction inputs, indexed by endpoint t."""
    def __init__(self, stream: np.ndarray, bounds: tuple[int, int], window: int = W) -> None:
        self.stream = np.asarray(stream)
        self.bounds = (int(bounds[0]), int(bounds[1]))
        self.window = int(window)
        a, b = _check_interval(*self.bounds, len(self.stream))
        if self.window <= 0:
            raise M1DataError("window must be positive")
        self.timestamps = reconstruction_timestamps(a, b, len(self.stream), self.window)

    def __len__(self) -> int:
        return len(self.timestamps)

    def __getitem__(self, index: int) -> tuple[np.ndarray, int]:
        t = int(self.timestamps[index])
        sample = reconstruction_window(self.stream, t, self.bounds, window=self.window)
        return np.array(sample, copy=True), t


def test_forecast_targets(test_n: int, window: int = W) -> np.ndarray:
    """Test decision indices; for frozen W=256 this begins exactly at t=256."""
    return forecast_targets(0, int(test_n), int(test_n), window)


def score_timestamp_contract(train_n: int, test_n: int) -> Mapping[str, np.ndarray]:
    """Return forecast/reconstruction eligible timestamps per frozen block."""
    blocks = split_boundaries(train_n)
    return {
        "fit_forecast": forecast_targets(*blocks.fit, blocks.train_n),
        "validation_forecast": forecast_targets(*blocks.validation, blocks.train_n),
        "calibration_forecast": forecast_targets(*blocks.calibration, blocks.train_n),
        "test_forecast": test_forecast_targets(test_n),
    }
