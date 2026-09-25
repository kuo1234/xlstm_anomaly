import numpy as np
import pytest
import json

from scripts import adaptive_normality_m1_data as data
from scripts import adaptive_normality_m1_execute as execute


def test_epoch_permutation_is_stable_and_seed_epoch_specific():
    a = execute.deterministic_order(100, 11, 0)
    b = execute.deterministic_order(100, 11, 0)
    c = execute.deterministic_order(100, 11, 1)
    np.testing.assert_array_equal(a, b)
    assert not np.array_equal(a, c)
    np.testing.assert_array_equal(np.sort(a), np.arange(100))


def test_fit_endpoint_counts_stop_at_fit_validation_boundary():
    n = 2000
    blocks = data.split_boundaries(n)
    assert execute._fit_endpoints("xlstmad_f", blocks.fit)[0] == data.W
    assert execute._fit_endpoints("xlstmad_f", blocks.fit)[-1] == blocks.fit[1] - 1
    assert execute._fit_endpoints("xlstmad_r", blocks.fit)[0] == data.W - 1
    assert execute._fit_endpoints("xlstmad_r", blocks.fit)[-1] == blocks.fit[1] - 1
    assert execute._validation_endpoints(blocks.validation)[0] == blocks.validation[0]
    assert execute._validation_endpoints(blocks.validation)[-1] == blocks.validation[1] - 1


def test_prediction_is_materialized_before_target_row_reaches_scoring_path():
    torch = execute._torch()
    matrix = np.arange(300 * data.D, dtype=np.float32).reshape(300, data.D)

    class ReadTrackedStream:
        def __init__(self, values):
            self.values = values
            self.target_reads = []

        def __len__(self):
            return len(self.values)

        def __getitem__(self, index):
            if isinstance(index, (int, np.integer)):
                self.target_reads.append(int(index))
            return self.values[index]

    stream = ReadTrackedStream(matrix)

    class ForwardBeforeTarget(torch.nn.Module):
        def forward(self, x):
            assert stream.target_reads == []
            assert x.shape[1:] == (data.W, data.D)
            return torch.zeros((len(x), data.D), dtype=x.dtype, device=x.device)

    prediction, target = execute.forecast_predictions_then_score(
        ForwardBeforeTarget(), stream, [256, 257], device="cpu", batch_size=2)
    assert stream.target_reads == [256, 257]
    assert prediction.shape == target.shape == (2, data.D)
    np.testing.assert_array_equal(target, matrix[[256, 257]])


def test_training_materialization_never_uses_validation_target_as_fit_endpoint():
    n = 2000
    blocks = data.split_boundaries(n)
    z = np.arange(n, dtype=np.int64)
    fit = execute._fit_endpoints("xlstmad_f", blocks.fit)
    validation = execute._validation_endpoints(blocks.validation)
    assert fit[-1] < blocks.validation[0]
    assert validation[0] == blocks.validation[0]
    assert _materialized_forecast_input(z, fit[-1]).max() < blocks.fit[1]
    assert _materialized_forecast_input(z, validation[0]).max() == validation[0] - 1


def _materialized_forecast_input(z, t):
    return z[int(t) - data.W:int(t)]


def test_validation_and_calibration_warmups_use_only_preceding_context():
    n = 2000
    blocks = data.split_boundaries(n)
    z = np.arange(n, dtype=np.int64)
    validation_t = execute._validation_endpoints(blocks.validation)[0]
    calibration_t = execute._validation_endpoints(blocks.calibration)[0]
    assert validation_t == blocks.validation[0]
    assert calibration_t == blocks.calibration[0]
    np.testing.assert_array_equal(_materialized_forecast_input(z, validation_t), z[validation_t-data.W:validation_t])
    np.testing.assert_array_equal(_materialized_forecast_input(z, calibration_t), z[calibration_t-data.W:calibration_t])
    assert _materialized_forecast_input(z, validation_t)[-1] == validation_t - 1
    assert _materialized_forecast_input(z, calibration_t)[-1] == calibration_t - 1


