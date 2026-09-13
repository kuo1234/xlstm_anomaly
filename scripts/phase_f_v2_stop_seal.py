"""Seal a fail-closed Phase F-v2 implementation stop without touching v1/E2."""
import json
import subprocess
from pathlib import Path
from phase_f_v2_common import ROOT,REPORT,sha,write_json

DATA_V2=ROOT/'data/phase_f_v2'

def main():
    execution=json.loads((REPORT/'execution.json').read_text())
    execution['active_terminated']=True; execution['stop_reason']='lstm_11_post_training_parity_exit3'; execution['complete_grid']=False
    execution['quarantined_runs']=['lstm_11','xlstm_11']; execution['remaining_not_started']=execution['remaining']
    execution['active_after_termination']=[]; execution['active']=[]
    write_json(REPORT/'execution.json',execution)
    lstm=json.loads((REPORT/'runs/lstm_11/manifest.json').read_text())
    parity=lstm['post_training_parity']; failed={k:v for k,v in parity['checks'].items() if not v['pass_']}
    assert 'partition_B1_output' in failed
    assert failed['partition_B1_output']['max_abs']>1e-5
    xcurve=json.loads((REPORT/'runs/xlstm_11/curves.json').read_text())
    assert len(xcurve)==2 and xcurve[-1]['epoch']==2
    index={}
    for run in ('lstm_11','xlstm_11'):
        data_dir=DATA_V2/'runs'/run
        if data_dir.exists():
            index[run]={str(p.relative_to(ROOT)):sha(p) for p in sorted(data_dir.iterdir()) if p.is_file()}
    write_json(REPORT/'quarantine.json',dict(policy='No Phase F-v2 artifact from this partial grid may enter G or any model-result estimate.',
        runs=index,reason='LSTM seed11 trained best checkpoint fails required post-training B1 output partition invariance.',
        failed_checks=failed,training_grid_complete=False,all_unstarted_runs=execution['remaining_not_started'],
        anomaly_metrics_computed=False,labels_read=False,test_sources_used=False,probes_fit=False))
    status=dict(phase_f='STOP_IMPLEMENTATION_VALIDITY',variant='F-v2',amendment_commit='1b5256c',gate_commit='9edbf0f',
        pretraining_gates='PASS',training_grid='STOP_AFTER_FIRST_POSTTRAIN_FAILURE',complete_grid=False,
        post_training_validity='FAIL_LSTM_SEED11_BATCH_PARTITION',
        failure=dict(run='lstm_11',check='partition_B1_output',max_abs=failed['partition_B1_output']['max_abs'],atol=1e-5,rtol=1e-4,
            interpretation='trained cuDNN nn.LSTM output is not invariant to B128 versus B1 partition under fixed tolerance'),
        runs=dict(lstm_11='QUARANTINED',xlstm_11='QUARANTINED_PARTIAL_EPOCH2',
            seeds_22_33_44_55='NOT_STARTED'),optimizer_steps=dict(lstm_11=lstm['optimizer_steps'],xlstm_11=632),
        trained_checkpoints_valid=0,scientific_results_valid=0,H1_controlled_harm='STOP',H1_natural_harm='NOT_RUN',H1_harm_overall='UNRESOLVED',
        H2_H3='NOT_TESTED',phase_g='LOCKED',anomaly_metrics_computed=False,labels_read=False,test_sources_used=False,probe_fit=False,
        tolerance_changed=False,backend_changed=False,quarantine=True)
    write_json(REPORT/'status.json',status)
    write_json(REPORT/'artifact_index.json',dict(reports={str(p.relative_to(ROOT)):sha(p) for p in sorted((REPORT/'runs').rglob('*')) if p.is_file()},data=index))
    paths=sorted(p for p in REPORT.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS','local_artifact_SHA256SUMS'))
    (REPORT/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(ROOT)}\n' for p in paths))
    print(json.dumps(dict(status='SEALED_STOP',failed_checks=list(failed),quarantined=list(index),sha_files=len(paths))))

if __name__=='__main__': main()
