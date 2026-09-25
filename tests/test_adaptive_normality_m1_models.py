import ast
import subprocess
import pytest

from scripts.adaptive_normality_m1_models import (
    D, W, EMBEDDING, build_lstm_f, build_xlstmad_f, build_xlstmad_r,
    count_parameters, seed_all, _official_source_checkout, _xlstm_config,
    HISTORICAL_F_COMMIT,
)


@pytest.mark.parametrize(
    "builder,expected",
    [(build_xlstmad_r, 75_934), (build_xlstmad_f, 80_510), (build_lstm_f, 81_838)],
)
def test_pinned_model_parameter_counts_and_synthetic_forward(builder, expected):
    import torch

    model = builder(seed=11, device="cpu")
    assert count_parameters(model) == expected
    model.eval()
    with torch.inference_mode():
        output = model(torch.zeros(2, W, D, dtype=torch.float32))
    assert output.shape == (2, W, D) if builder is build_xlstmad_r else output.shape == (2, D)
    assert torch.isfinite(output).all()


def test_model_initialization_is_seed_repeatable():
    import torch

    first = build_lstm_f(seed=2718)
    second = build_lstm_f(seed=2718)
    for left, right in zip(first.parameters(), second.parameters()):
        assert torch.equal(left, right)


def test_frozen_dimensions():
    assert (D, W, EMBEDDING) == (38, 256, 40)


def _historical_xlstmad_f_reference():
    """Load the historical model class from the pinned upstream git object."""
    import torch

    source = _official_source_checkout()
    raw = subprocess.check_output([
        "git", "-C", str(source), "show", f"{HISTORICAL_F_COMMIT}:models/xlstmad_pred.py"
    ], text=True)
    tree = ast.parse(raw)
    wanted = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))
              and node.name in {"create_config", "xLSTMModel"}]
    assert {node.name for node in wanted} == {"create_config", "xLSTMModel"}
    from scripts.adaptive_normality_m1_models import configure_runtime
    namespace = {"torch": torch, "nn": torch.nn,
                "xLSTMBlockStack": configure_runtime()["xLSTMBlockStack"]}
    exec(compile(ast.Module(body=wanted, type_ignores=[]), "pinned:models/xlstmad_pred.py", "exec"), namespace)
    # Only the backend/precision overlay is changed from the historical config.
    namespace["create_config"] = lambda window_size, features, embedding_dim=55: _xlstm_config(
        slstm_at=[1], float32=True
    )
    reference = namespace["xLSTMModel"](
        window_size=W, feats=D, lstm_embedding_dim=EMBEDDING, pred_len=1,
        num_layers=2, batch_size=2, device="cpu",
    )
    return reference


def test_forecaster_matches_historical_official_model_output():
    import torch

    port = build_xlstmad_f(seed=91).eval()
    reference = _historical_xlstmad_f_reference().eval()
    assert count_parameters(reference) == 80_510
    reference.load_state_dict(port.state_dict())
    x = torch.randn(2, W, D, generator=torch.Generator().manual_seed(10))
    with torch.inference_mode():
        got = port(x)
        expected = reference(x).squeeze(0)
    torch.testing.assert_close(got, expected, rtol=0, atol=0)


def test_forecast_architecture_and_fresh_window_state():
    import torch

    model = build_xlstmad_f(seed=91).eval()
    assert model.pred_len == 1
    assert len(model.lstm_encoder.blocks) == 3
    assert len(model.lstm_decoder.blocks) == 3
    assert model.lstm_encoder.config.embedding_dim == EMBEDDING
    assert model.lstm_decoder.config.embedding_dim == EMBEDDING
    assert model.lstm_encoder.config.slstm_at == [1]
    assert model.lstm_decoder.config.slstm_at == [1]
    x = torch.randn(1, W, D, generator=torch.Generator().manual_seed(11))
    with torch.inference_mode():
        alone = model(x)
        repeated = model(x)
        batched = model(torch.cat([x, x], dim=0))
    torch.testing.assert_close(alone, repeated, rtol=0, atol=0)
    torch.testing.assert_close(alone[0], batched[0], rtol=1e-6, atol=1e-7)
    torch.testing.assert_close(alone[0], batched[1], rtol=1e-6, atol=1e-7)


def test_data_and_score_contracts_do_not_normalize_windows_or_pad_scores():
    import inspect
    from scripts import adaptive_normality_m1_data as data
    from scripts import adaptive_normality_m1_scores as scores

    assert "mean" not in inspect.getsource(data.ForecastWindowDataset.__getitem__)
    assert "std" not in inspect.getsource(data.ForecastWindowDataset.__getitem__)
    assert "normalize" not in inspect.getsource(data.ForecastWindowDataset.__getitem__)
    # M1 scores are only formed for materialized eligible endpoints; the score
    # functions neither extend arrays nor synthesize warm-up values.
    assert "pad" not in inspect.getsource(scores.forecast_score).lower()
    assert "pad" not in inspect.getsource(scores.reconstruction_scores).lower()
    _, forecast_times = scores.forecast_score(
        __import__("numpy").ones((2, D)), __import__("numpy").zeros((2, D)), [256, 257]
    )
    assert forecast_times.tolist() == [256, 257]
