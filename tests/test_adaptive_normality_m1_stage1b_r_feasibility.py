import numpy as np
import pytest

from scripts.adaptive_normality_m1_metrics import BOOTSTRAP_SAMPLES, BOOTSTRAP_SEED, paired_machine_bootstrap
from scripts.adaptive_normality_m1_stage1b_r_feasibility import (
    STAGE1A_MACHINES,
    decide_complement_feasibility,
)
from scripts.adaptive_normality_m1_scores import STAGE1_MACHINES


UNOPENED = tuple(machine for machine in STAGE1_MACHINES if machine not in STAGE1A_MACHINES)


def _machine(machine, *, delta=0.03, ap=0.20, prevalence=0.05, event=0.60, fpr=0.01):
    return {
        "machine": machine,
        "prevalence": prevalence,
        "delta_AP_forecast_control_fusion": delta,
        "scores": {
            "forecast_control_fusion": {
                "AP": ap,
                "AP_over_prevalence": ap / prevalence,
                "event_detection_rate": event,
                "normal_point_FPR": fpr,
            },
            "control_fusion": {"AP": ap - delta},
        },
    }


def _inputs(**overrides):
    lengths = overrides.pop("_lengths", None)
    observed = []
    for machine in STAGE1A_MACHINES:
        values = overrides.get(machine, {})
        observed.append(_machine(machine, **values))
    # Exact eligible test lengths are used only to bound AP/prevalence by n.
    lengths = lengths or {machine: 1000 for machine in UNOPENED}
    return observed, lengths


def _audit(**overrides):
    observed, lengths = _inputs(**overrides)
    return decide_complement_feasibility(observed, lengths)


def test_order_and_inventory_are_exact_and_fail_closed():
    observed, lengths = _inputs()
    assert decide_complement_feasibility(observed, lengths)["decision"] == "FINAL_COMPLEMENT_ROUTE_STILL_FEASIBLE"
    with pytest.raises(ValueError, match="order"):
        decide_complement_feasibility(observed[::-1], lengths)
    malformed = dict(lengths)
    malformed.pop(UNOPENED[-1])
    malformed["unexpected-machine"] = 100
    with pytest.raises(ValueError, match="exact unopened"):
        decide_complement_feasibility(observed, malformed)


@pytest.mark.parametrize("count,impossible", [(3, True), (2, False)])
def test_high_fpr_count_bound(count, impossible):
    overrides = {m: {"fpr": 0.051 if i < count else 0.01} for i, m in enumerate(STAGE1A_MACHINES)}
    result = _audit(**overrides)
    assert result["bounds"]["high_fpr_count"]["impossible"] is impossible


def test_catastrophic_count_bound():
    overrides = {m: {"ap": 0.04, "prevalence": 0.05, "event": 0.10} for m in STAGE1A_MACHINES[:3]}
    result = _audit(**overrides)
    assert result["bounds"]["catastrophic_count"]["observed_count"] == 3
    assert result["bounds"]["catastrophic_count"]["impossible"] is True


def test_macro_fpr_optimistic_zero_unopened_bound():
    # 9 * .07 / 28 > .02 even if every remaining FPR is zero.
    result = _audit(**{m: {"fpr": 0.07} for m in STAGE1A_MACHINES})
    assert result["bounds"]["macro_normal_point_fpr"]["best_case"] == pytest.approx(9 * 0.07 / 28)
    assert result["bounds"]["macro_normal_point_fpr"]["impossible"] is True


def test_positive_delta_maximum_bound():
    result = _audit(**{m: {"delta": -0.1} for m in STAGE1A_MACHINES})
    bound = result["bounds"]["positive_delta_count"]
    assert bound["maximum_achievable"] == 19
    assert bound["impossible"] is True

    boundary = _audit(**{**{m: {"delta": -0.1} for m in STAGE1A_MACHINES},
                         STAGE1A_MACHINES[0]: {"delta": 0.01}})
    assert boundary["bounds"]["positive_delta_count"]["maximum_achievable"] == 20
    assert boundary["bounds"]["positive_delta_count"]["impossible"] is False


