import json
import inspect
import subprocess
from pathlib import Path

import numpy as np

from scripts.nonlinear_observable_control import (
    ARMS,
    ARCHITECTURES,
    FOLDS,
    MAX_ITER_GRID,
    SEEDS,
    _key_sha,
    arm_matrix,
    crossed_bootstrap,
    estimator_parameters,
    source_only_bootstrap,
)
from scripts.temporally_matched_observable_control import collect


def test_frozen_estimator_and_iteration_grid():
    assert MAX_ITER_GRID == (100, 300)
    for value in MAX_ITER_GRID:
        params = estimator_parameters(value)
        assert params["max_iter"] == value
        assert params["early_stopping"] is False
        assert params["categorical_features"] is None
        assert params["random_state"] == 901
        assert params["class_weight"] is None


def test_exact_folds_arms_and_seeds():
    assert FOLDS["train"] == tuple(range(1000, 1010))
    assert FOLDS["validation"] == tuple(range(2000, 2005))
    assert FOLDS["test"] == tuple(range(3000, 3010))
    assert SEEDS == (11, 22, 33)
    assert ARMS == ("H+O1r", "H+O1r+I")
    assert ARCHITECTURES == ("xlstm", "lstm")


def test_crossed_bootstrap_is_deterministic_and_distinct_from_source_only():
    matrix = np.arange(30, dtype=np.float64).reshape(10, 3)
    first = crossed_bootstrap(matrix, draws=500, seed=901)
    second = crossed_bootstrap(matrix, draws=500, seed=901)
    assert first == second
    assert first["method"] == "crossed_source_rows_seed_columns"
    assert first["ci95"][0] <= first["mean"] <= first["ci95"][1]
    source_only = source_only_bootstrap(matrix, draws=500, seed=901)
    assert source_only["method"] == "source_only_condition_on_three_observed_seeds"


def test_historical_g1_tree_is_untouched():
    completed = subprocess.run(
        ["git", "diff", "--quiet", "ccb9a3d7e8fc1ced5707b5691de6b09a90f3736f", "--", "reports/phase_g1"],
        check=False,
    )
    assert completed.returncode == 0


def test_linear_reference_artifacts_are_read_only_and_present():
    path = Path("research/aplus_solver_convergence_audit/s2_summary.json")
    payload = json.loads(path.read_text())
    assert path.exists()
    assert payload["status"] == "CONVERGENCE_PASS"
    assert "xlstm" in payload["comparison"]
    assert "lstm" in payload["comparison"]


def test_protocol_does_not_enable_internal_early_stopping():
    text = Path("research/nonlinear_observable_control/protocol.md").read_text()
    assert "early_stopping=False" in text
    assert "validation_fraction" not in text


def test_both_arms_preserve_identical_synthetic_row_keys_and_dimensions():
    records = [{
        "H": np.zeros((3, 14), dtype=np.float32),
        "O1r": np.zeros((3, 1664), dtype=np.float32),
        "I": np.zeros((3, 234), dtype=np.float32),
        "y": np.array([0, 1, 0], dtype=np.int8),
        "source": np.array([3000, 3000, 3000], dtype=np.int32),
        "scenario": np.array(["abrupt"] * 3, dtype=object),
        "condition": np.array(["none"] * 3, dtype=object),
        "timestamp": np.array([63, 64, 65], dtype=np.int64),
    }]
    observable = arm_matrix(records, "H+O1r")
    internal = arm_matrix(records, "H+O1r+I")
    observable_key = _key_sha(observable["source"], observable["scenario"], observable["condition"], observable["timestamp"])
    internal_key = _key_sha(internal["source"], internal["scenario"], internal["condition"], internal["timestamp"])
    assert observable_key == internal_key
    assert observable["X"].shape == (3, 1678)
    assert internal["X"].shape == (3, 1912)
    assert np.array_equal(observable["y"], internal["y"])


def test_feature_collector_has_no_label_or_evaluator_argument():
    assert tuple(inspect.signature(collect).parameters) == ("cache_dir", "fold")


def test_selection_path_is_validation_only_and_test_is_post_selection():
    text = Path("scripts/nonlinear_observable_control.py").read_text()
    assert "_fit_candidate(train, validation, max_iter)" in text
    assert "_fit_selected(test, train, selected_max_iter)" in text
    assert "StandardScaler" not in text
