import json
from pathlib import Path
import numpy as np

import pytest

from scripts import adaptive_normality_m1_stage1a as a
from scripts import adaptive_normality_m1_data as data
from scripts import adaptive_normality_m1_execute as execute
from scripts import adaptive_normality_m1_scores as score_utils


def test_selection_is_frozen_and_deterministic_without_label_fields():
    doc=json.loads((a.ROOT/a.MACHINE_LIST_PATH).read_text())
    assert a.selected_machines()==("machine-1-7","machine-1-3","machine-1-5",
        "machine-2-4","machine-2-7","machine-2-8","machine-3-2","machine-3-11","machine-3-7")
    assert a.selected_machines()==a.selected_machines()
    # Selection accepts only metadata needed for ordering; no label/score keys exist.
    toy={"machines":{}}
    for group,items in doc["groups"].items():
        for _,machine,train_rows in items:
            toy["machines"][machine]={"train_rows":train_rows}
    assert a.selected_machines(toy)==tuple(doc["machines"])
    assert len(set(doc["machines"]))==9


def test_exact_isolated_score_set_and_models_exclude_reconstruction():
    assert a.SCORE_NAMES==("last_value","moving_median","var1","xlstmad_f","lstm_f",
        "cheap_control_fusion","forecast_cheap_control_fusion")
    assert a.ARMS==("xlstmad_f","lstm_f")
    assert "xlstmad_r" not in a.ARMS
    assert a.BASE_DIR.as_posix()=="reports/adaptive_normality_m1_smd/stage1a_screen"
    assert a.SCORE_DIR!=Path("reports/adaptive_normality_m1_smd/stage1_scores")


def test_feature_hash_gate_rejects_mismatch(monkeypatch):
    monkeypatch.setattr(data,"verify_observation",lambda machine,split,root=None:{
        "match":split=="train","sha256":"a"*64,"bytes":123})
    with pytest.raises(a.Stage1AError,match="test feature data"):
        a._check_feature_hashes("machine-1-7",None)


def test_partial_run_is_fail_closed_and_not_overwritten(tmp_path,monkeypatch):
    monkeypatch.setattr(a,"ROOT",tmp_path)
    monkeypatch.setattr(a,"RUN_DIR",Path("run"))
    folder=tmp_path/"run"/"machine-1-7"; folder.mkdir(parents=True)
    with pytest.raises(a.Stage1AError,match="partial"):
        a._load_or_reject_run("machine-1-7","0"*40)


def test_completed_run_requires_exact_frozen_identity_flags_and_parameter_counts(tmp_path,monkeypatch):
    monkeypatch.setattr(a,"ROOT",tmp_path); monkeypatch.setattr(a,"RUN_DIR",Path("run"))
    folder=tmp_path/"run"/"machine-1-7"; folder.mkdir(parents=True)
    a._atomic_json(folder/"machine_run.json",{"machine":"machine-1-7"})
    with pytest.raises(a.Stage1AError,match="differs at"):
        a._load_or_reject_run("machine-1-7","0"*40)


def _synthetic_calibration_record(train_rows=100):
    blocks=data.split_boundaries(train_rows)
    start,stop=blocks.calibration; half=max(1,(stop-start)//2)
    first=np.arange(start,start+half,dtype=np.int64); second=np.arange(start+half,stop,dtype=np.int64)
    refs={name:np.arange(half,dtype=np.float64) for name in a.SEVERITY_NAMES}
    arrays={"timestamps":second,**{f"tail_reference__{k}":v for k,v in refs.items()}}
    threshold_samples={name:np.arange(len(second),dtype=np.float64)+i for i,name in enumerate(a.SCORE_NAMES)}
    arrays.update({f"threshold_scores__{k}":v for k,v in threshold_samples.items()})
    record={"calibration":{"first_half_timestamps":[int(first[0]),int(first[-1]+1)],
            "threshold_timestamps":[int(second[0]),int(second[-1]+1)]},
        "tail_reference_counts":{k:len(v) for k,v in refs.items()},
        "tail_reference_hashes":{k:a._sha_array(v) for k,v in refs.items()},
        "thresholds":{k:score_utils.higher_empirical_quantile(v,.99)
                      for k,v in threshold_samples.items()}}
    return record,arrays


def test_calibration_must_match_frozen_split_half_lengths_and_q99():
    record,arrays=_synthetic_calibration_record()
    a._validate_calibration_arrays("machine-1-7",record,arrays,100)
    bad=dict(arrays); bad["timestamps"]=arrays["timestamps"]+1
    with pytest.raises(a.Stage1AError,match="second half"):
        a._validate_calibration_arrays("machine-1-7",record,bad,100)
    bad=dict(arrays); bad["tail_reference__last_value"]=arrays["tail_reference__last_value"][:-1]
    with pytest.raises(a.Stage1AError,match="tail reference"):
        a._validate_calibration_arrays("machine-1-7",record,bad,100)
    bad=dict(arrays); bad["threshold_scores__var1"]=arrays["threshold_scores__var1"][:-1]
    with pytest.raises(a.Stage1AError,match="threshold samples"):
        a._validate_calibration_arrays("machine-1-7",record,bad,100)
    bad_record={**record,"thresholds":{**record["thresholds"],"xlstmad_f":-999.}}
    with pytest.raises(a.Stage1AError,match="threshold differs"):
        a._validate_calibration_arrays("machine-1-7",bad_record,arrays,100)


def test_scoring_rejects_nonfinite_and_timestamp_index_is_unpadded():
    assert a.SEED==11 and a.BATCH_SIZE==128 and a.MAX_EPOCHS==50
    assert execute.LEARNING_RATE==1e-3
    assert a.QUANTILE=={"q":.99,"method":"higher"}
