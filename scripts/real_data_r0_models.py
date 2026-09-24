"""R0 D=38 detector builders and the sealed observation-only extraction path.

The sealed Phase F/E2 builders hard-code D=8.  This module is the audited
D-parameterised counterpart:

* :func:`build_xlstm_vanilla` is ``phase_f_common.build('xlstm')`` with
  ``features_no=38`` (same official xLSTMAD pin, float32 sLSTM dtypes, vanilla
  backend for training).
* :func:`build_xlstm_cuda` is ``mlstm_inference_canary.build_cuda`` with
  ``features_no=38`` (native CUDA sLSTM overlay used only for extraction;
  weights come from a vanilla model through ``map_vanilla_weights``).
* :class:`MatchedLSTMD` is the Phase F-v3 ``MatchedLSTM`` with the input/output
  dimension and width as parameters and the same module names, so the sealed
  ``phase_f_lstm_observer`` binds unchanged.  The observer replays width 38
  only, which is exactly the frozen R0 width.

No function here creates an optimizer, reads labels or computes a metric.
"""
from __future__ import annotations

import importlib.metadata
import inspect
import random
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import real_data_r0_data as r0data  # noqa: E402

CONFIG = r0data.CONFIG
DETECTOR = CONFIG["detector"]
D = r0data.D
W = r0data.W
EMBEDDING = 40
OBSERVER_LSTM_WIDTH = 38
PIN = "e8b56ba27352733bb83729e85b1d6196dca70c99"
OFFICIAL = ROOT / "data" / "phase_e2" / "official_xlstmad"
ATOL, RTOL = 1e-5, 1e-4
SLSTM_DTYPES = ("dtype", "dtype_b", "dtype_r", "dtype_w", "dtype_g", "dtype_s", "dtype_a")


# --------------------------------------------------------------------------- capacity rule (torch-free)


def lstm_parameter_count(width: int, d: int = D) -> int:
    """Trainable parameters of Linear(d,w) + 6 x nn.LSTM(w,w) + Linear(w,d)."""
    w = int(width)
    return (d * w + w) + 6 * (8 * w * w + 8 * w) + (w * d + d)


def select_lstm_width(target: int, d: int = D, low: int = 8, high: int = 256) -> dict[str, Any]:
    """Nearest parameter count to ``target``; exact tie -> smaller width; must be within +/-10%."""
    best = min(range(low, high + 1), key=lambda w: (abs(lstm_parameter_count(w, d) - target), w))
    count = lstm_parameter_count(best, d)
    relative = count / target - 1.0
    if abs(relative) > 0.10:
        raise r0data.ProtocolViolation("no LSTM width within +/-10% of the xLSTM parameter count")
    return {"width": best, "parameters": count, "relative_difference": relative,
            "neighbours": {str(w): lstm_parameter_count(w, d) for w in (best - 1, best + 1)}}


# --------------------------------------------------------------------------- torch runtime


def _torch():
    import torch

    return torch


def configure() -> dict[str, Any]:
    """Pin versions/backends exactly as the frozen R0 config (F-v3 backend state)."""
    torch = _torch()
    if importlib.metadata.version("xlstm") != "2.0.5" or importlib.metadata.version("lightning") != "2.6.1":
        raise r0data.ProtocolViolation("xlstm/lightning version drift")
    head = subprocess.check_output(["git", "-C", str(OFFICIAL), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(OFFICIAL), "status", "--porcelain"], text=True).strip()
    if head != PIN or dirty:
        raise r0data.ProtocolViolation("official xLSTMAD checkout is not the clean pinned commit")
    state = DETECTOR["backend_state"]
    torch.set_num_threads(int(state["torch_threads"]))
    torch.backends.cudnn.deterministic = bool(state["cudnn_deterministic"])
    torch.backends.cudnn.benchmark = bool(state["cudnn_benchmark"])
    torch.set_float32_matmul_precision(state["matmul_precision"])
    torch.backends.cuda.matmul.allow_tf32 = bool(state["matmul_allow_tf32"])
    torch.backends.cudnn.allow_tf32 = bool(state["cudnn_allow_tf32"])
    actual = {
        "cudnn_deterministic": torch.backends.cudnn.deterministic,
        "cudnn_benchmark": torch.backends.cudnn.benchmark,
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "matmul_precision": torch.get_float32_matmul_precision(),
        "matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
        "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
        "torch_threads": torch.get_num_threads(),
    }
    if actual != state:
        raise r0data.ProtocolViolation(f"backend state drift: {actual}")
    return {**actual, "torch": torch.__version__, "cuda": torch.version.cuda,
            "device": torch.cuda.get_device_name() if torch.cuda.is_available() else None,
            "official_xlstmad": head, "xlstm": "2.0.5", "lightning": "2.6.1", "python": sys.version.split()[0]}


