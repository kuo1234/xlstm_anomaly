import inspect

import numpy as np

from scripts.strong_observable_control import _rolling
from scripts.temporally_matched_observable_control import (
    DECISION_START,
    INTERNAL_DIM,
    O1R_DIM,
    ROLLING_WIDTHS,
    arm_matrix,
    expand_o1r,
)


def test_o1r_dimension_and_feature_major_formula():
    base = np.arange(100 * 128, dtype=np.float64).reshape(100, 128)
    got = expand_o1r(base)
    assert got.shape == (100, O1R_DIM)
    assert O1R_DIM == 1664
    for column in (0, 7, 127):
        start = column * 13
        assert np.array_equal(got[:, start], base[:, column])
        for offset, width in enumerate(ROLLING_WIDTHS):
            expected = _rolling(base[:, column : column + 1], width)
            assert np.allclose(got[:, start + 1 + offset * 3 : start + 4 + offset * 3], expected, equal_nan=True)


def test_temporal_span_and_target_alignment_are_causal():
    base = np.arange(140 * 128, dtype=np.float64).reshape(140, 128)
    original = expand_o1r(base)
    changed_future = base.copy()
    changed_future[120:] += 1e9
    future = expand_o1r(changed_future)
    # At decision index 100 the widest window is indices 69..100; changing
    # rows after it cannot affect any feature at or before index 100.
    assert np.array_equal(original[:101], future[:101], equal_nan=True)
    assert not np.array_equal(original[120], future[120])
    # First fully finite O1r row is decision timestamp 94 (index 31 in the
    # dense cache beginning at timestamp 63).
    assert np.isfinite(original[31]).all()
    assert not np.isfinite(original[30]).all()
    assert DECISION_START + 31 == 94


def test_observable_only_api_and_no_internal_dimension_drift():
    assert INTERNAL_DIM == 234
    signature = inspect.signature(expand_o1r)
    assert tuple(signature.parameters) == ("base_o1",)
    assert not set(signature.parameters).intersection({"labels", "truth", "metadata", "event"})


def test_arm_alignment_is_identical_for_temporally_matched_arms():
    records = [{
        "H": np.zeros((2, 14), dtype=np.float32),
        "O1r": np.zeros((2, O1R_DIM), dtype=np.float32),
        "I": np.zeros((2, INTERNAL_DIM), dtype=np.float32),
        "y": np.array([0, 1], dtype=np.int8),
        "source": np.array([3000, 3000], dtype=np.int32),
        "scenario": np.array(["abrupt", "abrupt"], dtype=object),
        "condition": np.array(["none", "spike"], dtype=object),
        "timestamp": np.array([94, 95], dtype=np.int64),
    }]
    left = arm_matrix(records, "H+O1r")
    right = arm_matrix(records, "H+O1r+I")
    for key in ("y", "source", "scenario", "condition", "timestamp"):
        assert np.array_equal(left[key], right[key])


def test_deterministic_split_and_seed_contract():
    from scripts.strong_observable_control import FOLDS, SCENARIOS, SEEDS

    assert FOLDS == {"train": tuple(range(1000, 1010)), "validation": tuple(range(2000, 2005)), "test": tuple(range(3000, 3010))}
    assert SCENARIOS == ("abrupt", "gradual", "recurring", "correlation")
    assert SEEDS == (11, 22, 33)


def test_historical_phase_g1_tree_has_no_worktree_changes():
    import subprocess

    completed = subprocess.run(
        ["git", "diff", "--quiet", "2810c346d40ceb3e011625f6fbf63db8833d9572", "--", "reports/phase_g1"],
        check=False,
    )
    assert completed.returncode == 0
