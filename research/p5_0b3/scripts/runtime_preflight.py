#!/usr/bin/env python3
"""Synthetic-only runtime determinism preflight for P5-0B3.

This deliberately does not load project data or any experiment artifacts. Its
only successful output is a compact JSON record; failures emit only a status.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import platform
from importlib.metadata import distributions

import numpy as np

PINNED_EFD_COMMIT = "ced470e1386066931bad32f3cb6e24bac9c5bb89"
SEED = 17
INPUT_DIM = 8
ENCODER = (32, 16)
BOTTLENECK = max(2, (INPUT_DIM + 3) // 4)
EPOCHS = 100
N_SAMPLES = 259
ATOL = 1e-7
RTOL = 1e-7
NUMPY_VERSION = "1.26.4"
TENSORFLOW_VERSION = "2.18.1"
PYTHON_VERSION = "3.12.3"
EFD_VERSION = "0.7.1"
RUNTIME_LOCK_SHA256 = "5cc46d5a1b2dc63dd4ec1f879babd337a97481f1af8595603ea9ed97ecfad9a5"


class PreflightFailure(Exception):
    """Internal control flow for a fail-closed preflight."""


def _fail_if(condition: bool) -> None:
    if condition:
        raise PreflightFailure


def _locked_package_versions(lock_path: Path) -> dict[str, str]:
    """Read exact package versions from the pinned requirements lock."""
    result: dict[str, str] = {}
    for raw_line in lock_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if " @ " in line:
            name, _url = line.split(" @ ", maxsplit=1)
            version = EFD_VERSION
        elif "==" in line:
            name, version = line.split("==", maxsplit=1)
        else:
            raise PreflightFailure
        normalized = name.lower().replace("_", "-").replace(".", "-")
        _fail_if(normalized in result or not version)
        result[normalized] = version
    return result


def _verify_installed_lock(lock_path: Path) -> None:
    expected = _locked_package_versions(lock_path)
    observed: dict[str, str] = {}
    for distribution in distributions():
        name = distribution.metadata.get("Name")
        if not name:
            raise PreflightFailure
        normalized = name.lower().replace("_", "-").replace(".", "-")
        _fail_if(normalized in observed)
        observed[normalized] = distribution.version
    _fail_if(observed != expected)


def _source_identity(source: Path) -> tuple[str, str, Path, str, str, str, str]:
    root = source.resolve()
    _fail_if(not root.is_dir())
    commit = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    _fail_if(commit != PINNED_EFD_COMMIT)
    tree = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD^{tree}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    pinned_tree = subprocess.run(
        ["git", "-C", str(root), "rev-parse", f"{PINNED_EFD_COMMIT}^{{tree}}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    _fail_if(not tree or tree != pinned_tree or bool(status.strip()))
    module = root / "energy_fault_detector" / "autoencoders" / "multilayer_autoencoder.py"
    core_module = root / "energy_fault_detector" / "core" / "autoencoder.py"
    _fail_if(not module.is_file() or not core_module.is_file())
    lock_path = Path(__file__).resolve().parents[1] / "runtime.lock"
    lock_sha256 = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    _fail_if(lock_sha256 != RUNTIME_LOCK_SHA256)
    _verify_installed_lock(lock_path)
    return (
        commit,
        hashlib.sha256(module.read_bytes()).hexdigest(),
        root,
        tree,
        lock_sha256,
        hashlib.sha256(core_module.read_bytes()).hexdigest(),
        str(module.resolve()),
    )


def _runtime_setup():
    # These must be in place before importing TensorFlow/Keras.
    _fail_if(os.environ.get("CUDA_VISIBLE_DEVICES") != "-1")
    _fail_if(os.environ.get("PYTHONHASHSEED") != str(SEED))
    os.environ["TF_DETERMINISTIC_OPS"] = "1"
    os.environ["TF_NUM_INTRAOP_THREADS"] = "1"
    os.environ["TF_NUM_INTEROP_THREADS"] = "1"
    import tensorflow as tf  # pylint: disable=import-outside-toplevel

    _fail_if(np.__version__ != NUMPY_VERSION)
    _fail_if(tf.__version__ != TENSORFLOW_VERSION)
    tf.config.threading.set_intra_op_parallelism_threads(1)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.experimental.enable_op_determinism()
    _fail_if(tf.config.list_physical_devices("GPU"))
    return tf


def _seed(tf) -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    tf.keras.utils.set_random_seed(SEED)


def _cpu_identity() -> list[str]:
    result = subprocess.run(
        ["lscpu"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    fields = ("Architecture:", "CPU(s):", "Vendor ID:", "Model name:",
              "Thread(s) per core:", "Core(s) per socket:", "Socket(s):")
    return [line.strip() for line in result.splitlines()
            if line.lstrip().startswith(fields)]


def _synthetic_input() -> np.ndarray:
    # A fixed synthetic partial-NaN array; no filesystem input.
    x = np.random.default_rng(SEED).normal(size=(N_SAMPLES, INPUT_DIM)).astype(np.float64)
    x[::19, 1] = np.nan
    x[7::23, 5] = np.nan
    return x


def _learning_rate_matches_contract(actual) -> bool:
    """Compare the optimizer value to the contract's float32 representation."""
    try:
        value = np.asarray(actual)
        return value.shape == () and np.float32(value) == np.float32(0.001)
    except (TypeError, ValueError, OverflowError):
        return False


