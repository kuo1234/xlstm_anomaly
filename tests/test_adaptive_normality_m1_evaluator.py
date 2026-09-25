import hashlib
import json
import subprocess

import numpy as np
import pytest
from sklearn.metrics import average_precision_score, roc_auc_score

from scripts import adaptive_normality_m1_metrics as ev
from scripts import adaptive_normality_m1_data as m1_data
from scripts.adaptive_normality_m1_scores import STAGE1_MACHINES, STAGE1_SCORE_NAMES


def test_point_metrics_perfect_and_flat_detectors():
    y = np.array([0, 1, 0, 1], dtype=np.uint8)
    assert ev.average_precision(y, np.array([0, 1, 0, 1])) == 1.0
    assert ev.area_under_roc(y, np.array([0, 1, 0, 1])) == 1.0
    assert ev.average_precision(y, np.ones(4)) == pytest.approx(y.mean())
    assert ev.area_under_roc(y, np.ones(4)) == 0.5


def test_average_precision_and_auroc_match_sklearn_on_random_tied_scores():
    rng = np.random.default_rng(4107)
    y = rng.integers(0, 2, size=257, dtype=np.uint8)
    scores = np.round(rng.normal(size=len(y)), 1)
    assert ev.average_precision(y, scores) == pytest.approx(average_precision_score(y, scores), abs=1e-15)
    assert ev.area_under_roc(y, scores) == pytest.approx(roc_auc_score(y, scores), abs=1e-15)


def test_event_onset_boundaries_misses_fpr_and_recovery():
    # Alarm before event is ignored for onset; first alarm inside sets delay.
    y = np.array([0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0])
    s = np.zeros(len(y)); s[0] = 2; s[2] = 2; s[17] = 2
    r = ev.event_metrics(y, s, 1.0)
    assert r["event_detection_rate"] == 0.5
    assert r["onset_delay_by_event"] == [1, 2]  # alarm after the second event is ignored; miss is censored at length
    assert r["miss_fraction"] == 0.5
    assert r["normal_point_FPR"] == pytest.approx(2 / 16)
    assert r["false_alarm_points_per_10000_normal"] == pytest.approx(1250)
    assert r["false_alarm_runs_per_10000_normal"] == pytest.approx(1250)
    # Event 2 cannot reach ten normal points before test end: right censored.
    assert r["score_recovery_censoring"] == [False, True]
    assert r["score_recovery_censor_reason_by_event"] == [None, "test_end"]
    assert r["score_recovery_delay_by_event"] == [10, 3]


def test_missed_event_censored_onset_and_recovery_at_test_end():
    y = np.array([0, 0, 1, 1, 1, 0, 0])
    s = np.zeros(len(y))
    r = ev.event_metrics(y, s, 1)
    assert r["event_detection_rate"] == 0
    assert r["onset_delay_by_event"] == [3]
    assert r["miss_fraction"] == 1
    assert r["score_recovery_censoring"] == [True]
    assert r["score_recovery_censor_reason_by_event"] == ["test_end"]
    assert r["score_recovery_delay_by_event"] == [2]


def test_recovery_censor_reason_is_next_event_when_gap_is_too_short():
    y = np.array([1, 0, 1, 0, 0], dtype=np.uint8)
    result = ev.event_metrics(y, np.zeros(len(y)), 1.0)
    assert result["score_recovery_censoring"] == [True, True]
    assert result["score_recovery_censor_reason_by_event"] == ["next_event", "test_end"]


def test_metrics_equal_prevalence_and_oracle_identity():
    names = STAGE1_SCORE_NAMES
    y = np.array([0, 1, 0, 1, 0, 0], dtype=np.uint8)
    arrays = {name: np.ones(len(y)) for name in names}
    result = ev.evaluate_machine("synthetic", arrays, y, {name: 1 for name in names})
    assert result["scores"]["xlstmad_f"]["AP"] == pytest.approx(result["prevalence"])
    assert result["oracle_control_AP"] == pytest.approx(result["prevalence"])
    assert result["oracle_control_winner"] == "last_value"
    assert result["delta_AP_xlstmad_f"] == 0


