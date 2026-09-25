"""Metric-only evaluator for the isolated nine-machine Stage-1A screen.

No result is read or written at import. Real labels are opened only after the
pre-label commit is proven present on the configured remote branch and every
Stage-1A artifact is checked against that commit.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Callable, Mapping

import numpy as np

try:
    from scripts import adaptive_normality_m1_data as data
    from scripts import adaptive_normality_m1_metrics as base
    from scripts import adaptive_normality_m1_stage1a as stage1a
except ImportError:  # pragma: no cover
    import adaptive_normality_m1_data as data
    import adaptive_normality_m1_metrics as base
    import adaptive_normality_m1_stage1a as stage1a


class Stage1AMetricError(RuntimeError):
    pass


_STAGE1A_LABEL_AUTHORIZED: ContextVar[bool]=ContextVar("m1_stage1a_label_authorized",default=False)


@contextmanager
def _authorized_stage1a_labels():
    token=_STAGE1A_LABEL_AUTHORIZED.set(True)
    try:
        yield
    finally:
        _STAGE1A_LABEL_AUTHORIZED.reset(token)


def decide_futility(standalone_deltas, complement_deltas) -> dict:
    """Return only STOP_FOR_FUTILITY or CONTINUE_TO_STAGE1B, per frozen rule."""
    def route(values):
        x=np.asarray(values,dtype=np.float64)
        if x.shape!=(9,) or not np.isfinite(x).all():
            raise ValueError("futility decision requires nine finite paired machine deltas")
        positive=int(np.sum(x>0)); mean=float(x.mean())
        components={"mean_delta_le_zero":mean<=0.0,"positive_machines_le_3":positive<=3}
        return {"mean_delta":mean,"positive_machines":positive,"machine_count":9,
                "components":components,"futile":all(components.values())}
    standalone=route(standalone_deltas); complement=route(complement_deltas)
    return {"decision":"STOP_FOR_FUTILITY" if standalone["futile"] and complement["futile"] else "CONTINUE_TO_STAGE1B",
            "standalone":standalone,"complement":complement,
            "stage1a_is_not_confirmatory":True,"stage1b_started":False}


def evaluate_machine(machine: str, score_arrays: Mapping[str,np.ndarray], labels: np.ndarray,
                     thresholds: Mapping[str,float], timestamps: np.ndarray,
                     label_timestamps: np.ndarray) -> dict:
    if machine not in stage1a.selected_machines():
        raise Stage1AMetricError("labels are permitted only for the frozen nine Stage-1A machines")
    if set(score_arrays)!=set(stage1a.SCORE_NAMES) or set(thresholds)!=set(stage1a.SCORE_NAMES):
        raise ValueError("Stage-1A evaluator requires exactly seven frozen score arrays and thresholds")
    if not np.array_equal(timestamps,label_timestamps):
        raise ValueError("score and label timestamps differ")
    y=base._binary_labels(labels)
    records={}; prevalence=float(y.mean())
    for name in stage1a.SCORE_NAMES:
        s=base._scores(score_arrays[name]).reshape(-1)
        if len(s)!=len(y): raise ValueError("Stage-1A score length differs from labels")
        events=base.event_metrics(y,s,float(thresholds[name]))
        ap=base.average_precision(y,s); roc=base.area_under_roc(y,s)
        records[name]={"AP":ap,"AUROC":roc,"AP_over_prevalence":ap/prevalence,
                       "threshold":float(thresholds[name]),**events}
    cheap=max(("last_value","moving_median","var1"),key=lambda name:records[name]["AP"])
    oracle=records[cheap]["AP"]
    return {"machine":machine,"prevalence":prevalence,"scores":records,
            "cheap_oracle_AP":oracle,"cheap_oracle_winner":cheap,
            "delta_standalone":records["xlstmad_f"]["AP"]-oracle,
            "delta_complement":records["forecast_cheap_control_fusion"]["AP"]-records["cheap_control_fusion"]["AP"],
            "delta_lstm_f":records["lstm_f"]["AP"]-oracle}


def _remote_sha(repo: Path, remote: str, branch: str) -> str:
    output=subprocess.check_output(["git","-C",str(repo),"ls-remote",remote,f"refs/heads/{branch}"],text=True)
    rows=[line.split() for line in output.splitlines() if line.strip()]
    if len(rows)!=1 or len(rows[0])<2: raise Stage1AMetricError("cannot resolve unique remote branch for pre-label gate")
    return rows[0][0]


def require_remote_prelabel_commit(repo: Path, prelabel_sha: str, *, remote: str="origin",
                                   branch: str="research/adaptive-normality-m1-smd") -> str:
    if len(prelabel_sha)!=40 or any(c not in "0123456789abcdef" for c in prelabel_sha):
        raise Stage1AMetricError("pre-label SHA must be a full Git commit ID")
    remote_sha=_remote_sha(repo,remote,branch)
    try:
        subprocess.run(["git","-C",str(repo),"merge-base","--is-ancestor",prelabel_sha,remote_sha],
                       check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except (OSError,subprocess.CalledProcessError) as error:
        raise Stage1AMetricError("pre-label score/provenance commit is not present on remote branch") from error
    return remote_sha


def _git_blob(repo: Path, commit: str, relative: str) -> bytes:
    return subprocess.check_output(["git","-C",str(repo),"show",f"{commit}:{relative}"])


def _verify_sealed_inventory(repo: Path, prelabel_sha: str) -> tuple[dict,dict]:
    machines=stage1a.selected_machines()
    score_path=repo/stage1a.SCORE_MANIFEST; execution_path=repo/stage1a.EXECUTION_MANIFEST
    if not score_path.is_file() or not execution_path.is_file():
        raise Stage1AMetricError("both isolated Stage-1A seals must exist before labels")
    for path in (score_path,execution_path):
        if not base.git_committed(path,repo): raise Stage1AMetricError(f"seal is not committed: {path.name}")
        if _git_blob(repo,prelabel_sha,path.relative_to(repo).as_posix())!=path.read_bytes():
            raise Stage1AMetricError(f"seal changed after pre-label commit: {path.name}")
    sm=json.loads(score_path.read_text()); em=json.loads(execution_path.read_text())
    if sm.get("schema")!=stage1a.SCORE_SCHEMA or sm.get("score_names")!=list(stage1a.SCORE_NAMES):
        raise Stage1AMetricError("Stage-1A score seal has wrong schema or score inventory")
    if em.get("schema")!=stage1a.SCHEMA or em.get("threshold_quantile")!=stage1a.QUANTILE:
        raise Stage1AMetricError("Stage-1A execution seal has wrong schema or thresholds")
    if em.get("test_labels_read") is not False or em.get("anomaly_metrics_computed") is not False:
        raise Stage1AMetricError("execution seal does not prove result-blind label-free scoring")
    if [x.get("machine") for x in sm.get("machines",[])]!=list(machines) or [x.get("machine") for x in em.get("machines",[])]!=list(machines):
        raise Stage1AMetricError("Stage-1A seals must contain exactly the ordered frozen nine machines")
    exec_by={x["machine"]:x for x in em["machines"]}
    for entry in sm["machines"]:
        machine=entry["machine"]; score_rel=entry.get("artifact")
        if not isinstance(score_rel,str) or not score_rel.startswith(stage1a.SCORE_DIR.as_posix()+"/"):
            raise Stage1AMetricError("score artifact escaped isolated Stage-1A directory")
        artifact=repo/score_rel; ex=exec_by[machine]
        if (not artifact.is_file() or not base.git_committed(artifact,repo) or
                hashlib.sha256(artifact.read_bytes()).hexdigest()!=entry.get("sha256") or
                entry.get("sha256")!=ex.get("score_sha256")):
            raise Stage1AMetricError(f"{machine}: score artifact not committed or hash differs")
        if entry.get("score_names")!=list(stage1a.SCORE_NAMES):
            raise Stage1AMetricError(f"{machine}: per-machine score inventory differs")
        if ex.get("test_labels_read") is not False or ex.get("anomaly_metrics_computed") is not False:
            raise Stage1AMetricError(f"{machine}: execution entry is not label-free")
        if _git_blob(repo,prelabel_sha,score_rel)!=artifact.read_bytes():
            raise Stage1AMetricError(f"{machine}: score artifact differs from pre-label commit")
        if (ex.get("score_artifact")!=score_rel or ex.get("score_bytes")!=artifact.stat().st_size or
                entry.get("bytes")!=artifact.stat().st_size or
                ex.get("score_timestamp_sha256")!=entry.get("timestamp_sha256") or
                ex.get("score_timestamp_count")!=entry.get("count")):
            raise Stage1AMetricError(f"{machine}: execution/score inventory path, size, or timestamps disagree")
        run_rel=ex.get("run_record")
        run_path=repo/run_rel
        if (not run_path.is_file() or not base.git_committed(run_path,repo) or
                hashlib.sha256(run_path.read_bytes()).hexdigest()!=ex.get("run_record_sha256") or
                _git_blob(repo,prelabel_sha,run_rel)!=run_path.read_bytes()):
            raise Stage1AMetricError(f"{machine}: run record not sealed by pre-label commit")
        run=json.loads(run_path.read_text())
        if run.get("machine")!=machine or run.get("test_labels_read") is not False or run.get("anomaly_metrics_computed") is not False:
            raise Stage1AMetricError(f"{machine}: pre-label run flags or machine ID invalid")
        try:
            stage1a.validate_run_record(machine,run,repo=repo)
        except (KeyError,ValueError,RuntimeError,OSError) as error:
            raise Stage1AMetricError(f"{machine}: complete run/calibration provenance failed: {error}") from error
        if ex.get("thresholds")!=run.get("thresholds") or ex.get("threshold_quantile")!=stage1a.QUANTILE:
            raise Stage1AMetricError(f"{machine}: thresholds not sealed at frozen values")
        if ex.get("source_commit")!=run.get("source_commit"):
            raise Stage1AMetricError(f"{machine}: source commit mismatch")
        duplicated=("feature_data","scaler","arms","calibration","tail_reference_hashes","tail_reference_counts")
        if any(ex.get(key)!=run.get(key) for key in duplicated):
            raise Stage1AMetricError(f"{machine}: execution seal duplicates differ from the verified run record")
        run_score_path=Path(run.get("scores",{}).get("path",""))
        resolved_run_score=(run_score_path if run_score_path.is_absolute() else repo/run_score_path).resolve()
        try: normalized_run_score=resolved_run_score.relative_to(repo.resolve()).as_posix()
        except ValueError as error: raise Stage1AMetricError(f"{machine}: score path escapes repository") from error
        if (normalized_run_score!=score_rel or run["scores"].get("sha256")!=entry.get("sha256") or
                run["scores"].get("bytes")!=entry.get("bytes") or
                run["scores"].get("timestamp_sha256")!=entry.get("timestamp_sha256") or
                run["scores"].get("timestamp_count")!=entry.get("count") or
                run["scores"].get("score_names")!=list(stage1a.SCORE_NAMES)):
            raise Stage1AMetricError(f"{machine}: run record and canonical score inventory disagree")
        try:
            subprocess.run(["git","-C",str(repo),"merge-base","--is-ancestor",run["source_commit"],prelabel_sha],
                           check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except (KeyError,OSError,subprocess.CalledProcessError) as error:
            raise Stage1AMetricError(f"{machine}: source code commit is not an ancestor of pre-label seal") from error
        file_seals=[run["scaler"],run["calibration"],*[
            {"path":arm["checkpoint_path"],"sha256":arm["checkpoint_sha256"]}
            for arm in run["arms"].values()],*[
            {"path":arm["run_record_path"],"sha256":arm["run_record_sha256"]}
            for arm in run["arms"].values()]]
        for seal in file_seals:
            provenance_rel=seal["path"]
            artifact=repo/provenance_rel
            if (not artifact.is_file() or not base.git_committed(artifact,repo) or
                    hashlib.sha256(artifact.read_bytes()).hexdigest()!=seal["sha256"] or
                    _git_blob(repo,prelabel_sha,provenance_rel)!=artifact.read_bytes()):
                raise Stage1AMetricError(f"{machine}: model/scaler/calibration artifact not sealed before labels")
        score=repo/score_rel
        with np.load(score,allow_pickle=False) as arrays:
            if set(arrays.files)!={"timestamps",*stage1a.SCORE_NAMES}:
                raise Stage1AMetricError(f"{machine}: score arrays differ from exact seven-score set")
            test_rows=int(data.MANIFEST["machines"][machine]["test_rows"])
            ts=np.asarray(arrays["timestamps"])
            if not np.array_equal(ts,np.arange(data.W,test_rows)):
                raise Stage1AMetricError(f"{machine}: timestamps not exactly [256,test_rows)")
            if hashlib.sha256(np.ascontiguousarray(ts).tobytes()).hexdigest()!=entry.get("timestamp_sha256"):
                raise Stage1AMetricError(f"{machine}: timestamp digest mismatch")
            for name in stage1a.SCORE_NAMES:
                if arrays[name].shape!=ts.shape or not np.isfinite(arrays[name]).all():
                    raise Stage1AMetricError(f"{machine}: invalid score array {name}")
        if set(ex.get("thresholds",{}))!=set(stage1a.SCORE_NAMES): raise Stage1AMetricError(f"{machine}: threshold inventory differs")
    return sm,em


def _load_one_selected_label(machine: str, *, label_loader: Callable | None=None):
    if not _STAGE1A_LABEL_AUTHORIZED.get():
        raise Stage1AMetricError("Stage-1A labels require the verified remote pre-label seal context")
    if machine not in stage1a.selected_machines(): raise Stage1AMetricError("attempt to access labels outside frozen nine")
    if label_loader is not None: return label_loader(machine)
    label_path=data.data_root()/f"{machine}_test_label.txt"
    with base._authorized_production_label_access():
        return base.load_pinned_test_labels(machine,label_path)


def evaluate_stage1a(repo: Path, prelabel_sha: str, *, remote: str="origin",
                     branch: str="research/adaptive-normality-m1-smd",
                     label_loader: Callable | None=None, write: bool=True) -> dict:
    """Validate remote pre-label seal, then and only then read its nine labels."""
    root=Path(repo).resolve()
    remote_sha=require_remote_prelabel_commit(root,prelabel_sha,remote=remote,branch=branch)
    sm,em=_verify_sealed_inventory(root,prelabel_sha)
    if data.test_label_open_attempt_count()!=0:
        raise Stage1AMetricError("test-label open attempt occurred before Stage-1A metric gate")
    machine_rows=[]; opened=[]
    exec_by={x["machine"]:x for x in em["machines"]}
    with _authorized_stage1a_labels():
        for entry in sm["machines"]:
            machine=entry["machine"]
            label_doc=_load_one_selected_label(machine,label_loader=label_loader)
            opened.append(machine)
            score_path=root/entry["artifact"]
            with np.load(score_path,allow_pickle=False) as arrays:
                score_arrays={k:np.asarray(arrays[k]) for k in stage1a.SCORE_NAMES}
                times=np.asarray(arrays["timestamps"])
            row=evaluate_machine(machine,score_arrays,label_doc["labels"],exec_by[machine]["thresholds"],
                                 times,np.asarray(label_doc["timestamps"]))
            machine_rows.append(row)
    gate=decide_futility([r["delta_standalone"] for r in machine_rows],
                         [r["delta_complement"] for r in machine_rows])
    lstm_rows=[r["scores"]["lstm_f"] for r in machine_rows]
    gate["lstm_diagnostic"]={"mean_delta_ap":float(np.mean([r["delta_lstm_f"] for r in machine_rows])),
        "positive_machines":int(sum(r["delta_lstm_f"]>0 for r in machine_rows)),
        "mean_ap_over_prevalence":float(np.mean([s["AP_over_prevalence"] for s in lstm_rows])),
        "mean_event_detection_rate":float(np.mean([s["event_detection_rate"] for s in lstm_rows])),
        "mean_normal_point_FPR":float(np.mean([s["normal_point_FPR"] for s in lstm_rows])),
        "affects_decision":False}
    opened_set=set(opened); all_m1=set(data.MACHINES)
    access={"schema":"adaptive-normality-m1-stage1a-label-access-v1",
        "stage1a_pre_label_sha":prelabel_sha,"remote_branch_sha":remote_sha,
        "real_M1_test_label_reads":len(opened),"machines_opened":opened,
        "unopened_machines":sorted(all_m1-opened_set),"other_19_unopened":len(all_m1-opened_set)==19,
        "labels_read_before_prelabel_sha":0,"anomaly_metrics_computed":True}
    result={"schema":"adaptive-normality-m1-stage1a-results-v1","machines":machine_rows,
            "gate":gate,"label_access":access,"interpretation":(
                "Under the frozen nine-machine screen, one-step xLSTM forecasting showed sufficiently weak evidence relative to cheap causal controls that further M1 forecasting expenditure is not justified."
                if gate["decision"]=="STOP_FOR_FUTILITY" else
                "Stage 1A did not provide sufficient evidence for futility."),
            "stage1b_started":False,"confirmatory_claim_permitted":False}
    if write:
        destinations=(root/stage1a.RESULTS_JSON,root/stage1a.GATE_JSON,
                      root/stage1a.LABEL_LOG,root/stage1a.RESULTS_MD)
        if any(path.exists() for path in destinations):
            raise FileExistsError("Stage-1A result artifact exists; refusing overwrite")
        for path,doc in ((root/stage1a.RESULTS_JSON,result),(root/stage1a.GATE_JSON,gate)):
            stage1a._atomic_json(path,doc,immutable=True)
        table=["# M1 Stage-1A futility screen","",f"Decision: `{gate['decision']}`","",
            "This nine-machine screen is futility-only and is not confirmatory.","",
            "| Machine | Prevalence | Score | AP | AUROC | AP/prevalence | Event detection | Normal FPR | False alarm points/10k | Recovery delay |",
            "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|"]
        for m in machine_rows:
            for n,v in m["scores"].items():
                table.append(f"| {m['machine']} | {m['prevalence']:.8g} | {n} | {v['AP']:.8g} | {v['AUROC']:.8g} | {v['AP_over_prevalence']:.8g} | {v['event_detection_rate']:.8g} | {v['normal_point_FPR']:.8g} | {v['false_alarm_points_per_10000_normal']:.8g} | {v['score_recovery_delay']:.8g} |")
        stage1a._atomic_json(root/stage1a.LABEL_LOG,access,immutable=True)
        md_path=root/stage1a.RESULTS_MD; md_path.parent.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(dir=md_path.parent,prefix=f".{md_path.name}.",suffix=".partial")
        temporary=Path(name)
        try:
            with os.fdopen(fd,"w",encoding="utf-8") as f:
                f.write("\n".join(table)+"\n"); f.flush(); os.fsync(f.fileno())
            os.link(temporary,md_path)
        finally:
            temporary.unlink(missing_ok=True)
    return result
