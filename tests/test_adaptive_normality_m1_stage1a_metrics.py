import numpy as np
import pytest
import hashlib
import json
from pathlib import Path

from scripts import adaptive_normality_m1_stage1a as a
from scripts import adaptive_normality_m1_stage1a_metrics as m
from scripts import adaptive_normality_m1_metrics as final
from scripts import adaptive_normality_m1_data as data
from scripts import adaptive_normality_m1_models as models
from scripts import adaptive_normality_m1_scores as scores


def test_futility_requires_both_routes_and_exact_zero_boundary():
    zero=np.zeros(9)
    out=m.decide_futility(zero,zero)
    assert out["decision"]=="STOP_FOR_FUTILITY"
    assert out["standalone"]["components"]=={"mean_delta_le_zero":True,"positive_machines_le_3":True}
    assert m.decide_futility(np.r_[np.ones(4),-np.ones(5)],zero)["decision"]=="CONTINUE_TO_STAGE1B"
    assert m.decide_futility(zero,np.r_[np.ones(4),-np.ones(5)])["decision"]=="CONTINUE_TO_STAGE1B"


def test_three_vs_four_positive_machine_boundary():
    three=np.r_[np.array([.1,.1,.1]),np.array([-.1]*6)]
    four=np.r_[np.array([.1]*4),np.array([-.1]*5)]
    assert m.decide_futility(three,three)["decision"]=="STOP_FOR_FUTILITY"
    route=m.decide_futility(four,np.zeros(9))["standalone"]
    assert route["positive_machines"]==4 and not route["components"]["positive_machines_le_3"]
    assert m.decide_futility(four,np.zeros(9))["decision"]=="CONTINUE_TO_STAGE1B"


def test_mean_delta_zero_and_strictly_positive_boundary():
    assert m.decide_futility(np.zeros(9),np.zeros(9))["standalone"]["mean_delta"]==0
    positive=np.array([.01]*9)
    assert not m.decide_futility(positive,np.zeros(9))["standalone"]["futile"]
    with pytest.raises(ValueError): m.decide_futility(np.zeros(8),np.zeros(9))


def test_exact_stage1a_scores_and_machine_only_metric_path():
    assert a.SCORE_NAMES==("last_value","moving_median","var1","xlstmad_f","lstm_f",
        "cheap_control_fusion","forecast_cheap_control_fusion")
    n=40; labels=np.zeros(n,dtype=np.uint8); labels[12:18]=1; labels[30:34]=1
    ts=np.arange(256,256+n)
    arrays={name:np.linspace(0,1,n) for name in a.SCORE_NAMES}
    thresholds={name:.7 for name in a.SCORE_NAMES}
    row=m.evaluate_machine("machine-1-7",arrays,labels,thresholds,ts,ts.copy())
    assert row["machine"]=="machine-1-7"
    assert set(row["scores"])==set(a.SCORE_NAMES)
    assert row["prevalence"]==pytest.approx(labels.mean())
    assert "event_detection_rate" in row["scores"]["xlstmad_f"]
    assert "normal_point_FPR" in row["scores"]["xlstmad_f"]
    assert "false_alarm_points_per_10000_normal" in row["scores"]["xlstmad_f"]
    assert "score_recovery_delay" in row["scores"]["xlstmad_f"]
    with pytest.raises(m.Stage1AMetricError,match="only for the frozen nine"):
        m.evaluate_machine("machine-1-1",arrays,labels,thresholds,ts,ts)


def test_score_and_label_timestamp_mismatch_rejected():
    labels=np.array([0,1,0,0],dtype=np.uint8); ts=np.arange(256,260)
    arrays={name:np.arange(4,dtype=float) for name in a.SCORE_NAMES}
    thresholds={name:2.0 for name in a.SCORE_NAMES}
    with pytest.raises(ValueError,match="timestamps"):
        m.evaluate_machine("machine-1-7",arrays,labels,thresholds,ts,ts+1)


