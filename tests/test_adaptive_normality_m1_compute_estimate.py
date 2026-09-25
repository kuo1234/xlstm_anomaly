import json
from pathlib import Path

import pytest

from scripts.adaptive_normality_m1_compute_estimate import estimate_stage1_compute
from scripts.adaptive_normality_m1_data import MANIFEST


ROOT = Path(__file__).resolve().parents[1]


def test_compute_estimate_uses_all_28_train_counts_and_respects_memory_limit():
    canary = json.loads((ROOT / "reports/adaptive_normality_m1_smd/timing_canary.json").read_text())
    estimate = estimate_stage1_compute(canary, MANIFEST,
        available_memory_after_canary_bytes=7_207_804_928)
    assert estimate["frozen_configuration"]["machines"] == 28
    assert estimate["frozen_configuration"]["epochs"] == 50
    assert estimate["serial_components"]["xLSTMAD-R"] > estimate["serial_components"]["xLSTMAD-F"]
    assert estimate["serial_GB10_hours"] == pytest.approx(sum(estimate["serial_components"].values()))
    assert len(estimate["per_machine_fit_estimates"]["xlstmad_f"]) == 28
    assert estimate["concurrency"]["two_concurrent_fits_permitted_with_15pct_margin"] is False
    assert estimate["planning_contingency"]["serial_GB10_hours_with_contingency"] == pytest.approx(estimate["serial_GB10_hours"] * 1.25)
    assert estimate["disk"]["uncompressed_calibration_score_and_tail_reference_bytes"] > 0
    assert estimate["disk"]["uncompressed_scaler_artifact_bytes"] > 0
    assert estimate["disk"]["total_with_25pct_staging_margin_GiB"] == pytest.approx(0.672234327532351)
