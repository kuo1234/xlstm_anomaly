import subprocess

import numpy as np
import pytest

from scripts.adaptive_normality_m1_metrics import (
    require_all_stage1_scores_sealed_and_committed, require_stage1_inventory, run_metric_entrypoint,
)
from scripts.adaptive_normality_m1_scores import (
    STAGE1_MACHINES, STAGE1_SCORE_DIR, STAGE1_SCORE_NAMES,
    seal_score_artifact, seal_stage1_machine_scores,
)


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_metric_entrypoint_refuses_before_label_loader_when_scores_uncommitted(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    _git(repo, "init", "-q")
    seal_stage1_machine_scores(repo, _stage1_synthetic())
    paths = [repo / STAGE1_SCORE_DIR / f"{m}.npz" for m in STAGE1_MACHINES]
    touched = []
    with pytest.raises(RuntimeError, match="manifest must be committed"):
        run_metric_entrypoint(score_artifacts=paths, repo=repo,
                              label_loader=lambda: touched.append("label") or object(),
                              metric_runner=lambda *_: None)
    assert touched == []


def test_metric_entrypoint_rejects_missing_seal_without_label_access(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir(); _git(repo, "init", "-q")
    paths = [repo / STAGE1_SCORE_DIR / f"{m}.npz" for m in STAGE1_MACHINES]
    touched = []
    with pytest.raises(RuntimeError, match="inventory seal is missing"):
        run_metric_entrypoint(score_artifacts=paths, repo=repo,
                              label_loader=lambda: touched.append(True),
                              metric_runner=lambda *_: None)
    assert touched == []


def test_metric_entrypoint_allows_label_callback_only_after_committed_inventory(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir(); _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "m1-test@example.invalid")
    _git(repo, "config", "user.name", "M1 synthetic test")
    seal_stage1_machine_scores(repo, _stage1_synthetic())
    _git(repo, "add", "reports/adaptive_normality_m1_smd")
    _git(repo, "commit", "-qm", "synthetic sealed inventory")
    paths = [repo / STAGE1_SCORE_DIR / f"{machine}.npz" for machine in STAGE1_MACHINES]
    calls = []
    result = run_metric_entrypoint(
        score_artifacts=paths, repo=repo,
        label_loader=lambda: calls.append("authorized_loader") or {"synthetic": True},
        metric_runner=lambda manifests, labels: (len(manifests[0]["machines"]), labels),
    )
    assert calls == ["authorized_loader"]
    assert result == (28, {"synthetic": True})


def test_gate_accepts_only_committed_exact_artifact_and_seal(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir(); _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "m1-test@example.invalid")
    _git(repo, "config", "user.name", "M1 synthetic test")
    path = repo / "scores.npz"
    seal_score_artifact(path, np.array([1., 2.]), [256, 257], arm="x", machine="m")
    _git(repo, "add", "scores.npz", "scores.npz.manifest.json")
    _git(repo, "commit", "-qm", "synthetic sealed scores")
    docs = require_all_stage1_scores_sealed_and_committed([path], repo)
    assert docs[0]["count"] == 2
    # Changed bytes invalidate both the seal and the committed-blob check.
    with path.open("ab") as f:
        f.write(b"x")
    with pytest.raises(ValueError, match="hash"):
        require_all_stage1_scores_sealed_and_committed([path], repo)


def _stage1_synthetic():
    return {machine: {"timestamps": np.array([256, 257]),
                      **{name: np.array([1., 2.]) for name in STAGE1_SCORE_NAMES}}
            for machine in STAGE1_MACHINES}


def test_canonical_inventory_requires_exact_28_machine_nine_array_set(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir(); _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "m1-test@example.invalid")
    _git(repo, "config", "user.name", "M1 synthetic test")
    manifest = seal_stage1_machine_scores(repo, _stage1_synthetic())
    _git(repo, "add", "reports/adaptive_normality_m1_smd")
    _git(repo, "commit", "-qm", "synthetic sealed inventory")
    inventory = require_stage1_inventory(repo)
    assert len(inventory["machines"]) == 28
    assert manifest.is_file()


def test_stage1_inventory_rejects_incomplete_machine_set(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    records = _stage1_synthetic(); records.pop(STAGE1_MACHINES[0])
    with pytest.raises(ValueError, match="exactly the frozen 28"):
        seal_stage1_machine_scores(repo, records)
