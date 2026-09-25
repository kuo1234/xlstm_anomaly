from scripts.adaptive_normality_m1_timing_canary import select_canary_machines, training_scope_record


def test_canary_selection_is_mechanical_from_train_lengths_only():
    selected = select_canary_machines()
    assert selected["train_rows_only"] is True
    assert [row["role"] for row in selected["selected"]] == [
        "shortest", "median_lower_rank", "longest"]
    assert [(row["train_rows"], row["machine"]) for row in selected["selected"]] == [
        (23687, "machine-3-4"), (23702, "machine-1-3"), (28743, "machine-2-6")]


def test_canary_tie_break_uses_machine_name_and_documented_lower_median_rank():
    values = [10, 10, 11, 12, 12] + [20] * 11 + [30] * 12
    machines = {f"m{i:02d}": {"train_rows": value} for i, value in enumerate(values)}
    chosen = select_canary_machines({"machines": machines})["selected"]
    assert chosen[0]["machine"] == "m00"
    assert chosen[1]["machine"] == "m13"  # sorted rank floor((28-1)/2) == 13
    assert chosen[2]["machine"] == "m27"


def test_completed_canary_report_distinguishes_canary_from_full_stage1_training():
    assert training_scope_record() == {
        "canary_training_started": True,
        "full_stage1_training_started": False,
    }