def test_ap_above_prevalence_maximum_bound():
    # Nine observed failures leave only 19 possible successes, below 20.
    result = _audit(**{m: {"ap": 0.04, "prevalence": 0.05} for m in STAGE1A_MACHINES})
    assert result["bounds"]["ap_above_prevalence_count"]["maximum_achievable"] == 19
    assert result["bounds"]["ap_above_prevalence_count"]["impossible"] is True

    boundary = _audit(**{**{m: {"ap": 0.04, "prevalence": 0.05} for m in STAGE1A_MACHINES},
                         STAGE1A_MACHINES[0]: {"ap": 0.08, "prevalence": 0.05}})
    assert boundary["bounds"]["ap_above_prevalence_count"]["maximum_achievable"] == 20
    assert boundary["bounds"]["ap_above_prevalence_count"]["impossible"] is False


def test_median_ap_prevalence_optimistic_bound_uses_eligible_lengths():
    result = _audit(**{m: {"ap": 0.001, "prevalence": 0.1, "delta": -0.5} for m in STAGE1A_MACHINES},
                    _lengths={m: 1 for m in UNOPENED})
    ratio = result["bounds"]["median_ap_over_prevalence"]["best_case"]
    assert ratio == pytest.approx(1.0)  # unopened upper ratios are exactly their eligible lengths, here one.
    assert result["bounds"]["median_ap_over_prevalence"]["impossible"] is True


def test_event_detection_optimistic_bound():
    result = _audit(**{m: {"event": 0.0} for m in STAGE1A_MACHINES})
    assert result["bounds"]["macro_event_detection"]["best_case"] == pytest.approx(19 / 28)
    assert result["bounds"]["macro_event_detection"]["impossible"] is False


def test_mean_delta_ap_optimistic_bound_uses_physical_delta_ceiling_one():
    result = _audit(**{m: {"delta": -1.0, "ap": 0.0} for m in STAGE1A_MACHINES})
    bound = result["bounds"]["mean_delta_ap"]
    assert bound["best_case"] == pytest.approx((sum([-1.0] * 9) + 19) / 28)
    assert bound["impossible"] is False


def test_bootstrap_upper_bound_uses_frozen_seed_and_sample_count():
    result = _audit()
    bound = result["bounds"]["bootstrap_lower_95"]
    deltas = np.array([_machine(m)["delta_AP_forecast_control_fusion"] for m in STAGE1A_MACHINES] + [1.0] * 19)
    expected = paired_machine_bootstrap(deltas)
    assert bound["best_case_lower_95"] == expected["lower_95"]
    assert bound["samples"] == BOOTSTRAP_SAMPLES == 10_000
    assert bound["seed"] == BOOTSTRAP_SEED == 901

    worst_observed = _audit(**{m: {"delta": -1.0, "ap": 0.0} for m in STAGE1A_MACHINES})
    expected_worst = paired_machine_bootstrap(np.array([-1.0] * 9 + [1.0] * 19))
    assert worst_observed["bounds"]["bootstrap_lower_95"]["best_case_lower_95"] == expected_worst["lower_95"]
    assert worst_observed["bounds"]["bootstrap_lower_95"]["impossible"] is (
        expected_worst["lower_95"] <= 0.0
    )


def test_all_components_possible_means_still_feasible():
    result = _audit()
    assert result["decision"] == "FINAL_COMPLEMENT_ROUTE_STILL_FEASIBLE"
    assert result["impossible_components"] == []


def test_result_is_feasibility_only_not_efficacy_gate():
    result = _audit()
    assert set(result) >= {"decision", "bounds", "impossible_components", "stage1_pass_permitted"}
    assert result["stage1_pass_permitted"] is False
    assert result["decision"] in {
        "FINAL_COMPLEMENT_ROUTE_IMPOSSIBLE",
        "FINAL_COMPLEMENT_ROUTE_STILL_FEASIBLE",
    }
