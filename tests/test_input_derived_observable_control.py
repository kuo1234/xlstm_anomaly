import inspect
import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

import scripts.input_derived_observable_control as p1r

# The module under test imports its dependencies from scripts/ on sys.path; use
# those exact module objects so identity checks compare the objects it uses.
nl = p1r._nl
soc = p1r._soc
ap = p1r._ap

CONSOLIDATED_MAIN = "855c34d29920cc9aa85fa26d438784d150ac0d79"


def test_frozen_dimensions():
    assert p1r.P1_BASE_DIM == 128
    assert p1r.P1R_DIM == 1664 == ap.O1R_DIM
    assert p1r.ARM_DIMS == {"H+P1r": 1678, "H+P1r+I": 1912}
    assert p1r.ARMS == ("H+P1r", "H+P1r+I")
    assert p1r.FIRST_FINITE_INDEX == 31 and p1r.FIRST_FINITE_TIMESTAMP == 94
    assert p1r.RAW_SUPPORT_LAG == 94
    assert tuple(ap.ROLLING_WIDTHS) == (4, 8, 16, 32)


def test_statistic_family_scaler_and_expansion_are_the_frozen_objects():
    windows = np.random.default_rng(0).normal(size=(5, 64, 8)).astype(np.float32)
    assert np.array_equal(p1r.p1_statistic_family(windows), soc.residual_o1(windows))
    assert p1r.residual_o1 is soc.residual_o1
    assert p1r._scaler is soc._scaler and p1r.scale_input is soc.scale_input
    assert p1r.expand_o1r is ap.expand_o1r and p1r.dense_windows is soc.dense_windows


def test_p1r_shape_and_warmup_pattern():
    scaled = np.random.default_rng(1).normal(size=(300, 8)).astype(np.float32)
    values, timestamps = p1r.p1r_from_scaled(scaled)
    assert values.shape == (237, 1664)
    assert np.array_equal(timestamps, np.arange(63, 300))
    finite = np.isfinite(values).all(axis=1)
    assert not finite[:31].any() and finite[31:].all()


@pytest.mark.parametrize("offset", [0, 40, 150, 299])
def test_temporal_support_is_t_minus_94_to_t_and_causal(offset):
    scaled = np.random.default_rng(2).normal(size=(300, 8)).astype(np.float32)
    check = p1r.temporal_support_check(scaled, offset)
    assert check["pass"], check
    assert check["no_backward_leakage"]


def test_feature_path_has_no_truth_or_backbone_inputs():
    truth = p1r.truth_free_feature_path()
    assert truth["pass"], truth
    assert tuple(inspect.signature(p1r.p1r_from_observations).parameters) == ("observations", "scaler")
    assert p1r.backbone_invariance()["pass"]


def test_detector_observations_mirror_cache_extraction():
    from m0.synthetic import generate

    expected = np.asarray(generate(3000, "gradual", "none").observations, dtype=np.float32)
    observed = p1r.detector_observations(3000, "gradual", "none")
    assert observed.dtype == np.float32 and np.array_equal(observed, expected)


def test_p1r_is_invariant_to_evaluator_semantics():
    assert p1r._semantic_observation_identity(("test", 3000, "abrupt", "spike"))


def test_selection_path_is_validation_only():
    check = p1r.selection_path_check()
    assert check["pass"], check
    assert p1r.estimator_parameters is nl.estimator_parameters
    assert p1r.MAX_ITER_GRID == (100, 300)


def test_outcome_classification_is_frozen():
    assert p1r.classify([0.001, 0.02]) == "ADDITIONAL_UTILITY_BEYOND_P1R"
    assert p1r.classify([-0.001, 0.02]) == "NO_RESOLVED_ADDITIONAL_UTILITY"
    assert p1r.classify([-0.02, -0.001]) == "NEGATIVE_INCREMENT"


def test_fit_refuses_without_passing_preflights(tmp_path, monkeypatch):
    monkeypatch.setattr(p1r, "PREFLIGHT", tmp_path / "preflight.json")
    monkeypatch.setattr(p1r, "HOST_PREFLIGHT", tmp_path / "host_preflight.json")
    with pytest.raises(PermissionError):
        p1r.require_preflights("seal")
    (tmp_path / "preflight.json").write_text(json.dumps({"status": "FAIL", "protocol_seal": "seal"}))
    (tmp_path / "host_preflight.json").write_text(json.dumps({"status": "PASS", "protocol_seal": "seal"}))
    with pytest.raises(PermissionError):
        p1r.require_preflights("seal")


def test_protocol_freezes_last_control_and_bounded_wording():
    text = " ".join(Path("research/input_derived_observable_control/protocol.md").read_text().split())
    assert "last bounded input-derived control" in text
    assert "additional predictive/decodable utility under the fixed decoder" in text
    assert "early_stopping=False" in text
    for forbidden in ("decoder zoo", "HGB budget sweep", "MLP/CNN", "W128/W256", "persistent state", "new observable summary"):
        assert forbidden in text


def test_historical_artifacts_untouched_since_consolidated_main():
    paths = [
        "reports", "m0", "configs", "data",
        "research/temporally_matched_observable_control",
        "research/aplus_solver_convergence_audit",
        "research/nonlinear_observable_control",
        "scripts/strong_observable_control.py",
        "scripts/temporally_matched_observable_control.py",
        "scripts/nonlinear_observable_control.py",
    ]
    completed = subprocess.run(["git", "diff", "--quiet", CONSOLIDATED_MAIN, "--", *paths], check=False)
    assert completed.returncode == 0
