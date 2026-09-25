"""Metric-only entry point, gated on committed immutable Stage-1 score seals.

No label path is inspected or opened by this module until
``run_metric_entrypoint`` has verified every required score artifact and seal
against both the manifest and the current git HEAD.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable, TypeVar
import hashlib

import numpy as np

try:
    from scripts import adaptive_normality_m1_data as m1_data
except ImportError:  # pragma: no cover - direct script execution
    import adaptive_normality_m1_data as m1_data

try:  # Support both ``scripts.foo`` imports and direct script execution.
    from scripts.adaptive_normality_m1_scores import (STAGE1_MACHINES, STAGE1_MANIFEST_PATH, STAGE1_SCORE_DIR, STAGE1_SCORE_NAMES,
        _check_times, _scores, _sha256, git_committed, verify_score_seal)
except ImportError:  # pragma: no cover - direct script execution
    from adaptive_normality_m1_scores import (STAGE1_MACHINES, STAGE1_MANIFEST_PATH, STAGE1_SCORE_DIR, STAGE1_SCORE_NAMES,
        _check_times, _scores, _sha256, git_committed, verify_score_seal)

T = TypeVar("T")


def require_all_stage1_scores_sealed_and_committed(score_artifacts: Iterable[str | Path], repo: str | Path) -> list[dict]:
    """Verify each required NPZ has a valid seal and both files are committed."""
    root = Path(repo).resolve()
    artifacts = [Path(p).resolve() for p in score_artifacts]
    if not artifacts:
        raise ValueError("required Stage-1 score artifact list is empty")
    if len(set(artifacts)) != len(artifacts):
        raise ValueError("duplicate Stage-1 score artifact")
    manifests = []
    for artifact in artifacts:
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
        manifests.append(doc)
    return manifests


require_committed_sealed_scores = require_all_stage1_scores_sealed_and_committed


def require_stage1_inventory(repo: str | Path) -> dict:
    """Require the exact committed 28-machine/nine-score Stage-1 inventory."""
    root = Path(repo).resolve()
    directory = root / STAGE1_SCORE_DIR
    manifest = root / STAGE1_MANIFEST_PATH
    if not manifest.is_file():
        raise RuntimeError("canonical Stage-1 score inventory seal is missing")
    doc = __import__("json").loads(manifest.read_text(encoding="utf-8"))
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
        expected_rel = (STAGE1_SCORE_DIR / f"{machine}.npz").as_posix()
        if entry.get("artifact") != expected_rel or entry.get("arrays") != list(STAGE1_SCORE_NAMES):
            raise RuntimeError(f"{machine}: noncanonical artifact path or score array set")
        artifact = root / expected_rel
        if not artifact.is_file() or not git_committed(artifact, root):
            raise RuntimeError(f"{machine}: score artifact must exist and be committed")
        if _sha256(artifact) != entry.get("sha256"):
            raise RuntimeError(f"{machine}: score artifact hash differs from inventory seal")
        with np.load(artifact, allow_pickle=False) as arrays:
            if set(arrays.files) != {"timestamps", *STAGE1_SCORE_NAMES}:
                raise RuntimeError(f"{machine}: artifact does not contain the exact required arrays")
            times = arrays["timestamps"]
            _check_times(times, len(times))
            if hashlib.sha256(times.tobytes()).hexdigest() != entry.get("timestamp_sha256"):
                raise RuntimeError(f"{machine}: timestamp hash differs from inventory seal")
            if len(times) != entry.get("count"):
                raise RuntimeError(f"{machine}: timestamp count differs from inventory seal")
            for name in STAGE1_SCORE_NAMES:
                values = _scores(arrays[name])
                if values.ndim != 1 or len(values) != len(times):
                    raise RuntimeError(f"{machine}: invalid score vector {name}")
    return doc


require_committed_sealed_scores = require_stage1_inventory


def run_metric_entrypoint(*, score_artifacts: Iterable[str | Path], repo: str | Path,
                          label_loader: Callable[[], T], metric_runner: Callable[[list[dict], T], object]) -> object:
    """Open labels and run metrics only after all required scores pass the gate.

    This is a future metric-only entry point. It is intentionally not invoked
    during result-blind M1 implementation/preflight.
    """
    m1_data.install_test_label_access_guard()
    # The supplied list must enumerate the canonical per-machine score files;
    # completeness is established from the independently sealed inventory.
    expected = [Path(repo).resolve() / STAGE1_SCORE_DIR / f"{m}.npz" for m in STAGE1_MACHINES]
    supplied = [Path(p).resolve() for p in score_artifacts]
    if supplied != expected:
        raise RuntimeError("metric entry point requires the exact canonical 28-machine score inventory")
    inventory = require_stage1_inventory(repo)
    manifests = [inventory]
    # The only permitted label-loading window begins after the complete,
    # committed 28-machine score inventory has passed verification.
    with m1_data.sealed_metric_label_access():
        labels = label_loader()
    return metric_runner(manifests, labels)
