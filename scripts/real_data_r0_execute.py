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

    train    --machine M --backbone {xlstm,lstm} --seed S   train split only, no label file opened
    extract  --machine M --backbone B --seed S              checkpoint parity gate, validation + test features
    schedule --workers 2                                    18 x (train, extract), <= 2 concurrent, commit+push per run
    seal-features                                           feature_cache_manifest.json over all 18 caches
    probe                                                   requires the committed manifest; first label access
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
FEATURE_MANIFEST = RESULTS / "feature_cache_manifest.json"
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
    return RUN_RECORDS / f"extract_{name}.json"


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


def _parity_gate(models, backbone: str, reference, model, inputs) -> dict[str, Any]:
    import torch

    import real_data_r0_preflight as pf

    result: dict[str, Any] = {}
    for label, x in inputs.items():
        row: dict[str, Any] = {}
        if backbone == "xlstm":
            with torch.no_grad():
                plain_reference, plain_fast = reference(x), model(x)
            out_r, score_r, base_r = models.extract_batch(reference, "xlstm_reference", x)
            out_f, score_f, base_f = models.extract_batch(model, "xlstm", x)
            row["reference_observer_on_off"] = pf._cmp(plain_reference, out_r, exact=True)
            row["fast_observer_on_off"] = pf._cmp(plain_fast, out_f, exact=True)
            row["vanilla_vs_cuda_output"] = pf._cmp(out_r, out_f)
            row["reference_vs_fast_score"] = pf._cmp(score_r, score_f)
            row["reference_vs_fast_common18"] = pf._cmp(base_r, base_f)
        else:
            with torch.no_grad():
                plain = model(x)
            out, _score, base = models.extract_batch(model, "lstm", x)  # manual replay parity enforced inside
            row["observer_on_off"] = pf._cmp(plain, out, exact=True)
            row["replay_parity"] = {"pass": True, "bitwise": None, "max_abs": None}
        result[label] = row
    on_off = [v["bitwise"] for r in result.values() for k, v in r.items() if k.endswith("on_off")]
    close = [v["pass"] for r in result.values() for k, v in r.items() if not k.endswith("on_off")]
    result["pass"] = bool(all(on_off) and all(close))
    return result


def extract(machine: str, backbone: str, seed: int) -> dict[str, Any]:
    import torch

    import real_data_r0_models as models
    from phase_g1_core import expand_internal234, history14

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
    if backbone == "xlstm":
        model, arch = models.cuda_overlay_from_vanilla(reference), "xlstm"
    else:
        model, arch = reference, "lstm"
    train_obs = r0data.load_observations(machine, "train")
    scaler = r0data.fit_scaler(train_obs)
    if _scaler_record(scaler)["scale_sha256"] != train_record["scaler"]["scale_sha256"] or \
            _scaler_record(scaler)["mean_sha256"] != train_record["scaler"]["mean_sha256"]:
        raise r0data.ProtocolViolation("scaler drift between train and extract")
    scaled_train = r0data.apply_scaler(train_obs, scaler)
    end = r0data.fit_end(len(train_obs))
    fit_edges = r0data.fit_window_edges(len(train_obs))
    try:
        parity = _parity_gate(models, backbone, reference, model, _parity_inputs(machine, scaled_train[:end], fit_edges))
    except r0data.ProtocolViolation as error:  # sealed observer raised on a parity failure
        parity = {"pass": False, "error": str(error)}
    if not parity["pass"]:
        write_immutable(record_path, {"stage": "extract", "status": "STOP_CHECKPOINT_PARITY", "run": name, "parity": parity,
                                      "execution_commit": git_head(), "finished_utc": utc()})
        raise SystemExit(f"{name}: checkpoint parity failed — R0 stops")
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
    cache = data_dir / "features.npz"
    arrays = {"edges": edges, "score": test["score"], "internal_base18": test["internal_base18"], "H": history,
              "internal234": internal, "validation_edges": val_edges, "validation_score": validation["score"]}
    np.savez(cache, **arrays)
    _assert_no_labels("extraction")
    record = {
        "stage": "extract", "status": "PASS", "run": name, "machine": machine, "backbone": backbone, "seed": seed,
        "execution_commit": git_head(), "protocol_head": PROTOCOL_HEAD, "environment": environment,
        "extraction_path": "CUDA overlay + FastStateObserver" if arch == "xlstm" else "matched LSTM + manual replay observer",
        "best_checkpoint_sha256": train_record["checkpoints"]["best.pt"], "best_model_hash": train_record["best_model_hash"],
        "parity": parity, "threshold": threshold, "validation_windows": int(len(val_edges)),
        "test_rows": int(len(edges)), "test_edge_range": [int(edges[0]), int(edges[-1])],
        "first_finite_edge": int(edges[np.flatnonzero(finite)[0]]), "warmup_rows": int(warm.sum()),
        "dimensions": {"H": int(history.shape[1]), "internal234": int(internal.shape[1])},
        "feature_cache": {"file": str(cache.relative_to(ROOT)) if cache.is_relative_to(ROOT) else cache.name,
                          "sha256": sha_file(cache), "arrays": {k: array_sha(v) for k, v in arrays.items()}},
        "labels_read": False, "seconds": time.perf_counter() - start, "finished_utc": utc(),
    }
    write_immutable(record_path, record)
    return record