def _machine_rows(delta_x=0.03, delta_fusion=0.03, delta_lstm=-0.01):
    rows = []
    for i, machine in enumerate(STAGE1_MACHINES):
        prev, base = .1, .3
        def score(ap, event=.7, fpr=.01):
            event_count = 10
            detected = round(event * event_count)
            missed = event_count - detected
            normals = 100
            false_points = round(fpr * normals)
            false_runs = min(false_points, round(false_points / 2))
            return {
                "AP": ap, "AUROC": .6, "AP_over_prevalence": ap / prev, "threshold": 1.0,
                "event_count": event_count, "event_detection_rate": detected / event_count,
                "detected_event_count": detected, "missed_event_count": missed,
                "onset_delay": 1.0, "onset_delay_by_event": [1] * event_count,
                "miss_fraction": missed / event_count, "normal_point_FPR": false_points / normals,
                "normal_point_count": normals, "false_alarm_point_count": false_points,
                "false_alarm_run_count": false_runs,
                "false_alarm_points_per_10000_normal": false_points * 10000 / normals,
                "false_alarm_runs_per_10000_normal": false_runs * 10000 / normals,
                "score_recovery_delay": 10.0, "score_recovery_censored_count": 0,
                "score_recovery_censoring": [False] * event_count,
                "score_recovery_censor_reason_by_event": [None] * event_count,
                "score_recovery_delay_by_event": [10] * event_count,
            }
        controls = {name: score(base) for name in ev.CONTROL_SCORE_NAMES}
        rows.append({"machine": machine, "prevalence": prev, "scores": {
            **controls, "xlstmad_f": score(base + delta_x),
            "forecast_control_fusion": score(base + delta_fusion),
            "control_fusion": score(base), "lstm_f": score(base + delta_lstm)},
            "oracle_control_AP": base, "oracle_control_winner": "last_value",
            "delta_AP_xlstmad_f": delta_x, "delta_AP_forecast_control_fusion": delta_fusion,
            "delta_AP_lstm_f": delta_lstm})
    return rows


def test_mechanical_routes_standalone_complement_both_fail_and_lstm_only():
    assert ev.decide_stage1(_machine_rows())["decision"] == "M1_STAGE1_PASS"
    assert ev.decide_stage1(_machine_rows(delta_x=-.01, delta_fusion=.03))["complement_route"]["passed"]
    assert ev.decide_stage1(_machine_rows(delta_x=-.01, delta_fusion=.03, delta_lstm=.03))["interpretation"] is None
    fail = ev.decide_stage1(_machine_rows(delta_x=-.01, delta_fusion=-.01))
    assert fail["decision"] == "FORECASTING_NOT_JUSTIFIED"
    lstm = ev.decide_stage1(_machine_rows(delta_x=-.01, delta_fusion=-.01, delta_lstm=.03))
    assert lstm["lstm_viability"] == "LSTM_FORECAST_VIABLE"
    assert lstm["interpretation"] == "ARCHITECTURE_AGNOSTIC_REFRAME_CANDIDATE"


def test_gate_win_count_and_delta_boundary():
    rows = _machine_rows(delta_x=.0199, delta_fusion=-.01)
    assert not ev.decide_stage1(rows)["standalone_route"]["gate_components"]["macro_delta_ap_ge_0_02"]
    rows = _machine_rows(delta_x=.02, delta_fusion=-.01)
    assert ev.decide_stage1(rows)["standalone_route"]["gate_components"]["macro_delta_ap_ge_0_02"]
    for row in rows[20:]:
        row["delta_AP_xlstmad_f"] = -.01
        row["scores"]["xlstmad_f"]["AP"] = .29
        row["scores"]["xlstmad_f"]["AP_over_prevalence"] = 2.9
    twenty_wins = ev.decide_stage1(rows)["standalone_route"]
    assert twenty_wins["positive_delta_machines"] == 20
    assert twenty_wins["gate_components"]["positive_delta_on_at_least_20"]
    rows[19]["delta_AP_xlstmad_f"] = -.01
    rows[19]["scores"]["xlstmad_f"]["AP"] = .29
    rows[19]["scores"]["xlstmad_f"]["AP_over_prevalence"] = 2.9
    result = ev.decide_stage1(rows)
    assert result["standalone_route"]["positive_delta_machines"] == 19
    assert not result["standalone_route"]["gate_components"]["positive_delta_on_at_least_20"]


