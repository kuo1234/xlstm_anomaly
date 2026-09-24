"""R0 execution runner — thin orchestration of the sealed R0 library.

This file adds no scientific logic.  Every scientific operation is a call into
the sealed modules named in ``research/real_data_r0/execution_handoff.md``:
``real_data_r0_data`` (loading, scaler, windows, labels, Design-B blocks),
``real_data_r0_models`` (configure, builders, CUDA overlay, observers,
extraction, hashes), ``real_data_r0_probe`` (arms, HGB selection/evaluation,
estimand, resampling, wording, detector sanity) and
``phase_g1_core.history14`` / ``expand_internal234``.  The training loop is the
Phase F-v3 loop with the frozen R0 constants.

Stages (fail-closed, chronological)::

    invalidate-v1-caches                                    r0-v1.1: retire the five v1 CUDA-path caches (hash-checked)
    preflight-v1-1                                          r0-v1.1: result-blind gate on the six reused xLSTM checkpoints
    train    --machine M --backbone {xlstm,lstm} --seed S   train split only, no label file opened
    extract  --machine M --backbone B --seed S              checkpoint gate, validation + test features (r0-v1.1 paths)
    schedule --workers 2                                    18 x (train, extract), <= 2 concurrent, commit+push per run
    seal-features                                           feature_cache_manifest_v1_1.json over all 18 caches
    probe                                                   requires the committed + pushed manifest; first label access
    aggregate                                               3x3 delta-AP matrices, bootstraps, classification
    sanity                                                  detector-sanity table (after results.json is committed)
    report                                                  results.md from results.json + detector_sanity.json

Run records under ``research/real_data_r0/runs/`` are immutable (never
overwritten).  Checkpoints and feature caches live git-ignored under
``data/r0_runs/``.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as _dt
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import real_data_r0_data as r0data  # noqa: E402
import real_data_r0_probe as r0probe  # noqa: E402

CONFIG = r0data.CONFIG
DETECTOR = CONFIG["detector"]
MACHINES = r0data.MACHINES
BACKBONES = tuple(DETECTOR["backbones"])
SEEDS = tuple(int(s) for s in DETECTOR["seeds"])
RESULTS = Path(os.environ.get("R0_RESULTS_DIR", ROOT / "research" / "real_data_r0"))
RUN_RECORDS = RESULTS / "runs"
RUNS_DATA = Path(os.environ.get("R0_RUNS_DATA", ROOT / "data" / "r0_runs"))
AMENDMENT_PATH = ROOT / "research" / "real_data_r0" / "amendment_v1_1.json"
AMENDMENT: dict[str, Any] = json.loads(AMENDMENT_PATH.read_text())
PROTOCOL_VERSION = AMENDMENT["protocol_version"]  # "r0-v1.1"
FEATURE_MANIFEST = RESULTS / "feature_cache_manifest_v1_1.json"
CACHE_FILE = "features_v1_1.npz"
INVALIDATED_V1_CACHE_FILE = "features_v1_cuda_invalidated.npz"
INVALIDATION_RECORD = RESULTS / "runs" / "v1_cuda_cache_invalidation.json"
PREFLIGHT_V1_1 = RESULTS / "preflight_v1_1.json"
# r0-v1.1 (amendment_v1_1.json): xLSTM scientific extraction uses the vanilla training backend and the
# scalar reference observer only; the matched LSTM keeps its r0-v1 path and gate unchanged.
EXTRACTION_PLAN = {
    "xlstm": {"arch": "xlstm_reference", "backend": "vanilla_reference", "gate": "v1_1_vanilla_reference"},
    "lstm": {"arch": "lstm", "backend": "lstm_manual_replay", "gate": "v1_lstm_observer"},
}
RESULTS_JSON = RESULTS / "results.json"
SANITY_JSON = RESULTS / "detector_sanity.json"
BRANCH = "experiment/real-data-r0-execution"
PROTOCOL_HEAD = "d7708586fe3264fcd6e5567504cccd97104c2a2e"
CANARY_SEED, CANARY_SHAPE = 710, (128, 64, 38)
MAX_CONCURRENT_DETECTOR_PROCESSES = 2  # execution_handoff.md §3 (F-v4 convention)


# --------------------------------------------------------------------------- bookkeeping


def utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_name(machine: str, backbone: str, seed: int) -> str:
    return f"{machine}_{backbone}_{seed}"


def planned_runs() -> list[tuple[str, str, int]]:
    """All 18 (machine, backbone, seed) units; longest (xLSTM) runs first for scheduling."""
    return [(m, b, s) for b in BACKBONES for m in MACHINES for s in SEEDS]


def sha_file(path: Path) -> str:
    return r0data.sha256_file(path)


def array_sha(array: np.ndarray) -> str:
    a = np.ascontiguousarray(array)
    return hashlib.sha256(str(a.dtype).encode() + str(a.shape).encode() + a.tobytes()).hexdigest()


def write_immutable(path: Path, value: Any) -> None:
    """Write a run record once; an existing record is never overwritten."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise r0data.ProtocolViolation(f"immutable record already exists: {path.name}")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    os.replace(tmp, path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def git(*args: str, check: bool = True) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=check, capture_output=True, text=True).stdout.strip()


def git_head() -> str:
    try:
        return git("rev-parse", "HEAD")
    except Exception:  # tests outside a checkout
        return "unknown"


def is_committed_clean(path: Path) -> bool:
    rel = str(path.resolve().relative_to(ROOT.resolve()))
    tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--error-unmatch", rel], capture_output=True).returncode == 0
    clean = subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", rel]).returncode == 0
    return tracked and clean


def is_pushed() -> bool:
    """HEAD is contained in the remote execution branch (fetched now)."""
    fetch = subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "origin", BRANCH], capture_output=True)
    if fetch.returncode != 0:
        return False
    return subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", "HEAD", "FETCH_HEAD"]).returncode == 0


def _assert_no_labels(stage: str) -> None:
    if r0data.label_access_log():
        raise r0data.ProtocolViolation(f"label access during {stage}")


def _scaler_record(scaler: dict[str, Any]) -> dict[str, Any]:
    return {"mean": [float(v) for v in scaler["mean"]], "scale": [float(v) for v in scaler["scale"]],
            "zero_std_channels": scaler["zero_std_channels"], "fit_rows": scaler["fit_rows"], "train_N": scaler["train_N"],
            "mean_sha256": array_sha(np.asarray(scaler["mean"])), "scale_sha256": array_sha(np.asarray(scaler["scale"]))}


def _train_record_path(name: str) -> Path:
    return RUN_RECORDS / f"train_{name}.json"


