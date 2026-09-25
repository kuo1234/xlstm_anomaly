"""Isolated, resumable execution and pre-label sealing for M1 Stage 1A.

Importing this module never trains or opens data. The only public execution
entry point is ``run_stage1a``; it is intentionally not called automatically.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np

try:
    from scripts import adaptive_normality_m1_data as data
    from scripts import adaptive_normality_m1_execute as execute
    from scripts import adaptive_normality_m1_models as models
    from scripts import adaptive_normality_m1_scores as scores
except ImportError:  # direct script execution
    import adaptive_normality_m1_data as data
    import adaptive_normality_m1_execute as execute
    import adaptive_normality_m1_models as models
    import adaptive_normality_m1_scores as scores

ROOT = Path(__file__).resolve().parents[1]
AMENDMENT_PATH = Path("research/adaptive_normality_m1_smd/stage1a_futility_amendment.md")
MACHINE_LIST_PATH = Path("research/adaptive_normality_m1_smd/stage1a_machines.json")
BASE_DIR = Path("reports/adaptive_normality_m1_smd/stage1a_screen")
RUN_DIR = BASE_DIR / "runs"
SCORE_DIR = BASE_DIR / "scores"
SCORE_MANIFEST = BASE_DIR / "score_manifest.json"
EXECUTION_MANIFEST = BASE_DIR / "execution_calibration_manifest.json"
EXECUTION_SUMMARY = BASE_DIR / "execution_summary.json"
RESULTS_JSON = BASE_DIR / "stage1a_results.json"
RESULTS_MD = BASE_DIR / "stage1a_results.md"
LABEL_LOG = BASE_DIR / "label_access_log.json"
GATE_JSON = BASE_DIR / "futility_gate.json"
SCHEMA = "adaptive-normality-m1-stage1a-execution-calibration-v1"
SCORE_SCHEMA = "adaptive-normality-m1-stage1a-score-inventory-v1"
SCORE_NAMES = ("last_value", "moving_median", "var1", "xlstmad_f", "lstm_f",
               "cheap_control_fusion", "forecast_cheap_control_fusion")
RAW_NAMES = SCORE_NAMES[:5]
SEVERITY_NAMES = ("last_value", "moving_median", "var1", "xlstmad_f")
ARMS = ("xlstmad_f", "lstm_f")
SEED = 11
BATCH_SIZE = 128
MAX_EPOCHS = 50
QUANTILE = {"q": 0.99, "method": "higher"}


class Stage1AError(RuntimeError):
    pass


def _sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _sha_array(value: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def _git_head(repo: Path) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()


def selected_machines(manifest: Mapping | None = None) -> tuple[str, ...]:
    """Recompute the frozen selection from train_rows only and cross-check JSON."""
    doc = json.loads((ROOT / MACHINE_LIST_PATH).read_text())
    source = data.MANIFEST if manifest is None else manifest
    groups: dict[str, list[tuple[int, str]]] = {f"machine-{i}": [] for i in (1, 2, 3)}
    for machine, record in source["machines"].items():
        groups[machine.rsplit("-", 1)[0]].append((int(record["train_rows"]), machine))
    selected = []
    for group in ("machine-1", "machine-2", "machine-3"):
        ordered = sorted(groups[group], key=lambda pair: (pair[0], pair[1]))
        n = len(ordered)
        used: set[int] = set()
        for q in (0.25, 0.50, 0.75):
            rank = int(np.floor(q * (n - 1) + 0.5))
            if rank in used:
                rank = min((candidate for candidate in range(n) if candidate not in used),
                           key=lambda candidate: (abs(candidate-rank), candidate < rank, -candidate))
            used.add(rank)
            selected.append(ordered[rank][1])
    if tuple(selected) != tuple(doc["machines"]):
        raise Stage1AError("frozen Stage-1A machine list differs from train-metadata selection")
    return tuple(selected)


def _check_feature_hashes(machine: str, root: Path | None) -> dict[str, dict[str, Any]]:
    rows = {}
    for split in ("train", "test"):
        check = data.verify_observation(machine, split, root)
        if not check.get("match"):
            raise Stage1AError(f"{machine}: pinned {split} feature data hash/byte check failed")
        rows[split] = {"sha256": check["sha256"], "bytes": int(check["bytes"])}
    return rows


def _atomic_json(path: Path, doc: Mapping[str, Any], *, immutable: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if immutable and path.exists():
        raise FileExistsError(f"refusing to overwrite Stage-1A artifact {path}")
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".partial")
    tmp = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(doc, f, sort_keys=True, indent=2, allow_nan=False)
            f.write("\n"); f.flush(); os.fsync(f.fileno())
        if immutable:
            os.link(tmp, path)
        else:
            os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _write_npz(path: Path, arrays: Mapping[str, np.ndarray]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite Stage-1A artifact {path}")
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".partial")
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as f:
            np.savez_compressed(f, **arrays); f.flush(); os.fsync(f.fileno())
        os.link(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)
    return {"path": path.as_posix(), "sha256": _sha_file(path), "bytes": path.stat().st_size}


class _GpuSampler:
    """Best-effort 15-second nvidia-smi utilization sampler; never affects fit."""
    def __init__(self, device: str):
        self.device=device; self.stop=threading.Event(); self.values=[]; self.reason=None
        self.thread=None

    def _sample(self):
        if not self.device.startswith("cuda"):
            self.reason="fit device is not CUDA"; return
        try:
            index=self.device.split(":",1)[1] if ":" in self.device else "0"
            output=subprocess.check_output(["nvidia-smi",f"--id={index}",
                "--query-gpu=utilization.gpu,memory.used","--format=csv,noheader,nounits"],
                text=True,stderr=subprocess.DEVNULL,timeout=5).strip()
            util,mem=output.split(",",1)
            self.values.append((float(util.strip()),float(mem.strip())))
        except (OSError,subprocess.SubprocessError,ValueError,IndexError) as error:
            self.reason=f"nvidia-smi sampling unavailable: {type(error).__name__}"

    def _loop(self):
        self._sample()
        while not self.stop.wait(15): self._sample()

    def __enter__(self):
        self.thread=threading.Thread(target=self._loop,daemon=True); self.thread.start(); return self

    def __exit__(self,*_):
        self.stop.set()
        if self.thread is not None: self.thread.join(timeout=6)

    def record(self):
        if not self.values:
            return {"available":False,"sample_count":0,"reason":self.reason or "fit completed before first telemetry sample"}
        util=[x[0] for x in self.values]; mem=[x[1] for x in self.values]
        return {"available":True,"sample_count":len(util),"interval_seconds":15,
            "mean_gpu_utilization_percent":float(np.mean(util)),"max_gpu_utilization_percent":float(np.max(util)),
            "mean_memory_used_mib":float(np.mean(mem)),"max_memory_used_mib":float(np.max(mem)),
            "reason":self.reason}


def _load_or_reject_run(machine: str, source_commit: str) -> dict | None:
    folder = ROOT / RUN_DIR / machine
    record_path = folder / "machine_run.json"
    if not folder.exists():
        return None
    if not folder.is_dir() or not record_path.is_file():
        raise Stage1AError(f"{machine}: partial Stage-1A run exists; refusing to overwrite")
    record = json.loads(record_path.read_text())
    validate_run_record(machine, record, source_commit=source_commit)
    return record


def _validate_calibration_arrays(machine: str, record: Mapping[str, Any], arrays,
                                 train_rows: int) -> None:
    blocks=data.split_boundaries(train_rows)
    cal_start,cal_stop=blocks.calibration
    calibration_count=cal_stop-cal_start
    half=max(1,calibration_count//2)
    if half>=calibration_count:
        raise Stage1AError(f"{machine}: frozen calibration split cannot provide a threshold half")
    first=np.arange(cal_start,cal_start+half,dtype=np.int64)
    second=np.arange(cal_start+half,cal_stop,dtype=np.int64)
    metadata=record["calibration"]
    if (metadata.get("first_half_timestamps")!=[int(first[0]),int(first[-1]+1)] or
            metadata.get("threshold_timestamps")!=[int(second[0]),int(second[-1]+1)]):
        raise Stage1AError(f"{machine}: recorded calibration boundaries differ from frozen train split")
    timestamps=np.asarray(arrays["timestamps"])
    if not np.array_equal(timestamps,second):
        raise Stage1AError(f"{machine}: threshold samples do not occupy frozen calibration second half")
    for name in SEVERITY_NAMES:
        ref=np.asarray(arrays[f"tail_reference__{name}"]).reshape(-1)
        if (len(ref)!=half or len(ref)!=record["tail_reference_counts"].get(name) or
                _sha_array(ref)!=record["tail_reference_hashes"].get(name) or
                not np.isfinite(ref).all() or np.any(ref[1:]<ref[:-1])):
            raise Stage1AError(f"{machine}: {name} tail reference differs from frozen calibration first half")
    expected_thresholds={}
    for name in SCORE_NAMES:
        sample=np.asarray(arrays[f"threshold_scores__{name}"]).reshape(-1)
        if len(sample)!=len(second) or not np.isfinite(sample).all():
            raise Stage1AError(f"{machine}: {name} threshold samples differ from frozen calibration second half")
        expected_thresholds[name]=scores.higher_empirical_quantile(sample,.99)
    if expected_thresholds!=record.get("thresholds"):
        raise Stage1AError(f"{machine}: threshold differs from q=.99 higher calibration samples")


def validate_run_record(machine: str, record: Mapping[str, Any], *, source_commit: str | None=None,
                        repo: Path=ROOT, data_root: Path | None=None) -> None:
    """Recompute every threshold and validate the full machine artifact chain."""
    expected = {"machine": machine, "seed": SEED, "W": data.W, "status": "complete",
                "test_labels_read": False,"anomaly_metrics_computed": False,"arm_names":list(ARMS),
                "threshold_quantile":QUANTILE}
    if source_commit is not None: expected["source_commit"]=source_commit
    for key,value in expected.items():
        if record.get(key)!=value: raise Stage1AError(f"{machine}: run provenance differs at {key}")
    if set(record.get("feature_data",{}))!={"train","test"}:
        raise Stage1AError(f"{machine}: train/test feature hashes are required")
    for split,seal in record["feature_data"].items():
        observed=data.verify_observation(machine,split,data_root)
        if (not observed.get("match") or observed.get("sha256")!=seal.get("sha256") or
                int(observed.get("bytes",-1))!=seal.get("bytes")):
            raise Stage1AError(f"{machine}: pinned {split} feature hash/bytes differ")
    scaler=repo/record["scaler"]["path"]
    if not scaler.is_file() or _sha_file(scaler)!=record["scaler"].get("sha256"):
        raise Stage1AError(f"{machine}: scaler artifact missing or changed")
    with np.load(scaler,allow_pickle=False) as values:
        if set(values.files)!={"center","scale","raw_robust_scale","scale_floor","fit_rows"}:
            raise Stage1AError(f"{machine}: scaler artifact schema changed")
    if set(record.get("arms",{}))!=set(ARMS): raise Stage1AError(f"{machine}: exact two-arm run inventory required")
    for arm in ARMS:
        entry=record["arms"][arm]
        if entry.get("parameter_count")!=models.EXPECTED_PARAMETERS[arm]:
            raise Stage1AError(f"{machine}/{arm}: parameter count mismatch")
        cp=repo/entry["checkpoint_path"]; rp=repo/entry["run_record_path"]
        if not cp.is_file() or _sha_file(cp)!=entry.get("checkpoint_sha256"):
            raise Stage1AError(f"{machine}/{arm}: checkpoint missing or changed")
        if not rp.is_file() or _sha_file(rp)!=entry.get("run_record_sha256"):
            raise Stage1AError(f"{machine}/{arm}: arm run record missing or changed")
        fit=json.loads(rp.read_text())
        if (fit.get("arm_key")!=arm or fit.get("seed")!=SEED or
                fit.get("parameter_count")!=models.EXPECTED_PARAMETERS[arm] or
                fit.get("best_model_sha256")!=entry.get("model_state_sha256") or
                fit.get("best_checkpoint",{}).get("sha256")!=entry.get("checkpoint_sha256")):
            raise Stage1AError(f"{machine}/{arm}: checkpoint state/run hashes disagree")
    for key in ("calibration","scores"):
        item=record.get(key,{})
        artifact=repo/item.get("path","")
        if not artifact.is_file() or _sha_file(artifact)!=item.get("sha256"):
            raise Stage1AError(f"{machine}: {key} artifact missing or changed")
    calibration=repo/record["calibration"]["path"]
    with np.load(calibration,allow_pickle=False) as c:
        expected_arrays={"timestamps",*(f"tail_reference__{name}" for name in SEVERITY_NAMES),
                         *(f"threshold_scores__{name}" for name in SCORE_NAMES)}
        if set(c.files)!=expected_arrays: raise Stage1AError(f"{machine}: calibration inventory differs")
        train_rows=int(data.MANIFEST["machines"][machine]["train_rows"])
        _validate_calibration_arrays(machine,record,c,train_rows)
    score=repo/record["scores"]["path"]
    with np.load(score,allow_pickle=False) as s:
        if set(s.files)!={"timestamps",*SCORE_NAMES}: raise Stage1AError(f"{machine}: score inventory differs")
        times=np.asarray(s["timestamps"])
        test_rows=int(data.MANIFEST["machines"][machine]["test_rows"])
        if not np.array_equal(times,np.arange(data.W,test_rows)):
            raise Stage1AError(f"{machine}: test timestamps are not exactly [256,test_rows)")
        if _sha_array(times)!=record["scores"].get("timestamp_sha256"):
            raise Stage1AError(f"{machine}: score timestamp hash differs")
        for name in SCORE_NAMES:
            if s[name].shape!=times.shape or not np.isfinite(s[name]).all():
                raise Stage1AError(f"{machine}: score array invalid: {name}")


def _raw_calibration(train: np.ndarray, transform, fitted: Mapping[str, Any], device: str):
    blocks = data.split_boundaries(len(train))
    z = data.apply_robust_transform(train, transform)
    start, stop = blocks.calibration
    times = np.arange(start, stop, dtype=np.int64)
    raw: dict[str, np.ndarray] = {}
    for arm in ARMS:
        raw[arm] = execute.score_forecaster(fitted[arm], z, times, device=device)[0]
    last, _ = scores.last_value_score(z, np.arange(len(z)))
    med, _ = scores.moving_median_score(z, data.W, np.arange(len(z)))
    a, b = blocks.fit
    intercept, coef = scores.fit_ridge_var1(z[a:b], lam=1.0)
    var, _ = scores.ridge_var1_score(z, intercept, coef, np.arange(len(z)))
    raw.update(last_value=last[times-1], moving_median=med[times-data.W], var1=var[times-1])
    if set(raw) != set(RAW_NAMES) or any(v.shape != times.shape for v in raw.values()):
        raise Stage1AError("Stage-1A calibration score arrays have unexpected alignment")
    return times, raw


def _calibrate(raw: Mapping[str, np.ndarray], times: np.ndarray):
    half = max(1, len(times)//2)
    refs = {name: scores.fit_tail_rank(raw[name][:half]) for name in SEVERITY_NAMES}
    second_times = times[half:]
    sev = {name: scores.normal_tail_severity(raw[name][half:], refs[name]) for name in SEVERITY_NAMES}
    cheap = np.maximum.reduce([sev[k] for k in ("last_value", "moving_median", "var1")])
    forecast = np.maximum(cheap, sev["xlstmad_f"])
    threshold_samples = {**{k: v[half:] for k, v in raw.items()},
                         "cheap_control_fusion": cheap,
                         "forecast_cheap_control_fusion": forecast}
    thresholds = {k: scores.higher_empirical_quantile(v, 0.99) for k, v in threshold_samples.items()}
    return refs, threshold_samples, thresholds, second_times, times[:half], times[half:]


def _test_scores(train, test, transform, fitted, refs, device):
    z = data.apply_robust_transform(test, transform)
    times = np.arange(data.W, len(z), dtype=np.int64)
    if not len(times):
        raise Stage1AError("test data has no eligible forecast endpoint")
    raw = {arm: execute.score_forecaster(fitted[arm], z, times, device=device)[0] for arm in ARMS}
    last, _ = scores.last_value_score(z, np.arange(len(z)))
    med, _ = scores.moving_median_score(z, data.W, np.arange(len(z)))
    blocks = data.split_boundaries(len(train)); ztrain = data.apply_robust_transform(train, transform)
    a, b = blocks.fit
    intercept, coef = scores.fit_ridge_var1(ztrain[a:b], lam=1.0)
    var, _ = scores.ridge_var1_score(z, intercept, coef, np.arange(len(z)))
    raw.update(last_value=last[times-1], moving_median=med[times-data.W], var1=var[times-1])
    severity = {k: scores.normal_tail_severity(raw[k], refs[k]) for k in SEVERITY_NAMES}
    cheap = np.maximum.reduce([severity[k] for k in ("last_value", "moving_median", "var1")])
    fusion = {"cheap_control_fusion": cheap,
              "forecast_cheap_control_fusion": np.maximum(cheap, severity["xlstmad_f"])}
    all_scores = {k: np.asarray(raw[k], dtype=np.float64) for k in RAW_NAMES}
    all_scores.update(fusion)
    if tuple(sorted(all_scores)) != tuple(sorted(SCORE_NAMES)) or any(v.shape != times.shape or not np.isfinite(v).all() for v in all_scores.values()):
        raise Stage1AError("Stage-1A score inventory must be exact, finite, and aligned")
    return all_scores, times


def run_stage1a_machine(machine: str, *, source_commit: str, device: str = "cuda:0",
                         data_root: Path | None = None) -> dict:
    allowed = selected_machines()
    if machine not in allowed:
        raise Stage1AError("machine is outside frozen Stage-1A subset")
    existing = _load_or_reject_run(machine, source_commit)
    if existing is not None:
        return existing
    feature_hashes = _check_feature_hashes(machine, data_root)
    train = data.load_train(machine, data_root)
    test = data.load_test(machine, data_root)
    blocks = data.split_boundaries(len(train)); transform = data.RobustScaler().fit(train, blocks.fit[1]).statistics
    if transform is None:
        raise Stage1AError("frozen scaler did not fit")
    ztrain = data.apply_robust_transform(train, transform)
    bounds = {"fit": blocks.fit, "validation": blocks.validation, "calibration": blocks.calibration}
    folder = ROOT / RUN_DIR / machine
    folder.mkdir(parents=True, exist_ok=False)
    scaler_info = execute._immutable_npz_write(folder / "scaler.npz", center=transform.center,
        scale=transform.scale, raw_robust_scale=transform.raw_robust_scale,
        scale_floor=np.asarray(transform.scale_floor), fit_rows=np.asarray(transform.fit_rows))
    fitted: dict[str, Any] = {}; arm_records = {}
    for arm in ARMS:
        checkpoint = folder / f"{arm}.best.pt"
        sampler=_GpuSampler(device)
        with sampler:
            model, fit_record = execute.fit_arm(ztrain, bounds, arm, device=device, seed=SEED,
                                                max_epochs=MAX_EPOCHS, checkpoint_path=checkpoint)
        fitted[arm] = model
        run_path = folder / f"{arm}_run.json"
        execute.immutable_json_write(run_path, fit_record)
        arm_records[arm] = {"parameter_count": models.count_parameters(model),
            "model_state_sha256": fit_record["best_model_sha256"],
            "checkpoint_path": checkpoint.relative_to(ROOT).as_posix(),
            "checkpoint_sha256": execute._sha256_file(checkpoint),
            "run_record_path": run_path.relative_to(ROOT).as_posix(),
            "run_record_sha256": execute._sha256_file(run_path),
            "selected_epoch": fit_record["best_epoch"], "elapsed_seconds": fit_record["elapsed_seconds"],
            "peak_allocated_bytes":fit_record["peak_allocated_bytes"],
            "peak_reserved_bytes":fit_record["peak_reserved_bytes"],
            "gpu_telemetry":sampler.record()}
    cal_times, raw_cal, = _raw_calibration(train, transform, fitted, device)
    refs, threshold_samples, thresholds, threshold_times, first_bounds, second_bounds = _calibrate(raw_cal, cal_times)
    cal_arrays = {"timestamps": threshold_times}
    cal_arrays.update({f"tail_reference__{k}": v for k,v in refs.items()})
    cal_arrays.update({f"threshold_scores__{k}": v for k,v in threshold_samples.items()})
    cal_info = _write_npz(folder / "calibration.npz", cal_arrays)
    all_scores, times = _test_scores(train, test, transform, fitted, refs, device)
    score_path = ROOT / SCORE_DIR / f"{machine}.npz"
    score_info = _write_npz(score_path, {"timestamps": times, **all_scores})
    run = {"schema":"adaptive-normality-m1-stage1a-machine-run-v1", "status":"complete",
        "machine":machine,"source_commit":source_commit,"seed":SEED,"W":data.W,"batch_size":BATCH_SIZE,
        "arm_names":list(ARMS),"arms":arm_records,"feature_data":feature_hashes,
        "scaler":{"path":str((folder/"scaler.npz").relative_to(ROOT)),"sha256":scaler_info["sha256"]},
        "calibration":{"path":str((folder/"calibration.npz").relative_to(ROOT)),"sha256":cal_info["sha256"],
            "tail_reference_hashes":{k:_sha_array(v) for k,v in refs.items()},
            "tail_reference_counts":{k:len(v) for k,v in refs.items()},
            "first_half_timestamps":[int(first_bounds[0]),int(first_bounds[-1]+1)],
            "threshold_timestamps":[int(second_bounds[0]),int(second_bounds[-1]+1)]},
        "thresholds":thresholds,"threshold_quantile":QUANTILE,
        "tail_reference_hashes":{k:_sha_array(v) for k,v in refs.items()},
        "tail_reference_counts":{k:len(v) for k,v in refs.items()},
        "scores":{"path":score_info["path"],"sha256":score_info["sha256"],"bytes":score_info["bytes"],
            "timestamp_sha256":_sha_array(times),"timestamp_count":len(times),"score_names":list(SCORE_NAMES)},
        "test_labels_read":False,"anomaly_metrics_computed":False}
    _atomic_json(folder / "machine_run.json", run)
    return run


def seal_stage1a(*, repo: Path = ROOT) -> tuple[Path, Path]:
    """Create immutable exact-nine score and execution/calibration inventories."""
    root = Path(repo).resolve(); machines = selected_machines()
    if (root/SCORE_MANIFEST).exists() or (root/EXECUTION_MANIFEST).exists() or (root/EXECUTION_SUMMARY).exists():
        raise Stage1AError("Stage-1A score/provenance seal already exists; refusing overwrite")
    score_entries=[]; execution_entries=[]
    for machine in machines:
        run_path=root/RUN_DIR/machine/"machine_run.json"
        if not run_path.is_file(): raise Stage1AError(f"missing completed run {machine}")
        run=json.loads(run_path.read_text())
        validate_run_record(machine,run,repo=root)
        if run.get("test_labels_read") or run.get("anomaly_metrics_computed") or run.get("status")!="complete":
            raise Stage1AError(f"{machine}: invalid pre-label run flags")
        sp=root/run["scores"]["path"]
        with np.load(sp,allow_pickle=False) as a:
            if set(a.files)!={"timestamps",*SCORE_NAMES}: raise Stage1AError(f"{machine}: score set differs")
            ts=np.asarray(a["timestamps"])
            expected=np.arange(data.W,int(data.MANIFEST["machines"][machine]["test_rows"]))
            if not np.array_equal(ts,expected): raise Stage1AError(f"{machine}: timestamps are not exactly [256,test_rows)")
            if any(np.asarray(a[k]).shape!=ts.shape or not np.isfinite(a[k]).all() for k in SCORE_NAMES):
                raise Stage1AError(f"{machine}: invalid score values")
        digest=_sha_file(sp); t_hash=_sha_array(ts)
        score_entries.append({"machine":machine,"artifact":sp.relative_to(root).as_posix(),"sha256":digest,
            "bytes":int(sp.stat().st_size),"score_names":list(SCORE_NAMES),"timestamp_sha256":t_hash,"count":len(ts)})
        execution_entries.append({"machine":machine,"run_record":run_path.relative_to(root).as_posix(),
            "run_record_sha256":_sha_file(run_path),"source_commit":run["source_commit"],
            "feature_data":run["feature_data"],"scaler":run["scaler"],"arms":run["arms"],
            "calibration":run["calibration"],"thresholds":run["thresholds"],
            "threshold_quantile":run["threshold_quantile"],"tail_reference_hashes":run["tail_reference_hashes"],
            "tail_reference_counts":run["tail_reference_counts"],"score_sha256":digest,
            "score_artifact":sp.relative_to(root).as_posix(),"score_bytes":int(sp.stat().st_size),
            "score_timestamp_count":int(len(ts)),"score_timestamp_sha256":t_hash,
            "test_labels_read":False,"anomaly_metrics_computed":False})
    sm=root/SCORE_MANIFEST; em=root/EXECUTION_MANIFEST
    _atomic_json(sm,{"schema":SCORE_SCHEMA,"machines":score_entries,"score_names":list(SCORE_NAMES)})
    _atomic_json(em,{"schema":SCHEMA,"machines":execution_entries,"threshold_quantile":QUANTILE,
        "test_labels_read":False,"anomaly_metrics_computed":False})
    return sm,em


def run_stage1a(*, repo: Path = ROOT, device: str = "cuda:0", data_root: Path | None = None) -> dict:
    """Run/reuse nine isolated machine jobs and publish pre-label seals only."""
    root=Path(repo).resolve(); source=_git_head(root)
    for rel in (AMENDMENT_PATH,MACHINE_LIST_PATH):
        if not scores.git_committed(root/rel,root):
            raise Stage1AError(f"prospective amendment/selection must be committed before execution: {rel}")
    if (root/SCORE_MANIFEST).exists() or (root/EXECUTION_MANIFEST).exists() or (root/EXECUTION_SUMMARY).exists():
        raise Stage1AError("Stage-1A seal exists; runner will not overwrite")
    started=time.perf_counter(); rows=[]
    for machine in selected_machines():
        rows.append(run_stage1a_machine(machine,source_commit=source,device=device,data_root=data_root))
    score_manifest,execution_manifest=seal_stage1a(repo=root)
    result={"schema":"adaptive-normality-m1-stage1a-execution-summary-v1",
        "source_commit":source,"machines":list(selected_machines()),
        "score_manifest":score_manifest.as_posix(),"execution_manifest":execution_manifest.as_posix(),
        "wall_time_seconds":time.perf_counter()-started,
        "training_seconds":float(sum(arm["elapsed_seconds"] for row in rows for arm in row["arms"].values())),
        "selected_epochs":{row["machine"]:{arm:row["arms"][arm]["selected_epoch"] for arm in ARMS} for row in rows},
        "gpu_telemetry":{row["machine"]:{arm:row["arms"][arm]["gpu_telemetry"] for arm in ARMS} for row in rows},
        "test_labels_read":False,"anomaly_metrics_computed":False}
    _atomic_json(root/EXECUTION_SUMMARY,result)
    return result