def test_catastrophic_and_high_fpr_identities_are_reported():
    rows = _machine_rows(delta_x=.03, delta_fusion=-.01)
    rows[0]["scores"]["xlstmad_f"].update(
        AP=.1, AP_over_prevalence=1.0, event_detection_rate=.1,
        detected_event_count=1, missed_event_count=9, miss_fraction=.9,
        normal_point_FPR=.06, false_alarm_point_count=6, false_alarm_run_count=3,
        false_alarm_points_per_10000_normal=600.0,
        false_alarm_runs_per_10000_normal=300.0)
    rows[0]["delta_AP_xlstmad_f"] = -.2
    gate = ev.decide_stage1(rows)["standalone_route"]
    assert gate["catastrophic_machines"] == [STAGE1_MACHINES[0]]
    assert gate["high_fpr_machines"] == [STAGE1_MACHINES[0]]


def test_bootstrap_determinism_constant_zero_positive_and_mixed_sign():
    positive = ev.paired_machine_bootstrap(np.full(28, .02))
    replay = ev.paired_machine_bootstrap(np.full(28, .02))
    zero = ev.paired_machine_bootstrap(np.zeros(28))
    mixed = ev.paired_machine_bootstrap(np.r_[np.ones(14), -np.ones(14)])
    assert np.array_equal(positive["bootstrap_means"], replay["bootstrap_means"])
    assert positive["lower_95"] == positive["upper_95"] == pytest.approx(.02)
    assert zero["lower_95"] == zero["upper_95"] == 0
    assert mixed["lower_95"] < 0 < mixed["upper_95"]
    assert positive["samples"] == 10000 and positive["seed"] == 901


def test_synthetic_pinned_label_loader_and_rejections(tmp_path):
    data = b"0\n1\n0\n1\n"
    label = tmp_path / "synthetic_test_label.txt"
    with ev._sealed_metric_label_access():
        label.write_bytes(data)
    manifest = {"machines": {"synthetic": {"test_rows": 4,
        "test_label": {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "evaluator_only": True}}}}
    with pytest.raises(RuntimeError, match="forbidden"):
        ev.load_pinned_test_labels("synthetic", label, manifest=manifest, warmup=2)
    with ev._sealed_metric_label_access():
        loaded = ev.load_pinned_test_labels("synthetic", label, manifest=manifest, warmup=2)
    assert loaded["timestamps"].tolist() == [2, 3]
    assert loaded["labels"].tolist() == [0, 1]
    with pytest.raises(ValueError, match="SHA-256"):
        with ev._sealed_metric_label_access():
            ev.load_pinned_test_labels("synthetic", label, manifest={"machines": {"synthetic": {"test_rows": 4,
                "test_label": {"bytes": len(data), "sha256": "0" * 64, "evaluator_only": True}}}}, warmup=0)
    with pytest.raises(ValueError, match="exactly one binary"):
        with ev._sealed_metric_label_access():
            ev.load_pinned_test_labels("synthetic", label, manifest=manifest, expected_test_rows=3, warmup=0)
    bad = tmp_path / "synthetic_test_label.txt"
    bad_bytes = b"0\n2\n0\n1\n"
    with ev._sealed_metric_label_access():
        bad.write_bytes(bad_bytes)
    bad_manifest = {"machines": {"synthetic": {"test_rows": 4,
        "test_label": {"bytes": len(bad_bytes), "sha256": hashlib.sha256(bad_bytes).hexdigest(), "evaluator_only": True}}}}
    with pytest.raises(ValueError, match="binary"):
        with ev._sealed_metric_label_access():
            ev.load_pinned_test_labels("synthetic", bad, manifest=bad_manifest, warmup=0)