def seed_all(seed: int) -> None:
    if int(seed) not in DETECTOR["seeds"]:
        raise r0data.ProtocolViolation("unregistered R0 detector seed")
    torch = _torch()
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def trainable_parameters(model) -> int:
    return int(sum(p.numel() for p in model.parameters() if p.requires_grad))


def _float32_factory(original, backend: str):
    def factory(*args, **kwargs):
        cfg = original(*args, **kwargs)
        if cfg.slstm_block.slstm.backend != backend:
            raise r0data.ProtocolViolation("unexpected sLSTM backend")
        for name in SLSTM_DTYPES:
            setattr(cfg.slstm_block.slstm, name, "float32")
        return cfg

    return factory


def _native():
    import phase_e2_common as e2  # inserts the pinned official checkout on sys.path

    if Path(e2.OFFICIAL).resolve() != OFFICIAL.resolve():
        raise r0data.ProtocolViolation("official xLSTMAD path mismatch")
    return e2.native


def build_xlstm_vanilla(seed: int, device: str = "cuda"):
    """Training/reference model: official xLSTMAD, features_no=38, vanilla float32."""
    native = _native()
    seed_all(seed)
    with patch.object(native, "create_config", _float32_factory(native.create_config, "vanilla")):
        model = native.xLSTMAD(embedding_dim=EMBEDDING, features_no=D, window_size=W, lr=0.001, slstm_backend="vanilla")
    if trainable_parameters(model) != DETECTOR["xlstm"]["trainable_parameters"]:
        raise r0data.ProtocolViolation("xLSTM D=38 parameter count drift")
    return model.float().to(device)


def build_xlstm_cuda():
    """Extraction-only native CUDA overlay with features_no=38 (weights must be mapped in)."""
    import mlstm_inference_canary as canary  # noqa: F401  (sets overlay/extension paths)

    # Prefer the fixture tracked in this checkout over the external overlay worktree.
    sys.path.insert(0, str(ROOT / "research" / "cuda_spark"))
    from slstm_cuda_fixture import install_loader

    import slstm_cuda_fixture

    if Path(slstm_cuda_fixture.__file__).resolve() != (ROOT / "research" / "cuda_spark" / "slstm_cuda_fixture.py").resolve():
        raise r0data.ProtocolViolation("unexpected sLSTM CUDA fixture module")
    native = _native()
    # Dedicated R0 build directory: never rewrites another line's shared JIT cache.
    install_loader(arch="121", code="sm_121", static_stub="false", rdc=False, extension_dir=slstm_extension_dir())
    import xlstm.blocks.slstm.cell as cell_mod

    cell_mod.sLSTMCellCUDA.mod.clear()
    original = native.create_config
    native.create_config = _float32_factory(original, "cuda")
    try:
        model = native.xLSTMAD(embedding_dim=EMBEDDING, features_no=D, window_size=W, lr=0.001, slstm_backend="cuda")
    finally:
        native.create_config = original
    if trainable_parameters(model) != DETECTOR["xlstm"]["trainable_parameters"]:
        raise r0data.ProtocolViolation("xLSTM CUDA overlay parameter count drift")
    return model.float().cuda()


def slstm_extension_dir() -> Path:
    import os

    return Path(os.environ.get("R0_SLSTM_EXTENSION_DIR", CONFIG["compute"]["slstm_extension_dir"]))


def cuda_overlay_from_vanilla(vanilla):
    import mlstm_inference_canary as canary

    model = build_xlstm_cuda()
    canary.map_vanilla_weights(vanilla, model)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    return model


def _matched_lstm_class():
    torch = _torch()

    class MatchedLSTMD(torch.nn.Module):
        """Phase F-v3 MatchedLSTM with D and width as parameters; identical module names."""

        def __init__(self, d: int = D, width: int = OBSERVER_LSTM_WIDTH):
            super().__init__()
            self.input_projection = torch.nn.Linear(d, width)
            self.encoder = torch.nn.ModuleList([torch.nn.LSTM(width, width, batch_first=True) for _ in range(3)])
            self.decoder = torch.nn.ModuleList([torch.nn.LSTM(width, width, batch_first=True) for _ in range(3)])
            self.gelu = torch.nn.GELU()
            self.output_projection = torch.nn.Linear(width, d)
            self.last_cudnn_enabled = None

        def forward(self, x):
            x = self.input_projection(x)
            with torch.backends.cudnn.flags(enabled=False, benchmark=False, deterministic=True, allow_tf32=False):
                self.last_cudnn_enabled = torch.backends.cudnn.enabled
                for layer in (*self.encoder, *self.decoder):
                    x, _ = layer(x)  # fresh zero h/c per window; never cross-window state
            return self.output_projection(self.gelu(x))

    return MatchedLSTMD


