"""Versioned Phase F-v4 runtime facade.

The accepted F-v3 implementation remains immutable.  This module binds its
frozen model/data primitives to a new report/checkpoint namespace and exposes
the F-v4 validity contract without changing the scientific operator.
"""
from __future__ import annotations

import json
from pathlib import Path

import torch
import phase_f_v3_common as v3

ROOT: Path = v3.ROOT
CONFIG = json.loads((ROOT / "configs/phase_f_v4.json").read_text())
BASE_CONFIG = json.loads((ROOT / "configs/phase_f_v3.json").read_text())
REPORT = ROOT / "reports/phase_f_v4"
# Prefixes, scalers, windows and shuffle orders are the sealed Phase-F inputs.
# They are intentionally not regenerated or copied into the v4 namespace.
DATA = v3.DATA

native = v3.native
PIN = v3.PIN
sha = v3.sha
tensor_hash = v3.tensor_hash
model_hash = v3.model_hash
recurrent_name = v3.recurrent_name
reconstruction_loss = v3.reconstruction_loss
score = v3.score
optimizer = v3.optimizer
forbid_native_predict = v3.forbid_native_predict
seed_all = v3.seed_all
canary_input = v3.canary_input


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def bind_legacy_globals() -> None:
    """Point the immutable v3 functions at the F4 output namespace.

    ``phase_f_v3_common`` functions close over module globals.  Binding only
    these paths/config values leaves the architecture, optimizer and input
    transformations unchanged while preventing any F3 artifact overwrite.
    """
    v3.CONFIG = BASE_CONFIG
    v3.REPORT = REPORT
    v3.DATA = DATA


def configure() -> dict:
    bind_legacy_globals()
    environment = v3.configure()
    environment["config_sha256"] = sha(ROOT / "configs/phase_f_v4.json")
    environment["phase_f_version"] = "v4"
    environment["validity_contract"] = "raw_output_partition_diagnostic_only"
    return environment


def build(architecture: str, seed: int):
    bind_legacy_globals()
    return v3.build(architecture, seed)


def verify_sealed_inputs() -> dict:
    bind_legacy_globals()
    sealed = v3.verify_sealed_inputs()
    sealed["phase_f_v4_config_sha256"] = sha(ROOT / "configs/phase_f_v4.json")
    sealed["input_namespace"] = "sealed data/phase_f; no regeneration"
    return sealed


def load_windows(fold: str):
    bind_legacy_globals()
    return v3.load_windows(fold)


def canary_input():
    bind_legacy_globals()
    generator = torch.Generator(device="cuda").manual_seed(CONFIG["canary"]["seed"])
    return torch.randn(*CONFIG["canary"]["shape"], device="cuda", generator=generator)


__all__ = [
    "ROOT", "CONFIG", "BASE_CONFIG", "REPORT", "DATA", "native", "PIN", "sha",
    "tensor_hash", "model_hash", "recurrent_name", "reconstruction_loss", "score",
    "optimizer", "forbid_native_predict", "seed_all", "write_json", "configure",
    "build", "verify_sealed_inputs", "load_windows", "canary_input",
]
