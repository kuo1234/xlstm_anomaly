"""R0 SMD data layer: pinned acquisition, verification, parsing and index contracts.

Torch-free and sklearn-free.  Every constant comes from ``configs/real_data_r0.json``.

Access boundary
---------------
* Observations are read through :func:`load_observations`; that API has no
  label argument and never opens a label file.
* Test labels are reachable only through :func:`load_test_labels`, which
  requires an explicit, allow-listed ``purpose`` and records every access.
* Nothing in this module computes a detector or probe metric.

CLI
---
``python3 scripts/real_data_r0_data.py acquire [--staged DIR] --report FILE``
    Download/verify the nine pinned raw files into the git-ignored R0 data
    directory and write ``local_manifest.json`` there.  Fails closed on any
    hash or byte-count mismatch and never overwrites a differing file.
``python3 scripts/real_data_r0_data.py verify``
    Re-hash the installed files against the frozen expectations.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import os
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "real_data_r0.json"
CONFIG: dict[str, Any] = json.loads(CONFIG_PATH.read_text())
DATASET = CONFIG["dataset"]
MACHINES: tuple[str, ...] = tuple(DATASET["machines"])
SPLITS: tuple[str, ...] = tuple(DATASET["splits"])
D = int(DATASET["D"])
W = int(CONFIG["windowing"]["W"])
ROLLING_WIDTHS = tuple(int(v) for v in CONFIG["windowing"]["rolling_widths"])
FIRST_DECISION = W - 1
FIRST_FINITE = FIRST_DECISION + max(ROLLING_WIDTHS) - 1
RECEPTIVE_FIELD = FIRST_FINITE + 1
EMBARGO = int(CONFIG["probe"]["embargo"])
FIT_NUMERATOR, FIT_DENOMINATOR = 4, 5  # exact integer form of floor(0.8 * n)
LABEL_PURPOSES = frozenset({"preflight_counts", "probe_fit_selection", "probe_final_evaluation", "detector_sanity"})
_LABEL_ACCESS_LOG: list[dict[str, str]] = []

if FIRST_DECISION != CONFIG["windowing"]["first_decision_index"] or FIRST_FINITE != CONFIG["windowing"]["first_finite_feature_index"]:
    raise RuntimeError("configuration window constants are inconsistent")
if EMBARGO < RECEPTIVE_FIELD:
    raise RuntimeError("embargo shorter than the feature receptive field")


class ProtocolViolation(RuntimeError):
    """Raised whenever a frozen R0 contract would be violated."""


# --------------------------------------------------------------------------- paths


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def data_root() -> Path:
    override = os.environ.get(DATASET["raw_dir_env"])
    return Path(override).expanduser() if override else ROOT / DATASET["raw_dir_repo_relative"]


def _check_key(machine: str, split: str) -> None:
    if machine not in MACHINES:
        raise ProtocolViolation(f"unregistered machine {machine!r}")
    if split not in SPLITS:
        raise ProtocolViolation(f"unregistered split {split!r}")


def raw_path(machine: str, split: str, root: Path | None = None) -> Path:
    _check_key(machine, split)
    return (root or data_root()) / DATASET["file_name_template"].format(machine=machine, split=split)


def source_url(machine: str, split: str) -> str:
    _check_key(machine, split)
    return DATASET["url_template"].format(commit=DATASET["upstream_commit"], split=split, machine=machine)


def expected(machine: str, split: str) -> dict[str, Any]:
    _check_key(machine, split)
    return dict(DATASET["expected"][machine][split])


def verify_file(path: Path, machine: str, split: str) -> dict[str, Any]:
    exp = expected(machine, split)
    if not path.is_file():
        return {"path_exists": False, "match": False}
    size = path.stat().st_size
    digest = sha256_file(path)
    return {"path_exists": True, "bytes": size, "sha256": digest,
            "match": bool(size == exp["bytes"] and digest == exp["sha256"])}


def verify_all(root: Path | None = None) -> dict[str, Any]:
    rows = {}
    for machine in MACHINES:
        for split in SPLITS:
            rows[f"{machine}/{split}"] = verify_file(raw_path(machine, split, root), machine, split)
    return {"files": rows, "all_match": all(row["match"] for row in rows.values())}


# --------------------------------------------------------------------------- acquisition


def _utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _download(url: str, target: Path) -> None:
    with urllib.request.urlopen(url, timeout=120) as response, open(target, "wb") as handle:  # noqa: S310 (pinned https URL)
        shutil.copyfileobj(response, handle)


def acquire(staged: Path | None, dest: Path | None = None) -> dict[str, Any]:
    """Install the nine pinned raw files; fail closed on any provenance mismatch.

    machine-1-8 is always reacquired from the pinned public URL.  For
    machine-2-1 and machine-1-4 a staged copy of the feasibility-worktree bytes
    is the install source when it verifies; the pinned public URL is downloaded
    independently for every file as a reproducibility cross-check.
    """
    dest = dest or data_root()
    dest.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {"dest_repo_relative": DATASET["raw_dir_repo_relative"], "started_utc": _utc(), "files": [], "blocked": []}
    legacy_dir = ROOT / "data" / "phase_a" / "smd_raw"
    with tempfile.TemporaryDirectory(prefix="r0_smd_") as tmp:
        for machine in MACHINES:
            for split in SPLITS:
                exp = expected(machine, split)
                url = source_url(machine, split)
                name = DATASET["file_name_template"].format(machine=machine, split=split)
                public = Path(tmp) / f"public_{name}"
                row: dict[str, Any] = {"machine": machine, "split": split, "source_url": url,
                                       "upstream_commit": DATASET["upstream_commit"], "expected_sha256": exp["sha256"],
                                       "expected_bytes": exp["bytes"],
                                       "hash_authority": DATASET["expected"][machine]["hash_authority"]}
                try:
                    _download(url, public)
                    row["public_download"] = verify_file(public, machine, split) | {"utc": _utc()}
                except Exception as error:  # network failure is recorded, never masked
                    row["public_download"] = {"error": f"{type(error).__name__}: {error}", "match": False}
                staged_file = staged / name if staged else None
                if staged_file is not None and staged_file.is_file():
                    row["staged_feasibility_copy"] = verify_file(staged_file, machine, split)
                legacy = legacy_dir / name
                if legacy.is_file():
                    row["legacy_phase_a_copy"] = verify_file(legacy, machine, split)
                if machine == "machine-1-8":
                    source, route = public, "public_pinned_reacquisition"
                elif row.get("staged_feasibility_copy", {}).get("match"):
                    source, route = staged_file, "feasibility_worktree_copy"
                else:
                    source, route = public, "public_pinned_reacquisition"
                source_check = verify_file(source, machine, split) if source is not None else {"match": False}
                row["install_route"] = route
                target = dest / name
                if not source_check["match"]:
                    row["status"] = "DATA_PROVENANCE_BLOCKED"
                    report["blocked"].append(f"{machine}/{split}")
                elif target.exists():
                    existing = verify_file(target, machine, split)
                    row["status"] = "already_present_verified" if existing["match"] else "DATA_PROVENANCE_BLOCKED"
                    if not existing["match"]:
                        report["blocked"].append(f"{machine}/{split} (existing differing file left untouched)")
                else:
                    partial = target.with_suffix(target.suffix + ".partial")
                    shutil.copyfile(source, partial)
                    if not verify_file(partial, machine, split)["match"]:
                        partial.unlink()
                        row["status"] = "DATA_PROVENANCE_BLOCKED"
                        report["blocked"].append(f"{machine}/{split} (copy verification)")
                    else:
                        os.replace(partial, target)
                        row["status"] = "installed_verified"
                installed = verify_file(target, machine, split)
                row.update({"local_path": str(target), "bytes": installed.get("bytes"), "sha256": installed.get("sha256"),
                            "installed_match": installed["match"], "timestamp_utc": _utc()})
                report["files"].append(row)
    report["finished_utc"] = _utc()
    report["status"] = "DATA_PROVENANCE_BLOCKED" if report["blocked"] else "ACQUIRED_AND_VERIFIED"
    manifest = {
        "stage": "R0",
        "note": "Git-ignored local manifest; contains host paths by design and is never committed.",
        "upstream_repository": DATASET["upstream_repository"],
        "upstream_commit": DATASET["upstream_commit"],
        "status": report["status"],
        "files": [{key: row.get(key) for key in ("machine", "split", "source_url", "upstream_commit", "bytes", "sha256",
                                                   "local_path", "install_route", "status", "timestamp_utc")} for row in report["files"]],
    }
    (dest / "local_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return report


# --------------------------------------------------------------------------- parsing


def _require_verified(machine: str, split: str) -> Path:
    path = raw_path(machine, split)
    check = verify_file(path, machine, split)
    if not check["match"]:
        raise ProtocolViolation(f"raw file failed provenance verification: {machine}/{split}")
    return path


def load_observations(machine: str, split: str) -> np.ndarray:
    """Float64 [N, 38] observations of the original train or test split (no labels)."""
    if split not in ("train", "test"):
        raise ProtocolViolation("observations are only the original train or test split")
    matrix = np.loadtxt(_require_verified(machine, split), delimiter=",", dtype=np.float64, ndmin=2)
    expected_rows = DATASET["expected"][machine][f"{split}_N"]
    if matrix.shape != (expected_rows, D):
        raise ProtocolViolation(f"{machine}/{split} shape {matrix.shape} != {(expected_rows, D)}")
    if not np.isfinite(matrix).all():
        raise ProtocolViolation(f"{machine}/{split} contains non-finite observations")
    return matrix


def load_test_labels(machine: str, *, purpose: str) -> np.ndarray:
    """Point labels of the original test split; access is purpose-gated and logged."""
    if purpose not in LABEL_PURPOSES:
        raise ProtocolViolation(f"label access purpose {purpose!r} is not allow-listed")
    labels = np.loadtxt(_require_verified(machine, "test_label"), dtype=np.float64, ndmin=1)
    if labels.ndim != 1 or len(labels) != DATASET["expected"][machine]["test_N"]:
        raise ProtocolViolation(f"{machine} label length does not match the test split")
    if not np.isin(labels, (0.0, 1.0)).all():
        raise ProtocolViolation(f"{machine} labels are not binary")
    _LABEL_ACCESS_LOG.append({"machine": machine, "purpose": purpose, "utc": _utc()})
    return labels.astype(np.uint8)


def label_access_log() -> list[dict[str, str]]:
    return [dict(row) for row in _LABEL_ACCESS_LOG]


# --------------------------------------------------------------------------- splits and scaler


def fit_end(train_n: int) -> int:
    value = (int(train_n) * FIT_NUMERATOR) // FIT_DENOMINATOR
    if value != math.floor(CONFIG["split"]["fit_fraction"] * int(train_n)):
        raise ProtocolViolation("integer and floating fit boundaries disagree")
    return value


def fit_scaler(train_observations: np.ndarray) -> dict[str, Any]:
    """Population mean/std over the fit interval only; exact zero std becomes 1."""
    x = np.asarray(train_observations, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != D:
        raise ProtocolViolation("scaler input must be the [N, 38] original train split")
    end = fit_end(len(x))
    fit = x[:end]
    mean = fit.mean(axis=0)
    std = fit.std(axis=0)
    zero = std == 0.0
    scale = np.where(zero, 1.0, std)
    return {"mean": mean, "scale": scale, "zero_std_channels": [int(i) for i in np.flatnonzero(zero)],
            "fit_rows": [0, int(end)], "train_N": int(len(x))}


def apply_scaler(observations: np.ndarray, scaler: dict[str, Any]) -> np.ndarray:
    x = np.asarray(observations, dtype=np.float64)
    mean = np.asarray(scaler["mean"], dtype=np.float64)
    scale = np.asarray(scaler["scale"], dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != D or mean.shape != (D,) or scale.shape != (D,) or np.any(scale <= 0):
        raise ProtocolViolation("invalid D=38 scaler application")
    result = ((x - mean) / scale).astype(np.float32)
    if not np.isfinite(result).all():
        raise ProtocolViolation("scaled observations are non-finite")
    return result


# --------------------------------------------------------------------------- windows and labels


def right_edges(start: int, stop: int) -> np.ndarray:
    """Right edges of W64 windows lying entirely inside [start, stop)."""
    if stop - start < W:
        raise ProtocolViolation("interval shorter than one window")
    return np.arange(start + W - 1, stop, dtype=np.int64)


def fit_window_edges(train_n: int) -> np.ndarray:
    return right_edges(0, fit_end(train_n))


def validation_window_edges(train_n: int) -> np.ndarray:
    return right_edges(fit_end(train_n), int(train_n))


def test_window_edges(test_n: int) -> np.ndarray:
    return right_edges(0, int(test_n))


def window_matrix(scaled: np.ndarray, edges: np.ndarray) -> np.ndarray:
    x = np.asarray(scaled)
    t = np.asarray(edges, dtype=np.int64)
    if x.ndim != 2 or x.shape[1] != D or t.ndim != 1 or (len(t) and (t.min() < W - 1 or t.max() >= len(x))):
        raise ProtocolViolation("window request outside the stream")
    view = np.lib.stride_tricks.sliding_window_view(x, W, axis=0)  # [N-W+1, D, W]
    windows = np.ascontiguousarray(view[t - (W - 1)].transpose(0, 2, 1))
    if windows.shape != (len(t), W, D):
        raise ProtocolViolation("window shape mismatch")
    return windows


def window_any_labels(point_labels: np.ndarray, edges: np.ndarray) -> np.ndarray:
    labels = np.asarray(point_labels, dtype=np.int64)
    t = np.asarray(edges, dtype=np.int64)
    if len(t) and (t.min() < W - 1 or t.max() >= len(labels)):
        raise ProtocolViolation("label window outside the test split")
    cumulative = np.concatenate(([0], np.cumsum(labels)))
    return ((cumulative[t + 1] - cumulative[t + 1 - W]) > 0).astype(np.uint8)


def receptive_interval(edge: int) -> tuple[int, int]:
    """Inclusive observation interval that a finite H/internal234 row at ``edge`` depends on."""
    return int(edge) - FIRST_FINITE, int(edge)


# --------------------------------------------------------------------------- Design B probe blocks


def design_b_blocks(test_n: int) -> dict[str, tuple[int, int]]:
    """Fixed chronological probe blocks over eligible test right edges, half-open."""
    n = int(test_n)
    length = n - FIRST_FINITE
    c1 = FIRST_FINITE + length // 3
    c2 = FIRST_FINITE + (2 * length) // 3
    blocks = {"train": (FIRST_FINITE, c1), "validation": (c1 + EMBARGO, c2), "test": (c2 + EMBARGO, n)}
    order = ("train", "validation", "test")
    for left, right in zip(order, order[1:]):
        if receptive_interval(blocks[left][1] - 1)[1] >= receptive_interval(blocks[right][0])[0]:
            raise ProtocolViolation("probe blocks share observations inside the receptive field")
    if any(stop - start < 1 for start, stop in blocks.values()):
        raise ProtocolViolation("empty probe block")
    return blocks


def block_rows(test_n: int, block: str) -> np.ndarray:
    start, stop = design_b_blocks(test_n)[block]
    return np.arange(start, stop, dtype=np.int64)


# --------------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    acq = sub.add_parser("acquire")
    acq.add_argument("--staged", type=Path, default=None)
    acq.add_argument("--report", type=Path, required=True)
    sub.add_parser("verify")
    args = parser.parse_args(argv)
    if args.command == "acquire":
        report = acquire(args.staged)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"status": report["status"], "blocked": report["blocked"]}))
        return 0 if report["status"] == "ACQUIRED_AND_VERIFIED" else 2
    result = verify_all()
    print(json.dumps(result, indent=2))
    return 0 if result["all_match"] else 2


if __name__ == "__main__":
    sys.exit(main())
