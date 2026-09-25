"""Pinned, result-blind model constructors for adaptive-normality M1.

The forecasting stack follows the historical xLSTMAD forecasting implementation
(``models/xlstmad_pred.py`` at 3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6).
The reconstruction stack follows the official reconstruction implementation
(``xlstmad.py`` at e8b56ba27352733bb83729e85b1d6196dca70c99).
"""
from __future__ import annotations

import random
import importlib.util
import os
import subprocess
import tempfile
from pathlib import Path

D = 38
W = 256
EMBEDDING = 40
FORECAST_SLSTM_AT = [1]
EXPECTED_PARAMETERS = {"xlstmad_r": 75_934, "xlstmad_f": 80_510, "lstm_f": 81_838}
OFFICIAL_R_COMMIT = "e8b56ba27352733bb83729e85b1d6196dca70c99"
HISTORICAL_F_COMMIT = "3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6"
OFFICIAL_R_URL = "https://github.com/Nyderx/xlstmad.git"


def configure_runtime():
    """Import and return torch and xLSTM primitives from the pinned environment."""
    import torch
    from xlstm import (
        FeedForwardConfig, mLSTMBlockConfig, mLSTMLayerConfig,
        sLSTMBlockConfig, sLSTMLayerConfig, xLSTMBlockStack,
        xLSTMBlockStackConfig,
    )

    return {
        "torch": torch,
        "FeedForwardConfig": FeedForwardConfig,
        "mLSTMBlockConfig": mLSTMBlockConfig,
        "mLSTMLayerConfig": mLSTMLayerConfig,
        "sLSTMBlockConfig": sLSTMBlockConfig,
        "sLSTMLayerConfig": sLSTMLayerConfig,
        "xLSTMBlockStack": xLSTMBlockStack,
        "xLSTMBlockStackConfig": xLSTMBlockStackConfig,
    }


def seed_all(seed: int) -> None:
    """Seed Python, NumPy, and PyTorch before model construction."""
    import numpy as np
    torch = configure_runtime()["torch"]
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def count_parameters(model) -> int:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


def _xlstm_config(*, slstm_at, float32: bool):
    api = configure_runtime()
    layer = api["sLSTMLayerConfig"](
        backend="vanilla", num_heads=4, conv1d_kernel_size=4,
        bias_init="powerlaw_blockdependent", embedding_dim=EMBEDDING,
    )
    if float32:
        for field in ("dtype", "dtype_b", "dtype_r", "dtype_w", "dtype_g", "dtype_s", "dtype_a"):
            setattr(layer, field, "float32")
        layer.enable_automatic_mixed_precision = False
    return api["xLSTMBlockStackConfig"](
        mlstm_block=api["mLSTMBlockConfig"](
            mlstm=api["mLSTMLayerConfig"](
                conv1d_kernel_size=8, qkv_proj_blocksize=5, num_heads=4,
                round_proj_up_dim_up=False, round_proj_up_to_multiple_of=5,
                embedding_dim=EMBEDDING,
            )
        ),
        slstm_block=api["sLSTMBlockConfig"](
            slstm=layer,
            feedforward=api["FeedForwardConfig"](
                proj_factor=1.3, act_fn="gelu", embedding_dim=EMBEDDING,
            ),
        ),
        context_length=W, num_blocks=3, embedding_dim=EMBEDDING,
        slstm_at=list(slstm_at),
    )


def _check_count(model, arm: str):
    observed = count_parameters(model)
    expected = EXPECTED_PARAMETERS[arm]
    if observed != expected:
        raise RuntimeError(f"{arm} parameter count {observed} != frozen {expected}; refusing to proceed")
    return model


def _official_source_checkout() -> Path:
    """Find or create a clean checkout containing both pinned upstream commits."""
    configured = os.environ.get("M1_XLSTMAD_SOURCE")
    cache = Path(tempfile.gettempdir()) / "adaptive_normality_m1_xlstmad_source"
    source = Path(configured).expanduser().resolve() if configured else cache
    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--quiet", OFFICIAL_R_URL, str(source)], check=True)
        subprocess.run(["git", "-C", str(source), "checkout", "--quiet", OFFICIAL_R_COMMIT], check=True)
    try:
        head = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
        dirty = subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"], text=True)
        subprocess.run(["git", "-C", str(source), "cat-file", "-e", f"{HISTORICAL_F_COMMIT}^{{commit}}"], check=True, stdout=subprocess.DEVNULL)
        official_blob = subprocess.check_output(["git", "-C", str(source), "show", f"{OFFICIAL_R_COMMIT}:xlstmad.py"])
        checked_file = (source / "xlstmad.py").read_bytes()
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError("cannot verify pinned official xLSTMAD source checkout") from error
    if head != OFFICIAL_R_COMMIT or dirty:
        raise RuntimeError(f"official xLSTMAD source must be clean at {OFFICIAL_R_COMMIT}; found {head}")
    if checked_file != official_blob:
        raise RuntimeError("official xlstmad.py working file differs from the pinned commit blob")
    return source