def build_lstm(seed: int, device: str = "cuda"):
    width = int(DETECTOR["lstm"]["width"])
    if width != OBSERVER_LSTM_WIDTH:
        raise r0data.ProtocolViolation("sealed LSTM observer replays width 38 only")
    seed_all(seed)
    model = _matched_lstm_class()(D, width)
    if trainable_parameters(model) != DETECTOR["lstm"]["trainable_parameters"]:
        raise r0data.ProtocolViolation("LSTM D=38 parameter count drift")
    return model.float().to(device)


def model_hash(model) -> str:
    import phase_e2_common as e2

    return e2.model_hash(model)


# --------------------------------------------------------------------------- extraction (observation-only)


def extract_batch(model, architecture: str, batch):
    """Score and common18 for one [B,64,38] batch through the sealed observers.

    ``architecture='xlstm'`` requires the CUDA overlay (fast observer);
    ``'xlstm_reference'`` uses the vanilla model with the parity-checked scalar
    reference observer; ``'lstm'`` uses the parity-checked manual replay.
    """
    torch = _torch()
    if architecture == "xlstm":
        from phase_e2_fast_observer import FastStateObserver

        with torch.no_grad(), FastStateObserver(model) as observer:
            output = model(batch)
            internal = observer.summary()
    elif architecture == "xlstm_reference":
        from phase_e2_observer import Observer

        with torch.no_grad(), Observer(model) as observer:
            output = model(batch)
            internal = observer.summary()
        if not all(c["hidden_close"] and c["state_close"] and c["finite"] and c["all_float32"] for c in observer.checks):
            raise r0data.ProtocolViolation("xLSTM scalar reference parity failed")
    elif architecture == "lstm":
        from phase_f_lstm_observer import Observer

        with torch.backends.cudnn.flags(enabled=False, benchmark=False, deterministic=True, allow_tf32=False):
            with torch.no_grad(), Observer(model) as observer:
                output = model(batch)
                internal = observer.summary()
        for row in observer.checks:
            if not all(v if isinstance(v, bool) else v["pass_"] for v in row["checks"].values()):
                raise r0data.ProtocolViolation("LSTM manual recurrence parity failed")
    else:
        raise r0data.ProtocolViolation("unregistered backbone")
    score = (output - batch).square().mean((1, 2))
    if internal.shape != (batch.shape[0], 18) or not bool(torch.isfinite(internal).all()) or not bool(torch.isfinite(score).all()):
        raise r0data.ProtocolViolation("invalid or non-finite score/common18")
    return output, score, internal


def extract_windows(model, architecture: str, windows: np.ndarray, batch_size: int = 128) -> dict[str, np.ndarray]:
    """Observation-only extraction over independent W64 windows (no labels in the signature)."""
    torch = _torch()
    x = np.asarray(windows, dtype=np.float32)
    if x.ndim != 3 or x.shape[1:] != (W, D):
        raise r0data.ProtocolViolation("windows must be [n, 64, 38] float32")
    before = model_hash(model)
    device = next(model.parameters()).device
    scores, bases = [], []
    for left in range(0, len(x), batch_size):
        batch = torch.from_numpy(np.ascontiguousarray(x[left : left + batch_size])).to(device)
        _output, score, internal = extract_batch(model, architecture, batch)
        scores.append(score.detach().cpu().numpy().astype(np.float64))
        bases.append(internal.detach().cpu().numpy().astype(np.float64))
    if model_hash(model) != before:
        raise r0data.ProtocolViolation("model mutated during extraction")
    return {"score": np.concatenate(scores), "internal_base18": np.concatenate(bases)}


FORBIDDEN_PARAMETER_NAMES = frozenset({"label", "labels", "y", "target", "targets", "anomaly", "truth"})


def observation_only_signatures() -> dict[str, list[str]]:
    """Parameter names of every model-facing entry point (audited to exclude labels)."""
    functions = (extract_batch, extract_windows, build_xlstm_vanilla, build_xlstm_cuda, build_lstm,
                 cuda_overlay_from_vanilla, r0data.load_observations, r0data.fit_scaler, r0data.apply_scaler,
                 r0data.window_matrix)
    return {f.__name__: list(inspect.signature(f).parameters) for f in functions}