def _assert_model_contract(model, autoencoder) -> None:
    _fail_if(tuple(autoencoder.layers) != ENCODER)
    _fail_if(autoencoder.code_size != BOTTLENECK)
    _fail_if(autoencoder.epochs != EPOCHS or autoencoder.batch_size != 128)
    _fail_if(autoencoder.loss_name != "mean_squared_error" or autoencoder.noise != 0.0)
    _fail_if(autoencoder.callbacks)
    expected_dense = [32, 16, 2, 16, 32, 8]
    dense = [layer for layer in model.layers if layer.__class__.__name__ == "Dense"]
    _fail_if([int(layer.units) for layer in dense] != expected_dense)
    _fail_if(any(layer.kernel_initializer.__class__.__name__ != "HeNormal" for layer in dense))
    _fail_if(any(layer.bias_initializer.__class__.__name__ != "Zeros" for layer in dense))
    _fail_if(any(layer.dtype_policy.name != "float32" for layer in model.layers))
    _fail_if(sum(layer.__class__.__name__ == "PReLU" for layer in model.layers) != 5)
    prelus = [layer for layer in model.layers if layer.__class__.__name__ == "PReLU"]
    _fail_if(any(layer.shared_axes is not None for layer in prelus))
    _fail_if(any(layer.alpha_initializer.__class__.__name__ != "Zeros" for layer in prelus))
    _fail_if(model.layers[-1].activation.__name__ != "linear")
    optimizer = model.optimizer
    _fail_if(optimizer.__class__.__name__ != "Adam")
    _fail_if(not _learning_rate_matches_contract(optimizer.learning_rate.numpy()))
    _fail_if(float(optimizer.beta_1) != 0.9 or float(optimizer.beta_2) != 0.999)
    _fail_if(float(optimizer.epsilon) != 1e-7)
    _fail_if(bool(optimizer.amsgrad))
    _fail_if(getattr(optimizer, "weight_decay", None) is not None)


def _one_run(tf, model_class, x: np.ndarray) -> np.ndarray:
    _seed(tf)
    ae = model_class(
        layers=list(ENCODER),
        code_size=BOTTLENECK,
        kernel_initializer="he_normal",
        act="prelu",
        last_act="linear",
        learning_rate=0.001,
        batch_size=128,
        epochs=EPOCHS,
        loss_name="mean_squared_error",
        early_stopping=False,
        verbose=0,
    )
    ae.fit(x, x_val=None, shuffle=False)
    _fail_if(ae.epochs_completed != EPOCHS)
    _assert_model_contract(ae.model, ae)
    rebuilt = np.asarray(ae.predict(x), dtype=np.float32)
    scores = np.sqrt(np.mean(np.square(x - rebuilt), axis=1)).astype(np.float32)
    _fail_if(scores.shape != (N_SAMPLES,) or not np.isfinite(scores).all())
    return scores