def _extract_record_path(name: str) -> Path:
    """r0-v1.1 extraction record (v1 records ``extract_<unit>.json`` are history only)."""
    return RUN_RECORDS / f"extract_v1_1_{name}.json"


def _v1_extract_record_path(name: str) -> Path:
    return RUN_RECORDS / f"extract_{name}.json"


def extraction_plan(backbone: str) -> dict[str, str]:
    if backbone not in EXTRACTION_PLAN:
        raise r0data.ProtocolViolation("unregistered backbone")
    return dict(EXTRACTION_PLAN[backbone])


def validate_extract_record(record: dict[str, Any], backbone: str) -> None:
    """Accept only a passing r0-v1.1 extraction of the registered backend (rejects every v1 CUDA cache)."""
    plan = extraction_plan(backbone)
    problems = []
    if record.get("protocol_version") != PROTOCOL_VERSION:
        problems.append("protocol_version")
    if record.get("status") != "PASS" or not record.get("gate", {}).get("pass"):
        problems.append("status/gate")
    if record.get("extraction_backend") != plan["backend"] or record.get("gate", {}).get("name") != plan["gate"]:
        problems.append("extraction_backend")
    if Path(record.get("feature_cache", {}).get("file", "")).name != CACHE_FILE:
        problems.append("cache_file")
    if record.get("label_read_count") != 0:
        problems.append("label_read_count")
    if record.get("dimensions") != {"H": 14, "internal234": 234}:
        problems.append("dimensions")
    if problems:
        raise r0data.ProtocolViolation(f"extraction record rejected for r0-v1.1: {problems}")


def _probe_record_path(name: str) -> Path:
    return RUN_RECORDS / f"probe_{name}.json"


def _run_dir(machine: str, backbone: str, seed: int) -> Path:
    return RUNS_DATA / machine / f"{backbone}_{seed}"


# --------------------------------------------------------------------------- train (no labels)