def test_remote_prelabel_sha_gate_is_ancestor_and_reads_remote(monkeypatch,tmp_path):
    monkeypatch.setattr(m,"_remote_sha",lambda *args:"f"*40)
    calls=[]
    def run(*args,**kwargs): calls.append(args[0]); return None
    monkeypatch.setattr(m.subprocess,"run",run)
    assert m.require_remote_prelabel_commit(tmp_path,"a"*40)=="f"*40
    assert "ls-remote" not in calls[0]
    assert calls and "merge-base" in calls[0]


def test_prelabel_failure_precedes_any_label_loader(monkeypatch,tmp_path):
    calls=[]
    def fail(*args,**kwargs): raise m.Stage1AMetricError("not on remote")
    monkeypatch.setattr(m,"require_remote_prelabel_commit",fail)
    def loader(machine): calls.append(machine); raise AssertionError("must not read label")
    with pytest.raises(m.Stage1AMetricError,match="remote"):
        m.evaluate_stage1a(tmp_path,"a"*40,label_loader=loader,write=False)
    assert calls==[]


def test_exact_nine_label_loader_allowlist():
    assert len(a.selected_machines())==9
    calls=[]
    with pytest.raises(m.Stage1AMetricError,match="verified remote pre-label seal"):
        m._load_one_selected_label("machine-1-1",label_loader=lambda machine:calls.append(machine))
    assert calls==[]
    with m._authorized_stage1a_labels():
        with pytest.raises(m.Stage1AMetricError,match="outside frozen nine"):
            m._load_one_selected_label("machine-1-1",label_loader=lambda machine:calls.append(machine))
    assert calls==[]


def test_incomplete_or_tampered_inventory_fails_before_label_access(tmp_path,monkeypatch):
    (tmp_path/a.SCORE_MANIFEST).parent.mkdir(parents=True,exist_ok=True)
    (tmp_path/a.SCORE_MANIFEST).write_text('{"schema":"wrong"}')
    (tmp_path/a.EXECUTION_MANIFEST).write_text('{"schema":"wrong"}')
    monkeypatch.setattr(final,"git_committed",lambda *args:True)
    monkeypatch.setattr(m,"_git_blob",lambda repo,sha,path:(tmp_path/path).read_bytes())
    with pytest.raises(m.Stage1AMetricError,match="schema"):
        m._verify_sealed_inventory(tmp_path,"a"*40)


def test_final_28_machine_evaluator_contract_is_unchanged():
    assert len(final.STAGE1_MACHINES)==28
    assert final.STAGE1_SCORE_NAMES==("last_value","moving_median","var1","r_native_window","r_endpoint",
        "xlstmad_f","lstm_f","control_fusion","forecast_control_fusion")
    with pytest.raises(ValueError,match="exactly 28"):
        final.decide_stage1([])


