import json
import subprocess

import numpy as np

from scripts.aplus_solver_convergence_audit import (
    crossed_bootstrap,
    load_ap_aggregate,
    source_only_bootstrap,
)


def test_crossed_bootstrap_is_deterministic_and_resamples_shared_seed_columns():
    matrix = np.arange(30, dtype=np.float64).reshape(10, 3)
    first = crossed_bootstrap(matrix, draws=200, seed=901)
    second = crossed_bootstrap(matrix, draws=200, seed=901)
    assert first == second
    assert first["method"] == "two_way_crossed_source_rows_seed_columns"
    assert first["ci95"][0] <= first["mean"] <= first["ci95"][1]


def test_source_only_bootstrap_is_distinct_and_deterministic():
    matrix = np.arange(30, dtype=np.float64).reshape(10, 3)
    result = source_only_bootstrap(matrix, draws=200, seed=901)
    assert result["method"] == "source_only_condition_on_observed_seeds"
    assert result == source_only_bootstrap(matrix, draws=200, seed=901)


def test_committed_a_plus_matrices_are_10_by_3_and_g1_tree_is_untouched():
    data = load_ap_aggregate()
    for architecture in ("xlstm", "lstm"):
        assert np.asarray(data["architectures"][architecture]["source_seed_matrix"]).shape == (10, 3)
    completed = subprocess.run(
        ["git", "diff", "--quiet", "04e0abbd7a9a6a8c8d00052cd1b20c51e0a71d28", "--", "reports/phase_g1"],
        check=False,
    )
    assert completed.returncode == 0


def test_convergence_metadata_serialization_contract(tmp_path):
    payload = {
        "C": 0.01,
        "validation_AP": 0.5,
        "n_iter": 123,
        "convergence_warning": False,
        "hit_max_iter": False,
        "coef_sha256": "abc",
        "intercept_sha256": "def",
    }
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(payload))
    loaded = json.loads(path.read_text())
    assert loaded["n_iter"] == 123
    assert loaded["convergence_warning"] is False
    assert loaded["hit_max_iter"] is False
    assert loaded["coef_sha256"] == "abc"


def test_completed_s1_s2_artifacts_are_converged_and_retain_reference_rows():
    root = __import__("pathlib").Path("research/aplus_solver_convergence_audit")
    for stage in ("s1", "s2"):
        for architecture in ("xlstm", "lstm"):
            for seed in (11, 22, 33):
                payload = json.loads((root / stage / f"{stage}_{architecture}_{seed}.json").read_text())
                assert payload["cache_read_only"] is True
                assert payload["primary"]["all_fits_converged"] is True
                assert payload["row_key_sha256"] == payload["arms"]["H+O1r"]["row_key_sha256"]
                assert payload["row_key_sha256"] == payload["arms"]["H+O1r+I"]["row_key_sha256"]
                for arm in payload["arms"].values():
                    assert arm["all_fits_converged"] is True
                    assert all(candidate["converged"] for candidate in arm["validation_candidates"])
                    assert arm["selected_final"]["converged"] is True


def test_a_plus_s_does_not_change_historical_g1_tree():
    completed = subprocess.run(
        ["git", "diff", "--quiet", "04e0abbd7a9a6a8c8d00052cd1b20c51e0a71d28", "--", "reports/phase_g1"],
        check=False,
    )
    assert completed.returncode == 0
