"""Logical upper-bound audit for the frozen 28-machine Stage-1 complement gate.

This module consumes only the already-computed metrics for the frozen Stage-1A
nine and exact eligible test lengths for the remaining machines. It does not
load labels, scores, or result artifacts and cannot declare Stage-1 success.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

try:
    from scripts.adaptive_normality_m1_metrics import paired_machine_bootstrap
    from scripts.adaptive_normality_m1_scores import STAGE1_MACHINES
except ImportError:  # pragma: no cover
    from adaptive_normality_m1_metrics import paired_machine_bootstrap
    from adaptive_normality_m1_scores import STAGE1_MACHINES


STAGE1A_MACHINES = (
    "machine-1-7", "machine-1-3", "machine-1-5",
    "machine-2-4", "machine-2-7", "machine-2-8",
    "machine-3-2", "machine-3-11", "machine-3-7",
)
UNOPENED_MACHINES = tuple(machine for machine in STAGE1_MACHINES if machine not in STAGE1A_MACHINES)
_CANDIDATE = "forecast_control_fusion"
_CONTROL = "control_fusion"


def _finite_number(value: Any, field: str, *, low: float | None = None,
                   high: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, np.number)):
        raise ValueError(f"{field} must be a finite number")
    result = float(value)
    if not np.isfinite(result) or (low is not None and result < low) or (high is not None and result > high):
        raise ValueError(f"{field} is outside its valid range")
    return result


def _observed_rows(metrics: Sequence[Mapping[str, Any]]) -> list[dict[str, float | str]]:
    if not isinstance(metrics, Sequence) or isinstance(metrics, (str, bytes)) or len(metrics) != 9:
        raise ValueError("feasibility audit requires ordered metrics for exactly the frozen nine Stage-1A machines")
    rows: list[dict[str, float | str]] = []
    for expected, row in zip(STAGE1A_MACHINES, metrics):
        if not isinstance(row, Mapping) or row.get("machine") != expected:
            raise ValueError("observed metrics must be in the exact frozen Stage-1A machine order")
        scores = row.get("scores")
        if not isinstance(scores, Mapping) or not isinstance(scores.get(_CANDIDATE), Mapping) or not isinstance(scores.get(_CONTROL), Mapping):
            raise ValueError(f"{expected}: full complement score metrics are required")
        candidate, control = scores[_CANDIDATE], scores[_CONTROL]
        prevalence = _finite_number(row.get("prevalence"), f"{expected}.prevalence", low=0.0, high=1.0)
        if prevalence <= 0.0:
            raise ValueError(f"{expected}: prevalence must be positive")
        ap = _finite_number(candidate.get("AP"), f"{expected}.AP", low=0.0, high=1.0)
        control_ap = _finite_number(control.get("AP"), f"{expected}.control_AP", low=0.0, high=1.0)
        delta = _finite_number(row.get("delta_AP_forecast_control_fusion"), f"{expected}.delta_AP", low=-1.0, high=1.0)
        if not np.isclose(delta, ap - control_ap, rtol=0.0, atol=1e-12):
            raise ValueError(f"{expected}: complement delta differs from the two AP values")
        event = _finite_number(candidate.get("event_detection_rate"), f"{expected}.event_detection_rate", low=0.0, high=1.0)
        fpr = _finite_number(candidate.get("normal_point_FPR"), f"{expected}.normal_point_FPR", low=0.0, high=1.0)
        rows.append({"machine": expected, "prevalence": prevalence, "AP": ap,
                     "AP_over_prevalence": ap / prevalence, "event_detection_rate": event,
                     "normal_point_FPR": fpr, "delta_AP": delta})
    return rows


def _unopened_lengths(lengths: Mapping[str, int]) -> dict[str, int]:
    if not isinstance(lengths, Mapping) or tuple(lengths.keys()) != UNOPENED_MACHINES:
        raise ValueError("eligible-label lengths must enumerate the exact unopened 19 machines in canonical order")
    result = {}
    for machine in UNOPENED_MACHINES:
        value = lengths[machine]
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or int(value) <= 0:
            raise ValueError(f"{machine}: eligible-label length must be a positive integer")
        result[machine] = int(value)
    return result


def decide_complement_feasibility(
    observed_metrics: Sequence[Mapping[str, Any]],
    unopened_eligible_label_lengths: Mapping[str, int],
) -> dict[str, Any]:
    """Return whether any original complement-gate component is irrecoverable.

    Unopened machines receive componentwise optimistic values: zero FPR,
    event-detection one, AP/prevalence equal to their eligible label length,
    AP-above-prevalence true, positive delta true, and delta AP one. The
    paired bootstrap bound uses this same delta upper-bound vector under the
    frozen 10,000-resample/901-seed machine bootstrap.
    """
    rows = _observed_rows(observed_metrics)
    lengths = _unopened_lengths(unopened_eligible_label_lengths)
    deltas = np.asarray([float(row["delta_AP"]) for row in rows], dtype=np.float64)
    aps = np.asarray([float(row["AP"]) for row in rows], dtype=np.float64)
    prevalence = np.asarray([float(row["prevalence"]) for row in rows], dtype=np.float64)
    events = np.asarray([float(row["event_detection_rate"]) for row in rows], dtype=np.float64)
    fprs = np.asarray([float(row["normal_point_FPR"]) for row in rows], dtype=np.float64)
    ratios = np.asarray([float(row["AP_over_prevalence"]) for row in rows], dtype=np.float64)

    high_fpr_count = int(np.sum(fprs > 0.05))
    high_fpr_machines = [str(row["machine"]) for row in rows if float(row["normal_point_FPR"]) > 0.05]
    catastrophic_machines = [str(row["machine"]) for row in rows
                             if float(row["AP"]) <= float(row["prevalence"])
                             and float(row["event_detection_rate"]) <= 0.10]
    catastrophic = len(catastrophic_machines)
    positive_delta = int(np.sum(deltas > 0.0))
    ap_above_prevalence = int(np.sum(aps > prevalence))
    delta_upper_vector = np.concatenate([deltas, np.ones(19, dtype=np.float64)])
    optimistic_bootstrap = paired_machine_bootstrap(delta_upper_vector)

    optimistic_fpr = float(fprs.sum() / 28.0)  # zero for every unopened machine
    optimistic_positive = positive_delta + 19
    optimistic_ap_prevalence = ap_above_prevalence + 19
    optimistic_event = float((events.sum() + 19.0) / 28.0)
    optimistic_mean_delta = float(delta_upper_vector.mean())
    # With at least one anomaly in n eligible binary labels, prevalence >= 1/n;
    # AP <= 1, hence AP/prevalence <= n. Treat this as the valid physical upper bound.
    optimistic_ratios = np.concatenate([ratios, np.asarray(list(lengths.values()), dtype=np.float64)])
    optimistic_median_ratio = float(np.median(optimistic_ratios))

    bounds: dict[str, dict[str, Any]] = {
        "high_fpr_count": {"observed_count": high_fpr_count, "maximum": 2,
                           "observed_machines": high_fpr_machines,
                           "impossible": high_fpr_count > 2},
        "catastrophic_count": {"observed_count": catastrophic, "maximum": 2,
                               "observed_machines": catastrophic_machines,
                               "impossible": catastrophic > 2},
        "macro_normal_point_fpr": {"best_case": optimistic_fpr, "maximum": 0.02,
                                    "unopened_assumption": "all 19 FPRs equal zero",
                                    "impossible": optimistic_fpr > 0.02},
        "positive_delta_count": {"observed_count": positive_delta, "maximum_achievable": optimistic_positive,
                                 "required": 20, "impossible": optimistic_positive < 20},
        "ap_above_prevalence_count": {"observed_count": ap_above_prevalence,
                                      "maximum_achievable": optimistic_ap_prevalence,
                                      "required": 20, "impossible": optimistic_ap_prevalence < 20},
        "median_ap_over_prevalence": {"best_case": optimistic_median_ratio, "minimum": 1.5,
                                      "unopened_ratio_upper_bounds": dict(lengths),
                                      "impossible": optimistic_median_ratio < 1.5},
        "macro_event_detection": {"best_case": optimistic_event, "minimum": 0.50,
                                  "unopened_assumption": "all 19 event detection rates equal one",
                                  "impossible": optimistic_event < 0.50},
        "mean_delta_ap": {"best_case": optimistic_mean_delta, "minimum": 0.02,
                          "unopened_delta_upper_bound": 1.0,
                          "impossible": optimistic_mean_delta < 0.02},
        "bootstrap_lower_95": {"best_case_lower_95": float(optimistic_bootstrap["lower_95"]),
                                "required_strictly_greater_than": 0.0,
                                "samples": int(optimistic_bootstrap["samples"]),
                                "seed": int(optimistic_bootstrap["seed"]),
                                "resampling_unit": optimistic_bootstrap["resampling_unit"],
                                "impossible": optimistic_bootstrap["lower_95"] <= 0.0},
    }
    impossible = [name for name, bound in bounds.items() if bound["impossible"]]
    return {
        "decision": "FINAL_COMPLEMENT_ROUTE_IMPOSSIBLE" if impossible else "FINAL_COMPLEMENT_ROUTE_STILL_FEASIBLE",
        "bounds": bounds,
        "impossible_components": impossible,
        "observed_machines": list(STAGE1A_MACHINES),
        "unopened_machines": list(UNOPENED_MACHINES),
        "unopened_eligible_label_lengths": lengths,
        "observed_delta_AP": [float(value) for value in deltas],
        "observed_high_fpr_machines": high_fpr_machines,
        "observed_catastrophic_machines": catastrophic_machines,
        "optimistic_bootstrap_mean_delta_AP": float(optimistic_bootstrap["mean"]),
        "stage1_pass_permitted": False,
        "audit_kind": "logical_feasibility_only_no_efficacy_decision",
    }