def _synthetic_sealed_inventory(tmp_path,monkeypatch):
    machines=a.selected_machines()
    monkeypatch.setattr(a,"selected_machines",lambda manifest=None:machines)
    monkeypatch.setattr(m.stage1a,"selected_machines",lambda manifest=None:machines)
    manifest={"machines":{machine:{"train_rows":100,"test_rows":260} for machine in machines}}
    monkeypatch.setattr(data,"MANIFEST",manifest)
    monkeypatch.setattr(data,"verify_observation",lambda machine,split,root=None:{
        "match":True,"sha256":hashlib.sha256(f"{machine}/{split}".encode()).hexdigest(),"bytes":17})
    monkeypatch.setattr(final,"git_committed",lambda *args:True)
    monkeypatch.setattr(m,"_git_blob",lambda repo,sha,rel:(repo/rel).read_bytes())
    monkeypatch.setattr(m.subprocess,"run",lambda *args,**kwargs:None)
    entries=[]; executions=[]
    source="c"*40
    run_root=tmp_path/a.RUN_DIR
    score_root=tmp_path/a.SCORE_DIR
    for machine in machines:
        folder=run_root/machine; folder.mkdir(parents=True)
        score_folder=score_root; score_folder.mkdir(parents=True,exist_ok=True)
        scaler_path=folder/"scaler.npz"
        with scaler_path.open("wb") as f:
            np.savez(f,center=np.zeros(1),scale=np.ones(1),raw_robust_scale=np.ones(1),
                     scale_floor=np.asarray(1.),fit_rows=np.asarray([0,70]))
        scaler={"path":scaler_path.relative_to(tmp_path).as_posix(),"sha256":hashlib.sha256(scaler_path.read_bytes()).hexdigest()}
        arms={}
        for arm in a.ARMS:
            cp=folder/f"{arm}.pt"; cp.write_bytes(f"cp:{machine}:{arm}".encode())
            cph=hashlib.sha256(cp.read_bytes()).hexdigest(); state_hash=hashlib.sha256(f"state:{machine}:{arm}".encode()).hexdigest()
            rp=folder/f"{arm}_run.json"
            fit={"arm_key":arm,"seed":11,"parameter_count":models.EXPECTED_PARAMETERS[arm],
                 "best_model_sha256":state_hash,"best_checkpoint":{"sha256":cph}}
            rp.write_text(json.dumps(fit,sort_keys=True))
            arms[arm]={"parameter_count":models.EXPECTED_PARAMETERS[arm],"model_state_sha256":state_hash,
                "checkpoint_path":cp.relative_to(tmp_path).as_posix(),"checkpoint_sha256":cph,
                "run_record_path":rp.relative_to(tmp_path).as_posix(),
                "run_record_sha256":hashlib.sha256(rp.read_bytes()).hexdigest()}
        block=data.split_boundaries(100); start,stop=block.calibration; half=(stop-start)//2
        first=np.arange(start,start+half,dtype=np.int64); second=np.arange(start+half,stop,dtype=np.int64)
        refs={name:np.arange(half,dtype=np.float64) for name in a.SEVERITY_NAMES}
        samples={name:np.arange(len(second),dtype=np.float64)+i for i,name in enumerate(a.SCORE_NAMES)}
        thresholds={name:scores.higher_empirical_quantile(value,.99) for name,value in samples.items()}
        cal_path=folder/"calibration.npz"
        with cal_path.open("wb") as f:
            np.savez(f,timestamps=second,**{f"tail_reference__{k}":v for k,v in refs.items()},
                     **{f"threshold_scores__{k}":v for k,v in samples.items()})
        calibration={"path":cal_path.relative_to(tmp_path).as_posix(),"sha256":hashlib.sha256(cal_path.read_bytes()).hexdigest(),
            "first_half_timestamps":[int(first[0]),int(first[-1]+1)],"threshold_timestamps":[int(second[0]),int(second[-1]+1)],
            "tail_reference_hashes":{k:a._sha_array(v) for k,v in refs.items()},
            "tail_reference_counts":{k:len(v) for k,v in refs.items()}}
        times=np.arange(256,260,dtype=np.int64)
        score_values={name:np.array([.1,.8,.2,.9])+i*.001 for i,name in enumerate(a.SCORE_NAMES)}
        score_path=score_folder/f"{machine}.npz"
        with score_path.open("wb") as f: np.savez(f,timestamps=times,**score_values)
        score_digest=hashlib.sha256(score_path.read_bytes()).hexdigest(); timestamp_digest=a._sha_array(times)
        score_record={"path":score_path.relative_to(tmp_path).as_posix(),"sha256":score_digest,
            "bytes":score_path.stat().st_size,"timestamp_sha256":timestamp_digest,
            "timestamp_count":len(times),"score_names":list(a.SCORE_NAMES)}
        feature_data={split:{"sha256":hashlib.sha256(f"{machine}/{split}".encode()).hexdigest(),"bytes":17}
                      for split in ("train","test")}
        run={"schema":"adaptive-normality-m1-stage1a-machine-run-v1","status":"complete","machine":machine,
            "source_commit":source,"seed":11,"W":256,"arm_names":list(a.ARMS),"feature_data":feature_data,
            "scaler":scaler,"arms":arms,"calibration":calibration,"thresholds":thresholds,
            "threshold_quantile":a.QUANTILE,"tail_reference_hashes":calibration["tail_reference_hashes"],
            "tail_reference_counts":calibration["tail_reference_counts"],"scores":score_record,
            "test_labels_read":False,"anomaly_metrics_computed":False}
        run_path=folder/"machine_run.json"; run_path.write_text(json.dumps(run,sort_keys=True))
        run_rel=run_path.relative_to(tmp_path).as_posix(); run_digest=hashlib.sha256(run_path.read_bytes()).hexdigest()
        entries.append({"machine":machine,"artifact":score_record["path"],"sha256":score_digest,
            "bytes":score_path.stat().st_size,"score_names":list(a.SCORE_NAMES),
            "timestamp_sha256":timestamp_digest,"count":len(times)})
        executions.append({"machine":machine,"run_record":run_rel,"run_record_sha256":run_digest,
            "source_commit":source,"feature_data":feature_data,"scaler":scaler,"arms":arms,
            "calibration":calibration,"thresholds":thresholds,"threshold_quantile":a.QUANTILE,
            "tail_reference_hashes":calibration["tail_reference_hashes"],
            "tail_reference_counts":calibration["tail_reference_counts"],"score_sha256":score_digest,
            "score_artifact":score_record["path"],"score_bytes":score_record["bytes"],
            "score_timestamp_count":len(times),"score_timestamp_sha256":timestamp_digest,
            "test_labels_read":False,"anomaly_metrics_computed":False})
    score_manifest=tmp_path/a.SCORE_MANIFEST; score_manifest.parent.mkdir(parents=True,exist_ok=True)
    score_manifest.write_text(json.dumps({"schema":a.SCORE_SCHEMA,"machines":entries,"score_names":list(a.SCORE_NAMES)}))
    execution_manifest=tmp_path/a.EXECUTION_MANIFEST
    execution_manifest.write_text(json.dumps({"schema":a.SCHEMA,"machines":executions,
        "threshold_quantile":a.QUANTILE,"test_labels_read":False,"anomaly_metrics_computed":False}))
    return machines,entries,executions