def test_unsealed_production_label_loader_rejects_before_path_operations(monkeypatch):
    touched = []
    original_stat, original_resolve = ev.Path.stat, ev.Path.resolve
    def stat(path, *args, **kwargs):
        touched.append(("stat", str(path)))
        return original_stat(path, *args, **kwargs)
    def resolve(path, *args, **kwargs):
        touched.append(("resolve", str(path)))
        return original_resolve(path, *args, **kwargs)
    monkeypatch.setattr(ev.Path, "stat", stat)
    monkeypatch.setattr(ev.Path, "resolve", resolve)
    with pytest.raises(RuntimeError, match="verified score and execution seals"):
        ev.load_pinned_test_labels(STAGE1_MACHINES[0], object())
    assert touched == []


def test_custom_manifest_cannot_authorize_pinned_machine_id(tmp_path):
    touched = []
    original_stat = ev.Path.stat
    def stat(path, *args, **kwargs):
        touched.append(str(path))
        return original_stat(path, *args, **kwargs)
    label = tmp_path / f"{STAGE1_MACHINES[0]}_test_label.txt"
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(ev.Path, "stat", stat)
    try:
        with pytest.raises(RuntimeError, match="synthetic machine IDs"):
            ev.load_pinned_test_labels(STAGE1_MACHINES[0], label,
                manifest={"machines": {STAGE1_MACHINES[0]: {"test_label": {"evaluator_only": True}}}})
        assert touched == []
    finally:
        monkeypatch.undo()


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_result_artifact_schema_is_deterministic_and_predeclared(tmp_path):
    y = np.array([0, 1, 0, 1], dtype=np.uint8)
    arrays = {name: np.array([0., 1., 0., 1.]) for name in STAGE1_SCORE_NAMES}
    thresholds = {name: 1.0 for name in STAGE1_SCORE_NAMES}
    machine_metrics = [ev.evaluate_machine(machine, arrays, y, thresholds)
                       for machine in STAGE1_MACHINES]
    gate = {"decision": "FORECASTING_NOT_JUSTIFIED"}
    access_log = {"real_SMD_test_label_reads": 0}
    docs = ev.result_artifact_documents(machine_metrics, gate, label_access_log=access_log)
    assert set(docs) == {ev.RESULTS_JSON_PATH.as_posix(), ev.GATE_PATH.as_posix(), ev.LABEL_ACCESS_LOG_PATH.as_posix()}
    assert docs[ev.LABEL_ACCESS_LOG_PATH.as_posix()]["real_SMD_test_label_reads"] == 0
    assert docs[ev.RESULTS_JSON_PATH.as_posix()]["summary"]["machine_count"] == 28
    assert set(docs[ev.RESULTS_JSON_PATH.as_posix()]["summary"]["per_score"]) == set(STAGE1_SCORE_NAMES)
    first = ev.write_result_artifacts(tmp_path, machine_metrics, gate, access_log)
    assert set(first) == {ev.RESULTS_JSON_PATH.as_posix(), ev.GATE_PATH.as_posix(),
                          ev.LABEL_ACCESS_LOG_PATH.as_posix(), ev.RESULTS_MD_PATH.as_posix()}
    assert all(path.is_file() for path in first.values())
    before = {path: path.read_bytes() for path in first.values()}
    with pytest.raises(FileExistsError, match="immutable"):
        ev.write_result_artifacts(tmp_path, machine_metrics, gate, access_log)
    assert {path: path.read_bytes() for path in first.values()} == before
    lock_path = tmp_path / "reports/adaptive_normality_m1_smd/.stage1_results.lock"
    lock_path.write_text("another publisher owns the lock")
    with pytest.raises(FileExistsError, match="already in progress"):
        ev.write_result_artifacts(tmp_path, machine_metrics, gate, access_log)
    assert {path: path.read_bytes() for path in first.values()} == before