# --------------------------------------------------------------------------- scheduling (<= 2 concurrent)


def _unit_done(machine: str, backbone: str, seed: int) -> bool:
    name = run_name(machine, backbone, seed)
    paths = (_train_record_path(name), _extract_record_path(name))
    return all(p.exists() and read_json(p)["status"] == "PASS" for p in paths)


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


# --------------------------------------------------------------------------- seal features


def seal_features() -> dict[str, Any]:
    if FEATURE_MANIFEST.exists():
        raise r0data.ProtocolViolation("feature manifest already sealed")
    entries = []
    for machine, backbone, seed in planned_runs():
        name = run_name(machine, backbone, seed)
        extract_record = read_json(_extract_record_path(name))
        train_record = read_json(_train_record_path(name))
        if extract_record["status"] != "PASS" or train_record["status"] != "PASS" or not extract_record["parity"]["pass"]:
            raise r0data.ProtocolViolation(f"{name} is not a passing unit")
        cache = _run_dir(machine, backbone, seed) / "features.npz"
        digest = sha_file(cache)
        if digest != extract_record["feature_cache"]["sha256"]:
            raise r0data.ProtocolViolation(f"{name} feature cache hash drift")
        entries.append({"run": name, "machine": machine, "backbone": backbone, "seed": seed,
                        "feature_cache_sha256": digest, "arrays": extract_record["feature_cache"]["arrays"],
                        "threshold": extract_record["threshold"], "test_rows": extract_record["test_rows"],
                        "best_checkpoint_sha256": extract_record["best_checkpoint_sha256"],
                        "train_record_sha256": sha_file(_train_record_path(name)),
                        "extract_record_sha256": sha_file(_extract_record_path(name))})
    if len(entries) != 18:
        raise r0data.ProtocolViolation("expected 18 feature caches")
    manifest = {"stage": "feature_cache_seal", "n_caches": len(entries), "entries": entries,
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
    if require_committed_manifest and not is_committed_clean(FEATURE_MANIFEST):
        raise r0data.ProtocolViolation("feature manifest must be committed before any label is read")
    if r0data.label_access_log():
        raise r0data.ProtocolViolation("labels were read before the probe stage")
    manifest = read_json(FEATURE_MANIFEST)
    records = []
    for entry in manifest["entries"]:
        name, machine = entry["run"], entry["machine"]
        record_path = _probe_record_path(name)
        if record_path.exists():
            raise r0data.ProtocolViolation(f"{name} already probed")
        cache = _run_dir(machine, entry["backbone"], entry["seed"]) / "features.npz"
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
        record = {"stage": "probe", "run": name, "machine": machine, "backbone": entry["backbone"], "seed": entry["seed"],
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
    result = {"stage": "R0 results", "protocol_head": PROTOCOL_HEAD, "design": CONFIG["probe"]["design"],
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
        cache = _run_dir(machine, entry["backbone"], entry["seed"]) / "features.npz"
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
    lines = ["# R0 results — source-native SMD recurrent-state measurement (Design B)", "",
             f"Protocol `{PROTOCOL_HEAD}`. Estimand per cell: `ΔAP = AP_test(H+internal234) − AP_test(H)` on the frozen "
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
    for stage in ("seal-features", "probe", "aggregate", "sanity", "report", "status"):
        sub.add_parser(stage)
    args = parser.parse_args(argv)
    if args.command == "train":
        record = train(args.machine, args.backbone, args.seed)
        print(json.dumps({"run": record["run"], "status": record["status"], "selected_epoch": record["selected_epoch"]}))
    elif args.command == "extract":
        record = extract(args.machine, args.backbone, args.seed)
        print(json.dumps({"run": record["run"], "status": record["status"], "parity": record["parity"]["pass"]}))
    elif args.command == "schedule":
        return schedule(args.workers)
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