def test_test_warmup_has_exact_unpadded_context_from_zero_through_255():
    z = np.arange(400, dtype=np.int64)
    targets = data.test_forecast_targets(len(z))
    assert targets[0] == data.W
    assert targets[-1] == len(z) - 1
    np.testing.assert_array_equal(_materialized_forecast_input(z, int(targets[0])), z[:data.W])


def test_bounded_fit_uses_deterministic_fit_only_window_batches():
    torch = execute._torch()
    z = np.random.default_rng(17).normal(size=(320, data.D)).astype(np.float32)
    endpoints = execute._fit_endpoints("xlstmad_f", (0, 300))

    class TinyForecast(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.scale = torch.nn.Parameter(torch.tensor(0.5))

        def forward(self, x):
            return self.scale * x[:, -1, :]

    model = TinyForecast()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    order = execute.deterministic_order(len(endpoints), 11, 0)
    record = execute.run_epoch(model, optimizer, z, "xlstmad_f", endpoints,
        device="cpu", seed=11, epoch_zero_based=0, batch_size=16,
        max_batches=1, order=order)
    assert record["windows"] == 16
    assert record["optimizer_steps"] == 1
    assert record["complete_epoch"] is False
    assert np.isfinite(record["loss"])


def test_guard_path_matcher_only_flags_test_label_spellings():
    assert data._is_test_label_path("/some/root/machine-1-1_test_label.txt")
    assert data._is_test_label_path("ServerMachineDataset/test_label/machine-1-1.txt")
    assert not data._is_test_label_path("/some/root/machine-1-1_test.txt")
    assert not data._is_test_label_path("/some/root/machine-1-1_train.txt")


def test_machine_runner_passes_raw_train_to_calibration_and_persists_audit_artifacts(monkeypatch, tmp_path):
    rng = np.random.default_rng(29)
    train = rng.normal(size=(2000, data.D)).astype(np.float64)
    test = rng.normal(size=(300, data.D)).astype(np.float64)
    monkeypatch.setattr(data, "load_train", lambda machine, root=None: train)
    monkeypatch.setattr(data, "load_test", lambda machine, root=None: test)
    monkeypatch.setattr(execute, "_git_head", lambda repo=None: "a" * 40)
    monkeypatch.setattr(execute, "environment_record", lambda: {"test": "pinned"})
    checkpoints = []

    class Model:
        pass

    def fake_fit(z, bounds, arm, *, device, seed, checkpoint_path):
        assert checkpoint_path is not None
        checkpoint_path.write_bytes(f"checkpoint:{arm}".encode())
        checkpoints.append(checkpoint_path)
        return Model(), {
            "best_checkpoint": {"path": str(checkpoint_path), "sha256": "b" * 64, "bytes": checkpoint_path.stat().st_size},
            "arm": execute.ARM_NAMES[arm], "arm_key": arm, "seed": seed,
        }

    monkeypatch.setattr(execute, "fit_arm", fake_fit)
    calibration_seen = {}

    def fake_calibration(raw_train, transform, trained, *, device):
        calibration_seen["raw_train"] = raw_train
        assert raw_train is train
        threshold_scores = {name: np.arange(11, dtype=np.float64)
                            for name in execute.scores.STAGE1_SCORE_NAMES}
        return {
            "tail_references": {name: np.arange(10, dtype=np.float64)
                                for name in ("last_value", "moving_median", "var1", "r_native_window",
                                             "r_endpoint", "xlstmad_f")},
            "threshold_calibration_scores": threshold_scores,
            "thresholds": {name: 9.0 for name in threshold_scores},
            "threshold_quantile": {"q": 0.99, "method": "higher"},
            "threshold_timestamps": np.arange(100, 111, dtype=np.int64),
            "first_half_bounds": [100, 110], "second_half_bounds": [110, 121],
        }

    monkeypatch.setattr(execute, "calibration_fusions", fake_calibration)
    timestamps = np.arange(data.W, len(test), dtype=np.int64)
    monkeypatch.setattr(execute, "_machine_score_vectors",
                        lambda *args, **kwargs: ({"xlstmad_f": np.zeros(len(timestamps)),
                                                  "lstm_f": np.ones(len(timestamps))}, timestamps))
    monkeypatch.setattr(execute, "stage1_score_record",
                        lambda raw, times, refs, lstm: {"timestamps": times, "xlstmad_f": raw["xlstmad_f"]})

    output, record = execute.run_stage1_machine("machine-1-1", device="cpu", run_root=tmp_path)
    assert calibration_seen["raw_train"] is train
    assert len(output["timestamps"]) == len(timestamps)
    machine_dir = tmp_path / "machine-1-1"
    with np.load(machine_dir / "scaler.npz", allow_pickle=False) as saved:
        np.testing.assert_array_equal(saved["center"], record["scaler"]["center"])
        np.testing.assert_array_equal(saved["scale"], record["scaler"]["scale"])
    assert record["source_commit"] == "a" * 40
    assert len(record["calibration"]["thresholds"]) == 9
    assert record["calibration"]["artifact"]["sha256"]
    assert {path.name for path in checkpoints} == {f"{arm}.best.pt" for arm in execute.ARMS}
    for arm in execute.ARMS:
        persisted = json.loads((machine_dir / f"{arm}_run.json").read_text())
        assert persisted["source_commit"] == "a" * 40
        assert persisted["data_partitions"] == {"fit": [0, 1400], "validation": [1400, 1700],
                                                "calibration": [1700, 2000]}
        assert persisted["fit"]["best_checkpoint"]["path"].endswith(f"{arm}.best.pt")
        assert persisted["transform"]["artifact"]["sha256"]
        assert (machine_dir / f"{arm}.best.pt").is_file()
    with np.load(machine_dir / "calibration_scores.npz", allow_pickle=False) as saved:
        assert set(saved.files) >= {f"threshold_scores__{name}" for name in execute.scores.STAGE1_SCORE_NAMES}
        np.testing.assert_array_equal(saved["timestamps"], np.arange(100, 111))
    assert record["score_timestamp_bounds"] == [data.W, len(test)]


def test_stage1_machine_requires_persistent_run_root():
    with pytest.raises(execute.M1ExecutionError, match="persistent run_root"):
        execute.run_stage1_machine("machine-1-1", device="cpu")


def test_calibration_fits_tail_reference_and_higher_thresholds_on_disjoint_halves_only():
    torch = execute._torch()
    rng = np.random.default_rng(2027)
    train = rng.normal(size=(2000, data.D)).astype(np.float64)
    blocks = data.split_boundaries(len(train))
    transform = data.RobustScaler().fit(train, blocks.fit[1]).statistics
    assert transform is not None

    class Forecast(torch.nn.Module):
        def forward(self, x):
            return x[:, -1, :]

    class Reconstruction(torch.nn.Module):
        def forward(self, x):
            return x

    result = execute.calibration_fusions(
        train, transform,
        {"xlstmad_f": Forecast(), "lstm_f": Forecast(), "xlstmad_r": Reconstruction()},
        device="cpu",
    )
    assert set(result["thresholds"]) == set(execute.scores.STAGE1_SCORE_NAMES)
    assert "lstm_f" not in result["tail_references"]
    start, end = blocks.calibration
    half = (end - start) // 2
    assert result["first_half_bounds"] == [start, start + half]
    assert result["second_half_bounds"] == [start + half, end]
    np.testing.assert_array_equal(result["threshold_timestamps"], np.arange(start + half, end))
    for name in execute.scores.STAGE1_SCORE_NAMES:
        np.testing.assert_allclose(
            result["thresholds"][name],
            np.quantile(result["threshold_calibration_scores"][name], 0.99, method="higher"),
            rtol=0, atol=0,
        )