def test_valid_complete_seal_reaches_only_nine_synthetic_labels_then_tampered_score_fails(tmp_path,monkeypatch):
    machines,entries,_=_synthetic_sealed_inventory(tmp_path,monkeypatch)
    monkeypatch.setattr(m,"require_remote_prelabel_commit",lambda *args,**kwargs:"f"*40)
    labels_opened=[]
    def synthetic_label(machine):
        labels_opened.append(machine)
        return {"timestamps":np.arange(256,260),"labels":np.array([0,1,0,1],dtype=np.uint8)}
    result=m.evaluate_stage1a(tmp_path,"a"*40,label_loader=synthetic_label,write=False)
    assert [row["machine"] for row in result["machines"]]==list(machines)
    assert set(result["machines"][0]["scores"])==set(a.SCORE_NAMES)
    assert labels_opened==list(machines)
    assert result["label_access"]["real_M1_test_label_reads"]==9
    assert result["label_access"]["other_19_unopened"] is True
    # Seal-time score file tampering is caught before another label callback.
    score_path=tmp_path/entries[0]["artifact"]
    score_path.write_bytes(score_path.read_bytes()+b"tampered")
    labels_opened.clear()
    with pytest.raises(m.Stage1AMetricError,match="score artifact not committed or hash differs"):
        m.evaluate_stage1a(tmp_path,"a"*40,label_loader=synthetic_label,write=False)
    assert labels_opened==[]


def test_tampered_execution_threshold_rejected_before_any_label_callback(tmp_path,monkeypatch):
    machines,_,executions=_synthetic_sealed_inventory(tmp_path,monkeypatch)
    monkeypatch.setattr(m,"require_remote_prelabel_commit",lambda *args,**kwargs:"f"*40)
    path=tmp_path/a.EXECUTION_MANIFEST
    doc=json.loads(path.read_text())
    doc["machines"][0]["thresholds"]["xlstmad_f"]+=1
    path.write_text(json.dumps(doc))
    opened=[]
    with pytest.raises(m.Stage1AMetricError,match="thresholds not sealed"):
        m.evaluate_stage1a(tmp_path,"a"*40,label_loader=lambda machine:opened.append(machine),write=False)
    assert opened==[]
