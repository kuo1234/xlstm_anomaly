import copy
import json
from pathlib import Path
import numpy as np
import pytest
from p10_p3a_response_audit import (OUT,ROOT,CONFIG,check_config,lag_rows,spectrum,
    stats,train_scale,duplicate_audit,load_healthy,sha)

def test_future_current_observation_cannot_enter_past_regressor():
    x=np.arange(72,dtype=float).reshape(24,3)
    a=lag_rows(x,8)
    y=x.copy();y[16:]+=999
    b=lag_rows(y,8)
    np.testing.assert_array_equal(a[:9],b[:9]) # through prediction point16
    assert not np.array_equal(a[9],b[9])

def test_run_boundaries_not_joined():
    a=lag_rows(np.zeros((12,3)),8);b=lag_rows(np.ones((12,3)),8)
    joined=np.concatenate([a,b])
    assert joined.shape==(8,24)
    assert np.all(joined[:4]==0) and np.all(joined[4:]==1)

def test_scale_only_training_and_no_clip():
    train=[np.array([[1.,4],[3,4]])]
    mu,sd,raw=train_scale(train)
    np.testing.assert_array_equal(mu,[2,4])
    np.testing.assert_array_equal(sd,[1,.02])
    assert ((np.array([200,4])-mu)/sd)[0]>20
    assert raw[1]==0

def test_rank_reports_known_dependencies_keeps_constant_columns():
    x=np.column_stack([np.arange(20),2*np.arange(20),np.ones(20)])
    s=spectrum(x,[1e-8])
    assert s["columns"]==3 and s["constant_regressor_columns"]==[2]
    assert s["resolved_rank_by_relative_eigenvalue"]["1e-08"]==1
    assert s["entropy_effective_rank"]==pytest.approx(1)
    assert spectrum(np.ones((10,4)),[1e-8])["stable_rank"]==0

def test_stats_handles_constant_and_hold_deterministically():
    x=np.column_stack([np.ones(10)*.3,np.repeat(np.arange(5),2)])
    s=stats(x,[1,2])
    assert s["constant_observation_indices"]==[0]
    assert s["autocorrelation"][0][0] is None
    assert s["unchanged_step_fraction"][1]==pytest.approx(5/9)

def test_prefix_and_duplicate_groups_across_roles():
    a=np.zeros((8,2));b=a.copy();b[2:]=1
    es=[{"id":"a","role":"train","native_seed":1},{"id":"b","role":"validation","native_seed":2}]
    d=duplicate_audit(es,[a,b],[1,8])
    assert d["exact_prefix_groups"]["1"][0]["ids"]==["a","b"]
    assert d["exact_prefix_groups"]["8"]==[]
    assert d["pairs_with_nonzero_exact_prefix"][0]["rows"]==2
    assert d["pairs_with_nonzero_exact_prefix"][0]["cross_role"]

def test_fixed_cohort_lags_and_no_model_switch():
    c=json.loads(CONFIG.read_text());check_config(c)
    for k,v in [("train_ids",["healthy157"]),("pooled_train_history_lengths",[1,4]),
                ("models",1),("new_inputs_enabled",True)]:
        changed=copy.deepcopy(c);changed[k]=v
        with pytest.raises(ValueError):check_config(changed)

def test_runner_rejects_event_and_changed_role_without_reading(tmp_path):
    with pytest.raises(ValueError,match="allowlist"):
        load_healthy({"id":"left01","file":"left01.npy"},tmp_path)
    e={"id":"healthy100","file":"healthy100.npy","role":"validation"}
    with pytest.raises(ValueError,match="role"):
        load_healthy(e,tmp_path)

def test_hash_guard_and_symlink_escape(tmp_path):
    e={"id":"healthy100","file":"healthy100.npy","role":"train",
       "source_path":"Mode1/SingleFault/SimulationCompleted/IDV1/Mode1_IDVInfo_1_100/Run100",
       "shape":[600,53],"time_first":0.,"time_last":29.95,"sha256":"bad"}
    np.save(tmp_path/e["file"],np.zeros((600,53)))
    with pytest.raises(ValueError,match="hash mismatch"):load_healthy(e,tmp_path)
    outside=tmp_path.parent/"outside.npy";np.save(outside,np.zeros((600,53)))
    (tmp_path/e["file"]).unlink();(tmp_path/e["file"]).symlink_to(outside)
    e["sha256"]=sha(outside)
    with pytest.raises(ValueError,match="escaped"):load_healthy(e,tmp_path)

def test_source_table_inventory_and_evaluator_boundary():
    m=json.loads((OUT/"channel_manifest.json").read_text())
    assert len(m["channels"])==54
    assert [x["raw_index"] for x in m["channels"]]==list(range(54))
    assert sum(x["role"]=="manipulated" for x in m["channels"])==12
    assert sum(x["role"]=="measurement" for x in m["channels"][1:])==41
    assert all(not x["authorized_exogenous_command"] for x in m["channels"])
    assert all(not x["input_enabled"] for x in m["additional_inventory"])
    assert all(x["same_tick_ordering"]=="UNKNOWN" for x in m["channels"])

def test_source_inventory_is_cache_only_no_silent_acquisition():
    from p10_p3a_source_inventory import NoNetwork
    session=NoNetwork()
    with pytest.raises(RuntimeError,match="cache miss"):
        session.get("https://ndownloader.figshare.com/files/26003087",headers={"Range":"bytes=0-65535"})
    assert session.denied==[{"url":"https://ndownloader.figshare.com/files/26003087","range":"bytes=0-65535"}]