def _load_official_r_module():
    """Dynamically load xlstmad.py only after verifying its clean pinned checkout."""
    source = _official_source_checkout()
    path = source / "xlstmad.py"
    name = f"_m1_official_xlstmad_{OFFICIAL_R_COMMIT[:12]}"
    cached = __import__("sys").modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to create loader for pinned xlstmad.py")
    module = importlib.util.module_from_spec(spec)
    __import__("sys").modules[name] = module
    spec.loader.exec_module(module)
    return module


def build_xlstmad_r(seed: int = 11, device="cpu"):
    """Instantiate the pinned official xLSTMAD class with the audited config."""
    seed_all(seed)
    module = _load_official_r_module()
    original_create_config = module.create_config

    def frozen_config(window_size, embedding_dim=55, backend="cuda"):
        if (window_size, embedding_dim, backend) != (W, EMBEDDING, "vanilla"):
            raise RuntimeError("M1 xLSTMAD-R requires pinned W/E and vanilla sLSTM backend")
        return _xlstm_config(slstm_at=[0, 1], float32=True)

    module.create_config = frozen_config
    try:
        model = module.xLSTMAD(embedding_dim=EMBEDDING, features_no=D, window_size=W,
                               slstm_backend="vanilla").to(device)
    finally:
        module.create_config = original_create_config
    return _check_count(model, "xlstmad_r")


def build_xlstmad_f(seed: int = 11, device="cpu"):
    """Historical xLSTMAD-F one-step encoder/decoder port, without score padding."""
    torch = configure_runtime()["torch"]
    seed_all(seed)
    stack = configure_runtime()["xLSTMBlockStack"]
    cfg = _xlstm_config(slstm_at=FORECAST_SLSTM_AT, float32=True)

    class XLSTMADF(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.pred_len = 1
            self.encoder_projection = torch.nn.Linear(D, EMBEDDING)
            self.lstm_encoder = stack(cfg)
            self.lstm_decoder = stack(cfg)
            self.relu = torch.nn.GELU()
            self.fc = torch.nn.Linear(EMBEDDING, D)

        def forward(self, src):
            if src.ndim != 3 or src.shape[1:] != (W, D):
                raise ValueError(f"expected (batch,{W},{D}), got {tuple(src.shape)}")
            # Historical implementation: encode the context, then decode the last
            # encoder state for exactly pred_len=1 and project that point to D.
            encoded = self.lstm_encoder(self.encoder_projection(src))
            one_step = encoded[:, -1:, :]
            decoded = self.lstm_decoder(one_step)
            return self.fc(self.relu(decoded[:, -1, :]))

    return _check_count(XLSTMADF().to(device), "xlstmad_f")


def build_lstm_f(seed: int = 11, device="cpu"):
    """Frozen capacity-matched recurrent one-step forecasting control."""
    torch = configure_runtime()["torch"]
    seed_all(seed)

    class LSTMF(torch.nn.Module):
        def __init__(self):
            super().__init__()
            # The frozen control uses three one-layer encoder LSTMs and three
            # one-layer decoder LSTMs, all width 40, with fresh zero states.
            self.input_projection = torch.nn.Linear(D, EMBEDDING)
            self.encoder = torch.nn.ModuleList(
                torch.nn.LSTM(EMBEDDING, EMBEDDING, num_layers=1, batch_first=True)
                for _ in range(3)
            )
            self.decoder = torch.nn.ModuleList(
                torch.nn.LSTM(EMBEDDING, EMBEDDING, num_layers=1, batch_first=True)
                for _ in range(3)
            )
            self.gelu = torch.nn.GELU()
            self.output_projection = torch.nn.Linear(EMBEDDING, D)

        def forward(self, x):
            if x.ndim != 3 or x.shape[1:] != (W, D):
                raise ValueError(f"expected (batch,{W},{D}), got {tuple(x.shape)}")
            h = self.input_projection(x)
            for layer in self.encoder:
                h, _ = layer(h)
            h = h[:, -1:, :]
            for layer in self.decoder:
                h, _ = layer(h)
            return self.output_projection(self.gelu(h[:, -1, :]))

    return _check_count(LSTMF().to(device), "lstm_f")