def test_metric_entrypoint_requires_execution_manifest_before_callback(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir(); _git(repo, "init", "-q")
    paths = [repo / ev.STAGE1_SCORE_DIR / f"{m}.npz" for m in STAGE1_MACHINES]
    touched = []
    with pytest.raises(RuntimeError, match="inventory seal is missing"):
        ev.run_metric_entrypoint(score_artifacts=paths, repo=repo,
                                 label_loader=lambda: touched.append(True), metric_runner=lambda *_: None)
    assert touched == []


def test_gate_rejects_metric_vectors_that_are_not_exact_nine():
    with pytest.raises(ValueError, match="exact frozen nine"):
        ev.evaluate_machine("m", {"xlstmad_f": np.ones(2)}, np.array([0, 1]),
                             {"xlstmad_f": 1.0})


def _commit_all(repo, msg):
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", msg)


def _synthetic_execution_repo(tmp_path):
    from scripts.adaptive_normality_m1_scores import seal_stage1_machine_scores

    repo = tmp_path / "sealed-repo"; repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "evaluator@example.invalid")
    _git(repo, "config", "user.name", "Synthetic Evaluator")
    (repo / "README").write_text("source anchor\n")
    _commit_all(repo, "source anchor")
    source = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    machine_scores = {}
    for machine in STAGE1_MACHINES:
        test_rows = m1_data.MANIFEST["machines"][machine]["test_rows"]
        machine_scores[machine] = {"timestamps": np.arange(256, test_rows, dtype=np.int64),
            **{name: np.full(test_rows - 256, 0.2, dtype=np.float32) for name in STAGE1_SCORE_NAMES}}
    seal_stage1_machine_scores(repo, machine_scores)
    score_doc = json.loads((repo / ev.STAGE1_MANIFEST_PATH).read_text())
    entries = []
    ref_names = ev.TAIL_REFERENCE_NAMES
    for mi, machine in enumerate(STAGE1_MACHINES):
        directory = repo / "reports/adaptive_normality_m1_smd/stage1_execution" / machine
        directory.mkdir(parents=True)
        scaler_rel = (directory / "scaler.npz").relative_to(repo).as_posix()
        scaler_path = repo / scaler_rel
        np.savez(scaler_path, center=np.zeros(1))
        scaler_hash = ev._sha256(scaler_path)
        cal_rel = (directory / "calibration_scores.npz").relative_to(repo).as_posix()
        cal_path = repo / cal_rel
        train_rows = m1_data.MANIFEST["machines"][machine]["train_rows"]
        blocks = m1_data.split_boundaries(train_rows)
        cal_start, cal_stop = blocks.calibration
        half = max(1, (cal_stop - cal_start) // 2)
        cal_times = np.arange(cal_start + half, cal_stop, dtype=np.int64)
        arrays = {"timestamps": cal_times}
        arrays.update({f"tail_reference__{name}": np.full(half, .2, dtype=np.float64) for name in ref_names})
        arrays.update({f"threshold_scores__{name}": np.linspace(0., 1., len(cal_times)) for name in STAGE1_SCORE_NAMES})
        np.savez(cal_path, **arrays)
        cal_hash = ev._sha256(cal_path)
        thresholds = {name: float(np.quantile(arrays[f"threshold_scores__{name}"], .99, method="higher"))
                      for name in STAGE1_SCORE_NAMES}
        tail_hashes = {name: ev._array_sha256(arrays[f"tail_reference__{name}"]) for name in ref_names}
        tail_counts = {name: half for name in ref_names}
        model_hashes, checkpoints, arms = {}, {}, {}
        for arm in ("xlstmad_r", "xlstmad_f", "lstm_f"):
            digest = hashlib.sha256(f"model:{machine}:{arm}".encode()).hexdigest()
            ck_bytes = f"checkpoint:{machine}:{arm}".encode()
            ck_hash = hashlib.sha256(ck_bytes).hexdigest()
            ck_rel = f"external_checkpoints/{machine}_{arm}.pt"
            checkpoint_file = repo / ck_rel
            checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            checkpoint_file.write_bytes(ck_bytes)
            model_hashes[arm] = digest
            checkpoints[arm] = {"path": ck_rel, "sha256": ck_hash, "bytes": len(ck_bytes)}
            arms[arm] = {"fit": {"best_model_sha256": digest,
                "best_checkpoint": {"path": ck_rel, "sha256": ck_hash, "bytes": len(ck_bytes)},
                "labels_read": False, "test_observations_read": False}}
        run_rel = (directory / "run_record.json").relative_to(repo).as_posix()
        score_entry = score_doc["machines"][mi]
        record = {"schema": "adaptive-normality-m1-machine-run-v1", "machine": machine,
            "source_commit": source, "arms": arms,
            "scaler": {"artifact": {"path": scaler_rel, "sha256": scaler_hash}},
            "calibration": {"artifact": {"path": cal_rel, "sha256": cal_hash},
                "thresholds": thresholds, "threshold_quantile": {"q": .99, "method": "higher"},
                "tail_reference_counts": tail_counts,
                "first_half_bounds": [cal_start, cal_start + half],
                "second_half_bounds": [cal_start + half, cal_stop],
                "threshold_calibration_count": len(cal_times),
                "threshold_score_names": list(STAGE1_SCORE_NAMES)},
            "score_timestamp_sha256": score_entry["timestamp_sha256"],
            "test_labels_read": False, "anomaly_metrics_computed": False}
        (repo / run_rel).write_text(json.dumps(record, sort_keys=True) + "\n")
        entries.append({"machine": machine, "source_commit": source,
            "scaler_artifact": scaler_rel, "scaler_sha256": scaler_hash,
            "model_state_sha256": model_hashes, "model_checkpoints": checkpoints,
            "calibration_artifact": cal_rel, "calibration_artifact_sha256": cal_hash,
            "thresholds": thresholds, "threshold_quantile": {"q": .99, "method": "higher"},
            "tail_reference_hashes": tail_hashes, "tail_reference_counts": tail_counts,
            "score_artifact": score_entry["artifact"], "score_artifact_sha256": score_entry["sha256"],
            "timestamp_sha256": score_entry["timestamp_sha256"],
            "run_record": run_rel, "run_record_sha256": ev._sha256(repo / run_rel)})
    manifest = {"schema": ev.EXECUTION_SCHEMA, "machines": entries}
    path = repo / ev.EXECUTION_MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    _commit_all(repo, "synthetic complete score and execution seals")
    return repo, manifest, score_doc


def test_complete_execution_provenance_validates_synthetic_seal_and_detects_tamper(tmp_path):
    repo, manifest, score_doc = _synthetic_execution_repo(tmp_path)
    assert len(ev.verify_complete_execution_calibration_provenance(repo, score_doc)["machines"]) == 28
    # A post-seal threshold edit is rejected before any possible label loader.
    path = repo / ev.EXECUTION_MANIFEST_PATH
    doc = json.loads(path.read_text())
    doc["machines"][0]["thresholds"]["xlstmad_f"] = 0.9
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n")
    with pytest.raises(RuntimeError, match="must have the frozen schema and be committed"):
        ev.verify_complete_execution_calibration_provenance(repo, score_doc)


def test_tail_reference_length_is_bound_to_frozen_first_half_even_if_seal_is_updated(tmp_path):
    repo, manifest, score_doc = _synthetic_execution_repo(tmp_path)
    first = manifest["machines"][0]
    reference = ev.TAIL_REFERENCE_NAMES[0]
    cal_path = repo / first["calibration_artifact"]
    with np.load(cal_path, allow_pickle=False) as packed:
        arrays = {key: packed[key] for key in packed.files}
    arrays[f"tail_reference__{reference}"] = arrays[f"tail_reference__{reference}"][:-1]
    np.savez(cal_path, **arrays)
    first["calibration_artifact_sha256"] = ev._sha256(cal_path)
    first["tail_reference_counts"][reference] -= 1
    first["tail_reference_hashes"][reference] = ev._array_sha256(arrays[f"tail_reference__{reference}"])
    run_path = repo / first["run_record"]
    record = json.loads(run_path.read_text())
    record["calibration"]["artifact"]["sha256"] = first["calibration_artifact_sha256"]
    record["calibration"]["tail_reference_counts"] = first["tail_reference_counts"]
    run_path.write_text(json.dumps(record, sort_keys=True) + "\n")
    first["run_record_sha256"] = ev._sha256(run_path)
    (repo / ev.EXECUTION_MANIFEST_PATH).write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    _git(repo, "add", "-A"); _git(repo, "commit", "-qm", "consistently sealed truncated tail reference")
    with pytest.raises(RuntimeError, match="tail-reference count differs from frozen first-half"):
        ev.verify_complete_execution_calibration_provenance(repo, score_doc)


@pytest.mark.parametrize("malformation", ["cal_bounds", "cal_times", "test_times", "cal_count"])
def test_execution_provenance_rejects_malformed_boundary_artifacts(tmp_path, malformation):
    repo, manifest, score_doc = _synthetic_execution_repo(tmp_path)
    first = manifest["machines"][0]
    if malformation == "cal_bounds":
        record_path = repo / first["run_record"]
        record = json.loads(record_path.read_text())
        record["calibration"]["second_half_bounds"][0] += 1
        record_path.write_text(json.dumps(record, sort_keys=True) + "\n")
        first["run_record_sha256"] = ev._sha256(record_path)
        (repo / ev.EXECUTION_MANIFEST_PATH).write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        _git(repo, "add", "-A"); _git(repo, "commit", "-qm", "malformed calibration bounds")
    elif malformation in {"cal_times", "cal_count"}:
        cal_path = repo / first["calibration_artifact"]
        with np.load(cal_path, allow_pickle=False) as packed:
            arrays = {key: packed[key] for key in packed.files}
        if malformation == "cal_times":
            arrays["timestamps"] = arrays["timestamps"] + 1
        else:
            arrays["threshold_scores__last_value"] = arrays["threshold_scores__last_value"][:-1]
        np.savez(cal_path, **arrays)
        first["calibration_artifact_sha256"] = ev._sha256(cal_path)
        record_path = repo / first["run_record"]
        record = json.loads(record_path.read_text())
        record["calibration"]["artifact"]["sha256"] = ev._sha256(cal_path)
        record_path.write_text(json.dumps(record, sort_keys=True) + "\n")
        first["run_record_sha256"] = ev._sha256(record_path)
        (repo / ev.EXECUTION_MANIFEST_PATH).write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        _git(repo, "add", "-A"); _git(repo, "commit", "-qm", "malformed calibration arrays")
    else:
        score_path = repo / first["score_artifact"]
        with np.load(score_path, allow_pickle=False) as packed:
            arrays = {key: packed[key] for key in packed.files}
        arrays["timestamps"] = arrays["timestamps"].copy()
        arrays["timestamps"][0] += 1
        np.savez(score_path, **arrays)
        first["score_artifact_sha256"] = ev._sha256(score_path)
        first["timestamp_sha256"] = ev._array_sha256(arrays["timestamps"])
        record_path = repo / first["run_record"]
        record = json.loads(record_path.read_text())
        record["score_timestamp_sha256"] = first["timestamp_sha256"]
        record_path.write_text(json.dumps(record, sort_keys=True) + "\n")
        first["run_record_sha256"] = ev._sha256(record_path)
        score_entry = score_doc["machines"][0]
        score_entry["sha256"] = first["score_artifact_sha256"]
        score_entry["timestamp_sha256"] = first["timestamp_sha256"]
        (repo / ev.STAGE1_MANIFEST_PATH).write_text(json.dumps(score_doc, sort_keys=True, indent=2) + "\n")
        (repo / ev.EXECUTION_MANIFEST_PATH).write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        _git(repo, "add", "-A"); _git(repo, "commit", "-qm", "malformed test timestamps")
    with pytest.raises((RuntimeError, ValueError), match="calibration|timestamps|count|provenance"):
        ev.verify_complete_execution_calibration_provenance(repo, score_doc)


def test_changed_committed_run_record_bytes_rejected(tmp_path):
    repo, manifest, score_doc = _synthetic_execution_repo(tmp_path)
    run_path = repo / manifest["machines"][0]["run_record"]
    run_path.write_text(run_path.read_text() + " ")
    with pytest.raises(RuntimeError, match="run record must exist, match its committed hash"):
        ev.verify_complete_execution_calibration_provenance(repo, score_doc)


def test_metric_callback_waits_for_both_complete_committed_seals(tmp_path):
    repo, manifest, _ = _synthetic_execution_repo(tmp_path)
    paths = [repo / ev.STAGE1_SCORE_DIR / f"{machine}.npz" for machine in STAGE1_MACHINES]
    touched = []
    execution_path = repo / ev.EXECUTION_MANIFEST_PATH
    execution_path.write_text(execution_path.read_text() + " ")
    with pytest.raises(RuntimeError, match="execution/calibration manifest must have"):
        ev.run_metric_entrypoint(score_artifacts=paths, repo=repo,
                                 label_loader=lambda: touched.append("bad"), metric_runner=lambda *_: None)
    assert touched == []
    execution_path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    # Restore the committed bytes before the successful synthetic callback.
    _git(repo, "checkout", "--", ev.EXECUTION_MANIFEST_PATH.as_posix())
    result = ev.run_metric_entrypoint(score_artifacts=paths, repo=repo,
        label_loader=lambda: touched.append("authorized") or {"synthetic": True},
        metric_runner=lambda inventories, labels: (len(inventories[0]["machines"]), len(inventories[1]["machines"]), labels))
    assert touched == ["authorized"]
    assert result == (28, 28, {"synthetic": True})


def test_metric_entrypoint_opens_authorized_label_window_after_both_seals(tmp_path, monkeypatch):
    machine = STAGE1_MACHINES[0]
    label_bytes = (b"0\n" * 256) + b"1\n"
    label_path = tmp_path / f"{machine}_test_label.txt"
    with ev._sealed_metric_label_access():
        label_path.write_bytes(label_bytes)
    fake_manifest = {"machines": {machine: {"test_rows": 257,
        "test_label": {"bytes": len(label_bytes), "sha256": hashlib.sha256(label_bytes).hexdigest(),
                       "evaluator_only": True}}}}
    monkeypatch.setattr(ev.m1_data, "MANIFEST", fake_manifest)
    monkeypatch.setattr(ev.m1_data, "data_root", lambda: tmp_path)
    calls = []
    monkeypatch.setattr(ev, "verify_complete_stage1_score_inventory",
                        lambda repo: calls.append("inventory") or {"seal": "scores"})
    monkeypatch.setattr(ev, "verify_complete_execution_calibration_provenance",
                        lambda repo, inventory: calls.append("execution") or {"seal": "calibration"})
    with pytest.raises(RuntimeError, match="verified score and execution seals"):
        ev.load_pinned_test_labels(machine, label_path)

    score_paths = [tmp_path.resolve() / ev.STAGE1_SCORE_DIR / f"{name}.npz" for name in STAGE1_MACHINES]
    def label_loader():
        calls.append("labels")
        return ev.load_pinned_test_labels(machine, label_path)
    result = ev.run_metric_entrypoint(score_artifacts=score_paths, repo=tmp_path,
        label_loader=label_loader,
        metric_runner=lambda seals, labels: (seals, labels["timestamps"].tolist(), labels["labels"].tolist()))
    assert calls == ["inventory", "execution", "labels"]
    assert result == ([{"seal": "scores"}, {"seal": "calibration"}], [256], [1])