def train(machine: str, backbone: str, seed: int) -> dict[str, Any]:
    import torch

    import real_data_r0_models as models

    name = run_name(machine, backbone, seed)
    if machine not in MACHINES or backbone not in BACKBONES or seed not in SEEDS:
        raise r0data.ProtocolViolation("unregistered R0 unit")
    record_path = _train_record_path(name)
    if record_path.exists():
        raise r0data.ProtocolViolation(f"{name} already trained")
    start = time.perf_counter()
    environment = models.configure()
    data_dir = _run_dir(machine, backbone, seed)
    data_dir.mkdir(parents=True, exist_ok=False)
    observations = r0data.load_observations(machine, "train")
    scaler = r0data.fit_scaler(observations)
    scaled = r0data.apply_scaler(observations, scaler)
    fit_edges = r0data.fit_window_edges(len(observations))
    val_edges = r0data.validation_window_edges(len(observations))
    fit = torch.from_numpy(r0data.window_matrix(scaled, fit_edges)).cuda()
    validation = torch.from_numpy(r0data.window_matrix(scaled, val_edges)).cuda()
    model = models.build_xlstm_vanilla(seed) if backbone == "xlstm" else models.build_lstm(seed)
    parameter_count = models.trainable_parameters(model)
    settings = {k: v for k, v in DETECTOR["optimizer"].items() if k != "name"}
    settings["betas"] = tuple(settings["betas"])
    optimizer = torch.optim.Adam(model.parameters(), **settings)

    def cpu_state():
        return {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    initial_hash = models.model_hash(model)
    torch.save(cpu_state(), data_dir / "initial.pt")
    batch = int(DETECTOR["batch_size"])
    epochs = int(DETECTOR["epochs"])
    steps_per_epoch = -(-len(fit) // batch)
    order_hasher = hashlib.sha256()
    curves: list[dict[str, Any]] = []
    best, best_epoch, steps, exposures = float("inf"), None, 0, 0
    predict_guard = _native_predict_guard(backbone)
    torch.cuda.reset_peak_memory_stats()
    training_start = time.perf_counter()
    with predict_guard as trap:
        for epoch in range(epochs):
            epoch_start = time.perf_counter()
            order = np.random.default_rng(np.random.SeedSequence([seed, epoch, 1701])).permutation(len(fit))
            order_hasher.update(order.tobytes())
            ids = torch.from_numpy(order.copy()).cuda()
            model.train()
            total = torch.zeros((), device="cuda", dtype=torch.float64)
            for batch_ids in ids.split(batch):
                x = fit[batch_ids]
                optimizer.zero_grad(set_to_none=True)
                loss = (model(x) - x).square().mean()
                if not bool(torch.isfinite(loss)):
                    raise r0data.ProtocolViolation("non-finite training loss")
                loss.backward()
                if not all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in model.parameters()):
                    raise r0data.ProtocolViolation("non-finite training gradient")
                optimizer.step()
                steps += 1
                exposures += len(batch_ids)
                total += loss.detach().double() * len(batch_ids)
            model.eval()
            val_total = torch.zeros((), device="cuda", dtype=torch.float64)
            with torch.no_grad():
                for x in validation.split(batch):
                    val_loss = (model(x) - x).square().mean()
                    if not bool(torch.isfinite(val_loss)):
                        raise r0data.ProtocolViolation("non-finite validation loss")
                    val_total += val_loss.double() * len(x)
            train_mse, validation_mse = float(total / len(fit)), float(val_total / len(validation))
            if validation_mse < best:  # strict: earliest epoch wins exact ties
                best, best_epoch = validation_mse, epoch + 1
                torch.save({"model": cpu_state(), "epoch": best_epoch, "validation_mse": best}, data_dir / "best.pt")
            row = {"epoch": epoch + 1, "train_mse": train_mse, "validation_mse": validation_mse,
                   "training_order_sha256": hashlib.sha256(order.tobytes()).hexdigest(),
                   "seconds": time.perf_counter() - epoch_start}
            curves.append(row)
            print(json.dumps({"run": name, **row}), flush=True)
        native_predict_calls = trap.call_count if trap is not None else 0
    torch.cuda.synchronize()
    training_seconds = time.perf_counter() - training_start
    if steps != epochs * steps_per_epoch or exposures != epochs * len(fit):
        raise r0data.ProtocolViolation("optimizer step/exposure count mismatch")
    final_hash = models.model_hash(model)
    torch.save({"model": cpu_state(), "optimizer": optimizer.state_dict(), "epoch": epochs}, data_dir / "final.pt")
    payload = torch.load(data_dir / "best.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(payload["model"], strict=True)
    best_hash = models.model_hash(model)
    _assert_no_labels("training")
    record = {
        "stage": "train", "status": "PASS", "run": name, "machine": machine, "backbone": backbone, "seed": seed,
        "execution_commit": git_head(), "protocol_head": PROTOCOL_HEAD, "environment": environment,
        "parameter_count": parameter_count, "expected_parameter_count": DETECTOR[backbone]["trainable_parameters"],
        "scaler": _scaler_record(scaler), "fit_windows": int(len(fit)), "validation_windows": int(len(validation)),
        "fit_edge_range": [int(fit_edges[0]), int(fit_edges[-1])], "validation_edge_range": [int(val_edges[0]), int(val_edges[-1])],
        "batch_size": batch, "epochs": epochs, "steps_per_epoch": steps_per_epoch, "optimizer_steps": steps,
        "window_exposures": exposures, "optimizer": DETECTOR["optimizer"], "consumed_order_sha256": order_hasher.hexdigest(),
        "curves": curves, "selected_epoch": best_epoch, "best_validation_mse": best,
        "initial_model_hash": initial_hash, "final_model_hash": final_hash, "best_model_hash": best_hash,
        "checkpoints": {p.name: sha_file(p) for p in sorted(data_dir.iterdir())},
        "native_predict_calls": native_predict_calls, "labels_read": False, "test_split_read": False,
        "training_seconds": training_seconds, "total_seconds": time.perf_counter() - start,
        "peak_allocated_bytes": int(torch.cuda.max_memory_allocated()), "finished_utc": utc(),
    }
    if parameter_count != record["expected_parameter_count"]:
        raise r0data.ProtocolViolation("parameter-count drift")
    write_immutable(record_path, record)
    return record


class _NullTrap:
    call_count = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _native_predict_guard(backbone: str):
    """Fail closed if the official native predict/test path were ever invoked."""
    if backbone != "xlstm":
        return _NullTrap()
    from unittest.mock import patch

    import phase_e2_common as e2

    return patch.object(e2.native.xLSTMAD, "predict_step", side_effect=RuntimeError("native predict_step forbidden"))


# --------------------------------------------------------------------------- extract (no labels)


def _parity_inputs(machine: str, scaled_fit: np.ndarray, fit_edges: np.ndarray):
    import torch

    generator = torch.Generator(device="cpu").manual_seed(CANARY_SEED)
    canary = torch.randn(*CANARY_SHAPE, generator=generator).cuda()
    pick = np.concatenate((fit_edges[:64], fit_edges[-64:]))
    fit_batch = torch.from_numpy(r0data.window_matrix(scaled_fit, pick)).cuda()
    return {"canary_N01": canary, f"fit_windows_{machine}": fit_batch}


def _forbid_cuda_overlay(models) -> None:
    """r0-v1.1: the native CUDA sLSTM overlay may not produce any scientific value in this process."""
    def forbidden(*args, **kwargs):
        raise r0data.ProtocolViolation("CUDA overlay forbidden in r0-v1.1 scientific extraction")

    models.cuda_overlay_from_vanilla = forbidden
    models.build_xlstm_cuda = forbidden


def _lstm_gate_v1(models, model, inputs) -> dict[str, Any]:
    """Matched-LSTM checkpoint gate, unchanged from r0-v1: observer on/off bitwise + manual replay parity."""
    import torch

    import real_data_r0_preflight as pf

    result: dict[str, Any] = {"name": EXTRACTION_PLAN["lstm"]["gate"]}
    for label, x in inputs.items():
        with torch.no_grad():
            plain = model(x)
        out, _score, base = models.extract_batch(model, "lstm", x)  # manual replay parity enforced inside
        result[label] = {"observer_on_off": pf._cmp(plain, out, exact=True),
                         "replay_parity": {"pass": True, "bitwise": None, "max_abs": None}}
    result["pass"] = bool(all(r["observer_on_off"]["bitwise"] for k, r in result.items() if isinstance(r, dict)))
    return result


def _xlstm_gate_v1_1(models, model, inputs) -> dict[str, Any]:
    """r0-v1.1 xLSTM gate on the vanilla backend + scalar reference observer (no second implementation)."""
    import torch

    import real_data_r0_preflight as pf

    result: dict[str, Any] = {"name": EXTRACTION_PLAN["xlstm"]["gate"], "eval_mode": not model.training,
                              "trainable_parameters": models.trainable_parameters(model) if any(p.requires_grad for p in model.parameters())
                              else int(sum(p.numel() for p in model.parameters()))}
    ok = result["eval_mode"] and result["trainable_parameters"] == DETECTOR["xlstm"]["trainable_parameters"]
    for label, x in inputs.items():
        with torch.no_grad():
            first, second = model(x), model(x)
        out, score, base = models.extract_batch(model, EXTRACTION_PLAN["xlstm"]["arch"], x)  # reference parity enforced inside
        row = {"observer_on_off": pf._cmp(first, out, exact=True), "repeat_inference": pf._cmp(first, second, exact=True),
               "reference_observer_parity": True, "output_finite": bool(torch.isfinite(out).all()),
               "score_finite": bool(torch.isfinite(score).all()), "common18_finite": bool(torch.isfinite(base).all()),
               "common18_shape": list(base.shape)}
        ok = ok and row["observer_on_off"]["bitwise"] and row["repeat_inference"]["bitwise"] and row["output_finite"] \
            and row["score_finite"] and row["common18_finite"] and row["common18_shape"] == [x.shape[0], 18]
        result[label] = row
    result["pass"] = bool(ok)
    return result


def extract(machine: str, backbone: str, seed: int) -> dict[str, Any]:
    import torch

    import real_data_r0_models as models
    from phase_g1_core import expand_internal234, history14

    _forbid_cuda_overlay(models)
    name = run_name(machine, backbone, seed)
    train_record = read_json(_train_record_path(name))
    if train_record["status"] != "PASS":
        raise r0data.ProtocolViolation(f"{name} has no passing training record")
    record_path = _extract_record_path(name)
    if record_path.exists():
        raise r0data.ProtocolViolation(f"{name} already extracted")
    start = time.perf_counter()
    environment = models.configure()
    data_dir = _run_dir(machine, backbone, seed)
    best_path = data_dir / "best.pt"
    if sha_file(best_path) != train_record["checkpoints"]["best.pt"]:
        raise r0data.ProtocolViolation("best checkpoint hash mismatch")
    payload = torch.load(best_path, map_location="cpu", weights_only=True)
    reference = models.build_xlstm_vanilla(seed) if backbone == "xlstm" else models.build_lstm(seed)
    reference.load_state_dict(payload["model"], strict=True)
    reference.eval()
    for parameter in reference.parameters():
        parameter.requires_grad_(False)
    if models.model_hash(reference) != train_record["best_model_hash"]:
        raise r0data.ProtocolViolation("best model hash mismatch")
    plan = extraction_plan(backbone)
    model, arch = reference, plan["arch"]  # r0-v1.1: one implementation for training and extraction
    train_obs = r0data.load_observations(machine, "train")
    scaler = r0data.fit_scaler(train_obs)
    if _scaler_record(scaler)["scale_sha256"] != train_record["scaler"]["scale_sha256"] or \
            _scaler_record(scaler)["mean_sha256"] != train_record["scaler"]["mean_sha256"]:
        raise r0data.ProtocolViolation("scaler drift between train and extract")
    scaled_train = r0data.apply_scaler(train_obs, scaler)
    end = r0data.fit_end(len(train_obs))
    fit_edges = r0data.fit_window_edges(len(train_obs))
    gate_fn = _xlstm_gate_v1_1 if backbone == "xlstm" else _lstm_gate_v1
    try:
        gate = gate_fn(models, model, _parity_inputs(machine, scaled_train[:end], fit_edges))
    except r0data.ProtocolViolation as error:  # sealed observer raised on a parity failure
        gate = {"name": plan["gate"], "pass": False, "error": str(error)}
    if not gate["pass"]:
        write_immutable(record_path, {"stage": "extract", "protocol_version": PROTOCOL_VERSION, "status": "STOP_CHECKPOINT_GATE",
                                      "run": name, "extraction_backend": plan["backend"], "gate": gate,
                                      "execution_commit": git_head(), "finished_utc": utc()})
        raise SystemExit(f"{name}: checkpoint gate failed — R0 stops")
    val_edges = r0data.validation_window_edges(len(train_obs))
    validation = models.extract_windows(model, arch, r0data.window_matrix(scaled_train, val_edges))
    threshold = r0probe.calibration_threshold(validation["score"])
    test_obs = r0data.load_observations(machine, "test")
    scaled_test = r0data.apply_scaler(test_obs, scaler)
    edges = r0data.test_window_edges(len(test_obs))
    test = models.extract_windows(model, arch, r0data.window_matrix(scaled_test, edges))
    history = history14(test["score"])
    internal = expand_internal234(test["internal_base18"])
    finite = np.isfinite(history).all(1) & np.isfinite(internal).all(1)
    warm = edges < r0data.FIRST_FINITE
    if history.shape != (len(edges), 14) or internal.shape != (len(edges), 234):
        raise r0data.ProtocolViolation("feature dimension drift")
    if not finite[~warm].all() or finite[warm].any():
        raise r0data.ProtocolViolation("feature warm-up/finiteness contract violated")
    cache = data_dir / CACHE_FILE
    if cache.exists():
        raise r0data.ProtocolViolation("v1.1 feature cache already exists")
    arrays = {"edges": edges, "score": test["score"], "internal_base18": test["internal_base18"], "H": history,
              "internal234": internal, "validation_edges": val_edges, "validation_score": validation["score"]}
    np.savez(cache, **arrays)
    _assert_no_labels("extraction")
    record = {
        "stage": "extract", "protocol_version": PROTOCOL_VERSION, "status": "PASS", "run": name, "machine": machine,
        "backbone": backbone, "seed": seed, "execution_commit": git_head(), "protocol_head": PROTOCOL_HEAD,
        "environment": environment, "extraction_backend": plan["backend"], "observer_arch": arch,
        "extraction_path": ("vanilla xLSTM backend + phase_e2_observer scalar reference observer" if backbone == "xlstm"
                            else "matched LSTM + manual replay observer (unchanged from r0-v1)"),
        "best_checkpoint_sha256": train_record["checkpoints"]["best.pt"], "best_model_hash": train_record["best_model_hash"],
        "checkpoint_reuse_authorised_by_v1_1": name in AMENDMENT["reused_checkpoints"]["units"],
        "gate": gate, "threshold": threshold, "validation_windows": int(len(val_edges)),
        "test_rows": int(len(edges)), "test_edge_range": [int(edges[0]), int(edges[-1])],
        "first_finite_edge": int(edges[np.flatnonzero(finite)[0]]), "warmup_rows": int(warm.sum()),
        "dimensions": {"H": int(history.shape[1]), "internal234": int(internal.shape[1])},
        "feature_cache": {"file": str(cache.relative_to(ROOT)) if cache.is_relative_to(ROOT) else cache.name,
                          "sha256": sha_file(cache), "arrays": {k: array_sha(v) for k, v in arrays.items()}},
        "labels_read": False, "label_read_count": len(r0data.label_access_log()), "seconds": time.perf_counter() - start,
        "finished_utc": utc(),
    }
    validate_extract_record(record, backbone)
    write_immutable(record_path, record)
    return record


# --------------------------------------------------------------------------- scheduling (<= 2 concurrent)


def _unit_done(machine: str, backbone: str, seed: int) -> bool:
    name = run_name(machine, backbone, seed)
    train_path, extract_path = _train_record_path(name), _extract_record_path(name)
    if not (train_path.exists() and read_json(train_path)["status"] == "PASS" and extract_path.exists()):
        return False
    try:
        validate_extract_record(read_json(extract_path), backbone)
    except r0data.ProtocolViolation:
        return False
    return True


def _run_unit(machine: str, backbone: str, seed: int) -> tuple[str, int, str]:
    name = run_name(machine, backbone, seed)
    log_dir = RUNS_DATA / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    codes = []
    for stage in ("train", "extract"):
        record = (_train_record_path if stage == "train" else _extract_record_path)(name)
        if record.exists() and read_json(record)["status"] == "PASS":
            continue
        with open(log_dir / f"{stage}_{name}.log", "a") as log:
            code = subprocess.run([sys.executable, str(Path(__file__)), stage, "--machine", machine, "--backbone", backbone,
                                   "--seed", str(seed)], stdout=log, stderr=subprocess.STDOUT, cwd=ROOT).returncode
        codes.append(code)
        if code != 0:
            return name, code, stage
    return name, 0, "done"


def _commit_push(message: str, paths: list[Path]) -> dict[str, Any]:
    rels = [str(p.relative_to(ROOT)) for p in paths if p.exists()]
    if not rels:
        return {"committed": False}
    git("add", "--", *rels)
    if subprocess.run(["git", "-C", str(ROOT), "diff", "--cached", "--quiet"]).returncode == 0:
        return {"committed": False}
    git("commit", "-q", "-m", message)
    push = subprocess.run(["git", "-C", str(ROOT), "push", "-q", "origin", f"HEAD:{BRANCH}"], capture_output=True, text=True)
    return {"committed": True, "commit": git_head(), "pushed": push.returncode == 0, "push_stderr": push.stderr[-300:]}


def schedule(workers: int) -> int:
    limit = MAX_CONCURRENT_DETECTOR_PROCESSES
    if workers < 1 or workers > limit:
        raise r0data.ProtocolViolation(f"at most {limit} concurrent detector processes")
    if not PREFLIGHT_V1_1.exists() or read_json(PREFLIGHT_V1_1)["status"] != "R0_V1_1_READY_TO_RESUME":
        raise r0data.ProtocolViolation("r0-v1.1 preflight has not passed")
    pending = [u for u in planned_runs() if not _unit_done(*u)]
    print(json.dumps({"schedule": [run_name(*u) for u in pending], "workers": workers, "utc": utc()}), flush=True)
    failed = None
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        queue = list(pending)
        running: dict[concurrent.futures.Future, tuple[str, str, int]] = {}
        while queue or running:
            while queue and len(running) < workers and failed is None:
                unit = queue.pop(0)
                running[pool.submit(_run_unit, *unit)] = unit
            if not running:
                break
            done, _ = concurrent.futures.wait(running, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                unit = running.pop(future)
                name, code, stage = future.result()
                git_result = _commit_push(f"Record R0 detector run {name}",
                                          [_train_record_path(name), _extract_record_path(name)])
                print(json.dumps({"unit": name, "exit": code, "stage": stage, "git": git_result, "utc": utc()}), flush=True)
                if code != 0:
                    failed = (name, stage, code)
            if failed is not None:
                queue.clear()
    if failed:
        print(json.dumps({"schedule_status": "STOPPED", "failed": failed}), flush=True)
        return 3
    print(json.dumps({"schedule_status": "COMPLETE", "utc": utc()}), flush=True)
    return 0


# --------------------------------------------------------------------------- r0-v1.1: invalidate v1 caches, preflight


def invalidate_v1_caches() -> dict[str, Any]:
    """Retire every v1 CUDA-path cache before any v1.1 extraction (hash-checked rename; record kept)."""
    rows = {}
    for name, entry in AMENDMENT["invalidated_v1_caches"].items():
        machine, backbone, seed = name.rsplit("_", 2)
        v1_record = read_json(_v1_extract_record_path(name))
        run_dir = _run_dir(machine, backbone, int(seed))
        original, retired = run_dir / "features.npz", run_dir / INVALIDATED_V1_CACHE_FILE
        row = {"v1_record_status": v1_record["status"], "v1_cache_sha256": entry.get("v1_cache_sha256")}
        if entry.get("v1_cache_sha256") is None:
            row.update({"status": entry["status"], "file_present": original.exists()})
            if original.exists():
                raise r0data.ProtocolViolation(f"{name}: unexpected v1 cache for a stopped unit")
        else:
            if original.exists():
                if sha_file(original) != entry["v1_cache_sha256"]:
                    raise r0data.ProtocolViolation(f"{name}: v1 cache hash differs from the v1 record")
                os.replace(original, retired)
            if sha_file(retired) != entry["v1_cache_sha256"]:
                raise r0data.ProtocolViolation(f"{name}: retired v1 cache hash mismatch")
            row.update({"status": "INVALIDATED_BY_R0_V1_1_EXTRACTION_AMENDMENT", "retired_file": INVALIDATED_V1_CACHE_FILE})
        rows[name] = row
    record = {"stage": "v1_cuda_cache_invalidation", "protocol_version": PROTOCOL_VERSION, "caches": rows,
              "labels_read": False, "execution_commit": git_head(), "finished_utc": utc()}
    write_immutable(INVALIDATION_RECORD, record)
    return record


def preflight_v1_1() -> dict[str, Any]:
    """Result-blind v1.1 preflight on the six reused xLSTM checkpoints (vanilla/reference path only)."""
    import real_data_r0_preflight as pf

    pf.install_metric_trap()  # before any model import
    from unittest.mock import patch

    import torch

    import real_data_r0_models as models
    from phase_g1_core import expand_internal234, history14

    sealed = read_json(ROOT / "research" / "real_data_r0" / "preflight.json")["code_sha256"]
    current = {k: sha_file(ROOT / k) for k in sealed}
    cuda_calls: list[str] = []

    def forbidden(*args, **kwargs):
        cuda_calls.append("cuda_overlay")
        raise r0data.ProtocolViolation("CUDA overlay forbidden in r0-v1.1 scientific extraction")

    environment = models.configure()
    units = {}
    with patch.object(models, "cuda_overlay_from_vanilla", forbidden), patch.object(models, "build_xlstm_cuda", forbidden):
        for name, reused in AMENDMENT["reused_checkpoints"]["units"].items():
            machine, backbone, seed = name.rsplit("_", 2)
            seed = int(seed)
            train_record = read_json(_train_record_path(name))
            best = _run_dir(machine, backbone, seed) / "best.pt"
            row: dict[str, Any] = {"checkpoint_sha256": sha_file(best)}
            row["checkpoint_matches_train_record"] = row["checkpoint_sha256"] == train_record["checkpoints"]["best.pt"] == reused["best_checkpoint_sha256"]
            model = models.build_xlstm_vanilla(seed)
            model.load_state_dict(torch.load(best, map_location="cpu", weights_only=True)["model"], strict=True)
            model.eval()
            for parameter in model.parameters():
                parameter.requires_grad_(False)
            row["model_hash_matches"] = models.model_hash(model) == train_record["best_model_hash"] == reused["best_model_hash"]
            row["parameters"] = int(sum(p.numel() for p in model.parameters()))
            train_obs = r0data.load_observations(machine, "train")
            scaler = r0data.fit_scaler(train_obs)
            scaled = r0data.apply_scaler(train_obs, scaler)
            end = r0data.fit_end(len(train_obs))
            fit_edges = r0data.fit_window_edges(len(train_obs))
            row["gate"] = _xlstm_gate_v1_1(models, model, _parity_inputs(machine, scaled[:end], fit_edges))
            stream = scaled[:400].copy()
            perturbed = stream.copy()
            perturbed[250:] += np.random.default_rng(1).normal(size=perturbed[250:].shape).astype(np.float32) * 5.0
            edges = np.arange(63, 400, dtype=np.int64)
            a = models.extract_windows(model, EXTRACTION_PLAN["xlstm"]["arch"], r0data.window_matrix(stream, edges))
            b = models.extract_windows(model, EXTRACTION_PLAN["xlstm"]["arch"], r0data.window_matrix(perturbed, edges))
            ha, hb = history14(a["score"]), history14(b["score"])
            ia, ib = expand_internal234(a["internal_base18"]), expand_internal234(b["internal_base18"])
            before = edges < 250
            finite = np.isfinite(ha).all(1) & np.isfinite(ia).all(1)
            row["causality"] = {
                "past_rows_bitwise_equal": bool(np.array_equal(a["score"][before], b["score"][before])
                                                and np.array_equal(a["internal_base18"][before], b["internal_base18"][before])
                                                and np.array_equal(ha[before], hb[before], equal_nan=True)
                                                and np.array_equal(ia[before], ib[before], equal_nan=True)),
                "future_rows_changed": bool(not np.array_equal(a["score"][~before], b["score"][~before])),
                "H_dim": int(ha.shape[1]), "internal234_dim": int(ia.shape[1]),
                "first_finite_edge": int(edges[np.flatnonzero(finite)[0]]), "warmup_rows": int((~finite).sum()),
            }
            c = row["causality"]
            row["pass"] = bool(row["checkpoint_matches_train_record"] and row["model_hash_matches"]
                               and row["parameters"] == DETECTOR["xlstm"]["trainable_parameters"] and row["gate"]["pass"]
                               and c["past_rows_bitwise_equal"] and c["future_rows_changed"] and c["H_dim"] == 14
                               and c["internal234_dim"] == 234 and c["first_finite_edge"] == 94 and c["warmup_rows"] == 31)
            units[name] = row
    checks = {
        "six_reused_checkpoints_pass": len(units) == 6 and all(u["pass"] for u in units.values()),
        "sealed_library_and_config_unchanged": current == sealed,
        "cuda_overlay_never_called": not cuda_calls,
        "no_label_access": not r0data.label_access_log(),
        "no_metric_calls": not pf._METRIC_CALLS,
        "amendment_protocol_version": PROTOCOL_VERSION == "r0-v1.1",
        "v1_caches_invalidated": INVALIDATION_RECORD.exists() and all(
            v["status"].startswith(("INVALIDATED", "NO_V1_CACHE")) for v in read_json(INVALIDATION_RECORD)["caches"].values()),
    }
    status = "R0_V1_1_READY_TO_RESUME" if all(checks.values()) else "R0_V1_1_BLOCKED"
    record = {"stage": "preflight_v1_1", "protocol_version": PROTOCOL_VERSION, "status": status, "checks": checks,
              "units": units, "environment": environment, "sealed_code_sha256": sealed, "current_code_sha256": current,
              "label_access_log": r0data.label_access_log(), "metric_calls": list(pf._METRIC_CALLS),
              "cuda_overlay_calls": len(cuda_calls), "execution_commit": git_head(), "finished_utc": utc()}
    write_immutable(PREFLIGHT_V1_1, record)
    return record


# --------------------------------------------------------------------------- seal features


def seal_features() -> dict[str, Any]:
    if FEATURE_MANIFEST.exists():
        raise r0data.ProtocolViolation("feature manifest already sealed")
    entries = []
    for machine, backbone, seed in planned_runs():
        name = run_name(machine, backbone, seed)
        extract_record = read_json(_extract_record_path(name))
        train_record = read_json(_train_record_path(name))
        if train_record["status"] != "PASS":
            raise r0data.ProtocolViolation(f"{name} is not a passing unit")
        validate_extract_record(extract_record, backbone)
        if extract_record["best_checkpoint_sha256"] != train_record["checkpoints"]["best.pt"]:
            raise r0data.ProtocolViolation(f"{name} checkpoint identity changed")
        reused = AMENDMENT["reused_checkpoints"]["units"].get(name)
        if reused and (reused["best_checkpoint_sha256"] != train_record["checkpoints"]["best.pt"]
                       or reused["best_model_hash"] != train_record["best_model_hash"]):
            raise r0data.ProtocolViolation(f"{name} reused checkpoint differs from the amendment record")
        cache = _run_dir(machine, backbone, seed) / CACHE_FILE
        digest = sha_file(cache)
        if digest != extract_record["feature_cache"]["sha256"]:
            raise r0data.ProtocolViolation(f"{name} feature cache hash drift")
        entries.append({"run": name, "machine": machine, "backbone": backbone, "seed": seed,
                        "extraction_backend": extract_record["extraction_backend"],
                        "feature_cache_file": f"data/r0_runs/{machine}/{backbone}_{seed}/{CACHE_FILE}",
                        "feature_cache_sha256": digest, "arrays": extract_record["feature_cache"]["arrays"],
                        "threshold": extract_record["threshold"], "test_rows": extract_record["test_rows"],
                        "best_checkpoint_sha256": extract_record["best_checkpoint_sha256"],
                        "train_record_sha256": sha_file(_train_record_path(name)),
                        "extract_record_sha256": sha_file(_extract_record_path(name))})
    if len(entries) != 18:
        raise r0data.ProtocolViolation("expected 18 feature caches")
    backends = {b: sorted({e["extraction_backend"] for e in entries if e["backbone"] == b}) for b in BACKBONES}
    if backends != {"xlstm": ["vanilla_reference"], "lstm": ["lstm_manual_replay"]}:
        raise r0data.ProtocolViolation(f"mixed or unexpected extraction backends: {backends}")
    manifest = {"stage": "feature_cache_seal", "protocol_version": PROTOCOL_VERSION, "backends": backends,
                "n_caches": len(entries), "entries": entries,
                "labels_read_before_seal": False, "execution_commit": git_head(), "sealed_utc": utc()}
    _assert_no_labels("feature sealing")
    write_immutable(FEATURE_MANIFEST, manifest)
    return manifest


# --------------------------------------------------------------------------- probe (first label access)


def _block_indices(edges: np.ndarray, test_n: int) -> dict[str, np.ndarray]:
    if edges[0] != r0data.FIRST_DECISION or not np.array_equal(edges, np.arange(r0data.FIRST_DECISION, test_n)):
        raise r0data.ProtocolViolation("test edges are not the contiguous stream [63, test_N)")
    return {block: r0data.block_rows(test_n, block) - r0data.FIRST_DECISION for block in ("train", "validation", "test")}


def probe(require_committed_manifest: bool = True) -> dict[str, Any]:
    if not FEATURE_MANIFEST.exists():
        raise r0data.ProtocolViolation("feature caches are not sealed")
    if require_committed_manifest and not (is_committed_clean(FEATURE_MANIFEST) and is_pushed()):
        raise r0data.ProtocolViolation("feature manifest must be committed and pushed before any label is read")
    if r0data.label_access_log():
        raise r0data.ProtocolViolation("labels were read before the probe stage")
    manifest = read_json(FEATURE_MANIFEST)
    records = []
    for entry in manifest["entries"]:
        name, machine = entry["run"], entry["machine"]
        record_path = _probe_record_path(name)
        if record_path.exists():
            raise r0data.ProtocolViolation(f"{name} already probed")
        cache = _run_dir(machine, entry["backbone"], entry["seed"]) / CACHE_FILE
        if sha_file(cache) != entry["feature_cache_sha256"]:
            raise r0data.ProtocolViolation(f"{name} feature cache changed after sealing")
        with np.load(cache) as loaded:
            edges, history, internal = loaded["edges"], loaded["H"], loaded["internal234"]
        test_n = int(CONFIG["dataset"]["expected"][machine]["test_N"])
        rows = _block_indices(edges, test_n)
        labels = r0data.load_test_labels(machine, purpose="probe_fit_selection")
        window = r0data.window_any_labels(labels, edges)
        y_train, y_validation = window[rows["train"]].copy(), window[rows["validation"]].copy()
        del labels, window

        def load_probe_test_labels(machine=machine, edges=edges, test_rows=rows["test"]):
            return r0data.window_any_labels(r0data.load_test_labels(machine, purpose="probe_final_evaluation"), edges)[test_rows]

        arms = {}
        for arm in r0probe.ARMS:
            x = {block: r0probe.arm_matrix(history[r], internal[r], arm) for block, r in rows.items()}
            arms[arm] = r0probe.select_and_evaluate(x["train"], y_train, x["validation"], y_validation,
                                                    x["test"], load_probe_test_labels)
        record = {"stage": "probe", "protocol_version": PROTOCOL_VERSION, "run": name, "machine": machine, "backbone": entry["backbone"], "seed": entry["seed"],
                  "design": CONFIG["probe"]["design"], "blocks": {k: list(v) for k, v in r0data.design_b_blocks(test_n).items()},
                  "embargo": r0data.EMBARGO, "rows": {k: int(len(v)) for k, v in rows.items()},
                  "positives": {"train": int(y_train.sum()), "validation": int(y_validation.sum())},
                  "arms": arms, "delta_ap": arms["H+I"]["test_ap"] - arms["H"]["test_ap"],
                  "feature_cache_sha256": entry["feature_cache_sha256"], "hgb_parameters": r0probe.HGB_PARAMETERS,
                  "execution_commit": git_head(), "finished_utc": utc()}
        write_immutable(record_path, record)
        records.append(record)
    summary = {"stage": "probe_summary", "cells": len(records), "hgb_fits": 2 * 2 * len(records),
               "label_access_log": r0data.label_access_log(), "finished_utc": utc()}
    write_immutable(RUN_RECORDS / "probe_label_access_log.json", summary)
    return summary


# --------------------------------------------------------------------------- aggregate / sanity / report


def _matrix(records: dict[str, dict[str, Any]], backbone: str) -> np.ndarray:
    return np.array([[records[run_name(m, backbone, s)]["delta_ap"] for s in SEEDS] for m in MACHINES], dtype=np.float64)


def aggregate() -> dict[str, Any]:
    if RESULTS_JSON.exists():
        raise r0data.ProtocolViolation("results.json already sealed")
    records = {run_name(*u): read_json(_probe_record_path(run_name(*u))) for u in planned_runs()}
    estimand = CONFIG["estimand"]
    backbones = {}
    for backbone in BACKBONES:
        matrix = _matrix(records, backbone)
        summary = r0probe.summarize_matrix(matrix, MACHINES, SEEDS)
        two_way = r0probe.two_way_bootstrap(matrix, draws=estimand["two_way_bootstrap"]["draws"], seed=estimand["two_way_bootstrap"]["seed"])
        machine_only = r0probe.machine_only_bootstrap(matrix, draws=estimand["machine_only_bootstrap"]["draws"],
                                                      seed=estimand["machine_only_bootstrap"]["seed"])
        backbones[backbone] = {
            "matrix_rows": list(MACHINES), "matrix_columns": list(SEEDS), "delta_ap_matrix": matrix.tolist(),
            "summary": summary, "two_way_bootstrap": two_way, "machine_only_bootstrap": machine_only,
            "classification": r0probe.classify(summary, two_way, machine_only),
            "cells": {run_name(m, backbone, s): {
                "ap_H": records[run_name(m, backbone, s)]["arms"]["H"]["test_ap"],
                "ap_H+I": records[run_name(m, backbone, s)]["arms"]["H+I"]["test_ap"],
                "selected_max_iter": {a: records[run_name(m, backbone, s)]["arms"][a]["selected_max_iter"] for a in r0probe.ARMS},
                "validation_ap": {a: records[run_name(m, backbone, s)]["arms"][a]["validation_ap"] for a in r0probe.ARMS},
                "delta_ap": records[run_name(m, backbone, s)]["delta_ap"]} for m in MACHINES for s in SEEDS},
        }
    result = {"stage": "R0 results", "protocol_version": PROTOCOL_VERSION, "protocol_head": PROTOCOL_HEAD,
              "feature_manifest_sha256": sha_file(FEATURE_MANIFEST), "design": CONFIG["probe"]["design"],
              "estimand": "delta_AP = AP_test(H+internal234) - AP_test(H)", "backbones": backbones,
              "uncertainty_label": estimand["uncertainty_label"], "never_claim": list(r0probe.NEVER_CLAIM),
              "probe_record_sha256": {k: sha_file(_probe_record_path(k)) for k in records},
              "execution_commit": git_head(), "finished_utc": utc()}
    write_immutable(RESULTS_JSON, result)
    return result


def sanity(require_committed_results: bool = True) -> dict[str, Any]:
    if require_committed_results and not is_committed_clean(RESULTS_JSON):
        raise r0data.ProtocolViolation("results.json must be committed before the detector-sanity report")
    if SANITY_JSON.exists():
        raise r0data.ProtocolViolation("detector sanity already written")
    manifest = read_json(FEATURE_MANIFEST)
    rows = {}
    labels_cache: dict[str, np.ndarray] = {}
    for entry in manifest["entries"]:
        machine = entry["machine"]
        cache = _run_dir(machine, entry["backbone"], entry["seed"]) / CACHE_FILE
        if sha_file(cache) != entry["feature_cache_sha256"]:
            raise r0data.ProtocolViolation("feature cache changed after sealing")
        with np.load(cache) as loaded:
            edges, score = loaded["edges"], loaded["score"]
        if machine not in labels_cache:
            labels_cache[machine] = r0data.load_test_labels(machine, purpose="detector_sanity")
        y = r0data.window_any_labels(labels_cache[machine], edges)
        rows[entry["run"]] = {"machine": machine, "backbone": entry["backbone"], "seed": entry["seed"],
                              **r0probe.detector_sanity(score, y, entry["threshold"])}
    scaling = {}
    for machine in MACHINES:
        record = read_json(_train_record_path(run_name(machine, BACKBONES[0], SEEDS[0])))
        scale = np.asarray(record["scaler"]["scale"])
        nonzero = np.flatnonzero(scale != 1.0)
        smallest = int(nonzero[np.argmin(scale[nonzero])]) if len(nonzero) else None
        scaling[machine] = {"zero_std_channels": record["scaler"]["zero_std_channels"], "smallest_std_channel": smallest,
                            "smallest_std": float(scale[smallest]) if smallest is not None else None}
    result = {"stage": "detector_sanity", "rows_definition": CONFIG["detector_sanity"]["rows"], "label": "window_any_anomaly",
              "detectors": rows, "near_constant_channel_note": scaling,
              "status": CONFIG["detector_sanity"]["status"], "finished_utc": utc()}
    write_immutable(SANITY_JSON, result)
    return result


def _fmt(value: float, digits: int = 4) -> str:
    return f"{value:+.{digits}f}"


def report() -> str:
    results, sanity_rows = read_json(RESULTS_JSON), read_json(SANITY_JSON)
    lines = ["# R0 results — source-native SMD recurrent-state measurement (Design B, r0-v1.1)", "",
             f"Protocol `{PROTOCOL_HEAD}` with amendment r0-v1.1 (xLSTM features from the vanilla backend + scalar "
             "reference observer). Estimand per cell: `ΔAP = AP_test(H+internal234) − AP_test(H)` on the frozen "
             "probe-test block of one machine and one detector. Design B is an offline within-machine diagnostic, not "
             "unseen-machine transfer. Intervals are exploratory resampling intervals (3 machines × 3 seeds), not "
             "calibrated population 95% CIs.", ""]
    for backbone in BACKBONES:
        b = results["backbones"][backbone]
        s = b["summary"]
        lines += [f"## {'xLSTM' if backbone == 'xlstm' else 'Matched LSTM'}", "",
                  "| machine | seed 11 | seed 22 | seed 33 | machine mean |", "|---|---:|---:|---:|---:|"]
        for i, machine in enumerate(MACHINES):
            cells = " | ".join(_fmt(v) for v in b["delta_ap_matrix"][i])
            lines.append(f"| {machine} | {cells} | {_fmt(s['machine_means'][machine])} |")
        seeds = " | ".join(_fmt(s["seed_means"][str(seed)]) for seed in SEEDS)
        lines += [f"| seed mean | {seeds} | {_fmt(s['mean'])} |", "",
                  f"Mean ΔAP {_fmt(s['mean'])}; positive cells {s['positive_cells']}/9; two-way interval "
                  f"[{_fmt(b['two_way_bootstrap']['lower'])}, {_fmt(b['two_way_bootstrap']['upper'])}]; machine-only interval "
                  f"[{_fmt(b['machine_only_bootstrap']['lower'])}, {_fmt(b['machine_only_bootstrap']['upper'])}].", "",
                  f"**Classification: `{b['classification']['class']}`.** {b['classification']['wording']}", "",
                  "| cell | AP(H) | AP(H+I) | ΔAP | selected max_iter H / H+I |", "|---|---:|---:|---:|---|"]
        for name, cell in b["cells"].items():
            lines.append(f"| {name} | {cell['ap_H']:.4f} | {cell['ap_H+I']:.4f} | {_fmt(cell['delta_ap'])} | "
                         f"{cell['selected_max_iter']['H']} / {cell['selected_max_iter']['H+I']} |")
        lines.append("")
    lines += ["## Detector sanity (diagnostic context only; computed after the probe matrices were sealed)", "",
              "| detector | AP | AUROC | recall@thr | FPR@thr | window prevalence | flag |", "|---|---:|---:|---:|---:|---:|---|"]
    for name, row in sanity_rows["detectors"].items():
        flag = "DETECTOR_WEAK" if row["detector_weak_flag"] else ""
        lines.append(f"| {name} | {row['ap']:.4f} | {row['auroc']:.4f} | {row['recall_at_threshold']:.4f} | "
                     f"{row['fpr_at_threshold']:.4f} | {row['window_prevalence']:.4f} | {flag} |")
    note = sanity_rows["near_constant_channel_note"]
    lines += ["", "Near-constant fit channels (sealed zero-std-only scaler; no post-hoc repair): " + "; ".join(
        f"{m}: zero-std {v['zero_std_channels']}, smallest non-zero std channel {v['smallest_std_channel']} "
        f"({v['smallest_std']:.3g})" for m, v in note.items()) + ".", "",
              "Never claimed from R0: " + "; ".join(results["never_claim"]) + ".", ""]
    text = "\n".join(lines)
    (RESULTS / "results.md").write_text(text)
    return text


# --------------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="R0 execution runner (thin orchestration)")
    sub = parser.add_subparsers(dest="command", required=True)
    for stage in ("train", "extract"):
        p = sub.add_parser(stage)
        p.add_argument("--machine", required=True, choices=MACHINES)
        p.add_argument("--backbone", required=True, choices=BACKBONES)
        p.add_argument("--seed", required=True, type=int, choices=SEEDS)
    sch = sub.add_parser("schedule")
    sch.add_argument("--workers", type=int, default=2)
    for stage in ("invalidate-v1-caches", "preflight-v1-1", "seal-features", "probe", "aggregate", "sanity", "report", "status"):
        sub.add_parser(stage)
    args = parser.parse_args(argv)
    if args.command == "train":
        record = train(args.machine, args.backbone, args.seed)
        print(json.dumps({"run": record["run"], "status": record["status"], "selected_epoch": record["selected_epoch"]}))
    elif args.command == "extract":
        record = extract(args.machine, args.backbone, args.seed)
        print(json.dumps({"run": record["run"], "status": record["status"], "gate": record["gate"]["pass"],
                          "backend": record["extraction_backend"]}))
    elif args.command == "schedule":
        return schedule(args.workers)
    elif args.command == "invalidate-v1-caches":
        print(json.dumps({k: v["status"] for k, v in invalidate_v1_caches()["caches"].items()}))
    elif args.command == "preflight-v1-1":
        record = preflight_v1_1()
        print(json.dumps({"status": record["status"], "failed": [k for k, v in record["checks"].items() if not v]}))
        return 0 if record["status"] == "R0_V1_1_READY_TO_RESUME" else 2
    elif args.command == "seal-features":
        print(json.dumps({"sealed": seal_features()["n_caches"]}))
    elif args.command == "probe":
        print(json.dumps({"probe_cells": probe()["cells"]}))
    elif args.command == "aggregate":
        result = aggregate()
        print(json.dumps({b: result["backbones"][b]["classification"]["class"] for b in BACKBONES}))
    elif args.command == "sanity":
        print(json.dumps({"detectors": len(sanity()["detectors"])}))
    elif args.command == "report":
        report()
        print(json.dumps({"results_md": True}))
    else:
        print(json.dumps({run_name(*u): _unit_done(*u) for u in planned_runs()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