def run(source: Path) -> dict:
    _fail_if(platform.python_implementation() != "CPython")
    _fail_if(platform.python_version() != PYTHON_VERSION)
    (commit, model_code_sha256, source_root, source_tree, lock_sha256,
     core_code_sha256, expected_module_path) = _source_identity(source)
    tf = _runtime_setup()
    sys.path.insert(0, str(source_root))
    import energy_fault_detector  # pylint: disable=import-outside-toplevel
    from energy_fault_detector.autoencoders import multilayer_autoencoder  # pylint: disable=import-outside-toplevel
    from energy_fault_detector.autoencoders.multilayer_autoencoder import (  # pylint: disable=import-outside-toplevel
        MultilayerAutoencoder,
    )
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from energy_fault_detector import __version__ as efd_version  # pylint: disable=import-outside-toplevel
    from preprocessing import MedianImputeStandardScaler  # pylint: disable=import-outside-toplevel

    _fail_if(MultilayerAutoencoder.__module__ != "energy_fault_detector.autoencoders.multilayer_autoencoder")
    _fail_if(Path(multilayer_autoencoder.__file__).resolve() != Path(expected_module_path))
    expected_core_module = (source_root / "energy_fault_detector" / "core" / "autoencoder.py").resolve()
    from energy_fault_detector.core import autoencoder as core_autoencoder  # pylint: disable=import-outside-toplevel
    _fail_if(Path(core_autoencoder.__file__).resolve() != expected_core_module)
    _fail_if(Path(energy_fault_detector.__file__).resolve().parent !=
             (source_root / "energy_fault_detector").resolve())
    _fail_if(efd_version != EFD_VERSION)
    _fail_if(tf.keras.mixed_precision.global_policy().name != "float32")
    _fail_if(tf.config.list_logical_devices("GPU"))
    _fail_if(not tf.config.list_logical_devices("CPU"))
    raw1 = _synthetic_input()
    raw2 = _synthetic_input()
    _fail_if(raw1.tobytes() != raw2.tobytes())
    x1 = MedianImputeStandardScaler().fit(raw1).transform(raw1)
    x2 = MedianImputeStandardScaler().fit(raw2).transform(raw2)
    _fail_if(x1.dtype != np.float32 or x1.tobytes() != x2.tobytes())
    score1 = _one_run(tf, MultilayerAutoencoder, x1)
    score2 = _one_run(tf, MultilayerAutoencoder, x2)
    _fail_if(not np.allclose(score1, score2, atol=ATOL, rtol=RTOL))
    delta = np.abs(score1.astype(np.float64) - score2.astype(np.float64))
    denominator = np.maximum(np.maximum(np.abs(score1), np.abs(score2)), np.finfo(np.float64).tiny)
    max_abs_delta = float(np.max(delta))
    max_rel_delta = float(np.max(delta / denominator))
    _fail_if(tf.config.threading.get_intra_op_parallelism_threads() != 1)
    _fail_if(tf.config.threading.get_inter_op_parallelism_threads() != 1)
    return {
        "status": "PASS",
        "code": {
            "efd_commit": commit,
            "efd_git_tree": source_tree,
            "multilayer_autoencoder_sha256": model_code_sha256,
            "core_autoencoder_sha256": core_code_sha256,
            "multilayer_autoencoder_path": str(Path(multilayer_autoencoder.__file__).resolve()),
            "core_autoencoder_path": str(Path(core_autoencoder.__file__).resolve()),
            "package_version": efd_version,
            "python": platform.python_version(),
            "python_full_version": sys.version,
            "runtime_lock_sha256": lock_sha256,
        },
        "runtime": {
            "tensorflow": tf.__version__,
            "keras": __import__("keras").__version__,
            "numpy": np.__version__,
            "platform": platform.platform(),
            "kernel_release": platform.release(),
            "libc": list(platform.libc_ver()),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_topology": _cpu_identity(),
            "cpu_count": os.cpu_count(),
            "device": "CPU",
            "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"],
            "deterministic_ops": True,
            "intra_threads": 1,
            "inter_threads": 1,
        },
        "result": {
            "seed": SEED,
            "synthetic_shape": list(x1.shape),
            "epochs_per_run": EPOCHS,
            "runs": 2,
            "score_count": int(score1.size),
            "scores_allclose_atol_rtol": ATOL,
            "max_absolute_score_delta": max_abs_delta,
            "max_relative_score_delta": max_rel_delta,
            "preprocessed_arrays_byte_identical": True,
        },
    }


def main() -> int:
    try:
        source = Path(os.environ.get("P5_EFD_SOURCE", "/tmp/p5-efd-v071"))
        record = run(source)
    except Exception:  # Fail closed without leaking values or traces.
        print(json.dumps({"status": "BLOCKED"}, separators=(",", ":")))
        return 1
    print(json.dumps(record, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
