"""Step 0 (issue #15) parity tests for scripts/p10_canonical_mlstm.py.  float64 on CPU."""
import sys
from pathlib import Path

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import p10_step0_parity as P  # noqa: E402
from p10_canonical_mlstm import KERNELS, VERSIONS  # noqa: E402

TOL = 1e-10


def _states_ok(e, tol=TOL):
    return e["C_eff_rel"] < tol and e["n_eff_rel"] < tol and e["conv"] == 0.0


def test_versions_pinned():
    assert VERSIONS["xlstm"] == "2.0.5" and VERSIONS["mlstm_kernels"] == "2.0.5"
    assert "mlstm_chunkwise__native_autograd" in KERNELS["mLSTMexp"]["chunk"]


@pytest.mark.parametrize("S", [150, 128, 50, 1])
def test_kernel_chunkwise_initial_state_matches_recurrence(S):
    r = P.check_kernel_chunk_vs_step(S)
    assert r["H_chunk_vs_native_step"] < TOL and r["H_chunk_vs_xlstm_backend_step"] < TOL
    assert _states_ok(r["state_chunk_vs_native_step"]) and _states_ok(r["state_chunk_vs_xlstm_backend_step"])


@pytest.mark.parametrize("S,split", [(150, None), (150, 70), (129, 1), (64, 63), (200, 128)])
def test_layer_matches_official_step_full_state(S, split):
    r = P.check_layer_vs_official_step(S, split)
    assert r["y_max_abs"] < TOL * max(r["y_scale"], 1.0)
    assert _states_ok(r["state"])


def test_state_bridge_chunk_and_official_step_interchangeable():
    r = P.check_mixed_chunk_then_official_step()
    assert r["chunk_then_official_step"] < TOL and r["official_step_then_chunk"] < TOL
    assert _states_ok(r["state_chunk_then_step"]) and _states_ok(r["state_step_then_chunk"])


def test_matches_official_parallel_forward_zero_state():
    r = P.check_layer_vs_official_parallel_forward()
    assert r["y_max_abs"] < 1e-6 * r["y_scale"]   # official parallel form differs only at stabilizer/eps level


@pytest.mark.parametrize("variant", ["exp", "sig"])
def test_conv_state_is_carried_and_matters(variant):
    r = P.check_conv_state_carried()[variant]
    assert r["split_vs_full"] < TOL
    assert r["conv_state_full_vs_split"] == 0.0 and r["conv_state_equals_last_inputs"] == 0.0
    assert r["effect_of_zeroing_conv_state_first3"] > 1e-3   # dropping it would be a real bug


def test_siging_step_matches_official_kernels():
    r = P.check_siging()
    for k in ("normalize=False", "normalize=True"):
        assert r[k]["step_vs_official_parallel"] < TOL * r[k]["scale"]
    assert r["layer_wrapper_vs_official_parallel_core"] < TOL


@pytest.mark.skipif(not torch.cuda.is_available(), reason="triton siging chunk kernel needs CUDA")
def test_siging_triton_chunk_with_initial_state():
    r = P.check_siging_triton()
    for k in ("normalize=False", "normalize=True"):   # triton tl.dot = TF32 for fp32 inputs
        assert r[k]["H"] < 5e-3 * max(r[k]["H_scale"], 1.0) and r[k]["C_rel"] < 5e-3
    assert r["normalize=True"]["n_rel"] < 1e-5
    assert r["layer_gpu_triton_split_vs_cpu_step"] < 5e-3 * max(r["layer_scale"], 1.0)
    assert r["exp_gpu_fp32_split_vs_official_step"] < 1e-4 and r["exp_gpu_fp32_state"]["C_eff_rel"] < 1e-4


def test_forecaster_smoke():
    r = P.check_forecaster_smoke(train_steps=40)
    for v in ("exp", "sig"):
        x = r[v]
        assert x["pred_shape"] == [2, 150, 7]
        assert x["split_vs_full"] < TOL and x["step_loop_vs_forward"] < TOL
        assert x["causality_leak_before_t100"] == 0.0 and x["perturbation_effect_at_t100"] > 0
        assert x["loss_last"] < 0.2 * x["loss_first"]
