"""Backend-only D-v2 correction and fail-closed fresh-process orchestration."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
import torch
from phase_d_operator import ROOT,OFFICIAL,object_hash,tensor_hash,rng_state,update
from phase_c_run import digest,state_hash
import phase_d_grid as old

REPORT=ROOT/'reports/phase_d_v2'
DATA=ROOT/'data/phase_d_v2'
V1=ROOT/'reports/phase_d'
OLD_DATA=ROOT/'data/phase_d'
NOTE='a40634b'
EXPECTED=json.loads((REPORT/'backend_seal.json').read_text())
FINGERPRINT=hashlib.sha256(json.dumps(EXPECTED,sort_keys=True).encode()).hexdigest()


def backend():
    return dict(cudnn_deterministic=torch.backends.cudnn.deterministic,
        cudnn_benchmark=torch.backends.cudnn.benchmark,
        deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
        float32_matmul_precision=torch.get_float32_matmul_precision(),
        matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32,cudnn_allow_tf32=torch.backends.cudnn.allow_tf32,
        torch=torch.__version__,cuda=torch.version.cuda,cudnn=torch.backends.cudnn.version(),
        device=torch.cuda.get_device_name(),capability=list(torch.cuda.get_device_capability()),
        driver=subprocess.check_output(['rtk','nvidia-smi','--query-gpu=driver_version','--format=csv,noheader'],text=True).strip())


def assert_backend():
    # Device/version/driver are checked at start; low-latency flag checks every arm.
    actual=dict(cudnn_deterministic=torch.backends.cudnn.deterministic,cudnn_benchmark=torch.backends.cudnn.benchmark,
        deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),float32_matmul_precision=torch.get_float32_matmul_precision(),
        matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32,cudnn_allow_tf32=torch.backends.cudnn.allow_tf32)
    assert all(EXPECTED[k]==v for k,v in actual.items()),actual
    assert digest(REPORT/'backend_seal.json')==SEAL_SHA


SEAL_SHA=digest(REPORT/'backend_seal.json')


def start(tag):
    assert subprocess.check_output(['rtk','git','show',f'{NOTE}:reports/phase_d_v2/amendment.md'])==(REPORT/'amendment.md').read_bytes()
    assert subprocess.check_output(['rtk','git','show',f'{NOTE}:reports/phase_d_v2/backend_seal.json'])==(REPORT/'backend_seal.json').read_bytes()
    subprocess.run(['rtk','git','merge-base','--is-ancestor',NOTE,'origin/main'],check=True)
    incoming=backend()
    # Restore accepted semantics, not additional deterministic modes.
    torch.backends.cudnn.deterministic=EXPECTED['cudnn_deterministic']
    torch.backends.cudnn.benchmark=EXPECTED['cudnn_benchmark']
    torch.use_deterministic_algorithms(EXPECTED['deterministic_algorithms'])
    torch.set_float32_matmul_precision(EXPECTED['float32_matmul_precision'])
    torch.backends.cuda.matmul.allow_tf32=EXPECTED['matmul_allow_tf32']
    torch.backends.cudnn.allow_tf32=EXPECTED['cudnn_allow_tf32']
    assert backend()==EXPECTED
    packages=json.loads((ROOT/'reports/phase_c/environment.json').read_text())['packages']
    import importlib.metadata
    installed={d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
    assert all(installed.get(k)==v for k,v in packages.items())
    code=json.loads((ROOT/'reports/phase_c/official_code_hashes.json').read_text())
    assert all(digest(OFFICIAL/p)==h for p,h in code.items())
    assert not subprocess.check_output(['rtk','git','-C',str(OFFICIAL),'status','--porcelain'],text=True).strip()
    (REPORT/'processes').mkdir(parents=True,exist_ok=True)
    props=torch.cuda.get_device_properties(0)
    metadata=dict(tag=tag,pid=os.getpid(),incoming=incoming,restored=backend(),backend_fingerprint=FINGERPRINT,
        backend_seal_sha256=SEAL_SHA,device_uuid=str(getattr(props,'uuid','not_exposed')),
        python=sys.version,packages_match_frozen=True,amendment_commit=NOTE)
    path=REPORT/'processes'/f'{tag}.json'
    assert not path.exists();path.write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata


def verify_reuse():
    # Compare only sealed input artifacts; never parse old grid outcomes.
    for name in ('synthetic_backbone_manifest.json','buffer_manifest.json'):
        assert subprocess.check_output(['rtk','git','show',f'3485a61:reports/phase_d/{name}'])==(V1/name).read_bytes()
        (REPORT/name).write_bytes((V1/name).read_bytes())
    manifest=json.loads((V1/'synthetic_backbone_manifest.json').read_text())
    rows=[]
    from phase_d_backbone import windows,score
    from m0.synthetic import generate
    for r in manifest['rows']:
        for p,h in r['artifacts'].items():assert digest(ROOT/p)==h
        adapter,state=old.load(r['detector_seed']);old.reset(adapter,state)
        assert state_hash(adapter.model)==r['initial_model_sha256']
        assert state_hash(adapter.model.sana_in)==r['sana_in_sha256']
        assert state_hash(adapter.model.sana_out)==r['sana_out_sha256']
        assert object_hash(state['optimizer_state'])==r['optimizer_sha256']
        assert object_hash(state['rng'])==r['rng_sha256']
        assert state['scaler']==r['preprocessing'] and state['threshold']==r['threshold']
        backbone=torch.load(OLD_DATA/f'backbone_{r["detector_seed"]}/checkpoint_best.pth',map_location='cpu',weights_only=False)['model_state']
        assert all(torch.equal(v,adapter.model.state_dict()[k].cpu()) for k,v in backbone.items())
        mean=np.array(state['scaler']['scaler_mean']);scale=np.array(state['scaler']['scaler_scale'])
        cal=np.concatenate([windows((generate(s,'stationary','none').observations[4096:5120]-mean)/scale) for s in range(1000,1010)])
        assert tensor_hash(cal)==state['scaler']['calibration_array_sha256']
        got=score(adapter.model,torch.from_numpy(cal))
        sealed=np.load(OLD_DATA/f'backbone_{r["detector_seed"]}/calibration_scores.npy')
        assert np.array_equal(got,sealed) and float(np.quantile(got,.95))==r['threshold']
        rows.append(dict(seed=r['detector_seed'],artifacts_exact=True,scaler_exact=True,calibration_scores_exact=True,
            threshold_exact=True,sana_exact=True,optimizer_exact=True,rng_exact=True,backbone_exact=True))
        assert_backend()
    from phase_d_buffers import compose
    buffers=json.loads((V1/'buffer_manifest.json').read_text())['rows']
    for m in buffers:
        assert compose(m['source'],m['scenario'],m['condition'])[-1]==m
    result=dict(status='PASS',rows=rows,buffer_layouts_verified=len(buffers),no_retraining=True,
        quarantined_results_read=False,backend_fingerprint=FINGERPRINT,
        input_seals={name:digest(V1/name) for name in ('synthetic_backbone_manifest.json','buffer_manifest.json')})
    (REPORT/'reuse_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Reuse verification PASS; all five calibration arrays bitwise equal;160 layouts exact',flush=True)


def arm(tag,no_update=False,permuted=False,canary=False):
    assert_backend()
    from phase_d_buffers import compose
    arms,x,y,primary,m=compose(3000,'abrupt','spike')
    adapter,state=old.load(11);old.reset(adapter,state)
    mean=np.array(state['scaler']['scaler_mean']);scale=np.array(state['scaler']['scaler_scale'])
    buf=torch.from_numpy(np.ascontiguousarray((arms[10]-mean)/scale,dtype=np.float32)).cuda()
    test=torch.from_numpy(np.ascontiguousarray((x-mean)/scale,dtype=np.float32))
    evaluator=np.random.default_rng(902).permutation(y) if permuted else y.copy()
    pre=dict(model=state_hash(adapter.model),optimizer=object_hash(adapter.optimizer.state_dict()),rng=object_hash(rng_state()),backend=FINGERPRINT)
    t=time.perf_counter();torch.cuda.reset_peak_memory_stats()
    losses=[] if no_update else update(adapter,buf)
    scores=old.score(adapter.model,test);torch.cuda.synchronize();assert_backend()
    result=dict(tag=tag,no_update=no_update,labels_permuted=permuted,pre=pre,buffer_sha256=tensor_hash(buf),
        losses=losses,trainable_tensor_hashes={k:tensor_hash(p) for k,p in adapter.model.named_parameters() if p.requires_grad},
        model_sha256=state_hash(adapter.model),optimizer_sha256=object_hash(adapter.optimizer.state_dict()),
        rng_sha256=object_hash(rng_state()),scores_tensor_sha256=tensor_hash(scores),backend_fingerprint=FINGERPRINT,
        backend_seal_sha256=SEAL_SHA,runtime_seconds=time.perf_counter()-t,
        peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved(),
        evaluator_label_sha256=tensor_hash(evaluator),anomalous_windows=int(evaluator[primary].sum()))
    if not canary:
        path=DATA/'gates'/tag;path.mkdir(parents=True,exist_ok=False)
        np.save(path/'scores.npy',scores,allow_pickle=False)
        torch.save(adapter.model.state_dict(),path/'post_model.pth');torch.save(adapter.optimizer.state_dict(),path/'post_optimizer.pth')
        result['artifacts']={str(p.relative_to(ROOT)):digest(p) for p in path.iterdir()}
        (REPORT/'gates').mkdir(exist_ok=True)
        (REPORT/'gates'/f'{tag}.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def behavior(r):
    return {k:r[k] for k in ('pre','buffer_sha256','losses','trainable_tensor_hashes','model_sha256',
        'optimizer_sha256','rng_sha256','scores_tensor_sha256','backend_fingerprint')}


def gates():
    real=json.loads((REPORT/'operator_parity.json').read_text());assert real['status']=='PASS'
    for k,v in real.items():
        if k.endswith(('_exact','_equal','_tolerance')): assert v,k
    assert digest(ROOT/real['snapshot_path'])==real['snapshot_sha256']
    capture=torch.load(ROOT/real['snapshot_path'],map_location='cpu',weights_only=False)
    from config import get_cfg_defaults
    from datasets.build import build_dataset
    cfg=get_cfg_defaults();cfg.merge_from_other_cfg(type(cfg).load_cfg(capture['config']))
    cfg.DATA.BASE_DIR=str(OFFICIAL/'data')
    dataset=build_dataset(cfg,'test')
    expected=torch.from_numpy(np.stack([dataset[i][0] for i in capture['event']['ids']]))
    segment=torch.from_numpy(np.stack([dataset[i][0] for i in range(256,512)]))
    assert torch.equal(expected,capture['buffer']) and torch.equal(segment,capture['segment'])
    tags=[f'{p}_{i}' for p in ('repeat','zero') for i in range(3)]+['label_permuted','real_d0','reuse']
    processes=[json.loads((REPORT/'processes'/f'{t}.json').read_text()) for t in tags]
    assert len({p['device_uuid'] for p in processes})==1
    assert all(p['restored']==EXPECTED and p['backend_fingerprint']==FINGERPRINT for p in processes)
    for tag in tags[:7]:
        row=json.loads((REPORT/'gates'/f'{tag}.json').read_text())
        assert all(digest(ROOT/p)==h for p,h in row['artifacts'].items())
        saved=DATA/'gates'/tag
        assert tensor_hash(np.load(saved/'scores.npy'))==row['scores_tensor_sha256']
        post=torch.load(saved/'post_model.pth',map_location='cpu',weights_only=False)
        assert all(tensor_hash(post[k])==h for k,h in row['trainable_tensor_hashes'].items())
        assert object_hash(torch.load(saved/'post_optimizer.pth',map_location='cpu',weights_only=False))==row['optimizer_sha256']
    groups={}
    for prefix in ('repeat','zero'):
        rows=[json.loads((REPORT/'gates'/f'{prefix}_{i}.json').read_text()) for i in range(3)]
        assert len({json.loads((REPORT/'processes'/f'{prefix}_{i}.json').read_text())['pid'] for i in range(3)})==3
        assert all(behavior(r)==behavior(rows[0]) for r in rows)
        if prefix=='zero':assert rows[0]['model_sha256']==rows[0]['pre']['model'] and rows[0]['optimizer_sha256']==rows[0]['pre']['optimizer']
        groups[prefix]=dict(status='PASS',fresh_processes=3,reference=rows[0]['tag'],behavior=behavior(rows[0]))
    label=json.loads((REPORT/'gates/label_permuted.json').read_text())
    reference=json.loads((REPORT/'gates/repeat_0.json').read_text())
    assert behavior(label)==behavior(reference) and label['evaluator_label_sha256']!=reference['evaluator_label_sha256']
    estimated=2*sum(json.loads((REPORT/'gates'/f'repeat_{i}.json').read_text())['runtime_seconds'] for i in range(3))/3*4800
    assert estimated<86400,estimated
    result=dict(status='PASS',gate1='PASS_BITWISE',gate2=groups['repeat'],gate3='PASS_EXACT_LABEL_PERMUTATION',gate4=groups['zero'],
        native_buffer_independently_reconstructed=True,native_next_segment_independently_reconstructed=True,
        saved_gate_artifacts_verified=True,device_uuid=processes[0]['device_uuid'],
        backend_fingerprint=FINGERPRINT,estimated_conservative_grid_seconds=estimated,compute_gate='PASS',
        no_grid_rows_yet=not (REPORT/'rows').exists())
    (REPORT/'pre_grid_gates.json').write_text(json.dumps(result,indent=2)+'\n')
    (REPORT/'compute_preflight.json').write_text(json.dumps(dict(status='PASS',estimated_total_seconds=estimated,
        conservative_factor=2,planned_rows=4800,limit_seconds=86400,no_training=True,
        method='2 times mean fresh-process update-and-full-suffix-score seconds times 4800 arms; startup, compose and canary overhead additional'),indent=2)+'\n')
    print('ALL FOUR GATES PASS; projected conservative seconds',estimated,flush=True)


def grid():
    assert json.loads((REPORT/'pre_grid_gates.json').read_text())['status']=='PASS'
    assert json.loads((REPORT/'reuse_verification.json').read_text())['status']=='PASS'
    for name in ('pre_grid_gates.json','reuse_verification.json'):
        assert subprocess.check_output(['rtk','git','show',f'origin/main:reports/phase_d_v2/{name}'])==(REPORT/name).read_bytes()
    checks=json.loads((REPORT/'implementation_integrity.json').read_text())
    assert checks['status']=='PASS'
    assert all(digest(ROOT/p)==h for p,h in checks['code_sha256'].items())
    assert str(torch.cuda.get_device_properties(0).uuid)==json.loads((REPORT/'pre_grid_gates.json').read_text())['device_uuid']
    assert not (REPORT/'rows').exists(),'Fresh full grid only; no importing or silently resuming rows'
    reference=json.loads((REPORT/'gates/repeat_0.json').read_text())
    original_load=old.load;original_reset=old.reset;original_update=old.update;original_score=old.score
    def canary(tag):
        # Old loader continues reading only sealed input states from v1.
        got=arm(tag,canary=True)
        ok=behavior(got)==behavior(reference)
        entry=dict(tag=tag,status='PASS' if ok else 'FAIL',behavior=behavior(got),runtime_seconds=got['runtime_seconds'])
        with (REPORT/'canaries.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
        assert ok,'Canary failed: invalidate rows since previous passing canary'
    def reused_load(seed):
        target=old.DATA;old.DATA=OLD_DATA
        try:return original_load(seed)
        finally:old.DATA=target
    def checked_reset(*a,**kw):
        assert_backend();result=original_reset(*a,**kw);assert_backend();return result
    def checked_update(*a,**kw):
        assert_backend();result=original_update(*a,**kw);assert_backend();return result
    def checked_score(*a,**kw):
        assert_backend();result=original_score(*a,**kw);assert_backend();return result
    old.REPORT=REPORT;old.DATA=DATA;old.load=reused_load;old.reset=checked_reset;old.update=checked_update;old.score=checked_score
    (REPORT/'grid_start.json').write_text(json.dumps(dict(time=time.time(),backend_fingerprint=FINGERPRINT,planned_rows=4800))+'\n')
    completed=[]
    try:
        canary('before_grid')
        for source in range(3000,3010):
            for scenario in old.SCENARIOS:
                for kind in old.TYPES:
                    for seed in old.SEEDS:
                        result=old.run(source,scenario,kind,seed)
                        for r in result['rows']:
                            r.update(backend_fingerprint=FINGERPRINT,backend_seal_sha256=SEAL_SHA,version='D-v2',quarantined_v1_reused=False)
                        (REPORT/'rows'/f'{result["tag"]}.json').write_text(json.dumps(result,indent=2)+'\n')
            canary(f'after_source_{source}')
            completed.append(source)
        canary('after_grid')
    except BaseException as exc:
        (REPORT/'execution_stop.json').write_text(json.dumps(dict(status='STOP',error=repr(exc),validated_sources=completed,
            invalid_sources=[s for s in range(3000,3010) if s not in completed]),indent=2)+'\n')
        raise
    (REPORT/'grid_complete.json').write_text(json.dumps(dict(time=time.time(),rows=4800,validated_sources=completed,canaries=12,status='PASS'))+'\n')


def main():
    mode=sys.argv[1];tag=sys.argv[2] if len(sys.argv)>2 else mode
    start(tag)
    if mode=='reuse':verify_reuse()
    elif mode=='repeat':arm(tag)
    elif mode=='zero':arm(tag,no_update=True)
    elif mode=='label':arm(tag,permuted=True)
    elif mode=='gates':gates()
    elif mode=='grid':grid()
    else:raise ValueError(mode)


if __name__=='__main__':main()
