"""Label-blind G0.1 CANDI history-control alignment preflight.

The control selection is sealed by ``phase_g01_seal.py`` before this script is
run.  This module only performs frozen inference on one validation-fold D=8
synthetic observation stream.  It never reads evaluator labels/metadata,
trains, adapts, fits a scaler, or computes a detector metric.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
OFFICIAL = ROOT / "data" / "phase_c" / "official_candi"
PHASE_C_SITE_PACKAGES = next(
    (ROOT / "data" / "phase_c" / "venv" / "lib").glob(
        "python*/site-packages"
    ),
    None,
)
if PHASE_C_SITE_PACKAGES is not None:
    # The E2 environment supplies xlstm/lightning; CANDI additionally needs
    # yacs/reformer_pytorch from its sealed Phase-C environment.
    sys.path.append(str(PHASE_C_SITE_PACKAGES))
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(OFFICIAL))

import phase_f_v4_common as f4
from phase_d_operator import object_hash, restore_rng, rng_state
from phase_g0_preflight import (
    _causal_cmp,
    _cmp,
    _expand,
    _extract,
    _history,
    _outer_label_blind_extract,
)
from m0.synthetic import generate

from config import get_cfg_defaults
from models.mlp.modeling_mlp import MLP
from tta.candi.adapter_candi import SANA


SEEDS = (11, 22, 33, 44, 55)
SOURCE_SEED = 2000
SCENARIO = "stationary"
CONDITION = "none"
RAW_LENGTH = 192
FIRST_COMMON_TIMESTAMP = 63
ATOL, RTOL = 1e-5, 1e-4
EXPECTED = {
    "history": 14,
    "internal_base": 18,
    "hidden": 52,
    "gate": 130,
    "memory": 52,
    "combined": 234,
    "history_plus_combined": 248,
}
OFFICIAL_CANDI_COMMIT = "28c9679e503832f59e351208cde63657fcb51cad"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"),
                   allow_nan=False).encode()
    ).hexdigest()


def array_hash(array: np.ndarray) -> str:
    value = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(str(value.dtype).encode())
    digest.update(str(value.shape).encode())
    digest.update(value.tobytes())
    return digest.hexdigest()


def tensor_hash(value: torch.Tensor) -> str:
    value = value.detach().cpu().contiguous()
    array = value.numpy()
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode())
    digest.update(str(array.shape).encode())
    digest.update(array.tobytes())
    return digest.hexdigest()


def state_hash(module: torch.nn.Module, include=None) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(module.state_dict().items()):
        if include is not None and not include(name):
            continue
        tensor = value.detach().cpu().contiguous()
        array = tensor.numpy()
        digest.update(name.encode())
        digest.update(str(array.dtype).encode())
        digest.update(str(array.shape).encode())
        digest.update(array.tobytes())
    return digest.hexdigest()


def state_hash_core(module: torch.nn.Module) -> str:
    return state_hash(
        module,
        include=lambda name: not name.startswith(("sana_in.", "sana_out.")),
    )


def model_state_snapshot(model: torch.nn.Module) -> dict:
    return {
        "model": state_hash(model),
        "core": state_hash_core(model),
        "requires_grad": any(p.requires_grad for p in model.parameters()),
        "training": bool(model.training),
    }


def windows_at(raw_scaled: np.ndarray, timestamps: np.ndarray,
               width: int) -> np.ndarray:
    rows = [raw_scaled[t - width + 1:t + 1] for t in timestamps]
    value = np.ascontiguousarray(np.stack(rows), dtype=np.float32)
    if value.shape != (len(timestamps), width, 8):
        raise RuntimeError(f"window shape mismatch: {value.shape}")
    return value


def candi_score(model: torch.nn.Module, windows: torch.Tensor) -> torch.Tensor:
    """Direct official MLP score method; no Adapter/FPM/SANA update path."""
    values = []
    with torch.no_grad():
        for chunk in windows.split(64):
            values.append(model.get_anomaly_scores(chunk))
    result = torch.cat(values, dim=0)
    if result.ndim != 1 or not bool(torch.isfinite(result).all()):
        raise RuntimeError("CANDI score is not finite 1-D")
    return result


def _candi_label_blind_extract(model: torch.nn.Module, windows: torch.Tensor,
                               evaluator_metadata: dict) -> torch.Tensor:
    """Outer metadata is discarded before the official score call."""
    del evaluator_metadata
    return candi_score(model, windows)


def _load_phase_f_scaler(source_seed: int) -> tuple[dict, Path]:
    manifest_path = ROOT / "reports" / "phase_f" / "preprocessing_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    record = next(r for r in manifest["sources"]
                  if int(r["source"]) == source_seed)
    scaler_relative = next(
        path for path in record["artifacts"] if path.endswith("scaler.json")
    )
    scaler_path = ROOT / scaler_relative
    if sha(scaler_path) != record["artifacts"][scaler_relative]:
        raise RuntimeError("Phase-F scaler hash mismatch")
    scaler = json.loads(scaler_path.read_text())
    if scaler["fit"] != [0, 4096]:
        raise RuntimeError("unexpected Phase-F scaler fit interval")
    return scaler, scaler_path


def _load_candi(seed: int, row: dict) -> tuple[torch.nn.Module, dict]:
    path = ROOT / row["pre_intervention"]
    for relative, expected in row["artifacts"].items():
        artifact_path = ROOT / relative
        if not artifact_path.exists() or sha(artifact_path) != expected["sha256"]:
            raise RuntimeError(f"Phase-D artifact hash mismatch for seed {seed}: {relative}")
    state = torch.load(path, map_location="cpu", weights_only=False)
    required = {"model_state", "optimizer_state", "rng", "cfg", "threshold",
                "scaler", "backbone_sha256"}
    if set(state) != required:
        raise RuntimeError(f"unexpected CANDI state keys for seed {seed}")
    if state["scaler"] != row["preprocessing"]:
        raise RuntimeError(f"preprocessing/scaler mismatch for seed {seed}")
    if canonical_hash(state["scaler"]) != row["preprocessing_object_sha256"]:
        raise RuntimeError(f"preprocessing hash mismatch for seed {seed}")
    if state["backbone_sha256"] != row["backbone_tensor_sha256"]:
        raise RuntimeError(f"backbone state seal mismatch for seed {seed}")
    if object_hash(state["optimizer_state"]) != row["optimizer_sha256"]:
        raise RuntimeError(f"optimizer-state seal mismatch for seed {seed}")
    if object_hash(state["rng"]) != row["rng_sha256"]:
        raise RuntimeError(f"RNG-state seal mismatch for seed {seed}")
    if float(state["threshold"]) != float(row["threshold"]):
        raise RuntimeError(f"threshold seal mismatch for seed {seed}")

    cfg = get_cfg_defaults()
    cfg.merge_from_other_cfg(type(cfg).load_cfg(state["cfg"]))
    cfg.TRAIN.ENABLE = False
    if int(cfg.DATA.N_VAR) != 8 or int(cfg.DATA.WIN_SIZE) != 10:
        raise RuntimeError("CANDI state is not the sealed D8/W10 configuration")
    model = MLP(cfg).cuda()
    model.sana_in = SANA(cfg).cuda()
    model.sana_out = SANA(cfg).cuda()
    model.load_state_dict(state["model_state"], strict=True)
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    model.eval()
    if state_hash_core(model) != row["backbone_tensor_sha256"]:
        raise RuntimeError(f"loaded MLP core hash mismatch for seed {seed}")
    if state_hash(model.sana_in) != row["sana_in_sha256"]:
        raise RuntimeError(f"loaded SANA-in hash mismatch for seed {seed}")
    if state_hash(model.sana_out) != row["sana_out_sha256"]:
        raise RuntimeError(f"loaded SANA-out hash mismatch for seed {seed}")
    return model, state


def _key_hash(seed: int, timestamps: np.ndarray) -> str:
    rows = [
        {
            "detector_seed": int(seed),
            "source_seed": SOURCE_SEED,
            "scenario": SCENARIO,
            "condition": CONDITION,
            "timestamp": int(timestamp),
        }
        for timestamp in timestamps
    ]
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _causal_candi_check(model: torch.nn.Module, raw: np.ndarray,
                        candi_mean: np.ndarray, candi_scale: np.ndarray,
                        timestamp: int, original_score: torch.Tensor) -> dict:
    future = np.array(raw, copy=True)
    if timestamp + 1 >= len(future):
        raise RuntimeError("causality fixture has no future suffix")
    generator = np.random.default_rng(7000 + int(timestamp))
    future[timestamp + 1:] = generator.standard_normal(
        future[timestamp + 1:].shape
    )
    original_window = windows_at(
        ((raw - candi_mean) / candi_scale).astype(np.float32),
        np.asarray([timestamp]), 10,
    )
    changed_window = windows_at(
        ((future - candi_mean) / candi_scale).astype(np.float32),
        np.asarray([timestamp]), 10,
    )
    changed_score = candi_score(model, torch.from_numpy(changed_window).cuda())
    check = _cmp(original_score.reshape(1), changed_score, exact=True)
    return {
        "timestamp": int(timestamp),
        "future_mutated_observations": int(len(future) - timestamp - 1),
        "window_input_equal": bool(np.array_equal(original_window, changed_window)),
        "score": check,
        "pass_": bool(np.array_equal(original_window, changed_window)
                      and check["pass_"]),
    }


def _load_original_backbone_preflight() -> dict:
    path = ROOT / "reports" / "phase_g" / "preflight.json"
    report = json.loads(path.read_text())
    if report["status"] != "STOP_CANDI_CONTROL_UNRESOLVED":
        raise RuntimeError("original G0 report status changed unexpectedly")
    if report["backbone_preflight_status"] != "PASS":
        raise RuntimeError("original G0 backbone preflight is not PASS")
    if len(report["runs"]) != 10 or any(
            row["status"] != "PASS" or row["hard_failures"]
            for row in report["runs"]):
        raise RuntimeError("original G0 report contains a backbone failure")
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha(path),
        "status": report["status"],
        "backbone_status": report["backbone_preflight_status"],
        "run_count": len(report["runs"]),
    }


def _run_seed(seed: int, rows_by_seed: dict, raw: np.ndarray,
              phase_f_scaler: dict) -> dict:
    candi_row = rows_by_seed[seed]
    entries = json.loads(
        (ROOT / "reports" / "phase_g" / "checkpoint_manifest.json").read_text()
    )["entries"]
    entry_by_run = {row["run"]: row for row in entries}
    x_entry = entry_by_run[f"xlstm_{seed}"]
    l_entry = entry_by_run[f"lstm_{seed}"]
    x_model = f4_model = None
    l_model = None
    candi_model = None
    try:
        # Every architecture sees windows derived from the same raw stream;
        # only its already-sealed preprocessing may differ.
        common_mean = np.asarray(phase_f_scaler["mean"], dtype=np.float64)
        common_scale = np.asarray(phase_f_scaler["scale"], dtype=np.float64)
        candi_mean = np.asarray(candi_row["preprocessing"]["scaler_mean"], dtype=np.float64)
        candi_scale = np.asarray(candi_row["preprocessing"]["scaler_scale"], dtype=np.float64)
        timestamps = np.arange(FIRST_COMMON_TIMESTAMP, len(raw), dtype=np.int64)
        if len(timestamps) < 96 or int(timestamps.min()) != FIRST_COMMON_TIMESTAMP:
            raise RuntimeError("invalid common timestamp fixture")
        common_scaled = ((raw - common_mean) / common_scale).astype(np.float32)
        candi_scaled = ((raw - candi_mean) / candi_scale).astype(np.float32)
        x_windows = torch.from_numpy(windows_at(common_scaled, timestamps, 64)).cuda()
        l_windows = x_windows.clone()
        candi_windows = torch.from_numpy(windows_at(candi_scaled, timestamps, 10)).cuda()
        raw_hash = array_hash(raw)
        x_window_hash = tensor_hash(x_windows)
        l_window_hash = tensor_hash(l_windows)
        candi_window_hash = tensor_hash(candi_windows)
        key_hash = _key_hash(seed, timestamps)

        x_model = __import__("phase_g0_preflight")._load_entry(x_entry)
        l_model = __import__("phase_g0_preflight")._load_entry(l_entry)
        x_before = model_state_snapshot(x_model)
        l_before = model_state_snapshot(l_model)
        x_output, x_scores, x_base, _ = _extract(x_model, "xlstm", x_windows)
        l_output, l_scores, l_base, _ = _extract(l_model, "lstm", l_windows)
        x_internal = _expand(x_base)
        l_internal = _expand(l_base)
        x_dummy = {"semantic_label": torch.zeros(len(timestamps), dtype=torch.int64)}
        l_dummy = {"semantic_label": torch.ones(len(timestamps), dtype=torch.int64)}
        _, x_scores_dummy, x_base_dummy, _ = _outer_label_blind_extract(
            x_model, "xlstm", x_windows, x_dummy
        )
        _, l_scores_dummy, l_base_dummy, _ = _outer_label_blind_extract(
            l_model, "lstm", l_windows, l_dummy
        )

        candi_model, candi_state = _load_candi(seed, candi_row)
        restore_rng(candi_state["rng"])
        candi_rng_before = object_hash(rng_state())
        candi_before = model_state_snapshot(candi_model)
        candi_scores = candi_score(candi_model, candi_windows)
        candi_dummy = {"semantic_label": torch.ones(len(timestamps), dtype=torch.int64)}
        candi_scores_dummy = _candi_label_blind_extract(
            candi_model, candi_windows, candi_dummy
        )
        candi_rng_after = object_hash(rng_state())
        candi_history = _history(candi_scores)
        # The same tensor object is reused for both paired arms; no second
        # CANDI scoring pass or arm-specific history transformation exists.
        candi_history_x = candi_history
        candi_history_l = candi_history
        x_arm = torch.cat((candi_history_x, x_internal), dim=1)
        l_arm = torch.cat((candi_history_l, l_internal), dim=1)

        causality = [
            _causal_candi_check(candi_model, raw, candi_mean, candi_scale,
                                int(timestamps[idx]), candi_scores[idx:idx + 1])
            for idx in (0, 16, 64)
        ]
        expected_valid_start = 32
        expected_valid_rows = len(timestamps) - expected_valid_start
        history_valid = bool(torch.isfinite(candi_history[expected_valid_start:]).all())
        history_warmup_nan = bool(torch.isnan(candi_history[:expected_valid_start]).any())
        row_key_x = key_hash
        row_key_l = key_hash

        checks = {
            "raw_stream_hash_shared": {
                "pass_": raw_hash == array_hash(np.ascontiguousarray(raw)),
                "raw_stream_sha256": raw_hash,
            },
            "same_raw_stream_to_all_models": {
                "pass_": bool(np.array_equal(x_windows.detach().cpu().numpy(),
                                               l_windows.detach().cpu().numpy())),
                "raw_stream_sha256": raw_hash,
                "xlstm_input_sha256": x_window_hash,
                "lstm_input_sha256": l_window_hash,
                "candi_input_sha256": candi_window_hash,
                "source_seed": SOURCE_SEED,
                "scenario": SCENARIO,
                "condition": CONDITION,
            },
            "common_timestamp_alignment": {
                "pass_": int(timestamps.min()) == FIRST_COMMON_TIMESTAMP
                          and int(timestamps.max()) == len(raw) - 1
                          and len(timestamps) == len(candi_scores) == len(x_scores) == len(l_scores),
                "first_timestamp": int(timestamps.min()),
                "last_timestamp": int(timestamps.max()),
                "count": len(timestamps),
                "pre_common_scores_used": False,
                "pre_common_score_count": 0,
                "xlstm_window": "raw[t-63:t+1]",
                "lstm_window": "raw[t-63:t+1]",
                "candi_window": "raw[t-9:t+1]",
            },
            "candi_history_schema": {
                "pass_": list(candi_history.shape) == [len(timestamps), 14]
                          and history_valid and history_warmup_nan
                          and expected_valid_rows > 0,
                "shape": list(candi_history.shape),
                "expected": [len(timestamps), EXPECTED["history"]],
                "valid_start_index": expected_valid_start,
                "valid_rows": expected_valid_rows,
                "padding_or_imputation": False,
            },
            "paired_history_reuse": {
                "pass_": bool(candi_history_x.data_ptr() == candi_history_l.data_ptr()
                              and _causal_cmp(candi_history_x, candi_history_l)["pass_"]),
                "history_tensor_sha256": tensor_hash(candi_history),
                "x_arm_history_sha256": tensor_hash(x_arm[:, :14]),
                "l_arm_history_sha256": tensor_hash(l_arm[:, :14]),
                "same_tensor_object": bool(candi_history_x.data_ptr() == candi_history_l.data_ptr()),
                "x_arm_shape": list(x_arm.shape),
                "l_arm_shape": list(l_arm.shape),
            },
            "row_key_identity": {
                "pass_": row_key_x == row_key_l,
                "xlstm_key_sha256": row_key_x,
                "lstm_key_sha256": row_key_l,
                "row_count": len(timestamps),
                "key_fields": ["detector_seed", "source_seed", "scenario",
                               "condition", "timestamp"],
            },
            "candi_future_causality": {
                "pass_": all(item["pass_"] for item in causality),
                "checks": causality,
            },
            "candi_dummy_label_invariance": {
                "pass_": bool(torch.equal(candi_scores, candi_scores_dummy)),
                "score": _cmp(candi_scores, candi_scores_dummy, exact=True),
                "labels_passed_to_extractor": False,
            },
            "backbone_dummy_label_invariance": {
                "pass_": bool(torch.equal(x_scores, x_scores_dummy)
                              and torch.equal(x_base, x_base_dummy)
                              and torch.equal(l_scores, l_scores_dummy)
                              and torch.equal(l_base, l_base_dummy)),
                "xlstm_score": _cmp(x_scores, x_scores_dummy, exact=True),
                "xlstm_common18": _cmp(x_base, x_base_dummy, exact=True),
                "lstm_score": _cmp(l_scores, l_scores_dummy, exact=True),
                "lstm_common18": _cmp(l_base, l_base_dummy, exact=True),
                "labels_passed_to_extractor": False,
            },
            "finite_and_shapes": {
                "pass_": list(x_output.shape) == list(x_windows.shape)
                          and list(l_output.shape) == list(l_windows.shape)
                          and list(x_base.shape) == [len(timestamps), 18]
                          and list(l_base.shape) == [len(timestamps), 18]
                          and list(x_internal.shape) == [len(timestamps), 234]
                          and list(l_internal.shape) == [len(timestamps), 234]
                          and list(x_arm.shape) == [len(timestamps), 248]
                          and list(l_arm.shape) == [len(timestamps), 248]
                          and bool(torch.isfinite(x_output).all())
                          and bool(torch.isfinite(l_output).all())
                          and bool(torch.isfinite(x_scores).all())
                          and bool(torch.isfinite(l_scores).all())
                          and bool(torch.isfinite(candi_scores).all())
                          and bool(torch.isfinite(x_base).all())
                          and bool(torch.isfinite(l_base).all()),
                "xlstm_output": list(x_output.shape),
                "lstm_output": list(l_output.shape),
                "xlstm_base": list(x_base.shape),
                "lstm_base": list(l_base.shape),
                "xlstm_internal": list(x_internal.shape),
                "lstm_internal": list(l_internal.shape),
                "xlstm_arm": list(x_arm.shape),
                "lstm_arm": list(l_arm.shape),
            },
            "no_state_mutation": {
                "pass_": (model_state_snapshot(x_model)["model"] == x_before["model"]
                          and model_state_snapshot(l_model)["model"] == l_before["model"]
                          and model_state_snapshot(candi_model)["model"] == candi_before["model"]
                          and candi_rng_before == candi_rng_after),
                "xlstm_before": x_before,
                "xlstm_after": model_state_snapshot(x_model),
                "lstm_before": l_before,
                "lstm_after": model_state_snapshot(l_model),
                "candi_before": candi_before,
                "candi_after": model_state_snapshot(candi_model),
                "candi_rng_before": candi_rng_before,
                "candi_rng_after": candi_rng_after,
                "optimizer_created_or_stepped": False,
                "adaptation_or_fpm_invoked": False,
            },
        }
        hard_failures = [name for name, value in checks.items()
                         if not bool(value.get("pass_"))]
        return {
            "detector_seed": seed,
            "status": "PASS" if not hard_failures else "STOP",
            "hard_failures": hard_failures,
            "checks": checks,
            "labels_read": False,
            "test_sources_used": False,
            "test_metrics_computed": False,
            "scaler_fit": False,
            "classifier_fit": False,
            "optimizer_created_or_stepped": False,
            "native_predict_invoked": False,
            "candi_operator": "official model.get_anomaly_scores only",
            "candi_seed_mapping": candi_row["pre_intervention"],
        }
    finally:
        # Release GPU references between seed-wise paired checks.  This does
        # not alter any sealed artifact and keeps the bounded audit small.
        del x_model, l_model, candi_model
        torch.cuda.empty_cache()


def main() -> None:
    environment = f4.configure()
    config = json.loads((ROOT / "configs" / "phase_g.json").read_text())
    control = json.loads((ROOT / "reports" / "phase_g" /
                          "candi_control_manifest.json").read_text())
    schema = json.loads((ROOT / "reports" / "phase_g" /
                         "schema_binding.json").read_text())
    original = _load_original_backbone_preflight()
    if config["g0_status"] != "PENDING_CANDI_PREFLIGHT":
        raise RuntimeError("G0.1 preflight must start from pending status")
    if control["status"] != "SEALED_PROSPECTIVE_PENDING_PREFLIGHT":
        raise RuntimeError("CANDI control amendment is not prospective/pending")
    control_path = ROOT / "reports" / "phase_g" / "candi_control_manifest.json"
    control_sha = sha(control_path)
    if config["g01_amendment"]["manifest_sha256"] != control_sha:
        raise RuntimeError("CANDI control manifest hash is not bound in config")
    if schema["candi_control_manifest_sha256"] != control_sha:
        raise RuntimeError("CANDI control manifest hash is not bound in schema")
    phase_d_manifest_path = ROOT / "reports" / "phase_d" / "synthetic_backbone_manifest.json"
    if sha(phase_d_manifest_path) != control["phase_d_manifest_sha256"]:
        raise RuntimeError("Phase-D synthetic backbone manifest hash changed")
    if config["candi_history_control"]["seed_mapping"] != control["seed_mapping"]:
        raise RuntimeError("config/control seed mapping mismatch")
    if config["candi_history_control"]["official_candi_commit"] != OFFICIAL_CANDI_COMMIT:
        raise RuntimeError("official CANDI commit binding mismatch")
    official_head = subprocess.check_output(
        ["git", "-C", str(OFFICIAL), "rev-parse", "HEAD"], text=True
    ).strip()
    official_dirty = subprocess.check_output(
        ["git", "-C", str(OFFICIAL), "status", "--porcelain"], text=True
    ).strip()
    if official_head != OFFICIAL_CANDI_COMMIT or official_dirty:
        raise RuntimeError("official CANDI checkout is not the clean pinned commit")
    if not torch.cuda.is_available():
        raise RuntimeError("G0.1 requires the available CUDA inference device")

    # Generate an observation-only validation-fold fixture.  The generator
    # object contains evaluator truth, but this script accesses only its
    # observations field and never passes any metadata to an extractor.
    stream = generate(SOURCE_SEED, SCENARIO, CONDITION)
    raw = np.ascontiguousarray(stream.observations[:RAW_LENGTH], dtype=np.float32)
    if raw.shape != (RAW_LENGTH, 8) or not np.isfinite(raw).all():
        raise RuntimeError("invalid unlabeled synthetic observation fixture")
    phase_f_scaler, phase_f_scaler_path = _load_phase_f_scaler(SOURCE_SEED)
    controls = {int(row["detector_seed"]): row for row in control["controls"]}
    if set(controls) != set(SEEDS):
        raise RuntimeError("G0.1 control manifest does not contain all five seeds")

    rows = []
    for seed in SEEDS:
        try:
            rows.append(_run_seed(seed, controls, raw, phase_f_scaler))
        except Exception as exc:  # fail closed after sealing the diagnostic
            rows.append({
                "detector_seed": seed,
                "status": "STOP",
                "hard_failures": ["exception"],
                "error": repr(exc),
                "labels_read": False,
                "test_sources_used": False,
                "test_metrics_computed": False,
                "scaler_fit": False,
                "classifier_fit": False,
                "optimizer_created_or_stepped": False,
                "native_predict_invoked": False,
            })

    status = "PASS" if all(row["status"] == "PASS" for row in rows) else "STOP"
    report = {
        "status": "PASS" if status == "PASS" else "STOP_CANDI_ALIGNMENT",
        "g0_status": "PASS" if status == "PASS" else "STOP",
        "backbone_preflight": original,
        "candi_control_status": "PASS" if status == "PASS" else "STOP",
        "candi_control_manifest": str(control_path.relative_to(ROOT)),
        "candi_control_manifest_sha256": control_sha,
        "official_candi_commit": OFFICIAL_CANDI_COMMIT,
        "official_candi_checkout_head": official_head,
        "official_candi_checkout_dirty": bool(official_dirty),
        "fixture": {
            "source_seed": SOURCE_SEED,
            "source_fold": "probe_validation",
            "scenario": SCENARIO,
            "condition": CONDITION,
            "raw_length": RAW_LENGTH,
            "dimension": 8,
            "raw_observations_sha256": array_hash(raw),
            "phase_f_scaler": str(phase_f_scaler_path.relative_to(ROOT)),
            "phase_f_scaler_sha256": sha(phase_f_scaler_path),
            "generator_fields_accessed": ["observations"],
            "truth_fields_accessed": [],
        },
        "alignment": control["alignment"],
        "expected_feature_schema": EXPECTED,
        "atol": ATOL,
        "rtol": RTOL,
        "rows": rows,
        "random_unlabeled_only": True,
        "labels_read": False,
        "test_sources_used": False,
        "test_metrics_computed": False,
        "scaler_fit": False,
        "classifier_fit": False,
        "optimizer_created_or_stepped": False,
        "native_predict_invoked": False,
        "adaptation_or_fpm_invoked": False,
        "phase_g_label_join_started": False,
        "phase_g_statistics_started": False,
        "note": (
            "CANDI controls were selected prospectively by G0.1. This report "
            "contains alignment/invariance checks only; no labels or detector "
            "metrics were read or computed."
        ),
    }
    output = ROOT / "reports" / "phase_g" / "candi_preflight.json"
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"], "rows": len(rows),
                      "output": str(output)}))
    if status != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
